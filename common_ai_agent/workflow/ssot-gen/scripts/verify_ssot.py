#!/usr/bin/env python3
"""Validate SSOT YAML shape for gates and ATLAS SSOT Preview.

This is a read-mostly verifier. It does not repair YAML. It writes one
machine-readable report to <ip>/req/ssot_validation.json so ssot-gen can use
the result as a tool-call artifact.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


RUN_MODES = {"starter", "engineering", "signoff"}

CANONICAL_ORDER = [
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
        if not ip or ip_root.name == ip or (ip_root / "yaml").is_dir():
            return ip_root.parent
    return project_root

REQUIRED_BY_MODE = {
    "starter": ["top_module", "io_list", "function_model"],
    "engineering": [
        key
        for key in CANONICAL_ORDER
        if key not in {"dft", "pnr"}
    ],
    "signoff": CANONICAL_ORDER,
}

WRAPPER_KEYS = {"ssot", "sections", "spec"}
LEGACY_TOP_LEVEL_ALIASES = {
    "interface": "io_list",
    "interfaces": "io_list",
    "bus_interface": "io_list",
    "bus_interfaces": "io_list",
    "register_map": "registers",
    "clock_reset": "clock_reset_domains",
    "errors": "error_handling",
    "debug": "debug_observability",
    "dv_plan": "test_requirements",
    "verification_plan": "test_requirements",
}
LOCKED_TRUTH_TRANSACTION_PLACEHOLDERS = {f"FM{i}" for i in range(1, 5)} | {
    f"feature_{i}" for i in range(1, 5)
}
LOCKED_TRUTH_TEXT_MARKERS = (
    "Auto-injected transaction coverage/state marker",
    "replace with IP-specific",
)


def _normalize_mode(value: Any) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text == "eng":
        text = "engineering"
    if text == "sign-off":
        text = "signoff"
    return text if text in RUN_MODES else "engineering"


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {
            "none",
            "n/a",
            "na",
            "tbd",
            "todo",
            "<tbd>",
            "unknown",
            "placeholder",
        }
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _issue(severity: str, check_id: str, path: str, message: str, fix: str) -> dict[str, str]:
    return {
        "severity": severity,
        "id": check_id,
        "path": path,
        "message": message,
        "fix": fix,
    }


def _find_ssot(root: Path, ip: str) -> Path:
    bases = [root / ip]
    if root.name == ip or (root / "yaml").is_dir():
        bases.insert(0, root)
    for base in bases:
        for name in (f"{ip}.ssot.yaml", f"{ip}_ssot.yaml", f"{ip}.ssot.yml"):
            candidate = base / "yaml" / name
            if candidate.is_file():
                return candidate
    return bases[0] / "yaml" / f"{ip}.ssot.yaml"


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_yaml(path: Path) -> tuple[Any, list[dict[str, str]]]:
    if not path.is_file():
        return None, [
            _issue(
                "blocker",
                "ssot.file_missing",
                str(path),
                "SSOT YAML file does not exist.",
                "Run /to-ssot <ip> or write <ip>/yaml/<ip>.ssot.yaml first.",
            )
        ]
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), []
    except Exception as exc:
        return None, [
            _issue(
                "blocker",
                "ssot.yaml_parse_failed",
                str(path),
                f"YAML parse failed: {exc}",
                "Fix YAML syntax, then rerun verify_ssot.",
            )
        ]


def _first_line(text: str) -> str:
    for line in str(text or "").splitlines():
        if line.strip():
            return line.strip()
    return ""


def _top_level_shape_issues(doc: Any, mode: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(doc, dict):
        blockers.append(_issue(
            "blocker",
            "ssot.top_level_mapping",
            "$",
            "Top-level YAML must be one mapping.",
            "Write canonical section keys at the top level, without markdown fences or list wrapping.",
        ))
        return blockers, warnings

    keys = list(doc.keys())
    if len(keys) == 1 and str(keys[0]) in WRAPPER_KEYS and isinstance(doc.get(keys[0]), dict):
        blockers.append(_issue(
            "blocker",
            "ssot.wrapper_key",
            str(keys[0]),
            f"Top-level wrapper key '{keys[0]}' hides canonical SSOT sections from Preview.",
            "Remove the wrapper and move canonical sections to the YAML top level.",
        ))

    for key in keys:
        skey = str(key)
        if skey in WRAPPER_KEYS:
            blockers.append(_issue(
                "blocker",
                "ssot.wrapper_key",
                skey,
                f"Top-level '{skey}' is not a canonical SSOT section.",
                "Do not wrap the document in ssot:, sections:, or spec:.",
            ))
        if skey in LEGACY_TOP_LEVEL_ALIASES:
            blockers.append(_issue(
                "blocker",
                "ssot.legacy_top_level_alias",
                skey,
                f"Legacy top-level section '{skey}' is not read by the canonical gates.",
                f"Move this content under '{LEGACY_TOP_LEVEL_ALIASES[skey]}'.",
            ))

    required = REQUIRED_BY_MODE[mode]
    missing = [key for key in required if key not in doc]
    for key in missing:
        blockers.append(_issue(
            "blocker",
            "ssot.required_section_missing",
            key,
            f"Required top-level section '{key}' is missing for mode={mode}.",
            f"Add '{key}:' using workflow/ssot-gen/rules/ssot-template.yaml as the field reference.",
        ))

    canonical_seen = [key for key in keys if key in CANONICAL_ORDER]
    expected_seen = [key for key in CANONICAL_ORDER if key in canonical_seen]
    if canonical_seen != expected_seen:
        warnings.append(_issue(
            "warning",
            "ssot.canonical_order",
            "$",
            "Canonical sections are present but not in the standard order.",
            "Run repair_ssot_schema.py <ip> --mode engineering or reorder sections to match ssot-template.yaml.",
        ))

    extra = [str(key) for key in keys if str(key) not in CANONICAL_ORDER]
    for key in extra:
        warnings.append(_issue(
            "warning",
            "ssot.extra_top_level_section",
            key,
            f"Extra top-level section '{key}' is not part of the canonical schema.",
            "Move project-specific data under custom unless a downstream gate explicitly owns this section.",
        ))

    return blockers, warnings


def _interface_ports(doc: dict[str, Any]) -> list[dict[str, Any]]:
    io_raw = doc.get("io_list")
    io: dict[str, Any] = io_raw if isinstance(io_raw, dict) else {}
    ports: list[dict[str, Any]] = []
    for iface in _as_list(io.get("interfaces")):
        if not isinstance(iface, dict):
            continue
        for port in _as_list(iface.get("ports")):
            if isinstance(port, dict):
                ports.append(port)
    return ports


def _has_register_policy(regs: Any) -> bool:
    if not isinstance(regs, dict):
        return False
    if _as_list(regs.get("register_list")):
        return True
    for key in ("no_registers", "no_csr", "no_register_map"):
        if _present(regs.get(key)):
            return _present(regs.get("reason") or regs.get("policy") or regs.get("description") or regs.get("access_model"))
    return False


def _fsm_machine_count(fsm: Any) -> int:
    if not isinstance(fsm, dict):
        return 0
    if _as_list(fsm.get("states")) and _as_list(fsm.get("transitions")):
        return 1
    count = 0
    for value in fsm.values():
        if isinstance(value, dict) and _as_list(value.get("states")) and _as_list(value.get("transitions")):
            count += 1
    return count


def _has_no_fsm_policy(fsm: Any) -> bool:
    if not isinstance(fsm, dict):
        return False
    for key in ("no_fsm", "no_state_machine", "combinational_only"):
        if _present(fsm.get(key)):
            return _present(fsm.get("reason") or fsm.get("policy") or fsm.get("description"))
    return False


def _preview_issues(doc: Any, mode: str, severity: str) -> list[dict[str, str]]:
    if not isinstance(doc, dict):
        return []
    issues: list[dict[str, str]] = []

    top_raw = doc.get("top_module")
    top: dict[str, Any] = top_raw if isinstance(top_raw, dict) else {}
    if not _present(top.get("description")):
        issues.append(_issue(
            severity,
            "preview.top_module.description",
            "top_module.description",
            "SSOT Preview Brief needs a concrete top-module description.",
            "Fill top_module.description with the IP purpose from requirements or approved Q&A.",
        ))

    ports = _interface_ports(doc)
    if not ports:
        issues.append(_issue(
            severity,
            "preview.io_list.interfaces.ports",
            "io_list.interfaces[].ports[]",
            "SSOT Preview Interfaces needs interfaces with port lists.",
            "Add io_list.interfaces entries with ports containing name, direction, width, and description where known.",
        ))

    fm_raw = doc.get("function_model")
    fm: dict[str, Any] = fm_raw if isinstance(fm_raw, dict) else {}
    if not _as_list(fm.get("transactions")):
        issues.append(_issue(
            severity,
            "preview.function_model.transactions",
            "function_model.transactions[]",
            "SSOT Preview Function Model needs transactions to render behavior.",
            "Add function_model.transactions[] with id, name, preconditions, outputs, and machine-readable rules where available.",
        ))

    if mode == "starter":
        return issues

    cm_raw = doc.get("cycle_model")
    cm: dict[str, Any] = cm_raw if isinstance(cm_raw, dict) else {}
    if not _as_list(cm.get("pipeline")):
        issues.append(_issue(
            severity,
            "preview.cycle_model.pipeline",
            "cycle_model.pipeline[]",
            "SSOT Preview Cycle Model needs pipeline stages.",
            "Add cycle_model.pipeline[] entries with stage/cycle/action or record a blocking QA item.",
        ))

    scenario_sources = [
        _as_list(cm.get("scenarios")),
        _as_list(fm.get("scenarios")),
        _as_list((doc.get("test_requirements") or {}).get("scenarios") if isinstance(doc.get("test_requirements"), dict) else []),
    ]
    if not any(source for source in scenario_sources):
        issues.append(_issue(
            severity,
            "preview.scenarios",
            "cycle_model.scenarios[]|function_model.scenarios[]|test_requirements.scenarios[]",
            "SSOT Preview Scenarios has no structured scenario source.",
            "Add cycle_model.scenarios[] or test_requirements.scenarios[] so Preview and TB handoff share the same scenario anchors.",
        ))

    regs = doc.get("registers")
    if not _has_register_policy(regs):
        issues.append(_issue(
            severity,
            "preview.registers",
            "registers.register_list[]",
            "SSOT Preview Register Map needs registers or an explicit no-register policy.",
            "Add registers.register_list[] or registers.no_registers/no_csr with reason/policy/description.",
        ))

    fsm = doc.get("fsm")
    if _fsm_machine_count(fsm) <= 0 and not _has_no_fsm_policy(fsm):
        issues.append(_issue(
            severity,
            "preview.fsm",
            "fsm.states/transitions",
            "SSOT Preview FSM needs states/transitions or an explicit no-FSM policy.",
            "Add fsm.<machine>.states and transitions, or fsm.no_fsm with reason/policy.",
        ))

    tr_raw = doc.get("test_requirements")
    tr: dict[str, Any] = tr_raw if isinstance(tr_raw, dict) else {}
    if not _as_list(tr.get("scenarios")):
        issues.append(_issue(
            severity,
            "preview.test_requirements.scenarios",
            "test_requirements.scenarios[]",
            "SSOT Preview and downstream TB need test_requirements.scenarios.",
            "Add test_requirements.scenarios[] with stimulus, expected, checker, and coverage.",
        ))

    return issues


def _locked_truth_placeholder_issues(doc: Any, approval_manifest_exists: bool) -> list[dict[str, str]]:
    if not approval_manifest_exists or not isinstance(doc, dict):
        return []

    hits: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add_hit(path: str, value: str) -> None:
        key = (path, value)
        if key not in seen:
            seen.add(key)
            hits.append(key)

    def walk(value: Any, path: str, parent_key: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}" if path else key_text
                walk(child, child_path, key_text)
            return
        if isinstance(value, list):
            for idx, child in enumerate(value):
                walk(child, f"{path}[{idx}]", parent_key)
            return
        if not isinstance(value, str):
            return

        text = value.strip()
        if not text:
            return
        if any(marker in text for marker in LOCKED_TRUTH_TEXT_MARKERS):
            add_hit(path, text)
        if text.startswith("EXEC_FEATURE_"):
            add_hit(path, text)
        if (
            parent_key in {"id", "name"}
            and "function_model.transactions" in path
            and text in LOCKED_TRUTH_TRANSACTION_PLACEHOLDERS
        ):
            add_hit(path, text)

    walk(doc, "")
    if not hits:
        return []

    summary = ", ".join(f"{path}={value}" for path, value in hits[:6])
    if len(hits) > 6:
        summary += f", +{len(hits) - 6} more"
    return [
        _issue(
            "blocker",
            "ssot.locked_truth_placeholders",
            "function_model/fsm/test_requirements",
            (
                "req/approval_manifest.json exists, but generic repair placeholders remain in the SSOT: "
                f"{summary}."
            ),
            (
                "Owner: ssot-gen. Replace generic repair placeholders with locked requirement-specific "
                "function_model/fsm/test_requirements content before signoff."
            ),
        )
    ]


def _run_check_ssot(root: Path, ip: str, mode: str) -> dict[str, Any]:
    checker = Path(__file__).with_name("check_ssot_disk.sh")
    bash = shutil.which("bash")
    if not checker.is_file() or not bash:
        reason = []
        if not checker.is_file():
            reason.append(f"checker not found: {checker}")
        if not bash:
            reason.append("bash not found on PATH")
        return _run_native_disk_check(root, ip, mode, "; ".join(reason))
    checker_root = root
    if not (checker_root / ip).is_dir() and root.name == ip and (root / "yaml").is_dir():
        checker_root = root.parent
    if not (checker_root / ip).is_dir():
        return _run_native_disk_check(
            root,
            ip,
            mode,
            f"check_ssot_disk.sh expects <root>/<ip>; got root={root}",
        )
    proc = subprocess.run(
        [bash, str(checker), ip, "--root", str(checker_root), "--mode", mode],
        cwd=str(checker_root),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=90,
    )
    if proc.returncode != 0:
        try:
            checker_py_err = Path("/tmp/_ssot_yaml.err").read_text(encoding="utf-8", errors="replace")
        except Exception:
            checker_py_err = ""
        if "ModuleNotFoundError" in checker_py_err and "yaml" in checker_py_err:
            return _run_native_disk_check(
                root,
                ip,
                mode,
                "check_ssot_disk.sh helper python cannot import PyYAML",
            )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _run_native_disk_check(root: Path, ip: str, mode: str, reason: str) -> dict[str, Any]:
    """Small Python fallback for environments that cannot launch bash.

    The full shell checker remains authoritative when available. This fallback
    keeps ATLAS UI validation useful on Windows or packaged installs where
    `bash check_ssot_disk.sh` cannot be launched, while the main verifier still
    performs canonical-shape and Preview-readable checks above.
    """
    ssot = _find_ssot(root, ip)
    min_yaml = {"starter": 120, "engineering": 3000, "signoff": 4000}[mode]
    min_sections = {"starter": 3, "engineering": 30, "signoff": 34}[mode]
    if not ssot.is_file():
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"[verify_ssot] native disk check: no SSOT YAML at {_rel(ssot, root)} ({reason})",
            "fallback": "python",
        }
    size = ssot.stat().st_size
    if size < min_yaml:
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"[verify_ssot] native disk check: {_rel(ssot, root)} = {size}B (need >= {min_yaml}) ({reason})",
            "fallback": "python",
        }
    doc, blockers = _load_yaml(ssot)
    if blockers:
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"[verify_ssot] native disk check: YAML parse failed ({reason})",
            "fallback": "python",
        }
    if not isinstance(doc, dict):
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"[verify_ssot] native disk check: top-level YAML must be a mapping ({reason})",
            "fallback": "python",
        }
    hits = sum(1 for key in REQUIRED_BY_MODE[mode] if key in doc)
    if hits < min_sections:
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": f"[verify_ssot] native disk check: {_rel(ssot, root)} has {hits} required top-level section keys (need >= {min_sections}) ({reason})",
            "fallback": "python",
        }
    return {
        "ok": True,
        "returncode": 0,
        "stdout": f"[verify_ssot] native disk check PASS: {_rel(ssot, root)} ({reason})",
        "stderr": "",
        "fallback": "python",
    }


def _render(report: dict[str, Any]) -> str:
    status = "PASS" if report.get("ok") else "FAIL"
    lines = [
        f"[verify_ssot] {status}: {report.get('ssot')} mode={report.get('mode')}",
        f"blockers: {len(report.get('blockers') or [])}",
        f"warnings: {len(report.get('warnings') or [])}",
    ]
    if report.get("report"):
        lines.append(f"report: {report['report']}")
    for title, items in (("blockers", report.get("blockers") or []), ("warnings", report.get("warnings") or [])):
        if not items:
            continue
        lines.append("")
        lines.append(f"{title}:")
        for item in items[:20]:
            lines.append(f"  - {item.get('path')}: {item.get('message')}")
            if item.get("fix"):
                lines.append(f"    fix: {item['fix']}")
        if len(items) > 20:
            lines.append(f"  ... {len(items) - 20} more")
    check = report.get("check_ssot_disk") or {}
    if check:
        lines.append("")
        lines.append(f"check_ssot_disk exit: {check.get('returncode')}")
        first = _first_line((check.get("stdout") or "") + "\n" + (check.get("stderr") or ""))
        if first:
            lines.append(first)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip", nargs="?", default="")
    ap.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    ap.add_argument("--ip-root", "--ip_root", dest="ip_root", default=os.environ.get("ATLAS_IP_ROOT") or "")
    ap.add_argument(
        "--mode",
        default="",
        help="starter, engineering, or signoff. Defaults to ATLAS_RUN_MODE or engineering.",
    )
    ap.add_argument(
        "--preview",
        choices=("strict", "warn", "off"),
        default="strict",
        help="Whether missing Preview-readable fields are blockers, warnings, or ignored.",
    )
    ap.add_argument("--skip-disk-check", action="store_true", help="Skip check_ssot_disk.sh.")
    ap.add_argument("--json", action="store_true", help="Emit only JSON.")
    ns = ap.parse_args()

    ip = (ns.ip or os.environ.get("IP_NAME") or os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
    root = _resolve_project_root(ns.root, ns.ip_root, ip)
    mode = _normalize_mode(ns.mode or os.environ.get("ATLAS_RUN_MODE") or "engineering")
    ssot = _find_ssot(root, ip) if ip else root / "<missing-ip>" / "yaml" / "<missing-ip>.ssot.yaml"

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not ip:
        blockers.append(_issue(
            "blocker",
            "ssot.ip_missing",
            "ip",
            "IP name is required.",
            "Run verify_ssot with an IP argument or set ATLAS_ACTIVE_IP.",
        ))
        doc = None
    else:
        doc, load_blockers = _load_yaml(ssot)
        blockers.extend(load_blockers)
        if not load_blockers:
            shape_blockers, shape_warnings = _top_level_shape_issues(doc, mode)
            blockers.extend(shape_blockers)
            warnings.extend(shape_warnings)
            manifest_path = root / ip / "req" / "approval_manifest.json"
            blockers.extend(_locked_truth_placeholder_issues(doc, manifest_path.is_file()))
            if ns.preview != "off":
                severity = "blocker" if ns.preview == "strict" else "warning"
                target = blockers if severity == "blocker" else warnings
                target.extend(_preview_issues(doc, mode, severity))

    check_result: dict[str, Any] = {}
    if ip and not ns.skip_disk_check:
        try:
            check_result = _run_check_ssot(root, ip, mode)
            if not check_result.get("ok"):
                blockers.append(_issue(
                    "blocker",
                    "check_ssot_disk.failed",
                    _rel(ssot, root),
                    f"check_ssot_disk.sh failed with exit {check_result.get('returncode')}.",
                    _first_line((check_result.get("stdout") or "") + "\n" + (check_result.get("stderr") or ""))
                    or "Run the same check command and repair the reported YAML contract failure.",
                ))
        except Exception as exc:
            check_result = {"ok": False, "returncode": 1, "stdout": "", "stderr": str(exc)}
            blockers.append(_issue(
                "blocker",
                "check_ssot_disk.error",
                _rel(ssot, root),
                f"check_ssot_disk.sh could not run: {exc}",
                "Fix the verifier runtime issue, then rerun verify_ssot.",
            ))

    report_path = root / ip / "req" / "ssot_validation.json" if ip else None
    report = {
        "schema_version": "ssot_validation.v2",
        "ip": ip,
        "mode": mode,
        "ssot": _rel(ssot, root),
        "ok": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "check_ssot_disk": check_result,
        "preview_contract": ns.preview,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = _rel(report_path, root)

    if ns.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_render(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
