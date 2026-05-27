from pathlib import Path

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


def _write_minimal_ssot(root: Path, ip: str) -> Path:
    yaml_dir = root / ip / "yaml"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    path = yaml_dir / f"{ip}.ssot.yaml"
    path.write_text(
        f"""top_module:
  name: {ip}
  file: rtl/{ip}.sv
  type: rtl
  description: Minimal inline export test IP
sub_modules:
  - name: cfg_regs
    description: APB-visible register block
  - name: counter_core
    description: Counter datapath and control FSM
io_list:
  interfaces:
    - name: apb
      type: APB
      role: slave
      ports:
        - name: pclk
          direction: input
          width: 1
        - name: prdata
          direction: output
          width: 32
features:
  - id: F_COUNTER
    description: Minimal counter feature
fsm:
  machines:
    - name: main_fsm
      reset_state: IDLE
      states:
        - name: IDLE
          description: Wait for enable
        - name: RUN
          description: Count cycles
      transitions:
        - from: IDLE
          condition: enable
          to: RUN
        - from: RUN
          condition: disable
          to: IDLE
timing:
  diagrams:
    - name: apb_write
      signals:
        - name: psel
          values: [0, 1, 1, 0]
        - name: penable
          values: [0, 0, 1, 0]
        - name: pready
          values: [0, 0, 1, 0]
""",
        encoding="utf-8",
    )
    return path


def test_export_endpoint_can_render_html_inline(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    _write_minimal_ssot(tmp_path, "inline_doc_ip")

    resp = client.get("/api/ssot/export?ip=inline_doc_ip&format=html&inline=1")

    assert resp.status_code == 200, resp.text
    assert "text/html" in resp.headers.get("content-type", "")
    assert resp.headers.get("content-disposition", "").startswith("inline;")
    assert resp.text.startswith("<!DOCTYPE html>")
    assert "<h2>Design Views</h2>" in resp.text
    assert "Block Diagram" in resp.text
    assert "FSM" in resp.text
    assert 'class="mermaid"' in resp.text
    assert "../../vendor/mermaid.min.js" in resp.text
    assert "/vendor/mermaid.min.js" in resp.text
    assert "window.__ssotRenderMermaid" in resp.text
    assert "mermaid.run" in resp.text
    assert "Timing Diagram" in resp.text
    assert (tmp_path / "inline_doc_ip" / "doc" / "inline_doc_ip_ssot.html").is_file()

    asset = client.get("/vendor/mermaid.min.js")
    assert asset.status_code == 200
    assert "javascript" in asset.headers.get("content-type", "")
