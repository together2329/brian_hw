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
