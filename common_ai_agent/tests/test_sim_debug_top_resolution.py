from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_resolve_sim_debug_top_prefers_manifest_for_ip_scoped_request(tmp_path: Path) -> None:
    from atlas_sim_debug_top import resolve_sim_debug_top

    ip_dir = tmp_path / "gpio" / "demo_ip"
    (ip_dir / "tb" / "cocotb").mkdir(parents=True)
    (ip_dir / "yaml").mkdir()
    (ip_dir / "tb" / "cocotb" / "tb_manifest.json").write_text(
        json.dumps({"ip": "demo_ip", "top": "demo_rtl_top"}),
        encoding="utf-8",
    )
    (ip_dir / "yaml" / "demo_ip.ssot.yaml").write_text(
        "top_module:\n  name: demo_ssot_top\n",
        encoding="utf-8",
    )

    out = resolve_sim_debug_top(tmp_path, ip="demo_ip", requested_top="demo_ip")

    assert out["top"] == "demo_rtl_top"
    assert out["source"] == "tb_manifest"
    assert out["manifest_path"] == "gpio/demo_ip/tb/cocotb/tb_manifest.json"


def test_resolve_sim_debug_top_keeps_explicit_non_ip_top(tmp_path: Path) -> None:
    from atlas_sim_debug_top import resolve_sim_debug_top

    out = resolve_sim_debug_top(
        tmp_path,
        ip="demo_ip",
        requested_top="child_block",
        vcd_scope="demo_rtl_top.u_child",
    )

    assert out["top"] == "child_block"
    assert out["source"] == "request"


def test_resolve_sim_debug_top_uses_vcd_scope_but_ignores_dump_helper(tmp_path: Path) -> None:
    from atlas_sim_debug_top import resolve_sim_debug_top

    out = resolve_sim_debug_top(
        tmp_path,
        ip="demo_ip",
        requested_top="demo_ip",
        vcd_scope="atlas_iverilog_vcd_dump.demo_rtl_top.u_core",
    )

    assert out["top"] == "demo_rtl_top"
    assert out["source"] == "vcd_scope"


def test_goal_scoreboard_runner_emits_icarus_vcd_helper_without_dut_wrapper() -> None:
    script = PROJECT_ROOT / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
    spec = importlib.util.spec_from_file_location("emit_goal_scoreboard_cocotb_test", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    compile(module.RUNNER_PY, "RUNNER_PY", "exec")

    assert "atlas_iverilog_vcd_dump" in module.RUNNER_PY
    assert "$dumpvars(0, {top})" in module.RUNNER_PY
    assert "run_sources, run_top = _with_icarus_vcd_dump" in module.RUNNER_PY
    assert "waves = False" in module.RUNNER_PY


def test_hierarchy_normalizes_symlinked_filelist_sources(tmp_path: Path, monkeypatch) -> None:
    import src.atlas_ui as atlas_ui

    ip_dir = tmp_path / "demo_ip"
    rtl_dir = ip_dir / "rtl"
    list_dir = ip_dir / "list"
    tb_dir = ip_dir / "tb" / "cocotb"
    yaml_dir = ip_dir / "yaml"
    rtl_dir.mkdir(parents=True)
    list_dir.mkdir()
    tb_dir.mkdir(parents=True)
    yaml_dir.mkdir()
    (rtl_dir / "demo_rtl_top.sv").write_text(
        "module demo_rtl_top(input logic clk, input logic din, output logic dout);\n"
        "  assign dout = din;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (tb_dir / "tb_manifest.json").write_text(
        json.dumps({"top": "demo_rtl_top"}),
        encoding="utf-8",
    )
    (yaml_dir / "demo_ip.ssot.yaml").write_text(
        "top_module:\n  name: demo_rtl_top\n",
        encoding="utf-8",
    )

    alias = tmp_path.parent / f"{tmp_path.name}_alias"
    try:
        alias.symlink_to(tmp_path, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    try:
        (list_dir / "demo_ip.f").write_text(
            str(alias / "demo_ip" / "rtl" / "demo_rtl_top.sv") + "\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
        monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path.resolve())

        client = TestClient(atlas_ui.create_app())
        client.post("/api/auth/register", json={"username": "debugger", "password": "pw"})
        response = client.get("/api/hierarchy?ip=demo_ip&top=demo_ip&backend=pyslang")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["resolved_top"] == "demo_rtl_top"
        assert data["sources"] == ["demo_ip/rtl/demo_rtl_top.sv"]
        assert data["tree"]["module"] == "demo_rtl_top"
    finally:
        try:
            alias.unlink()
        except OSError:
            pass
