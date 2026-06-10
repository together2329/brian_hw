#!/usr/bin/env python3
"""Headless multi-IP orchestrating-system validation campaign.

For each campaign IP (truth already human-locked via orch_campaign_truth.py at
the session-scoped root), runs the headless workflow stage-by-stage with REAL
gpt-5.4 and records per-IP outcomes. Validates the 2026-06-11 ssot-gen fix
(locked behavioral DETAIL injected → real function_model, not feature_N
placeholders) across multiple IPs, plus how far the chain advances.

Usage:
  python3 scripts/orch_campaign_run.py [--root <ws>] [--ips a,b,c]
                                       [--stages ssot-gen,fl-model-gen]
Writes scripts/_campaign/results.json + prints a per-IP table.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "scripts" / "_campaign"

# Brief requirements.md per IP (the human's prose; the locked req/ pack carries
# the machine contracts). Counter/shift/pwm/gray/arbiter — simple, FL-checkable.
REQ_MD = {
    "cnt8_en_v1": "# cnt8_en_v1\n8-bit synchronous up-counter. Ports: clk, rst_n(async low), en, clr, count[7:0]. en=1 -> count+=1 (wraps 255->0); en=0 hold; clr=1 -> count=0 next edge (clr dominates en); rst_n=0 -> count=0 async.\n",
    "shift8_lr_v1": "# shift8_lr_v1\n8-bit bidirectional shift register. Ports: clk, rst_n, load, dir, sh_en, din[7:0], sin, q[7:0]. load=1 -> q=din; load=0&sh_en=1&dir=0 -> q={q[6:0],sin}; dir=1 -> q={sin,q[7:1]}; sh_en=0 hold; rst_n=0 -> q=0.\n",
    "pwm8_duty_v1": "# pwm8_duty_v1\n8-bit PWM. Ports: clk, rst_n, en, duty[7:0], pwm_out. en=1 -> free-running 8-bit phase++; pwm_out=(phase<duty). duty=0 -> always 0. en=0 -> phase hold, pwm_out=0. duty change applies at phase wrap.\n",
    "gray8_enc_v1": "# gray8_enc_v1\n8-bit binary->Gray encoder, registered. Ports: clk, rst_n, valid_in, bin_in[7:0], valid_out, gray_out[7:0]. valid_in=1@T -> gray_out=bin^(bin>>1), valid_out=1 @T+1; valid_in=0 -> valid_out=0 @T+1.\n",
    "rr_arb4_v1": "# rr_arb4_v1\n4-way round-robin arbiter. Ports: clk, rst_n, req[3:0], grant[3:0]. grant one-hot or 0; grant only where req set. Priority rotates after each grant; persistent requests -> no starvation; single req[i] -> grant[i] every cycle.\n",
}


def run_stage(root: Path, ip: str, stage: str, timeout_s: int = 600) -> dict:
    env = dict(os.environ)
    env.update({
        "ATLAS_RUN_REAL_LLM_TDD": "1",
        "ATLAS_HEADLESS_LLM_MODEL": "gpt-5.4",
        "ATLAS_REQ_APPROVED_BY": "brian",
    })
    req_path = OUT / f"{ip}_requirements.md"
    cmd = [sys.executable, "-m", "src.headless_workflow",
           "--root", str(root), "--ip", ip, "--req", str(req_path),
           "--stages", stage, "--provider", "real", "--model", "gpt-5.4",
           "--run-mode", "signoff"]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=str(REPO), env=env, capture_output=True,
                           text=True, timeout=timeout_s)
        out = p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        return {"stage": stage, "status": "timeout", "secs": round(time.time() - t0)}
    # Parse the result JSON the CLI prints.
    status = "unknown"
    try:
        start = out.rfind("{\n")
        doc = json.loads(out[start:]) if start >= 0 else {}
        stages = doc.get("stages", [])
        for s in stages:
            if s.get("stage") in (stage, stage.replace("-gen", "")):
                status = s.get("status", "unknown")
        status = doc.get("status", status)
    except Exception:
        pass
    return {"stage": stage, "status": status, "secs": round(time.time() - t0)}


def ssot_quality(root: Path, ip: str) -> dict:
    s = root / ip / "yaml" / f"{ip}.ssot.yaml"
    if not s.is_file():
        return {"ssot": "missing"}
    txt = s.read_text(encoding="utf-8", errors="ignore")
    return {
        "ssot_lines": txt.count("\n"),
        "feature_N_placeholders": txt.count("feature_1") + txt.count("feature_2")
        + txt.count("feature_3") + txt.count("feature_4"),
        "has_transactions": "transactions:" in txt,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/Users/brian/Desktop/Project/NEW_WORKSPACE/admin/default")
    ap.add_argument("--ips", default="cnt8_en_v1,shift8_lr_v1,pwm8_duty_v1,gray8_enc_v1,rr_arb4_v1")
    ap.add_argument("--stages", default="ssot-gen,fl-model-gen")
    ns = ap.parse_args()
    root = Path(ns.root)
    ips = [x.strip() for x in ns.ips.split(",") if x.strip()]
    stages = [x.strip() for x in ns.stages.split(",") if x.strip()]
    OUT.mkdir(parents=True, exist_ok=True)

    results = {}
    for ip in ips:
        OUT.joinpath(f"{ip}_requirements.md").write_text(REQ_MD.get(ip, f"# {ip}\n"), encoding="utf-8")
        ip_res = {"stages": []}
        print(f"\n=== {ip} ===", flush=True)
        for stage in stages:
            r = run_stage(root, ip, stage)
            ip_res["stages"].append(r)
            print(f"  {stage}: {r['status']} ({r['secs']}s)", flush=True)
            if stage == "ssot-gen":
                q = ssot_quality(root, ip)
                ip_res["ssot_quality"] = q
                print(f"    ssot: {q}", flush=True)
                if r["status"] not in ("pass", "passed"):
                    break  # don't run fl if ssot didn't pass
        results[ip] = ip_res
        OUT.joinpath("results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n=== CAMPAIGN SUMMARY ===", flush=True)
    for ip, r in results.items():
        line = " · ".join(f"{s['stage']}={s['status']}" for s in r["stages"])
        q = r.get("ssot_quality", {})
        print(f"{ip}: {line} | feature_N={q.get('feature_N_placeholders','?')} lines={q.get('ssot_lines','?')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
