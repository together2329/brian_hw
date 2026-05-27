"""Tests for the SSOT export pipeline: yaml -> md / docx / html.

Run with:
    cd common_ai_agent
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_export.py -v
"""

from __future__ import annotations

import shutil
import xml.etree.ElementTree as ET
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
    if not src.is_file():
        src = REPO_ROOT / "ip_examples" / src_ip / "yaml" / f"{src_ip}.ssot.yaml"
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


def _docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    return "\n".join(node.text or "" for node in root.findall(".//w:t", ns))


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
    html = atlas_ui._ssot_to_html(md, ip, data)
    assert html.startswith("<!DOCTYPE html>"), "html missing doctype"
    assert "<h1" in html and f">{ip}</h1>" in html, "h1 tag with ip name missing"
    assert "<table>" in html, "expected at least one table"

    # Complex diagram-like sections stay as raw source until a renderer is
    # stable enough to avoid clipping/truncation in the DOC iframe.
    assert "fsm" in data, f"sample {ip} unexpectedly lacks an fsm section"
    assert '<div class="fsm-flow-map"' not in html
    assert "stateDiagram" not in html
    assert "/vendor/mermaid.min.js" not in html
    assert "window.__ssotRenderMermaid" not in html
    assert "<pre><code class=\"language-yaml\">" in html

    # Block diagrams were too easy to render as clipped/broken approximations;
    # the DOC export prefers the source contract over misleading graphics.
    import re as _re

    top_match = _re.search(r"<h2\b[^>]*>\s*Top Module\s*</h2>", html, _re.IGNORECASE)
    assert top_match, "Top Module heading missing from html"
    assert "<h3>Block Diagram</h3>" not in html
    assert "<h2>Design Views</h2>" not in html


def test_block_diagram_renders_interfaces_as_arrow_lanes():
    data = {
        "top_module": {"name": "demo_dma", "description": "demo top"},
        "sub_modules": [{"name": "csr"}, {"name": "mm2s"}, {"name": "s2mm"}],
        "io_list": {
            "interfaces": [
                {
                    "name": "s_axi_lite",
                    "type": "AXI4-Lite",
                    "role": "slave",
                    "ports": [
                        {"name": "awvalid", "direction": "input"},
                        {"name": "rdata", "direction": "output"},
                    ],
                },
                {
                    "name": "m_axi_mm2s",
                    "type": "AXI4",
                    "role": "master",
                    "ports": [
                        {"name": "arvalid", "direction": "output"},
                        {"name": "rdata", "direction": "input"},
                    ],
                },
                {
                    "name": "irq_out",
                    "type": "custom",
                    "ports": [{"name": "irq", "direction": "output"}],
                },
            ],
        },
    }

    html = atlas_ui._ssot_html_block_diagram(data)

    assert "iface-link left flow-bi" in html
    assert "iface-link right flow-bi" in html
    assert "iface-link right flow-out" in html
    assert "iface-chip" not in html
    assert "no input-side interface declared" not in html


@pytest.mark.parametrize("ip", SAMPLE_IPS)
def test_html_register_map_bit_field_tables(tmp_path, monkeypatch, ip):
    """The datasheet HTML must render the register map as clean bit-field tables."""
    import re as _re

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    _copy_sample_ssot(ip, tmp_path)
    data = atlas_ui._load_ssot_yaml(ip)
    # Both samples ship registers with fields; guard the precondition.
    registers = data.get("registers")
    assert isinstance(registers, dict) and registers.get("register_list"), (
        f"sample {ip} unexpectedly lacks registers.register_list"
    )

    md = atlas_ui._ssot_to_markdown(data, ip)
    html = atlas_ui._ssot_to_html(md, ip, data)

    # Rich register-map section replaces the plain markdown register table.
    assert "<h3>Register Map</h3>" in html, "Register Map section missing from html"
    # Bit-field table headers.
    assert "<th>Field</th><th>Bits</th>" in html, "Field/Bits table headers missing"
    assert "<table class=\"register-fields\">" in html, "register-fields table missing"
    # A multi-bit field must render as an `msb:lsb` range cell (e.g. 2:0 / 31:0).
    assert _re.search(r"<td>\d+:\d+</td>", html), "expected an msb:lsb bit range cell"
    # The plain markdown "Register List" sub-table body must be replaced.
    assert ">Register List<" not in html, "markdown register table should be replaced"


