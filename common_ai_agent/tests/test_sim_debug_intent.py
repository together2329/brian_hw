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

    # Resolution needs a real VCD; mock it so this exercises the tool's action
    # dispatch (intent push) deterministically rather than a live waveform DB.
    import core.sim_debug_analyze as sda
    monkeypatch.setattr(
        sda, "resolve_wave_signal",
        lambda ip, sig, scope="": {"status": "resolved", "resolved_signal": sig},
    )
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


def test_sim_debug_radix_and_remove_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPR")
    from core.tools import sim_debug

    # radix=fsm -> FSM (the parameter/enum-name display the user wants on/off)
    msg = sim_debug(action="radix", signals="prdata, addr", radix="fsm")
    assert "FSM" in msg
    got = sdi.get_intent("IPR")
    assert got["action"] == "radix" and got["radix"] == "FSM"
    assert got["signals"] == ["prdata", "addr"]

    # hex/dec/bin normalize
    sim_debug(action="radix", signals="prdata", radix="dec")
    assert sdi.get_intent("IPR")["radix"] == "DEC"

    # off -> the radix field is dropped, so the panel clears the override
    sim_debug(action="radix", signals="prdata", radix="off")
    cleared = sdi.get_intent("IPR")
    assert cleared["action"] == "radix" and "radix" not in cleared

    # remove
    rmsg = sim_debug(action="remove", signals="prdata, addr")
    assert "removed" in rmsg
    rem = sdi.get_intent("IPR")
    assert rem["action"] == "remove" and rem["signals"] == ["prdata", "addr"]

    # guards
    assert "radix" in sim_debug(action="radix", signals="prdata", radix="bogus").lower()
    assert "signals" in sim_debug(action="radix", radix="hex")
    assert "signals" in sim_debug(action="remove")


def test_sim_debug_keep_and_clear_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPK")
    from core.tools import sim_debug

    msg = sim_debug(action="keep", signals="irq")
    assert "only" in msg.lower()
    got = sdi.get_intent("IPK")
    assert got["action"] == "keep" and got["signals"] == ["irq"]

    cmsg = sim_debug(action="clear")
    assert "cleared" in cmsg.lower()
    assert sdi.get_intent("IPK")["action"] == "clear"

    assert "signals" in sim_debug(action="keep")  # guard: keep needs signals


def test_sim_debug_show_flags_not_dumped_as_placeholder(tmp_path, monkeypatch):
    """A signal that resolves in RTL but is NOT in the VCD (rtl_not_dumped) is
    pushed so the panel renders a '⚠ not in VCD' placeholder (visible feedback),
    and the message says clearly it is a placeholder — not a silent no-op and not
    a false 'added'. Regression for the 'added but not visible' confusion."""
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPD")

    import core.sim_debug_analyze as sda

    def fake_resolve(ip, sig, scope=""):
        if sig == "psel":
            return {"status": "resolved", "resolved_signal": "tb.psel"}
        if sig == "clk":
            return {"status": "rtl_not_dumped", "resolved_signal": "tb.pclk"}
        return {"status": "unresolved", "candidates": []}

    monkeypatch.setattr(sda, "resolve_wave_signal", fake_resolve)
    from core.tools import sim_debug

    msg = sim_debug(action="show", signals="psel, clk")
    # both are pushed: real signal + the placeholder so the user SEES feedback
    got = sdi.get_intent("IPD")
    assert got["action"] == "show" and got["signals"] == ["tb.psel", "tb.pclk"]
    # the message distinguishes the real add from the not-dumped placeholder
    assert "added tb.psel" in msg
    assert "tb.pclk" in msg and "not dumped" in msg and "placeholder" in msg

    # even when EVERY requested signal is not dumped, it is still pushed as a
    # placeholder (feedback) — not dropped — with the honest caveat.
    msg2 = sim_debug(action="show", signals="clk")
    assert sdi.get_intent("IPD")["signals"] == ["tb.pclk"]
    assert "not dumped" in msg2 and "placeholder" in msg2

    # truly unresolvable names still produce nothing (no phantom push)
    msg3 = sim_debug(action="show", signals="zzz_nope")
    assert "no signal could be shown" in msg3


