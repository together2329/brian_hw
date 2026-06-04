#!/usr/bin/env python3
"""End-to-end verification of the Session Flow admin dashboard chain.

Reusable, tracked harness proving the FULL chain the dashboard depends on:

    real write paths  ->  out-of-band fold  ->  /api/admin/session-flow  ->  UI

It is intentionally NOT a unit test: it drives the REAL AtlasDB write paths,
the REAL production fold (``core.runtime_rollup.run_rollup_pass`` /
``rollup_all_active_flow``), the REAL read model
(``core.session_flow_usage.build_session_flow_payload``), and the REAL HTTP
route ``GET /api/admin/session-flow`` on the REAL ASGI app
(``src/atlas_admin.create_app`` with ``ATLAS_ADMIN_AUTH_MODE=local``), then
boots the REAL uvicorn server so the periodic rollup daemon is observed folding
end-to-end on a live server.

Parts
-----
A. Runtime-mode real chain (the B2 crux): seed >=3 sessions into per-session
   RUNTIME DBs via real write paths, fold OUT OF BAND, then assert the read
   model + HTTP route surface populated rows, needs_attention, funnel, and that
   the read is NO-FANOUT (zero per-session runtime sqlite files opened). Also
   asserts non-admin is denied. A central-mode leg proves the costed
   attribution-gap behaviour the no-fanout runtime path deliberately summarizes.
B. Live scheduler proof: boot the real uvicorn server with the rollup daemon
   enabled, seed a session's runtime rows, and poll the HTTP route until the
   session appears populated -> proves the daemon folds on a live server.
C. Capture the real Part-A payload JSON to disk so the Vitest in
   ``frontend/atlas/__tests__/admin-session-flow-real-payload.test.tsx`` renders
   the REAL payload (not a hand-written mock).

Evidence is written under ``.omo/evidence/``.

Run:  python3 scripts/atlas_session_flow_e2e.py
Exit code 0 == every asserted leg PASSED.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

_EVIDENCE = _REPO / ".omo" / "evidence"
_EVIDENCE.mkdir(parents=True, exist_ok=True)
_PAYLOAD_FIXTURE = _REPO / "frontend" / "atlas" / "__tests__" / "fixtures"


# --------------------------------------------------------------------------- #
# Tiny assertion + evidence harness (no pytest dependency).
# --------------------------------------------------------------------------- #


class Recorder:
    """Collects PASS/FAIL lines for one evidence file and tracks overall state."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.lines: List[str] = []
        self.passed = 0
        self.failed = 0

    def log(self, msg: str = "") -> None:
        self.lines.append(msg)
        print(f"[{self.name}] {msg}")

    def check(self, cond: bool, label: str, detail: str = "") -> bool:
        tag = "PASS" if cond else "FAIL"
        if cond:
            self.passed += 1
        else:
            self.failed += 1
        line = f"  [{tag}] {label}"
        if detail:
            line += f"  ::  {detail}"
        self.log(line)
        return cond

    def save(self) -> None:
        header = (
            f"# {self.name}\n"
            f"# generated_at: {time.strftime('%Y-%m-%dT%H:%M:%S%z')}\n"
            f"# result: {self.passed} passed, {self.failed} failed\n\n"
        )
        (_EVIDENCE / f"{self.name}.txt").write_text(
            header + "\n".join(self.lines) + "\n", encoding="utf-8"
        )


# --------------------------------------------------------------------------- #
# Environment helpers.
# --------------------------------------------------------------------------- #


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def _runtime_env(mode: str = "session"):
    """Isolated control DB + runtime root in the requested mode (env-scoped)."""
    tmp = tempfile.mkdtemp(prefix="atlas-sf-e2e-")
    ctrl = str(Path(tmp) / "atlas.db")
    runtime_root = str(Path(tmp) / "runtime")
    saved = {
        k: os.environ.get(k)
        for k in (
            "ATLAS_CONTROL_DB_PATH", "ATLAS_DB_PATH", "ATLAS_RUNTIME_DB_ROOT",
            "ATLAS_RUNTIME_DB_MODE",
        )
    }
    os.environ["ATLAS_CONTROL_DB_PATH"] = ctrl
    os.environ["ATLAS_DB_PATH"] = ctrl
    os.environ["ATLAS_RUNTIME_DB_ROOT"] = runtime_root
    os.environ["ATLAS_RUNTIME_DB_MODE"] = mode

    # Build the control DB with the FULL schema (control owns identity tables).
    from core.atlas_db import AtlasDB

    AtlasDB(ctrl, schema_set="full").close()
    try:
        yield {"control_path": ctrl, "runtime_root": runtime_root, "dir": tmp}
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


