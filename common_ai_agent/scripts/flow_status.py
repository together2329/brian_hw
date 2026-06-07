#!/usr/bin/env python3
"""flow_status.py — one-line-per-stage rollup of the IP generation flow, over the
CURRENT repo structure (no truth-graph rewrite needed).

It is READ-ONLY: it only reads the evidence the existing stages already emit
(`*/`*_todo_plan.json`, `req/*.json`, `sim/mismatch_classification.json`,
`signoff/ip_signoff.json`, ...) and renders the operational flow

  draft/finalize/lock-req -> to-ssot -> gen-rtl -> gen-tb -> sim
                          -> sim-debug -> coverage -> signoff

as the user designed it:
  STAGE | STATUS | one representative TODO (next open required task) | owner route on fail.

This is the operational spine of the loop: a stage is PASS by its OWN gate evidence
(not self-reported prose), the representative TODO is the next open required task in
that stage's internal ledger (the "1 TODO per stage" the UI would surface), and a
non-pass stage prints where to route the repair (the owner workflow / command).

Exit 0 iff every required stage is pass. `--json` emits the same rollup as data so a
UI or the orchestrator can consume the identical verdict.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _rep_todo(tasks: Any) -> tuple[str, str] | None:
    """First open, required task = the stage's representative TODO."""
    if not isinstance(tasks, list):
        return None
    for t in tasks:
        if not isinstance(t, dict):
            continue
        approved = str(t.get("approval_state") or "") == "approved"
        comp = str((t.get("todo_completion") or {}).get("status") or "")
        done = approved or comp in {"pass", "done", "complete", "closed"}
        required = t.get("required", True)
        if required and not done:
            text = str(t.get("content") or t.get("detail") or t.get("criteria") or "").strip()
            return str(t.get("id") or "?"), text[:90]
    return None


@dataclass
class StageResult:
    name: str
    command: str
    status: str          # pass | fail | blocked | absent
    detail: str
    todo: str            # representative open TODO or "(all required closed)"
    route: str           # owner route when not pass


@dataclass
class Stage:
    name: str
    command: str
    owner_route: str
    resolve: Callable[[Path], tuple[str, str, str | None]]
    # resolve -> (status, detail, representative_todo_or_None)


# --------------------------------------------------------------------------- #
# Per-stage resolvers (read existing evidence only)                            #
# --------------------------------------------------------------------------- #
def _resolve_req(ip_dir: Path) -> tuple[str, str, str | None]:
    manifest = _read_json(ip_dir / "req" / "approval_manifest.json")
    bundle = [p for p in ("requirements_index.json", "obligations.json", "contract_refs.json",
                          "evidence_plan.json", "approval_manifest.json")
              if (ip_dir / "req" / p).is_file()]
    if not bundle:
        return "absent", "no req/*.json locked-truth bundle", "[lock-req] author + lock requirement set"
    locked = bool(manifest) and str(manifest.get("status") or "").lower() in {"requirements_locked", "locked", "approved"}
    status = "pass" if locked else "blocked"
    detail = f"bundle={len(bundle)} files; locked={locked}"
    todo = None if locked else "[finalize-req/lock-req] approve + lock the requirement set"
    return status, detail, todo


def _resolve_to_ssot(ip_dir: Path) -> tuple[str, str, str | None]:
    yamls = list((ip_dir / "yaml").glob("*.ssot.yaml")) if (ip_dir / "yaml").is_dir() else []
    if not yamls:
        return "absent", "no yaml/*.ssot.yaml projection", "[to-ssot] project locked truth to SSOT"
    val = _read_json(ip_dir / "req" / "ssot_validation.json")
    blockers = val.get("blockers") if isinstance(val, dict) else None
    nb = len(blockers) if isinstance(blockers, list) else 0
    status = "pass" if nb == 0 else "fail"
    todo = None if nb == 0 else f"[to-ssot] resolve {nb} SSOT validation blocker(s)"
    return status, f"ssot present; blockers={nb}", todo


def _ledger_resolver(rel: str) -> Callable[[Path], tuple[str, str, str | None]]:
    def _r(ip_dir: Path) -> tuple[str, str, str | None]:
        doc = _read_json(ip_dir / rel)
        if not doc:
            return "absent", f"no {rel}", f"generate {rel}"
        gate = doc.get("gate") if isinstance(doc.get("gate"), dict) else {}
        status = str(gate.get("status") or doc.get("status") or "absent")
        rep = _rep_todo(doc.get("tasks"))
        nopen = gate.get("open_required_todos")
        detail = f"gate={status}" + (f" open_required={nopen}" if nopen is not None else "")
        todo = f"{rep[0]}: {rep[1]}" if rep else None
        return ("pass" if status == "pass" else status), detail, todo
    return _r


