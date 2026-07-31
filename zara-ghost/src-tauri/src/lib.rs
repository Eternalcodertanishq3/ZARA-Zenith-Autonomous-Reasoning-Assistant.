use tauri::{WebviewWindow, Position, Size, LogicalSize, LogicalPosition, Manager};

#[cfg(target_os = "windows")]
#[allow(non_snake_case, non_camel_case_types)]
mod win32_capture {
    use std::ffi::c_void;

    type HDC = *mut c_void;
    type HBITMAP = *mut c_void;
    type HGDIOBJ = *mut c_void;
    type BOOL = i32;

    #[repr(C)]
    struct BITMAPINFOHEADER {
        biSize: u32,
        biWidth: i32,
        biHeight: i32,
        biPlanes: u16,
        biBitCount: u16,
        biCompression: u32,
        biSizeImage: u32,
        biXPelsPerMeter: i32,
        biYPelsPerMeter: i32,
        biClrUsed: u32,
        biClrImportant: u32,
    }

    #[repr(C)]
    struct RGBQUAD {
        rgbBlue: u8,
        rgbGreen: u8,
        rgbRed: u8,
        rgbReserved: u8,
    }

    #[repr(C)]
    struct BITMAPINFO {
        bmiHeader: BITMAPINFOHEADER,
        bmiColors: [RGBQUAD; 1],
    }

    extern "system" {
        fn GetDC(hWnd: *mut c_void) -> HDC;
        fn ReleaseDC(hWnd: *mut c_void, hDC: HDC) -> i32;
        fn CreateCompatibleDC(hDC: HDC) -> HDC;
        fn CreateCompatibleBitmap(hDC: HDC, cx: i32, cy: i32) -> HBITMAP;
        fn SelectObject(hDC: HDC, h: HGDIOBJ) -> HGDIOBJ;
        fn BitBlt(hdcDst: HDC, xDst: i32, yDst: i32, width: i32, height: i32, hdcSrc: HDC, xSrc: i32, ySrc: i32, rop: u32) -> BOOL;
        fn GetDIBits(hdc: HDC, hbm: HBITMAP, start: u32, lines: u32, bits: *mut c_void, bmi: *mut BITMAPINFO, usage: u32) -> i32;
        fn DeleteDC(hdc: HDC) -> BOOL;
        fn DeleteObject(ho: HGDIOBJ) -> BOOL;
    }

    const SRCCOPY: u32 = 0x00CC0020;
    const BI_RGB: u32 = 0;
    const DIB_RGB_COLORS: u32 = 0;

    pub fn capture_screen_area(x: i32, y: i32, width: i32, height: i32) -> Option<Vec<u8>> {
        if width <= 0 || height <= 0 { return None; }
        unsafe {
            let hdc_screen = GetDC(std::ptr::null_mut());
            if hdc_screen.is_null() { return None; }

            let hdc_mem = CreateCompatibleDC(hdc_screen);
            let hbitmap = CreateCompatibleBitmap(hdc_screen, width, height);
            let old_obj = SelectObject(hdc_mem, hbitmap as HGDIOBJ);

            BitBlt(hdc_mem, 0, 0, width, height, hdc_screen, x, y, SRCCOPY);

            let mut bmi = BITMAPINFO {
                bmiHeader: BITMAPINFOHEADER {
                    biSize: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    biWidth: width,
                    biHeight: -height,
                    biPlanes: 1,
                    biBitCount: 32,
                    biCompression: BI_RGB,
                    biSizeImage: (width * height * 4) as u32,
                    biXPelsPerMeter: 0,
                    biYPelsPerMeter: 0,
                    biClrUsed: 0,
                    biClrImportant: 0,
                },
                bmiColors: [RGBQUAD { rgbBlue: 0, rgbGreen: 0, rgbRed: 0, rgbReserved: 0 }],
            };

            let mut buffer = vec![0u8; (width * height * 4) as usize];
            GetDIBits(hdc_mem, hbitmap, 0, height as u32, buffer.as_mut_ptr() as *mut c_void, &mut bmi, DIB_RGB_COLORS);

            for chunk in buffer.chunks_exact_mut(4) {
                let b = chunk[0];
                let r = chunk[2];
                chunk[0] = r;
                chunk[2] = b;
                chunk[3] = 255;
            }

            SelectObject(hdc_mem, old_obj);
            DeleteObject(hbitmap as HGDIOBJ);
            DeleteDC(hdc_mem);
            ReleaseDC(std::ptr::null_mut(), hdc_screen);

            Some(buffer)
        }
    }
}

#[tauri::command]
async fn capture_desktop(window: WebviewWindow) -> Result<Vec<u8>, String> {
    let position = window.outer_position().map_err(|e| e.to_string())?;
    let size = window.inner_size().map_err(|e| e.to_string())?;

    #[cfg(target_os = "windows")]
    {
        win32_capture::capture_screen_area(position.x, position.y, size.width as i32, size.height as i32)
            .ok_or_else(|| "Failed to capture desktop screen".to_string())
    }
    #[cfg(not(target_os = "windows"))]
    {
        Err("Not supported on non-windows platform".to_string())
    }
}

#[tauri::command]
async fn morph_window(window: WebviewWindow, task: String) {
    let _ = window.set_shadow(false);
    let monitor = match window.current_monitor() {
        Ok(Some(m)) => m,
        _ => return,
    };
    
    let scale_factor = monitor.scale_factor();
    let screen_size = monitor.size().to_logical::<f64>(scale_factor);

    let center_x = screen_size.width / 2.0;
    let center_y = screen_size.height / 2.0;

    let (w, h, x, y) = match task.as_str() {
        "idle"     => (200.0, 200.0, center_x - 100.0, center_y - 100.0),
        "thinking" => (200.0, 200.0, center_x - 100.0, center_y - 100.0),
        "chat"     => (520.0, 280.0, center_x - 260.0, center_y - 140.0),
        "code"     => (860.0, 520.0, center_x - 430.0, center_y - 260.0),
        "system"   => (480.0, 400.0, center_x - 240.0, center_y - 200.0),
        "vision"   => (640.0, 220.0, center_x - 320.0, center_y - 110.0),
        _ => return,
    };

    let _ = window.set_size(Size::Logical(LogicalSize { width: w, height: h }));
    let _ = window.set_position(Position::Logical(LogicalPosition { x, y }));
    let _ = window.set_ignore_cursor_events(false);
}

#[tauri::command]
fn start_drag(window: WebviewWindow) {
    let _ = window.start_dragging();
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_shadow(false);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![morph_window, start_drag, capture_desktop])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
