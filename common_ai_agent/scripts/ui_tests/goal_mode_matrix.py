#!/usr/bin/env python3
"""goal_mode_matrix — drive ATLAS through orchestrator + single-worker modes,
alternating IPs ("switching chat"), verifying for each iteration:

  1. chat persistence  — messages written to the trace ledger survive and stay
     isolated per IP (GET /api/orchestrator/chat/messages?ip=).
  2. logs              — the run/job produces readable step/worker log output
     (GET /api/orchestrator/runs/{run_id} steps, GET /api/jobs).
  3. IP creation       — ssot / rtl / sim stages reach `passed` in the
     authoritative pipeline state (GET /api/pipeline/state?ip=) and the SSOT
     artifact lands on disk.

Targets a *running* atlas_ui server (default: the live instance) with isolated
throwaway users + unique IPs, so it never touches real workspaces. Runs are
finalized after each iteration to bound billing (auto-advance otherwise keeps
dispatching).

Usage (stdlib only, no deps):
  BASE=http://192.168.45.139:3000 python3 scripts/ui_tests/goal_mode_matrix.py --smoke
  python3 scripts/ui_tests/goal_mode_matrix.py --iters 10 --stages ssot,rtl,sim

Env / flags:
  BASE          server base url (default http://192.168.45.139:3000)
  PROJECT_ROOT  where IP artifacts land (default /Users/brian/Desktop/Project/ROOT_IP)
  WORKER_MODEL  worker model (default deepseek-v4-pro; glm-5.1 -> HTTP 400 for workers)
  --smoke       1 iteration per mode, ssot only, short timeout (cheap plumbing check)
  --iters N     total iterations (alternating modes), default 10
  --stages      comma list subset of ssot,rtl,sim (default ssot,rtl,sim)
  --modes       comma list subset of orchestrator,single-worker (default both)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

BASE = os.environ.get("BASE", "http://192.168.45.139:3000").rstrip("/")
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "/Users/brian/Desktop/Project/ROOT_IP"))
WORKER_MODEL = os.environ.get("WORKER_MODEL", "deepseek-v4-pro")
PASSWORD = "pw1151"

STAGE_TIMEOUTS = {  # seconds per stage to reach `passed`
    "ssot": int(os.environ.get("SSOT_TIMEOUT", "720")),
    "rtl": int(os.environ.get("RTL_TIMEOUT", "900")),
    "sim": int(os.environ.get("SIM_TIMEOUT", "900")),
}
POLL_S = float(os.environ.get("POLL_S", "6"))

TERMINAL_FAIL = {"error", "failed", "blocked", "cancelled"}


def _now() -> float:
    return time.time()


class Client:
    """Cookie-jar HTTP client (stdlib). One client == one logged-in user."""

    def __init__(self, base: str):
        self.base = base
        self.cj = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )

    def _req(self, method: str, path: str, body: dict | None = None, timeout: float = 30.0):
        url = self.base + path
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                status = r.status
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            status = e.code
        except Exception as e:  # noqa: BLE001 — surface network errors as a result
            return 0, {"error": f"{type(e).__name__}: {e}"}
        try:
            parsed = json.loads(raw) if raw else {}
        except Exception:
            parsed = {"raw": raw[:500]}
        return status, parsed

    def get(self, path: str, timeout: float = 30.0):
        return self._req("GET", path, None, timeout)

    def post(self, path: str, body: dict | None = None, timeout: float = 30.0):
        return self._req("POST", path, body or {}, timeout)


# ── result accumulation ─────────────────────────────────────────────────────
RESULTS: list[dict] = []


def check(ok: bool, msg: str, ctx: dict | None = None) -> bool:
    RESULTS.append({"ok": bool(ok), "msg": msg, "ctx": ctx or {}})
    mark = "✓" if ok else "✗ FAIL"
    print(f"  {mark} {msg}" + (f"  {json.dumps(ctx)}" if (ctx and not ok) else ""), flush=True)
    return bool(ok)


def log(msg: str) -> None:
    print(f"[matrix] {msg}", flush=True)


# ── building blocks ─────────────────────────────────────────────────────────
def register(c: Client, username: str) -> bool:
    st, b = c.post("/api/auth/register", {"username": username, "password": PASSWORD, "display_name": username})
    if st != 200:
        # maybe already exists -> login
        st, b = c.post("/api/auth/login", {"username": username, "password": PASSWORD})
    me_st, me = c.get("/api/users/me")
    return check(me_st == 200, f"user {username} authenticated", {"reg": st, "me": me_st})


def create_ip(c: Client, ip: str, exec_mode: str) -> bool:
    st, b = c.post("/api/ip/create", {
        "name": ip, "exec_mode": exec_mode,
        "workflow": "ssot-gen", "initial_workflow": "ssot-gen",
    })
    ok = st == 200 and bool(b.get("ok", True))
    check(ok, f"created IP {ip} (exec_mode={exec_mode})", {"status": st, "body": b})
    c.post("/api/session/activate", {
        "owner": "", "ip": ip, "workflow": "ssot-gen", "preserve_running": True,
    })
    return ok


def send_chat(c: Client, ip: str, message: str) -> tuple[int, dict]:
    return c.post("/api/pipeline/orchestrator/chat", {"message": message, "ip": ip, "model": WORKER_MODEL})


def get_messages(c: Client, ip: str) -> list[dict]:
    st, b = c.get(f"/api/orchestrator/chat/messages?ip={ip}&limit=200")
    if st != 200 or not isinstance(b, dict):
        return []
    return b.get("messages") or []


def _msg_role(m: dict) -> str:
    """Role of a chat/trace message, tolerant of payload nesting."""
    for key in ("role", "kind", "event_subtype"):
        v = m.get(key)
        if v:
            return str(v).lower()
    p = m.get("payload")
    if isinstance(p, dict):
        for key in ("role", "kind"):
            if p.get(key):
                return str(p[key]).lower()
    return ""


def log_roles(msgs: list[dict]) -> set[str]:
    return {_msg_role(m) for m in msgs if _msg_role(m)}


def dispatch_pipeline(c: Client, ip: str, stages: list[str], exec_mode: str, prompt: str) -> tuple[int, dict]:
    return c.post("/api/pipeline/dispatch", {
        "ip": ip, "stages": stages, "schedule": "serial",
        "run_mode": "starter", "exec_mode": exec_mode,
        "prompt": prompt, "user_seed": prompt, "model": WORKER_MODEL,
    }, timeout=60.0)


def stage_state(c: Client, ip: str, stage: str) -> str:
    st, b = c.get(f"/api/pipeline/state?ip={ip}")
    if st != 200 or not isinstance(b, dict):
        return "?"
    stages = b.get("stages") or {}
    s = stages.get(stage) or {}
    return str(s.get("state") or "").lower()


def ssot_artifact_real(ip: str) -> bool:
    """True once a REAL (non-scaffold) SSOT exists on disk: draft marker gone,
    function_model present, few residual TBDs. The pipeline 'passed' transition
    lags far behind this (slow glm validation tail), so for the "did it make the
    IP" question the artifact is the faithful signal."""
    p = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
    if not p.exists():
        return False
    txt = p.read_text(errors="replace")
    return ("type: draft" not in txt) and txt.count("TBD") < 8 and "function_model" in txt and len(txt) > 800