def test_bit_ranges_normalize_for_html_and_docx(tmp_path, monkeypatch):
    """Comma/list bit ranges render as clean msb:lsb ranges in both DOC outputs."""
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    data = {
        "top_module": {"name": "demo", "description": "demo top"},
        "registers": {"register_list": [
            {
                "name": "OPC",
                "offset": "0x00",
                "fields": [
                    {
                        "name": "common_opcode",
                        "bits": "39, 73",
                        "access": "ro",
                        "reset": "0x0",
                        "description": "Common opcode slice",
                    },
                    {
                        "name": "payload",
                        "bits": [7, 0],
                        "access": "rw",
                        "reset": "0x0",
                        "description": "Payload bits",
                    },
                ],
            },
        ]},
    }

    md = atlas_ui._ssot_to_markdown(data, "demo")
    html = atlas_ui._ssot_to_html(md, "demo", data)

    assert "<td>73:39</td>" in html
    assert "<td>35</td>" in html
    assert "39, 73" not in html

    docx_path = tmp_path / "demo.docx"
    atlas_ui._ssot_to_docx(data, "demo", docx_path)
    text = _docx_text(docx_path)
    assert "73:39" in text
    assert "39, 73" not in text


def test_html_datasheet_uses_readable_cards_for_behavior_models():
    data = {
        "top_module": {"name": "demo", "description": "demo top"},
        "function_model": {
            "purpose": "Executable contract.",
            "state_variables": [{"name": "mm2s_len", "reset": 0}],
            "transactions": [
                {
                    "id": "MM2S_TRANSFER",
                    "name": "mm2s_transfer",
                    "preconditions": [
                        "mm2s_status & 1 == 1",
                        "mm2s_len > 0",
                        "mm2s_sa is word-aligned",
                    ],
                    "inputs": ["memory_data at mm2s_sa"],
                    "output_rules": [
                        {"name": "strm_tdata", "port": "mm2s_tdata", "expr": "memory_data", "width": 32},
                        {"name": "strm_tvalid", "port": "mm2s_tvalid", "expr": "1", "width": 1},
                    ],
                    "state_updates": [
                        {"name": "mm2s_sa", "expr": "mm2s_sa + (DATA_WIDTH // 8)", "width": 32},
                    ],
                    "side_effects": ["IOC bit asserted on final beat"],
                }
            ],
        },
        "cycle_model": {
            "clock": "aclk",
            "pipeline": [
                {"stage": "AR issue", "cycle": 0, "action": "Drive read address"},
                {"stage": "R capture", "cycle": 1, "action": "Capture memory beat"},
                {"stage": "AXI-Stream output", "cycle": 2, "ready": "tready applies backpressure"},
            ],
            "backpressure": ["Hold tdata/tvalid stable while tready is low."],
        },
        "fsm": {
            "machines": [{
                "name": "s2mm_engine",
                "reset_state": "S2MM_IDLE",
                "transitions": [
                    {"from": "S2MM_IDLE", "to": "S2MM_ACCEPT_STREAM", "condition": "s2mm_control_start"},
                    {"from": "S2MM_ACCEPT_STREAM", "to": "S2MM_AW_ISSUE", "condition": "tvalid and tready"},
                ],
            }],
        },
    }

    md = atlas_ui._ssot_to_markdown(data, "demo")
    html = atlas_ui._ssot_to_html(md, "demo", data)

    assert 'class="transaction-card"' not in html
    assert 'class="transaction-grid"' not in html
    assert 'class="cycle-flow"' not in html
    assert 'class="cycle-stage"' not in html
    assert 'class="fsm-flow-map"' not in html
    assert "MM2S_TRANSFER" in html
    assert "output_rules:" in html
    assert "pipeline:" in html
    assert "reset_state: S2MM_IDLE" in html
    assert "stateDiagram-v2" not in html


