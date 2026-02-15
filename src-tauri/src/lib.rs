use serde::{Deserialize, Serialize};
use image::{GenericImageView, ImageBuffer, Rgb};
use imageproc::drawing::draw_text_mut;
use ab_glyph::{FontArc, PxScale};
use std::fs::File;
use std::io::Write;

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
    text: String,
    image_path: String,
    txt_path: String,
}

// Exactly matching the Python char set after reverse:
// "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
const CHARS: &str = " .'`^ \",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$";
const ONE_CHAR_WIDTH: u32 = 10;
const ONE_CHAR_HEIGHT: u32 = 18;

#[tauri::command]
async fn convert_image(params: ConversionParams) -> Result<ConversionResult, String> {
    // 1. Load Image
    let mut img = image::open(&params.filepath)
        .map_err(|e| format!("Failed to open image: {e}"))?;

    // 2. Adjustments (matching PIL's behavior as closely as possible)
    
    // Saturation (Color Enhancement)
    // PIL's Color.enhance(factor): 0.0 is grayscale, 1.0 is original.
    // result = grayscale * (1-factor) + original * factor
    if (params.saturation - 1.0).abs() > 0.01 {
        let mut rgb_img = img.to_rgb8();
        for pixel in rgb_img.pixels_mut() {
            let [r, g, b] = pixel.0;
            // Simple average matches the Python's intent for grayscale
            let gray = (r as f32 + g as f32 + b as f32) / 3.0;
            
            pixel.0[0] = (gray + params.saturation * (r as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (gray + params.saturation * (g as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (gray + params.saturation * (b as f32 - gray)).clamp(0.0, 255.0) as u8;
        }
        img = image::DynamicImage::ImageRgb8(rgb_img);
    }

    // Brightness
    if (params.brightness - 1.0).abs() > 0.01 {
        // PIL brighten scale factor is multiplicative on pixels.
        // image crate `brighten` is additive. We want multiplicative.
        let mut rgb_img = img.to_rgb8();
        for pixel in rgb_img.pixels_mut() {
            pixel.0[0] = (pixel.0[0] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (pixel.0[1] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (pixel.0[2] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
        }
        img = image::DynamicImage::ImageRgb8(rgb_img);
    }
    
    // Contrast
    if (params.contrast - 1.0).abs() > 0.01 {
        // image crate `adjust_contrast` takes percentage (-100 to 100) or similar? 
        // Actually it takes f32: 0 is gray, 1 is original, >1 increases.
        // Wait, different image crate versions have different signatures.
        // Let's use manual to be safe and match PIL: (pixel - 128) * contrast + 128
        let mut rgb_img = img.to_rgb8();
        for pixel in rgb_img.pixels_mut() {
            for i in 0..3 {
                pixel.0[i] = ((pixel.0[i] as f32 - 128.0) * params.contrast + 128.0).clamp(0.0, 255.0) as u8;
            }
        }
        img = image::DynamicImage::ImageRgb8(rgb_img);
    }

    // 3. Resize
    let (orig_width, orig_height) = img.dimensions();
    let (new_width, new_height) = if params.orientation == "L" {
        (
            (params.scale_factor * orig_width as f32) as u32,
            (params.scale_factor * orig_height as f32 * (ONE_CHAR_WIDTH as f32 / ONE_CHAR_HEIGHT as f32)) as u32
        )
    } else {
        (
            (params.scale_factor * orig_width as f32 * (ONE_CHAR_HEIGHT as f32 / ONE_CHAR_WIDTH as f32)) as u32,
            (params.scale_factor * orig_height as f32) as u32
        )
    };
    
    let resized = img.resize_exact(new_width, new_height, image::imageops::FilterType::Nearest);
    let (w, h) = resized.dimensions();
    let resized_rgb = resized.to_rgb8();
    
    // 4. ASCII Conversion
    let char_array: Vec<char> = CHARS.chars().collect();
    let char_len = char_array.len();
    let interval = char_len as f32 / 256.0;

    let mut ascii_text = String::with_capacity((w * h + h) as usize);
    let mut output_img = ImageBuffer::new(w * ONE_CHAR_WIDTH, h * ONE_CHAR_HEIGHT);
    
    // Load font
    let font_data = include_bytes!("../courier.ttf");
    let font = FontArc::try_from_slice(font_data as &[u8])
        .map_err(|e| format!("Error constructing font: {e}"))?;
    let scale = PxScale::from(16.0);

    for y in 0..h {
        let mut line_chars = String::with_capacity(w as usize);
        
        // Horizontal scan for grouping
        let mut x = 0;
        while x < w {
            let start_x = x;
            let pixel = resized_rgb.get_pixel(x, y);
            let color = Rgb(pixel.0);
            
            // Find length of consecutive pixels with same color
            while x + 1 < w && resized_rgb.get_pixel(x + 1, y).0 == pixel.0 {
                x += 1;
            }
            
            // Collect characters for this group
            let mut group_text = String::new();
            for gx in start_x..=x {
                let gp = resized_rgb.get_pixel(gx, y);
                let gray = (gp.0[0] as u32 + gp.0[1] as u32 + gp.0[2] as u32) / 3;
                let idx = ((gray as f32 * interval) as usize).min(char_len - 1);
                let c = char_array[idx];
                group_text.push(c);
                line_chars.push(c);
            }
            
            // Draw the group
            draw_text_mut(
                &mut output_img,
                color,
                (start_x * ONE_CHAR_WIDTH) as i32,
                (y * ONE_CHAR_HEIGHT) as i32,
                scale,
                &font,
                &group_text
            );
            
            x += 1;
        }
        
        ascii_text.push_str(&line_chars);
        ascii_text.push('\n');
    }

    // 5. Save results
    let base_name = &params.output_name;
    let png_path = format!("{}.png", base_name);
    let txt_path = format!("{}.txt", base_name);
    
    output_img.save(&png_path)
        .map_err(|e| format!("Failed to save image: {e}"))?;
        
    let mut f = File::create(&txt_path)
        .map_err(|e| format!("Failed to create txt file: {e}"))?;
    f.write_all(ascii_text.as_bytes())
        .map_err(|e| format!("Failed to write txt file: {e}"))?;

    Ok(ConversionResult {
        text: ascii_text,
        image_path: std::env::current_dir().unwrap().join(&png_path).to_string_lossy().to_string(),
        txt_path: std::env::current_dir().unwrap().join(&txt_path).to_string_lossy().to_string(),
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![convert_image])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
