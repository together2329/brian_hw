"""Prompt input helpers for text plus image attachments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_ALLOWED_IMAGE_DETAILS = {"auto", "low", "high"}


@dataclass(frozen=True)
class PromptImage:
    """Image attachment normalized for Responses API input blocks."""

    image_url: str
    detail: str = "auto"


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
        raw_url = item.get("image_url") or item.get("imageUrl") or item.get("url")
        image_url = str(raw_url or "").strip()
        if not image_url.startswith(("data:image/", "https://", "http://")):
            continue
        raw_detail = str(item.get("detail") or "auto").strip().lower()
        detail = raw_detail if raw_detail in _ALLOWED_IMAGE_DETAILS else "auto"
        images.append(PromptImage(image_url=image_url, detail=detail))
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
        blocks.append({
            "type": "input_image",
            "image_url": image.image_url,
            "detail": image.detail,
        })
    return blocks