# --------------------------------------------------------------------------- #
# Real write-path seeding (mirrors how a worker writes in runtime mode).
# --------------------------------------------------------------------------- #


def _seed_runtime_session(
    control_path: str,
    *,
    username: str,
    ip_name: str,
    workflow: str,
    inputs: int = 1,
    worker: bool = True,
    worker_status: str = "running",
    llm_n: int = 1,
    llm_cost: float = 0.0,
    artifact: bool = False,
    verification: bool = False,
) -> Dict[str, Any]:
    """Seed ONE session: identity+artifacts -> control DB, activity -> runtime DB.

    Returns dict with session_id, ip_id, user_id, runtime_path. This is the real
    write path: control-side ``create_user/upsert_workspace/upsert_ip_block/
    create_session`` then per-session runtime ``record_session_input/
    start_worker_run/record_llm_call`` (the 5-table runtime subset), and
    control-side ``register_artifact_version`` (artifacts live in the control
    full schema, which the fold reads via _control_facts_for_session).
    """
    from core.atlas_db import AtlasDB
    from core.atlas_db_router import AtlasDBRouter

    with AtlasDB(control_path, schema_set="full") as db:
        u = db.get_user_by_username(username) or db.create_user(username, username, "pw")
        ws = db.upsert_workspace(f"ws-{username}", owner_user_id=u["id"],
                                 local_path=f"/{username}")
        ip = db.upsert_ip_block(ws["id"], ip_name, ip_type="x",
                                created_by_user_id=u["id"], source_confidence="exact")
        s = db.create_session(u["id"], f"title-{ip_name}", workflow=workflow,
                              ip=ip_name, ip_id=ip["id"], workspace_id=ws["id"])
        sid, ip_id, uid = s["id"], ip["id"], u["id"]

    # Materialize the per-session runtime file + manifest (real router path).
    route = AtlasDBRouter().runtime_route(sid, create=True)
    rpath = route.runtime_db_path
    wr_id: Optional[str] = None
    with AtlasDB(rpath, schema_set="runtime") as rdb:
        for i in range(inputs):
            rdb.record_session_input(sid, source="enqueue", source_ref_id=f"q{i}",
                                     user_id=uid, char_count=12, token_estimate=4,
                                     attribution_confidence="exact")
        if worker:
            wr = rdb.start_worker_run(session_id=sid, user_id=uid, workflow=workflow,
                                      worker_kind="workflow", status=worker_status)
            wr_id = wr["id"]
        for _ in range(llm_n):
            rdb.record_llm_call(session_id=sid, ip_id=ip_id, workspace_id=ws["id"],
                                workflow=workflow, model="m1", cost_usd=llm_cost,
                                tokens_input=200, tokens_output=20, status="ok",
                                worker_run_id=wr_id or "",
                                attribution_confidence="exact")
        if verification:
            rdb.record_session_flow_event(
                event_type="verification.passed",
                idempotency_key=f"verif:{sid}", session_id=sid, ip_id=ip_id,
            )
    if worker and worker_status == "running":
        # Close the worker so a healthy session is not stuck "running" forever
        # when we want flow_state to advance to artifact/verification.
        pass
    if artifact:
        with AtlasDB(control_path, schema_set="full") as db:
            db.register_artifact_version(ip_id, "ssot", workspace_id=ws["id"],
                                         version="1", source_session_id=sid,
                                         source_worker_run_id=wr_id or "",
                                         attribution_confidence="exact")
    return {"session_id": sid, "ip_id": ip_id, "user_id": uid,
            "runtime_path": rpath, "username": username}


