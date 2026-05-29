// ATLAS desktop shell (Tauri v2) — Option A MVP.
//
// The webview loads the RUNNING ATLAS backend (see tauri.conf.json
// build.frontendDist / devUrl). The backend serves the React frontend with its
// server-injected window.ATLAS_BOOT_CONFIG, same-origin /vendor + /backend.js,
// and the /ws/agent WebSocket — none of which survive static bundling, so the
// shell is a native window + native file plugins, NOT a static-asset host.
//
// Deferred (see doc/wiki/tauri-desktop-shell.md): PyInstaller backend freeze +
// Tauri sidecar (Option B), code signing/notarization, CSP hardening.

// Prevents an extra console window on Windows in release. Harmless on macOS.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running ATLAS desktop shell");
}
