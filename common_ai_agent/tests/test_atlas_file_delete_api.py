import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _create_app(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    from src import atlas_ui

    atlas_ui.PROJECT_ROOT = tmp_path
    return atlas_ui.create_app()


def _authenticated_client(app) -> TestClient:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"username": "fileuser", "password": "pw"},
    )
    assert response.status_code == 200, response.text
    return client


def test_file_delete_is_ip_scoped_and_file_only(tmp_path: Path, monkeypatch):
    alpha = tmp_path / "alpha"
    beta = tmp_path / "beta"
    (alpha / "rtl").mkdir(parents=True)
    beta.mkdir()
    target = alpha / "rtl" / "scratch.log"
    sibling = beta / "keep.log"
    target.write_text("delete me\n", encoding="utf-8")
    sibling.write_text("keep me\n", encoding="utf-8")

    client = _authenticated_client(_create_app(tmp_path, monkeypatch))

    # /api/file was renamed to /api/file/delete by Phase 9 of
    # refactor/atlas-modular (the file API cluster moved to atlas_api_files.py
    # via a factory). /api/file now exists as GET only; DELETE lives at
    # /api/file/delete. Test semantics (ip-scoped, file-only, no escape)
    # are unchanged.
    ok = client.delete("/api/file/delete", params={"ip": "alpha", "path": "alpha/rtl/scratch.log"})
    assert ok.status_code == 200, ok.text
    assert ok.json() == {"deleted": True, "ip": "alpha", "path": "alpha/rtl/scratch.log"}
    assert not target.exists()

    outside = client.delete("/api/file/delete", params={"ip": "alpha", "path": "beta/keep.log"})
    assert outside.status_code == 400
    assert sibling.exists()

    directory = client.delete("/api/file/delete", params={"ip": "alpha", "path": "alpha/rtl"})
    assert directory.status_code == 400
    assert (alpha / "rtl").is_dir()

    escape = client.delete("/api/file/delete", params={"ip": "alpha", "path": "alpha/../beta/keep.log"})
    assert escape.status_code == 400
    assert sibling.read_text(encoding="utf-8") == "keep me\n"
