"""Entry-document cache-control contract.

The built Vite dist references content-hashed asset filenames. If the browser
is allowed to cache the entry HTML (index.vite.html / lobby.vite.html), a
returning client keeps booting an OLD entry that points at asset hashes which
no longer exist after a rebuild -> 404 -> blank app. The entry documents MUST
be served `no-store` so every load re-fetches the current shell (assets are
already no-store via _NoCacheStatic).

Deterministic: builds a minimal fake dist in a tmp dir and drives the real
routes via TestClient — no skip-on-missing-dist (which would be a silent pass).
"""
from __future__ import annotations

from pathlib import Path

import pytest


def _make_fake_dist(root: Path) -> Path:
    dist = root / "frontend" / "atlas" / "dist"
    (dist / "assets").mkdir(parents=True)
    # a populated assets/ dir with at least one .js is required by the
    # _vite_index_html QA #5 partial-dist guard.
    (dist / "assets" / "app-TEST1234.js").write_text("// test asset\n", encoding="utf-8")
    (dist / "index.vite.html").write_text(
        "<!doctype html><html><head></head><body>index</body></html>", encoding="utf-8"
    )
    (dist / "lobby.vite.html").write_text(
        "<!doctype html><html><head></head><body>lobby</body></html>", encoding="utf-8"
    )
    return root / "frontend" / "atlas"


def _client(tmp_path, monkeypatch):
    # local-admin so the auth-gated /lobby is reachable; single-user keeps the
    # test independent of any multi-user DB state. is_local_admin_mode() reads
    # the env live per-request, so setenv here takes effect at request time.
    monkeypatch.setenv("ATLAS_LOCAL_ADMIN", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    import src.atlas_ui as aui
    try:
        from starlette.testclient import TestClient
    except Exception:  # pragma: no cover - starlette always present with fastapi
        from fastapi.testclient import TestClient  # type: ignore
    frontend = _make_fake_dist(tmp_path)
    monkeypatch.setattr(aui, "FRONTEND", frontend)
    app = aui.create_app()
    return TestClient(app)


def test_index_entry_html_is_no_store(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.get("/")
    assert r.status_code == 200, f"index served {r.status_code}, expected 200 with fake dist"
    cc = r.headers.get("cache-control", "").lower()
    assert "no-store" in cc, f"index Cache-Control must be no-store, got {cc!r}"


def test_lobby_entry_html_is_no_store(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    r = client.get("/lobby")
    assert r.status_code == 200, f"lobby served {r.status_code}, expected 200 with fake dist"
    cc = r.headers.get("cache-control", "").lower()
    assert "no-store" in cc, f"lobby Cache-Control must be no-store, got {cc!r}"
