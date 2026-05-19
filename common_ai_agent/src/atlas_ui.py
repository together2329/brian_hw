"""
src/atlas_ui.py — Atlas frontend server for common_ai_agent

Serves the static frontend bundle at common_ai_agent/frontend/atlas/ and
bridges it to the existing main.py agent loop via:

  • GET  /                       → frontend/atlas/index.html
  • GET  /<asset>                → frontend/atlas/<asset>     (jsx, css, js)
  • WS   /ws/agent               → bidirectional event stream

Activation:
    UI_MODE=atlas  python src/textual_main.py         (Windows)
    UI_MODE=atlas  python3 src/textual_main.py        (macOS/Linux)
    or directly:   python -m src.atlas_ui --port 8765 (Windows)

This mirrors web_ui.py (SSE) but uses WebSockets so the frontend can both
push prompts AND receive token / stage / tool / cost / todo events.

Author: Atlas frontend
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import contextvars
import faulthandler
import hashlib
import html as html_lib
import json
import os
import queue
import re
import signal
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional, TYPE_CHECKING


def _configure_utf8_process_io() -> None:
    """Keep Atlas server/worker console I/O from crashing on Windows code pages."""

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8:replace")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


_configure_utf8_process_io()


def _install_stack_dump_signal() -> None:
    """Allow `kill -USR1 <pid>` to dump stuck Atlas server stacks."""

    sigusr1 = getattr(signal, "SIGUSR1", None)
    if sigusr1 is None:
        return
    try:
        faulthandler.register(sigusr1, all_threads=True)
    except Exception:
        pass


_install_stack_dump_signal()


# Self-bootstrap PYTHONPATH so `python3 src/atlas_ui.py` works without
# the caller exporting PYTHONPATH=.:src first. atlas_ui imports modules
# from BOTH this directory (other src/*.py siblings) AND the repo root
# (core/, lib/, workflow/loader). Adding both up front lets the binary
# be launched from any cwd.
_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent
for _p in (str(_THIS_DIR), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# `from __future__ import annotations` turns every type annotation into
# a string. FastAPI's `get_type_hints()` then needs to resolve those
# strings in the *module globals*. The inner endpoint functions live
# inside create_app() (they import fastapi locally), so without a
# module-level alias of `Request`, the annotation `request: Request`
# becomes an unresolvable ForwardRef and pydantic v2 falls back to
# treating `request` as a query parameter (→ 422 on every POST).
# This conditional import keeps the script usable even when fastapi is
# missing — `Request` just becomes None and the endpoint won't be
# registered (the local import inside create_app sys.exits first).
if TYPE_CHECKING:
    from fastapi import Request
else:
    try:
        from fastapi import Request  # noqa: F401  (runtime forward-ref target)
    except ImportError:
        class Request:  # fallback name for annotations when FastAPI is absent
            pass

# ── Paths ──────────────────────────────────────────────────────────
HERE         = Path(__file__).resolve().parent
SOURCE_ROOT  = HERE.parent                            # common_ai_agent/ (source)
FRONTEND     = SOURCE_ROOT / "frontend" / "atlas"
# PROJECT_ROOT is the user's cwd at launch, NOT the source repo. This
# lets the user run `python ../path/to/textual_main.py` from any
# project directory and have the file API + scope operate on THAT dir.
PROJECT_ROOT = Path(os.getcwd()).resolve()
# Backwards compat alias — older code references ROOT.
ROOT         = SOURCE_ROOT

_REASONING_EFFORT_OPTIONS = ("none", "low", "medium", "high", "xhigh")
_REASONING_EFFORT_ALIASES = {
    "none": "none",
    "low": "low",
    "l": "low",
    "med": "medium",
    "mid": "medium",
    "medium": "medium",
    "m": "medium",
    "high": "high",
    "h": "high",
    "hi": "high",
    "xhigh": "xhigh",
    "x": "xhigh",
    "xh": "xhigh",
    "xhi": "xhigh",
    "max": "xhigh",
}
_MODEL_OPTION_KEYS = ("LLM_MODEL_NAME", "LLM_MODEL_NAME_2", "LLM_MODEL_NAME_3")
_BASE_MODEL_OPTION_KEYS = ("LLM_BASE_NAME", "LLM_BASE_NAME_2", "LLM_BASE_NAME_3")
_LEGACY_MODEL_OPTION_KEYS = ("LLM_BASE_MODEL", "LLM_BASE_MODEL_2", "LLM_BASE_MODEL_3")
_RUNTIME_MODEL_OPTION_KEY = "__runtime_model__"

_atlas_active_session_cv = contextvars.ContextVar("atlas_active_session", default="")
_atlas_active_ip_cv = contextvars.ContextVar("atlas_active_ip", default="")
_atlas_ui_lang_cv = contextvars.ContextVar("atlas_ui_lang", default="")
_agent_mode_override_cv = contextvars.ContextVar("agent_mode_override", default="")
_plan_mode_cv = contextvars.ContextVar("plan_mode", default="false")


def _active_session_value() -> str:
    current = (_atlas_active_session_cv.get() or "").strip()
    env_value = (os.environ.get("ATLAS_ACTIVE_SESSION", "") or "").strip()
    # FastAPI request tasks can inherit the startup contextvar value
    # ("default/default/default"). /api/session/activate mirrors the real
    # active namespace into os.environ for cross-task visibility, so do not
    # let that placeholder shadow a newer backend activation.
    if current and (current not in {"default", "default/default", "default/default/default"} or not env_value):
        return current
    return env_value or current


def _atlas_todo_item_from_raw(item: dict[str, Any]) -> dict[str, Any]:
    todo = dict(item)
    content = todo.get("content") or todo.get("title") or todo.get("id") or ""
    todo["content"] = str(content)
    todo["activeForm"] = str(todo.get("activeForm") or todo.get("active_form") or content)
    todo["status"] = str(todo.get("status") or "pending")
    todo["priority"] = str(todo.get("priority") or "medium")
    todo["detail"] = str(todo.get("detail") or "")
    todo["criteria"] = str(todo.get("criteria") or "")
    return todo


def _atlas_todo_payload_from_raw(raw: Any, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(fallback or {})
    raw_items: Any = None
    if isinstance(raw, dict):
        for key in (
            "name",
            "description",
            "lock_additions",
            "source_plan",
            "source_task_count",
            "status_counts",
            "ui_grouping",
            "current_index",
        ):
            if key in raw:
                payload[key] = raw[key]
        raw_items = raw.get("todos")
        if not isinstance(raw_items, list):
            raw_items = raw.get("tasks")
    elif isinstance(raw, list):
        raw_items = raw
    if isinstance(raw_items, list):
        payload["todos"] = [
            _atlas_todo_item_from_raw(item)
            for item in raw_items
            if isinstance(item, dict)
        ]
    else:
        payload.setdefault("todos", [])
    return payload


def _normalize_reasoning_effort(raw: Any) -> str:
    effort = _REASONING_EFFORT_ALIASES.get(str(raw or "").strip().lower(), "")
    if not effort:
        raise ValueError(f"unknown reasoning effort: {raw!r}")
    return effort


def _persist_config_values(updates: dict[str, str]) -> None:
    """Persist simple KEY=value settings to common_ai_agent/.config."""
    _persist_key_values(SOURCE_ROOT / ".config", updates)


def _persist_env_values(updates: dict[str, str]) -> None:
    """Persist user-editable runtime settings to common_ai_agent/.env."""
    _persist_key_values(SOURCE_ROOT / ".env", updates)


def _persist_key_values(path: Path, updates: dict[str, str]) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        lines = []

    seen = set()
    key_re = "|".join(re.escape(k) for k in updates)
    out = []
    for line in lines:
        match = re.match(rf"^(\s*)({key_re})(\s*)=.*$", line)
        if match:
            key = match.group(2)
            out.append(f"{match.group(1)}{key}{match.group(3)}={updates[key]}")
            seen.add(key)
        else:
            out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


def _read_env_file_values() -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = (SOURCE_ROOT / ".env").read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        if key:
            values[key] = value
    return values


def _canonical_model_option_key(key: str) -> str:
    raw = str(key or "").strip()
    for group in (_MODEL_OPTION_KEYS, _BASE_MODEL_OPTION_KEYS, _LEGACY_MODEL_OPTION_KEYS):
        if raw in group:
            return raw
    return raw


def _model_option_index(key: str) -> int | None:
    raw = _canonical_model_option_key(key)
    for group in (_MODEL_OPTION_KEYS, _BASE_MODEL_OPTION_KEYS, _LEGACY_MODEL_OPTION_KEYS):
        if raw in group:
            return group.index(raw)
    return None


def _display_model_option_keys(env_file: dict[str, str]) -> tuple[str, str, str]:
    selected_key = (
        env_file.get("LLM_SELECTED_MODEL_KEY", "")
        or os.environ.get("LLM_SELECTED_MODEL_KEY", "")
    ).strip()
    if selected_key in _BASE_MODEL_OPTION_KEYS:
        return _BASE_MODEL_OPTION_KEYS
    if selected_key in _LEGACY_MODEL_OPTION_KEYS:
        return _LEGACY_MODEL_OPTION_KEYS
    if any((env_file.get(key, os.environ.get(key, "")) or "").strip() for key in _BASE_MODEL_OPTION_KEYS):
        return _BASE_MODEL_OPTION_KEYS
    if any((env_file.get(key, os.environ.get(key, "")) or "").strip() for key in _LEGACY_MODEL_OPTION_KEYS):
        return _LEGACY_MODEL_OPTION_KEYS
    return _MODEL_OPTION_KEYS


def _model_option_value(env_file: dict[str, str], index: int) -> str:
    """Return dropdown slot value, preferring LLM_MODEL_NAME* over old names."""
    for group in (_MODEL_OPTION_KEYS, _BASE_MODEL_OPTION_KEYS, _LEGACY_MODEL_OPTION_KEYS):
        key = group[index]
        value = (env_file.get(key, os.environ.get(key, "")) or "").strip()
        if value:
            return value
    return ""


def _refresh_config_after_persist() -> None:
    """Refresh config mtime cache so the next /healthz does not undo runtime settings."""
    for mod_name in ("src.config", "config"):
        mod = sys.modules.get(mod_name)
        if mod is None:
            try:
                mod = __import__(mod_name, fromlist=["*"])
            except Exception:
                mod = None
        if mod is not None:
            try:
                mod.reload_env()
            except Exception:
                pass


def _persist_reasoning_effort(effort: str) -> None:
    glm_thinking = "disabled" if effort == "none" else "enabled"
    _persist_config_values({
        "REASONING_MODE": effort,
        "REASONING_EFFORT": effort,
        "GLM_THINKING_TYPE": glm_thinking,
    })


def _set_runtime_reasoning_effort(effort: str) -> None:
    glm_thinking = "disabled" if effort == "none" else "enabled"
    os.environ["REASONING_MODE"] = effort
    os.environ["REASONING_EFFORT"] = effort
    os.environ["GLM_THINKING_TYPE"] = glm_thinking
    config_modules = []
    seen_module_ids = set()
    for mod_name in ("src.config", "config"):
        mod = sys.modules.get(mod_name)
        if mod is not None and id(mod) not in seen_module_ids:
            config_modules.append(mod)
            seen_module_ids.add(id(mod))
    if not config_modules:
        try:
            mod = __import__("src.config", fromlist=["*"])
            config_modules.append(mod)
            sys.modules.setdefault("config", mod)
        except Exception:
            try:
                mod = __import__("config", fromlist=["*"])
                config_modules.append(mod)
                sys.modules.setdefault("src.config", mod)
            except Exception:
                pass
    for mod in config_modules:
        if mod is not None:
            setattr(mod, "REASONING_MODE", effort)
            setattr(mod, "REASONING_EFFORT", effort)
            setattr(mod, "GLM_THINKING_TYPE", glm_thinking)


def _model_option_rows(active_model: str = "") -> list[dict[str, str]]:
    env_file = _read_env_file_values()
    display_keys = _display_model_option_keys(env_file)

    rows: list[dict[str, str]] = []
    seen_models: set[str] = set()
    for index, key in enumerate(display_keys):
        model = _model_option_value(env_file, index)
        if not model or model in seen_models or model.lower().startswith("default"):
            continue
        seen_models.add(model)
        rows.append({"key": key, "model": model})
    selected = ""
    selected_key = (
        env_file.get("LLM_SELECTED_MODEL_KEY", "")
        or os.environ.get("LLM_SELECTED_MODEL_KEY", "")
    ).strip()
    selected_key = _canonical_model_option_key(selected_key)
    if selected_key:
        selected_row = next((row for row in rows if row["key"] == selected_key), None)
        if selected_row and (not active_model or selected_row["model"] == active_model):
            selected = selected_key
    for row in rows:
        if not selected and active_model and row["model"] == active_model:
            selected = row["key"]
            break
    if active_model and not selected and not active_model.lower().startswith("default"):
        rows.insert(0, {
            "key": _RUNTIME_MODEL_OPTION_KEY,
            "model": active_model,
            "runtime": "true",
        })
        selected = _RUNTIME_MODEL_OPTION_KEY
    if not selected and rows:
        selected = rows[0]["key"]
    for row in rows:
        row["selected"] = "true" if row["key"] == selected else "false"
    return rows


def _set_runtime_model(model: str, selected_key: str = "") -> None:
    activated_runtime = False
    os.environ["LLM_RUNTIME_MODEL_OVERRIDE"] = "1"
    os.environ["LLM_ACTIVE_MODEL_NAME"] = model
    os.environ["LLM_ACTIVE_BASE_NAME"] = model
    os.environ["LLM_ACTIVE_BASE_MODEL"] = model
    if selected_key:
        os.environ["LLM_SELECTED_MODEL_KEY"] = _canonical_model_option_key(selected_key)
    config_modules = []
    seen_module_ids = set()
    for mod_name in ("src.config", "config"):
        mod = sys.modules.get(mod_name)
        if mod is not None and id(mod) not in seen_module_ids:
            config_modules.append(mod)
            seen_module_ids.add(id(mod))
    if not config_modules:
        try:
            mod = __import__("src.config", fromlist=["*"])
            config_modules.append(mod)
            sys.modules.setdefault("config", mod)
        except Exception:
            try:
                mod = __import__("config", fromlist=["*"])
                config_modules.append(mod)
                sys.modules.setdefault("src.config", mod)
            except Exception:
                pass
    for mod in config_modules:
        if mod is None:
            continue
        applied = False
        try:
            if callable(getattr(mod, "set_active_profile", None)) and mod.set_active_profile(model):
                applied = True
            elif callable(getattr(mod, "_profile_name_for_model", None)):
                profile_name = mod._profile_name_for_model(model)
                if profile_name and callable(getattr(mod, "set_active_profile", None)):
                    applied = bool(mod.set_active_profile(profile_name))
            if not applied and callable(getattr(mod, "activate_cli_backend", None)) and mod.activate_cli_backend(model):
                applied = True
            if (
                not applied
                and callable(getattr(mod, "is_opencode_model", None))
                and mod.is_opencode_model(model)
                and callable(getattr(mod, "activate_opencode_oauth", None))
            ):
                applied = bool(mod.activate_opencode_oauth(model.split("/", 1)[-1]))
            if not applied and callable(getattr(mod, "deactivate_cli_backends", None)):
                mod.deactivate_cli_backends()
        except Exception:
            pass
        if applied:
            activated_runtime = True
            active_model = str(getattr(mod, "MODEL_NAME", "") or model)
            os.environ["LLM_MODEL_NAME"] = active_model
            os.environ["MODEL_NAME"] = active_model
        else:
            setattr(mod, "MODEL_NAME", model)
    if not activated_runtime:
        os.environ["LLM_MODEL_NAME"] = model
        os.environ["MODEL_NAME"] = model


def _apply_selected_model_from_env() -> str:
    selected_key = _canonical_model_option_key(os.environ.get("LLM_SELECTED_MODEL_KEY", ""))
    selected_index = _model_option_index(selected_key)
    if selected_index is not None:
        model = _model_option_value({}, selected_index)
        if model:
            _set_runtime_model(model, selected_key)
            return model
    return ""


def _active_ip_value() -> str:
    current = (_atlas_active_ip_cv.get() or "").strip()
    env_value = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if current and (current != "default" or not env_value):
        return current
    return env_value or current


def _ui_lang_value() -> str:
    return _atlas_ui_lang_cv.get() or os.environ.get("ATLAS_UI_LANG", "")


def _plan_mode_value() -> str:
    return _plan_mode_cv.get() or os.environ.get("PLAN_MODE", "false")


def _sync_env_to_context() -> None:
    """Copy contextvars back to os.environ for legacy main.py reads."""
    session_value = (_atlas_active_session_cv.get() or "").strip()
    session_env = (os.environ.get("ATLAS_ACTIVE_SESSION", "") or "").strip()
    if session_value and (
        session_value not in {"default", "default/default", "default/default/default"}
        or not session_env
    ):
        os.environ["ATLAS_ACTIVE_SESSION"] = session_value
    elif not session_env:
        os.environ["ATLAS_ACTIVE_SESSION"] = session_value

    ip_value = (_atlas_active_ip_cv.get() or "").strip()
    ip_env = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if ip_value and (ip_value != "default" or not ip_env):
        os.environ["ATLAS_ACTIVE_IP"] = ip_value
    elif not ip_env:
        os.environ["ATLAS_ACTIVE_IP"] = ip_value

    os.environ["ATLAS_UI_LANG"] = _atlas_ui_lang_cv.get()
    os.environ["AGENT_MODE_OVERRIDE"] = _agent_mode_override_cv.get()
    os.environ["PLAN_MODE"] = _plan_mode_cv.get()


def _python_cmd() -> str:
    """Return the Python launcher for generated user-facing commands."""
    return "python" if os.name == "nt" else "python3"


try:
    from .workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress
except Exception:
    try:
        from workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress  # type: ignore
    except Exception:
        _shared_rtl_manifest_progress = None  # type: ignore

try:
    from core.session_names import normalize_session_name
except Exception:
    from session_names import normalize_session_name  # type: ignore


# ── ask_user answer formatter ──────────────────────────────────────
def _format_answer(ans: dict[str, Any], options: list[dict[str, Any]]) -> str:
    """Render a UI answer payload back into a tool observation string."""
    selected_ids = ans.get("selected") or []
    custom = (ans.get("custom") or "").strip()
    label_by_id = {o.get("id"): o.get("label", o.get("id")) for o in options or []}
    selected_labels = [label_by_id.get(sid, sid) for sid in selected_ids]
    parts = []
    if selected_labels:
        parts.append("selected: " + ", ".join(selected_labels))
    if custom:
        parts.append("note: " + custom)
    if not parts:
        return "(user submitted with no selection)"
    return " · ".join(parts)


# ── App factory ────────────────────────────────────────────────────
def create_app():
    try:
        from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
        from fastapi.staticfiles import StaticFiles
        from starlette.routing import WebSocketRoute
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn websockets")
        sys.exit(1)
    from core.atlas_db import AtlasDB
    from core.atlas_multiuser import _MultiUserBridge, set_atlas_bridge_session_id

    if not FRONTEND.exists():
        print(f"ERROR: frontend bundle not found at {FRONTEND}")
        sys.exit(1)

    # Load common_ai_agent/.config even when atlas_ui.py is launched directly
    # instead of through textual_main.py. Shell-set env still wins because
    # src.config only fills missing keys at first load.
    try:
        try:
            from . import config as _atlas_boot_config  # noqa: F401
        except Exception:
            import config as _atlas_boot_config  # type: ignore  # noqa: F401
    except Exception:
        pass

    app = FastAPI(title="ATLAS · common_ai_agent")
    _multi_raw = os.environ.get("ATLAS_MULTI_USER", "1").strip().lower()
    _multi_user_env = _multi_raw not in ("0", "false", "no", "off")
    # Multi-user and process-per-session isolation default on so agent output,
    # command results, and main.py global state do not bleed across users.
    # Operators can still opt out explicitly with ATLAS_MULTI_USER=0 or
    # ATLAS_MULTI_USER_PROC=0.
    _proc_raw = os.environ.get("ATLAS_MULTI_USER_PROC", "1").strip().lower()
    _use_proc = _multi_user_env and _proc_raw not in ("0", "false", "no", "off")
    _strict_raw = os.environ.get("ATLAS_STRICT_SESSION_ROUTING", "0").strip().lower()
    _strict_routing = _strict_raw in ("1", "true", "yes", "on")
    if _multi_user_env:
        print(f"[atlas] Multi-user enabled (process_per_session={'on' if _use_proc else 'off'})")
    # single_user collapses every WS-bound session_id onto "default" so
    # the agent thread's inbox and the WS handler's inbox are the same.
    bridge = _MultiUserBridge(
        single_user=not _multi_user_env,
        use_processes=_use_proc,
        strict_session_routing=_strict_routing,
    )
    # Register the bridge so the ReAct loop's orchestrator chat
    # injector (built lazily inside main.py / agent_server.py before
    # this point) can resolve sessions for the chat watermark.
    try:
        from core.orchestrator_inject import register_bridge as _orch_register_bridge
        _orch_register_bridge(bridge)
    except Exception:
        pass
    # Opt-in auto-start of the chat-responder bots. With
    # CHAT_RESPONDER_AUTOSTART=1 in .env, atlas_ui spawns one daemon
    # thread per IP room plus one for _global, so launching the UI is
    # enough to make the bot respond to teammate feedback. Threads die
    # with the parent. Without the env var, users still launch
    # responders manually via `python3 -m core.chat_responder <room>`.
    if os.environ.get("CHAT_RESPONDER_AUTOSTART", "").strip() in ("1", "true", "yes", "on"):
        try:
            from core.chat_responder import autostart_all as _chat_autostart
            _chat_autostart()
        except Exception as _e:
            print(f"[chat-responder] autostart failed: {_e}")
    clients: set[Any] = set()
    broadcaster_task: asyncio.Task | None = None

    def _session_emit_target(client_session: Any | None) -> str | None:
        return getattr(client_session, "session_id", None) if client_session is not None else None

    def _queue_prompt_for_session(client_session: Any | None, text: str) -> None:
        if client_session is not None:
            bridge.queue_prompt_for_session(client_session.session_id, text)
            return
        bridge.queue_prompt(text)

    def _input_history_path() -> Path:
        try:
            try:
                from . import config as _config
            except Exception:
                import config as _config  # type: ignore
            base = str(getattr(_config, "SESSION_DIR", "") or "").strip()
        except Exception:
            base = ""
        return Path(base) / "input_history.txt" if base else PROJECT_ROOT / ".session" / "input_history.txt"

    def _read_input_history(limit: int = 200) -> list[str]:
        path = _input_history_path()
        if not path.is_file():
            return []
        entries: list[str] = []
        cur: list[str] = []
        try:
            for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if raw.startswith("+"):
                    cur.append(raw[1:])
                elif raw.startswith("#"):
                    if cur:
                        entries.append("\n".join(cur))
                        cur = []
            if cur:
                entries.append("\n".join(cur))
        except OSError:
            return []
        return [e for e in entries if e.strip()][-max(1, min(int(limit or 200), 1000)):]

    def _append_input_history(text: str) -> None:
        body = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not body:
            return
        path = _input_history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n# {time.ctime()}\n")
            for line in body.split("\n"):
                fh.write("+" + line + "\n")

    async def _send_one(client, raw: str, timeout: float):
        # raw is the already-serialized JSON text — broadcasters
        # serialize ONCE up front and pass the same string to every
        # client instead of re-serializing per WS. send_text avoids
        # FastAPI re-encoding the message a second time too. Scale
        # timeout with message size; tiny frames floor at 4 s.
        try:
            await asyncio.wait_for(client.send_text(raw), timeout=timeout)
            return None
        except Exception:
            return client

    def _is_websocket_disconnect(exc: BaseException) -> bool:
        """Return True only for normal client-side websocket disconnects."""
        seen: set[int] = set()
        cur: BaseException | None = exc
        while cur is not None and id(cur) not in seen:
            seen.add(id(cur))
            if isinstance(cur, WebSocketDisconnect):
                return True
            cls_name = cur.__class__.__name__
            if cls_name in {
                "ClientDisconnected",
                "ConnectionClosed",
                "ConnectionClosedError",
                "ConnectionClosedOK",
            }:
                return True
            if cls_name == "RuntimeError":
                msg = str(cur).lower()
                if "disconnect" in msg or "websocket is not connected" in msg:
                    return True
            if cls_name == "AttributeError" and "transfer_data_task" in str(cur):
                return True
            cur = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)
        return False

    async def _close_websocket_quietly(client, *, code: int, reason: str) -> None:
        try:
            await client.close(code=code, reason=reason)
        except Exception as exc:
            if not _is_websocket_disconnect(exc):
                raise

    async def _broadcast_outbox():
        """Single consumer for bridge events, broadcast to every live WS.

        Each websocket used to start its own consumer on the same queue. With
        a browser tab plus an automation client, events were load-balanced
        between clients instead of broadcast, so ask_user cards and slash
        output could disappear from one surface.

        The whole loop body is wrapped in try/except so a transient lookup
        miss (e.g. ``get_session`` raising KeyError for a session that was
        deleted between event emit and broadcast) never kills the task —
        a dead broadcaster silently strands every connected WS client and
        looks to the frontend like "Backend disconnected" even though the
        agent process is still alive.
        """
        while True:
            try:
                msg, session_id = await bridge.next_event()
                if msg is None:
                    continue
                # _ensure_session is non-raising; get_session raises KeyError
                # for unknown ids which would propagate up and kill the task.
                try:
                    session = bridge.get_session(session_id)
                except Exception:
                    session = bridge._ensure_session(session_id)
                snapshot = list(session.clients)
                if not snapshot:
                    continue
                # Serialize once for the whole fan-out and skip the
                # second encode-to-bytes the timeout sizing used to do
                # for every frame — len(raw) is the same order of
                # magnitude as the UTF-8 byte length for ASCII-heavy
                # JSON, and the 4-second floor swallows the rounding
                # error.
                raw = json.dumps(msg, ensure_ascii=False)
                size_kb = max(len(raw) / 1024, 1)
                timeout = max(4.0, size_kb * 0.25)
                results = await asyncio.gather(
                    *(_send_one(c, raw, timeout) for c in snapshot),
                    return_exceptions=True,
                )
                for stale_client in results:
                    if stale_client is None or isinstance(stale_client, BaseException):
                        continue
                    session.clients.discard(stale_client)
            except asyncio.CancelledError:
                raise
            except Exception as _bcast_err:
                # Never let the broadcaster die. A killed broadcaster
                # produces the exact "WS open but no events flowing" symptom
                # users see as "Backend disconnected" with the chat empty.
                import sys as _sys
                print(f"[broadcaster] swallowed: {_bcast_err!r}", file=_sys.stderr)
                continue

    def _ensure_broadcaster() -> None:
        nonlocal broadcaster_task
        if broadcaster_task is None or broadcaster_task.done():
            broadcaster_task = asyncio.create_task(_broadcast_outbox())

    # ── inlined-HTML cache ────────────────────────────────────────
    # The browser fetches /  on every reload — the 14 .jsx files we
    # inline are large (~1.1 MB total) and each read_text() is sync,
    # so doing it from inside `async def index()` blocks the event
    # loop and starves every other request (api, static assets, ws).
    # Cache the assembled HTML and rebuild only when any inlined
    # source file's mtime changes.
    _INLINE_INDEX_RE = re.compile(
        r'<script\s+type="text/babel"\s+(?P<attrs>[^>]*?)src="(?P<src>[^"]+)"[^>]*>\s*</script>'
    )
    _inline_cache: dict[str, dict[str, Any]] = {}

    def _inline_html_cached(template_name: str) -> str:
        """Return the inlined HTML for a frontend template, cached by
        max mtime of (template + every referenced .jsx/.js asset)."""
        tmpl = FRONTEND / template_name
        if not tmpl.is_file():
            return ""
        # Cheap stat-only mtime scan over the frontend dir.
        candidates = [tmpl, *FRONTEND.glob("*.jsx"), *FRONTEND.glob("*.js")]
        latest = 0.0
        for p in candidates:
            try:
                m = p.stat().st_mtime
                if m > latest:
                    latest = m
            except OSError:
                pass
        cached = _inline_cache.get(template_name)
        if cached and cached["stamp"] >= latest:
            return cached["html"]

        html = tmpl.read_text(encoding="utf-8")
        def _inline_script(match):
            attrs = match.group("attrs")
            src = match.group("src").split("?", 1)[0]
            if not src.endswith((".jsx", ".js")):
                return match.group(0)
            path = (FRONTEND / src).resolve()
            try:
                path.relative_to(FRONTEND.resolve())
            except Exception:
                return match.group(0)
            if not path.is_file():
                return match.group(0)
            code = path.read_text(encoding="utf-8")
            if "data-filename" not in attrs:
                attrs = f'data-filename="{html_lib.escape(src, quote=True)}" {attrs}'
            return f'<script type="text/babel" {attrs}>{code.rstrip()}\n//# sourceURL={src}</script>'
        html = _INLINE_INDEX_RE.sub(_inline_script, html)
        _inline_cache[template_name] = {"html": html, "stamp": latest}
        return html

    def _html_with_atlas_boot_config(template_name: str) -> str:
        html = _inline_html_cached(template_name)
        if not html:
            return html
        exec_mode = (os.environ.get("ATLAS_EXEC_MODE")
                     or os.environ.get("ATLAS_DEFAULT_EXEC_MODE")
                     or ("orchestrator" if os.environ.get("ATLAS_ORCHESTRATOR_MODE", "1").strip().lower()
                         not in ("0", "false", "no", "off") else "single-worker"))
        payload = {
            "run_mode": os.environ.get("ATLAS_RUN_MODE", "engineering"),
            "exec_mode": exec_mode,
            "multi_user": os.environ.get("ATLAS_MULTI_USER", "1"),
            "multi_user_proc": os.environ.get("ATLAS_MULTI_USER_PROC", "1"),
        }
        script = (
            "<script>window.ATLAS_BOOT_CONFIG="
            + json.dumps(payload, separators=(",", ":"))
            + ";window.ATLAS_DEFAULT_RUN_MODE=window.ATLAS_BOOT_CONFIG.run_mode;"
            + "window.ATLAS_DEFAULT_EXEC_MODE=window.ATLAS_BOOT_CONFIG.exec_mode;</script>"
        )
        return html.replace("</head>", script + "\n</head>", 1)

    _asset_cache: dict[str, dict[str, Any]] = {}

    def _cached_frontend_asset_response(rel_path: str) -> Response:
        """Serve critical frontend assets from memory.

        Starlette StaticFiles streams large files in chunks.  On the shared
        ATLAS backend process that can make first paint hang on vendor Babel
        long enough that the browser stays blank and the chat textarea never
        mounts.  These vendor files are small enough to cache as bytes and
        return in one response.
        """
        clean = rel_path.replace("\\", "/").lstrip("/")
        if ".." in clean.split("/"):
            return JSONResponse({"ok": False, "error": "invalid asset path"}, status_code=404)
        path = (FRONTEND / clean).resolve()
        try:
            path.relative_to(FRONTEND.resolve())
        except Exception:
            return JSONResponse({"ok": False, "error": "invalid asset path"}, status_code=404)
        if not path.is_file():
            return JSONResponse({"ok": False, "error": "asset not found"}, status_code=404)

        stat = path.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        cached = _asset_cache.get(clean)
        if not cached or cached.get("stamp") != stamp:
            cached = {"stamp": stamp, "body": path.read_bytes()}
            _asset_cache[clean] = cached

        ext = path.suffix.lower()
        media_type = _MIME_OVERRIDES.get(ext)
        if not media_type:
            media_type = _mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        return Response(
            content=cached["body"],
            media_type=media_type,
            headers={"Cache-Control": "no-store, max-age=0"},
        )

    @app.get("/")
    async def index():
        """Serve index.html with local JSX inlined.

        Babel standalone loads `type=text/babel src=...` via XHR.  The
        in-app browser can intermittently fail those localhost XHRs even
        when the same asset is directly reachable.  Inlining keeps the
        dev-time Babel path but removes the fragile second fetch.
        Cached by frontend mtime — see _inline_html_cached().
        """
        return HTMLResponse(_html_with_atlas_boot_config("index.html"))

    @app.get("/vendor/{asset_path:path}")
    async def vendor_asset(asset_path: str):
        return _cached_frontend_asset_response(f"vendor/{asset_path}")

    @app.get("/lobby")
    async def lobby():
        return HTMLResponse(_html_with_atlas_boot_config("lobby.html"))

    # Per-process startup epoch — bumps every time the backend
    # restarts. Surfaced in /api/version so the frontend polling loop
    # triggers a reload not only on frontend file edits (mtime track)
    # but also on a pure backend restart, even when no .jsx changed.
    _BACKEND_STARTED_AT = time.time()

    @app.get("/api/version")
    async def api_version():
        """Returns two pieces of "should the browser reload?" data:

        - `mtime`   — latest mtime across the frontend bundle (catches
                      .jsx / .js / .html edits)
        - `started` — backend process start epoch (catches a pure
                      backend reboot when only .py changed)

        The browser polls every few seconds and reloads when EITHER
        value bumps, so backend-reboot and frontend-reload paths both
        propagate without manual cache clears.
        """
        latest = 0.0
        try:
            for f in FRONTEND.iterdir():
                if f.is_file():
                    latest = max(latest, f.stat().st_mtime)
        except OSError:
            pass
        return JSONResponse({"mtime": latest, "started": _BACKEND_STARTED_AT})

    @app.get("/api/pdk/status")
    async def api_pdk_status():
        """Expose the resolved PDK/liberty paths used by Python-launched flows."""
        try:
            try:
                import src.config as _cfg
            except Exception:
                import config as _cfg  # type: ignore
            try:
                _cfg.reload_env()
            except Exception:
                pass
            status_fn = getattr(_cfg, "pdk_status", None)
            if callable(status_fn):
                return JSONResponse(status_fn())
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)
        return JSONResponse({"ok": False, "error": "config.pdk_status unavailable"}, status_code=500)

    @app.get("/api/llm/ping")
    async def api_llm_ping():
        """Cheap provider reachability probe (no token spend).

        Hits `${BASE_URL}/models` with the configured bearer key.
        200 → provider URL + auth + network all OK.
        4xx → auth or path issue (key expired, wrong base_url).
        5xx → provider outage.
        timeout → network / DNS / firewall.

        Used by the frontend boot handshake to surface LLM-side problems
        before the user types their first prompt. Does NOT validate the
        model can actually generate — that needs a real completion call,
        which costs tokens. /models is a list endpoint, 0 tokens.
        """
        try:
            import src.config as _cfg
        except Exception:
            try:
                import config as _cfg  # type: ignore
            except Exception:
                return JSONResponse({"ok": False, "error": "config not loadable"},
                                    status_code=500)
        base = (getattr(_cfg, "BASE_URL", "") or "").rstrip("/")
        api_key = getattr(_cfg, "API_KEY", "") or ""
        if not base:
            return JSONResponse({"ok": False, "error": "BASE_URL not configured"},
                                status_code=500)
        url = base + "/models"

        def _probe():
            import http.client as _hc
            from urllib.parse import urlparse
            u = urlparse(url)
            host, port = u.hostname, (u.port or (443 if u.scheme == "https" else 80))
            conn_cls = _hc.HTTPSConnection if u.scheme == "https" else _hc.HTTPConnection
            conn = conn_cls(host, port, timeout=4)
            try:
                headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
                conn.request("GET", u.path + (("?" + u.query) if u.query else ""),
                             headers=headers)
                resp = conn.getresponse()
                body = resp.read(2048).decode("utf-8", errors="replace")
                return resp.status, body
            finally:
                try: conn.close()
                except Exception: pass

        try:
            status, body = await asyncio.to_thread(_probe)
            # 2xx → fully OK.
            # 401/403 → real auth failure (key bad / expired).
            # 400 → server reachable but rejects the bare /models GET.
            #       Codex OAuth backend (chatgpt.com/backend-api/codex)
            #       demands a `client_version` query param and replies
            #       400 without it; the chat completions path still
            #       works fine. TCP + DNS + TLS all proved alive, so
            #       count as reachable.
            # 404 → endpoint /models not supported, but the server
            #       responded → network + DNS OK. Several providers
            #       (some Azure deployments) don't expose /models;
            #       treat as "reachable" too.
            # 5xx / other → upstream problem.
            ok = (200 <= status < 300) or status in (400, 404)
            reason = (
                "ok" if 200 <= status < 300
                else "auth failed" if status in (401, 403)
                else "server reachable, /models rejected the bare GET" if status == 400
                else "endpoint not exposed but server reachable" if status == 404
                else f"http {status}"
            )
            return JSONResponse({
                "ok": ok,
                "status": status,
                "reason": reason,
                "base_url": base,
                "provider": getattr(_cfg, "LLM_PROVIDER", ""),
                "model": getattr(_cfg, "MODEL", ""),
                "preview": body[:240],
            }, status_code=200 if ok else 502)
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e), "base_url": base},
                                status_code=502)

    @app.post("/api/control/stop")
    async def api_control_stop():
        """HTTP fallback for the UI Stop button and Escape key.

        The primary control plane is the WebSocket, but control buttons
        should still work when the WS is reconnecting or its outbound queue
        is wedged behind a larger message.
        """
        bridge.request_stop()
        bridge.agent_running = False
        bridge.emit("agent_state", running=False)
        return JSONResponse({"ok": True, "action": "stop"})

    @app.post("/api/control/shutdown")
    async def api_control_shutdown():
        """HTTP fallback for the UI Exit button.

        Exit terminates the active session worker only. Atlas UI is the
        backend server for every browser/user, so it must stay alive.
        """
        bridge.exit_active_session()
        return JSONResponse({"ok": True, "action": "exit_session"})

    @app.post("/api/settings/reasoning-effort")
    async def api_settings_reasoning_effort(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            effort = _normalize_reasoning_effort(
                body.get("effort") or body.get("reasoning_effort")
            )
        except ValueError as exc:
            return JSONResponse({
                "ok": False,
                "error": str(exc),
                "allowed": list(_REASONING_EFFORT_OPTIONS),
            }, status_code=400)
        try:
            _persist_reasoning_effort(effort)
            _refresh_config_after_persist()
            _set_runtime_reasoning_effort(effort)
            bridge.emit("context", reasoning_effort=effort)
            return JSONResponse({"ok": True, "reasoning_effort": effort})
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    @app.post("/api/settings/model")
    async def api_settings_model(request: Request):
        try:
            body = await request.json()
        except Exception:
            body = {}

        try:
            import src.config as _cfg_model  # noqa: WPS433
        except Exception:
            try: import config as _cfg_model  # noqa: WPS433
            except Exception: _cfg_model = None
        if _cfg_model is not None:
            try:
                _cfg_model.reload_env()
            except Exception:
                pass

        active = getattr(_cfg_model, "MODEL_NAME", "") if _cfg_model is not None else os.environ.get("LLM_MODEL_NAME", "")
        options = _model_option_rows(active)
        model_key = str(body.get("key") or body.get("model_key") or "").strip()
        requested_model = str(body.get("model") or "").strip()

        selected = None
        if model_key:
            selected = next((row for row in options if row["key"] == model_key), None)
        if selected is None and requested_model:
            selected = next((row for row in options if row["model"] == requested_model), None)
        if selected is None:
            return JSONResponse({
                "ok": False,
                "error": "unknown or empty model option",
                "model_options": options,
            }, status_code=400)
        if selected.get("runtime") == "true":
            return JSONResponse({
                "ok": True,
                "model": selected["model"],
                "selected_model_key": selected["key"],
                "model_options": options,
            })

        model = selected["model"]
        try:
            _persist_env_values({
                selected["key"]: model,
                "LLM_SELECTED_MODEL_KEY": selected["key"],
                "LLM_ACTIVE_MODEL_NAME": model,
                "LLM_ACTIVE_BASE_NAME": model,
            })
            _refresh_config_after_persist()
            _set_runtime_model(model, selected["key"])
            updated_options = _model_option_rows(model)
            updated_selected_key = next(
                (row["key"] for row in updated_options if row.get("selected") == "true"),
                selected["key"],
            )
            bridge.emit("context", model=model, model_options=updated_options, selected_model_key=updated_selected_key)
            return JSONResponse({
                "ok": True,
                "model": model,
                "selected_model_key": updated_selected_key,
                "model_options": updated_options,
            })
        except Exception as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)

    @app.get("/healthz")
    async def healthz(request: Request):
        info = {
            "ok": True,
            "frontend": str(FRONTEND),
            "source_root":  str(SOURCE_ROOT),     # where atlas_ui.py lives
            "project_root": str(PROJECT_ROOT),    # = user's cwd at launch
            "cwd": os.getcwd(),
        }
        # Identity is now derived from the authenticated user (cookie).
        # Single-user vs multi-user only affects whether multiple distinct
        # users can run concurrently — login is required either way.
        _multi_user_on = os.environ.get("ATLAS_MULTI_USER", "").strip().lower() in ("1", "true", "yes", "on")
        info["multi_user"] = _multi_user_on
        user = request.scope.get("user")
        info["user_session"] = (user.get("username") if user else None)
        client_host = (request.client.host if request.client else "") or "127.0.0.1"
        if client_host.startswith("::ffff:"):
            client_host = client_host[7:]
        info["client_ip"] = client_host
        info["project_root_name"] = PROJECT_ROOT.name or ""
        # Expose the real model + context window so the sidebar doesn't
        # have to invent values. Pull from src.config (the per-process
        # frozen settings); if config isn't importable yet, fall through
        # to env vars.
        try:
            import src.config as _cfg  # noqa: WPS433
        except Exception:
            try: import config as _cfg  # noqa: WPS433
            except Exception: _cfg = None
        # Pick up any .env edits made while the server has been running so
        # the sidebar (and dispatch on the next call) reflect the latest
        # active model / profile without a restart. mtime-cached → cheap.
        if _cfg is not None:
            try:
                _cfg.reload_env()
            except Exception:
                pass
        if _cfg is not None:
            model = ""
            try:
                from src.llm_client import get_active_model
                model = get_active_model() or ""
            except Exception:
                pass
            if not model:
                model = (
                    getattr(_cfg, "MODEL_NAME", None)
                    or getattr(_cfg, "PRIMARY_MODEL", None)
                    or getattr(_cfg, "LLM_MODEL_NAME", "")
                )
            info["model"] = model
            info["model_options"] = _model_option_rows(model)
            info["selected_model_key"] = next(
                (row["key"] for row in info["model_options"] if row.get("selected") == "true"),
                "",
            )
            # Use the active dispatch model as the primary display value.
            # PRIMARY_MODEL can remain stale after --model/profile overrides
            # (for example glm in .env while --model deepseek is active),
            # which made the ATLAS sidebar look like it was calling the wrong
            # backend even though dispatch was already using MODEL_NAME.
            info["base_model"] = model or getattr(_cfg, "MODEL_NAME", "")
            if getattr(_cfg, "CURSOR_AGENT_ENABLE", False):
                info["base_url"] = "cursor-agent"
            elif getattr(_cfg, "CLAUDE_CLI_ENABLE", False):
                info["base_url"] = "claude-cli"
            else:
                info["base_url"] = getattr(_cfg, "BASE_URL", "")
            info["provider"] = getattr(_cfg, "LLM_PROVIDER", "")
            info["max_context"] = getattr(_cfg, "MAX_CONTEXT_TOKENS", 0)
            info["max_iterations"] = getattr(_cfg, "MAX_ITERATIONS", 0)
            # Surface the active reasoning effort/mode so the ATLAS sidebar
            # mirrors what textual_main.py shows in its model line.
            info["reasoning_effort"] = (
                getattr(_cfg, "REASONING_MODE", "")
                or getattr(_cfg, "REASONING_EFFORT", "")
                or os.environ.get("REASONING_EFFORT", "")
                or os.environ.get("REASONING_MODE", "")
                or ""
            )
            info["chat_feed_summary"] = bool(getattr(_cfg, "ATLAS_CHAT_FEED_SUMMARY", True))
            # Resolve the "active session" the user is looking at. When
            # the agent boots WITHOUT -w, ACTIVE_WORKSPACE is unset but
            # the session still maps to .session/default/. Prefer the
            # explicit workspace; fall back to the actual project the
            # session loader is using (config.ACTIVE_PROJECT) so the
            # UI can show "default" instead of an ambiguous "—".
            info["workspace"] = (os.environ.get("ACTIVE_WORKSPACE")
                                  or os.environ.get("WORKSPACE")
                                  or getattr(_cfg, "ACTIVE_PROJECT", "")
                                  or "default")
            # Canonical (session_id, ip, workflow) triple — the single
            # source of truth for which IP the user is editing. Updated
            # any time _set_active_ssot_ip runs (e.g. /new-ip <name>),
            # so polling /healthz from the frontend is enough to keep
            # the preview / SSOT / QA panels in sync without a custom
            # WS event.
            info["active_session"] = (
                _active_session_value()
                or _canonical_session_string()
            )
            info["active_ip"] = _active_ip_value() or "default"
            info["active_workflow"] = (
                os.environ.get("ATLAS_DEFAULT_WORKFLOW") or "default"
            )
            info["session_dir"] = str(getattr(_cfg, "SESSION_DIR", "") or "")
            info["todo_file"] = str(getattr(_cfg, "TODO_FILE", "") or "")
            info["history_file"] = str(getattr(_cfg, "HISTORY_FILE", "") or "")
            # Per-model pricing (USD / 1M tokens) — input / cache / output.
            # get_active_pricing honors LLM_BASE_NAME env first, falling
            # back to LLM_MODEL_NAME / config.MODEL_NAME, so the rate shown
            # in the sidebar always matches the model actually in use.
            info["pricing"] = None
            try:
                from lib.model_pricing import get_active_pricing
                p = get_active_pricing()
                if p is not None:
                    info["pricing"] = {
                        "input": p.input, "cache": p.cache, "output": p.output,
                    }
            except Exception:
                pass
            # Live cumulative token + cost totals (from session cost.json).
            # Hot path: /healthz polls every few seconds and the disk
            # read used to block the asyncio loop. Push the read into
            # a thread; the surrounding logic stays cheap.
            try:
                import json as _json
                from pathlib import Path as _P
                _sess = os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()
                _candidates = [
                    _P(_sess) / ".session" / (info["workspace"] or "default") / "cost.json",
                    _P(_sess) / ".session" / "default" / "cost.json",
                ]
                def _pick_cost():
                    for c in _candidates:
                        if c.exists():
                            try:
                                return _json.loads(c.read_text(encoding="utf-8", errors="replace"))
                            except Exception:
                                return None
                    return None
                d = await asyncio.to_thread(_pick_cost)
                if d is not None:
                    # cost.json schema (written by lib/textual_ui.py):
                    # {in_tok, cache_tok, out_tok, sum_tok}. The
                    # previous code read input/cached/output, which
                    # always missed and reported 0 — that wiped the
                    # live-accumulated tokens on every flush via the
                    # /healthz refresh path.
                    info["tokens_in"]    = d.get("in_tok",    d.get("input",  0))
                    info["tokens_cache"] = d.get("cache_tok", d.get("cached", 0))
                    info["tokens_out"]   = d.get("out_tok",   d.get("output", 0))
                    # Cost in USD. tokens_in is total prompt_tokens
                    # (includes cached subset); tokens_cache is that
                    # cached subset, NOT additive. Subtract cached
                    # before applying p.input or we'd bill the cache
                    # twice (once at input, once at cache rate).
                    if info["pricing"]:
                        ti = info["tokens_in"]    or 0
                        tc = info["tokens_cache"] or 0
                        to = info["tokens_out"]   or 0
                        ti_billable = max(0, ti - tc)
                        info["cost_usd"] = (
                            ti_billable * info["pricing"]["input"]  / 1_000_000
                            + tc        * info["pricing"]["cache"]  / 1_000_000
                            + to        * info["pricing"]["output"] / 1_000_000
                        )
            except Exception:
                pass
        else:
            import os as _os
            info["model"] = _os.environ.get("LLM_MODEL_NAME", "") or _os.environ.get("MODEL_NAME", "")
            info["model_options"] = _model_option_rows(info["model"])
            info["selected_model_key"] = next(
                (row["key"] for row in info["model_options"] if row.get("selected") == "true"),
                "",
            )
            info["max_context"] = int(_os.environ.get("MAX_CONTEXT_TOKENS", "0") or "0")
            info["max_iterations"] = int(_os.environ.get("MAX_ITERATIONS", "0") or "0")
            info["workspace"] = _os.environ.get("ACTIVE_WORKSPACE", "") or _os.environ.get("WORKSPACE", "")
        return JSONResponse(info)

    # ── REAL project data API ────────────────────────────────────
    # File-system backed endpoints. All paths are confined to the user's
    # PROJECT_ROOT (= cwd at launch, computed at module import) and
    # rejected if they try to escape via .. or absolute paths. This is
    # NOT the source repo — when the user runs:
    #   cd Custom_IP && python ../brian_hw/common_ai_agent/src/textual_main.py
    # the file API operates on Custom_IP, not on common_ai_agent/.
    # We intentionally re-bind here as a local var so the module-level
    # PROJECT_ROOT survives even if the import gets reloaded weirdly.
    import sys as _sys_local
    _PROJECT_ROOT = globals().get("PROJECT_ROOT") or Path(os.getcwd()).resolve()
    PROJECT_ROOT = _PROJECT_ROOT
    MAX_READ_BYTES = 256 * 1024
    SKIP_DIRS = {".git", "__pycache__", "node_modules", ".session",
                 "ATLAS", "vendor", ".venv", ".pytest_cache",
                 # Internal workflow scaffolding — generated for the LLM as
                 # authoring inputs, not user-facing artifacts. Keep on disk
                 # (workflow scripts still read them) but hide from the file
                 # tree so `rtl/` only surfaces real RTL (.sv/.v) plus the
                 # canonical compile/lint evidence JSONs.
                 "authoring_packets", "stage_engine"}

    # Files that are produced by workflow scripts for downstream-stage
    # consumption (TODO trackers, traceability maps, blocker reports,
    # authoring plans, gate-evidence packets, manifest bookkeeping). They
    # are *not* user-facing artifacts — the relevant data already shows
    # up in the Gates tab / TODO panel / compile/lint evidence cards.
    # Hide them in `/api/files` listings and exclude them from .ZIP
    # downloads. They remain on disk; workflow scripts and the
    # `/resolve-rtl-blockers` flow still read them directly.
    SKIP_FILES = {
        "manifest.json", "decomposition.json",
        "import_manifest.json", "ssot_downstream_blockers.json",
        "rtl_authoring_plan.json", "rtl_authoring_status.md",
        "rtl_blocked.json", "rtl_blocked_resolved.json",
        "rtl_todo_plan.json", "rtl_todo_tracker.json",
        "rtl_traceability.json",
    }

    def _is_internal_artifact(name: str) -> bool:
        if name in SKIP_FILES:
            return True
        if name.startswith("rtl_gate_") and (name.endswith(".json") or name.endswith(".md")):
            return True
        return False

    def _safe(rel_path):
        rel = (rel_path or "").lstrip("/")
        candidate = (PROJECT_ROOT / rel).resolve()
        try:
            candidate.relative_to(PROJECT_ROOT)
        except ValueError:
            return None
        return candidate

    @app.get("/api/files")
    async def api_files(path: str = "", recursive: int = 0, max_depth: int = 4,
                          max_entries: int = 800):
        target = _safe(path)
        if target is None:
            return JSONResponse({"error": "path outside project root"},
                                status_code=400)
        if not target.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        rel = "" if target == PROJECT_ROOT else target.relative_to(PROJECT_ROOT).as_posix()
        if target.is_file():
            stat = target.stat()
            return JSONResponse({
                "type": "file", "path": rel,
                "size": stat.st_size, "mtime": stat.st_mtime,
            })

        entries: list = []

        def _list_one(d, depth):
            try:
                children = sorted(d.iterdir(),
                                   key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return
            for child in children:
                if len(entries) >= max_entries:
                    return
                if child.name in SKIP_DIRS or child.name.startswith("."):
                    continue
                if child.is_file() and _is_internal_artifact(child.name):
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    continue
                entries.append({
                    "name":  child.name if not recursive else child.relative_to(target).as_posix(),
                    "type":  "dir" if child.is_dir() else "file",
                    "size":  stat.st_size if child.is_file() else None,
                    "mtime": stat.st_mtime,
                    "depth": depth,
                })
                if recursive and child.is_dir() and depth < max_depth:
                    _list_one(child, depth + 1)

        _list_one(target, 0)
        return JSONResponse({"type": "dir", "path": rel,
                              "entries": entries,
                              "truncated": len(entries) >= max_entries})

    @app.get("/api/file")
    async def api_file(path: str):
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        try:
            def _read_preview():
                stat = target.stat()
                data = target.read_bytes()[:MAX_READ_BYTES]
                return stat, data.decode("utf-8", errors="replace")
            stat, content = await asyncio.to_thread(_read_preview)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        truncated = stat.st_size > MAX_READ_BYTES
        return JSONResponse({
            "path": path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    def _lint_ip_candidates(ip: str) -> list[Path]:
        clean = str(ip or "").strip().strip("/")
        if not clean:
            return []
        parts = [p for p in clean.split("/") if p]
        if any(p in {".", ".."} or not re.match(r"^[A-Za-z0-9_.-]+$", p) for p in parts):
            return []

        candidates: list[Path] = []
        if len(parts) > 1:
            target = _safe(clean)
            if target is not None:
                candidates.append(target)
        else:
            leaf = parts[0]
            direct = _safe(leaf)
            if direct is not None:
                candidates.append(direct)
            for pattern in (f"*/{leaf}", f"*/*/{leaf}"):
                for match in PROJECT_ROOT.glob(pattern):
                    try:
                        match.relative_to(PROJECT_ROOT)
                    except ValueError:
                        continue
                    if any(part in SKIP_DIRS for part in match.parts):
                        continue
                    candidates.append(match)

        out: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
                rel = resolved.relative_to(PROJECT_ROOT).as_posix()
            except (OSError, ValueError):
                continue
            if rel in seen or not resolved.is_dir():
                continue
            seen.add(rel)
            out.append(resolved)
        return out

    def _choose_lint_ip_dir(ip: str) -> Optional[Path]:
        candidates = _lint_ip_candidates(ip)
        if not candidates:
            return None
        with_report = [p for p in candidates if (p / "lint" / "dut_lint.json").is_file()]
        if with_report:
            return max(with_report, key=lambda p: (p / "lint" / "dut_lint.json").stat().st_mtime)
        with_filelist = [p for p in candidates if (p / "list" / f"{p.name}.f").is_file()]
        if with_filelist:
            return with_filelist[0]
        return candidates[0]

    def _read_lint_report(ip_dir: Path) -> tuple[dict, str]:
        report_path = ip_dir / "lint" / "dut_lint.json"
        if not report_path.is_file():
            return {}, "missing lint/dut_lint.json"
        try:
            return json.loads(report_path.read_text(encoding="utf-8")), ""
        except Exception as exc:
            return {}, f"invalid lint report: {exc}"

    def _lint_diagnostic_path(rel_ip: str, diag_file: Any) -> str:
        file_text = str(diag_file or "").strip()
        if not file_text:
            return ""
        try:
            if os.path.isabs(file_text):
                return Path(file_text).resolve().relative_to(PROJECT_ROOT).as_posix()
        except (OSError, ValueError):
            return file_text
        file_text = file_text.replace("\\", "/").lstrip("/")
        if file_text == rel_ip or file_text.startswith(rel_ip + "/"):
            return file_text
        return f"{rel_ip}/{file_text}"

    def _normalize_lint_tool_results(report: dict, rel_ip: str) -> list[dict]:
        raw_results = report.get("tool_results") if isinstance(report, dict) else []
        if not isinstance(raw_results, list):
            return []
        out: list[dict] = []
        for result in raw_results:
            if not isinstance(result, dict):
                continue
            next_result = dict(result)
            diagnostics = []
            for diag in result.get("diagnostics") or []:
                if not isinstance(diag, dict):
                    continue
                next_diag = dict(diag)
                next_diag["path"] = _lint_diagnostic_path(rel_ip, next_diag.get("file"))
                diagnostics.append(next_diag)
            next_result["diagnostics"] = diagnostics
            out.append(next_result)
        return out

    @app.get("/api/lint/report")
    async def api_lint_report(ip: str, top: str = "", refresh: int = 0):
        """Return the canonical DUT lint report, split by pyslang/Verilator.

        `refresh=1` runs workflow/lint/scripts/dut_lint_report.py first so
        the UI can regenerate the report without asking the user to leave ATLAS.
        """
        ip_dir = _choose_lint_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "IP directory not found", "ip": ip}, status_code=404)

        rel_ip = ip_dir.relative_to(PROJECT_ROOT).as_posix()
        run_info: dict[str, Any] | None = None
        if refresh:
            script = SOURCE_ROOT / "workflow" / "lint" / "scripts" / "dut_lint_report.py"
            cmd = [sys.executable, str(script), rel_ip, "--top", top or ip_dir.name]

            def _run_lint_report():
                return subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                )

            try:
                proc = await asyncio.to_thread(_run_lint_report)
                run_info = {
                    "command": " ".join(cmd),
                    "returncode": proc.returncode,
                    "output": proc.stdout[-12000:] if proc.stdout else "",
                }
            except subprocess.TimeoutExpired as exc:
                run_info = {
                    "command": " ".join(cmd),
                    "returncode": 124,
                    "output": str(exc),
                }
            except Exception as exc:
                run_info = {
                    "command": " ".join(cmd),
                    "returncode": 1,
                    "output": str(exc),
                }

        report, error = _read_lint_report(ip_dir)
        report_path = ip_dir / "lint" / "dut_lint.json"
        log_path = ip_dir / "lint" / "dut_lint.log"
        tool_results = _normalize_lint_tool_results(report, rel_ip) if report else []
        return JSONResponse({
            "ip": ip,
            "resolved_ip": rel_ip,
            "top": top or ip_dir.name,
            "exists": bool(report),
            "error": error,
            "report_path": report_path.relative_to(PROJECT_ROOT).as_posix(),
            "log_path": log_path.relative_to(PROJECT_ROOT).as_posix(),
            "log_exists": log_path.is_file(),
            "tool": report.get("tool", "") if report else "",
            "passed": report.get("passed") if report else None,
            "errors": int(report.get("errors") or 0) if report else 0,
            "warnings": int(report.get("warnings") or 0) if report else 0,
            "suppression_violations": int(report.get("suppression_violation_count") or 0) if report else 0,
            "style_violations": int(report.get("style_violation_count") or 0) if report else 0,
            "command": report.get("command", "") if report else "",
            "timestamp": report.get("timestamp", "") if report else "",
            "rtl_files": report.get("rtl_files", []) if report else [],
            "tool_results": tool_results,
            "run": run_info,
        })

    def _choose_coverage_ip_dir(ip: str) -> Optional[Path]:
        candidates = _lint_ip_candidates(ip)
        if not candidates:
            return None
        artifact_names = (
            "coverage.json",
            "coverage_ssot.json",
            "coverage.info",
            "toggle.json",
            "merged.dat",
        )
        with_cov = [
            p for p in candidates
            if any((p / "cov" / name).is_file() for name in artifact_names)
            or any((p / "sim").glob("*.vcd"))
        ]
        if with_cov:
            def _latest_artifact(path: Path) -> float:
                mtimes: list[float] = []
                for name in artifact_names:
                    target = path / "cov" / name
                    if target.is_file():
                        mtimes.append(target.stat().st_mtime)
                mtimes.extend(p.stat().st_mtime for p in (path / "sim").glob("*.vcd") if p.is_file())
                return max(mtimes or [0.0])
            return max(with_cov, key=_latest_artifact)
        with_filelist = [p for p in candidates if (p / "list" / f"{p.name}.f").is_file()]
        if with_filelist:
            return with_filelist[0]
        return candidates[0]

    def _read_json_artifact(path: Path) -> tuple[dict, str]:
        if not path.is_file():
            return {}, ""
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {}, f"invalid json: {exc}"
        return data if isinstance(data, dict) else {}, ""

    def _coverage_metric(hit: Any, total: Any, target: Any = None) -> dict[str, Any]:
        try:
            hit_i = int(hit or 0)
        except (TypeError, ValueError):
            hit_i = 0
        try:
            total_i = int(total or 0)
        except (TypeError, ValueError):
            total_i = 0
        pct_val = round(100.0 * hit_i / total_i, 2) if total_i else None
        out: dict[str, Any] = {"hit": hit_i, "total": total_i, "pct": pct_val}
        if target is not None:
            try:
                out["target_pct"] = float(target)
                out["meets_target"] = pct_val is not None and pct_val >= out["target_pct"]
            except (TypeError, ValueError):
                out["target_pct"] = target
        return out

    def _parse_lcov_summary(path: Path) -> dict[str, Any]:
        empty = {
            "available": False,
            "path": path.relative_to(PROJECT_ROOT).as_posix() if path.exists() else "",
            "lines": _coverage_metric(0, 0),
            "branches": _coverage_metric(0, 0),
            "functions": _coverage_metric(0, 0),
            "files": [],
            "error": "",
        }
        if not path.is_file():
            return empty

        def new_record() -> dict[str, Any]:
            return {
                "source": "",
                "line_total": 0,
                "line_hit": 0,
                "line_seen": set(),
                "branch_total": 0,
                "branch_hit": 0,
                "branch_seen": set(),
                "function_total": 0,
                "function_hit": 0,
                "function_seen": set(),
            }

        records: list[dict[str, Any]] = []
        current = new_record()

        def finish_record() -> None:
            nonlocal current
            if not current["source"] and not current["line_seen"] and not current["branch_seen"] and not current["function_seen"]:
                current = new_record()
                return
            if current["line_total"] == 0 and current["line_seen"]:
                current["line_total"] = len(current["line_seen"])
                current["line_hit"] = sum(1 for _, hits in current["line_seen"] if hits > 0)
            if current["branch_total"] == 0 and current["branch_seen"]:
                current["branch_total"] = len(current["branch_seen"])
                current["branch_hit"] = sum(1 for _, taken in current["branch_seen"] if taken > 0)
            if current["function_total"] == 0 and current["function_seen"]:
                current["function_total"] = len(current["function_seen"])
                current["function_hit"] = sum(1 for _, hits in current["function_seen"] if hits > 0)
            records.append(current)
            current = new_record()

        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            empty["error"] = str(exc)
            return empty

        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            if line == "end_of_record":
                finish_record()
                continue
            if line.startswith("SF:"):
                current["source"] = line[3:]
                continue
            if line.startswith("DA:"):
                parts = line[3:].split(",")
                if len(parts) >= 2:
                    try:
                        current["line_seen"].add((int(parts[0]), int(parts[1])))
                    except ValueError:
                        pass
                continue
            if line.startswith("LF:"):
                try:
                    current["line_total"] = int(line[3:])
                except ValueError:
                    pass
                continue
            if line.startswith("LH:"):
                try:
                    current["line_hit"] = int(line[3:])
                except ValueError:
                    pass
                continue
            if line.startswith("BRDA:"):
                parts = line[5:].split(",")
                if len(parts) >= 4:
                    try:
                        current["branch_seen"].add((":".join(parts[:3]), 0 if parts[3] == "-" else int(parts[3])))
                    except ValueError:
                        pass
                continue
            if line.startswith("BRF:"):
                try:
                    current["branch_total"] = int(line[4:])
                except ValueError:
                    pass
                continue
            if line.startswith("BRH:"):
                try:
                    current["branch_hit"] = int(line[4:])
                except ValueError:
                    pass
                continue
            if line.startswith("FNDA:"):
                parts = line[5:].split(",", 1)
                if len(parts) == 2:
                    try:
                        current["function_seen"].add((parts[1], int(parts[0])))
                    except ValueError:
                        pass
                continue
            if line.startswith("FNF:"):
                try:
                    current["function_total"] = int(line[4:])
                except ValueError:
                    pass
                continue
            if line.startswith("FNH:"):
                try:
                    current["function_hit"] = int(line[4:])
                except ValueError:
                    pass
        finish_record()

        total_lines = sum(int(r["line_total"] or 0) for r in records)
        hit_lines = sum(int(r["line_hit"] or 0) for r in records)
        total_branches = sum(int(r["branch_total"] or 0) for r in records)
        hit_branches = sum(int(r["branch_hit"] or 0) for r in records)
        total_functions = sum(int(r["function_total"] or 0) for r in records)
        hit_functions = sum(int(r["function_hit"] or 0) for r in records)

        files = []
        for record in records:
            source = str(record["source"] or "")
            try:
                if os.path.isabs(source):
                    source = Path(source).resolve().relative_to(PROJECT_ROOT).as_posix()
            except (OSError, ValueError):
                pass
            files.append({
                "path": source,
                "lines": _coverage_metric(record["line_hit"], record["line_total"]),
                "branches": _coverage_metric(record["branch_hit"], record["branch_total"]),
                "functions": _coverage_metric(record["function_hit"], record["function_total"]),
            })

        return {
            "available": True,
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "lines": _coverage_metric(hit_lines, total_lines),
            "branches": _coverage_metric(hit_branches, total_branches),
            "functions": _coverage_metric(hit_functions, total_functions),
            "files": files,
            "error": "",
        }

    def _coverage_filelist_entries(ip_dir: Path) -> list[str]:
        filelist = ip_dir / "list" / f"{ip_dir.name}.f"
        entries: list[str] = []
        if filelist.is_file():
            for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
                line = raw.split("//", 1)[0].strip()
                if not line or line.startswith("+"):
                    continue
                if line.endswith((".v", ".sv", ".vh", ".svh")) and "/tb/" not in line and not line.startswith("tb/"):
                    entries.append(line)
        if entries:
            return entries
        return [
            path.relative_to(ip_dir).as_posix()
            for path in sorted((ip_dir / "rtl").glob("**/*"))
            if path.is_file() and path.suffix.lower() in {".v", ".sv", ".vh", ".svh"}
        ]

    def _diagnostic_file_name(diag: Any, sm: Any) -> str:
        loc = getattr(diag, "location", None)
        if loc is None or sm is None:
            return ""
        for arg in (loc, getattr(loc, "buffer", None)):
            if arg is None:
                continue
            try:
                file_name = sm.getFileName(arg)
                if file_name:
                    return str(file_name)
            except Exception:
                pass
        for attr in ("fileName", "filename", "file"):
            value = getattr(loc, attr, None)
            if value:
                return str(value)
        return ""

    def _static_rtl_coverage(ip_dir: Path, rel_ip: str) -> dict[str, Any]:
        entries = _coverage_filelist_entries(ip_dir)
        paths = [ip_dir / rel for rel in entries if rel.endswith((".v", ".sv", ".vh", ".svh"))]
        missing = [str(path.relative_to(ip_dir)) for path in paths if not path.is_file()]
        existing = [path for path in paths if path.is_file()]

        counts = {
            "files": len(existing),
            "listed_files": len(paths),
            "missing_files": len(missing),
            "lines": 0,
            "nonempty_lines": 0,
            "modules": 0,
            "always_blocks": 0,
            "assigns": 0,
            "case_blocks": 0,
            "assertions": 0,
            "cover_statements": 0,
        }
        file_rows: list[dict[str, Any]] = []
        for path in existing:
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            row = {
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "lines": len(lines),
                "modules": len(re.findall(r"\bmodule\s+[A-Za-z_][A-Za-z0-9_$]*", text)),
                "always_blocks": len(re.findall(r"\balways(?:_ff|_comb|_latch)?\b", text)),
                "assigns": len(re.findall(r"\bassign\b", text)),
                "case_blocks": len(re.findall(r"\bcase[zx]?\s*\(", text)),
                "assertions": len(re.findall(r"\bassert(?:\s+property)?\b", text)),
                "cover_statements": len(re.findall(r"\bcover(?:\s+property)?\b", text)),
            }
            file_rows.append(row)
            counts["lines"] += row["lines"]
            counts["nonempty_lines"] += sum(1 for line in lines if line.strip())
            for key in ("modules", "always_blocks", "assigns", "case_blocks", "assertions", "cover_statements"):
                counts[key] += int(row[key])

        diagnostics: list[dict[str, Any]] = []
        compile_error = ""
        pyslang_available = False
        try:
            from core.pyslang_compat import compile_files as compile_pyslang_files
            from core.pyslang_compat import diagnostic_is_error, diagnostic_line, diagnostic_message
            compiled = compile_pyslang_files(existing)
            pyslang_available = not str(compiled.error or "").startswith("pyslang import failed")
            sm = compiled.source_manager
            for diag in compiled.diagnostics or []:
                is_error = diagnostic_is_error(diag)
                diag_file = _diagnostic_file_name(diag, sm)
                diagnostics.append({
                    "severity": "error" if is_error else "warning",
                    "file": diag_file,
                    "path": _lint_diagnostic_path(rel_ip, diag_file),
                    "line": diagnostic_line(diag, sm),
                    "message": diagnostic_message(compiled.pyslang, diag, sm),
                })
            if compiled.error:
                compile_error = compiled.error
                if not diagnostics:
                    diagnostics.append({
                        "severity": "error",
                        "file": "",
                        "path": "",
                        "line": 0,
                        "message": compiled.error,
                    })
        except Exception as exc:
            compile_error = f"pyslang static analysis failed: {exc}"
            diagnostics.append({"severity": "error", "file": "", "path": "", "line": 0, "message": compile_error})

        errors = sum(1 for d in diagnostics if str(d.get("severity", "")).lower() == "error")
        warnings = len(diagnostics) - errors
        return {
            "tool": "pyslang",
            "kind": "static_elab",
            "available": pyslang_available,
            "passed": bool(existing) and not missing and errors == 0,
            "source": "list/{name}.f + pyslang compile + static RTL scan".format(name=ip_dir.name),
            "filelist": (ip_dir / "list" / f"{ip_dir.name}.f").relative_to(PROJECT_ROOT).as_posix()
                if (ip_dir / "list" / f"{ip_dir.name}.f").is_file() else "",
            "rtl_files": [path.relative_to(PROJECT_ROOT).as_posix() for path in existing],
            "missing": missing,
            "metrics": counts,
            "files": file_rows,
            "diagnostics": diagnostics[:100],
            "errors": errors,
            "warnings": warnings,
            "error": compile_error,
        }

    def _domain_matches(bin_id: str, item: Any, domain: str) -> bool:
        text = str(bin_id).lower()
        if isinstance(item, dict):
            text += " " + " ".join(
                str(item.get(key, "")).lower()
                for key in ("coverage_domain", "domain", "class", "source", "description")
            )
            plan = item.get("plan")
            if isinstance(plan, dict):
                text += " " + " ".join(str(plan.get(key, "")).lower() for key in ("coverage_domain", "domain", "class", "source", "description"))
        if domain == "function":
            return any(token in text for token in ("function", "functional", "transaction", "scenario", "fl"))
        return any(token in text for token in ("cycle", "protocol", "handshake", "latency", "fsm", "transition", "cl"))

    def _domain_coverage_from_report(report: dict, domain: str) -> dict[str, Any]:
        key = "function_coverage" if domain == "function" else "cycle_coverage"
        raw = report.get(key) if isinstance(report.get(key), dict) else {}
        out = {
            "domain": domain,
            "hit": int(raw.get("hit") or 0),
            "total": int(raw.get("total") or 0),
            "pct": raw.get("pct"),
            "target_pct": raw.get("target_pct"),
            "meets_target": raw.get("meets_target"),
            "source": raw.get("source") or ("function_model" if domain == "function" else "cycle_model"),
            "missing_bins": [],
            "bins": [],
        }
        bins = report.get("functional_bins") if isinstance(report.get("functional_bins"), dict) else {}
        for bin_id, item in bins.items():
            if not _domain_matches(str(bin_id), item, domain):
                continue
            hit = bool(item.get("hit") or item.get("covered") or item.get("raw_hit")) if isinstance(item, dict) else bool(item)
            row = {
                "id": str(bin_id),
                "hit": hit,
                "source": item.get("source", "") if isinstance(item, dict) else "",
                "description": item.get("description", "") if isinstance(item, dict) else "",
            }
            out["bins"].append(row)
            if not hit:
                out["missing_bins"].append(row)
        return out

    def _normalize_toggle_report(toggle: dict, path: Path) -> dict[str, Any]:
        if not toggle:
            return {
                "available": False,
                "path": path.relative_to(PROJECT_ROOT).as_posix() if path.exists() else "",
                "vcd": "",
                "metrics": _coverage_metric(0, 0),
                "nets": 0,
                "scopes": [],
            }
        total = int(toggle.get("total_bits") or 0)
        hit = int(toggle.get("toggled_bits") or 0)
        scopes = toggle.get("scopes") if isinstance(toggle.get("scopes"), list) else []
        scopes = sorted(
            [s for s in scopes if isinstance(s, dict)],
            key=lambda s: (float(s.get("pct") or 0.0), str(s.get("scope") or "")),
        )
        return {
            "available": True,
            "path": path.relative_to(PROJECT_ROOT).as_posix(),
            "vcd": str(toggle.get("vcd") or ""),
            "metrics": {**_coverage_metric(hit, total), "pct": round(float(toggle.get("pct") or 0.0), 2) if total else None},
            "nets": int(toggle.get("nets") or 0),
            "scopes": scopes[:20],
        }

    def _coverage_card(id_: str, label: str, available: bool, status: str, metrics: list[dict[str, Any]], **extra: Any) -> dict[str, Any]:
        payload = {
            "id": id_,
            "label": label,
            "available": available,
            "status": status,
            "metrics": metrics,
        }
        payload.update(extra)
        return payload

    @app.get("/reports/cov")
    @app.get("/api/reports/cov")
    @app.get("/api/reports/coverage")
    @app.get("/api/coverage/report")
    async def api_coverage_report(ip: str, top: str = "", refresh: int = 0, vcd: int = 0):
        """Return a consolidated coverage report for Atlas.

        The endpoint intentionally aggregates existing workflow artifacts
        instead of inventing a second coverage format:
        Verilator LCOV, SSOT FL/CL coverage, VCD toggle coverage, and a
        pyslang/static RTL source universe.
        """
        ip_dir = _choose_coverage_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "IP directory not found", "ip": ip}, status_code=404)

        rel_ip = ip_dir.relative_to(PROJECT_ROOT).as_posix()
        cov_dir = ip_dir / "cov"
        sim_dir = ip_dir / "sim"
        run_info: dict[str, Any] = {}

        if refresh:
            script = SOURCE_ROOT / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"
            cmd = [sys.executable, str(script), rel_ip]

            def _run_summary():
                return subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                )

            try:
                proc = await asyncio.to_thread(_run_summary)
                run_info["summary"] = {
                    "command": shlex.join(cmd),
                    "returncode": proc.returncode,
                    "output": proc.stdout[-12000:] if proc.stdout else "",
                }
            except subprocess.TimeoutExpired as exc:
                run_info["summary"] = {"command": shlex.join(cmd), "returncode": 124, "output": str(exc)}
            except Exception as exc:
                run_info["summary"] = {"command": shlex.join(cmd), "returncode": 1, "output": str(exc)}

        if vcd:
            script = SOURCE_ROOT / "workflow" / "coverage" / "scripts" / "coverage_vcd_toggle.sh"
            cmd = ["bash", str(script), rel_ip, "--json"]
            if top:
                cmd.extend(["--top", top])

            def _run_vcd_toggle():
                return subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=180,
                )

            try:
                proc = await asyncio.to_thread(_run_vcd_toggle)
                run_info["vcd"] = {
                    "command": shlex.join(cmd),
                    "returncode": proc.returncode,
                    "output": proc.stdout[-12000:] if proc.stdout else "",
                }
            except subprocess.TimeoutExpired as exc:
                run_info["vcd"] = {"command": shlex.join(cmd), "returncode": 124, "output": str(exc)}
            except Exception as exc:
                run_info["vcd"] = {"command": shlex.join(cmd), "returncode": 1, "output": str(exc)}

        coverage_json_path = cov_dir / "coverage.json"
        coverage_ssot_path = cov_dir / "coverage_ssot.json"
        coverage_info_path = cov_dir / "coverage.info"
        toggle_path = cov_dir / "toggle.json"
        report_md_path = sim_dir / "coverage_report.md"

        coverage_doc, coverage_error = _read_json_artifact(coverage_json_path)
        ssot_doc, ssot_error = _read_json_artifact(coverage_ssot_path)
        if not coverage_doc and ssot_doc:
            coverage_doc = ssot_doc
        lcov = _parse_lcov_summary(coverage_info_path)
        toggle_doc, toggle_error = _read_json_artifact(toggle_path)
        toggle_report = _normalize_toggle_report(toggle_doc, toggle_path)
        static_report = _static_rtl_coverage(ip_dir, rel_ip)
        function_cov = _domain_coverage_from_report(coverage_doc, "function")
        cycle_cov = _domain_coverage_from_report(coverage_doc, "cycle")

        ver_lines = coverage_doc.get("lines") if isinstance(coverage_doc.get("lines"), dict) else lcov["lines"]
        ver_branches = coverage_doc.get("branches") if isinstance(coverage_doc.get("branches"), dict) else lcov["branches"]
        ver_functions = coverage_doc.get("functions") if isinstance(coverage_doc.get("functions"), dict) else lcov["functions"]
        verilator_available = lcov["available"] or bool(coverage_doc.get("lines") or coverage_doc.get("branches"))
        static_metrics = static_report["metrics"]

        tools = [
            _coverage_card(
                "verilator",
                "Verilator code coverage",
                verilator_available,
                "available" if verilator_available else "missing",
                [
                    {"label": "line", **_coverage_metric(ver_lines.get("hit"), ver_lines.get("total"), ver_lines.get("target_pct"))},
                    {"label": "branch", **_coverage_metric(ver_branches.get("hit"), ver_branches.get("total"), ver_branches.get("target_pct"))},
                    {"label": "function", **_coverage_metric(ver_functions.get("hit"), ver_functions.get("total"))},
                ],
                path=lcov.get("path") or coverage_info_path.relative_to(PROJECT_ROOT).as_posix(),
                files=lcov.get("files", []),
                note="Runtime code coverage from Verilator LCOV / coverage.info.",
            ),
            _coverage_card(
                "pyslang",
                "pyslang static/elab coverage",
                bool(static_report["rtl_files"]),
                "pass" if static_report["passed"] else "blocked",
                [
                    {"label": "rtl files", "hit": static_metrics["files"], "total": static_metrics["listed_files"], "pct": round(100.0 * static_metrics["files"] / static_metrics["listed_files"], 2) if static_metrics["listed_files"] else None},
                    {"label": "modules", "value": static_metrics["modules"]},
                    {"label": "source lines", "value": static_metrics["lines"]},
                    {"label": "always", "value": static_metrics["always_blocks"]},
                ],
                diagnostics=static_report["diagnostics"],
                files=static_report["files"],
                missing=static_report["missing"],
                note="Static RTL universe plus pyslang parse/elaboration diagnostics. This is not runtime hit coverage.",
            ),
            _coverage_card(
                "sim-vcd",
                "Simulation VCD toggle coverage",
                toggle_report["available"],
                "available" if toggle_report["available"] else "missing",
                [
                    {"label": "toggle", **toggle_report["metrics"]},
                    {"label": "nets", "value": toggle_report["nets"]},
                ],
                path=toggle_report["path"],
                vcd=toggle_report["vcd"],
                scopes=toggle_report["scopes"],
                note="Bit is covered when it observed both a rise and a fall in the VCD.",
            ),
            _coverage_card(
                "functional-fl",
                "FL function coverage",
                function_cov["total"] > 0,
                "pass" if function_cov.get("meets_target") else "blocked",
                [{"label": "function bins", **_coverage_metric(function_cov["hit"], function_cov["total"], function_cov.get("target_pct"))}],
                bins=function_cov["bins"],
                missing_bins=function_cov["missing_bins"],
                note="Function-model / scenario coverage from SSOT functional bins.",
            ),
            _coverage_card(
                "functional-cl",
                "CL cycle coverage",
                cycle_cov["total"] > 0,
                "pass" if cycle_cov.get("meets_target") else "blocked",
                [{"label": "cycle bins", **_coverage_metric(cycle_cov["hit"], cycle_cov["total"], cycle_cov.get("target_pct"))}],
                bins=cycle_cov["bins"],
                missing_bins=cycle_cov["missing_bins"],
                note="Cycle-model / protocol coverage from SSOT functional bins.",
            ),
        ]

        vcd_paths = [
            p.relative_to(PROJECT_ROOT).as_posix()
            for p in sorted(list(sim_dir.glob("**/*.vcd")) + list(cov_dir.glob("**/*.vcd")))
            if p.is_file()
        ]
        artifact_paths = [
            p.relative_to(PROJECT_ROOT).as_posix()
            for p in (coverage_json_path, coverage_ssot_path, coverage_info_path, toggle_path, report_md_path)
            if p.is_file()
        ]

        return JSONResponse({
            "ip": ip,
            "resolved_ip": rel_ip,
            "top": top or ip_dir.name,
            "exists": bool(coverage_doc or lcov["available"] or toggle_report["available"] or static_report["rtl_files"]),
            "status": coverage_doc.get("status", "unknown") if coverage_doc else "unknown",
            "errors": [e for e in (coverage_error, ssot_error, toggle_error, lcov.get("error")) if e],
            "report_path": coverage_json_path.relative_to(PROJECT_ROOT).as_posix(),
            "report_exists": coverage_json_path.is_file(),
            "ssot_path": coverage_ssot_path.relative_to(PROJECT_ROOT).as_posix(),
            "ssot_exists": coverage_ssot_path.is_file(),
            "lcov_path": coverage_info_path.relative_to(PROJECT_ROOT).as_posix(),
            "lcov_exists": coverage_info_path.is_file(),
            "toggle_path": toggle_path.relative_to(PROJECT_ROOT).as_posix(),
            "toggle_exists": toggle_path.is_file(),
            "markdown_path": report_md_path.relative_to(PROJECT_ROOT).as_posix(),
            "markdown_exists": report_md_path.is_file(),
            "artifacts": artifact_paths,
            "vcd_paths": vcd_paths,
            "tools": tools,
            "coverage": coverage_doc,
            "lcov": lcov,
            "toggle": toggle_report,
            "static": static_report,
            "run": run_info,
        })

    # ── Foldable structure for PreviewPane (sv / yaml) ────────────
    # Returns line ranges the frontend wraps in <details>. Empty list
    # for unknown extensions — caller falls back to plain Prism.
    _FOLD_CACHE: "collections.OrderedDict[str, tuple[float, list]]" = collections.OrderedDict()
    _FOLD_CACHE_CAP = 32
    _FOLD_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
    _FOLD_MAX_LINES = 10_000

    @app.get("/api/fold-symbols")
    async def api_fold_symbols(path: str):
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        stat = target.stat()
        # mtime-keyed LRU
        cached = _FOLD_CACHE.get(path)
        if cached and cached[0] == stat.st_mtime:
            _FOLD_CACHE.move_to_end(path)
            return JSONResponse({
                "path": path, "ranges": cached[1], "cached": True,
            })
        if stat.st_size > _FOLD_MAX_BYTES:
            return JSONResponse({
                "path": path, "ranges": [], "skipped": True,
                "reason": f"file > {_FOLD_MAX_BYTES // (1024*1024)} MB",
            })
        try:
            text = await asyncio.to_thread(
                lambda: target.read_text(encoding="utf-8", errors="replace")
            )
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        if text.count("\n") > _FOLD_MAX_LINES:
            return JSONResponse({
                "path": path, "ranges": [], "skipped": True,
                "reason": f"more than {_FOLD_MAX_LINES} lines",
            })
        try:
            from core.fold_extractor import folds_for_path
            ranges = await asyncio.to_thread(folds_for_path, path, text)
        except Exception as e:
            return JSONResponse({
                "path": path, "ranges": [], "error": f"extractor failed: {e}",
            }, status_code=422)
        _FOLD_CACHE[path] = (stat.st_mtime, ranges)
        _FOLD_CACHE.move_to_end(path)
        while len(_FOLD_CACHE) > _FOLD_CACHE_CAP:
            _FOLD_CACHE.popitem(last=False)
        return JSONResponse({
            "path": path, "ranges": ranges, "cached": False,
        })

    # ── VCD (waveform) endpoints — sim_debug workspace ────────────
    # VCD files can be MB+ so we bypass MAX_READ_BYTES with a separate
    # ceiling. Path resolution still goes through _safe() so the user
    # can't escape PROJECT_ROOT.
    MAX_VCD_BYTES = 32 * 1024 * 1024  # 32 MB
    # Routes registered via register_vcd_routes() below (see atlas_api_vcd.py).

    @app.post("/api/ip/create")
    async def api_ip_create(request: Request):
        """Legacy no-op for older Atlas frontends.

        IP creation/scaffolding is handled by `/new-ip <name>` so there is
        exactly one path that creates `<PROJECT_ROOT>/<ip>/...`. Keeping
        this endpoint as validation-only lets stale browser bundles proceed
        to `/new-ip` without creating an extra empty IP root first.
        """
        try:
            body = await request.json()
        except Exception:
            body = {}
        name = str((body or {}).get("name") or "").strip()
        if not name:
            return JSONResponse({"error": "name required"}, status_code=400)
        if "/" in name or "\\" in name or ".." in name:
            return JSONResponse({"error": "invalid name"}, status_code=400)
        target = (PROJECT_ROOT / name).resolve()
        try:
            target.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return JSONResponse({"error": "outside project root"}, status_code=400)
        return JSONResponse({"ok": True,
                             "ip": name,
                             "created": False,
                             "path": str(target.relative_to(PROJECT_ROOT.resolve())),
                             "message": "IP scaffolding is handled by /new-ip"})

    def _resolve_ip_path(name: str) -> Path | tuple[None, JSONResponse]:
        """Validate a path-segment-style IP name and return its on-disk dir.

        Returns a Path on success, or a (None, JSONResponse) tuple on
        failure for the caller to forward."""
        clean = str(name or "").strip()
        if not clean or "/" in clean or "\\" in clean or ".." in clean:
            return None, JSONResponse({"error": "invalid ip name"}, status_code=400)
        target = (PROJECT_ROOT / clean).resolve()
        try:
            target.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return None, JSONResponse({"error": "outside project root"}, status_code=400)
        if not target.is_dir():
            return None, JSONResponse({"error": "ip not found"}, status_code=404)
        if not (target / ".git").is_dir():
            return None, JSONResponse({"error": "ip has no .git — create via /new-ip first"}, status_code=409)
        return target

    @app.post("/api/ip/{name}/git/commit")
    async def api_ip_git_commit(name: str, request: Request):
        """Stage and commit the IP's working tree with a user/agent message."""
        try:
            body = await request.json()
        except Exception:
            body = {}
        message = str((body or {}).get("message") or "").strip() or "commit"
        resolved = _resolve_ip_path(name)
        if isinstance(resolved, tuple):
            _, err = resolved
            return err
        target = resolved
        try:
            import subprocess as _sp
            _sp.run(["git", "add", "--", "."], cwd=str(target),
                    capture_output=True, timeout=15, check=False)
            out = _sp.run(["git", "commit", "--allow-empty", "-m", message],
                          cwd=str(target), capture_output=True,
                          timeout=15, check=False)
            head = _sp.run(["git", "rev-parse", "HEAD"], cwd=str(target),
                           capture_output=True, timeout=5, check=False)
            return JSONResponse({
                "ok": out.returncode == 0,
                "ip": name,
                "hash": head.stdout.decode("utf-8", "replace").strip()[:12],
                "stdout": out.stdout.decode("utf-8", "replace"),
                "stderr": out.stderr.decode("utf-8", "replace"),
            })
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/ip/{name}/git/log")
    async def api_ip_git_log(name: str, limit: int = 50):
        """Return the last N commits of the per-IP repo as JSON."""
        resolved = _resolve_ip_path(name)
        if isinstance(resolved, tuple):
            _, err = resolved
            return err
        target = resolved
        try:
            import subprocess as _sp
            limit = max(1, min(int(limit or 50), 500))
            sep = "\x1f"
            fmt = sep.join(["%H", "%h", "%an", "%at", "%s"])
            out = _sp.run(
                ["git", "log", f"--pretty=format:{fmt}", f"-n{limit}"],
                cwd=str(target), capture_output=True, timeout=10, check=False,
            )
            commits = []
            for line in out.stdout.decode("utf-8", "replace").splitlines():
                parts = line.split(sep)
                if len(parts) >= 5:
                    commits.append({
                        "hash":   parts[0],
                        "short":  parts[1],
                        "author": parts[2],
                        "time":   float(parts[3]) if parts[3].isdigit() else 0,
                        "subject": parts[4],
                    })
            return JSONResponse({"ip": name, "commits": commits})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/ip/{name}/git/url")
    async def api_ip_git_url(name: str, request: Request):
        """Return clone URLs for the per-IP bare repo at <root>/<name>.git.
        Honors BARE_GIT_OPTION — returns 404 when the bare wasn't built."""
        clean = str(name or "").strip()
        if not clean or "/" in clean or "\\" in clean or ".." in clean:
            return JSONResponse({"error": "invalid ip name"}, status_code=400)
        bare = (PROJECT_ROOT / f"{clean}.git").resolve()
        try:
            bare.relative_to(PROJECT_ROOT.resolve())
        except ValueError:
            return JSONResponse({"error": "outside project root"}, status_code=400)
        if not (bare / "HEAD").is_file():
            return JSONResponse({"error": "no bare repo — BARE_GIT_OPTION may be off, or scaffold hasn't run"},
                                status_code=404)
        host = request.headers.get("host") or "127.0.0.1:8765"
        scheme = "https" if request.url.scheme == "https" else "http"
        return JSONResponse({
            "ip": clean,
            "bare_path": str(bare),
            "clone": {
                "http": f"{scheme}://{host}/git/{clean}.git",
                "file": f"file://{bare}",
            },
        })

    @app.api_route("/git/{path:path}", methods=["GET", "POST"])
    async def git_http_backend_proxy(path: str, request: Request):
        """Smart-HTTP gateway over git-http-backend so the per-IP bare
        repos under PROJECT_ROOT are clone+push targets on the LAN.
        Honors BARE_GIT_OPTION — returns 404 when disabled."""
        from starlette.responses import Response as _StarResponse
        try:
            import config as _cfg_git
            if not getattr(_cfg_git, "BARE_GIT_OPTION", True):
                return JSONResponse({"error": "BARE_GIT_OPTION disabled"}, status_code=404)
        except Exception:
            pass
        # Find git-http-backend. Brew puts it under libexec/git-core.
        import subprocess as _sp_git
        backend = ""
        try:
            ep = _sp_git.run(["git", "--exec-path"], capture_output=True,
                             timeout=3, check=False)
            cand = (ep.stdout.decode("utf-8", "replace").strip() + "/git-http-backend")
            if Path(cand).is_file():
                backend = cand
        except Exception:
            pass
        if not backend:
            return JSONResponse({"error": "git-http-backend not found on host"},
                                status_code=501)
        auth_header = request.headers.get("authorization", "")
        query_string = request.url.query or ""
        if "service=git-receive-pack" in query_string and not auth_header.lower().startswith("basic "):
            return _StarResponse(
                content=b"Authentication required for git push\n",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Atlas Git"'},
            )
        env = dict(os.environ)
        env.update({
            "GIT_PROJECT_ROOT": str(PROJECT_ROOT.resolve()),
            "GIT_HTTP_EXPORT_ALL": "1",
            "PATH_INFO": "/" + path,
            "REQUEST_METHOD": request.method,
            "QUERY_STRING": query_string,
            "CONTENT_TYPE": request.headers.get("content-type", ""),
            "CONTENT_LENGTH": request.headers.get("content-length", "0"),
            "REMOTE_ADDR": (request.client.host if request.client else "127.0.0.1"),
        })
        if auth_header.lower().startswith("basic "):
            try:
                import base64 as _base64_git_auth
                raw = _base64_git_auth.b64decode(
                    auth_header.split(None, 1)[1],
                    validate=True,
                ).decode("utf-8", "replace")
                username = raw.split(":", 1)[0].strip()
                if username:
                    # git-http-backend treats REMOTE_USER as the signal
                    # that HTTP auth succeeded. Without this, clients that
                    # retry with http://user:pass@host/... still look
                    # anonymous to receive-pack and can get Unauthorized.
                    env["REMOTE_USER"] = username
                    env["AUTH_TYPE"] = "Basic"
            except Exception:
                pass
        body = await request.body()
        proc = await asyncio.create_subprocess_exec(
            backend,
            env=env,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _stderr = await asyncio.wait_for(
                proc.communicate(body), timeout=120,
            )
        except asyncio.TimeoutError:
            proc.kill()
            return JSONResponse({"error": "git-http-backend timed out"},
                                status_code=504)
        sep = stdout.find(b"\r\n\r\n")
        if sep == -1:
            return _StarResponse(content=stdout, status_code=200)
        header_text = stdout[:sep].decode("latin-1", "replace")
        resp_body = stdout[sep + 4:]
        status = 200
        headers: dict[str, str] = {}
        for line in header_text.split("\r\n"):
            if line.lower().startswith("status:"):
                try: status = int(line.split(":", 1)[1].strip().split()[0])
                except Exception: status = 200
            elif ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip()] = v.strip()
        return _StarResponse(content=resp_body, status_code=status, headers=headers)

    @app.get("/api/ip/{name}/git/graph")
    async def api_ip_git_graph(name: str, limit: int = 80):
        """ASCII graph of the per-IP commit history. Returns the raw
        `git log --graph --oneline --decorate --all` text plus a parsed
        commit list so the frontend can render either a monospaced graph
        or a structured list."""
        resolved = _resolve_ip_path(name)
        if isinstance(resolved, tuple):
            _, err = resolved
            return err
        target = resolved
        try:
            import subprocess as _sp
            limit = max(1, min(int(limit or 80), 1000))
            graph = _sp.run(
                ["git", "log", "--graph", "--oneline", "--decorate", "--all",
                 "--date=relative", f"-n{limit}",
                 "--pretty=format:%h %s%d (%cr)"],
                cwd=str(target), capture_output=True, timeout=10, check=False,
            )
            structured = _sp.run(
                ["git", "log", f"-n{limit}",
                 "--pretty=format:%H\x1f%h\x1f%an\x1f%at\x1f%s\x1f%P"],
                cwd=str(target), capture_output=True, timeout=10, check=False,
            )
            commits = []
            for line in structured.stdout.decode("utf-8", "replace").splitlines():
                parts = line.split("\x1f")
                if len(parts) >= 5:
                    commits.append({
                        "hash":    parts[0],
                        "short":   parts[1],
                        "author":  parts[2],
                        "time":    float(parts[3]) if parts[3].isdigit() else 0,
                        "subject": parts[4],
                        "parents": (parts[5].split() if len(parts) >= 6 else []),
                    })
            return JSONResponse({
                "ip": name,
                "graph": graph.stdout.decode("utf-8", "replace"),
                "commits": commits,
            })
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/ip/{name}/git/revert")
    async def api_ip_git_revert(name: str, request: Request):
        """Restore the working tree to a previous commit (hard reset)."""
        try:
            body = await request.json()
        except Exception:
            body = {}
        target_hash = str((body or {}).get("hash") or "").strip()
        if not re.match(r"^[0-9a-f]{7,40}$", target_hash, re.I):
            return JSONResponse({"error": "invalid hash"}, status_code=400)
        resolved = _resolve_ip_path(name)
        if isinstance(resolved, tuple):
            _, err = resolved
            return err
        target = resolved
        try:
            import subprocess as _sp
            verify = _sp.run(["git", "cat-file", "-e", target_hash],
                             cwd=str(target), capture_output=True, timeout=5, check=False)
            if verify.returncode != 0:
                return JSONResponse({"error": "hash not in this ip's history"}, status_code=404)
            # Use `git reset --hard` so the working tree and HEAD both
            # snap to the requested commit. Caller has been warned via
            # UI confirmation; auto-commits will resume from this point.
            out = _sp.run(["git", "reset", "--hard", target_hash],
                          cwd=str(target), capture_output=True, timeout=15, check=False)
            return JSONResponse({
                "ok": out.returncode == 0,
                "ip": name,
                "hash": target_hash,
                "stdout": out.stdout.decode("utf-8", "replace"),
                "stderr": out.stderr.decode("utf-8", "replace"),
            })
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/ip/list")
    async def api_ip_list(request: Request, session_id: str = ""):
        """List IPs that belong to a session namespace.

        In single-user desktop mode the dropdown should include real IP
        directories under PROJECT_ROOT, so a newly generated IP is
        selectable before any per-user session history exists. In
        multi-user mode the authoritative source remains
        `.session/<session_id>/<ip>/<workflow>/` to avoid cross-user IP
        leakage.
        """
        skip = set(SKIP_DIRS) | {
            ".session", ".git", ".venv", ".sisyphus", ".omc", "logs",
            "node_modules", "workflow", "src", "core", "lib", "tests",
            "frontend", "docs", "scripts",
        }
        ip_markers = {
            "yaml", "rtl", "tb", "sim", "lint", "syn", "sta", "sta-post",
            "pnr", "dft", "doc", "req", "list", "cov", "verify", "model",
        }
        by_name: dict[str, dict[str, Any]] = {}

        def _ssot_exists(name: str) -> bool:
            yaml_dir = PROJECT_ROOT / name / "yaml"
            if not yaml_dir.is_dir():
                return False
            if (yaml_dir / f"{name}.ssot.yaml").is_file():
                return True
            try:
                return any(yaml_dir.glob("*.ssot.yaml"))
            except OSError:
                return False

        def _add_item(name: str, *, workflows=None, mtime: float = 0.0) -> None:
            if not name or name.startswith(".") or name in skip:
                return
            row = by_name.setdefault(name, {
                "name": name,
                "has_ssot": _ssot_exists(name),
                "workflows": [],
                "mtime": mtime,
            })
            row["has_ssot"] = bool(row.get("has_ssot")) or _ssot_exists(name)
            row["mtime"] = max(float(row.get("mtime") or 0.0), float(mtime or 0.0))
            if workflows:
                merged = set(row.get("workflows") or [])
                merged.update(str(w) for w in workflows if str(w or "").strip())
                row["workflows"] = sorted(merged)

        def _looks_like_project_ip(entry: Path) -> bool:
            if not entry.is_dir() or entry.name.startswith(".") or entry.name in skip:
                return False
            try:
                return any((entry / marker).is_dir() for marker in ip_markers)
            except OSError:
                return False

        user = request.scope.get("user") or {}
        username = normalize_session_name(str(user.get("username") or ""))
        requested = normalize_session_name(str(session_id or ""))
        owner = (requested.split("/", 1)[0] if requested else "") or username
        multi_user_on = os.environ.get("ATLAS_MULTI_USER", "").strip().lower() in ("1", "true", "yes", "on")
        if multi_user_on and username and owner and owner != username:
            return JSONResponse({"error": "session owner mismatch", "items": []}, status_code=403)
        session_root = (PROJECT_ROOT / ".session" / owner).resolve() if owner else None
        try:
            if not multi_user_on:
                for entry in PROJECT_ROOT.iterdir():
                    if _looks_like_project_ip(entry):
                        _add_item(entry.name, mtime=entry.stat().st_mtime)
            if session_root is None or not session_root.is_dir():
                items = sorted(by_name.values(), key=lambda x: (-x["mtime"], x["name"]))
                return JSONResponse({
                    "project_root": str(PROJECT_ROOT),
                    "session_id": owner or "",
                    "items": items,
                    "count": len(items),
                })
            try:
                session_root.relative_to((PROJECT_ROOT / ".session").resolve())
            except ValueError:
                return JSONResponse({"error": "session path escapes .session", "items": []}, status_code=400)
            for entry in session_root.iterdir():
                if not entry.is_dir():
                    continue
                name = entry.name
                if name.startswith(".") or name in skip:
                    continue
                workflows = sorted(
                    child.name for child in entry.iterdir()
                    if child.is_dir() and not child.name.startswith(".")
                )
                _add_item(name, workflows=workflows, mtime=entry.stat().st_mtime)
        except OSError as exc:
            return JSONResponse({"error": str(exc), "items": []}, status_code=500)
        items = sorted(by_name.values(), key=lambda x: (-x["mtime"], x["name"]))
        return JSONResponse({
            "project_root": str(PROJECT_ROOT),
            "session_id": owner or "",
            "items": items,
            "count": len(items),
        })

    @app.get("/api/ssot-gates/{ip}")
    async def api_ssot_gates(ip: str):
        """Aggregate SSOT-quality + per-stage checker results for one IP.

        Drives the SSOT Design Preview "Gates" tab. Reads existing
        artifacts produced by repair_ssot_schema, check_ssot_disk,
        emit_fl_model, emit_equivalence_goals, ssot_to_rtl, rtl_compile,
        dut_lint, fl_rtl_compare, fl_rtl_goal_audit, etc. Does NOT
        re-run any LLM-bearing stage; only inspects evidence on disk.
        """
        import yaml as _yaml
        ip_dir = _safe(ip)
        if ip_dir is None or not ip_dir.is_dir():
            return JSONResponse({"error": "ip not found", "ip": ip}, status_code=404)

        def _read_json(path: Path) -> Any:
            if not path.is_file():
                return None
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None

        def _stat_iso(path: Path) -> str:
            if not path.exists():
                return ""
            try:
                ts = path.stat().st_mtime
                return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))
            except Exception:
                return ""

        def _rel(path: Path) -> str:
            try:
                return str(path.relative_to(PROJECT_ROOT))
            except Exception:
                return str(path)

        ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
        ssot_doc: dict[str, Any] = {}
        ssot_parses = False
        if ssot_path.is_file():
            try:
                ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
                ssot_parses = isinstance(ssot_doc, dict)
            except Exception:
                ssot_parses = False

        REQUIRED_SECTIONS = [
            "top_module", "sub_modules", "decomposition", "parameters", "io_list",
            "features", "dataflow", "function_model", "cycle_model", "rtl_contract",
            "clock_reset_domains", "registers", "memory", "interrupts", "fsm",
            "timing", "power", "security", "error_handling", "debug_observability",
            "integration", "dft", "synthesis", "pnr", "test_requirements",
            "quality_gates", "traceability", "workflow_todos", "filelist",
            "coding_rules", "reuse_modules", "custom", "dir_structure",
            "generation_flow", "cdc_requirements",
        ]

        present_sections = sum(1 for k in REQUIRED_SECTIONS if k in ssot_doc)
        legacy_keys = [
            k for k in ("interface", "bus_interface", "apb_behavior", "clock_reset",
                        "interrupt", "interrupt_behavior", "register_map",
                        "submodule_structure", "counter_behavior", "reset_behavior")
            if k in ssot_doc
        ]
        ssot_text = ""
        try:
            ssot_text = ssot_path.read_text(encoding="utf-8") if ssot_path.is_file() else ""
        except Exception:
            pass
        tbd_count = ssot_text.count("TBD") + ssot_text.count("?TBD")

        downstream_doc = _read_json(ip_dir / "req" / "ssot_downstream_blockers.json")
        downstream_blockers = []
        if isinstance(downstream_doc, dict):
            downstream_blockers = downstream_doc.get("issues") or downstream_doc.get("blockers") or []

        fm = ssot_doc.get("function_model") if isinstance(ssot_doc.get("function_model"), dict) else {}
        txs = [t for t in (fm.get("transactions") or []) if isinstance(t, dict)]
        rtl_contract = ssot_doc.get("rtl_contract") if isinstance(ssot_doc.get("rtl_contract"), dict) else {}
        input_map = rtl_contract.get("input_map") if isinstance(rtl_contract.get("input_map"), dict) else {}
        output_map = rtl_contract.get("output_map") if isinstance(rtl_contract.get("output_map"), dict) else {}
        sample_condition = str(rtl_contract.get("sample_condition") or "")

        sub_modules = ssot_doc.get("sub_modules") if isinstance(ssot_doc.get("sub_modules"), list) else []
        owned = sum(1 for m in sub_modules if isinstance(m, dict) and (m.get("owner") or m.get("ownership")))
        with_fm_refs = sum(1 for m in sub_modules if isinstance(m, dict) and m.get("function_model_refs"))

        quality: list[dict[str, Any]] = []

        def _add_q(id_: str, label: str, status: str, summary: str, evidence: list[str] = None,
                   helper: str = ""):
            quality.append({
                "id": id_,
                "label": label,
                "status": status,
                "summary": summary,
                "evidence": evidence or [],
                "helper": helper,
            })

        _add_q(
            "structure",
            "Structure (REQUIRED_ORDER)",
            "pass" if present_sections >= len(REQUIRED_SECTIONS) else (
                "fail" if not ssot_parses else "unverified"
            ),
            f"{present_sections}/{len(REQUIRED_SECTIONS)} canonical sections present",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py (REQUIRED_ORDER)",
        )
        _add_q(
            "disk_validator",
            "Disk validator (size + parse)",
            "pass" if ssot_parses and ssot_path.is_file() and ssot_path.stat().st_size >= 4000 else "fail",
            (
                f"{ssot_path.stat().st_size}B parses={ssot_parses}"
                if ssot_path.is_file() else "ssot file not found"
            ),
            [_rel(ssot_path)] if ssot_path.is_file() else [],
            "workflow/ssot-gen/scripts/check_ssot_disk.sh",
        )
        _add_q(
            "downstream_readiness",
            "Downstream readiness (--strict-downstream)",
            "pass" if not downstream_blockers else "fail",
            f"{len(downstream_blockers)} blocker(s)" if downstream_blockers else "clean",
            [_rel(ip_dir / "req" / "ssot_downstream_blockers.json")] if downstream_doc else [],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py --strict-downstream",
        )
        _add_q(
            "legacy_detection",
            "Legacy top-level keys",
            "pass" if not legacy_keys else "unverified",
            "no legacy keys" if not legacy_keys else f"{len(legacy_keys)} found: " + ", ".join(legacy_keys[:5]),
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_legacy_interface_to_io_list",
        )
        _add_q(
            "tbd_count",
            "TBD / placeholder count",
            "pass" if tbd_count == 0 else "unverified",
            f"{tbd_count} TBD occurrences" if tbd_count else "0 TBD",
            [_rel(ssot_path)] if ssot_path.is_file() else [],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_has_tbd",
        )
        _add_q(
            "submodule_ownership",
            "Submodule ownership",
            "pass" if sub_modules and owned == len(sub_modules) else (
                "skip" if not sub_modules else "fail"
            ),
            f"{owned}/{len(sub_modules)} owned" if sub_modules else "no sub_modules",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_validate_submodule_ownership",
        )
        _add_q(
            "fm_refs_completeness",
            "Function-model refs on sub_modules",
            "pass" if sub_modules and with_fm_refs == len(sub_modules) else (
                "skip" if not sub_modules else "unverified"
            ),
            f"{with_fm_refs}/{len(sub_modules)} have function_model_refs" if sub_modules else "no sub_modules",
            [_rel(ssot_path)],
            "workflow/fl-model-gen/scripts/emit_equivalence_goals.py (B-2 advisory)",
        )

        # IO completeness — referenced names in expressions vs declared ports + input_map
        try:
            import ast as _ast
            referenced: set[str] = set()
            for tx in txs:
                for r in (tx.get("output_rules") or []):
                    if isinstance(r, dict):
                        for k in ("expr", "expression", "value"):
                            if k in r:
                                py = str(r.get(k) or "").replace("&&", " and ").replace("||", " or ")
                                try:
                                    for n in _ast.walk(_ast.parse(py, mode="eval")):
                                        if isinstance(n, _ast.Name): referenced.add(n.id)
                                except Exception: pass
            io = ssot_doc.get("io_list") if isinstance(ssot_doc.get("io_list"), dict) else {}
            declared_ports: set[str] = set()
            for grp in (io.get("interfaces") or []) + (io.get("clock_domains") or []) + (io.get("resets") or []):
                if isinstance(grp, dict):
                    for p in (grp.get("ports") or []):
                        if isinstance(p, dict):
                            n = str(p.get("name") or "").strip()
                            if n: declared_ports.add(n)
            helpers = {"and","or","not","True","False","None","gray_to_bin","bin_to_gray","popcount","parity","clog2","min","max","abs"}
            missing_io = sorted(n for n in referenced if n and n not in declared_ports and n not in input_map and n not in output_map and n not in helpers and not n.isdigit())
        except Exception:
            missing_io = []

        _add_q(
            "io_completeness",
            "IO completeness (rule names → input_map/ports)",
            "pass" if not missing_io else "fail",
            f"{len(missing_io)} unmapped names: {', '.join(missing_io[:5])}" if missing_io else f"{len(input_map)} mapped, 0 missing",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_ensure_rule_expr_input_map_completeness (C-1)",
        )

        # Sample condition DSL parseable
        try:
            sc_py = sample_condition.replace("&&", " and ").replace("||", " or ")
            sc_ok = bool(sample_condition.strip())
            if sc_ok:
                try:
                    import ast as _ast2
                    _ast2.parse(sc_py, mode="eval")
                except Exception:
                    sc_ok = False
        except Exception:
            sc_ok = False
        _add_q(
            "sample_condition",
            "rtl_contract.sample_condition DSL",
            "pass" if sc_ok else "fail",
            f"sample_condition={sample_condition!r}" if sample_condition else "empty",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_validate_sample_conditions (C-2)",
        )

        state_vars = (fm.get("state_variables") or []) if isinstance(fm.get("state_variables"), list) else []
        observable_state_count = 0
        observable_with_rule = 0
        for s in state_vars:
            if not isinstance(s, dict): continue
            name = str(s.get("name") or "").strip()
            if not name: continue
            for grp in (ssot_doc.get("io_list") or {}).get("interfaces") or []:
                ports = (grp.get("ports") or []) if isinstance(grp, dict) else []
                if any(isinstance(p, dict) and str(p.get("name") or "") == name and str(p.get("direction") or "") == "output" for p in ports):
                    observable_state_count += 1
                    has_rule = False
                    for tx in txs:
                        for r in (tx.get("output_rules") or []) + (tx.get("state_updates") or []):
                            if isinstance(r, dict) and (str(r.get("name") or "") == name or str(r.get("port") or "") == name):
                                has_rule = True; break
                        if has_rule: break
                    if has_rule:
                        observable_with_rule += 1
                    break
        _add_q(
            "state_observability",
            "Observable state variables have rules",
            "pass" if observable_state_count == 0 or observable_with_rule == observable_state_count else "unverified",
            f"{observable_with_rule}/{observable_state_count} observable state vars have rules" if observable_state_count else "no observable state vars",
            [_rel(ssot_path)],
            "workflow/ssot-gen/scripts/repair_ssot_schema.py::_ensure_rule_expr_input_map_completeness (C-3)",
        )

        # Equivalence goals
        eg = _read_json(ip_dir / "verify" / "equivalence_goals.json")
        eg_total = eg_blocked = eg_unverified = None
        if isinstance(eg, dict):
            s = eg.get("summary") or {}
            eg_total = int(s.get("total", 0))
            eg_blocked = int(s.get("blocked", 0))
            eg_unverified = int(s.get("unverified", 0))
        _add_q(
            "equiv_goals",
            "Equivalence goals (FL↔RTL)",
            "skip" if eg is None else (
                "fail" if (eg_blocked or 0) > 0 else (
                    "unverified" if (eg_unverified or 0) > 0 else "pass"
                )
            ),
            f"total={eg_total} blocked={eg_blocked} unverified={eg_unverified}" if eg else "not yet generated",
            [_rel(ip_dir / "verify" / "equivalence_goals.json")] if eg else [],
            "workflow/fl-model-gen/scripts/emit_equivalence_goals.py",
        )

        # Connection contracts (production manifest)
        connection_issues = 0
        prov = _read_json(ip_dir / "rtl" / "rtl_authoring_provenance.json")
        if isinstance(prov, dict):
            connection_issues = int(prov.get("quality_issues", 0)) + int(prov.get("hierarchy_issues", 0))
        _add_q(
            "connection_contracts",
            "RTL manifest connection contracts",
            "skip" if not prov else ("pass" if connection_issues == 0 else "fail"),
            f"{connection_issues} hierarchy/quality issues" if prov else "not yet generated",
            [_rel(ip_dir / "rtl" / "rtl_authoring_provenance.json")] if prov else [],
            "workflow/rtl-gen/scripts/derive_rtl_todos.py",
        )

        # Coverage refs
        fcov = _read_json(ip_dir / "cov" / "fcov_plan.json")
        bins = (fcov.get("bins") or fcov.get("plan") or []) if isinstance(fcov, dict) else []
        _add_q(
            "coverage_refs",
            "Functional coverage plan exists",
            "skip" if not fcov else ("pass" if bins else "unverified"),
            f"{len(bins)} bins/plan entries" if fcov else "not yet generated",
            [_rel(ip_dir / "cov" / "fcov_plan.json")] if fcov else [],
            "workflow/fl-model-gen/scripts/emit_fl_model.py",
        )

        # Per-stage results
        stages: list[dict[str, Any]] = []

        def _add_s(stage: str, status: str, summary: str, evidence: list[str] = None,
                   scripts: list[str] = None):
            stages.append({
                "stage": stage,
                "status": status,
                "summary": summary,
                "evidence": evidence or [],
                "scripts": scripts or [],
                "last_modified": max((_stat_iso(PROJECT_ROOT / e) for e in (evidence or [])), default=""),
            })

        # ssot-gen
        ssot_gen_status = "pass" if ssot_parses and present_sections >= 30 and not downstream_blockers else (
            "skip" if not ssot_parses else "fail"
        )
        _add_s(
            "ssot-gen",
            ssot_gen_status,
            f"sections={present_sections}/{len(REQUIRED_SECTIONS)} downstream_blockers={len(downstream_blockers)}",
            [_rel(ssot_path)],
            ["workflow/ssot-gen/scripts/repair_ssot_schema.py", "workflow/ssot-gen/scripts/check_ssot_disk.sh"],
        )

        # fl-model-gen
        fl_check = _read_json(ip_dir / "model" / "fl_model_check.json")
        fl_passed = isinstance(fl_check, dict) and fl_check.get("passed")
        _add_s(
            "fl-model-gen",
            "skip" if not fl_check else ("pass" if fl_passed else "fail"),
            (f"checks={(fl_check.get('self_check') or {}).get('checks',0)} passed={fl_passed}" if fl_check else "not yet run"),
            [_rel(ip_dir / "model" / "fl_model_check.json"), _rel(ip_dir / "model" / "functional_model.py")] if fl_check else [],
            ["workflow/fl-model-gen/scripts/emit_fl_model.py"],
        )

        # cl-model-gen
        cl_check = _read_json(ip_dir / "model" / "cl_model_check.json")
        cl_passed = isinstance(cl_check, dict) and cl_check.get("passed")
        _add_s(
            "cl-model-gen",
            "skip" if not cl_check else ("pass" if cl_passed else "fail"),
            (f"passed={cl_passed}" if cl_check else "not yet run"),
            [_rel(ip_dir / "model" / "cl_model_check.json")] if cl_check else [],
            ["workflow/cl-model-gen/scripts/emit_cl_model.py"],
        )

        # equiv-goals
        _add_s(
            "equiv-goals",
            "skip" if eg is None else (
                "fail" if (eg_blocked or 0) > 0 else (
                    "unverified" if (eg_unverified or 0) > 0 else "pass"
                )
            ),
            f"total={eg_total} blocked={eg_blocked} unverified={eg_unverified}" if eg else "not yet run",
            [_rel(ip_dir / "verify" / "equivalence_goals.json")] if eg else [],
            ["workflow/fl-model-gen/scripts/emit_equivalence_goals.py"],
        )

        # rtl-gen
        rtl_blocked_doc = _read_json(ip_dir / "rtl" / "rtl_blocked.json")
        rtl_compile = _read_json(ip_dir / "rtl" / "rtl_compile.json")
        dut_lint = _read_json(ip_dir / "lint" / "dut_lint.json")
        compile_errors = int((rtl_compile or {}).get("errors", 0))
        lint_errors = int((dut_lint or {}).get("errors", 0))
        lint_warnings = int((dut_lint or {}).get("warnings", 0))
        if rtl_blocked_doc:
            rtl_status = "blocked"
            rtl_summary = f"preflight blocked: {len((rtl_blocked_doc or {}).get('questions') or [])} questions"
        elif rtl_compile is None:
            rtl_status = "skip"
            rtl_summary = "not yet run"
        elif compile_errors == 0 and lint_errors == 0:
            rtl_status = "pass"
            rtl_summary = f"compile_errors=0 lint_errors=0 warnings={lint_warnings}"
        else:
            rtl_status = "fail"
            rtl_summary = f"compile_errors={compile_errors} lint_errors={lint_errors} warnings={lint_warnings}"
        _add_s(
            "rtl-gen",
            rtl_status,
            rtl_summary,
            [p for p in [
                _rel(ip_dir / "rtl" / "rtl_compile.json") if rtl_compile else "",
                _rel(ip_dir / "lint" / "dut_lint.json") if dut_lint else "",
                _rel(ip_dir / "rtl" / "rtl_blocked.json") if rtl_blocked_doc else "",
                _rel(ip_dir / "rtl" / "rtl_authoring_provenance.json") if prov else "",
            ] if p],
            [
                "workflow/rtl-gen/scripts/ssot_to_rtl.py",
                "workflow/rtl-gen/scripts/derive_rtl_todos.py",
                "workflow/rtl-gen/scripts/rtl_compile_report.py",
                "workflow/lint/scripts/dut_lint_report.py",
            ],
        )

        # tb-gen
        tb_dir = ip_dir / "tb"
        tb_artifacts = sorted(p.name for p in tb_dir.glob("**/*.py")) if tb_dir.is_dir() else []
        _add_s(
            "tb-gen",
            "skip" if not tb_artifacts else "pass",
            f"{len(tb_artifacts)} TB python files" if tb_artifacts else "not yet run",
            [_rel(tb_dir)] if tb_artifacts else [],
            ["workflow/tb-gen/scripts/emit_tb.py", "workflow/tb-gen/runtime/equivalence_scoreboard.py"],
        )

        # sim
        sim_compare = _read_json(ip_dir / "sim" / "fl_rtl_compare.json")
        sim_status = "skip"
        sim_summary = "not yet run"
        if sim_compare:
            mm = int(sim_compare.get("mismatch_count", sim_compare.get("mismatches", 0)))
            tot = int(sim_compare.get("total_rows", sim_compare.get("total", 0)))
            sim_status = "pass" if mm == 0 else "fail"
            sim_summary = f"total={tot} mismatch={mm}"
        _add_s(
            "sim", sim_status, sim_summary,
            [_rel(ip_dir / "sim" / "fl_rtl_compare.json")] if sim_compare else [],
            ["workflow/sim_debug/scripts/compare_fl_rtl_results.py"],
        )

        # sim-debug
        mc = _read_json(ip_dir / "sim" / "mismatch_classification.json")
        if mc:
            items = mc.get("classifications") or []
            owners: dict[str, int] = {}
            for it in items:
                if isinstance(it, dict):
                    o = str(it.get("owner", "?"))
                    owners[o] = owners.get(o, 0) + 1
            sd_summary = " ".join(f"{k}:{v}" for k, v in sorted(owners.items())) if owners else "no mismatches"
            _add_s("sim-debug", "pass" if items else "skip", sd_summary,
                   [_rel(ip_dir / "sim" / "mismatch_classification.json")],
                   ["workflow/sim_debug/scripts/compare_fl_rtl_results.py"])
        else:
            _add_s("sim-debug", "skip", "not yet run", [], [])

        # lint
        if dut_lint:
            _add_s("lint", "pass" if lint_errors == 0 else "fail",
                   f"errors={lint_errors} warnings={lint_warnings}",
                   [_rel(ip_dir / "lint" / "dut_lint.json")],
                   ["workflow/lint/scripts/dut_lint_report.py"])
        else:
            _add_s("lint", "skip", "not yet run", [], [])

        # coverage
        cov = _read_json(ip_dir / "cov" / "coverage.json")
        ga = _read_json(ip_dir / "sim" / "fl_rtl_goal_audit.json")
        cov_summary = "not yet run"
        cov_status = "skip"
        if ga:
            bins_doc = ga.get("bins") if isinstance(ga.get("bins"), dict) else {}
            hit = int(bins_doc.get("hit", bins_doc.get("hit_count", 0)) or 0)
            tot = int(bins_doc.get("total", 0) or 0)
            cov_status = "pass" if (tot > 0 and hit == tot) else ("fail" if tot else "skip")
            cov_summary = f"bins_hit={hit}/{tot}"
        _add_s("coverage", cov_status, cov_summary,
               [_rel(ip_dir / "sim" / "fl_rtl_goal_audit.json")] if ga else [],
               ["workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py"])

        # goal-audit
        ga_audit = _read_json(ip_dir / "verify" / "equivalence_goals_audit.json")
        ga_summary = "not yet run"
        ga_status = "skip"
        if ga_audit:
            ga_status = str(ga_audit.get("status", "unknown"))
            if ga_status not in ("pass", "fail", "blocked"): ga_status = "unverified"
            s = ga_audit.get("summary") or {}
            ga_summary = ", ".join(f"{k}={v}" for k, v in list(s.items())[:6]) if s else "audit produced"
        _add_s("goal-audit", ga_status, ga_summary,
               [_rel(ip_dir / "verify" / "equivalence_goals_audit.json")] if ga_audit else [],
               ["workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py"])

        passed_q = sum(1 for q in quality if q["status"] == "pass")
        passed_s = sum(1 for s in stages if s["status"] == "pass")
        return JSONResponse({
            "ip": ip,
            "ssot_path": _rel(ssot_path),
            "ssot_exists": ssot_path.is_file(),
            "ssot_parses": ssot_parses,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ssot_quality": {
                "items": quality,
                "passed": passed_q,
                "total": len(quality),
            },
            "stages": {
                "items": stages,
                "passed": passed_s,
                "total": len(stages),
            },
        })

    @app.get("/api/debug/scenarios")
    async def api_debug_scenarios(ip: str):
        """Resolve `<ip>/yaml/<ip>.ssot.yaml` test_requirements.scenarios
        and roll up pass/fail per scenario from
        `<ip>/sim/scoreboard_events.jsonl`.

        Drives the Debug tab's Tests panel: scenarios are the source of
        truth (SSOT), status comes from the latest sim run. No cross-IP
        leakage — only the requested IP's directory is read.
        """
        ip_dir = _safe(ip)
        if ip_dir is None or not ip_dir.is_dir():
            return JSONResponse({"error": "ip not found", "tests": []}, status_code=404)
        ssot_path = ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml"
        sb_path   = ip_dir / "sim"  / "scoreboard_events.jsonl"

        # Disk reads moved off the event loop. Reading SSOT YAML +
        # scoreboard JSONL synchronously inside the coroutine pinned
        # every other request behind it for hundreds of milliseconds
        # whenever the user opened the Debug tab.
        def _read_ssot_scenarios() -> list:
            if not ssot_path.is_file():
                return []
            try:
                import yaml as _yaml  # type: ignore
                doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace"))
                tr = (doc or {}).get("test_requirements") or {}
                return list(tr.get("scenarios") or [])
            except Exception:
                return []

        def _read_scoreboard_rows() -> list:
            if not sb_path.is_file():
                return []
            import json as _json
            out = []
            for line in sb_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(_json.loads(line))
                except Exception:
                    continue
            return out

        scenarios = await asyncio.to_thread(_read_ssot_scenarios)
        rows = await asyncio.to_thread(_read_scoreboard_rows)

        by_sid: dict[str, dict] = {}
        for r in rows:
            sid = r.get("scenario_id")
            if not sid:
                continue
            bucket = by_sid.setdefault(sid, {"pass": 0, "fail": 0, "rows": []})
            bucket["rows"].append(r)
            if r.get("passed"):
                bucket["pass"] += 1
            else:
                bucket["fail"] += 1

        tests = []
        seen_sids: set[str] = set()
        for sc in scenarios:
            sid = sc.get("id")
            if sid:
                seen_sids.add(str(sid))
            b = by_sid.get(sid, {"pass": 0, "fail": 0, "rows": []})
            if b["fail"] > 0:
                status = "fail"
            elif b["pass"] > 0:
                status = "pass"
            else:
                status = "pending"
            tests.append({
                "scenario_id": sid,
                "name": sc.get("name", sid or ""),
                "status": status,
                "stimulus": sc.get("stimulus", ""),
                "expected": sc.get("expected", ""),
                "checker":  sc.get("checker", ""),
                "coverage": sc.get("coverage", []),
                "pass_rows": b["pass"],
                "fail_rows": b["fail"],
                "source": "ssot",
            })
        for sid in sorted(k for k in by_sid.keys() if str(k) not in seen_sids):
            b = by_sid.get(sid, {"pass": 0, "fail": 0, "rows": []})
            if b["fail"] > 0:
                status = "fail"
            elif b["pass"] > 0:
                status = "pass"
            else:
                status = "pending"
            tests.append({
                "scenario_id": sid,
                "name": sid,
                "status": status,
                "stimulus": "",
                "expected": "",
                "checker": "",
                "coverage": [],
                "pass_rows": b["pass"],
                "fail_rows": b["fail"],
                "source": "scoreboard",
            })
        summary = {
            "pass":    sum(1 for t in tests if t["status"] == "pass"),
            "fail":    sum(1 for t in tests if t["status"] == "fail"),
            "pending": sum(1 for t in tests if t["status"] == "pending"),
            "total":   len(tests),
        }
        return JSONResponse({
            "ip": ip,
            "ssot_path": str(ssot_path.relative_to(PROJECT_ROOT)) if ssot_path.is_file() else "",
            "sb_path":   str(sb_path.relative_to(PROJECT_ROOT))   if sb_path.is_file()   else "",
            "tests":   tests,
            "summary": summary,
        })

    # ── Source endpoint — sim_debug signal→driver + cocotb test view ─
    # Accepts SV/V plus the text extensions that show up in the
    # cocotb tab (Python tests, sequences, agents, env, Makefile,
    # YAML/JSON, etc.). Rejects binaries to avoid shipping .vvp / .out
    # contents over WS.
    _SOURCE_EXTS = {
        ".sv", ".v", ".svh", ".vh",          # SystemVerilog
        ".py",                                # cocotb / Python testbench
        ".sdc", ".tcl", ".f",                 # constraints / filelists
        ".yaml", ".yml", ".json", ".md",      # config / docs
        ".txt", ".log", ".rpt",               # reports
        ".sh", ".bash",                       # scripts
        ".c", ".h", ".cpp", ".hpp",           # firmware
        ".xml",                               # results.xml
    }
    _SOURCE_NO_EXT_NAMES = {"Makefile", "makefile", "Dockerfile"}

    @app.get("/api/source")
    async def api_source(path: str):
        """Read a source file. Accepts SV / V / Python / Make /
        constraints / YAML / JSON / Markdown / shell / firmware /
        results.xml. Returns split-by-line array for the SourceViewer
        component."""
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        suffix = target.suffix.lower()
        if suffix not in _SOURCE_EXTS and target.name not in _SOURCE_NO_EXT_NAMES:
            return JSONResponse({
                "error": f"unsupported extension '{suffix or target.name}'",
                "allowed": sorted(_SOURCE_EXTS) + sorted(_SOURCE_NO_EXT_NAMES),
            }, status_code=400)
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path,
            "size": len(content),
            "content": content,
            "lines": content.split("\n"),
        })

    # ── sim_debug elab module loader ─────────────────────────────
    # Lives at workflow/sim_debug/elab.py — co-located with the rest
    # of the sim_debug workspace (system_prompt.md, commands/, rules/,
    # scripts/). Loaded via importlib so we don't have to add
    # workflow/sim_debug/ to sys.path globally.
    _ELAB_CACHE = {}
    def _load_sim_debug_elab():
        import importlib.util as _ilu
        elab_path = SOURCE_ROOT / "workflow" / "sim_debug" / "elab.py"
        if not elab_path.is_file():
            raise FileNotFoundError(f"sim_debug elab module not found at {elab_path}")
        try:
            mtime_ns = elab_path.stat().st_mtime_ns
        except OSError:
            mtime_ns = 0
        if _ELAB_CACHE.get("path") == str(elab_path) and _ELAB_CACHE.get("mtime_ns") == mtime_ns:
            return _ELAB_CACHE["mod"]
        spec = _ilu.spec_from_file_location("sim_debug_elab", str(elab_path))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ELAB_CACHE.update({"mod": mod, "path": str(elab_path), "mtime_ns": mtime_ns})
        return mod

    # ── Elab endpoints (pyslang / Verilator / slang) — sim_debug hierarchy + trace ─
    @app.get("/api/elab/status")
    async def api_elab_status():
        try:
            mod = _load_sim_debug_elab()
            return JSONResponse(mod.status())
        except Exception as e:
            return JSONResponse({"error": str(e), "pyslang": False, "verilator": False, "slang": False}, status_code=500)

    def _elab_resolve_sources(sources_glob: str, ip: str = "") -> list:
        """Resolve a comma-separated glob list (or a single ip-tree default).
        Each pattern is interpreted relative to PROJECT_ROOT and clipped to
        files that pass _safe(). Default source discovery prefers the IP
        filelist (`<ip>/list/*.f` or nested `*/<ip>/list/*.f`) before
        falling back to RTL directory scans.
        """
        skip_parts = {
            ".git", ".session", "__pycache__", "node_modules", "vendor",
            ".venv", "venv", "dist", "build",
        }
        rtl_suffixes = (".sv", ".v", ".svh", ".vh")
        filelist_suffixes = (".f", ".vf", ".flist", ".list")
        out: list = []
        seen: set[str] = set()
        seen_filelists: set[str] = set()

        def _add(f):
            try:
                resolved = f.resolve()
                rel = resolved.relative_to(PROJECT_ROOT)
            except (OSError, ValueError):
                return
            if any(part in skip_parts for part in rel.parts):
                return
            if not f.is_file() or f.suffix.lower() not in rtl_suffixes:
                return
            key = rel.as_posix()
            if key in seen:
                return
            seen.add(key)
            out.append(resolved)

        def _project_relative_file(p: Path, suffixes: tuple[str, ...]) -> Optional[Path]:
            try:
                resolved = p.resolve()
                rel = resolved.relative_to(PROJECT_ROOT)
            except (OSError, ValueError):
                return None
            if any(part in skip_parts for part in rel.parts):
                return None
            if not resolved.is_file() or resolved.suffix.lower() not in suffixes:
                return None
            return resolved

        def _resolve_filelist_token(token: str, bases: list[Path]) -> list[Path]:
            raw = os.path.expanduser(os.path.expandvars(str(token or "").strip()))
            if not raw:
                return []
            p = Path(raw)
            if p.is_absolute():
                return [p]
            candidates: list[Path] = []
            for base in bases:
                candidates.append(base / p)
            candidates.append(PROJECT_ROOT / p)
            return candidates

        def _read_filelist(filelist: Path) -> None:
            resolved = _project_relative_file(filelist, filelist_suffixes)
            if resolved is None:
                return
            key = resolved.relative_to(PROJECT_ROOT).as_posix()
            if key in seen_filelists:
                return
            seen_filelists.add(key)
            bases = [resolved.parent, resolved.parent.parent, PROJECT_ROOT]
            try:
                lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                return
            for raw in lines:
                line = raw.split("//", 1)[0].split("#", 1)[0].strip()
                if not line:
                    continue
                try:
                    tokens = shlex.split(line, comments=False, posix=True)
                except ValueError:
                    tokens = line.split()
                i = 0
                while i < len(tokens):
                    token = tokens[i].strip()
                    if token in ("-f", "-F") and i + 1 < len(tokens):
                        for candidate in _resolve_filelist_token(tokens[i + 1], bases):
                            _read_filelist(candidate)
                        i += 2
                        continue
                    if (token.startswith("-f") or token.startswith("-F")) and len(token) > 2:
                        for candidate in _resolve_filelist_token(token[2:], bases):
                            _read_filelist(candidate)
                        i += 1
                        continue
                    if token.startswith("+incdir+") or token.startswith("+define+") or token.startswith("-I"):
                        i += 1
                        continue
                    if token.startswith("-") or token.startswith("+"):
                        i += 1
                        continue
                    if Path(token).suffix.lower() in rtl_suffixes:
                        for candidate in _resolve_filelist_token(token, bases):
                            _add(candidate)
                    i += 1

        def _add_default_filelists(clean_ip: str) -> None:
            ip_leaf = Path(clean_ip).name
            patterns = [
                f"{clean_ip}/list/{ip_leaf}.f",
                f"{clean_ip}/list/*.f",
                f"common_ai_agent/{clean_ip}/list/{ip_leaf}.f",
                f"common_ai_agent/{clean_ip}/list/*.f",
                f"common_ai_agent/*/{clean_ip}/list/{ip_leaf}.f",
                f"common_ai_agent/*/{clean_ip}/list/*.f",
                f"*/{clean_ip}/list/{ip_leaf}.f",
                f"*/{clean_ip}/list/*.f",
                f"*/*/{clean_ip}/list/{ip_leaf}.f",
                f"*/*/{clean_ip}/list/*.f",
            ]
            for pat in patterns:
                for f in PROJECT_ROOT.glob(pat):
                    _read_filelist(f)

        if not sources_glob and ip:
            clean_ip = str(ip).strip().strip("/")
            _add_default_filelists(clean_ip)
            if out:
                return out
            default_patterns = [
                f"{clean_ip}/rtl/*",
                f"common_ai_agent/{clean_ip}/rtl/*",
                f"common_ai_agent/*/{clean_ip}/rtl/*",
                f"*/{clean_ip}/rtl/*",
                f"*/*/{clean_ip}/rtl/*",
            ]
            for pat in default_patterns:
                for f in PROJECT_ROOT.glob(pat):
                    _add(f)
            if not out:
                for rtl_dir in PROJECT_ROOT.rglob("rtl"):
                    try:
                        rel = rtl_dir.resolve().relative_to(PROJECT_ROOT)
                    except (OSError, ValueError):
                        continue
                    if any(part in skip_parts for part in rel.parts):
                        continue
                    parent = rtl_dir.parent.name
                    if parent == clean_ip or clean_ip in rel.parts:
                        for f in rtl_dir.glob("*"):
                            _add(f)
            return out
        for pat in (sources_glob or "").split(","):
            pat = pat.strip().lstrip("/")
            if not pat:
                continue
            for f in PROJECT_ROOT.glob(pat):
                _add(f)
        return out

    @app.get("/api/hierarchy")
    async def api_hierarchy(top: str, sources: str = "", ip: str = "",
                            backend: str = ""):
        """Return the elaborated instance tree.

        Query params:
          - top      : top module name (required)
          - sources  : comma-separated globs of SV/V files (relative to PROJECT_ROOT)
          - ip       : shorthand — prefers `<ip>/list/*.f`, then `<ip>/rtl/*.sv`
          - backend  : 'dual' (default), 'pyslang', 'verilator', or 'slang'
        """
        try:
            mod = _load_sim_debug_elab()
            build_hierarchy_cached = mod.build_hierarchy_cached
            from atlas_sim_debug_top import resolve_sim_debug_top
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched", "sources_tried": sources or ip}, status_code=400)
        try:
            top_info = resolve_sim_debug_top(PROJECT_ROOT, ip=ip, requested_top=top)
            resolved_top = top_info.get("top") or top
            res = build_hierarchy_cached(backend, resolved_top, srcs)
            res = dict(res)
            res["requested_top"] = top
            res["resolved_top"] = resolved_top
            res["top_resolution"] = top_info
            res["sources"] = [p.relative_to(PROJECT_ROOT).as_posix() for p in srcs]
            return JSONResponse(res)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/trace")
    async def api_trace(signal: str, top: str = "", scope: str = "",
                        sources: str = "", ip: str = "",
                        backend: str = ""):
        """Trace driver/sinks for a signal. Top module resolution priority:
        explicit `top` > scope[0] > `ip` > signal[0]. Same source resolution
        as /api/hierarchy."""
        try:
            mod = _load_sim_debug_elab()
            trace_driver_cached = mod.trace_driver_cached
            from atlas_sim_debug_top import resolve_sim_debug_top
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched"}, status_code=400)
        top_info = resolve_sim_debug_top(
            PROJECT_ROOT,
            ip=ip,
            requested_top=top,
            vcd_scope=scope,
        )
        resolved_top = top_info.get("top") or signal.split(".", 1)[0]
        try:
            res = trace_driver_cached(backend, resolved_top, signal, srcs)
            res = dict(res)
            res["requested_top"] = top
            res["resolved_top"] = resolved_top
            res["top_resolution"] = top_info
            res["sources"] = [p.relative_to(PROJECT_ROOT).as_posix() for p in srcs]
            return JSONResponse(res)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── cocotb / TB env browsing — sim_debug "TB" tab ─────────────
    @app.get("/api/cocotb")
    async def api_cocotb(ip: str = ""):
        """Inspect a cocotb testbench environment under <ip>/cocotb/ or <ip>/tb/cocotb/.
        Returns a categorised file tree + parsed results.xml summary
        so the sim_debug UI can show 'TB' alongside the RTL hierarchy.
        """
        if not ip:
            return JSONResponse({"error": "ip parameter required"}, status_code=400)
        base = _safe(ip + "/cocotb")
        if base is None or not base.is_dir():
            base = _safe(ip + "/tb/cocotb")
        if base is None or not base.is_dir():
            return JSONResponse({"error": f"no cocotb dir under {ip}/ or {ip}/tb/", "exists": False})
        out = {
            "exists": True,
            "ip": ip,
            "tests":     [],   # tests/*.py
            "sequences": [],
            "env":       [],
            "agent":     [],
            "other":     [],   # Makefile, __init__.py, sim_dump.v, etc.
            "build":     [],   # sim_build/*
            "results":   None, # parsed results.xml
        }
        bucket_dirs = {
            "tests": "tests", "sequences": "sequences",
            "env": "env", "agent": "agent",
        }

        def _parse_py(p):
            """Static-analyse a cocotb Python file via the `ast` module.
            Returns { classes, tests, functions } with file:line locs.
            Same idea as pyslang for SV — no execution, fast, accurate."""
            import ast as _ast
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
                tree = _ast.parse(src, filename=str(p))
            except Exception as e:
                return {"error": str(e)}
            classes, tests, funcs = [], [], []
            for node in tree.body:
                if isinstance(node, _ast.ClassDef):
                    bases = [_ast.unparse(b) if hasattr(_ast, "unparse") else "" for b in node.bases]
                    methods = []
                    for sub in node.body:
                        if isinstance(sub, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                            methods.append({"name": sub.name, "line": sub.lineno, "is_async": isinstance(sub, _ast.AsyncFunctionDef)})
                    classes.append({"name": node.name, "line": node.lineno, "bases": bases, "methods": methods})
                elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    decorators = []
                    is_test = False
                    for d in node.decorator_list:
                        try:
                            ds = _ast.unparse(d) if hasattr(_ast, "unparse") else ""
                        except Exception:
                            ds = ""
                        decorators.append(ds)
                        if "cocotb.test" in ds:
                            is_test = True
                    entry = {
                        "name": node.name, "line": node.lineno,
                        "is_async": isinstance(node, _ast.AsyncFunctionDef),
                        "decorators": decorators,
                    }
                    (tests if is_test else funcs).append(entry)
            return {"classes": classes, "tests": tests, "functions": funcs}

        try:
            for sub in sorted(base.iterdir()):
                if sub.is_file():
                    rel = sub.relative_to(PROJECT_ROOT).as_posix()
                    entry = {"path": rel, "name": sub.name, "size": sub.stat().st_size}
                    if sub.suffix == ".py" and sub.name.startswith("test_"):
                        entry["parsed"] = _parse_py(sub)
                        out["tests"].append(entry)
                    else:
                        out["other"].append(entry)
                    continue
                if sub.is_dir():
                    bucket = next((k for k, v in bucket_dirs.items() if v == sub.name), None)
                    if bucket:
                        for f in sorted(sub.rglob("*.py")):
                            if "__pycache__" in f.parts or f.name == "__init__.py":
                                rel = f.relative_to(PROJECT_ROOT).as_posix()
                                if f.name == "__init__.py":
                                    out[bucket].append({"path": rel, "name": f.name, "size": f.stat().st_size, "parsed": None})
                                continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out[bucket].append({
                                "path": rel, "name": f.name,
                                "size": f.stat().st_size,
                                "parsed": _parse_py(f),
                            })
                    elif sub.name == "sim_build":
                        for f in sorted(sub.iterdir()):
                            if not f.is_file(): continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out["build"].append({"path": rel, "name": f.name, "size": f.stat().st_size})
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        # Build TB hierarchy: aggregate class definitions across files.
        tb_hier = {"agents": [], "envs": [], "scoreboards": [], "sequences": [], "tests": []}
        for bucket in ("agent", "env", "sequences", "tests"):
            for f in out.get(bucket, []):
                p = f.get("parsed") or {}
                for c in p.get("classes", []):
                    info = {"name": c["name"], "line": c["line"], "file": f["path"], "bases": c["bases"], "methods": [m["name"] for m in c["methods"]]}
                    bases_blob = " ".join(c["bases"]).lower()
                    if "scoreboard" in c["name"].lower() or "scoreboard" in bases_blob:
                        tb_hier["scoreboards"].append(info)
                    elif bucket == "agent" or "agent" in c["name"].lower() or "driver" in c["name"].lower() or "monitor" in c["name"].lower():
                        tb_hier["agents"].append(info)
                    elif bucket == "env" or "env" in c["name"].lower() or "tb" in c["name"].lower():
                        tb_hier["envs"].append(info)
                    elif bucket == "sequences" or "sequence" in c["name"].lower() or "seq" in c["name"].lower():
                        tb_hier["sequences"].append(info)
                for t in p.get("tests", []):
                    tb_hier["tests"].append({"name": t["name"], "line": t["line"], "file": f["path"], "decorators": t["decorators"]})
        out["tb_hierarchy"] = tb_hier

        # Parse results.xml (cocotb format) for test pass/fail summary.
        rx = base / "results.xml"
        if rx.is_file():
            try:
                import xml.etree.ElementTree as _ET
                root_xml = _ET.parse(str(rx)).getroot()
                cases = []
                pass_n = 0; fail_n = 0; skip_n = 0
                for tc in root_xml.iter("testcase"):
                    name = tc.attrib.get("name", "")
                    classname = tc.attrib.get("classname", "")
                    time_s = tc.attrib.get("time", "0")
                    sim_t  = tc.attrib.get("sim_time_ns", "")
                    file_attr = tc.attrib.get("file", "")
                    line_attr = tc.attrib.get("lineno", "0")
                    failure = tc.find("failure") is not None or tc.find("error") is not None
                    skipped = tc.find("skipped") is not None
                    if failure: fail_n += 1
                    elif skipped: skip_n += 1
                    else: pass_n += 1
                    rel_file = ""
                    if file_attr:
                        try:
                            fp = Path(file_attr)
                            if fp.is_absolute():
                                rel_file = str(fp.resolve().relative_to(PROJECT_ROOT))
                            else:
                                safe_fp = _safe(file_attr)
                                rel_file = safe_fp.relative_to(PROJECT_ROOT).as_posix() if safe_fp else file_attr
                        except Exception:
                            try:
                                rel_file = str(Path(file_attr).resolve().relative_to(PROJECT_ROOT))
                            except Exception:
                                rel_file = file_attr
                    cases.append({
                        "name": name, "classname": classname,
                        "time_s": float(time_s) if time_s else 0,
                        "sim_time_ns": sim_t,
                        "file": rel_file, "line": int(line_attr) if line_attr.isdigit() else 0,
                        "status": "fail" if failure else ("skip" if skipped else "pass"),
                    })
                out["results"] = {
                    "total": pass_n + fail_n + skip_n,
                    "pass": pass_n, "fail": fail_n, "skip": skip_n,
                    "cases": cases,
                    "mtime": rx.stat().st_mtime,
                }
            except Exception as e:
                out["results"] = {"error": f"parse failed: {e}"}
        return JSONResponse(out)

    @app.post("/api/todos/clear")
    async def api_todos_clear():
        """Wipe both the in-memory tracker and the on-disk file."""
        import os as _os
        _os.environ.pop("TODO_TEMPLATE_LOCK_ADDITIONS", None)
        _os.environ.pop("TODO_TEMPLATE_LOCK_NAME", None)
        try:
            import main as _main  # noqa: WPS433
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "todos"):
                tt.todos = []
                if hasattr(tt, "current_index"):
                    tt.current_index = -1
                if hasattr(tt, "save"):
                    try: tt.save()
                    except Exception: pass
        except Exception:
            pass
        # Remove the on-disk file too so the legacy fallback can't
        # re-surface old todos.
        try:
            from pathlib import Path as _P
            for cand in ("current_todos.json",
                         str(_P.home() / ".common_ai_agent" / "current_todos.json")):
                p = _P(cand)
                if p.exists():
                    try: p.unlink()
                    except Exception: pass
        except Exception:
            pass
        return JSONResponse({"ok": True})

    def _tracker_stage(name: str) -> str:
        # `derive_rtl_todos.py` writes tracker name as "<ip>-rtl"; other
        # generators follow the same `<ip>-<stage>` convention so we can
        # cheaply read the trailing stage off the name.
        s = (name or "").rsplit("-", 1)
        return s[-1] if len(s) == 2 else ""

    def _active_workflow_stage() -> str:
        sess = _active_session_value() or ""
        parts = [p for p in sess.split("/") if p]
        if len(parts) < 3:
            return ""
        wf = parts[-1]
        return wf.split("-")[0] if "-" in wf else wf

    def _gate_for_workflow(d: dict | None) -> dict | None:
        # Tracker carries an SSOT-derived workflow stage in its name.
        # When the user is viewing a different workflow we hide the
        # tracker so a previous /gen-rtl run doesn't keep showing 20
        # auto-generated rtl-gen TODOs in sim_debug or other workflows.
        if not isinstance(d, dict):
            return d
        ts = _tracker_stage(d.get("name", ""))
        ws = _active_workflow_stage()
        if ts and ws and ts != ws:
            return {"todos": [], "auto_hidden": True,
                    "reason": f"tracker '{d.get('name')}' is for {ts}, active workflow is {ws}"}
        return d

    @app.get("/api/todos")
    async def api_todos():
        # Prefer the live tracker the agent is mutating in main.py — that's
        # the only way to see in-progress changes before they hit disk. Fall
        # back to the on-disk file if main hasn't initialized one yet. When
        # ATLAS has an active namespaced session, that session's todo.json is
        # the source of truth; a process-global live tracker may still point at
        # an older HOME-level current_todos.json from another IP.
        candidates: list[Path] = []
        active_session = normalize_session_name(_active_session_value())
        active_todo_path = (
            PROJECT_ROOT / ".session" / active_session / "todo.json"
            if active_session else None
        )

        def _same_path(left: Path | None, right: Path | None) -> bool:
            if left is None or right is None:
                return False
            try:
                return left.expanduser().resolve() == right.expanduser().resolve()
            except Exception:
                return str(left) == str(right)

        try:
            import main as _main  # noqa: WPS433
            live = getattr(_main, "todo_tracker", None)
            live_persist_path = (
                getattr(live, "_persist_path", None)
                if live is not None
                else None
            )
            live_path = Path(live_persist_path) if live_persist_path else None
            if live is not None and getattr(live, "todos", None):
                if (
                    not active_todo_path
                    or not active_todo_path.exists()
                    or _same_path(live_path, active_todo_path)
                ):
                    return JSONResponse(_gate_for_workflow(live.to_dict()))
            if active_todo_path:
                candidates.append(active_todo_path)
            if live_path:
                candidates.append(live_path)
        except Exception:
            pass
        # On-disk fallback. Two persistence paths exist in this repo:
        #   1. <PROJECT_ROOT>/current_todos.json    (relative TODO_FILE,
        #                                            agent's actual writes)
        #   2. ~/.common_ai_agent/current_todos.json (HOME default for
        #                                            stand-alone scripts)
        # When `import config` succeeds at module load, TodoTracker module
        # caches TODO_FILE as Path("current_todos.json") — relative — and
        # whether `.exists()` resolves depends on the server's cwd at
        # request time. Resolve them *both* explicitly so the panel never
        # silently falls through to "no todos" when the file is right
        # there in PROJECT_ROOT.
        try:
            import json as _json
            from lib.todo_tracker import TodoTracker
            try:
                import config as _cfg
                cfg_todo = Path(str(getattr(_cfg, "TODO_FILE", "current_todos.json")))
                candidates.append(cfg_todo if cfg_todo.is_absolute() else PROJECT_ROOT / cfg_todo)
            except Exception:
                pass
            candidates.extend([
                PROJECT_ROOT / "current_todos.json",
                Path.cwd() / "current_todos.json",
                Path.home() / ".common_ai_agent" / "current_todos.json",
            ])
            deduped: list[Path] = []
            seen_paths: set[str] = set()
            for cand in candidates:
                try:
                    key = str(cand.expanduser().resolve())
                except Exception:
                    key = str(cand)
                if key not in seen_paths:
                    seen_paths.add(key)
                    deduped.append(cand)
            picked = next((p for p in deduped if p.exists()), None)
            if picked is None:
                return JSONResponse({"todos": []})
            raw = None
            try:
                raw = _json.loads(picked.read_text(encoding="utf-8"))
            except Exception:
                raw = None
            tt = TodoTracker.load(picked)
            d = tt.to_dict()
            if d.get("todos"):
                return JSONResponse(_gate_for_workflow(d))
            d = _atlas_todo_payload_from_raw(raw, d)
            return JSONResponse(_gate_for_workflow(d))
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/commands")
    async def api_commands():
        """List every slash command currently registered, including the
        workspace-specific ones (e.g. /grill-me, /to-ssot for ssot-gen).
        """
        try:
            from core.slash_commands import get_registry as _gr
            reg = _gr()
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        # The registry stores commands in an internal dict; read it
        # defensively through whatever public surface is available.
        cmds = []
        seen = set()
        for attr in ("commands", "_commands"):
            entries = getattr(reg, attr, None)
            if isinstance(entries, dict):
                for name, spec in entries.items():
                    canonical = spec.get("name", name) if isinstance(spec, dict) else name
                    if canonical in seen:
                        continue
                    seen.add(canonical)
                    if isinstance(spec, dict):
                        cmds.append({
                            "cmd":     "/" + canonical,
                            "name":    canonical,
                            "aliases": spec.get("aliases", []) or [],
                            "hint":    spec.get("description", "") or "",
                            "usage":   spec.get("usage", f"/{canonical}"),
                        })
                break
        cmds.sort(key=lambda c: c["name"])
        return JSONResponse({"commands": cmds})

    @app.get("/api/input-history")
    async def api_input_history(limit: int = 200):
        try:
            history = _read_input_history(limit)
            return JSONResponse({
                "history": history,
                "path": _relative_project_path(_input_history_path()),
            })
        except Exception as e:
            return JSONResponse({"error": str(e), "history": []}, status_code=500)

    @app.post("/api/input-history")
    async def api_append_input_history(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        text = str(payload.get("text") or "").strip()
        if not text:
            return JSONResponse({"ok": True, "stored": False})
        try:
            _append_input_history(text)
            return JSONResponse({"ok": True, "stored": True})
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    # SSOT routes registered via register_ssot_routes() below (see atlas_api_ssot.py).
    # /api/session/activate registered via register_sessions_routes() (see atlas_api_sessions.py).

    # POST /api/ssot/qa/answer registered via register_ssot_routes() (see atlas_api_ssot.py).

    @app.get("/api/soc")
    def api_soc(scope: str = "", ip: str = ""):
        """Build a SoC-Architect-friendly view of the project's IPs.

        Two-tier source-of-truth model:
          1. SoC-level SSOT  — `<project_root>/soc.ssot.yaml`
             Owned by the Architect supervisor. Lists clusters, IP
             instances (with overrides + addresses), connections, and
             generators. When present, drives the architect view.
          2. Per-IP leaf SSOT — `<ip>/yaml/<ip>.ssot.yaml`
             Each instance points to its leaf SSOT for parameters,
             busInterfaces, model.ports → clocks/resets, memoryMap.

        When the SoC SSOT is missing we fall back to the directory walk
        (every `*.ssot.yaml` under the project becomes a module under a
        single `ips` cluster) so existing projects keep working without
        an explicit SoC file.

        Status (ssot/rtl/sim) is derived from filesystem presence:
          ssot = ok  if yaml file parses
          rtl  = ok  if <ip>/rtl/*.sv exists, partial if dir exists empty,
                     pending otherwise
          sim  = ok  if <ip>/sim/ has any *.log or *.vcd, pending otherwise
        Used by the Atlas Architect screen to replace the mock SOC.
        """
        try:
            try: import yaml as _yaml  # type: ignore
            except Exception: _yaml = None

            def _kind_for(name: str) -> str:
                """Infer module kind from its name. Used as a fallback
                when no cluster.role is available (dir-walk mode) or
                when the cluster lists a generic role. Heuristic patterns
                broaden to catch real-world IP names: cortexa15, riscv,
                cci550, ccn508, nic400, etc."""
                n = (name or "").lower()
                if any(s in n for s in ("cpu", "core", "rv", "cortex", "riscv",
                                         "arm", "neoverse", "amba_a", "hart")): return "cpu"
                if any(s in n for s in ("mem", "ram", "ddr", "cache", "sram",
                                         "rom", "flash", "ocm")): return "mem"
                if any(s in n for s in ("noc", "bus", "axi", "apb", "ahb", "xbar",
                                         "cci", "ccn", "nic", "nip", "interconnect",
                                         "crossbar", "smmu", "iommu")): return "bus"
                if any(s in n for s in ("phy", "ana", "pll", "ldo", "vco",
                                         "adc", "dac", "afe", "rf")): return "analog"
                return "periph"

            # Cluster role string from soc.ssot.yaml → module kind. The
            # role is more authoritative than the name heuristic; we let
            # it win when present so cortexa15_0 under a CPU cluster is
            # always classified `cpu` regardless of name.
            _ROLE_TO_KIND = {
                "CPU": "cpu", "MEM": "mem", "BUS": "bus",
                "PERIPH": "periph", "ANALOG": "analog",
                "INTERCONNECT": "bus", "FABRIC": "bus", "NOC": "bus",
                "PERIPHERAL": "periph", "MISC": "periph",
            }
            def _kind_from_role(role):
                if not isinstance(role, str): return None
                return _ROLE_TO_KIND.get(role.strip().upper())

            # YAML hex literals like `0x8000_0000` are parsed by PyYAML
            # to a Python int. Re-format as a hex string with 4-digit
            # underscore groups so the architect UI shows the canonical
            # SoC notation (`0x8000_0000`, `0x4000_2000`) instead of a
            # raw decimal (`2147483648`).
            def _hex_addr(v):
                if v is None: return ""
                if isinstance(v, int):
                    h = f"{v:x}"
                    # Zero-pad to at least 8 hex digits (32-bit address
                    # convention) so 0x0800_0000 doesn't collapse to
                    # 0x800_0000 after grouping. Larger values use the
                    # next multiple of 4.
                    target = max(8, ((len(h) - 1) // 4 + 1) * 4)
                    h = h.zfill(target)
                    if len(h) > 4:
                        rev = h[::-1]
                        groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                        h = "_".join(groups)[::-1]
                    return f"0x{h}"
                # Already a string (might or might not be hex-prefixed).
                s = str(v).strip()
                if s.startswith("0x") or s.startswith("0X"): return s
                # Try parse as int — covers decimal-string cases.
                try:
                    return _hex_addr(int(s))
                except ValueError:
                    return s

            def _has_live_content(value: Any) -> bool:
                if value is None:
                    return False
                if isinstance(value, str):
                    text = value.strip()
                    return bool(text) and text.upper() not in {"TBD", "TODO", "NONE", "NULL"}
                if isinstance(value, (list, tuple, set)):
                    return any(_has_live_content(v) for v in value)
                if isinstance(value, dict):
                    return any(_has_live_content(v) for v in value.values())
                return True

            def _contains_tbd(value: Any) -> bool:
                if isinstance(value, str):
                    return bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", value, re.I))
                if isinstance(value, list):
                    return any(_contains_tbd(v) for v in value)
                if isinstance(value, dict):
                    return any(_contains_tbd(v) for v in value.values())
                return False

            _SSOT_SECTIONS = [
                ("top_module", "top module"),
                ("sub_modules", "sub modules"),
                ("parameters", "parameters"),
                ("io_list", "I/O"),
                ("features", "features"),
                ("dataflow", "dataflow"),
                ("function_model", "function model"),
                ("cycle_model", "cycle model"),
                ("clock_reset_domains", "clock/reset"),
                ("cdc_requirements", "CDC"),
                ("rdc_requirements", "RDC"),
                ("registers", "registers"),
                ("memory", "memory"),
                ("interrupts", "interrupts"),
                ("fsm", "FSM"),
                ("timing", "timing"),
                ("power", "power"),
                ("security", "security"),
                ("error_handling", "errors"),
                ("debug_observability", "debug"),
                ("integration", "integration"),
                ("dft", "DFT"),
                ("synthesis", "synthesis"),
                ("coding_rules", "coding rules"),
                ("reuse_modules", "reuse modules"),
                ("custom", "custom"),
                ("dir_structure", "dir structure"),
                ("filelist", "filelist"),
                ("test_requirements", "DV plan"),
                ("quality_gates", "quality gates"),
                ("traceability", "traceability"),
                ("workflow_todos", "workflow TODOs"),
                ("generation_flow", "generation flow"),
            ]
            _SSOT_SECTION_ALIASES = {
                "clock_reset_domains": ["clock_reset_domains", "reset_behavior", "clocks", "resets"],
                "function_model": ["function_model", "functional_model", "behavior_model", "reference_model"],
                "cycle_model": ["cycle_model", "cycle_accurate_model", "timing_model", "pipeline_model"],
                "debug_observability": ["debug_observability", "debug", "observability", "trace_debug"],
                "dft": ["dft", "dfd", "testability"],
                "synthesis": ["synthesis", "implementation_constraints", "physical_constraints"],
                "coding_rules": ["coding_rules", "constraints"],
                "test_requirements": ["test_requirements", "verification"],
                "quality_gates": ["quality_gates", "acceptance_criteria", "pass_criteria", "signoff_criteria"],
                "workflow_todos": ["workflow_todos", "next_step_todos"],
            }

            def _pct(done: int, total: int) -> int:
                return int(round((100.0 * done / total))) if total else 0

            _SSOT_EMPTY_IS_DECLARED = {
                "reuse_modules",
            }

            def _is_non_empty_mapping(value: Any) -> bool:
                return isinstance(value, dict) and bool(value)

            def _is_non_empty_list(value: Any) -> bool:
                return isinstance(value, list) and bool(value)

            def _has_required_fields(value: Any, fields: list[str]) -> bool:
                if not isinstance(value, dict):
                    return False
                for field in fields:
                    item = value.get(field)
                    if item is None or item == "" or item == [] or item == {}:
                        return False
                return True

            def _scenario_complete(item: Any) -> bool:
                return _has_required_fields(item, ["id", "name", "stimulus", "expected", "checker", "coverage"])

            def _gate_complete(item: Any) -> bool:
                return _has_required_fields(item, ["pass", "evidence"])

            def _ssot_section_complete(key: str, value: Any, present: bool) -> bool:
                if not present or _contains_tbd(value):
                    return False
                if key in _SSOT_EMPTY_IS_DECLARED and isinstance(value, (list, tuple, set, dict)):
                    return True
                if key == "function_model":
                    if not isinstance(value, dict):
                        return False
                    state_variables = value.get("state_variables") if isinstance(value.get("state_variables"), list) else []
                    transactions = value.get("transactions") if isinstance(value.get("transactions"), list) else []
                    invariants = value.get("invariants") if isinstance(value.get("invariants"), list) else []
                    return (
                        _has_required_fields(value, ["state_variables", "transactions", "invariants"])
                        and _is_non_empty_list(state_variables)
                        and _is_non_empty_list(transactions)
                        and _is_non_empty_list(invariants)
                        and all(
                            _has_required_fields(tx, ["id", "name", "preconditions", "outputs"])
                            and bool(tx.get("side_effects") or tx.get("error_cases"))
                            for tx in transactions
                        )
                    )
                if key == "cycle_model":
                    return (
                        _has_required_fields(value, ["clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"])
                        and _is_non_empty_list(value.get("handshake_rules"))
                        and _is_non_empty_list(value.get("pipeline"))
                        and _is_non_empty_list(value.get("ordering"))
                    )
                if key == "timing":
                    return _has_required_fields(value, ["target_clocks", "latency_budget"]) and _is_non_empty_list(value.get("target_clocks"))
                if key == "power":
                    return _has_required_fields(value, ["domains", "power_states"]) and _is_non_empty_list(value.get("domains"))
                if key == "security":
                    return (
                        _has_required_fields(value, ["classification", "assets", "threat_model"])
                        and _is_non_empty_list(value.get("assets"))
                        and _is_non_empty_list(value.get("threat_model"))
                    )
                if key == "error_handling":
                    return _has_required_fields(value, ["error_sources", "propagation", "recovery"]) and _is_non_empty_list(value.get("error_sources"))
                if key == "debug_observability":
                    return _has_required_fields(value, ["waveform_must_probe", "trace_events"]) and _is_non_empty_list(value.get("waveform_must_probe"))
                if key == "integration":
                    return _has_required_fields(value, ["bus_attachment", "dependencies"])
                if key == "dft":
                    return _has_required_fields(value, ["scan_required", "controllability", "observability"])
                if key == "synthesis":
                    return _has_required_fields(value, ["dialect", "constraints", "required_outputs"])
                if key == "test_requirements":
                    scenarios = value.get("scenarios") if isinstance(value, dict) else None
                    return (
                        _has_required_fields(value, ["scenarios", "scoreboard_checks", "coverage_goals"])
                        and _is_non_empty_list(scenarios)
                        and all(_scenario_complete(item) for item in scenarios)
                    )
                if key == "quality_gates":
                    if not _is_non_empty_mapping(value):
                        return False
                    return all(_gate_complete(value.get(gate)) for gate in ["ssot", "rtl", "dv", "coverage", "eda", "signoff"])
                if key == "traceability":
                    return _has_required_fields(value, ["yaml_to_output"]) and _is_non_empty_list(value.get("yaml_to_output"))
                return _has_live_content(value)

            def _count_list(value: Any) -> int:
                return len(value) if isinstance(value, list) else 0

            def _ssot_metrics(doc: dict) -> dict:
                io_list = doc.get("io_list") if isinstance(doc, dict) else {}
                interfaces = io_list.get("interfaces") if isinstance(io_list, dict) else []
                ports = 0
                if isinstance(interfaces, list):
                    for iface in interfaces:
                        if isinstance(iface, dict) and isinstance(iface.get("ports"), list):
                            ports += len(iface["ports"])
                registers = doc.get("registers") if isinstance(doc, dict) else {}
                register_list = registers.get("register_list") if isinstance(registers, dict) else []
                memory = doc.get("memory") if isinstance(doc, dict) else {}
                memory_instances = memory.get("instances") if isinstance(memory, dict) else []
                fsm = doc.get("fsm") if isinstance(doc, dict) else {}
                fsm_states = 0
                fsm_transitions = 0
                if isinstance(fsm, dict):
                    for item in fsm.values():
                        if isinstance(item, dict):
                            fsm_states += _count_list(item.get("states"))
                            fsm_transitions += _count_list(item.get("transitions"))
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                function_model = doc.get("function_model") if isinstance(doc, dict) else {}
                fm_transactions = function_model.get("transactions") if isinstance(function_model, dict) else []
                fm_state = function_model.get("state_variables") if isinstance(function_model, dict) else []
                cycle_model = doc.get("cycle_model") if isinstance(doc, dict) else {}
                cm_handshakes = cycle_model.get("handshake_rules") if isinstance(cycle_model, dict) else []
                cm_pipeline = cycle_model.get("pipeline") if isinstance(cycle_model, dict) else []
                quality_gates = doc.get("quality_gates") if isinstance(doc, dict) else {}
                timing = doc.get("timing") if isinstance(doc, dict) else {}
                security = doc.get("security") if isinstance(doc, dict) else {}
                error_handling = doc.get("error_handling") if isinstance(doc, dict) else {}
                submods = doc.get("sub_modules") if isinstance(doc, dict) else []
                return {
                    "submodules": _count_list(submods),
                    "parameters": _count_list(doc.get("parameters") if isinstance(doc, dict) else []),
                    "interfaces": _count_list(interfaces),
                    "ports": ports,
                    "registers": _count_list(register_list),
                    "memories": _count_list(memory_instances),
                    "fsm_states": fsm_states,
                    "fsm_transitions": fsm_transitions,
                    "dv_scenarios": _count_list(scenarios),
                    "function_transactions": _count_list(fm_transactions),
                    "function_state_variables": _count_list(fm_state),
                    "cycle_handshake_rules": _count_list(cm_handshakes),
                    "cycle_pipeline_stages": _count_list(cm_pipeline),
                    "timing_clocks": _count_list(timing.get("target_clocks") if isinstance(timing, dict) else []),
                    "security_assets": _count_list(security.get("assets") if isinstance(security, dict) else []),
                    "error_sources": _count_list(error_handling.get("error_sources") if isinstance(error_handling, dict) else []),
                    "scoreboard_checks": tr.get("scoreboard_checks") if isinstance(tr, dict) else None,
                    "coverage_goals": len(coverage_goals) if isinstance(coverage_goals, dict) else 0,
                    "quality_gates": len(quality_gates) if isinstance(quality_gates, dict) else 0,
                }

            def _ssot_progress(doc: dict) -> dict:
                sections = []
                canonical_keys = {k for k, _ in _SSOT_SECTIONS}
                section_defs = list(_SSOT_SECTIONS)
                if isinstance(doc, dict) and doc:
                    known = set(canonical_keys)
                    known.update(a for aliases in _SSOT_SECTION_ALIASES.values() for a in aliases)
                    for key in doc.keys():
                        if key not in known:
                            section_defs.append((str(key), str(key).replace("_", " ")))
                for key, label in section_defs:
                    keys = _SSOT_SECTION_ALIASES.get(key, [key])
                    actual_key = next((k for k in keys if isinstance(doc, dict) and k in doc), key)
                    val = doc.get(actual_key) if isinstance(doc, dict) else None
                    present = actual_key in doc if isinstance(doc, dict) else False
                    complete = _ssot_section_complete(key, val, present)
                    status = "approved" if complete else ("incomplete" if present else "missing")
                    sections.append({
                        "key": key,
                        "actual_key": actual_key if present else "",
                        "label": label,
                        "status": status,
                        "canonical": key in canonical_keys,
                    })
                approved = sum(1 for s in sections if s.get("canonical") and s["status"] == "approved")
                total = sum(1 for s in sections if s.get("canonical"))
                return {
                    "approved": approved,
                    "total": total,
                    "pct": _pct(approved, total),
                    "sections": sections,
                    "metrics": _ssot_metrics(doc if isinstance(doc, dict) else {}),
                }

            def _extract_expected_rtl(doc: dict) -> list[dict[str, str]]:
                expected: list[dict[str, str]] = []
                seen: set[str] = set()
                subs = doc.get("sub_modules") if isinstance(doc, dict) else []
                if isinstance(subs, list):
                    for idx, item in enumerate(subs):
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name") or f"module_{idx}")
                        file_name = str(item.get("file") or "").strip()
                        if file_name and file_name not in seen:
                            expected.append({"name": name, "file": file_name})
                            seen.add(file_name)
                fl = doc.get("filelist") if isinstance(doc, dict) else {}
                rtl_list = fl.get("rtl") if isinstance(fl, dict) else []
                if isinstance(rtl_list, list):
                    for raw in rtl_list:
                        file_name = str(raw or "").strip()
                        if not file_name or file_name in seen:
                            continue
                        expected.append({"name": Path(file_name).stem, "file": file_name})
                        seen.add(file_name)
                return expected

            def _resolve_ip_file(ip_dir: Path, rel: str) -> Path:
                p = Path(rel)
                if p.is_absolute():
                    return p
                cand = ip_dir / rel
                if cand.is_file():
                    return cand
                return PROJECT_ROOT / rel

            def _filelist_entries(ip_dir: Path) -> tuple[list[str], Path | None]:
                f = ip_dir / "list" / f"{ip_dir.name}.f"
                if not f.is_file():
                    return [], None
                entries: list[str] = []
                try:
                    for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
                        line = raw.split("//", 1)[0].strip()
                        if line and line.endswith((".v", ".sv", ".vh", ".svh")):
                            entries.append(line)
                except OSError:
                    pass
                return entries, f

            def _rtl_progress(ip_dir: Path, doc: dict) -> dict:
                if _shared_rtl_manifest_progress is not None:
                    try:
                        return _shared_rtl_manifest_progress(ip_dir, doc if isinstance(doc, dict) else {})
                    except Exception:
                        pass
                blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
                blocked_doc: dict[str, Any] = {}
                if blocked_path.is_file():
                    try:
                        blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                    except Exception:
                        blocked_doc = {
                            "status": "blocked",
                            "reason": "rtl_blocked.json is present but could not be parsed",
                        }
                entries, fpath = _filelist_entries(ip_dir)
                entry_set = set(entries)
                top_doc = doc.get("top_module") if isinstance(doc, dict) else {}
                top_name = ""
                if isinstance(top_doc, dict):
                    top_name = str(top_doc.get("name") or "").strip()
                if not top_name:
                    top_name = ip_dir.name
                listed_text = ""
                listed_sources: list[Path] = []
                for ent in entries:
                    src = _resolve_ip_file(ip_dir, ent)
                    if src.is_file():
                        listed_sources.append(src)
                        try:
                            listed_text += "\n" + src.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            pass
                modules = []
                expected = _extract_expected_rtl(doc)
                if not expected:
                    rtl_dir = ip_dir / "rtl"
                    expected = [
                        {"name": p.stem, "file": p.relative_to(ip_dir).as_posix()}
                        for p in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
                    ] if rtl_dir.is_dir() else []
                for item in expected:
                    rel = item["file"]
                    path = _resolve_ip_file(ip_dir, rel)
                    resolved_rel = rel
                    manifest_mismatch = False
                    # SSOTs often describe the integration wrapper as
                    # `<ip>_top.sv` while the real top module is `<ip>`.
                    # Verilator's DECLFILENAME rule requires the file stem
                    # to match the module name, so accept `rtl/<top>.sv`
                    # when the canonical filelist has already been repaired.
                    if (
                        not path.is_file()
                        and top_name
                        and item.get("name") in {f"{top_name}_top", "top", "wrapper"}
                    ):
                        alias_rel = f"rtl/{top_name}.sv"
                        alias_path = _resolve_ip_file(ip_dir, alias_rel)
                        if alias_rel in entry_set and alias_path.is_file():
                            path = alias_path
                            resolved_rel = alias_rel
                            manifest_mismatch = True
                    exists = path.is_file()
                    size = path.stat().st_size if exists else 0
                    text = ""
                    if exists:
                        try:
                            text = path.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            text = ""
                    scaffold_only = bool(
                        re.search(r"Auto-generated manifest submodule", text, re.I)
                        or re.search(r"\balive_q\b", text)
                        or re.search(r"\bheartbeat_q\b", text)
                    )
                    placeholder = bool(re.search(r"\b(TBD|TODO:|FIXME|HACK)\b", text, re.I)) or scaffold_only
                    listed = rel in entry_set or resolved_rel in entry_set
                    if exists:
                        try:
                            listed = listed or path.relative_to(PROJECT_ROOT).as_posix() in entry_set
                        except Exception:
                            pass
                    include_header = False
                    if exists and not listed and path.suffix in {".sv", ".svh", ".vh"}:
                        include_name = path.name
                        include_header = (
                            bool(re.search(rf'`include\s+"{re.escape(include_name)}"', listed_text))
                            or path.stem.endswith("_pkg")
                            or "include header" in text[:2000].lower()
                        )
                    approved = exists and size >= 200 and (listed or include_header) and not placeholder
                    modules.append({
                        "name": item["name"],
                        "file": rel,
                        "resolved_file": resolved_rel,
                        "manifest_mismatch": manifest_mismatch or (resolved_rel != rel),
                        "status": "approved" if approved else ("partial" if exists else "missing"),
                        "exists": exists,
                        "listed": listed,
                        "include_header": include_header,
                        "bytes": size,
                        "placeholder": placeholder,
                        "scaffold_only": scaffold_only,
                    })
                approved = sum(1 for m in modules if m["status"] == "approved")
                mismatches = [m for m in modules if m.get("manifest_mismatch")]
                return {
                    "approved": approved,
                    "total": len(modules),
                    "pct": _pct(approved, len(modules)),
                    "filelist": fpath.relative_to(PROJECT_ROOT).as_posix() if fpath else "",
                    "manifest_mismatches": len(mismatches),
                    "manifest_mismatch_details": mismatches,
                    "blocked": bool(blocked_doc),
                    "blocker": str(blocked_doc.get("reason") or "") if blocked_doc else "",
                    "blocker_source": blocked_path.relative_to(PROJECT_ROOT).as_posix() if blocked_doc else "",
                    "questions": blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else [],
                    "next_action": str(blocked_doc.get("next_action") or "") if blocked_doc else "",
                    "modules": modules,
                }

            def _compile_progress(ip_dir: Path) -> dict:
                report_path = ip_dir / "rtl" / "rtl_compile.json"
                if not report_path.is_file():
                    return {
                        "status": "unknown",
                        "errors": 0,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": "",
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                except Exception:
                    return {
                        "status": "fail",
                        "errors": 1,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": report_path.relative_to(PROJECT_ROOT).as_posix(),
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                if report.get("dut_only") is not True or str(report.get("type") or "") != "rtl_compile":
                    status = "fail"
                elif report.get("passed") is True:
                    status = "pass"
                else:
                    status = "fail"
                return {
                    "status": status,
                    "errors": int(report.get("errors") or 0),
                    "diagnostics": int(report.get("diagnostics") or report.get("warnings") or 0),
                    "style_violations": int(report.get("style_violations") or 0),
                    "style_violation_details": report.get("style_violation_details") or [],
                    "returncode": int(report.get("returncode") or 0),
                    "source": report_path.relative_to(PROJECT_ROOT).as_posix(),
                    "tool": str(report.get("tool") or ""),
                    "command": str(report.get("command") or ""),
                    "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json; warnings, Icarus sorry diagnostics, and procedural parameterized part-selects are blockers",
                }

            def _waived_warning_kinds(waivers: list[str]) -> set[str]:
                kinds: set[str] = set()
                for raw in waivers:
                    for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", str(raw).upper()):
                        kinds.add(token)
                return kinds

            def _count_log_diagnostics(text: str, waivers: list[str] | None = None) -> dict:
                summary = re.search(
                    r"%Error:\s+Exiting due to\s+(\d+)\s+error\(s\),\s+(\d+)\s+warning\(s\)",
                    text,
                    re.I,
                )
                if summary:
                    return {
                        "errors": int(summary.group(1)),
                        "warnings": int(summary.group(2)),
                        "waived_warnings": 0,
                    }
                waived = _waived_warning_kinds(waivers or [])
                lines = text.splitlines()
                error_re = re.compile(r"(%ERROR\b|(^|\s)(ERROR|FATAL)(:|-)|\b\d+\s+ERROR\(S\))", re.I)
                errors = 0
                warnings = 0
                waived_warnings = 0
                for line in lines:
                    line_u = line.upper()
                    if re.search(r"%ERROR:\s+EXITING DUE TO \d+ WARNING", line_u):
                        continue
                    warning_kind = ""
                    m = re.search(r"%WARNING-([A-Z0-9_]+)", line_u)
                    if m:
                        warning_kind = m.group(1)
                    is_waived_warning = bool(warning_kind and warning_kind in waived)
                    is_warning_line = bool(
                        warning_kind
                        or re.search(r":\s*warning:", line, re.I)
                        or re.search(r"\bsorry:", line, re.I)
                    )
                    if is_warning_line and not error_re.search(line):
                        if is_waived_warning:
                            waived_warnings += 1
                        else:
                            warnings += 1
                    elif error_re.search(line):
                        errors += 1
                return {"errors": errors, "warnings": warnings, "waived_warnings": waived_warnings}

            def _lint_progress(ip_dir: Path, doc: dict) -> dict:
                lint_dir = ip_dir / "lint"
                latest: Path | None = None
                latest_mtime = -1.0
                diag = {"errors": 0, "warnings": 0, "waived_warnings": 0, "suppression_violations": 0}
                source_kind = ""
                command = ""
                tool = ""
                coding_rules = doc.get("coding_rules") if isinstance(doc, dict) else {}
                waivers = []
                if isinstance(coding_rules, dict):
                    raw_waivers = coding_rules.get("lint_waivers") or coding_rules.get("waivers") or []
                    if isinstance(raw_waivers, list):
                        waivers = [str(w) for w in raw_waivers]

                def _canonical_report_ok(report: dict) -> bool:
                    if not isinstance(report, dict):
                        return False
                    if report.get("dut_only") is not True:
                        return False
                    scope = str(report.get("scope") or report.get("type") or "").lower()
                    if scope not in {"dut", "rtl", "dut_lint", "rtl_lint"}:
                        return False
                    cmd = str(report.get("command") or "").lower()
                    if "cocotb" in cmd or "pytest" in cmd or "vvp" in cmd:
                        return False
                    return any(tok in cmd for tok in ("verilator", "pyslang", "iverilog", "slang"))

                def _reject_sim_log(text_l: str, pth: Path) -> bool:
                    parts_l = {part.lower() for part in pth.parts}
                    if {"tb", "cocotb", "sim", "sim_build"} & parts_l:
                        return True
                    sim_markers = (
                        "cocotb", "pytest", "results.xml", "module not found",
                        "vvp ", "make sim", "sim_build", "test_runner.py",
                    )
                    return any(marker in text_l for marker in sim_markers)

                report_candidates: list[Path] = []
                if lint_dir.is_dir():
                    report_candidates.extend(lint_dir.rglob("dut_lint.json"))
                    report_candidates.extend(lint_dir.rglob("rtl_lint.json"))
                    report_candidates.extend(lint_dir.rglob("*lint*.json"))
                for pth in report_candidates:
                    try:
                        report = json.loads(pth.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not _canonical_report_ok(report):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime <= latest_mtime:
                        continue
                    latest = pth
                    latest_mtime = mtime
                    diag = {
                        "errors": int(report.get("errors") or 0),
                        "warnings": int(report.get("warnings") or 0),
                        "waived_warnings": int(report.get("waived_warnings") or 0),
                        "suppression_violations": int(report.get("suppression_violation_count") or 0),
                    }
                    command = str(report.get("command") or "")
                    tool = str(report.get("tool") or "")
                    source_kind = "canonical-dut-lint-json"

                text_candidates: list[Path] = []
                if lint_dir.is_dir():
                    for suffix in ("*.log", "*.txt", "*.out"):
                        text_candidates.extend(lint_dir.rglob(suffix))
                for pth in text_candidates:
                    name_l = pth.name.lower()
                    if name_l.startswith("sim_report") or name_l.startswith("coverage_report") or "results" in name_l:
                        continue
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    text_l = text.lower()
                    if _reject_sim_log(text_l, pth):
                        continue
                    if not any(tok in text_l for tok in ("verilator", "pyslang", "iverilog", "slang", "lint-only")):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime > latest_mtime:
                        latest = pth
                        latest_mtime = mtime
                        diag = _count_log_diagnostics(text, waivers)
                        command = ""
                        tool = ""
                        source_kind = "lint-dir-text"
                warning_budget = 0
                status = "unknown" if latest is None else (
                    "pass" if (
                        diag["errors"] == 0
                        and diag["warnings"] == 0
                        and diag.get("suppression_violations", 0) == 0
                    ) else "fail"
                )
                return {
                    "status": status,
                    "errors": diag["errors"],
                    "warnings": diag["warnings"],
                    "suppression_violations": diag.get("suppression_violations", 0),
                    "warning_budget": warning_budget,
                    "waivers": waivers,
                    "source": latest.relative_to(PROJECT_ROOT).as_posix() if latest else "",
                    "source_kind": source_kind,
                    "tool": tool,
                    "command": command,
                    "criteria": "DUT RTL-only lint report from <ip>/lint; sim/cocotb/root cmd_output logs are not valid lint evidence",
                }

            def _sim_progress(ip_dir: Path, doc: dict) -> dict:
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                scenario_count = len(scenarios) if isinstance(scenarios, list) else 0
                scoreboard = tr.get("scoreboard_checks") if isinstance(tr, dict) else None
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                coverage_goal_count = len(coverage_goals) if isinstance(coverage_goals, dict) else 0
                scenario_rows = []
                if isinstance(scenarios, list):
                    for sc in scenarios:
                        if isinstance(sc, dict):
                            scenario_rows.append({
                                "id": str(sc.get("id") or ""),
                                "name": str(sc.get("name") or sc.get("title") or ""),
                                "expected": str(sc.get("expected") or ""),
                                "status": "pending",
                            })
                tb_dir = ip_dir / "tb"
                tests = []
                tb_text = ""
                if tb_dir.is_dir():
                    for pth in tb_dir.rglob("test*.py"):
                        try:
                            text = pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                        tb_text += "\n" + text
                        tests.extend(re.findall(r"@cocotb\.test|def\s+test_", text))
                    for pth in list(tb_dir.rglob("*.sv")) + list(tb_dir.rglob("*.v")):
                        try:
                            tb_text += "\n" + pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                for row in scenario_rows:
                    sid = row.get("id") or ""
                    if sid and re.search(rf"\b{re.escape(sid)}\b", tb_text):
                        row["status"] = "implemented"
                def _result_xml_paths() -> list[Path]:
                    canonical = ip_dir / "sim" / "results.xml"
                    roots = [
                        ip_dir / "sim",
                        ip_dir / "tb" / "cocotb",
                        ip_dir / "tb",
                    ]
                    out: list[Path] = []
                    seen: set[Path] = set()
                    for root in roots:
                        if not root.is_dir():
                            continue
                        for pth in root.rglob("*results.xml"):
                            rp = pth.resolve()
                            if rp not in seen:
                                out.append(pth)
                                seen.add(rp)
                    if not out:
                        return [canonical] if canonical.is_file() else []
                    canonical_rp = canonical.resolve() if canonical.exists() else None
                    noncanonical = [p for p in out if canonical_rp is None or p.resolve() != canonical_rp]
                    if not noncanonical:
                        return sorted(out, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)[:1]
                    newest_noncanonical = max(p.stat().st_mtime for p in noncanonical if p.exists())
                    # Cocotb often writes one result XML per config/run. Keep the latest
                    # result from each run directory, and ignore stale canonical summaries.
                    latest_by_dir: dict[Path, Path] = {}
                    for pth in noncanonical:
                        parent = pth.parent
                        cur = latest_by_dir.get(parent)
                        if cur is None or pth.stat().st_mtime > cur.stat().st_mtime:
                            latest_by_dir[parent] = pth
                    selected = [
                        p for p in latest_by_dir.values()
                        if p.exists() and p.stat().st_mtime >= newest_noncanonical - 10.0
                    ]
                    if canonical.is_file() and canonical.stat().st_mtime >= newest_noncanonical - 2.0:
                        selected.append(canonical)
                    return sorted(selected, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)

                results = []
                result_text = ""
                has_valid_result_xml = False
                testcase_names: set[str] = set()
                failed_names: set[str] = set()
                testcase_failed: dict[str, bool] = {}
                for pth in _result_xml_paths():
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if not text.strip():
                        continue
                    result_text += "\n" + text
                    parsed_xml = False
                    try:
                        import xml.etree.ElementTree as _ET
                        root_xml = _ET.fromstring(text)
                        cases = list(root_xml.iter("testcase"))
                        if cases:
                            parsed_xml = True
                            has_valid_result_xml = True
                            source_fail = 0
                            source_err = 0
                            for tc in cases:
                                name = tc.attrib.get("name") or ""
                                if not name:
                                    continue
                                testcase_names.add(name)
                                has_failure = tc.find("failure") is not None
                                has_error = tc.find("error") is not None
                                if has_failure or has_error:
                                    failed_names.add(name)
                                if has_failure:
                                    source_fail += 1
                                if has_error:
                                    source_err += 1
                                # Result files can be mirrored under sim/ and tb/cocotb/.
                                # _result_xml_paths() returns newest first, so keep the
                                # first observation for a testcase name to avoid double
                                # counting the same run.
                                testcase_failed.setdefault(name, has_failure or has_error)
                            results.append({
                                "tests": len(cases),
                                "failures": source_fail,
                                "errors": source_err,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                    except Exception:
                        parsed_xml = False
                    if not parsed_xml:
                        names = re.findall(r'<testcase[^>]*name="([^"]+)"', text)
                        testcase_names.update(names)
                        source_failed: set[str] = set()
                        for m in re.finditer(r'<testcase[^>]*name="([^"]+)"[^>]*>(.*?)</testcase>', text, re.S):
                            if re.search(r'<(?:failure|error)\b', m.group(2)):
                                source_failed.add(m.group(1))
                        failed_names.update(source_failed)
                        for name in names:
                            testcase_failed.setdefault(name, name in source_failed)
                        tests_attr = re.search(r'tests="(\d+)"', text)
                        fail_attr = re.search(r'failures="(\d+)"', text)
                        err_attr = re.search(r'errors="(\d+)"', text)
                        if tests_attr:
                            has_valid_result_xml = True
                            results.append({
                                "tests": int(tests_attr.group(1)),
                                "failures": int(fail_attr.group(1)) if fail_attr else 0,
                                "errors": int(err_attr.group(1)) if err_attr else 0,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                        elif names:
                            has_valid_result_xml = True
                            results.append({
                                "tests": len(names),
                                "failures": len(source_failed),
                                "errors": 0,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                def _sid_matches_name(sid: str, name: str) -> bool:
                    if not sid:
                        return False
                    sid_l = sid.lower()
                    name_l = name.lower()
                    if sid_l in name_l:
                        return True
                    m = re.match(r"sc(\d+)$", sid_l)
                    return bool(m and f"sc{int(m.group(1)):02d}" in name_l)

                if has_valid_result_xml:
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in testcase_names):
                            row["status"] = "pass"
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in failed_names):
                            row["status"] = "fail"
                if testcase_failed:
                    total = len(testcase_failed)
                    fail = sum(1 for failed in testcase_failed.values() if failed)
                else:
                    total = sum(r["tests"] for r in results)
                    fail = sum(r["failures"] + r["errors"] for r in results)
                cov_pct = None
                cov_doc = {}
                cov_bins: dict[str, object] = {}
                coverage_limitations: dict[str, object] = {}
                coverage_static: dict[str, object] = {}
                check_total = None
                check_pass = None
                check_fail = None
                escalations = []
                cov_paths = sorted((ip_dir / "cov").glob("coverage*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
                for cov_json in cov_paths:
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict):
                            cov_pct = functional.get("pct", cov_pct)
                        if isinstance(cov_doc, dict):
                            bins = cov_doc.get("functional_bins")
                            if isinstance(bins, dict):
                                cov_bins.update(bins)
                        if isinstance(cov_doc, dict):
                            if isinstance(cov_doc.get("total_checks"), int):
                                check_total = (check_total or 0) + cov_doc.get("total_checks")
                            if isinstance(cov_doc.get("passed"), int):
                                check_pass = (check_pass or 0) + cov_doc.get("passed")
                            if isinstance(cov_doc.get("failed"), int):
                                check_fail = (check_fail or 0) + cov_doc.get("failed")
                            static_limits = cov_doc.get("static_universe_not_instrumented")
                            if isinstance(static_limits, dict):
                                for k, v in static_limits.items():
                                    coverage_limitations[k] = v
                            explicit_limits = cov_doc.get("limitations")
                            if isinstance(explicit_limits, dict):
                                for k, v in explicit_limits.items():
                                    coverage_limitations[k] = v
                            for metric_key in ("lines", "branches", "functions", "fsm_state"):
                                metric_doc = cov_doc.get(metric_key)
                                if isinstance(metric_doc, dict):
                                    coverage_static[metric_key] = metric_doc
                            raw_escalations = cov_doc.get("escalations")
                            if isinstance(raw_escalations, list):
                                escalations.extend(e for e in raw_escalations if isinstance(e, dict))
                    except Exception:
                        pass
                if cov_bins:
                    hit = sum(1 for v in cov_bins.values() if bool(v))
                    total_bins = max(scenario_count, len(cov_bins))
                    cov_pct = _pct(hit, total_bins)
                    for row in scenario_rows:
                        sid = str(row.get("id") or "")
                        if not sid or row.get("status") == "fail":
                            continue
                        prefix = f"{sid}_".lower()
                        if any(str(k).lower().startswith(prefix) and bool(v) for k, v in cov_bins.items()):
                            row["status"] = "pass"
                escalation_by_sid: dict[str, list[dict]] = {}
                for esc in escalations:
                    sid = str(esc.get("test_id") or esc.get("scenario") or esc.get("id") or "").strip()
                    if not sid:
                        text = json.dumps(esc, ensure_ascii=False)
                        m = re.search(r"\b(SC\d+)\b", text, re.I)
                        sid = m.group(1) if m else ""
                    if sid:
                        escalation_by_sid.setdefault(sid.lower(), []).append(esc)
                for row in scenario_rows:
                    sid = str(row.get("id") or "").lower()
                    row_escalations = escalation_by_sid.get(sid, [])
                    if not row_escalations:
                        continue
                    text = json.dumps(row_escalations, ensure_ascii=False).lower()
                    row["status"] = "blocked" if (
                        "blocked" in text or "infrastructure" in text or "parameter override" in text
                    ) else "fail"
                    row["escalation"] = row_escalations[0]
                if isinstance(check_fail, int) and check_fail > fail:
                    fail = check_fail
                has_sim_evidence = total > 0
                sim_pass_evidence = has_sim_evidence and fail == 0
                passed_scenarios = sum(1 for r in scenario_rows if r["status"] == "pass")
                failed_scenarios = sum(1 for r in scenario_rows if r["status"] == "fail")
                all_scenarios_passed = scenario_count == 0 or passed_scenarios >= scenario_count
                has_coverage_numbers = cov_pct is not None or isinstance(check_total, int)
                functional_closed = cov_pct is not None and float(cov_pct) >= 100.0
                if not has_sim_evidence:
                    coverage_status = "pending"
                elif fail:
                    coverage_status = "fail"
                elif not all_scenarios_passed:
                    coverage_status = "pending"
                elif not cov_paths:
                    coverage_status = "pending"
                elif not has_coverage_numbers:
                    coverage_status = "pending"
                elif coverage_limitations:
                    coverage_status = "blocked"
                elif not functional_closed:
                    coverage_status = "fail"
                else:
                    coverage_status = "pass"
                return {
                    "dv_plan": {
                        "scenarios": scenario_count,
                        "scoreboard_checks": scoreboard,
                        "coverage_goals": coverage_goal_count,
                        "scenario_rows": scenario_rows,
                    },
                    "implemented_scenarios": sum(1 for r in scenario_rows if r["status"] in ("implemented", "pass")),
                    "passed_scenarios": passed_scenarios,
                    "failed_scenarios": failed_scenarios,
                    "implemented_tests": len(tests),
                    "results": {
                        "total": total,
                        "pass": max(total - fail, 0),
                        "fail": fail,
                        "sources": [r["source"] for r in results],
                        "check_total": check_total,
                        "check_pass": check_pass,
                        "check_fail": check_fail,
                    },
                    "coverage": {
                        "status": coverage_status,
                        "functional_pct": cov_pct,
                        "static": coverage_static,
                        "criteria": coverage_goals if isinstance(coverage_goals, dict) else {},
                        "limitations": coverage_limitations,
                    },
                    "escalations": escalations,
                }

            def _req_progress(ip_dir: Path) -> dict:
                req_dir = ip_dir / "req"
                files = []
                if req_dir.is_dir():
                    files = [
                        p for p in sorted(req_dir.rglob("*"))
                        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".yaml", ".yml", ".json"}
                    ]
                total_bytes = sum(p.stat().st_size for p in files if p.exists())
                text = ""
                for p in files[:12]:
                    try:
                        text += "\n" + p.read_text(encoding="utf-8", errors="replace")[:200000]
                    except OSError:
                        pass
                placeholder = bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", text, re.I))
                enough = total_bytes >= 1000 and not placeholder
                return {
                    "status": "ok" if files and enough else ("partial" if files else "pending"),
                    "files": [p.relative_to(PROJECT_ROOT).as_posix() for p in files[:12]],
                    "bytes": total_bytes,
                    "placeholder": placeholder,
                    "criteria": "REQ capture exists under <ip>/req, has substantive content, and contains no TBD/TODO/FIXME placeholders",
                }

            def _fl_model_progress(ip_dir: Path, doc: dict | None = None) -> dict:
                model_path = ip_dir / "model" / "functional_model.py"
                check_path = ip_dir / "model" / "fl_model_check.json"
                exists = model_path.is_file()
                size = model_path.stat().st_size if exists else 0
                text = ""
                if exists:
                    try:
                        text = model_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        text = ""
                check = {}
                if check_path.is_file():
                    try:
                        check = json.loads(check_path.read_text(encoding="utf-8"))
                    except Exception:
                        check = {"passed": False}
                has_api = "class FunctionalModel" in text and "def apply" in text
                imports_ok = bool(check.get("passed") is True)
                fm = doc.get("function_model") if isinstance(doc, dict) and isinstance(doc.get("function_model"), dict) else {}
                txns = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
                expected_txns = [
                    str(tx.get("id") or tx.get("name") or "").strip()
                    for tx in txns
                    if isinstance(tx, dict) and (tx.get("id") or tx.get("name"))
                ]
                trace_sources = [
                    check.get("transaction_results"),
                    check.get("transaction_traceability"),
                    (check.get("self_check") or {}).get("transaction_results") if isinstance(check.get("self_check"), dict) else None,
                    (check.get("self_check") or {}).get("transaction_traceability") if isinstance(check.get("self_check"), dict) else None,
                ]
                trace_text = json.dumps(trace_sources, ensure_ascii=False).lower()
                traced_txns = [
                    txn for txn in expected_txns
                    if txn.lower() in trace_text
                ]
                trace_complete = not expected_txns or len(traced_txns) == len(expected_txns)
                status = "pass" if exists and size >= 500 and has_api and imports_ok and trace_complete else (
                    "partial" if exists else "pending"
                )
                return {
                    "status": status,
                    "source": model_path.relative_to(PROJECT_ROOT).as_posix() if exists else "",
                    "check_source": check_path.relative_to(PROJECT_ROOT).as_posix() if check_path.is_file() else "",
                    "bytes": size,
                    "has_apply": has_api,
                    "self_check": check,
                    "transactions_expected": expected_txns,
                    "transactions_traced": traced_txns,
                    "trace_complete": trace_complete,
                    "criteria": "executable Python FL model generated from SSOT with FunctionalModel.apply(txn), passing self-check, and tracing every SSOT function_model transaction",
                }

            def _fl_decomp_progress(ip_dir: Path) -> dict:
                path = ip_dir / "model" / "decomposition.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                units = doc.get("units") if isinstance(doc, dict) else []
                if not isinstance(units, list):
                    units = []
                kinds = sorted({str(u.get("kind")) for u in units if isinstance(u, dict) and u.get("kind")})
                status = "pass" if path.is_file() and isinstance(units, list) and len(units) >= 2 and doc.get("complete") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": path.relative_to(PROJECT_ROOT).as_posix() if path.is_file() else "",
                    "units": len(units) if isinstance(units, list) else 0,
                    "kinds": kinds,
                    "criteria": "FL model decomposition traces protocol/register/memory/datapath/FSM/error/security units to SSOT sections",
                }

            def _fcov_plan_progress(ip_dir: Path) -> dict:
                path = ip_dir / "cov" / "fcov_plan.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                bins = doc.get("bins") if isinstance(doc, dict) else []
                if not isinstance(bins, list):
                    bins = []
                classes = sorted({str(b.get("class")) for b in bins if isinstance(b, dict) and b.get("class")})
                status = "pass" if path.is_file() and isinstance(bins, list) and len(bins) > 0 and doc.get("planned_before_rtl") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": path.relative_to(PROJECT_ROOT).as_posix() if path.is_file() else "",
                    "bins": len(bins) if isinstance(bins, list) else 0,
                    "classes": classes,
                    "summary": doc.get("summary") if isinstance(doc, dict) else {},
                    "criteria": "functional coverage bins are planned from SSOT/FL model before RTL signoff",
                }

            def _equivalence_progress(ip_dir: Path) -> dict:
                goals_path = ip_dir / "verify" / "equivalence_goals.json"
                compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
                classify_path = ip_dir / "sim" / "mismatch_classification.json"
                goals_doc: dict[str, Any] = {}
                compare_doc: dict[str, Any] = {}
                classify_doc: dict[str, Any] = {}
                if goals_path.is_file():
                    try:
                        loaded = json.loads(goals_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            goals_doc = loaded
                    except Exception:
                        goals_doc = {}
                if compare_path.is_file():
                    try:
                        loaded = json.loads(compare_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            compare_doc = loaded
                    except Exception:
                        compare_doc = {}
                if classify_path.is_file():
                    try:
                        loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            classify_doc = loaded
                    except Exception:
                        classify_doc = {}

                goals = goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []
                goal_summary = goals_doc.get("summary") if isinstance(goals_doc.get("summary"), dict) else {}
                source_of_truth = goals_doc.get("source_of_truth") if isinstance(goals_doc.get("source_of_truth"), dict) else {}
                authority_contract = source_of_truth.get("authority_contract") if isinstance(source_of_truth.get("authority_contract"), dict) else {}
                compare_summary = compare_doc.get("summary") if isinstance(compare_doc.get("summary"), dict) else {}
                classifications = classify_doc.get("classifications") if isinstance(classify_doc.get("classifications"), list) else []
                classification_counts: dict[str, int] = {}
                owner_counts: dict[str, int] = {}
                loopable_repairs = 0
                human_gated_repairs = 0
                for item in classifications:
                    if not isinstance(item, dict):
                        continue
                    cls = str(item.get("classification") or "unknown")
                    owner = str(item.get("owner") or "unknown")
                    classification_counts[cls] = classification_counts.get(cls, 0) + 1
                    owner_counts[owner] = owner_counts.get(owner, 0) + 1
                    if item.get("llm_loop_allowed") is True:
                        loopable_repairs += 1
                    elif item.get("llm_loop_allowed") is False:
                        human_gated_repairs += 1
                total = int(goal_summary.get("total") or len(goals) or 0)
                generated = total
                checked = int(compare_summary.get("goals_checked") or 0)
                passed = int(compare_summary.get("goals_passed") or 0)
                failed = int(compare_summary.get("goals_failed") or 0)
                blocked = int(compare_summary.get("goals_blocked") or goal_summary.get("blocked") or 0)
                untested = int(compare_summary.get("goals_untested") or 0)
                compare_status = str(compare_doc.get("status") or "")
                stale_evidence = compare_summary.get("stale_evidence") if isinstance(compare_summary.get("stale_evidence"), list) else []
                if compare_status == "pass":
                    status = "pass"
                elif compare_status == "fail":
                    status = "fail"
                elif compare_status == "stale" or stale_evidence:
                    status = "stale"
                elif blocked:
                    status = "blocked"
                elif goals_path.is_file() and total:
                    status = "partial"
                else:
                    status = "pending"
                failed_ids = []
                blocked_ids = []
                untested_ids = []
                for item in compare_doc.get("goals") if isinstance(compare_doc.get("goals"), list) else []:
                    if not isinstance(item, dict):
                        continue
                    goal_id = str(item.get("goal_id") or "")
                    if item.get("status") == "fail":
                        failed_ids.append(goal_id)
                    elif item.get("status") == "blocked":
                        blocked_ids.append(goal_id)
                    elif item.get("status") == "untested":
                        untested_ids.append(goal_id)
                return {
                    "status": status,
                    "total": total,
                    "generated": generated,
                    "checked": checked,
                    "passed": passed,
                    "failed": failed,
                    "blocked": blocked,
                    "untested": untested,
                    "failed_goal_ids": [x for x in failed_ids if x][:12],
                    "blocked_goal_ids": [x for x in blocked_ids if x][:12],
                    "untested_goal_ids": [x for x in untested_ids if x][:12],
                    "classifications": len(classifications),
                    "loopable_repairs": loopable_repairs,
                    "human_gated_repairs": human_gated_repairs,
                    "classification_counts": classification_counts,
                    "owner_counts": owner_counts,
                    "module_total": int(goal_summary.get("module_total") or 0),
                    "module_required": int(goal_summary.get("module_required") or 0),
                    "module_blocked": int(goal_summary.get("module_blocked") or 0),
                    "authority_contract": authority_contract,
                    "general_evaluation_criteria": authority_contract.get("general_evaluation_criteria") if isinstance(authority_contract.get("general_evaluation_criteria"), list) else [],
                    "locked_artifacts": authority_contract.get("locked_artifacts") if isinstance(authority_contract.get("locked_artifacts"), list) else [],
                    "llm_editable_artifacts": authority_contract.get("llm_editable_artifacts") if isinstance(authority_contract.get("llm_editable_artifacts"), list) else [],
                    "loopable_evidence_points": authority_contract.get("loopable_evidence_points") if isinstance(authority_contract.get("loopable_evidence_points"), list) else [],
                    "loopable_oracles": authority_contract.get("loopable_oracles") if isinstance(authority_contract.get("loopable_oracles"), list) else [],
                    "missing_evidence": compare_summary.get("missing_evidence") if isinstance(compare_summary.get("missing_evidence"), list) else [],
                    "stale_evidence": stale_evidence,
                    "evidence": goals_path.relative_to(PROJECT_ROOT).as_posix() if goals_path.is_file() else "",
                    "compare_evidence": compare_path.relative_to(PROJECT_ROOT).as_posix() if compare_path.is_file() else "",
                    "classification_evidence": classify_path.relative_to(PROJECT_ROOT).as_posix() if classify_path.is_file() else "",
                    "next_action": (
                        "none; all equivalence goals passed"
                        if status == "pass" else
                        "rerun /sim <ip> and /sim-debug <ip>; existing evidence is stale"
                        if status == "stale" else
                        "answer SSOT/human gate questions from mismatch_classification.json"
                        if status == "blocked" else
                        "repair classified FL/RTL/TB/coverage owner from mismatch_classification.json"
                        if status == "fail" else
                        "run sim_debug comparator after TB emits scoreboard_events.jsonl"
                        if goals_path.is_file() else
                        "run /ssot-equiv-goals <ip>"
                    ),
                    "owner": (
                        "human gate" if status == "blocked" else
                        "LLM loop" if status in {"fail", "partial", "pending"} else
                        "LLM loop"
                    ),
                    "criteria": "SSOT-derived equivalence goals exist, TB scoreboard checks them, sim_debug compare passes every required goal, and all mismatches are classified",
                }

            def _goal_audit_progress(ip_dir: Path) -> dict:
                audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
                doc: dict[str, Any] = {}
                if audit_path.is_file():
                    try:
                        loaded = json.loads(audit_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            doc = loaded
                    except Exception:
                        doc = {}
                summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
                checks = doc.get("checks") if isinstance(doc.get("checks"), list) else []
                blockers = [str(x) for x in summary.get("blockers") or []] if isinstance(summary, dict) else []
                source_paths = [
                    ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml",
                    ip_dir / "model" / "functional_model.py",
                    ip_dir / "model" / "fl_model_check.json",
                    ip_dir / "model" / "decomposition.json",
                    ip_dir / "cov" / "fcov_plan.json",
                    ip_dir / "verify" / "equivalence_goals.json",
                    ip_dir / "sim" / "scoreboard_events.jsonl",
                    ip_dir / "sim" / "results.xml",
                    ip_dir / "tb" / "cocotb" / "results.xml",
                    ip_dir / "cov" / "coverage.json",
                    ip_dir / "sim" / "fl_rtl_compare.json",
                    ip_dir / "sim" / "mismatch_classification.json",
                    ip_dir / "rtl" / "rtl_compile.json",
                    ip_dir / "lint" / "dut_lint.json",
                    ip_dir / "lint" / "rtl_lint.json",
                ]
                stale_evidence: list[str] = []
                if audit_path.is_file():
                    existing_sources = [p for p in source_paths if p.is_file()]
                    if existing_sources:
                        newest = max(existing_sources, key=lambda p: p.stat().st_mtime)
                        if audit_path.stat().st_mtime + 0.5 < newest.stat().st_mtime:
                            try:
                                stale_evidence.append(
                                    f"{audit_path.relative_to(PROJECT_ROOT)} older than {newest.relative_to(PROJECT_ROOT)}"
                                )
                            except ValueError:
                                stale_evidence.append("goal audit artifact is older than a source artifact")
                raw_status = str(doc.get("status") or "") if doc else ""
                if stale_evidence:
                    status = "stale"
                elif raw_status == "pass":
                    status = "pass"
                elif raw_status == "fail":
                    status = "fail"
                elif audit_path.is_file():
                    status = "partial"
                else:
                    status = "pending"
                return {
                    "status": status,
                    "source": audit_path.relative_to(PROJECT_ROOT).as_posix() if audit_path.is_file() else "",
                    "total_checks": int(summary.get("total_checks") or 0) if isinstance(summary, dict) else 0,
                    "passed_checks": int(summary.get("passed_checks") or 0) if isinstance(summary, dict) else 0,
                    "failed_checks": int(summary.get("failed_checks") or 0) if isinstance(summary, dict) else 0,
                    "blockers": blockers,
                    "stale_evidence": stale_evidence,
                    "generated_at": doc.get("generated_at") if isinstance(doc, dict) else "",
                    "checks": [
                        {
                            "id": str(item.get("id") or ""),
                            "status": str(item.get("status") or ""),
                            "owner": str(item.get("owner") or ""),
                            "next_action": str(item.get("next_action") or ""),
                        }
                        for item in checks[:20]
                        if isinstance(item, dict)
                    ],
                    "next_action": (
                        "none; goal audit passed"
                        if status == "pass" else
                        "rerun /goal-audit <ip>; existing audit is stale"
                        if status == "stale" else
                        "inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage"
                        if status == "fail" else
                        "run /goal-audit <ip> after sim-debug and coverage evidence exist"
                    ),
                    "owner": "LLM loop",
                    "criteria": "single disk-truth audit proves REQ, SSOT, FL, cycle model, RTL DUT-only compile/lint, TB scoreboard, sim, compare, coverage, and signoff evidence",
                }

            def _strict_gate_from_progress(progress: dict) -> dict:
                ssot = progress.get("ssot") if isinstance(progress, dict) else {}
                req = progress.get("req") if isinstance(progress, dict) else {}
                fl_model = progress.get("fl_model") if isinstance(progress, dict) else {}
                fl_decomp = progress.get("fl_decomp") if isinstance(progress, dict) else {}
                fcov_plan = progress.get("fcov_plan") if isinstance(progress, dict) else {}
                equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                rtl = progress.get("rtl") if isinstance(progress, dict) else {}
                compile_st = progress.get("compile") if isinstance(progress, dict) else {}
                lint = progress.get("lint") if isinstance(progress, dict) else {}
                sim = progress.get("sim") if isinstance(progress, dict) else {}
                dv = sim.get("dv_plan") if isinstance(sim, dict) else {}
                results = sim.get("results") if isinstance(sim, dict) else {}
                coverage = sim.get("coverage") if isinstance(sim, dict) else {}

                ssot_total = int(ssot.get("total") or 0) if isinstance(ssot, dict) else 0
                ssot_approved = int(ssot.get("approved") or 0) if isinstance(ssot, dict) else 0
                req_status = str(req.get("status") or "pending") if isinstance(req, dict) else "pending"
                fl_model_status = str(fl_model.get("status") or "pending") if isinstance(fl_model, dict) else "pending"
                fl_decomp_status = str(fl_decomp.get("status") or "pending") if isinstance(fl_decomp, dict) else "pending"
                fcov_plan_status = str(fcov_plan.get("status") or "pending") if isinstance(fcov_plan, dict) else "pending"
                equivalence_status = str(equivalence.get("status") or "pending") if isinstance(equivalence, dict) else "pending"
                goal_audit_status = str(goal_audit.get("status") or "pending") if isinstance(goal_audit, dict) else "pending"
                rtl_total = int(rtl.get("total") or 0) if isinstance(rtl, dict) else 0
                rtl_approved = int(rtl.get("approved") or 0) if isinstance(rtl, dict) else 0
                rtl_mismatches = int(rtl.get("manifest_mismatches") or 0) if isinstance(rtl, dict) else 0
                rtl_quality = int(rtl.get("quality_issue_count") or 0) if isinstance(rtl, dict) else 0
                rtl_quality_issues = rtl.get("quality_issues") if isinstance(rtl, dict) and isinstance(rtl.get("quality_issues"), list) else []
                rtl_blocked = bool(rtl.get("blocked")) if isinstance(rtl, dict) else False
                rtl_blocker = str(rtl.get("blocker") or "") if isinstance(rtl, dict) else ""
                compile_status = str(compile_st.get("status") or "unknown") if isinstance(compile_st, dict) else "unknown"
                scenario_total = int(dv.get("scenarios") or 0) if isinstance(dv, dict) else 0
                implemented = int(sim.get("implemented_scenarios") or 0) if isinstance(sim, dict) else 0
                passed_scenarios = int(sim.get("passed_scenarios") or 0) if isinstance(sim, dict) else 0
                failed_scenarios = int(sim.get("failed_scenarios") or 0) if isinstance(sim, dict) else 0
                result_total = int(results.get("total") or 0) if isinstance(results, dict) else 0
                result_fail = int(results.get("fail") or 0) if isinstance(results, dict) else 0
                lint_status = str(lint.get("status") or "unknown") if isinstance(lint, dict) else "unknown"
                raw_cov_status = str(coverage.get("status") or "unknown") if isinstance(coverage, dict) else "unknown"
                all_scenarios_passed = scenario_total == 0 or passed_scenarios >= scenario_total
                sim_pass_evidence = result_total > 0 and result_fail == 0 and failed_scenarios == 0 and all_scenarios_passed
                if result_total <= 0:
                    cov_status = "pending"
                elif result_fail:
                    cov_status = "fail"
                elif not all_scenarios_passed:
                    cov_status = "pending"
                else:
                    cov_status = raw_cov_status

                ssot_status = "ok" if ssot_total and ssot_approved == ssot_total else (
                    "partial" if ssot_approved else "pending"
                )
                rtl_modules_status = "blocked" if rtl_blocked else ("ok" if rtl_total and rtl_approved == rtl_total else (
                    "partial" if rtl_approved else "pending"
                ))
                if rtl_blocked:
                    rtl_status = "blocked"
                elif lint_status == "fail":
                    rtl_status = "fail"
                elif compile_status == "fail":
                    rtl_status = "fail"
                elif rtl_mismatches:
                    rtl_status = "fail"
                elif rtl_modules_status == "ok" and compile_status == "pass" and lint_status == "pass":
                    rtl_status = "ok"
                elif rtl_modules_status == "pending":
                    rtl_status = "pending"
                else:
                    rtl_status = "partial"

                tb_status = "ok" if scenario_total and implemented >= scenario_total else (
                    "partial" if implemented else "pending"
                )
                if result_total <= 0:
                    sim_status = "pending"
                elif result_fail or failed_scenarios:
                    sim_status = "fail"
                elif not all_scenarios_passed:
                    sim_status = "partial"
                else:
                    sim_status = "ok"

                blockers: list[str] = []
                if ssot_status != "ok":
                    blockers.append(f"SSOT sections {ssot_approved}/{ssot_total} approved")
                if req_status != "ok":
                    blockers.append(f"REQ capture {req_status}")
                if fl_model_status != "pass":
                    blockers.append(f"FL model {fl_model_status}")
                if fl_decomp_status != "pass":
                    blockers.append(f"FL decomposition {fl_decomp_status}")
                if fcov_plan_status != "pass":
                    blockers.append(f"FCOV plan {fcov_plan_status}")
                if equivalence_status != "pass":
                    blockers.append(
                        "equivalence goals "
                        f"{equivalence_status} "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} passed"
                    )
                if goal_audit_status != "pass":
                    audit_blockers = goal_audit.get("blockers", []) if isinstance(goal_audit, dict) else []
                    blockers.append(
                        "goal audit "
                        f"{goal_audit_status}"
                        + (f" blockers={','.join(str(x) for x in audit_blockers[:6])}" if audit_blockers else "")
                    )
                if rtl_blocked:
                    blockers.append(f"RTL blocked: {rtl_blocker or 'SSOT decision required'}")
                elif rtl_modules_status != "ok":
                    blockers.append(f"RTL modules {rtl_approved}/{rtl_total} approved")
                if rtl_mismatches:
                    blockers.append(f"SSOT/RTL manifest mismatch {rtl_mismatches}")
                if rtl_quality:
                    first_issue = ""
                    if rtl_quality_issues and isinstance(rtl_quality_issues[0], dict):
                        first_issue = str(rtl_quality_issues[0].get("issue") or "")
                    blockers.append(
                        f"RTL quality issues {rtl_quality}"
                        + (f": {first_issue}" if first_issue else "")
                    )
                if compile_status != "pass":
                    comp_err = compile_st.get("errors", 0) if isinstance(compile_st, dict) else 0
                    comp_diag = compile_st.get("diagnostics", 0) if isinstance(compile_st, dict) else 0
                    comp_style = compile_st.get("style_violations", 0) if isinstance(compile_st, dict) else 0
                    blockers.append(f"RTL compile {compile_status} E{comp_err}/D{comp_diag}/S{comp_style}")
                if lint_status != "pass":
                    err = lint.get("errors", 0) if isinstance(lint, dict) else 0
                    warn = lint.get("warnings", 0) if isinstance(lint, dict) else 0
                    suppressions = lint.get("suppression_violations", 0) if isinstance(lint, dict) else 0
                    suffix = f"/S{suppressions}" if suppressions else ""
                    blockers.append(f"lint {lint_status} E{err}/W{warn}{suffix}")
                if tb_status != "ok":
                    blockers.append(f"DV scenarios implemented {implemented}/{scenario_total}")
                if result_total <= 0:
                    blockers.append("no fresh sim result XML found")
                elif result_fail:
                    blockers.append(f"simulation failures {result_fail}/{result_total}")
                if scenario_total and passed_scenarios < scenario_total:
                    blockers.append(f"sim scenarios passed {passed_scenarios}/{scenario_total}")
                if cov_status != "pass":
                    if not sim_pass_evidence:
                        blockers.append("coverage requires fresh passing simulation result")
                    else:
                        blockers.append(f"coverage {cov_status}")

                if any(v in {"fail"} for v in (rtl_status, sim_status, lint_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "fail"
                elif any(v in {"blocked", "stale"} for v in (rtl_status, sim_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "blocked"
                elif not blockers:
                    signoff = "pass"
                elif ssot_approved or rtl_approved or implemented or result_total:
                    signoff = "partial"
                else:
                    signoff = "pending"

                status = {
                    "req": req_status,
                    "ssot": ssot_status,
                    "fl_model": fl_model_status,
                    "fl_decomp": fl_decomp_status,
                    "fcov_plan": fcov_plan_status,
                    "equivalence_goals": equivalence_status,
                    "goal_audit": goal_audit_status,
                    "rtl": rtl_status,
                    "lint": lint_status,
                    "tb": tb_status,
                    "sim_debug": sim_status,
                    "coverage": cov_status,
                    "signoff": signoff,
                }
                detail = {
                    "req": f"{req_status}: {len(req.get('files', [])) if isinstance(req, dict) else 0} requirement artifact(s)",
                    "ssot": f"{ssot_approved}/{ssot_total} canonical sections approved",
                    "fl_model": (
                        f"{fl_model_status}: "
                        f"{fl_model.get('source', '') if isinstance(fl_model, dict) else ''} "
                        f"self_check={bool(fl_model.get('self_check', {}).get('passed')) if isinstance(fl_model, dict) else False}"
                    ),
                    "fl_decomp": (
                        f"{fl_decomp_status}: "
                        f"{fl_decomp.get('units', 0) if isinstance(fl_decomp, dict) else 0} unit(s)"
                    ),
                    "fcov_plan": (
                        f"{fcov_plan_status}: "
                        f"{fcov_plan.get('bins', 0) if isinstance(fcov_plan, dict) else 0} bin(s)"
                    ),
                    "equivalence_goals": (
                        f"{equivalence_status}: "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} pass; "
                        f"checked {equivalence.get('checked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"failed {equivalence.get('failed', 0) if isinstance(equivalence, dict) else 0}; "
                        f"blocked {equivalence.get('blocked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"untested {equivalence.get('untested', 0) if isinstance(equivalence, dict) else 0}"
                    ),
                    "goal_audit": (
                        f"{goal_audit_status}: "
                        f"{goal_audit.get('passed_checks', 0) if isinstance(goal_audit, dict) else 0}/"
                        f"{goal_audit.get('total_checks', 0) if isinstance(goal_audit, dict) else 0} checks; "
                        f"blockers {', '.join(goal_audit.get('blockers', [])[:6]) if isinstance(goal_audit.get('blockers', []), list) else ''}"
                    ),
                    "rtl": (
                        f"{rtl_approved}/{rtl_total} RTL files approved; "
                        f"blocked {rtl_blocked}; "
                        f"manifest mismatch {rtl_mismatches}; "
                        f"quality issues {rtl_quality}; "
                        f"compile {compile_status} "
                        f"E{compile_st.get('errors', 0) if isinstance(compile_st, dict) else 0}/"
                        f"D{compile_st.get('diagnostics', 0) if isinstance(compile_st, dict) else 0}/"
                        f"S{compile_st.get('style_violations', 0) if isinstance(compile_st, dict) else 0}; "
                        f"lint {lint_status} E{lint.get('errors', 0) if isinstance(lint, dict) else 0}/"
                        f"W{lint.get('warnings', 0) if isinstance(lint, dict) else 0}"
                        f"/S{lint.get('suppression_violations', 0) if isinstance(lint, dict) else 0}"
                    ),
                    "tb": f"{implemented}/{scenario_total} SSOT DV scenarios implemented",
                    "sim_debug": (
                        f"results {max(result_total - result_fail, 0)} pass / "
                        f"{result_fail} fail / {result_total} total; coverage {cov_status}"
                    ),
                    "coverage": f"coverage {cov_status}",
                    "signoff": "pass" if signoff == "pass" else "; ".join(blockers[:6]),
                }

                def _first_source(*values: Any) -> str:
                    for value in values:
                        if isinstance(value, str) and value:
                            return value
                        if isinstance(value, list) and value:
                            return str(value[0])
                    return ""

                def _owner(stage: str, stage_status: str) -> str:
                    if stage == "req" and stage_status != "ok":
                        return "human gate"
                    if stage == "rtl" and stage_status == "blocked":
                        return "human gate" if rtl_blocked else "blocked"
                    if stage == "signoff":
                        if stage_status == "pass":
                            return "human gate"
                        if req_status != "ok" or cov_status == "blocked" or equivalence_status == "blocked":
                            return "human gate"
                    if stage == "equivalence_goals" and stage_status == "blocked":
                        return "human gate"
                    if stage == "coverage" and stage_status == "blocked":
                        return "human gate"
                    if stage_status in {"blocked"}:
                        return "blocked"
                    return "LLM loop"

                def _next_action(stage: str, stage_status: str) -> str:
                    if stage_status in {"ok", "pass"}:
                        if stage == "signoff":
                            return "tool evidence passed; human final acceptance may proceed"
                        return "none; evidence accepted"
                    if stage == "req":
                        return "answer missing requirement questions or refresh req-gen ledger"
                    if stage == "ssot":
                        return "repair SSOT sections or ask human for undefined behavior"
                    if stage == "fl_model":
                        return "run fl-model-gen and repair FunctionalModel self-check"
                    if stage == "fl_decomp":
                        return "generate SSOT-traced FL decomposition units"
                    if stage == "fcov_plan":
                        return "generate planned functional coverage bins from SSOT/FL"
                    if stage == "equivalence_goals":
                        return equivalence.get("next_action", "run /ssot-equiv-goals and sim_debug compare") if isinstance(equivalence, dict) else "run /ssot-equiv-goals"
                    if stage == "goal_audit":
                        return goal_audit.get("next_action", "run /goal-audit after evidence exists") if isinstance(goal_audit, dict) else "run /goal-audit"
                    if stage == "rtl":
                        if stage_status == "blocked":
                            return "answer rtl_blocked SSOT questions, refresh SSOT/FL model, then rerun /ssot-rtl"
                        return "run rtl-gen repair from SSOT, compile, and lint evidence"
                    if stage == "lint":
                        return "repair DUT-only lint diagnostics or request explicit waiver"
                    if stage == "tb":
                        return "generate missing cocotb/pyuvm scenario checkers"
                    if stage == "sim_debug":
                        return "classify mismatch owner, then repair RTL/FL/TB or ask on SSOT ambiguity"
                    if stage == "coverage":
                        return "close missing planned bins or request explicit waiver"
                    if stage == "signoff":
                        return "resolve blockers before evidence signoff can pass"
                    return "inspect stage evidence"

                def _stage_entry(stage: str, stage_status: str, validator: str, evidence: str = "") -> dict:
                    blocker = detail.get(stage, "")
                    if stage_status in {"ok", "pass"}:
                        blocker = ""
                    elif stage == "rtl" and rtl_blocked and rtl_blocker:
                        blocker = rtl_blocker
                    return {
                        "stage": stage,
                        "status": stage_status,
                        "owner": _owner(stage, stage_status),
                        "validator": validator,
                        "evidence": evidence,
                        "blocker": blocker,
                        "next_action": _next_action(stage, stage_status),
                    }

                def _simple_summary() -> dict:
                    visible_order = [
                        "req",
                        "ssot",
                        "fl_model",
                        "fl_decomp",
                        "fcov_plan",
                        "equivalence_goals",
                        "rtl",
                        "lint",
                        "tb",
                        "sim_debug",
                        "coverage",
                        "goal_audit",
                    ]
                    passed = sum(1 for stage in visible_order if status.get(stage) in {"ok", "pass"})
                    total = len(visible_order)
                    percent = 100 if signoff == "pass" else int(round((passed / total) * 100)) if total else 0
                    audit_blockers = [
                        str(item).lower()
                        for item in (goal_audit.get("blockers", []) if isinstance(goal_audit, dict) else [])
                        if str(item)
                    ]
                    req_needed = req_status != "ok" or any(item == "req" for item in audit_blockers)
                    hard_fail = any(
                        status.get(stage) == "fail"
                        for stage in ("rtl", "lint", "sim_debug", "coverage", "equivalence_goals")
                    )
                    if signoff == "pass":
                        simple_state = "green"
                        headline = "Ready for signoff"
                        message = "All required evidence is green."
                    elif req_needed:
                        simple_state = "needs_review"
                        headline = "One user review is needed"
                        message = "Generated evidence can continue, but requirements need a real review before final green."
                    elif hard_fail:
                        simple_state = "needs_repair"
                        headline = "A generated stage needs repair"
                        message = "ATLAS should route the failed evidence to the owning workflow and rerun downstream checks."
                    elif passed:
                        simple_state = "needs_evidence"
                        headline = "Run the next evidence step"
                        message = "Some stages are complete. Continue the pipeline to collect the missing evidence."
                    else:
                        simple_state = "not_started"
                        headline = "Start the IP pipeline"
                        message = "Create or import SSOT, then run the flow toward RTL, TB, sim, coverage, and signoff."

                    stage_labels = {
                        "req": "Complete requirements review",
                        "ssot": "Complete SSOT",
                        "fl_model": "Generate FL model",
                        "fl_decomp": "Generate model decomposition",
                        "fcov_plan": "Create coverage plan",
                        "equivalence_goals": "Generate equivalence goals",
                        "rtl": "Generate or repair RTL",
                        "lint": "Run lint",
                        "tb": "Generate TB",
                        "sim_debug": "Run simulation and compare",
                        "coverage": "Close coverage evidence",
                        "goal_audit": "Run final evidence audit",
                    }
                    stage_reasons = {
                        "req": "Human-owned design intent must not be guessed.",
                        "ssot": "SSOT is the source of truth for every downstream workflow.",
                        "fl_model": "The executable functional model is the golden behavior reference.",
                        "fl_decomp": "Decomposition tells RTL/TB which design units must exist.",
                        "fcov_plan": "Coverage needs planned bins before signoff.",
                        "equivalence_goals": "Scoreboard checks need explicit FL/RTL goals.",
                        "rtl": "RTL must match SSOT and compile/lint cleanly.",
                        "lint": "DUT-only lint must be clean or explicitly waived.",
                        "tb": "Every SSOT DV scenario needs a runnable test.",
                        "sim_debug": "Simulation must produce fresh zero-fail results.",
                        "coverage": "Coverage must show required functional/cycle evidence.",
                        "goal_audit": "The final audit ties every artifact back to SSOT evidence.",
                    }
                    next_steps: list[dict[str, str]] = []
                    for stage in visible_order:
                        if stage == "req" and req_needed:
                            needs_step = True
                        else:
                            needs_step = status.get(stage) not in {"ok", "pass"}
                        if not needs_step:
                            continue
                        next_steps.append({
                            "stage": stage,
                            "label": stage_labels.get(stage, stage),
                            "owner": "user" if stage == "req" else "atlas",
                            "reason": stage_reasons.get(stage, ""),
                            "status": str(status.get(stage) or "pending"),
                        })
                        if len(next_steps) >= 3:
                            break

                    if not next_steps and signoff != "pass":
                        next_steps.append({
                            "stage": "signoff",
                            "label": "Review final signoff",
                            "owner": "user",
                            "reason": "Tool evidence is available; final acceptance is a user decision.",
                            "status": signoff,
                        })

                    next_stage = next_steps[0]["stage"] if next_steps else "signoff"
                    primary_label = "Run to Green"
                    if simple_state == "needs_review":
                        primary_label = "Open Review"
                    elif simple_state == "green":
                        primary_label = "View Evidence"

                    return {
                        "state": simple_state,
                        "headline": headline,
                        "message": message,
                        "percent": max(0, min(100, percent)),
                        "passed_checks": passed,
                        "total_checks": total,
                        "next_stage": next_stage,
                        "next_steps": next_steps,
                        "primary_action": {
                            "label": primary_label,
                            "kind": "open_stage" if simple_state in {"green", "needs_review"} else "run_pipeline",
                            "stage": next_stage,
                            "flow": "full",
                        },
                        "expert_blockers": blockers[:12],
                    }

                ownership = {
                    "req": _stage_entry("req", req_status, "REQ ledger placeholder/substance check", _first_source(req.get("files") if isinstance(req, dict) else "")),
                    "ssot": _stage_entry("ssot", ssot_status, "canonical SSOT section checker", "yaml/<ip>.ssot.yaml"),
                    "fl_model": _stage_entry("fl_model", fl_model_status, "FunctionalModel API + self-check", _first_source(fl_model.get("source", "") if isinstance(fl_model, dict) else "")),
                    "fl_decomp": _stage_entry("fl_decomp", fl_decomp_status, "decomposition completeness checker", _first_source(fl_decomp.get("source", "") if isinstance(fl_decomp, dict) else "")),
                    "fcov_plan": _stage_entry("fcov_plan", fcov_plan_status, "planned coverage-bin checker", _first_source(fcov_plan.get("source", "") if isinstance(fcov_plan, dict) else "")),
                    "equivalence_goals": _stage_entry("equivalence_goals", equivalence_status, "FL-vs-RTL equivalence goal + scoreboard comparator", _first_source(equivalence.get("compare_evidence", "") if isinstance(equivalence, dict) else "", equivalence.get("evidence", "") if isinstance(equivalence, dict) else "")),
                    "goal_audit": _stage_entry("goal_audit", goal_audit_status, "fl_rtl_goal_audit disk-truth verifier", _first_source(goal_audit.get("source", "") if isinstance(goal_audit, dict) else "")),
                    "rtl": _stage_entry("rtl", rtl_status, "SSOT filelist + DUT compile/lint", _first_source(rtl.get("blocker_source", "") if isinstance(rtl, dict) else "", rtl.get("filelist", "") if isinstance(rtl, dict) else "")),
                    "lint": _stage_entry("lint", lint_status, "DUT-only lint report", _first_source(lint.get("source", "") if isinstance(lint, dict) else "")),
                    "tb": _stage_entry("tb", tb_status, "SSOT scenario implementation checker", "tb/cocotb"),
                    "sim_debug": _stage_entry("sim_debug", sim_status, "fresh cocotb results.xml + scenario pass map", _first_source(results.get("sources", []) if isinstance(results, dict) else [])),
                    "coverage": _stage_entry("coverage", cov_status, "planned functional coverage closure", "cov/coverage.json"),
                    "signoff": _stage_entry("signoff", signoff, "strict SSOT progress gate", "ATLAS /api/progress"),
                }
                return {
                    "status": status,
                    "blockers": blockers,
                    "ownership": ownership,
                    "simple_summary": _simple_summary(),
                    "criteria": {
                        "req": "requirements captured before SSOT",
                        "ssot": "all canonical SSOT sections approved",
                        "fl_model": "executable FL model exists and self-check passes",
                        "fl_decomp": "FL model decomposition exists and drives RTL/TB planning",
                        "fcov_plan": "functional coverage plan exists before RTL signoff",
                        "equivalence_goals": "equivalence goals exist, scoreboard events cover them, and FL-vs-RTL compare passes",
                        "goal_audit": "single audit artifact proves all required REQ->SSOT->FL->RTL->TB->sim->coverage evidence",
                        "rtl": "all expected RTL files approved and compile/lint pass",
                        "tb": "all SSOT DV scenarios have implemented tests",
                        "sim_debug": "latest result XML has tests and zero failures/errors",
                        "coverage": "coverage report is pass with no limitations",
                        "signoff": "SSOT, FL/equivalence, RTL/lint, TB, sim, and coverage all pass",
                    },
                    "detail": detail,
                    "source": "strict-ssot-progress-gate",
                }

            def _build_module(leaf_ssot_path):
                """Read a leaf <ip>/yaml/<ip>.ssot.yaml → architect module dict."""
                p = leaf_ssot_path
                ip_dir = p.parent
                if ip_dir.name == "yaml":
                    ip_dir = ip_dir.parent
                ip_name = ip_dir.name
                top = ip_name
                params, interfaces = [], []
                clocks_n, resets_n = 0, 0
                addr = ""
                doc: dict[str, Any] = {}

                def _top_name(v):
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, dict):
                        for key in ("name", "module", "top", "id"):
                            val = v.get(key)
                            if isinstance(val, str) and val.strip():
                                return val.strip()
                    return ip_name

                def _param_value(it):
                    for key in ("value", "default", "v"):
                        if key in it:
                            return it.get(key)
                    return ""

                def _iface_proto(it):
                    return (
                        it.get("proto") or it.get("protocol") or it.get("type")
                        or it.get("busType") or it.get("bus_type") or "AXI4"
                    )

                def _iface_side(role, idx):
                    role_s = str(role or "").lower()
                    if role_s == "master":
                        return "right"
                    if role_s == "slave":
                        return "left"
                    return ["right", "left", "top", "bottom"][idx % 4]

                if _yaml is not None:
                    try:
                        loaded_doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
                        if isinstance(loaded_doc, dict):
                            doc = loaded_doc
                            top = _top_name(doc.get("top_module") or top)
                            io_list = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
                            cl = doc.get("clocks") or io_list.get("clock_domains") or []
                            rs = doc.get("resets") or io_list.get("resets") or []
                            clocks_n, resets_n = len(cl), len(rs)
                            for k in ("parameters", "params"):
                                if isinstance(doc.get(k), list):
                                    for it in doc[k][:6]:
                                        if isinstance(it, dict):
                                            nm = it.get("name") or it.get("k")
                                            vv = _param_value(it)
                                            if nm is not None:
                                                params.append({"k": str(nm), "v": str(vv)})
                            bif = (
                                doc.get("busInterfaces")
                                or doc.get("bus_interfaces")
                                or doc.get("interfaces")
                                or io_list.get("interfaces")
                                or []
                            )
                            if isinstance(bif, list):
                                for i, it in enumerate(bif[:8]):
                                    if not isinstance(it, dict): continue
                                    role = str(it.get("role") or "slave")
                                    interfaces.append({
                                        "name": str(it.get("name") or f"if{i}"),
                                        "proto": str(_iface_proto(it)),
                                        "role":  role,
                                        "side":  str(it.get("side") or _iface_side(role, i)),
                                        "width": int(it.get("width") or 0) or None,
                                    })
                            for c in cl[:2]:
                                if isinstance(c, dict):
                                    interfaces.append({"name": c.get("name") or "clk",
                                                       "proto": "CLK", "role": "slave", "side": "left"})
                            for r in rs[:2]:
                                if isinstance(r, dict):
                                    interfaces.append({"name": r.get("name") or "rst_n",
                                                       "proto": "RST", "role": "slave", "side": "left"})
                            mm = doc.get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base is not None: addr = _hex_addr(base)
                    except Exception:
                        pass
                rtl_dir = ip_dir / "rtl"
                rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
                list_path = ip_dir / "list" / f"{ip_dir.name}.f"
                rtl_detail = ""
                if not rtl_files:
                    rtl_st = "partial" if rtl_dir.is_dir() else "pending"
                    rtl_detail = "rtl directory exists but no RTL files" if rtl_dir.is_dir() else "no rtl directory"
                elif not list_path.is_file():
                    rtl_st = "partial"
                    rtl_detail = f"RTL files exist but filelist missing: {list_path.relative_to(PROJECT_ROOT)}"
                else:
                    missing = []
                    try:
                        for raw in list_path.read_text(encoding="utf-8", errors="replace").splitlines():
                            line = raw.split("//", 1)[0].strip()
                            if not line or not line.endswith((".v", ".sv", ".vh", ".svh")):
                                continue
                            candidate = ip_dir / line
                            if not candidate.is_file():
                                candidate = PROJECT_ROOT / line
                            if not candidate.is_file():
                                missing.append(line)
                    except OSError as e:
                        missing.append(f"{list_path}: {e}")
                    if missing:
                        rtl_st = "partial"
                        rtl_detail = "filelist has missing entries: " + ", ".join(missing[:3])
                    else:
                        rtl_st = "ok"
                        rtl_detail = f"filelist OK: {list_path.relative_to(PROJECT_ROOT)}"
                sim_dir = ip_dir / "sim"
                sim_files = []
                if sim_dir.is_dir():
                    sim_files = list(sim_dir.rglob("*.log")) + list(sim_dir.rglob("*.vcd"))
                sim_history = []
                hist = sim_dir / "history.json"
                if hist.is_file():
                    try:
                        h = json.loads(hist.read_text(encoding="utf-8"))
                        if isinstance(h, dict) and isinstance(h.get("runs"), list):
                            sim_history = h["runs"][-12:]
                    except Exception:
                        pass
                tb_dir = ip_dir / "tb"
                cocotb_dir = tb_dir / "cocotb"
                tb_files = []
                if tb_dir.is_dir():
                    tb_files = (
                        list(tb_dir.rglob("*.py"))
                        + list(tb_dir.rglob("*.sv"))
                        + list(tb_dir.rglob("*.v"))
                    )
                cov_json = ip_dir / "cov" / "coverage.json"
                cov_detail = ""
                sim_debug_st = "pending"
                sim_debug_detail = "no VCD or coverage artifacts"
                if cov_json.is_file():
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        lines = cov_doc.get("lines") if isinstance(cov_doc, dict) else {}
                        branches = cov_doc.get("branches") if isinstance(cov_doc, dict) else {}
                        fsm = cov_doc.get("fsm") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict) and functional.get("pct") is not None:
                            cov_detail = f", functional coverage {functional.get('pct')}%"
                        static_bits = []
                        for name, item in (("line", lines), ("branch", branches), ("fsm", fsm)):
                            if isinstance(item, dict):
                                source = item.get("source") or "unknown"
                                total = item.get("total")
                                pct = item.get("pct")
                                if str(source).startswith("static"):
                                    static_bits.append(f"{name} static {total}")
                                elif pct is not None:
                                    static_bits.append(f"{name} {pct}%")
                        if static_bits:
                            cov_detail += "; " + ", ".join(static_bits)
                    except Exception:
                        pass
                ssot_state = _load_ssot_state(ip_name)
                ssot_st = "ok"
                if ssot_state.get("approved") and not p.is_file():
                    ssot_st = "approved"
                elif ssot_state.get("status") == "planned" and not p.is_file():
                    ssot_st = "planned"
                tb_st = "ok" if tb_files else ("partial" if tb_dir.is_dir() else "pending")
                sim_debug_artifacts = []
                sim_wave_artifacts = []
                sim_result_artifacts = []
                sim_coverage_artifacts = []
                if sim_dir.is_dir():
                    sim_wave_artifacts.extend(list(sim_dir.rglob("*.vcd")))
                    sim_wave_artifacts.extend(list(sim_dir.rglob("*.fst")))
                    sim_coverage_artifacts.extend(list(sim_dir.rglob("coverage_report.*")))
                    sim_result_artifacts.extend(list(sim_dir.rglob("*results.xml")))
                cocotb_build = ip_dir / "tb" / "cocotb"
                if cocotb_build.is_dir():
                    sim_wave_artifacts.extend(list(cocotb_build.rglob("*.vcd")))
                    sim_wave_artifacts.extend(list(cocotb_build.rglob("*.fst")))
                    sim_result_artifacts.extend(list(cocotb_build.rglob("*results.xml")))
                cov_dir = ip_dir / "cov"
                if cov_dir.is_dir():
                    sim_coverage_artifacts.extend(list(cov_dir.rglob("coverage.json")))
                    sim_coverage_artifacts.extend(list(cov_dir.rglob("toggle.json")))
                sim_debug_artifacts = sim_wave_artifacts + sim_result_artifacts + sim_coverage_artifacts
                if sim_result_artifacts and (sim_wave_artifacts or sim_coverage_artifacts):
                    sim_debug_st = "ok"
                    sim_debug_detail = f"{len(sim_debug_artifacts)} debug artifact(s)"
                    if cov_detail:
                        sim_debug_detail += cov_detail
                elif sim_debug_artifacts:
                    sim_debug_st = "partial"
                    sim_debug_detail = (
                        f"{len(sim_debug_artifacts)} debug artifact(s); "
                        "needs result XML plus waveform or coverage artifact"
                    )
                req_prog = _req_progress(ip_dir)
                fl_model_prog = _fl_model_progress(ip_dir, doc)
                fl_decomp_prog = _fl_decomp_progress(ip_dir)
                fcov_plan_prog = _fcov_plan_progress(ip_dir)
                equivalence_prog = _equivalence_progress(ip_dir)
                goal_audit_prog = _goal_audit_progress(ip_dir)
                artifact_status = {
                    "req": req_prog["status"],
                    "ssot": ssot_st,
                    "fl_model": fl_model_prog["status"],
                    "fl_decomp": fl_decomp_prog["status"],
                    "fcov_plan": fcov_plan_prog["status"],
                    "equivalence_goals": equivalence_prog["status"],
                    "goal_audit": goal_audit_prog["status"],
                    "rtl": rtl_st,
                    "tb": tb_st,
                    "sim_debug": sim_debug_st,
                }
                artifact_detail = {
                    "req": f"{len(req_prog.get('files', []))} requirement artifact(s), {req_prog.get('bytes', 0)}B",
                    "ssot": (
                        f"parsed {p.relative_to(PROJECT_ROOT)}"
                        + ("; approved via .session state" if ssot_state.get("approved") else "")
                    ),
                    "fl_model": fl_model_prog.get("source") or "no executable FL model",
                    "fl_decomp": (
                        f"{fl_decomp_prog.get('units', 0)} unit(s): "
                        + ", ".join(fl_decomp_prog.get("kinds") or [])
                    ),
                    "fcov_plan": f"{fcov_plan_prog.get('bins', 0)} bin(s)",
                    "equivalence_goals": (
                        f"{equivalence_prog.get('passed', 0)}/"
                        f"{equivalence_prog.get('total', 0)} pass, "
                        f"{equivalence_prog.get('blocked', 0)} blocked, "
                        f"{equivalence_prog.get('untested', 0)} untested"
                    ),
                    "goal_audit": (
                        f"{goal_audit_prog.get('passed_checks', 0)}/"
                        f"{goal_audit_prog.get('total_checks', 0)} checks, "
                        f"{goal_audit_prog.get('failed_checks', 0)} failed"
                    ),
                    "rtl": rtl_detail,
                    "tb": (
                        f"{len(tb_files)} TB artifact(s)"
                        + (" under tb/cocotb" if cocotb_dir.is_dir() else "")
                        + cov_detail
                        if tb_files else "no tb artifacts"
                    ),
                    "sim_debug": sim_debug_detail,
                }
                progress = {
                    "req": req_prog,
                    "ssot": _ssot_progress(doc),
                    "fl_model": fl_model_prog,
                    "fl_decomp": fl_decomp_prog,
                    "fcov_plan": fcov_plan_prog,
                    "equivalence_goals": equivalence_prog,
                    "goal_audit": goal_audit_prog,
                    "rtl": _rtl_progress(ip_dir, doc),
                    "compile": _compile_progress(ip_dir),
                    "lint": _lint_progress(ip_dir, doc),
                    "sim": _sim_progress(ip_dir, doc),
                }
                gate = _strict_gate_from_progress(progress)
                artifact_status["rtl"] = gate["status"].get("rtl", rtl_st)
                artifact_detail["rtl"] = gate["detail"].get("rtl", rtl_detail)
                top_meta = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
                ssot_kind = str(top_meta.get("type") or "").strip()
                return {
                    "id": ip_name,
                    "name": top,
                    "label": top,
                    "kind": _kind_for(ssot_kind or ip_name),
                    "params": params,
                    "status": gate["status"],
                    "status_detail": gate["detail"],
                    "status_source": {
                        "req": gate["source"],
                        "ssot": gate["source"],
                        "fl_model": gate["source"],
                        "fl_decomp": gate["source"],
                        "fcov_plan": gate["source"],
                        "equivalence_goals": gate["source"],
                        "goal_audit": gate["source"],
                        "rtl": gate["source"],
                        "compile": gate["source"],
                        "lint": gate["source"],
                        "tb": gate["source"],
                        "sim_debug": gate["source"],
                        "coverage": gate["source"],
                        "signoff": gate["source"],
                    },
                    "artifact_status": artifact_status,
                    "artifact_detail": artifact_detail,
                    "artifact_source": {
                        "req": "filesystem-artifact",
                        "ssot": "yaml-parse",
                        "fl_model": "model/fl_model_check.json",
                        "fl_decomp": "model/decomposition.json",
                        "fcov_plan": "cov/fcov_plan.json",
                        "equivalence_goals": "verify/equivalence_goals.json",
                        "goal_audit": "sim/fl_rtl_goal_audit.json",
                        "rtl": "rtl-filelist",
                        "tb": "filesystem-artifact",
                        "sim_debug": "filesystem-artifact",
                    },
                    "interfaces": interfaces,
                    "addr": addr,
                    "rtl_files": [f.relative_to(PROJECT_ROOT).as_posix() for f in rtl_files],
                    "ssot_path": p.relative_to(PROJECT_ROOT).as_posix(),
                    "ip_dir": ip_dir.relative_to(PROJECT_ROOT).as_posix(),
                    "clocks": clocks_n,
                    "resets": resets_n,
                    "sim_history": sim_history,
                    "ssot_mtime": p.stat().st_mtime,
                    "progress": progress,
                    "signoff": gate,
                    "simple_summary": gate.get("simple_summary", {}),
                }

            def _aggregate_status(modules):
                if not modules:
                    return {
                        "req": "pending", "ssot": "pending", "fl_model": "pending",
                        "fl_decomp": "pending", "fcov_plan": "pending",
                        "equivalence_goals": "pending", "goal_audit": "pending",
                        "rtl": "pending", "lint": "unknown",
                        "tb": "pending", "sim_debug": "pending", "coverage": "unknown",
                        "signoff": "pending",
                    }
                def _all(stage: str, value: str) -> bool:
                    return all(m.get("status", {}).get(stage) == value for m in modules)
                def _any(stage: str, *values: str) -> bool:
                    return any(m.get("status", {}).get(stage) in values for m in modules)
                return {
                    "req": "ok" if _all("req", "ok") else (
                        "partial" if _any("req", "ok", "partial") else "pending"
                    ),
                    "ssot": "ok" if _all("ssot", "ok") else (
                        "partial" if _any("ssot", "ok", "partial") else "pending"
                    ),
                    "fl_model": "pass" if _all("fl_model", "pass") else (
                        "partial" if _any("fl_model", "pass", "partial") else "pending"
                    ),
                    "fl_decomp": "pass" if _all("fl_decomp", "pass") else (
                        "partial" if _any("fl_decomp", "pass", "partial") else "pending"
                    ),
                    "fcov_plan": "pass" if _all("fcov_plan", "pass") else (
                        "partial" if _any("fcov_plan", "pass", "partial") else "pending"
                    ),
                    "equivalence_goals": "fail" if _any("equivalence_goals", "fail") else (
                        "blocked" if _any("equivalence_goals", "blocked") else (
                            "pass" if _all("equivalence_goals", "pass") else (
                                "partial" if _any("equivalence_goals", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "goal_audit": "fail" if _any("goal_audit", "fail") else (
                        "blocked" if _any("goal_audit", "blocked", "stale") else (
                            "pass" if _all("goal_audit", "pass") else (
                                "partial" if _any("goal_audit", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "rtl": "fail" if _any("rtl", "fail") else (
                        "ok" if _all("rtl", "ok") else ("partial" if _any("rtl", "ok", "partial") else "pending")
                    ),
                    "lint": "fail" if _any("lint", "fail") else (
                        "pass" if _all("lint", "pass") else "unknown"
                    ),
                    "tb": "ok" if _all("tb", "ok") else (
                        "partial" if _any("tb", "ok", "partial") else "pending"
                    ),
                    "sim_debug": "fail" if _any("sim_debug", "fail") else (
                        "blocked" if _any("sim_debug", "blocked") else (
                            "ok" if _all("sim_debug", "ok") else (
                                "partial" if _any("sim_debug", "ok", "partial") else "pending"
                            )
                        )
                    ),
                    "coverage": "fail" if _any("coverage", "fail") else (
                        "blocked" if _any("coverage", "blocked") else (
                            "pass" if _all("coverage", "pass") else "unknown"
                        )
                    ),
                    "signoff": "fail" if _any("signoff", "fail") else (
                        "blocked" if _any("signoff", "blocked") else (
                            "pass" if _all("signoff", "pass") else (
                                "partial" if _any("signoff", "partial") else "pending"
                            )
                        )
                    ),
                }

            project_name = PROJECT_ROOT.name or "project"
            soc_path = PROJECT_ROOT / "soc.ssot.yaml"
            want_raw = str(ip or scope or "").strip().strip("/")
            want_parts = [part for part in want_raw.split("/") if part]
            want_ip = (
                want_parts[-2]
                if len(want_parts) >= 3
                else want_parts[0]
                if want_parts
                else ""
            )

            def _scoped_leaf_paths(ip_name: str) -> list[Path]:
                if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip_name or ""):
                    return []
                seen: set[Path] = set()
                out: list[Path] = []
                bases = [PROJECT_ROOT, SOURCE_ROOT, PROJECT_ROOT / "common_ai_agent"]
                for base in bases:
                    candidates = [
                        base / ip_name / "yaml" / f"{ip_name}.ssot.yaml",
                        *(base.glob(f"*/{ip_name}/yaml/{ip_name}.ssot.yaml") if base.is_dir() else []),
                    ]
                    for candidate in candidates:
                        try:
                            resolved = candidate.resolve()
                            resolved.relative_to(PROJECT_ROOT)
                        except Exception:
                            try:
                                resolved.relative_to(SOURCE_ROOT)
                            except Exception:
                                continue
                        if resolved in seen or not resolved.is_file():
                            continue
                        if any(part in SKIP_DIRS or part.startswith(".") for part in resolved.parts):
                            continue
                        seen.add(resolved)
                        out.append(resolved)
                return out

            if want_ip:
                modules = [_build_module(p) for p in _scoped_leaf_paths(want_ip)]
                modules.sort(key=lambda m: m["id"])
                cluster = {
                    "id": "ips", "name": "ips", "label": "Project IPs",
                    "x": 60, "y": 80, "w": 1200, "h": 600,
                    "status": _aggregate_status(modules),
                    "modules": modules,
                }
                return JSONResponse({
                    "name": project_name,
                    "version": "live",
                    "clusters": [cluster] if modules else [],
                    "busses": [],
                    "addrMap": [],
                    "module_count": len(modules),
                    "source": "scoped-dir-walk",
                    "scope": want_ip,
                })

            # ── Tier 1: SoC-level SSOT exists → use it as the spine ──
            if _yaml is not None and soc_path.is_file():
                try:
                    soc_doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8", errors="replace")) or {}
                except Exception as e:
                    return JSONResponse({"error": f"soc.ssot.yaml parse: {e}", "clusters": []},
                                        status_code=500)
                if not isinstance(soc_doc, dict): soc_doc = {}

                instances = soc_doc.get("instances") or []
                clusters_def = soc_doc.get("clusters") or []
                connections = soc_doc.get("connections") or []
                addr_map = soc_doc.get("addrMap") or []

                # Build module dict per instance, looking up its leaf SSOT.
                inst_to_mod = {}
                for inst in instances:
                    if not isinstance(inst, dict): continue
                    iid = inst.get("id")
                    if not iid: continue
                    leaf = inst.get("ssot")
                    leaf_path = (PROJECT_ROOT / leaf) if leaf else None
                    if leaf_path and leaf_path.is_file():
                        m = _build_module(leaf_path)
                    else:
                        # No leaf SSOT yet — minimal stub.
                        m = {
                            "id": iid, "name": iid, "label": iid,
                            "kind": _kind_for(inst.get("kind") or iid),
                            "params": [], "interfaces": [],
                            "status": {"ssot": "pending", "rtl": "pending", "sim": "pending"},
                            "rtl_files": [], "ssot_path": leaf or "",
                            "ip_dir": "", "addr": "",
                            "clocks": 0, "resets": 0, "sim_history": [], "ssot_mtime": 0,
                        }
                    # Apply instance-level overrides.
                    m["id"] = iid
                    if inst.get("name"):  m["name"] = inst["name"]; m["label"] = inst["name"]
                    if inst.get("addr") is not None: m["addr"] = _hex_addr(inst["addr"])
                    if inst.get("kind"):  m["kind"] = inst["kind"]
                    # Saved layout: `instances[].x/y` from soc.ssot.yaml
                    # (set by /api/soc/layout). Surfaces as module.savedX/Y
                    # so the frontend can use it as the default block
                    # position when localStorage doesn't override.
                    if isinstance(inst.get("x"), (int, float)): m["savedX"] = float(inst["x"])
                    if isinstance(inst.get("y"), (int, float)): m["savedY"] = float(inst["y"])
                    # Separate full-SoC canvas placement. Cluster/module
                    # views use x/y in a different coordinate system.
                    if isinstance(inst.get("top_x"), (int, float)): m["savedTopX"] = float(inst["top_x"])
                    if isinstance(inst.get("top_y"), (int, float)): m["savedTopY"] = float(inst["top_y"])
                    if isinstance(inst.get("overrides"), dict):
                        # Surface overrides as extra params.
                        for k, v in inst["overrides"].items():
                            m["params"].append({"k": str(k), "v": str(v)})
                    inst_to_mod[iid] = m

                # Group modules by cluster membership. Anything not in a
                # cluster falls into a synthetic "uncategorized" cluster.
                # While we're walking, propagate `cluster.role` → each
                # member's `kind` (CPU/BUS/MEM/PERIPH/ANALOG). The role
                # is the architect's explicit declaration and beats the
                # name heuristic (e.g. cortexa15_0 has no "cpu" in its
                # name; without role propagation it would fall through
                # to "periph").
                claimed = set()
                clusters_out = []
                for c in clusters_def:
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name")
                    if not cid: continue
                    members = c.get("members") or []
                    role_kind = _kind_from_role(c.get("role"))
                    cmods = []
                    for mid in members:
                        if mid not in inst_to_mod: continue
                        mod = inst_to_mod[mid]
                        # Role-from-cluster wins UNLESS the instance had
                        # an explicit `kind:` override in soc.ssot.yaml
                        # (set above when applying instance overrides).
                        # We detect "explicit override" by checking the
                        # raw instance dict, not the heuristic-derived
                        # value already in mod.
                        inst_def = next((i for i in instances
                                         if isinstance(i, dict) and i.get("id") == mid), {})
                        if not inst_def.get("kind") and role_kind:
                            mod["kind"] = role_kind
                        cmods.append(mod)
                    for m in members: claimed.add(m)
                    clusters_out.append({
                        "id": cid,
                        "name": cid,
                        "label": c.get("label") or cid,
                        "x": c.get("x", 60), "y": c.get("y", 80),
                        "w": c.get("w", 1200), "h": c.get("h", 600),
                        "role": c.get("role"),
                        "status": _aggregate_status(cmods),
                        "modules": cmods,
                    })
                stray = [m for iid, m in inst_to_mod.items() if iid not in claimed]
                if stray:
                    clusters_out.append({
                        "id": "uncategorized", "name": "uncategorized",
                        "label": "Uncategorized",
                        "x": 60, "y": 80, "w": 1200, "h": 600,
                        "status": _aggregate_status(stray),
                        "modules": stray,
                    })

                # Normalize connections — frontend renderer expects
                # {from: 'inst/iface', to: 'inst/iface', proto: 'AXI4'}.
                norm_conns = []
                for cn in connections:
                    if not isinstance(cn, dict): continue
                    if cn.get("from") and cn.get("to"):
                        norm_conns.append({
                            "from": str(cn["from"]),
                            "to":   str(cn["to"]),
                            "proto": str(cn.get("proto") or "AXI4"),
                        })

                return JSONResponse({
                    "name": soc_doc.get("name") or project_name,
                    "version": str(soc_doc.get("version") or "live"),
                    "clusters": clusters_out,
                    "busses": norm_conns,
                    "connections": norm_conns,        # alias for clarity
                    "addrMap": [
                        {**e, "base": _hex_addr(e.get("base")), "range": _hex_addr(e.get("range"))}
                        for e in (addr_map if isinstance(addr_map, list) else [])
                        if isinstance(e, dict)
                    ],
                    "module_count": len(inst_to_mod),
                    "source": "soc.ssot.yaml",
                    "soc_ssot_path": soc_path.relative_to(PROJECT_ROOT).as_posix(),
                    "soc_ssot_mtime": soc_path.stat().st_mtime,
                })

            # ── Tier 2: no soc.ssot.yaml → fall back to dir-walk ──
            modules = []
            for p in PROJECT_ROOT.rglob("*.ssot.yaml"):
                if any(part in SKIP_DIRS or part.startswith(".")
                       for part in p.parts):
                    continue
                if p.name == "soc.ssot.yaml": continue  # handled above
                modules.append(_build_module(p))
            seen_ids = {m.get("id") for m in modules}
            session_root = PROJECT_ROOT / ".session"
            if session_root.is_dir():
                for state_path in session_root.rglob("ssot-gen/state.json"):
                    # Only accept owner-scoped trees:
                    #     .session/<owner>/<ip>/ssot-gen/state.json   (4 parts)
                    # Legacy bare-IP layouts written by pre-owner
                    # backends:
                    #     .session/<ip>/ssot-gen/state.json           (3 parts)
                    # used to leak ip_name = '<ip>' into the SoC view
                    # forever, even after the user wiped that owner
                    # from disk. Skip anything shorter than 4 segments.
                    try:
                        rel_parts = state_path.relative_to(session_root).parts
                    except Exception:
                        continue
                    if len(rel_parts) != 4 or rel_parts[2] != "ssot-gen":
                        continue
                    ip_name = rel_parts[1]
                    if ip_name in seen_ids or not _valid_ip_name(ip_name):
                        continue
                    try:
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                        if not isinstance(state, dict):
                            state = {}
                    except Exception:
                        state = {}
                    status = (
                        "approved" if state.get("approved")
                        else "answered" if str(state.get("status") or "").lower() == "answered"
                        else "planned"
                    )
                    raw_kind = str(state.get("kind") or ip_name)
                    low_kind = raw_kind.lower()
                    if any(s in low_kind for s in (
                        "i2c", "uart", "spi", "gpio", "timer", "pwm",
                        "peripheral", "controller",
                    )):
                        module_kind = "periph"
                    else:
                        module_kind = _kind_for(raw_kind)
                    modules.append({
                        "id": ip_name,
                        "name": ip_name,
                        "label": ip_name,
                        "kind": module_kind,
                        "params": [],
                        "status": {
                            "ssot": status,
                            "rtl": "pending",
                            "tb": "pending",
                            "sim": "pending",
                        },
                        "status_detail": {
                            "ssot": (
                                f"{status}; waiting for /to-ssot {ip_name}"
                                if status == "approved"
                                else f"answered; waiting for approve {ip_name}"
                                if status == "answered"
                                else f"planned; answer Web Q&A, then approve {ip_name}"
                            ),
                            "rtl": "blocked until SSOT ok",
                            "tb": "blocked until RTL/TB generation",
                            "sim": "blocked until TB/SIM generation",
                        },
                        "status_source": {
                            "ssot": ".session-state",
                            "rtl": "filesystem-artifact",
                            "tb": "filesystem-artifact",
                            "sim": "filesystem-artifact",
                        },
                        "interfaces": [],
                        "addr": "",
                        "rtl_files": [],
                        "ssot_path": f"{ip_name}/yaml/{ip_name}.ssot.yaml",
                        "ip_dir": ip_name,
                        "clocks": 0,
                        "resets": 0,
                        "sim_history": [],
                        "ssot_mtime": state_path.stat().st_mtime,
                    })
            modules.sort(key=lambda m: m["id"])
            cluster = {
                "id": "ips", "name": "ips", "label": "Project IPs",
                "x": 60, "y": 80, "w": 1200, "h": 600,
                "status": _aggregate_status(modules),
                "modules": modules,
            }
            return JSONResponse({
                "name": project_name,
                "version": "live",
                "clusters": [cluster] if modules else [],
                "busses": [],
                "addrMap": [],
                "module_count": len(modules),
                "source": "dir-walk",
            })
        except Exception as e:
            return JSONResponse({"error": str(e), "clusters": []}, status_code=500)

    @app.get("/api/progress")
    def api_progress(scope: str = "", ip: str = ""):
        """Return SSOT-derived implementation progress for the Atlas sidebar.

        The heavy lifting already lives in /api/soc because the architect
        canvas needs the same SSOT/RTL/TB/sim evidence. This endpoint flattens
        that structure into a compact shape for the normal chat workspace:
        one selected module plus the full module list. All metrics are derived
        from the canonical leaf SSOT YAML and disk artifacts, not from fixed IP
        templates or assistant prose.
        """
        resp = api_soc(scope=scope, ip=ip)
        try:
            data = json.loads(resp.body.decode("utf-8"))
        except Exception as e:
            return JSONResponse({"error": f"soc progress parse: {e}", "modules": []}, status_code=500)

        modules: list[dict[str, Any]] = []
        for cluster in data.get("clusters", []) if isinstance(data, dict) else []:
            if not isinstance(cluster, dict):
                continue
            for mod in cluster.get("modules", []) or []:
                if not isinstance(mod, dict):
                    continue
                entry = {
                    "id": mod.get("id") or mod.get("name") or "",
                    "name": mod.get("name") or mod.get("id") or "",
                    "label": mod.get("label") or mod.get("name") or mod.get("id") or "",
                    "kind": mod.get("kind") or "",
                    "ip_dir": mod.get("ip_dir") or "",
                    "ssot_path": mod.get("ssot_path") or "",
                    "status": mod.get("status") or {},
                    "status_detail": mod.get("status_detail") or {},
                    "status_source": mod.get("status_source") or {},
                    "artifact_status": mod.get("artifact_status") or {},
                    "artifact_detail": mod.get("artifact_detail") or {},
                    "artifact_source": mod.get("artifact_source") or {},
                    "progress": mod.get("progress") or {},
                    "signoff": mod.get("signoff") or {},
                    "simple_summary": (
                        mod.get("simple_summary")
                        or (mod.get("signoff") or {}).get("simple_summary")
                        or {}
                    ),
                }
                modules.append(entry)

        want = (ip or scope or "").strip().strip("/")
        selected = None
        if want:
            selected = next((
                m for m in modules
                if want in {str(m.get("id") or ""), str(m.get("name") or ""), str(m.get("ip_dir") or "")}
            ), None)
            if selected is None:
                selected = next((
                    m for m in modules
                    if str(m.get("ip_dir") or "").startswith(want + "/")
                    or str(m.get("ssot_path") or "").startswith(want + "/")
                ), None)
        if selected is None and modules:
            selected = modules[0]

        return JSONResponse({
            "project": data.get("name") if isinstance(data, dict) else PROJECT_ROOT.name,
            "source": data.get("source") if isinstance(data, dict) else "",
            "scope": want,
            "selected": selected,
            "modules": modules,
            "module_count": len(modules),
        })

    # ── Jobs (HTTP-worker dispatch tracker) ────────────────────────
    # Routes + state live in src/atlas_api_jobs.py (phase 6 of split).
    # register_jobs_routes() is called below near the other registrars.

    _WORKFLOW_SLASHES = {
        "/wf", "/workflow",
        "/ip", "/use",
        "/session",
        "/new-ip", "/ni",
        "/import", "/imp",
        "/grill-me", "/grill", "/g",
        "/to-ssot", "/ssot", "/ts",
        "/resolve-rtl-blockers", "/rrb",
        "/validate-yaml",
        "/ssot-fl-model", "/sfm",
        "/ssot-equiv-goals", "/equiv-goals", "/seg",
        "/repair-equiv", "/repair-equivalence", "/reqv",
        "/ssot-rtl", "/sr",
        "/repair-rtl", "/rrtl",
        "/lint", "/l",
        "/tb",
        "/ssot-tb", "/stb",
        "/ssot-tb-cocotb", "/stb-cocotb",
        "/ssot-tb-uvm", "/stb-uvm",
        "/ssot-tb-verilog", "/stb-verilog", "/ssot-tb-sv", "/stb-sv",
        "/sim", "/s",
        "/sim-debug", "/sd",
        "/coverage", "/cov",
        "/goal-audit", "/audit", "/ga",
        "/signoff",
    }

    _STAGE_RUNNERS = {
        "ssot-rtl": {
            "workflow": "rtl-gen",
            "template": "ssot-rtl",
            "artifact_hint": "rtl/",
        },
        "ssot-fl-model": {
            "workflow": "fl-model-gen",
            "template": "ssot-fl-model",
            "artifact_hint": "model/ and cov/fcov_plan.json",
        },
        "ssot-equiv-goals": {
            "workflow": "fl-model-gen",
            "template": "ssot-equiv-goals",
            "artifact_hint": "verify/equivalence_goals.json",
        },
        "lint": {
            "workflow": "lint",
            "template": "lint-fix",
            "artifact_hint": "lint/dut_lint.json",
        },
        "ssot-tb": {
            "workflow": "tb-gen",
            "template": "ssot-tb-cocotb",
            "artifact_hint": "tb/cocotb/ and sim/",
        },
        "ssot-tb-cocotb": {
            "workflow": "tb-gen",
            "template": "ssot-tb-cocotb",
            "artifact_hint": "tb/cocotb/ and sim/",
        },
        "ssot-tb-uvm": {
            "workflow": "tb-gen",
            "template": "ssot-tb-uvm",
            "artifact_hint": "tb/uvm/ and sim/",
        },
        "ssot-tb-verilog": {
            "workflow": "tb-gen",
            "template": "ssot-tb-verilog",
            "artifact_hint": "tb/tb_*.sv and sim/",
        },
        "sim": {
            "workflow": "sim",
            "template": "sim-debug",
            "artifact_hint": "sim/results.xml, sim/scoreboard_events.jsonl, and waveform/coverage artifacts",
        },
        "sim-debug": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "sim/fl_rtl_compare.json and sim/mismatch_classification.json",
        },
        "coverage": {
            "workflow": "coverage",
            "template": "coverage_iter",
            "artifact_hint": "cov/coverage.json and sim/coverage_report.md",
        },
        "goal-audit": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "sim/fl_rtl_goal_audit.json",
        },
        "signoff": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "ATLAS /api/progress signoff gate",
        },
    }

    _SSOT_REQUIRED_DECISIONS = [
        ("purpose", "IP purpose / one sentence behavior"),
        ("bus_interface", "bus interface and role, e.g. APB4 slave"),
        ("register_map", "register map, address offsets, access policies"),
        ("clock_reset", "clock/reset names, frequency, reset polarity"),
        ("interrupt", "interrupt behavior, or explicit none"),
        ("memory_map", "memory map/base address requirement, or explicit none"),
        ("parameters", "parameters and defaults, or explicit none"),
        ("submodule_structure", "leaf submodule hierarchy and ownership"),
        ("test_expectation", "minimum cocotb/pyuvm TB/SIM acceptance expectations"),
    ]

    _SSOT_IMPORT_SECTION_TODO_SPECS = [
        ("top_module", "00 Top Module Identity", ("purpose", "submodule_structure")),
        ("sub_modules", "01 Sub-Module List", ("submodule_structure", "purpose")),
        ("parameters", "02 Parameters", ("parameters", "clock_reset", "memory_map")),
        ("io_list", "03 IO List", ("bus_interface", "clock_reset", "interrupt")),
        ("features", "04 Main Features", ("purpose", "register_map", "memory_map", "interrupt")),
        ("dataflow", "05 Data Flow", ("purpose", "bus_interface", "memory_map", "submodule_structure")),
        ("function_model", "06 Function Model", ("purpose", "register_map", "memory_map", "test_expectation")),
        ("cycle_model", "07 Cycle Model", ("clock_reset", "bus_interface", "test_expectation")),
        ("clock_reset_domains", "08 Clock & Reset Domain", ("clock_reset",)),
        ("cdc_requirements", "09 CDC Requirements", ("clock_reset", "bus_interface")),
        ("rdc_requirements", "10 RDC Requirements", ("clock_reset",)),
        ("registers", "11 Registers", ("register_map", "bus_interface")),
        ("memory", "12 Memory Requirements", ("memory_map", "parameters")),
        ("interrupts", "13 Interrupt", ("interrupt", "register_map")),
        ("fsm", "14 FSM", ("submodule_structure", "purpose", "test_expectation")),
        ("timing", "15 Timing & Performance", ("clock_reset", "parameters", "test_expectation")),
        ("power", "16 Power Intent", ("clock_reset", "parameters")),
        ("security", "17 Security & Safety", ("purpose", "bus_interface", "register_map")),
        ("error_handling", "18 Error Handling", ("interrupt", "register_map", "test_expectation")),
        ("debug_observability", "19 Debug & Observability", ("test_expectation", "interrupt", "clock_reset")),
        ("integration", "20 Integration Contract", ("bus_interface", "memory_map", "submodule_structure")),
        ("dft", "21 DFT / DFD", ("test_expectation", "clock_reset")),
        ("synthesis", "22 Synthesis / Implementation Constraints", ("parameters", "clock_reset", "submodule_structure")),
        ("coding_rules", "23 Coding Rules", ("parameters", "submodule_structure")),
        ("reuse_modules", "24 Reuse Modules", ("submodule_structure", "purpose")),
        ("custom", "25 Custom Extensions", ("purpose", "parameters", "test_expectation")),
        ("dir_structure", "26 Dir Structure", ("submodule_structure", "purpose")),
        ("filelist", "27 Filelist", ("submodule_structure", "purpose")),
        ("test_requirements", "28 Test Requirements / DV Plan", ("test_expectation", "bus_interface", "register_map", "interrupt")),
        ("quality_gates", "29 Quality Gates / Pass Criteria", ("test_expectation", "clock_reset", "parameters")),
        ("traceability", "30 Traceability", ("purpose", "test_expectation", "submodule_structure")),
        ("workflow_todos", "31 Workflow TODOs / Downstream Task Contract", ("test_expectation", "submodule_structure", "purpose")),
        ("generation_flow", "32 Generation Flow", ("purpose", "test_expectation")),
    ]

    _SSOT_IMPORT_EXTENSIONS = {
        ".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".sv", ".svh",
        ".v", ".vh", ".py", ".csv", ".tsv", ".xml", ".f", ".sdc",
        ".tcl", ".rpt", ".log", ".h", ".c", ".cpp",
    }
    _SSOT_IMPORT_SKIP_DIRS = {
        ".git", ".session", ".omx", "__pycache__", "node_modules",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }

    def _valid_ip_name(name: str) -> bool:
        return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name or ""))

    def _slash_head(text: str) -> str:
        return (text.strip().split(None, 1)[0] if text and text.strip() else "").lower()

    def _is_workflow_slash(text: str) -> bool:
        head = _slash_head(text)
        return head in _WORKFLOW_SLASHES

    def _split_slash(text: str) -> tuple[str, str]:
        raw = (text or "").strip()
        if not raw:
            return "", ""
        parts = raw.split(None, 1)
        return parts[0].lstrip("/").lower(), (parts[1] if len(parts) > 1 else "").strip()

    _SLASH_ANSI_RE = re.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]"
        r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
        r"|\[(?:\d{1,3};)*\d{0,3}m"
    )

    def _clean_slash_output(text: str) -> str:
        return _SLASH_ANSI_RE.sub("", str(text or "")).strip("\n")

    def _emit_slash_output(client_session: Any, text: str = "", *, finish: bool = True) -> None:
        cleaned = _clean_slash_output(text)
        if cleaned:
            client_session.emit("slash_output", text=cleaned)
        # Slash commands are command-plane operations. They should not
        # leave the chat input in "agent is streaming" state unless the
        # command explicitly queues an agent task below.
        if finish and not getattr(client_session, "agent_running", False):
            client_session.emit("agent_state", running=False)
        client_session.emit("flush")

    def _apply_slash_model_switch(target: str, client_session: Any) -> str:
        try:
            import src.config as _cfg_model  # noqa: WPS433
        except Exception:
            import config as _cfg_model  # type: ignore  # noqa: WPS433

        if target == "1":
            model = str(getattr(_cfg_model, "PRIMARY_MODEL", "") or "").strip()
            if not model:
                return "No PRIMARY_MODEL is configured."
            _set_runtime_model(model)
            _cfg_model.MODEL_NAME = model
            msg = f"Model switched to: {model}"
        elif target == "2":
            model = str(getattr(_cfg_model, "SECONDARY_MODEL", "") or "").strip()
            if not model:
                return "No SECONDARY_MODEL is configured."
            _set_runtime_model(model)
            _cfg_model.MODEL_NAME = model
            msg = f"Model switched to: {model}"
        elif target.startswith("profile:"):
            profile = target.split(":", 1)[1]
            if not _cfg_model.set_active_profile(profile):
                return f"Profile '{profile}' is not defined."
            _set_runtime_model(str(getattr(_cfg_model, "MODEL_NAME", "") or ""))
            msg = (
                f"Profile '{profile}' active -> "
                f"{getattr(_cfg_model, 'MODEL_NAME', '')} @ {getattr(_cfg_model, 'BASE_URL', '')}"
            )
        elif target.startswith("cli:"):
            backend = target.split(":", 1)[1]
            if not _cfg_model.activate_cli_backend(backend):
                return f"CLI backend '{backend}' is not available."
            _set_runtime_model(str(getattr(_cfg_model, "MODEL_NAME", "") or backend))
            try:
                from src.llm_client import get_active_model as _get_active_model
                label = _get_active_model()
            except Exception:
                label = backend
            msg = f"CLI backend active -> {label}"
        elif target.startswith("opencode:"):
            model = target.split(":", 1)[1]
            if not _cfg_model.activate_opencode_oauth(model):
                return (
                    f"'{model}' needs ChatGPT OAuth but no opencode credential is available.\n"
                    "Run: python -m src.opencode_backend login"
                )
            _set_runtime_model(str(getattr(_cfg_model, "MODEL_NAME", "") or ""))
            msg = (
                f"Opencode-OAuth active -> "
                f"{getattr(_cfg_model, 'MODEL_NAME', '')} @ {getattr(_cfg_model, 'BASE_URL', '')}"
            )
        else:
            model = target.strip()
            _set_runtime_model(model)
            _cfg_model.MODEL_NAME = model
            msg = f"Model switched to: {model}"

        model_now = str(getattr(_cfg_model, "MODEL_NAME", "") or os.environ.get("LLM_MODEL_NAME", ""))
        options = _model_option_rows(model_now)
        selected_key = next((row["key"] for row in options if row.get("selected") == "true"), "")
        client_session.emit(
            "context",
            model=model_now,
            model_options=options,
            selected_model_key=selected_key,
        )
        return msg

    def _execute_generic_slash_command(text: str, client_session: Any) -> bool:
        """Run non-ATLAS slash commands immediately on the command plane."""
        raw = (text or "").strip()
        if not raw.startswith("/"):
            return False
        if raw.lower() == "/normal":
            result = "AGENT_MODE:normal"
        else:
            try:
                from core.slash_commands import get_registry as _get_slash_registry
                result = _get_slash_registry().execute(raw)
            except Exception as exc:
                _emit_slash_output(client_session, f"Error executing {raw.split(None, 1)[0]}: {exc}")
                return True
        if result is None:
            return False

        if result.startswith("MODEL_SWITCH:"):
            msg = _apply_slash_model_switch(result.split(":", 1)[1], client_session)
            _emit_slash_output(client_session, msg)
            return True

        if result.startswith("AGENT_MODE:"):
            target = result.split(":", 1)[1]
            is_plan = target == "plan"
            _agent_mode_override_cv.set("plan_q" if is_plan else "normal")
            _plan_mode_cv.set("true" if is_plan else "false")
            os.environ["AGENT_MODE_OVERRIDE"] = "plan_q" if is_plan else "normal"
            os.environ["PLAN_MODE"] = "true" if is_plan else "false"
            if not is_plan:
                os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
            client_session.emit("mode_change", mode="plan" if is_plan else "normal")
            _emit_slash_output(
                client_session,
                "Plan mode: read-only until confirmation." if is_plan else "Normal mode: tools enabled.",
            )
            return True

        if result.startswith("EXECUTION_MODE:"):
            parts = result.split(":")
            mode = parts[1] if len(parts) > 1 else "agent"
            count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            try:
                import src.config as _cfg_exec  # noqa: WPS433
            except Exception:
                import config as _cfg_exec  # type: ignore  # noqa: WPS433
            _cfg_exec.EXECUTION_MODE = mode
            _cfg_exec.STEP_BY_STEP_MODE = mode == "step"
            if mode == "chat":
                _cfg_exec.CHAT_MAX_ITERATIONS = count
            _emit_slash_output(client_session, f"Execution mode set to: {mode}")
            return True

        if result.startswith("WINDOW_MODE:") or result.startswith("COMPRESSION_MODE:"):
            _emit_slash_output(client_session, result)
            return True

        if result.startswith("PLAN_AND_RUN:"):
            task = result[len("PLAN_AND_RUN:"):].strip()
            _agent_mode_override_cv.set("plan_q")
            _plan_mode_cv.set("true")
            os.environ["AGENT_MODE_OVERRIDE"] = "plan_q"
            os.environ["PLAN_MODE"] = "true"
            bridge.submit_prompt_for_session(client_session.session_id, task)
            client_session.emit("agent_state", running=True)
            _emit_slash_output(client_session, "Plan command accepted; agent task queued.", finish=False)
            return True

        if result.startswith("INJECT_PROMPT:"):
            prompt = result[len("INJECT_PROMPT:"):].strip()
            bridge.submit_prompt_for_session(client_session.session_id, prompt)
            client_session.emit("agent_state", running=True)
            _emit_slash_output(client_session, "Command accepted; agent task queued.", finish=False)
            return True

        if result.startswith("WORKSPACE_SWITCH:"):
            # Workspace switching rewrites main.py's in-memory prompt and
            # todo bindings. Queue that specialized state transition through
            # the agent control loop, but keep the chat command itself out
            # of the LLM prompt stream.
            was_running = bool(getattr(client_session, "agent_running", False))
            bridge.submit_prompt_for_session(client_session.session_id, raw)
            if not was_running:
                client_session.agent_running = False
            _emit_slash_output(
                client_session,
                "Workflow switch command accepted.",
                finish=not was_running,
            )
            return True

        if result in {"CLEAR_ALL", "GIT_CLEAR"} or result.startswith("TODO_REVERT:"):
            _emit_slash_output(
                client_session,
                "This slash command is destructive and is not executed directly from the web command plane.",
            )
            return True

        _emit_slash_output(client_session, result)
        return True

    def _session_json_path(session: str) -> Path:
        """Map any session string (1/2/3-part) to the canonical
        .session/<session_id>/<ip>/<workflow>/conversation.json path.

        Legacy (shorter) on-disk locations are auto-migrated on read.
        """
        clean = normalize_session_name(session or "")
        parts = [p for p in clean.split("/") if p]
        owner_default = os.environ.get("ATLAS_DEFAULT_SESSION_ID") or "default"
        ip_default = _active_ip_value() or "default"
        wf_default = os.environ.get("ATLAS_DEFAULT_WORKFLOW") or "default"
        owner = _resolve_session_owner() or owner_default
        if len(parts) >= 3:
            owner, ip, wf = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            ip, wf = parts[0], parts[1]
        elif len(parts) == 1:
            ip, wf = ip_default, parts[0]
        else:
            ip, wf = ip_default, wf_default
        canon = PROJECT_ROOT / ".session" / owner / ip / wf
        # Migrate legacy 2-part / 1-part dirs to canonical on first access.
        if not canon.exists():
            for legacy in (
                PROJECT_ROOT / ".session" / ip / wf,    # 2-part: ip/wf
                PROJECT_ROOT / ".session" / wf,          # 1-part: wf only
            ):
                try:
                    if legacy != canon and legacy.exists() and legacy.is_dir():
                        canon.parent.mkdir(parents=True, exist_ok=True)
                        legacy.rename(canon)
                        break
                except OSError:
                    continue
        return canon / "conversation.json"

    def _append_session_message(session: str, role: str, content: str) -> None:
        session = normalize_session_name(session)
        if not session:
            return
        path = _session_json_path(session)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                msgs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
                if not isinstance(msgs, list):
                    msgs = []
            except Exception:
                msgs = []
            msgs.append({"role": role, "content": content})
            path.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _append_active_history(role: str, content: str) -> None:
        """Mirror direct Web workflow command output into the currently
        hydrated chat history. Without this, commands like `/new-ip` can
        emit a visible WS event and then disappear when data.jsx reloads
        `/api/conversation` for the active workspace.
        """
        try:
            try:
                import src.config as _cfg_hist  # type: ignore
            except Exception:
                try:
                    import config as _cfg_hist  # type: ignore
                except Exception:
                    _cfg_hist = None
            if _cfg_hist is None:
                return
            hpath = Path(getattr(_cfg_hist, "HISTORY_FILE", "") or "")
            if not hpath:
                return
            hpath.parent.mkdir(parents=True, exist_ok=True)
            try:
                msgs = json.loads(hpath.read_text(encoding="utf-8")) if hpath.exists() else []
                if not isinstance(msgs, list):
                    msgs = []
            except Exception:
                msgs = []
            msgs.append({"role": role, "content": content})
            hpath.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _append_workflow_history(workflow: str, role: str, content: str) -> None:
        """Persist a message in the workflow-level session as well as the
        per-IP session. The actual slash dispatcher reloads `.session/<wf>`
        after `/wf <name>`, so approved Web Q&A must be visible there before
        `/to-ssot` runs.
        """
        _append_session_message(workflow, role, content)

    def _ssot_state_path(ip: str) -> Path:
        return _ssot_session_dir(ip) / "state.json"

    def _load_ssot_state(ip: str) -> dict[str, Any]:
        path = _ssot_state_path(ip)
        if not path.is_file():
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            return doc if isinstance(doc, dict) else {}
        except Exception:
            return {}

    def _save_ssot_state(ip: str, state: dict[str, Any]) -> None:
        path = _ssot_state_path(ip)
        path.parent.mkdir(parents=True, exist_ok=True)
        state["updated_at"] = time.time()
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    _SSOT_QA_SECTIONS = {
        "purpose": ("00_overview", "0. Overview / Intent"),
        "parameters": ("01_parameters", "1. Parameters"),
        "clock_reset": ("02_clock_reset", "2. Clock / Reset"),
        "bus_interface": ("03_interface", "3. Interface"),
        "submodule_structure": ("04_architecture", "4. Architecture / Decomposition"),
        "memory_map": ("05_memory", "5. Memory / Buffering"),
        "register_map": ("06_registers", "6. Register Map"),
        "interrupt": ("07_interrupt_error", "7. Interrupt / Error Policy"),
        "test_expectation": ("18_verification", "18. Verification / Gates"),
    }

    def _ssot_session_dir(ip: str, session: str | None = None) -> Path:
        # Canonical layout under --ui atlas: .session/<session_id>/<ip>/ssot-gen
        # Honor an explicitly-passed canonical session string (3-part). For all
        # other cases delegate to the central canonical resolver, so the
        # session_id is never silently dropped from the path.
        if session:
            clean = normalize_session_name(str(session))
            parts = [p for p in clean.split("/") if p]
            if len(parts) >= 3 and parts[-1] == "ssot-gen" and parts[-2] == ip:
                return PROJECT_ROOT / ".session" / clean
        return PROJECT_ROOT / ".session" / _canonical_session_string(ip, "ssot-gen")

    def _legacy_ssot_session_dir(ip: str) -> Path:
        return PROJECT_ROOT / ".session" / ip / "ssot-gen"

    def _ssot_qa_path(ip: str, session: str | None = None) -> Path:
        return _ssot_session_dir(ip, session) / "qa.json"

    def _ssot_qa_section(decision_key: str) -> tuple[str, str]:
        return _SSOT_QA_SECTIONS.get(
            decision_key,
            ("99_other", "99. Other / Open Decisions"),
        )

    def _load_ssot_qa_items(ip: str, session: str | None = None) -> list[dict[str, Any]]:
        path = _ssot_qa_path(ip, session)
        if not path.is_file() and session:
            path = _legacy_ssot_session_dir(ip) / "qa.json"
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = raw.get("items") if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return []
        return [dict(x) for x in items if isinstance(x, dict)]

    def _save_ssot_qa_items(ip: str, items: list[dict[str, Any]], session: str | None = None) -> None:
        path = _ssot_qa_path(ip, session)
        doc = {
            "ip": ip,
            "workflow": "ssot-gen",
            "updated_at": time.time(),
            "items": items,
        }
        text = json.dumps(doc, ensure_ascii=False, indent=2)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

        # Compatibility bridge: before canonical session paths, SSOT QA lived at
        # .session/<ip>/ssot-gen/qa.json. Keep mirroring default-owner sessions
        # there so old UI/tests/tools continue to read the same cards, while
        # avoiding cross-user leakage for real owner sessions.
        clean = normalize_session_name(str(session or ""))
        parts = [p for p in clean.split("/") if p]
        try:
            path_parts = [p for p in path.relative_to(PROJECT_ROOT / ".session").parts if p]
        except Exception:
            path_parts = []
        mirror_legacy = (
            not clean
            or (len(parts) >= 3 and parts[0] == "default" and parts[-2] == ip and parts[-1] == "ssot-gen")
            or (
                len(path_parts) >= 4
                and path_parts[0] == "default"
                and path_parts[-3] == ip
                and path_parts[-2] == "ssot-gen"
                and path_parts[-1] == "qa.json"
            )
        )
        legacy_path = _legacy_ssot_session_dir(ip) / "qa.json"
        if mirror_legacy and legacy_path != path:
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text(text, encoding="utf-8")

    def _status_group(status: str) -> str:
        return "approved" if str(status or "").lower() in {"approved", "answered", "resolved"} else "pending"

    def _qa_slug(value: str, fallback: str) -> str:
        slug = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        return (slug[:72] or fallback)

    def _ssot_q_pairs_from_questions(questions: list[dict[str, Any]] | None) -> list[tuple[str, str, dict[str, Any]]]:
        pairs: list[tuple[str, str, dict[str, Any]]] = []
        for idx, raw in enumerate(questions or []):
            if not isinstance(raw, dict):
                continue
            question = dict(raw)
            key_src = (
                question.get("decision_key")
                or question.get("id")
                or question.get("field_path")
                or question.get("section_id")
                or question.get("question")
            )
            key = _qa_slug(str(key_src or ""), f"qa_{idx + 1}")
            label = str(
                question.get("decision_label")
                or question.get("field_path")
                or question.get("subtitle")
                or question.get("question")
                or key
            ).strip()
            pairs.append((key, label[:240] or key, question))
        return pairs

    def _active_ssot_qa_context() -> tuple[str, str]:
        session = normalize_session_name(str(_active_session_value() or ""))
        parts = [p for p in session.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and _valid_ip_name(parts[-2]):
            return parts[-2], session
        ip = str(_active_ip_value() or "").strip()
        if _valid_ip_name(ip):
            return ip, _canonical_session_string(ip)
        return "", ""

    def _upsert_ssot_qa_items(
        ip: str,
        *,
        flow_id: str,
        kind: str,
        q_pairs: list[tuple[str, str, dict[str, Any]]],
        status: str,
        answers: dict[str, dict[str, Any]] | None = None,
        session: str | None = None,
        source: str = "ssot-qna",
    ) -> None:
        items = _load_ssot_qa_items(ip, session)
        index = {
            (str(item.get("flow_id") or ""), str(item.get("decision_key") or "")): idx
            for idx, item in enumerate(items)
        }
        now = time.time()
        answers = answers or {}
        for order, (key, label, question) in enumerate(q_pairs):
            default_section_id, default_section_title = _ssot_qa_section(key)
            section_id = str(
                question.get("section_id")
                or question.get("section")
                or default_section_id
            ).strip()
            section_title = str(
                question.get("section_title")
                or question.get("section_name")
                or question.get("section")
                or default_section_title
            ).strip()
            answer = answers.get(key) if isinstance(answers.get(key), dict) else {}
            answer_text = str(answer.get("answer") or "").strip()
            existing_idx = index.get((flow_id, key))
            prior = items[existing_idx] if existing_idx is not None else {}
            prior_answer_text = str(prior.get("answer") or "").strip()
            item_status = "approved" if answer_text or prior_answer_text else status
            item = {
                **prior,
                "ip": ip,
                "workflow": "ssot-gen",
                "kind": kind or "TBD",
                "flow_id": flow_id,
                "source": source or "ssot-qna",
                "section_id": section_id,
                "section_title": section_title,
                "decision_key": key,
                "decision_label": label,
                "question": str(question.get("question") or ""),
                "subtitle": str(question.get("subtitle") or ""),
                "question_kind": str(question.get("kind") or "single"),
                "options": question.get("options") or [],
                "qa_type": str(question.get("qa_type") or question.get("type") or "human_decision"),
                "content": question.get("content") or "",
                "detail": question.get("detail") or "",
                "criteria": question.get("criteria") or [],
                "source_refs": question.get("source_refs") or question.get("sources") or [],
                "field_path": question.get("field_path") or "",
                "order": order,
                "status": item_status,
                "status_group": _status_group(item_status),
                "answer": answer_text or str(prior.get("answer") or ""),
                "selected": answer.get("selected") or prior.get("selected") or [],
                "custom": answer.get("custom") or prior.get("custom") or "",
                "updated_at": now,
                "created_at": prior.get("created_at") or now,
            }
            if existing_idx is None:
                items.append(item)
            else:
                items[existing_idx] = item
        _save_ssot_qa_items(ip, items, session)

    def _ssot_qa_view(ip: str, session: str | None = None) -> dict[str, Any]:
        state = _load_ssot_state(ip)
        decisions = _ssot_decisions(ip, state)
        items = _load_ssot_qa_items(ip, session)
        required_index = {key: idx for idx, (key, _label) in enumerate(_SSOT_REQUIRED_DECISIONS)}
        seen_keys = {str(item.get("decision_key") or "") for item in items}
        for key, label in _SSOT_REQUIRED_DECISIONS:
            if key in seen_keys:
                continue
            answer = str(decisions.get(key) or "").strip()
            if not answer:
                continue
            section_id, section_title = _ssot_qa_section(key)
            items.append({
                "ip": ip,
                "workflow": "ssot-gen",
                "kind": state.get("kind") or "TBD",
                "flow_id": f"decision:{key}",
                "source": "ssot-decision",
                "section_id": section_id,
                "section_title": section_title,
                "decision_key": key,
                "decision_label": label,
                "question": label,
                "subtitle": key,
                "question_kind": "derived",
                "options": [],
                "order": required_index.get(key, 999),
                "status": "approved",
                "status_group": "approved",
                "answer": answer,
                "selected": [],
                "custom": "",
                "created_at": state.get("created_at") or 0,
                "updated_at": state.get("updated_at") or 0,
            })
        for item in items:
            key = str(item.get("decision_key") or "")
            answer = str(item.get("answer") or decisions.get(key) or "").strip()
            status = "approved" if answer else _status_group(str(item.get("status") or "pending"))
            item["answer"] = answer
            item["status_group"] = "approved" if status == "approved" else "pending"
            if item["status_group"] == "approved":
                item["status"] = "approved"
        items.sort(key=lambda item: (
            str(item.get("section_id") or ""),
            required_index.get(str(item.get("decision_key") or ""), 999),
            float(item.get("created_at") or 0),
        ))
        groups: dict[str, dict[str, Any]] = {}
        for item in items:
            section_id = str(item.get("section_id") or "99_other")
            section = groups.setdefault(section_id, {
                "id": section_id,
                "title": str(item.get("section_title") or "99. Other / Open Decisions"),
                "approved": [],
                "pending": [],
                "items": [],
            })
            copied = dict(item)
            section["items"].append(copied)
            bucket = "approved" if copied.get("status_group") == "approved" else "pending"
            section[bucket].append(copied)
        sections = list(groups.values())
        toc = [
            {
                "id": section["id"],
                "title": section["title"],
                "approved": len(section["approved"]),
                "pending": len(section["pending"]),
                "total": len(section["items"]),
            }
            for section in sections
        ]
        approved = sum(1 for item in items if item.get("status_group") == "approved")
        pending = sum(1 for item in items if item.get("status_group") != "approved")
        missing_requirements = _missing_ssot_decisions(ip, state)
        missing_set = set(missing_requirements)
        requirements = [
            {
                "key": key,
                "label": label,
                "status": "missing" if key in missing_set else "filled",
                "answer": decisions.get(key, ""),
            }
            for key, label in _SSOT_REQUIRED_DECISIONS
        ]
        return {
            "ip": ip,
            "workflow": "ssot-gen",
            "session": normalize_session_name(str(session or _active_session_value() or _canonical_session_string(ip))),
            "approved": bool(state.get("approved")),
            "state_status": state.get("status") or "",
            "toc": toc,
            "sections": sections,
            "summary": {"total": approved + pending, "approved": approved, "pending": pending},
            "requirements": {
                "total": len(_SSOT_REQUIRED_DECISIONS),
                "filled": len(_SSOT_REQUIRED_DECISIONS) - len(missing_requirements),
                "missing": len(missing_requirements),
                "items": requirements,
                "missing_keys": missing_requirements,
            },
            "items": items,
            "path": str(_ssot_qa_path(ip, session).relative_to(PROJECT_ROOT)),
        }

    def _ssot_qa_sessions_view() -> dict[str, Any]:
        root = PROJECT_ROOT / ".session"
        sessions: list[dict[str, Any]] = []
        if not root.is_dir():
            return {"sessions": sessions, "count": 0}
        seen: set[str] = set()
        for sdir in root.rglob("ssot-gen"):
            if not sdir.is_dir():
                continue
            try:
                rel = sdir.relative_to(root)
            except Exception:
                continue
            parts = [p for p in rel.parts if p]
            if len(parts) < 2 or parts[-1] != "ssot-gen":
                continue
            ip = parts[-2]
            if not _valid_ip_name(ip):
                continue
            session = str(rel)
            if session in seen:
                continue
            seen.add(session)
            files = [sdir / name for name in ("state.json", "qa.json", "conversation.json")]
            if not any(p.is_file() for p in files):
                continue
            mtimes = []
            for p in files:
                try:
                    if p.is_file():
                        mtimes.append(p.stat().st_mtime)
                except Exception:
                    pass
            state = {}
            state_path = sdir / "state.json"
            if state_path.is_file():
                try:
                    loaded = json.loads(state_path.read_text(encoding="utf-8"))
                    state = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    state = {}
            if not state:
                state = _load_ssot_state(ip)
            # Keep the sessions list cheap: it is polled during first page
            # load and should never parse every IP's SSOT YAML. Some generated
            # drafts can be very large or malformed enough for PyYAML to hold
            # the single uvicorn event loop for seconds. The detailed SSOT
            # pane still calls _ssot_qa_view() for one selected IP.
            qa_items = _load_ssot_qa_items(ip, session)
            approved = sum(
                1 for item in qa_items
                if _status_group(str(item.get("status") or "")) == "approved"
                or str(item.get("answer") or "").strip()
            )
            pending = max(0, len(qa_items) - approved)
            qa_path = _ssot_qa_path(ip, session)
            sessions.append({
                "session": session,
                "owner": "/".join(parts[:-2]),
                "ip": ip,
                "workflow": "ssot-gen",
                "status": state.get("status") or "draft",
                "approved": bool(state.get("approved")),
                "summary": {
                    "total": approved + pending,
                    "approved": approved,
                    "pending": pending,
                },
                "updated_at": max(mtimes) if mtimes else float(state.get("updated_at") or 0),
                "qa_path": str(qa_path.relative_to(PROJECT_ROOT)) if qa_path.exists() else "",
            })
        sessions.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        return {"sessions": sessions, "count": len(sessions)}

    def _ssot_yaml_path(ip: str) -> Path:
        return PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"

    def _load_ssot_draft(ip: str) -> dict[str, Any]:
        path = _ssot_yaml_path(ip)
        if not path.is_file():
            return {}
        try:
            import yaml as _yaml  # type: ignore

            doc = _yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
            return doc if isinstance(doc, dict) else {}
        except Exception:
            return {}

    def _save_ssot_draft(ip: str, doc: dict[str, Any]) -> None:
        path = _ssot_yaml_path(ip)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import yaml as _yaml  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"PyYAML is required to update SSOT draft: {exc}") from exc
        path.write_text(_yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
        # Fire file_changed so the open SSOT preview / full view / file
        # tree auto-reload. _emit_tool_result only catches tool-driven
        # writes (write_file / replace_in_file / …); _save_ssot_draft
        # is a direct Python disk write (called by /api/ssot/qa/answer
        # and the ssot scaffold helpers), so it would otherwise look
        # like a silent update from the frontend's perspective.
        try:
            bridge.emit("file_changed", path=str(path), tool="ssot_save")
        except Exception:
            pass

    def _ensure_ssot_draft(ip: str, kind: str = "TBD") -> dict[str, Any]:
        # Default top file path follows the canonical convention
        # `rtl/<ip>.sv` so /new-ip scaffolds an SSOT that already has
        # the synthesizable top wired to a name matching the IP. Without
        # this, drafts shipped without a `file` field and downstream
        # rtl-gen runs occasionally settled on `<ip>_wrapper.sv` as the
        # de facto top, which surprised reviewers expecting `<ip>.sv`.
        _default_top_file = f"rtl/{ip}.sv" if ip else "rtl/top.sv"
        doc = _load_ssot_draft(ip)
        if not doc:
            doc = {
                "top_module": {
                    "name": ip,
                    "file": _default_top_file,
                    "type": "draft",
                    "description": kind or "TBD",
                    "version": "draft",
                },
                "custom": {},
            }
        top = doc.setdefault("top_module", {})
        if isinstance(top, dict):
            top.setdefault("name", ip)
            top.setdefault("file", _default_top_file)
            top.setdefault("type", "draft")
            top.setdefault("description", kind or "TBD")
            top.setdefault("version", "draft")
        custom = doc.setdefault("custom", {})
        if not isinstance(custom, dict):
            custom = {}
            doc["custom"] = custom
        workflow = custom.setdefault("atlas_workflow", {})
        if isinstance(workflow, dict):
            workflow.setdefault("status", "draft")
            workflow.setdefault("source", "atlas-ui")
            workflow["updated_at"] = time.time()
        custom.setdefault("atlas_decisions", {})
        custom.setdefault("atlas_decision_sources", {})
        custom.setdefault("atlas_imports", [])
        custom.setdefault("atlas_import_conflicts", [])
        _save_ssot_draft(ip, doc)
        return doc

    def _ssot_custom(ip: str, kind: str = "TBD") -> tuple[dict[str, Any], dict[str, Any]]:
        doc = _ensure_ssot_draft(ip, kind)
        custom = doc.setdefault("custom", {})
        if not isinstance(custom, dict):
            custom = {}
            doc["custom"] = custom
        return doc, custom

    def _ssot_decisions(ip: str, state: dict[str, Any] | None = None) -> dict[str, str]:
        doc = _load_ssot_draft(ip)
        custom = doc.get("custom") if isinstance(doc.get("custom"), dict) else {}
        raw = custom.get("atlas_decisions") if isinstance(custom, dict) else {}
        if not isinstance(raw, dict) or not raw:
            legacy = state if isinstance(state, dict) else _load_ssot_state(ip)
            raw = legacy.get("decisions") if isinstance(legacy.get("decisions"), dict) else {}
        return {str(k): str(v).strip() for k, v in (raw or {}).items() if str(v or "").strip()}

    def _missing_ssot_decisions(ip: str, state: dict[str, Any] | None = None) -> list[str]:
        decisions = _ssot_decisions(ip, state)
        return [key for key, _ in _SSOT_REQUIRED_DECISIONS if not str(decisions.get(key) or "").strip()]

    def _record_ssot_decisions(
        ip: str,
        kind: str,
        updates: dict[str, str],
        sources: dict[str, list[dict[str, str]]] | None = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        doc, custom = _ssot_custom(ip, kind)
        decisions = custom.get("atlas_decisions")
        if not isinstance(decisions, dict):
            decisions = {}
            custom["atlas_decisions"] = decisions
        decision_sources = custom.get("atlas_decision_sources")
        if not isinstance(decision_sources, dict):
            decision_sources = {}
            custom["atlas_decision_sources"] = decision_sources
        filled: list[str] = []
        conflicts: list[dict[str, Any]] = []
        source_map = sources or {}
        for key, value in updates.items():
            candidate = str(value or "").strip()
            if not candidate:
                continue
            existing = str(decisions.get(key) or "").strip()
            if existing:
                if re.sub(r"\s+", " ", existing).lower() != re.sub(r"\s+", " ", candidate).lower():
                    conflicts.append({
                        "key": key,
                        "existing": existing[:500],
                        "candidate": candidate[:500],
                        "sources": source_map.get(key, [])[:5],
                    })
                continue
            decisions[key] = candidate
            decision_sources[key] = source_map.get(key, [])[:8]
            filled.append(key)
        if conflicts:
            prior = custom.get("atlas_import_conflicts")
            if not isinstance(prior, list):
                prior = []
            custom["atlas_import_conflicts"] = prior + conflicts
        _save_ssot_draft(ip, doc)
        return filled, conflicts

    def _latest_pending_ssot_ip() -> str:
        root = PROJECT_ROOT / ".session"
        candidates: list[tuple[float, str]] = []
        if root.is_dir():
            for p in root.rglob("ssot-gen/state.json"):
                try:
                    doc = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(doc, dict) and not doc.get("approved"):
                        candidates.append((p.stat().st_mtime, p.parent.parent.name))
                except Exception:
                    continue
        candidates.sort(reverse=True)
        return candidates[0][1] if candidates else ""

    def _resolve_session_owner() -> str:
        """Extract the session_id (owner) from ATLAS_ACTIVE_SESSION env.

        Canonical session string layout for --ui atlas is always 3-part:
            <session_id>/<ip>/<workflow>
        This helper returns just the session_id (or empty string if no owner
        can be determined).

        Accepted current-env shapes:
          - 3+ parts:                       owner/ip/wf[/...] -> owner = parts[0]
          - 2 parts ending in 'default':    owner/default     -> owner = parts[0]
          - 1 part that is NOT an IP-like:  bare session_id   -> owner = parts[0]
        """
        current = normalize_session_name(str(_active_session_value() or ""))
        parts = [p for p in current.split("/") if p]
        if len(parts) >= 3:
            return parts[0]
        if len(parts) == 2 and parts[-1] == "default":
            return parts[0]
        if len(parts) == 1 and parts[0] and not _valid_ip_name(parts[0]):
            return parts[0]
        return ""

    def _session_owner_with_model(owner: str) -> str:
        """Optionally isolate session namespace per model.

        When enabled, the owner segment becomes:
            <owner>__<model_slug>
        so model runs cannot overwrite each other's .session trees.
        """
        base = str(owner or "default").strip() or "default"
        enabled = os.environ.get("ATLAS_SESSION_PER_MODEL", "0").strip().lower() in ("1", "true", "yes", "on")
        if not enabled:
            return base
        raw_model = (
            os.environ.get("LLM_ACTIVE_MODEL_NAME")
            or os.environ.get("MODEL_NAME")
            or os.environ.get("LLM_MODEL_NAME")
            or ""
        ).strip()
        if not raw_model:
            return base
        model_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_model).strip("_")
        if not model_slug:
            return base
        if base.endswith(f"__{model_slug}"):
            return base
        return f"{base}__{model_slug}"

    def _canonical_session_string(ip: str | None = None,
                                   workflow: str | None = None) -> str:
        """Return canonical 3-part session path string for --ui atlas:
            <session_id>/<ip>/<workflow>

        Any segment that is empty/None falls back to "default", so the
        on-disk layout is always 3 levels deep. Defaults can be overridden
        from CLI via `-s/-ip/-w` (env: ATLAS_DEFAULT_SESSION_ID,
        ATLAS_ACTIVE_IP, ATLAS_DEFAULT_WORKFLOW).
        """
        owner = _resolve_session_owner() or os.environ.get("ATLAS_DEFAULT_SESSION_ID") or "default"
        owner = _session_owner_with_model(owner)
        ip = ip or _active_ip_value() or "default"
        workflow = workflow or os.environ.get("ATLAS_DEFAULT_WORKFLOW") or "default"
        return f"{owner}/{ip}/{workflow}"

    def _canonical_session_dir(ip: str | None = None,
                                workflow: str | None = None) -> Path:
        """Filesystem dir for the canonical session path (3 segments)."""
        return PROJECT_ROOT / ".session" / _canonical_session_string(ip, workflow)

    def _legacy_session_candidates(ip: str | None,
                                    workflow: str | None) -> list[Path]:
        """Legacy on-disk locations used before path canonicalization.
        Used by readers to recover history from older runs."""
        ip_seg = ip or "default"
        wf_seg = workflow or "default"
        cands: list[Path] = []
        # 2-part: <ip>/<workflow>
        cands.append(PROJECT_ROOT / ".session" / ip_seg / wf_seg)
        # 1-part: <workflow> alone (very old)
        cands.append(PROJECT_ROOT / ".session" / wf_seg)
        # 1-part: <ip> alone
        cands.append(PROJECT_ROOT / ".session" / ip_seg)
        return cands

    def _migrate_legacy_session(ip: str | None,
                                 workflow: str | None) -> Path:
        """Locate canonical path; if absent and a legacy path exists, move it
        in-place. Returns the canonical path (whether or not migration ran)."""
        canon = _canonical_session_dir(ip, workflow)
        if canon.exists():
            return canon
        for legacy in _legacy_session_candidates(ip, workflow):
            try:
                if legacy.exists() and legacy != canon and legacy.is_dir():
                    canon.parent.mkdir(parents=True, exist_ok=True)
                    legacy.rename(canon)
                    break
            except OSError:
                continue
        return canon

    def _set_active_ssot_ip(ip: str) -> None:
        if not _valid_ip_name(ip):
            return
        _atlas_active_ip_cv.set(ip)
        _atlas_active_session_cv.set(_canonical_session_string(ip, "ssot-gen"))

    def _active_ssot_ip() -> str:
        env_ip = str(_active_ip_value() or "").strip()
        if _valid_ip_name(env_ip):
            return env_ip
        session = normalize_session_name(str(_active_session_value() or ""))
        parts = [p for p in session.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and _valid_ip_name(parts[-2]):
            return parts[-2]
        if len(parts) == 1 and _valid_ip_name(parts[0]) and _ssot_state_path(parts[0]).is_file():
            return parts[0]
        return _latest_pending_ssot_ip()

    def _render_new_ip_plan(ip: str, kind: str, state: dict[str, Any]) -> str:
        missing = _missing_ssot_decisions(ip, state)
        lines = [
            f"[SSOT PLAN] {ip}",
            f"kind: {kind or 'simple APB peripheral'}",
            "mode: structure only; no document import is run by /new-ip",
            "",
            "Created structure:",
            f"- {ip}/doc, {ip}/req, {ip}/yaml",
            f"- {ip}/rtl, {ip}/list, {ip}/tb/cocotb",
            f"- {ip}/tc, {ip}/sim, {ip}/cov, {ip}/lint",
            "",
            "SSOT decisions still needed before production YAML write:",
        ]
        for key, label in _SSOT_REQUIRED_DECISIONS:
            mark = "✓" if key not in missing else "·"
            lines.append(f"- {mark} `{key}`: {label}")
        lines += [
            "",
            "Short flow:",
            f"1. Put source docs, RTL, specs, logs, or notes anywhere under `{ip}/`",
            f"2. Run `/import {ip}` or `/import @path` to scan the workspace into SSOT section TODOs",
            f"3. Run `/to-ssot {ip}`; use `/grill-me` only for gaps or conflicts",
        ]
        if missing:
            lines.append("")
            lines.append("missing decisions: " + ", ".join(missing))
        return "\n".join(lines)

    def _parse_new_ip_args(args: str) -> tuple[str, str, list[str], str]:
        import shlex

        try:
            tokens = [t.strip().strip("\"'") for t in shlex.split(args or "", posix=False) if t.strip()]
        except ValueError as exc:
            return "", "", [], f"cannot parse /new-ip arguments: {exc}"
        if not tokens:
            return "", "", [], ""
        ip = tokens[0]
        import_paths: list[str] = []
        kind_tokens: list[str] = []
        idx = 1
        while idx < len(tokens):
            tok = tokens[idx]
            if tok in ("--import", "--doc", "--docs"):
                if idx + 1 >= len(tokens):
                    return "", "", [], f"missing value after {tok}"
                import_paths.append(tokens[idx + 1])
                idx += 2
                continue
            if tok.startswith("@"):
                import_paths.append(tok)
                idx += 1
                continue
            kind_tokens.append(tok)
            idx += 1
        kind = " ".join(kind_tokens).strip() or "TBD"
        return ip, kind, import_paths, ""

    def _render_ssot_llm_qna_prompt(ip: str, kind: str, state: dict[str, Any]) -> str:
        session = normalize_session_name(str(_active_session_value() or _canonical_session_string(ip)))
        imported = state.get("imported_artifacts") if isinstance(state.get("imported_artifacts"), list) else []
        imported_paths = [
            str(item.get("path") or "").strip()
            for item in imported
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        ]
        missing = _missing_ssot_decisions(ip, state)
        lang = os.environ.get("ATLAS_UI_LANG") or "English"
        path_lines = "\n".join(f"- {p}" for p in imported_paths[:24]) or "- (none recorded; inspect the IP directory and draft SSOT)"
        missing_line = ", ".join(missing) if missing else "(backend baseline decisions already filled; still inspect for SSOT TBD/conflicts)"
        return "\n".join([
            f"You are ssot-gen for IP `{ip}` in ATLAS UI.",
            f"Session: `{session}`",
            f"Preferred visible language: {lang}. Default to English when no explicit language is requested.",
            "",
            "Goal: create IP-specific SSOT Q&A from the current evidence, not from a fixed template.",
            "This is a general-IP flow. Do not assume APB/register-only/simple peripheral structure unless evidence says so.",
            "",
            "Truth ownership model:",
            "- Human owns requirement/spec/interface/FL golden model/coverage goals/performance targets/sign-off.",
            "- LLM owns drafting, import analysis, QA generation, SSOT patch proposals, and downstream workflow_todos.",
            "- Do not change locked truth to make downstream RTL pass; make a change-request question instead.",
            "- TODOs are execution work, not substitutes for unresolved human decisions.",
            "",
            "Current backend baseline missing keys, for orientation only:",
            f"- {missing_line}",
            "",
            "Evidence paths imported or known:",
            path_lines,
            "",
            "Required action:",
            f"1. Read `{ip}/yaml/{ip}.ssot.yaml` if it exists, plus relevant docs/RTL under `{ip}/` and the evidence paths above.",
            "2. Detect unresolved SSOT decisions, contradictions, assumptions, TBD/null/placeholders, and any truth that needs human approval.",
            "3. Generate ONLY the questions needed for this IP. The question set may be 0, 1, 4, 20, or more depending on complexity.",
            "4. If the answer is not an immediate blocker, use `record_ssot_qa(questions=[...])` to save deferred QA cards.",
            "5. Use `ask_user(questions=[...])` only when the answer blocks the next SSOT write or import pass.",
            "   Do not ask plain prose questions in chat. Both tools preserve SSOT QA metadata.",
            "6. Each question object must carry metadata so ATLAS can save it in SSOT QA preview:",
            "   - id: stable snake_case id",
            "   - section_id: canonical section bucket such as 00_overview, 03_interface, 06_registers, 18_verification, 19_workflow_todos, or a specific section number",
            "   - section_title: human-readable SSOT section title",
            "   - decision_key: stable key for the decision",
            "   - decision_label: short label",
            "   - qa_type: human_decision | clarification | change_request | execution_blocker",
            "   - question, subtitle, kind, options when useful",
            "   - criteria: pass/fail criteria for using the answer downstream",
            "   - source_refs: SSOT paths, doc paths, or RTL paths that caused the question",
            "7. Prefer section-specific QA cards. Group by SSOT section and ask concrete decisions, not generic template prompts.",
            "8. If downstream RTL needs explicit decomposition, write `workflow_todos.rtl-gen[]` with content/detail/criteria/source_refs.",
            "9. If no immediate answer is needed after recording deferred QA, say `[SSOT Q&A] deferred questions recorded` with a short evidence summary.",
            "10. If no human decision is needed at all, say `[SSOT Q&A] no generated questions required` and explain the evidence briefly.",
            "",
            "Important: fixed question templates are forbidden here. Derive the QA from this IP's evidence and current SSOT only.",
        ])

    def _render_approved_ssot_spec(ip: str, state: dict[str, Any]) -> str:
        decisions = _ssot_decisions(ip, state)
        lines = [
            f"[APPROVED WEB SSOT SPEC] {ip}",
            f"kind: {state.get('kind') or 'simple APB peripheral'}",
            "source: Web UI Plan Mode + SSOT draft decisions",
            "",
            "Use this as the source of truth for /to-ssot. Do not invent over missing fields.",
        ]
        for key, _label in _SSOT_REQUIRED_DECISIONS:
            lines.append(f"- {key}: {decisions.get(key) or '(missing)'}")
        return "\n".join(lines)

    def _emit_ssot_approval_ready(ip: str, state: dict[str, Any], missing: list[str] | None = None) -> None:
        decisions = _ssot_decisions(ip, state)
        miss = missing if missing is not None else _missing_ssot_decisions(ip, state)
        bridge.emit(
            "ssot_approval_ready",
            ip=ip,
            kind=state.get("kind") or "TBD",
            status=state.get("status") or ("approved" if state.get("approved") else "answered"),
            approved=bool(state.get("approved")),
            missing=miss,
            decisions=decisions,
            approve_cmd=f"approve {ip}",
            generate_cmd=f"/to-ssot {ip}",
        )

    def _answer_text(answer: dict[str, Any], question: dict[str, Any]) -> str:
        custom = str(answer.get("custom") or "").strip()
        if custom:
            return custom
        selected = answer.get("selected") or []
        by_id = {str(o.get("id")): str(o.get("label") or o.get("id"))
                 for o in (question.get("options") or []) if isinstance(o, dict)}
        labels = [by_id.get(str(s), str(s)) for s in selected]
        return ", ".join([x for x in labels if x]).strip()

    def _new_ssot_state(ip: str, kind: str = "TBD") -> dict[str, Any]:
        return {
            "ip": ip,
            "kind": kind,
            "approved": False,
            "approved_at": 0,
            "status": "planned",
            "active_session": _active_session_value() or _canonical_session_string(ip),
            "last_step": "new-ip",
            "created_at": time.time(),
        }

    def _scaffold_ip_wiki(ip: str) -> None:
        """Seed <ip>/wiki/{index.md, log.md, notes.md} idempotently.

        Karpathy-style: `[[link]]` ToC into the IP tree + append-only log + free-form notes.
        Re-runs of /new-ip leave existing pages untouched.
        """
        wiki_dir = PROJECT_ROOT / ip / "wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        today = time.strftime("%Y-%m-%d", time.gmtime())
        seeds = {
            "index.md": (
                f"# {ip} IP Wiki\n\n"
                f"Per-IP knowledge base. Read with `wiki_query(ip=\"{ip}\")` or run\n"
                f"`python3 workflow/wiki/build_graph.py --ip {ip}` to refresh the index.\n\n"
                "## Status snapshot\n\n"
                "Populated by `workflow/wiki/build_graph.py --ip <ip>`; the synthetic\n"
                "`[[ssot]]`, `[[fl_model]]`, `[[cl_model]]`, `[[rtl]]`, `[[filelist]]`,\n"
                "`[[lint]]`, `[[tb]]`, `[[sim]]`, `[[coverage]]`, `[[audit]]`, and\n"
                "`[[last_run]]` nodes carry status/digest fields.\n\n"
                "## Tree\n\n"
                f"- [[notes]] — free-form owner/manager notes\n"
                f"- [[log]] — append-only event log\n"
                f"- requirements at `../req/`\n"
                f"- SSOT YAML at `../yaml/{ip}.ssot.yaml`\n"
                f"- function/cycle model at `../model/`\n"
                f"- RTL at `../rtl/` (filelist `../list/{ip}.f`)\n"
                f"- testbench at `../tb/`\n"
                f"- sim evidence at `../sim/`\n"
                f"- lint/coverage at `../lint/` and `../cov/`\n"
                f"- run logs at `../logs/`\n"
            ),
            "log.md": (
                "# Wiki Log\n\n"
                f"## [{today}] new-ip | scaffolded {ip} wiki\n"
            ),
            "notes.md": (
                f"# {ip} Notes\n\n"
                "Free-form notes for the IP owner and manager. Tooling does not\n"
                "write to this file; only humans (and chat agents acting on a\n"
                "user request) edit it. Cross-link with `[[ssot]]`, `[[rtl]]`,\n"
                "`[[sim]]`, etc. to compound context across sessions.\n"
            ),
        }
        for name, content in seeds.items():
            target = wiki_dir / name
            if not target.exists():
                try:
                    target.write_text(content, encoding="utf-8")
                except Exception:
                    pass

    def _ensure_new_ip_structure(ip: str) -> list[str]:
        dirs = [
            "doc",
            "req",
            "yaml",
            "rtl",
            "list",
            "tb/cocotb",
            "tc",
            "sim",
            "cov",
            "lint",
            "wiki",
        ]
        created: list[str] = []
        for rel in dirs:
            path = PROJECT_ROOT / ip / rel
            path.mkdir(parents=True, exist_ok=True)
            created.append(f"{ip}/{rel}")
        _scaffold_ip_wiki(ip)
        # Per-IP git repo. Each IP gets its OWN .git so the agent's
        # write_file / replace_in_file calls can auto-commit and the
        # user has a per-IP history independent of the outer project
        # repo. Idempotent — `git init` on an existing repo is a no-op.
        _ip_root = PROJECT_ROOT / ip
        _git_dir = _ip_root / ".git"
        _gitignore = _ip_root / ".gitignore"
        # Ignore the heavy/derived artifacts so per-IP git history stays
        # small and reviewable. write it before `git init` so the first
        # `git add .` doesn't sweep up sim/*.vcd etc.
        if not _gitignore.exists():
            try:
                _gitignore.write_text(
                    "# Atlas-managed — generated/binary artifacts excluded\n"
                    "__pycache__/\n*.pyc\n.DS_Store\n*.log\n"
                    "sim/build/\nsim/results/\nsim/work/\n"
                    "sim/*.vcd\nsim/*.fst\nsim/*.shm/\nsim/*.vpd\nsim/*.wlf\n"
                    "tb/cocotb/__pycache__/\ntb/cocotb/results.xml\n"
                    "cov/build/\ncov/*.dat\ncov/*.ucdb\n"
                    "lint/build/\nlint/*.rpt\nlint/*.tmp\n"
                    ".vscode/\n.idea/\n",
                    encoding="utf-8",
                )
            except Exception:
                pass
        try:
            import subprocess as _sp_init
            if not _git_dir.is_dir():
                _sp_init.run(
                    ["git", "init", "-q", "-b", "main"],
                    cwd=str(_ip_root),
                    capture_output=True,
                    timeout=10,
                )
                # Pin the committer to a benign default so `git commit`
                # doesn't fail with "Please tell me who you are" on
                # fresh boxes that have no global git config.
                for _k, _v in (("user.email", "atlas@local"),
                                ("user.name",  "Atlas Agent")):
                    _sp_init.run(
                        ["git", "config", _k, _v],
                        cwd=str(_ip_root),
                        capture_output=True,
                        timeout=5,
                    )
                # Initial commit so subsequent auto-commits have a
                # parent — `git commit --allow-empty` keeps it clean
                # even when the dirs are empty at scaffold time.
                _sp_init.run(
                    ["git", "add", "--", ".gitignore"],
                    cwd=str(_ip_root),
                    capture_output=True,
                    timeout=5,
                )
                _sp_init.run(
                    ["git", "commit", "--allow-empty",
                     "-m", f"atlas: scaffold {ip}"],
                    cwd=str(_ip_root),
                    capture_output=True,
                    timeout=10,
                )
            # BARE_GIT_OPTION: also stand up a central bare repo as a
            # sibling of the IP (<root>/<ip>.git). Wire the working
            # repo's origin to it + install hooks so that:
            #   • atlas's per-edit auto-commits propagate to the bare
            #     via post-commit `git push origin main`
            #   • external pushes (`git push http://host:port/git/<ip>.git`)
            #     land in the bare, and a post-receive hook fast-forwards
            #     the atlas working tree so the agent sees the change
            try:
                import config as _cfg_bare
                _bare_on = getattr(_cfg_bare, "BARE_GIT_OPTION", True)
            except Exception:
                _bare_on = True
            if _bare_on:
                import shlex as _shlex_bare
                _bare_dir = PROJECT_ROOT / f"{ip}.git"
                _post_commit  = _ip_root / ".git" / "hooks" / "post-commit"
                _post_receive = _bare_dir / "hooks" / "post-receive"
                try:
                    if not (_bare_dir / "HEAD").is_file():
                        _sp_init.run(
                            ["git", "init", "--bare", "-q", "-b", "main",
                             str(_bare_dir)],
                            capture_output=True, timeout=10,
                        )
                    # git-http-backend refuses receive-pack by default;
                    # enable it so /git/<ip>.git accepts `git push` over
                    # smart HTTP. Idempotent.
                    _sp_init.run(
                        ["git", "config", "http.receivepack", "true"],
                        cwd=str(_bare_dir), capture_output=True, timeout=5,
                    )
                    # Wire / re-wire working repo's origin to the bare.
                    _sp_init.run(
                        ["git", "remote", "remove", "origin"],
                        cwd=str(_ip_root), capture_output=True, timeout=5,
                    )
                    _sp_init.run(
                        ["git", "remote", "add", "origin",
                         str(_bare_dir.resolve())],
                        cwd=str(_ip_root), capture_output=True, timeout=5,
                    )
                    # Initial push so the bare has the scaffold commit.
                    _sp_init.run(
                        ["git", "push", "-u", "-q", "origin", "main"],
                        cwd=str(_ip_root), capture_output=True, timeout=15,
                    )
                    # post-commit hook in working repo → push to bare.
                    _post_commit.parent.mkdir(parents=True, exist_ok=True)
                    _post_commit.write_text(
                        "#!/bin/sh\n"
                        "# Atlas — mirror each working-tree commit to the central bare.\n"
                        "git push -q origin HEAD >/dev/null 2>&1 || true\n",
                        encoding="utf-8",
                    )
                    _post_commit.chmod(0o755)
                    # post-receive hook in bare → fast-forward the
                    # working tree so external pushes land in the live
                    # IP dir the agent reads from.
                    _post_receive.parent.mkdir(parents=True, exist_ok=True)
                    _post_receive.write_text(
                        "#!/bin/sh\n"
                        "# Atlas — fast-forward the working tree when an external push arrives.\n"
                        f"WORK={_shlex_bare.quote(str(_ip_root.resolve()))}\n"
                        "( cd \"$WORK\" && unset GIT_DIR && "
                        "  git fetch -q origin && "
                        "  git reset -q --hard origin/main ) >/dev/null 2>&1 || true\n",
                        encoding="utf-8",
                    )
                    _post_receive.chmod(0o755)
                except Exception:
                    pass
        except Exception:
            # Best-effort — never block /new-ip on a git failure.
            pass
        return created

    def _auto_commit_for_path(path: Path | str, tool: str = "edit") -> None:
        """After a write/replace tool call, auto-commit the change in
        the nearest enclosing per-IP git repo. Silent-best-effort: any
        git error is swallowed so a write to a non-IP location never
        blocks the agent. Walks up from `path` looking for `.git`,
        stops at PROJECT_ROOT — never escapes the project boundary."""
        try:
            import subprocess as _sp_ac
            p = Path(path).resolve()
            project_root = PROJECT_ROOT.resolve()
            try:
                p.relative_to(project_root)
            except ValueError:
                return
            # Walk up looking for .git, but stop before / and don't
            # land on the outer project's git repo (we only want per-IP).
            cur = p if p.is_dir() else p.parent
            git_root: Path | None = None
            while cur != project_root and cur != cur.parent:
                if (cur / ".git").is_dir() and cur != project_root:
                    git_root = cur
                    break
                cur = cur.parent
            if git_root is None:
                return
            rel = ""
            try:
                rel = str(p.relative_to(git_root))
            except ValueError:
                rel = str(p.name)
            _sp_ac.run(
                ["git", "add", "--", "."],
                cwd=str(git_root),
                capture_output=True,
                timeout=15,
            )
            # `git commit` returns non-zero when there's nothing to
            # commit — that's fine, just means the file content didn't
            # change. We don't surface it.
            _sp_ac.run(
                ["git", "commit",
                 "-m", f"{tool}: {rel}",
                 "--allow-empty-message"],
                cwd=str(git_root),
                capture_output=True,
                timeout=15,
            )
        except Exception:
            pass

    def _relative_project_path(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
        except Exception:
            return str(path)

    def _strip_import_marker(raw: str) -> str:
        token = str(raw or "").strip().strip("\"'")
        return token[1:] if token.startswith("@") else token

    def _safe_import_path(raw: str) -> Path | None:
        token = _strip_import_marker(raw)
        if not token:
            return None
        if os.name != "nt":
            token = token.replace("\\", "/")
        try:
            p = Path(token).expanduser()
            if not p.is_absolute():
                p = PROJECT_ROOT / token
            resolved = p.resolve()
            resolved.relative_to(PROJECT_ROOT.resolve())
            return resolved
        except Exception:
            return None

    def _resolve_import_path(ip: str, raw: str) -> tuple[Path | None, str]:
        token = _strip_import_marker(raw)
        if not token:
            return None, "empty import path"
        candidates = [token]
        maybe_path = Path(token)
        if not maybe_path.is_absolute():
            norm = token.replace("\\", "/")
            if not norm.startswith(f"{ip}/"):
                candidates.append(f"{ip}/{token}")
        first_safe: Path | None = None
        for candidate in candidates:
            p = _safe_import_path(candidate)
            if p is None:
                continue
            if first_safe is None:
                first_safe = p
            if p.exists():
                return p, ""
        if first_safe is None:
            return None, f"unsafe import path: {token}"
        return first_safe, f"import path not found: {_relative_project_path(first_safe)}"

    def _parse_import_args(args: str) -> tuple[str, list[str], str]:
        import shlex

        try:
            raw_tokens = shlex.split(args or "", posix=False)
        except ValueError as exc:
            return "", [], f"cannot parse /import arguments: {exc}"
        tokens = []
        for raw in raw_tokens:
            tok = _strip_import_marker(raw)
            if tok:
                tokens.append(tok)
        ip = ""
        paths: list[str] = []
        idx = 0
        while idx < len(tokens):
            tok = tokens[idx]
            if tok in ("--ip", "-i"):
                if idx + 1 >= len(tokens):
                    return "", [], "missing value after --ip"
                ip = tokens[idx + 1]
                idx += 2
                continue
            paths.append(tok)
            idx += 1
        if not ip and len(paths) > 1 and _valid_ip_name(paths[0]):
            maybe_ip = paths[0]
            if _ssot_state_path(maybe_ip).is_file() or (PROJECT_ROOT / maybe_ip).exists():
                ip = maybe_ip
                paths = paths[1:]
        if not ip:
            ip = _active_ssot_ip()
        if not _valid_ip_name(ip):
            return "", [], (
                "[SSOT IMPORT] no active IP found\n"
                "usage: /new-ip <ip_name> first, then /import [path ...]\n"
                "or: /import --ip <ip_name> [path ...]"
            )
        return ip, paths, ""

    def _default_import_roots(ip: str) -> list[Path]:
        ip_dir = PROJECT_ROOT / ip
        return [ip_dir] if ip_dir.exists() else []

    def _collect_import_files(ip: str, raw_paths: list[str]) -> tuple[list[Path], list[str]]:
        roots: list[Path] = []
        errors: list[str] = []
        if raw_paths:
            for raw in raw_paths:
                p, err = _resolve_import_path(ip, raw)
                if err:
                    errors.append(err)
                if p is not None and p.exists():
                    roots.append(p)
        else:
            roots = _default_import_roots(ip)

        files: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            candidates = [root]
            if root.is_dir():
                candidates = sorted(root.rglob("*"), key=lambda p: p.as_posix())
            for p in candidates:
                try:
                    rp = p.resolve()
                    rel_parts = rp.relative_to(PROJECT_ROOT.resolve()).parts
                except Exception:
                    continue
                if any(part in _SSOT_IMPORT_SKIP_DIRS or part.startswith(".") for part in rel_parts[:-1]):
                    continue
                if not rp.is_file() or rp.suffix.lower() not in _SSOT_IMPORT_EXTENSIONS:
                    continue
                if rp in seen:
                    continue
                seen.add(rp)
                files.append(rp)
                if len(files) >= 256:
                    errors.append("import file limit reached at 256 files")
                    return files, errors
        return files, errors

    def _clean_import_line(line: str) -> str:
        line = re.sub(r"\s+", " ", str(line or "").strip())
        line = line.lstrip("#/*- ").rstrip("*/ ")
        return line[:260]

    def _snippet_lines(text: str, pattern: str, *, limit: int = 5) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in text.splitlines():
            line = _clean_import_line(raw)
            if len(line) < 4 or line in seen:
                continue
            if re.search(pattern, line, re.IGNORECASE):
                seen.add(line)
                out.append(line)
                if len(out) >= limit:
                    break
        return out

    def _purpose_lines(ip: str, path: Path, text: str) -> list[str]:
        out: list[str] = []
        module_names = re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)
        if module_names:
            out.append("RTL modules: " + ", ".join(module_names[:8]))
        for raw in text.splitlines():
            line = _clean_import_line(raw)
            if len(line) < 12:
                continue
            if re.search(r"\b(purpose|overview|summary|objective|function|module|ip)\b", line, re.IGNORECASE):
                out.append(line)
            elif ip.lower() in line.lower():
                out.append(line)
            elif path.suffix.lower() in {".md", ".txt", ".rst"} and not out:
                out.append(line)
            if len(out) >= 5:
                break
        return out

    def _extract_import_candidates(
        ip: str,
        files: list[Path],
    ) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, list[dict[str, str]]]]:
        patterns = {
            "bus_interface": r"\b(APB|APB4|AXI|AXI4|AXI4[- ]?Lite|AHB|Wishbone|I2C|I3C|SMBus|SPI|UART|PCIe|VDM)\b",
            "register_map": r"\b(register|csr|offset|address|addr|0x[0-9a-f]+|CTRL|STATUS|DATA|CMD|PRESCALE|IRQ|W1C|RO|RW)\b",
            "clock_reset": r"\b(clock|clk|reset|rst|rst_n|resetn|frequency|MHz|active[- ]?(low|high))\b",
            "interrupt": r"\b(interrupt|irq|int_|level|pulse|w1c|done|error)\b",
            "memory_map": r"\b(memory map|base address|base|range|window|SRAM|RAM|FIFO|buffer|address map)\b",
            "parameters": r"\b(parameter|localparam|define|configurable|width|depth|DATA_WIDTH|ADDR_WIDTH|FIFO_DEPTH|default)\b",
            "submodule_structure": r"\b(submodule|hierarchy|block|fsm|module|parser|core|regs|fifo|engine|controller)\b",
            "test_expectation": r"\b(test|verify|verification|coverage|scenario|assert|scoreboard|cocotb|uvm|regression|acceptance)\b",
        }
        snippets: dict[str, list[str]] = {key: [] for key, _ in _SSOT_REQUIRED_DECISIONS}
        sources: dict[str, list[dict[str, str]]] = {key: [] for key, _ in _SSOT_REQUIRED_DECISIONS}
        artifacts: list[dict[str, Any]] = []

        for path in files:
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                artifacts.append({
                    "path": _relative_project_path(path),
                    "error": f"read failed: {exc}",
                    "bytes": 0,
                })
                continue
            text = raw[:262_144]
            rel = _relative_project_path(path)
            artifacts.append({
                "path": rel,
                "bytes": len(raw.encode("utf-8", errors="ignore")),
                "truncated": len(raw) > len(text),
            })
            for line in _purpose_lines(ip, path, text):
                if line not in snippets["purpose"]:
                    snippets["purpose"].append(line)
                    sources["purpose"].append({"path": rel, "excerpt": line})
            for key, pattern in patterns.items():
                for line in _snippet_lines(text, pattern):
                    if line not in snippets[key]:
                        snippets[key].append(line)
                        sources[key].append({"path": rel, "excerpt": line})

        candidates: dict[str, str] = {}
        for key, _label in _SSOT_REQUIRED_DECISIONS:
            vals = snippets.get(key) or []
            if vals:
                candidates[key] = "; ".join(vals[:8])[:1200]
        return artifacts, candidates, sources

    def _merge_unique_records(
        existing: list[Any],
        incoming: list[dict[str, Any]],
        key_fields: tuple[str, ...],
        *,
        limit: int = 128,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [dict(x) for x in existing if isinstance(x, dict)]
        index: dict[tuple[str, ...], int] = {}
        for idx, item in enumerate(out):
            key = tuple(str(item.get(field) or "") for field in key_fields)
            if any(key):
                index[key] = idx
        for item in incoming:
            key = tuple(str(item.get(field) or "") for field in key_fields)
            if any(key) and key in index:
                out[index[key]].update(item)
            else:
                if any(key):
                    index[key] = len(out)
                out.append(dict(item))
        return out[-limit:]

    def _merge_todos_by_id(existing: Any, incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [dict(x) for x in existing if isinstance(x, dict)] if isinstance(existing, list) else []
        index = {str(item.get("id") or ""): idx for idx, item in enumerate(out) if str(item.get("id") or "")}
        for item in incoming:
            tid = str(item.get("id") or "").strip()
            if not tid:
                continue
            if tid in index:
                prior = out[index[tid]]
                status = prior.get("status")
                prior.update(item)
                if status:
                    prior["status"] = status
            else:
                index[tid] = len(out)
                out.append(dict(item))
        return out

    def _import_evidence_rows(
        artifacts: list[dict[str, Any]],
        sources: dict[str, list[dict[str, str]]],
    ) -> list[dict[str, Any]]:
        paths = [
            str(item.get("path") or "").strip()
            for item in artifacts
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        ]
        by_path: dict[str, list[dict[str, str]]] = {path: [] for path in paths}
        for key, entries in sources.items():
            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path") or "").strip()
                excerpt = str(entry.get("excerpt") or "").strip()
                if not path or not excerpt:
                    continue
                by_path.setdefault(path, []).append({"decision_key": key, "excerpt": excerpt[:500]})
        rows: list[dict[str, Any]] = []
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            path = str(artifact.get("path") or "").strip()
            if not path:
                continue
            rows.append({
                "path": path,
                "bytes": int(artifact.get("bytes") or 0),
                "truncated": bool(artifact.get("truncated")),
                "excerpts": by_path.get(path, [])[:24],
            })
        return rows

    def _import_section_todos(
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> list[dict[str, Any]]:
        todos: list[dict[str, Any]] = []
        all_refs = sorted({
            str(item.get("path") or "").strip()
            for entries in sources.values()
            for item in (entries or [])
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        })
        for section, title, keys in _SSOT_IMPORT_SECTION_TODO_SPECS:
            evidence_keys = [key for key in keys if str(candidates.get(key) or "").strip()]
            refs = sorted({
                str(item.get("path") or "").strip()
                for key in keys
                for item in sources.get(key, [])
                if isinstance(item, dict) and str(item.get("path") or "").strip()
            })
            evidence_note = ", ".join(evidence_keys) if evidence_keys else "no direct heuristic hit"
            todos.append({
                "id": f"IMPORT_SSOT_SECTION_{section.upper()}",
                "content": f"Review imported workspace evidence for SSOT `{section}`",
                "detail": (
                    f"Section {title}: inspect the imported workspace inventory and promote only "
                    f"source-backed facts into `{section}`. Current heuristic evidence keys: {evidence_note}. "
                    "If the workspace lacks this information, leave a precise SSOT QA/TBD item instead of "
                    "inventing fixed-template content."
                ),
                "criteria": [
                    f"`{section}` contains only source-backed values or explicit TBD/none markers",
                    "Every promoted field has a source_ref back to imported workspace evidence",
                    "Contradictions are listed under custom.atlas_import_conflicts or SSOT QA",
                    "No fixed-template behavior is added without evidence",
                ],
                "source_refs": refs or all_refs[:24] or ["custom.atlas_workspace_inventory"],
                "section": section,
                "decision_keys": list(keys),
                "evidence_keys": evidence_keys,
                "priority": "high" if evidence_keys else "normal",
                "required": True,
            })
        return todos

    def _import_downstream_todos(ip: str, source_refs: list[str], has_dv: bool) -> dict[str, list[dict[str, Any]]]:
        refs = source_refs[:24] or ["custom.atlas_import_doc_evidence"]
        todos: dict[str, list[dict[str, Any]]] = {
            "rtl-gen": [
                {
                    "id": "IMPORT_RTL_FROM_DOC_EVIDENCE",
                    "content": "Implement RTL only from imported doc-backed SSOT facts",
                    "detail": (
                        "Use custom.atlas_import_doc_evidence, custom.atlas_decisions, and the canonical "
                        "SSOT sections derived from them. If a required RTL behavior is only implied or "
                        "contradictory in the docs, emit an SSOT question instead of filling a template."
                    ),
                    "criteria": [
                        "RTL TODO plan references imported source_refs for doc-derived behavior",
                        "No RTL behavior is implemented from a fixed template when the import lacks evidence",
                        "DUT compile/lint evidence is fresh after doc-derived RTL edits",
                    ],
                    "source_refs": refs,
                    "owner_module": f"{ip}_core",
                    "owner_file": f"rtl/{ip}.sv",
                    "priority": "high",
                    "required": True,
                }
            ],
            "tb-gen": [
                {
                    "id": "IMPORT_TB_FROM_DOC_EVIDENCE",
                    "content": "Generate cocotb/pyuvm tests from imported verification evidence",
                    "detail": (
                        "Convert imported scenarios, acceptance criteria, protocol timing, and coverage notes "
                        "into SSOT test_requirements and executable cocotb/pyuvm tests. Use Python/pyuvm by default; "
                        "do not create SV tc/tb files unless the SSOT explicitly requests that backend."
                    ),
                    "criteria": [
                        "Every imported scenario has a cocotb/pyuvm test or a precise blocker",
                        "Scoreboard expectations trace to function_model or imported source_refs",
                        "Simulation emits results.xml, scoreboard_events.jsonl, VCD, and coverage evidence",
                    ],
                    "source_refs": refs,
                    "priority": "high" if has_dv else "normal",
                    "required": True,
                }
            ],
            "sim_debug": [
                {
                    "id": "IMPORT_SIM_DEBUG_EVIDENCE_MAP",
                    "content": "Use imported doc evidence to classify simulation failures",
                    "detail": (
                        "When cocotb/pyuvm results or waveforms disagree with expected behavior, classify the "
                        "mismatch against imported source_refs, SSOT function/cycle model, RTL, or TB ownership."
                    ),
                    "criteria": [
                        "Every failure report cites expected/got evidence and an imported or SSOT source_ref",
                        "Waveform/VCD checks cover imported timing, reset, interrupt, and protocol expectations when present",
                        "Escalations name the owning workflow: ssot-gen, rtl-gen, tb-gen, or coverage",
                    ],
                    "source_refs": refs,
                    "priority": "normal",
                    "required": True,
                }
            ],
        }
        return todos

    def _apply_import_yaml_todos(
        ip: str,
        doc: dict[str, Any],
        custom: dict[str, Any],
        artifacts: list[dict[str, Any]],
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> dict[str, Any]:
        evidence_rows = _import_evidence_rows(artifacts, sources)
        source_refs = [
            str(row.get("path") or "").strip()
            for row in evidence_rows
            if str(row.get("path") or "").strip()
        ]
        section_todos = _import_section_todos(candidates, sources)
        downstream = _import_downstream_todos(ip, source_refs, bool(candidates.get("test_expectation")))

        custom["atlas_import_doc_evidence"] = _merge_unique_records(
            custom.get("atlas_import_doc_evidence") if isinstance(custom.get("atlas_import_doc_evidence"), list) else [],
            evidence_rows,
            ("path",),
            limit=256,
        )
        custom["atlas_workspace_inventory"] = _merge_unique_records(
            custom.get("atlas_workspace_inventory") if isinstance(custom.get("atlas_workspace_inventory"), list) else [],
            evidence_rows,
            ("path",),
            limit=256,
        )
        prior_draft = custom.get("atlas_import_todo_draft") if isinstance(custom.get("atlas_import_todo_draft"), dict) else {}
        merged_section_todos = _merge_todos_by_id(
            prior_draft.get("section_todos") if isinstance(prior_draft, dict) else [],
            section_todos,
        )
        custom["atlas_import_section_todos"] = merged_section_todos
        custom["atlas_import_todo_draft"] = {
            "updated_at": time.time(),
            "source_refs": source_refs[:64],
            "section_todos": merged_section_todos,
            "downstream_todos": {
                stage: _merge_todos_by_id(
                    (prior_draft.get("downstream_todos") or {}).get(stage) if isinstance(prior_draft.get("downstream_todos"), dict) else [],
                    items,
                )
                for stage, items in downstream.items()
            },
        }

        workflow_todos = doc.get("workflow_todos")
        if not isinstance(workflow_todos, dict):
            workflow_todos = {}
            doc["workflow_todos"] = workflow_todos
        workflow_todos["ssot-gen"] = _merge_todos_by_id(workflow_todos.get("ssot-gen"), section_todos)
        for stage, items in downstream.items():
            workflow_todos[stage] = _merge_todos_by_id(workflow_todos.get(stage), items)

        return {
            "evidence_rows": len(evidence_rows),
            "section_todos": len(section_todos),
            "downstream_todos": {stage: len(items) for stage, items in downstream.items()},
        }

    def _merge_import_candidates(
        ip: str,
        kind: str,
        state: dict[str, Any],
        artifacts: list[dict[str, Any]],
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        filled, conflicts = _record_ssot_decisions(ip, kind, candidates, sources)
        doc, custom = _ssot_custom(ip, kind)
        todo_summary = _apply_import_yaml_todos(ip, doc, custom, artifacts, candidates, sources)
        manifest_path = PROJECT_ROOT / ip / "req" / "import_manifest.json"
        try:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "ssot_import_manifest.v1",
                        "ip": ip,
                        "workflow": "ssot-gen",
                        "updated_at": time.time(),
                        "kind": kind,
                        "artifacts": artifacts,
                        "candidate_facts": candidates,
                        "sources": sources,
                        "filled_decisions": filled,
                        "conflicts": conflicts,
                        "workflow_todo_summary": todo_summary,
                        "next": "/grill-me" if conflicts or _missing_ssot_decisions(ip, state) else "/to-ssot",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass
        imports = custom.get("atlas_imports")
        if not isinstance(imports, list):
            imports = []
        imports.append({
            "imported_at": time.time(),
            "artifacts": artifacts,
            "filled": filled,
            "conflicts": conflicts,
            "yaml_todos": todo_summary,
        })
        custom["atlas_imports"] = imports
        _save_ssot_draft(ip, doc)
        imported_artifacts = state.get("imported_artifacts")
        if not isinstance(imported_artifacts, list):
            imported_artifacts = []
        imported_artifacts.extend({
            "path": str(a.get("path") or ""),
            "imported_at": time.time(),
        } for a in artifacts if a.get("path"))
        state["imported_artifacts"] = imported_artifacts[-64:]
        state["last_import_yaml_todos"] = todo_summary
        state["last_step"] = "import"
        if conflicts:
            state["last_issue"] = "import_conflicts"
        if conflicts:
            state["approved"] = False
            state["approved_at"] = 0
        state["status"] = "answered" if not _missing_ssot_decisions(ip, state) else "planned"
        return filled, conflicts

    def _import_defaults_if_available(ip: str, kind: str, state: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        """Import the current IP workspace into the SSOT draft when requested."""
        files, errors = _collect_import_files(ip, [])
        if not files:
            return [], [], [], errors
        artifacts, candidates, sources = _extract_import_candidates(ip, files)
        filled, conflicts = _merge_import_candidates(ip, kind, state, artifacts, candidates, sources)
        state.setdefault("ip", ip)
        state.setdefault("kind", kind)
        state["active_session"] = _active_session_value() or _canonical_session_string(ip)
        _save_ssot_state(ip, state)
        return filled, conflicts, artifacts, errors

    def _auto_approve_if_complete(ip: str, state: dict[str, Any], *, reason: str) -> bool:
        if state.get("approved"):
            return False
        if _missing_ssot_decisions(ip, state):
            return False
        doc = _load_ssot_draft(ip)
        custom = doc.get("custom") if isinstance(doc.get("custom"), dict) else {}
        conflicts = custom.get("atlas_import_conflicts") if isinstance(custom, dict) else []
        if conflicts:
            return False
        state["approved"] = True
        state["approved_at"] = time.time()
        state["status"] = "approved"
        state["last_step"] = reason
        _save_ssot_state(ip, state)
        return True

    def _rtl_blocker_path(ip: str) -> Path:
        return PROJECT_ROOT / ip / "rtl" / "rtl_blocked.json"

    def _load_rtl_blocker(ip: str) -> dict[str, Any]:
        path = _rtl_blocker_path(ip)
        if not path.is_file():
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            return doc if isinstance(doc, dict) else {}
        except Exception as exc:
            return {"reason": f"rtl_blocked.json parse failed: {exc}", "questions": []}

    def _rtl_module_contract_placeholder(q: dict[str, Any]) -> str:
        missing = q.get("missing_modules") if isinstance(q.get("missing_modules"), list) else []
        if not missing and isinstance(q.get("candidate_modules"), list):
            missing = q.get("candidate_modules") or []
        available = q.get("available_refs") if isinstance(q.get("available_refs"), dict) else {}
        rows: list[str] = []
        orphan_refs = q.get("orphan_refs") if isinstance(q.get("orphan_refs"), list) else []
        if orphan_refs:
            rows.append("# orphan refs needing an RTL owner: " + ", ".join(str(v) for v in orphan_refs[:16]))
        if available:
            for key in ("source_sections", "function_model_refs", "decomposition_refs", "cycle_model_refs", "feature_refs", "dataflow_refs", "register_refs", "fsm_refs", "test_refs", "ports"):
                vals = available.get(key) if isinstance(available.get(key), list) else []
                if vals:
                    rows.append(f"# available {key}: " + ", ".join(str(v) for v in vals[:10]))
        rows.append("module_contracts:")
        for item in missing[:8]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            file = str(item.get("file") or "").strip()
            rows += [
                f"  - name: {name}",
                f"    file: {file}",
                "    implements:",
                "      - <specific behavior this module owns>",
                "    source_sections: [<ssot section names>]",
                "    function_model_refs: [<function_model paths>]",
                "    decomposition_refs: [<decomposition paths>]",
                "    cycle_model_refs: [<cycle_model paths>]",
                "    feature_refs: [<feature names or paths>]",
                "    dataflow_refs: [<dataflow paths>]",
                "    register_refs: [<register names or paths>]",
                "    fsm_refs: [<fsm paths>]",
                "    ports: [<owned ports or internal interface ports>]",
                "    connections: {<local_port>: <ssot/interface signal>}",
            ]
        return "\n".join(rows)

    _RTL_OWNERSHIP_BLOCKER_IDS = {
        "RTL_DYNAMIC_TODO_OWNERSHIP",
        "RTL_MODULE_CONTRACTS",
        "RTL_MODULE_BEHAVIOR_MATCH",
        "SSOT_BEHAVIOR_OWNERSHIP",
    }
    _RTL_CONNECTION_BLOCKER_IDS = {
        "RTL_RESOLVE_CONNECTION_CONTRACTS",
        "RTL_CONNECTION_CONTRACTS",
        "RTL_MANIFEST_CONNECTION_CONTRACTS",
    }
    _RTL_IMPL_BLOCKER_IDS = {
        "RTL_TODO_PLAN_MISSING",
        "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
        "LLM_RTL_IMPLEMENTATION_REQUIRED",
        "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
    }

    def _rtl_blocker_qa_section(qid: str, raw: dict[str, Any]) -> tuple[str, str, str]:
        text = " ".join(
            [
                qid,
                str(raw.get("decision_needed") or ""),
                str(raw.get("evidence") or ""),
                " ".join(str(ref) for ref in raw.get("source_refs") or [] if isinstance(raw.get("source_refs"), list)),
                " ".join(str(field) for field in raw.get("required_fields") or [] if isinstance(raw.get("required_fields"), list)),
            ]
        ).lower()
        if qid == "RTL_TARGET_SCALE_POLICY" or "target_scale" in text or "target scale" in text:
            return "19_workflow_todos", "19. Workflow / Human Gates", "quality_gates.rtl_gen.target_scale"
        if qid in _RTL_CONNECTION_BLOCKER_IDS or "connection_contract" in text or "integration.connections" in text:
            return "17_integration", "17. Integration / Connection Contracts", "integration.connections"
        if qid in _RTL_OWNERSHIP_BLOCKER_IDS or "sub_modules" in text or "ownership" in text:
            return "04_architecture", "4. Architecture / Decomposition", "sub_modules"
        if "interface" in text or "port" in text or "clock" in text or "reset" in text:
            return "03_interface", "3. Interface", "io_list"
        if "coverage" in text or "test_requirements" in text or "verification" in text:
            return "18_verification", "18. Verification / Gates", "test_requirements"
        return "19_workflow_todos", "19. Workflow / Human Gates", "workflow_todos.rtl-gen"

    def _rtl_blocker_cards(blocker: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for q in blocker.get("questions") if isinstance(blocker.get("questions"), list) else []:
            if not isinstance(q, dict):
                continue
            qid = str(q.get("id") or "").strip() or "RTL_BLOCKER"
            if qid in _RTL_IMPL_BLOCKER_IDS:
                continue
            raw_options = q.get("options") if isinstance(q.get("options"), list) else []
            options = [
                {
                    "id": f"{qid}_opt{idx}",
                    "label": str(opt)[:96],
                    "detail": str(opt),
                }
                for idx, opt in enumerate(raw_options, start=1)
                if str(opt).strip()
            ]
            subtitle_parts = [qid]
            if q.get("evidence"):
                subtitle_parts.append(str(q.get("evidence"))[:220])
            if q.get("recommended_default"):
                subtitle_parts.append("Recommended: " + str(q.get("recommended_default"))[:220])
            card = {
                "id": qid,
                "question": str(q.get("decision_needed") or qid),
                "kind": "single" if options else "input",
                "subtitle": " · ".join(subtitle_parts),
                "options": options,
                "blocker": q,
            }
            if qid in _RTL_OWNERSHIP_BLOCKER_IDS:
                card["kind"] = "input"
                card["multiline"] = True
                card["subtitle"] = (
                    str(card.get("subtitle") or "")
                    + " · Paste YAML/JSON with module_contracts; option clicks alone do not approve RTL ownership."
                )[:900]
                card["placeholder"] = _rtl_module_contract_placeholder(q)
            cards.append(card)
        return cards

    def _rtl_blocker_flow_id(blocker: dict[str, Any]) -> str:
        payload = json.dumps(blocker.get("questions") or blocker, ensure_ascii=False, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"rtl_blocker_{digest}"

    def _rtl_blocker_qa_questions(
        ip: str,
        blocker: dict[str, Any],
        cards: list[dict[str, Any]],
        *,
        reason: str,
    ) -> list[dict[str, Any]]:
        source_path = str(_rtl_blocker_path(ip).relative_to(PROJECT_ROOT))
        questions: list[dict[str, Any]] = []
        for card in cards:
            qid = str(card.get("id") or "RTL_BLOCKER").strip() or "RTL_BLOCKER"
            raw = card.get("blocker") if isinstance(card.get("blocker"), dict) else {}
            orphan_refs = raw.get("orphan_refs") if isinstance(raw.get("orphan_refs"), list) else []
            required_fields = raw.get("required_fields") if isinstance(raw.get("required_fields"), list) else []
            candidate_modules = raw.get("candidate_modules") if isinstance(raw.get("candidate_modules"), list) else []
            section_id, section_title, field_path = _rtl_blocker_qa_section(qid, raw)
            criteria = [
                "Resolve the blocker by updating SSOT-owned authority artifacts, not by hand-editing generated RTL.",
                f"Rerun rtl-gen preflight until `{qid}` no longer appears in `{source_path}`.",
            ]
            if qid in _RTL_OWNERSHIP_BLOCKER_IDS:
                criteria.append("Every orphan source_ref must be covered by an exact or dotted-parent ref in one RTL module contract.")
            elif qid == "RTL_TARGET_SCALE_POLICY":
                criteria.append("Lock positive quality_gates.rtl_gen.target_scale minima or approve target_scale_waiver with owner and reason.")
            elif qid in _RTL_CONNECTION_BLOCKER_IDS:
                criteria.append("Answer with machine-readable module/port/signal connection contracts before top integration signoff.")
            source_refs = [source_path]
            source_refs.extend(str(ref) for ref in orphan_refs[:64])
            if raw.get("evidence"):
                source_refs.append(str(raw.get("evidence")))
            questions.append({
                "id": qid,
                "decision_key": qid,
                "decision_label": str(card.get("question") or raw.get("decision_needed") or qid),
                "question": str(card.get("question") or raw.get("decision_needed") or qid),
                "kind": str(card.get("kind") or "input"),
                "subtitle": str(card.get("subtitle") or ""),
                "options": card.get("options") or [],
                "qa_type": "rtl_blocker",
                "source": reason,
                "source_refs": source_refs,
                "field_path": field_path,
                "section_id": section_id,
                "section_title": section_title,
                "content": f"Resolve rtl-gen blocker `{qid}` for `{ip}`.",
                "detail": (
                    f"Evidence: {raw.get('evidence') or blocker.get('reason') or source_path}. "
                    f"Required fields: {', '.join(str(v) for v in required_fields[:12]) or 'SSOT module contract fields'}. "
                    f"Orphan refs: {len(orphan_refs)}. Candidate modules: {len(candidate_modules)}."
                ),
                "criteria": criteria,
                "placeholder": card.get("placeholder") or "",
                "multiline": bool(card.get("multiline")),
            })
        return questions

    def _run_rtl_blocker_resolution(ip: str, blocker: dict[str, Any], answer_entries: list[dict[str, Any]], client_session: Any | None = None) -> str:
        import subprocess

        state = _load_ssot_state(ip)
        state.setdefault("ip", ip)
        state.setdefault("kind", "rtl blocker resolution")
        state["approved"] = True
        state["status"] = "rtl_blocker_answered"
        state["rtl_blocker_source"] = str(_rtl_blocker_path(ip).relative_to(PROJECT_ROOT))
        state["rtl_blocker_answers"] = answer_entries
        _save_ssot_state(ip, state)
        answers_path = _ssot_session_dir(ip) / "rtl_blocker_answers.json"
        answers_path.parent.mkdir(parents=True, exist_ok=True)
        answers_path.write_text(json.dumps({
            "rtl_blocker_answers": answer_entries,
            "source": "atlas-ui",
            "ip": ip,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        scripts = {
            "resolve": SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "resolve_rtl_blockers.py",
            "check": SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh",
            "fl": SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py",
            "preflight": SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py",
        }
        runs: list[dict[str, Any]] = []

        def _run(label: str, cmd: list[str], timeout_s: int = 180) -> int:
            proc = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout_s,
            )
            runs.append({
                "label": label,
                "cmd": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "").strip()[:12000],
                "stderr": (proc.stderr or "").strip()[:12000],
            })
            return int(proc.returncode)

        resolve_rc = _run("resolve_rtl_blockers", [
            sys.executable,
            str(scripts["resolve"]),
            ip,
            "--root",
            str(PROJECT_ROOT),
            "--answers-json",
            str(answers_path),
        ])
        check_rc = _run("check_ssot_disk", ["bash", str(scripts["check"]), ip]) if resolve_rc == 0 else None
        fl_rc = _run("emit_fl_model", [sys.executable, str(scripts["fl"]), ip, "--root", str(PROJECT_ROOT)]) if check_rc == 0 else None
        preflight_rc = _run("rtl_preflight", [sys.executable, str(scripts["preflight"]), ip, "--root", str(PROJECT_ROOT), "--preflight-only"]) if fl_rc == 0 else None

        if preflight_rc == 0:
            headline = "[SSOT RESULT] rtl blocker decisions applied; rtl-gen preflight PASS"
        elif preflight_rc == 2:
            headline = "[SSOT QUESTION] rtl-gen still needs SSOT decisions"
        else:
            headline = "[SSOT BLOCKED] rtl blocker resolution failed validation"

        lines = [
            headline,
            f"module: {ip}",
            f"source blocker: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}",
            f"answers captured: {len(answer_entries)}",
            "",
            "runs:",
        ]
        for run in runs:
            lines.append(f"- {run['label']}: exit {run['returncode']}")
            lines.append(f"  cmd: {run['cmd']}")
            if run["stdout"]:
                lines.append("  stdout:")
                lines.append(run["stdout"])
            if run["stderr"]:
                lines.append("  stderr:")
                lines.append(run["stderr"])
        lines += [
            "",
            "artifacts:",
            f"- {ip}/yaml/{ip}.ssot.yaml",
            f"- {ip}/rtl/rtl_blocked_resolved.json",
            f"- {ip}/model/functional_model.py",
            f"- {ip}/model/decomposition.json",
            f"- {ip}/cov/fcov_plan.json",
        ]
        if preflight_rc == 0:
            lines.append("")
            lines.append("next: queued /ssot-rtl to start RTL implementation from the repaired SSOT")
            _queue_prompt_for_session(client_session, f"/ssot-rtl {ip}")
        return "\n".join(lines)

    def _start_rtl_blocker_qna(
        ip: str,
        *,
        reason: str = "rtl-gen preflight",
        interactive: bool = True,
        client_session: Any | None = None,
    ) -> bool:
        blocker = _load_rtl_blocker(ip)
        cards = _rtl_blocker_cards(blocker)
        if not blocker or not cards:
            _emit_workflow_result(
                f"[RTL BLOCKER Q&A] no rtl_blocked.json questions found for {ip}",
                "resolve-rtl-blockers",
            )
            return True

        # ATLAS_RTL_BLOCKER_AUTO_SKIP=1 → never surface SSOT QA cards from
        # rtl_blocked.json. The blocker JSON is still written on disk so
        # `/resolve-rtl-blockers <ip>` and ssot-gen can still address them
        # on demand, but the agent stops popping 8+ Q&A cards at the user
        # mid-flight. Matches the user's "SSOT-GEN 만 QA" policy: rtl-gen
        # writing blockers is fine, but auto-promoting them into SSOT QA
        # is the part that became spam.
        if os.environ.get("ATLAS_RTL_BLOCKER_AUTO_SKIP", "").strip() in {"1", "true", "yes", "on"}:
            msg = (
                f"[RTL BLOCKER] {len(cards)} blocker(s) for {ip} recorded to "
                f"{_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}\n"
                "QA card promotion suppressed by ATLAS_RTL_BLOCKER_AUTO_SKIP.\n"
                f"Run `/resolve-rtl-blockers {ip}` to address them on demand."
            )
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _emit_workflow_result(msg, "resolve-rtl-blockers")
            return True

        ctx_ip, ctx_session = _active_ssot_qa_context()
        ssot_session = ctx_session if ctx_ip == ip and ctx_session else _canonical_session_string(ip)
        qa_write_session = ssot_session if client_session is not None else None
        qa_flow_id = _rtl_blocker_flow_id(blocker)
        qa_questions = _rtl_blocker_qa_questions(ip, blocker, cards, reason=reason)
        qa_pairs = _ssot_q_pairs_from_questions(qa_questions)
        if qa_pairs:
            _upsert_ssot_qa_items(
                ip,
                flow_id=qa_flow_id,
                kind=str((_load_ssot_state(ip) or {}).get("kind") or "general IP"),
                q_pairs=qa_pairs,
                status="pending",
                session=qa_write_session,
                source="rtl-blocker",
            )
            bridge.emit(
                "ssot_qa_updated",
                ip=ip,
                workflow="ssot-gen",
                flow_id=qa_flow_id,
                session=ssot_session,
            )

        if not interactive:
            msg = (
                f"[RTL BLOCKER Q&A] recorded {len(qa_pairs)} pending SSOT QA card(s) for {ip}\n"
                f"source: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}\n"
                f"session: {ssot_session}\n"
                "next: answer from SSOT QA/Preview, or run /resolve-rtl-blockers "
                f"{ip} when ready to apply the decisions."
            )
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "resolve-rtl-blockers")
            return True

        def _worker() -> None:
            import uuid as _uuid

            flow_id = "rtlq_" + _uuid.uuid4().hex[:10]
            bridge.open_question(flow_id)
            bridge.emit("ask_user", flow_id=flow_id, questions=cards)
            bridge.emit("agent_state", running=True)
            try:
                ans = bridge.wait_answer(flow_id, timeout=900)
            finally:
                bridge.close_question(flow_id)
            if not isinstance(ans, dict) or not isinstance(ans.get("answers"), list):
                msg = (
                    f"[RTL BLOCKER Q&A] {ip}: no answer received; SSOT remains blocked.\n"
                    f"source: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}"
                )
                _append_session_message(_canonical_session_string(ip), "assistant", msg)
                _append_workflow_history("ssot-gen", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, "resolve-rtl-blockers")
                return

            answer_entries: list[dict[str, Any]] = []
            qa_answers: dict[str, dict[str, Any]] = {}
            for qa_pair, card, raw_answer in zip(qa_pairs, cards, ans.get("answers") or []):
                qa = raw_answer if isinstance(raw_answer, dict) else {}
                key, _label, question = qa_pair
                answer_text = _answer_text(qa, question)
                answer_entries.append({
                    "id": card.get("id"),
                    "decision_needed": card.get("question"),
                    "answer": answer_text,
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                    "source": reason,
                })
                qa_answers[key] = {
                    "answer": answer_text,
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                }
            if qa_pairs:
                _upsert_ssot_qa_items(
                    ip,
                    flow_id=qa_flow_id,
                    kind=str((_load_ssot_state(ip) or {}).get("kind") or "general IP"),
                    q_pairs=qa_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=qa_write_session,
                    source="rtl-blocker",
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ip,
                    workflow="ssot-gen",
                    flow_id=qa_flow_id,
                    session=ssot_session,
                )
            try:
                msg = _run_rtl_blocker_resolution(ip, blocker, answer_entries, client_session)
            except Exception as exc:
                msg = f"[RTL BLOCKER Q&A] {ip}: failed to apply answers: {exc}"
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "resolve-rtl-blockers")

        ctx = contextvars.copy_context()
        threading.Thread(target=ctx.run, args=(_worker,), daemon=True).start()
        return True

    def _sim_human_gate_cards(ip: str, classify_doc: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        classifications = classify_doc.get("classifications")
        for item in classifications if isinstance(classifications, list) else []:
            if not isinstance(item, dict) or item.get("llm_loop_allowed") is not False:
                continue
            goal_id = str(item.get("goal_id") or "EQ_HUMAN_GATE").strip() or "EQ_HUMAN_GATE"
            human_question = str(item.get("human_question") or "").strip()
            evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
            ssot_refs = evidence.get("ssot_refs") if isinstance(evidence.get("ssot_refs"), list) else []
            fl_expected = evidence.get("fl_expected") if isinstance(evidence.get("fl_expected"), dict) else {}
            rtl_observed = evidence.get("rtl_observed") if isinstance(evidence.get("rtl_observed"), dict) else {}
            evidence_bits = [
                f"class={item.get('classification') or 'unknown'}",
                f"owner={item.get('owner') or 'human'}",
            ]
            if ssot_refs:
                evidence_bits.append("SSOT " + ", ".join(str(x) for x in ssot_refs[:3]))
            if fl_expected:
                evidence_bits.append("FL " + json.dumps(fl_expected, sort_keys=True)[:180])
            if rtl_observed:
                evidence_bits.append("RTL " + json.dumps(rtl_observed, sort_keys=True)[:180])
            cards.append({
                "id": goal_id,
                "question": f"Decision needed for {goal_id}: define expected behavior or approve waiver",
                "kind": "single",
                "subtitle": " · ".join(evidence_bits)[:500],
                "options": [
                    {
                        "id": f"{goal_id}_update_ssot",
                        "label": "Update SSOT",
                        "detail": "Record the intended behavior in SSOT/requirements, then regenerate FL, equivalence goals, TB, and coverage.",
                    },
                    {
                        "id": f"{goal_id}_waiver",
                        "label": "Waiver",
                        "detail": "Record an explicit waiver/rationale; signoff remains human-owned until the waiver is reviewed.",
                    },
                ],
                "human_question": human_question,
                "classification": item,
            })
        return cards

    def _persist_sim_human_gate_answers(
        ip: str,
        classify_doc: dict[str, Any],
        cards: list[dict[str, Any]],
        answer_entries: list[dict[str, Any]],
    ) -> Path:
        sim_dir = PROJECT_ROOT / ip / "sim"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_path = sim_dir / "human_gate_answers.json"
        doc = {
            "schema_version": 1,
            "type": "fl_rtl_human_gate_answers",
            "ip": ip,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": str((PROJECT_ROOT / ip / "sim" / "mismatch_classification.json").relative_to(PROJECT_ROOT)),
            "answers": answer_entries,
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        state = _load_ssot_state(ip)
        state.setdefault("ip", ip)
        state.setdefault("kind", "equivalence human gate")
        state["status"] = "equivalence_human_gate_answered"
        state["equivalence_human_gate_source"] = doc["source"]
        state["equivalence_human_gate_answers"] = answer_entries
        state["equivalence_human_gate_classifications"] = [
            card.get("classification") for card in cards if isinstance(card.get("classification"), dict)
        ]
        _save_ssot_state(ip, state)

        return out_path

    def _start_sim_human_gate_qna(ip: str, classify_doc: dict[str, Any], *, reason: str = "sim-debug", client_session: Any | None = None) -> bool:
        cards = _sim_human_gate_cards(ip, classify_doc)
        if not cards:
            return False

        def _worker() -> None:
            import uuid as _uuid

            flow_id = "simq_" + _uuid.uuid4().hex[:10]
            bridge.open_question(flow_id)
            bridge.emit("ask_user", flow_id=flow_id, questions=cards)
            bridge.emit("agent_state", running=True)
            try:
                ans = bridge.wait_answer(flow_id, timeout=900)
            finally:
                bridge.close_question(flow_id)
            if not isinstance(ans, dict) or not isinstance(ans.get("answers"), list):
                msg = (
                    f"[SIM HUMAN GATE] {ip}: no answer received; mismatch remains human-gated.\n"
                    f"source: {ip}/sim/mismatch_classification.json"
                )
                _append_session_message(f"{ip}/sim_debug", "assistant", msg)
                _append_workflow_history("sim_debug", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, "sim-debug")
                return

            answer_entries: list[dict[str, Any]] = []
            for card, raw_answer in zip(cards, ans.get("answers") or []):
                qa = raw_answer if isinstance(raw_answer, dict) else {}
                classification = card.get("classification") if isinstance(card.get("classification"), dict) else {}
                answer_entries.append({
                    "goal_id": card.get("id"),
                    "decision_needed": card.get("question"),
                    "answer": _answer_text(qa, card),
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                    "source": reason,
                    "classification": classification.get("classification"),
                    "owner": classification.get("owner"),
                    "evidence": classification.get("evidence") if isinstance(classification.get("evidence"), dict) else {},
                    "human_question": card.get("human_question") or "",
                })
            try:
                out_path = _persist_sim_human_gate_answers(ip, classify_doc, cards, answer_entries)
                msg = (
                    f"[SIM HUMAN GATE] captured {len(answer_entries)} answer(s) for {ip}\n"
                    f"answers: {out_path.relative_to(PROJECT_ROOT)}\n"
                    "next: rerun SSOT/FL/equivalence generation if behavior changed, or keep signoff human-owned for waivers"
                )
            except Exception as exc:
                msg = f"[SIM HUMAN GATE] {ip}: failed to persist answers: {exc}"
            _append_session_message(f"{ip}/sim_debug", "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "sim-debug")

        ctx = contextvars.copy_context()
        threading.Thread(target=ctx.run, args=(_worker,), daemon=True).start()
        return True

    def _handle_resolve_rtl_blockers_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("resolve-rtl-blockers", "rrb"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[resolve-rtl-blockers] missing or invalid IP name\n"
                "usage: /resolve-rtl-blockers <ip_name>",
                "resolve-rtl-blockers",
            )
            return True
        return _start_rtl_blocker_qna(ip, reason="manual /resolve-rtl-blockers", client_session=client_session)

    app.state.atlas_bridge = bridge
    app.state.start_rtl_blocker_qna = _start_rtl_blocker_qna
    app.state.active_ssot_qa_context = _active_ssot_qa_context
    app.state.valid_ip_name = _valid_ip_name
    app.state.ssot_q_pairs_from_questions = _ssot_q_pairs_from_questions
    app.state.load_ssot_state = _load_ssot_state
    app.state.upsert_ssot_qa_items = _upsert_ssot_qa_items
    app.state.status_group = _status_group

    def _emit_workflow_result(text: str, tool: str = "workflow") -> None:
        body = (text or "").strip() or "(no output)"
        payload = "```\n" + body + "\n```"
        bridge.emit("tool_result", text=payload, tool=tool, truncated=False)
        bridge.emit("slash_output", text=payload)
        bridge.emit("flush")
        bridge.emit("commands_changed")
        bridge.emit("agent_state", running=False)

    def _handle_import_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("import", "imp"):
            return False

        ip, raw_paths, err = _parse_import_args(args)
        if err:
            _emit_workflow_result(err, "import")
            return True
        _set_active_ssot_ip(ip)
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT IMPORT] failed to scaffold {ip}: {exc}", "import")
            return True

        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        kind = str(state.get("kind") or "imported IP evidence")
        _ensure_ssot_draft(ip, kind)
        files, errors = _collect_import_files(ip, raw_paths)
        if not files:
            msg = (
                f"[SSOT IMPORT] {ip}: no importable files found\n"
                f"searched: {', '.join(raw_paths) if raw_paths else ip + '/'}\n"
                "usage: /import [path ...]  or  /import --ip <ip_name> [path ...]"
            )
            if errors:
                msg += "\n\nnotes:\n" + "\n".join(f"- {e}" for e in errors[:8])
            _append_session_message(_canonical_session_string(ip), "user", text)
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "import")
            _emit_ssot_approval_ready(ip, state)
            return True

        artifacts, candidates, sources = _extract_import_candidates(ip, files)
        filled, conflicts = _merge_import_candidates(ip, kind, state, artifacts, candidates, sources)
        state.setdefault("ip", ip)
        state.setdefault("kind", kind)
        state["active_session"] = _active_session_value() or _canonical_session_string(ip)
        _save_ssot_state(ip, state)

        missing = _missing_ssot_decisions(ip, state)
        todo_summary = state.get("last_import_yaml_todos") if isinstance(state.get("last_import_yaml_todos"), dict) else {}
        downstream_summary = todo_summary.get("downstream_todos") if isinstance(todo_summary.get("downstream_todos"), dict) else {}
        todo_parts = [f"ssot-gen sections={todo_summary.get('section_todos', 0)}"]
        todo_parts.extend(f"{stage}={count}" for stage, count in downstream_summary.items())
        todo_parts.append(f"evidence rows={todo_summary.get('evidence_rows', 0)}")
        lines = [
            f"[SSOT IMPORT] {ip}",
            f"imported files: {len(files)}",
            "yaml TODO draft: " + ", ".join(todo_parts),
        ]
        if filled:
            lines.append("filled decisions: " + ", ".join(filled))
        else:
            lines.append("filled decisions: (none)")
        if conflicts:
            lines.append("conflicts needing /grill-me review: " + ", ".join(c["key"] for c in conflicts[:8]))
        if missing:
            lines.append("missing decisions: " + ", ".join(missing))
        else:
            lines.append("missing decisions: (none)")
        if errors:
            lines += ["", "notes:"]
            lines.extend(f"- {e}" for e in errors[:8])
        lines += [
            "",
            "evidence:",
            f"- {ip}/req/import_manifest.json",
        ]
        lines.extend(f"- {a.get('path')}" for a in artifacts[:12])
        if len(artifacts) > 12:
            lines.append(f"- ... {len(artifacts) - 12} more")
        lines += [
            "",
            "Next:",
            "  /grill-me" if missing or conflicts else "  approve",
            "  /to-ssot after approval",
        ]
        msg = "\n".join(lines)
        _append_session_message(_canonical_session_string(ip), "user", text)
        _append_session_message(_canonical_session_string(ip), "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "import")
        _emit_ssot_approval_ready(ip, state, missing)
        return True

    def _safe_import_upload_name(name: str) -> str:
        raw = Path(str(name or "import.txt")).name
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._")
        if not safe:
            safe = "import.txt"
        return safe[:120]

    @app.post("/api/ssot/import/upload")
    async def api_ssot_import_upload(request: Request):
        """Upload requirement/source evidence into <ip>/req/imports/.

        The route only stores the attachment and returns the exact /import
        command to run. That keeps import semantics in the existing slash
        command path, so Web UI, Textual UI, and headless command handling
        stay aligned.
        """
        content_type = (request.headers.get("content-type") or "").lower()
        upload_entries: list[tuple[str, bytes]] = []
        ip = ""
        if "json" in content_type:
            try:
                body = await request.json()
            except Exception as exc:
                return JSONResponse({"error": f"invalid json body: {exc}"}, status_code=400)
            ip = str((body or {}).get("ip") or _active_ssot_ip() or "").strip()
            import base64 as _base64_import

            for idx, item in enumerate((body or {}).get("files") or []):
                if not isinstance(item, dict):
                    continue
                filename = str(item.get("name") or f"import_{idx}.txt")
                encoded = str(item.get("content_b64") or "")
                if not encoded:
                    continue
                try:
                    upload_entries.append((filename, _base64_import.b64decode(encoded, validate=True)))
                except Exception as exc:
                    return JSONResponse({"error": f"{filename}: invalid base64 payload: {exc}"}, status_code=400)
        else:
            try:
                form = await request.form()
            except Exception as exc:
                return JSONResponse({"error": f"invalid multipart form: {exc}"}, status_code=400)
            ip = str(form.get("ip") or _active_ssot_ip() or "").strip()
            uploads = []
            try:
                uploads.extend(form.getlist("files"))  # type: ignore[attr-defined]
                uploads.extend(form.getlist("file"))  # type: ignore[attr-defined]
            except Exception:
                one = form.get("files") or form.get("file")
                if one is not None:
                    uploads.append(one)
            uploads = [up for up in uploads if hasattr(up, "read")]
            for idx, upload in enumerate(uploads[:16]):
                filename = getattr(upload, "filename", "") or f"import_{idx}.txt"
                try:
                    raw = await upload.read()
                except Exception as exc:
                    return JSONResponse({"error": f"{filename}: read failed: {exc}"}, status_code=400)
                if not isinstance(raw, (bytes, bytearray)):
                    raw = str(raw).encode("utf-8", errors="replace")
                upload_entries.append((filename, bytes(raw)))

        if not _valid_ip_name(ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        if not upload_entries:
            return JSONResponse({"error": "missing file upload"}, status_code=400)

        dest_dir = PROJECT_ROOT / ip / "req" / "imports"
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return JSONResponse({"error": f"cannot create import dir: {exc}"}, status_code=500)

        saved: list[dict[str, Any]] = []
        errors: list[str] = []
        max_bytes = 12 * 1024 * 1024
        for idx, (raw_name, raw) in enumerate(upload_entries[:16]):
            filename = _safe_import_upload_name(raw_name or f"import_{idx}.txt")
            suffix = Path(filename).suffix.lower()
            if suffix not in _SSOT_IMPORT_EXTENSIONS:
                errors.append(f"{filename}: unsupported extension {suffix or '(none)'}")
                continue
            if len(raw) > max_bytes:
                errors.append(f"{filename}: file too large ({len(raw)} bytes > {max_bytes})")
                continue
            stamp = int(time.time() * 1000)
            target = dest_dir / f"{stamp}_{idx}_{filename}"
            try:
                target.write_bytes(bytes(raw))
                rel = target.relative_to(PROJECT_ROOT).as_posix()
                saved.append({"path": rel, "name": filename, "bytes": len(raw)})
            except OSError as exc:
                errors.append(f"{filename}: write failed: {exc}")

        if not saved:
            return JSONResponse({"error": "no files saved", "errors": errors}, status_code=400)
        paths = [item["path"] for item in saved]
        command = f"/import --ip {ip} " + " ".join(f"@{path}" for path in paths)
        return JSONResponse({
            "ok": True,
            "ip": ip,
            "saved": saved,
            "paths": paths,
            "errors": errors,
            "command": command,
        })

    def _handle_grill_me_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("grill-me", "grill", "g"):
            return False
        # First arg, if it parses as a valid IP name, is the explicit
        # IP target. Anything else (e.g. "Q&A", "memory_map") is treated
        # as a topic hint and the active IP is used instead. Previously
        # we hard-rejected with "invalid IP name" any time the first
        # token failed _valid_ip_name, which made `/grill-me Q&A` blow
        # up even though the user clearly meant the active IP.
        ip_arg = args.split(None, 1)[0] if args else ""
        if ip_arg and not _valid_ip_name(ip_arg):
            ip_arg = ""  # fall through to _active_ssot_ip()
        ip = ip_arg or _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GRILL] no active IP found\n"
                "usage: /new-ip <ip_name> first, then /grill-me",
                "grill-me",
            )
            return True
        _set_active_ssot_ip(ip)
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT GRILL] failed to scaffold {ip}: {exc}", "grill-me")
            return True
        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "TBD"))
        state["active_session"] = _active_session_value() or _canonical_session_string(ip)
        state["last_step"] = "grill-me"
        _save_ssot_state(ip, state)
        missing = _missing_ssot_decisions(ip, state)
        msg = (
            f"[SSOT GRILL] {ip}: queued ssot-gen LLM to generate IP-specific Q&A.\n"
            f"backend baseline missing keys: {', '.join(missing) if missing else '(none)'}\n"
            "Fixed question templates are bypassed; questions must be derived from the current SSOT/imported evidence."
        )
        _append_session_message(_canonical_session_string(ip), "user", text)
        _append_session_message(_canonical_session_string(ip), "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "grill-me")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf ssot-gen")
        _queue_prompt_for_session(client_session, _render_ssot_llm_qna_prompt(ip, str(state.get("kind") or "TBD"), state))
        bridge.emit("agent_state", running=True)
        return True

    def _handle_new_ip_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("new-ip", "ni"):
            return False
        ip, kind, import_paths, parse_err = _parse_new_ip_args(args)
        if parse_err:
            _emit_workflow_result(parse_err, "new-ip")
            return True
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT PLAN] missing or invalid IP name\n"
                "usage: /new-ip <ip_name> [kind]\n"
                "example: /new-ip demo_i2c APB4 I2C controller\n"
                "then: /import <ip_name> or /import @path",
                "new-ip",
            )
            return True

        # Approval gate allows scaffold/session creation and draft SSOT
        # accumulation only. Production SSOT canonicalization remains
        # blocked until explicit approval.
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            _emit_workflow_result(f"[SSOT PLAN] failed to scaffold {ip}: {e}", "new-ip")
            return True

        _set_active_ssot_ip(ip)
        state = _new_ssot_state(ip, kind)
        _ensure_new_ip_structure(ip)
        _ensure_ssot_draft(ip, kind)
        import_notes = []
        if import_paths:
            import_notes.append(
                "/new-ip is structure-only; import markers were not scanned. "
                "Run `/import " + ip + " " + " ".join(import_paths) + "` to populate SSOT TODOs."
            )
        _save_ssot_state(ip, state)
        session = _canonical_session_string(ip)
        plan = _render_new_ip_plan(ip, kind, state)
        if import_notes:
            plan += "\n\nImport:\n" + "\n".join(f"- {line}" for line in import_notes)
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", plan)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", plan)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + plan + "\n```")
        _emit_workflow_result(plan, "new-ip")
        _emit_ssot_approval_ready(ip, state)
        return True

    def _handle_ip_command(text: str, client_session: Any | None = None) -> bool:
        """`/ip <name>` — switch the active IP without spinning up a turn.

        Halts any running agent first (drains the inbox so queued
        workflow prompts don't auto-fire), repoints ATLAS_ACTIVE_IP
        plus the canonical session string, and emits commands_changed
        so the frontend refreshes /healthz and pivots the SSOT / QA /
        preview panels onto the new IP. No LLM call.
        """
        cmd, args = _split_slash(text)
        if cmd not in ("ip", "use"):  # `/use` retained as alias
            return False
        ip = (args or "").strip().split()[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[IP] missing or invalid IP name\n"
                "usage: /ip <ip_name>\n"
                "example: /ip gpio",
                "ip",
            )
            return True
        bridge.request_stop()
        bridge.emit("agent_state", running=False)
        _set_active_ssot_ip(ip)
        msg = (
            f"[IP] active IP -> {ip}\n"
            f"session: {_canonical_session_string(ip)}"
        )
        _emit_workflow_result(msg, "ip")
        bridge.emit("commands_changed")
        return True

    def _handle_session_command(text: str, client_session: Any | None = None) -> bool:
        """`/session <id>` — switch the active session_id (owner namespace).

        Halts the agent, sets ATLAS_ACTIVE_SESSION to the canonical
        triple `<id>/<active-ip>/<active-workflow>`, and emits a refresh
        signal. The frontend's /healthz poll picks up the new owner and
        re-pivots the workspace UI without a page reload.
        """
        cmd, args = _split_slash(text)
        if cmd not in ("session",):
            return False
        sid = (args or "").strip().split()[0] if args else ""
        if not sid or not _valid_ip_name(sid):
            _emit_workflow_result(
                "[SESSION] missing or invalid session id\n"
                "usage: /session <session_id>\n"
                "example: /session brian",
                "session",
            )
            return True
        bridge.request_stop()
        bridge.emit("agent_state", running=False)
        ip = _active_ssot_ip() or "default"
        wf = os.environ.get("ATLAS_DEFAULT_WORKFLOW") or "default"
        _atlas_active_session_cv.set(f"{sid}/{ip}/{wf}")
        _emit_workflow_result(
            f"[SESSION] active session -> {sid}/{ip}/{wf}",
            "session",
        )
        bridge.emit("commands_changed")
        return True

    def _handle_approval_command(text: str, client_session: Any | None = None) -> bool:
        raw = (text or "").strip()
        low = raw.lower()
        if not (low.startswith("approve") or raw.startswith("승인")):
            return False
        parts = raw.split()
        ip = parts[1] if len(parts) > 1 else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT APPROVAL] no pending IP found\n"
                "usage: approve [<ip_name>]  or  승인 [<ip_name>]",
                "approve",
            )
            return True
        _set_active_ssot_ip(ip)
        state = _load_ssot_state(ip)
        if not state:
            state = _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "TBD"))
        missing = _missing_ssot_decisions(ip, state)
        if missing:
            msg = (
                f"[SSOT APPROVAL] blocked: {ip} still has missing decisions\n"
                f"missing decisions: {', '.join(missing)}\n"
                "Use /import to seed existing evidence, then /grill-me to answer only the gaps."
            )
            _append_session_message(_canonical_session_string(ip), "user", text)
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "approve")
            _emit_ssot_approval_ready(ip, state, missing)
            return True
        state["approved"] = True
        state["approved_at"] = time.time()
        state["status"] = "approved"
        state["active_session"] = _active_session_value() or _canonical_session_string(ip)
        state["last_step"] = "approve"
        _save_ssot_state(ip, state)
        spec = _render_approved_ssot_spec(ip, state)
        msg = (
            f"[SSOT APPROVED] {ip}\n"
            f"YAML write is now allowed.\n"
            "Next: type /to-ssot in the Web UI when the summary looks correct."
        )
        session = _canonical_session_string(ip)
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", spec)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "approve")
        _emit_ssot_approval_ready(ip, state, [])
        return True

    def _handle_to_ssot_gate(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("to-ssot", "ssot", "ts"):
            return False
        ip = args.split(None, 1)[0] if args else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GATE] missing IP name\n"
                "usage: /to-ssot [<ip_name>]",
                "to-ssot",
            )
            return True
        _set_active_ssot_ip(ip)
        state = _load_ssot_state(ip)
        if state and not state.get("approved"):
            kind = str(state.get("kind") or "imported IP evidence")
            filled, conflicts, artifacts, errors = _import_defaults_if_available(ip, kind, state)
            state = _load_ssot_state(ip)
            if artifacts:
                note = (
                    f"[SSOT IMPORT] auto-imported {len(artifacts)} file(s) before /to-ssot {ip}\n"
                    f"filled decisions: {', '.join(filled) if filled else '(none)'}\n"
                    f"conflicts: {', '.join(str(c.get('key') or '') for c in conflicts[:8]) if conflicts else '(none)'}"
                )
                if errors:
                    note += "\nnotes:\n" + "\n".join(f"- {err}" for err in errors[:8])
                _append_session_message(_canonical_session_string(ip), "assistant", note)
                _append_workflow_history("ssot-gen", "assistant", note)
                _append_active_history("assistant", "```\n" + note + "\n```")
            if _auto_approve_if_complete(ip, state, reason="auto_approve_from_import_before_to_ssot"):
                state = _load_ssot_state(ip)
                note = f"[SSOT APPROVED] {ip}: auto-approved because imported evidence filled all required decisions."
                _append_session_message(_canonical_session_string(ip), "assistant", note)
                _append_workflow_history("ssot-gen", "assistant", note)
                _append_active_history("assistant", "```\n" + note + "\n```")
        if not state.get("approved"):
            missing = _missing_ssot_decisions(ip, state) if state else [k for k, _ in _SSOT_REQUIRED_DECISIONS]
            msg = (
                f"[SSOT GATE] blocked: {ip} is not approved yet\n"
                "YAML writes need either complete imported evidence or explicit approval.\n"
                f"missing decisions: {', '.join(missing) if missing else '(review not approved)'}\n\n"
                f"Put files under {ip}/doc/ or run /import @doc, then /to-ssot again. Use /grill-me only for the listed gaps."
            )
            _append_session_message(_canonical_session_string(ip), "user", text)
            _append_session_message(_canonical_session_string(ip), "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "to-ssot")
            if state:
                _emit_ssot_approval_ready(ip, state, missing)
            return True
        spec = _render_approved_ssot_spec(ip, state)
        _append_session_message(_canonical_session_string(ip), "user", text)
        _append_session_message(_canonical_session_string(ip), "assistant", spec)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_active_history("user", text)
        script_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "approved_to_ssot.py"
        validator_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        template_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "rules" / "ssot-template.yaml"
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"

        try:
            import subprocess

            draft = subprocess.run(
                [sys.executable, str(script_path), ip, "--root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            validate = subprocess.run(
                ["bash", str(validator_path), ip],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            draft = None
            validate = None
            bridge_msg = f"[to-ssot] generic bridge failed before validation: {exc}"
        else:
            bridge_parts = [
                f"[to-ssot] generic approved-state SSOT bridge for {ip}",
                f"script: {script_path}",
                f"ssot: {ssot_path}",
                f"bridge exit: {draft.returncode}",
            ]
            if draft.stdout.strip():
                bridge_parts += ["", "bridge stdout:", draft.stdout.strip()]
            if draft.stderr.strip():
                bridge_parts += ["", "bridge stderr:", draft.stderr.strip()]
            bridge_parts += ["", f"validator exit: {validate.returncode}"]
            if validate.stdout.strip():
                bridge_parts += ["", "validator stdout:", validate.stdout.strip()]
            if validate.stderr.strip():
                bridge_parts += ["", "validator stderr:", validate.stderr.strip()]
            bridge_msg = "\n".join(bridge_parts)

        _append_session_message(_canonical_session_string(ip), "assistant", bridge_msg)
        _append_workflow_history("ssot-gen", "assistant", bridge_msg)
        _append_active_history("assistant", "```\n" + bridge_msg + "\n```")
        _emit_workflow_result(bridge_msg, "to-ssot")

        if draft is not None and validate is not None and draft.returncode == 0 and validate.returncode == 0:
            return True

        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf ssot-gen")
        _queue_prompt_for_session(client_session, "/clear")
        _queue_prompt_for_session(client_session,
            f"/to-ssot {ip}\n\n"
            f"Hard workspace boundary for this run:\n"
            f"- Project root / IP artifacts: `{PROJECT_ROOT}`\n"
            f"- Common agent source root: `{SOURCE_ROOT}`\n"
            f"- SSOT path to edit: `{ssot_path}`\n"
            "Do not search or read outside those two roots. Ignore similarly named "
            "directories such as NEW_IP, NEW_CPU, brian_home, or other legacy projects.\n\n"
            "The generic approved-state bridge attempted to write the SSOT first. "
            "Its exact disk-truth result was:\n"
            "```text\n"
            f"{bridge_msg}\n"
            "```\n\n"
            "Approved Web SSOT Spec, copied inline so this fresh run does not depend "
            "on stale workflow chat history:\n"
            "```text\n"
            f"{spec}\n"
            "```\n\n"
            "Execute this as the approved SSOT write step. Do not call todo_write; "
            "it is Plan Mode only. Use the approved Web SSOT Spec above as source truth, "
            "replace scaffold-only placeholders, "
            "write the complete production canonical SSOT, and run the exact validator "
            f"`bash {validator_path} {ip}` before emitting [SSOT HANDOFF]. "
            f"The authoritative 33-section template is `{template_path}`. "
            "Do not use an inline/stale 20/25-section validator, and do not claim "
            "PASS unless that exact script exits 0.\n\n"
            "Bounded execution requirement: read the template, existing SSOT, and "
            "validator at most once each. After identifying missing/weak sections, "
            "your next tool action must be write_file, replace_in_file, or the "
            "validator run if the file is already complete. Do not reread the same "
            "files or draft the full YAML in prose before using the file tool."
        )
        bridge.emit("agent_state", running=True)
        return True

    def _handle_repair_ssot_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-ssot", "rs"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-ssot] missing or invalid IP name\nusage: /repair-ssot <ip_name>",
                "repair-ssot",
            )
            return True

        script = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        validator = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        session = _canonical_session_string(ip)
        _append_session_message(session, "user", text)
        _append_workflow_history("ssot-gen", "user", text)
        _append_active_history("user", text)
        bridge.emit("agent_state", running=True)

        if not ssot_path.is_file():
            msg = (
                f"[repair-ssot] blocked: SSOT not found at {ssot_path}\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first."
            )
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        try:
            import subprocess

            repair = subprocess.run(
                [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
            validate = subprocess.run(
                ["bash", str(validator), ip],
                cwd=str(PROJECT_ROOT),
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            msg = f"[repair-ssot] failed: {exc}"
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        parts = [
            f"[repair-ssot] {ip}",
            f"source: {ssot_path}",
            f"repair exit: {repair.returncode}",
        ]
        if repair.stdout.strip():
            parts += ["", "repair stdout:", repair.stdout.strip()]
        if repair.stderr.strip():
            parts += ["", "repair stderr:", repair.stderr.strip()]
        parts += ["", f"validator exit: {validate.returncode}"]
        if validate.stdout.strip():
            parts += ["", "validator stdout:", validate.stdout.strip()]
        if validate.stderr.strip():
            parts += ["", "validator stderr:", validate.stderr.strip()]
        msg = "\n".join(parts)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-ssot")
        return True

    def _handle_repair_rtl_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-rtl", "rrtl"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-rtl] missing or invalid IP name\nusage: /repair-rtl <ip_name>",
                "repair-rtl",
            )
            return True
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[repair-rtl] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first.",
                "repair-rtl",
            )
            return True
        session = f"{ip}/rtl-gen"
        compile_report = PROJECT_ROOT / ip / "rtl" / "rtl_compile.json"
        lint_report = PROJECT_ROOT / ip / "lint" / "dut_lint.json"
        py_cmd = _python_cmd()
        queued = (
            f"[repair-rtl] queued through rtl-gen\n"
            f"module: {ip}\n"
            f"ssot: {ip}/yaml/{ip}.ssot.yaml\n"
            f"compile report: {ip}/rtl/rtl_compile.json\n"
            f"lint report: {ip}/lint/dut_lint.json"
        )
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, "/wf rtl-gen")
        _queue_prompt_for_session(client_session, "/clear")
        _queue_prompt_for_session(client_session, f"/todo template ssot-rtl {ip}")
        _queue_prompt_for_session(client_session,
            f"Repair RTL for {ip} using only SSOT-driven rtl-gen ownership.\n\n"
            f"Read these evidence files first:\n"
            f"- SSOT: `{ssot_path}`\n"
            f"- compile report: `{compile_report}`\n"
            f"- compile log: `{PROJECT_ROOT / ip / 'rtl' / 'rtl_compile.log'}`\n"
            f"- lint report: `{lint_report}`\n"
            f"- filelist: `{PROJECT_ROOT / ip / 'list' / f'{ip}.f'}`\n\n"
            "Repair only files under `<ip>/rtl/` and `<ip>/list/` unless the evidence "
            "proves the SSOT manifest itself is wrong. If SSOT/filelist/top-module "
            "naming is inconsistent, emit `[SSOT QUESTION] -> ssot-gen` with the exact "
            "YAML fields to repair instead of silently changing the YAML. Do not edit TB, "
            "sim, cov, or unrelated IPs.\n\n"
            "Current required repair classes:\n"
            "- Eliminate all `rtl_compile.json.style_violation_details`; especially no "
            "parameterized part-selects inside `always`, `always_comb`, `always_ff`, or "
            "`always_latch`. Use helper wires and continuous assigns.\n"
            "- Eliminate all Icarus `sorry:` diagnostics and any compile warnings/errors.\n"
            "- Preserve DUT-only lint pass with zero suppressions; on Windows use Icarus "
            "Verilog (`iverilog`) rather than Verilator.\n"
            "- Reconcile filelist and top wrapper naming with SSOT, or escalate to ssot-gen "
            "if the SSOT source of truth must change.\n\n"
            "After the final RTL edit, run exactly:\n"
            f"`{py_cmd} {SOURCE_ROOT / 'workflow' / 'rtl-gen' / 'scripts' / 'rtl_compile_report.py'} {ip} --top {ip}`\n"
            f"`{py_cmd} {SOURCE_ROOT / 'workflow' / 'lint' / 'scripts' / 'dut_lint_report.py'} {ip} --top {ip}`\n\n"
            "DONE requires compile pass E0/D0/S0, lint pass E0/W0/S0, and no hidden "
            "waivers/suppressions. If any part cannot be fixed from RTL alone, stop with "
            "a precise `[SSOT QUESTION]` or `[RTL BLOCKED]` rather than claiming DONE."
        )
        bridge.emit("agent_state", running=True)
        _emit_workflow_result(queued, "repair-rtl")
        bridge.emit("agent_state", running=True)
        return True

    def _handle_repair_equiv_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-equiv", "repair-equivalence", "reqv"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-equiv] missing or invalid IP name\nusage: /repair-equiv <ip_name>",
                "repair-equiv",
            )
            return True
        classify_path = PROJECT_ROOT / ip / "sim" / "mismatch_classification.json"
        if not classify_path.is_file():
            _emit_workflow_result(
                f"[repair-equiv] blocked: missing {ip}/sim/mismatch_classification.json\n"
                f"Run /sim-debug {ip} first.",
                "repair-equiv",
            )
            return True
        try:
            classify_doc = json.loads(classify_path.read_text(encoding="utf-8"))
            if not isinstance(classify_doc, dict):
                classify_doc = {}
        except Exception as exc:
            _emit_workflow_result(
                f"[repair-equiv] blocked: cannot parse {ip}/sim/mismatch_classification.json: {exc}",
                "repair-equiv",
            )
            return True
        classifications = classify_doc.get("classifications")
        if not isinstance(classifications, list):
            classifications = []

        loopable = [
            item for item in classifications
            if isinstance(item, dict)
            and item.get("llm_loop_allowed") is True
            and str(item.get("owner") or "").strip()
            and str(item.get("repair_prompt") or "").strip()
        ]
        human_only = [
            item for item in classifications
            if isinstance(item, dict) and item.get("llm_loop_allowed") is False
        ]
        if not loopable:
            lines = [
                "[repair-equiv] no loopable classifications found",
                f"module: {ip}",
                f"classification status: {classify_doc.get('status') or 'unknown'}",
                f"human-gated: {len(human_only)}",
                f"source: {ip}/sim/mismatch_classification.json",
            ]
            if human_only:
                lines.append("next: answer ATLAS human-gate questions from /sim-debug before repair")
            else:
                lines.append("next: rerun /sim-debug after a failing sim to create repair classifications")
            _emit_workflow_result("\n".join(lines), "repair-equiv")
            return True

        route = {
            "rtl-gen": ("rtl-gen", "ssot-rtl"),
            "rtl": ("rtl-gen", "ssot-rtl"),
            "fl-model-gen": ("fl-model-gen", "ssot-fl-model"),
            "fl_model": ("fl-model-gen", "ssot-fl-model"),
            "tb-gen": ("tb-gen", "ssot-tb-cocotb"),
            "tb": ("tb-gen", "ssot-tb-cocotb"),
            "coverage": ("coverage", "coverage_iter"),
            "sim_debug": ("sim_debug", "sim-debug"),
            "sim-debug": ("sim_debug", "sim-debug"),
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        unrouted: list[dict[str, Any]] = []
        for item in loopable:
            owner = str(item.get("owner") or "").strip()
            key = route.get(owner)
            if key is None:
                unrouted.append(item)
                continue
            grouped.setdefault(key, []).append(item)

        session = f"{ip}/sim_debug"
        _append_session_message(session, "user", text)
        _append_active_history("user", text)
        queued_lines = [
            "[repair-equiv] queued loopable equivalence repairs",
            f"module: {ip}",
            f"source: {ip}/sim/mismatch_classification.json",
            f"loopable: {len(loopable)}",
            f"human-gated: {len(human_only)}",
        ]
        for (workflow, template), items in grouped.items():
            queued_lines.append(f"- {workflow}: {len(items)} classification(s)")
            _queue_prompt_for_session(client_session, "/mode normal")
            _queue_prompt_for_session(client_session, f"/wf {workflow}")
            _queue_prompt_for_session(client_session, "/clear")
            _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
            payload = json.dumps(items, indent=2, ensure_ascii=False)[:12000]
            _queue_prompt_for_session(client_session,
                f"Execute classified FL-vs-RTL repair for {ip}.\n\n"
                "Hard rules:\n"
                "- Use SSOT YAML, FunctionalModel, equivalence_goals.json, scoreboard_events.jsonl, "
                "fl_rtl_compare.json, and mismatch_classification.json as evidence.\n"
                "- Repair only this workflow owner's artifacts. Do not change SSOT semantics unless "
                "the classification explicitly routes to ssot-gen and a human answer exists.\n"
                "- Do not copy wrong RTL observed behavior into expected values.\n"
                "- After repair, rerun the smallest owning validator, then tell the user to rerun "
                f"/sim {ip}, /sim-debug {ip}, and /goal-audit {ip}.\n\n"
                f"Classifications for this owner:\n```json\n{payload}\n```"
            )
        if unrouted:
            queued_lines.append(f"unrouted owners: {', '.join(str(i.get('owner')) for i in unrouted[:8] if isinstance(i, dict))}")
        if human_only:
            queued_lines.append("human gate remains required for non-loopable classifications")
        msg = "\n".join(queued_lines)
        _append_session_message(session, "assistant", "```\n" + msg + "\n```")
        _append_workflow_history("sim_debug", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-equiv")
        bridge.emit("agent_state", running=True)
        return True

    def _run_stage_command(text: str, client_session: Any | None = None) -> bool:
        cmd, args = _split_slash(text)
        alias = {
            "sr": "ssot-rtl",
            "sfm": "ssot-fl-model",
            "seg": "ssot-equiv-goals",
            "equiv-goals": "ssot-equiv-goals",
            "tb": "ssot-tb-cocotb",
            "stb": "ssot-tb",
            "stb-cocotb": "ssot-tb-cocotb",
            "stb-uvm": "ssot-tb-uvm",
            "stb-verilog": "ssot-tb-verilog",
            "ssot-tb-sv": "ssot-tb-verilog",
            "stb-sv": "ssot-tb-verilog",
            "s": "sim",
            "sd": "sim-debug",
            "cov": "coverage",
            "l": "lint",
            "audit": "goal-audit",
            "ga": "goal-audit",
        }.get(cmd, cmd)
        spec = _STAGE_RUNNERS.get(alias)
        if not spec:
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                f"[{alias}] missing or invalid IP name\nusage: /{alias} <ip_name>",
                alias,
            )
            return True
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[{alias}] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first.",
                alias,
            )
            return True
        if alias == "signoff":
            session = f"{ip}/signoff"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)

            async def _emit_signoff_snapshot() -> None:
                try:
                    resp = await api_progress(scope=ip)
                    data = json.loads(resp.body.decode("utf-8"))
                    selected = data.get("selected") if isinstance(data, dict) else {}
                    signoff = selected.get("signoff") if isinstance(selected, dict) else {}
                    status = signoff.get("status") if isinstance(signoff, dict) else {}
                    blockers = signoff.get("blockers") if isinstance(signoff, dict) else []
                    progress = selected.get("progress") if isinstance(selected, dict) else {}
                    equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                    goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                    lines = [
                        "[signoff] strict SSOT progress gate",
                        f"module: {ip}",
                        f"status: {status.get('signoff', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"equivalence: {status.get('equivalence_goals', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"goal_audit: {status.get('goal_audit', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"coverage: {status.get('coverage', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"evidence: /api/progress?scope={ip}",
                    ]
                    if isinstance(equivalence, dict):
                        lines.append(
                            "equivalence_counts: "
                            f"{equivalence.get('passed', 0)}/{equivalence.get('total', 0)} pass, "
                            f"failed={equivalence.get('failed', 0)}, "
                            f"blocked={equivalence.get('blocked', 0)}, "
                            f"untested={equivalence.get('untested', 0)}"
                        )
                    if isinstance(goal_audit, dict):
                        lines.append(
                            "goal_audit_checks: "
                            f"{goal_audit.get('passed_checks', 0)}/{goal_audit.get('total_checks', 0)} pass, "
                            f"failed={goal_audit.get('failed_checks', 0)}"
                        )
                    if blockers:
                        lines.append("")
                        lines.append("blockers:")
                        for blocker in blockers[:12]:
                            lines.append(f"- {blocker}")
                    msg = "\n".join(lines)
                except Exception as exc:
                    msg = f"[signoff] failed to read ATLAS progress gate for {ip}: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim_debug", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)

            asyncio.create_task(_emit_signoff_snapshot())
            return True

        try:
            from src.workflow_stage_surface import is_common_stage, run_common_stage_surface
        except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
            from workflow_stage_surface import is_common_stage, run_common_stage_surface

        if is_common_stage(alias):
            template = str(spec.get("template") or alias)
            surface = run_common_stage_surface(
                project_root=PROJECT_ROOT,
                source_root=SOURCE_ROOT,
                alias=alias,
                ip=ip,
                template=template,
            )
            if not surface.handled:
                return False
            session = surface.session
            workflow = surface.workflow
            msg = surface.message
            engine_alias = surface.alias
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history(workflow, "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, engine_alias)

            if surface.rtl_blocked:
                _start_rtl_blocker_qna(ip, reason="automatic /ssot-rtl preflight", interactive=False, client_session=client_session)
                return True
            for prompt in surface.queue_prompts:
                _queue_prompt_for_session(client_session, prompt)
            if surface.queue_prompts:
                bridge.emit("agent_state", running=True)
                return True
            if surface.sim_human_gate_doc is not None:
                opened_human_gate = _start_sim_human_gate_qna(
                    ip,
                    surface.sim_human_gate_doc,
                    reason="automatic /sim-debug",
                    client_session=client_session,
                )
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history(workflow, "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    bridge.emit("tool_result", text="```\n" + note + "\n```", tool=engine_alias, truncated=False)
                    bridge.emit("slash_output", text="```\n" + note + "\n```")
                    bridge.emit("flush")
                    return True
            bridge.emit("agent_state", running=False)
            return True
        if alias == "sim":
            session = f"{ip}/sim"
            script = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "sim.sh"
            validator = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
            coverage_script = SOURCE_ROOT / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"
            runner_candidates = [
                PROJECT_ROOT / ip / "tb" / "cocotb" / "test_runner.py",
                PROJECT_ROOT / ip / "tb" / "cocotb" / "run_tests.py",
                PROJECT_ROOT / ip / "tb" / "test_runner.py",
                PROJECT_ROOT / ip / "tb" / "run_tests.py",
                PROJECT_ROOT / ip / "sim" / f"test_{ip}.py",
            ]
            runner = next((p for p in runner_candidates if p.is_file()), None)
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            if runner is None:
                msg = (
                    f"[sim] blocked: no executable TB runner found for {ip}\n"
                    "expected one of:\n"
                    f"- {ip}/tb/cocotb/test_runner.py\n"
                    f"- {ip}/tb/cocotb/run_tests.py\n"
                    f"- {ip}/tb/test_runner.py\n"
                    f"- {ip}/tb/run_tests.py\n"
                    "Run /tb <ip> first."
                )
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True
            try:
                import subprocess

                sim_run = subprocess.run(
                    ["bash", str(script), runner.relative_to(PROJECT_ROOT).as_posix()],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=180,
                )
                validate_run = subprocess.run(
                    ["bash", str(validator), ip],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=180,
                )
                coverage_run = subprocess.CompletedProcess(
                    args=[sys.executable, str(coverage_script), str(PROJECT_ROOT / ip)],
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                if sim_run.returncode == 0 and validate_run.returncode == 0:
                    coverage_run = subprocess.run(
                        [sys.executable, str(coverage_script), str(PROJECT_ROOT / ip)],
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=90,
                    )
            except Exception as exc:
                msg = f"[sim] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True

            status_word = "PASS" if sim_run.returncode == 0 and validate_run.returncode == 0 and coverage_run.returncode == 0 else "FAIL"
            parts = [
                f"[sim] {status_word}",
                f"script: {script}",
                f"validator: {validator}",
                f"coverage: {coverage_script}",
                f"module: {ip}",
                f"runner: {runner.relative_to(PROJECT_ROOT)}",
                f"sim exit: {sim_run.returncode}",
            ]
            if sim_run.stdout.strip():
                parts += ["", "sim stdout:", sim_run.stdout.strip()]
            if sim_run.stderr.strip():
                parts += ["", "sim stderr:", sim_run.stderr.strip()]
            parts += ["", f"validator exit: {validate_run.returncode}"]
            if validate_run.stdout.strip():
                parts += ["", "validator stdout:", validate_run.stdout.strip()]
            if validate_run.stderr.strip():
                parts += ["", "validator stderr:", validate_run.stderr.strip()]
            parts += ["", f"coverage exit: {coverage_run.returncode}"]
            if coverage_run.stdout.strip():
                parts += ["", "coverage stdout:", coverage_run.stdout.strip()]
            if coverage_run.stderr.strip():
                parts += ["", "coverage stderr:", coverage_run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/results.xml or {ip}/tb/cocotb/results.xml",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/cov/coverage.json",
                f"- {ip}/sim/sim_report.txt",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            return True
        if alias == "ssot-rtl":
            session = f"{ip}/rtl-gen"
            script = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
            top = ip
            try:
                import yaml as _yaml  # type: ignore
                ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace")) or {}
                top_doc = ssot_doc.get("top_module") if isinstance(ssot_doc, dict) else {}
                if isinstance(top_doc, dict) and top_doc.get("name"):
                    top = str(top_doc.get("name"))
                elif isinstance(top_doc, str) and top_doc.strip():
                    top = top_doc.strip()
            except Exception:
                top = ip

            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _clip(s: str, limit: int = 12000) -> str:
                if len(s) <= limit:
                    return s
                return s[:limit] + f"\n... <truncated {len(s) - limit} chars>"

            def _run_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": _clip((proc.stdout or "").strip()),
                        "stderr": _clip((proc.stderr or "").strip()),
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tool("rtl_generate", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)])
            compile_rc: int | None = None
            lint_rc: int | None = None
            if gen_rc == 0:
                compile_script = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "rtl_compile_report.py"
                lint_script = SOURCE_ROOT / "workflow" / "lint" / "scripts" / "dut_lint_report.py"
                compile_rc = _run_tool(
                    "dut_compile",
                    [
                        sys.executable,
                        str(compile_script),
                        ip,
                        "--top",
                        top,
                        "--project-root",
                        str(PROJECT_ROOT),
                    ],
                )
                lint_rc = _run_tool("dut_lint", [sys.executable, str(lint_script), ip, "--top", top])

            blocked_path = PROJECT_ROOT / ip / "rtl" / "rtl_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    blocked_doc = {"reason": f"rtl_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc:
                headline = "[SSOT QUESTION] rtl-gen BLOCKED"
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                headline = "[RTL RESULT] PASS - generated RTL and DUT-only compile/lint evidence"
            elif gen_rc == 0:
                headline = "[RTL RESULT] FAIL - generated RTL needs rtl-gen repair"
            else:
                headline = "[RTL BLOCKED] rtl-gen failed before producing approved evidence"

            parts = [
                headline,
                f"module: {ip}",
                f"top: {top}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT decision required'}",
                    f"evidence: {ip}/rtl/rtl_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'answer SSOT questions and rerun /ssot-rtl'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts.append("")
            parts.append("runs:")
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['command']}")
                if run.get("stdout"):
                    parts.append("  stdout:")
                    parts.append(str(run["stdout"]))
                if run.get("stderr"):
                    parts.append("  stderr:")
                    parts.append(str(run["stderr"]))
            parts += [
                "",
                "artifacts:",
                f"- {ip}/yaml/{ip}.ssot.yaml",
                f"- {ip}/list/{ip}.f",
                f"- {ip}/rtl/rtl_compile.json",
                f"- {ip}/lint/dut_lint.json",
                f"- {ip}/rtl/rtl_blocked.json (only when SSOT decision is required)",
            ]
            if blocked_doc:
                parts.append("")
                parts.append("next: ATLAS opened an SSOT decision Q&A card for the RTL blocker.")
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                parts += [
                    "",
                    "next: run /tb, /sim, /sim-debug, and /goal-audit to prove FL-vs-RTL behavior.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued rtl-gen repair with compile/lint diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("rtl-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            if blocked_doc:
                _start_rtl_blocker_qna(ip, reason="automatic /ssot-rtl preflight", interactive=False, client_session=client_session)
            elif gen_rc == 0 and (compile_rc != 0 or lint_rc != 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or alias)
                _queue_prompt_for_session(client_session, "/mode normal")
                _queue_prompt_for_session(client_session, f"/wf {workflow}")
                _queue_prompt_for_session(client_session, "/clear")
                _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
                _queue_prompt_for_session(client_session,
                    f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
                    "The SSOT-driven RTL generator produced artifacts but compile/lint did not approve them. "
                    "Repair only the generated RTL against function_model, cycle_model, interfaces, "
                    "error_handling, and test_requirements. Then run the canonical DUT-only compile and "
                    "lint commands, repair diagnostics, and report exact artifact evidence. If new behavior "
                    "is still ambiguous, emit a precise "
                    "[SSOT QUESTION] and stop."
                )
            bridge.emit("agent_state", running=False)
            return True
        if alias == "ssot-equiv-goals":
            session = f"{ip}/fl-model-gen"
            fl_script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _run_local(label: str, cmdline: list[str], timeout_s: int = 60) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        cmdline,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            fl_rc = _run_local("emit_fl_model", [sys.executable, str(fl_script), ip, "--root", str(PROJECT_ROOT)])
            eq_rc = _run_local("emit_equivalence_goals", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)]) if fl_rc == 0 else 999
            goals_path = PROJECT_ROOT / ip / "verify" / "equivalence_goals.json"
            goal_summary = ""
            if goals_path.is_file():
                try:
                    gdoc = json.loads(goals_path.read_text(encoding="utf-8"))
                    summary = gdoc.get("summary") if isinstance(gdoc, dict) else {}
                    if isinstance(summary, dict):
                        goal_summary = (
                            f"total={summary.get('total', 0)} "
                            f"required={summary.get('required', 0)} "
                            f"blocked={summary.get('blocked', 0)}"
                        )
                except Exception:
                    goal_summary = "unparseable equivalence_goals.json"
            headline = (
                "[ssot-equiv-goals] PASS"
                if eq_rc == 0 else
                "[ssot-equiv-goals] BLOCKED"
            )
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"goals: {goal_summary or '(not generated)'}",
                "",
                "runs:",
            ]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/verify/equivalence_goals.json",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            if eq_rc != 0:
                parts.append("")
                parts.append("next: inspect blocked goals and answer/repair SSOT behavior before TB signoff")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        if alias in {"ssot-tb", "ssot-tb-cocotb"}:
            canonical_alias = "ssot-tb-cocotb"
            session = f"{ip}/tb-gen"
            script = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
            validator = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
            scoreboard = SOURCE_ROOT / "workflow" / "tb-gen" / "runtime" / "equivalence_scoreboard.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _run_tb_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tb_tool("emit_goal_scoreboard_cocotb", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)])
            structure_rc: int | None = None
            self_check_rc: int | None = None
            if gen_rc == 0:
                structure_rc = _run_tb_tool("check_pyuvm_structure", ["bash", str(validator), ip])
                self_check_rc = _run_tb_tool(
                    "equivalence_scoreboard_self_check",
                    [sys.executable, str(scoreboard), ip, "--root", str(PROJECT_ROOT), "--self-check"],
                )

            blocked_path = PROJECT_ROOT / ip / "tb" / "cocotb" / "tb_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    loaded = json.loads(blocked_path.read_text(encoding="utf-8"))
                    blocked_doc = loaded if isinstance(loaded, dict) else {}
                except Exception as exc:
                    blocked_doc = {"reason": f"tb_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc or gen_rc == 2:
                headline = "[ssot-tb-cocotb] BLOCKED - SSOT/RTL contract needs repair"
            elif gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                headline = "[ssot-tb-cocotb] PASS - generated goal-driven pyuvm/cocotb scoreboard"
            elif gen_rc == 0:
                headline = "[ssot-tb-cocotb] FAIL - generated TB needs tb-gen repair"
            else:
                headline = "[ssot-tb-cocotb] FAIL - generator did not produce approved TB artifacts"

            parts = [
                headline,
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
                f"validator: {validator}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT/RTL decision required'}",
                    f"evidence: {ip}/tb/cocotb/tb_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'repair SSOT/RTL contract and rerun /tb'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts += ["", "runs:"]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/tb/cocotb/test_{ip}.py",
                f"- {ip}/tb/cocotb/test_runner.py",
                f"- {ip}/tb/cocotb/tb_manifest.json",
                f"- {ip}/tb/cocotb/tb_generation.json",
                f"- {ip}/sim/scoreboard_events.jsonl after /sim",
                f"- {ip}/cov/coverage.json after /sim",
            ]
            if gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                parts += [
                    "",
                    "next: run /sim, /sim-debug, and /goal-audit to collect FL-vs-RTL evidence.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued tb-gen repair with structure/self-check diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("tb-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, canonical_alias)
            if gen_rc == 0 and not (structure_rc == 0 and self_check_rc == 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or canonical_alias)
                _queue_prompt_for_session(client_session, "/mode normal")
                _queue_prompt_for_session(client_session, f"/wf {workflow}")
                _queue_prompt_for_session(client_session, "/clear")
                _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
                _queue_prompt_for_session(client_session,
                    f"Repair generated pyuvm/cocotb TB for {ip} using SSOT, FunctionalModel, "
                    "equivalence_goals.json, rtl_contract.json, and the validator output below. "
                    "Do not use fixed IP templates. Keep the TB goal-driven, instantiate "
                    "EquivalenceScoreboard, preserve all required scoreboard row fields, and rerun "
                    f"`bash {validator} {ip}` plus the scoreboard self-check before reporting DONE.\n\n"
                    "ATLAS direct-generation evidence:\n```text\n"
                    f"{msg}\n"
                    "```"
                )
                bridge.emit("agent_state", running=True)
            else:
                bridge.emit("agent_state", running=False)
            return True
        if alias == "sim-debug":
            session = f"{ip}/sim_debug"
            script = SOURCE_ROOT / "workflow" / "sim_debug" / "scripts" / "compare_fl_rtl_results.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[sim-debug] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            compare_path = PROJECT_ROOT / ip / "sim" / "fl_rtl_compare.json"
            classify_path = PROJECT_ROOT / ip / "sim" / "mismatch_classification.json"
            summary_line = ""
            if compare_path.is_file():
                try:
                    cdoc = json.loads(compare_path.read_text(encoding="utf-8"))
                    summary = cdoc.get("summary") if isinstance(cdoc, dict) else {}
                    if isinstance(summary, dict):
                        summary_line = (
                            f"status={cdoc.get('status')} total={summary.get('total', 0)} "
                            f"checked={summary.get('goals_checked', 0)} passed={summary.get('goals_passed', 0)} "
                            f"failed={summary.get('goals_failed', 0)} blocked={summary.get('goals_blocked', 0)} "
                            f"untested={summary.get('goals_untested', 0)}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_compare.json"
            parts = [
                "[sim-debug] FL-vs-RTL compare",
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/fl_rtl_compare.json",
                f"- {ip}/sim/mismatch_classification.json",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/verify/equivalence_goals.json",
            ]
            if run.returncode != 0 and classify_path.is_file():
                parts.append("")
                parts.append("next: repair classified owner or answer human-gate questions from mismatch_classification.json")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            opened_human_gate = False
            if classify_path.is_file():
                try:
                    loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                    classify_doc = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    classify_doc = {}
                opened_human_gate = _start_sim_human_gate_qna(ip, classify_doc, reason="automatic /sim-debug", client_session=client_session)
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history("sim_debug", "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    bridge.emit("tool_result", text="```\n" + note + "\n```", tool=alias, truncated=False)
                    bridge.emit("slash_output", text="```\n" + note + "\n```")
                    bridge.emit("flush")
            if not opened_human_gate:
                bridge.emit("agent_state", running=False)
            return True
        if alias == "goal-audit":
            session = f"{ip}/goal-audit"
            script = SOURCE_ROOT / "workflow" / "sim_debug" / "scripts" / "audit_fl_rtl_equivalence_goal.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[goal-audit] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            audit_path = PROJECT_ROOT / ip / "sim" / "fl_rtl_goal_audit.json"
            summary_line = ""
            blockers: list[str] = []
            if audit_path.is_file():
                try:
                    audit_doc = json.loads(audit_path.read_text(encoding="utf-8"))
                    summary = audit_doc.get("summary") if isinstance(audit_doc, dict) else {}
                    if isinstance(summary, dict):
                        blockers = [str(x) for x in summary.get("blockers") or []]
                        summary_line = (
                            f"status={audit_doc.get('status')} "
                            f"passed={summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)} "
                            f"blockers={', '.join(blockers) if blockers else 'none'}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_goal_audit.json"
            headline = "[goal-audit] PASS" if run.returncode == 0 else "[goal-audit] FAIL"
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifact:",
                f"- {ip}/sim/fl_rtl_goal_audit.json",
            ]
            if blockers:
                parts += ["", "blockers:"]
                parts += [f"- {blocker}" for blocker in blockers[:12]]
            if run.returncode != 0:
                parts += [
                    "",
                    "next: inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage; do not bypass with a fixed IP template.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        if alias == "ssot-fl-model":
            session = f"{ip}/fl-model-gen"
            script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[ssot-fl-model] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            parts = [
                "[ssot-fl-model] generic SSOT-driven FL model stage",
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"exit: {run.returncode}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/model/fl_model_check.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        workflow = str(spec["workflow"])
        template = str(spec.get("template") or alias)
        session = f"{ip}/{workflow}"
        _append_session_message(session, "user", text)
        queued = (
            f"[{alias}] queued through workflow agent\n"
            f"workflow: {workflow}\n"
            f"template: {template}\n"
            f"module: {ip}\n"
            f"source: {ip}/yaml/{ip}.ssot.yaml\n"
            f"expected artifacts: {ip}/{spec['artifact_hint']}"
        )
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        _queue_prompt_for_session(client_session, "/mode normal")
        _queue_prompt_for_session(client_session, f"/wf {workflow}")
        # Per-IP stage runs must not inherit stale workflow-level chat/todo
        # context from a previous IP. The concrete SSOT path and rerun prompt
        # below re-establish the only context the worker should use.
        _queue_prompt_for_session(client_session, "/clear")
        _queue_prompt_for_session(client_session, f"/todo template {template} {ip}")
        _queue_prompt_for_session(client_session,
            f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
            "Use the workflow todo detail/criteria. Do not use fixed IP templates; "
            "derive implementation from SSOT and verify with real commands. "
            "After reading the SSOT, keep the ledger bounded and move to "
            "write_file/replace_in_file/run_command; do not loop on architecture "
            "debate before producing artifacts. Do not publish the ledger as a long "
            "chat answer; if work remains, the next response must start with an "
            "Action line. Use small action chunks: one file or one validation command "
            "per response, prefer dependency/leaf files before the top wrapper, and "
            "split any file that would exceed about 180 lines into replace_in_file "
            "or replace_lines follow-up actions."
        )
        bridge.emit("agent_state", running=True)
        _emit_workflow_result(queued, alias)
        bridge.emit("agent_state", running=True)
        return True

    @app.get("/api/catalog/models")
    async def api_catalog_models():
        """Return available IP models/templates discoverable in the project.

        Catalog models are reusable sources that can be instantiated.
        /api/soc remains the actual placed instance hierarchy.
        """
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"models": [], "count": 0,
                                 "error": "PyYAML not installed"})
        models = []
        seen = set()
        def _catalog_kind(name: str) -> str:
            n = (name or "").lower()
            if any(x in n for x in ["cpu", "core", "cortex", "riscv"]): return "cpu"
            if any(x in n for x in ["noc", "axi", "crossbar", "interconnect", "cci"]): return "bus"
            if any(x in n for x in ["ddr", "sram", "mem", "dram"]): return "mem"
            if any(x in n for x in ["pll", "adc", "dac", "phy"]): return "analog"
            return "periph"
        for p in sorted(PROJECT_ROOT.glob("*/yaml/*.ssot.yaml")):
            try:
                doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            except Exception:
                doc = {}
            if not isinstance(doc, dict):
                doc = {}
            ip_dir = p.parents[1]
            top = doc.get("top_module")
            name = top if isinstance(top, str) and top.strip() else ip_dir.name
            if name in seen:
                continue
            seen.add(name)
            ports = []
            for bi in (doc.get("busInterfaces") or []):
                if isinstance(bi, dict):
                    ports.append({
                        "name": bi.get("name"),
                        "proto": bi.get("proto"),
                        "role": bi.get("role"),
                        "side": bi.get("side"),
                    })
            models.append({
                "name": name,
                "id": ip_dir.name,
                "kind": _catalog_kind(name),
                "source": "project",
                "ssot_path": p.relative_to(PROJECT_ROOT).as_posix(),
                "ports": ports,
            })
        return JSONResponse({"models": models, "count": len(models)})

    @app.get("/api/workspace/tree")
    async def api_workspace_tree(depth: int = 2):
        """Return the real project directory hierarchy for Architect.

        This is separate from /api/catalog/models: catalog is reusable IP
        models; workspace tree is the on-disk project shape.
        """
        max_depth = max(1, min(int(depth or 2), 4))
        skip = {
            ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", "node_modules", ".venv", "venv", "vendor",
            ".session", ".rag", ".claude", ".omc", ".benchmark",
            ".benchmarks", ".common_ai_agent", ".session_debug",
        }
        ip_artifacts = {"yaml", "rtl", "tb", "sim", "lint", "syn", "sta", "sta-post", "pnr", "dft", "doc", "req", "list"}

        def _meta(p: Path) -> dict:
            child_names = set()
            try:
                child_names = {c.name for c in p.iterdir() if c.is_dir()}
            except OSError:
                pass
            ssot_count = 0
            try:
                ssot_count = len(list((p / "yaml").glob("*.ssot.yaml"))) if (p / "yaml").is_dir() else 0
            except OSError:
                ssot_count = 0
            artifacts = sorted(child_names & ip_artifacts)
            return {
                "is_ip": ssot_count > 0,
                "ssot_count": ssot_count,
                "artifacts": artifacts,
            }

        def _node(p: Path, level: int) -> dict | None:
            name = p.name or str(p)
            if name in skip or name.startswith("."):
                return None
            node = {
                "name": name,
                "path": p.relative_to(PROJECT_ROOT).as_posix(),
                "kind": "dir",
                **_meta(p),
                "children": [],
            }
            if level >= max_depth:
                return node
            try:
                dirs = sorted([c for c in p.iterdir() if c.is_dir()],
                              key=lambda c: (not ((c / "yaml").is_dir()), c.name.lower()))
            except OSError:
                dirs = []
            for child in dirs:
                child_node = _node(child, level + 1)
                if child_node is not None:
                    node["children"].append(child_node)
            return node

        root = {
            "name": PROJECT_ROOT.name,
            "path": ".",
            "kind": "root",
            "children": [],
        }
        try:
            top_dirs = sorted([p for p in PROJECT_ROOT.iterdir() if p.is_dir()],
                              key=lambda p: (not ((p / "yaml").is_dir()), p.name.lower()))
        except OSError:
            top_dirs = []
        for p in top_dirs:
            n = _node(p, 1)
            if n is not None:
                root["children"].append(n)
        return JSONResponse({"root": root, "count": len(root["children"]),
                             "project_root": str(PROJECT_ROOT)})

    @app.post("/api/soc/layout")
    async def api_soc_layout(request: Request):
        """Persist user-dragged block positions back into soc.ssot.yaml.

        Body (JSON): `{"layout": {"<cluster>/<inst>": {"x": <num>, "y": <num>}, …}}`

        For each entry, find the matching `instances[].id` (`<cluster>/<inst>`
        is split on `/`; we use just the inst id since SoC SSOT instance
        ids are unique) and set its `x:` / `y:` keys. Other fields are
        left untouched. The file is rewritten in-place with
        `yaml.safe_dump`. Empty layout `{}` clears all x/y from every
        instance (paired with the frontend's [reset] button).

        Architect screen reads these on the next /api/soc fetch and
        uses them as the default block position (overriding the
        auto-grid). LocalStorage layout still wins as the most-local
        cache, so a user can preview drag-arounds before committing.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        layout = body.get("layout") if isinstance(body, dict) else None
        if not isinstance(layout, dict):
            return JSONResponse({"error": "missing 'layout' object"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)

        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                 status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"parse: {e}"}, status_code=500)
        if not isinstance(doc, dict): doc = {}
        instances = doc.get("instances")
        if not isinstance(instances, list):
            return JSONResponse({"error": "soc.ssot.yaml has no instances[]"},
                                 status_code=400)

        # Build lookup `inst_id → ref` from layout keys.
        ref_for_inst = {}
        for ref in layout.keys():
            if not isinstance(ref, str) or "/" not in ref: continue
            inst_id = ref.split("/", 1)[1]
            ref_for_inst[inst_id] = ref

        touched = 0
        cleared = 0
        for inst in instances:
            if not isinstance(inst, dict): continue
            iid = inst.get("id")
            if not iid: continue
            ref = ref_for_inst.get(iid)
            if ref is None:
                # Instance not in incoming layout: if it has stale x/y
                # AND the incoming layout was empty `{}`, clear them.
                if not layout:
                    if "x" in inst: inst.pop("x"); cleared += 1
                    if "y" in inst: inst.pop("y"); cleared += 1
                    if "top_x" in inst: inst.pop("top_x"); cleared += 1
                    if "top_y" in inst: inst.pop("top_y"); cleared += 1
                continue
            pos = layout.get(ref)
            if isinstance(pos, dict) and isinstance(pos.get("x"), (int, float)) \
               and isinstance(pos.get("y"), (int, float)):
                if ref.startswith("top:"):
                    inst["top_x"] = round(float(pos["x"]), 1)
                    inst["top_y"] = round(float(pos["y"]), 1)
                else:
                    inst["x"] = round(float(pos["x"]), 1)
                    inst["y"] = round(float(pos["y"]), 1)
                touched += 1

        # Preserve hex formatting on address fields. PyYAML parses
        # `0x4000_2000` to int 1073750016 on load; safe_dump would write
        # it back as decimal. Walk the doc and stringify any int in
        # known address slots so the rewritten file keeps the canonical
        # `0x4000_2000` notation the user wrote.
        def _hex8(n):
            h = f"{n:x}"
            target = max(8, ((len(h) - 1) // 4 + 1) * 4)
            h = h.zfill(target)
            if len(h) > 4:
                rev = h[::-1]
                groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                h = "_".join(groups)[::-1]
            return f"0x{h}"
        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int):  e["base"]  = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])

        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "touched": touched, "cleared": cleared,
                              "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/connect")
    async def api_soc_connect(request: Request):
        """Append a port-to-port connection to soc.ssot.yaml.

        Body: {"from": "ip/PORT", "to": "ip/PORT", "proto": "AXI4"}
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected json object"}, status_code=400)
        src = str(body.get("from") or "").strip()
        dst = str(body.get("to") or "").strip()
        proto = str(body.get("proto") or "").strip().upper()
        if "/" not in src or "/" not in dst:
            return JSONResponse({"error": "from/to must look like ip/PORT"},
                                status_code=400)
        if src == dst:
            return JSONResponse({"error": "cannot connect a port to itself"},
                                status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)

        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        conns = doc.setdefault("connections", [])
        if not isinstance(conns, list):
            return JSONResponse({"error": "soc.ssot.yaml connections is not a list"},
                                status_code=400)
        for c in conns:
            if isinstance(c, dict) and c.get("from") == src and c.get("to") == dst:
                return JSONResponse({"ok": True, "duplicate": True,
                                     "connection": c,
                                     "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})
        entry = {"from": src, "to": dst}
        if proto:
            entry["proto"] = proto
        conns.append(entry)

        def _hex8(n):
            h = f"{n:x}"
            target = max(8, ((len(h) - 1) // 4 + 1) * 4)
            h = h.zfill(target)
            if len(h) > 4:
                rev = h[::-1]
                groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                h = "_".join(groups)[::-1]
            return f"0x{h}"
        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int):  e["base"]  = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])
        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "connection": entry,
                             "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/instance/add")
    async def api_soc_instance_add(request: Request):
        """Instantiate a catalog model into soc.ssot.yaml.

        Body: {"model":"spi_master", "id":"spi_master_0",
               "cluster":"periph_ss", "addr":"0x4000_3000"}
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected json object"}, status_code=400)
        model = str(body.get("model") or body.get("name") or "").strip()
        req_id = str(body.get("id") or "").strip()
        cluster_id = str(body.get("cluster") or "").strip()
        addr = body.get("addr")
        if not model:
            return JSONResponse({"error": "missing model"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)

        catalog = []
        for p in sorted(PROJECT_ROOT.glob("*/yaml/*.ssot.yaml")):
            try:
                d = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            except Exception:
                d = {}
            if not isinstance(d, dict):
                d = {}
            ip_dir = p.parents[1]
            top = d.get("top_module")
            name = top if isinstance(top, str) and top.strip() else ip_dir.name
            catalog.append({"name": name, "id": ip_dir.name,
                            "ssot": p.relative_to(PROJECT_ROOT).as_posix()})
        found = next((m for m in catalog
                      if m["name"] == model or m["id"] == model), None)
        if not found:
            return JSONResponse({"error": f"model not found: {model}"}, status_code=404)

        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        instances = doc.setdefault("instances", [])
        clusters = doc.setdefault("clusters", [])
        if not isinstance(instances, list) or not isinstance(clusters, list):
            return JSONResponse({"error": "soc.ssot.yaml instances/clusters must be lists"},
                                status_code=400)
        existing_ids = {str(i.get("id")) for i in instances if isinstance(i, dict) and i.get("id")}
        base = req_id or found["name"]
        inst_id = base
        if inst_id in existing_ids:
            i = 0
            while f"{base}_{i}" in existing_ids:
                i += 1
            inst_id = f"{base}_{i}"

        def _role_for_name(name):
            n = (name or "").lower()
            if any(x in n for x in ["cpu", "core", "cortex", "riscv"]): return ("cpu_ss", "CPU")
            if any(x in n for x in ["noc", "axi", "crossbar", "interconnect", "cci"]): return ("noc", "BUS")
            if any(x in n for x in ["ddr", "sram", "mem", "dram"]): return ("mem_ss", "MEM")
            return ("periph_ss", "PERIPH")

        default_cluster, default_role = _role_for_name(found["name"])
        cluster_id = cluster_id or default_cluster
        cluster = next((c for c in clusters
                        if isinstance(c, dict) and (c.get("id") or c.get("name")) == cluster_id), None)
        if cluster is None:
            cluster = {"id": cluster_id, "role": default_role, "members": []}
            clusters.append(cluster)
        members = cluster.setdefault("members", [])
        if isinstance(members, list) and inst_id not in members:
            members.append(inst_id)

        inst = {"id": inst_id, "ssot": found["ssot"]}
        if addr not in (None, ""):
            inst["addr"] = str(addr)
        if isinstance(body.get("x"), (int, float)): inst["top_x"] = round(float(body["x"]), 1)
        if isinstance(body.get("y"), (int, float)): inst["top_y"] = round(float(body["y"]), 1)
        instances.append(inst)

        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "instance": inst, "cluster": cluster_id,
                             "model": found, "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/instance/delete")
    async def api_soc_instance_delete(request: Request):
        """Remove an instance from the SoC hierarchy without deleting model files.

        Body: {"id":"counter"}
        Removes:
          - instances[] entry
          - clusters[].members[] reference
          - connections touching <id>/*
          - addrMap entry matching id/name
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        inst_id = str((body or {}).get("id") or "").strip()
        if not inst_id:
            return JSONResponse({"error": "missing id"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        removed = {"instances": 0, "members": 0, "connections": 0, "addrMap": 0}
        instances = doc.get("instances") or []
        if isinstance(instances, list):
            kept = []
            for inst in instances:
                if isinstance(inst, dict) and str(inst.get("id") or "") == inst_id:
                    removed["instances"] += 1
                else:
                    kept.append(inst)
            doc["instances"] = kept
        for c in (doc.get("clusters") or []):
            if not isinstance(c, dict) or not isinstance(c.get("members"), list):
                continue
            before = len(c["members"])
            c["members"] = [m for m in c["members"] if str(m) != inst_id]
            removed["members"] += before - len(c["members"])
        conns = doc.get("connections") or []
        if isinstance(conns, list):
            kept = []
            prefix = f"{inst_id}/"
            for conn in conns:
                if isinstance(conn, dict) and (
                    str(conn.get("from") or "").startswith(prefix) or
                    str(conn.get("to") or "").startswith(prefix)
                ):
                    removed["connections"] += 1
                else:
                    kept.append(conn)
            doc["connections"] = kept
        amap = doc.get("addrMap") or []
        if isinstance(amap, list):
            kept = []
            for ent in amap:
                if isinstance(ent, dict) and str(ent.get("name") or "") == inst_id:
                    removed["addrMap"] += 1
                else:
                    kept.append(ent)
            doc["addrMap"] = kept
        if removed["instances"] == 0:
            return JSONResponse({"error": f"instance not found: {inst_id}",
                                 "removed": removed}, status_code=404)

        def _hex8(n):
            if isinstance(n, int):
                return "0x" + format(n, "08x")
            s = str(n)
            if s.startswith("0x"):
                return s
            return n

        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int): e["base"] = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])
        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "id": inst_id, "removed": removed,
                             "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/diagram/plan")
    async def api_diagram_plan(request: Request):
        """Plan diagram edits with the configured LLM.

        The model returns a narrow action JSON. The frontend owns actual
        application through existing layout/connect APIs.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        prompt = str((body or {}).get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "missing prompt"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        modules = []
        for inst in (doc.get("instances") or []):
            if not isinstance(inst, dict) or not inst.get("id"):
                continue
            mid = str(inst["id"])
            ports = []
            leaf = inst.get("ssot")
            if leaf:
                p = PROJECT_ROOT / str(leaf)
                if p.is_file():
                    try:
                        leaf_doc = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                        for bi in (leaf_doc.get("busInterfaces") or []):
                            if isinstance(bi, dict):
                                ports.append({
                                    "name": bi.get("name"),
                                    "proto": bi.get("proto"),
                                    "role": bi.get("role"),
                                    "side": bi.get("side"),
                                })
                    except Exception:
                        pass
            modules.append({"id": mid, "name": inst.get("name") or mid,
                            "addr": inst.get("addr"),
                            "x": inst.get("top_x") or inst.get("x"),
                            "y": inst.get("top_y") or inst.get("y"),
                            "ports": ports})
        context = {
            "soc": doc.get("name") or PROJECT_ROOT.name,
            "clusters": doc.get("clusters") or [],
            "modules": modules,
            "connections": doc.get("connections") or [],
            "current_layout": (body or {}).get("layout") or {},
            "canvas": {"w": 1180, "h": 720},
        }

        def _quick_architect_plan(text: str, ctx: dict):
            """Small deterministic command layer before the LLM planner.

            This is intentionally narrow: it gives the Architect chat a
            reliable tool-call surface for common diagram edits, while the
            LLM still handles freer natural language.
            """
            raw = (text or "").strip()
            if not raw:
                return None
            low = raw.lower()
            mods = {str(m.get("id")): m for m in (ctx.get("modules") or [])}
            layout = ctx.get("current_layout") or {}

            def _ref_for(mid: str) -> str:
                for c in (ctx.get("clusters") or []):
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name") or "uncategorized"
                    for member in (c.get("members") or []):
                        if str(member) == mid:
                            return f"{cid}/{mid}"
                return f"uncategorized/{mid}"

            def _pos(mid: str):
                ref = _ref_for(mid)
                p = layout.get(f"top:{ref}") or layout.get(ref) or {}
                m = mods.get(mid) or {}
                x = p.get("x", m.get("x"))
                y = p.get("y", m.get("y"))
                try: x = float(x)
                except Exception: x = 170.0
                try: y = float(y)
                except Exception: y = 240.0
                return x, y

            def _move_action(mid: str, where: str = "", x=None, y=None):
                if mid not in mods:
                    return None
                cx, cy = _pos(mid)
                w = (where or "").lower()
                if x is None or y is None:
                    if w in ("left", "좌", "왼쪽"): x, y = 80, cy
                    elif w in ("right", "우", "오른쪽"): x, y = 850, cy
                    elif w in ("top", "up", "위", "상단"): x, y = cx, 70
                    elif w in ("bottom", "down", "아래", "하단"): x, y = cx, 540
                    elif w in ("center", "middle", "중앙", "가운데"): x, y = 470, 280
                    else: return None
                return {"type": "move_block", "id": mid, "x": x, "y": y}

            if low in ("/arch", "/arch help", "/diagram help", "help", "도움말"):
                return {
                    "summary": "Architect commands: /move <inst> <x> <y>|left|right|top|bottom|center; /connect <inst/port> <inst/port> [proto]; /add <model> [id] [cluster]; /delete <inst>; /layout",
                    "actions": [],
                }

            if re.match(r"^/(layout|auto-?layout)\b", low) or low in ("자동배치", "자동 배치"):
                return {"summary": "Reset to automatic top-level layout", "actions": [{"type": "auto_layout"}]}

            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), x=float(m.group(2)), y=float(m.group(3)))
                return {"summary": f"Move {m.group(1)}", "actions": [act] if act else []}
            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+([A-Za-z가-힣]+)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), m.group(2))
                return {"summary": f"Move {m.group(1)} {m.group(2)}", "actions": [act] if act else []}

            for mid in mods:
                if re.search(rf"\b{re.escape(mid)}\b", raw):
                    where = None
                    if re.search(r"(left|왼쪽|좌측|좌로)", low): where = "left"
                    elif re.search(r"(right|오른쪽|우측|우로)", low): where = "right"
                    elif re.search(r"(top|up|위|상단)", low): where = "top"
                    elif re.search(r"(bottom|down|아래|하단)", low): where = "bottom"
                    elif re.search(r"(center|middle|중앙|가운데)", low): where = "center"
                    if where and re.search(r"(move|옮겨|움직|배치|놓|보내)", low):
                        act = _move_action(mid, where)
                        return {"summary": f"Move {mid} {where}", "actions": [act] if act else []}

            m = re.match(r"^/(?:connect|cn)\s+([\w.-]+/[\w.-]+)\s+([\w.-]+/[\w.-]+)(?:\s+([A-Za-z0-9_]+))?\s*$", raw, re.I)
            if m:
                proto = m.group(3) or ""
                return {"summary": f"Connect {m.group(1)} to {m.group(2)}",
                        "actions": [{"type": "connect_ports", "from": m.group(1), "to": m.group(2), "proto": proto}]}

            m = re.match(r"^/(?:add|add-instance|instantiate)\s+([A-Za-z_][\w]*)(?:\s+([A-Za-z_][\w]*))?(?:\s+([A-Za-z_][\w]*))?\s*$", raw, re.I)
            if m:
                model, inst_id, cluster = m.group(1), m.group(2), m.group(3)
                return {"summary": f"Add {model}",
                        "actions": [{"type": "add_instance", "model": model, "id": inst_id, "cluster": cluster, "x": 170, "y": 560}]}

            m = re.match(r"^/(?:delete|del|remove|rm)\s+([A-Za-z_][\w]*)\s*$", raw, re.I)
            if m:
                return {"summary": f"Delete {m.group(1)}",
                        "actions": [{"type": "delete_instance", "id": m.group(1)}]}

            return None

        quick_plan = _quick_architect_plan(prompt, context)
        if quick_plan is not None:
            return JSONResponse({"ok": True, "plan": quick_plan, "raw": "quick_architect_command"})

        try:
            arch_prompt = (PROJECT_ROOT / "workflow/architect/system_prompt.md").read_text(encoding="utf-8")[:4500]
            arch_commands = (PROJECT_ROOT / "workflow/architect/commands/architect.json").read_text(encoding="utf-8")[:2500]
        except Exception:
            arch_prompt = ""
            arch_commands = ""
        sys_prompt = (
            "You are an SoC Architect diagram planner. Convert the user request "
            "into ONLY strict JSON. No markdown. No prose. Schema: "
            "{\"summary\":\"...\",\"actions\":[...]}. "
            "Allowed actions: "
            "{\"type\":\"move_block\",\"id\":\"<module id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"connect_ports\",\"from\":\"<module>/<port>\",\"to\":\"<module>/<port>\",\"proto\":\"ACE|AXI4|APB|IRQ|...\"}; "
            "{\"type\":\"auto_layout\"}; "
            "{\"type\":\"add_instance\",\"model\":\"<catalog model>\",\"id\":\"<new instance id>\",\"cluster\":\"<cluster id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"delete_instance\",\"id\":\"<instance id>\"}. "
            "Use only module ids and ports present in context. For vague placement, choose reasonable canvas coordinates. "
            "You are attached to the workflow/architect supervisor contract below, but your output is still ONLY the diagram action JSON."
        )
        user_prompt = (
            "WORKFLOW ARCHITECT PROMPT EXCERPT:\n" + arch_prompt +
            "\n\nARCHITECT COMMANDS:\n" + arch_commands +
            "\n\nCONTEXT JSON:\n" + json.dumps(context, ensure_ascii=False, default=str) +
            "\n\nUSER REQUEST:\n" + prompt
        )
        try:
            from src.llm_client import call_llm_raw
            raw = await asyncio.to_thread(
                call_llm_raw,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1200,
                caller_tag="atlas_diagram_plan",
            )
        except Exception as e:
            return JSONResponse({"error": f"llm: {e}"}, status_code=500)
        txt = str(raw or "").strip()
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt)
        try:
            plan = json.loads(txt)
        except Exception:
            m = re.search(r"\{.*\}", txt, re.S)
            if not m:
                return JSONResponse({"error": "llm returned non-json", "raw": txt},
                                    status_code=500)
            try:
                plan = json.loads(m.group(0))
            except Exception as e:
                return JSONResponse({"error": f"json parse: {e}", "raw": txt},
                                    status_code=500)
        if not isinstance(plan, dict):
            return JSONResponse({"error": "plan must be object", "raw": txt},
                                status_code=500)
        actions = plan.get("actions")
        if not isinstance(actions, list):
            return JSONResponse({"error": "plan.actions must be list", "plan": plan},
                                status_code=500)
        allowed = {"move_block", "connect_ports", "auto_layout", "add_instance", "delete_instance"}
        plan["actions"] = [a for a in actions[:12]
                           if isinstance(a, dict) and a.get("type") in allowed]
        return JSONResponse({"ok": True, "plan": plan, "raw": txt})

    @app.post("/api/ipxact/import")
    async def api_ipxact_import(request: Request):
        """Import an IP-XACT XML payload into the project as a new IP.

        Accepts either:
          • multipart/form-data with a `xml` file part + optional `name`
          • application/json: {"xml": "<XML…>", "name": "spi_master"}
          • application/xml or text/xml body + ?name=<ip_name> query

        Writes <project_root>/<name>/yaml/<name>.ssot.yaml and scaffolds
        the surrounding IP layout. Returns the parsed SSOT + path.
        """
        try:
            ct = (request.headers.get("content-type") or "").lower()
            xml_text: str = ""
            ip_name: str = ""
            if ct.startswith("multipart/form-data"):
                form = await request.form()
                up = form.get("xml")
                if up is None:
                    return JSONResponse({"error": "missing 'xml' file part"}, status_code=400)
                if hasattr(up, "read"):
                    raw = await up.read()
                    xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                else:
                    xml_text = str(up)
                ip_name = (form.get("name") or "").strip()
            elif "json" in ct:
                body = await request.json()
                xml_text = body.get("xml", "") or ""
                ip_name = (body.get("name") or "").strip()
            else:
                raw = await request.body()
                xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                ip_name = (request.query_params.get("name") or "").strip()
            if not xml_text.strip():
                return JSONResponse({"error": "empty XML payload"}, status_code=400)

            try:
                from core.ipxact_import import import_ipxact as _conv
            except Exception:
                try: from ipxact_import import import_ipxact as _conv  # type: ignore
                except Exception as e:
                    return JSONResponse({"error": f"importer unavailable: {e}"}, status_code=500)
            try:
                ssot = _conv(xml_text, ip_name=ip_name or None)
            except Exception as e:
                return JSONResponse({"error": f"parse error: {e}"}, status_code=400)
            name = (ip_name or ssot.get("top_module") or "").strip()
            if not name or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
                return JSONResponse({"error": f"invalid ip name {name!r}"}, status_code=400)

            # Write into <project_root>/<name>/yaml/<name>.ssot.yaml.
            ip_dir = PROJECT_ROOT / name
            (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
            for sub in ("rtl", "sim", "tb", "list", "lint", "doc"):
                (ip_dir / sub).mkdir(parents=True, exist_ok=True)
            yaml_path = ip_dir / "yaml" / f"{name}.ssot.yaml"
            try:
                import yaml as _yaml
                with open(yaml_path, "w", encoding="utf-8") as f:
                    f.write("# Auto-imported from IP-XACT — review and edit as needed.\n")
                    _yaml.safe_dump(ssot, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            except ImportError:
                # No PyYAML → write a JSON sidecar so the import still
                # produces something usable.
                with open(yaml_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                    json.dump(ssot, f, indent=2)
                yaml_path = yaml_path.with_suffix(".json")
            except OSError as e:
                return JSONResponse({"error": f"write error: {e}"}, status_code=500)

            # Auto-register into soc.ssot.yaml when Tier-1 is active so
            # the new IP appears in the architect tree on the next
            # /api/soc fetch (was P1 bug — yaml on disk but tree empty).
            registered = False
            try:
                soc_path = PROJECT_ROOT / "soc.ssot.yaml"
                if soc_path.is_file():
                    import yaml as _y
                    sd = _y.safe_load(soc_path.read_text(encoding="utf-8")) or {}
                    if isinstance(sd, dict):
                        instances = sd.setdefault("instances", [])
                        # Skip if an instance with this id already exists.
                        existing = next((i for i in instances
                                          if isinstance(i, dict) and i.get("id") == name), None)
                        if existing is None:
                            new_inst = {
                                "id": name,
                                "ssot": yaml_path.relative_to(PROJECT_ROOT).as_posix(),
                            }
                            # Pull addr from the imported IP's memoryMap
                            # so addrmap_check can validate it.
                            mm = (ssot or {}).get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base: new_inst["addr"] = base
                            instances.append(new_inst)
                            # Drop into a synthetic "uncategorized" cluster
                            # if nothing else claims it (clusters[].members
                            # is the source of truth — auto-add a stub).
                            clusters = sd.setdefault("clusters", [])
                            uncat = next((c for c in clusters
                                          if isinstance(c, dict) and c.get("id") == "uncategorized"),
                                          None)
                            if uncat is None:
                                clusters.append({
                                    "id": "uncategorized",
                                    "role": "PERIPH",
                                    "label": "Uncategorized (auto-imported)",
                                    "members": [name],
                                })
                            else:
                                members = uncat.setdefault("members", [])
                                if name not in members: members.append(name)
                            with open(soc_path, "w", encoding="utf-8") as f:
                                _y.safe_dump(sd, f, sort_keys=False,
                                             default_flow_style=False, allow_unicode=True)
                            registered = True
            except Exception as e:
                # Non-fatal — IP file is on disk, just couldn't auto-register.
                # Frontend will still see it via Tier-2 fallback.
                pass

            return JSONResponse({
                "ok": True,
                "name": name,
                "path": yaml_path.relative_to(PROJECT_ROOT).as_posix(),
                "registered_in_soc": registered,
                "ssot": ssot,
            })
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/conversation")
    async def api_conversation(limit: int = 200):
        """Return the last N messages from the active workspace's
        conversation.json. Used by the Atlas frontend to hydrate the
        chat feed when the user switches workflow (/wf <name>) — without
        this the Atlas chat is browser-session-only and prior context
        from the workflow is invisible.

        config.HISTORY_FILE is already redirected per workspace by
        session_setup.setup_session, so we just read whichever file
        the live session points at right now.
        """
        try:
            try: import src.config as _cfg  # type: ignore
            except Exception:
                try: import config as _cfg  # type: ignore
                except Exception: _cfg = None
            if _cfg is None:
                return JSONResponse({"messages": [], "error": "config unavailable"})
            hpath = Path(getattr(_cfg, "HISTORY_FILE", "") or "")

            def _read_history(path: Path) -> list[dict[str, Any]]:
                if not path.is_file():
                    return []
                raw = json.loads(path.read_text(encoding="utf-8"))
                return raw if isinstance(raw, list) else []

            fallback_session = ""
            try:
                msgs = _read_history(hpath)
            except Exception as e:
                return JSONResponse({"messages": [], "path": str(hpath),
                                       "error": f"parse: {e}"})
            non_system = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if not non_system:
                root = PROJECT_ROOT / ".session"
                candidates = []
                if root.is_dir():
                    for p in root.rglob("conversation.json"):
                        try:
                            candidates.append((p.stat().st_mtime, p))
                        except Exception:
                            pass
                for _, p in sorted(candidates, reverse=True):
                    try:
                        alt = _read_history(p)
                    except Exception:
                        continue
                    alt_non_system = [
                        m for m in alt
                        if isinstance(m, dict) and m.get("role") != "system"
                    ]
                    if alt_non_system:
                        msgs = alt
                        hpath = p
                        try:
                            fallback_session = p.parent.relative_to(root).as_posix()
                        except Exception:
                            fallback_session = str(p.parent)
                        break
            # Drop system prompts (huge, useless in chat replay) and
            # keep only the last `limit` items.
            msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if len(msgs) > limit:
                msgs = msgs[-limit:]
            return JSONResponse({"messages": msgs, "path": str(hpath),
                                  "fallback_session": fallback_session,
                                  "truncated_to": limit})
        except Exception as e:
            return JSONResponse({"messages": [], "error": str(e)},
                                 status_code=500)

    # /api/session/history, /api/session/state, /api/session/list registered
    # via register_sessions_routes() (see atlas_api_sessions.py).

    # Jobs API (/api/job/dispatch, /api/jobs, /api/job/{id}/log, /api/job/{id}/cancel,
    # /api/jobs/dispatch_many, /api/jobs/clear, /api/pipeline/*) lives in
    # src/atlas_api_jobs.py. Inject runtime callables so routes see PROJECT_ROOT
    # changes from --root and the live normalize_session_name function.
    from atlas_api_jobs import register_jobs_routes, get_jobs_state as _get_jobs_state  # noqa: WPS433
    register_jobs_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        normalize_session_name=normalize_session_name,
        persist_config_values=_persist_config_values,
    )

    # ── Git API — status / diff / commit / push ─────────────────
    # All git commands run inside PROJECT_ROOT (the user's cwd at
    # launch). Read-only ops stream back; commit + push run sync
    # and return their stdout/stderr. Push includes an explicit
    # confirm flag because it's destructive (remote-visible).
    import subprocess as _sp_git
    # Git API (status / log / show / diff / commit / push) lives in
    # src/atlas_api_git.py. Inject runtime callables so the routes see
    # PROJECT_ROOT changes from --root and the live active-IP value.
    from atlas_api_git import register_git_routes  # noqa: WPS433
    register_git_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        active_ip_value=_active_ip_value,
        valid_ip_name=_valid_ip_name,
    )
    from atlas_api_vcd import register_vcd_routes  # noqa: WPS433
    register_vcd_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        safe_path=_safe,
        skip_dirs=SKIP_DIRS,
        max_vcd_bytes=MAX_VCD_BYTES,
    )
    # Workspaces API (list workflow definitions + download.zip) lives in
    # src/atlas_api_workspaces.py. Inject runtime callables so routes see
    # PROJECT_ROOT changes from --root.
    from atlas_api_workspaces import register_workspaces_routes  # noqa: WPS433
    register_workspaces_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        source_root=SOURCE_ROOT,
        safe_path=_safe,
    )
    # Orchestrator Chat API (per-IP rooms + _global). Routes share the
    # AtlasDB used everywhere else and route chat events through the
    # multi-user bridge's broadcast_all so cross-session clients see
    # them in real time.
    from atlas_api_chat import register_chat_routes  # noqa: WPS433
    from core.atlas_db import AtlasDB as _ChatAtlasDB  # noqa: WPS433
    from core.atlas_permissions import PermissionPolicy as _ChatPermissionPolicy  # noqa: WPS433
    _chat_db = _ChatAtlasDB()
    register_chat_routes(
        app,
        db=_chat_db,
        bridge=bridge,
        permissions=_ChatPermissionPolicy(_chat_db),
    )
    # SSOT API (/api/ssot, /api/ssot/qa, /api/ssot/qa/sessions,
    # /api/ssot/qa/answer) lives in src/atlas_api_ssot.py.
    from atlas_api_ssot import register_ssot_routes  # noqa: WPS433
    register_ssot_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        safe_path=_safe,
        skip_dirs=SKIP_DIRS,
        max_read_bytes=MAX_READ_BYTES,
        valid_ip_name=_valid_ip_name,
        active_ssot_ip=_active_ssot_ip,
        ssot_qa_view=_ssot_qa_view,
        ssot_qa_sessions_view=_ssot_qa_sessions_view,
        ssot_qa_path=_ssot_qa_path,
        qa_slug=_qa_slug,
        upsert_ssot_qa_items=_upsert_ssot_qa_items,
        load_ssot_state=_load_ssot_state,
        canonical_session_string=_canonical_session_string,
        normalize_session_name=normalize_session_name,
        append_session_message=_append_session_message,
        bridge=bridge,
    )

    # ── Sessions API (/api/session*, /api/sessions*) ────────────────
    # Routes live in src/atlas_api_sessions.py. Inject runtime callables
    # so routes see PROJECT_ROOT changes from --root and the live bridge.
    from atlas_api_sessions import register_sessions_routes  # noqa: WPS433

    # Lazy proxy for main._setup_workspace — main is imported later by
    # run_atlas_ui, so this wrapper does the import on first call.
    # Without it, /api/session/activate could only mirror env vars and
    # the live workspace stayed pinned to whatever was last loaded by
    # main.py's chat_loop /wf handler, producing the UI(tb-gen)/backend
    # (fl-model-gen) desync the user reported.
    def _setup_workspace_proxy(name: str) -> None:
        try:
            import main as _main_mod  # type: ignore
        except ImportError:
            try:
                from src import main as _main_mod  # type: ignore
            except ImportError:
                return
        fn = getattr(_main_mod, "_setup_workspace", None)
        if callable(fn):
            fn(name)

    def _setup_session_proxy(session_id: str) -> None:
        session = normalize_session_name(str(session_id or ""))
        if not session:
            return
        _atlas_active_session_cv.set(session)
        os.environ["ATLAS_ACTIVE_SESSION"] = session
        try:
            import main as _main_mod  # type: ignore
        except ImportError:
            try:
                from src import main as _main_mod  # type: ignore
            except ImportError:
                _main_mod = None
        fn = getattr(_main_mod, "_setup_session", None) if _main_mod is not None else None
        if callable(fn):
            fn(session)
        else:
            from core.session_setup import setup_session as _shared_setup_session
            _shared_setup_session(session)
        os.environ["ATLAS_SESSION_APPLIED"] = session

    register_sessions_routes(
        app,
        project_root=lambda: PROJECT_ROOT,
        normalize_session_name=normalize_session_name,
        active_session_value=_active_session_value,
        atlas_active_session_cv=_atlas_active_session_cv,
        atlas_active_ip_cv=_atlas_active_ip_cv,
        bridge=bridge,
        get_jobs_state=_get_jobs_state,
        atlas_db_factory=AtlasDB,
        setup_session=_setup_session_proxy,
        setup_workspace=_setup_workspace_proxy,
    )

    # ── Admin endpoints ──────────────────────────────────────────
    from core.atlas_auth import admin_auth_status, is_admin_user, is_local_admin_mode

    def _admin_required(request: Request) -> Optional[dict]:
        user = request.scope.get("user") or {}
        if is_local_admin_mode():
            return {
                "id": user.get("id") or "local-admin",
                "username": user.get("username") or "local-admin",
                "role": "admin",
            }
        return user if is_admin_user(user) else None

    def _admin_denied(request: Request) -> JSONResponse:
        if request.scope.get("user"):
            return JSONResponse({"error": "Admin role required"}, status_code=403)
        return JSONResponse({"error": "Admin login required"}, status_code=401)

    @app.get("/api/admin/auth/status")
    async def api_admin_auth_status(request: Request):
        try:
            with AtlasDB() as db:
                return JSONResponse(admin_auth_status(db, request.scope.get("user")))
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/admin/users")
    async def api_admin_users(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            with AtlasDB() as db:
                users = db.list_all_users()
                counts = db.count_sessions_by_user()
                for u in users:
                    u["session_count"] = counts.get(u["id"], 0)
                return JSONResponse({"users": users})
        except Exception as e:
            print(f"api_admin_users error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/admin/sessions")
    async def api_admin_sessions(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            with AtlasDB() as db:
                sessions = db.list_all_sessions()
                return JSONResponse({"sessions": sessions})
        except Exception as e:
            print(f"api_admin_sessions error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/admin/usage")
    async def api_admin_usage(request: Request):
        """Per-user usage aggregation: tokens, cost, message count, model
        distribution. Joined across users / sessions / messages."""
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            with AtlasDB() as db:
                from core.atlas_admin_usage import build_admin_usage_payload
                return JSONResponse(build_admin_usage_payload(db))
        except Exception as e:
            print(f"api_admin_usage error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/feedback")
    async def api_feedback_submit(request: Request):
        """Any logged-in user can drop a feedback message via /feedback
        slash. Stored in the `feedback` table and surfaced in the admin
        dashboard's Feedback tab."""
        user = request.scope.get("user")
        if not user:
            return JSONResponse({"error": "login required"}, status_code=401)
        try:
            body = await request.json()
        except Exception:
            body = {}
        content = str((body or {}).get("content") or "").strip()
        if not content:
            return JSONResponse({"error": "content required"}, status_code=400)
        if len(content) > 4000:
            return JSONResponse({"error": "content too long (max 4000 chars)"},
                                status_code=413)
        try:
            import uuid as _uuid
            with AtlasDB() as db:
                fid = _uuid.uuid4().hex
                db._execute(
                    "INSERT INTO feedback (id, user_id, content, status, created_at) "
                    "VALUES (?, ?, ?, 'open', ?)",
                    (fid, user["id"], content, time.time()),
                )
            return JSONResponse({"ok": True, "id": fid})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/admin/feedback")
    async def api_admin_feedback(request: Request):
        """Admin view of every feedback row, joined to the submitter's
        username for readability."""
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            with AtlasDB() as db:
                rows = db._fetchall(
                    "SELECT f.id, f.user_id, u.username, f.content, f.status, "
                    "       f.created_at, f.resolved_at, f.resolved_by, f.notes "
                    "  FROM feedback f "
                    "  LEFT JOIN users u ON u.id = f.user_id "
                    " ORDER BY f.created_at DESC"
                )
                items = [dict(r) for r in rows]
            return JSONResponse({"feedback": items})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/api/admin/feedback/{fid}/resolve")
    async def api_admin_feedback_resolve(fid: str, request: Request):
        """Mark a feedback item resolved. Body: {notes: str (optional)}."""
        admin = _admin_required(request)
        if admin is None:
            return _admin_denied(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        notes = str((body or {}).get("notes") or "").strip()
        try:
            with AtlasDB() as db:
                db._execute(
                    "UPDATE feedback SET status = 'resolved', resolved_at = ?, "
                    "       resolved_by = ?, notes = ? WHERE id = ?",
                    (time.time(), admin.get("username", ""), notes, fid),
                )
            return JSONResponse({"ok": True})
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.delete("/api/admin/sessions/{session_id}")
    async def api_admin_delete_session(session_id: str, request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            with AtlasDB() as db:
                if db.get_session(session_id) is None:
                    return JSONResponse({"error": "session not found"}, status_code=404)
                db.delete_session(session_id)
                return JSONResponse({"deleted": True})
        except Exception as e:
            print(f"api_admin_delete_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/admin")
    async def admin_page(request: Request):
        html = (FRONTEND / "admin.html").read_text(encoding="utf-8")

        def _inline_script(match):
            attrs = match.group("attrs")
            src = match.group("src").split("?", 1)[0]
            if not src.endswith((".jsx", ".js")):
                return match.group(0)
            path = (FRONTEND / src).resolve()
            try:
                path.relative_to(FRONTEND.resolve())
            except Exception:
                return match.group(0)
            if not path.is_file():
                return match.group(0)
            code = path.read_text(encoding="utf-8")
            if "data-filename" not in attrs:
                attrs = f'data-filename="{html_lib.escape(src, quote=True)}" {attrs}'
            return f'<script type="text/babel" {attrs}>{code.rstrip()}\n//# sourceURL={src}</script>'

        html = re.sub(
            r'<script\s+type="text/babel"\s+(?P<attrs>[^>]*?)src="(?P<src>[^"]+)"[^>]*>\s*</script>',
            _inline_script,
            html,
        )
        return HTMLResponse(html)

    # NOTE: WebSocket endpoint is registered via Starlette's WebSocketRoute
    # (added to app.router.routes below) instead of the @app.websocket
    # decorator. The decorator routes through FastAPI's dependency-injection
    # layer, which can't resolve the `websocket: WebSocket` annotation when
    # `from __future__ import annotations` is active (PEP 563 turns all
    # annotations into strings) and rejects the handshake with HTTP 403.
    # Starlette's WebSocketRoute talks to the function directly and ignores
    # parameter annotations entirely.
    async def ws_agent(websocket: WebSocket):
        try:
            await websocket.accept()
        except Exception as exc:
            if _is_websocket_disconnect(exc):
                return
            raise
        session_id = websocket.query_params.get("session_id", "")
        _multi_raw = os.environ.get("ATLAS_MULTI_USER", "1").strip().lower()
        _multi_user = _multi_raw not in ("0", "false", "no", "off")

        class _WebSocketCookieRequest:
            def __init__(self, cookies: dict):
                self.cookies = cookies

        cookies = getattr(websocket, "cookies", None)
        if cookies is None:
            cookies = websocket.scope.get("cookies") or {}
        user = auth.get_user_from_cookie(_WebSocketCookieRequest(cookies))
        if user is None:
            try:
                from core.atlas_auth import is_local_admin_mode, local_admin_user
            except Exception:
                try:
                    from atlas_auth import is_local_admin_mode, local_admin_user  # type: ignore
                except Exception:
                    is_local_admin_mode = None  # type: ignore
                    local_admin_user = None  # type: ignore
            if callable(is_local_admin_mode) and is_local_admin_mode() and callable(local_admin_user):
                user = local_admin_user()
        if user is None:
            await _close_websocket_quietly(websocket, code=1008, reason="unauthenticated")
            return

        username = normalize_session_name(str(user.get("username") or ""))

        def _authorize_ws_session(raw_session: str) -> str | None:
            normalized = normalize_session_name(str(raw_session or ""))
            if not normalized or normalized == "default":
                normalized = f"{username}/default" if username else "default"
            elif username and normalized == username:
                normalized = f"{username}/default"
            owner = normalized.split("/", 1)[0]
            if _multi_user and username and owner != username:
                with AtlasDB() as db:
                    owned = db.get_session(normalized)
                if not (owned and owned.get("user_id") == user["id"]):
                    return None
            return normalized

        # Identity-driven default: empty / legacy "default" session_id
        # collapses to the user's default namespace. Full
        # <user>/<ip>/<workflow> namespaces are allowed for that user, so
        # two browser tabs on different IP/workflow views do not receive
        # each other's backend stream.
        session_id = _authorize_ws_session(session_id)
        if session_id is None:
            await _close_websocket_quietly(websocket, code=1008, reason="forbidden")
            return
        bridge.bind_client(websocket, session_id)
        try:
            _setup_session_proxy(session_id)
        except Exception:
            pass
        _ensure_broadcaster()
        # Greeting — surface user-tunable layout settings so the frontend
        # can pick its center-column shape (classic vs tabbed Chat/Preview/Q&A).
        _center_layout = "classic"
        _chat_feed_summary = True
        try:
            import src.config as _cfg_hello
            # /healthz already calls reload_env on every poll, so the
            # WS-connect handshake doesn't need to repeat the sync .env
            # read. Reading the cached attribute values is plenty.
            _center_layout = getattr(_cfg_hello, "ATLAS_CENTER_LAYOUT", "classic")
            _chat_feed_summary = bool(getattr(_cfg_hello, "ATLAS_CHAT_FEED_SUMMARY", True))
        except Exception:
            pass
        try:
            try:
                _session_running = bool(getattr(bridge.get_session(session_id), "agent_running", False))
            except Exception:
                _session_running = bool(bridge.agent_running)
            await websocket.send_json({"type": "hello", "frontend": "atlas",
                                        "running": _session_running,
                                        "center_layout": _center_layout,
                                        "chat_feed_summary": _chat_feed_summary})
            for pending_event in bridge.session_pending_ask_user_events(session_id):
                await websocket.send_json(pending_event)
        except Exception as exc:
            if not _is_websocket_disconnect(exc):
                raise
            bridge.unbind_client(websocket)
            return
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except Exception:
                    continue
                session = bridge.get_client_session(websocket)
                if session is None:
                    continue
                set_atlas_bridge_session_id(session.session_id)
                t = msg.get("type")
                if t in ("prompt", "send") and msg.get("text"):
                    _txt = msg["text"].strip()
                    _session_raw = str(msg.get("session") or "").strip()
                    if _session_raw:
                        _session = _authorize_ws_session(_session_raw)
                        if not _session:
                            session.emit("error", message=f"invalid or forbidden session: {_session_raw!r}")
                            continue
                        if _session != session.session_id:
                            bridge.bind_client(websocket, _session)
                            session = bridge.get_client_session(websocket)
                            if session is None:
                                continue
                            set_atlas_bridge_session_id(session.session_id)
                        _atlas_active_session_cv.set(_session)
                        try:
                            _setup_session_proxy(_session)
                        except Exception as exc:
                            session.emit("error", message=f"session setup failed: {exc}")
                            continue
                    # Idempotent submit + ack:
                    # The frontend retransmits a prompt with the same
                    # msg_id if it doesn't see an `agent_received`
                    # ack within ~3s. We always emit the ack so the
                    # frontend cancels its retry timer; we only call
                    # submit_prompt the first time.
                    _msg_id = str(msg.get("msg_id") or "").strip()
                    _txt_preview = str(msg.get("text") or "")[:80].replace("\n", " ")
                    session.emit(
                        "agent_received",
                        msg_id=_msg_id,
                        text_preview=_txt_preview,
                    )
                    if _msg_id and session.msg_id_seen(_msg_id):
                        continue
                    import os as _os
                    _ui_lang_raw = str(msg.get("ui_lang") or _ui_lang_value() or "").strip().lower()
                    _ui_lang = {
                        "ko": "ko",
                        "kr": "ko",
                        "korean": "ko",
                        "한국어": "ko",
                        "en": "en",
                        "eng": "en",
                        "english": "en",
                    }.get(_ui_lang_raw, "")
                    if _ui_lang:
                        _atlas_ui_lang_cv.set(_ui_lang)
                    # ── Mode-flip slashes need to apply mid-loop ──
                    # `/mode normal` and `/plan` typed while the agent is
                    # running normally land in the _interrupts queue,
                    # which feeds the agent as conversational text — the
                    # slash dispatcher only runs against _inbox between
                    # turns. So agent_mode never actually flips and the
                    # agent stays trapped in plan_q forever, hitting
                    # `[Plan Mode] blocked` on every write_file. We
                    # intercept those four canonical forms here and set
                    # AGENT_MODE_OVERRIDE in the environment; react_loop
                    # reads it at the top of each iteration.
                    _low = _txt.lower()
                    if _handle_new_ip_command(_txt, client_session=session):
                        continue
                    if _handle_ip_command(_txt, client_session=session):
                        continue
                    if _handle_session_command(_txt, client_session=session):
                        continue
                    if _handle_import_command(_txt, client_session=session):
                        continue
                    if _handle_grill_me_command(_txt, client_session=session):
                        continue
                    if _handle_approval_command(_txt, client_session=session):
                        continue
                    if _handle_resolve_rtl_blockers_command(_txt, client_session=session):
                        continue
                    if _handle_repair_ssot_command(_txt, client_session=session):
                        continue
                    if _handle_repair_rtl_command(_txt, client_session=session):
                        continue
                    if _handle_repair_equiv_command(_txt, client_session=session):
                        continue
                    if _handle_to_ssot_gate(_txt, client_session=session):
                        continue
                    if _run_stage_command(_txt, client_session=session):
                        continue
                    if _execute_generic_slash_command(_txt, session):
                        continue
                    if _low in ("/plan", "/mode plan", "/mode normal", "/normal"):
                        is_plan = _low in ("/plan", "/mode plan")
                        if is_plan:
                            _agent_mode_override_cv.set("plan_q")
                            _plan_mode_cv.set("true")
                            os.environ["AGENT_MODE_OVERRIDE"] = "plan_q"
                            os.environ["PLAN_MODE"] = "true"
                        else:
                            _agent_mode_override_cv.set("normal")
                            _plan_mode_cv.set("false")
                            os.environ["AGENT_MODE_OVERRIDE"] = "normal"
                            os.environ["PLAN_MODE"] = "false"
                            _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        # Immediate UI feedback so the chat reflects the
                        # mode flip the moment the user clicks the
                        # NORMAL/PLAN pill (or types /plan), instead of
                        # waiting for the next turn boundary. Previously
                        # we deferred the banner to main.py's dispatcher
                        # which only runs between turns — clicking PLAN
                        # while the agent was idle left the chat silent
                        # until the user typed a message.
                        try:
                            if is_plan:
                                session.emit("agent", text=(
                                    "✅ Plan mode — read-only. "
                                    "The agent will analyze and propose without mutating tools. "
                                    "Type `apply` or click NORMAL to execute."
                                ))
                            else:
                                session.emit("agent", text=(
                                    "✅ Normal mode — tools enabled."
                                ))
                            session.emit("flush")
                        except Exception:
                            pass
                        # Two-pronged dispatch:
                        # (1) AGENT_MODE_OVERRIDE handles the MID-LOOP case
                        #     (agent currently iterating; react_loop top
                        #     pops it on the next pass and flips local
                        #     agent_mode for parallel_executor).
                        # (2) submit_prompt forwards the slash so main.py's
                        #     dispatcher can fire AGENT_MODE:normal/plan
                        #     when the loop is IDLE — that path is what
                        #     keeps main.py's local agent_mode + the
                        #     system prompt in messages[0] consistent
                        #     across turns. Without this submit, the
                        #     UI's "● NORMAL" pill could click without
                        #     ever telling main.py to flip — desync.
                        bridge.submit_prompt_for_session(session.session_id, _txt)
                        continue

                    # `y` / `yc` / `yes` / `confirm` mid-loop while agent
                    # is in plan mode → treat as plan confirmation. Without
                    # this, the input lands in the _interrupts queue and
                    # gets fed to the LLM as conversational text — the
                    # plan-confirmation handler in chat_loop only runs
                    # against _inbox between turns. So `y` after the
                    # agent shows the [Plan Mode] Plan ready prompt does
                    # nothing if the agent is still mid-iteration.
                    if (_plan_mode_value() == "true"
                            and bridge.agent_running
                            and _low in ("y", "yes", "yc", "confirm", "ok",
                                         "proceed", "ㅇㅇ", "확인", "진행")):
                        _agent_mode_override_cv.set("normal")
                        _plan_mode_cv.set("false")
                        _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        session.emit("token", text="\n✅ Plan confirmed (mid-loop): tools enabled. Executing.\n")
                        session.emit("flush")
                        # Inject an instruction so the agent knows to start
                        # executing the agreed-upon plan. This goes to
                        # _interrupts (since agent is running), fed mid-loop.
                        bridge.submit_prompt_for_session(
                            session.session_id,
                            "Confirmed. Execute all tasks in order. "
                            "For EACH task: todo_update(in_progress) → do work "
                            "→ todo_update(completed) → verify → todo_update(approved)."
                        )
                        continue
                    _control_heads = {"approve", "y", "yes", "yc", "confirm", "ok", "proceed", "ㅇㅇ", "확인", "진행"}
                    _head = (_txt.split(None, 1)[0] if _txt else "").lower()
                    if _ui_lang and _txt and not _txt.startswith("/") and _head not in _control_heads:
                        if _ui_lang == "ko":
                            _txt = (
                                "[Atlas UI language preference]\n"
                                "User-visible explanations, status summaries, questions, and reports should be written in Korean as much as possible. "
                                "Keep code, file paths, commands, signal names, protocol names, and exact identifiers unchanged.\n\n"
                                + _txt
                            )
                        elif _ui_lang == "en":
                            _txt = (
                                "[Atlas UI language preference]\n"
                                "User-visible explanations, status summaries, questions, and reports should be written in English as much as possible. "
                                "Keep code, file paths, commands, signal names, protocol names, and exact identifiers unchanged.\n\n"
                                + _txt
                            )
                    bridge.submit_prompt_for_session(session.session_id, _txt)
                elif t == "interrupt":
                    bridge.submit_interrupt_for_session(session.session_id, msg.get("text", ""))
                elif t == "answer" and msg.get("flow_id"):
                    accepted = bridge.submit_answer_for_session(session.session_id, msg["flow_id"], msg)
                    if accepted:
                        session.emit("agent_state", running=True)
                    else:
                        session.emit(
                            "error",
                            message=(
                                "answer rejected: no pending ask_user flow "
                                f"for {msg['flow_id']}"
                            ),
                        )
                elif t == "stop":
                    # Esc from the UI — abort the current iteration.
                    # Surface the stop on the chat feed so the user sees
                    # the backend acknowledged the ESC immediately,
                    # before the agent thread gets to its next poll.
                    session.emit("token", text="\n⏹  stop received\n")
                    session.emit("flush")
                    bridge.request_stop_for_session(session.session_id)
                    session.emit("agent_state", running=False)
                elif t == "shutdown":
                    # Exit button — terminate only this session's worker.
                    # Atlas UI is the shared backend server, so keep it alive.
                    session.emit("token", text="\n⏹  worker exit requested\n")
                    session.emit("flush")
                    bridge.exit_session(session.session_id)
                # Other types (e.g. run_stage, tool_call) can be wired later
        except Exception as exc:
            if not _is_websocket_disconnect(exc):
                raise
        finally:
            bridge.unbind_client(websocket)

    from core.atlas_auth import GuestAuth, AuthMiddleware, create_auth_endpoints
    auth = GuestAuth(AtlasDB())
    app.state.auth = auth
    app.add_middleware(AuthMiddleware, auth=auth)
    create_auth_endpoints(app, auth)

    # Register the WebSocket endpoint via Starlette so we don't go through
    # FastAPI's DI layer (see the long comment above the ws_agent definition).
    app.router.routes.append(WebSocketRoute("/ws/agent", ws_agent))

    # Static assets — jsx, css, js, fonts (registered LAST so it doesn't
    # shadow the explicit routes above). Disable client-side caching so
    # a normal page refresh always picks up new JSX/CSS.
    import mimetypes as _mimetypes
    _JS_CONTENT_TYPE = "application/javascript; charset=utf-8"
    _MIME_OVERRIDES: dict[str, str] = {
        ".js": _JS_CONTENT_TYPE,
        ".jsx": _JS_CONTENT_TYPE,
        ".mjs": _JS_CONTENT_TYPE,
    }

    class _NoCacheStatic(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-store, max-age=0"
            p = str(path)
            ext = p[p.rfind("."):] if "." in p else ""
            if ext in _MIME_OVERRIDES:
                resp.headers["Content-Type"] = _MIME_OVERRIDES[ext]
            else:
                guessed = _mimetypes.guess_type(p)[0]
                if guessed and resp.headers.get("Content-Type", "").startswith("text/plain"):
                    resp.headers["Content-Type"] = guessed
            return resp

    app.mount("/", _NoCacheStatic(directory=str(FRONTEND), html=False),
              name="atlas-static")

    app.state.bridge = bridge

    # Expose SSOT-QA helpers so run_atlas_ui's nested callbacks
    # (_ask_user_cb, _record_ssot_qa_cb) can reach them across function
    # scopes — these helpers live in create_app's local closure and were
    # otherwise invisible from run_atlas_ui, causing NameError at the
    # first ask_user / record_ssot_qa invocation.
    app.state.active_ssot_qa_context = _active_ssot_qa_context
    app.state.ssot_q_pairs_from_questions = _ssot_q_pairs_from_questions
    app.state.upsert_ssot_qa_items = _upsert_ssot_qa_items
    app.state.load_ssot_state = _load_ssot_state
    app.state.valid_ip_name = _valid_ip_name
    app.state.status_group = _status_group
    app.state.answer_text = _answer_text
    return app


# ── Entry point ────────────────────────────────────────────────────
def run_atlas_ui(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Start the Atlas web UI server and run the agent in a worker thread.

    Wires brian_hw/common_ai_agent/src/main.py's _textual_* callbacks so the
    existing ReAct loop streams to all connected WS clients.
    """
    import uvicorn
    import main as _main  # noqa: WPS433  (intentional runtime import)
    from core.atlas_multiuser import changed_paths_from_tool_result

    app = create_app()
    bridge = app.state.bridge

    # Rebind SSOT-QA helpers from create_app's closure (exposed via
    # app.state) so the nested _ask_user_cb / _record_ssot_qa_cb defined
    # below can reference them by their original local names without
    # raising NameError. See create_app return block for the export side.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _load_ssot_state = app.state.load_ssot_state
    _valid_ip_name = app.state.valid_ip_name
    _status_group = app.state.status_group
    _answer_text = app.state.answer_text

    # ── Wire main.py callbacks → bridge.emit ───────────────────────
    _main._textual_input_fn = bridge.get_input
    # Esc from the UI sets bridge._stop_flag; react_loop polls this
    # via esc_check_fn and aborts the current iteration cleanly.
    _main._textual_esc_check_fn = bridge.check_stop
    _main._textual_poll_human_input_fn = bridge.poll_interrupt
    # Per-thread active-session reader. main.py used to read
    # os.environ["ATLAS_ACTIVE_SESSION"] directly which races between
    # concurrent users in multi-user mode. By exposing the contextvar
    # via a callback, main.py can resolve the per-thread value first.
    _main._textual_active_session_fn = _active_session_value
    _main._textual_active_ip_fn      = _active_ip_value

    # Strip ANSI escape sequences from ANY text destined for the browser.
    # The terminal-targeting Color class wraps lines in \x1b[2m … \x1b[0m;
    # the browser renders the ESC byte invisibly but happily prints the
    # leftover "[2m" / "[0m" markers, which leaked into the chat as visible
    # garbage. Doing the strip once here covers every emit path.
    import re as _re_ansi
    # First branch: full CSI/OSC sequences w/ the leading ESC byte.
    # Last branch: ORPHAN SGR codes whose ESC was stripped upstream
    # (common on Windows when the console host or codec drops 0x1b),
    # leaving visible garbage like `[2m 187 [0m` in the chat. Match
    # them only when they look like real SGR — `[<digits[;digits]*>m`.
    _ANSI_RE = _re_ansi.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]"
        r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
        r"|\[(?:\d{1,3};)*\d{0,3}m"
    )
    def _clean(s):
        return _ANSI_RE.sub("", s) if isinstance(s, str) else s

    def _current_todo_state() -> dict[str, Any]:
        """Return the freshest structured todo state for browser rendering."""
        try:
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "to_dict"):
                state = tt.to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list) and state.get("todos"):
                    return state
        except Exception:
            pass
        try:
            import config as _cfg
            from lib.todo_tracker import TodoTracker
            todo_path = Path(str(getattr(_cfg, "TODO_FILE", "current_todos.json")))
            if not todo_path.is_absolute():
                todo_path = PROJECT_ROOT / todo_path
            if todo_path.exists():
                state = TodoTracker.load(todo_path).to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list):
                    return state
        except Exception:
            pass
        return {"todos": []}

    def _emit_todo_line(text: str) -> None:
        state = {"todos": []} if not str(text or "").strip() else _current_todo_state()
        bridge.emit(
            "todo_line",
            text=_clean(text),
            todo_state=state,
            todos=state.get("todos", []),
        )

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=_clean(text), cls=cls)

    def _atlas_emit_reasoning(text, blank=False):
        cleaned = _clean(text)
        # Browser side via the live WS bridge (chat feed renders this
        # as a CollapsibleThought block — see workspace.jsx).
        bridge.emit("reasoning", text=cleaned)
        # Server-console mirror: an operator running textual_main.py
        # in a terminal needs to see what the model is thinking too,
        # not just the tool calls. Mirror to stderr with a CYAN ┃
        # prefix so reasoning lines are scannable amid debug output.
        if cleaned:
            try:
                import sys as _sys_re
                if blank:
                    _sys_re.stderr.write("\n")
                else:
                    _sys_re.stderr.write(
                        f"  \033[36m┃\033[0m \033[2m{cleaned}\033[0m\n"
                    )
                _sys_re.stderr.flush()
            except Exception:
                pass

    _main._textual_emit_reasoning_fn = _atlas_emit_reasoning
    _main._textual_emit_todo_fn      = _emit_todo_line
    _main._textual_emit_flush_fn     = lambda: (
        bridge.emit("flush"),
        # Workspace switches happen behind a slash command and re-register
        # the slash registry. Nudge the UI to re-fetch /api/commands so the
        # autocomplete dropdown picks up new workspace commands.
        bridge.emit("commands_changed"),
    )
    _main._textual_emit_tool_fn      = lambda text: bridge.emit("tool", text=_clean(text))
    # Browser-side tool_result cap. Display-only — LLM still gets the
    # full obs upstream; this just trims what we ship over the WS so a
    # multi-MB grep / sim log doesn't drown the chat. Configurable via
    # WS_TOOL_RESULT_MAX_CHARS. Default raised to 128 KB so a typical
    # SSOT YAML (≈ 60-100 KB) renders end-to-end without the previous
    # 8 KB ceiling chopping the file at the registers section.
    _ws_tool_max = 128000
    try:
        try: import src.config as _cfg2  # type: ignore  # noqa: WPS433
        except Exception:
            try: import config as _cfg2  # type: ignore  # noqa: WPS433
            except Exception: _cfg2 = None
        if _cfg2 is not None:
            _ws_tool_max = int(getattr(_cfg2, "WS_TOOL_RESULT_MAX_CHARS", 128000))
    except Exception:
        _ws_tool_max = 128000
    # Strip the `[Step N/M: ...] ... → Interpret the result below in
    # context of the current goal` block that react_loop prepends to
    # observations for the LLM. That header is useful in the LLM
    # message stream but pollutes the user-facing tool_result card —
    # without this defensive strip a write/replace tool_result body
    # opens with the entire todo header instead of the actual diff.
    _STEP_HEADER_RE = re.compile(
        r"^\[Step\s+\d+/\d+:[^\n]*\]\n"
        r"(?:[^\n]*\n)*?"
        r"→ Interpret the result below in context of the current goal\n+",
        re.MULTILINE,
    )

    def _emit_tool_result(obs, tool=""):
        cleaned = _clean(obs)
        cleaned = _STEP_HEADER_RE.sub("", cleaned, count=1)
        bridge.emit(
            "tool_result",
            text=cleaned[:_ws_tool_max],
            tool=tool,
            truncated=len(cleaned) > _ws_tool_max,
        )
        # Auto-commit for write/replace/edit tools — capture the
        # operated-on path from the tool result body and snapshot the
        # change into the per-IP .git so each agent edit becomes a
        # discrete commit. Best-effort: any parse miss or git failure
        # is silent (Atlas should never refuse to display a result
        # because the optional commit failed).
        try:
            for _path_hit in changed_paths_from_tool_result(tool, cleaned):
                _auto_commit_for_path(_path_hit, tool=tool)
                # Push a file_changed event so the frontend can
                # auto-reload preview / SSOT / file-tree without
                # waiting for the next tool_result coalesce window.
                try:
                    bridge.emit("file_changed", path=str(_path_hit), tool=tool)
                except Exception:
                    pass
        except Exception:
            pass
    _main._textual_emit_tool_result_fn = _emit_tool_result

    def _ctx_update(tokens, max_tok):
        bridge.emit("context", used=tokens, max=max_tok)
    _main._textual_emit_context_fn = _ctx_update
    def _emit_token(in_tok, cache_tok, out_tok):
        # Resolve pricing at LLM-call time so the rate matches the model
        # actually used for THIS call (LLM_ACTIVE_BASE_NAME / LLM_BASE_NAME
        # can pin the base model; otherwise fall back to MODEL_NAME /
        # LLM_MODEL_NAME).
        # Computing the USD delta on the backend keeps frontend math simple
        # and avoids drift between page-load /healthz pricing and the
        # current call's model.
        try:
            from lib.model_pricing import get_active_pricing
            p = get_active_pricing()
        except Exception:
            p = None
        cost_delta = 0.0
        if p is not None:
            # in_tok from react_loop is the FULL prompt_tokens (includes
            # the cached subset). cache_tok is that cached subset only.
            # Charging both `in_tok * input` and `cache_tok * cache` would
            # bill the cached portion twice — once at the input rate and
            # once at the cache rate. Subtract the cache slice first so
            # billable_input = prompt − cached.
            _in = max(0, (in_tok or 0) - (cache_tok or 0))
            cost_delta = (
                _in              * p.input  +
                (cache_tok or 0) * p.cache  +
                (out_tok or 0)   * p.output
            ) / 1_000_000.0
        # Resolve display model name for the frontend cost panel.
        try:
            import os as _os_cost
            _model_now = (
                _os_cost.getenv("LLM_ACTIVE_BASE_NAME", "").strip()
                or _os_cost.getenv("LLM_BASE_NAME", "").strip()
                or _os_cost.getenv("LLM_ACTIVE_BASE_MODEL", "").strip()
                or _os_cost.getenv("LLM_BASE_MODEL", "").strip()
                or _os_cost.getenv("LLM_MODEL_NAME", "").strip()
            )
            if not _model_now:
                try:
                    from src.llm_client import get_active_model as _gam
                    _model_now = _gam() or ""
                except Exception:
                    _model_now = ""
        except Exception:
            _model_now = ""
        bridge.emit(
            "cost",
            input=in_tok, cached=cache_tok, output=out_tok,
            cost_usd_delta=cost_delta,
            pricing={"input": p.input, "cache": p.cache, "output": p.output} if p else None,
            model=_model_now,
        )
    _main._textual_emit_token_fn = _emit_token

    def _set_running(val: bool):
        bridge.agent_running = val
        bridge.emit("agent_state", running=val)
    _main._textual_set_agent_running_fn = _set_running

    # Safety-net emit for slash command output. The token+flush pipeline has
    # shown intermittent delivery for slash payloads (frontend gets the
    # subsequent agent_state but no token frame), leaving the user with a
    # missing /context / /help / /skills response. This event lands the
    # payload directly in the feed via workspace.jsx's slash_output handler.
    _main._textual_emit_slash_output_fn = lambda text: bridge.emit(
        "slash_output", text=_clean(text)
    )

    # Mode-change notification — chat_loop auto-promotes plan_q→normal when
    # the user types "y" to confirm. Without this signal the React mode pill
    # stays on PLAN even though the agent is now executing.
    _main._textual_emit_mode_fn = lambda mode: bridge.emit("mode_change", mode=mode)

    # ── ask_user → emit qcard event, block on answer queue ────────
    import uuid
    try:
        from core import tools as _tools
    except ImportError:
        _tools = None

    # Helpers are defined as closures inside create_app(); pull them off
    # app.state so this module-level function can reach them.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _valid_ip_name = app.state.valid_ip_name
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _load_ssot_state = app.state.load_ssot_state
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _status_group = app.state.status_group

    def _record_ssot_qa_cb(questions=None, ip=None, session=None, kind="",
                           source="llm-ssot-qna", status="pending"):
        """Record deferred SSOT QA without blocking the agent thread."""
        ctx_ip, ctx_session = _active_ssot_qa_context()
        target_ip = str(ip or ctx_ip or "").strip()
        if not _valid_ip_name(target_ip):
            return "[record_ssot_qa: no active valid SSOT IP]"
        target_session = normalize_session_name(str(session or ctx_session or f"{target_ip}/ssot-gen"))
        flow_id = "qa_backlog_" + uuid.uuid4().hex[:10]
        q_pairs = _ssot_q_pairs_from_questions(questions or [])
        if not q_pairs:
            return "[record_ssot_qa: no valid QA items to record]"
        state = _load_ssot_state(target_ip) or {}
        ip_kind = str(kind or "").strip()
        if ip_kind.lower() in {"single", "multi", "input"}:
            ip_kind = ""
        _upsert_ssot_qa_items(
            target_ip,
            flow_id=flow_id,
            kind=str(ip_kind or state.get("kind") or "general IP"),
            q_pairs=q_pairs,
            status=str(status or "pending"),
            session=target_session,
            source=str(source or "llm-ssot-qna"),
        )
        bridge.emit(
            "ssot_qa_updated",
            ip=target_ip,
            workflow="ssot-gen",
            flow_id=flow_id,
            session=target_session,
        )
        return (
            f"[record_ssot_qa] recorded {len(q_pairs)} "
            f"{_status_group(str(status or 'pending'))} SSOT QA item(s) "
            f"for {target_session}"
        )

    def _ask_user_cb(question, options, kind, subtitle, questions=None):
        """ask_user UI bridge.

        Single-question mode: pass `question/options/kind/subtitle`.
        Batched mode (mirrors textual UI): pass `questions=[{...}, ...]`
        and the frontend renders a tab strip — one breadcrumb per
        question, ☐/☒ answered marker, plus a final 'Submit' tab — so
        the user fills N answers in one round-trip.
        """
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        ssot_ip, ssot_session = _active_ssot_qa_context()
        ssot_q_pairs: list[tuple[str, str, dict[str, Any]]] = []
        if ssot_ip:
            if questions:
                ssot_q_pairs = _ssot_q_pairs_from_questions(questions)
            elif question:
                ssot_q_pairs = _ssot_q_pairs_from_questions([{
                    "id": "question",
                    "decision_key": "question",
                    "decision_label": subtitle or question,
                    "question": question,
                    "kind": kind,
                    "subtitle": subtitle or "",
                    "options": options or [],
                }])
            if ssot_q_pairs:
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="pending",
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                )
        ssot_emit = (
            {"session": ssot_session, "ip": ssot_ip, "workflow": "ssot-gen", "source": "llm-ssot-qna"}
            if ssot_ip else {}
        )
        auto_mode = bool(
            _tools
            and hasattr(_tools, "_ask_user_exec_mode")
            and _tools._ask_user_exec_mode() == "auto-select"
            and hasattr(_tools, "auto_select_ask_user_answer")
        )
        if auto_mode:
            ans = _tools.auto_select_ask_user_answer(
                question=question,
                options=options or [],
                kind=kind,
                subtitle=subtitle or "",
                questions=questions,
            )
            if ssot_ip and ssot_q_pairs and isinstance(ans, dict):
                qa_answers: dict[str, dict[str, Any]] = {}
                if questions and isinstance(ans.get("answers"), list):
                    for (key, _label, q), qa in zip(ssot_q_pairs, ans.get("answers") or []):
                        qa_dict = qa if isinstance(qa, dict) else {}
                        qa_answers[key] = {
                            "answer": _answer_text(qa_dict, q),
                            "selected": qa_dict.get("selected") or [],
                            "custom": str(qa_dict.get("custom") or "").strip(),
                        }
                else:
                    key, _label, q = ssot_q_pairs[0]
                    qa_answers[key] = {
                        "answer": _answer_text(ans, q),
                        "selected": ans.get("selected") or [],
                        "custom": str(ans.get("custom") or "").strip(),
                    }
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                    source="llm-ssot-qna.auto_select",
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                )
            bridge.emit("ask_user_auto_selected", flow_id=flow_id, **ssot_emit)
            if questions and isinstance(ans, dict) and "answers" in ans:
                blocks = []
                for q, qa in zip(questions, ans.get("answers") or []):
                    label = (q.get("subtitle") or q.get("question", ""))[:40]
                    blocks.append(f"  • {label}\n    {_format_answer(qa, q.get('options') or [])}")
                return "Auto-selected answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
            return "Auto-selected answer: " + _format_answer(ans, options or [])
        bridge.open_question(flow_id)
        if questions:
            # Batched payload — frontend (workspace.jsx) detects the
            # `questions` array and switches to tabbed render.
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                questions=questions,
                **ssot_emit,
            )
        else:
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                question=question,
                kind=kind,
                subtitle=subtitle or "",
                options=options or [],
                **ssot_emit,
            )
        try:
            ans = bridge.wait_answer(flow_id, timeout=900)  # 15 min ceiling
        finally:
            bridge.close_question(flow_id)
        if ans is None:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match textual UI wording.
        if isinstance(ans, dict) and ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched answer format: {"answers": [{...}, ...]} aligned with questions.
        if questions and isinstance(ans, dict) and "answers" in ans:
            blocks = []
            qa_answers: dict[str, dict[str, Any]] = {}
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(
                    f"  • {label}\n    {_format_answer(qa, q.get('options'))}"
                )
            if ssot_ip and ssot_q_pairs:
                for (key, _label, q), qa in zip(ssot_q_pairs, ans.get("answers") or []):
                    qa_dict = qa if isinstance(qa, dict) else {}
                    qa_answers[key] = {
                        "answer": _answer_text(qa_dict, q),
                        "selected": qa_dict.get("selected") or [],
                        "custom": str(qa_dict.get("custom") or "").strip(),
                    }
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                )
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        if ssot_ip and ssot_q_pairs and isinstance(ans, dict):
            key, _label, q = ssot_q_pairs[0]
            _upsert_ssot_qa_items(
                ssot_ip,
                flow_id=flow_id,
                kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                q_pairs=ssot_q_pairs,
                status="approved",
                answers={
                    key: {
                        "answer": _answer_text(ans, q),
                        "selected": ans.get("selected") or [],
                        "custom": str(ans.get("custom") or "").strip(),
                    }
                },
                session=ssot_session,
            )
            bridge.emit(
                "ssot_qa_updated",
                ip=ssot_ip,
                workflow="ssot-gen",
                flow_id=flow_id,
                session=ssot_session,
            )
        return _format_answer(ans, options or [])

    if _tools and hasattr(_tools, "set_ask_user_callback"):
        _tools.set_ask_user_callback(_ask_user_cb)
    if _tools and hasattr(_tools, "set_record_ssot_qa_callback"):
        _tools.set_record_ssot_qa_callback(_record_ssot_qa_cb)

    def _run_agent():
        _sync_env_to_context()
        try:
            _main.chat_loop()
        except Exception as e:
            bridge.emit("error", message=str(e))
        finally:
            with bridge._agent_lock:
                bridge.agent_alive = False
            bridge.agent_running = False
            bridge.emit("agent_state", running=False)
            bridge.emit("done")

    def _start_agent_thread():
        ctx = contextvars.copy_context()
        threading.Thread(target=ctx.run, args=(_run_agent,), daemon=True).start()

    bridge.set_agent_starter(_start_agent_thread)
    # Process-per-session mode is lazy by design: the selected worker
    # should start when that workspace receives chat input, not as an
    # unrelated default worker during shared backend boot.
    _autostart_default = "0" if bridge._using_processes() else "1"
    if os.environ.get("ATLAS_AGENT_AUTOSTART", _autostart_default).strip().lower() not in {"0", "false", "off", "no"}:
        bridge.ensure_agent_alive()

    # Surface the source-repo path to the agent so it can locate
    # workflow/, rules/, templates/, etc. when running from a non-source
    # cwd (e.g. user runs `cd Custom_IP && python ../…/textual_main.py`).
    os.environ["ATLAS_SOURCE_ROOT"] = str(SOURCE_ROOT)
    os.environ["ATLAS_PROJECT_ROOT"] = str(PROJECT_ROOT)
    # Inject a system-prompt note so the LLM knows about both roots.
    _root_note = (
        f"\n\n[Atlas Runtime] You are running with cwd = {PROJECT_ROOT}. "
        f"All file reads/writes default to here. The source repo "
        f"(workflow templates, ssot-template.yaml, skills) lives at "
        f"{SOURCE_ROOT} — reference those by absolute path, not by "
        f"relative path from cwd. This source path is allowed for "
        f"read-only workflow tooling/scripts such as "
        f"$ATLAS_SOURCE_ROOT/workflow/...; keep generated IP artifacts "
        f"under cwd and do not ask the user to mount or copy workflow/ "
        f"into the project workspace."
    )
    try:
        # Append to whatever the existing system prompt builder produces
        # so the hint is part of every system-prompt rebuild (workspace
        # switches included).
        _orig_builder = getattr(_main, "_build_system_prompt_str", None)
        if callable(_orig_builder):
            def _patched_builder(*a, _orig=_orig_builder, _note=_root_note, **kw):
                return _orig(*a, **kw) + _note
            _main._build_system_prompt_str = _patched_builder
    except Exception:
        pass

    print(f"\n  ATLAS UI → http://{host}:{port}\n")
    print(
        "  [stdin] commands: 'status' (snapshot), 'heal' "
        "(force agent_running=False + drain inbox), 'sessions' "
        "(list .session/), 'help', 'quit'"
    )

    # ── Operator stdin command lane ───────────────────────────────────
    # Lets the user inspect / unstuck the running backend without
    # restarting. Reads one line at a time off stdin in a daemon
    # thread; each command prints its result to stdout. Designed for
    # the common case where a stuck chat_loop / hung WS leaves the
    # browser blank — operator types `heal`, gets the agent unstuck,
    # carries on. The xterm focus-event noise (`^[[O^[[I`) the user
    # was seeing in the terminal is also suppressed here because the
    # readline loop consumes those bytes silently.
    def _stdin_command_loop() -> None:
        import threading as _t
        while True:
            try:
                raw = sys.stdin.readline()
            except Exception:
                return
            if raw == "":
                return  # EOF — terminal closed
            cmd = raw.strip()
            # Suppress xterm focus / mouse escape sequences silently —
            # they show up as the literal text "[O" / "[I" / "[?1004h"
            # when the terminal sends ESC-prefixed bytes that python's
            # readline echoes through. Anything entirely non-alphanumeric
            # at the head is treated as terminal control noise.
            if not cmd or not cmd[0].isalnum():
                continue
            head = cmd.split(None, 1)[0].lower()
            if head in ("status", "stat"):
                try:
                    print(f"  [status] active_session={_active_session_value()!r} "
                          f"active_ip={_active_ip_value()!r} "
                          f"agent_running={bridge.agent_running} "
                          f"agent_alive={bridge.agent_alive} "
                          f"threads={len(_t.enumerate())}")
                except Exception as e:
                    print(f"  [status] error: {e}")
            elif head in ("heal", "unstuck"):
                try:
                    bridge.agent_running = False
                    bridge.request_stop()
                    print("  [heal] agent_running=False, _inbox preserved (slash items dropped, user prompts kept)")
                except Exception as e:
                    print(f"  [heal] error: {e}")
            elif head == "sessions":
                try:
                    sroot = PROJECT_ROOT / ".session"
                    if not sroot.is_dir():
                        print("  [sessions] no .session/ tree")
                        continue
                    print(f"  [sessions] root={sroot}")
                    for entry in sorted(sroot.rglob("conversation.json")):
                        rel = entry.parent.relative_to(sroot).as_posix()
                        size = entry.stat().st_size
                        print(f"    - {rel:60s} {size//1024}KB")
                except Exception as e:
                    print(f"  [sessions] error: {e}")
            elif head in ("help", "?"):
                print("  [help] status | heal | sessions | help | quit")
            elif head in ("quit", "exit"):
                print("  [quit] shutting down…")
                os._exit(0)
            else:
                print(f"  [?] unknown: {cmd!r} — try 'help'")

    try:
        threading.Thread(target=_stdin_command_loop, name="atlas-stdin",
                         daemon=True).start()
    except Exception:
        pass

    # ── Single-worker mode: spawn one main-loop worker on port 5601 ──────
    _single_worker_proc: "subprocess.Popen[bytes] | None" = None
    _single_worker_mode = (
        os.environ.get("ATLAS_SINGLE_MAIN_LOOP", "").strip().lower() not in ("", "0", "false", "no", "off")
        or os.environ.get("ATLAS_EXEC_MODE", "").strip().lower() == "single-worker"
    )
    if _single_worker_mode:
        import urllib.request as _urllib_req
        _sw_port = 5601
        _sw_env = {**os.environ}
        _sw_db = os.environ.get("ATLAS_DB_PATH", "")
        if _sw_db:
            _sw_env["ATLAS_DB_PATH"] = _sw_db
        _main_py = str(HERE / "main.py")
        _single_worker_proc = subprocess.Popen(
            [sys.executable, _main_py, "--serve", "--host", "127.0.0.1",
             "--port", str(_sw_port), "--all-workflows"],
            env=_sw_env,
        )
        print(f"[single-worker] spawned main-loop worker on port {_sw_port} (pid={_single_worker_proc.pid})")
        # Health probe: wait up to 10 s for the worker to become ready.
        _sw_ready = False
        _sw_deadline = 10.0
        _sw_start = __import__("time").monotonic()
        while __import__("time").monotonic() - _sw_start < _sw_deadline:
            try:
                with _urllib_req.urlopen(f"http://127.0.0.1:{_sw_port}/health", timeout=1) as _r:
                    if _r.status == 200:
                        _sw_ready = True
                        break
            except Exception:
                pass
            __import__("time").sleep(0.5)
        if _sw_ready:
            print(f"[single-worker] worker on port {_sw_port} is healthy")
        else:
            print(f"[single-worker] WARNING: worker on port {_sw_port} did not respond within {_sw_deadline}s")

        import atexit as _atexit

        def _terminate_single_worker(_proc=_single_worker_proc) -> None:
            if _proc and _proc.poll() is None:
                print(f"[single-worker] sending SIGTERM to pid={_proc.pid}")
                import signal as _signal
                try:
                    _proc.send_signal(_signal.SIGTERM)
                except Exception:
                    pass

        _atexit.register(_terminate_single_worker)
    else:
        print("[orchestrator-mode] expecting external 12-worker fleet on 5621-5632")

    uvicorn.run(app, host=host, port=port, log_level="warning", loop="asyncio", http="h11")


def main() -> None:
    ap = argparse.ArgumentParser(prog="atlas_ui",
                                  description="Atlas frontend for common_ai_agent")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--root", default=None,
                    help="Project root directory the backend serves "
                         "(.session/, IPs, file tree, …). Defaults to the "
                         "current working directory.")
    # Canonical 3-part session path: <session_id>/<ip>/<workflow>
    # All three default to "default" so the directory layout is uniform.
    ap.add_argument("-s", "--session", dest="session_id", default="default",
                    help="session_id segment (default: 'default')")
    ap.add_argument("-ip", "--ip", dest="ip", default="default",
                    help="ip segment (default: 'default')")
    ap.add_argument("-w", "--workflow", dest="workflow", default="default",
                    help="workflow segment (default: 'default')")
    ap.add_argument("--model", default="",
                    help="Runtime model/profile for the Atlas orchestrator "
                         "(e.g. gpt-5.5, deepseek, glm).")
    ap.add_argument("--effort", default="",
                    help="Runtime reasoning effort for the Atlas orchestrator "
                         "(none, low, medium, high, xhigh).")
    args = ap.parse_args()
    # Re-anchor PROJECT_ROOT before any request handler runs. Module-level
    # PROJECT_ROOT was computed from the import-time cwd; chdir + rebind
    # so /api/files, .session/, and friends all serve from --root.
    if args.root:
        target = Path(args.root).expanduser().resolve()
        if not target.is_dir():
            sys.exit(f"--root not found: {target}")
        os.chdir(str(target))
        global PROJECT_ROOT
        PROJECT_ROOT = target
    # Seed environment so all path resolvers see the canonical 3-part string.
    new_session = f"{args.session_id}/{args.ip}/{args.workflow}"
    _atlas_active_session_cv.set(new_session)
    _atlas_active_ip_cv.set(args.ip)
    _sync_env_to_context()
    os.environ.setdefault("ATLAS_DEFAULT_SESSION_ID", args.session_id)
    os.environ.setdefault("ATLAS_DEFAULT_WORKFLOW", args.workflow)
    orchestrator_model = (
        (args.model or "").strip()
        or os.environ.get("ATLAS_ORCHESTRATOR_MODEL", "").strip()
        or os.environ.get("ATLAS_MODEL", "").strip()
    )
    if orchestrator_model:
        _set_runtime_model(orchestrator_model)
    orchestrator_effort = (
        (args.effort or "").strip()
        or os.environ.get("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "").strip()
        or os.environ.get("ATLAS_REASONING_EFFORT", "").strip()
    )
    if orchestrator_effort:
        try:
            _set_runtime_reasoning_effort(_normalize_reasoning_effort(orchestrator_effort))
        except ValueError:
            print(f"[atlas_ui] ignoring unknown reasoning effort: {orchestrator_effort}", file=sys.stderr)
    run_atlas_ui(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
