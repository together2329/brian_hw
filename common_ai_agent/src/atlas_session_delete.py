from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi.requests import Request
from fastapi.responses import JSONResponse

_TRUE_QUERY_VALUES = frozenset({"1", "true", "yes", "on"})


def force_delete_requested(request: Request) -> bool:
    return str(request.query_params.get("force") or "").strip().lower() in _TRUE_QUERY_VALUES


def session_delete_response(result: Mapping[str, Any]) -> JSONResponse:
    runtime = result.get("runtime")
    if bool(result.get("deleted")):
        return JSONResponse(dict(result), status_code=200)
    # Not deleted: the control session was deliberately preserved so the runtime
    # file/manifest is not orphaned. 409 when a ?force=1 retry can succeed
    # (pending runtime queue); 500 when a runtime cleanup error blocked the delete.
    force_required = isinstance(runtime, Mapping) and runtime.get("force_required") is True
    return JSONResponse(dict(result), status_code=409 if force_required else 500)
