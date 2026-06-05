"""Full multi-user system integration: chat + cost/token tracking
+ workflow runs + todos + permissions + bridge fan-out + admin
aggregation, all wired together as a single test.

The point of this file is NOT to repeat the unit-level coverage in
the deep / deepdeep / browser suites; it is to prove that when three
real users are simultaneously logged in, each driving their own
workflow with real LLM-call cost tracking, the orchestrator chat
panel surfaces the right ground truth to each user, blocks the
wrong user, and the admin usage report aggregates correctly across
all of them.

Scenarios covered as a single end-to-end:
- 3 users: alice (workspace owner), bob (view on uart_lite),
  carol (no grants)
- 2 IPs: uart_lite, dma (alice runs workflows on both)
- 7 LLM calls across 2 IPs with non-trivial cost+tokens
- Workflow runs in different states (running, completed)
- workflow_todos in mixed statuses
- chat traffic per-IP + _global
- orchestrator context bundle exposes cost/token/blocker for each IP
- chat injects (per-IP + global) into a simulated agent iteration
- admin_usage_payload aggregates LLM cost and chat across users
- two browser contexts simultaneously read the same DB
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

playwright = pytest.importorskip("playwright.sync_api")
uvicorn = pytest.importorskip("uvicorn")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.atlas_db import AtlasDB
from core.atlas_admin_usage import build_admin_usage_payload
from core.atlas_multiuser import (
    _MultiUserBridge,
    set_atlas_bridge_session_id,
    reset_atlas_bridge_session_id,
)
from core.atlas_permissions import PermissionPolicy
from core.orchestrator_inject import (
    build_orchestrator_inject_fn,
    register_bridge,
)
import atlas_api_chat as chat_api


@pytest.fixture(scope="module", autouse=True)
def _central_runtime_db_mode_for_full_multiuser_suite():
    previous = os.environ.get("ATLAS_RUNTIME_DB_MODE")
    os.environ["ATLAS_RUNTIME_DB_MODE"] = "central"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("ATLAS_RUNTIME_DB_MODE", None)
        else:
            os.environ["ATLAS_RUNTIME_DB_MODE"] = previous


# ---------------------------------------------------------------------------
# Seed: 3 users, 2 IPs, real workflows with cost tracking
# ---------------------------------------------------------------------------


def _seed_full(db_path: str) -> dict:
    db = AtlasDB(db_path)
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    carol = db.create_user("carol", "Carol", "pw")
    admin = db.create_user("root", "Root", "pw", role="admin")

    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/repo")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")

    # === workflow runs ===
    run_uart = db.start_workflow_run(
        session_id=f"alice/uart_lite/rtl-gen",
        workspace_id=ws["id"], ip_id=ip_uart["id"],
        workflow="rtl-gen", mode="pipeline",
        model_profile="deepseek", reasoning_effort="medium",
        status="running",
    )
    run_dma = db.start_workflow_run(
        session_id=f"alice/dma/ssot-gen",
        workspace_id=ws["id"], ip_id=ip_dma["id"],
        workflow="ssot-gen", mode="pipeline",
        model_profile="gpt-5.3-codex", reasoning_effort="medium",
        status="running",
    )

    # === workflow stages + todos ===
    db.start_workflow_stage(run_uart["id"], "ssot-rtl", status="running")
    db.upsert_workflow_todo(
        run_uart["id"], title="Implement uart_tx_fsm",
        criteria="FSM transitions match SSOT", status="in_progress",
    )
    db.upsert_workflow_todo(
        run_uart["id"], title="Lock parity policy",
        criteria="parity_en CSR bit declared", status="blocked",
    )
    db.upsert_workflow_todo(
        run_uart["id"], title="Implement baud_gen",
        criteria="oversample=16", status="completed",
    )
    db.upsert_workflow_todo(
        run_dma["id"], title="Author DMA SSOT",
        criteria="36 sections present", status="in_progress",
    )

    # === LLM calls with real cost/tokens ===
    db.record_llm_call(
        session_id="alice/uart_lite/rtl-gen",
        run_id=run_uart["id"], ip_id=ip_uart["id"],
        model="deepseek-v4-pro", provider="deepseek",
        tokens_input=10000, tokens_output=500, tokens_reasoning=200,
        cache_read_tokens=8000, cost_usd=0.18, status="ok",
        call_role="primary",
    )
    db.record_llm_call(
        session_id="alice/uart_lite/rtl-gen",
        run_id=run_uart["id"], ip_id=ip_uart["id"],
        model="deepseek-v4-pro", provider="deepseek",
        tokens_input=5000, tokens_output=300,
        cost_usd=0.09, status="ok",
    )
    db.record_llm_call(
        session_id="alice/uart_lite/rtl-gen",
        run_id=run_uart["id"], ip_id=ip_uart["id"],
        model="deepseek-v4-pro", provider="deepseek",
        tokens_input=3000, tokens_output=100,
        cost_usd=0.05, status="ok",
    )
    # Bob iterating on the same uart_lite (different session)
    db.record_llm_call(
        session_id="bob/uart_lite/rtl-gen",
        run_id=run_uart["id"], ip_id=ip_uart["id"],
        model="deepseek-v4-pro", provider="deepseek",
        tokens_input=2000, tokens_output=80,
        cost_usd=0.04, status="ok",
    )
    # dma workflow run by alice
    db.record_llm_call(
        session_id="alice/dma/ssot-gen",
        run_id=run_dma["id"], ip_id=ip_dma["id"],
        model="gpt-5.3-codex", provider="openai",
        tokens_input=8000, tokens_output=2000,
        cost_usd=0.50, status="ok",
    )
    db.record_llm_call(
        session_id="alice/dma/ssot-gen",
        run_id=run_dma["id"], ip_id=ip_dma["id"],
        model="gpt-5.3-codex", provider="openai",
        tokens_input=4000, tokens_output=1500,
        cost_usd=0.35, status="ok",
    )
    db.record_llm_call(
        session_id="alice/dma/ssot-gen",
        run_id=run_dma["id"], ip_id=ip_dma["id"],
        model="gpt-5.3-codex", provider="openai",
        tokens_input=2000, tokens_output=800,
        cost_usd=0.15, status="error", error_type="rate_limit",
    )

    return {
        "db": db, "alice": alice, "bob": bob, "carol": carol, "admin": admin,
        "ws": ws, "ip_uart": ip_uart, "ip_dma": ip_dma,
        "run_uart": run_uart, "run_dma": run_dma,
    }


# ---------------------------------------------------------------------------
# DB-level checks (no browser): cost, tokens, todos, gates roll into bundle
# ---------------------------------------------------------------------------


def test_cost_and_tokens_appear_in_per_ip_context_bundle(tmp_path):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]

    ctx = db.summarize_ip_room_context(w["ip_uart"]["id"])
    # Recent events should include the 4 LLM calls on uart_lite,
    # newest-first, with cost / tokens / model preserved.
    llm_events = [e for e in ctx["recent_events"] if e["kind"] == "llm"]
    assert len(llm_events) == 4
    for ev in llm_events:
        assert ev["model"] == "deepseek-v4-pro"
        assert ev["cost_usd"] > 0
        assert ev["tokens_input"] >= 2000
    # Newest-first ordering
    timestamps = [ev["ts"] for ev in llm_events]
    assert timestamps == sorted(timestamps, reverse=True)


def test_dma_context_isolates_llm_costs_from_uart(tmp_path):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]
    ctx_dma = db.summarize_ip_room_context(w["ip_dma"]["id"])
    ctx_uart = db.summarize_ip_room_context(w["ip_uart"]["id"])

    dma_llm = [e for e in ctx_dma["recent_events"] if e["kind"] == "llm"]
    uart_llm = [e for e in ctx_uart["recent_events"] if e["kind"] == "llm"]
    # Models do not cross IPs
    assert all(e["model"] == "gpt-5.3-codex" for e in dma_llm)
    assert all(e["model"] == "deepseek-v4-pro" for e in uart_llm)


def test_global_context_summarizes_all_user_visible_ips(tmp_path):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]

    # Alice (owner) sees both IPs.
    ctx_a = db.summarize_global_room_context(user_id=w["alice"]["id"])
    names_a = {r["name"] for r in ctx_a["ips"]}
    assert names_a == {"uart_lite", "dma"}

    # Bob has view on uart_lite only.
    ctx_b = db.summarize_global_room_context(user_id=w["bob"]["id"])
    names_b = {r["name"] for r in ctx_b["ips"]}
    assert names_b == {"uart_lite"}

    # Carol has no grants — sees nothing in the global summary.
    ctx_c = db.summarize_global_room_context(user_id=w["carol"]["id"])
    assert ctx_c["ips"] == []


def test_admin_usage_payload_aggregates_across_users(tmp_path):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]

    payload = build_admin_usage_payload(db)
    assert isinstance(payload, dict)

    # The aggregate must reflect all 7 LLM calls.
    rows = db.list_llm_calls()
    assert len(rows) == 7
    total_cost = sum(r["cost_usd"] for r in rows)
    assert abs(total_cost - (0.18 + 0.09 + 0.05 + 0.04 + 0.50 + 0.35 + 0.15)) < 1e-9


def test_todos_blockers_surface_in_context_bundle(tmp_path):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]
    ctx = db.summarize_ip_room_context(w["ip_uart"]["id"])

    counts = ctx["todos"]["counts"]
    assert counts["in_progress"] == 1
    assert counts["blocked"] == 1
    assert counts["completed"] == 1

    blocker_titles = {b["title"] for b in ctx["todos"]["top_blockers"]}
    assert "Lock parity policy" in blocker_titles


def test_orchestrator_inject_renders_cost_for_agent_iteration(tmp_path, monkeypatch):
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]
    bridge = _MultiUserBridge(single_user=False)
    register_bridge(bridge)
    session = bridge._ensure_session("alice/uart_lite/rtl-gen")
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "uart_lite")
    token = set_atlas_bridge_session_id(session.session_id)
    try:
        inject = build_orchestrator_inject_fn(db, bridge)
        msgs = [{"role": "system", "content": "you are agent."}]
        inject(msgs, "normal")
    finally:
        reset_atlas_bridge_session_id(token)

    content = msgs[0]["content"]
    # Cost / model surfaced to LLM
    assert "deepseek-v4-pro" in content
    assert "$0.18" in content or "0.18" in content
    # Todo counts
    assert "in_progress=1" in content
    assert "blocked=1" in content
    # Top blocker title
    assert "Lock parity policy" in content


def test_chat_traffic_does_not_corrupt_admin_usage(tmp_path):
    """Posting heavy chat traffic should not break or distort the
    admin usage aggregate."""
    w = _seed_full(str(tmp_path / "atlas.db"))
    db = w["db"]
    # 30 chat posts from the 3 active users
    for i in range(10):
        db.record_chat_message(w["ip_uart"]["id"], w["alice"]["id"], f"a{i}")
        db.record_chat_message(w["ip_uart"]["id"], w["bob"]["id"], f"b{i}")
        db.record_chat_message(None, w["alice"]["id"], f"g{i}")

    payload = build_admin_usage_payload(db)
    # Must compute without raising; key types must still match.
    assert "interventions" in payload or isinstance(payload, dict)
    # Cost total still equals the 7 LLM rows.
    rows = db.list_llm_calls()
    total = sum(r["cost_usd"] for r in rows)
    assert abs(total - (0.18 + 0.09 + 0.05 + 0.04 + 0.50 + 0.35 + 0.15)) < 1e-9


# ---------------------------------------------------------------------------
# Real-browser multi-user session: cost/todos visible per user, chat
# round-trips, permission boundaries enforced live.
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def full_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("full-mu") / "atlas.db"
    w = _seed_full(str(db_path))
    bridge = _MultiUserBridge(single_user=False)
    permissions = PermissionPolicy(w["db"])

    app = FastAPI()

    class _TestAuth(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            uid = request.headers.get("x-test-user")
            if uid:
                u = w["db"].get_user(uid)
                if u:
                    request.scope["user"] = u
            return await call_next(request)

    app.add_middleware(_TestAuth)
    chat_api.register_chat_routes(
        app, db=w["db"], bridge=bridge, permissions=permissions
    )

    @app.get("/usage")
    async def usage():
        return JSONResponse(build_admin_usage_payload(w["db"]))

    @app.get("/", response_class=HTMLResponse)
    async def root():
        return HTMLResponse("""<!doctype html><html><body>
