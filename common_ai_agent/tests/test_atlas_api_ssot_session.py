from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.atlas_api_ssot import register_ssot_routes


def _safe(root: Path, rel_path: str) -> Optional[Path]:
    target = (root / str(rel_path or "").lstrip("/")).resolve()
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

    register_ssot_routes(
        app,
        project_root=lambda: root,
        safe_path=lambda path: _safe(root, path),
        skip_dirs={".git", "__pycache__"},
        max_read_bytes=4096,
        valid_ip_name=lambda ip: bool(ip),
        active_ssot_ip=lambda: "demo_ip",
        ssot_qa_view=lambda *args, **kwargs: {},
        ssot_qa_sessions_view=lambda: {},
        ssot_qa_path=lambda *args, **kwargs: root / "qa.json",
        qa_slug=lambda text, fallback: fallback,
        upsert_ssot_qa_items=lambda *args, **kwargs: None,
        load_ssot_state=lambda ip: {},
        canonical_session_string=lambda ip: f"alice/s1/{ip}/ssot-gen",
        normalize_session_name=lambda session: str(session or "").strip("/"),
        append_session_message=lambda *args, **kwargs: None,
        bridge=SimpleNamespace(emit=lambda *args, **kwargs: None),
    )
    return TestClient(app)


def test_ssot_read_resolves_ip_local_path_inside_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    ssot = tmp_path / "alice" / "s1" / "demo_ip" / "yaml" / "demo_ip.ssot.yaml"
    ssot.parent.mkdir(parents=True)
    ssot.write_text("ip: demo_ip\n", encoding="utf-8")

    response = _client(tmp_path).get(
        "/api/ssot",
        params={
            "file": "yaml/demo_ip.ssot.yaml",
            "session_id": "alice/s1/demo_ip/rtl-gen",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "demo_ip/yaml/demo_ip.ssot.yaml"
    assert payload["content"] == "ip: demo_ip\n"


def test_ssot_read_accepts_ui_prefixed_workspace_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    ssot = tmp_path / "alice" / "s1" / "demo_ip" / "yaml" / "demo_ip.ssot.yaml"
    ssot.parent.mkdir(parents=True)
    ssot.write_text("ip: demo_ip\n", encoding="utf-8")

    response = _client(tmp_path).get(
        "/api/ssot",
        params={
            "file": "alice/s1/demo_ip/yaml/demo_ip.ssot.yaml",
            "session_id": "alice/s1/demo_ip/rtl-gen",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "demo_ip/yaml/demo_ip.ssot.yaml"
    assert payload["content"] == "ip: demo_ip\n"
