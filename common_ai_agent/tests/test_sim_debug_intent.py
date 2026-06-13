from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core import sim_debug_intent as sdi


def test_push_get_roundtrip_and_monotonic_seq(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    assert sdi.get_intent("anything") == {"seq": 0}

    seq1 = sdi.push_intent("MY_IP", "show", signals=["a", "b"], note=None)
    got = sdi.get_intent("MY_IP")
    assert got["seq"] == seq1 and got["action"] == "show"
    assert got["ip"] == "MY_IP" and got["signals"] == ["a", "b"]
    assert "note" not in got  # None fields dropped

    seq2 = sdi.push_intent("MY_IP", "goto", t_start=1000, t_end=8000)
    assert seq2 > seq1                       # monotonic
    latest = sdi.get_intent("MY_IP")
    assert latest["action"] == "goto" and latest["t_end"] == 8000  # only latest kept

    # file lives under .session and is valid json
    f = tmp_path / ".session" / "sim_debug_intent.json"
    assert f.is_file()


def test_sim_debug_tool_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPX")
    from core.tools import sim_debug

    msg = sim_debug(action="show", signals="clk, rst, dout")
    assert "added" in msg and "clk" in msg
    stored = sdi.get_intent("IPX")
    assert stored["action"] == "show" and stored["signals"] == ["clk", "rst", "dout"]

    assert "5000" in sim_debug(action="goto", t_start=5000, t_end=15000)
    assert sdi.get_intent("IPX")["action"] == "goto"

    sim_debug(action="cursor", cursor_a=100, cursor_b=200)
    assert sdi.get_intent("IPX")["action"] == "cursor"

    sim_debug(action="fit")
    assert sdi.get_intent("IPX")["action"] == "fit"

    assert "no signals" in sim_debug(action="show")          # guard
    assert "unknown action" in sim_debug(action="bogus")     # guard


def test_sim_debug_registered_and_schema():
    from core.tools import AVAILABLE_TOOLS
    from core.tool_schema import TOOL_SCHEMAS
    assert "sim_debug" in AVAILABLE_TOOLS
    sch = TOOL_SCHEMAS["sim_debug"]["function"]
    assert sch["name"] == "sim_debug"
    assert "action" in sch["parameters"]["properties"]
    assert sch["parameters"]["required"] == ["action"]


def test_sim_debug_intent_api_route_reads_file_channel(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    app = FastAPI()
    from src.atlas_api_sim_debug import register_sim_debug_routes

    register_sim_debug_routes(
        app,
        _safe=lambda rel: (tmp_path / rel).resolve(),
        PROJECT_ROOT=tmp_path,
        WORKFLOW_ROOT=tmp_path / "workflow",
    )

    seq = sdi.push_intent("IP_ROUTE", "show", signals=["clk"])
    r = TestClient(app).get("/api/sim_debug/intent?ip=IP_ROUTE")

    assert r.status_code == 200
    assert r.json()["seq"] == seq
    assert r.json()["ip"] == "IP_ROUTE"
    assert r.json()["signals"] == ["clk"]


def test_get_intent_base_root_isolation(tmp_path, monkeypatch):
    """The agent worker (process_per_session) writes the intent under its
    session WORKSPACE root; the web API must read from that SAME root. Reading
    from a different root must miss — this is exactly the bug where the web
    process's global PROJECT_ROOT != the worker's workspace root."""
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    root_a = tmp_path / "owner_a" / "default"
    root_b = tmp_path / "owner_b" / "default"
    seq = sdi.push_intent("IP1", "goto", base_root=str(root_a), t_start=10, t_end=99)

    got = sdi.get_intent("IP1", base_root=str(root_a))
    assert got["seq"] == seq and got["action"] == "goto" and got["t_end"] == 99
    # A different workspace root must NOT see it (the pre-fix global-root read).
    assert sdi.get_intent("IP1", base_root=str(root_b)) == {"seq": 0}


def _app_with_user(tmp_path, username):
    """A bare app with the sim_debug routes plus a middleware that stamps an
    authenticated user onto the request scope (the real app's auth layer)."""
    from starlette.middleware.base import BaseHTTPMiddleware

    from src.atlas_api_sim_debug import register_sim_debug_routes

    app = FastAPI()

    class _UserMW(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.scope["user"] = {"id": f"uid_{username}", "username": username}
            return await call_next(request)

    app.add_middleware(_UserMW)
    register_sim_debug_routes(
        app,
        _safe=lambda rel: (tmp_path / rel).resolve(),
        PROJECT_ROOT=tmp_path,
        WORKFLOW_ROOT=tmp_path / "workflow",
    )
    return app


def test_intent_route_reads_from_session_workspace_root(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    ws_root = tmp_path / "alice" / "default"
    seq = sdi.push_intent("IPW", "show", base_root=str(ws_root), signals=["pclk"])

    client = TestClient(_app_with_user(tmp_path, "alice"))
    # Without the session key the API reads the global root and misses (the bug).
    assert client.get("/api/sim_debug/intent?ip=IPW").json() == {"seq": 0}
    # With it, the API resolves the session workspace root and finds the intent.
    r = client.get("/api/sim_debug/intent?ip=IPW&session_id=alice/default/IPW/default")
    assert r.status_code == 200 and r.json()["seq"] == seq
    assert r.json()["signals"] == ["pclk"]


def test_intent_route_cross_owner_session_denied(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    sdi.push_intent("IPW", "show", base_root=str(tmp_path / "bob" / "default"), signals=["x"])
    client = TestClient(_app_with_user(tmp_path, "alice"))
    # alice may not read bob's workspace intent by passing bob's session key.
    r = client.get("/api/sim_debug/intent?ip=IPW&session_id=bob/default/IPW/default")
    assert r.status_code == 403


def test_scenarios_route_resolves_ip_under_session_root(tmp_path, monkeypatch):
    monkeypatch.delenv("ATLAS_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    ip_dir = tmp_path / "alice" / "default" / "IPS"
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / "IPS.ssot.yaml").write_text(
        "test_requirements:\n"
        "  scenarios:\n"
        "    - id: SC1\n"
        "      name: basic\n",
        encoding="utf-8",
    )
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        '{"scenario_id": "SC1", "passed": true}\n', encoding="utf-8")

    client = TestClient(_app_with_user(tmp_path, "alice"))
    # Global-root lookup (no session key) cannot find the IP -> the reported bug.
    assert client.get("/api/debug/scenarios?ip=IPS").json().get("error") == "ip not found"
    # Session-scoped lookup finds it and rolls up the scoreboard.
    r = client.get("/api/debug/scenarios?ip=IPS&session_id=alice/default/IPS/default")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 1
    assert body["tests"][0]["scenario_id"] == "SC1"
    assert body["tests"][0]["status"] == "pass"
