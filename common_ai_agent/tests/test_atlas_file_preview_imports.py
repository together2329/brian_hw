import base64
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

WORKSPACE_JSX = ROOT / "frontend" / "atlas" / "workspace.jsx"
ATLAS_UI_PY = ROOT / "src" / "atlas_ui.py"


def test_api_files_hides_import_image_cache_but_raw_serves_it(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip = tmp_path / "new_spi"
    image_dir = ip / "req" / "imports" / "images"
    originals_dir = ip / "req" / "imports" / "originals"
    image_dir.mkdir(parents=True)
    originals_dir.mkdir(parents=True)
    (ip / "req" / "imports" / "spec.md").write_text("# imported spec\n", encoding="utf-8")
    (originals_dir / "spec.pdf").write_bytes(b"%PDF-1.4\n% test\n")
    (image_dir / "noise.png").write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
    ))

    client = TestClient(atlas_ui.create_app())
    register = client.post("/api/auth/register", json={"username": "alice", "password": "pw"})
    assert register.status_code == 200, register.text
    listed = client.get("/api/files", params={"path": "new_spi", "recursive": 1, "max_depth": 5})

    assert listed.status_code == 200, listed.text
    names = {item["name"] for item in listed.json()["entries"]}
    assert "req/imports/spec.md" in names
    assert "req/imports/originals/spec.pdf" in names
    assert "req/imports/images/noise.png" not in names

    raw = client.get("/api/file/raw", params={"path": "new_spi/req/imports/images/noise.png"})
    assert raw.status_code == 200, raw.text
    assert raw.headers["content-type"].startswith("image/png")
    assert raw.content.startswith(b"\x89PNG")


def test_preview_pane_labels_binary_images_with_image_metadata():
    # PreviewPane was extracted from workspace.jsx into preview-pane.jsx by
    # Phase 13d of refactor/atlas-modular. The image-label markup (naturalWidth
    # readout, "file <span ...>", "Image preview failed..." fallback) lives in
    # preview-pane.jsx now; atlasFileTreeMetaForPath / atlasImageMimeForExt
    # remain in workspace.jsx (still consumed by other panes too).
    src = WORKSPACE_JSX.read_text(encoding="utf-8")
    preview_pane_src = (ROOT / "frontend" / "atlas" / "preview-pane.jsx").read_text(encoding="utf-8")
    combined = src + "\n" + preview_pane_src
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")

    assert "const atlasFileTreeMetaForPath = (rawPath)" in src
    assert "const atlasImageMimeForExt = (ext)" in src
    assert "naturalWidth" in combined
    assert "file <span" in combined
    assert "Image preview failed. Use copy path" in combined
    assert "resource.mtime || 0" in combined
    assert "flat tiny extracted image" in atlas_ui_src
    assert "filter_noise=True" in atlas_ui_src
