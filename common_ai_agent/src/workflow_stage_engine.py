#!/usr/bin/env python3
"""Shared SSOT workflow stage engine for ATLAS UI, Textual UI, and headless TDD.

Control surfaces should render and route. This module owns the deterministic
stage commands, artifact paths, validator evidence, and blocker classification.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


SOURCE_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = SOURCE_ROOT / "workflow"

STAGE_ALIASES = {
    "sfm": "ssot-fl-model",
    "ssot-fl-model": "ssot-fl-model",
    "fl-model": "ssot-fl-model",
    "fl-model-gen": "ssot-fl-model",
    "seg": "ssot-equiv-goals",
    "equiv-goals": "ssot-equiv-goals",
    "ssot-equiv-goals": "ssot-equiv-goals",
    "spa": "ssot-protocol-assertions",
    "protocol-assertions": "ssot-protocol-assertions",
    "ssot-protocol-assertions": "ssot-protocol-assertions",
    "sr": "ssot-rtl",
    "rtl": "ssot-rtl",
    "rtl-gen": "ssot-rtl",
    "ssot-rtl": "ssot-rtl",
    "lint": "lint",
    "tb": "ssot-tb-cocotb",
    "stb": "ssot-tb-cocotb",
    "ssot-tb": "ssot-tb-cocotb",
    "stb-cocotb": "ssot-tb-cocotb",
    "ssot-tb-cocotb": "ssot-tb-cocotb",
    "coverage": "coverage",
    "cov": "coverage",
    "coverage-report": "coverage",
    "cov-report": "coverage",
    "s": "sim",
    "sim": "sim",
    "sd": "sim-debug",
    "sim-debug": "sim-debug",
    "audit": "goal-audit",
    "ga": "goal-audit",
    "goal-audit": "goal-audit",
}

STAGE_WORKFLOW = {
    "ssot-fl-model": "fl-model-gen",
    "ssot-equiv-goals": "fl-model-gen",
    "ssot-protocol-assertions": "fl-model-gen",
    "ssot-rtl": "rtl-gen",
    "lint": "lint",
    "ssot-tb-cocotb": "tb-gen",
    "coverage": "coverage",
    "sim": "sim",
    "sim-debug": "sim_debug",
    "goal-audit": "sim_debug",
}


def safe_ip_name(value: str, fallback: str = "ip") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text or not re.match(r"^[A-Za-z]", text):
        return fallback
    return text


def is_valid_ip_name(value: str) -> bool:
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", value or ""))


def canonical_stage(stage: str) -> str:
    return STAGE_ALIASES.get((stage or "").strip().lstrip("/").lower(), stage)


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _clip(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... <truncated {len(text) - limit} chars>"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _top_module_name(doc: dict[str, Any], fallback: str) -> str:
    top = doc.get("top_module") if isinstance(doc, dict) else {}
    if isinstance(top, dict) and top.get("name"):
        return str(top["name"]).strip() or fallback
    if isinstance(top, str) and top.strip():
        return top.strip()
    return fallback


def _expected_rtl_files(doc: dict[str, Any]) -> list[dict[str, str]]:
    expected: list[dict[str, str]] = []
    seen: set[str] = set()
    subs = doc.get("sub_modules") if isinstance(doc, dict) else []
    if isinstance(subs, list):
        for idx, item in enumerate(subs):
            if not isinstance(item, dict):
                continue
            file_name = str(item.get("file") or "").strip()
            if not file_name or file_name in seen:
                continue
            record = dict(item)
            record["name"] = str(item.get("name") or Path(file_name).stem or f"module_{idx}")
            record["file"] = file_name
            expected.append(record)
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


def _filelist_entries(ip_dir: Path) -> tuple[list[str], Path | None]:
    filelist = ip_dir / "list" / f"{ip_dir.name}.f"
    if not filelist.is_file():
        return [], None
    entries: list[str] = []
    try:
        for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("//", 1)[0].split("#", 1)[0].strip()
            if line and line.endswith((".v", ".sv", ".vh", ".svh")):
                entries.append(line)
    except OSError:
        return [], filelist
    return entries, filelist


def _strip_sv_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text or "", flags=re.S)
    return re.sub(r"//.*", "", text)


def _flatten_text(value: Any, *, limit: int = 50000) -> str:
    parts: list[str] = []

    def visit(item: Any) -> None:
        if sum(len(part) for part in parts) > limit:
            return
        if isinstance(item, dict):
            for key, val in item.items():
                parts.append(str(key))
                visit(val)
        elif isinstance(item, list):
            for val in item:
                visit(val)
        elif item is not None:
            parts.append(str(item))

    visit(value)
    return " ".join(parts)[:limit].lower()


def _sv_declared_ports(text: str) -> dict[str, set[str]]:
    clean = _strip_sv_comments(text)
    ports: dict[str, set[str]] = {"input": set(), "output": set(), "inout": set()}
    for raw in clean.splitlines():
        line = raw.strip()
        m = re.search(r"\b(input|output|inout)\b(?P<body>.*)", line)
        if not m:
            continue
        direction = m.group(1)
        body = re.sub(r"\[[^\]]+\]", " ", m.group("body"))
        body = re.sub(r"\b(?:wire|reg|logic|signed|unsigned)\b", " ", body)
        body = body.split("//", 1)[0]
        body = body.rstrip(",;)")
        for token in re.split(r"[,=\s]+", body):
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                ports[direction].add(token)
    return ports


def _sv_assignments(text: str) -> dict[str, str]:
    clean = _strip_sv_comments(text)
    assigns: dict[str, str] = {}
    for lhs, expr in re.findall(r"\bassign\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);", clean):
        assigns[lhs] = " ".join(expr.split())
    return assigns


def _is_zero_constant_expr(expr: str) -> bool:
    norm = re.sub(r"\s+", "", str(expr or "")).lower().replace("_", "")
    norm = norm.strip("()")
    if norm in {"0", "'0"}:
        return True
    if re.fullmatch(r"\d+'[s]?[bdh]0+", norm):
        return True
    if re.fullmatch(r"\d+'[s]?o0+", norm):
        return True
    if re.fullmatch(r"\d+\(?'?[s]?[bdho]?0+\)?", norm):
        return True
    return False


def _meaningful_lhs_names(text: str) -> set[str]:
    clean = _strip_sv_comments(text)
    names: set[str] = set()
    for lhs in re.findall(r"\bassign\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", clean):
        if not lhs.startswith("ssot_"):
            names.add(lhs)
    for lhs in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:<=|=)\s*", clean):
        if lhs not in {"if", "for", "while", "case"} and not lhs.startswith("ssot_"):
            names.add(lhs)
    return names


def _module_claims_behavior(item: dict[str, Any]) -> bool:
    text = _flatten_text(item, limit=12000)
    behavior_tokens = (
        "function_model",
        "cycle_model",
        "dataflow",
        "fsm",
        "test_requirements",
        "feature",
        "primary behavior",
        "behavior slice",
    )
    return any(token in text for token in behavior_tokens)


def _top_aliases(top_name: str) -> set[str]:
    return {name for name in {top_name, f"{top_name}_top", "top", "wrapper"} if name}


def _manifest_submodule_items(doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    raw = doc.get("sub_modules") if isinstance(doc, dict) else []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        ownership = str(item.get("ownership") or "manifest").strip().lower()
        if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or item.get("ssot"):
            continue
        if item.get("rtl_emit") is False:
            continue
        out.append(item)
    return out


def _module_aliases(item: dict[str, Any]) -> set[str]:
    aliases: set[str] = set()
    for raw in (item.get("name"), Path(str(item.get("file") or "")).stem):
        name = str(raw or "").strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            aliases.add(name)
    return aliases


def _skip_hierarchy_item(item: dict[str, Any]) -> bool:
    file_name = str(item.get("file") or "")
    name = str(item.get("name") or Path(file_name).stem)
    kind = str(item.get("type") or item.get("kind") or item.get("role") or "").strip().lower()
    if kind in {"package", "header", "include", "typedef"}:
        return True
    if file_name.endswith((".svh", ".vh")):
        return True
    return name.endswith("_pkg") or name.endswith("_types")


def _sv_module_bodies(text: str) -> dict[str, str]:
    clean = _strip_sv_comments(text)
    modules: dict[str, str] = {}
    pattern = re.compile(
        r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b(?P<body>.*?)(?=\bendmodule\b)",
        re.S,
    )
    for match in pattern.finditer(clean):
        modules[match.group(1)] = match.group("body")
    return modules


def _sv_instantiated_module_names(text: str) -> set[str]:
    clean = _strip_sv_comments(text)
    keywords = {
        "assign",
        "always",
        "always_comb",
        "always_ff",
        "always_latch",
        "begin",
        "case",
        "casex",
        "casez",
        "class",
        "end",
        "endcase",
        "endclass",
        "endfunction",
        "endgenerate",
        "endmodule",
        "endpackage",
        "endtask",
        "enum",
        "for",
        "function",
        "generate",
        "if",
        "initial",
        "input",
        "inout",
        "interface",
        "localparam",
        "logic",
        "modport",
        "module",
        "output",
        "package",
        "parameter",
        "reg",
        "return",
        "struct",
        "task",
        "typedef",
        "union",
        "while",
        "wire",
    }
    out: set[str] = set()
    pattern = re.compile(
        r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\((?:[^()]|\([^()]*\))*\)\s*)?"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        re.S,
    )
    for match in pattern.finditer(clean):
        module_name = match.group(1)
        if module_name.lower() not in keywords:
            out.add(module_name)
    return out


def _rtl_hierarchy_progress(ip_dir: Path, listed_sources: list[Path], doc: dict[str, Any], top_name: str) -> dict[str, Any]:
    declarations: dict[str, str] = {}
    graph: dict[str, set[str]] = {}
    for path in listed_sources:
        try:
            rel = str(path.relative_to(ip_dir))
        except ValueError:
            try:
                rel = str(path.relative_to(ip_dir.parent))
            except ValueError:
                rel = path.name
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:400000]
        except OSError:
            continue
        for module_name, body in _sv_module_bodies(text).items():
            declarations[module_name] = rel
            graph[module_name] = _sv_instantiated_module_names(body)

    roots = sorted(_top_aliases(top_name) & set(declarations))
    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        for child in graph.get(current, set()):
            if child in declarations and child not in reachable:
                stack.append(child)

    issues: list[dict[str, str]] = []
    manifest_items = _manifest_submodule_items(doc)
    if manifest_items and not roots:
        expected_top_file = f"rtl/{top_name}.sv"
        issues.append({
            "name": top_name,
            "file": expected_top_file,
            "issue": "SSOT top module is not declared in listed RTL sources",
        })

    top_names = _top_aliases(top_name)
    for item in manifest_items:
        if _skip_hierarchy_item(item):
            continue
        aliases = _module_aliases(item)
        if aliases & top_names:
            continue
        rel = str(item.get("file") or "")
        declared = sorted(aliases & set(declarations))
        if not declared:
            issues.append({
                "name": str(item.get("name") or Path(rel).stem),
                "file": rel,
                "issue": "SSOT manifest child module is not declared in listed RTL sources",
            })
            continue
        if not (set(declared) & reachable):
            issues.append({
                "name": declared[0],
                "file": rel or declarations.get(declared[0], ""),
                "issue": "SSOT manifest child module is declared but not reachable from the top RTL hierarchy",
            })

    return {
        "status": "pass" if not issues else "fail",
        "roots": roots,
        "declared_modules": sorted(declarations),
        "reachable_modules": sorted(reachable),
        "graph": {key: sorted(value) for key, value in sorted(graph.items())},
        "issues": issues,
    }


def _memory_mapped_registers_required(doc: dict[str, Any]) -> bool:
    registers = doc.get("registers") if isinstance(doc, dict) else {}
    if isinstance(registers, dict):
        config = registers.get("config")
        if isinstance(config, dict) and config.get("memory_mapped_registers") is True:
            return True
        reg_list = registers.get("register_list")
        if isinstance(reg_list, list) and reg_list:
            return True
    return False


def _register_list_present(doc: dict[str, Any]) -> bool:
    registers = doc.get("registers") if isinstance(doc, dict) else {}
    return bool(isinstance(registers, dict) and isinstance(registers.get("register_list"), list) and registers["register_list"])


def _pslverr_required(doc: dict[str, Any]) -> bool:
    registers = doc.get("registers") if isinstance(doc, dict) else {}
    if not isinstance(registers, dict):
        return False
    config = registers.get("config")
    policy = config.get("access_policy") if isinstance(config, dict) else {}
    if isinstance(policy, dict) and policy.get("pslverr_on_decode_error") is True:
        return True
    return "pslverr_on_decode_error" in _flatten_text(registers, limit=16000)


def _ssot_requires_interrupt(doc: dict[str, Any]) -> bool:
    if isinstance(doc.get("interrupts"), (dict, list)):
        return True
    text = _flatten_text(
        {
            "features": doc.get("features"),
            "function_model": doc.get("function_model"),
            "test_requirements": doc.get("test_requirements"),
            "traceability": doc.get("traceability"),
        },
        limit=30000,
    )
    return "interrupt" in text or re.search(r"\birq\b", text) is not None


def _ssot_observability_names(doc: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    cycle = doc.get("cycle_model") if isinstance(doc, dict) else {}
    if isinstance(cycle, dict):
        obs = cycle.get("observability")
        if isinstance(obs, list):
            names.update(str(item).strip().lower() for item in obs if str(item).strip())
    text = _flatten_text(
        {
            "function_model": doc.get("function_model"),
            "features": doc.get("features"),
            "registers": doc.get("registers"),
            "error_handling": doc.get("error_handling"),
        },
        limit=30000,
    )
    for name in ("busy", "error", "fault_status", "status"):
        if name in text:
            names.add(name)
    return names


def _ssot_requires_valid_ready(doc: dict[str, Any]) -> bool:
    cycle = doc.get("cycle_model") if isinstance(doc, dict) else {}
    if isinstance(cycle, dict):
        rules = cycle.get("handshake_rules")
        if isinstance(rules, list):
            for rule in rules:
                text = _flatten_text(rule, limit=4000)
                if "valid_ready" in text or ("valid" in text and "ready" in text):
                    return True
    return "valid_ready" in _flatten_text(doc.get("io_list") if isinstance(doc, dict) else {}, limit=12000)


def _rtl_sample_condition(ip_dir: Path, doc: dict[str, Any]) -> str:
    contract = doc.get("rtl_contract") if isinstance(doc, dict) else {}
    if isinstance(contract, dict) and contract.get("sample_condition"):
        return str(contract.get("sample_condition") or "")
    contract_path = ip_dir / "rtl" / "rtl_contract.json"
    if contract_path.is_file():
        data = _read_json(contract_path)
        nested = data.get("contract") if isinstance(data.get("contract"), dict) else data
        if isinstance(nested, dict) and nested.get("sample_condition"):
            return str(nested.get("sample_condition") or "")
    return ""


def _rtl_module_quality_issues(
    *,
    item: dict[str, Any],
    text: str,
    doc: dict[str, Any],
    ip_dir: Path,
    is_top: bool,
) -> list[str]:
    issues: list[str] = []
    ports = _sv_declared_ports(text)
    output_ports = ports.get("output", set())
    inout_ports = ports.get("inout", set())
    meaningful_lhs = _meaningful_lhs_names(text)

    if not is_top and _module_claims_behavior(item):
        if not output_ports and not inout_ports:
            issues.append("SSOT behavior-owner module exposes no output/inout path back to the design")
        if not meaningful_lhs:
            issues.append("SSOT behavior-owner module contains no meaningful non-trace assignment or state update")

    if is_top:
        assigns = _sv_assignments(text)
        if _memory_mapped_registers_required(doc):
            if "pslverr" in output_ports and _pslverr_required(doc) and _is_zero_constant_expr(assigns.get("pslverr", "")):
                issues.append("SSOT register access policy requires decode-error pslverr, but top ties pslverr to zero")
            if "prdata" in output_ports and _register_list_present(doc) and _is_zero_constant_expr(assigns.get("prdata", "")):
                issues.append("SSOT register_list exists, but top ties prdata to zero instead of decode/read data")
        if _ssot_requires_interrupt(doc):
            for port in sorted(output_ports):
                if port.lower() in {"irq", "interrupt", "intr"} and _is_zero_constant_expr(assigns.get(port, "")):
                    issues.append(f"SSOT interrupt behavior exists, but top ties {port} to zero")
        observability = _ssot_observability_names(doc)
        for port in sorted(output_ports):
            name_l = port.lower()
            if name_l in observability and _is_zero_constant_expr(assigns.get(port, "")):
                issues.append(f"SSOT observability requires {port}, but top ties it to zero")
        sample = _rtl_sample_condition(ip_dir, doc)
        sample_l = sample.lower()
        if _ssot_requires_valid_ready(doc) and sample_l and "valid" in sample_l and not any(
            token in sample_l for token in ("ready", "accept", "pready", "penable")
        ):
            issues.append(
                f"SSOT valid-ready acceptance requires ready/equivalent phase, but rtl_contract.sample_condition is {sample!r}"
            )

    return issues


def _rtl_manifest_progress(ip_dir: Path, doc: dict[str, Any]) -> dict[str, Any]:
    """Return SSOT-manifest RTL file approval evidence.

    Compile/lint only prove the filelist is syntactically clean. This check
    proves the filelist also covers the RTL modules the SSOT says should exist.
    It is intentionally IP-agnostic and rejects placeholder manifest stubs.
    """
    blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
    blocked_doc = _read_json(blocked_path) if blocked_path.is_file() else {}
    entries, filelist = _filelist_entries(ip_dir)
    entry_set = set(entries)
    top_name = _top_module_name(doc, ip_dir.name)
    listed_sources: list[Path] = []
    listed_text = ""
    for entry in entries:
        path = ip_dir / entry
        if not path.is_file():
            path = ip_dir.parent / entry
        if path.is_file():
            listed_sources.append(path)
            try:
                listed_text += "\n" + path.read_text(encoding="utf-8", errors="replace")[:200000]
            except OSError:
                pass

    expected = _expected_rtl_files(doc)
    if not expected:
        rtl_dir = ip_dir / "rtl"
        expected = [
            {"name": path.stem, "file": str(path.relative_to(ip_dir))}
            for path in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
        ] if rtl_dir.is_dir() else []

    hierarchy = _rtl_hierarchy_progress(ip_dir, listed_sources, doc, top_name)
    hierarchy_issues_by_file: dict[str, list[str]] = {}
    for issue in hierarchy.get("issues") or []:
        if not isinstance(issue, dict):
            continue
        rel = str(issue.get("file") or "")
        if rel:
            hierarchy_issues_by_file.setdefault(rel, []).append(str(issue.get("issue") or "RTL hierarchy issue"))

    modules: list[dict[str, Any]] = []
    for item in expected:
        rel = item["file"]
        path = ip_dir / rel
        resolved_rel = rel
        manifest_mismatch = False
        if (
            not path.is_file()
            and top_name
            and item.get("name") in {f"{top_name}_top", "top", "wrapper"}
        ):
            alias_rel = f"rtl/{top_name}.sv"
            alias_path = ip_dir / alias_rel
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
        is_top = bool(item.get("name") == top_name or Path(resolved_rel).stem == top_name)
        scaffold_only = bool(
            re.search(r"Auto-generated manifest submodule", text, re.I)
            or re.search(r"\balive_q\b|\bheartbeat_q\b", text)
        )
        placeholder = bool(re.search(r"\b(TBD|TODO:|FIXME|HACK)\b", text, re.I)) or scaffold_only
        quality_issues = _rtl_module_quality_issues(
            item=item,
            text=text,
            doc=doc,
            ip_dir=ip_dir,
            is_top=is_top,
        ) if exists else []
        for issue_rel in {rel, resolved_rel}:
            quality_issues.extend(hierarchy_issues_by_file.get(issue_rel, []))
        listed = rel in entry_set or resolved_rel in entry_set
        try:
            listed = listed or (exists and str(path.relative_to(ip_dir.parent)) in entry_set)
        except Exception:
            pass
        include_header = False
        if exists and not listed and path.suffix in {".sv", ".svh", ".vh"}:
            include_header = (
                bool(re.search(rf'`include\s+"{re.escape(path.name)}"', listed_text))
                or path.stem.endswith("_pkg")
                or "include header" in text[:2000].lower()
            )
        approved = exists and size >= 200 and (listed or include_header) and not placeholder and not quality_issues
        modules.append({
            "name": item.get("name") or Path(rel).stem,
            "file": rel,
            "resolved_file": resolved_rel,
            "status": "approved" if approved else ("partial" if exists else "missing"),
            "exists": exists,
            "listed": listed,
            "include_header": include_header,
            "bytes": size,
            "placeholder": placeholder,
            "scaffold_only": scaffold_only,
            "quality_issues": quality_issues,
            "manifest_mismatch": manifest_mismatch or (resolved_rel != rel),
        })

    approved = sum(1 for item in modules if item["status"] == "approved")
    quality_issues = [
        {
            "module": item.get("name"),
            "file": item.get("resolved_file") or item.get("file"),
            "issue": issue,
        }
        for item in modules
        for issue in (item.get("quality_issues") or [])
    ]
    return {
        "status": "pass" if modules and approved == len(modules) and filelist else ("partial" if approved else "pending"),
        "approved": approved,
        "total": len(modules),
        "pct": round((approved / len(modules)) * 100.0, 1) if modules else 0.0,
        "filelist": str(filelist.relative_to(ip_dir.parent)) if filelist else "",
        "modules": modules,
        "manifest_mismatches": sum(1 for item in modules if item.get("manifest_mismatch")),
        "manifest_mismatch_details": [item for item in modules if item.get("manifest_mismatch")],
        "hierarchy": hierarchy,
        "hierarchy_issue_count": len(hierarchy.get("issues") or []),
        "quality_issue_count": len(quality_issues),
        "quality_issues": quality_issues,
        "blocked": bool(blocked_doc),
        "blocker": str(blocked_doc.get("reason") or "") if blocked_doc else "",
        "blocker_source": str(blocked_path.relative_to(ip_dir.parent)) if blocked_doc else "",
        "questions": blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else [],
        "next_action": str(blocked_doc.get("next_action") or "") if blocked_doc else "",
    }


@dataclass
class ToolRun:
    label: str
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "cmd": " ".join(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass
class StageEngineResult:
    stage: str
    ip: str
    status: str
    headline: str
    message: str
    runs: list[ToolRun] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    blocker: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def returncode(self) -> int:
        if self.status == "pass":
            return 0
        if self.status in {"blocked", "human_gate"}:
            return 2
        return 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "workflow": STAGE_WORKFLOW.get(self.stage, self.stage),
            "ip": self.ip,
            "status": self.status,
            "headline": self.headline,
            "message": self.message,
            "returncode": self.returncode,
            "runs": [run.to_dict() for run in self.runs],
            "artifacts": self.artifacts,
            "blocker": self.blocker,
            "metadata": self.metadata,
        }


class WorkflowStageEngine:
    """Run SSOT-derived workflow stages with disk-truth validators."""

    def __init__(self, project_root: str | Path, source_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.source_root = Path(source_root).resolve() if source_root else SOURCE_ROOT
        self.workflow_root = self.source_root / "workflow"

    def ip_dir(self, ip: str) -> Path:
        return self.project_root / safe_ip_name(ip)

    def ssot_path(self, ip: str) -> Path:
        ip = safe_ip_name(ip)
        return self.ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"

    def top_name(self, ip: str) -> str:
        ip = safe_ip_name(ip)
        try:
            doc = yaml.safe_load(self.ssot_path(ip).read_text(encoding="utf-8", errors="replace")) or {}
        except Exception:
            return ip
        top = doc.get("top_module") if isinstance(doc, dict) else {}
        if isinstance(top, dict) and top.get("name"):
            return str(top["name"])
        if isinstance(top, str) and top.strip():
            return top.strip()
        return ip

    def run_stage(self, stage: str, ip: str) -> StageEngineResult:
        ip = safe_ip_name(ip)
        stage = canonical_stage(stage)
        if stage not in STAGE_WORKFLOW:
            result = self._result(stage, ip, "fail", f"[{stage}] unknown stage", [f"unknown stage: {stage}"])
            self._write_run_log(result)
            return result
        if stage != "sim" and not self.ssot_path(ip).is_file():
            result = self._result(
                stage,
                ip,
                "blocked",
                f"[{stage}] blocked: SSOT not found",
                [
                    f"[{stage}] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml",
                    f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first.",
                ],
                blocker=f"{ip}/yaml/{ip}.ssot.yaml",
            )
            self._write_run_log(result)
            return result

        dispatch = {
            "ssot-fl-model": self._run_fl_model,
            "ssot-equiv-goals": self._run_equiv_goals,
            "ssot-protocol-assertions": self._run_protocol_assertions,
            "ssot-rtl": self._run_rtl,
            "lint": self._run_lint,
            "ssot-tb-cocotb": self._run_tb_cocotb,
            "coverage": self._run_coverage,
            "sim": self._run_sim,
            "sim-debug": self._run_sim_debug,
            "goal-audit": self._run_goal_audit,
        }
        result = dispatch[stage](ip)
        self._write_run_log(result)
        return result

    def _run_tool(self, label: str, command: list[str], timeout_s: int = 180) -> ToolRun:
        try:
            proc = subprocess.run(
                command,
                cwd=str(self.project_root),
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
            return ToolRun(
                label=label,
                command=command,
                returncode=int(proc.returncode),
                stdout=_clip((proc.stdout or "").strip()),
                stderr=_clip((proc.stderr or "").strip()),
            )
        except Exception as exc:
            return ToolRun(label=label, command=command, returncode=999, stderr=str(exc))

    def _run_fl_model(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "fl-model-gen" / "scripts" / "emit_fl_model.py"
        run = self._run_tool("emit_fl_model", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=90)
        status = "pass" if run.returncode == 0 else "fail"
        lines = [
            "[ssot-fl-model] generic SSOT-driven FL model stage",
            f"script: {script}",
            f"module: {ip}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            f"exit: {run.returncode}",
        ]
        self._append_runs(lines, [run])
        artifacts = [
            f"{ip}/model/functional_model.py",
            f"{ip}/model/decomposition.json",
            f"{ip}/model/fl_model_check.json",
            f"{ip}/cov/fcov_plan.json",
        ]
        self._append_expected(lines, artifacts)
        return self._result("ssot-fl-model", ip, status, lines[0], lines, runs=[run], artifacts=artifacts)

    def _run_equiv_goals(self, ip: str) -> StageEngineResult:
        fl_script = self.workflow_root / "fl-model-gen" / "scripts" / "emit_fl_model.py"
        eq_script = self.workflow_root / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"
        runs = [
            self._run_tool("emit_fl_model", [sys.executable, str(fl_script), ip, "--root", str(self.project_root)], timeout_s=90)
        ]
        if runs[-1].returncode == 0:
            runs.append(self._run_tool("emit_equivalence_goals", [sys.executable, str(eq_script), ip, "--root", str(self.project_root)], timeout_s=90))
        else:
            runs.append(ToolRun("emit_equivalence_goals", [sys.executable, str(eq_script), ip, "--root", str(self.project_root)], 999, stderr="skipped because emit_fl_model failed"))

        goals_path = self.ip_dir(ip) / "verify" / "equivalence_goals.json"
        summary = ""
        if goals_path.is_file():
            doc = _read_json(goals_path)
            s = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
            summary = (
                f"total={s.get('total', 0)} required={s.get('required', 0)} "
                f"blocked={s.get('blocked', 0)} "
                f"module={s.get('module_required', 0)}/{s.get('module_total', 0)}"
            )
        status = "pass" if runs[-1].returncode == 0 else "blocked"
        headline = "[ssot-equiv-goals] PASS" if status == "pass" else "[ssot-equiv-goals] BLOCKED"
        lines = [
            headline,
            f"script: {eq_script}",
            f"module: {ip}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            f"goals: {summary or '(not generated)'}",
        ]
        self._append_runs(lines, runs)
        artifacts = [
            f"{ip}/verify/equivalence_goals.json",
            f"{ip}/model/functional_model.py",
            f"{ip}/model/decomposition.json",
            f"{ip}/cov/fcov_plan.json",
        ]
        self._append_expected(lines, artifacts)
        if status != "pass":
            lines += ["", "next: inspect blocked goals and answer/repair SSOT behavior before TB signoff"]
        return self._result("ssot-equiv-goals", ip, status, headline, lines, runs=runs, artifacts=artifacts)

    def _run_protocol_assertions(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "fl-model-gen" / "scripts" / "emit_protocol_assertions.py"
        run = self._run_tool("emit_protocol_assertions", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=90)
        summary_path = self.ip_dir(ip) / "verify" / "protocol_assertions.summary.json"
        summary_doc = _read_json(summary_path) if summary_path.is_file() else {}
        assertions_total = int(summary_doc.get("assertions_total") or 0)
        status = "pass" if run.returncode == 0 and assertions_total > 0 else "blocked"
        headline = "[ssot-protocol-assertions] PASS" if status == "pass" else "[ssot-protocol-assertions] BLOCKED"
        lines = [
            headline,
            f"script: {script}",
            f"module: {ip}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            f"assertions: {assertions_total}",
        ]
        self._append_runs(lines, [run])
        artifacts = [
            f"{ip}/verify/protocol_assertions.sva",
            f"{ip}/verify/protocol_assertions.summary.json",
            f"{ip}/sim/assertion_failures.jsonl after /sim",
        ]
        self._append_expected(lines, artifacts)
        if status != "pass":
            lines += ["", "next: add machine-checkable cycle_model.handshake_rules/order rules in SSOT, then rerun /ssot-protocol-assertions"]
        return self._result("ssot-protocol-assertions", ip, status, headline, lines, runs=[run], artifacts=artifacts)

    def _run_rtl(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
        todo_script = self.workflow_root / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
        top = self.top_name(ip)
        try:
            ssot_doc = yaml.safe_load(self.ssot_path(ip).read_text(encoding="utf-8", errors="replace")) or {}
        except Exception:
            ssot_doc = {}
        if not isinstance(ssot_doc, dict):
            ssot_doc = {}
        runs = [
            self._run_tool(
                "derive_rtl_todos",
                [sys.executable, str(todo_script), ip, "--root", str(self.project_root)],
                timeout_s=90,
            )
        ]
        compile_rc = lint_rc = None
        runs.append(self._run_tool("rtl_preflight", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=180))
        if runs[-1].returncode == 0:
            compile_script = self.workflow_root / "rtl-gen" / "scripts" / "rtl_compile_report.py"
            lint_script = self.workflow_root / "lint" / "scripts" / "dut_lint_report.py"
            runs.append(self._run_tool("dut_compile", [sys.executable, str(compile_script), ip, "--top", top, "--project-root", str(self.project_root)], timeout_s=180))
            compile_rc = runs[-1].returncode
            runs.append(self._run_tool("dut_lint", [sys.executable, str(lint_script), ip, "--top", top], timeout_s=180))
            lint_rc = runs[-1].returncode
            runs.append(
                self._run_tool(
                    "audit_rtl_todos",
                    [sys.executable, str(todo_script), ip, "--root", str(self.project_root), "--audit-rtl"],
                    timeout_s=90,
                )
            )
        else:
            runs.append(
                self._run_tool(
                    "audit_rtl_todos",
                    [sys.executable, str(todo_script), ip, "--root", str(self.project_root), "--audit-rtl"],
                    timeout_s=90,
                )
            )

        blocked_path = self.ip_dir(ip) / "rtl" / "rtl_blocked.json"
        blocked_doc = _read_json(blocked_path) if blocked_path.is_file() else {}
        todo_plan_path = self.ip_dir(ip) / "rtl" / "rtl_todo_plan.json"
        todo_plan = _read_json(todo_plan_path) if todo_plan_path.is_file() else {}
        todo_summary = todo_plan.get("summary") if isinstance(todo_plan.get("summary"), dict) else {}
        todo_gate = todo_plan.get("gate") if isinstance(todo_plan.get("gate"), dict) else {}
        todo_completion = todo_plan.get("todo_completion") if isinstance(todo_plan.get("todo_completion"), dict) else {}
        rtl_progress = _rtl_manifest_progress(self.ip_dir(ip), ssot_doc)
        blocked_questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
        llm_rtl_blockers = {
            "RTL_TODO_PLAN_MISSING",
            "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
            "LLM_RTL_IMPLEMENTATION_REQUIRED",
            "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
        }
        llm_only_blocked = bool(blocked_doc) and bool(blocked_questions) and all(
            isinstance(q, dict) and str(q.get("id") or "") in llm_rtl_blockers
            for q in blocked_questions
        )
        if blocked_doc:
            if llm_only_blocked:
                status = "blocked"
                headline = "[RTL BLOCKED] rtl-gen waiting for LLM-authored RTL"
            else:
                status = "human_gate"
                headline = "[SSOT QUESTION] rtl-gen BLOCKED"
        elif (
            runs[0].returncode == 0
            and runs[1].returncode == 0
            and compile_rc == 0
            and lint_rc == 0
            and runs[-1].returncode == 0
            and todo_gate.get("status") == "pass"
            and todo_completion.get("all_required_todos_pass") is True
            and rtl_progress.get("status") == "pass"
            and int(rtl_progress.get("manifest_mismatches") or 0) == 0
        ):
            status = "pass"
            headline = "[RTL RESULT] PASS - generated RTL and DUT-only compile/lint evidence"
        elif runs[1].returncode == 0:
            status = "fail"
            headline = "[RTL RESULT] FAIL - LLM-authored RTL needs rtl-gen repair"
        else:
            status = "blocked"
            headline = "[RTL BLOCKED] rtl-gen waiting for LLM-authored RTL evidence"

        lines = [
            headline,
            f"module: {ip}",
            f"top: {top}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            f"preflight: {script}",
            f"dynamic_todos: {todo_plan_path.relative_to(self.project_root) if todo_plan_path.is_file() else '(missing)'}",
        ]
        metadata: dict[str, Any] = {"top": top, "rtl_manifest": rtl_progress, "rtl_todo_plan": todo_plan}
        blocker = ""
        if blocked_doc:
            blocker = f"{ip}/rtl/rtl_blocked.json"
            metadata["rtl_blocked"] = blocked_doc
            lines += [
                f"blocker: {blocked_doc.get('reason') or 'SSOT decision required'}",
                f"evidence: {blocker}",
                f"next: {blocked_doc.get('next_action') or 'answer SSOT questions and rerun /ssot-rtl'}",
            ]
            if blocked_questions:
                lines += ["", "questions:"]
                for q in blocked_questions:
                    if not isinstance(q, dict):
                        continue
                    lines.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                    if q.get("recommended_default"):
                        lines.append(f"  recommended: {q.get('recommended_default')}")
                    orphan_groups = q.get("orphan_groups") if isinstance(q.get("orphan_groups"), list) else []
                    if orphan_groups:
                        lines.append("  orphan_groups:")
                        for group in orphan_groups[:8]:
                            if not isinstance(group, dict):
                                continue
                            samples = group.get("sample_refs") if isinstance(group.get("sample_refs"), list) else []
                            sample_text = ", ".join(str(item) for item in samples[:2])
                            section = str(group.get("section_id") or "").strip()
                            category = str(group.get("category") or "").strip()
                            label = category if category.startswith(section + ".") else f"{section}.{category}".strip(".")
                            lines.append(
                                "    - "
                                f"{label}: "
                                f"count={group.get('count')} "
                                f"field={group.get('required_field')}"
                                + (f" sample={sample_text}" if sample_text else "")
                            )
        self._append_runs(lines, runs)
        lines += [
            "",
            "rtl_dynamic_todos:",
            f"- tasks: {todo_summary.get('total_tasks', 0)} required={todo_summary.get('required_tasks', 0)}",
            f"- ssot_workflow_todos: {todo_summary.get('ssot_workflow_todos', 0)}",
            f"- rtl_gate_todos: {todo_summary.get('rtl_gate_todos', 0)}",
            f"- sections: {', '.join(sorted((todo_summary.get('by_section') or {}).keys())[:12]) if isinstance(todo_summary.get('by_section'), dict) else '(none)'}",
            f"- gate: {todo_gate.get('status') or '(missing)'}",
            f"- blockers: {todo_gate.get('blocking_questions', 0)}",
            f"- orphans: {todo_gate.get('orphan_tasks', 0)}",
            f"- static_missing: {todo_gate.get('static_missing', 0)}",
            f"- open_required_todos: {todo_gate.get('open_required_todos', todo_completion.get('open_required_tasks', 0))}",
            f"- all_required_todos_pass: {todo_gate.get('all_required_todos_pass', todo_completion.get('all_required_todos_pass', False))}",
        ]
        static_missing = []
        static_doc = todo_plan.get("static_rtl_evidence") if isinstance(todo_plan.get("static_rtl_evidence"), dict) else {}
        if isinstance(static_doc.get("missing_tasks"), list):
            static_missing = static_doc.get("missing_tasks") or []
        owner_logic_doc = todo_plan.get("owner_logic_evidence") if isinstance(todo_plan.get("owner_logic_evidence"), dict) else {}
        top_io_doc = todo_plan.get("top_io_contract_evidence") if isinstance(todo_plan.get("top_io_contract_evidence"), dict) else {}
        hierarchy_doc = todo_plan.get("manifest_hierarchy_evidence") if isinstance(todo_plan.get("manifest_hierarchy_evidence"), dict) else {}
        if owner_logic_doc:
            lines += [
                f"- owner_logic_checked: {owner_logic_doc.get('checked', 0)}",
                f"- owner_logic_issues: {len(owner_logic_doc.get('issues') or [])}",
            ]
        if top_io_doc:
            lines += [
                f"- top_io_contracts: {top_io_doc.get('contracts', 0)}",
                f"- top_io_issues: {len(top_io_doc.get('issues') or [])}",
            ]
        if hierarchy_doc:
            lines += [
                f"- port_connection_issues: {len(hierarchy_doc.get('port_connection_issues') or [])}",
                f"- connection_contract_issues: {len(hierarchy_doc.get('connection_contract_issues') or [])}",
            ]
        if static_missing:
            lines.append("- static_missing_details:")
            for item in static_missing[:12]:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    f"  - {item.get('task_id')}: {item.get('source_ref')} "
                    f"terms={item.get('required_terms')}"
                )
        open_tasks = todo_completion.get("open_tasks") if isinstance(todo_completion.get("open_tasks"), list) else []
        if open_tasks and todo_completion.get("audit_rtl") is True:
            lines.append("- open_required_details:")
            gate_first = sorted(
                [item for item in open_tasks if isinstance(item, dict)],
                key=lambda item: (0 if str(item.get("category") or "") == "rtl_gate.rtl_gen" else 1, str(item.get("task_id") or "")),
            )
            for item in gate_first[:12]:
                lines.append(
                    f"  - {item.get('task_id')}: {item.get('source_ref')} "
                    f"category={item.get('category')} reason={item.get('reason')}"
                )
        lines += [
            "",
            "rtl_manifest:",
            f"- approved: {rtl_progress.get('approved', 0)}/{rtl_progress.get('total', 0)}",
            f"- filelist: {rtl_progress.get('filelist') or '(missing)'}",
            f"- manifest_mismatches: {rtl_progress.get('manifest_mismatches', 0)}",
            f"- hierarchy_issues: {rtl_progress.get('hierarchy_issue_count', 0)}",
            f"- quality_issues: {rtl_progress.get('quality_issue_count', 0)}",
        ]
        quality_issues = rtl_progress.get("quality_issues") if isinstance(rtl_progress.get("quality_issues"), list) else []
        if quality_issues:
            lines.append("- quality_issue_details:")
            for issue in quality_issues[:12]:
                if not isinstance(issue, dict):
                    continue
                lines.append(
                    f"  - {issue.get('module')}: {issue.get('issue')} "
                    f"file={issue.get('file')}"
                )
        missing_modules = [
            item for item in rtl_progress.get("modules", [])
            if isinstance(item, dict) and item.get("status") != "approved"
        ]
        if missing_modules:
            lines.append("- missing_or_partial:")
            for item in missing_modules[:12]:
                lines.append(
                    f"  - {item.get('name')}: {item.get('status')} "
                    f"file={item.get('file')} listed={item.get('listed')} bytes={item.get('bytes')}"
                )
                for issue in (item.get("quality_issues") or [])[:3]:
                    lines.append(f"    quality: {issue}")
        artifacts = [
            f"{ip}/yaml/{ip}.ssot.yaml",
            f"{ip}/rtl/rtl_todo_plan.json",
            f"{ip}/rtl/rtl_todo_tracker.json",
            f"{ip}/rtl/rtl_traceability.json",
            f"{ip}/list/{ip}.f",
            f"{ip}/rtl/rtl_compile.json",
            f"{ip}/lint/dut_lint.json",
            f"{ip}/rtl/rtl_blocked.json (only when SSOT decision is required)",
        ]
        self._append_artifacts(lines, artifacts)
        if blocked_doc:
            lines += ["", "next: ATLAS opened an SSOT decision Q&A card for the RTL blocker."]
        elif status == "pass":
            lines += ["", "next: run /tb, /sim, /sim-debug, and /goal-audit to prove FL-vs-RTL behavior."]
        elif runs[0].returncode == 0:
            metadata["needs_repair"] = True
            lines += ["", "next: queued rtl-gen repair with compile/lint/SSOT-manifest diagnostics as evidence."]
        return self._result("ssot-rtl", ip, status, headline, lines, runs=runs, artifacts=artifacts, blocker=blocker, metadata=metadata)

    def _run_lint(self, ip: str) -> StageEngineResult:
        top = self.top_name(ip)
        script = self.workflow_root / "lint" / "scripts" / "dut_lint_report.py"
        run = self._run_tool("dut_lint", [sys.executable, str(script), ip, "--top", top], timeout_s=180)
        status = "pass" if run.returncode == 0 else "fail"
        headline = "[lint] PASS" if status == "pass" else "[lint] FAIL"
        lines = [headline, f"script: {script}", f"module: {ip}", f"top: {top}"]
        self._append_runs(lines, [run])
        artifacts = [f"{ip}/lint/dut_lint.json"]
        self._append_expected(lines, artifacts)
        return self._result("lint", ip, status, headline, lines, runs=[run], artifacts=artifacts, metadata={"top": top})

    def _run_tb_cocotb(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
        validator = self.workflow_root / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
        scoreboard = self.workflow_root / "tb-gen" / "runtime" / "equivalence_scoreboard.py"
        runs = [self._run_tool("emit_goal_scoreboard_cocotb", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=180)]
        structure_rc = self_check_rc = None
        if runs[-1].returncode == 0:
            runs.append(self._run_tool("check_pyuvm_structure", ["bash", str(validator), ip], timeout_s=180))
            structure_rc = runs[-1].returncode
            runs.append(self._run_tool("equivalence_scoreboard_self_check", [sys.executable, str(scoreboard), ip, "--root", str(self.project_root), "--self-check"], timeout_s=90))
            self_check_rc = runs[-1].returncode

        blocked_path = self.ip_dir(ip) / "tb" / "cocotb" / "tb_blocked.json"
        blocked_doc = _read_json(blocked_path) if blocked_path.is_file() else {}
        if blocked_doc or runs[0].returncode == 2:
            status = "human_gate"
            headline = "[ssot-tb-cocotb] BLOCKED - SSOT/RTL contract needs repair"
        elif runs[0].returncode == 0 and structure_rc == 0 and self_check_rc == 0:
            status = "pass"
            headline = "[ssot-tb-cocotb] PASS - generated goal-driven pyuvm/cocotb scoreboard"
        elif runs[0].returncode == 0:
            status = "fail"
            headline = "[ssot-tb-cocotb] FAIL - generated TB needs tb-gen repair"
        else:
            status = "fail"
            headline = "[ssot-tb-cocotb] FAIL - generator did not produce approved TB artifacts"

        lines = [
            headline,
            f"module: {ip}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            f"generator: {script}",
            f"validator: {validator}",
        ]
        metadata: dict[str, Any] = {}
        blocker = ""
        if blocked_doc:
            blocker = f"{ip}/tb/cocotb/tb_blocked.json"
            metadata["tb_blocked"] = blocked_doc
            lines += [
                f"blocker: {blocked_doc.get('reason') or 'SSOT/RTL decision required'}",
                f"evidence: {blocker}",
                f"next: {blocked_doc.get('next_action') or 'repair SSOT/RTL contract and rerun /tb'}",
            ]
            questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
            if questions:
                lines += ["", "questions:"]
                for q in questions:
                    if not isinstance(q, dict):
                        continue
                    lines.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                    if q.get("recommended_default"):
                        lines.append(f"  recommended: {q.get('recommended_default')}")
        self._append_runs(lines, runs)
        artifacts = [
            f"{ip}/tb/cocotb/test_{ip}.py",
            f"{ip}/tb/cocotb/test_runner.py",
            f"{ip}/tb/cocotb/tb_manifest.json",
            f"{ip}/tb/cocotb/tb_generation.json",
            f"{ip}/sim/scoreboard_events.jsonl after /sim",
            f"{ip}/cov/coverage.json after /sim",
        ]
        self._append_expected(lines, artifacts)
        if status == "pass":
            lines += ["", "next: run /sim, /sim-debug, and /goal-audit to collect FL-vs-RTL evidence."]
        elif runs[0].returncode == 0 and status == "fail":
            metadata["needs_repair"] = True
            lines += ["", "next: queued tb-gen repair with structure/self-check diagnostics as evidence."]
        return self._result("ssot-tb-cocotb", ip, status, headline, lines, runs=runs, artifacts=artifacts, blocker=blocker, metadata=metadata)

    def _run_sim(self, ip: str) -> StageEngineResult:
        runner = self._find_tb_runner(ip)
        if runner is None:
            headline = "[sim] blocked: no executable TB runner found"
            lines = [
                f"[sim] blocked: no executable TB runner found for {ip}",
                "expected one of:",
                f"- {ip}/tb/cocotb/test_runner.py",
                f"- {ip}/tb/cocotb/run_tests.py",
                f"- {ip}/tb/test_runner.py",
                f"- {ip}/tb/run_tests.py",
                "Run /tb <ip> first.",
            ]
            return self._result("sim", ip, "blocked", headline, lines, blocker=f"{ip}/tb")
        script = self.workflow_root / "tb-gen" / "scripts" / "sim.sh"
        validator = self.workflow_root / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
        coverage_script = self.workflow_root / "coverage" / "scripts" / "ssot_coverage_summary.py"
        rel_runner = str(runner.relative_to(self.project_root))
        runs = [
            self._run_tool("sim", ["bash", str(script), rel_runner], timeout_s=240),
            self._run_tool("sim_evidence", ["bash", str(validator), ip], timeout_s=180),
        ]
        if all(run.returncode == 0 for run in runs):
            runs.append(
                self._run_tool(
                    "ssot_coverage_summary",
                    [sys.executable, str(coverage_script), str(self.ip_dir(ip))],
                    timeout_s=90,
                )
            )
        status = "pass" if all(run.returncode == 0 for run in runs) else "fail"
        headline = "[sim] PASS" if status == "pass" else "[sim] FAIL"
        lines = [
            headline,
            f"script: {script}",
            f"validator: {validator}",
            f"coverage: {coverage_script}",
            f"module: {ip}",
            f"runner: {rel_runner}",
        ]
        self._append_runs(lines, runs)
        artifacts = [
            f"{ip}/sim/results.xml or {ip}/tb/cocotb/results.xml",
            f"{ip}/sim/scoreboard_events.jsonl",
            f"{ip}/cov/coverage.json",
            f"{ip}/sim/sim_report.txt",
        ]
        self._append_expected(lines, artifacts)
        return self._result("sim", ip, status, headline, lines, runs=runs, artifacts=artifacts, metadata={"runner": rel_runner})

    def _run_coverage(self, ip: str) -> StageEngineResult:
        sim_validator = self.workflow_root / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
        summary_script = self.workflow_root / "coverage" / "scripts" / "ssot_coverage_summary.py"
        runs = [
            self._run_tool("sim_evidence", ["bash", str(sim_validator), ip], timeout_s=180),
        ]
        runs.append(
            self._run_tool(
                "ssot_coverage_summary",
                [sys.executable, str(summary_script), str(self.ip_dir(ip))],
                timeout_s=90,
            )
        )

        coverage_path = self.ip_dir(ip) / "cov" / "coverage.json"
        coverage_doc = _read_json(coverage_path) if coverage_path.is_file() else {}
        coverage_status = str(coverage_doc.get("status") or "").lower()
        limitations = coverage_doc.get("limitations") if isinstance(coverage_doc.get("limitations"), dict) else {}
        functional = coverage_doc.get("functional") if isinstance(coverage_doc.get("functional"), dict) else {}
        lines_metric = coverage_doc.get("lines") if isinstance(coverage_doc.get("lines"), dict) else {}
        branches_metric = coverage_doc.get("branches") if isinstance(coverage_doc.get("branches"), dict) else {}

        if runs[0].returncode != 0:
            status = "blocked"
            headline = "[coverage] BLOCKED - fresh passing simulation evidence required"
        elif runs[-1].returncode == 0 and coverage_status in {"pass", "passed", "ok"}:
            status = "pass"
            headline = "[coverage] PASS - SSOT functional coverage summary approved"
        elif coverage_status == "fail":
            status = "fail"
            headline = "[coverage] FAIL - coverage evidence has failing checks"
        else:
            status = "blocked"
            headline = "[coverage] BLOCKED - coverage gaps or capability limits remain"

        lines = [
            headline,
            f"script: {summary_script}",
            f"module: {ip}",
            f"source: {ip}/yaml/{ip}.ssot.yaml",
            (
                "functional: "
                f"{functional.get('hit', 0)}/{functional.get('total', 0)} "
                f"pct={functional.get('pct')}"
            ),
            (
                "line: "
                f"{lines_metric.get('hit', 0)}/{lines_metric.get('total', 0)} "
                f"pct={lines_metric.get('pct')} target={lines_metric.get('target_pct')}"
            ),
            (
                "branch: "
                f"{branches_metric.get('hit', 0)}/{branches_metric.get('total', 0)} "
                f"pct={branches_metric.get('pct')} target={branches_metric.get('target_pct')}"
            ),
        ]
        if limitations:
            lines.append("limitations:")
            for key, value in list(limitations.items())[:12]:
                lines.append(f"- {key}: {value}")
        self._append_runs(lines, runs)
        artifacts = [
            f"{ip}/cov/fcov_plan.json",
            f"{ip}/cov/coverage_functional.json",
            f"{ip}/cov/coverage.json",
            f"{ip}/cov/coverage_ssot.json",
            f"{ip}/sim/coverage_report.md",
            f"{ip}/sim/results.xml or {ip}/tb/cocotb/results.xml",
        ]
        self._append_expected(lines, artifacts)
        if status == "pass":
            lines += ["", "next: run /sim-debug and /goal-audit before any synthesis-stage work."]
        elif runs[0].returncode != 0:
            lines += ["", "next: rerun /sim after TB repair; coverage is not meaningful on stale or failing simulation evidence."]
        else:
            lines += ["", "next: close SSOT functional coverage gaps or record explicit tool limitations before signoff."]
        return self._result(
            "coverage",
            ip,
            status,
            headline,
            lines,
            runs=runs,
            artifacts=artifacts,
            metadata={"coverage": coverage_doc, "limitations": limitations},
        )

    def _run_sim_debug(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "sim_debug" / "scripts" / "compare_fl_rtl_results.py"
        run = self._run_tool("sim_debug", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=90)
        compare_path = self.ip_dir(ip) / "sim" / "fl_rtl_compare.json"
        classify_path = self.ip_dir(ip) / "sim" / "mismatch_classification.json"
        summary_line = ""
        if compare_path.is_file():
            doc = _read_json(compare_path)
            summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
            summary_line = (
                f"status={doc.get('status')} total={summary.get('total', 0)} "
                f"checked={summary.get('goals_checked', 0)} passed={summary.get('goals_passed', 0)} "
                f"failed={summary.get('goals_failed', 0)} blocked={summary.get('goals_blocked', 0)} "
                f"untested={summary.get('goals_untested', 0)}"
            )
        status = "pass" if run.returncode == 0 else "fail"
        metadata: dict[str, Any] = {}
        classify_doc = _read_json(classify_path) if classify_path.is_file() else {}
        human_items = [
            item for item in classify_doc.get("classifications", [])
            if isinstance(item, dict) and item.get("llm_loop_allowed") is False
        ] if isinstance(classify_doc.get("classifications"), list) else []
        if human_items:
            status = "human_gate"
            metadata["human_gate_classifications"] = human_items
            metadata["mismatch_classification"] = classify_doc
        headline = "[sim-debug] FL-vs-RTL compare"
        lines = [
            headline,
            f"script: {script}",
            f"module: {ip}",
            f"exit: {run.returncode}",
            f"summary: {summary_line or '(not generated)'}",
        ]
        self._append_runs(lines, [run])
        artifacts = [
            f"{ip}/sim/fl_rtl_compare.json",
            f"{ip}/sim/mismatch_classification.json",
            f"{ip}/sim/scoreboard_events.jsonl",
            f"{ip}/verify/equivalence_goals.json",
        ]
        self._append_expected(lines, artifacts)
        if run.returncode != 0 and classify_path.is_file():
            lines += ["", "next: repair classified owner or answer human-gate questions from mismatch_classification.json"]
        return self._result("sim-debug", ip, status, headline, lines, runs=[run], artifacts=artifacts, metadata=metadata)

    def _run_goal_audit(self, ip: str) -> StageEngineResult:
        script = self.workflow_root / "sim_debug" / "scripts" / "audit_fl_rtl_equivalence_goal.py"
        run = self._run_tool("goal_audit", [sys.executable, str(script), ip, "--root", str(self.project_root)], timeout_s=90)
        audit_path = self.ip_dir(ip) / "sim" / "fl_rtl_goal_audit.json"
        summary_line = ""
        blockers: list[str] = []
        if audit_path.is_file():
            doc = _read_json(audit_path)
            summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
            blockers = [str(x) for x in summary.get("blockers") or []]
            summary_line = (
                f"status={doc.get('status')} "
                f"passed={summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)} "
                f"blockers={', '.join(blockers) if blockers else 'none'}"
            )
        status = "pass" if run.returncode == 0 else "fail"
        headline = "[goal-audit] PASS" if status == "pass" else "[goal-audit] FAIL"
        lines = [headline, f"script: {script}", f"module: {ip}", f"exit: {run.returncode}", f"summary: {summary_line or '(not generated)'}"]
        self._append_runs(lines, [run])
        artifacts = [f"{ip}/sim/fl_rtl_goal_audit.json"]
        self._append_expected(lines, artifacts[:-1] or artifacts, label="expected artifact")
        if blockers:
            lines += ["", "blockers:"]
            lines += [f"- {blocker}" for blocker in blockers[:12]]
        if status != "pass":
            lines += ["", "next: inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage; do not bypass with a fixed IP template."]
        return self._result("goal-audit", ip, status, headline, lines, runs=[run], artifacts=artifacts, metadata={"blockers": blockers})

    def _find_tb_runner(self, ip: str) -> Path | None:
        candidates = [
            self.ip_dir(ip) / "tb" / "cocotb" / "test_runner.py",
            self.ip_dir(ip) / "tb" / "cocotb" / "run_tests.py",
            self.ip_dir(ip) / "tb" / "test_runner.py",
            self.ip_dir(ip) / "tb" / "run_tests.py",
            self.ip_dir(ip) / "sim" / f"test_{ip}.py",
        ]
        return next((path for path in candidates if path.is_file()), None)

    def _append_runs(self, lines: list[str], runs: list[ToolRun]) -> None:
        lines += ["", "runs:"]
        for run in runs:
            lines.append(f"- {run.label}: exit {run.returncode}")
            lines.append(f"  cmd: {' '.join(run.command)}")
            if run.stdout:
                lines.append("  stdout:")
                lines.append(run.stdout)
            if run.stderr:
                lines.append("  stderr:")
                lines.append(run.stderr)

    def _append_expected(self, lines: list[str], artifacts: list[str], label: str = "expected artifacts") -> None:
        lines += ["", f"{label}:"]
        lines += [f"- {artifact}" for artifact in artifacts]

    def _append_artifacts(self, lines: list[str], artifacts: list[str]) -> None:
        lines += ["", "artifacts:"]
        lines += [f"- {artifact}" for artifact in artifacts]

    def _result(
        self,
        stage: str,
        ip: str,
        status: str,
        headline: str,
        lines: list[str],
        *,
        runs: list[ToolRun] | None = None,
        artifacts: list[str] | None = None,
        blocker: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> StageEngineResult:
        return StageEngineResult(
            stage=stage,
            ip=ip,
            status=status,
            headline=headline,
            message="\n".join(lines),
            runs=runs or [],
            artifacts=artifacts or [],
            blocker=blocker,
            metadata=metadata or {},
        )

    def _write_run_log(self, result: StageEngineResult) -> None:
        log_path = self.ip_dir(result.ip) / "logs" / "stage_engine" / f"{result.stage}.json"
        data = result.to_dict()
        data["created_at"] = _utc()
        _write_json(log_path, data)
