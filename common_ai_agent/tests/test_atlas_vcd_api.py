from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.atlas_api_vcd import register_vcd_routes


VCD_TEXT = "$date\nx\n$end\n$timescale 1ns $end\n$scope module top $end\n$var wire 1 ! clk $end\n$upscope $end\n$enddefinitions $end\n#0\n0!\n"


def _safe(root: Path, rel_path: str) -> Optional[Path]:
    target = (root / rel_path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def _client(root: Path) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def _attach_user(request, call_next):
        request.scope["user"] = {"id": "uid_alice", "username": "alice", "role": "user"}
        return await call_next(request)

    register_vcd_routes(
        app,
        project_root=lambda: root,
        safe_path=lambda path: _safe(root, path),
        skip_dirs={".git", "__pycache__"},
        max_vcd_bytes=4096,
    )
    return TestClient(app)


def _install_fake_fst2vcd(bin_dir: Path) -> None:
    bin_dir.mkdir()
    exe = bin_dir / "fst2vcd"
    exe.write_text("#!/bin/sh\ncat <<'EOF'\n" + VCD_TEXT + "EOF\n", encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)


def test_vcd_list_converts_fst_to_cached_vcd_for_active_ip(tmp_path: Path, monkeypatch) -> None:
    ip_dir = tmp_path / "demo_ip"
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True)
    fst = sim_dir / "demo_ip.fst"
    fst.write_bytes(b"FSTDATA")
    bin_dir = tmp_path / "bin"
    _install_fake_fst2vcd(bin_dir)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    response = _client(tmp_path).get("/api/vcd/list?ip=demo_ip")

    assert response.status_code == 200
    payload = response.json()
    files = payload["files"]
    assert len(files) == 1
    assert files[0]["source"] == "converted_fst"
    assert files[0]["converted_from"] == "demo_ip/sim/demo_ip.fst"
    assert files[0]["path"].startswith("demo_ip/sim/.wave_cache/")
    assert (tmp_path / files[0]["path"]).read_text(encoding="utf-8") == VCD_TEXT


def test_vcd_list_discovers_waveforms_anywhere_under_active_ip(tmp_path: Path) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim" / "nested"
    cocotb_dir = tmp_path / "demo_ip" / "tb" / "cocotb" / "sim_build"
    other_ip_dir = tmp_path / "other_ip" / "sim"
    sim_dir.mkdir(parents=True)
    cocotb_dir.mkdir(parents=True)
    other_ip_dir.mkdir(parents=True)
    (sim_dir / "waves.vcd").write_text(VCD_TEXT, encoding="utf-8")
    (cocotb_dir / "trace.vcd").write_text(VCD_TEXT, encoding="utf-8")
    (other_ip_dir / "hidden.vcd").write_text(VCD_TEXT, encoding="utf-8")

    response = _client(tmp_path).get("/api/vcd/list?ip=demo_ip")

    assert response.status_code == 200
    paths = {entry["path"] for entry in response.json()["files"]}
    assert "demo_ip/sim/nested/waves.vcd" in paths
    assert "demo_ip/tb/cocotb/sim_build/trace.vcd" in paths
    assert "other_ip/sim/hidden.vcd" not in paths


def test_vcd_list_and_raw_resolve_workspace_session_ip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    sim_dir = tmp_path / "alice" / "s1" / "demo_ip" / "sim" / "nested"
    sim_dir.mkdir(parents=True)
    (sim_dir / "waves.vcd").write_text(VCD_TEXT, encoding="utf-8")
    client = _client(tmp_path)

    listed = client.get(
        "/api/vcd/list",
        params={
            "ip": "demo_ip",
            "session_id": "alice/s1/demo_ip/sim_debug",
        },
    )

    assert listed.status_code == 200
    paths = {entry["path"] for entry in listed.json()["files"]}
    assert "demo_ip/sim/nested/waves.vcd" in paths

    raw = client.get(
        "/api/vcd/raw",
        params={
            "path": "demo_ip/sim/nested/waves.vcd",
            "session_id": "alice/s1/demo_ip/sim_debug",
        },
    )

    assert raw.status_code == 200
    payload = raw.json()
    assert payload["path"] == "demo_ip/sim/nested/waves.vcd"
    assert payload["content"] == VCD_TEXT


def test_vcd_raw_accepts_fst_path_and_returns_converted_vcd(tmp_path: Path, monkeypatch) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "trace.fst").write_bytes(b"FSTDATA")
    bin_dir = tmp_path / "bin"
    _install_fake_fst2vcd(bin_dir)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    response = _client(tmp_path).get("/api/vcd/raw?path=demo_ip/sim/trace.fst")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "converted_fst"
    assert payload["converted_from"] == "demo_ip/sim/trace.fst"
    assert payload["content"] == VCD_TEXT


def test_vcd_list_preserves_converted_fst_metadata_after_cache_hit(tmp_path: Path, monkeypatch) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "trace.fst").write_bytes(b"FSTDATA")
    bin_dir = tmp_path / "bin"
    _install_fake_fst2vcd(bin_dir)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    client = _client(tmp_path)

    first = client.get("/api/vcd/list?ip=demo_ip")
    second = client.get("/api/vcd/list?ip=demo_ip")

    assert first.status_code == 200
    assert second.status_code == 200
    files = second.json()["files"]
    assert len(files) == 1
    assert files[0]["source"] == "converted_fst"
    assert files[0]["converted_from"] == "demo_ip/sim/trace.fst"


def test_vcd_list_replaces_stale_sibling_vcd_with_converted_fst(tmp_path: Path, monkeypatch) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim"
    sim_dir.mkdir(parents=True)
    stale_vcd = sim_dir / "trace.vcd"
    stale_vcd.write_text("STALE_VCD", encoding="utf-8")
    fst = sim_dir / "trace.fst"
    fst.write_bytes(b"FSTDATA")
    os.utime(stale_vcd, (100, 100))
    os.utime(fst, (200, 200))
    bin_dir = tmp_path / "bin"
    _install_fake_fst2vcd(bin_dir)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")

    response = _client(tmp_path).get("/api/vcd/list?ip=demo_ip")

    assert response.status_code == 200
    files = response.json()["files"]
    assert len(files) == 1
    assert files[0]["source"] == "converted_fst"
    assert files[0]["converted_from"] == "demo_ip/sim/trace.fst"
    assert files[0]["path"] != "demo_ip/sim/trace.vcd"


def test_vcd_list_reports_missing_fst_converter(tmp_path: Path, monkeypatch) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "trace.fst").write_bytes(b"FSTDATA")
    monkeypatch.setenv("PATH", "")

    response = _client(tmp_path).get("/api/vcd/list?ip=demo_ip")

    assert response.status_code == 200
    payload = response.json()
    assert payload["files"] == []
    assert payload["waveform_errors"][0]["status"] == "converter_missing"
    assert payload["waveform_errors"][0]["source"] == "demo_ip/sim/trace.fst"


def test_vcd_raw_reports_missing_fst_converter(tmp_path: Path, monkeypatch) -> None:
    sim_dir = tmp_path / "demo_ip" / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "trace.fst").write_bytes(b"FSTDATA")
    monkeypatch.setenv("PATH", "")

    response = _client(tmp_path).get("/api/vcd/raw?path=demo_ip/sim/trace.fst")

    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "converter_missing"
    assert "fst2vcd" in payload["message"]
