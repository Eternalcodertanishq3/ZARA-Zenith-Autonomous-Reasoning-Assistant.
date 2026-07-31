use tauri::{WebviewWindow, Position, Size, LogicalSize, LogicalPosition, Manager};

#[tauri::command]
async fn morph_window(window: WebviewWindow, task: String) {
    let _ = window.set_shadow(false);
    
    // Get current window position and size for adaptive position-preserving expansion
    let current_pos = match window.outer_position() {
        Ok(pos) => pos,
        _ => return,
    };
    let current_size = match window.inner_size() {
        Ok(s) => s,
        _ => return,
    };

    let scale_factor = match window.current_monitor() {
        Ok(Some(m)) => m.scale_factor(),
        _ => 1.0,
    };

    let cur_x = current_pos.x as f64 / scale_factor;
    let cur_y = current_pos.y as f64 / scale_factor;
    let cur_w = current_size.width as f64 / scale_factor;
    let cur_h = current_size.height as f64 / scale_factor;

    // Current center point of the orb/pill on screen
    let center_x = cur_x + cur_w / 2.0;
    let center_y = cur_y + cur_h / 2.0;

    let (new_w, new_h) = match task.as_str() {
        "idle"     => (200.0, 200.0),
        "thinking" => (200.0, 200.0),
        "chat"     => (520.0, 200.0),
        "code"     => (820.0, 460.0),
        "system"   => (520.0, 360.0),
        "vision"   => (640.0, 240.0),
        _ => return,
    };

    // Calculate new top-left so window center stays stationary in place on screen!
    let new_x = center_x - new_w / 2.0;
    let new_y = center_y - new_h / 2.0;

    let _ = window.set_size(Size::Logical(LogicalSize { width: new_w, height: new_h }));
    let _ = window.set_position(Position::Logical(LogicalPosition { x: new_x, y: new_y }));
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
        .invoke_handler(tauri::generate_handler![morph_window, start_drag])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
