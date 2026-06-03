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

use std::{env, error::Error, fmt};

const DEFAULT_BACKEND_URL: &str = "http://localhost:3000/";

#[derive(Debug, PartialEq, Eq)]
enum BackendUrlError {
    Parse { value: String },
    UnsupportedScheme { scheme: String },
}

impl fmt::Display for BackendUrlError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Parse { value } => write!(formatter, "invalid backend URL: {value}"),
            Self::UnsupportedScheme { scheme } => {
                write!(formatter, "backend URL must use http or https, got {scheme}")
            }
        }
    }
}

impl Error for BackendUrlError {}

fn parse_backend_url(value: &str) -> Result<tauri::Url, BackendUrlError> {
    let parsed = tauri::Url::parse(value).map_err(|_| BackendUrlError::Parse {
        value: value.to_string(),
    })?;
    match parsed.scheme() {
        "http" | "https" => Ok(parsed),
        scheme => Err(BackendUrlError::UnsupportedScheme {
            scheme: scheme.to_string(),
        }),
    }
}

fn backend_url_from_args_and_env<I, S>(
    args: I,
    env_value: Option<&str>,
) -> Result<tauri::Url, BackendUrlError>
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let mut iter = args.into_iter();
    while let Some(arg) = iter.next() {
        let text = arg.as_ref();
        if let Some(value) = text.strip_prefix("--backend-url=") {
            return parse_backend_url(value);
        }
        if text == "--backend-url" || text == "--backend" {
            if let Some(value) = iter.next() {
                return parse_backend_url(value.as_ref());
            }
        }
    }

    let raw = env_value
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or(DEFAULT_BACKEND_URL);
    parse_backend_url(raw)
}

fn backend_url() -> Result<tauri::Url, BackendUrlError> {
    let env_value = env::var("ATLAS_DESKTOP_BACKEND_URL").ok();
    backend_url_from_args_and_env(env::args(), env_value.as_deref())
}

fn build_main_window(app: &mut tauri::App) -> Result<(), Box<dyn Error>> {
    let url = backend_url()?;
    tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::External(url))
        .title("ATLAS")
        .inner_size(1600.0, 1000.0)
        .min_inner_size(1024.0, 700.0)
        .resizable(true)
        .center()
        .build()?;
    Ok(())
}

fn main() {
    let result = tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .setup(build_main_window)
        .run(tauri::generate_context!())
        .map_err(|error| {
            eprintln!("error while running ATLAS desktop shell: {error}");
            error
        });
    if result.is_err() {
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn backend_url_defaults_to_localhost_when_unset() {
        let url = backend_url_from_args_and_env(["atlas-desktop"], None);

        assert_eq!(
            url.map(|value| value.to_string()),
            Ok("http://localhost:3000/".to_string()),
        );
    }

    #[test]
    fn backend_url_prefers_launch_argument_over_env() {
        let url = backend_url_from_args_and_env(
            ["atlas-desktop", "--backend-url=http://127.0.0.1:4567/?scm=perforce"],
            Some("http://127.0.0.1:3000"),
        );

        assert_eq!(
            url.map(|value| value.to_string()),
            Ok("http://127.0.0.1:4567/?scm=perforce".to_string()),
        );
    }

    #[test]
    fn backend_url_rejects_non_http_schemes() {
        let url = backend_url_from_args_and_env(["atlas-desktop"], Some("file:///tmp/index.html"));

        assert!(matches!(url, Err(BackendUrlError::UnsupportedScheme { .. })));
    }
}
