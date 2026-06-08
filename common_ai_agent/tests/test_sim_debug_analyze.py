from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core import vcd_timeline


_VCD = """$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$var wire 1 " en $end
$var wire 8 # data $end
$upscope $end
$enddefinitions $end
#0
0!
0"
b00000000 #
#5
1!
#10
0!
1"
b00001010 #
#15
1!
#20
0"
0!
"""

_HIER_VCD = """$timescale 1ns $end
$scope module tb $end
$scope module top $end
$scope module u_child $end
$var wire 1 ! dout $end
$upscope $end
$scope module u_other $end
$var wire 1 " dout $end
$upscope $end
$upscope $end
$upscope $end
$enddefinitions $end
#0
0!
0"
#5
1!
#7
1"
"""


def _write_vcd(tmp_path) -> Path:
    p = tmp_path / "t.vcd"
    p.write_text(_VCD, encoding="utf-8")
    return p


def test_timeline_parse_edges_and_value(tmp_path):
    tl = vcd_timeline.load(_write_vcd(tmp_path))
    assert tl.timescale == "ns"
    assert tl.time_range() == (0, 20)
    assert tl.match_signals("en") == ["top.en"]
    # en rises at 10, falls at 20
    assert tl.edges("en", "rising") == [10]
    assert tl.edges("en", "falling") == [20]
    # clk rises at 5 and 15
    assert tl.edges("clk", "rising") == [5, 15]
    # value sampling (last value at-or-before t)
    assert tl.value_at("en", 12) == "1"
    assert tl.value_at("en", 25) == "0"
    assert tl.value_at("data", 12) == "b00001010"
    # bus 'any' change recorded at #10 (first sample at #0 is not an edge)
    assert 10 in tl.edges("data", "any")
    # leaf and scope-qualified lookups both resolve
    assert tl.resolve_id("top.en") == tl.resolve_id("en")
    # unknown signal
    assert tl.edges("nope", "rising") == []


def test_rising_edge_includes_signal_asserted_at_t0(tmp_path):
    # Regression: a signal asserted in $dumpvars at t0 (e.g. psel for the FIRST
    # APB access) is an X->1 rising edge and must be findable. Previously the
    # first sample was never an edge, so "find the first access" skipped the t0
    # transaction and the waveform window opened on the 2nd access instead.
    vcd = """$timescale 1ns $end
$scope module top $end
$var wire 1 ! psel $end
$upscope $end
$enddefinitions $end
#0
$dumpvars
1!
$end
#10
0!
#20
1!
"""
    p = tmp_path / "t0.vcd"
    p.write_text(vcd, encoding="utf-8")
    tl = vcd_timeline.load(p)
    # psel: (0,'1'),(10,'0'),(20,'1') -> rising at t0 AND at 20
    assert tl.edges("psel", "rising") == [0, 20]
    # X->0 is NOT a falling edge; first real fall is at 10
    assert tl.edges("psel", "falling") == [10]
    # 'any' keeps the documented "first sample is not an edge" behaviour
    assert tl.edges("psel", "any") == [10, 20]


def test_timeline_resolves_scope_and_refuses_ambiguous_leaf(tmp_path):
    p = tmp_path / "hier.vcd"
    p.write_text(_HIER_VCD, encoding="utf-8")
    tl = vcd_timeline.load(p)

    assert tl.resolve_id("dout") is None
    assert tl.resolve_id("dout", scope="top.u_child") == "!"
    assert tl.resolve_id("u_child.dout") == "!"
    assert tl.resolve_id("dout", scope="tb.top.u_other") == '"'