def test_sim_debug_reorder_group_ungroup_color_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPG")
    from core.tools import sim_debug

    # reorder — exact top-to-bottom order, no resolution needed
    msg = sim_debug(action="reorder", signals="psel, penable, irq")
    assert "reorder" in msg.lower()
    got = sdi.get_intent("IPG")
    assert got["action"] == "reorder" and got["signals"] == ["psel", "penable", "irq"]
    assert "reorder" in sim_debug(action="reorder")  # guard

    # group with colour
    sim_debug(action="group", group="apb", signals="psel, penable", color="#4dd0e1")
    g = sdi.get_intent("IPG")
    assert g["action"] == "group" and g["group"] == "apb"
    assert g["signals"] == ["psel", "penable"] and g["color"] == "#4dd0e1"
    # group without colour (colour is optional → dropped)
    sim_debug(action="group", group="ctl", signals="pwrite")
    g2 = sdi.get_intent("IPG")
    assert g2["group"] == "ctl" and "color" not in g2
    # group guards
    assert "group" in sim_debug(action="group", signals="psel")    # missing group name
    assert "group" in sim_debug(action="group", group="apb")        # missing signals

    # ungroup
    sim_debug(action="ungroup", signals="psel, penable")
    u = sdi.get_intent("IPG")
    assert u["action"] == "ungroup" and u["signals"] == ["psel", "penable"]
    assert "signals" in sim_debug(action="ungroup")  # guard

    # color
    sim_debug(action="color", signals="irq", color="#ff0000")
    c = sdi.get_intent("IPG")
    assert c["action"] == "color" and c["color"] == "#ff0000" and c["signals"] == ["irq"]
    assert "color" in sim_debug(action="color", signals="irq")   # missing colour
    assert "color" in sim_debug(action="color", color="#fff")    # missing signals

    # scope is carried through for actions that take it
    sim_debug(action="reorder", signals="a, b", scope="tb.dut.u_core")
    assert sdi.get_intent("IPG")["scope"] == "tb.dut.u_core"

    # rename a group (old -> new)
    sim_debug(action="group", group="apb", signals="psel")
    rn = sim_debug(action="rename", group="apb", to="apb_if")
    assert "apb_if" in rn
    r = sdi.get_intent("IPG")
    assert r["action"] == "rename" and r["group"] == "apb" and r["to"] == "apb_if"
    assert "old name" in sim_debug(action="rename", group="apb")   # guard: needs `to`
    assert "old name" in sim_debug(action="rename", to="x")         # guard: needs group


def test_sim_debug_fold_unfold_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPF")
    from core.tools import sim_debug

    sim_debug(action="fold", group="apb")
    f = sdi.get_intent("IPF")
    assert f["action"] == "fold" and f["group"] == "apb"

    sim_debug(action="unfold", group="apb")
    assert sdi.get_intent("IPF")["action"] == "unfold"

    assert "group" in sim_debug(action="fold")    # guard
    assert "group" in sim_debug(action="unfold")  # guard


def test_sim_debug_trace_find_value_dispatch(tmp_path, monkeypatch):
    """trace/find/value delegate to run_sim_debug_analysis (pyslang/VCD). Verify
    the tool routes the right action + args to it (analysis itself needs a real
    design, exercised by test_sim_debug_analyze.py)."""
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPA")

    import core.sim_debug_analyze as sda
    calls = []

    def fake_analysis(action, ip="", signal="", edge="rising", nth=1, at=None,
                      push_intent=None, scope=""):
        calls.append((action, ip, signal, edge, nth, at, scope))
        return f"[analysis {action} {signal}]"

    monkeypatch.setattr(sda, "run_sim_debug_analysis", fake_analysis)
    from core.tools import sim_debug

    assert "analysis trace" in sim_debug(action="trace", signal="irq")
    assert "analysis find" in sim_debug(action="find", signal="psel", edge="falling", nth=2)
    assert "analysis value" in sim_debug(action="value", signal="prdata", at=500)
    assert [c[0] for c in calls] == ["trace", "find", "value"]
    assert calls[1][3] == "falling" and calls[1][4] == 2   # edge, nth threaded
    assert calls[2][5] == 500                                # at threaded