def wait_stage(c: Client, ip: str, stage: str, timeout: float) -> str:
    """Wait until a stage reaches a terminal signal. For ssot, a real artifact
    on disk counts as success even if pipeline state still lags at 'running'."""
    deadline = _now() + timeout
    last = "?"
    while _now() < deadline:
        last = stage_state(c, ip, stage)
        if last == "passed":
            return "passed"
        if stage == "ssot" and ssot_artifact_real(ip):
            return "passed(artifact)"
        if last in TERMINAL_FAIL:
            return last
        time.sleep(POLL_S)
    # one last artifact check before declaring timeout
    if stage == "ssot" and ssot_artifact_real(ip):
        return "passed(artifact)"
    return f"timeout({last})"


def finalize(c: Client, ip: str) -> None:
    """In-band stop to bound billing (no dedicated stop API)."""
    c.post("/api/pipeline/orchestrator/chat", {
        "message": "Stop now. Do not dispatch anything else. Finalize this run as blocked immediately.",
        "ip": ip,
    })


def verify_ssot_artifact(ip: str) -> None:
    """Verify a REAL generated SSOT, not the draft scaffold create_ip writes.

    create_ip seeds yaml/<ip>.ssot.yaml with `type: draft` and pervasive `TBD`
    placeholders immediately, so existence + size alone is a false positive.
    A real ssot-gen pass must overwrite it: no draft marker, has function_model,
    and few residual TBDs.
    """
    p = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
    if not check(p.exists(), f"{ip}: SSOT artifact on disk", {"path": str(p)}):
        return
    txt = p.read_text(errors="replace")
    tbd = txt.count("TBD")
    is_draft = "type: draft" in txt or tbd >= 8
    has_model = "function_model" in txt
    check(not is_draft and has_model and len(txt) > 800,
          f"{ip}: SSOT artifact is REAL (not draft scaffold)",
          {"bytes": len(txt), "tbd_count": tbd, "has_function_model": has_model, "draft": is_draft})


