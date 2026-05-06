#!/usr/bin/env python3
"""Derive RTL implementation TODOs directly from the SSOT.

The fixed ssot-rtl template is only a seed.  This script builds the real,
IP-sized implementation plan from the YAML SSOT so a complex IP naturally
produces dozens or hundreds of concrete RTL tasks.  It also emits a lightweight
static gate that rejects orphan function/cycle behavior and, after RTL exists,
checks that required implementation terms appear in the generated DUT sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTATION_SECTIONS = (
    "parameters",
    "io_list",
    "sub_modules",
    "registers",
    "memory",
    "interrupts",
    "fsm",
    "features",
    "dataflow",
    "function_model",
    "cycle_model",
    "timing",
    "power",
    "security",
    "error_handling",
    "debug_observability",
    "integration",
    "dft",
    "synthesis",
    "coding_rules",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "next_step_todos",
)

STATIC_EVIDENCE_CATEGORIES = (
    "function_model.",
    "cycle_model.",
    "registers.",
    "memory.",
    "interrupts.",
    "fsm.",
    "features.",
    "dataflow.",
    "error_handling.",
    "security.",
    "debug_observability.",
)

EVIDENCE_STOPWORDS = {
    "access",
    "according",
    "all",
    "an",
    "and",
    "any",
    "approved",
    "as",
    "be",
    "before",
    "behavior",
    "boundary",
    "clear",
    "clears",
    "control",
    "counter",
    "counters",
    "cycle",
    "effect",
    "effects",
    "error",
    "event",
    "events",
    "exactly",
    "externally",
    "feature",
    "field",
    "fields",
    "fl",
    "for",
    "from",
    "function_model",
    "gen",
    "implement",
    "input",
    "is",
    "listed",
    "model",
    "module",
    "non",
    "observable",
    "output",
    "pending",
    "preserve",
    "protocol",
    "retained",
    "rtl",
    "rule",
    "side",
    "state",
    "the",
    "to",
    "transaction",
    "with",
}

REFERENCE_STOPWORDS = {
    "backpressure",
    "cycle_model",
    "dataflow",
    "error_cases",
    "fsm",
    "function_model",
    "handshake_rules",
    "inputs",
    "invariants",
    "observability",
    "ordering",
    "output_rules",
    "outputs",
    "pipeline",
    "preconditions",
    "register_list",
    "registers",
    "side_effects",
    "state_updates",
    "state_variables",
    "test_requirements",
    "transactions",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(value: object, fallback: str = "item") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text:
        text = fallback
    if not re.match(r"^[A-Za-z_]", text):
        text = f"{fallback}_{text}"
    return text[:96]


def _present(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"none", "n/a", "na", "tbd", "todo"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": val} for key, val in value.items()]
    return [value]


RTL_WORKFLOW_NAMES = {"rtl", "rtl-gen", "ssot-rtl", "ssot-rtl-gen", "rtl-generation"}


def _norm_workflow(value: Any) -> str:
    return re.sub(r"[\s_]+", "-", str(value or "").strip().lower())


def _is_rtl_workflow(value: Any) -> bool:
    return _norm_workflow(value) in RTL_WORKFLOW_NAMES


def _ci_get(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    lower_to_key = {str(key).lower(): key for key in item}
    for key in keys:
        actual = lower_to_key.get(key.lower())
        if actual is not None:
            return item[actual]
    return None


def _criteria_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip(" -") for line in value.splitlines() if line.strip(" -")]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = _ci_get(item, "criteria", "criterion", "content", "description", "text", "name")
                out.append(_short_text(text if _present(text) else item))
            elif _present(item):
                out.append(str(item))
        return [item for item in out if item]
    if isinstance(value, dict):
        return [f"{key}: {_short_text(val)}" for key, val in value.items() if _present(val)]
    return [str(value)] if _present(value) else []


def _workflow_todo_refs(item: Any) -> list[str]:
    if not isinstance(item, dict):
        return []
    refs: list[str] = []
    for key in ("source_refs", "ssot_refs", "refs", "trace_refs", "source_ref", "ssot_ref", "ref"):
        raw = _ci_get(item, key)
        if isinstance(raw, str):
            refs.extend(part.strip() for part in re.split(r"[,;\n]+", raw) if part.strip())
        elif isinstance(raw, list):
            refs.extend(str(part).strip() for part in raw if str(part).strip())
    return sorted({ref for ref in refs if ref})


def _workflow_todo_entries(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []

    def add_from_sequence(source_base: str, value: Any, *, require_stage: bool) -> None:
        if isinstance(value, dict) and _present(_ci_get(value, "content", "title", "task", "name")):
            stage = _ci_get(value, "workflow", "stage", "step", "target", "agent")
            if not require_stage or not _present(stage) or _is_rtl_workflow(stage):
                entries.append((source_base, value))
            return
        for idx, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                item = {"content": item}
            stage = _ci_get(item, "workflow", "stage", "step", "target", "agent")
            if require_stage and _present(stage) and not _is_rtl_workflow(stage):
                continue
            if require_stage and not _present(stage):
                continue
            entries.append((f"{source_base}[{idx}]", item))

    for section in ("workflow_todos", "next_step_todos"):
        root = doc.get(section)
        if isinstance(root, dict):
            for key, value in root.items():
                if _is_rtl_workflow(key):
                    add_from_sequence(f"{section}.{key}", value, require_stage=False)
            for key in ("todos", "items", "tasks"):
                if key in root:
                    add_from_sequence(f"{section}.{key}", root.get(key), require_stage=True)
        elif isinstance(root, list):
            add_from_sequence(section, root, require_stage=True)

    flow = doc.get("generation_flow")
    if isinstance(flow, dict):
        for key in ("workflow_todos", "next_step_todos", "todos", "tasks"):
            if key in flow:
                add_from_sequence(f"generation_flow.{key}", flow.get(key), require_stage=True)
        for step_idx, step in enumerate(_as_list(flow.get("steps"))):
            if not isinstance(step, dict):
                continue
            name = _ci_get(step, "name", "workflow", "stage")
            if not _is_rtl_workflow(name) and "rtl" not in _norm_workflow(name):
                continue
            for key in ("todos", "tasks", "next_step_todos"):
                if key in step:
                    add_from_sequence(f"generation_flow.steps[{step_idx}].{key}", step.get(key), require_stage=False)
    return entries


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json_sha256(path: Path, *, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or {"generated_at"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in volatile_keys
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_ssot(root: Path, ip: str) -> tuple[Path, dict[str, Any]]:
    path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"[derive_rtl_todos] missing SSOT: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(data, dict):
        raise SystemExit("[derive_rtl_todos] SSOT top-level must be a mapping")
    return path, data


def _top_name(doc: dict[str, Any], fallback: str) -> str:
    top = doc.get("top_module") or fallback
    if isinstance(top, dict):
        top = top.get("name") or fallback
    return str(top or fallback)


def _module_file(ip: str, top: str, module: dict[str, Any]) -> str:
    rel = str(module.get("file") or "").strip()
    if rel:
        return rel
    name = str(module.get("name") or top or ip)
    return f"rtl/{_slug(name)}.sv"


def _module_contract_refs(module: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "implements",
        "source_sections",
        "ssot_refs",
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
    ):
        value = module.get(key)
        if isinstance(value, str):
            refs.extend(item.strip() for item in re.split(r"[,;\n]+", value) if item.strip())
        elif isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            refs.extend(str(key2).strip() for key2 in value if str(key2).strip())
    return sorted({ref for ref in refs if ref})


def _active_modules(doc: dict[str, Any], ip: str, top: str) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    raw = doc.get("sub_modules")
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            ownership = str(item.get("ownership") or "manifest").lower()
            if ownership in {"child_ssot", "conceptual", "coverage", "verification"} or item.get("ssot"):
                continue
            if item.get("rtl_emit") is False:
                continue
            name = str(item.get("name") or Path(_module_file(ip, top, item)).stem or top)
            modules.append({
                "name": name,
                "file": _module_file(ip, top, item),
                "refs": _module_contract_refs(item),
                "raw": item,
            })
    if not modules:
        modules.append({"name": top, "file": f"rtl/{top}.sv", "refs": ["top_module", "function_model", "cycle_model"], "raw": {}})
    return modules


def _ref_is_covered(ref: str, owner_ref: str) -> bool:
    return ref == owner_ref or ref.startswith(owner_ref + ".") or owner_ref.startswith(ref + ".")


def _owner_for(ref: str, modules: list[dict[str, Any]], top: str) -> dict[str, str]:
    matches: list[dict[str, Any]] = []
    for module in modules:
        refs = module.get("refs") if isinstance(module.get("refs"), list) else []
        if any(_ref_is_covered(ref, str(owner_ref)) for owner_ref in refs):
            matches.append(module)
    if matches:
        module = matches[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": str((module.get("refs") or [""])[0])}
    if len(modules) == 1:
        module = modules[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": "single_owner"}
    top_module = next((m for m in modules if str(m.get("name")) == top or Path(str(m.get("file"))).stem == top), None)
    if top_module is not None:
        return {"module": str(top_module["name"]), "file": str(top_module["file"]), "matched_ref": "top_fallback"}
    return {"module": "", "file": "", "matched_ref": ""}


def _looks_like_design_token(token: str) -> bool:
    text = str(token or "").strip()
    if len(text) <= 1:
        return False
    lower = text.lower()
    if lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
        return False
    if re.fullmatch(r".*_\d+", text):
        return False
    return bool("_" in text or re.search(r"[A-Z]", text) or re.search(r"\d", text))


def _split_design_token(token: str) -> set[str]:
    out = {token}
    if "_" in token:
        for part in token.split("_"):
            if _looks_like_design_token(part) or part.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS:
                out.add(part)
    return {
        item
        for item in out
        if _looks_like_design_token(item)
        or ("_" not in item and len(item) > 1 and item.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS)
    }


DIRECT_STRING_EVIDENCE_CATEGORIES = {
    "cycle_model.observability",
    "registers.field",
    "fsm.state",
    "fsm.transition",
}

NAME_EVIDENCE_CATEGORIES = {
    "function_model.output_rule",
    "function_model.state_update",
    "function_model.state_variable",
    "registers.register",
    "registers.field",
    "registers.architectural_state",
    "memory.instances",
    "interrupts.sources",
    "cycle_model.handshake_rules",
    "cycle_model.pipeline",
    "cycle_model.observability",
    "fsm.state",
    "fsm.transition",
}


def _evidence_terms(category: str, source_ref: str, value: Any) -> list[str]:
    terms: set[str] = set()

    def visit(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            identity_keys = ("field", "signal", "port", "state", "output", "event", "stage", "register", "from", "to")
            if category in NAME_EVIDENCE_CATEGORIES:
                identity_keys = ("id", *identity_keys)
            if category == "workflow_todo.rtl_gen":
                identity_keys = ("id", "content", "detail", "criteria", "source_refs", "owner_module", "owner_file", *identity_keys)
            for key in identity_keys:
                if _present(value.get(key)):
                    visit(value.get(key))
            for key in ("expr", "expression", "condition"):
                if isinstance(value.get(key), str):
                    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", value[key]):
                        if _looks_like_design_token(token):
                            terms.update(_split_design_token(token))
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        text = str(value)
        for quoted in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", text):
            if _looks_like_design_token(quoted):
                terms.update(_split_design_token(quoted))
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            if category in DIRECT_STRING_EVIDENCE_CATEGORIES and token.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS:
                terms.add(token)
            elif "_" in token and _looks_like_design_token(token):
                terms.update(_split_design_token(token))

    visit(value)
    terms = {term for term in terms if term.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS}
    return sorted(terms)[:16]


def _short_text(value: Any, limit: int = 120) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _ssot_context(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"value": _short_text(value)} if _present(value) else {}
    context: dict[str, str] = {}
    for key in (
        "id",
        "name",
        "field",
        "register",
        "port",
        "signal",
        "state",
        "output",
        "event",
        "stage",
        "from",
        "to",
        "condition",
        "expr",
        "expression",
        "value",
        "width",
        "depth",
        "reset",
        "access",
        "offset",
        "address",
        "cycle",
        "latency",
        "direction",
        "clear",
        "mask",
        "expected",
    ):
        if _present(value.get(key)):
            context[key] = _short_text(value.get(key))
    return context


def _append_detail_context(detail: str, *, source_ref: str, owner: dict[str, str], value: Any) -> str:
    lines = [detail.rstrip()]
    lines.append(f"SSOT ref: {source_ref}.")
    if owner.get("module") or owner.get("file"):
        lines.append(
            "Owner: "
            f"{owner.get('module') or '(unassigned)'}"
            f" in {owner.get('file') or '(unassigned file)'}"
            f" via {owner.get('matched_ref') or 'no match'}."
        )
    context = _ssot_context(value)
    if context:
        rendered = "; ".join(f"{key}={val}" for key, val in context.items())
        lines.append(f"SSOT item context: {rendered}.")
    return "\n".join(lines)


def _specific_criteria(category: str, source_ref: str, value: Any, owner: dict[str, str]) -> list[str]:
    criteria: list[str] = [
        f"Traceability keeps source_ref {source_ref}",
    ]
    if owner.get("file"):
        criteria.append(f"Primary implementation evidence is in {owner['file']}")
    context = _ssot_context(value)
    name = context.get("name") or context.get("id") or context.get("field") or context.get("port") or source_ref
    if context.get("width"):
        criteria.append(f"{name} width matches SSOT value {context['width']}")
    if "reset" in context:
        criteria.append(f"{name} reset behavior matches SSOT value {context['reset']}")
    if context.get("access"):
        criteria.append(f"{name} access policy {context['access']} is implemented without read/write shortcuts")
    if context.get("offset") or context.get("address"):
        criteria.append(f"{name} decode uses SSOT address/offset {context.get('offset') or context.get('address')}")
    if context.get("expr") or context.get("expression"):
        criteria.append(f"{name} RTL expression implements SSOT expression {context.get('expr') or context.get('expression')}")
    if context.get("port"):
        criteria.append(f"DUT port {context['port']} is the implementation/observation point for {name}")
    if context.get("direction"):
        criteria.append(f"{name} port direction remains {context['direction']}")
    if context.get("condition"):
        criteria.append(f"{name} condition is implemented as RTL control logic: {context['condition']}")
    if context.get("from") or context.get("to"):
        criteria.append(f"{name} transition path {context.get('from', '?')} -> {context.get('to', '?')} is encoded or explicitly proven equivalent")
    if context.get("cycle") or context.get("latency"):
        criteria.append(f"{name} timing uses SSOT cycle/latency {context.get('cycle') or context.get('latency')}")
    if context.get("depth"):
        criteria.append(f"{name} storage depth matches SSOT value {context['depth']}")
    if context.get("clear"):
        criteria.append(f"{name} clear behavior matches SSOT clear policy {context['clear']}")
    if context.get("mask"):
        criteria.append(f"{name} mask behavior matches SSOT mask policy {context['mask']}")
    if context.get("expected"):
        criteria.append(f"Downstream checker compares RTL-observed behavior against expected result: {context['expected']}")

    if category == "registers.field":
        criteria.extend([
            f"{name} readback returns implemented RTL state when readable",
            f"{name} write/clear side effects are connected to owning control/status logic",
        ])
    elif category == "function_model.output_rule":
        criteria.append(f"{name} is not implemented only in FunctionalModel or scoreboard code")
    elif category == "function_model.state_update":
        criteria.append(f"{name} updates exactly once at the SSOT-defined transaction acceptance point")
    elif category.startswith("cycle_model."):
        criteria.append(f"{name} appears in RTL sample/hold/FSM/ready-valid timing, not only in TB")
    elif category == "coverage.functional_bin":
        criteria.append(f"{name} can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals")

    seen: set[str] = set()
    out: list[str] = []
    for item in criteria:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _task(
    tasks: list[dict[str, Any]],
    *,
    category: str,
    source_ref: str,
    title: str,
    detail: str,
    criteria: list[str],
    owner: dict[str, str],
    priority: str = "high",
    value: Any = None,
    required: bool = True,
) -> None:
    index = len(tasks) + 1
    requires_static = category.startswith(STATIC_EVIDENCE_CATEGORIES) or category == "workflow_todo.rtl_gen"
    terms = _evidence_terms(category, source_ref, value)
    enriched_detail = _append_detail_context(detail, source_ref=source_ref, owner=owner, value=value)
    enriched_criteria: list[str] = []
    seen_criteria: set[str] = set()
    for item in [*criteria, *_specific_criteria(category, source_ref, value, owner)]:
        if item not in seen_criteria:
            enriched_criteria.append(item)
            seen_criteria.add(item)
    tasks.append({
        "id": f"RTL-{index:04d}",
        "category": category,
        "source_ref": source_ref,
        "content": title,
        "detail": enriched_detail,
        "criteria": enriched_criteria,
        "owner_module": owner.get("module") or "",
        "owner_file": owner.get("file") or "",
        "owner_match": owner.get("matched_ref") or "",
        "ssot_refs": [source_ref],
        "ssot_context": _ssot_context(value),
        "evidence_terms": terms,
        "requires_static_rtl_evidence": requires_static and bool(terms),
        "required": required,
        "priority": priority,
    })


def _item_name(item: Any, idx: int, fallback: str = "item") -> str:
    if isinstance(item, dict):
        for key in ("id", "name", "field", "signal", "port", "state", "stage", "event", "register"):
            if _present(item.get(key)):
                return str(item[key])
    return f"{fallback}_{idx}"


def _add_base_tasks(tasks: list[dict[str, Any]], ip: str, top: str, owner: dict[str, str]) -> None:
    _task(
        tasks,
        category="rtl_flow.seed",
        source_ref="top_module",
        title="Read SSOT and build dynamic RTL implementation ledger",
        detail="Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.",
        criteria=[
            "rtl_todo_plan.json was regenerated from the current SSOT",
            "Every required task in the plan is either implemented, evidenced, or escalated",
            "No IP-specific fixed template is used as the source of truth",
        ],
        owner=owner,
        value={"ip": ip, "top": top},
    )
    _task(
        tasks,
        category="rtl_flow.top",
        source_ref="io_list",
        title="Implement top-level ports, reset, and filelist integration",
        detail="The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.",
        criteria=[
            "Top module name matches SSOT top_module",
            "Every SSOT top-level port appears with matching direction and width",
            "Filelist contains all LLM-authored RTL sources and no stale sources",
        ],
        owner=owner,
        value=top,
    )


def _add_rtl_gate_todo_tasks(tasks: list[dict[str, Any]], owner: dict[str, str]) -> None:
    gate_specs = [
        {
            "kind": "ssot_required_sections",
            "source_ref": "quality_gates.rtl_gen.ssot_required_sections",
            "content": "Gate: SSOT function_model and cycle_model are present before RTL generation",
            "detail": "rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.",
            "criteria": [
                "function_model is present and non-empty in the SSOT",
                "cycle_model is present and non-empty in the SSOT",
                "Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL",
            ],
            "artifact": "yaml/<ip>.ssot.yaml",
        },
        {
            "kind": "ssot_workflow_todo_format",
            "source_ref": "quality_gates.rtl_gen.workflow_todo_contract",
            "content": "Gate: SSOT-authored rtl-gen workflow TODOs are well formed",
            "detail": "Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.",
            "criteria": [
                "Every workflow_todos.rtl-gen item has content",
                "Every workflow_todos.rtl-gen item has detail",
                "Every workflow_todos.rtl-gen item has at least one criteria entry",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "owner_traceability",
            "source_ref": "quality_gates.rtl_gen.owner_traceability",
            "content": "Gate: every SSOT-derived RTL behavior has an owner module",
            "detail": "Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.",
            "criteria": [
                "No required function_model task is orphaned",
                "No required cycle_model task is orphaned",
                "No required register/dataflow/FSM task is orphaned",
                "Owner module and owner file are recorded in rtl_todo_plan.json",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "common_ai_agent_authoring",
            "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
            "content": "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
            "detail": "RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.",
            "criteria": [
                "rtl/rtl_authoring_provenance.json exists",
                "provenance agent is common_ai_agent",
                "provenance workflow is rtl-gen",
                "provenance surface is atlas_ui, textual_ui, or headless_common_engine",
                "provenance todo_plan_sha256 matches the current rtl_todo_plan.json",
                "provenance rtl_files lists every SSOT manifest RTL file",
            ],
            "artifact": "rtl/rtl_authoring_provenance.json",
        },
        {
            "kind": "static_rtl_evidence",
            "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
            "content": "Gate: required SSOT behavior has static DUT RTL evidence after audit",
            "detail": "After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.",
            "criteria": [
                "derive_rtl_todos.py --audit-rtl ran after the final RTL edit",
                "rtl_todo_plan.json static_rtl_evidence.missing is zero",
                "No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "dut_compile",
            "source_ref": "quality_gates.rtl_gen.dut_compile",
            "content": "Gate: DUT-only RTL compile report passes after the final RTL edit",
            "detail": "Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.",
            "criteria": [
                "rtl/rtl_compile.json exists",
                "rtl_compile.json reports dut_only=true",
                "rtl_compile.json passed=true with zero errors, diagnostics, and style violations",
            ],
            "artifact": "rtl/rtl_compile.json",
        },
        {
            "kind": "dut_lint",
            "source_ref": "quality_gates.rtl_gen.dut_lint",
            "content": "Gate: DUT-only lint report passes after the final RTL edit",
            "detail": "Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.",
            "criteria": [
                "lint/dut_lint.json exists",
                "dut_lint.json reports dut_only=true",
                "dut_lint.json passed=true with zero errors and zero warnings",
                "No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver",
            ],
            "artifact": "lint/dut_lint.json",
        },
        {
            "kind": "dynamic_todo_closure",
            "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
            "content": "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS",
            "detail": "rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.",
            "criteria": [
                "Every required non-closure task has todo_completion.status=pass",
                "open_required_todos is zero",
                "all_required_todos_pass is true",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
    ]
    for spec in gate_specs:
        _task(
            tasks,
            category="rtl_gate.rtl_gen",
            source_ref=spec["source_ref"],
            title=spec["content"],
            detail=spec["detail"],
            criteria=spec["criteria"],
            owner=owner,
            value={"gate_check": spec["kind"], "artifact": spec["artifact"]},
            priority="critical",
        )
        task = tasks[-1]
        task["gate_todo"] = {
            "stage": "rtl-gen",
            "kind": spec["kind"],
            "artifact": spec["artifact"],
        }
        task["ssot_refs"] = sorted({spec["source_ref"], "quality_gates"})


def _add_parameter_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for idx, item in enumerate(_as_list(doc.get("parameters"))):
        name = _item_name(item, idx, "param")
        ref = f"parameters.{_slug(name)}"
        _task(
            tasks,
            category="parameters.item",
            source_ref=ref,
            title=f"Implement parameter {name}",
            detail="Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.",
            criteria=[
                "Parameter default/value matches SSOT",
                "Parameter-derived widths are implemented outside procedural part-selects",
                "Compile/lint evidence covers the parameterized form",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
            priority="normal",
        )


def _iter_io_ports(io: Any) -> list[tuple[str, dict[str, Any]]]:
    ports: list[tuple[str, dict[str, Any]]] = []
    if not isinstance(io, dict):
        return ports
    for group_key in ("clock_domains", "resets", "interfaces"):
        for group_idx, group in enumerate(_as_list(io.get(group_key))):
            if not isinstance(group, dict):
                continue
            for idx, port in enumerate(_as_list(group.get("ports"))):
                if isinstance(port, dict) and _present(port.get("name")):
                    base = str(group.get("name") or group.get("type") or group_key)
                    ports.append((f"io_list.{group_key}.{_slug(base)}.ports.{_slug(port.get('name'))}", port))
                elif _present(port):
                    ports.append((f"io_list.{group_key}.{group_idx}.ports.{idx}", {"name": str(port)}))
    return ports


def _add_io_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for ref, port in _iter_io_ports(doc.get("io_list")):
        name = str(port.get("name") or ref.rsplit(".", 1)[-1])
        _task(
            tasks,
            category="io_list.port",
            source_ref=ref,
            title=f"Implement and connect port {name}",
            detail="The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.",
            criteria=[
                "RTL declaration matches SSOT direction and width",
                "Active input controls are consumed by behavior or explicitly justified",
                "Active outputs are driven by implemented logic, not placeholder constants",
            ],
            owner=_owner_for(ref, modules, top),
            value=port,
            priority="normal",
        )


def _add_function_model_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        return
    for idx, item in enumerate(_as_list(fm.get("state_variables"))):
        name = _item_name(item, idx, "state")
        ref = f"function_model.state_variables.{_slug(name)}"
        _task(
            tasks,
            category="function_model.state_variable",
            source_ref=ref,
            title=f"Implement RTL state owner for FL state {name}",
            detail="Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.",
            criteria=[
                "State has a flop/register/memory owner in RTL",
                "Reset value matches SSOT",
                "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
        )
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            tx = {"name": str(tx)}
        tx_name = _item_name(tx, idx, "transaction")
        base = f"function_model.transactions.{_slug(tx.get('id') or tx_name)}"
        _task(
            tasks,
            category="function_model.transaction",
            source_ref=base,
            title=f"Implement transaction {tx_name}",
            detail="Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.",
            criteria=[
                "Acceptance/precondition logic is explicit in RTL",
                "All outputs and side effects occur exactly once per accepted transaction",
                "The transaction is covered by equivalence goals and scoreboard observations downstream",
            ],
            owner=_owner_for(base, modules, top),
            value=tx,
        )
        for key, category, label in (
            ("preconditions", "function_model.precondition", "precondition"),
            ("inputs", "function_model.input", "input"),
            ("outputs", "function_model.output", "output"),
            ("output_rules", "function_model.output_rule", "output rule"),
            ("state_updates", "function_model.state_update", "state update"),
            ("side_effects", "function_model.side_effect", "side effect"),
            ("counter_rules", "function_model.counter_rule", "counter rule"),
            ("event_rules", "function_model.event_rule", "event rule"),
            ("error_cases", "function_model.error_case", "error case"),
        ):
            for sub_idx, sub in enumerate(_as_list(tx.get(key))):
                sub_name = _item_name(sub, sub_idx, label.replace(" ", "_"))
                ref = f"{base}.{key}.{_slug(sub_name, 'entry')}"
                _task(
                    tasks,
                    category=category,
                    source_ref=ref,
                    title=f"Implement {label} for {tx_name}: {sub_name}",
                    detail="This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.",
                    criteria=[
                        "RTL owner logic is identifiable for this SSOT leaf",
                        "Reset/enable/error behavior is consistent with the parent transaction",
                        "Downstream equivalence/coverage can observe this behavior",
                    ],
                    owner=_owner_for(ref, modules, top),
                    value=sub,
                )
    for idx, item in enumerate(_as_list(fm.get("invariants"))):
        name = _item_name(item, idx, "invariant")
        ref = f"function_model.invariants.{_slug(name)}"
        _task(
            tasks,
            category="function_model.invariant",
            source_ref=ref,
            title=f"Preserve FL invariant {name}",
            detail="Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.",
            criteria=[
                "RTL behavior cannot violate the invariant in normal operation",
                "If the invariant is verification-only, the SSOT names that evidence owner",
                "Coverage/equivalence references this invariant when observable",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
        )


def _add_cycle_model_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    cm = doc.get("cycle_model")
    if not isinstance(cm, dict):
        return
    for key in ("clock", "reset", "latency"):
        if _present(cm.get(key)):
            ref = f"cycle_model.{key}"
            _task(
                tasks,
                category=f"cycle_model.{key}",
                source_ref=ref,
                title=f"Implement cycle-model {key}",
                detail="Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.",
                criteria=[
                    "RTL sequential logic uses the SSOT clock/reset phase",
                    "Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence",
                    "Downstream scoreboard samples the same acceptance/result phase",
                ],
                owner=_owner_for(ref, modules, top),
                value=cm.get(key),
            )
    for key, label in (
        ("handshake_rules", "handshake rule"),
        ("pipeline", "pipeline stage"),
        ("ordering", "ordering rule"),
        ("backpressure", "backpressure rule"),
        ("observability", "observability signal"),
        ("arbitration", "arbitration rule"),
        ("stall_rules", "stall rule"),
        ("completion", "completion rule"),
        ("timeouts", "timeout rule"),
    ):
        for idx, item in enumerate(_as_list(cm.get(key))):
            name = _item_name(item, idx, label.replace(" ", "_"))
            ref = f"cycle_model.{key}.{_slug(name)}"
            _task(
                tasks,
                category=f"cycle_model.{key}",
                source_ref=ref,
                title=f"Implement {label}: {name}",
                detail="Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.",
                criteria=[
                    "RTL contains the control/state/handshake logic for this cycle rule",
                    "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
                    "TB scoreboard/coverage can observe the rule at the declared phase",
                ],
                owner=_owner_for(ref, modules, top),
                value=item,
            )


def _register_fields(reg: Any) -> list[tuple[str, Any]]:
    if not isinstance(reg, dict):
        return []
    raw = reg.get("fields")
    out: list[tuple[str, Any]] = []
    if isinstance(raw, dict):
        for name, value in raw.items():
            item = value if isinstance(value, dict) else {"value": value}
            item.setdefault("name", name)
            out.append((str(name), item))
    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            name = _item_name(item, idx, "field")
            out.append((name, item))
    return out


def _add_register_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    regs = doc.get("registers")
    if not isinstance(regs, dict):
        return
    for idx, reg in enumerate(_as_list(regs.get("register_list"))):
        if not isinstance(reg, dict):
            reg = {"name": str(reg)}
        name = _item_name(reg, idx, "register")
        ref = f"registers.register_list.{_slug(name)}"
        _task(
            tasks,
            category="registers.register",
            source_ref=ref,
            title=f"Implement CSR/register {name}",
            detail="Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.",
            criteria=[
                "Address/decode behavior matches SSOT",
                "Readable fields return RTL state, not a constant placeholder",
                "Write semantics and illegal access response match SSOT",
            ],
            owner=_owner_for(ref, modules, top),
            value=reg,
        )
        for field_name, field in _register_fields(reg):
            field_ref = f"{ref}.fields.{_slug(field_name)}"
            _task(
                tasks,
                category="registers.field",
                source_ref=field_ref,
                title=f"Implement field {name}.{field_name}",
                detail="Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.",
                criteria=[
                    "Field reset/access policy matches SSOT",
                    "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
                    "Field side effects are connected to owning control/status logic",
                ],
                owner=_owner_for(field_ref, modules, top),
                value=field,
            )
    for idx, item in enumerate(_as_list(regs.get("architectural_state"))):
        name = _item_name(item, idx, "architectural_state")
        ref = f"registers.architectural_state.{_slug(name)}"
        _task(
            tasks,
            category="registers.architectural_state",
            source_ref=ref,
            title=f"Implement architectural state {name}",
            detail="Architectural state listed outside the register map still needs RTL storage and reset/update ownership.",
            criteria=[
                "State storage is present in RTL",
                "Reset/update behavior matches SSOT",
                "State is observable if required by registers/debug/coverage",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
        )


def _add_section_list_tasks(
    tasks: list[dict[str, Any]],
    doc: dict[str, Any],
    modules: list[dict[str, Any]],
    top: str,
    *,
    section: str,
    keys: tuple[str, ...],
    label: str,
    category_prefix: str | None = None,
) -> None:
    value = doc.get(section)
    if not isinstance(value, dict):
        return
    category_prefix = category_prefix or section
    for key in keys:
        for idx, item in enumerate(_as_list(value.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or label)
            ref = f"{section}.{key}.{_slug(name)}"
            _task(
                tasks,
                category=f"{category_prefix}.{key}",
                source_ref=ref,
                title=f"Implement {label} {name}",
                detail=f"This SSOT {section}.{key} item must map to RTL behavior, integration evidence, or a precise blocker.",
                criteria=[
                    "RTL owner/evidence is named for this SSOT item",
                    "Behavior is not represented only by comments or TB code",
                    "Downstream verification can observe or justify the item",
                ],
                owner=_owner_for(ref, modules, top),
                value=item,
            )


def _add_feature_dataflow_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for idx, feature in enumerate(_as_list(doc.get("features"))):
        name = _item_name(feature, idx, "feature")
        ref = f"features.{_slug(name)}"
        _task(
            tasks,
            category="features.item",
            source_ref=ref,
            title=f"Implement feature {name}",
            detail="Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.",
            criteria=[
                "Feature trigger/control/data behavior has RTL owner logic",
                "Feature observability and error behavior match SSOT",
                "Feature is covered by function/cycle/coverage tasks or explicitly blocked",
            ],
            owner=_owner_for(ref, modules, top),
            value=feature,
        )
    dataflow = doc.get("dataflow")
    if isinstance(dataflow, dict):
        for key in ("source", "sequence", "sinks", "ordering", "transforms", "notes"):
            for idx, item in enumerate(_as_list(dataflow.get(key))):
                name = _item_name(item, idx, key)
                ref = f"dataflow.{key}.{_slug(name)}"
                _task(
                    tasks,
                    category=f"dataflow.{key}",
                    source_ref=ref,
                    title=f"Implement dataflow {key}: {name}",
                    detail="Dataflow steps must be reflected in real datapath/control/storage logic.",
                    criteria=[
                        "RTL data/control path implements the described step",
                        "Ordering/backpressure is consistent with cycle_model",
                        "Downstream checks can observe the result or side effect",
                    ],
                    owner=_owner_for(ref, modules, top),
                    value=item,
                )


def _add_fsm_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    fsm = doc.get("fsm")
    if not isinstance(fsm, dict):
        return
    controls = []
    if isinstance(fsm.get("control"), dict):
        controls.append(("control", fsm["control"]))
    for key, value in fsm.items():
        if isinstance(value, dict) and key != "control":
            controls.append((key, value))
    if not controls and fsm:
        controls.append(("fsm", fsm))
    for ctrl_name, ctrl in controls:
        for idx, state in enumerate(_as_list(ctrl.get("states"))):
            name = _item_name(state, idx, "state")
            ref = f"fsm.{_slug(ctrl_name)}.states.{_slug(name)}"
            _task(
                tasks,
                category="fsm.state",
                source_ref=ref,
                title=f"Implement FSM state {ctrl_name}.{name}",
                detail="Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.",
                criteria=[
                    "State is encoded/reachable or explicitly replaced by equivalent logic",
                    "Reset/entry/exit behavior matches SSOT",
                    "Coverage can observe the state or equivalent condition",
                ],
                owner=_owner_for(ref, modules, top),
                value=state,
            )
        for idx, transition in enumerate(_as_list(ctrl.get("transitions"))):
            name = _item_name(transition, idx, "transition")
            ref = f"fsm.{_slug(ctrl_name)}.transitions.{_slug(name)}"
            _task(
                tasks,
                category="fsm.transition",
                source_ref=ref,
                title=f"Implement FSM transition {ctrl_name}.{name}",
                detail="Transition condition, action, and timing must be implemented in RTL and covered downstream.",
                criteria=[
                    "Transition condition is present in RTL control logic",
                    "Transition action/state update is implemented",
                    "Illegal/missing transition behavior is handled per SSOT",
                ],
                owner=_owner_for(ref, modules, top),
                value=transition,
            )


def _add_test_coverage_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    tests = doc.get("test_requirements")
    if not isinstance(tests, dict):
        return
    for idx, scenario in enumerate(_as_list(tests.get("scenarios"))):
        name = _item_name(scenario, idx, "scenario")
        ref = f"test_requirements.scenarios.{_slug(name)}"
        _task(
            tasks,
            category="test_requirements.scenario",
            source_ref=ref,
            title=f"Keep RTL observable for scenario {name}",
            detail="Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.",
            criteria=[
                "RTL exposes enough signals/status/outputs for the scenario checker",
                "FunctionalModel expected result and RTL observed result can be compared",
                "Scenario has coverage refs or a precise SSOT reason for exclusion",
            ],
            owner=_owner_for(ref, modules, top),
            value=scenario,
            priority="normal",
        )
    goals = tests.get("coverage_goals")
    planned_bins = goals.get("planned_bins") if isinstance(goals, dict) else None
    for idx, bin_item in enumerate(_as_list(planned_bins)):
        name = _item_name(bin_item, idx, "coverage_bin")
        ref = f"test_requirements.coverage_goals.planned_bins.{_slug(name)}"
        _task(
            tasks,
            category="coverage.functional_bin",
            source_ref=ref,
            title=f"Provide RTL evidence for coverage bin {name}",
            detail="Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.",
            criteria=[
                "Bin has a scoreboard coverage_refs entry",
                "Scoreboard row includes concrete rtl_observed DUT signals",
                "Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage",
            ],
            owner=_owner_for(ref, modules, top),
            value=bin_item,
            priority="normal",
        )


def _add_module_equivalence_tasks(tasks: list[dict[str, Any]], modules: list[dict[str, Any]], top: str) -> None:
    for module in modules:
        refs = [str(ref) for ref in module.get("refs") or [] if str(ref).strip()]
        behavior_refs = [
            ref for ref in refs
            if ref.startswith((
                "function_model",
                "cycle_model",
                "features",
                "dataflow",
                "registers",
                "memory",
                "interrupts",
                "fsm",
                "error_handling",
            ))
        ]
        if len(modules) == 1 and not behavior_refs:
            behavior_refs = ["function_model", "cycle_model"]
        if not behavior_refs:
            continue
        name = str(module.get("name") or top)
        file_name = str(module.get("file") or f"rtl/{name}.sv")
        ref = f"sub_modules.{_slug(name)}.module_equivalence"
        _task(
            tasks,
            category="equivalence.module",
            source_ref=ref,
            title=f"Prove module {name} is functionally equivalent to FL",
            detail=(
                "This is a functionality-equality gate, not a style or file-existence check. "
                "The module must be driven from the same SSOT transaction intent used by "
                "FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result."
            ),
            criteria=[
                "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
                "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
                "scoreboard row fl_expected.model_api is FunctionalModel.apply",
                "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
                "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
            ],
            owner={"module": name, "file": file_name, "matched_ref": "module_equivalence"},
            value={"module": name, "file": file_name, "behavior_refs": behavior_refs},
        )


def _workflow_todo_owner(item: dict[str, Any], source_refs: list[str], modules: list[dict[str, Any]], top: str) -> dict[str, str]:
    owner_module = _ci_get(item, "owner_module", "module", "rtl_module")
    owner_file = _ci_get(item, "owner_file", "file", "rtl_file")
    if _present(owner_module) or _present(owner_file):
        module_name = str(owner_module or Path(str(owner_file)).stem)
        file_name = str(owner_file or "")
        if not file_name:
            matched = next((module for module in modules if str(module.get("name")) == module_name), None)
            file_name = str((matched or {}).get("file") or f"rtl/{_slug(module_name)}.sv")
        return {"module": module_name, "file": file_name, "matched_ref": "workflow_todos.owner"}
    for ref in source_refs:
        owner = _owner_for(ref, modules, top)
        if owner.get("module") or owner.get("file"):
            return owner
    return _owner_for("top_module", modules, top)


def _add_workflow_todo_tasks(
    tasks: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    doc: dict[str, Any],
    modules: list[dict[str, Any]],
    top: str,
) -> None:
    for idx, (source_ref, item) in enumerate(_workflow_todo_entries(doc), start=1):
        content = _ci_get(item, "content", "title", "task", "name", "summary")
        detail = _ci_get(item, "detail", "details", "description", "instructions", "rationale")
        criteria = _criteria_items(_ci_get(item, "criteria", "acceptance_criteria", "done_when", "pass_criteria"))
        missing = [
            field
            for field, value in (("content", content), ("detail", detail), ("criteria", criteria))
            if not _present(value)
        ]
        todo_id = str(_ci_get(item, "id", "todo_id", "name") or f"RTL_WORKFLOW_TODO_{idx:03d}")
        if missing:
            blockers.append({
                "id": f"MALFORMED_RTL_WORKFLOW_TODO_{idx:03d}",
                "source_ref": source_ref,
                "reason": "SSOT workflow_todos entries for rtl-gen must include content, detail, and criteria.",
                "missing_fields": missing,
                "owner": "ssot-gen",
            })
            continue

        source_refs = _workflow_todo_refs(item)
        owner = _workflow_todo_owner(item, source_refs, modules, top)
        priority = str(_ci_get(item, "priority") or "high").lower()
        required_raw = _ci_get(item, "required", "mandatory")
        required = False if str(required_raw).strip().lower() in {"false", "0", "no", "optional"} else True
        category_raw = _ci_get(item, "category", "class")
        _task(
            tasks,
            category="workflow_todo.rtl_gen",
            source_ref=source_ref,
            title=str(content),
            detail=str(detail),
            criteria=[
                *criteria,
                "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
                "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
            ],
            owner=owner,
            value=item,
            priority=priority if priority in {"critical", "high", "normal", "low"} else "high",
            required=required,
        )
        task = tasks[-1]
        task["workflow_todo"] = {
            "stage": "rtl-gen",
            "id": todo_id,
            "user_category": str(category_raw or ""),
            "source_refs": source_refs,
        }
        task["ssot_refs"] = sorted({source_ref, *source_refs})
        if source_refs:
            task["criteria"].append("Semantic source_refs covered: " + ", ".join(source_refs))


def _convert_to_template_format(plan: dict[str, Any]) -> dict[str, Any]:
    tasks = []
    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue

        content = task.get("content", "")
        criteria = task.get("criteria", [])
        criteria_lines = [str(item) for item in criteria] if isinstance(criteria, list) else [str(criteria)]

        detail = task.get("detail", "")

        active_form = content
        verb_map = {
            "read": "Reading", "write": "Writing", "implement": "Implementing",
            "create": "Creating", "run": "Running", "check": "Checking",
            "verify": "Verifying", "build": "Building", "design": "Designing",
            "extract": "Extracting", "define": "Defining", "add": "Adding",
            "instantiate": "Instantiating", "connect": "Connecting",
        }
        content_lower = content.lower()
        for verb, verb_ing in verb_map.items():
            if content_lower.startswith(verb):
                active_form = verb_ing + content[len(verb):]
                break

        tasks.append({
            "content": content,
            "activeForm": active_form,
            "detail": detail,
            "criteria": "\n".join(line for line in criteria_lines if line),
            "priority": task.get("priority", "medium"),
        })

    return {
        "name": f"{plan.get('ip', 'unknown')}-rtl",
        "description": f"Auto-generated TodoTracker tasks from SSOT RTL plan for {plan.get('ip', '')}",
        "source_plan": "rtl/rtl_todo_plan.json",
        "lock_additions": False,
        "tasks": tasks,
    }


def _write_outputs(ip_dir: Path, plan: dict[str, Any]) -> None:
    rtl_dir = ip_dir / "rtl"
    logs_dir = ip_dir / "logs" / "rtl-gen"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    full_plan_text = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (logs_dir / "rtl_todo_plan.json").write_text(full_plan_text, encoding="utf-8")
    (rtl_dir / "rtl_todo_plan.json").write_text(full_plan_text, encoding="utf-8")

    template_plan = _convert_to_template_format(plan)
    template_text = json.dumps(template_plan, ensure_ascii=False, indent=2) + "\n"
    (rtl_dir / "rtl_todo_tracker.json").write_text(template_text, encoding="utf-8")
    trace = {
        "schema_version": plan["schema_version"],
        "type": "rtl_traceability_matrix",
        "ip": plan["ip"],
        "top": plan["top"],
        "generated_at": plan["generated_at"],
        "rows": [
            {
                "task_id": task["id"],
                "source_ref": task["source_ref"],
                "category": task["category"],
                "owner_module": task["owner_module"],
                "owner_file": task["owner_file"],
                "evidence_terms": task["evidence_terms"],
                "static_evidence": task.get("static_evidence"),
            }
            for task in plan["tasks"]
        ],
        "gate": plan["gate"],
    }
    (rtl_dir / "rtl_traceability.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_dynamic_blocker(ip_dir: Path, plan: dict[str, Any]) -> None:
    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
    if not blockers and not orphans:
        return
    questions: list[dict[str, Any]] = []
    if blockers:
        required_fields = sorted({
            str(item.get("source_ref") or item.get("id") or "")
            for item in blockers
            if isinstance(item, dict) and (item.get("source_ref") or item.get("id"))
        })
        questions.append({
            "id": "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS",
            "decision_needed": "Repair the SSOT so rtl-gen has mandatory source sections and well-formed SSOT-defined workflow todos.",
            "evidence": "rtl/rtl_todo_plan.json blockers",
            "options": [
                "Update SSOT with structured function_model and cycle_model sections.",
                "Update workflow_todos.rtl-gen[] entries so every item has content, detail, and criteria.",
                "Move non-RTL intent out of RTL implementation sections and rerun /ssot-rtl.",
            ],
            "recommended_default": "Use ssot-gen to fill function_model, cycle_model, workflow_todos.rtl-gen content/detail/criteria, decomposition, DV plan, and coverage from the requirement.",
            "required_fields": required_fields or ["function_model", "cycle_model", "workflow_todos.rtl-gen[].content/detail/criteria"],
            "blocking_items": blockers[:32],
        })
    if orphans:
        candidate_modules = [
            {"name": item.get("name"), "file": item.get("file"), "refs": item.get("refs")}
            for item in ((plan.get("summary") or {}).get("owner_modules") or [])
            if isinstance(item, dict)
        ]
        questions.append({
            "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
            "decision_needed": "Assign every SSOT-derived function/cycle/register/dataflow/FSM task to an RTL module owner.",
            "evidence": "rtl/rtl_todo_plan.json orphans",
            "options": [
                "Add exact sub_modules[].*_refs ownership for each orphan source_ref.",
                "Split or refine SSOT decomposition until each behavior has one RTL owner.",
                "Promote independently verified blocks to child_ssot with an explicit SSOT path.",
            ],
            "recommended_default": "Patch sub_modules[] with function_model_refs, cycle_model_refs, register_refs, dataflow_refs, and fsm_refs.",
            "orphan_refs": [item.get("source_ref") for item in orphans[:128] if isinstance(item, dict)],
            "candidate_modules": candidate_modules[:32],
            "required_fields": [
                "sub_modules[].function_model_refs",
                "sub_modules[].cycle_model_refs",
                "sub_modules[].register_refs",
                "sub_modules[].dataflow_refs",
                "sub_modules[].fsm_refs",
            ],
            "answer_schema": {
                "format": "YAML or JSON",
                "root_key": "module_contracts",
                "rule": "Every orphan source_ref must be covered by an exact ref or a dotted parent ref in the owning sub_modules[] row.",
            },
        })
    out = {
        "schema_version": 1,
        "type": "rtl_blocker",
        "status": "blocked",
        "owner": "ssot-gen + human gate",
        "ip": plan.get("ip"),
        "top": plan.get("top"),
        "reason": "SSOT-derived dynamic RTL TODO gate is blocked.",
        "questions": questions,
        "next_action": "Answer these questions through ATLAS UI, update SSOT, regenerate FL/equivalence goals, then rerun /ssot-rtl.",
        "timestamp": _utc(),
    }
    path = ip_dir / "rtl" / "rtl_blocked.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_rtl_sources(ip_dir: Path) -> dict[str, str]:
    entries: list[str] = []
    filelist = ip_dir / "list" / f"{ip_dir.name}.f"
    if filelist.is_file():
        for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("//", 1)[0].split("#", 1)[0].strip()
            if line.endswith((".sv", ".v", ".svh", ".vh")):
                entries.append(line)
    if not entries and (ip_dir / "rtl").is_dir():
        entries = [str(path.relative_to(ip_dir)) for path in sorted((ip_dir / "rtl").glob("*.sv")) + sorted((ip_dir / "rtl").glob("*.v"))]
    sources: dict[str, str] = {}
    for rel in entries:
        path = ip_dir / rel
        if not path.is_file():
            path = ip_dir.parent / rel
        if path.is_file():
            try:
                sources[rel] = path.read_text(encoding="utf-8", errors="replace")[:400000]
            except OSError:
                pass
    return sources


def _audit_static_evidence(ip_dir: Path, plan: dict[str, Any]) -> None:
    sources = _read_rtl_sources(ip_dir)
    all_text = "\n".join(sources.values())
    clean = re.sub(r"/\*.*?\*/", "", all_text, flags=re.S)
    clean = re.sub(r"//.*", "", clean)
    tokens: set[str] = set()
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", clean):
        tokens.add(token)
        parts = [part for part in token.split("_") if part]
        tokens.update(parts)
        for idx in range(len(parts)):
            suffix = "_".join(parts[idx:])
            if suffix:
                tokens.add(suffix)
    missing: list[dict[str, Any]] = []
    checked = 0
    passed = 0
    for task in plan["tasks"]:
        if not task.get("requires_static_rtl_evidence"):
            task["static_evidence"] = {"required": False, "status": "not_required"}
            continue
        checked += 1
        terms = [term for term in task.get("evidence_terms") or [] if len(str(term)) > 1]
        matched = sorted({term for term in terms if term in tokens})
        status = "pass" if matched else "missing"
        if matched:
            passed += 1
        task["static_evidence"] = {
            "required": True,
            "status": status,
            "matched_terms": matched,
            "required_terms": terms,
        }
        if status != "pass":
            missing.append({
                "task_id": task["id"],
                "source_ref": task["source_ref"],
                "category": task["category"],
                "owner_file": task["owner_file"],
                "required_terms": terms[:8],
            })
    plan["static_rtl_evidence"] = {
        "sources": sorted(sources),
        "checked": checked,
        "passed": passed,
        "missing": len(missing),
        "missing_tasks": missing[:128],
    }


def _gate_todo_completion(plan: dict[str, Any], ip_dir: Path, task: dict[str, Any], *, audit_rtl: bool) -> tuple[str, str, list[str]]:
    gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
    kind = str(gate.get("kind") or "")
    artifact = str(gate.get("artifact") or "")
    basis = [
        "rtl_todo_plan.json gate_todo.kind",
        "rtl_todo_plan.json task criteria",
    ]
    if artifact:
        basis.append(artifact)
    if not audit_rtl:
        return "planned", "RTL audit has not run yet.", basis

    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    blocker_ids = {str(item.get("id") or "") for item in blockers if isinstance(item, dict)}
    orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
    static = plan.get("static_rtl_evidence") if isinstance(plan.get("static_rtl_evidence"), dict) else {}

    if kind == "ssot_required_sections":
        missing = sorted(item for item in blocker_ids if item.startswith("MISSING_FUNCTION_MODEL") or item.startswith("MISSING_CYCLE_MODEL"))
        if missing:
            return "open", "SSOT function_model/cycle_model blocker is still open: " + ", ".join(missing), basis
        return "pass", "SSOT function_model and cycle_model authority is present.", basis
    if kind == "ssot_workflow_todo_format":
        malformed = sorted(item for item in blocker_ids if item.startswith("MALFORMED_RTL_WORKFLOW_TODO"))
        if malformed:
            return "open", "Malformed SSOT workflow_todos.rtl-gen entries remain: " + ", ".join(malformed), basis
        return "pass", "SSOT-authored rtl-gen workflow TODOs are well formed.", basis
    if kind == "owner_traceability":
        if orphans:
            return "open", f"{len(orphans)} required SSOT-derived RTL task(s) still have no owner module.", basis
        return "pass", "Every required SSOT-derived RTL behavior has an owner module.", basis
    if kind == "common_ai_agent_authoring":
        path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing common_ai_agent RTL authoring provenance.", basis
        allowed_surfaces = {"atlas_ui", "textual_ui", "headless_common_engine"}
        todo_plan = ip_dir / "rtl" / "rtl_todo_plan.json"
        expected_hashes = {_sha256_file(todo_plan), _stable_json_sha256(todo_plan)} if todo_plan.is_file() else set()
        rtl_files = report.get("rtl_files") if isinstance(report.get("rtl_files"), list) else []
        issues = []
        if report.get("type") != "rtl_authoring_provenance":
            issues.append("type")
        if report.get("agent") != "common_ai_agent":
            issues.append("agent")
        if report.get("workflow") != "rtl-gen":
            issues.append("workflow")
        if report.get("surface") not in allowed_surfaces:
            issues.append("surface")
        if expected_hashes and report.get("todo_plan_sha256") not in expected_hashes:
            issues.append("todo_plan_sha256")
        if not rtl_files:
            issues.append("rtl_files")
        if issues:
            return "open", "RTL authoring provenance is incomplete: " + ", ".join(issues), basis
        return "pass", "RTL authoring provenance proves common_ai_agent rtl-gen ownership.", basis
    if kind == "static_rtl_evidence":
        missing = int(static.get("missing") or 0)
        if missing:
            return "open", f"{missing} static-evidence-required task(s) still lack DUT RTL evidence.", basis
        return "pass", "Static DUT RTL evidence audit has no missing required task.", basis
    if kind == "dut_compile":
        path = ip_dir / "rtl" / "rtl_compile.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing canonical DUT compile artifact: rtl/rtl_compile.json.", basis
        passed = (
            report.get("passed") is True
            and report.get("dut_only") is True
            and int(report.get("errors") or 0) == 0
            and int(report.get("diagnostics") or 0) == 0
            and int(report.get("style_violations") or 0) == 0
        )
        if not passed:
            return "open", "DUT compile artifact is not clean.", basis
        return "pass", "DUT-only compile artifact passed with zero errors, diagnostics, and style violations.", basis
    if kind == "dut_lint":
        path = ip_dir / "lint" / "dut_lint.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing canonical DUT lint artifact: lint/dut_lint.json.", basis
        passed = (
            report.get("passed") is True
            and report.get("dut_only") is True
            and int(report.get("errors") or 0) == 0
            and int(report.get("warnings") or 0) == 0
            and int(report.get("suppression_violation_count") or 0) == 0
        )
        if not passed:
            return "open", "DUT lint artifact is not clean.", basis
        return "pass", "DUT-only lint artifact passed with zero errors, warnings, and suppression violations.", basis
    if kind == "dynamic_todo_closure":
        return "deferred", "Dynamic TODO closure is evaluated after other required TODOs.", basis
    return "open", "Unknown RTL gate kind.", basis


def _default_todo_completion(task: dict[str, Any], *, audit_rtl: bool) -> tuple[str, str, list[str]]:
    static = task.get("static_evidence") if isinstance(task.get("static_evidence"), dict) else {}
    basis = [
        "rtl_todo_plan.json task criteria",
        "rtl_traceability.json source_ref mapping",
        "DUT-only compile/lint stage evidence",
        "static RTL evidence audit when evidence_terms are required",
    ]
    if not audit_rtl:
        return "planned", "RTL audit has not run yet.", basis
    if static.get("status") == "missing":
        return "open", "Required RTL static evidence is missing.", basis
    return "pass", "Task criteria are closed by SSOT traceability plus RTL audit/compile/lint evidence.", basis


def _update_todo_completion(plan: dict[str, Any], ip_dir: Path, *, audit_rtl: bool) -> None:
    tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    closure_tasks: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("category") == "rtl_gate.rtl_gen":
            status, reason, basis = _gate_todo_completion(plan, ip_dir, task, audit_rtl=audit_rtl)
            if (task.get("gate_todo") or {}).get("kind") == "dynamic_todo_closure":
                closure_tasks.append(task)
        else:
            status, reason, basis = _default_todo_completion(task, audit_rtl=audit_rtl)
        task["todo_completion"] = {
            "status": status,
            "required": bool(task.get("required")),
            "criteria_total": len(task.get("criteria") or []),
            "evidence_basis": basis,
            "reason": reason,
        }

    def required_open_tasks(*, include_closure: bool) -> list[dict[str, Any]]:
        open_items: list[dict[str, Any]] = []
        for task in tasks:
            if not isinstance(task, dict) or not bool(task.get("required")):
                continue
            gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
            if not include_closure and gate.get("kind") == "dynamic_todo_closure":
                continue
            completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
            if completion.get("status") != "pass":
                open_items.append({
                    "task_id": task.get("id"),
                    "source_ref": task.get("source_ref"),
                    "category": task.get("category"),
                    "reason": completion.get("reason") or "Task is not closed.",
                })
        return open_items

    open_before_closure = required_open_tasks(include_closure=False)
    for task in closure_tasks:
        basis = list((task.get("todo_completion") or {}).get("evidence_basis") or [])
        if not audit_rtl:
            status = "planned"
            reason = "RTL audit has not run yet."
        elif open_before_closure:
            status = "open"
            reason = f"{len(open_before_closure)} required non-closure TODO(s) remain open."
        else:
            status = "pass"
            reason = "Every required non-closure TODO has pass status."
        task["todo_completion"] = {
            "status": status,
            "required": bool(task.get("required")),
            "criteria_total": len(task.get("criteria") or []),
            "evidence_basis": basis,
            "reason": reason,
        }

    open_required = required_open_tasks(include_closure=True)
    required_total = sum(1 for task in tasks if isinstance(task, dict) and bool(task.get("required")))
    passed_required = 0
    for task in tasks:
        if isinstance(task, dict) and bool(task.get("required")):
            completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
            if completion.get("status") == "pass":
                passed_required += 1
    plan["todo_completion"] = {
        "audit_rtl": audit_rtl,
        "required_total": required_total,
        "required_passed": passed_required,
        "open_required_tasks": len(open_required),
        "open_tasks": open_required[:128],
        "all_required_todos_pass": audit_rtl and not open_required,
        "rule": "rtl-gen may not claim PASS until every required SSOT-derived TODO has pass status.",
    }


def derive_plan(root: Path, ip: str, *, audit_rtl: bool = False) -> dict[str, Any]:
    ssot_path, doc = _load_ssot(root, ip)
    top = _top_name(doc, ip)
    ip_dir = root / ip
    modules = _active_modules(doc, ip, top)
    top_owner = _owner_for("top_module", modules, top)
    tasks: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    _add_base_tasks(tasks, ip, top, top_owner)
    _add_rtl_gate_todo_tasks(tasks, top_owner)
    _add_workflow_todo_tasks(tasks, blockers, doc, modules, top)
    _add_parameter_tasks(tasks, doc, modules, top)
    _add_io_tasks(tasks, doc, modules, top)
    _add_function_model_tasks(tasks, doc, modules, top)
    _add_cycle_model_tasks(tasks, doc, modules, top)
    _add_register_tasks(tasks, doc, modules, top)
    _add_section_list_tasks(tasks, doc, modules, top, section="memory", keys=("instances", "ports", "init", "maps"), label="memory item")
    _add_section_list_tasks(tasks, doc, modules, top, section="interrupts", keys=("sources", "outputs", "masks", "clears"), label="interrupt item")
    _add_fsm_tasks(tasks, doc, modules, top)
    _add_feature_dataflow_tasks(tasks, doc, modules, top)
    _add_section_list_tasks(tasks, doc, modules, top, section="error_handling", keys=("errors", "faults", "recovery", "responses"), label="error/fault item")
    _add_section_list_tasks(tasks, doc, modules, top, section="security", keys=("requirements", "assets", "checks", "policies"), label="security item")
    _add_section_list_tasks(tasks, doc, modules, top, section="debug_observability", keys=("signals", "status", "trace", "commands"), label="debug/observability item")
    _add_section_list_tasks(tasks, doc, modules, top, section="integration", keys=("dependencies", "interfaces", "address_map", "connections"), label="integration item")
    _add_section_list_tasks(tasks, doc, modules, top, section="dft", keys=("requirements", "scan", "test_points"), label="DFT item")
    _add_section_list_tasks(tasks, doc, modules, top, section="synthesis", keys=("constraints", "ppa_targets", "dont_touch"), label="synthesis item")
    _add_module_equivalence_tasks(tasks, modules, top)
    _add_test_coverage_tasks(tasks, doc, modules, top)

    for key in ("function_model", "cycle_model"):
        if not _present(doc.get(key)):
            blockers.append({
                "id": f"MISSING_{key.upper()}",
                "source_ref": key,
                "reason": f"SSOT must include non-empty {key} before RTL generation.",
                "owner": "ssot-gen",
            })

    orphans = [
        {
            "task_id": task["id"],
            "source_ref": task["source_ref"],
            "category": task["category"],
            "reason": "No RTL owner module could be inferred from SSOT sub_modules contracts.",
        }
        for task in tasks
        if task["required"]
        and task["category"].startswith(("function_model.", "cycle_model.", "registers.", "dataflow.", "fsm."))
        and not task.get("owner_module")
    ]

    counts = Counter(task["category"] for task in tasks)
    by_section = Counter(task["category"].split(".", 1)[0] for task in tasks)
    plan: dict[str, Any] = {
        "schema_version": 1,
        "type": "ssot_derived_rtl_todo_plan",
        "ip": ip,
        "top": top,
        "generated_at": _utc(),
        "source": str(ssot_path.relative_to(root)),
        "summary": {
            "total_tasks": len(tasks),
            "required_tasks": sum(1 for task in tasks if task.get("required")),
            "by_category": dict(sorted(counts.items())),
            "by_section": dict(sorted(by_section.items())),
            "ssot_workflow_todos": counts.get("workflow_todo.rtl_gen", 0),
            "rtl_gate_todos": counts.get("rtl_gate.rtl_gen", 0),
            "owner_modules": [{"name": item["name"], "file": item["file"], "refs": item["refs"]} for item in modules],
            "blocking_questions": len(blockers),
            "orphan_tasks": len(orphans),
        },
        "policy": {
            "fixed_template_role": "seed_only",
            "dynamic_task_rule": "Use every required task in this file as the active RTL implementation checklist; add as many UI todos as this plan requires.",
            "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
            "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership gates must close as TODOs before PASS.",
            "no_orphan_function_level": True,
            "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
        },
        "blockers": blockers,
        "orphans": orphans[:128],
        "tasks": tasks,
        "static_rtl_evidence": {"sources": [], "checked": 0, "passed": 0, "missing": 0, "missing_tasks": []},
        "gate": {},
    }
    if audit_rtl:
        _audit_static_evidence(ip_dir, plan)
    _update_todo_completion(plan, ip_dir, audit_rtl=audit_rtl)
    static_missing = int((plan.get("static_rtl_evidence") or {}).get("missing") or 0)
    open_todos = int((plan.get("todo_completion") or {}).get("open_required_tasks") or 0)
    gate_status = "pass"
    if blockers:
        gate_status = "blocked"
    elif orphans:
        gate_status = "blocked"
    elif audit_rtl and static_missing:
        gate_status = "fail"
    elif audit_rtl and open_todos:
        gate_status = "fail"
    elif not audit_rtl:
        gate_status = "planned"
    plan["gate"] = {
        "status": gate_status,
        "audit_rtl": audit_rtl,
        "blocking_questions": len(blockers),
        "orphan_tasks": len(orphans),
        "static_missing": static_missing,
        "open_required_todos": open_todos,
        "all_required_todos_pass": bool((plan.get("todo_completion") or {}).get("all_required_todos_pass")),
        "criteria": [
            task["content"]
            for task in tasks
            if task.get("category") == "rtl_gate.rtl_gen"
        ],
    }
    _write_outputs(ip_dir, plan)
    _write_dynamic_blocker(ip_dir, plan)
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--audit-rtl", action="store_true")
    ns = ap.parse_args()
    plan = derive_plan(Path(ns.root).resolve(), ns.ip, audit_rtl=ns.audit_rtl)
    summary = plan.get("summary") or {}
    gate = plan.get("gate") or {}
    print(
        "[derive_rtl_todos] "
        f"{ns.ip}: tasks={summary.get('total_tasks', 0)} "
        f"blockers={summary.get('blocking_questions', 0)} "
        f"orphans={summary.get('orphan_tasks', 0)} "
        f"gate={gate.get('status')}"
    )
    if gate.get("status") == "blocked":
        return 2
    return 1 if gate.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
