#!/usr/bin/env python3
"""Refresh RTL filelist/provenance after SSOT metadata-only gate updates.

This script does not bless manual RTL. It only refreshes an existing
common_ai_agent rtl-gen provenance record when the expected RTL files already
exist and were already listed by that provenance. Its main use is after human
approval of SSOT target_scale or connection contracts changes rtl_todo_plan.json
without changing the RTL source files.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import yaml

SOURCE_ROOT = Path(__file__).resolve().parents[3]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from src.headless_workflow import _stable_json_sha256  # noqa: E402


ALLOWED_SURFACES = {"atlas_ui", "textual_ui", "headless_common_engine"}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[refresh_rtl_provenance] invalid JSON {path}: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _top_name(doc: dict[str, Any], ip: str) -> str:
    top = doc.get("top_module")
    if isinstance(top, dict):
        name = str(top.get("name") or "").strip()
        if name:
            return name
    if isinstance(top, str) and top.strip():
        return top.strip()
    return ip


def _manifest_submodules(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = doc.get("sub_modules")
    return [item for item in rows if isinstance(item, dict)] if isinstance(rows, list) else []


def _skip_rtl_manifest_row(row: dict[str, Any]) -> bool:
    ownership = str(row.get("ownership") or "manifest").strip().lower()
    if ownership in {"child_ssot", "conceptual", "verification", "coverage"}:
        return True
    if row.get("ssot") or row.get("rtl_emit") is False:
        return True
    rel = str(row.get("file") or "").strip()
    return rel.endswith((".svh", ".vh"))


def _expected_rtl_files(doc: dict[str, Any], top: str) -> list[str]:
    files: list[str] = []
    for row in _manifest_submodules(doc):
        if _skip_rtl_manifest_row(row):
            continue
        rel = str(row.get("file") or "").strip()
        if rel:
            files.append(rel)
    filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
    for rel in filelist.get("rtl") or []:
        if isinstance(rel, str) and rel.strip():
            files.append(rel.strip())
    if not files:
        files.append(f"rtl/{top}.sv")
    seen: set[str] = set()
    out: list[str] = []
    for rel in files:
        if rel and rel not in seen:
            seen.add(rel)
            out.append(rel)
    return out


def _validate_prior_common_agent(prior: dict[str, Any], expected: list[str]) -> None:
    issues: list[str] = []
    if prior.get("type") != "rtl_authoring_provenance":
        issues.append("type must be rtl_authoring_provenance")
    if prior.get("agent") != "common_ai_agent":
        issues.append("agent must be common_ai_agent")
    if prior.get("workflow") != "rtl-gen":
        issues.append("workflow must be rtl-gen")
    if prior.get("surface") not in ALLOWED_SURFACES:
        issues.append("surface must be atlas_ui, textual_ui, or headless_common_engine")
    rtl_files = prior.get("rtl_files") if isinstance(prior.get("rtl_files"), list) else []
    missing = [rel for rel in expected if rel not in rtl_files]
    if missing:
        issues.append("existing provenance does not list expected RTL files: " + ", ".join(missing[:12]))
    if issues:
        raise SystemExit("[refresh_rtl_provenance] refusing to refresh non-authoritative provenance: " + "; ".join(issues))


def refresh(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot_path.is_file():
        raise SystemExit(f"[refresh_rtl_provenance] missing SSOT: {ssot_path}")
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[refresh_rtl_provenance] SSOT top-level must be mapping")
    top = _top_name(doc, ip)
    expected = _expected_rtl_files(doc, top)
    missing = [rel for rel in expected if not (ip_dir / rel).is_file()]
    if missing:
        raise SystemExit("[refresh_rtl_provenance] missing expected RTL files: " + ", ".join(missing[:12]))

    provenance_path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
    prior = _read_json(provenance_path)
    if not prior:
        raise SystemExit("[refresh_rtl_provenance] missing existing rtl/rtl_authoring_provenance.json")
    _validate_prior_common_agent(prior, expected)

    filelist = ip_dir / "list" / f"{ip}.f"
    filelist.parent.mkdir(parents=True, exist_ok=True)
    filelist.write_text("".join(f"{rel}\n" for rel in expected), encoding="utf-8")

    todo_hash = _stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
    payload = {
        **prior,
        "schema_version": 1,
        "type": "rtl_authoring_provenance",
        "agent": "common_ai_agent",
        "workflow": "rtl-gen",
        "surface": prior.get("surface") if prior.get("surface") in ALLOWED_SURFACES else "headless_common_engine",
        "todo_plan_sha256": todo_hash,
        "rtl_files": expected,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "refresh_reason": "SSOT metadata gate update refreshed rtl_todo_plan hash without changing RTL files.",
    }
    provenance_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ip": ip,
        "top": top,
        "rtl_files": expected,
        "todo_plan_sha256": todo_hash,
        "provenance": str(provenance_path.relative_to(root)),
        "filelist": str(filelist.relative_to(root)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    result = refresh(ns.ip, Path(ns.root).resolve())
    print(f"[refresh_rtl_provenance] refreshed {result['provenance']}")
    print(f"[refresh_rtl_provenance] wrote {result['filelist']}")
    print(f"[refresh_rtl_provenance] rtl_files={len(result['rtl_files'])} todo_plan_sha256={result['todo_plan_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
