"""Tests for the REQ tab backend: GET /api/req/export.

Mirrors tests/test_ssot_inline_export_endpoint.py — build the app with a
multi-user client, lay down the canonical per-IP REQ (locked-truth) bundle on
disk, and assert the aggregated HTML renders inline and is written to
<ip>/doc/<ip>_req.html. The bundle shape matches the normalized req/ layout
(requirements_index / obligations / contract_refs / evidence_plan /
approval_manifest / ssot_validation), cross-linked by id.
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
    req.mkdir(parents=True, exist_ok=True)

    (req / "requirements_index.json").write_text(json.dumps({
        "ip": ip, "schema_version": 1, "type": "requirements_index",
        "requirements": [
            {"requirement_id": "REQ_APB3", "title": "APB3 slave interface",
             "kind": "interface", "status": "locked", "required": True,
             "source": "user-interview", "obligation_refs": ["OBL_APB_READ"],
             "statement": "Control/status register access via APB3 slave."},
            {"requirement_id": "REQ_COUNTER", "title": "Count-up timer",
             "kind": "functional", "status": "locked", "required": True,
             "source": "grill-me", "obligation_refs": ["OBL_COUNTER_INCR"],
             "statement": "Two independent 32-bit count-up channels."},
        ],
    }), encoding="utf-8")
    (req / "obligations.json").write_text(json.dumps({
        "ip": ip, "schema_version": 1, "type": "obligations",
        "obligations": [
            {"obligation_id": "OBL_APB_READ", "status": "review_candidate",
             "requirement_refs": ["REQ_APB3"], "contract_refs": ["CR_APB_READ_PROTOCOL"],
             "statement": "APB3 read returns addressed register combinationally."},
            {"obligation_id": "OBL_COUNTER_INCR", "status": "review_candidate",
             "requirement_refs": ["REQ_COUNTER"], "contract_refs": ["CR_COUNTER_BEHAVIOR"],
             "statement": "Counter increments each enabled cycle."},
        ],
    }), encoding="utf-8")
    (req / "contract_refs.json").write_text(json.dumps({
        "ip": ip, "schema_version": 1, "type": "contract_refs",
        "contract_refs": [
            {"contract_ref_id": "CR_APB_READ_PROTOCOL", "kind": "protocol_assertion",
             "check_type": "simulation", "signal": "prdata",
             "signal_refs": ["psel", "penable", "prdata"], "obligation_refs": ["OBL_APB_READ"],
             "statement": "prdata valid in same cycle as psel=1 && penable=1 && pwrite=0."},
        ],
    }), encoding="utf-8")
    (req / "evidence_plan.json").write_text(json.dumps({
        "ip": ip, "schema_version": 1, "type": "evidence_plan",
        "evidence_plan": [
            {"evidence_id": "EV_APB_READ", "contract_ref": "CR_APB_READ_PROTOCOL",
             "validator": "SVA on prdata", "artifact": "sim/tb_top.sv",
             "pass_condition": "All APB reads return correct values, zero wait states."},
        ],
    }), encoding="utf-8")
    (req / "approval_manifest.json").write_text(json.dumps({
        "ip": ip, "schema_version": 1, "type": "starter_requirement_approval_manifest",
        "status": "requirements_locked", "approved_by": "brian",
        "approved_at_utc": "2026-06-06T07:42:23Z",
        "decision_note": "Locked after grill-me Q&A.",
        "bundle_sha256": "a" * 64,
        "requirements": [
            {"requirement_id": "REQ_APB3", "status": "locked", "required": True},
            {"requirement_id": "REQ_COUNTER", "status": "locked", "required": True},
        ],
    }), encoding="utf-8")
    (req / "ssot_validation.json").write_text(json.dumps({
        "schema_version": "ssot_validation.v2", "ip": ip, "mode": "engineering",
        "ok": False,
        "blockers": [
            {"severity": "blocker", "id": "preview.top_module.description",
             "path": "top_module.description",
             "message": "SSOT Preview Brief needs a concrete top-module description.",
             "fix": "Fill top_module.description from requirements."},
        ],
        "warnings": [],
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
    # all four pillars + lock section present
    assert "Requirements</h2>" in body
    assert "Obligations</h2>" in body
    assert "Contract References" in body
    assert "Evidence Plan" in body
    assert "Approval &amp; Locked Truth" in body  # full variant only
    # the cross-linked chain made it through (req -> obli -> contract -> evidence)
    assert "REQ_APB3" in body
    assert "OBL_APB_READ" in body
    assert "CR_APB_READ_PROTOCOL" in body
    assert "EV_APB_READ" in body
    assert "requirements_locked" in body
    # ssot validation blockers surfaced
    assert "top_module.description" in body
    # rendered file persisted under doc/
    assert (tmp_path / "req_demo_ip" / "doc" / "req_demo_ip_req.html").is_file()


def test_req_export_core4_omits_approval_section(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_req_bundle(tmp_path, "req_demo_ip")

    resp = client.get("/api/req/export?ip=req_demo_ip&format=html&inline=1&variant=core4")

    assert resp.status_code == 200, resp.text
    body = resp.text
    assert "Approval &amp; Locked Truth" not in body  # no approval section
    assert ">requirements_locked<" in body  # lock still shown as header badge
    assert "Requirements</h2>" in body
    assert "Obligations</h2>" in body


def test_req_export_rejects_bad_variant_and_format(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_req_bundle(tmp_path, "req_demo_ip")

    assert client.get("/api/req/export?ip=req_demo_ip&variant=bogus").status_code == 400
    assert client.get("/api/req/export?ip=req_demo_ip&format=pdf").status_code == 400


def test_render_req_html_handles_empty_bundle(tmp_path):
    # An IP with no req/ bundle still renders without raising.
    (tmp_path / "bare_ip").mkdir()
    bundle = load_req_bundle(tmp_path / "bare_ip", "bare_ip")
    html_full = render_req_html(bundle, "bare_ip", "full")
    html_core = render_req_html(bundle, "bare_ip", "core4")
    assert "bare_ip" in html_full
    assert "no requirements index" in html_full
    assert "no obligations" in html_full
    assert "Approval &amp; Locked Truth" not in html_core