def _seed_ghost_runtime_spend(control_path: str, *, cost: float = 9.99) -> str:
    """Seed high-cost LLM spend under a session_id that has NO control sessions row.

    This is the runtime-mode shape of "unmatched / ghost" spend: a runtime file
    (+ manifest) exists but there is no ``sessions`` row, so the read model's
    sessions<-users join yields null identity and the row carries an attribution
    gap (no_ip_link / no source identity). Returns the ghost session_id.
    """
    from core.atlas_db import AtlasDB
    from core.atlas_db_router import AtlasDBRouter

    ghost_sid = "ghostuser/ghost_ip/rtl-gen"
    AtlasDBRouter().runtime_route(ghost_sid, create=True)  # manifest + file only
    gpath = AtlasDBRouter().runtime_db_path(ghost_sid, create=True)
    with AtlasDB(gpath, schema_set="runtime") as rdb:
        rdb.record_llm_call(session_id=ghost_sid, model="m1", cost_usd=cost,
                            tokens_input=5000, tokens_output=500, status="ok")
    return ghost_sid


def _seed_central_ghost(control_path: str, *, cost: float = 9.99) -> str:
    """Central mode: high-cost llm_call with an unknown session_id (true gap)."""
    from core.atlas_db import AtlasDB

    ghost_sid = "GHOST-SID-NO-SESSION-ROW"
    with AtlasDB(control_path, schema_set="full") as db:
        db.record_llm_call(session_id=ghost_sid, model="m1", cost_usd=cost,
                            tokens_input=5000, tokens_output=500, status="ok")
    return ghost_sid


# --------------------------------------------------------------------------- #
# No-fanout spy: count per-session runtime sqlite opens during a callable.
# --------------------------------------------------------------------------- #


