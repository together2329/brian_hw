from __future__ import annotations

from pathlib import Path
from typing import Final

from pydantic import JsonValue as PydanticJsonValue
from pydantic import TypeAdapter, ValidationError
from typing_extensions import TypeAlias


JsonValue: TypeAlias = PydanticJsonValue
JsonMap: TypeAlias = dict[str, JsonValue]
JsonList: TypeAlias = list[JsonValue]
JSON_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)


def load_json(path: Path, label: str) -> JsonMap:
    if not path.is_file():
        raise SystemExit(f"[{label}] FAIL: missing {path}")
    try:
        value = JSON_ADAPTER.validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise SystemExit(f"[{label}] FAIL: invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"[{label}] FAIL: {path} root must be an object")
    return value


def load_rows(path: Path, label: str) -> list[JsonMap]:
    if not path.is_file():
        raise SystemExit(f"[{label}] FAIL: missing {path}")
    rows: list[JsonMap] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = JSON_ADAPTER.validate_json(raw)
        except ValidationError as exc:
            raise SystemExit(f"[{label}] FAIL: {path}:{line_no}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise SystemExit(f"[{label}] FAIL: {path}:{line_no}: row must be an object")
        rows.append(value)
    return rows


def as_list(value: JsonValue) -> JsonList:
    return value if isinstance(value, list) else []


def as_map(value: JsonValue) -> JsonMap:
    return value if isinstance(value, dict) else {}


def strings(value: JsonValue) -> list[str]:
    return [item for item in as_list(value) if isinstance(item, str) and item.strip()]


def json_strings(values: list[str] | tuple[str, ...]) -> JsonList:
    return [value for value in values]


def text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""
