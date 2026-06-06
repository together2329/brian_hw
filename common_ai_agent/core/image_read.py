"""Image-read tool implementation backed by current LLM multimodal input."""

import base64
import glob
import importlib
import mimetypes
import os
import re
import sys
from types import ModuleType
from typing import Callable, Optional, Tuple


DEFAULT_IMAGE_PROMPT = "Describe this image in detail."
VALID_IMAGE_EXTENSIONS = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".svg",
    ".ico",
    ".tiff",
    ".tif",
})

NormalizeToolPath = Callable[[Optional[str]], str]
ResolveAssetPath = Callable[[str], str]
FindGitRoot = Callable[[str], Optional[str]]


def _load_config() -> Optional[ModuleType]:
    for module_name in ("config", "src.config"):
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue
    return None


def _load_llm_client() -> ModuleType:
    try:
        return importlib.import_module("llm_client")
    except ImportError:
        src_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        return importlib.import_module("llm_client")


def _default_normalize_tool_path(path: Optional[str]) -> str:
    return os.path.expanduser(str(path or "").strip()).replace("\\", "/")


def _default_resolve_asset_path(path: str) -> str:
    return path


def _default_find_git_root(path: str) -> Optional[str]:
    check = os.path.abspath(path) if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.exists(os.path.join(check, ".git")):
            return check
        parent = os.path.dirname(check)
        if parent == check:
            return None
        check = parent


def _similar_image_suggestions(search_dirs: list[str], name_no_ext: str) -> list[str]:
    suggestions: list[str] = []
    for search_dir in search_dirs:
        if not search_dir or not os.path.isdir(search_dir):
            continue
        for ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
            suggestions.extend(glob.glob(os.path.join(search_dir, name_no_ext[:10] + "*." + ext))[:2])
    return suggestions


def _find_fuzzy_image(path: str, basename: str, parent: str, cwd: str, desktop: str) -> str:
    name_no_ext = os.path.splitext(basename)[0]
    for search_dir in (parent, cwd, desktop):
        if not search_dir or not os.path.isdir(search_dir):
            continue
        for ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
            pattern = os.path.join(search_dir, "*" + name_no_ext[:15] + "*." + ext)
            matches = glob.glob(pattern)
            if matches:
                return matches[0]

    if not os.path.isdir(desktop):
        return ""
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", basename)
    time_match = re.search(r"(\d{1,2}\.\d{2})", basename)
    if not date_match and not time_match:
        return ""
    search_pat = "*"
    if date_match:
        search_pat += date_match.group(1) + "*"
    if time_match:
        search_pat += "*" + time_match.group(1) + "*"
    for ext in ("png", "jpg", "jpeg"):
        matches = glob.glob(os.path.join(desktop, search_pat + "." + ext))
        if matches:
            return matches[0]
    return ""


def _resolve_image_path(
    raw_path: str,
    normalize_tool_path: NormalizeToolPath,
    resolve_asset_path: ResolveAssetPath,
    find_git_root: FindGitRoot,
) -> Tuple[str, str]:
    path = normalize_tool_path(raw_path)
    path = re.sub(r"\s+", " ", path).strip("\"'")
    path = resolve_asset_path(path)
    if os.path.isfile(path):
        return path, ""

    basename = os.path.basename(path)
    parent = os.path.dirname(path) or "."
    cwd = os.getcwd()
    desktop = os.path.expanduser("~/Desktop")
    candidates = [os.path.join(cwd, path)]
    git_root = find_git_root(cwd)
    if git_root:
        candidates.append(os.path.join(git_root, path))
    if os.path.isdir(desktop):
        candidates.extend([os.path.join(desktop, basename), os.path.join(desktop, path)])
    candidates.append(os.path.expanduser("~/" + basename))
    downloads = os.path.expanduser("~/Downloads")
    if os.path.isdir(downloads):
        candidates.append(os.path.join(downloads, basename))

    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate, ""

    fuzzy = _find_fuzzy_image(path, basename, parent, cwd, desktop)
    if fuzzy:
        return fuzzy, ""

    suggestions = _similar_image_suggestions([parent, cwd, desktop], os.path.splitext(basename)[0])
    if suggestions:
        hint = ", ".join(f"'{suggestion}'" for suggestion in suggestions[:3])
        return "", f"Error: Image file not found: {path}. Did you mean: {hint}?"
    return "", f"Error: Image file not found: {path}. Use find_files('{basename}') to locate it."