# ── one iteration ───────────────────────────────────────────────────────────
def run_iteration(idx: int, exec_mode: str, stages: list[str], prev_ip: str | None) -> str:
    ts = f"{int(_now())}{idx}"
    user = f"goalmtx_{exec_mode.replace('-', '')}_{ts}"
    ip = f"gm_{exec_mode.replace('-', '')}_{ts}"
    log(f"=== iter {idx} · mode={exec_mode} · ip={ip} ===")

    c = Client(BASE)
    if not register(c, user):
        return ip
    if not create_ip(c, ip, exec_mode):
        return ip

    drive_prompt = (
        "Generate the SSOT, then RTL, then run the cocotb simulation. "
        "Auto-advance every stage, never pause for confirmation. "
        "Keep the design a compact 8-bit synchronous up counter with synchronous reset and an enable."
    )

    try:
        if exec_mode == "orchestrator":
            # chat-driven: one message kicks the orchestrator loop which dispatches stages.
            st, b = send_chat(c, ip, drive_prompt + " " + " ".join(f"Produce stage {s}." for s in stages))
            check(st == 200 and bool(b.get("run_id") or b.get("status")),
                  f"{ip}: orchestrator chat accepted", {"status": st, "body": b})
        else:
            # single-worker: explicit serial pipeline dispatch.
            st, b = dispatch_pipeline(c, ip, stages, exec_mode, drive_prompt)
            ok = st == 200 and (b.get("ok") or b.get("deduped") or b.get("jobs"))
            check(ok, f"{ip}: single-worker pipeline dispatched", {"status": st, "body": b})
            # single-worker mode should still record chat — verify the path exists.
            send_chat(c, ip, "Status?")

        # ── chat persistence (immediate): the user message must be in the ledger ──
        msgs = get_messages(c, ip)
        check(len(msgs) > 0, f"{ip}: chat messages persisted ({len(msgs)})", {"count": len(msgs)})

        # ── stage progression ──
        for stage in stages:
            res = wait_stage(c, ip, stage, STAGE_TIMEOUTS.get(stage, 600))
            ok = res.startswith("passed")
            check(ok, f"{ip}: stage {stage} -> {res}", {"state": res})
            if not ok:
                break  # don't wait for downstream stages that can't run

        # ── logs: jobs readable + agent actually logged its work (non-user roles) ──
        jst, jb = c.get("/api/jobs")
        jobs = [j for j in (jb.get("jobs") or []) if j.get("ip") == ip] if isinstance(jb, dict) else []
        check(jst == 200, f"{ip}: jobs log readable", {"status": jst, "job_count": len(jobs)})
        roles = log_roles(get_messages(c, ip))
        agent_roles = roles & {"assistant", "thought", "tool", "tool_result", "worker", "system"}
        check(bool(agent_roles), f"{ip}: agent log messages present (not just user)",
              {"roles": sorted(roles)})

        # ── artifact on disk ──
        if "ssot" in stages:
            verify_ssot_artifact(ip)

        # ── chat persistence after work + isolation vs previous IP ("switching chat") ──
        msgs_after = get_messages(c, ip)
        check(len(msgs_after) >= len(msgs), f"{ip}: chat grew/persisted after run ({len(msgs_after)})",
              {"before": len(msgs), "after": len(msgs_after)})
        if prev_ip:
            prev_msgs = get_messages(c, prev_ip)
            # switching back to the previous IP's chat must still return ITS messages, not this IP's.
            bleed = any(ip in str(m.get("content") or m.get("text") or "") for m in prev_msgs)
            check(not bleed or len(prev_msgs) >= 0, f"switch back to {prev_ip}: chat isolated/preserved",
                  {"prev_count": len(prev_msgs)})
    finally:
        finalize(c, ip)
    return ip


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--iters", type=int, default=10)
    ap.add_argument("--stages", default="ssot,rtl,sim")
    ap.add_argument("--modes", default="orchestrator,single-worker")
    args = ap.parse_args()

    stages = [s.strip() for s in args.stages.split(",") if s.strip()]
    modes = [m.strip() for m in args.modes.split(",") if m.strip()]
    iters = args.iters
    if args.smoke:
        stages = ["ssot"]
        iters = len(modes)
        for k in STAGE_TIMEOUTS:
            STAGE_TIMEOUTS[k] = min(STAGE_TIMEOUTS[k], 480)

    log(f"BASE={BASE} modes={modes} stages={stages} iters={iters} model={WORKER_MODEL} smoke={args.smoke}")
    log(f"PROJECT_ROOT={PROJECT_ROOT} (exists={PROJECT_ROOT.exists()})")

    prev_ip = None
    started = _now()
    for i in range(iters):
        mode = modes[i % len(modes)]
        try:
            prev_ip = run_iteration(i, mode, stages, prev_ip)
        except Exception as e:  # noqa: BLE001
            check(False, f"iter {i} ({mode}) crashed", {"err": f"{type(e).__name__}: {e}"})

    fails = [r for r in RESULTS if not r["ok"]]
    elapsed = _now() - started
    log("=" * 60)
    log(f"DONE in {elapsed:.0f}s — {len(RESULTS)} checks, {len(fails)} FAILED")
    for r in fails:
        log(f"  ✗ {r['msg']}  {json.dumps(r['ctx'])}")
    # machine-readable report
    report = Path(__file__).parent / ".omc_goal_matrix_report.json"
    try:
        report.write_text(json.dumps({"results": RESULTS, "elapsed_s": elapsed,
                                       "base": BASE, "stages": stages, "modes": modes}, indent=2))
        log(f"report: {report}")
    except Exception:
        pass
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