def test_custom_blocks_render_after_anchor_sections(tmp_path, monkeypatch):
    """SSOT custom_blocks (markdown/mermaid; inline or file) inject after their
    anchor section in the HTML datasheet; path traversal is rejected."""
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    (tmp_path / "demo" / "doc").mkdir(parents=True, exist_ok=True)
    (tmp_path / "demo" / "doc" / "flow.mmd").write_text(
        "stateDiagram-v2\n[*] --> A\nA --> B\n", encoding="utf-8")
    data = {
        "top_module": {"name": "demo", "description": "demo top"},
        "registers": {"register_list": [
            {"name": "R0", "offset": 0, "fields": [{"name": "en", "lsb": 0, "width": 1}]},
        ]},
        "custom_blocks": [
            {"after": "top_module", "title": "Arch note", "type": "markdown", "inline": "**bold** note"},
            {"after": "registers", "title": "Flow", "type": "mermaid", "file": "demo/doc/flow.mmd"},
            {"after": "top_module", "type": "html", "file": "../escape.html"},
        ],
    }
    md = atlas_ui._ssot_to_markdown(data, "demo")
    html = atlas_ui._ssot_to_html(md, "demo", data)
    # markdown block rendered and placed after the Top Module heading.
    assert "<strong>bold</strong>" in html
    assert html.find("Top Module") < html.find("Arch note")
    # mermaid FILE is shown as raw source, not auto-rendered into a fragile SVG.
    assert 'class="mermaid-source"' in html and "stateDiagram-v2" in html
    assert 'class="mermaid"' not in html
    assert "../../vendor/mermaid.min.js" not in html
    assert html.find("Registers") < html.find("Flow")
    # path traversal (../) is rejected -> "not found", never embedded.
    assert "not found" in html


def test_ssot_doc_feedback_updates_yaml_and_export(tmp_path, monkeypatch):
    import yaml

    ip = "doc_feedback_ip"
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True, exist_ok=True)
    ssot_path.write_text(
        yaml.safe_dump({
            "top_module": {"name": ip, "description": "demo top"},
            "custom": {},
        }, sort_keys=False),
        encoding="utf-8",
    )
    client = _make_client(tmp_path, monkeypatch)

    response = client.post("/api/ssot/doc-feedback", json={
        "ip": ip,
        "section": "top_module",
        "field": "review_note",
        "value": "Reset policy needs W1C detail.",
        "comment": "Please show this near top module.",
    })

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["path"] == "top_module.review_note"

    saved = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    assert saved["top_module"]["review_note"] == "Reset policy needs W1C detail."
    feedback = saved["custom"]["atlas_doc_feedback"]
    assert feedback[0]["comment"] == "Please show this near top module."
    blocks = saved["custom_blocks"]
    assert blocks[-1]["after"] == "top_module"
    assert "Reset policy needs W1C detail." in blocks[-1]["inline"]

    html_response = client.get(f"/api/ssot/export?ip={ip}&format=html&inline=1")
    assert html_response.status_code == 200, html_response.text
    assert "Doc Feedback: review_note" in html_response.text
    assert "Please show this near top module." in html_response.text


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
    text = _docx_text(out_path)
    block_idx = text.find("Block Diagram")
    features_idx = text.find("Features")
    assert block_idx != -1, "Block Diagram heading missing from docx"
    assert features_idx == -1 or block_idx < features_idx, "Block Diagram should render before Features"


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