def _mime_type_for_path(path: str, ext: str) -> str:
    if ext == ".svg":
        return "image/svg+xml"
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or "image/png"


def _image_read_model(cfg: ModuleType) -> str:
    env_model = os.getenv("IMAGE_READ_MODEL", "").strip()
    if env_model:
        return env_model
    model = str(getattr(cfg, "IMAGE_READ_MODEL", "") or "").strip()
    current_model = str(getattr(cfg, "MODEL_NAME", "") or "").strip()
    if model and model != "glm-4.6v":
        return model
    return current_model or model or "glm-4.6v"


def _format_size(file_size: int) -> str:
    if file_size < 1024 * 1024:
        return f"{file_size / 1024:.1f}KB"
    return f"{file_size / (1024 * 1024):.1f}MB"


def _data_url_for_image(path: str, mime_type: str) -> str:
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def read_image(
    path: Optional[str] = None,
    prompt: str = DEFAULT_IMAGE_PROMPT,
    normalize_tool_path: NormalizeToolPath = _default_normalize_tool_path,
    resolve_asset_path: ResolveAssetPath = _default_resolve_asset_path,
    find_git_root: FindGitRoot = _default_find_git_root,
) -> str:
    """Analyze a local image by sending it as an LLM input_image block."""

    if path is None:
        return 'Error: read_image() requires \'path\'. Usage: read_image(path="screenshot.png", prompt="What does this show?")'

    cfg = _load_config()
    if cfg is None:
        return "Error: config module not found"
    if not getattr(cfg, "ENABLE_IMAGE_READ", False):
        return "Error: Image read is disabled. Set ENABLE_IMAGE_READ=true in .config to enable."

    image_path, path_error = _resolve_image_path(path, normalize_tool_path, resolve_asset_path, find_git_root)
    if path_error:
        return path_error

    ext = os.path.splitext(image_path)[1].lower()
    if ext not in VALID_IMAGE_EXTENSIONS:
        supported = ", ".join(sorted(VALID_IMAGE_EXTENSIONS))
        return f"Error: Unsupported image format '{ext}'. Supported: {supported}"

    max_size_mb = int(getattr(cfg, "IMAGE_READ_MAX_SIZE", 8))
    file_size = os.path.getsize(image_path)
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return f"Error: Image too large ({file_size / (1024 * 1024):.1f}MB). Maximum: {max_size_mb}MB. Set IMAGE_READ_MAX_SIZE to increase."

    mime_type = _mime_type_for_path(image_path, ext)
    try:
        data_url = _data_url_for_image(image_path, mime_type)
    except OSError as exc:
        return f"Error reading image: {exc}"

    llm_client = _load_llm_client()
    result = str(llm_client.call_llm_raw(
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": str(prompt or DEFAULT_IMAGE_PROMPT)},
                {"type": "input_image", "image_url": data_url, "detail": "high"},
            ],
        }],
        model=_image_read_model(cfg),
        temperature=0.0,
        max_tokens=2048,
        caller_tag="read_image",
    ) or "").strip()
    if not result:
        return "Error: Empty response from vision-capable LLM."
    if result.startswith("Error"):
        return result

    header = (
        f"[Image: {os.path.basename(image_path)} | {mime_type} | "
        f"{_format_size(file_size)} | Model: {_image_read_model(cfg)}]\n\n"
    )
    return header + result