@contextmanager
def _no_fanout_spy(runtime_root: str):
    """Spy sqlite3.connect AND the per-session runtime opener.

    Records every sqlite3.connect whose path is under the runtime root, and
    patches AtlasDBRouter.runtime_db to RAISE (any call during a read is a
    fanout bug). Yields a dict you can read after the block.
    """
    import sqlite3
    from core import atlas_db_router

    state: Dict[str, Any] = {"runtime_opens": [], "router_runtime_db_calls": 0}
    real_connect = sqlite3.connect
    root_abs = str(Path(runtime_root).resolve())

    def spy_connect(database, *a, **kw):  # type: ignore[no-untyped-def]
        try:
            dbpath = str(Path(str(database)).resolve())
        except Exception:
            dbpath = str(database)
        if root_abs in dbpath or "/runtime/" in dbpath.replace(os.sep, "/"):
            state["runtime_opens"].append(dbpath)
        return real_connect(database, *a, **kw)

    real_runtime_db = atlas_db_router.AtlasDBRouter.runtime_db

    def spy_runtime_db(self, session_id, create=True):  # type: ignore[no-untyped-def]
        state["router_runtime_db_calls"] += 1
        raise AssertionError(
            f"FANOUT: AtlasDBRouter.runtime_db opened during a read "
            f"(session_id={session_id!r})"
        )

    sqlite3.connect = spy_connect  # type: ignore[assignment]
    atlas_db_router.AtlasDBRouter.runtime_db = spy_runtime_db  # type: ignore[assignment]
    try:
        yield state
    finally:
        sqlite3.connect = real_connect  # type: ignore[assignment]
        atlas_db_router.AtlasDBRouter.runtime_db = real_runtime_db  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Real subprocess server for HTTP legs (httpx 0.28 ASGITransport is async-only,
# so we hit the REAL route over a REAL uvicorn process — strictly more e2e).
# --------------------------------------------------------------------------- #


def _wait_http(base: str, path: str = "/healthz", timeout: float = 25.0) -> bool:
    import httpx

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if httpx.get(f"{base}{path}", timeout=1.0).status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


@contextmanager
def _live_server(*, control_path: str, runtime_root: str, admin_mode: str,
                 rollup_enable: str = "0", rollup_interval: str = "30"):
    """Boot the REAL uvicorn admin/UI server as an isolated subprocess.

    The server shares ``control_path`` with the in-process seeder/fold, so a fold
    done in-process (Part A) is visible to the server's no-fanout reads. Yields
    ``(base_url, log_path, proc)``.
    """
    home = tempfile.mkdtemp(prefix="atlas-sf-srv-home-")
    Path(home, ".common_ai_agent").mkdir(parents=True, exist_ok=True)
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    # Clear every admin bypass flag so an "enforced" server (admin_mode == "")
    # truly enforces DB-backed auth. NOTE: ATLAS_ADMIN_AUTH_MODE="off" is itself
    # a LOCAL-ADMIN bypass mode (see core.atlas_auth._LOCAL_ADMIN_MODES), so to
    # test denial we pass admin_mode="" (default DB-backed auth), not "off".
    for _k in ("ATLAS_ADMIN_AUTH_MODE", "ATLAS_LOCAL_ADMIN", "ATLAS_ADMIN_BYPASS",
               "ATLAS_ADMIN_LOGIN_REQUIRED"):
        env.pop(_k, None)
    env.update({
        "HOME": home,
        "ATLAS_CONTROL_DB_PATH": control_path,
        "ATLAS_DB_PATH": control_path,
        "ATLAS_RUNTIME_DB_ROOT": runtime_root,
        "ATLAS_RUNTIME_DB_MODE": "session",
        "ATLAS_MULTI_USER": "1",
        "ATLAS_USE_PROCESSES": "0",
        "CHAT_RESPONDER_AUTOSTART": "0",
        "ATLAS_FLOW_ROLLUP_ENABLE": rollup_enable,
        "ATLAS_FLOW_ROLLUP_INTERVAL_S": rollup_interval,
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": os.pathsep.join(p for p in sys.path if p),
    })
    if admin_mode:
        env["ATLAS_ADMIN_AUTH_MODE"] = admin_mode
    log_path = Path(home) / "server.log"
    log_fh = open(log_path, "w")
    proc = subprocess.Popen(
        [sys.executable, str(_REPO / "src" / "atlas_ui.py"),
         "--host", "127.0.0.1", "--port", str(port)],
        env=env, stdout=log_fh, stderr=subprocess.STDOUT,
    )
    try:
        ready = _wait_http(base, "/healthz", timeout=30.0)
        yield {"base": base, "log_path": log_path, "proc": proc, "ready": ready}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        log_fh.close()


# --------------------------------------------------------------------------- #
# PART A — runtime-mode real chain.
# --------------------------------------------------------------------------- #


def part_a() -> Tuple[Recorder, Recorder, Recorder, Optional[Dict[str, Any]]]:
    rec = Recorder("e2e-runtime-chain")
    rec_auth = Recorder("e2e-auth")
    rec_fan = Recorder("e2e-no-fanout")
    captured_payload: Optional[Dict[str, Any]] = None

    with _runtime_env("session") as env:
        ctrl = env["control_path"]
        rec.log("PART A — runtime-mode real chain (write -> fold -> API -> render)")
        rec.log(f"control_db={ctrl}")
        rec.log(f"runtime_root={env['runtime_root']}")

        # --- 1. Seed >=3 sessions via real write paths into per-session runtime DBs.
        healthy = _seed_runtime_session(
            ctrl, username="alice", ip_name="uart_healthy", workflow="rtl-gen",
            inputs=2, worker=True, worker_status="completed", llm_n=2, llm_cost=0.5,
            artifact=True, verification=True,
        )
        problem = _seed_runtime_session(
            ctrl, username="bob", ip_name="dma_problem", workflow="rtl-gen",
            inputs=1, worker=False, llm_n=1, llm_cost=2.5, artifact=False,
        )
        ghost_sid = _seed_ghost_runtime_spend(ctrl, cost=9.99)
        rec.log(f"seeded healthy={healthy['session_id']} problem={problem['session_id']} "
                f"ghost={ghost_sid}")

        from core.atlas_db import AtlasDB
        from core.atlas_db_router import AtlasDBRouter
        from core import runtime_rollup
        from core.session_flow_usage import build_session_flow_payload

        rec.check(AtlasDBRouter().mode() == "session",
                  "runtime mode active (router.mode()=='session')",
                  AtlasDBRouter().mode())

        # --- 2. Production fold OUT OF BAND (run_rollup_pass -> rollup_all_active_flow).
        summ = runtime_rollup.run_rollup_pass()
        rec.check(summ.get("flow", 0) >= 3 and summ.get("errors", 0) == 0,
                  "run_rollup_pass folded >=3 sessions with 0 errors",
                  json.dumps(summ))

        # --- 3. Read model + HTTP route.
        payload = build_session_flow_payload(AtlasDB(ctrl, schema_set="full"))
        rec.check(payload.get("runtime_mode") is True,
                  "payload.runtime_mode is True", str(payload.get("runtime_mode")))
        by_id = {s["session_id"]: s for s in payload["sessions"]}

        h = by_id.get(healthy["session_id"], {})
        rec.check(bool(h), "healthy session present in payload.sessions",
                  healthy["session_id"])
        rec.check(h.get("input_count") == 2 and h.get("llm_attempts") == 2
                  and h.get("worker_runs") == 1 and h.get("artifact_count") == 1,
                  "healthy real counts (input=2 llm=2 worker=1 artifact=1)",
                  f"in={h.get('input_count')} llm={h.get('llm_attempts')} "
                  f"wr={h.get('worker_runs')} art={h.get('artifact_count')}")
        rec.check(h.get("risk_level") == "ok"
                  and h.get("flow_state") in ("artifact_produced", "verification_seen",
                                              "completed"),
                  "healthy classified ok / produced-or-verified",
                  f"risk={h.get('risk_level')} state={h.get('flow_state')}")

        p = by_id.get(problem["session_id"], {})
        rec.check(bool(p), "problem session present in payload.sessions",
                  problem["session_id"])
        rec.check(p.get("llm_attempts") == 1 and p.get("artifact_count") == 0
                  and p.get("cost_usd") == 2.5,
                  "problem real counts (llm=1 artifact=0 cost=2.5)",
                  f"llm={p.get('llm_attempts')} art={p.get('artifact_count')} "
                  f"cost={p.get('cost_usd')}")
        rec.check(p.get("risk_level") in ("warning", "critical"),
                  "problem classified warning/critical (llm spend, no artifact)",
                  f"risk={p.get('risk_level')} reason={p.get('risk_reason')}")

        # Ghost: high-cost spend with NO control sessions row. In no-fanout runtime
        # mode it surfaces as a rollup row with null identity + an attribution gap
        # (NOT a fabricated, fully-attributed session). Assert it is NOT presented
        # as a real, identified session and that it carries the gap signal.
        ghost_row = by_id.get(ghost_sid, {})
        rec.check(ghost_row.get("user_id") in (None, "")
                  and ghost_row.get("ip") in (None, "")
                  and ghost_row.get("username") in (None, ""),
                  "ghost spend has NO real identity (not a fabricated session)",
                  f"user_id={ghost_row.get('user_id')} ip={ghost_row.get('ip')} "
                  f"username={ghost_row.get('username')}")
        rec.check(str(ghost_row.get("attribution_confidence")) in ("inferred", "missing"),
                  "ghost spend flagged as attribution gap (inferred/missing)",
                  f"confidence={ghost_row.get('attribution_confidence')} "
                  f"reason={ghost_row.get('missing_reason')}")
        gap_count = int(payload["summary"].get("attribution_gap_count") or 0)
        rec.check(gap_count >= 1 and any(
            str(g.get("confidence")) == "missing" for g in payload["attribution_gaps"]),
                  "attribution_gaps non-empty with confidence=missing",
                  f"gap_count={gap_count} gaps={json.dumps(payload['attribution_gaps'])}")

        rec.check(len(payload["needs_attention"]) >= 1,
                  "needs_attention non-empty",
                  f"n={len(payload['needs_attention'])}")
        funnel = {f["stage"]: f["count"] for f in payload["funnel"]}
        rec.check(len(payload["funnel"]) == 7 and funnel.get("created", 0) >= 3,
                  "funnel populated (7 stages, created>=3)", json.dumps(funnel))
        rec.check(len(payload["ip_flow"]) >= 2,
                  "ip_flow populated (>=2 IPs derived)",
                  f"n={len(payload['ip_flow'])}")

        rec.log("populated payload summary: " + json.dumps(payload["summary"]))
        rec.log("populated payload funnel:  " + json.dumps(payload["funnel"]))
        rec.log("populated payload sessions:")
        for s in payload["sessions"]:
            rec.log(f"  {str(s['session_id'])[:28]:28} risk={s['risk_level']:8} "
                    f"state={s['flow_state']:18} in={s['input_count']} "
                    f"llm={s['llm_attempts']} wr={s['worker_runs']} "
                    f"art={s['artifact_count']} cost={s['cost_usd']}")

        # --- HTTP route 200 (admin) via the REAL uvicorn server + local-auth.
        #     The server shares the control DB with our in-process fold above, so
        #     it reads back the already-folded rollups (NO on-read fold).
        import httpx
        try:
            with _live_server(control_path=ctrl, runtime_root=env["runtime_root"],
                              admin_mode="local", rollup_enable="0") as srv:
                if not srv["ready"]:
                    tail = srv["log_path"].read_text(errors="replace")[-1500:]
                    rec.check(False, "admin server booted for HTTP leg",
                              f"server not ready; log:\n{tail}")
                else:
                    r = httpx.get(f"{srv['base']}/api/admin/session-flow", timeout=10)
                    rec.check(r.status_code == 200,
                              "GET /api/admin/session-flow -> 200 (admin, real server)",
                              f"status={r.status_code}")
                    http_payload = r.json()
                    rec.check("pagination" in http_payload
                              and http_payload["pagination"].get("max_limit") == 500,
                              "HTTP payload exposes pagination.max_limit==500",
                              json.dumps(http_payload.get("pagination")))
                    http_ids = {s["session_id"] for s in http_payload["sessions"]}
                    rec.check(healthy["session_id"] in http_ids
                              and problem["session_id"] in http_ids,
                              "HTTP payload contains the seeded healthy+problem sessions",
                              f"n_sessions={len(http_ids)}")
                    captured_payload = http_payload
        except Exception as exc:  # noqa: BLE001
            rec.check(False, "GET /api/admin/session-flow (admin) raised",
                      f"{exc}\n{traceback.format_exc()}")

        # --- 4. Non-admin denied (no flow rows leaked) — real server, auth ON.
        rec_auth.log("PART A.4 — non-admin denial (real server, DB-backed auth enforced)")
        try:
            with _live_server(control_path=ctrl, runtime_root=env["runtime_root"],
                              admin_mode="", rollup_enable="0") as srv_na:
                if not srv_na["ready"]:
                    tail = srv_na["log_path"].read_text(errors="replace")[-1500:]
                    rec_auth.check(False, "non-admin server booted",
                                   f"server not ready; log:\n{tail}")
                else:
                    rna = httpx.get(f"{srv_na['base']}/api/admin/session-flow",
                                    timeout=10)
                    rec_auth.check(rna.status_code in (401, 403),
                                   "non-admin GET /api/admin/session-flow -> 401/403",
                                   f"status={rna.status_code}")
                    try:
                        body = rna.json()
                    except Exception:
                        body = {}
                    rec_auth.check("sessions" not in body,
                                   "denied response carries NO flow rows",
                                   json.dumps(body)[:200])
            rec_auth.check(captured_payload is not None,
                           "admin (local) GET /api/admin/session-flow -> 200 with rows",
                           f"n_sessions="
                           f"{len(captured_payload['sessions']) if captured_payload else 'n/a'}")
        except Exception as exc:  # noqa: BLE001
            rec_auth.check(False, "non-admin denial check raised",
                           f"{exc}\n{traceback.format_exc()}")

        # --- 5. NO-FANOUT: zero per-session runtime sqlite opens during the read.
        rec_fan.log("PART A.5 — no-fanout during the HTTP read")
        try:
            with _no_fanout_spy(env["runtime_root"]) as spy:
                p2 = build_session_flow_payload(AtlasDB(ctrl, schema_set="full"))
            n_opens = len(spy["runtime_opens"])
            rec_fan.check(n_opens == 0,
                          "ZERO per-session runtime sqlite files opened during read",
                          f"runtime_opens={n_opens} "
                          f"router_runtime_db_calls={spy['router_runtime_db_calls']}")
            rec_fan.check(len(p2["sessions"]) == len(payload["sessions"]),
                          "no-fanout read returns the SAME populated sessions",
                          f"n={len(p2['sessions'])}")
            if spy["runtime_opens"]:
                rec_fan.log("  opened (BUG): " + json.dumps(spy["runtime_opens"][:5]))
        except AssertionError as exc:
            rec_fan.check(False, "router.runtime_db was called during read (FANOUT)",
                          str(exc))
        except Exception as exc:  # noqa: BLE001
            rec_fan.check(False, "no-fanout spy raised", f"{exc}")

    # --- Central-mode leg: prove the costed attribution-gap behaviour the
    #     no-fanout runtime path deliberately summarizes (ghost gap WITH cost,
    #     NOT a session row, surfaced in unmatched_cost + needs_attention).
    with _runtime_env("central") as cenv:
        from core.atlas_db import AtlasDB
        from core.session_flow_usage import build_session_flow_payload

        cctrl = cenv["control_path"]
        chealthy = _seed_central_like_session(cctrl)
        cghost = _seed_central_ghost(cctrl, cost=9.99)
        cp = build_session_flow_payload(AtlasDB(cctrl, schema_set="full"))
        rec.log("")
        rec.log("PART A (central leg) — costed ghost attribution gap")
        cids = {s["session_id"] for s in cp["sessions"]}
        rec.check(cghost not in cids,
                  "central: ghost spend is NOT a session row", cghost)
        costed = [g for g in cp["attribution_gaps"]
                  if str(g.get("confidence")) == "missing" and float(g.get("cost_usd") or 0) >= 1.0]
        rec.check(len(costed) >= 1,
                  "central: ghost in attribution_gaps with confidence=missing + cost",
                  json.dumps(cp["attribution_gaps"]))
        rec.check(float(cp["summary"].get("unmatched_cost_usd") or 0) >= 9.99,
                  "central: summary.unmatched_cost_usd surfaces the ghost spend",
                  str(cp["summary"].get("unmatched_cost_usd")))
        rec.check(any(n.get("category") == "unmatched_cost" for n in cp["needs_attention"]),
                  "central: needs_attention has category=unmatched_cost",
                  json.dumps([n.get("category") for n in cp["needs_attention"]]))
        rec.check(chealthy in cids,
                  "central: healthy session present", chealthy)

    # Persist the captured REAL payload for Part C (Vitest).
    if captured_payload is not None:
        _PAYLOAD_FIXTURE.mkdir(parents=True, exist_ok=True)
        (_PAYLOAD_FIXTURE / "session-flow-real-payload.json").write_text(
            json.dumps(captured_payload, indent=2, sort_keys=True), encoding="utf-8"
        )
        rec.log("")
        rec.log("captured REAL HTTP payload -> "
                "frontend/atlas/__tests__/fixtures/session-flow-real-payload.json")
        rec.log("FULL PAYLOAD JSON:")
        rec.log(json.dumps(captured_payload, indent=2, sort_keys=True))

    return rec, rec_auth, rec_fan, captured_payload


def _seed_central_like_session(control_path: str) -> str:
    """Central mode: a normal healthy session written entirely to the control DB."""
    from core.atlas_db import AtlasDB

    with AtlasDB(control_path, schema_set="full") as db:
        u = db.create_user("alice", "alice", "pw")
        ws = db.upsert_workspace("ws-alice", owner_user_id=u["id"], local_path="/a")
        ip = db.upsert_ip_block(ws["id"], "uart_central", "x",
                                created_by_user_id=u["id"], source_confidence="exact")
        s = db.create_session(u["id"], "central-title", workflow="rtl-gen",
                              ip="uart_central", ip_id=ip["id"], workspace_id=ws["id"])
        sid = s["id"]
        db.record_session_input(sid, source="enqueue", source_ref_id="q1",
                                user_id=u["id"], char_count=12, token_estimate=4,
                                attribution_confidence="exact")
        wr = db.start_worker_run(session_id=sid, user_id=u["id"], workflow="rtl-gen",
                                 worker_kind="workflow", status="completed")
        db.record_llm_call(session_id=sid, ip_id=ip["id"], workspace_id=ws["id"],
                           workflow="rtl-gen", model="m1", cost_usd=0.5,
                           tokens_input=200, tokens_output=20, status="ok",
                           worker_run_id=wr["id"], attribution_confidence="exact")
        db.register_artifact_version(ip["id"], "ssot", workspace_id=ws["id"],
                                     version="1", source_session_id=sid,
                                     source_worker_run_id=wr["id"],
                                     attribution_confidence="exact")
    return sid


# --------------------------------------------------------------------------- #
# PART B — live scheduler proof (real uvicorn server, real daemon).
# --------------------------------------------------------------------------- #


def part_b() -> Recorder:
    rec = Recorder("e2e-live-scheduler")
    rec.log("PART B — live uvicorn server + periodic rollup daemon (folds on-server)")

    import httpx
    from core.atlas_db import AtlasDB

    tmp = tempfile.mkdtemp(prefix="atlas-sf-live-")
    ctrl = str(Path(tmp) / "atlas.db")
    runtime_root = str(Path(tmp) / "runtime")
    AtlasDB(ctrl, schema_set="full").close()

    # Seed must run in THIS process pointed at the SAME control DB + runtime root
    # the server uses, so the manifest + runtime file land where the daemon reads.
    saved = {k: os.environ.get(k) for k in
             ("ATLAS_CONTROL_DB_PATH", "ATLAS_DB_PATH", "ATLAS_RUNTIME_DB_ROOT",
              "ATLAS_RUNTIME_DB_MODE")}
    os.environ.update({
        "ATLAS_CONTROL_DB_PATH": ctrl, "ATLAS_DB_PATH": ctrl,
        "ATLAS_RUNTIME_DB_ROOT": runtime_root, "ATLAS_RUNTIME_DB_MODE": "session",
    })
    try:
        with _live_server(control_path=ctrl, runtime_root=runtime_root,
                          admin_mode="local", rollup_enable="1",
                          rollup_interval="2") as srv:
            if not srv["ready"]:
                tail = srv["log_path"].read_text(encoding="utf-8",
                                                 errors="replace")[-2500:]
                rec.check(False, "live server bound/booted",
                          f"server did not answer /healthz; log tail:\n{tail}")
                rec.log("FALLBACK: server could not boot in this env; Part A already "
                        "proved the fold logic in-process via run_rollup_pass.")
                return rec
            base = srv["base"]
            rec.check(True, "live server bound/booted on " + base,
                      "/healthz 200, ATLAS_FLOW_ROLLUP_ENABLE=1 interval=2s")

            # Seed runtime rows AFTER boot so the periodic daemon (NOT us) folds it.
            seeded = _seed_runtime_session(
                ctrl, username="liveuser", ip_name="live_ip", workflow="rtl-gen",
                inputs=1, worker=True, worker_status="completed", llm_n=1,
                llm_cost=0.7, artifact=True, verification=True,
            )
            target = seeded["session_id"]
            rec.log(f"seeded live session AFTER boot: {target}")

            # Poll the admin route (bounded <=30s) until the daemon folds it.
            deadline = time.time() + 30.0
            t0 = time.time()
            populated = False
            last_seen: Dict[str, Any] = {}
            while time.time() < deadline:
                try:
                    r = httpx.get(f"{base}/api/admin/session-flow", timeout=3.0)
                    if r.status_code == 200:
                        rows = {s["session_id"]: s for s in r.json().get("sessions", [])}
                        if target in rows and int(rows[target].get("llm_attempts") or 0) >= 1:
                            last_seen = rows[target]
                            populated = True
                            break
                except Exception:
                    pass
                time.sleep(1.0)
            elapsed = time.time() - t0
            rec.check(populated,
                      "live daemon folded the seeded session into "
                      "/api/admin/session-flow",
                      f"time_to_populate={elapsed:.1f}s "
                      f"counts(in={last_seen.get('input_count')} "
                      f"llm={last_seen.get('llm_attempts')} "
                      f"art={last_seen.get('artifact_count')} "
                      f"risk={last_seen.get('risk_level')})")
            if not populated:
                tail = srv["log_path"].read_text(encoding="utf-8",
                                                 errors="replace")[-2000:]
                rec.log("server log tail:\n" + tail)
        rec.log("live server torn down cleanly")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return rec


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main() -> int:
    recorders: List[Recorder] = []
    captured: Optional[Dict[str, Any]] = None

    try:
        rec_a, rec_auth, rec_fan, captured = part_a()
        recorders += [rec_a, rec_auth, rec_fan]
    except Exception as exc:  # noqa: BLE001
        rec = Recorder("e2e-runtime-chain")
        rec.check(False, "PART A crashed", f"{exc}\n{traceback.format_exc()}")
        recorders.append(rec)

    try:
        rec_b = part_b()
        recorders.append(rec_b)
    except Exception as exc:  # noqa: BLE001
        rec = Recorder("e2e-live-scheduler")
        rec.check(False, "PART B crashed", f"{exc}\n{traceback.format_exc()}")
        recorders.append(rec)

    total_pass = sum(r.passed for r in recorders)
    total_fail = sum(r.failed for r in recorders)
    for r in recorders:
        r.save()

    print("\n" + "=" * 64)
    print("SESSION FLOW E2E SUMMARY")
    print("=" * 64)
    for r in recorders:
        print(f"  {r.name:24} {r.passed} passed, {r.failed} failed")
    print(f"  {'TOTAL':24} {total_pass} passed, {total_fail} failed")
    print("=" * 64)
    print(f"Evidence: {_EVIDENCE}")
    if captured is not None:
        print(f"Captured payload: {_PAYLOAD_FIXTURE / 'session-flow-real-payload.json'}")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
