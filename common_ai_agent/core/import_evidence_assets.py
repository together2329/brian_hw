"""Asset path extraction for imported Markdown evidence."""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Final


_MARKDOWN_IMAGE_RE: Final = re.compile(r"!\[[^\]]*]\(\s*<?([^)\s>]+)>?(?:\s+['\"][^)]*['\"])?\s*\)")
_CODE_ASSET_RE: Final = re.compile(r"`([^`]*(?:/req/imports/(?:images|visual)/|/imports/(?:images|visual)/)[^`]*)`")


@dataclass(frozen=True)
class ImportEvidenceAssets:
    """Imported evidence asset paths grouped by how the importer uses them."""

    image_paths: tuple[str, ...]
    visual_paths: tuple[str, ...]


def _normalize_import_asset_ref(raw_ref: str, artifact_rel_path: str) -> str | None:
    raw = str(raw_ref or "").strip().strip("\"'")
    if not raw or raw.startswith("#") or raw.lower().startswith("data:") or "://" in raw:
        return None
    raw = raw.split("#", 1)[0].split("?", 1)[0].strip()
    if not raw:
        return None
    if raw.startswith("/"):
        candidate = raw.lstrip("/")
    elif "/req/imports/" in raw:
        candidate = raw
    else:
        base = PurePosixPath(str(artifact_rel_path or "")).parent
        candidate = (base / raw).as_posix()
    normalized = posixpath.normpath(candidate).lstrip("./")
    if normalized == ".":
        return None
    if "/req/imports/images/" in normalized or "/req/imports/visual/" in normalized:
        return normalized
    return None


def extract_markdown_import_assets(markdown_text: str, artifact_rel_path: str) -> ImportEvidenceAssets:
    """Find importer-managed image and rendered-page assets linked from Markdown."""

    images: list[str] = []
    visuals: list[str] = []
    seen_images: set[str] = set()
    seen_visuals: set[str] = set()

    refs = [match.group(1) for match in _MARKDOWN_IMAGE_RE.finditer(str(markdown_text or ""))]
    refs.extend(match.group(1) for match in _CODE_ASSET_RE.finditer(str(markdown_text or "")))
    for ref in refs:
        path = _normalize_import_asset_ref(ref, artifact_rel_path)
        if not path:
            continue
        if "/req/imports/visual/" in path:
            if path not in seen_visuals:
                seen_visuals.add(path)
                visuals.append(path)
        elif path not in seen_images:
            seen_images.add(path)
            images.append(path)

    return ImportEvidenceAssets(image_paths=tuple(images), visual_paths=tuple(visuals))