def test_sim_debug_search_and_source_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPS2")
    rtl = tmp_path / "IPS2" / "rtl"
    rtl.mkdir(parents=True)
    (rtl / "timer_core.sv").write_text(
        "module timer_core;\n"
        "  always_ff @(posedge clk) if (wrap_next) count_q <= '0;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    from core.tools import sim_debug

    # text search of the IP source ("actually read it") jumps to the top hit
    msg = sim_debug(action="search", pattern="wrap_next")
    assert "wrap_next" in msg and "timer_core.sv:2" in msg
    intent = sdi.get_intent("IPS2")
    assert intent["action"] == "source" and intent["line"] == 2
    assert intent["path"].endswith("timer_core.sv")

    assert "no source match" in sim_debug(action="search", pattern="zzz_nomatch_xyz")
    assert "pattern" in sim_debug(action="search")          # guard

    # explicit open of a source file:line
    o = sim_debug(action="source", path="IPS2/rtl/timer_core.sv", line=2)
    assert "opened" in o
    op = sdi.get_intent("IPS2")
    assert op["action"] == "source" and op["line"] == 2
    assert "path" in sim_debug(action="source")             # guard


def test_sim_debug_source_self_corrects_to_trace_or_search(tmp_path, monkeypatch):
    """Regression (finding: 'interrupt 만들어내는 소스'): the model reaches for
    action="source" when the user asks "find the source that drives/creates
    signal X", but source needs a path and used to dead-end to a no-op hint —
    so the model abandoned trace/search for raw grep. Now a path-less source
    self-corrects: signal -> trace (driver + conditions), pattern -> search,
    and nothing -> an actionable hint that routes to trace/search."""
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPSC")
    rtl = tmp_path / "IPSC" / "rtl"
    rtl.mkdir(parents=True)
    (rtl / "irq.sv").write_text(
        "module irq_gen;\n"
        "  always_ff @(posedge clk) if (overflow) irq <= 1'b1;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    from core.tools import sim_debug

    # path-less source + signal -> routes to trace (driver + conditions)
    by_sig = sim_debug(action="source", signal="irq")
    assert "routing to trace" in by_sig

    # path-less source + pattern -> routes to search and actually finds the text
    by_pat = sim_debug(action="source", pattern="overflow")
    assert "routing your pattern to search" in by_pat and "overflow" in by_pat
    intent = sdi.get_intent("IPSC")
    assert intent["action"] == "source"   # search jumped the source pane to the hit

    # path-less source + no target -> actionable routing hint, not a dead end
    hint = sim_debug(action="source")
    assert "trace" in hint and "search" in hint


def test_sim_debug_unknown_action_lists_all_actions(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPU")
    from core.tools import sim_debug
    msg = sim_debug(action="nonsense")
    assert "unknown action" in msg
    # every supported action is advertised so the agent can self-correct
    for act in ("show", "goto", "cursor", "fit", "reorder", "group", "ungroup",
                "rename", "color", "radix", "remove", "keep", "clear", "fold", "unfold",
                "search", "source", "fsm", "trace", "find", "value"):
        assert act in msg, f"{act} missing from help"


def test_sim_debug_fsm_action(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPFSM")
    rtl = tmp_path / "IPFSM" / "rtl"
    rtl.mkdir(parents=True)
    (rtl / "fsm.sv").write_text(
        "module fsm;\n"
        "  localparam IDLE = 0, RUN = 1;\n"
        "  always_ff @(posedge clk) begin\n"
        "    case (state_q)\n"
        "      IDLE: if (start) state_q <= RUN;\n"
        "      RUN:  state_q <= IDLE;\n"
        "    endcase\n"
        "  end\n"
        "endmodule\n",
        encoding="utf-8",
    )
    from core.tools import sim_debug

    msg = sim_debug(action="fsm", signal="state_q")
    assert "FSM" in msg
    # the case-decode usage is found by grep regardless of pyslang availability
    assert "case (state_q)" in msg and "state usage" in msg
    assert "state register" in sim_debug(action="fsm")   # guard


def test_sim_debug_show_ambiguous_not_pushed(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "IPAMB")
    import core.sim_debug_analyze as sda
    monkeypatch.setattr(sda, "resolve_wave_signal", lambda ip, sig, scope="": {
        "status": "ambiguous",
        "candidates": [{"resolved_signal": "tb.u_a.clk"}, {"resolved_signal": "tb.u_b.clk"}],
    })
    from core.tools import sim_debug
    msg = sim_debug(action="show", signals="clk")
    assert "ambiguous" in msg and "no signal could be shown" in msg
    # nothing pushed for a purely-ambiguous request
    assert sdi.get_intent("IPAMB") == {"seq": 0}


def test_sim_debug_every_action_in_valid_actions():
    """The VALID_ACTIONS set the panel trusts must list every action the tool
    can push, so no tool intent is silently rejected by the channel."""
    pushable = {"show", "goto", "cursor", "trace", "fit", "reorder", "group",
                "ungroup", "color", "radix", "remove", "keep", "clear", "fold", "unfold"}
    assert pushable <= sdi.VALID_ACTIONS


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
