"""Session namespace normalization helpers.

The server stores run state under ``.session/<namespace>/``. UI clients may
send either that namespace (``ip/rtl-gen``) or a platform path copied from a
session artifact. Never use a client path directly; extract the namespace and
then resolve it under the local project ``.session`` root.
"""

from __future__ import annotations

import re

_SESSION_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_KNOWN_SESSION_FILES = {
    "conversation.json",
    "todo.json",
    "todo_error.json",
    "cost.json",
    "state.json",
}


def normalize_session_name(value: str) -> str:
    """Return a safe ``.session`` namespace, or ``""`` when invalid.

    Accepted inputs:
    - ``dma330/rtl-gen``
    - ``.session/dma330/rtl-gen``
    - ``C:\\repo\\common_ai_agent\\.session\\dma330\\rtl-gen``
    - ``C:\\repo\\common_ai_agent\\.session\\dma330\\rtl-gen\\conversation.json``

    The returned value is always slash-separated and relative to ``.session``.
    """

    raw = str(value or "").strip().strip("\"'")
    if not raw:
        return ""

    normalized = raw.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part and part != "."]
    if not parts:
        return ""

    lowered = [part.lower() for part in parts]
    if ".session" in lowered:
        index = len(lowered) - 1 - lowered[::-1].index(".session")
        parts = parts[index + 1:]

    if parts and parts[-1].lower() in _KNOWN_SESSION_FILES:
        parts = parts[:-1]

    if not parts:
        return ""

    safe_parts: list[str] = []
    for part in parts:
        if part == ".." or ":" in part or not _SESSION_SEGMENT_RE.match(part):
            return ""
        safe_parts.append(part)

    return "/".join(safe_parts)
