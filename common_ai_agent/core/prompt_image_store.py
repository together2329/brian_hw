"""Prompt image storage and lazy conversion helpers."""

from __future__ import annotations

import base64
import binascii
import hashlib
import mimetypes
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

try:
    from PIL import Image
except Exception:  # pragma: no cover - Pillow is optional at import time.
    Image = None  # type: ignore[assignment]


MAX_PROMPT_IMAGE_DIMENSION = 2048

_ALLOWED_IMAGE_DETAILS = {"auto", "low", "high"}
_DATA_IMAGE_PREFIX = "data:image/"
_REMOTE_IMAGE_PREFIXES = ("https://", "http://")
_PATH_KEYS = ("path", "image_path", "imagePath", "local_path", "localPath", "file_path", "filePath")
_URL_KEYS = ("image_url", "imageUrl", "url")
_PRESERVABLE_MIME_TYPES = {"image/png", "image/jpeg", "image/webp"}
_FORMAT_MIME_TYPES = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "WEBP": "image/webp",
}


def normalize_prompt_image_detail(value: Any) -> str:
    """Return a Responses-compatible image detail value."""

    raw = str(value or "auto").strip().lower()
    return raw if raw in _ALLOWED_IMAGE_DETAILS else "auto"


def default_prompt_image_store_root() -> Path:
    """Return the directory used for browser-pasted prompt image files."""

    raw = os.environ.get("ATLAS_PROMPT_IMAGE_STORE", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".common_ai_agent" / "runtime" / "prompt_images"


def spool_prompt_images_for_session(
    value: Any,
    *,
    session_id: str | None = None,
    store_root: Path | None = None,
) -> list[dict[str, str]]:
    """Convert browser image attachments into small queue-safe payloads.

    Data URLs are written to local files and represented by ``path`` metadata.
    Existing local path and remote URL payloads are preserved.
    """

    if not isinstance(value, list):
        return []
    root = store_root or default_prompt_image_store_root()
    attachments: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        detail = normalize_prompt_image_detail(item.get("detail"))
        name = _first_nonempty_string(item, ("name", "filename", "fileName"))
        mime_type = _first_nonempty_string(item, ("mime_type", "mimeType", "type"))
        path = _first_nonempty_string(item, _PATH_KEYS)
        if path:
            payload = {"path": path, "detail": detail}
            if mime_type:
                payload["mime_type"] = mime_type
            if name:
                payload["name"] = name
            attachments.append(payload)
            continue

        image_url = _first_nonempty_string(item, _URL_KEYS)
        if not image_url:
            continue
        if image_url.startswith(_DATA_IMAGE_PREFIX):
            try:
                stored = _spool_data_url(
                    image_url,
                    session_id=session_id,
                    store_root=root,
                    detail=detail,
                    name=name,
                    fallback_mime_type=mime_type,
                )
            except ValueError:
                continue
            attachments.append(stored)
            continue
        if image_url.startswith(_REMOTE_IMAGE_PREFIXES):
            payload = {"image_url": image_url, "detail": detail}
            if name:
                payload["name"] = name
            attachments.append(payload)
    return attachments


def load_prompt_image_path_as_data_url(path: str, *, detail: str = "auto") -> str:
    """Read a local image file and return a resized data URL for the LLM."""

    raw_path = str(path or "").strip()
    if not raw_path:
        raise ValueError("empty image path")
    image_path = Path(raw_path).expanduser()
    data = image_path.read_bytes()
    output, mime_type = _prepare_prompt_image_bytes(
        image_path,
        data,
        detail=detail,
    )
    encoded = base64.b64encode(output).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _spool_data_url(
    data_url: str,
    *,
    session_id: str | None,
    store_root: Path,
    detail: str,
    name: str,
    fallback_mime_type: str,
) -> dict[str, str]:
    mime_type, data = _decode_data_url(data_url, fallback_mime_type=fallback_mime_type)
    digest = hashlib.sha256(data).hexdigest()
    session_dir = store_root / _session_store_name(session_id)
    ext = _extension_for_mime_type(mime_type)
    target = session_dir / f"{digest}{ext}"
    session_dir.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        tmp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
        tmp.write_bytes(data)
        os.replace(tmp, target)
    payload = {
        "path": str(target),
        "detail": detail,
        "mime_type": mime_type,
    }
    if name:
        payload["name"] = name
    return payload


def _prepare_prompt_image_bytes(
    image_path: Path,
    data: bytes,
    *,
    detail: str,
) -> tuple[bytes, str]:
    mime_type = _mime_type_for_path(image_path)
    if Image is None:
        if mime_type in _PRESERVABLE_MIME_TYPES:
            return data, mime_type
        raise RuntimeError("Pillow is required to decode this image")

    with Image.open(BytesIO(data)) as image:
        image.load()
        source_format = str(image.format or "").upper()
        source_mime = _FORMAT_MIME_TYPES.get(source_format) or mime_type
        width, height = image.size
        resized = _needs_resize(width, height)
        if not resized and source_mime in _PRESERVABLE_MIME_TYPES:
            return data, source_mime

        output_mime = source_mime if source_mime in _PRESERVABLE_MIME_TYPES else "image/png"
        output_image = image.copy()
        if resized:
            resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
            output_image.thumbnail(
                (MAX_PROMPT_IMAGE_DIMENSION, MAX_PROMPT_IMAGE_DIMENSION),
                resampling,
            )
        output = BytesIO()
        output_format = _format_for_mime_type(output_mime)
        save_kwargs: dict[str, Any] = {}
        if output_mime == "image/jpeg":
            if output_image.mode not in {"RGB", "L"}:
                output_image = output_image.convert("RGB")
            save_kwargs.update({"quality": 85, "optimize": True})
        elif output_mime == "image/webp":
            save_kwargs.update({"quality": 85, "method": 4})
        elif output_mime == "image/png":
            save_kwargs.update({"optimize": True})
        output_image.save(output, format=output_format, **save_kwargs)
        return output.getvalue(), output_mime


def _decode_data_url(data_url: str, *, fallback_mime_type: str) -> tuple[str, bytes]:
    if "," not in data_url:
        raise ValueError("invalid image data URL")
    header, encoded = data_url.split(",", 1)
    header_l = header.lower()
    if not header_l.startswith(_DATA_IMAGE_PREFIX) or ";base64" not in header_l:
        raise ValueError("unsupported image data URL")
    mime_type = header[5:].split(";", 1)[0].lower().strip()
    if not mime_type.startswith("image/"):
        mime_type = fallback_mime_type if fallback_mime_type.startswith("image/") else "image/png"
    try:
        return mime_type, base64.b64decode(encoded, validate=True)
    except binascii.Error as exc:
        raise ValueError("invalid image base64") from exc


def _first_nonempty_string(item: Mapping[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _session_store_name(session_id: str | None) -> str:
    raw = str(session_id or "default").strip() or "default"
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._-")
    digest = hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:12]
    if safe:
        return f"{safe[:80]}-{digest}"
    return digest


def _extension_for_mime_type(mime_type: str) -> str:
    if mime_type == "image/jpeg":
        return ".jpg"
    if mime_type == "image/png":
        return ".png"
    if mime_type == "image/webp":
        return ".webp"
    ext = mimetypes.guess_extension(mime_type)
    return ext if ext else ".img"


def _mime_type_for_path(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    guessed_l = str(guessed or "").lower()
    return guessed_l if guessed_l.startswith("image/") else "image/png"


def _format_for_mime_type(mime_type: str) -> str:
    if mime_type == "image/jpeg":
        return "JPEG"
    if mime_type == "image/webp":
        return "WEBP"
    return "PNG"


def _needs_resize(width: int, height: int) -> bool:
    return width > MAX_PROMPT_IMAGE_DIMENSION or height > MAX_PROMPT_IMAGE_DIMENSION
