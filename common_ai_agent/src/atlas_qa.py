"""SSOT Q&A board helpers — extracted from src/atlas_ui.py.

Phases 10 / 10b / 10c / 10d of refactor/atlas-modular:
- Phase 10:  section-key→label mapping (pure consts + lookup).
- Phase 10b: factory `make_qa_helpers(**deps)` for path/load/save/active_context.
- Phase 10c: pure utility helpers (status_group/qa_slug/q_pairs) + upsert.
- Phase 10d: view + sessions_view (the heaviest renderers).

The factory pattern keeps closures intact while moving the code out of
create_app(): each helper closes over its sibling helpers + the injected
deps, and atlas_ui aliases the returned callables back to the original
public names so call sites stay unchanged.
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
    load_ssot_state_fn: Callable[[str], dict],
    ssot_decisions_fn: Callable[[str, dict], dict],
    required_decisions_fn: Callable[[], List[Tuple[str, str]]],
) -> Dict[str, Callable]:
    """Build the Q&A I/O + upsert + view helpers.

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

    def _ssot_qa_view(ip: str, session: Optional[str] = None) -> Dict[str, Any]:
        state = load_ssot_state_fn(ip)
        decisions = ssot_decisions_fn(ip, state)
        items = _load_ssot_qa_items(ip, session)
        required_index = {key: idx for idx, (key, _label) in enumerate(required_decisions_fn())}
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
        groups: Dict[str, Dict[str, Any]] = {}
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
        # Q&A is now driven only by real recorded questions/answers. The
        # nine SSOT decision names still guide /new-ip and /to-ssot prompts,
        # but they must not seed the UI with synthetic required boxes.
        requirement_rows: List[Dict[str, Any]] = []
        requirement_missing_keys: List[str] = []
        seen_requirement_keys: set = set()
        for idx, item in enumerate(items):
            key = str(item.get("decision_key") or item.get("flow_id") or "").strip()
            if not key:
                key = _qa_slug(str(item.get("question") or item.get("subtitle") or ""), f"qa_{idx + 1}")
            if key in seen_requirement_keys:
                continue
            seen_requirement_keys.add(key)
            is_approved = item.get("status_group") == "approved"
            if not is_approved:
                requirement_missing_keys.append(key)
            requirement_rows.append({
                "key": key,
                "label": str(item.get("decision_label") or item.get("question") or key),
                "status": "filled" if is_approved else "missing",
                "answer": str(item.get("answer") or ""),
            })
        imported_files: List[Dict[str, Any]] = []
        seen_import_paths: set = set()
        project_root = project_root_fn()

        def _add_imported_file(row: Dict[str, Any]) -> None:
            path = str(row.get("path") or row.get("md_path") or row.get("original_path") or "").strip()
            original = str(row.get("original_path") or row.get("path") or "").strip()
            md_path_str = str(row.get("md_path") or "").strip()
            if not path and not original:
                return
            # Dedup against every path the artifact knows about so a manifest
            # entry for foo.docx (with md_path=foo.md) doesn't get re-added by
            # the imports/ glob pass that also iterates foo.md as standalone.
            keys = [k for k in (path, original, md_path_str) if k]
            if any(k in seen_import_paths for k in keys):
                return
            for k in keys:
                seen_import_paths.add(k)
            name = str(row.get("name") or Path(original or path).name or "").strip()
            images = row.get("image_paths") if isinstance(row.get("image_paths"), list) else []
            for img in images:
                if isinstance(img, str) and img:
                    seen_import_paths.add(img)
            visuals = row.get("visual_paths") if isinstance(row.get("visual_paths"), list) else []
            for visual in visuals:
                if isinstance(visual, str) and visual:
                    seen_import_paths.add(visual)
            imported_files.append({
                "name": name,
                "bytes": int(row.get("bytes") or row.get("size_bytes") or 0),
                "path": path,
                "md_path": md_path_str or (path if path.endswith(".md") else ""),
                "original_path": original,
                "image_paths": images,
                "image_count": len(images),
                "visual_paths": visuals,
                "visual_count": len(visuals),
                "convert_error": str(row.get("convert_error") or ""),
            })

        manifest_path = project_root / ip / "req" / "import_manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8", errors="replace")) if manifest_path.is_file() else {}
        except Exception:
            manifest = {}
        for artifact in (manifest.get("artifacts") if isinstance(manifest, dict) else []) or []:
            if isinstance(artifact, dict):
                _add_imported_file(artifact)
        imports_dir = project_root / ip / "req" / "imports"
        originals_dir = imports_dir / "originals"
        # Build a lookup of every uploaded source document under
        # imports/originals/<stamp>_<idx>_<filename>. The .md sibling in
        # imports/ has the same <stamp>_<idx>_ prefix; matching by stem
        # collapses the docx/md pair into a single row whose displayed name
        # is the user's original upload filename (foo.docx, not <stamp>_<idx>_foo.md).
        original_by_stem: Dict[str, Path] = {}
        if originals_dir.is_dir():
            for orig_path in originals_dir.iterdir():
                if not orig_path.is_file():
                    continue
                stem = orig_path.stem
                original_by_stem[stem] = orig_path
                try:
                    rel = orig_path.relative_to(project_root).as_posix()
                except Exception:
                    rel = orig_path.as_posix()
                m = re.match(r"^(\d+_\d+)_(.+)$", orig_path.name)
                display_name = m.group(2) if m else orig_path.name
                # Pair the original with its md sibling (same stem in imports/)
                # so the UI shows the docx name and the agent still sees md_path.
                md_sibling = imports_dir / f"{stem}.md"
                md_rel = ""
                if md_sibling.is_file():
                    try:
                        md_rel = md_sibling.relative_to(project_root).as_posix()
                    except Exception:
                        md_rel = md_sibling.as_posix()
                _add_imported_file({
                    "name": display_name,
                    "bytes": orig_path.stat().st_size,
                    "path": rel,
                    "md_path": md_rel,
                    "original_path": rel,
                })
        if imports_dir.is_dir():
            for path in sorted(imports_dir.glob("*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:80]:
                if path.is_dir():
                    continue
                if not path.is_file():
                    continue
                try:
                    rel = path.relative_to(project_root).as_posix()
                except Exception:
                    rel = path.as_posix()
                if rel in seen_import_paths:
                    continue
                # Loose .md files whose <stamp>_<idx>_<name> stem matches an
                # entry under originals/ are already covered by the pass above.
                if path.suffix.lower() == ".md" and path.stem in original_by_stem:
                    continue
                _add_imported_file({
                    "name": path.name,
                    "bytes": path.stat().st_size,
                    "path": rel,
                    "md_path": rel if path.suffix.lower() == ".md" else "",
                    "original_path": rel,
                })
        return {
            "ip": ip,
            "workflow": "ssot-gen",
            "session": normalize_session_name_fn(str(session or active_session_value_fn() or canonical_session_fn(ip))),
            "approved": bool(state.get("approved")),
            "state_status": state.get("status") or "",
            "toc": toc,
            "sections": sections,
            "summary": {"total": approved + pending, "approved": approved, "pending": pending},
            "requirements": {
                "total": len(requirement_rows),
                "filled": sum(1 for row in requirement_rows if row.get("status") == "filled"),
                "missing": len(requirement_missing_keys),
                "items": requirement_rows,
                "missing_keys": requirement_missing_keys,
            },
            "items": items,
            "imports": imported_files,
            "path": str(_ssot_qa_path(ip, session).relative_to(project_root)),
        }

    def _ssot_qa_sessions_view() -> Dict[str, Any]:
        root = project_root_fn() / ".session"
        sessions: List[Dict[str, Any]] = []
        if not root.is_dir():
            return {"sessions": sessions, "count": 0}
        seen: set = set()
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
            if not valid_ip_name_fn(ip):
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
                state = load_ssot_state_fn(ip)
            # Keep the sessions list cheap: it's polled during first page load
            # and must never parse every IP's SSOT YAML. Some generated drafts
            # are very large or malformed enough for PyYAML to stall the
            # single uvicorn event loop for seconds. The detailed SSOT pane
            # still calls _ssot_qa_view() for one selected IP.
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
                "qa_path": str(qa_path.relative_to(project_root_fn())) if qa_path.exists() else "",
            })
        sessions.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        return {"sessions": sessions, "count": len(sessions)}

    return {
        "path": _ssot_qa_path,
        "load": _load_ssot_qa_items,
        "save": _save_ssot_qa_items,
        "active_context": _active_ssot_qa_context,
        "upsert": _upsert_ssot_qa_items,
        "view": _ssot_qa_view,
        "sessions_view": _ssot_qa_sessions_view,
    }
