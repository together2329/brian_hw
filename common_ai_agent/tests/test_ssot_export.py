"""Tests for the SSOT export pipeline: yaml -> md / docx / html.

Run with:
    cd common_ai_agent
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_export.py -v
"""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import src.atlas_ui as atlas_ui


REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_IPS = ("qa_timer_pure", "quad_spi_ctrl")


def _copy_sample_ssot(src_ip: str, dst_root: Path, dst_ip: str | None = None) -> Path:
    """Copy <repo>/<src_ip>/yaml/<src_ip>.ssot.yaml into the test PROJECT_ROOT.

    When `dst_ip` is provided the destination ip name is renamed
    (so test fixtures don't collide with the real `qa_timer_pure`
    project root from the working repo).
    """
    src = REPO_ROOT / src_ip / "yaml" / f"{src_ip}.ssot.yaml"
    assert src.is_file(), f"sample ssot missing: {src}"
    ip = dst_ip or src_ip
    dest_dir = dst_root / ip / "yaml"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{ip}.ssot.yaml"
    shutil.copyfile(src, dest)
    return dest


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


# ---------------------------------------------------------------------------
# Helper-level tests (no FastAPI)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ip", SAMPLE_IPS)
def test_load_and_render_markdown(tmp_path, monkeypatch, ip):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    _copy_sample_ssot(ip, tmp_path)
    data = atlas_ui._load_ssot_yaml(ip)
    assert isinstance(data, dict) and data, "ssot yaml parsed empty"
    md = atlas_ui._ssot_to_markdown(data, ip)
    assert md.startswith(f"# {ip}\n"), f"missing H1 for {ip}"
    assert "## Parameters" in md, "expected '## Parameters' section in markdown"
    h2_count = sum(1 for line in md.splitlines() if line.startswith("## "))
    assert h2_count >= 10, f"expected ≥10 H2 sections, found {h2_count}"


@pytest.mark.parametrize("ip", SAMPLE_IPS)
def test_render_html(tmp_path, monkeypatch, ip):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    _copy_sample_ssot(ip, tmp_path)
    data = atlas_ui._load_ssot_yaml(ip)
    md = atlas_ui._ssot_to_markdown(data, ip)
    html = atlas_ui._ssot_to_html(md, ip)
    assert html.startswith("<!DOCTYPE html>"), "html missing doctype"
    assert "<h1" in html and f">{ip}</h1>" in html, "h1 tag with ip name missing"
    assert "<table>" in html, "expected at least one table"


@pytest.mark.parametrize("ip", SAMPLE_IPS)
def test_render_docx_is_valid_zip(tmp_path, monkeypatch, ip):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    _copy_sample_ssot(ip, tmp_path)
    data = atlas_ui._load_ssot_yaml(ip)
    out_path = tmp_path / f"{ip}_test.docx"
    atlas_ui._ssot_to_docx(data, ip, out_path)
    assert out_path.is_file() and out_path.stat().st_size > 0
    with zipfile.ZipFile(out_path) as zf:
        names = zf.namelist()
        assert "[Content_Types].xml" in names, "not a valid docx (missing manifest)"


def test_ssot_yaml_path_validates_ip(tmp_path, monkeypatch):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    with pytest.raises(ValueError):
        atlas_ui._ssot_yaml_path("../escape")
    with pytest.raises(ValueError):
        atlas_ui._ssot_yaml_path("9bad_start")
    with pytest.raises(ValueError):
        atlas_ui._ssot_yaml_path("")
    good = atlas_ui._ssot_yaml_path("good_name_42")
    assert str(good).endswith("/good_name_42/yaml/good_name_42.ssot.yaml")


def test_load_ssot_yaml_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    with pytest.raises(FileNotFoundError):
        atlas_ui._load_ssot_yaml("nope_ip")


def test_load_ssot_yaml_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    yaml_dir = tmp_path / "broken_ip" / "yaml"
    yaml_dir.mkdir(parents=True)
    (yaml_dir / "broken_ip.ssot.yaml").write_text(
        "top_module: { name: x\n  bad_indent: oops\n", encoding="utf-8",
    )
    with pytest.raises(ValueError):
        atlas_ui._load_ssot_yaml("broken_ip")


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ip", SAMPLE_IPS)
@pytest.mark.parametrize("fmt,media_substr", [
    ("md", "text/markdown"),
    ("html", "text/html"),
    ("docx", "officedocument.wordprocessingml.document"),
])
def test_export_endpoint_returns_expected_format(tmp_path, monkeypatch, ip, fmt, media_substr):
    client = _make_client(tmp_path, monkeypatch)
    _copy_sample_ssot(ip, tmp_path)
    resp = client.get(f"/api/ssot/export?ip={ip}&format={fmt}")
    assert resp.status_code == 200, resp.text
    assert media_substr in resp.headers.get("content-type", "")
    body = resp.content
    assert body, "empty response body"
    # File side-effect: <ip>/doc/<ip>_ssot.<ext>
    out_path = tmp_path / ip / "doc" / f"{ip}_ssot.{fmt}"
    assert out_path.is_file(), f"expected {out_path} to be written"


def test_export_endpoint_rejects_bad_ip(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/ssot/export?ip=../escape&format=md")
    assert resp.status_code == 400, resp.text


def test_export_endpoint_rejects_bad_format(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _copy_sample_ssot("qa_timer_pure", tmp_path)
    resp = client.get("/api/ssot/export?ip=qa_timer_pure&format=pdf")
    assert resp.status_code == 400, resp.text


def test_export_endpoint_404_when_yaml_missing(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/ssot/export?ip=nonexistent_ip_test&format=md")
    assert resp.status_code == 404, resp.text


def test_export_endpoint_default_format_is_md(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _copy_sample_ssot("qa_timer_pure", tmp_path)
    resp = client.get("/api/ssot/export?ip=qa_timer_pure")
    assert resp.status_code == 200, resp.text
    assert "text/markdown" in resp.headers.get("content-type", "")