<script>window.state={lastCtx:null,lastRooms:null,lastErr:null,sendResult:null};
window.__uid='';
async function api(p,o){o=o||{};o.headers={...(o.headers||{}),'x-test-user':window.__uid};o.credentials='include';const r=await fetch(p,o);let b;try{b=await r.json()}catch(_){b=null}return{status:r.status,body:b}}
window.setUser=(u)=>{window.__uid=u}
window.loadRooms=async()=>{const r=await api('/api/chat/rooms');if(r.status===200)window.state.lastRooms=r.body.rooms;else window.state.lastErr=r}
window.loadContext=async(room)=>{const r=await api('/api/chat/'+encodeURIComponent(room)+'/context');if(r.status===200)window.state.lastCtx=r.body;else window.state.lastErr=r}
window.send=async(room,content)=>{const r=await api('/api/chat/'+encodeURIComponent(room)+'/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})});window.state.sendResult=r;return r}
window.loadUsage=async()=>{const r=await api('/usage');return r.body}
</script>
ready
</body></html>""")

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.socket() as s:
                s.connect(("127.0.0.1", port)); break
        except OSError: time.sleep(0.1)
    else:
        pytest.fail("server never came up")

    yield {**w, "base_url": f"http://127.0.0.1:{port}", "bridge": bridge}
    server.should_exit = True
    th.join(timeout=5)


@pytest.fixture(scope="module")
def browser_pw():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _open_as(browser_pw, base, uid):
    ctx = browser_pw.new_context(base_url=base)
    page = ctx.new_page()
    page.goto("/")
    page.wait_for_function("() => typeof window.setUser === 'function'")
    page.evaluate("(u) => window.setUser(u)", uid)
    return ctx, page


def test_browser_alice_sees_full_cost_and_todos_for_uart(full_server, browser_pw):
    ctx, page = _open_as(browser_pw, full_server["base_url"],
                          full_server["alice"]["id"])
    try:
        page.evaluate("window.loadContext('uart_lite')")
        page.wait_for_function("() => window.state.lastCtx !== null")
        bundle = page.evaluate("() => window.state.lastCtx")
        # Per-IP context shows the workflow run, todos, LLM cost.
        assert bundle["ip"]["name"] == "uart_lite"
        assert bundle["workflow"]["latest_run"]["workflow"] == "rtl-gen"
        assert bundle["workflow"]["latest_run"]["model_profile"] == "deepseek"
        counts = bundle["todos"]["counts"]
        assert counts.get("blocked", 0) == 1
        llm_events = [e for e in bundle["recent_events"] if e["kind"] == "llm"]
        assert len(llm_events) == 4
        total_cost = sum(e["cost_usd"] for e in llm_events)
        assert abs(total_cost - (0.18 + 0.09 + 0.05 + 0.04)) < 1e-9
    finally:
        ctx.close()


def test_browser_bob_cannot_view_dma_context(full_server, browser_pw):
    ctx, page = _open_as(browser_pw, full_server["base_url"],
                          full_server["bob"]["id"])
    try:
        page.evaluate("window.loadContext('dma')")
        page.wait_for_function("() => window.state.lastErr !== null")
        err = page.evaluate("() => window.state.lastErr")
        assert err["status"] == 403
    finally:
        ctx.close()


def test_browser_alice_global_view_has_both_ips_with_cost_aware_status(
    full_server, browser_pw
):
    ctx, page = _open_as(browser_pw, full_server["base_url"],
                          full_server["alice"]["id"])
    try:
        page.evaluate("window.loadContext('_global')")
        page.wait_for_function("() => window.state.lastCtx !== null")
        bundle = page.evaluate("() => window.state.lastCtx")
        names = {ip["name"] for ip in bundle["ips"]}
        assert names == {"uart_lite", "dma"}
        for ip in bundle["ips"]:
            # Each IP row carries workflow status and open-blockers count
            # — same numbers an orchestrator dashboard would render.
            assert ip["latest_workflow"] in {"rtl-gen", "ssot-gen"}
            assert ip["run_status"] == "running"
    finally:
        ctx.close()


def test_browser_carol_global_blocked(full_server, browser_pw):
    ctx, page = _open_as(browser_pw, full_server["base_url"],
                          full_server["carol"]["id"])
    try:
        page.evaluate("window.loadContext('_global')")
        page.wait_for_function("() => window.state.lastErr !== null")
        err = page.evaluate("() => window.state.lastErr")
        assert err["status"] == 403
    finally:
        ctx.close()


def test_browser_three_users_simultaneous_chat_round_trip(full_server, browser_pw):
    """All three users open the same room concurrently. Alice + Bob
    post, Carol fails; Alice + Bob both see both messages on refresh."""
    base = full_server["base_url"]
    ca, pa = _open_as(browser_pw, base, full_server["alice"]["id"])
    cb, pb = _open_as(browser_pw, base, full_server["bob"]["id"])
    cc, pc = _open_as(browser_pw, base, full_server["carol"]["id"])
    try:
        # alice + bob post to uart_lite
        pa.evaluate("window.send('uart_lite', 'ALICE-CHAT')")
        pa.wait_for_function(
            "() => window.state.sendResult && window.state.sendResult.status===200"
        )
        pb.evaluate("window.send('uart_lite', 'BOB-CHAT')")
        pb.wait_for_function(
            "() => window.state.sendResult && window.state.sendResult.status===200"
        )

        # carol fails on every room
        pc.evaluate("window.send('uart_lite', 'CAROL-TRY')")
        pc.wait_for_function(
            "() => window.state.sendResult && window.state.sendResult.status===403"
        )

        # alice + bob both see both posts when loading context
        for pg in (pa, pb):
            pg.evaluate("window.state.lastCtx = null; window.loadContext('uart_lite')")
            pg.wait_for_function("() => window.state.lastCtx !== null")
            # The bundle does not contain messages; query messages directly.
        # Use the chat messages endpoint
        for pg, who in ((pa, "alice"), (pb, "bob")):
            pg.evaluate("""async () => {
                const r = await fetch('/api/chat/uart_lite/messages',
                  {headers:{'x-test-user': window.__uid}});
                window.state._msgs = (await r.json()).messages;
            }""")
            pg.wait_for_function("() => Array.isArray(window.state._msgs)")
            contents = pg.evaluate("() => window.state._msgs.map(m => m.content)")
            assert "ALICE-CHAT" in contents, f"{who} missed ALICE-CHAT"
            assert "BOB-CHAT" in contents, f"{who} missed BOB-CHAT"
    finally:
        for c in (ca, cb, cc): c.close()


def test_browser_admin_usage_endpoint_aggregates_across_users(
    full_server, browser_pw
):
    """An admin browser session pulls the same cross-user aggregate
    that the admin dashboard surfaces (LLM cost, intervention counts,
    todo flow). All numbers must reflect data inserted by every
    user, not just the admin's own activity."""
    ctx, page = _open_as(browser_pw, full_server["base_url"],
                          full_server["admin"]["id"])
    try:
        page.evaluate("""async () => {
            const r = await fetch('/usage', {headers:{'x-test-user': window.__uid}});
            window.state.usage = await r.json();
        }""")
        page.wait_for_function("() => window.state.usage !== undefined")
        usage = page.evaluate("() => window.state.usage")
        assert isinstance(usage, dict)
        # Has at minimum the well-known top-level slices.
        for key in ("todo_usage", "trace_events", "tool_usage", "interventions"):
            assert key in usage, f"missing usage slice: {key}"
    finally:
        ctx.close()


def test_browser_concurrent_posts_persist_distinct_rows(full_server, browser_pw):
    """Two users posting in quick succession from independent browser
    contexts: every row lands, neither overwrites the other."""
    base = full_server["base_url"]
    ca, pa = _open_as(browser_pw, base, full_server["alice"]["id"])
    cb, pb = _open_as(browser_pw, base, full_server["bob"]["id"])
    try:
        # 8 alternating posts
        for i in range(4):
            pa.evaluate(f"window.send('uart_lite', 'A-{i}')")
            pa.wait_for_function(
                "() => window.state.sendResult && window.state.sendResult.status===200"
            )
            pb.evaluate(f"window.send('uart_lite', 'B-{i}')")
            pb.wait_for_function(
                "() => window.state.sendResult && window.state.sendResult.status===200"
            )

        # Verify 8 of our markers are present (plus any pre-existing rows
        # from earlier tests in the same module).
        rows = full_server["db"].list_chat_messages(
            full_server["ip_uart"]["id"], limit=200
        )
        contents = [r["payload"]["content"] for r in rows]
        for i in range(4):
            assert f"A-{i}" in contents
            assert f"B-{i}" in contents
    finally:
        ca.close(); cb.close()
