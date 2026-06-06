"""Rendered visual evidence collection for imported documents."""

from __future__ import annotations

import re
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List


_FIGURE_RE = re.compile(
    r"\b(?:Figure|FIGURE|Fig\.|FIG\.)\s+([0-9]+)\s*[\.:]?\s*([^\n\r]{0,120})"
)
_SKIP_PAGE_RE = re.compile(r"\b(?:table of contents|list of figures)\b", re.IGNORECASE)


@dataclass(frozen=True)
class VisualSurface:
    """A rendered, human-visible document surface ready for image analysis."""

    source_kind: str
    page_number: int
    image_path: Path
    title: str
    reason: str
    text_hint: str


def _compact_text(text: str, limit: int = 900) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "..."


def _figure_titles(text: str) -> List[str]:
    titles: List[str] = []
    for match in _FIGURE_RE.finditer(text or ""):
        number = match.group(1).strip()
        caption = " ".join((match.group(2) or "").split())
        title = f"Figure {number}"
        if caption:
            title += f". {caption}"
        if title not in titles:
            titles.append(title)
    return titles


def render_pdf_visual_surfaces(
    pdf_path: Path,
    output_dir: Path,
    stamp: int,
    upload_index: int,
    *,
    max_pages: int = 100,
    scale: float = 2.0,
    source_kind: str = "pdf_page",
    image_name_prefix: str = "pdf_page",
    include_all_pages: bool = False,
) -> List[VisualSurface]:
    """Render PDF pages that contain figure captions into visual surfaces."""

    if max_pages <= 0:
        return []
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        import fitz  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF visual evidence rendering") from exc

    surfaces: List[VisualSurface] = []
    with fitz.open(str(pdf_path)) as doc:
        for page_index in range(doc.page_count):
            page = doc[page_index]
            raw_text = page.get_text("text")
            text = raw_text if isinstance(raw_text, str) else str(raw_text or "")
            if not include_all_pages and _SKIP_PAGE_RE.search(text):
                continue
            titles = _figure_titles(text)
            if not include_all_pages and not titles:
                continue
            page_number = page_index + 1
            image_path = output_dir / f"{stamp}_{upload_index}_{image_name_prefix}_{page_number:03d}.png"
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            pix.save(str(image_path))
            title = "; ".join(titles[:3]) if titles else f"{source_kind.replace('_', ' ')} {page_number}"
            surfaces.append(
                VisualSurface(
                    source_kind=source_kind,
                    page_number=page_number,
                    image_path=image_path,
                    title=title,
                    reason="figure caption detected" if titles else "rendered document page",
                    text_hint=_compact_text(text),
                )
            )
            if len(surfaces) >= max_pages:
                break
    return surfaces


def _office_renderer_candidates() -> List[str]:
    candidates: List[str] = []
    configured = str(os.environ.get("ATLAS_OFFICE_RENDERER_BIN", "") or "").strip()
    if configured:
        candidates.append(configured)
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found and found not in candidates:
            candidates.append(found)
    mac_soffice = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if Path(mac_soffice).is_file() and mac_soffice not in candidates:
        candidates.append(mac_soffice)
    return candidates


def convert_office_document_to_pdf(
    document_path: Path,
    output_dir: Path,
    *,
    timeout_seconds: int = 180,
) -> Path:
    """Convert a DOCX/PPTX document to PDF using a real office layout engine."""

    output_dir.mkdir(parents=True, exist_ok=True)
    expected = output_dir / f"{document_path.stem}.pdf"
    last_error = ""
    for executable in _office_renderer_candidates():
        try:
            result = subprocess.run(
                [
                    executable,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(output_dir),
                    str(document_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            last_error = f"{executable} timed out after {timeout_seconds}s"
            continue
        except OSError as exc:
            last_error = f"{executable} failed to start: {exc}"
            continue
        if result.returncode == 0 and expected.is_file():
            return expected
        detail = (result.stderr or result.stdout or "").strip()
        last_error = f"{executable} failed rc={result.returncode}: {detail[:300]}"
    if not _office_renderer_candidates():
        raise RuntimeError("LibreOffice/soffice is required for DOCX/PPTX visual evidence rendering")
    raise RuntimeError(last_error or "office document PDF conversion failed")


def render_office_visual_surfaces(
    document_path: Path,
    output_dir: Path,
    stamp: int,
    upload_index: int,
    *,
    max_pages: int = 100,
    scale: float = 2.0,
) -> List[VisualSurface]:
    """Render DOCX/PPTX pages or slides through PDF-normalized visual surfaces."""

    suffix = document_path.suffix.lower()
    source_kind = "pptx_slide" if suffix == ".pptx" else "docx_page"
    image_name_prefix = "pptx_slide" if suffix == ".pptx" else "docx_page"
    pdf_path = convert_office_document_to_pdf(document_path, output_dir / "_office_pdf")
    return render_pdf_visual_surfaces(
        pdf_path,
        output_dir,
        stamp,
        upload_index,
        max_pages=max_pages,
        scale=scale,
        source_kind=source_kind,
        image_name_prefix=image_name_prefix,
        include_all_pages=True,
    )


def visual_evidence_prompt(surface: VisualSurface) -> str:
    """Build the image prompt for a rendered document surface."""

    return (
        "Read this rendered document page for SSOT import evidence. "
        "Focus on technical figures, diagrams, timing/order examples, interfaces, "
        "signals, registers, architecture blocks, and data-flow implications. "
        "Ignore repeated headers, footers, watermarks, page numbers, and logos.\n\n"
        f"Surface: {surface.source_kind} page {surface.page_number}\n"
        f"Title/caption hint: {surface.title}\n"
        f"Text hint: {surface.text_hint}\n\n"
        "Return concise engineering notes. State whether this page contains useful SSOT evidence."
    )
