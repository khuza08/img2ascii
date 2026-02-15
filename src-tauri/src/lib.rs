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
    image_base64: String, // Added for reliable frontend preview
    txt_path: String,
}

// Exactly matching the Python char set after reverse:
// "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "[::-1]
const CHARS: &str = " .'`^ \",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$";
const ONE_CHAR_WIDTH: u32 = 10;
const ONE_CHAR_HEIGHT: u32 = 18;
const MAX_ASCII_WIDTH: u32 = 400; // Safety limit to prevent freezes

#[tauri::command]
async fn convert_image(params: ConversionParams) -> Result<ConversionResult, String> {
    // 1. Load Image
    let img = image::open(&params.filepath)
        .map_err(|e| format!("Failed to open image: {e}"))?;

    // 2. Resize First (Optimization)
    let (orig_width, orig_height) = img.dimensions();
    
    // Calculate raw target dimensions
    let mut target_w = if params.orientation == "L" {
        (params.scale_factor * orig_width as f32) as u32
    } else {
        (params.scale_factor * orig_width as f32 * (ONE_CHAR_HEIGHT as f32 / ONE_CHAR_WIDTH as f32)) as u32
    };
    
    // Apply safety cap
    if target_w > MAX_ASCII_WIDTH {
        target_w = MAX_ASCII_WIDTH;
    }
    
    // Maintain aspect ratio based on the (possibly capped) width
    let final_scale = target_w as f32 / (if params.orientation == "L" { orig_width as f32 } else { orig_width as f32 * (ONE_CHAR_HEIGHT as f32 / ONE_CHAR_WIDTH as f32) });
    
    let target_h = if params.orientation == "L" {
        (final_scale * orig_height as f32 * (ONE_CHAR_WIDTH as f32 / ONE_CHAR_HEIGHT as f32)) as u32
    } else {
        (final_scale * orig_height as f32) as u32
    };
    
    let resized = img.resize_exact(target_w, target_h, image::imageops::FilterType::Nearest);
    let mut resized_rgb = resized.to_rgb8();

    // 3. Adjustments on the small image
    
    // Saturation (Color Enhancement)
    if (params.saturation - 1.0).abs() > 0.01 {
        for pixel in resized_rgb.pixels_mut() {
            let [r, g, b] = pixel.0;
            let gray = (r as f32 + g as f32 + b as f32) / 3.0;
            pixel.0[0] = (gray + params.saturation * (r as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (gray + params.saturation * (g as f32 - gray)).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (gray + params.saturation * (b as f32 - gray)).clamp(0.0, 255.0) as u8;
        }
    }

    // Brightness
    if (params.brightness - 1.0).abs() > 0.01 {
        for pixel in resized_rgb.pixels_mut() {
            pixel.0[0] = (pixel.0[0] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[1] = (pixel.0[1] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
            pixel.0[2] = (pixel.0[2] as f32 * params.brightness).clamp(0.0, 255.0) as u8;
        }
    }
    
    // Contrast
    if (params.contrast - 1.0).abs() > 0.01 {
        for pixel in resized_rgb.pixels_mut() {
            for i in 0..3 {
                pixel.0[i] = ((pixel.0[i] as f32 - 128.0) * params.contrast + 128.0).clamp(0.0, 255.0) as u8;
            }
        }
    }

    let (w, h) = resized_rgb.dimensions();
    
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
        
    // Encode to base64 for reliable live preview
    let mut image_data = Vec::new();
    let mut cursor = std::io::Cursor::new(&mut image_data);
    output_img.write_to(&mut cursor, image::ImageFormat::Png)
        .map_err(|e| format!("Failed to encode image to PNG for base64: {e}"))?;
    
    use base64::{Engine as _, engine::general_purpose};
    let image_base64 = general_purpose::STANDARD.encode(&image_data);

    let mut f = File::create(&txt_path)
        .map_err(|e| format!("Failed to create txt file: {e}"))?;
    f.write_all(ascii_text.as_bytes())
        .map_err(|e| format!("Failed to write txt file: {e}"))?;

    Ok(ConversionResult {
        text: ascii_text,
        image_path: std::env::current_dir().unwrap().join(&png_path).to_string_lossy().to_string(),
        image_base64: format!("data:image/png;base64,{}", image_base64),
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
