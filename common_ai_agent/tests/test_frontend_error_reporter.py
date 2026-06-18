from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend" / "atlas"
ENTRY_HTML = [
    FRONTEND / "index.vite.html",
    FRONTEND / "lobby.vite.html",
    FRONTEND / "preview.html",
    FRONTEND / "admin.html",
]


def test_entry_error_reporters_ignore_resizeobserver_loop_notification():
    for path in ENTRY_HTML:
        src = path.read_text(encoding="utf-8")

        assert "function isResizeObserverLoopNotification(detail)" in src
        assert "function ignoreResizeObserverLoopNotification(ev, detail)" in src
        assert "ResizeObserver loop completed with undelivered notifications." in src
        assert "ResizeObserver loop limit exceeded" in src
        assert "ev.preventDefault()" in src
        assert "ev.stopImmediatePropagation()" in src
        assert "if (ignoreResizeObserverLoopNotification(ev, msg)) return;" in src


def test_entry_error_reporters_keep_generic_uncaught_errors_visible():
    for path in ENTRY_HTML:
        src = path.read_text(encoding="utf-8")
        error_handler = src.split("window.addEventListener('error'", 1)[1].split("window.addEventListener('unhandledrejection'", 1)[0]

        assert "append('uncaught', msg);" in error_handler
        assert "if (ignoreResizeObserverLoopNotification(ev, msg)) return;" in error_handler
        assert error_handler.index("if (ignoreResizeObserverLoopNotification(ev, msg)) return;") < error_handler.index("append('uncaught', msg);")
