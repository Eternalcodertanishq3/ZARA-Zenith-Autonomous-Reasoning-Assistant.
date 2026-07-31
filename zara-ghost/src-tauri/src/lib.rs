use tauri::{WebviewWindow, Position, Size, LogicalSize, LogicalPosition};

#[tauri::command]
async fn morph_window(window: WebviewWindow, task: String) {
    let (w, h, x, y, click_through) = match task.as_str() {
        "idle"   => (80.0,  80.0,  "Calc(100% - 120)", "Calc(100% - 120)", true),
        "chat"   => (420.0, 680.0, "Calc(100% - 460)",  "Calc(100% - 720)", false),
        "code"   => (900.0, 520.0, "Calc(100% - 940)",  "Calc(100% - 560)", false),
        "system" => (380.0, 380.0, "Calc(100% - 420)",  "Calc(100% - 420)", false),
        "vision" => (700.0, 140.0, "Calc(50% - 350)",   "40",               false),
        _ => return,
    };

    let _ = window.set_size(Size::Logical(LogicalSize { width: w, height: h }));
    let _ = window.set_position(Position::Logical(LogicalPosition { x: 0.0, y: 0.0 }));
    
    let _ = window.eval(&format!(
        "window.moveTo({{x: {}, y: {}}})",
        if x.starts_with("Calc") { "window.screen.availWidth - 460" } else { "window.screen.availWidth / 2 - 350" },
        if y.starts_with("Calc") && y.contains("100%") { "window.screen.availHeight - 720" } else { "40" }
    ));
    
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
        .invoke_handler(tauri::generate_handler![morph_window, start_drag])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
