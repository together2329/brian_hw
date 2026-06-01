from pathlib import Path

import yaml
from fastapi.testclient import TestClient

import src.atlas_ui as atlas_ui


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


def _write_ssot(root: Path, ip: str) -> Path:
    path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "top_module": {
                    "name": ip,
                    "file": f"rtl/{ip}.sv",
                    "description": "Demo top for DOC feedback.",
                },
                "sub_modules": [
                    {"name": "csr", "description": "CSR block"},
                ],
                "io_list": {
                    "interfaces": [
                        {
                            "name": "apb",
                            "type": "APB",
                            "role": "slave",
                            "ports": [{"name": "pclk", "direction": "input", "width": 1}],
                        },
                    ],
                },
                "registers": {
                    "register_list": [
                        {
                            "name": "CTRL",
                            "offset": "0x00",
                            "fields": [
                                {
                                    "name": "enable",
                                    "bits": [0, 0],
                                    "access": "rw",
                                    "description": "Enable transfer",
                                },
                            ],
                        },
                    ],
                },
                "custom": {
                    "atlas_doc_feedback": [
                        {
                            "id": "fb_1",
                            "path": "registers.register_list.0.fields.0.description",
                            "comment": "Clarify enable timing.",
                            "source": "ssot-doc",
                        },
                    ],
                },
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return path


def test_doc_source_lookup_returns_top_level_section(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_ssot(tmp_path, "doc_source_ip")

    response = client.get("/api/ssot/doc-source?ip=doc_source_ip&path=top_module")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["section"] == "top_module"
    assert payload["path"] == "top_module"
    assert payload["kind"] == "section"
    assert payload["label"] == "Top Module"
    assert payload["value"]["name"] == "doc_source_ip"
    assert "description: Demo top for DOC feedback." in payload["yaml"]


def test_doc_source_lookup_returns_nested_register_field(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_ssot(tmp_path, "doc_source_ip")

    response = client.get(
        "/api/ssot/doc-source"
        "?ip=doc_source_ip&path=registers.register_list.0.fields.0.description"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["section"] == "registers"
    assert payload["path"] == "registers.register_list.0.fields.0.description"
    assert payload["kind"] == "register_field"
    assert payload["label"] == "CTRL.enable.description"
    assert payload["value"] == "Enable transfer"
    assert "Enable transfer" in payload["yaml"]
    assert payload["feedback"][0]["comment"] == "Clarify enable timing."


def test_doc_source_lookup_rejects_invalid_path(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_ssot(tmp_path, "doc_source_ip")

    response = client.get("/api/ssot/doc-source?ip=doc_source_ip&path=../../.env")

    assert response.status_code == 400
    assert "path must use dot notation" in response.json()["error"]


def test_doc_source_lookup_requires_existing_ip_and_path(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)

    no_ip = client.get("/api/ssot/doc-source?ip=missing_ip&path=top_module")
    no_path = client.get("/api/ssot/doc-source?ip=missing_ip")

    assert no_ip.status_code == 404
    assert no_path.status_code == 400


def test_html_export_marks_selectable_doc_components(tmp_path, monkeypatch):
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    _write_ssot(tmp_path, "doc_source_ip")
    data = atlas_ui._load_ssot_yaml("doc_source_ip")
    html = atlas_ui._ssot_to_html(atlas_ui._ssot_to_markdown(data, "doc_source_ip"), "doc_source_ip", data)

    assert 'data-ssot-section="top_module"' in html
    assert 'data-ssot-path="top_module"' in html
    assert 'data-ssot-path="registers.register_list.0"' in html
    assert 'data-ssot-kind="register"' in html
    assert 'data-ssot-path="registers.register_list.0.fields.0"' in html
    assert 'data-ssot-kind="register_field"' in html


def test_doc_feedback_comment_only_does_not_overwrite_selected_mapping(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    ssot_path = _write_ssot(tmp_path, "doc_source_ip")

    response = client.post("/api/ssot/doc-feedback", json={
        "ip": "doc_source_ip",
        "section": "top_module",
        "path": "top_module",
        "comment": "Top-module intro is unclear.",
    })

    assert response.status_code == 200, response.text
    saved = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    assert isinstance(saved["top_module"], dict)
    assert saved["top_module"]["name"] == "doc_source_ip"
    assert saved["custom"]["atlas_doc_feedback"][-1]["comment"] == "Top-module intro is unclear."


def test_doc_feedback_value_on_selected_object_writes_review_note_without_clobber(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    ssot_path = _write_ssot(tmp_path, "doc_source_ip")

    response = client.post("/api/ssot/doc-feedback", json={
        "ip": "doc_source_ip",
        "section": "top_module",
        "path": "top_module",
        "value": "Document intro should call out reset defaults.",
        "comment": "Use this as a doc review note.",
    })

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["path"] == "top_module.review_note"
    saved = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    assert isinstance(saved["top_module"], dict)
    assert saved["top_module"]["name"] == "doc_source_ip"
    assert saved["top_module"]["review_note"] == "Document intro should call out reset defaults."


def test_doc_feedback_field_on_selected_object_appends_field_without_clobber(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    ssot_path = _write_ssot(tmp_path, "doc_source_ip")

    response = client.post("/api/ssot/doc-feedback", json={
        "ip": "doc_source_ip",
        "section": "registers",
        "path": "registers.register_list.0.fields.0",
        "field": "description",
        "value": "Enable bit arms packet acceptance.",
        "comment": "Update field description from DOC feedback.",
    })

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["path"] == "registers.register_list.0.fields.0.description"
    saved = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    field = saved["registers"]["register_list"][0]["fields"][0]
    assert isinstance(field, dict)
    assert field["name"] == "enable"
    assert field["description"] == "Enable bit arms packet acceptance."
