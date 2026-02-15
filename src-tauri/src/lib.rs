use serde::{Deserialize, Serialize};
use image::{GenericImageView, Rgb, DynamicImage, RgbImage};
use imageproc::drawing::draw_text_mut;
use ab_glyph::{FontArc, PxScale};
use std::fs::File;
use std::io::Write;
use std::sync::Arc;
use parking_lot::RwLock;
use rayon::prelude::*;

#[derive(Deserialize)]
pub struct ConversionParams {
    filepath: String,
    output_name: String,
    orientation: String,
    scale_factor: f32,
    brightness: f32,
    contrast: f32,
    saturation: f32,
}

#[derive(Serialize)]
pub struct ConversionResult {
    pub image_path: String,
    pub image_base64: String,
    pub txt_path: String,
}

// Global cache for the last loaded image to avoid disk I/O
pub struct ImageCache {
    pub path: RwLock<Option<String>>,
    pub image: RwLock<Option<Arc<DynamicImage>>>,
}

const CHARS: &str = " .'`^ \",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$";
const ONE_CHAR_WIDTH: u32 = 10;
const ONE_CHAR_HEIGHT: u32 = 18;
const MAX_ASCII_WIDTH: u32 = 400; // Safety limit

#[tauri::command]
async fn convert_image(
    params: ConversionParams,
    cache: tauri::State<'_, ImageCache>
) -> Result<ConversionResult, String> {
    // 1. Load or Get Cached Image
    let img_arc = {
        let current_path = cache.path.read();
        if current_path.as_deref() == Some(&params.filepath) {
            let img_opt = cache.image.read();
            img_opt.as_ref().cloned()
        } else {
            None
        }
    };

    let img = if let Some(cached) = img_arc {
        cached
    } else {
        let loaded = image::open(&params.filepath)
            .map_err(|e| format!("Failed to open image: {e}"))?;
        let wrapped = Arc::new(loaded);
        *cache.path.write() = Some(params.filepath.clone());
        *cache.image.write() = Some(wrapped.clone());
        wrapped
    };

    // 2. Resize First (Optimization)
    let (orig_width, orig_height) = img.dimensions();
    
    let mut target_w = if params.orientation == "L" {
        (params.scale_factor * orig_width as f32) as u32
    } else {
        (params.scale_factor * orig_width as f32 * (ONE_CHAR_HEIGHT as f32 / ONE_CHAR_WIDTH as f32)) as u32
    };
    
    if target_w > MAX_ASCII_WIDTH {
        target_w = MAX_ASCII_WIDTH;
    }
    
    let final_scale = target_w as f32 / (if params.orientation == "L" { orig_width as f32 } else { orig_width as f32 * (ONE_CHAR_HEIGHT as f32 / ONE_CHAR_WIDTH as f32) });
    
    let target_h = if params.orientation == "L" {
        (final_scale * orig_height as f32 * (ONE_CHAR_WIDTH as f32 / ONE_CHAR_HEIGHT as f32)) as u32
    } else {
        (final_scale * orig_height as f32) as u32
    };
    
    let resized = img.resize_exact(target_w, target_h, image::imageops::FilterType::Nearest);
    let mut resized_rgb = resized.to_rgb8();

    // 3. Parallel Adjustments
    resized_rgb.par_pixels_mut().for_each(|pixel| {
        // Saturation
        if (params.saturation - 1.0).abs() > 0.01 {
            let [r, g, b] = pixel.0;
            let gray = (r as f32 + g as f32 + b as f32) / 3.0;
            pixel.0[0] = (gray + params.saturation * (r as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (gray + params.saturation * (g as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (gray + params.saturation * (b as f32 - gray)).clamp(0.0, 255.0) as u8;
        }

        // Brightness
        if (params.brightness - 1.0).abs() > 0.01 {
            pixel.0[0] = (pixel.0[0] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (pixel.0[1] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (pixel.0[2] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
        }

        // Contrast
        if (params.contrast - 1.0).abs() > 0.01 {
            for i in 0..3 {
                pixel.0[i] = ((pixel.0[i] as f32 - 128.0) * params.contrast + 128.0).clamp(0.0, 255.0) as u8;
            }
        }
    });

    let (w, h) = resized_rgb.dimensions();
    
    // 4. Parallel ASCII & Rendering
    let char_array: Vec<char> = CHARS.chars().collect();
    let font_data = include_bytes!("../courier.ttf");
    let font = FontArc::try_from_slice(font_data as &[u8])
        .map_err(|e| format!("Error constructing font: {e}"))?;
    let scale = PxScale::from(16.0);
    
    // Prepare thread-safe chunks for drawing
    // We'll create the full buffer first
    let mut output_img = RgbImage::new(w * ONE_CHAR_WIDTH, h * ONE_CHAR_HEIGHT);
    let mut ascii_lines: Vec<String> = vec![String::new(); h as usize];

    // ASCII Text Generation (Parallel)
    ascii_lines.par_iter_mut().enumerate().for_each(|(y, line)| {
        let mut line_str = String::with_capacity(w as usize);
        let interval = char_array.len() as f32 / 256.0;
        for x in 0..w {
            let gp = resized_rgb.get_pixel(x, y as u32);
            let gray = (gp.0[0] as u32 + gp.0[1] as u32 + gp.0[2] as u32) / 3;
            let idx = ((gray as f32 * interval) as usize).min(char_array.len() - 1);
            line_str.push(char_array[idx]);
        }
        *line = line_str;
    });

    // Image Drawing (Chunked Rows) - imageproc isn't naturally thread-safe for buffer drawing,
    // so we render chunks of rows into separate sub-images and then combine, or just use a mutex wrap
    // FOR SPEED: We'll draw row-by-row consecutively for now since text drawing is font-heavy,
    // but the filter and text calc are already parallel.
    for y in 0..h {
        let line = &ascii_lines[y as usize];
        let mut x = 0;
        while x < w {
            let start_x = x;
            let pixel = resized_rgb.get_pixel(x, y);
            let color = Rgb(pixel.0);
            while x + 1 < w && resized_rgb.get_pixel(x + 1, y).0 == pixel.0 {
                x += 1;
            }
            let group_text = &line[start_x as usize..=x as usize];
            draw_text_mut(
                &mut output_img,
                color,
                (start_x * ONE_CHAR_WIDTH) as i32,
                (y * ONE_CHAR_HEIGHT) as i32,
                scale,
                &font,
                group_text
            );
            x += 1;
        }
    }

    let ascii_text = ascii_lines.join("\n");

    // 5. Save & Response
    let base_name = &params.output_name;
    let png_path = format!("{}.png", base_name);
    let txt_path = format!("{}.txt", base_name);
    
    // Save full resolution PNG to disk
    output_img.save(&png_path).map_err(|e| format!("Failed save: {e}"))?;
    
    // Create downscaled preview for Base64 (to keep IPC bridge fast)
    let (pw, ph) = output_img.dimensions();
    let preview_img = if pw > 1200 {
        let scale = 1200.0 / pw as f32;
        DynamicImage::ImageRgb8(output_img).resize(1200, (ph as f32 * scale) as u32, image::imageops::FilterType::Triangle)
    } else {
        DynamicImage::ImageRgb8(output_img)
    };
    
    let mut preview_data = Vec::new();
    let mut cursor = std::io::Cursor::new(&mut preview_data);
    preview_img.write_to(&mut cursor, image::ImageFormat::Png).map_err(|e| e.to_string())?;
    
    use base64::{Engine as _, engine::general_purpose};
    let image_base64 = format!("data:image/png;base64,{}", general_purpose::STANDARD.encode(&preview_data));

    let mut f = File::create(&txt_path).map_err(|e| e.to_string())?;
    f.write_all(ascii_text.as_bytes()).map_err(|e| e.to_string())?;

    Ok(ConversionResult {
        image_path: std::env::current_dir().unwrap().join(&png_path).to_string_lossy().to_string(),
        image_base64,
        txt_path: std::env::current_dir().unwrap().join(&txt_path).to_string_lossy().to_string(),
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(ImageCache {
            path: RwLock::new(None),
            image: RwLock::new(None),
        })
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![convert_image])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