def _resolve_sim_debug(ip_dir: Path) -> tuple[str, str, str | None]:
    doc = _read_json(ip_dir / "sim" / "mismatch_classification.json")
    if not doc:
        return "absent", "no mismatch_classification.json", None
    cls = doc.get("classifications") if isinstance(doc.get("classifications"), list) else []
    status = str(doc.get("status") or ("pass" if not cls else "fail"))
    if not cls:
        return ("pass" if status == "pass" else status), "0 mismatches classified", None
    owners = {}
    for c in cls:
        if isinstance(c, dict):
            owners[str(c.get("owner") or "?")] = owners.get(str(c.get("owner") or "?"), 0) + 1
    first = cls[0] if isinstance(cls[0], dict) else {}
    todo = f"{first.get('goal_id','?')} -> owner={first.get('owner','?')}: {str(first.get('reason') or '')[:60]}"
    return "fail", f"{len(cls)} mismatch(es); owners={owners}", todo


def _resolve_signoff(ip_dir: Path) -> tuple[str, str, str | None]:
    doc = _read_json(ip_dir / "signoff" / "ip_signoff.json")
    if not doc:
        return "absent", "no signoff/ip_signoff.json", "[signoff] run check_ip_signoff.py"
    status = str(doc.get("status") or "absent")
    summ = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
    bad = [g.get("name") for g in (doc.get("gates") or []) if isinstance(g, dict) and g.get("status") != "pass"]
    detail = f"gates {summ.get('passed')}/{summ.get('total_gates')} pass; failed={summ.get('failed')} blocked={summ.get('blocked')}"
    todo = None if status == "pass" else f"[signoff] fix gate(s): {', '.join(str(b) for b in bad[:4])}"
    return ("pass" if status == "pass" else status), detail, todo


STAGES: list[Stage] = [
    Stage("req (draft/finalize/lock)", "/lock-req", "/draft-req → /lock-req", _resolve_req),
    Stage("to-ssot", "/to-ssot", "/to-ssot (or req repair)", _resolve_to_ssot),
    Stage("gen-rtl", "/ssot-rtl", "/gen-rtl", _ledger_resolver("rtl/rtl_todo_plan.json")),
    Stage("gen-tb", "/ssot-tb", "/gen-tb", _ledger_resolver("tb/tb_todo_plan.json")),
    Stage("sim", "/sim", "/sim", _ledger_resolver("sim/sim_todo_plan.json")),
    Stage("sim-debug", "/sim-debug", "owner per classification (see route)", _resolve_sim_debug),
    Stage("coverage", "/coverage", "/coverage → /gen-tb", _ledger_resolver("cov/coverage_todo_plan.json")),
    Stage("signoff", "/ip-signoff", "/ip-signoff (owner per failing gate)", _resolve_signoff),
]

_ICON = {"pass": "✓", "fail": "✗", "blocked": "▣", "absent": "·"}


def run(ip: str, root: Path) -> tuple[list[StageResult], str]:
    ip_dir = (root / ip).resolve()
    results: list[StageResult] = []
    for st in STAGES:
        status, detail, todo = st.resolve(ip_dir)
        route = "" if status == "pass" else st.owner_route
        results.append(StageResult(
            name=st.name, command=st.command, status=status, detail=detail,
            todo=todo or "(all required closed)", route=route,
        ))
    required = [r for r in results if r.status not in {"pass", "absent"}]
    overall = "pass" if all(r.status == "pass" for r in results) else (
        "fail" if any(r.status == "fail" for r in results) else "blocked")
    return results, overall


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--json", action="store_true", help="emit the rollup as JSON (UI/orchestrator consumable)")
    args = ap.parse_args()

    results, overall = run(args.ip, Path(args.root))

    if args.json:
        print(json.dumps({
            "type": "flow_status", "ip": args.ip, "overall": overall,
            "stages": [vars(r) for r in results],
        }, indent=2))
        return 0 if overall == "pass" else 1

    print(f"\nFlow status — {args.ip}   overall={overall.upper()}\n")
    print(f"  {'STAGE':<26} {'ST':<3} {'DETAIL':<42} TODO / ROUTE")
    print("  " + "-" * 104)
    for r in results:
        line = f"  {r.name:<26} {_ICON.get(r.status,'?'):<3} {r.detail[:42]:<42} "
        if r.status == "pass":
            line += "—"
        else:
            line += r.todo
            if r.route:
                line += f"   → {r.route}"
        print(line)
    print()
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
