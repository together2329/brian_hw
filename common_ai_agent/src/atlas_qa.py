"""SSOT Q&A board helpers — extracted from src/atlas_ui.py.

Phases 10 / 10b / 10c of refactor/atlas-modular:
- Phase 10:  section-key→label mapping (pure consts + lookup).
- Phase 10b: factory `make_qa_helpers(**deps)` returning the simple I/O
  cluster (path/load/save/active_context).
- Phase 10c: pure utility helpers (status_group/qa_slug/q_pairs) +
  upsert(items) added to the factory.

Bigger helpers (view, sessions_view) extracted in subsequent phases.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


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


# Phase 10c: pure helpers (no closure deps).

def _status_group(status: str) -> str:
    """Map a raw status string to the high-level 'approved' / 'pending' bucket."""
    return "approved" if str(status or "").lower() in {"approved", "answered", "resolved"} else "pending"


def _qa_slug(value: str, fallback: str) -> str:
    """Slugify a decision key candidate; fall back when result is empty."""
    slug = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return (slug[:72] or fallback)


def _ssot_q_pairs_from_questions(
    questions: Optional[List[Dict[str, Any]]],
) -> List[Tuple[str, str, Dict[str, Any]]]:
    """Build (key, label, question) triples from an ask_user question list."""
    pairs: List[Tuple[str, str, Dict[str, Any]]] = []
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
    """Build the Q&A I/O + upsert helpers.

    Each kwarg replaces a closure capture from create_app(). The returned
    dict has the callables atlas_ui aliases back to its original names.
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

    def _upsert_ssot_qa_items(
        ip: str,
        *,
        flow_id: str,
        kind: str,
        q_pairs: List[Tuple[str, str, Dict[str, Any]]],
        status: str,
        answers: Optional[Dict[str, Dict[str, Any]]] = None,
        session: Optional[str] = None,
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

    return {
        "path": _ssot_qa_path,
        "load": _load_ssot_qa_items,
        "save": _save_ssot_qa_items,
        "active_context": _active_ssot_qa_context,
        "upsert": _upsert_ssot_qa_items,
    }
