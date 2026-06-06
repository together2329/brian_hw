"""Tests for the REQ tab backend: GET /api/req/export.

Mirrors tests/test_ssot_inline_export_endpoint.py — build the app with a
multi-user client, lay down a per-IP REQ bundle on disk, and assert the
aggregated HTML renders inline and is written to <ip>/doc/<ip>_req.html.
"""
import json
from pathlib import Path

from fastapi.testclient import TestClient

import src.atlas_ui as atlas_ui
from src.atlas_req_export import load_req_bundle, render_req_html


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


def _write_req_bundle(root: Path, ip: str) -> None:
    req = root / ip / "req"
    verify = root / ip / "verify"
    signoff = root / ip / "signoff"
    for d in (req, verify, signoff):
        d.mkdir(parents=True, exist_ok=True)

    (req / f"{ip}_requirements.md").write_text(
        "# Example Requirements\n\n"
        "## 1. Purpose\n\nThe IP does a bounded thing.\n\n"
        "| field | value |\n| --- | --- |\n| width | 32 |\n",
        encoding="utf-8",
    )
    (req / "approval_manifest.json").write_text(json.dumps({
        "status": "approved",
        "approval_mode": "starter",
        "locked_truth_scope": "local_engineering",
        "approved_by": "test",
        "approved_at_utc": "2026-06-06T00:00:00Z",
        "artifact": f"req/{ip}_requirements.md",
        "checks": {"has_feature_table": True, "no_tbd_markers": True},
    }), encoding="utf-8")
    (req / "ssot_validation.json").write_text(json.dumps({
        "ok": True,
        "check_ssot_disk": {"stdout": "[check_ssot_disk] PASS: 12 sections, 0 TBDs\n"},
    }), encoding="utf-8")

    (verify / "ip_contract.json").write_text(json.dumps({
        "capabilities": [
            {"id": "backpressure", "sources": ["cycle_model.backpressure"],
             "evidence": ["stall without dropping bytes"]},
            {"id": "fsm_state", "sources": ["fsm"], "evidence": ["declared FSM"]},
        ],
        "required_evidence": [1, 2, 3],
        "required_monitors": [1],
        "required_mutations": [],
        "interfaces": [1, 2],
        "source_artifacts": [f"yaml/{ip}.ssot.yaml"],
    }), encoding="utf-8")
    (signoff / "contract_check.json").write_text(json.dumps({
        "status": "pass",
        "summary": {"reflection_passed": 5, "reflection_total": 5},
    }), encoding="utf-8")
    (signoff / "evidence_contract_coverage.json").write_text(json.dumps({
        "status": "pass",
        "summary": {"passed": 2, "failed": 0, "total": 2},
        "obligations": [
            {"obligation_id": "OBL_ALPHA_001", "status": "pass",
             "matched_rows": [{"goal_id": "EQ_A", "scenario_id": "SC_1"}],
             "condition_results": {"c1": True, "c2": True}},
            {"obligation_id": "OBL_BETA_002", "status": "pass",
             "matched_rows": [{"goal_id": "EQ_B", "scenario_id": "SC_2"}],
             "condition_results": {"c1": True}},
        ],
    }), encoding="utf-8")
    (signoff / "ip_signoff.json").write_text(json.dumps({
        "status": "fail",
        "gates": [
            {"name": "ssot", "status": "pass", "summary": "SSOT parses"},
            {"name": "contract_sim_freshness", "status": "fail",
             "summary": "sim evidence stale"},
        ],
    }), encoding="utf-8")


def test_req_export_renders_full_bundle_inline(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_req_bundle(tmp_path, "req_demo_ip")

    resp = client.get("/api/req/export?ip=req_demo_ip&format=html&inline=1&variant=full")

    assert resp.status_code == 200, resp.text
    assert "text/html" in resp.headers.get("content-type", "")
    assert resp.headers.get("content-disposition", "").startswith("inline;")
    body = resp.text
    assert body.lstrip().lower().startswith("<!doctype html>")
    # all four user-named pillars + lock are present
    assert "Requirements" in body
    assert "Obligations" in body
    assert "Capability Contract" in body
    assert "Evidence &amp; Sign-off" in body
    assert "Approval &amp; Locked Truth" in body  # full variant only
    # real data made it through
    assert "OBL_ALPHA_001" in body
    assert "/2 pass" in body  # obligations summary: <b>2</b>/2 pass
    assert "backpressure" in body
    assert "contract_sim_freshness" in body
    assert "Example Requirements" in body  # markdown rendered
    # rendered file persisted under doc/
    assert (tmp_path / "req_demo_ip" / "doc" / "req_demo_ip_req.html").is_file()


def test_req_export_core4_omits_approval_section(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_req_bundle(tmp_path, "req_demo_ip")

    resp = client.get("/api/req/export?ip=req_demo_ip&format=html&inline=1&variant=core4")

    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "Approval &amp; Locked Truth" not in body  # no approval section
    assert ">approved<" in body  # lock still shown as header badge (CSS uppercases)
    assert "Requirements" in body
    assert "Obligations" in body


def test_req_export_rejects_bad_variant_and_format(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_req_bundle(tmp_path, "req_demo_ip")

    assert client.get("/api/req/export?ip=req_demo_ip&variant=bogus").status_code == 400
    assert client.get("/api/req/export?ip=req_demo_ip&format=pdf").status_code == 400


def test_render_req_html_handles_empty_bundle(tmp_path):
    # An IP with no req/verify/signoff artifacts still renders without raising.
    (tmp_path / "bare_ip").mkdir()
    bundle = load_req_bundle(tmp_path / "bare_ip", "bare_ip")
    html_full = render_req_html(bundle, "bare_ip", "full")
    html_core = render_req_html(bundle, "bare_ip", "core4")
    assert "bare_ip" in html_full
    assert "no requirements document" in html_full
    assert "Approval &amp; Locked Truth" not in html_core