def test_analyze_find_and_value_synthetic(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    sim = tmp_path / "IPS" / "sim"
    sim.mkdir(parents=True)
    (sim / "IPS.vcd").write_text(_VCD, encoding="utf-8")
    from core.sim_debug_analyze import find_event, signal_value

    r = find_event("IPS", "en", "rising", 1)
    assert r["time"] == 10 and r["count"] == 1 and r["timescale"] == "ns"
    bad = find_event("IPS", "does_not_exist", "rising", 1)
    assert bad["error"] and "did_you_mean" in bad
    v = signal_value("IPS", "data", 12)
    assert v["value"] == "b00001010" and v["at"] == 12


def test_resolve_wave_signal_uses_elab_module_pin_when_vcd_suffix_is_not_enough(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    sim = tmp_path / "IPS" / "sim"
    sim.mkdir(parents=True)
    (sim / "IPS.vcd").write_text(_HIER_VCD.replace("u_other", "u_sink"), encoding="utf-8")

    from core import sim_debug_analyze as sda

    class FakeElab:
        def build_hierarchy_cached(self, prefer, top, sources):
            return {
                "tree": {
                    "name": "top",
                    "module": "top",
                    "children": [{"name": "top.u_child", "module": "child", "children": []}],
                }
            }

        def module_signals_cached(self, prefer, top, module, sources):
            return {"signals": [{"name": "dout", "direction": "out"}] if module == "child" else []}

    monkeypatch.setattr(sda, "_resolve_sources_and_top", lambda root, ip, signal="": ([tmp_path / "rtl.sv"], "top"))
    monkeypatch.setattr(sda, "_load_elab", lambda root: FakeElab())

    r = sda.resolve_wave_signal("IPS", "child.dout")

    assert r["status"] == "resolved"
    assert r["source"] == "pyslang"
    assert r["resolved_signal"] == "tb.top.u_child.dout"


def test_resolve_wave_signal_reports_ambiguous_elab_module_pin(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    sim = tmp_path / "IPS" / "sim"
    sim.mkdir(parents=True)
    (sim / "IPS.vcd").write_text(_HIER_VCD, encoding="utf-8")

    from core import sim_debug_analyze as sda

    class FakeElab:
        def build_hierarchy_cached(self, prefer, top, sources):
            return {
                "tree": {
                    "name": "top",
                    "module": "top",
                    "children": [
                        {"name": "top.u_child", "module": "child", "children": []},
                        {"name": "top.u_other", "module": "child", "children": []},
                    ],
                }
            }

        def module_signals_cached(self, prefer, top, module, sources):
            return {"signals": [{"name": "dout", "direction": "out"}]}

    monkeypatch.setattr(sda, "_resolve_sources_and_top", lambda root, ip, signal="": ([tmp_path / "rtl.sv"], "top"))
    monkeypatch.setattr(sda, "_load_elab", lambda root: FakeElab())

    r = sda.resolve_wave_signal("IPS", "child.dout")

    assert r["status"] == "ambiguous"
    assert [c["resolved_signal"] for c in r["candidates"]] == [
        "tb.top.u_child.dout",
        "tb.top.u_other.dout",
    ]


def test_analyze_dispatch_pushes_intent(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    sim = tmp_path / "IPS" / "sim"
    sim.mkdir(parents=True)
    (sim / "IPS.vcd").write_text(_VCD, encoding="utf-8")
    from core.sim_debug_analyze import run_sim_debug_analysis
    from core import sim_debug_intent as sdi

    txt = run_sim_debug_analysis("find", ip="IPS", signal="en", edge="rising", nth=1,
                                 push_intent=sdi.push_intent)
    assert "10 ns" in txt
    intent = sdi.get_intent("IPS")
    # find → a goto intent that also carries the signal + a cursor at the edge
    assert intent["action"] == "goto" and intent.get("cursor_a") == 10
    assert intent.get("signals") == ["top.en"]


def test_analyze_trace_on_real_ip(monkeypatch):
    """trace via pyslang on a real IP if present (skip otherwise)."""
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(REPO))
    rtl = REPO / "mctp_assembler" / "rtl"
    if not rtl.is_dir():
        pytest.skip("mctp_assembler RTL not present")
    try:
        from core.pyslang_compat import import_pyslang
        if import_pyslang()[1]:
            pytest.skip("pyslang not available")
    except Exception:
        pytest.skip("pyslang_compat unavailable")
    from core.sim_debug_analyze import trace_signal
    r = trace_signal("mctp_assembler", "parse_ok")
    assert not r.get("error"), r
    assert r.get("driver") and r["driver"]["file_line"].endswith(".sv:188")
