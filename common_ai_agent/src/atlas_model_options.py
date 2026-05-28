"""Model options + reasoning-effort helpers — extracted from src/atlas_ui.py.

Self-contained: model picker rows, runtime-model setter, model-option key
canonicalization, reasoning-effort alias normalization, related constants.
Phase 5 of refactor/atlas-modular.
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Iterable


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

_MODEL_CATALOG_ENV_KEYS = ("LLM_MODEL_CATALOG", "LLM_MODEL_CHOICES", "ATLAS_MODEL_CATALOG")

_PROFILE_MODEL_OPTION_PREFIX = "profile:"

_RAW_MODEL_OPTION_PREFIX = "model:"

def _normalize_reasoning_effort(raw: Any) -> str:
    effort = _REASONING_EFFORT_ALIASES.get(str(raw or "").strip().lower(), "")
    if not effort:
        raise ValueError(f"unknown reasoning effort: {raw!r}")
    return effort

def _canonical_model_option_key(key: str) -> str:
    raw = str(key or "").strip()
    for group in (_MODEL_OPTION_KEYS, _BASE_MODEL_OPTION_KEYS, _LEGACY_MODEL_OPTION_KEYS):
        if raw in group:
            return raw
    return raw

def _catalog_model_option_rows(env_file: dict[str, str]) -> list[dict[str, str]]:
    raw_catalog = next((_env_value(env_file, key) for key in _MODEL_CATALOG_ENV_KEYS if _env_value(env_file, key)), "")
    rows: list[dict[str, str]] = []
    for raw_item in _split_model_catalog(raw_catalog):
        label = ""
        target = raw_item
        if "=" in raw_item:
            label, target = [part.strip() for part in raw_item.split("=", 1)]
        if not target:
            continue

        profile_name = ""
        if target.startswith(_PROFILE_MODEL_OPTION_PREFIX):
            profile_name = target[len(_PROFILE_MODEL_OPTION_PREFIX):].strip()
        elif _profile_from_env_values(target, env_file):
            profile_name = target

        if profile_name:
            profile = _profile_from_env_values(profile_name, env_file)
            if not profile:
                continue
            row = {
                "key": f"{_PROFILE_MODEL_OPTION_PREFIX}{profile_name}",
                "model": profile["model"],
                "profile": profile_name,
            }
            if label and label != profile["model"]:
                row["label"] = label
            rows.append(row)
            continue

        model = target[len(_RAW_MODEL_OPTION_PREFIX):].strip() if target.startswith(_RAW_MODEL_OPTION_PREFIX) else target
        if not model or model.lower().startswith("default"):
            continue
        row = {"key": f"{_RAW_MODEL_OPTION_PREFIX}{model}", "model": model}
        if label and label != model:
            row["label"] = label
        rows.append(row)
    return rows

def _hydrate_atlas_ui_helpers() -> None:
    """One-time backport of atlas_ui helpers Phase 5 didn't bring along.

    `_catalog_model_option_rows`, `_model_option_rows`, etc. are defined
    here but their bodies call into 7 atlas_ui helpers (_env_value,
    _read_env_file_values, _display_model_option_keys, _split_model_catalog,
    _model_option_value, _profile_from_env_values, _profile_name_from_option_key)
    using bare-name resolution. atlas_ui re-exports our public functions, so a
    top-level back-import would be circular. Hydration happens at first call
    (by then atlas_ui is fully loaded) and is idempotent.
    """
    g = globals()
    if g.get("_AUI_HYDRATED"):
        return
    from src import atlas_ui as _aui
    for name in (
        "_env_value", "_read_env_file_values", "_display_model_option_keys",
        "_split_model_catalog", "_model_option_value",
        "_profile_from_env_values", "_profile_name_from_option_key",
    ):
        if hasattr(_aui, name):
            g[name] = getattr(_aui, name)
    g["_AUI_HYDRATED"] = True


def _model_option_rows(active_model: str = "") -> list[dict[str, str]]:
    _hydrate_atlas_ui_helpers()
    env_file = _read_env_file_values()
    display_keys = _display_model_option_keys(env_file)

    rows: list[dict[str, str]] = []
    seen_models: set[str] = set()
    seen_keys: set[str] = set()
    for row in _catalog_model_option_rows(env_file):
        model = row.get("model", "")
        key = row.get("key", "")
        if not model or not key or key in seen_keys or model in seen_models:
            continue
        seen_keys.add(key)
        seen_models.add(model)
        rows.append(row)
    for index, key in enumerate(display_keys):
        model = _model_option_value(env_file, index)
        if not model or model in seen_models or model.lower().startswith("default"):
            continue
        seen_keys.add(key)
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
            profile_name = _profile_name_from_option_key(selected_key)
            if profile_name and callable(getattr(mod, "set_active_profile", None)) and mod.set_active_profile(profile_name):
                applied = True
            elif callable(getattr(mod, "set_active_profile", None)) and mod.set_active_profile(model):
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
