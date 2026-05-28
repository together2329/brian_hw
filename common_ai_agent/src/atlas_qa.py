"""SSOT Q&A board helpers — extracted from src/atlas_ui.py.

Phases 10 / 10b of refactor/atlas-modular:
- Phase 10:  section-key→label mapping (pure consts).
- Phase 10b: factory `make_qa_helpers(**deps)` for the simple I/O cluster
  (path/load/save/active_context). Bigger helpers (upsert/view/
  sessions_view) extracted in subsequent phases.

The factory pattern keeps closures intact while moving the code out of
create_app(): each helper closes over its sibling helpers + the injected
deps, and atlas_ui aliases the returned callables back to the original
public names so call sites stay unchanged.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple


# Section-key → (section_id, display_label) — Phase 10 PoC.
_SSOT_QA_SECTIONS: dict = {
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


def _ssot_qa_section(decision_key: str) -> Tuple[str, str]:
    """Resolve a decision key to its (section_id, display_label) pair."""
    return _SSOT_QA_SECTIONS.get(
        decision_key,
        ("99_other", "99. Other / Open Decisions"),
    )


def make_qa_helpers(
    *,
    ssot_session_dir_fn: Callable[[str, Optional[str]], Path],
    legacy_ssot_session_dir_fn: Callable[[str], Path],
    normalize_session_name_fn: Callable[[str], str],
    project_root_fn: Callable[[], Path],
    active_session_value_fn: Callable[[], str],
    active_ip_value_fn: Callable[[], str],
    valid_ip_name_fn: Callable[[str], bool],
    canonical_session_fn: Callable[..., str],
) -> Dict[str, Callable]:
    """Build the simple Q&A I/O helpers (path/load/save/active_context).

    Each kwarg replaces a closure capture from create_app(). The returned
    dict has the 4 callables atlas_ui aliases back to its original names.
    """

    def _ssot_qa_path(ip: str, session: Optional[str] = None) -> Path:
        return ssot_session_dir_fn(ip, session) / "qa.json"

    def _load_ssot_qa_items(ip: str, session: Optional[str] = None) -> list:
        path = _ssot_qa_path(ip, session)
        if not path.is_file() and session:
            path = legacy_ssot_session_dir_fn(ip) / "qa.json"
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

    def _save_ssot_qa_items(ip: str, items: list, session: Optional[str] = None) -> None:
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

        # Compatibility bridge: pre-canonical SSOT QA at
        # .session/<ip>/ssot-gen/qa.json. Mirror default-owner sessions so old
        # UI/tests/tools keep reading the same cards (no cross-user leakage).
        clean = normalize_session_name_fn(str(session or ""))
        parts = [p for p in clean.split("/") if p]
        try:
            path_parts = [p for p in path.relative_to(project_root_fn() / ".session").parts if p]
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
        legacy_path = legacy_ssot_session_dir_fn(ip) / "qa.json"
        if mirror_legacy and legacy_path != path:
            legacy_path.parent.mkdir(parents=True, exist_ok=True)
            legacy_path.write_text(text, encoding="utf-8")

    def _active_ssot_qa_context() -> Tuple[str, str]:
        session = normalize_session_name_fn(str(active_session_value_fn() or ""))
        parts = [p for p in session.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and valid_ip_name_fn(parts[-2]):
            return parts[-2], session
        ip = str(active_ip_value_fn() or "").strip()
        if valid_ip_name_fn(ip):
            return ip, canonical_session_fn(ip)
        return "", ""

    return {
        "path": _ssot_qa_path,
        "load": _load_ssot_qa_items,
        "save": _save_ssot_qa_items,
        "active_context": _active_ssot_qa_context,
    }
