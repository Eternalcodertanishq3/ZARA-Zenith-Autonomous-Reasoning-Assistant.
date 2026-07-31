use tauri::{WebviewWindow, Position, Size, LogicalSize, LogicalPosition, Manager};

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
        "idle"     => (240.0, 240.0, center_x - 120.0, center_y - 120.0),
        "thinking" => (240.0, 240.0, center_x - 120.0, center_y - 120.0),
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

#[tauri::command]
fn set_ignore_cursor(window: WebviewWindow, ignore: bool) {
    let _ = window.set_ignore_cursor_events(ignore);
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
        .invoke_handler(tauri::generate_handler![morph_window, start_drag, set_ignore_cursor])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
