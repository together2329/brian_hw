#!/usr/bin/env python3
"""Upgrade an existing IP SSOT to the canonical production schema.

This is a structure repair tool, not an IP generator. It preserves the
existing SSOT facts, derives missing model/signoff sections from those facts
and the approved ATLAS Q&A state when available, and then writes the same SSOT
path back in canonical section order.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import (  # noqa: E402 - sys.path bootstrap above
    behavioral_contract_map,
    _cycle_model_waived,
)


REQUIRED_ORDER = [
    "top_module",
    "sub_modules",
    "decomposition",
    "rtl_contract",
    "parameters",
    "io_list",
    "features",
    "dataflow",
    "function_model",
    "cycle_model",
    "clock_reset_domains",
    "cdc_requirements",
    "rdc_requirements",
    "registers",
    "memory",
    "interrupts",
    "fsm",
    "timing",
    "power",
    "security",
    "error_handling",
    "debug_observability",
    "integration",
    "dft",
    "synthesis",
    "pnr",
    "coding_rules",
    "reuse_modules",
    "custom",
    "dir_structure",
    "filelist",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "generation_flow",
]


def _resolve_project_root(root_arg: str, ip_root_arg: str, ip: str) -> Path:
    root_source = root_arg or os.environ.get("ATLAS_PROJECT_ROOT") or ""
    project_root = Path(os.path.expandvars(root_arg or os.environ.get("ATLAS_PROJECT_ROOT") or ".")).expanduser().resolve()
    if ip and (project_root / ip / "yaml" / f"{ip}.ssot.yaml").is_file():
        return project_root
    if ip and (project_root / "yaml" / f"{ip}.ssot.yaml").is_file():
        return project_root.parent
    ip_root_raw = (ip_root_arg or os.environ.get("ATLAS_IP_ROOT") or "").strip()
    if ip_root_raw:
        ip_root = Path(os.path.expandvars(ip_root_raw)).expanduser()
        if not ip_root.is_absolute():
            ip_root = project_root / ip_root
        ip_root = ip_root.resolve()
        if root_source:
            try:
                if ip_root != project_root:
                    ip_root.relative_to(project_root)
            except ValueError:
                return project_root
        candidate_root = ip_root.parent if (not ip or ip_root.name == ip or (ip_root / "yaml").is_dir()) else ip_root
        if ip and (candidate_root / ip / "yaml" / f"{ip}.ssot.yaml").is_file():
            return candidate_root
        if not ip and ip_root.is_dir():
            return ip_root.parent
    return project_root

EXPRESSION_SCALAR_KEYS = {
    "condition",
    "detection",
    "expr",
    "expression",
    "guard",
    "sample_condition",
    "trigger",
    "when",
}

RUN_MODES = {"starter", "engineering", "signoff"}
SIGNOFF_CRITICAL_DEFAULT_PATHS = {
    "cycle_model",
    "dft",
    "error_handling",
    "pnr",
    "quality_gates",
    "security",
    "synthesis",
    "test_requirements",
    "timing",
}
REPAIR_TRANSACTION_STATE_MARKER = "Auto-injected transaction coverage/state marker"
REPAIR_TRANSACTION_RULE_MARKER = "Repair marker making this transaction machine-checkable"
REPAIR_OBSERVABLE_RULE_MARKER = "Auto-injected placeholder rule for observable state"


def _normalize_run_mode(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text == "eng":
        text = "engineering"
    if text == "sign-off":
        text = "signoff"
    return text if text in RUN_MODES else "signoff"


def _mode_allowed_for_default(path: str) -> list[str]:
    top = str(path or "").split(".", 1)[0].split("[", 1)[0]
    if top in {"pnr", "dft"}:
        return ["starter", "engineering"]
    if _is_signoff_critical_path(path):
        return ["starter"]
    return ["starter", "engineering"]


def _is_signoff_critical_path(path: str) -> bool:
    field = str(path or "").strip().lstrip("/").replace("/", ".")
    for prefix in SIGNOFF_CRITICAL_DEFAULT_PATHS:
        if field == prefix or field.startswith(prefix + ".") or field.startswith(prefix + "["):
            return True
    return False


def _iter_provenance_paths(value: Any, prefix: str = ""):
    if prefix:
        yield prefix
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_provenance_paths(value[key], child)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            child = f"{prefix}[{idx}]" if prefix else f"[{idx}]"
            yield from _iter_provenance_paths(item, child)


def _write_provenance_sidecar(
    root: Path,
    ip: str,
    ssot: Path,
    before: dict[str, Any],
    after: dict[str, Any],
    run_mode: str,
) -> Path:
    entries: list[dict[str, Any]] = []
    before_paths = set(_iter_provenance_paths(before))
    after_paths = sorted(set(_iter_provenance_paths(after)))
    for path in after_paths:
        if path in before_paths:
            entries.append({
                "path": path,
                "authority": "user",
                "mode_allowed": ["starter", "engineering", "signoff"],
            })
        else:
            critical = _is_signoff_critical_path(path)
            entries.append({
                "path": path,
                "authority": "generated_default",
                "mode_allowed": _mode_allowed_for_default(path),
                "review_needed_for": "signoff" if critical else "",
                "signoff_critical": critical,
                "source": "repair_ssot_schema",
            })
    sidecar = ssot.with_suffix(".provenance.json")
    sidecar.write_text(
        json.dumps(
            {
                "schema_version": "ssot_provenance.v1",
                "ip": ip,
                "run_mode": run_mode,
                "ssot": str(ssot.relative_to(root)),
                "fields": entries,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return sidecar


def _split_inline_comment(value: str) -> tuple[str, str]:
    in_single = False
    in_double = False
    escaped = False
    for idx, ch in enumerate(value):
        if escaped:
            escaped = False
            continue
        if ch == "\\" and in_double:
            escaped = True
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            continue
        if ch == "#" and not in_single and not in_double and (idx == 0 or value[idx - 1].isspace()):
            return value[:idx].rstrip(), value[idx:].rstrip()
    return value.rstrip(), ""


def _needs_expression_quote(value: str) -> bool:
    text = value.strip()
    if not text or text[0] in {"'", '"', "[", "{", "|", ">"}:
        return False
    if text.startswith(("!", "&", "*", "@", "`", "%")):
        return True
    return any(token in text for token in (" && ", " || ", "==", "!=", "<=", ">=", "<<", ">>"))


def _quote_expression_scalars(text: str) -> str:
    """Quote common expression scalars before YAML parsing.

    LLMs often emit Verilog-like expressions such as ``!enable && !clear`` as
    plain YAML scalars. YAML interprets leading ``!`` as a tag, so quote only
    known expression fields and leave ordinary prose untouched.
    """
    pattern = re.compile(
        rf"^(\s*(?:-\s*)?(?:{'|'.join(sorted(EXPRESSION_SCALAR_KEYS))})\s*:\s*)(.+?)\s*$"
    )
    lines = text.splitlines()
    out: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        match = pattern.match(line)
        if not match:
            out.append(line)
            idx += 1
            continue
        prefix, raw_value = match.groups()
        base_indent = len(line) - len(line.lstrip(" "))
        continuation: list[str] = []
        cursor = idx + 1
        while cursor < len(lines):
            next_line = lines[cursor]
            if not next_line.strip():
                break
            next_indent = len(next_line) - len(next_line.lstrip(" "))
            stripped = next_line.strip()
            looks_like_next_key = bool(re.match(r"^(?:-\s*)?[A-Za-z_][A-Za-z0-9_-]*\s*:", stripped))
            if next_indent <= base_indent or looks_like_next_key:
                break
            continuation.append(stripped)
            cursor += 1
        if continuation and raw_value.strip()[:1] not in {"'", '"', "|", ">"}:
            raw_value = " ".join([raw_value.strip(), *continuation])
            idx = cursor
        else:
            idx += 1
        value, comment = _split_inline_comment(raw_value)
        if _needs_expression_quote(value):
            quoted = json.dumps(value.strip())
            out.append(prefix + quoted + (f" {comment}" if comment else ""))
        else:
            out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


_FLOW_MAPPING_LINE_RE = re.compile(r"^(\s*-\s*)\{\s*(.+?)\s*\}\s*$")
_FLOW_MAPPING_SPLIT_RE = re.compile(r"\s*,\s*(?=[A-Za-z_][A-Za-z0-9_]*\s*:)")
_FLOW_MAPPING_BRACKET_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_.]*\[[^\]\[]+\]")


def _expand_flow_mappings_with_brackets(text: str) -> str:
    """Rewrite ``- { key: REG[bit], ... }`` lines to block style.

    LLMs sometimes emit flow-style list items whose values contain bracketed
    register references such as ``IRQ_EN[0]`` or ``STATUS[3:0]``. PyYAML
    parses the ``[`` as starting a nested flow sequence, so the document
    fails to load. The semantically equivalent block form parses cleanly:

      - name: ST_BUSY
        enable_reg: "IRQ_EN[0]"
        ...

    This runs before YAML parsing as part of the deterministic repair pass.
    """
    out: list[str] = []
    for line in text.splitlines():
        match = _FLOW_MAPPING_LINE_RE.match(line)
        if not match or "[" not in line or "]" not in line:
            out.append(line)
            continue
        body = match.group(2)
        if not _FLOW_MAPPING_BRACKET_RE.search(body):
            out.append(line)
            continue
        prefix = match.group(1)
        dash_col = prefix.find("-")
        child_indent = " " * (dash_col + 2) if dash_col >= 0 else " " * len(prefix)
        first_indent = prefix
        pairs = _FLOW_MAPPING_SPLIT_RE.split(body)
        rewritten: list[str] = []
        bad = False
        for pidx, part in enumerate(pairs):
            if ":" not in part:
                bad = True
                break
            key, _, value = part.partition(":")
            value = value.strip()
            if value and value[0] not in {'"', "'"}:
                if _FLOW_MAPPING_BRACKET_RE.search(value):
                    value = '"' + value.replace('"', r'\"') + '"'
            indent = first_indent if pidx == 0 else child_indent
            rewritten.append(f"{indent}{key.strip()}: {value}")
        if bad or not rewritten:
            out.append(line)
        else:
            out.extend(rewritten)
    suffix = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + suffix


def _load_yaml(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    normalized = _expand_flow_mappings_with_brackets(_quote_expression_scalars(raw))
    doc = yaml.safe_load(normalized)
    if not isinstance(doc, dict):
        raise SystemExit(f"[repair_ssot_schema] {path} is not a YAML mapping")
    return doc


def _load_state(root: Path, ip: str) -> dict[str, Any]:
    path = root / ".session" / ip / "ssot-gen" / "state.json"
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _find_ssot(root: Path, ip: str) -> Path:
    for name in (f"{ip}.ssot.yaml", f"{ip}_ssot.yaml", f"{ip}.ssot.yml"):
        path = root / ip / "yaml" / name
        if path.is_file():
            return path
    raise SystemExit(f"[repair_ssot_schema] no SSOT YAML found for {ip}")


def _first_clock(doc: dict[str, Any]) -> tuple[str, int]:
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    freq = int(top.get("target", {}).get("clock_freq_mhz") or 100) if isinstance(top.get("target"), dict) else 100
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for dom in io.get("clock_domains") or []:
        if isinstance(dom, dict):
            name = dom.get("name") or "clk"
            ports = dom.get("ports") if isinstance(dom.get("ports"), list) else []
            if ports and isinstance(ports[0], dict) and ports[0].get("name"):
                name = ports[0]["name"]
            return str(name), int(dom.get("frequency_mhz") or freq)
    return "clk", freq


def _first_reset(doc: dict[str, Any]) -> tuple[str, str, str]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for rst in io.get("resets") or []:
        if isinstance(rst, dict):
            name = rst.get("name") or "rst_n"
            ports = rst.get("ports") if isinstance(rst.get("ports"), list) else []
            if ports and isinstance(ports[0], dict) and ports[0].get("name"):
                name = ports[0]["name"]
            return str(name), str(rst.get("polarity") or "active_low"), str(rst.get("sync_async") or "async_assert_sync_deassert")
    return "rst_n", "active_low", "async_assert_sync_deassert"


def _parameters(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in doc.get("parameters") or []:
        if isinstance(item, dict) and item.get("name"):
            out[str(item["name"])] = item.get("default")
    return out


def _decisions(state: dict[str, Any]) -> dict[str, str]:
    raw = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
    return {str(k): str(v) for k, v in raw.items() if str(v or "").strip()}


def _is_live(value: Any) -> bool:
    return value not in (None, "", [], {})


def _has_tbd(value: Any) -> bool:
    if isinstance(value, str):
        return "<TBD>" in value or "<placeholder>" in value or "TODO: confirm" in value
    if isinstance(value, list):
        return any(_has_tbd(v) for v in value)
    if isinstance(value, dict):
        return any(_has_tbd(v) for v in value.values())
    return False


def _norm_token(value: Any) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value or "")).strip("_")


def _smoke_scale_context(doc: dict[str, Any], ip: str) -> bool:
    """Detect intentionally small pipeline fixtures before applying production gates."""
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    custom = doc.get("custom") if isinstance(doc.get("custom"), dict) else {}
    text = " ".join(
        [
            str(ip),
            str(top.get("name") or ""),
            str(top.get("description") or ""),
            str(top.get("reference_spec") or ""),
            " ".join(str(item) for item in custom.get("assumptions") or []),
        ]
    ).lower()
    smoke_terms = ("smoke", "fixture", "tiny", "small", "narrow", "unit test", "unit-test", "example")
    if not any(term in text for term in smoke_terms):
        return False
    return not any(term in text for term in ("production", "signoff", "pl330", "dma330", "dma_330"))


def _rtl_quality_profile(doc: dict[str, Any], ip: str) -> str:
    qg = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
    rtl_gen = qg.get("rtl_gen") or qg.get("rtl-gen") if isinstance(qg, dict) else {}
    if not isinstance(rtl_gen, dict):
        rtl_gen = {}
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    raw = (
        rtl_gen.get("profile")
        or rtl_gen.get("quality_profile")
        or qg.get("rtl_quality_profile")
        or qg.get("quality_profile")
        or top.get("quality_profile")
        or top.get("rtl_quality_profile")
        or ""
    )
    if _smoke_scale_context(doc, ip):
        return "standard"
    norm = _norm_token(raw)
    if norm in {"prod", "production", "signoff", "pl330", "pl330_level", "dma330", "dma330_level"}:
        return "production"
    name_text = f"{ip} {top.get('name') or ''}".lower()
    if any(token in name_text for token in ("pl330", "dma330", "dma_330")):
        return "production"
    return "standard"


def _first_manifest_child(doc: dict[str, Any], ip: str) -> str:
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_names = {str(ip).lower(), str(top.get("name") or "").lower()}
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("ownership") or "manifest").lower() in {"child_ssot", "external", "blackbox"}:
            continue
        if bool(item.get("wiring_only")):
            continue
        name = str(item.get("name") or "")
        if name and name.lower() not in top_names:
            return name
    return str(top.get("name") or ip)


def _ensure_top_module(doc: dict[str, Any], state: dict[str, Any], ip: str) -> dict[str, Any]:
    decisions = _decisions(state)
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    kind = str(state.get("kind") or decisions.get("purpose") or "").lower()
    if not _is_live(top.get("type")) or _has_tbd(top.get("type")):
        if "sram" in kind or "memory" in kind:
            top["type"] = "memory"
        elif "bus" in kind or "interconnect" in kind:
            top["type"] = "bus"
        elif "dma" in kind:
            top["type"] = "dma"
        else:
            top["type"] = "peripheral"
    top["name"] = top.get("name") or ip
    if not _is_live(top.get("description")) or _has_tbd(top.get("description")):
        top["description"] = decisions.get("purpose") or f"{ip} leaf IP generated from approved ATLAS Web SSOT requirements"
    if not _is_live(top.get("file")) or _has_tbd(top.get("file")):
        top_name = str(top.get("name") or ip).strip()
        for item in doc.get("sub_modules") or []:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "").strip() == top_name and _is_live(item.get("file")):
                top["file"] = str(item.get("file")).strip()
                break
        else:
            top["file"] = f"rtl/{ip}.sv"
    target = top.get("target") if isinstance(top.get("target"), dict) else {}
    target.setdefault("technology", "generic")
    target.setdefault("clock_freq_mhz", 100)
    target.setdefault("area_um2", None)
    target.setdefault("power_mw", None)
    top.setdefault("version", "1.0")
    top.setdefault("reference_spec", "user-defined")
    top["target"] = target
    return top


def _filelist_rtl_entries(doc: dict[str, Any]) -> list[str]:
    filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
    return [str(item).strip() for item in filelist.get("rtl") or [] if str(item).strip()]


def _has_explicit_child_wiring(doc: dict[str, Any]) -> bool:
    integration = doc.get("integration") if isinstance(doc.get("integration"), dict) else {}
    if integration.get("connections") or integration.get("internal_interfaces"):
        return True
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        if item.get("ports") or item.get("connections") or item.get("internal_interfaces"):
            return True
    return False


def _decomposition_prefers_top_only(doc: dict[str, Any], ip: str) -> bool:
    decomp = doc.get("decomposition") if isinstance(doc.get("decomposition"), dict) else {}
    text = json.dumps(decomp, sort_keys=True, default=str).lower()
    if "monolithic" in text or "leaf ip" in text or "leaf_ip" in text:
        return True
    units = [item for item in decomp.get("units") or [] if isinstance(item, dict)]
    if not units:
        return False
    for unit in units:
        candidates = [str(item).strip() for item in unit.get("rtl_candidates") or [] if str(item).strip()]
        if candidates and any(candidate not in {ip, f"rtl/{ip}.sv"} for candidate in candidates):
            return False
    return True


def _should_collapse_to_top_module(doc: dict[str, Any], ip: str) -> bool:
    rtl_entries = _filelist_rtl_entries(doc)
    top_file = f"rtl/{ip}.sv"
    if rtl_entries and set(rtl_entries) != {top_file}:
        return False
    if _has_explicit_child_wiring(doc):
        return False
    return _decomposition_prefers_top_only(doc, ip)


def _ensure_sub_modules(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    # Resolve the SSOT-declared top module name and file. When the LLM emits a
    # top whose name differs from the IP name (e.g. `quad_spi_ctrl_top` for IP
    # `quad_spi_ctrl`), we must align the auto-generated wrapper sub_module to
    # the SSOT top so check_ssot_disk's structural invariants do not flag a
    # name/file collision. Falling back to `ip` preserves legacy IPs where
    # top_module.name == ip.
    top_module = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_name = str(top_module.get("name") or "").strip() or ip
    top_file = str(top_module.get("file") or "").strip() or f"rtl/{ip}.sv"

    def _top_wrapper_row(description: str) -> dict[str, Any]:
        return {
            "name": top_name,
            "file": top_file,
            "ownership": "manifest",
            "ssot_gen": True,
            "wiring_only": True,
            "description": description,
            "implements": ["top_module", "integration"],
            "source_sections": ["top_module", "io_list", "decomposition", "integration"],
            "decomposition_refs": ["decomposition"],
            "dataflow_refs": ["dataflow"],
        }

    def _apply_top_wrapper_defaults(row: dict[str, Any]) -> dict[str, Any]:
        defaults = _top_wrapper_row(
            str(row.get("description") or "Top-level integration module matching SSOT top_module")
        )
        merged = dict(row)
        merged["name"] = top_name
        merged["file"] = top_file
        merged["wiring_only"] = True
        for key, value in defaults.items():
            if key in {"name", "file", "wiring_only"}:
                continue
            if isinstance(value, list):
                existing = merged.get(key) if isinstance(merged.get(key), list) else []
                refs = [str(item).strip() for item in existing if str(item).strip()]
                for item in value:
                    if item not in refs:
                        refs.append(item)
                merged[key] = refs
            else:
                merged.setdefault(key, value)
        return merged

    if _should_collapse_to_top_module(doc, ip):
        return [{
            "name": top_name,
            "file": top_file,
            "ownership": "manifest",
            "ssot_gen": True,
            "description": "Top-level leaf implementation module matching SSOT top_module and monolithic decomposition.",
            "implements": ["top_module", "io_list", "function_model", "cycle_model", "decomposition"],
            "source_sections": ["top_module", "io_list", "parameters", "function_model", "cycle_model", "decomposition", "fsm", "features", "dataflow"],
            "function_model_refs": ["function_model.transactions", "function_model.state_variables"],
            "cycle_model_refs": ["cycle_model"],
            "decomposition_refs": ["decomposition"],
            "feature_refs": ["features"],
            "dataflow_refs": ["dataflow"],
            "fsm_refs": ["fsm"],
        }]
    subs = doc.get("sub_modules")
    if isinstance(subs, list) and subs and not _has_tbd(subs):
        fixed: list[dict[str, Any]] = []
        for item in subs:
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row_name = str(row.get("name") or "")
            row_file = str(row.get("file") or "")
            if row_name.endswith("_pkg") or row_file.endswith("_pkg.sv"):
                continue
            if row.get("name") in {f"{ip}_wrapper", "wrapper"}:
                row["name"] = top_name
                row["file"] = top_file
                row["description"] = "Top-level integration module matching SSOT top_module"
            # Drop any sub_module whose (name, file) silently duplicates the
            # top_module declaration. The top is declared by top_module and
            # appearing again as a sub_module breaks rtl-gen audit and the
            # check_ssot_disk invariant. Equivalent to the user-facing
            # invariant that flags `sub_modules[*].name == top_module.name`.
            row_top_collides = (
                (row.get("name") and row.get("name") == top_name)
                or (row.get("file") and row.get("file") == top_file)
            )
            if row_top_collides and row.get("wiring_only"):
                fixed.append(_apply_top_wrapper_defaults(row))
                continue
            if row_top_collides and not row.get("wiring_only"):
                continue
            # Drop sub_modules that share the IP name but the SSOT top is named
            # differently (`<ip>_top` is the new convention). They are leftover
            # LLM duplicates that conflict with the top declaration.
            if row.get("name") == ip and top_name != ip:
                continue
            ownership = str(row.get("ownership") or "manifest").lower()
            if (
                not _is_live(row.get("file"))
                and row_name
                and row_name != top_name
                and ownership not in {"child_ssot", "external", "blackbox", "conceptual", "verification", "coverage"}
            ):
                row["ownership"] = row.get("ownership") or "manifest"
                row["ssot_gen"] = row.get("ssot_gen", True)
                row["file"] = f"rtl/{row_name}.sv"
            fixed.append(row)
        # Only auto-append a wrapper sub_module entry when the SSOT top name
        # equals the IP name (legacy convention). When they differ — for
        # example top_module.name == `<ip>_top` — the top is fully described
        # by the `top_module:` section and must not also appear as a
        # sub_module (this would conflict with the check_ssot_disk invariant
        # that forbids `sub_modules[*].name == top_module.name`).
        if top_name == ip and not any(
            isinstance(item, dict) and item.get("name") == ip for item in fixed
        ):
            fixed.append(_top_wrapper_row("Top-level integration module matching SSOT top_module"))
        return fixed
    names = ["control", "datapath", "status", "core", "top"]
    desc = {
        "control": "Control/protocol sequencing derived from function_model and cycle_model",
        "datapath": "Datapath or payload transformation derived from approved features",
        "status": "Status, error, interrupt, and debug observability derived from SSOT",
        "core": "Primary behavior owner for function_model transactions and state updates",
        "top": "Top-level integration module matching SSOT top_module",
    }
    return [
        {
            "name": ip if name == "top" else f"{ip}_{name}",
            "file": f"rtl/{ip}.sv" if name == "top" else f"rtl/{ip}_{name}.sv",
            "ownership": "manifest",
            "ssot_gen": True,
            "description": desc[name],
            **(
                _top_wrapper_row(desc[name])
                if name == "top"
                else {}
            ),
        }
        for name in names
    ]


def _ensure_decomposition(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    existing = doc.get("decomposition") if isinstance(doc.get("decomposition"), dict) else {}
    sub_modules = [item for item in doc.get("sub_modules") or [] if isinstance(item, dict)]
    owners = []
    for item in sub_modules:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        owners.append({
            "module": name,
            "file": item.get("file") or f"rtl/{name}.sv",
            "responsibility": item.get("description") or "Implements the SSOT-owned behavior and interface contract assigned to this module.",
            "source_sections": item.get("source_sections") or item.get("function_model_refs") or ["function_model", "cycle_model", "io_list"],
        })
    existing.setdefault("strategy", "manifest_owned_leaf_decomposition")
    existing.setdefault("owners", owners)
    existing.setdefault("integration_policy", "Top-level wiring must be backed by integration.connections or sub_modules[].connections before signoff.")
    existing.setdefault("source_refs", ["sub_modules", "function_model", "cycle_model", "integration"])
    return existing


def _tokens_from(value: Any) -> set[str]:
    text = json.dumps(value, sort_keys=True, default=str) if isinstance(value, (dict, list)) else str(value or "")
    chars = [ch.lower() if ch.isalnum() else " " for ch in text]
    return {tok for tok in "".join(chars).split() if len(tok) > 1}


def _append_unique_ref(row: dict[str, Any], key: str, ref: str) -> None:
    existing = row.get(key)
    refs = [str(item).strip() for item in existing if str(item).strip()] if isinstance(existing, list) else []
    if ref not in refs:
        refs.append(ref)
    row[key] = refs


def _expr_tokens(expr: Any) -> set[str]:
    text = str(expr or "")
    chars = [ch if (ch.isalnum() or ch == "_") else " " for ch in text]
    return {tok for tok in "".join(chars).split() if tok}


def _choose_behavior_owner(candidates: list[dict[str, Any]], terms: set[str]) -> dict[str, Any] | None:
    if not candidates:
        return None
    preferred = {
        "reset": {"reset", "init", "fsm", "control", "manager", "core"},
        "csr": {"csr", "reg", "register", "apb", "cfg", "config", "status", "control"},
        "register": {"csr", "reg", "register", "apb", "cfg", "config", "status", "control"},
        "debug": {"debug", "csr", "control", "status"},
        "interrupt": {"irq", "intr", "interrupt", "event", "status", "control"},
        "error": {"fault", "error", "abort", "status", "control"},
        "state": {"state", "fsm", "thread", "manager", "control", "core"},
    }
    boosted_terms = set(terms)
    for term, boosts in preferred.items():
        if term in terms:
            boosted_terms |= boosts
    best: tuple[int, int, dict[str, Any]] | None = None
    for idx, row in enumerate(candidates):
        row_terms = _tokens_from({
            "name": row.get("name"),
            "description": row.get("description"),
            "source_sections": row.get("source_sections"),
        })
        score = len(boosted_terms & row_terms)
        if row.get("function_model_refs"):
            score += 1
        if best is None or score > best[0]:
            best = (score, -idx, row)
    return best[2] if best else candidates[0]


def _ensure_submodule_behavior_ownership(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    subs: list[dict[str, Any]] = []
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    merge_list_keys = (
        "implements",
        "source_sections",
        "function_model_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "fsm_refs",
        "decomposition_refs",
        "test_refs",
        "register_refs",
        "trace_refs",
        "ssot_refs",
    )
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        row = dict(item)
        key = (
            str(row.get("name") or "").strip(),
            str(row.get("file") or "").strip(),
        )
        if key in by_key:
            target = by_key[key]
            for list_key in merge_list_keys:
                for ref in row.get(list_key) or []:
                    _append_unique_ref(target, list_key, str(ref))
            for scalar_key, value in row.items():
                if scalar_key in merge_list_keys:
                    continue
                if scalar_key not in target and value not in (None, "", []):
                    target[scalar_key] = value
            continue
        by_key[key] = row
        subs.append(row)
    top_names = {ip, f"{ip}_top", "top", "wrapper"}
    def is_active_owner(row: dict[str, Any]) -> bool:
        ownership = str(row.get("ownership") or "manifest").lower()
        if ownership in {"child_ssot", "external", "blackbox", "conceptual", "verification", "coverage"}:
            return False
        if row.get("rtl_emit") is False or bool(row.get("wiring_only")):
            return False
        return True

    def is_top(row: dict[str, Any]) -> bool:
        return str(row.get("name") or "") in top_names or Path(str(row.get("file") or "")).stem in top_names

    active = [row for row in subs if is_active_owner(row)]
    candidates = [row for row in active if not is_top(row)] or [row for row in active if is_top(row)]
    if not candidates:
        owner = next(
            (
                row for row in subs
                if str(row.get("name") or "").strip() == f"{ip}_behavior_contract"
            ),
            None,
        )
        if owner is None:
            owner = {
                "name": f"{ip}_behavior_contract",
                "ownership": "conceptual",
                "ssot_gen": False,
                "rtl_emit": False,
                "description": "Conceptual owner for SSOT function-model behavior implemented by the generated RTL.",
                "source_sections": ["function_model", "cycle_model", "features", "test_requirements"],
            }
            subs.insert(0, owner)
        else:
            for ref in ["function_model", "cycle_model", "features", "test_requirements"]:
                _append_unique_ref(owner, "source_sections", ref)
        candidates = [owner]

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            continue
        tx_id = str(tx.get("id") or tx.get("name") or idx).strip()
        if not tx_id:
            continue
        owner = _choose_behavior_owner(candidates, _tokens_from(tx))
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", f"function_model.transactions.{tx_id}")

    if fm.get("state_variables"):
        owner = _choose_behavior_owner(candidates, {"state", "register", "status", "csr", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.state_variables")

    if fm.get("outputs"):
        owner = _choose_behavior_owner(candidates, {"output", "status", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.outputs")
    if fm.get("inputs"):
        owner = _choose_behavior_owner(candidates, {"input", "interface", "control"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.inputs")

    if fm.get("invariants"):
        owner = _choose_behavior_owner(candidates, {"invariant", "error", "state", "control", "core"})
        if owner is not None:
            _append_unique_ref(owner, "function_model_refs", "function_model.invariants")
            _append_unique_ref(owner, "source_sections", "function_model")

    if isinstance(doc.get("cycle_model"), dict) and doc["cycle_model"]:
        owner = _choose_behavior_owner(candidates, {"cycle", "handshake", "pipeline", "control"})
        if owner is not None:
            _append_unique_ref(owner, "cycle_model_refs", "cycle_model")
            _append_unique_ref(owner, "source_sections", "cycle_model")

    if isinstance(doc.get("features"), list) and doc["features"]:
        owner = _choose_behavior_owner(candidates, {"feature", "datapath", "core", "control"})
        if owner is not None:
            _append_unique_ref(owner, "feature_refs", "features")
            _append_unique_ref(owner, "source_sections", "features")

    if isinstance(doc.get("dataflow"), dict) and doc["dataflow"]:
        owner = _choose_behavior_owner(candidates, {"dataflow", "datapath", "core", "routing"})
        if owner is not None:
            _append_unique_ref(owner, "dataflow_refs", "dataflow")
            _append_unique_ref(owner, "source_sections", "dataflow")

    if isinstance(doc.get("fsm"), dict) and doc["fsm"]:
        owner = _choose_behavior_owner(candidates, {"fsm", "state", "control", "manager"})
        if owner is not None:
            _append_unique_ref(owner, "fsm_refs", "fsm")
            _append_unique_ref(owner, "source_sections", "fsm")

    if isinstance(doc.get("decomposition"), dict) and doc["decomposition"]:
        owner = _choose_behavior_owner(candidates, {"decomposition", "datapath", "control", "core", "top"})
        if owner is not None:
            _append_unique_ref(owner, "decomposition_refs", "decomposition")
            _append_unique_ref(owner, "source_sections", "decomposition")

    tests = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    if isinstance(tests.get("scenarios"), list) and tests["scenarios"]:
        owner = _choose_behavior_owner(candidates, {"test", "scenario", "coverage", "core"})
        if owner is not None:
            _append_unique_ref(owner, "test_refs", "test_requirements")
            _append_unique_ref(owner, "source_sections", "test_requirements")

    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    if isinstance(regs.get("register_list"), list) and regs["register_list"]:
        owner = _choose_behavior_owner(candidates, {"register", "csr", "status", "control"})
        if owner is not None:
            _append_unique_ref(owner, "register_refs", "registers.register_list")
            _append_unique_ref(owner, "source_sections", "registers")

    return subs


def _valid_ready_contract_required(doc: dict[str, Any]) -> bool:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for intf in io.get("interfaces") or []:
        if not isinstance(intf, dict):
            continue
        text = " ".join(str(intf.get(key) or "") for key in ("name", "type", "description")).lower()
        if "valid_ready" in text or ("valid" in text and "ready" in text):
            return True
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    for rule in cm.get("handshake_rules") or []:
        if isinstance(rule, dict):
            text = json.dumps(rule, sort_keys=True, default=str).lower()
        else:
            text = str(rule).lower()
        if "valid" in text and "ready" in text:
            return True
    return False


def _ensure_rtl_contract_consistency(doc: dict[str, Any]) -> None:
    contract = doc.get("rtl_contract")
    if not isinstance(contract, dict) or not _valid_ready_contract_required(doc):
        return
    ready = str(contract.get("ready_output") or "").strip()
    sample = str(contract.get("sample_condition") or "").strip()
    if not ready or not sample:
        return
    tokens = _expr_tokens(sample)
    if ready in tokens:
        return
    has_valid_input = any(tok == "valid" or tok.endswith("_valid") for tok in tokens)
    if not has_valid_input:
        return
    contract["sample_condition"] = f"({sample}) and {ready}"


def _all_interface_ports(doc: dict[str, Any]) -> list[dict[str, Any]]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    ports: list[dict[str, Any]] = []
    for intf in io.get("interfaces") or []:
        if not isinstance(intf, dict):
            continue
        for port in intf.get("ports") or []:
            if isinstance(port, dict) and port.get("name"):
                ports.append(port)
    return ports


def _port_widths(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        str(port.get("name")): port.get("width", 1)
        for port in _all_interface_ports(doc)
        if str(port.get("name") or "").strip()
    }


def _ports_by_direction(doc: dict[str, Any], direction: str) -> list[str]:
    requested = str(direction or "").lower()
    return [
        str(port.get("name"))
        for port in _all_interface_ports(doc)
        if (
            str(port.get("direction") or "").lower() == requested
            or (requested == "output" and str(port.get("direction") or "").lower() == "inout")
            or (requested == "input" and str(port.get("direction") or "").lower() == "inout")
        )
        and str(port.get("name") or "").strip()
    ]


def _concrete_port_ref(value: Any, valid_ports: set[str]) -> str:
    raw = str(value or "").strip()
    if raw in valid_ports:
        return raw
    parts = [part for part in re.split(r"[^A-Za-z0-9_]+", raw) if part]
    for part in reversed(parts):
        if part in valid_ports:
            return part
    return raw


def _normalize_contract_port_maps(contract: dict[str, Any], doc: dict[str, Any]) -> None:
    input_ports = set(_ports_by_direction(doc, "input"))
    output_ports = set(_ports_by_direction(doc, "output"))
    all_ports = input_ports | output_ports

    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    normalized_input: dict[str, str] = {}
    for field, port in input_map.items():
        normalized_input[str(field)] = _concrete_port_ref(port, all_ports)
    if normalized_input:
        contract["input_map"] = normalized_input

    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    normalized_output: dict[str, str] = {}
    for field, port in output_map.items():
        normalized_output[str(field)] = _concrete_port_ref(port, output_ports)
    if normalized_output:
        contract["output_map"] = normalized_output


def _ensure_rtl_contract(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    contract = dict(doc.get("rtl_contract")) if isinstance(doc.get("rtl_contract"), dict) else {}
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    txs = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
    tx_id = str((txs[0].get("id") if txs else "") or "FM_PRIMARY")
    clock, _ = _first_clock(doc)
    reset, polarity, _ = _first_reset(doc)
    ports = _all_interface_ports(doc)
    input_names = [
        str(port.get("name"))
        for port in ports
        if str(port.get("direction") or "").lower() == "input"
        and str(port.get("name")) not in {clock, reset}
    ]
    output_names = [
        str(port.get("name"))
        for port in ports
        if str(port.get("direction") or "").lower() == "output"
    ]
    ready = next((name for name in output_names if name == "ready" or name.endswith("_ready")), "")
    valid = next((name for name in input_names if name == "valid" or name.endswith("_valid")), "")
    start = next((name for name in input_names if name in {"start", "enable", "go"} or name.endswith("_start")), "")
    output_valid = next((name for name in output_names if name == "result_valid" or name.endswith("_valid")), "")
    contract.setdefault("owner", "ssot-gen")
    contract.setdefault("type", "ssot_derived_rule_contract")
    requested_tx = str(contract.get("transaction") or contract.get("transaction_id") or "").strip()
    known_txs = {
        str(tx.get(key) or "").strip().lower()
        for tx in txs
        for key in ("id", "name")
        if str(tx.get(key) or "").strip()
    }
    if not requested_tx or requested_tx.lower() not in known_txs:
        contract["transaction"] = tx_id
    else:
        contract.setdefault("transaction", tx_id)
    contract.setdefault("clock", clock)
    contract.setdefault("reset", reset)
    contract.setdefault("reset_active", "low" if "low" in polarity else "high")
    if valid and ready:
        contract.setdefault("sample_condition", f"{valid} && {ready}")
    elif start:
        contract.setdefault("sample_condition", start)
    else:
        contract.setdefault("sample_condition", "legal transaction accepted under cycle_model.handshake_rules")
    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    for name in input_names:
        if name not in {valid, ready}:
            input_map.setdefault(name, name)
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    for name in output_names:
        output_map.setdefault(name, name)
    contract["input_map"] = input_map or {"request": "declared input ports"}
    contract["output_map"] = output_map or {"response": "declared output ports"}
    if ready:
        contract.setdefault("ready_output", ready)
    if output_valid:
        contract.setdefault("output_valid", output_valid)
    contract.setdefault("contract_invariants", [
        "RTL-visible behavior implements the referenced function_model transaction.",
        "Input sampling and output observation follow cycle_model handshake and latency rules.",
    ])
    _normalize_contract_port_maps(contract, doc)
    return contract


def _infer_primary_input_port(doc: dict[str, Any], contract: dict[str, Any]) -> str:
    input_ports = _ports_by_direction(doc, "input")
    clock, _ = _first_clock(doc)
    reset, _, _ = _first_reset(doc)
    excluded = {clock, reset, "valid", "enable", "start", "go"}
    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    for key in ("data_in", "value", "data", "payload", "req_data", "in_data"):
        mapped = _concrete_port_ref(input_map.get(key), set(input_ports)) if key in input_map else ""
        if mapped in input_ports:
            return mapped
    for name in input_ports:
        low = name.lower()
        if low in excluded or low.endswith("_valid") or low.endswith("_ready"):
            continue
        if any(token in low for token in ("data", "payload", "value")):
            return name
    return next((name for name in input_ports if name not in {clock, reset}), "")


def _infer_primary_output_port(doc: dict[str, Any], contract: dict[str, Any]) -> str:
    output_ports = _ports_by_direction(doc, "output")
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    for key in ("result", "data_out", "out_data", "rsp_data", "response", "value"):
        mapped = _concrete_port_ref(output_map.get(key), set(output_ports)) if key in output_map else ""
        if mapped in output_ports:
            return mapped
    for name in output_ports:
        low = name.lower()
        if low in {"ready", "valid", "result_valid", "done", "error"} or low.endswith("_valid") or low.endswith("_ready"):
            continue
        if any(token in low for token in ("result", "data", "payload", "value", "response")):
            return name
    return next((name for name in output_ports if not name.endswith("_valid") and not name.endswith("_ready")), "")


def _mentions_shift_left_by_one(text: str) -> bool:
    low = text.lower()
    return (
        "shift left by one" in low
        or "shifted left by one" in low
        or "left-shift-by-one" in low
        or "left shift by 1" in low
        or "<< 1" in low
        or "multiply by two" in low
        or "multiplied by two" in low
        or "times two" in low
        or "data_in*2" in low.replace(" ", "")
    )


def _verilog_literal_to_int(match: re.Match[str]) -> str:
    width_text, base_text, value_text = match.group(1), match.group(2).lower(), match.group(3)
    base = {"b": 2, "o": 8, "d": 10, "h": 16}[base_text]
    cleaned = value_text.replace("_", "")
    cleaned = re.sub(r"[xXzZ?]", "0", cleaned)
    try:
        return str(int(cleaned or "0", base))
    except ValueError:
        return "0"


def _strip_outer_parens(text: str) -> str:
    text = text.strip()
    if not (text.startswith("(") and text.endswith(")")):
        return text
    depth = 0
    for idx, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and idx != len(text) - 1:
                return text
        if depth < 0:
            return text
    return text[1:-1].strip() if depth == 0 else text


def _find_top_level_char(text: str, target: str, start: int = 0) -> int:
    depth = 0
    quote = ""
    escaped = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if escaped:
            escaped = False
            continue
        if quote:
            if ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
            continue
        if ch in {"'", '"'}:
            quote = ch
            continue
        if ch in "([{":
            depth += 1
            continue
        if ch in ")]}":
            depth = max(depth - 1, 0)
            continue
        if ch == target and depth == 0:
            return idx
    return -1


def _convert_c_ternary_expr(text: str) -> str:
    q_idx = _find_top_level_char(text, "?")
    if q_idx < 0:
        return text
    c_idx = _find_top_level_char(text, ":", q_idx + 1)
    if c_idx < 0:
        return text
    cond = _strip_outer_parens(text[:q_idx])
    when_true = _convert_c_ternary_expr(text[q_idx + 1:c_idx].strip())
    when_false = _convert_c_ternary_expr(text[c_idx + 1:].strip())
    if not cond or not when_true or not when_false:
        return text
    return f"({when_true} if {cond} else {when_false})"


def _normalize_rule_expr(expr: Any) -> Any:
    if not isinstance(expr, str):
        return expr
    text = expr.strip()
    if not text:
        return expr
    text = re.sub(r"\b(\d+)?'[sS]?([bBoOdDhH])([0-9a-fA-F_xXzZ?]+)\b", _verilog_literal_to_int, text)
    text = re.sub(r"(?<![0-9A-Za-z_])'([01])(?![0-9A-Za-z_])", r"\1", text)
    text = re.sub(r"(?<![0-9A-Za-z_])'[xXzZ?](?![0-9A-Za-z_])", "0", text)
    text = _convert_c_ternary_expr(text)
    concat_shift = re.fullmatch(r"\(?\s*\{\s*0\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\s*<<\s*(\d+)\s*\)?", text)
    if concat_shift:
        return f"{concat_shift.group(1)} << {concat_shift.group(2)}"
    wrapped_concat_shift = re.fullmatch(r"\(?\s*\(\s*\{\s*0\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\s*\)\s*<<\s*(\d+)\s*\)?", text)
    if wrapped_concat_shift:
        return f"{wrapped_concat_shift.group(1)} << {wrapped_concat_shift.group(2)}"
    zero_extend = re.fullmatch(r"\{?\s*0\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}?", text)
    if zero_extend:
        return zero_extend.group(1)
    return text


def _normalize_machine_rule_exprs(doc: dict[str, Any]) -> None:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for tx in fm.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        if "sample_condition" in tx:
            tx["sample_condition"] = _normalize_rule_expr(tx.get("sample_condition"))
        for key in ("output_rules", "state_updates"):
            for rule in tx.get(key) or []:
                if not isinstance(rule, dict):
                    continue
                for expr_key in ("expr", "expression", "value"):
                    if expr_key in rule:
                        rule[expr_key] = _normalize_rule_expr(rule.get(expr_key))
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    for rule in contract.get("output_rules") or []:
        if not isinstance(rule, dict):
            continue
        for expr_key in ("expr", "expression", "value"):
            if expr_key in rule:
                rule[expr_key] = _normalize_rule_expr(rule.get(expr_key))


def _fm_list(fm: dict[str, Any], key: str) -> list[Any]:
    value = fm.get(key)
    if not isinstance(value, list):
        value = []
        fm[key] = value
    return value


def _add_or_update_derived_signal(
    fm: dict[str, Any],
    *,
    name: str,
    expr: str,
    width: Any,
    description: str,
) -> None:
    items = _fm_list(fm, "derived_signals")
    for item in items:
        if isinstance(item, dict) and str(item.get("name") or item.get("signal") or item.get("id") or "") == name:
            item["expr"] = expr
            item["width"] = width
            item.setdefault("description", description)
            item.setdefault("source", "repair_ssot_schema.apb_helper")
            return
    items.append({
        "name": name,
        "expr": expr,
        "width": width,
        "description": description,
        "source": "repair_ssot_schema.apb_helper",
    })


def _ssot_width(value: Any, default: Any = 1) -> Any:
    """Return a validator-friendly width without losing parameterized values."""

    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return default
    if re.fullmatch(r"\d+", text):
        return int(text)
    return text


def _ssot_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        return default
    try:
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text, 10)
    except ValueError:
        return default


def _reg_helper_name(name: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(name or "").strip()).strip("_").lower()
    return text or "reg"


def _state_expr_for_register(reg_name: str, state_names: set[str]) -> str:
    base = _reg_helper_name(reg_name)
    candidates = [
        base,
        f"{base}_reg",
        base.replace("data_in", "gpio_in_sync"),
        base.replace("irq_raw", "irq_raw_reg"),
        base.replace("irq_status", "irq_status_reg"),
        base.replace("irq_en_rise", "irq_en_rise_reg"),
        base.replace("irq_en_fall", "irq_en_fall_reg"),
        base.replace("data_out", "data_out_reg"),
        base.replace("dir", "dir_reg"),
    ]
    for cand in candidates:
        if cand in state_names:
            return cand
    return "0"


def _nested_if_expr(rows: list[tuple[str, str]], default: str = "0") -> str:
    expr = default
    for cond, value in reversed(rows):
        expr = f"({value} if {cond} else {expr})"
    return expr


def _apb_byte_mask_expr(*, pstrb_width: Any, data_width: Any) -> str:
    data_width_i = _ssot_int(data_width, 32) or 32
    strb_width_i = _ssot_int(pstrb_width, None)
    if strb_width_i is None:
        strb_width_i = max(1, (data_width_i + 7) // 8)
    lanes = max(1, min(strb_width_i, max(1, (data_width_i + 7) // 8)))
    hex_digits = max(2, (data_width_i + 3) // 4)
    terms = []
    for lane in range(lanes):
        mask = 0xFF << (lane * 8)
        terms.append(f"(0x{mask:0{hex_digits}X} if (pstrb & 0x{1 << lane:X}) != 0 else 0)")
    return "(" + " | ".join(terms) + ")"


def _ensure_apb_register_decode_helpers(doc: dict[str, Any], fm: dict[str, Any]) -> None:
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    reg_list = [item for item in regs.get("register_list") or [] if isinstance(item, dict)]
    inputs = set(_ports_by_direction(doc, "input"))
    if not reg_list or "paddr" not in inputs:
        return

    offsets: list[tuple[dict[str, Any], int]] = []
    for reg in reg_list:
        offset = _ssot_int(reg.get("offset"), None)
        if offset is None:
            continue
        offsets.append((reg, offset))
    if not offsets:
        return

    data_width = _ssot_width(
        _port_widths(doc).get("prdata"),
        (regs.get("config") if isinstance(regs.get("config"), dict) else {}).get("register_width", 32),
    )
    state_names = {
        str(item.get("name") or "").strip()
        for item in fm.get("state_variables") or []
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    addr_name = "addr"
    legal_terms = [f"({addr_name} == {offset})" for _reg, offset in offsets]
    _add_or_update_derived_signal(
        fm,
        name="legal_addr",
        expr=" or ".join(legal_terms) if legal_terms else "0",
        width=1,
        description="APB legal address decode derived from registers.register_list offsets.",
    )

    read_rows: list[tuple[str, str]] = []
    for reg, offset in offsets:
        helper = _reg_helper_name(reg.get("name"))
        read_rows.append((f"{addr_name} == {offset}", _state_expr_for_register(helper, state_names)))
        _add_or_update_derived_signal(
            fm,
            name=f"wr_{helper}",
            expr=f"apb_valid_write and ({addr_name} == {offset})",
            width=1,
            description=f"APB write decode helper for register {reg.get('name')}.",
        )
        _add_or_update_derived_signal(
            fm,
            name=f"rd_{helper}",
            expr=f"apb_valid_read and ({addr_name} == {offset})",
            width=1,
            description=f"APB read decode helper for register {reg.get('name')}.",
        )
        access = str(reg.get("access") or "").lower()
        field_text = json.dumps(reg.get("fields") or [], default=str).lower()
        if "w1c" in access or "w1c" in field_text or helper.endswith("irq_status"):
            _add_or_update_derived_signal(
                fm,
                name=f"{helper}_w1c",
                expr=f"((pwdata & gpio_mask) if wr_{helper} else 0)",
                width=_ssot_width(reg.get("width"), data_width),
                description=f"W1C write mask helper for register {reg.get('name')}.",
            )

    _add_or_update_derived_signal(
        fm,
        name="read_mux",
        expr=_nested_if_expr(read_rows, "0"),
        width=data_width,
        description="APB read data mux derived from registers.register_list offsets and function_model state variables.",
    )


def _ensure_apb_helper_signals(doc: dict[str, Any], fm: dict[str, Any]) -> None:
    """Make common APB phase predicates explicit SSOT-derived signals.

    LLM SSOT drafts often use names such as ``apb_valid_write`` inside
    function/output rules.  Those are not top-level ports and should not become
    user-facing questions when APB pins already make the meaning mechanical.
    """

    inputs = set(_ports_by_direction(doc, "input"))
    if not {"psel", "penable"}.issubset(inputs):
        return
    _add_or_update_derived_signal(
        fm,
        name="apb_access",
        expr="psel and penable",
        width=1,
        description="APB access phase helper derived from psel and penable.",
    )
    if "pwrite" in inputs:
        _add_or_update_derived_signal(
            fm,
            name="apb_valid_write",
            expr="psel and penable and pwrite",
            width=1,
            description="APB write access helper derived from psel, penable, and pwrite.",
        )
        _add_or_update_derived_signal(
            fm,
            name="apb_valid_read",
            expr="psel and penable and not pwrite",
            width=1,
            description="APB read access helper derived from psel, penable, and pwrite.",
        )
    if "paddr" in inputs:
        _add_or_update_derived_signal(
            fm,
            name="addr",
            expr="paddr",
            width=_ssot_width(_port_widths(doc).get("paddr"), 32),
            description="Register address helper derived from the APB paddr input.",
        )
    if "pstrb" in inputs:
        widths = _port_widths(doc)
        regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
        reg_config = regs.get("config") if isinstance(regs.get("config"), dict) else {}
        data_width = _ssot_width(
            widths.get("pwdata"),
            widths.get("prdata", reg_config.get("register_width", 32)),
        )
        _add_or_update_derived_signal(
            fm,
            name="wmask",
            expr=_apb_byte_mask_expr(pstrb_width=widths.get("pstrb", 4), data_width=data_width),
            width=data_width,
            description="APB byte-lane write mask expanded from pstrb.",
        )
    _ensure_apb_register_decode_helpers(doc, fm)


def _ensure_transaction_output_summaries(doc: dict[str, Any]) -> None:
    """Populate required transaction outputs from existing machine rules.

    This is a structural repair only: it mirrors already-authored output_rules
    and state_updates into the prose/summary `outputs` field required by the
    canonical SSOT validator. It must not invent new behavior.
    """

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for tx in fm.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        outputs = tx.get("outputs") if isinstance(tx.get("outputs"), list) else []
        seen: set[str] = set()
        for item in outputs:
            if isinstance(item, dict):
                key = str(item.get("port") or item.get("name") or item.get("state") or "").strip()
            else:
                key = str(item).strip()
            if key:
                seen.add(key)
        for rule in tx.get("output_rules") or []:
            if not isinstance(rule, dict):
                continue
            name = str(rule.get("name") or rule.get("output") or rule.get("port") or "").strip()
            port = str(rule.get("port") or rule.get("output_port") or "").strip()
            expr = rule.get("expr", rule.get("expression", rule.get("value", "")))
            key = port or name
            if key and key not in seen:
                outputs.append(
                    {
                        "name": name or port,
                        "port": port or name,
                        "expr": _normalize_rule_expr(expr),
                        "description": rule.get("description")
                        or "Mirrored from executable output_rules for SSOT validator completeness.",
                    }
                )
                seen.add(key)
        for update in tx.get("state_updates") or []:
            if not isinstance(update, dict):
                continue
            name = str(update.get("name") or update.get("state") or update.get("target") or "").strip()
            expr = update.get("expr", update.get("expression", update.get("value", update.get("next_value", ""))))
            if name and name not in seen:
                outputs.append(
                    {
                        "state": name,
                        "expr": _normalize_rule_expr(expr),
                        "description": update.get("description")
                        or "Mirrored from executable state_updates for SSOT validator completeness.",
                    }
                )
                seen.add(name)
        if outputs:
            tx["outputs"] = outputs


def _ensure_state_update_widths(doc: dict[str, Any]) -> None:
    """Fill validator-required state_update widths from declared state variables."""

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    if not isinstance(fm, dict):
        return
    state_widths: dict[str, int] = {}
    for state in fm.get("state_variables") or []:
        if not isinstance(state, dict):
            continue
        name = str(state.get("name") or "").strip()
        if not name:
            continue
        try:
            width = int(state.get("width") or 1)
        except Exception:
            width = 1
        state_widths[name] = max(1, width)
    for tx in fm.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        updates = tx.get("state_updates")
        if not isinstance(updates, list):
            continue
        for update in updates:
            if not isinstance(update, dict) or update.get("width") not in (None, ""):
                continue
            name = str(update.get("name") or update.get("state") or update.get("target") or "").strip()
            update["width"] = state_widths.get(name, 1)


def _rewrite_self_referential_output_defaults(doc: dict[str, Any]) -> None:
    """Remove output self-feedback fallbacks from observable rules.

    ``pready = 1 if apb_valid_write else pready`` is a common model draft
    artifact.  In SSOT transaction rules the precondition/sample condition owns
    when the rule is observed; feeding the output port back into its own
    same-cycle expression creates an artificial RTL_OUTPUT_DEP blocker.
    """

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}

    def rewrite(rule: dict[str, Any]) -> None:
        expr_key = next((key for key in ("expr", "expression", "value") if key in rule), "")
        if not expr_key:
            return
        expr = str(rule.get(expr_key) or "").strip()
        if not expr:
            return
        self_names = {
            str(rule.get("name") or "").strip(),
            str(rule.get("port") or "").strip(),
        }
        for key in tuple(self_names):
            if key in output_map:
                self_names.add(str(output_map.get(key) or "").strip())
        self_names = {name for name in self_names if name}
        match = re.fullmatch(
            r"(?P<then>.+?)\s+if\s+(?P<cond>.+?)\s+else\s+(?P<otherwise>\(?\s*[A-Za-z_][A-Za-z0-9_]*\s*\)?)",
            expr,
        )
        if not match:
            return
        otherwise = _strip_outer_parens(match.group("otherwise").strip())
        if otherwise in self_names:
            rule[expr_key] = match.group("then").strip()
            rule.setdefault(
                "repair_note",
                "Removed self-referential output fallback; transaction precondition/sample_condition owns rule applicability.",
            )

    for tx in fm.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        for rule in tx.get("output_rules") or []:
            if isinstance(rule, dict):
                rewrite(rule)
    for rule in contract.get("output_rules") or []:
        if isinstance(rule, dict):
            rewrite(rule)


def _ensure_ready_constant_policy(doc: dict[str, Any]) -> None:
    """Record explicit SSOT allowance for always-ready interfaces.

    rtl-gen rejects constant-driven top outputs unless the SSOT states that the
    constant is intentional. A valid/ready sink with ready specified HIGH during
    reset/idle is one such intentional contract.
    """

    context = json.dumps(
        {
            "io_list": doc.get("io_list"),
            "cycle_model": doc.get("cycle_model"),
            "features": doc.get("features"),
            "workflow_todos": doc.get("workflow_todos"),
        },
        sort_keys=True,
        default=str,
    ).lower()
    if "ready" not in context or not ("high" in context or "ready=1" in context or "1'b1" in context):
        return
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for iface in io.get("interfaces") or []:
        if not isinstance(iface, dict):
            continue
        ports = iface.get("ports") if isinstance(iface.get("ports"), list) else []
        for port in ports:
            if not isinstance(port, dict):
                continue
            if str(port.get("name") or "").strip() != "ready":
                continue
            if str(port.get("direction") or "").strip().lower() != "output":
                continue
            port.setdefault("allow_constant", True)
            port.setdefault("tieoff", "1'b1")
            port.setdefault("constant_value", "1'b1")


def _state_name_for_internal_output_rule(rule: dict[str, Any], state_names: set[str]) -> str:
    raw_values = [
        str(rule.get("port") or "").strip(),
        str(rule.get("name") or "").strip(),
    ]
    candidates: list[str] = []
    for raw in raw_values:
        if not raw:
            continue
        pieces = [part for part in re.split(r"[^A-Za-z0-9_]+", raw) if part]
        for value in [raw, *reversed(pieces)]:
            if value and value not in candidates:
                candidates.append(value)
            if value.endswith("_next"):
                base = value[: -len("_next")]
                for item in (f"{base}_q", base):
                    if item and item not in candidates:
                        candidates.append(item)
            if value.endswith("_d"):
                base = value[: -len("_d")]
                for item in (f"{base}_q", base):
                    if item and item not in candidates:
                        candidates.append(item)
    for candidate in candidates:
        if candidate in state_names:
            return candidate
    return candidates[0] if candidates else ""


def _move_internal_output_rules_to_state_updates(
    txs: list[dict[str, Any]],
    *,
    output_ports: set[str],
    output_map: dict[str, Any],
    state_names: set[str],
) -> None:
    if not output_ports:
        return
    for tx in txs:
        rules = tx.get("output_rules") if isinstance(tx.get("output_rules"), list) else []
        if not rules:
            continue
        kept_rules: list[Any] = []
        updates = tx.get("state_updates") if isinstance(tx.get("state_updates"), list) else []
        existing_updates = {
            str(item.get("name") or item.get("state") or "").strip()
            for item in updates
            if isinstance(item, dict)
        }
        for rule in rules:
            if not isinstance(rule, dict):
                kept_rules.append(rule)
                continue
            name = str(rule.get("name") or "").strip()
            raw_port = rule.get("port") or rule.get("output_port")
            if (raw_port is None or str(raw_port).strip() == "") and name:
                raw_port = output_map.get(name)
            port = _concrete_port_ref(raw_port or name, output_ports)
            if port in output_ports:
                rule["port"] = port
                kept_rules.append(rule)
                continue

            state_name = _state_name_for_internal_output_rule(rule, state_names)
            if not state_name:
                continue
            if state_name not in existing_updates:
                updates.append(
                    {
                        "name": state_name,
                        "expr": _normalize_rule_expr(rule.get("expr", rule.get("expression", rule.get("value", 0)))),
                        "width": rule.get("width", rule.get("bit_width", 1)),
                        "description": rule.get("description")
                        or "Moved from output_rules because this rule updates internal architectural state, not a declared output port.",
                    }
                )
                existing_updates.add(state_name)
        tx["output_rules"] = kept_rules
        if updates:
            tx["state_updates"] = updates


def _ensure_function_model_machine_rules(doc: dict[str, Any], combinational: bool = False) -> None:
    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        return
    txs = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
    if not txs:
        return
    if combinational:
        # A combinational IP has no architectural state. Keep promoting concrete
        # output_rules into the rtl_contract (machine-checkable outputs), but
        # never move rules into state_updates or synthesize state-driven rules.
        _prune_combinational_transaction_state(txs)
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    widths = _port_widths(doc)
    input_port = _infer_primary_input_port(doc, contract)
    output_port = _infer_primary_output_port(doc, contract)
    combined_doc_text = json.dumps(
        {
            "rtl_contract": contract,
            "features": doc.get("features"),
            "dataflow": doc.get("dataflow"),
            "test_requirements": doc.get("test_requirements"),
        },
        sort_keys=True,
        default=str,
    )

    for tx in txs:
        if not isinstance(tx.get("output_rules"), list):
            tx["output_rules"] = []
        local_tx_text = " ".join(
            [
                str(tx.get("id") or ""),
                str(tx.get("name") or ""),
                json.dumps(tx.get("outputs") or [], sort_keys=True, default=str),
                json.dumps(tx.get("side_effects") or [], sort_keys=True, default=str),
            ]
        )
        tx_text = " ".join([local_tx_text, combined_doc_text])
        if not tx["output_rules"] and input_port and output_port and _mentions_shift_left_by_one(local_tx_text):
            tx["output_rules"].append(
                {
                    "name": output_port,
                    "port": output_port,
                    "expr": f"{input_port} << 1",
                    "width": widths.get(output_port, 1),
                    "description": "Unsigned left shift by one; implemented in RTL with shift logic, not a multiplier.",
                }
            )

        state_updates = tx.get("state_updates") if isinstance(tx.get("state_updates"), list) else []
        has_accepted_count = any(
            isinstance(state, dict) and str(state.get("name") or "") == "accepted_count"
            for state in fm.get("state_variables") or []
        )
        if has_accepted_count and not state_updates and "accepted_count" in local_tx_text and "increment" in local_tx_text.lower():
            width = 32
            for state in fm.get("state_variables") or []:
                if isinstance(state, dict) and str(state.get("name") or "") == "accepted_count":
                    width = state.get("width", width)
                    break
            state_updates.append(
                {
                    "name": "accepted_count",
                    "expr": "accepted_count + 1",
                    "width": width,
                    "description": "Increment once for each accepted transaction.",
                }
            )
            tx["state_updates"] = state_updates

    output_ports = set(_ports_by_direction(doc, "output"))
    if not output_ports:
        return
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    state_names = {
        str(state.get("name") or "").strip()
        for state in fm.get("state_variables") or []
        if isinstance(state, dict) and str(state.get("name") or "").strip()
    }
    if not combinational:
        _move_internal_output_rules_to_state_updates(
            txs,
            output_ports=output_ports,
            output_map=output_map,
            state_names=state_names,
        )
    contract_rules = contract.get("output_rules") if isinstance(contract.get("output_rules"), list) else []
    contract_rule_ports = {
        _concrete_port_ref(rule.get("port") or rule.get("name"), output_ports)
        for rule in contract_rules
        if isinstance(rule, dict)
    }
    requested_tx_id = str(contract.get("transaction") or contract.get("transaction_id") or "").strip()
    requested_tx = next(
        (
            tx
            for tx in txs
            if requested_tx_id
            and str(tx.get("id") or tx.get("name") or "").strip().lower() == requested_tx_id.lower()
        ),
        None,
    )
    output_rule_tx = requested_tx if isinstance(requested_tx, dict) and requested_tx.get("output_rules") else next(
        (tx for tx in txs if isinstance(tx.get("output_rules"), list) and tx.get("output_rules")),
        None,
    )
    if isinstance(output_rule_tx, dict):
        tx_id = str(output_rule_tx.get("id") or output_rule_tx.get("name") or "").strip()
        if tx_id:
            contract["transaction"] = tx_id
    for source_tx in ([output_rule_tx] if isinstance(output_rule_tx, dict) else []) + [
        tx for tx in txs if tx is not output_rule_tx
    ]:
        if not isinstance(source_tx, dict):
            continue
        for rule in source_tx.get("output_rules") or []:
            if not isinstance(rule, dict):
                continue
            port = _concrete_port_ref(rule.get("port") or rule.get("name"), output_ports)
            if port not in output_ports or port in contract_rule_ports:
                continue
            contract_rules.append({
                "name": rule.get("name") or port,
                "port": port,
                "expr": _normalize_rule_expr(rule.get("expr", rule.get("expression", rule.get("value", 0)))),
                "width": rule.get("width", widths.get(port, 1)),
                "description": rule.get("description") or "FunctionalModel output observable mapped to DUT output port.",
            })
            contract_rule_ports.add(port)

    for state in fm.get("state_variables") or []:
        if not isinstance(state, dict):
            continue
        name = str(state.get("name") or "").strip()
        if not name:
            continue
        mapped = _concrete_port_ref(output_map.get(name), output_ports) if name in output_map else ""
        port = mapped if mapped in output_ports else name if name in output_ports else ""
        if not port:
            continue
        width = widths.get(port, state.get("width", 1))
        state_rule = {
            "name": name,
            "port": port,
            "expr": name,
            "width": width,
            "description": "Externally observable function_model state is driven from the RTL state register.",
        }
        if port not in contract_rule_ports:
            contract_rules.append(dict(state_rule))
            contract_rule_ports.add(port)

        for tx in txs:
            updates = tx.get("state_updates") if isinstance(tx.get("state_updates"), list) else []
            if not any(isinstance(update, dict) and str(update.get("name") or "") == name for update in updates):
                continue
            tx_rules = tx.get("output_rules") if isinstance(tx.get("output_rules"), list) else []
            tx_rule_ports = {
                _concrete_port_ref(rule.get("port") or rule.get("name"), output_ports)
                for rule in tx_rules
                if isinstance(rule, dict)
            }
            if port not in tx_rule_ports:
                tx_rules.append(dict(state_rule))
                tx["output_rules"] = tx_rules
    if contract_rules:
        contract["output_rules"] = contract_rules
    _normalize_machine_rule_exprs(doc)


def _ensure_transaction_machine_rule_completeness(doc: dict[str, Any], combinational: bool = False) -> None:
    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        return
    txs = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
    if not txs:
        return
    if combinational:
        # A combinational IP has no architectural state: never auto-inject the
        # {tx_id}_observed state markers (REPAIR_TRANSACTION_STATE_MARKER) or
        # state_updates. Make transactions machine-checkable via a benign
        # output_rule on a declared output port only (no state).
        output_ports = set(_ports_by_direction(doc, "output"))
        widths = _port_widths(doc)
        if output_ports and not any(
            isinstance(rule, dict)
            and str(rule.get("name") or rule.get("port") or "").strip()
            and _machine_rule_has_expr(rule)
            for tx in txs
            for rule in (tx.get("output_rules") if isinstance(tx.get("output_rules"), list) else [])
        ):
            target_tx = next((tx for tx in txs if not _is_reset_transaction(tx)), None)
            if target_tx is not None:
                preferred = ["error", "pslverr", "irq", "rsp_valid", "pready", "done", "busy"]
                port = next((name for name in preferred if name in output_ports), sorted(output_ports)[0])
                rules = target_tx.get("output_rules") if isinstance(target_tx.get("output_rules"), list) else []
                rules.append({
                    "name": port,
                    "port": port,
                    "expr": "0",
                    "width": widths.get(port, 1),
                    "description": (
                        "Auto-injected benign observable rule so the function_model has at least one "
                        "scoreboard-visible output equation; replace with IP-specific output behavior before signoff."
                    ),
                })
                target_tx["output_rules"] = rules
        return
    states = fm.get("state_variables") if isinstance(fm.get("state_variables"), list) else []
    output_ports = set(_ports_by_direction(doc, "output"))
    widths = _port_widths(doc)
    existing_states = {
        str(item.get("name") or "").strip()
        for item in states
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }

    def has_machine_rule(tx: dict[str, Any]) -> bool:
        output_rules = _machine_rule_items(tx.get("output_rules"))
        state_updates = _machine_rule_items(tx.get("state_updates"))
        return any(
            str(rule.get("name") or rule.get("output") or "").strip()
            and _machine_rule_has_expr(rule)
            for rule in output_rules
        ) or any(
            str(rule.get("name") or rule.get("state") or rule.get("target") or "").strip()
            and _machine_rule_has_expr(rule)
            for rule in state_updates
        )

    changed = False
    for idx, tx in enumerate(txs, start=1):
        if _is_reset_transaction(tx) or has_machine_rule(tx):
            continue
        tx_id = _norm_token(tx.get("id") or tx.get("name") or f"tx_{idx}") or f"tx_{idx}"
        state_name = f"{tx_id}_observed"
        if state_name not in existing_states:
            states.append({
                "name": state_name,
                "source": f"function_model.transactions.{tx.get('id') or tx.get('name') or tx_id}",
                "width": 1,
                "reset": 0,
                "description": (
                    "Auto-injected transaction coverage/state marker because the transaction "
                    "had prose outputs or side effects but no executable output_rules/state_updates."
                ),
            })
            existing_states.add(state_name)
        updates = tx.get("state_updates") if isinstance(tx.get("state_updates"), list) else []
        updates.append({
            "name": state_name,
            "expr": "1",
            "width": 1,
            "description": (
                "Repair marker making this transaction machine-checkable; ssot-gen should replace "
                "with IP-specific architectural state/output equations before signoff."
            ),
        })
        tx["state_updates"] = updates
        changed = True
    if output_ports and not any(
        isinstance(rule, dict)
        and str(rule.get("name") or rule.get("port") or "").strip()
        and _machine_rule_has_expr(rule)
        for tx in txs
        for rule in (tx.get("output_rules") if isinstance(tx.get("output_rules"), list) else [])
    ):
        target_tx = next((tx for tx in txs if not _is_reset_transaction(tx)), None)
        if target_tx is not None:
            preferred = ["error", "pslverr", "irq", "rsp_valid", "pready", "done", "busy"]
            port = next((name for name in preferred if name in output_ports), sorted(output_ports)[0])
            rules = target_tx.get("output_rules") if isinstance(target_tx.get("output_rules"), list) else []
            rules.append({
                "name": port,
                "port": port,
                "expr": "0",
                "width": widths.get(port, 1),
                "description": (
                    "Auto-injected benign observable rule so the function_model has at least one "
                    "scoreboard-visible output equation; replace with IP-specific output behavior before signoff."
                ),
            })
            target_tx["output_rules"] = rules
            changed = True
    if changed:
        fm["state_variables"] = states


def _machine_rule_name(item: dict[str, Any]) -> str:
    return str(
        item.get("name")
        or item.get("state")
        or item.get("target")
        or item.get("port")
        or ""
    ).strip()


def _is_repair_transaction_marker(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    text = str(item.get("description") or "")
    return REPAIR_TRANSACTION_RULE_MARKER in text or REPAIR_TRANSACTION_STATE_MARKER in text


def _has_non_repair_machine_rule(tx: dict[str, Any]) -> bool:
    for rule in _machine_rule_items(tx.get("output_rules")):
        if not _is_repair_transaction_marker(rule) and _machine_rule_name(rule) and _machine_rule_has_expr(rule):
            return True
    for update in _machine_rule_items(tx.get("state_updates")):
        if not _is_repair_transaction_marker(update) and _machine_rule_name(update) and _machine_rule_has_expr(update):
            return True
    return False


def _remove_stale_repair_machine_markers(doc: dict[str, Any]) -> None:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    if not isinstance(fm, dict):
        return
    txs = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
    if not txs:
        return

    stale_states: set[str] = set()
    for tx in txs:
        if not _has_non_repair_machine_rule(tx):
            continue
        kept_updates: list[Any] = []
        for update in tx.get("state_updates") or []:
            if isinstance(update, dict) and _is_repair_transaction_marker(update):
                name = _machine_rule_name(update)
                if name:
                    stale_states.add(name)
                continue
            kept_updates.append(update)
        if kept_updates:
            tx["state_updates"] = kept_updates
        else:
            tx.pop("state_updates", None)

        kept_outputs: list[Any] = []
        for output in tx.get("outputs") or []:
            if isinstance(output, dict) and _is_repair_transaction_marker(output):
                name = _machine_rule_name(output)
                if name:
                    stale_states.add(name)
                continue
            kept_outputs.append(output)
        if kept_outputs:
            tx["outputs"] = kept_outputs
        else:
            tx.pop("outputs", None)

    if not stale_states:
        return

    live_rule_targets: set[str] = set()
    for tx in txs:
        for item in (tx.get("output_rules") or []) + (tx.get("state_updates") or []):
            if isinstance(item, dict) and not _is_repair_transaction_marker(item):
                name = _machine_rule_name(item)
                if name:
                    live_rule_targets.add(name)

    states = fm.get("state_variables")
    if isinstance(states, list):
        fm["state_variables"] = [
            state
            for state in states
            if not (
                isinstance(state, dict)
                and str(state.get("name") or "").strip() in stale_states
                and str(state.get("name") or "").strip() not in live_rule_targets
                and REPAIR_TRANSACTION_STATE_MARKER in str(state.get("description") or "")
            )
        ]


_RULE_HELPER_NAMES: frozenset[str] = frozenset({
    "gray_to_bin", "bin_to_gray", "popcount", "parity",
    "clog2", "min", "max", "abs",
    "and", "or", "not", "True", "False", "None",
})


def _expr_to_python(expr: Any) -> str:
    text = str(expr or "").strip()
    if not text:
        return ""
    py = text.replace("&&", " and ").replace("||", " or ")
    py = re.sub(r"!(?=[A-Za-z_(])", " not ", py)
    return py


def _names_in_expr(expr: Any) -> set[str]:
    py = _expr_to_python(expr)
    if not py:
        return set()
    try:
        tree = ast.parse(py, mode="eval")
    except SyntaxError:
        return set()
    names: set[str] = set()

    class _Visitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:  # noqa: N802 - ast visitor API
            names.add(node.id)

        def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - ast visitor API
            if not isinstance(node.func, ast.Name):
                self.visit(node.func)
            for arg in node.args:
                self.visit(arg)
            for keyword in node.keywords:
                self.visit(keyword.value)

    _Visitor().visit(tree)
    return names


def _is_dsl_parseable(expr: Any) -> bool:
    py = _expr_to_python(expr)
    if not py:
        return False
    try:
        ast.parse(py, mode="eval")
        return True
    except SyntaxError:
        return False


def _ensure_rule_expr_input_map_completeness(doc: dict[str, Any]) -> None:
    """Repair rtl-gen preflight gates by deterministic SSOT extension.

    C-1: Keep expression references machine-checkable without inventing top
         level IO. Helper calls and internal derived signals must not be
         promoted to DUT ports; undeclared external fields should surface as
         contract questions in downstream gates.
    C-2: Replace prose sample_condition with a DSL-parseable default that
         uses declared input ports.
    C-3: Add placeholder output_rules for function_model state_variables that
         map to output ports but lack any rule.
    """
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    if not fm or not contract:
        return
    txs = [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]
    if not txs:
        return

    _ensure_apb_helper_signals(doc, fm)
    _rewrite_self_referential_output_defaults(doc)

    input_map = contract.get("input_map") if isinstance(contract.get("input_map"), dict) else {}
    output_map = contract.get("output_map") if isinstance(contract.get("output_map"), dict) else {}
    stale_auto_ports: set[str] = set()
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    interfaces = io.get("interfaces") if isinstance(io.get("interfaces"), list) else []
    for interface in interfaces:
        if not isinstance(interface, dict):
            continue
        ports = interface.get("ports") if isinstance(interface.get("ports"), list) else []
        kept_ports: list[dict[str, Any]] = []
        for port in ports:
            if not isinstance(port, dict):
                continue
            name = str(port.get("name") or "").strip()
            desc = str(port.get("description") or "")
            if name and "Auto-derived 1-bit input from rule expression" in desc:
                stale_auto_ports.add(name)
                continue
            kept_ports.append(port)
        interface["ports"] = kept_ports
    if stale_auto_ports:
        input_map = {
            str(field): port
            for field, port in input_map.items()
            if str(field) not in stale_auto_ports and str(port) not in stale_auto_ports
        }
        contract["input_map"] = input_map

    declared_inputs = set(_ports_by_direction(doc, "input"))
    declared_outputs = set(_ports_by_direction(doc, "output"))
    declared_all = declared_inputs | declared_outputs

    fm_state_names = {
        str(state.get("name") or "").strip()
        for state in fm.get("state_variables") or []
        if isinstance(state, dict) and str(state.get("name") or "").strip()
    }
    internal_signal_names: set[str] = set()
    for key in (
        "derived_signals",
        "intermediate_signals",
        "internal_signals",
        "combinational_signals",
    ):
        values = fm.get(key)
        if isinstance(values, dict):
            internal_signal_names.update(str(name).strip() for name in values if str(name).strip())
            values = list(values.values())
        if not isinstance(values, list):
            continue
        for item in values:
            if isinstance(item, str) and item.strip():
                internal_signal_names.add(item.strip())
            elif isinstance(item, dict):
                for name_key in ("name", "signal", "id"):
                    name = str(item.get(name_key) or "").strip()
                    if name:
                        internal_signal_names.add(name)
                        break

    rule_target_names: set[str] = set()
    for tx in txs:
        for rule in tx.get("output_rules") or []:
            if isinstance(rule, dict):
                for key in ("name", "port"):
                    val = str(rule.get(key) or "").strip()
                    if val:
                        rule_target_names.add(val)
        for su in tx.get("state_updates") or []:
            if isinstance(su, dict):
                val = str(su.get("name") or "").strip()
                if val:
                    rule_target_names.add(val)

    referenced: set[str] = set()
    for tx in txs:
        for rule in tx.get("output_rules") or []:
            if isinstance(rule, dict):
                for key in ("expr", "expression", "value"):
                    if key in rule:
                        referenced |= _names_in_expr(rule.get(key))
        for su in tx.get("state_updates") or []:
            if isinstance(su, dict):
                for key in ("expr", "expression", "value"):
                    if key in su:
                        referenced |= _names_in_expr(su.get(key))
        if "sample_condition" in tx:
            referenced |= _names_in_expr(tx.get("sample_condition"))
    sample_condition = contract.get("sample_condition")
    referenced |= _names_in_expr(sample_condition)
    for rule in contract.get("output_rules") or []:
        if isinstance(rule, dict):
            for key in ("expr", "expression", "value"):
                if key in rule:
                    referenced |= _names_in_expr(rule.get(key))

    known = (
        declared_all
        | set(input_map.keys())
        | set(output_map.keys())
        | fm_state_names
        | internal_signal_names
        | rule_target_names
        | _RULE_HELPER_NAMES
    )
    missing = sorted(
        name for name in referenced
        if name and name not in known and not name.isdigit() and not name.startswith("_")
    )

    if missing:
        contract["unresolved_expression_refs"] = missing
    else:
        contract.pop("unresolved_expression_refs", None)

    if sample_condition is not None and not _is_dsl_parseable(sample_condition):
        replacement = ""
        for cand in ("i_valid", "d_valid", "valid", "req_valid"):
            if cand in declared_inputs:
                replacement = cand
                break
        contract["sample_condition"] = replacement or "1"

    state_vars_by_name = {
        str(s.get("name") or "").strip(): s
        for s in fm.get("state_variables") or []
        if isinstance(s, dict)
    }
    for state_name, state in state_vars_by_name.items():
        if not state_name or state_name not in declared_outputs:
            continue
        has_rule = False
        for tx in txs:
            for r in (tx.get("output_rules") or []) + (tx.get("state_updates") or []):
                if isinstance(r, dict):
                    if str(r.get("name") or "") == state_name or str(r.get("port") or "") == state_name:
                        has_rule = True
                        break
            if has_rule:
                break
        if not has_rule and txs:
            placeholder = {
                "name": state_name,
                "port": state_name,
                "expr": "0",
                "width": int(state.get("width") or 1),
                "description": (
                    f"Auto-injected placeholder rule for observable state {state_name!r} "
                    "(repair_ssot_schema rule_expr_completeness pass; advisory: "
                    "downstream TB/scoreboard treats this as 0 unless overridden)."
                ),
            }
            txs[0].setdefault("output_rules", []).append(placeholder)


def _ensure_parameters_section(doc: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
    params = doc.get("parameters")
    if isinstance(params, list) and params and not _has_tbd(params):
        return params
    return [
        {"name": "DATA_WIDTH", "default": 32, "type": "int", "description": "Primary payload/result width in bits", "drives": ["rtl", "tb", "coverage"]},
        {"name": "ID_WIDTH", "default": 4, "type": "int", "description": "Optional request/context identifier width when the SSOT declares tagged work", "drives": ["rtl", "tb", "coverage"]},
        {"name": "DEPTH", "default": 4, "type": "int", "description": "Generic internal queue/state depth only if a later SSOT section assigns storage semantics", "drives": ["rtl", "tb", "coverage"]},
    ]


def _canonical_interface_ports(iface: dict[str, Any]) -> list[dict[str, Any]]:
    raw_ports = iface.get("ports") if isinstance(iface.get("ports"), list) else []
    source = raw_ports if raw_ports else iface.get("signals") if isinstance(iface.get("signals"), list) else []
    ports: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in source:
        if isinstance(item, str):
            name = item.strip()
            row: dict[str, Any] = {"name": name}
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("signal") or item.get("port") or "").strip()
            row = dict(item)
            row["name"] = name
        else:
            continue
        if not name or name in seen:
            continue
        row["direction"] = _normalize_port_direction(
            row.get("direction") or row.get("dir") or _infer_legacy_port_direction(name, iface)
        )
        row.setdefault("width", _infer_legacy_port_width(name))
        row.setdefault("description", f"Recovered from io_list.interfaces.{iface.get('name', 'unnamed')}.signals")
        ports.append(row)
        seen.add(name)
    return ports


def _ensure_io_list(doc: dict[str, Any]) -> dict[str, Any]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    if io.get("interfaces") and not _has_tbd(io):
        io.setdefault("clock_domains", [{
            "name": "clk",
            "frequency_mhz": 100,
            "description": "Primary synchronous clock",
            "ports": [{"name": "clk", "width": 1, "direction": "input", "description": "Primary clock"}],
        }])
        io.setdefault("resets", [{
            "name": "rst_n",
            "polarity": "active_low",
            "sync_async": "async_assert_sync_deassert",
            "description": "Active-low reset, asynchronous assert and synchronous release",
            "ports": [{"name": "rst_n", "width": 1, "direction": "input", "description": "Primary reset"}],
        }])
        clock = _first_clock(doc)[0]
        reset = _first_reset(doc)[0]
        for iface in io.get("interfaces") or []:
            if not isinstance(iface, dict):
                continue
            ports = _canonical_interface_ports(iface)
            if ports:
                iface["ports"] = ports
            names = {str(port.get("name") or "") for port in ports if isinstance(port, dict)}
            has_valid_ready = any(name.endswith("valid") for name in names) and any(name.endswith("ready") for name in names)
            iface.setdefault("type", "native_valid_ready" if has_valid_ready else "custom")
            iface.setdefault("role", "target")
            iface.setdefault("clock_domain", clock)
            iface.setdefault("reset_domain", reset)
            iface.setdefault("protocol", {
                "acceptance": "Transfer acceptance follows the declared valid/ready or protocol phase rule.",
                "stability": "Payload/control fields remain stable until accepted.",
                "response": "Observable response timing follows cycle_model latency and ordering.",
            })
            for port in ports:
                if not isinstance(port, dict):
                    continue
                port.setdefault("width", 1)
        return io
    return {
        "clock_domains": [{
            "name": "clk",
            "frequency_mhz": 100,
            "description": "Primary synchronous clock",
            "ports": [{"name": "clk", "width": 1, "direction": "input", "description": "Primary clock"}],
        }],
        "resets": [{
            "name": "rst_n",
            "polarity": "active_low",
            "sync_async": "async_assert_sync_deassert",
            "description": "Active-low reset, asynchronous assert and synchronous release",
            "ports": [{"name": "rst_n", "width": 1, "direction": "input", "description": "Primary reset"}],
        }],
        "interfaces": [{
            "name": "control_data",
            "type": "native_valid_ready",
            "role": "target",
            "clock_domain": "clk",
            "reset_domain": "rst_n",
            "description": "Generic request/response interface synthesized only as a repair fallback; replace with approved protocol ports before production signoff.",
            "protocol": {
                "acceptance": "req_valid && req_ready accepts one request payload.",
                "response": "rsp_valid marks a response payload, accepted with rsp_ready.",
                "stability": "Payload/control fields remain stable while valid is high and ready is low.",
            },
            "ports": [
                {"name": "req_valid", "width": 1, "direction": "input", "description": "Request/control payload valid"},
                {"name": "req_ready", "width": 1, "direction": "output", "description": "Request/control payload accepted when high with req_valid"},
                {"name": "req_data", "width": "DATA_WIDTH", "direction": "input", "description": "Generic request/control payload"},
                {"name": "rsp_valid", "width": 1, "direction": "output", "description": "Response/result payload valid"},
                {"name": "rsp_ready", "width": 1, "direction": "input", "description": "Response/result accepted when high with rsp_valid"},
                {"name": "rsp_data", "width": "DATA_WIDTH", "direction": "output", "description": "Generic response/result payload"},
                {"name": "error", "width": 1, "direction": "output", "description": "Generic architectural error indication"},
            ],
        }],
    }


def _ensure_features(doc: dict[str, Any]) -> list[dict[str, Any]]:
    features = doc.get("features")
    if isinstance(features, list) and features and not _has_tbd(features):
        return features
    return [
        {"name": "primary_approved_behavior", "trigger": "A legal request, transaction, packet, command, or CSR operation is accepted", "datapath": "Inputs are transformed only according to function_model transactions and declared state", "control": "Control advances through cycle_model pipeline and fsm transitions", "output": "Observable outputs/status/events match function_model outputs and side effects"},
        {"name": "backpressure_stability", "trigger": "Any declared ready/acceptance signal is deasserted while valid/work is pending", "datapath": "Payload and state remain stable until the matching handshake or acceptance condition", "control": "FSM stalls only the affected phase", "output": "No duplicated, dropped, or reordered transaction unless explicitly allowed"},
        {"name": "error_policy", "trigger": "A declared error_handling.error_sources condition is observed", "datapath": "No unrelated state is corrupted by the error path", "control": "Recovery follows error_handling.recovery", "output": "Error/status/response/debug behavior follows error_handling.propagation"},
    ]


def _ensure_dataflow(doc: dict[str, Any]) -> dict[str, Any]:
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    if dataflow and not _has_tbd(dataflow):
        return dataflow
    return {
        "source": "declared io_list request/control interfaces",
        "sequence": [
            "accept legal work under cycle_model handshake or command rules",
            "evaluate function_model transaction and declared feature behavior",
            "update only declared architectural state/status/events",
            "publish response, output, interrupt, or debug observability event",
        ],
        "sinks": ["declared outputs", "status/debug observability", "register reads if registers exist"],
        "ordering": "Externally visible ordering follows cycle_model.ordering unless the SSOT explicitly approves reordering.",
    }


def _ensure_clock_reset_domains(doc: dict[str, Any]) -> dict[str, Any]:
    value = doc.get("clock_reset_domains")
    if isinstance(value, dict) and value and not _has_tbd(value):
        return value
    return {
        "domains": [{"clock": "clk", "reset": "rst_n", "frequency_mhz": 100, "reset_scheme": "async_assert_sync_deassert"}],
        "reset_behavior": ["Handshake/control state resets to idle", "Observable outputs reset to function_model reset values"],
    }


def _ensure_cdc_rdc(section: str, doc: dict[str, Any]) -> dict[str, Any]:
    value = doc.get(section)
    if isinstance(value, dict) and value and not _has_tbd(value):
        return value
    return {
        "required": False,
        "rationale": "Single clock/reset domain in the repaired draft; update SSOT if additional clocks or resets are introduced",
        "checks": ["No crossing paths expected; update SSOT if additional clocks or resets are introduced"],
    }


def _ensure_registers(doc: dict[str, Any]) -> dict[str, Any]:
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    if regs and not _has_tbd(regs):
        promoted = _promote_register_note_entries(regs)
        if not promoted.get("register_list"):
            promoted.setdefault("no_registers", True)
            promoted.setdefault("policy", "No firmware-visible registers are declared; add register_list before CSR behavior is implemented.")
        _ensure_register_write_effects(promoted)
        return promoted
    out = {
        "no_registers": True,
        "policy": "No firmware-visible registers are implied by repair; add explicit register_list entries before rtl-gen implements CSR behavior.",
        "register_list": [],
    }
    _ensure_register_write_effects(out)
    return out


def _ensure_register_write_effects(regs: dict[str, Any]) -> None:
    for reg in regs.get("register_list") or []:
        if not isinstance(reg, dict):
            continue
        reg_write_effect = (
            reg.get("write_effect")
            or reg.get("write_behavior")
            or reg.get("write_side_effects")
            or reg.get("write_side_effect")
            or reg.get("side_effects")
        )
        for field in reg.get("fields") or []:
            if not isinstance(field, dict):
                continue
            access = str(field.get("access") or reg.get("access") or "").lower()
            if access == "reserved":
                field.setdefault("read_value", 0)
                field.setdefault("write_effect", "Writes are ignored and the field remains at its reserved read value.")
                continue
            if "w" not in access:
                continue
            field_effect = (
                field.get("write_effect")
                or field.get("write_behavior")
                or field.get("write_side_effects")
                or field.get("write_side_effect")
                or field.get("side_effects")
                or reg_write_effect
            )
            if field_effect:
                field["write_effect"] = field_effect
                continue
            if "w1c" in access:
                field["write_effect"] = "Writing 1 clears the corresponding status bit; writing 0 leaves it unchanged."
            elif "w1s" in access:
                field["write_effect"] = "Writing 1 sets the corresponding status bit; writing 0 leaves it unchanged."
            elif access in {"rw", "wr", "write", "wo"} or "w" in access:
                field["write_effect"] = "APB write data updates this field value according to its bit mask."


def _promote_register_note_entries(regs: dict[str, Any]) -> dict[str, Any]:
    out = dict(regs)
    reg_list = [dict(item) for item in out.get("register_list") or [] if isinstance(item, dict)]
    known = {str(item.get("name") or "").upper() for item in reg_list}
    config = out.get("config") if isinstance(out.get("config"), dict) else {}
    width = config.get("register_width", 32)
    note = " ".join(
        str(value or "")
        for value in (
            config.get("note"),
            config.get("source"),
            config.get("description"),
            config.get("access_policy"),
            out.get("note"),
            out.get("description"),
        )
    )
    for match in re.finditer(r"\b([A-Z][A-Z0-9_]{1,31})\s+0x([0-9A-Fa-f]+)\s+([A-Z][A-Z0-9_/]*)?", note):
        name = match.group(1).upper()
        if name in known:
            continue
        access = (match.group(3) or "RW").lower()
        desc_start = match.start()
        desc_end = note.find(",", match.end())
        if desc_end < 0:
            desc_end = min(len(note), match.end() + 96)
        description = note[desc_start:desc_end].strip(" ,.;") or f"Register {name} promoted from register note"
        reg_list.append({
            "name": name,
            "offset": int(match.group(2), 16),
            "width": width,
            "access": access,
            "reset": 0,
            "category": "status" if any(tok in name for tok in ("INT", "STATUS", "FSM", "FSC", "FTM", "FTC", "DBG")) else "data",
            "description": description,
            "fields": [{
                "name": name.lower(),
                "bits": [int(width) - 1 if isinstance(width, int) else 31, 0],
                "access": access,
                "reset": 0,
            }],
        })
        known.add(name)
    out["register_list"] = reg_list
    return out


def _ensure_memory(doc: dict[str, Any]) -> dict[str, Any]:
    mem = doc.get("memory") if isinstance(doc.get("memory"), dict) else {}
    if mem and not _has_tbd(mem):
        return mem
    return {
        "instances": [],
        "addressing": {"policy": "No SSOT-approved internal memory instances; add explicit memories before rtl-gen may implement storage behavior."},
        "storage_policy": "No storage behavior is implied by repair. rtl-gen may only implement memory described by SSOT facts.",
    }


def _ensure_interrupts(doc: dict[str, Any]) -> dict[str, Any]:
    intr = doc.get("interrupts") if isinstance(doc.get("interrupts"), dict) else {}
    if intr and not _has_tbd(intr):
        return intr
    return {"present": False, "sources": [], "rationale": "No interrupt output is implied by repair; add interrupt sources explicitly before rtl-gen implements IRQ behavior"}


def _combinational_fsm_section() -> dict[str, Any]:
    """The only legal fsm shape for a cycle-waived (combinational) IP: explicit
    absence. verify_ssot hard-blocks any fsm.*.states on a combinational IP, so
    repair must never synthesize a control FSM here."""
    return {
        "present": False,
        "rationale": (
            "Locked truth is cycle_model_waiver/combinational "
            "(req/behavioral_contracts.json); a purely combinational IP has no "
            "state-control FSM."
        ),
    }


def _ensure_fsm(doc: dict[str, Any], combinational: bool = False) -> dict[str, Any]:
    if combinational:
        return _combinational_fsm_section()
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    if fsm and not _has_tbd(fsm):
        return fsm
    feature_names = [
        str(item.get("name") or f"feature_{idx}").upper()
        for idx, item in enumerate(doc.get("features") or [], start=1)
        if isinstance(item, dict)
    ][:6]
    execute_states = [f"EXEC_{re.sub(r'[^A-Z0-9_]+', '_', name).strip('_') or idx}" for idx, name in enumerate(feature_names, start=1)]
    states = ["IDLE", "ACCEPT"] + (execute_states or ["EXECUTE"]) + ["COMPLETE", "ERROR"]
    transitions = [
        {"from": "IDLE", "to": "ACCEPT", "when": "A legal transaction, packet, command, or CSR operation is accepted"},
        {"from": "ACCEPT", "to": execute_states[0] if execute_states else "EXECUTE", "when": "Inputs and configuration match function_model preconditions"},
    ]
    for prev, nxt in zip(execute_states or ["EXECUTE"], (execute_states or ["EXECUTE"])[1:] + ["COMPLETE"]):
        transitions.append({"from": prev, "to": nxt, "when": "The current SSOT-owned behavior slice completes"})
    transitions.extend(
        [
            {"from": "COMPLETE", "to": "IDLE", "when": "Observable result/status handoff completes"},
            {"from": "*", "to": "ERROR", "when": "error_handling.error_sources condition is detected"},
            {"from": "ERROR", "to": "IDLE", "when": "Reset or approved recovery action clears the error"},
        ]
    )
    return {
        "control": {
            "states": states,
            "transitions": transitions,
            "source": "repair synthesized only generic control structure from existing SSOT facts; no IP-kind fixed FSM is implied",
        },
    }

def _register_state_variables(doc: dict[str, Any]) -> list[dict[str, Any]]:
    regs = doc.get("registers") if isinstance(doc.get("registers"), dict) else {}
    variables: list[dict[str, Any]] = []
    for reg in regs.get("register_list") or []:
        if not isinstance(reg, dict):
            continue
        reg_name = str(reg.get("name") or "reg").lower()
        fields = reg.get("fields") if isinstance(reg.get("fields"), list) else []
        if fields:
            for field in fields:
                if not isinstance(field, dict):
                    continue
                name = str(field.get("name") or reg_name)
                variables.append({
                    "name": name,
                    "source": f"registers.{reg.get('name')}.{name}",
                    "reset": field.get("reset", reg.get("reset", 0)),
                    "description": field.get("description") or f"Architectural field {name}",
                })
        else:
            variables.append({
                "name": reg_name,
                "source": f"registers.{reg.get('name')}",
                "reset": reg.get("reset", 0),
                "description": reg.get("description") or f"Architectural register {reg_name}",
            })
    if variables:
        return variables[:24]
    return [
        {"name": "state", "source": "fsm", "reset": "IDLE", "description": "Primary architectural state"},
        {"name": "error", "source": "error_handling", "reset": 0, "description": "Architectural error indicator"},
    ]


def _error_sources(doc: dict[str, Any]) -> list[dict[str, Any]]:
    errors = doc.get("error_handling") if isinstance(doc.get("error_handling"), dict) else {}
    raw = errors.get("error_sources") or errors.get("sources") or []
    out = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        out.append({
            "id": item.get("id") or item.get("name") or f"ERR{idx}",
            "condition": item.get("condition") or item.get("detection") or "Declared error condition is observed",
            "architectural_effect": item.get("architectural_effect") or item.get("response") or "Status/error reporting follows the SSOT error policy",
        })
    if out:
        return out
    return [{"id": "ERR_PROTOCOL", "condition": "Downstream protocol response is non-OKAY or invalid", "architectural_effect": "Set error status and block signoff until handled"}]


def _prune_combinational_transaction_state(txs: list[Any]) -> None:
    """Drop architectural state_updates from transactions of a combinational IP.

    verify_ssot hard-blocks any non-empty transaction state_updates on a
    cycle-waived IP, so pruning them (rather than leaving forbidden content)
    helps the repair loop converge."""
    for tx in txs:
        if isinstance(tx, dict):
            tx.pop("state_updates", None)


def _ensure_function_model(doc: dict[str, Any], state: dict[str, Any], combinational: bool = False) -> dict[str, Any]:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    existing_txs = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
    generic_only = (
        len(existing_txs) <= 1
        and existing_txs
        and str(existing_txs[0].get("name") or "").lower() in {"primary_operation", "basic_operation"}
    )
    if combinational:
        # A purely combinational IP has no architectural state to model.
        # Preserve the existing transactions but never inject (or keep)
        # state_variables / transaction state_updates -- verify_ssot blocks them.
        repaired = dict(fm)
        repaired.pop("state_variables", None)
        repaired_txs: list[dict[str, Any]] = []
        for idx, tx in enumerate(existing_txs, start=1):
            item = dict(tx) if isinstance(tx, dict) else {"name": str(tx)}
            tx_id = str(item.get("id") or item.get("name") or f"FM{idx}")
            item["id"] = tx_id
            item["name"] = item.get("name") or tx_id.lower()
            item.pop("state_updates", None)
            repaired_txs.append(item)
        repaired["transactions"] = repaired_txs
        if not repaired.get("purpose"):
            repaired["purpose"] = "Cycle-independent combinational behavioral contract for rtl-gen and tb-gen."
        repaired.setdefault(
            "reference_model_hint",
            "tb-gen must build a scoreboard/reference model from function_model transactions and compare expected versus observed results.",
        )
        return repaired
    if fm.get("state_variables") and fm.get("transactions") and fm.get("invariants") and not generic_only:
        repaired = dict(fm)
        repaired_txs: list[dict[str, Any]] = []
        for idx, tx in enumerate(existing_txs, start=1):
            item = dict(tx) if isinstance(tx, dict) else {"name": str(tx)}
            tx_id = str(item.get("id") or item.get("name") or f"FM{idx}")
            item["id"] = tx_id
            item["name"] = item.get("name") or tx_id.lower()
            item["preconditions"] = item.get("preconditions") or ["transaction is accepted under cycle_model rules"]
            item["outputs"] = item.get("outputs") or ["observable outputs/status match the approved SSOT behavior"]
            if not (item.get("side_effects") or item.get("error_cases")):
                item["side_effects"] = ["updates only SSOT-declared architectural state, status, events, or output handoff state"]
            repaired_txs.append(item)
        repaired["transactions"] = repaired_txs
        return repaired
    decisions = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
    features = [f for f in (doc.get("features") or []) if isinstance(f, dict)]
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    transactions = []
    for idx, feature in enumerate(features[:4], start=1):
        transactions.append({
            "id": f"FM{idx}",
            "name": str(feature.get("name") or f"feature_{idx}").lower().replace(" ", "_"),
            "preconditions": [str(feature.get("trigger") or "Feature trigger is asserted under legal configuration")],
            "inputs": [str(feature.get("datapath") or "Inputs described by io_list and dataflow")],
            "outputs": [str(feature.get("output") or "Architectural output matches feature definition")],
            "side_effects": [str(feature.get("control") or "Architectural state updates according to FSM/control policy")],
            "error_cases": [
                {"condition": src["condition"], "result": src["architectural_effect"]}
                for src in _error_sources(doc)[:3]
            ],
        })
    if not transactions or generic_only:
        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        primary = top.get("description") or decisions.get("purpose") or "the approved IP behavior"
        transactions = [
            {
                "id": "FM_RESET",
                "name": "reset",
                "preconditions": ["declared reset is asserted"],
                "inputs": ["clock", "reset", "retention/configuration policy from SSOT"],
                "outputs": ["all architectural state returns to declared reset values"],
                "side_effects": ["clears transient protocol, status, and error state unless SSOT explicitly marks retained state"],
                "error_cases": [],
            },
            {
                "id": "FM_PRIMARY",
                "name": "primary_approved_behavior",
                "preconditions": ["a legal request, command, packet, transaction, or CSR operation is accepted under cycle_model rules"],
                "inputs": ["external interface signals", "configuration/register state", "declared internal state"],
                "outputs": [str(primary)],
                "side_effects": ["updates only SSOT-declared state, status, counters, events, interrupts, buffers, or output handoff state"],
                "error_cases": [
                    {"condition": src["condition"], "result": src["architectural_effect"]}
                    for src in _error_sources(doc)[:3]
                ],
            },
            {
                "id": "FM_CONTROL_STATUS",
                "name": "control_status_access",
                "preconditions": ["a legal control/status access is accepted, if the SSOT declares such an interface"],
                "inputs": ["address/control fields", "write data or command payload", "current architectural state"],
                "outputs": ["read/status/response values match registers, debug_observability, and error_handling"],
                "side_effects": ["RW/W1C/command side effects occur only as declared in registers or features"],
                "error_cases": [{"condition": "unsupported access or illegal control operation", "result": "error_handling policy is applied without changing unrelated state"}],
            },
        ]
    invariants = [
        "No externally visible output changes except through declared interfaces, registers, interrupts, or debug signals.",
        "All state updates are synchronous to the declared clock and return to reset values under the declared reset policy.",
        "Every declared error source has a defined architectural effect and recovery path.",
    ]
    if dataflow:
        invariants.append("Data movement and ordering follow the dataflow section without bypassing declared buffers or counters.")
    return {
        "purpose": "Cycle-independent behavioral contract for rtl-gen and tb-gen.",
        "state_variables": _register_state_variables(doc),
        "transactions": transactions,
        "invariants": invariants,
        "reference_model_hint": "tb-gen must build a scoreboard/reference model from function_model transactions and compare expected versus observed results.",
    }


def _interface_handshakes(doc: dict[str, Any]) -> list[dict[str, str]]:
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    rules: list[dict[str, str]] = []
    for intf in io.get("interfaces") or []:
        if not isinstance(intf, dict):
            continue
        ports = intf.get("ports") if isinstance(intf.get("ports"), list) else []
        names = {str(p.get("name")) for p in ports if isinstance(p, dict) and p.get("name")}
        for name in sorted(names):
            if name.endswith("valid"):
                ready = name[:-5] + "ready"
                if ready in names:
                    rules.append({"signal": f"{name}/{ready}", "rule": f"{name} payload remains stable until {ready} is sampled asserted on {intf.get('name', 'interface')}."})
    return rules[:12] or [{"signal": "valid/ready", "rule": "All valid payloads remain stable until the matching ready handshake completes."}]


def _fsm_pipeline(doc: dict[str, Any]) -> list[dict[str, Any]]:
    fsm = doc.get("fsm") if isinstance(doc.get("fsm"), dict) else {}
    for value in fsm.values():
        if isinstance(value, dict) and isinstance(value.get("states"), list) and value["states"]:
            return [
                {"stage": str(state), "cycle": "state-dependent", "action": f"Execute {state} behavior from fsm and dataflow"}
                for state in value["states"][:12]
            ]
    return [
        {"stage": "S0_ACCEPT", "cycle": 0, "action": "Accept legal command or request"},
        {"stage": "S1_EXECUTE", "cycle": "1..N", "action": "Perform data/control operation with protocol handshakes"},
        {"stage": "S2_COMPLETE", "cycle": "N+1", "action": "Update status, interrupts, and debug observability"},
    ]


def _combinational_cycle_model(doc: dict[str, Any]) -> dict[str, Any]:
    """Cycle model for a cycle-waived (combinational) IP.

    verify_ssot hard-blocks handshake_rules/pipeline/backpressure and any
    min_cycles>=1 latency on a combinational IP, so repair must never inject
    them. Clock/reset metadata and min_cycles=0 lanes are allowed, so we keep
    the IP's existing cycle_model but strip the forbidden content (pruning is
    safe -- the gate blocks the same content anyway)."""
    cm = dict(doc.get("cycle_model")) if isinstance(doc.get("cycle_model"), dict) else {}
    clock, freq = _first_clock(doc)
    for forbidden in ("handshake_rules", "pipeline", "backpressure", "ordering"):
        cm.pop(forbidden, None)
    latency = cm.get("latency")
    if isinstance(latency, dict):
        pruned_latency: dict[str, Any] = {}
        for lane, entry in latency.items():
            if isinstance(entry, dict):
                lane_entry = dict(entry)
                try:
                    if int(lane_entry.get("min_cycles") or 0) >= 1:
                        lane_entry["min_cycles"] = 0
                except (TypeError, ValueError):
                    lane_entry["min_cycles"] = 0
                pruned_latency[lane] = lane_entry
            else:
                pruned_latency[lane] = entry
        cm["latency"] = pruned_latency
    cm["purpose"] = cm.get("purpose") or (
        "Combinational (cycle_model_waiver) IP: same-cycle outputs, no clocked "
        "ordering, no handshake. Retained only for clock/reset metadata."
    )
    cm["cycle_model_waiver"] = True
    cm["clock"] = cm.get("clock") or clock
    return cm


def _ensure_cycle_model(doc: dict[str, Any], combinational: bool = False) -> dict[str, Any]:
    if combinational:
        return _combinational_cycle_model(doc)
    cm = dict(doc.get("cycle_model")) if isinstance(doc.get("cycle_model"), dict) else {}
    clock, freq = _first_clock(doc)
    cm.setdefault("executable", "python")
    cm.setdefault(
        "backend_policy",
        "Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.",
    )
    cm.setdefault("performance", {
        "frequency_mhz": freq,
        "throughput": {"sustained_beats_per_cycle": 1, "condition": "No backpressure on the active interface"},
        "outstanding": {"max": 1, "description": "Default one accepted operation until the SSOT declares deeper buffering"},
        "depth": {"pipeline_stages": 3, "queue_depth": 1, "description": "Default accept/evaluate/observe cycle model depth"},
    })
    generic_handshake = (
        isinstance(cm.get("handshake_rules"), list)
        and len(cm.get("handshake_rules") or []) <= 1
        and "valid/ready" in str((cm.get("handshake_rules") or [{}])[0].get("signal", ""))
    )
    if all(cm.get(k) for k in ("clock", "reset", "latency", "handshake_rules", "pipeline", "ordering")) and not generic_handshake:
        return cm
    reset, polarity, sync_async = _first_reset(doc)
    dataflow = doc.get("dataflow") if isinstance(doc.get("dataflow"), dict) else {}
    return {
        "purpose": "Cycle/handshake contract for rtl-gen and waveform-based verification.",
        "executable": "python",
        "backend_policy": "Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.",
        "clock": clock,
        "reset": {
            "signal": reset,
            "polarity": polarity,
            "assertion": f"{reset} assertion returns architectural state to declared reset values",
            "deassertion": f"Logic may accept transactions after {sync_async} deassertion completes",
        },
        "latency": {
            "control_or_request_accept": {"min_cycles": 0, "max_cycles": None, "description": "Bounded by declared valid/ready or protocol acceptance rules"},
            "primary_operation": {"min_cycles": 1, "max_cycles": None, "description": f"Runs on {clock} at nominal {freq} MHz; max depends on declared backpressure and implementation state"},
            "response_or_observable_result": {"min_cycles": 0, "max_cycles": None, "description": "Held stable until the declared response/output acceptance condition"},
        },
        "handshake_rules": _interface_handshakes(doc),
        "pipeline": [
            {"stage": "S0_ACCEPT", "cycle": "0..N", "action": "Accept legal request/command/packet/control work under declared handshake rules."},
            {"stage": "S1_EVALUATE", "cycle": "N..M", "action": "Evaluate function_model transaction and update only declared state."},
            {"stage": "S2_OBSERVE", "cycle": "M..K", "action": "Publish response/status/output/debug event and hold it stable until accepted."},
        ],
        "ordering": [
            "Accepted requests update architectural state only on clock edges.",
            "Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.",
            "Backpressure stalls the active handshake stage without corrupting stored state.",
        ] + (["Read/dataflow stages must precede dependent write/output stages where declared in dataflow."] if dataflow else []),
        "backpressure": ["Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable."],
        "performance": {
            "frequency_mhz": freq,
            "throughput": {"sustained_beats_per_cycle": 1, "condition": "No backpressure on the active interface"},
            "outstanding": {"max": 1, "description": "Default one accepted operation until the SSOT declares deeper buffering"},
            "depth": {"pipeline_stages": 3, "queue_depth": 1, "description": "Default accept/evaluate/observe cycle model depth"},
        },
        "observability": ["Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario."],
    }


def _ensure_timing(doc: dict[str, Any]) -> dict[str, Any]:
    timing = doc.get("timing") if isinstance(doc.get("timing"), dict) else {}
    clock, freq = _first_clock(doc)
    timing.setdefault("target_clocks", [{"name": clock, "frequency_mhz": freq, "period_ns": round(1000 / max(freq, 1), 3), "uncertainty_ns": 0.2}])
    timing.setdefault("latency_budget", {
        "register_access": {"min": 0, "max": None, "measured_from": "valid && ready", "measured_to": "response valid && ready"},
        "primary_operation": {"min": 1, "max": None, "measured_from": "start/request accepted", "measured_to": "done/response accepted"},
    })
    timing.setdefault("sta_expectations", {"setup_wns_ns_min": 0.0, "hold_wns_ns_min": 0.0, "required_reports": ["sta/out/timing.rpt", "sta/out/wns.json"]})
    return timing


def _ensure_power(doc: dict[str, Any]) -> dict[str, Any]:
    power = doc.get("power") if isinstance(doc.get("power"), dict) else {}
    clock, _ = _first_clock(doc)
    power.setdefault("domains", [{"name": "PD_MAIN", "voltage": "nominal", "clock_domains": [clock], "isolation": "not_required_single_domain"}])
    states = power.get("power_states") or power.get("low_power_states")
    power["power_states"] = states if isinstance(states, list) and states else [{"name": "ON", "entry": "reset deasserted", "exit": "reset asserted", "guarantees": ["All declared IP functionality active"]}]
    power.setdefault("clock_gating", {"required": False, "rationale": "No explicit integrated clock-gating requirement in approved SSOT"})
    power.setdefault("upf_required", False)
    return power


def _ensure_security(doc: dict[str, Any]) -> dict[str, Any]:
    sec = doc.get("security") if isinstance(doc.get("security"), dict) else {}
    sec.setdefault("classification", "non_secure_leaf_ip")
    sec.setdefault("assets", [
        {"name": "configuration_state", "protection": "CSR/configuration updates must be deterministic and reset-safe"},
        {"name": "data_integrity", "protection": "Data/control outputs must match function_model transactions"},
    ])
    sec.setdefault("threat_model", [
        {"threat": "invalid configuration or address", "mitigation": "error_handling declares detection, architectural effect, and recovery"},
        {"threat": "silent data/control corruption", "mitigation": "test_requirements scoreboard checks every declared functional transaction"},
    ])
    sec.setdefault("privilege_model", "System-level access control is owned by the integrating bus/firewall unless explicitly declared here.")
    return sec


def _ensure_error_handling(doc: dict[str, Any]) -> dict[str, Any]:
    err = doc.get("error_handling") if isinstance(doc.get("error_handling"), dict) else {}
    sources = _error_sources(doc)
    recovery = err.get("recovery")
    if isinstance(recovery, dict):
        recovery_value: Any = recovery
    elif recovery:
        recovery_value = recovery
    else:
        recovery_value = [{"action": "reset or software clear", "clears": ["error/status indicators"], "preserves": ["configuration unless reset policy states otherwise"]}]
    return {
        **err,
        "error_sources": sources,
        "propagation": err.get("propagation") or ["Errors update status/debug observability and propagate through declared response/interrupt mechanisms."],
        "recovery": recovery_value,
    }


def _ensure_debug(doc: dict[str, Any]) -> dict[str, Any]:
    clock, _ = _first_clock(doc)
    debug = doc.get("debug_observability") if isinstance(doc.get("debug_observability"), dict) else {}
    debug.setdefault("waveform_must_probe", [clock, _first_reset(doc)[0], "fsm_state", "start_or_request", "done_or_response", "error_status", "irq_or_status_outputs"])
    debug.setdefault(
        "trace_events",
        [
            {"name": "operation_start", "trigger": "start/request accepted"},
            {"name": "operation_complete", "trigger": "done/response accepted"},
            {"name": "error_detected", "trigger": "any error_handling.error_sources condition"},
        ],
    )
    debug.setdefault("status_outputs", ["status/debug signals declared in io_list or registers"])
    return debug


def _ensure_integration(doc: dict[str, Any]) -> dict[str, Any]:
    existing = doc.get("integration") if isinstance(doc.get("integration"), dict) else {}
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    interfaces = [i.get("name") for i in io.get("interfaces") or [] if isinstance(i, dict) and i.get("name")]
    existing.setdefault("bus_attachment", {"interfaces": interfaces, "address_ownership": "SoC assigns base addresses and external routing not owned by this leaf IP"})
    existing.setdefault("dependencies", {"external_modules": [], "external_clocks": [_first_clock(doc)[0]], "external_resets": [_first_reset(doc)[0]]})
    existing.setdefault("connections", [])
    existing.setdefault(
        "connection_contract_status",
        (
            "missing machine-readable module wiring; child RTL drafts may proceed from owner packets, "
            "but top integration/signoff must stay blocked until SSOT authors integration.connections "
            "or sub_modules[].connections with module/port/signal records"
        ),
    )
    existing.setdefault("integration_notes", ["Integrator must connect every declared io_list port and honor timing/reset assumptions."])
    return existing


def _ensure_dft(doc: dict[str, Any]) -> dict[str, Any]:
    dft = doc.get("dft") if isinstance(doc.get("dft"), dict) else {}
    dft.setdefault("scan_required", False)
    dft.setdefault("controllability", {"reset": _first_reset(doc)[0], "clocks": [_first_clock(doc)[0]], "primary_inputs": "all io_list inputs controllable in testbench"})
    dft.setdefault("observability", {"required_internal_points": ["fsm_state", "status", "error_status"], "outputs": "all io_list outputs observable"})
    dft.setdefault("mbist_required", bool((doc.get("memory") or {}).get("instances")) if isinstance(doc.get("memory"), dict) else False)
    return dft


def _ensure_synthesis(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    syn = doc.get("synthesis") if isinstance(doc.get("synthesis"), dict) else {}
    syn["dialect"] = "systemverilog_2012"
    syn.setdefault("top_module", doc.get("top_module", {}).get("name", ip) if isinstance(doc.get("top_module"), dict) else ip)
    syn.setdefault("tool_flow", "yosys")
    syn.setdefault("target_technology", "sky130_fd_sc_hd")
    syn.setdefault("target_library", "sky130_fd_sc_hd")
    syn.setdefault("liberty_env_var", "SKY130_LIB")
    corner = syn.get("corner") if isinstance(syn.get("corner"), dict) else {}
    corner.setdefault("name", "sky130_fd_sc_hd__ss_100C_1v40")
    corner.setdefault("process", "ss")
    corner.setdefault("temperature_c", 100)
    corner.setdefault("voltage_v", 1.40)
    syn["corner"] = corner
    syn.setdefault(
        "library_policy",
        (
            "Use the SKY130_LIB environment variable to locate the SS corner "
            "Liberty file for the declared sky130_fd_sc_hd target library; "
            "synthesis and STA must stop if the file is unreadable or does not "
            "match the declared corner."
        ),
    )
    syn.setdefault("constraints", ["No inferred latches", "No unresolved black boxes", "All sequential state reset or intentionally initialized"])
    syn.setdefault("ppa_targets", {"area_um2_max": None, "power_mw_max": None, "frequency_mhz_min": _first_clock(doc)[1]})
    syn.setdefault("required_outputs", ["syn/out/synth.v", "syn/out/area.json", "syn/out/syn.report.md", "sta/out/wns.json"])
    return syn


def _ensure_pnr(doc: dict[str, Any]) -> dict[str, Any]:
    pnr = doc.get("pnr") if isinstance(doc.get("pnr"), dict) else {}
    pnr.setdefault("utilization_pct", 60)
    pnr.setdefault("aspect_ratio", 1.0)
    pnr.setdefault("core_space_um", 2.0)
    pnr.setdefault("global_density", 0.65)
    io_layers = pnr.get("io_layers") if isinstance(pnr.get("io_layers"), dict) else {}
    io_layers.setdefault("horizontal", "met3")
    io_layers.setdefault("vertical", "met2")
    pnr["io_layers"] = io_layers
    pnr.setdefault("cts_buf_list", ["sky130_fd_sc_hd__clkbuf_4", "sky130_fd_sc_hd__clkbuf_8"])
    routing = pnr.get("routing") if isinstance(pnr.get("routing"), dict) else {}
    routing.setdefault("signal_layers", {"min": "met1", "max": "met5"})
    routing.setdefault("drc_waivers", [])
    pnr["routing"] = routing
    return pnr


def _ensure_test_requirements(doc: dict[str, Any]) -> dict[str, Any]:
    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    scenarios = []
    for idx, sc in enumerate(tr.get("scenarios") or [], start=1):
        if not isinstance(sc, dict):
            continue
        sid = sc.get("id") or f"SC{idx:02d}"
        name = sc.get("name") or f"Scenario {idx}"
        scenarios.append({
            **sc,
            "id": sid,
            "name": name,
            "stimulus": sc.get("stimulus") or f"Drive the sequence for {name} using declared interfaces and configuration registers.",
            "expected": sc.get("expected") or f"{name} behavior matches function_model and cycle_model.",
            "checker": sc.get("checker") or f"Scoreboard/checker compares observed {name} result against function_model expected result.",
            "coverage": sc.get("coverage") or [str(sid), "function_model", "cycle_model"],
        })
    weak_default = (
        len(scenarios) < 10
        or any(str(sc.get("name") or "").lower() in {"primary operation", "basic operation"} for sc in scenarios)
    )
    if weak_default:
        fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
        transactions = [tx for tx in (fm.get("transactions") or []) if isinstance(tx, dict)]
        scenarios = [
            {
                "id": "SC01",
                "name": "reset contract",
                "stimulus": "Assert and release the declared reset while all external interfaces remain idle.",
                "expected": "Architectural state, status, outputs, and debug observability match function_model reset outputs.",
                "checker": "Reset checker compares all declared reset-visible state against function_model and cycle_model reset rules.",
                "coverage": ["function_model.reset", "cycle_model.reset"],
            },
            {
                "id": "SC02",
                "name": "primary approved behavior",
                "stimulus": "Drive a legal request, transaction, command, packet, or CSR operation from function_model primary preconditions.",
                "expected": "Externally observable result/status/side effects match the function_model primary transaction.",
                "checker": "FL-vs-RTL scoreboard compares observable outputs and state updates from the locked function_model.",
                "coverage": ["function_model.primary", "features", "dataflow"],
            },
            {
                "id": "SC03",
                "name": "cycle handshake and backpressure",
                "stimulus": "Apply legal stalls or delayed handshakes on every declared cycle_model interface phase.",
                "expected": "Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.",
                "checker": "Protocol monitor and scoreboard check cycle_model.handshake_rules, ordering, and latency budget.",
                "coverage": ["cycle_model.handshake_rules", "cycle_model.ordering", "backpressure"],
            },
            {
                "id": "SC04",
                "name": "error and recovery policy",
                "stimulus": "Inject each declared error_handling.error_sources condition where the interface can represent it.",
                "expected": "Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.",
                "checker": "Negative checker compares error result and recovery state against function_model error_cases.",
                "coverage": ["error_handling.error_sources", "function_model.error_cases"],
            },
            {
                "id": "SC05",
                "name": "debug and trace observability",
                "stimulus": "Run nominal and error flows while sampling every debug_observability waveform/status/trace point.",
                "expected": "Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.",
                "checker": "Waveform/trace checker validates debug_observability entries and traceability.yaml_to_output rows.",
                "coverage": ["debug_observability", "traceability"],
            },
        ]
        for idx, tx in enumerate(transactions[:7], start=6):
            tx_id = str(tx.get("id") or tx.get("name") or f"FM{idx}")
            scenarios.append(
                {
                    "id": f"SC{idx:02d}",
                    "name": f"function_model transaction {tx_id}",
                    "stimulus": f"Drive preconditions for function_model transaction `{tx_id}`.",
                    "expected": f"Outputs and side effects match `{tx_id}` exactly.",
                    "checker": "Transaction scoreboard compares RTL observations against the locked function_model transaction.",
                    "coverage": [f"function_model.transactions.{tx_id}"],
                }
            )
    tr["scenarios"] = scenarios
    existing_checks = tr.get("scoreboard_checks") or 0
    if isinstance(existing_checks, list):
        existing_checks = len(existing_checks)
    elif isinstance(existing_checks, dict):
        existing_checks = len(existing_checks)
    tr["scoreboard_checks"] = max(int(existing_checks or 0), len(scenarios))
    tr["coverage_goals"] = {
        **(
            {
                "function": {
                    "target_pct": 100,
                    "model": "function_model",
                    "description": "Behavioral coverage for function_model transactions, state updates, outputs, errors, and debug/status observability.",
                    "bins": [
                        {
                            "id": "FCOV_PRIMARY_TRANSACTION",
                            "source_ref": "function_model.transactions",
                            "class": "transaction",
                            "description": "Primary function_model transaction observed with RTL scoreboard evidence",
                        }
                    ],
                },
                "cycle": {
                    "target_pct": 100,
                    "model": "cycle_model",
                    "description": "Cycle coverage for cycle_model latency, pipeline stages, ordering, handshake rules, backpressure, and FSM transitions.",
                    "bins": [
                        {
                            "id": "CCOV_PRIMARY_CYCLE_RULE",
                            "source_ref": "cycle_model",
                            "class": "cycle_rule",
                            "description": "Primary cycle_model rule observed with RTL waveform/checker evidence",
                        }
                    ],
                },
                "functional": "Legacy alias: coverage_goals.function and coverage_goals.cycle must both close.",
                "evidence": (
                    "Tool-instrumented structural metrics are optional unless an explicit SSOT metric goal "
                    "with matching tool evidence is added."
                ),
            }
            if not isinstance(tr.get("coverage_goals"), dict)
            else tr.get("coverage_goals")
        ),
        "scenario": "All SSOT scenarios pass with executable cocotb/pyuvm checkers and FL-vs-RTL scoreboard evidence",
    }
    goals = tr["coverage_goals"]
    if isinstance(goals, dict):
        goals.setdefault("function", {
            "target_pct": 100,
            "model": "function_model",
            "description": "Behavioral coverage for function_model transactions and architecturally visible results.",
            "bins": [],
        })
        goals.setdefault("cycle", {
            "target_pct": 100,
            "model": "cycle_model",
            "description": "Cycle/handshake/latency/FSM coverage from cycle_model.",
            "bins": [],
        })
        for domain, model in (("function", "function_model"), ("cycle", "cycle_model")):
            section = goals.get(domain)
            if not isinstance(section, dict):
                section = {}
                goals[domain] = section
            section.setdefault("target_pct", 100)
            section.setdefault("model", model)
            section.setdefault(
                "description",
                "Behavioral coverage from function_model." if domain == "function" else "Cycle/performance coverage from cycle_model.",
            )
            bins = section.get("bins")
            normalized_bins: list[dict[str, Any]] = []
            if isinstance(bins, list):
                for idx, item in enumerate(bins, start=1):
                    row = dict(item) if isinstance(item, dict) else {"description": str(item)}
                    source_ref = str(row.get("source_ref") or "")
                    if domain == "function" and "function_model" not in source_ref:
                        source_ref = "function_model.transactions"
                    if domain == "cycle" and "cycle_model" not in source_ref and not source_ref.startswith("fsm."):
                        source_ref = "cycle_model.performance"
                    row["id"] = row.get("id") or f"{domain.upper()}_COV_{idx:02d}"
                    row["source_ref"] = source_ref or model
                    row["class"] = row.get("class") or ("transaction" if domain == "function" else "cycle_rule")
                    row["description"] = row.get("description") or f"{domain} coverage bin derived from {row['source_ref']}"
                    normalized_bins.append(row)
            if not normalized_bins:
                normalized_bins = [{
                    "id": "FCOV_PRIMARY_TRANSACTION" if domain == "function" else "CCOV_PRIMARY_CYCLE_RULE",
                    "source_ref": "function_model.transactions" if domain == "function" else "cycle_model",
                    "class": "transaction" if domain == "function" else "cycle_rule",
                    "description": (
                        "Primary function_model transaction observed with RTL scoreboard evidence"
                        if domain == "function"
                        else "Primary cycle_model rule observed with RTL waveform/checker evidence"
                    ),
                }]
            section["bins"] = normalized_bins
    return tr


def _ensure_quality_gates(doc: dict[str, Any] | None = None, ip: str = "") -> dict[str, Any]:
    doc = doc or {}
    profile = _rtl_quality_profile(doc, ip) if ip else "standard"
    return {
        "ssot": {"pass": "check_ssot_disk.sh exits 0 and ATLAS SSOT progress is fully approved", "evidence": ["check_ssot_disk.sh PASS", "ATLAS /api/progress ssot all sections approved"]},
        "rtl": {"pass": "All expected RTL files exist, are production-ready, compile, and lint within warning budget", "evidence": ["list/<ip>.f", "compile log", "lint log"]},
        "rtl_gen": {
            "profile": profile,
            "pass": (
                "rtl-gen execution_policy.pass_allowed is true, every required SSOT-derived RTL TODO is closed, "
                "and provenance proves common_ai_agent rtl-gen authored the RTL without fixed-template fallback behavior"
            ),
            "evidence": [
                "rtl/rtl_authoring_plan.json",
                "logs/rtl-gen/rtl_todo_plan.json",
                "rtl/provenance.json",
                "rtl_compile.json",
                "lint/dut_lint.json",
            ],
        },
        "dv": {"pass": "Every SSOT test_requirements scenario has an executable checker and FL-vs-RTL equivalence goal", "evidence": ["verify/equivalence_goals.json", "sim/scoreboard_events.jsonl", "tb/cocotb tests", "scenario implementation map"]},
        "coverage": {"pass": "Functional coverage passes and any explicitly requested structural metrics have matching evidence or approved waivers", "evidence": ["coverage report", "coverage waiver list if any"]},
        "eda": {"pass": "Synthesis/STA/DFT expectations have reports or approved waivers", "evidence": ["syn/sta/dft reports"]},
        "signoff": {"pass": "SSOT, FL/equivalence, RTL, lint, DV, sim, coverage, and EDA gates pass with fresh artifacts", "evidence": ["ATLAS progress signoff PASS"]},
    }


def _merge_quality_gates(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    defaults = _ensure_quality_gates(doc, ip)
    existing = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
    merged: dict[str, Any] = {}
    for key, default in defaults.items():
        current = existing.get(key) if isinstance(existing.get(key), dict) else {}
        merged[key] = {**default, **current}
    for key, value in existing.items():
        if key not in merged:
            merged[key] = value
    rtl_gen = merged.get("rtl_gen") if isinstance(merged.get("rtl_gen"), dict) else {}
    rtl_gen.setdefault("profile", _rtl_quality_profile({**doc, "quality_gates": merged}, ip))
    rtl_gen.setdefault(
        "pass",
        (
            "rtl-gen execution_policy.pass_allowed is true, every required SSOT-derived RTL TODO is closed, "
            "and provenance proves common_ai_agent rtl-gen authored the RTL without fixed-template fallback behavior"
        ),
    )
    rtl_gen.setdefault("evidence", defaults["rtl_gen"]["evidence"])
    rtl_gen["profile"] = _rtl_quality_profile({**doc, "quality_gates": {**merged, "rtl_gen": rtl_gen}}, ip)
    merged["rtl_gen"] = rtl_gen
    return merged


def _ensure_traceability(doc: dict[str, Any]) -> dict[str, Any]:
    trace = doc.get("traceability") if isinstance(doc.get("traceability"), dict) else {}
    rows = trace.get("yaml_to_output") if isinstance(trace.get("yaml_to_output"), list) else []
    required = [
        ("function_model", "RTL behavior and TB reference model"),
        ("cycle_model", "RTL handshake/pipeline timing and waveform checks"),
        ("function_model/cycle_model/test_requirements", "verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts"),
        ("timing", "STA constraints and latency pass/fail criteria"),
        ("security", "Threat mitigations and negative tests"),
        ("error_handling", "Fault RTL paths and DV error scenarios"),
        ("debug_observability", "VCD probes and sim_debug inspection"),
        ("quality_gates", "ATLAS progress/signoff criteria"),
    ]
    existing = {r.get("yaml") for r in rows if isinstance(r, dict)}
    for yaml_key, output in required:
        if yaml_key not in existing:
            rows.append({"yaml": yaml_key, "output": output})
    trace["yaml_to_output"] = rows or [{"yaml": "top_module", "output": "Generated RTL/TB/docs root identity"}]
    return trace


def _todo_text(value: Any, limit: int = 260) -> str:
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            if key in {"id", "name", "description", "condition", "rule", "action", "outputs", "side_effects", "expected"}:
                parts.append(f"{key}={_todo_text(val, 120)}")
        text = "; ".join(parts) if parts else str(value)
    elif isinstance(value, list):
        text = "; ".join(_todo_text(item, 120) for item in value[:5])
    else:
        text = str(value or "").strip()
    text = " ".join(text.split())
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def _todo_id(prefix: str, value: Any, index: int) -> str:
    token = str(value or f"item_{index}")
    token = "".join(ch if ch.isalnum() else "_" for ch in token.upper()).strip("_")
    token = token or f"ITEM_{index}"
    return f"{prefix}_{token[:64]}"


def _machine_connection_count(raw: Any, default_module: str = "") -> int:
    if isinstance(raw, list):
        return sum(_machine_connection_count(item, default_module) for item in raw)
    if not isinstance(raw, dict):
        return 0
    module = raw.get("module") or raw.get("child") or raw.get("target_module") or raw.get("sink_module") or default_module
    for key in ("ports", "port_map", "connections"):
        nested = raw.get(key)
        if isinstance(nested, dict):
            return sum(
                1
                for port, signal in nested.items()
                if str(module or "").strip() and str(port or "").strip() and str(signal or "").strip()
            )
        if isinstance(nested, list):
            return sum(_machine_connection_count(item, str(module or "")) for item in nested)
    port = raw.get("port") or raw.get("child_port") or raw.get("target_port") or raw.get("sink_port") or raw.get("to_port") or raw.get("dst_port")
    signal = raw.get("signal") or raw.get("expr") or raw.get("expression") or raw.get("source_signal") or raw.get("from_signal") or raw.get("top_signal")
    return 1 if str(module or "").strip() and str(port or "").strip() and str(signal or "").strip() else 0


def _production_connection_contract_missing(doc: dict[str, Any], ip: str) -> bool:
    if _rtl_quality_profile(doc, ip) != "production":
        return False
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_names = {str(ip).lower(), str(top.get("name") or "").lower()}
    active_children = []
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        ownership = str(item.get("ownership") or "manifest").lower()
        if ownership in {"child_ssot", "external", "blackbox", "conceptual", "coverage", "verification"}:
            continue
        if item.get("rtl_emit") is False or bool(item.get("wiring_only")):
            continue
        name = str(item.get("name") or "").lower()
        if name and name not in top_names:
            active_children.append(item)
    if not active_children:
        return False
    integration = doc.get("integration") if isinstance(doc.get("integration"), dict) else {}
    count = 0
    for key in ("connections", "internal_connections", "port_connections", "wiring"):
        count += _machine_connection_count(integration.get(key), "")
    for item in active_children:
        count += _machine_connection_count(item.get("connections"), str(item.get("name") or ""))
    return count <= 0


def _has_connection_contract_todo(todos: list[dict[str, Any]]) -> bool:
    for item in todos:
        if not isinstance(item, dict):
            continue
        text = " ".join(
            [
                str(item.get("id") or ""),
                str(item.get("content") or ""),
                str(item.get("detail") or ""),
                " ".join(str(ref) for ref in item.get("source_refs") or []),
            ]
        ).lower()
        if "connection" in text and ("integration" in text or "sub_modules" in text or "module" in text):
            return True
    return False


_TARGET_SCALE_MIN_ALIASES: tuple[tuple[str, ...], ...] = (
    ("min_source_files", "source_files_min", "file_count_min", "files_min", "min_files"),
    ("min_modules", "modules_min", "module_count_min"),
    ("min_lines", "lines_min", "line_count_min"),
    ("min_nonconstant_assigns", "nonconstant_assigns_min", "assigns_min", "min_assigns"),
    ("min_procedural_blocks", "procedural_blocks_min", "always_blocks_min", "min_always_blocks"),
    ("min_state_updates", "state_updates_min"),
    ("min_control_flow", "control_flow_min", "case_blocks_min", "min_case_blocks"),
    ("min_instances", "instances_min", "instance_candidates_min"),
    ("min_depth_score", "depth_score_min", "implementation_depth_score_min"),
    ("min_logic_modules", "logic_modules_min"),
    ("min_behavior_owner_logic_modules", "behavior_owner_logic_modules_min", "behavior_owner_modules_min"),
)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _target_scale_has_positive_min(raw: Any) -> bool:
    if not isinstance(raw, dict):
        return False
    for names in _TARGET_SCALE_MIN_ALIASES:
        if any(_positive_int(raw.get(name)) is not None for name in names):
            return True
    return False


def _target_scale_waiver_approved(raw: Any) -> bool:
    return isinstance(raw, dict) and bool(raw.get("approved") or raw.get("accepted") or raw.get("waived"))


def _production_target_scale_policy_missing(doc: dict[str, Any], ip: str) -> bool:
    if _rtl_quality_profile(doc, ip) != "production":
        return False
    qg = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
    rtl_gen = qg.get("rtl_gen") if isinstance(qg.get("rtl_gen"), dict) else {}
    if _target_scale_has_positive_min(rtl_gen.get("target_scale")):
        return False
    if _target_scale_waiver_approved(rtl_gen.get("target_scale_waiver")):
        return False
    return True


def _is_target_scale_policy_todo(item: dict[str, Any]) -> bool:
    if not isinstance(item, dict):
        return False
    text = " ".join(
        [
            str(item.get("id") or ""),
            str(item.get("content") or ""),
            str(item.get("detail") or ""),
            " ".join(str(ref) for ref in item.get("source_refs") or []),
        ]
    ).lower()
    return "target_scale" in text or ("target scale" in text and "quality_gates.rtl_gen" in text)


def _has_target_scale_policy_todo(todos: list[dict[str, Any]]) -> bool:
    return any(_is_target_scale_policy_todo(item) for item in todos if isinstance(item, dict))


def _module_owner(doc: dict[str, Any], ip: str, refs: list[str] | None = None) -> tuple[str, str]:
    refs_text = " ".join(refs or []).lower()
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_name = str(top.get("name") or ip)
    fallback = (top_name, f"rtl/{top_name}.sv")
    for item in doc.get("sub_modules") or []:
        if not isinstance(item, dict):
            continue
        ownership = str(item.get("ownership") or "manifest").lower()
        if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or item.get("rtl_emit") is False:
            continue
        name = str(item.get("name") or "").strip()
        file_name = str(item.get("file") or "").strip()
        if not name:
            continue
        if name.endswith("_pkg") or file_name.endswith("_pkg.sv"):
            continue
        haystack = " ".join(
            _todo_text(item.get(key), 400)
            for key in (
                "name",
                "description",
                "implements",
                "source_sections",
                "function_model_refs",
                "cycle_model_refs",
                "feature_refs",
                "dataflow_refs",
                "register_refs",
                "fsm_refs",
                "test_refs",
                "ssot_refs",
            )
        ).lower()
        if refs_text and any(ref.lower() in haystack or haystack in ref.lower() for ref in refs or []):
            return name, file_name or f"rtl/{name}.sv"
        if not refs_text:
            return name, file_name or f"rtl/{name}.sv"
    return fallback


def _append_rtl_todo(
    todos: list[dict[str, Any]],
    *,
    id: str,
    content: str,
    detail: str,
    criteria: list[str],
    source_refs: list[str],
    owner: tuple[str, str],
    priority: str = "high",
    extra: dict[str, Any] | None = None,
) -> None:
    seen = {item.get("id") for item in todos if isinstance(item, dict)}
    base = id
    suffix = 2
    while id in seen:
        id = f"{base}_{suffix}"
        suffix += 1
    item = {
        "id": id,
        "content": content,
        "detail": detail,
        "criteria": [item for item in criteria if str(item or "").strip()],
        "source_refs": source_refs,
        "owner_module": owner[0],
        "owner_file": owner[1],
        "priority": priority,
        "required": True,
    }
    if extra:
        item.update(extra)
    todos.append(item)


def _synthesize_rtl_workflow_todos(doc: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    top_name = str(top.get("name") or ip)
    top_owner = (top_name, f"rtl/{top_name}.sv")
    _append_rtl_todo(
        todos,
        id="RTL_IMPLEMENT_SSOT_CONTRACT",
        content="Implement the complete SSOT RTL contract without fixed-template fallback behavior",
        detail=(
            "Use the current SSOT as the only source for ports, parameters, function_model, cycle_model, "
            "registers, dataflow, error/security/debug behavior, decomposition ownership, and quality gates."
        ),
        criteria=[
            "Generated RTL drives only SSOT-approved externally visible behavior",
            "No placeholder heartbeat, tie-off, alive-only, or comment-only implementation is used as evidence",
            "derive_rtl_todos.py --audit-rtl reports every required TODO as pass",
        ],
        source_refs=["top_module", "function_model", "cycle_model", "quality_gates.rtl", "quality_gates.rtl_gen"],
        owner=top_owner,
    )

    for idx, item in enumerate(doc.get("sub_modules") or []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or f"module_{idx}")
        refs = []
        for key in (
            "source_sections",
            "function_model_refs",
            "cycle_model_refs",
            "feature_refs",
            "dataflow_refs",
            "register_refs",
            "fsm_refs",
            "test_refs",
            "ssot_refs",
        ):
            raw = item.get(key)
            if isinstance(raw, list):
                refs.extend(str(v) for v in raw if str(v or "").strip())
            elif raw:
                refs.append(str(raw))
        owner = _module_owner(doc, ip, refs) if str(item.get("ownership") or "").lower() == "conceptual" else (
            name,
            str(item.get("file") or f"rtl/{name}.sv"),
        )
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_MODULE", name, idx),
            content=f"Implement or account for SSOT module slice `{name}`",
            detail=_todo_text(item.get("description") or item),
            criteria=[
                "Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module",
                "Module slice has traceability evidence in rtl_todo_plan.json",
                "No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned",
            ],
            source_refs=refs or [f"sub_modules[{idx}]"],
            owner=owner,
        )

    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if not isinstance(tx, dict):
            continue
        tx_id = str(tx.get("id") or tx.get("name") or f"transaction_{idx}")
        source = f"function_model.transactions[{idx}]"
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_FM_TX", tx_id, idx),
            content=f"Implement FunctionalModel transaction `{tx_id}` in RTL",
            detail=(
                f"Preconditions: {_todo_text(tx.get('preconditions'))}. "
                f"Outputs: {_todo_text(tx.get('outputs'))}. "
                f"Side effects: {_todo_text(tx.get('side_effects'))}. "
                f"Error cases: {_todo_text(tx.get('error_cases'))}."
            ),
            criteria=[
                "RTL samples the transaction only under the approved preconditions",
                "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
                "All side effects and error cases have observable state, status, or handoff evidence",
            ],
            source_refs=[source, f"function_model.transactions.{tx_id}"],
            owner=_module_owner(doc, ip, [source, f"function_model.transactions.{tx_id}"]),
        )
        for rule_idx, rule in enumerate(tx.get("output_rules") or []):
            if not isinstance(rule, dict):
                continue
            rule_name = str(rule.get("name") or rule.get("port") or f"output_{rule_idx}")
            _append_rtl_todo(
                todos,
                id=_todo_id("RTL_OUTPUT_RULE", rule_name, rule_idx),
                content=f"Drive output rule `{rule_name}` from FunctionalModel expression",
                detail=f"Expression: {_todo_text(rule.get('expr') or rule.get('expression') or rule)}",
                criteria=[
                    f"RTL output `{rule.get('port') or rule_name}` follows the SSOT expression",
                    "Expression inputs are mapped through rtl_contract.input_map or declared ports",
                    "FL-vs-RTL scoreboard can compare this observable without changing SSOT",
                ],
                source_refs=[f"{source}.output_rules[{rule_idx}]"],
                owner=_module_owner(doc, ip, [f"{source}.output_rules[{rule_idx}]", rule_name]),
            )
        for rule_idx, rule in enumerate(tx.get("state_updates") or []):
            if not isinstance(rule, dict):
                continue
            state_name = str(rule.get("name") or rule.get("state") or f"state_{rule_idx}")
            _append_rtl_todo(
                todos,
                id=_todo_id("RTL_STATE_UPDATE", state_name, rule_idx),
                content=f"Implement state update `{state_name}` from FunctionalModel expression",
                detail=f"Expression: {_todo_text(rule.get('expr') or rule.get('expression') or rule)}",
                criteria=[
                    "RTL updates the state only on the approved sample condition",
                    "Reset value and width match function_model.state_variables",
                    "Debug/status visibility remains consistent with SSOT traceability",
                ],
                source_refs=[f"{source}.state_updates[{rule_idx}]"],
                owner=_module_owner(doc, ip, [f"{source}.state_updates[{rule_idx}]", state_name]),
            )

    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    for key, label in (("handshake_rules", "handshake rule"), ("pipeline", "pipeline stage"), ("ordering", "ordering rule"), ("backpressure", "backpressure rule")):
        for idx, item in enumerate(cm.get(key) or []):
            source = f"cycle_model.{key}[{idx}]"
            _append_rtl_todo(
                todos,
                id=_todo_id(f"RTL_CYCLE_{key}", idx, idx),
                content=f"Implement cycle_model {label} {idx}",
                detail=_todo_text(item),
                criteria=[
                    "RTL timing/handshake behavior follows this cycle_model entry",
                    "Signals remain stable or advance only under the approved protocol phase",
                    "The behavior is visible to waveform/sim-debug or scoreboard checks",
                ],
                source_refs=[source],
                owner=_module_owner(doc, ip, [source]),
            )

    regs = (doc.get("registers") or {}).get("register_list") if isinstance(doc.get("registers"), dict) else []
    for idx, reg in enumerate(regs or []):
        if not isinstance(reg, dict):
            continue
        name = str(reg.get("name") or f"reg_{idx}")
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_REGISTER", name, idx),
            content=f"Implement CSR/register `{name}` access behavior",
            detail=_todo_text(reg),
            criteria=[
                "Reset/access/field side effects match registers.register_list",
                "Illegal access behavior follows error_handling/security policy",
                "Readback and W1C/RW/RO semantics are covered by RTL and DV plan",
            ],
            source_refs=[f"registers.register_list[{idx}]"],
            owner=_module_owner(doc, ip, [f"registers.register_list[{idx}]", name]),
        )

    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    for idx, sc in enumerate(tr.get("scenarios") or []):
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or sc.get("name") or f"SC{idx}")
        _append_rtl_todo(
            todos,
            id=_todo_id("RTL_SCENARIO_SUPPORT", sid, idx),
            content=f"Expose RTL behavior needed by SSOT scenario `{sid}`",
            detail=f"Stimulus: {_todo_text(sc.get('stimulus'))}. Expected: {_todo_text(sc.get('expected'))}.",
            criteria=[
                "RTL has observable behavior for the scenario checker without weakening expected results",
                "Scenario coverage can be closed by tb-gen using function_model/cycle_model",
                "If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass",
            ],
            source_refs=[f"test_requirements.scenarios[{idx}]"],
            owner=_module_owner(doc, ip, [f"test_requirements.scenarios[{idx}]", sid]),
            priority="normal",
        )

    _append_rtl_todo(
        todos,
        id="RTL_CLOSE_GATE_TODOS",
        content="Close all rtl_gate.rtl_gen quality-gate TODOs with fresh evidence",
        detail=(
            "Run dynamic TODO audit, DUT compile, DUT-only lint, and static traceability checks after the final RTL edit. "
            "The gate TODOs are pass/fail work items, not summary prose."
        ),
        criteria=[
            "SSOT authority, workflow TODO format, owner traceability, static RTL evidence, compile, lint, and closure gate TODOs pass",
            "rtl_compile.json and lint/dut_lint.json are fresh and clean",
            "open_required_todos is zero",
        ],
        source_refs=["quality_gates.rtl", "quality_gates.rtl_gen", "workflow_todos.rtl-gen", "generation_flow"],
        owner=top_owner,
    )
    return todos


def _current_transaction_ids(doc: dict[str, Any]) -> set[str]:
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    return {
        str(tx.get("id") or tx.get("name") or "").strip()
        for tx in fm.get("transactions") or []
        if isinstance(tx, dict) and str(tx.get("id") or tx.get("name") or "").strip()
    }


def _has_stale_repair_todo_artifacts(doc: dict[str, Any], todos: list[Any]) -> bool:
    tx_ids = _current_transaction_ids(doc)
    stale_ids = {f"FM{i}" for i in range(1, 5) if f"FM{i}" not in tx_ids}
    for item in todos:
        if not isinstance(item, dict):
            continue
        text = json.dumps(item, sort_keys=True, default=str)
        if REPAIR_TRANSACTION_RULE_MARKER in text or REPAIR_TRANSACTION_STATE_MARKER in text:
            return True
        for tx_id in stale_ids:
            if f"function_model.transactions.{tx_id}" in text or f"`{tx_id}`" in text:
                return True
    return False


def _ensure_workflow_todos(doc: dict[str, Any], ip: str) -> dict[str, Any]:
    todos = doc.get("workflow_todos") if isinstance(doc.get("workflow_todos"), dict) else {}
    rtl_todos = todos.get("rtl-gen") if isinstance(todos.get("rtl-gen"), list) else []
    if not rtl_todos or _has_stale_repair_todo_artifacts(doc, rtl_todos):
        rtl_todos = _synthesize_rtl_workflow_todos(doc, ip)
    if _rtl_quality_profile(doc, ip) != "production":
        rtl_todos = [item for item in rtl_todos if not _is_target_scale_policy_todo(item)]
    if _production_target_scale_policy_missing(doc, ip) and not _has_target_scale_policy_todo(rtl_todos):
        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        top_name = str(top.get("name") or ip)
        _append_rtl_todo(
            rtl_todos,
            id="RTL_TARGET_SCALE_POLICY",
            content="Lock or waive RTL target-scale policy before production signoff",
            detail=(
                "The SSOT is production-profile, but quality_gates.rtl_gen.target_scale has no positive structural minima "
                "and no approved target_scale_waiver is present. Reference-derived target-scale candidates are review inputs "
                "only; a human must lock the chosen minima in SSOT or explicitly approve a waiver before rtl-gen can claim "
                "PL330-level or production top signoff."
            ),
            criteria=[
                "quality_gates.rtl_gen.target_scale contains at least one positive structural minimum such as source_files_min, modules_min, or depth_score_min",
                "or quality_gates.rtl_gen.target_scale_waiver.approved is true with owner and reason",
                "rtl_todo_plan.json target_scale_policy gate passes after rerunning rtl-gen TODO derivation",
            ],
            source_refs=["quality_gates.rtl_gen.target_scale", "quality_gates.rtl_gen.target_scale_waiver", "reports/rtl_reference_profile.json"],
            owner=(top_name, f"rtl/{top_name}.sv"),
            priority="high",
            extra={
                "answer_schema": {
                    "format": "YAML or JSON",
                    "root_key": "target_scale or target_scale_waiver",
                    "target_scale_fields": [
                        "source_files_min",
                        "modules_min",
                        "lines_min",
                        "depth_score_min",
                        "nonconstant_assigns_min",
                        "procedural_blocks_min",
                        "instances_min",
                        "basis",
                    ],
                    "target_scale_waiver_required_fields": ["approved", "reason", "owner"],
                    "rule": "Only human-approved SSOT minima or waiver can close this gate; do not infer target scale from generated RTL.",
                },
                "example_answer": {
                    "target_scale": {
                        "source_files_min": 4,
                        "modules_min": 8,
                        "lines_min": 1200,
                        "depth_score_min": 120,
                        "basis": "Human-approved architecture review calibrated from rtl_reference_profile.json.",
                    },
                    "target_scale_waiver": {
                        "approved": True,
                        "reason": "Smaller variant intentionally does not enforce reference-scale minima.",
                        "owner": "human-review",
                    },
                },
            },
        )
    if _production_connection_contract_missing(doc, ip) and not _has_connection_contract_todo(rtl_todos):
        top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
        top_name = str(top.get("name") or ip)
        _append_rtl_todo(
            rtl_todos,
            id="RTL_RESOLVE_CONNECTION_CONTRACTS",
            content="Resolve production multi-module connection contracts before top integration signoff",
            detail=(
                "The SSOT is production-profile and declares manifest child modules, but it has no machine-readable "
                "integration.connections or sub_modules[].connections records. Child module drafts may proceed from "
                "their owner packets; top wiring, PASS, and signoff must remain blocked until SSOT authors module/port/signal contracts."
            ),
            criteria=[
                "integration.connections or sub_modules[].connections lists every active child module connection as module/port/signal data",
                "rtl_authoring_plan.execution_policy.connection_contract_gap.status becomes ok",
                "Top/gate authoring packet integration_signoff_allowed is true after rerunning rtl-gen TODO derivation",
            ],
            source_refs=["integration.connections", "sub_modules[].connections", "quality_gates.rtl_gen", "workflow_todos.rtl-gen"],
            owner=(top_name, f"rtl/{top_name}.sv"),
            priority="high",
            extra={
                "answer_schema": {
                    "format": "YAML or JSON",
                    "root_key": "connection_contracts",
                    "item_required_fields": ["module", "port", "signal"],
                    "item_optional_fields": [
                        "instance",
                        "direction",
                        "source_ref",
                        "allow_constant",
                        "allow_unused",
                        "tieoff",
                        "reason",
                    ],
                    "rule": "Only approved rows become SSOT wiring contracts; do not infer missing wiring from RTL.",
                },
                "example_answer": {
                    "connection_contracts": [
                        {
                            "module": f"{top_name}_engine",
                            "instance": "u_engine",
                            "port": "done_o",
                            "signal": "done",
                            "source_ref": "integration.connections.done_o",
                        }
                    ]
                },
            },
        )
    todos["rtl-gen"] = rtl_todos
    todos.setdefault("tb-gen", [])
    todos.setdefault("sim_debug", [])
    return todos


_LEGACY_PROTOCOL_HINTS = {
    "apb": "APB4", "apb3": "APB3", "apb4": "APB4",
    "axi": "AXI4", "axil": "AXI4-Lite", "axilite": "AXI4-Lite", "axi_lite": "AXI4-Lite",
    "axi4": "AXI4", "axi4_lite": "AXI4-Lite",
    "ahb": "AHB", "ahbl": "AHB-Lite", "ahb_lite": "AHB-Lite",
    "wishbone": "Wishbone", "wb": "Wishbone",
    "i2c": "I2C", "i3c": "I3C", "spi": "SPI", "uart": "UART",
    "irq": "interrupt", "interrupt": "interrupt", "interrupts": "interrupt",
    "clock_reset": "clock_reset", "clk_rst": "clock_reset",
    "clk": "clock", "rst": "reset",
}


def _normalize_port_direction(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if raw in ("input", "in", "i"): return "input"
    if raw in ("output", "out", "o"): return "output"
    if raw in ("inout", "io", "bidir", "bidirectional"): return "inout"
    return raw or "input"


def _infer_legacy_port_direction(name: str, interface: dict[str, Any]) -> str:
    n = name.lower()
    proto = str(interface.get("protocol") or interface.get("type") or "").lower()
    role = str(interface.get("role") or "").lower()
    if "apb" in proto or n in {"psel", "penable", "pwrite", "paddr", "pwdata", "pstrb", "prdata", "pready", "pslverr"}:
        return "output" if n in {"prdata", "pready", "pslverr"} else "input"
    if role in {"read_master", "master"} and n.startswith(("mem_rd_", "rd_")):
        return "input" if n.endswith(("ready", "data_valid", "data")) else "output"
    if role in {"write_master", "master"} and n.startswith(("mem_wr_", "wr_")):
        return "input" if n.endswith("ready") else "output"
    output_names = {"irq", "done", "busy", "error", "csr_ready", "csr_rdata", "csr_error", "rsp_valid", "rsp_data", "req_ready"}
    return "output" if n in output_names or n.endswith(("_ready", "_rdata", "_error", "_irq")) else "input"


def _infer_legacy_port_width(name: str) -> Any:
    n = name.lower()
    if "addr" in n:
        return "ADDR_WIDTH"
    if n.endswith("strb") or "strobe" in n:
        return "DATA_WIDTH/8"
    if "data" in n or n.endswith(("wdata", "rdata")):
        return "DATA_WIDTH"
    if "length" in n or n.endswith("_len") or n == "len":
        return "LEN_WIDTH"
    return 1


def _legacy_top_interfaces_to_io_list(doc: dict[str, Any]) -> None:
    """Convert worker-authored top-level `interfaces: [{ports: [...]}]` into
    canonical `io_list.interfaces`. Some LLM drafts put interface contracts at
    the wrong root key; preserving them avoids falling back to generic req/rsp.
    """
    legacy = doc.get("interfaces")
    if not isinstance(legacy, list) or not legacy:
        return
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    interfaces = io.get("interfaces") if isinstance(io.get("interfaces"), list) else []
    interfaces = [
        item for item in interfaces
        if not (
            isinstance(item, dict)
            and str(item.get("name") or "") == "control_data"
            and "repair fallback" in str(item.get("description") or "").lower()
        )
    ]
    existing_names = {
        str(item.get("name") or "").strip().lower()
        for item in interfaces
        if isinstance(item, dict)
    }
    for item in legacy:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name or name.lower() in existing_names:
            continue
        ports: list[dict[str, Any]] = []
        for port in item.get("ports") or []:
            if isinstance(port, str):
                port_name = port.strip()
                if not port_name:
                    continue
                ports.append({
                    "name": port_name,
                    "direction": _infer_legacy_port_direction(port_name, item),
                    "width": _infer_legacy_port_width(port_name),
                    "description": f"Recovered from top-level interfaces.{name}.ports",
                })
            elif isinstance(port, dict):
                port_name = str(port.get("name") or "").strip()
                if not port_name:
                    continue
                fixed = dict(port)
                fixed["name"] = port_name
                fixed["direction"] = _normalize_port_direction(
                    fixed.get("direction") or fixed.get("dir") or _infer_legacy_port_direction(port_name, item)
                )
                fixed.setdefault("width", _infer_legacy_port_width(port_name))
                fixed.setdefault("description", f"Recovered from top-level interfaces.{name}.ports")
                ports.append(fixed)
        if not ports:
            continue
        interfaces.append({
            "name": name,
            "type": item.get("type") or item.get("protocol") or "custom",
            "role": item.get("role") or "target",
            "clock_domain": item.get("clock_domain") or _first_clock(doc)[0],
            "reset_domain": item.get("reset_domain") or _first_reset(doc)[0],
            "description": item.get("description") or f"Recovered from top-level interfaces.{name}",
            "protocol": {
                "acceptance": item.get("handshake") or "Transfer acceptance follows the declared protocol rule.",
                "stability": item.get("backpressure") or "Payload/control fields remain stable until accepted.",
                "response": item.get("response") or "Observable response timing follows cycle_model latency and ordering.",
            },
            "ports": ports,
        })
        existing_names.add(name.lower())
    if interfaces:
        io["interfaces"] = interfaces
        doc["io_list"] = io
    doc.pop("interfaces", None)


def _legacy_interface_to_io_list(doc: dict[str, Any]) -> None:
    """Convert top-level `interface.<bus>.<port>: {dir,width,desc}` legacy
    nested-dict format to canonical `io_list.interfaces[]: [{name, type,
    ports: [{name, direction, width, description}]}]`. Idempotent: removes
    the legacy key after migration so a second pass is a no-op.
    """
    legacy = doc.get("interface")
    if not isinstance(legacy, dict) or not legacy:
        return
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    interfaces = io.get("interfaces") if isinstance(io.get("interfaces"), list) else []
    existing_names = {
        str(item.get("name") or "").strip().lower()
        for item in interfaces
        if isinstance(item, dict)
    }
    for bus_name, ports_dict in legacy.items():
        if not isinstance(ports_dict, dict):
            continue
        bus_key = str(bus_name).strip()
        if not bus_key or bus_key.lower() in existing_names:
            continue
        proto = _LEGACY_PROTOCOL_HINTS.get(bus_key.lower(), "custom")
        ports: list[dict[str, Any]] = []
        for port_name, port_spec in ports_dict.items():
            if not isinstance(port_spec, dict):
                continue
            ports.append({
                "name": str(port_name).strip(),
                "direction": _normalize_port_direction(port_spec.get("dir") or port_spec.get("direction")),
                "width": port_spec.get("width", 1),
                "description": str(
                    port_spec.get("desc")
                    or port_spec.get("description")
                    or ""
                ).strip(),
            })
        if not ports:
            continue
        interfaces.append({
            "name": bus_key,
            "type": proto,
            "role": "target" if proto in ("APB4", "APB3", "AXI4-Lite", "AHB-Lite", "Wishbone") else "custom",
            "description": f"Legacy-migrated from `interface.{bus_key}` (auto-converted by repair_ssot_schema).",
            "ports": ports,
        })
        existing_names.add(bus_key.lower())
    if interfaces:
        io["interfaces"] = interfaces
        doc["io_list"] = io
    doc.pop("interface", None)


def repair(doc: dict[str, Any], state: dict[str, Any], ip: str, combinational: bool = False) -> dict[str, Any]:
    """Repair an SSOT to canonical schema.

    ``combinational=True`` activates the cycle-waived branch: the locked truth
    (req/behavioral_contracts.json) declares a purely combinational IP, so repair
    must not inject (or keep) any control FSM, function_model.state_variables,
    transaction state_updates, or cycle_model handshake/pipeline/backpressure/
    min_cycles>=1 latency. verify_ssot hard-blocks all of those for combinational
    IPs. ``combinational=False`` is the legacy stateful behavior, unchanged."""
    out = dict(doc)
    _legacy_interface_to_io_list(out)
    _legacy_top_interfaces_to_io_list(out)
    out["top_module"] = _ensure_top_module(out, state, ip)
    out["sub_modules"] = _ensure_sub_modules(out, ip)
    out["decomposition"] = _ensure_decomposition(out, ip)
    out["parameters"] = _ensure_parameters_section(out, state)
    out["io_list"] = _ensure_io_list(out)
    out["features"] = _ensure_features(out)
    out["dataflow"] = _ensure_dataflow(out)
    out["clock_reset_domains"] = _ensure_clock_reset_domains(out)
    out["cdc_requirements"] = _ensure_cdc_rdc("cdc_requirements", out)
    out["rdc_requirements"] = _ensure_cdc_rdc("rdc_requirements", out)
    out["registers"] = _ensure_registers(out)
    out["memory"] = _ensure_memory(out)
    out["interrupts"] = _ensure_interrupts(out)
    out["fsm"] = _ensure_fsm(out, combinational)
    out["function_model"] = _ensure_function_model(out, state, combinational)
    out["sub_modules"] = _ensure_submodule_behavior_ownership(out, ip)
    out["cycle_model"] = _ensure_cycle_model(out, combinational)
    _ensure_ready_constant_policy(out)
    out["rtl_contract"] = _ensure_rtl_contract(out, ip)
    _ensure_function_model_machine_rules(out, combinational)
    _ensure_rule_expr_input_map_completeness(out)
    _ensure_transaction_machine_rule_completeness(out, combinational)
    _remove_stale_repair_machine_markers(out)
    _ensure_state_update_widths(out)
    _ensure_transaction_output_summaries(out)
    out["timing"] = _ensure_timing(out)
    out["power"] = _ensure_power(out)
    out["security"] = _ensure_security(out)
    out["error_handling"] = _ensure_error_handling(out)
    out["debug_observability"] = _ensure_debug(out)
    out["integration"] = _ensure_integration(out)
    out["dft"] = _ensure_dft(out)
    out["synthesis"] = _ensure_synthesis(out, ip)
    out["pnr"] = _ensure_pnr(out)
    out["coding_rules"] = out.get("coding_rules") if isinstance(out.get("coding_rules"), dict) else {
        "verilog_style": "systemverilog_2012",
        "file_extension": ".sv",
        "parameter_header": f"rtl/{ip}_param.vh",
        "conventions": [
            "Use .sv filenames with the project SystemVerilog subset",
            "Use input logic/output logic ANSI ports and internal single-driver logic",
            "Put shared parameter declarations in rtl/<ip>_param.vh when needed; include it inside consuming modules",
            "Do not create *_pkg.sv or use typedef/enum/always_ff/always_comb/package/import/interface/modport/function/task/for/while constructs",
            "No inferred latches; every combinational branch assigns all outputs",
            "No parameterized part-selects inside procedural blocks; use helper wires/continuous assigns",
            "No ad-hoc lint suppressions without SSOT waiver and DUT-only lint evidence",
        ],
        "lint_waivers": [],
    }
    out["reuse_modules"] = out.get("reuse_modules") if isinstance(out.get("reuse_modules"), list) else []
    out["custom"] = out.get("custom") if isinstance(out.get("custom"), dict) else {
        "assumptions": [
            "Integration-owned address, routing, privilege, and clock/reset policies must be captured explicitly before signoff",
            "Repair does not imply IP-kind behavior; rtl-gen must implement only SSOT-owned function_model, cycle_model, and interface contracts",
            "Line/branch coverage is required when tool-supported; otherwise a waiver must be explicit in coverage evidence",
        ]
    }
    if "optional" in json.dumps(out, sort_keys=True, default=str).lower():
        out["custom"].setdefault("optional_behavior_policy", {
            "resolution": "non_required_optional_items_disabled_unless_ssot_marks_required_or_parameterized",
            "owner": "ssot-gen deterministic repair",
            "rule": (
                "Rows marked required:false or prose-only optional verification aids do not add RTL behavior. "
                "Any optional functional behavior must be converted by ssot-gen into required behavior or an explicit parameter/register policy before rtl-gen signoff."
            ),
        })
    out["dir_structure"] = out.get("dir_structure") if isinstance(out.get("dir_structure"), dict) else {
        "yaml_dir": "yaml/",
        "output_dirs": {"rtl": "rtl/", "list": "list/", "tb": "tb/cocotb/", "sim": "sim/", "lint": "lint/", "cov": "cov/", "doc": "doc/"},
        "generators_dir": "generators/",
    }
    filelist = out.get("filelist") if isinstance(out.get("filelist"), dict) else {}
    rtl_filelist = [item["file"] for item in out["sub_modules"] if isinstance(item, dict) and item.get("file")]
    # Always include the SSOT-declared top module file. When `top_module.name`
    # differs from `ip` (e.g. `<ip>_top`), the top is not in `sub_modules`, so
    # the filelist would otherwise miss the file that declares the top
    # module. iverilog/verilator need to see this file or elaboration fails
    # with "Unable to find the root module".
    top_module = out.get("top_module") if isinstance(out.get("top_module"), dict) else {}
    top_file = str(top_module.get("file") or "").strip()
    if top_file and top_file not in rtl_filelist:
        rtl_filelist.append(top_file)
    existing_rtl = [str(item).strip() for item in filelist.get("rtl") or [] if str(item).strip()] if isinstance(filelist.get("rtl"), list) else []
    missing_manifest = [item for item in rtl_filelist if item not in existing_rtl]
    legacy_top_missing = top_file == f"rtl/{ip}.sv" and top_file not in existing_rtl
    if (
        not isinstance(filelist.get("rtl"), list)
        or _has_tbd(filelist.get("rtl"))
        or legacy_top_missing
        or missing_manifest
    ):
        filelist["rtl"] = rtl_filelist
    filelist.setdefault("headers", [f"rtl/{ip}_param.vh"] if out.get("parameters") else [])
    filelist.setdefault("tb", [f"tb/cocotb/test_{ip}.py", "tb/cocotb/test_runner.py", "tb/cocotb/scoreboard.py"])
    filelist.setdefault("sim", ["sim/results.xml", "sim/waves.fst"])
    filelist.setdefault("coverage", ["cov/coverage.json"])
    out["filelist"] = filelist if filelist else {
        "rtl": [item["file"] for item in out["sub_modules"] if isinstance(item, dict) and item.get("file")],
        "tb": [f"tb/cocotb/test_{ip}.py", "tb/cocotb/test_runner.py", "tb/cocotb/scoreboard.py"],
        "sim": ["sim/results.xml", "sim/waves.fst"],
        "coverage": ["cov/coverage.json"],
    }
    out["test_requirements"] = _ensure_test_requirements(out)
    out["quality_gates"] = _merge_quality_gates(out, ip)
    out["traceability"] = _ensure_traceability(out)
    out["workflow_todos"] = _ensure_workflow_todos(out, ip)
    out["generation_flow"] = {
        "steps": [
            {"name": "verify_ssot", "command": f"python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py\" {ip} --root \"$ATLAS_PROJECT_ROOT\" --mode ${{ATLAS_RUN_MODE:-signoff}}", "description": "Validate SSOT structure, Preview fields, and quality gates at the selected Run Mode"},
            {"name": "handoff_fl_model", "command": f"/ssot-fl-model {ip}", "description": "Generate FunctionalModel, decomposition, and FCOV plan from SSOT"},
            {"name": "handoff_equivalence_goals", "command": f"/ssot-equiv-goals {ip}", "description": "Derive FL-vs-RTL equivalence goals before TB generation"},
            {"name": "handoff_rtl", "command": f"/ssot-rtl {ip}", "description": "Generate RTL from validated SSOT"},
            {"name": "handoff_tb", "command": f"/ssot-tb-cocotb {ip}", "description": "Generate cocotb/pyuvm verification from validated SSOT"},
            {"name": "handoff_sim_debug", "command": "/wf sim_debug", "description": "Run simulation, waveform, and coverage inspection"},
        ]
    }
    _ensure_rtl_contract_consistency(out)
    ordered = {key: out.get(key) for key in REQUIRED_ORDER}
    for key, value in out.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _validate_output_rule_cycles(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect cyclic same-cycle dependencies between output_rules per transaction."""
    issues: list[dict[str, Any]] = []
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    for tx in fm.get("transactions") or []:
        if not isinstance(tx, dict):
            continue
        rules = tx.get("output_rules") or []
        names = {
            _norm_token(str(r.get("name") or r.get("output") or r.get("port") or ""))
            for r in rules if isinstance(r, dict)
        }
        names.discard("")
        graph: dict[str, set[str]] = {}
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            name = _norm_token(str(rule.get("name") or rule.get("output") or rule.get("port") or ""))
            if not name:
                continue
            expr = str(rule.get("expr") or rule.get("expression") or rule.get("value") or "")
            tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr))
            tokens = {_norm_token(t) for t in tokens}
            graph[name] = (tokens & names) - {name}
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {n: WHITE for n in graph}
        def _dfs(node: str, stack: list[str]) -> list[str] | None:
            color[node] = GRAY
            for nxt in graph.get(node, ()):
                if color.get(nxt, WHITE) == GRAY:
                    return stack + [node, nxt]
                if color.get(nxt, WHITE) == WHITE:
                    cycle = _dfs(nxt, stack + [node])
                    if cycle:
                        return cycle
            color[node] = BLACK
            return None
        seen_cycle = False
        for start in list(graph):
            if color[start] != WHITE or seen_cycle:
                continue
            cycle = _dfs(start, [])
            if cycle:
                issues.append({
                    "id": f"SSOT_OUTPUT_DEP_CYCLE_{_norm_token(tx.get('id') or tx.get('name') or 'tx').upper()}",
                    "transaction": tx.get("id") or tx.get("name"),
                    "cycle": cycle,
                    "fix": "Break the cycle by introducing a helper expression in state_updates or splitting the output rule.",
                })
                seen_cycle = True
    return issues


