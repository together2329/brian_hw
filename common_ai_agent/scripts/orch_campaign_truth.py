#!/usr/bin/env python3
"""Author + lock a human-truth requirement pack for one campaign IP.

Campaign context (2026-06-10): 10-IP orchestrating-system validation. The
pipeline's dispatch gate (`truth_not_locked`) requires a locked req/ pack
before any stage runs — this script plays the human's role: it writes the
six candidate files (requirements_index / obligations / contract_refs /
structural_contracts / behavioral_contracts / evidence_plan) from a compact
spec dict and locks them via the real lock_requirement_set.py.

Usage:
    python3 scripts/orch_campaign_truth.py <ip> --root <workspace_root> \
        [--spec <spec.json>] [--approved-by brian]

Without --spec, the IP must be one of the built-in CAMPAIGN_SPECS below.
Spec shape (see CAMPAIGN_SPECS): ports[], plus per-feature entries each
becoming one requirement + obligation + contract + behavioral contract +
evidence row. Closure stages: temporal features close at sim, structural
at tb, and every IP gets a lint obligation.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOCK = REPO / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"


def _sig(name: str, dir_: str, width: int = 1) -> dict:
    return {"name": name, "dir": dir_, "width": width}


CAMPAIGN_SPECS: dict[str, dict] = {
    # Track A specimens (human-locked truth, orchestrator executes).
    "cnt8_en_v1": {
        "title": "8-bit enabled up-counter with sync clear",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("en", "input"),
                  _sig("clr", "input"), _sig("count", "output", 8)],
        "features": [
            {"key": "COUNT", "granularity": "temporal",
             "statement": "count[7:0] +1 per enabled cycle, holds when en=0, wraps 255->0; FL-vs-RTL byte-exact.",
             "when_then": [["rst_n==0", "count==0 (async)"],
                            ["en==1 && clr==0 at rising clk", "count+=1; 255 wraps to 0"],
                            ["en==0 && clr==0", "count holds"]]},
            {"key": "CLR", "granularity": "structural",
             "statement": "clr=1 forces count to 0 on next edge even when en=1 (clr dominates en).",
             "when_then": [["clr==1 at rising clk (any en)", "count==0 next cycle"]]},
        ],
    },
    "shift8_lr_v1": {
        "title": "8-bit bidirectional shift register",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("load", "input"),
                  _sig("dir", "input"), _sig("sh_en", "input"), _sig("din", "input", 8),
                  _sig("sin", "input"), _sig("q", "output", 8)],
        "features": [
            {"key": "SHIFT", "granularity": "temporal",
             "statement": "load=1 latches din; else sh_en=1 shifts q left (dir=0) or right (dir=1) inserting sin; FL-vs-RTL exact.",
             "when_then": [["load==1", "q<=din"],
                            ["load==0 && sh_en==1 && dir==0", "q<={q[6:0],sin}"],
                            ["load==0 && sh_en==1 && dir==1", "q<={sin,q[7:1]}"]]},
            {"key": "HOLD", "granularity": "structural",
             "statement": "load=0 && sh_en=0 holds q.",
             "when_then": [["load==0 && sh_en==0", "q holds"]]},
        ],
    },
    "pwm8_duty_v1": {
        "title": "8-bit PWM with programmable duty",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("en", "input"),
                  _sig("duty", "input", 8), _sig("pwm_out", "output")],
        "features": [
            {"key": "DUTY", "granularity": "temporal",
             "statement": "free-running 8-bit phase counter while en=1; pwm_out=1 iff phase<duty; duty=0 always low, duty=255 high 255/256.",
             "when_then": [["en==1", "phase+=1 each clk; pwm_out=(phase<duty)"],
                            ["duty==0", "pwm_out==0 always"],
                            ["en==0", "phase holds; pwm_out==0"]]},
            {"key": "GLITCH", "granularity": "structural",
             "statement": "duty change applies at next phase wrap (no mid-period glitch).",
             "when_then": [["duty written mid-period", "active period keeps old duty until wrap"]]},
        ],
    },
    "gray8_enc_v1": {
        "title": "8-bit binary-to-Gray encoder with registered output",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("valid_in", "input"),
                  _sig("bin_in", "input", 8), _sig("valid_out", "output"), _sig("gray_out", "output", 8)],
        "features": [
            {"key": "ENC", "granularity": "temporal",
             "statement": "gray_out = bin_in ^ (bin_in>>1) registered one cycle after valid_in; valid_out mirrors valid_in delayed 1.",
             "when_then": [["valid_in==1 at T", "gray_out==bin^(bin>>1) and valid_out==1 at T+1"],
                            ["valid_in==0 at T", "valid_out==0 at T+1; gray_out holds"]]},
        ],
    },
    "rr_arb4_v1": {
        "title": "4-way round-robin arbiter",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("req", "input", 4),
                  _sig("grant", "output", 4)],
        "features": [
            {"key": "ONEHOT", "granularity": "structural",
             "statement": "grant is one-hot or zero; grant bit only where req bit set.",
             "when_then": [["any cycle", "popcount(grant)<=1 && (grant&~req)==0"]]},
            {"key": "RR", "granularity": "temporal",
             "statement": "priority rotates: after grant[i], requester i becomes lowest priority next arbitration; no starvation with persistent requests.",
             "when_then": [["req held by all", "grants cycle 0,1,2,3,0,... (round robin)"],
                            ["single req[i]", "grant[i] every cycle"]]},
        ],
    },
    "add8_cin_v1": {
        "title": "8-bit adder with carry-in/out",
        "ports": [_sig("a", "input", 8), _sig("b", "input", 8), _sig("cin", "input"),
                  _sig("sum", "output", 8), _sig("cout", "output")],
        "features": [
            {"key": "ADD", "granularity": "structural",
             "statement": "{cout,sum} = a + b + cin (9-bit result); purely combinational.",
             "when_then": [["any a,b,cin", "{cout,sum}==a+b+cin"],
                            ["a=255,b=1,cin=0", "sum=0, cout=1"]]},
        ],
    },
    "mux4_v1": {
        "title": "4:1 8-bit multiplexer",
        "ports": [_sig("d0", "input", 8), _sig("d1", "input", 8), _sig("d2", "input", 8),
                  _sig("d3", "input", 8), _sig("sel", "input", 2), _sig("y", "output", 8)],
        "features": [
            {"key": "SEL", "granularity": "structural",
             "statement": "y = d[sel]; combinational select of one of four 8-bit inputs.",
             "when_then": [["sel=0", "y=d0"], ["sel=1", "y=d1"],
                            ["sel=2", "y=d2"], ["sel=3", "y=d3"]]},
        ],
    },
    "parity8_v1": {
        "title": "8-bit parity generator with registered output",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("valid_in", "input"),
                  _sig("data", "input", 8), _sig("valid_out", "output"), _sig("parity", "output")],
        "features": [
            {"key": "PAR", "granularity": "temporal",
             "statement": "parity = XOR of data bits (even parity), registered one cycle after valid_in; valid_out mirrors valid_in delayed 1.",
             "when_then": [["valid_in=1@T", "parity=^data, valid_out=1 @T+1"],
                            ["valid_in=0@T", "valid_out=0 @T+1"]]},
        ],
    },
    "updown8_v1": {
        "title": "8-bit up/down counter with load",
        "ports": [_sig("clk", "input"), _sig("rst_n", "input"), _sig("en", "input"),
                  _sig("up", "input"), _sig("load", "input"), _sig("din", "input", 8),
                  _sig("count", "output", 8)],
        "features": [
            {"key": "UPDOWN", "granularity": "temporal",
             "statement": "load=1 -> count=din; else en=1&up=1 -> count+=1 (wrap), en=1&up=0 -> count-=1 (wrap); en=0 hold; rst_n=0 -> count=0.",
             "when_then": [["load=1", "count=din next edge"],
                            ["en=1&up=1", "count+=1, 255->0"],
                            ["en=1&up=0", "count-=1, 0->255"],
                            ["en=0&load=0", "count holds"]]},
        ],
    },
    "onehot4_v1": {
        "title": "2-to-4 one-hot decoder with enable",
        "ports": [_sig("sel", "input", 2), _sig("en", "input"), _sig("y", "output", 4)],
        "features": [
            {"key": "DECODE", "granularity": "structural",
             "statement": "en=1 -> y is one-hot with bit sel set; en=0 -> y=0. Combinational.",
             "when_then": [["en=1,sel=k", "y == (1<<k)"], ["en=0", "y == 0"]]},
        ],
    },
}


def build_pack(ip: str, spec: dict) -> dict[str, object]:
    tag = ip.upper().replace("-", "_")
    reqs, obls, contracts, behaviorals, evidence = [], [], [], [], []
    req_id = f"REQ_{tag}_001"
    obl_refs = []
    for feat in spec["features"]:
        key = feat["key"]
        obl_id = f"OBL_{tag}_{key}_001"
        c_id = f"C_{tag}_{key}"
        obl_refs.append(obl_id)
        temporal = feat["granularity"] == "temporal"
        stages = ["rtl", "tb", "sim"] if temporal else ["rtl", "tb"]
        closure = "sim" if temporal else "tb"
        obls.append({"obligation_id": obl_id, "requirement_refs": [req_id],
                     "statement": feat["statement"], "contract_refs": [c_id],
                     "required_stages": stages, "owned_by_stage": closure,
                     "closure_stage": closure, "granularity": feat["granularity"],
                     "failure_owner": "rtl-gen"})
        stage_arts = [{"stage": "rtl", "artifact": f"rtl/{ip}.sv"},
                      {"stage": "tb", "artifact": f"tb/cocotb/test_{ip}.py"}]
        if temporal:
            stage_arts.append({"stage": "sim", "artifact": "sim/scoreboard_events.jsonl"})
        contracts.append({"contract_ref_id": c_id, "obligation_refs": [obl_id],
                          "ssot_anchor": f"function_model.transactions.{key.lower()}",
                          "stage_contracts": stage_arts})
        behaviorals.append({"id": f"BC-{tag}-{key}", "obligations": [obl_id],
                            "decision_table": [{"when": w, "then": t} for w, t in feat["when_then"]],
                            "stage_contracts": [{"stage": closure,
                                                  "check": feat["statement"][:80],
                                                  "pass_condition": "scoreboard/assert PASS per decision table",
                                                  "validator": "check_evidence_contract.py" if temporal else "check_scoreboard_events.py"}]})
        evidence.append({"evidence_id": f"E_{tag}_{key}", "contract_ref": c_id,
                         "artifact": "sim/scoreboard_events.jsonl" if temporal else f"tb/cocotb/test_{ip}.py",
                         "validator": "check_evidence_contract.py" if temporal else "check_scoreboard_events.py",
                         "pass_condition": feat["statement"]})
    # every IP: one lint obligation
    lint_obl = f"OBL_{tag}_LINT_001"
    obl_refs.append(lint_obl)
    obls.append({"obligation_id": lint_obl, "requirement_refs": [req_id],
                 "statement": "No inferred latches, single driver per register.",
                 "contract_refs": [f"C_{tag}_LINT"], "required_stages": ["lint"],
                 "owned_by_stage": "lint", "closure_stage": "lint",
                 "granularity": "structural", "failure_owner": "rtl-gen"})
    contracts.append({"contract_ref_id": f"C_{tag}_LINT", "obligation_refs": [lint_obl],
                      "ssot_anchor": "coding_rules",
                      "stage_contracts": [{"stage": "lint", "artifact": "lint/dut_lint.json"}]})
    behaviorals.append({"id": f"BC-{tag}-LINT", "obligations": [lint_obl],
                        "decision_table": [{"when": "static analysis runs", "then": "no latch, single driver"}],
                        "stage_contracts": [{"stage": "lint", "check": "lint clean",
                                              "pass_condition": "no latch / multi-driver findings",
                                              "validator": "dut_lint_report.py"}]})
    evidence.append({"evidence_id": f"E_{tag}_LINT", "contract_ref": f"C_{tag}_LINT",
                     "artifact": "lint/dut_lint.json", "validator": "dut_lint_report.py",
                     "pass_condition": "no latch / single-driver findings"})
    reqs.append({"requirement_id": req_id, "title": spec["title"],
                 "statement": " ".join(f["statement"] for f in spec["features"]),
                 "obligation_refs": obl_refs})
    structural = [{"id": f"SC_{tag}_PORTS", "obligations": obl_refs,
                   "ssot_anchor": "io_list", "signals": spec["ports"]}]
    return {
        "requirements_index.json": {"schema_version": 1, "type": "requirements_index", "ip": ip, "requirements": reqs},
        "obligations.json": {"schema_version": 1, "type": "obligations", "ip": ip, "obligations": obls},
        "contract_refs.json": {"schema_version": 1, "type": "contract_refs", "ip": ip, "contract_refs": contracts},
        "structural_contracts.json": {"schema_version": 1, "type": "structural_contracts", "ip": ip, "contracts": structural},
        "behavioral_contracts.json": {"schema_version": 1, "type": "behavioral_contracts", "ip": ip, "contracts": behaviorals},
        "evidence_plan.json": {"schema_version": 1, "type": "evidence_plan", "ip": ip, "evidence_plan": evidence},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ip")
    ap.add_argument("--root", required=True)
    ap.add_argument("--spec", default="")
    ap.add_argument("--approved-by", default="brian")
    ns = ap.parse_args()

    spec = json.loads(Path(ns.spec).read_text()) if ns.spec else CAMPAIGN_SPECS.get(ns.ip)
    if not spec:
        sys.exit(f"no spec for {ns.ip!r}; pass --spec or add to CAMPAIGN_SPECS")
    root = Path(ns.root)
    ip_dir = root / ns.ip
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    ssot = ip_dir / "yaml" / f"{ns.ip}.ssot.yaml"
    if not ssot.exists():
        ssot.write_text(f"ip: {ns.ip}\n", "utf-8")
    req_dir = ip_dir / "req"
    req_dir.mkdir(parents=True, exist_ok=True)
    for name, doc in build_pack(ns.ip, spec).items():
        (req_dir / name).write_text(json.dumps(doc, indent=1), "utf-8")
    r = subprocess.run([sys.executable, str(LOCK), ns.ip, "--root", str(root),
                        "--from-candidate", "--approved-by", ns.approved_by],
                       capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    print(out.splitlines()[-1] if out else "")
    if r.returncode != 0:
        print(out)
        return 1
    print(f"[campaign] locked truth ready: {req_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
