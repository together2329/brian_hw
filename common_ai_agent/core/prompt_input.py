"""Prompt input helpers for text plus image attachments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.prompt_image_store import (
    load_prompt_image_path_as_data_url,
    normalize_prompt_image_detail,
)


@dataclass(frozen=True)
class PromptImage:
    """Image attachment normalized for Responses API input blocks."""

    image_url: str | None = None
    detail: str = "auto"
    path: str | None = None
    mime_type: str | None = None
    name: str | None = None


class PromptInput(str):
    """String prompt carrying normalized image attachments."""

    __slots__ = ("images",)

    images: tuple[PromptImage, ...]

    def __new__(cls, text: str, images: tuple[PromptImage, ...]) -> "PromptInput":
        value = str.__new__(cls, text)
        value.images = images
        return value


def normalize_prompt_images(value: Any) -> tuple[PromptImage, ...]:
    """Parse a prompt payload's image list into Responses-compatible images."""

    if not isinstance(value, list):
        return ()
    images: list[PromptImage] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        raw_detail = normalize_prompt_image_detail(item.get("detail"))
        raw_path = (
            item.get("path")
            or item.get("image_path")
            or item.get("imagePath")
            or item.get("local_path")
            or item.get("localPath")
            or item.get("file_path")
            or item.get("filePath")
        )
        path = str(raw_path or "").strip()
        if path:
            raw_mime_type = item.get("mime_type") or item.get("mimeType") or item.get("type")
            raw_name = item.get("name") or item.get("filename") or item.get("fileName")
            images.append(PromptImage(
                detail=raw_detail,
                path=path,
                mime_type=str(raw_mime_type or "").strip() or None,
                name=str(raw_name or "").strip() or None,
            ))
            continue
        raw_url = item.get("image_url") or item.get("imageUrl") or item.get("url")
        image_url = str(raw_url or "").strip()
        if not image_url.startswith(("data:image/", "https://", "http://")):
            continue
        raw_name = item.get("name") or item.get("filename") or item.get("fileName")
        images.append(PromptImage(
            image_url=image_url,
            detail=raw_detail,
            name=str(raw_name or "").strip() or None,
        ))
    return tuple(images)


def prompt_input_from_payload(text: str, payload: Any) -> str:
    """Return a text prompt, preserving image attachments when present."""

    images: tuple[PromptImage, ...] = ()
    if isinstance(payload, Mapping):
        images = normalize_prompt_images(payload.get("images"))
    if not images:
        return text
    return PromptInput(text, images)


def prompt_has_content(prompt: str) -> bool:
    """Return True when prompt text or attached images carry user input."""

    if str(prompt).strip():
        return True
    return isinstance(prompt, PromptInput) and bool(prompt.images)


def prompt_content_for_llm(prompt: str) -> str | list[dict[str, str]]:
    """Convert prompt text plus images into LLM message content."""

    images = prompt.images if isinstance(prompt, PromptInput) else ()
    if not images:
        return str(prompt)
    blocks: list[dict[str, str]] = []
    text = str(prompt)
    if text.strip():
        blocks.append({"type": "text", "text": text})
    for image in images:
        image_url = image.image_url
        if not image_url and image.path:
            try:
                image_url = load_prompt_image_path_as_data_url(
                    image.path,
                    detail=image.detail,
                )
            except Exception as exc:
                blocks.append({
                    "type": "text",
                    "text": f"Atlas could not read prompt image at {image.path}: {exc}",
                })
                continue
        if not image_url:
            continue
        blocks.append({
            "type": "input_image",
            "image_url": image_url,
            "detail": image.detail,
        })
    return blocks


def message_content_text(content: Any) -> str:
    """Return the textual part of a chat message content value."""

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, Mapping):
                text = block.get("text")
                if text is not None:
                    parts.append(str(text))
            elif block is not None:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    if content is None:
        return ""
    return str(content)