def _validate_sample_conditions(doc: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    rtl_contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
    samples: list[tuple[str, Any]] = []
    if rtl_contract.get("sample_condition"):
        samples.append(("rtl_contract.sample_condition", rtl_contract.get("sample_condition")))
    for tx in fm.get("transactions") or []:
        if isinstance(tx, dict) and tx.get("sample_condition") not in (None, ""):
            samples.append((
                f"function_model.transactions.{tx.get('id') or tx.get('name')}.sample_condition",
                tx.get("sample_condition"),
            ))
    import ast as _ast
    for where, expr in samples:
        text = str(expr or "").strip()
        if not text:
            continue
        normalized = text.replace("&&", " and ").replace("||", " or ")
        normalized = re.sub(r"(?<![=!<>])!(?!=)", " not ", normalized)
        try:
            _ast.parse(normalized, mode="eval")
        except SyntaxError as exc:
            issues.append({
                "id": "SSOT_SAMPLE_CONDITION_DSL",
                "field": where,
                "expression": text,
                "error": f"{exc.msg} at column {exc.offset}",
                "fix": "Rewrite using DSL: Python comparisons (==, !=, <=, >=), and/or/not, & | ^ ~ for bitwise.",
            })
    return issues


def _validate_submodule_ownership(doc: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    ref_keys = ("implements", "function_model_refs", "cycle_model_refs", "fsm_refs", "register_refs", "dataflow_refs")
    for entry in doc.get("sub_modules") or []:
        if not isinstance(entry, dict):
            continue
        if any(entry.get(key) for key in ref_keys):
            continue
        issues.append({
            "id": f"SSOT_SUBMODULE_REFS_MISSING_{_norm_token(entry.get('name') or 'submodule').upper()}",
            "submodule": entry.get("name"),
            "fix": "Add at least one of implements / function_model_refs / cycle_model_refs / fsm_refs / register_refs / dataflow_refs.",
        })
    return issues


def _machine_rule_items(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _machine_rule_has_expr(rule: dict[str, Any]) -> bool:
    return any(str(rule.get(key) or "").strip() for key in ("expr", "expression", "value", "next_value"))


def _is_reset_transaction(tx: dict[str, Any]) -> bool:
    token = _norm_token(" ".join(str(tx.get(key) or "") for key in ("id", "name")))
    parts = {part for part in token.split("_") if part}
    return "reset" in parts or token in {"fm_reset", "reset_behavior", "reset_sequence"}


def _validate_function_model_machine_rules(doc: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    txs = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
    for idx, tx in enumerate(txs):
        if not isinstance(tx, dict):
            continue
        if _is_reset_transaction(tx):
            continue
        output_rules = _machine_rule_items(tx.get("output_rules"))
        state_updates = _machine_rule_items(tx.get("state_updates"))
        has_output_rule = any(
            str(rule.get("name") or rule.get("output") or "").strip() and _machine_rule_has_expr(rule)
            for rule in output_rules
        )
        has_state_update = any(
            str(rule.get("name") or rule.get("state") or rule.get("target") or "").strip()
            and _machine_rule_has_expr(rule)
            for rule in state_updates
        )
        if has_output_rule or has_state_update:
            continue
        tx_id = str(tx.get("id") or tx.get("name") or f"tx_{idx}").strip() or f"tx_{idx}"
        issues.append({
            "id": f"SSOT_FM_MACHINE_RULES_MISSING_{_norm_token(tx_id).upper()}",
            "field": f"function_model.transactions[{idx}]",
            "transaction": tx_id,
            "outputs": tx.get("outputs") or [],
            "side_effects": tx.get("side_effects") or [],
            "fix": (
                "Convert prose outputs/side_effects into executable output_rules or state_updates. "
                "Use output_rules with name, expr, width, and port for externally visible outputs; "
                "use state_updates with name, expr, and width for architectural state changes."
            ),
        })
    return issues


def _validate_downstream_readiness(doc: dict[str, Any], ip: str, root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(_validate_output_rule_cycles(doc))
    issues.extend(_validate_sample_conditions(doc))
    issues.extend(_validate_submodule_ownership(doc))
    issues.extend(_validate_function_model_machine_rules(doc))
    return issues


def _load_req_doc(root: Path, ip: str, name: str) -> dict[str, Any]:
    """Load a req/*.json locked-truth doc next to the SSOT, or {} if absent."""
    path = root / ip / "req" / name
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _is_combinational_locked_truth(root: Path, ip: str) -> bool:
    """True iff the locked truth says this IP is purely combinational.

    Mirrors verify_ssot._combinational_state_issues exactly: the IP is
    combinational when req/behavioral_contracts.json exists, declares at least
    one behavioral contract, AND every contract is cycle_model_waiver/
    combinational (derived from the locked decision tables by
    behavioral_contracts._cycle_model_waived). A single non-waived (sequential)
    contract, or an absent/empty behavioral_contracts.json, returns False so
    repair keeps its legacy stateful template behavior byte-for-byte.
    """
    behavioral = _load_req_doc(root, ip, "behavioral_contracts.json")
    contracts = behavioral_contract_map(behavioral)
    if not contracts:
        return False
    return all(_cycle_model_waived(contract) for contract in contracts.values())


def _obligation_to_transaction_index(doc: dict[str, Any]) -> dict[str, int]:
    """Map each obligation id to the function_model.transactions[] index that
    implements it.

    Transactions are positionally derived from features (FM{idx} <- features[idx-1]
    in ``_ensure_function_model``), so the obligation -> feature -> transaction
    chain is deterministic: obligations declared on ``features[i].obligation_refs``
    own the transaction at the same positional index. This keeps the projection
    LLM-independent.
    """
    mapping: dict[str, int] = {}
    txs = []
    fm = doc.get("function_model")
    if isinstance(fm, dict) and isinstance(fm.get("transactions"), list):
        txs = fm["transactions"]
    features = [f for f in (doc.get("features") or []) if isinstance(f, dict)]
    for idx, feature in enumerate(features):
        if idx >= len(txs):
            break
        for ob_ref in feature.get("obligation_refs") or []:
            ob_ref = str(ob_ref).strip()
            if ob_ref and ob_ref not in mapping:
                mapping[ob_ref] = idx
    return mapping


def _project_locked_behavioral_contracts(doc: dict[str, Any], root: Path, ip: str) -> list[dict[str, Any]]:
    """Project every locked behavioral contract id into the function_model.

    rtl-gen's contract-projection gate (``derive_rtl_todos._collect_contract_projection_refs``)
    requires every behavioral contract id from ``req/behavioral_contracts.json`` to
    appear literally inside a ``contract_refs`` / ``behavioral_contract_refs`` key of
    at least one ``function_model.transactions[]`` entry. Without this the gate emits
    ``LOCKED_TRUTH_CONTRACT_NOT_PROJECTED_<BC>`` and leaves the contract orphaned with
    no inferable RTL owner. This deterministic repair derives the mapping
    BC -> obligation -> feature -> transaction and appends the BC id so the contract
    is never left unprojected.
    """
    actions: list[dict[str, Any]] = []
    behavioral = _load_req_doc(root, ip, "behavioral_contracts.json")
    contracts = [c for c in (behavioral.get("contracts") or []) if isinstance(c, dict)]
    if not contracts:
        return actions

    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        return actions
    txs = fm.get("transactions")
    if not isinstance(txs, list):
        return actions

    ob_to_tx = _obligation_to_transaction_index(doc)
    for contract in contracts:
        bc_id = str(contract.get("id") or "").strip()
        if not bc_id:
            continue
        obligations = [str(o).strip() for o in (contract.get("obligations") or []) if str(o).strip()]
        # Choose the transaction that implements one of the contract's obligations.
        tx_index: int | None = None
        for ob in obligations:
            if ob in ob_to_tx:
                tx_index = ob_to_tx[ob]
                break
        # Fallback: attach to the first transaction so the contract is never
        # left unprojected. If there is no transaction at all, synthesize a
        # minimal projecting transaction from the contract.
        if tx_index is None:
            if txs:
                tx_index = 0
            else:
                txs.append({
                    "id": f"FM_{_norm_token(bc_id).upper()}",
                    "name": _norm_token(bc_id),
                    "preconditions": ["Feature trigger is asserted under legal configuration"],
                    "inputs": ["Inputs described by io_list and dataflow"],
                    "outputs": ["Architectural output matches the locked behavioral contract"],
                    "side_effects": ["Architectural state updates according to FSM/control policy"],
                })
                tx_index = len(txs) - 1
        tx = txs[tx_index]
        if not isinstance(tx, dict):
            continue
        before = list(tx.get("contract_refs") or [])
        _append_unique_ref(tx, "contract_refs", bc_id)
        _append_unique_ref(tx, "behavioral_contract_refs", bc_id)
        if tx.get("contract_refs") != before:
            actions.append({
                "behavioral_contract": bc_id,
                "transaction": str(tx.get("id") or tx.get("name") or f"transactions[{tx_index}]"),
                "via_obligations": obligations,
            })
    return actions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    ap.add_argument("--ip-root", "--ip_root", dest="ip_root", default=os.environ.get("ATLAS_IP_ROOT") or "")
    ap.add_argument(
        "--mode",
        default="",
        help="Run mode: starter, engineering, or signoff. Defaults to ATLAS_RUN_MODE or signoff.",
    )
    ap.add_argument(
        "--strict-downstream",
        action="store_true",
        help="Fail with non-zero exit when downstream readiness validators report issues.",
    )
    ns = ap.parse_args()
    run_mode = _normalize_run_mode(ns.mode or os.environ.get("ATLAS_RUN_MODE") or "signoff")
    root = _resolve_project_root(ns.root, ns.ip_root, ns.ip)
    ssot = _find_ssot(root, ns.ip)
    doc = _load_yaml(ssot)
    before_repair = dict(doc)
    strict_downstream_issues = _validate_downstream_readiness(doc, ns.ip, root) if ns.strict_downstream else []
    state = _load_state(root, ns.ip)
    combinational = _is_combinational_locked_truth(root, ns.ip)
    repaired = repair(doc, state, ns.ip, combinational)
    projection_actions = _project_locked_behavioral_contracts(repaired, root, ns.ip)
    ssot.write_text(yaml.safe_dump(repaired, sort_keys=False, width=4096, allow_unicode=False), encoding="utf-8")
    loaded = yaml.safe_load(ssot.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED_ORDER if key not in loaded]
    if missing:
        raise SystemExit("[repair_ssot_schema] missing after repair: " + ", ".join(missing))
    sidecar = _write_provenance_sidecar(root, ns.ip, ssot, before_repair, loaded, run_mode)
    print(f"[repair_ssot_schema] wrote {ssot.relative_to(root)}")
    print(f"[repair_ssot_schema] provenance: {sidecar.relative_to(root)}")
    print(f"[repair_ssot_schema] sections: {len([k for k in REQUIRED_ORDER if k in loaded])}/{len(REQUIRED_ORDER)}")
    if projection_actions:
        print(f"[repair_ssot_schema] locked behavioral contract projection: {len(projection_actions)} contract(s)")
        for action in projection_actions:
            print(f"  - {action['behavioral_contract']} -> function_model.transactions[{action['transaction']}]")
    downstream_issues = strict_downstream_issues or _validate_downstream_readiness(loaded, ns.ip, root)
    blockers_path = root / ns.ip / "req" / "ssot_downstream_blockers.json"
    blockers_path.parent.mkdir(parents=True, exist_ok=True)
    blockers_path.write_text(
        json.dumps(
            {
                "schema_version": "ssot_downstream_blockers.v1",
                "ip": ns.ip,
                "ssot": str(ssot.relative_to(root)),
                "issues": downstream_issues,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    if downstream_issues:
        print(f"[repair_ssot_schema] downstream_readiness: {len(downstream_issues)} issue(s)")
        for issue in downstream_issues:
            print(f"  - {issue.get('id')}: {issue.get('fix') or issue.get('error') or ''}")
        if ns.strict_downstream:
            return 2
    else:
        print("[repair_ssot_schema] downstream_readiness: clean")
    print(f"[repair_ssot_schema] next: python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py\" {ns.ip} --root \"$ATLAS_PROJECT_ROOT\" --mode {run_mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
