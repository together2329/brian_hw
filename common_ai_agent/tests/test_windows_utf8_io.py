import ast
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOTS = ("src", "core", "lib", "workflow", "scripts")
SKIP_PARTS = {"__pycache__", ".venv", "venv", "node_modules", "vendor"}


def _py_sources():
    for name in RUNTIME_ROOTS:
        root = PROJECT_ROOT / name
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if not (set(path.parts) & SKIP_PARTS):
                yield path


def _shell_sources():
    suffixes = {".sh", ".bash", ".ps1", ".bat", ".cmd"}
    for name in ("workflow", "scripts"):
        root = PROJECT_ROOT / name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in suffixes and not (set(path.parts) & SKIP_PARTS):
                yield path


def _call_text(source: str, open_paren: int) -> str:
    depth = 0
    quote = ""
    escaped = False
    for idx in range(open_paren, len(source)):
        ch = source[idx]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return source[open_paren : idx + 1]
    return source[open_paren:]


def _literal_mode(call: ast.Call) -> str:
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
        return str(call.args[1].value)
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
            return str(kw.value.value)
    return "r"


def test_runtime_text_file_io_is_utf8_explicit():
    """Windows cp949/mbcs defaults must not affect session/console files."""

    failures: list[str] = []
    for path in _py_sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"read_text", "write_text"}
                and not any(kw.arg == "encoding" for kw in node.keywords)
            ):
                failures.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: {node.func.attr} without encoding")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                if "b" not in _literal_mode(node) and not any(kw.arg == "encoding" for kw in node.keywords):
                    failures.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: open without encoding")
    assert failures == []


def test_workflow_shell_inline_python_text_io_is_utf8_explicit():
    failures: list[str] = []
    for path in _shell_sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        for attr in ("read_text", "write_text"):
            needle = f".{attr}("
            offset = 0
            while True:
                idx = text.find(needle, offset)
                if idx < 0:
                    break
                call = _call_text(text, idx + len(f".{attr}"))
                if "encoding=" not in call:
                    line = text.count("\n", 0, idx) + 1
                    failures.append(f"{path.relative_to(PROJECT_ROOT)}:{line}: {attr} without encoding")
                offset = idx + len(needle)
    assert failures == []


def test_text_subprocess_decoding_is_utf8_explicit():
    failures: list[str] = []
    for path in _py_sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            text_true = any(
                kw.arg == "text" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in node.keywords
            )
            if not text_true:
                continue
            has_encoding = any(kw.arg == "encoding" for kw in node.keywords)
            has_errors = any(kw.arg == "errors" for kw in node.keywords)
            if not (has_encoding and has_errors):
                failures.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: text=True without UTF-8 decoding policy")
    assert failures == []


def test_session_worker_env_forces_python_utf8(monkeypatch):
    monkeypatch.delenv("PYTHONUTF8", raising=False)
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    from core.session_process_manager import SessionProcessManager

    env = SessionProcessManager(db_path="atlas.db").build_worker_env("alice/dma/ssot-gen")

    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8:replace"
