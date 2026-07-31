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

    let (w, h, x, y, click_through) = match task.as_str() {
        "idle"   => (120.0, 120.0, center_x - 60.0,  20.0,  true),
        "chat"   => (420.0, 680.0, center_x - 210.0, 160.0, false),
        "code"   => (900.0, 520.0, center_x - 450.0, 160.0, false),
        "system" => (380.0, 380.0, center_x - 190.0, 160.0, false),
        "vision" => (700.0, 140.0, center_x - 350.0, 160.0, false),
        _ => return,
    };

    let _ = window.set_size(Size::Logical(LogicalSize { width: w, height: h }));
    let _ = window.set_position(Position::Logical(LogicalPosition { x, y }));
    let _ = window.set_ignore_cursor_events(click_through);
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
        .invoke_handler(tauri::generate_handler![morph_window, start_drag])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
