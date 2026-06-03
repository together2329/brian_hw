"""Integration test for the B1 read gate on the real /api/file* handlers.

Drives ``register_file_routes`` through Starlette's TestClient with an injected
``fs_authz`` adapter (mirroring the one ``atlas_ui.create_app`` builds) backed
by a fake ACL DB. Proves the gate end-to-end: cross-user reads 403, own/granted
reads 200, shared roots 200, admin bypass, unauthenticated 401, and that the
root listing is filtered (not 403'd) so the IP-rooted file tree keeps working.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("httpx")  # TestClient needs httpx
from starlette.testclient import TestClient  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from core import atlas_fs_authz as fsz  # noqa: E402
from src.atlas_api_files import register_file_routes  # noqa: E402


class FakeDB:
    """alpha -> alice, beta -> bob."""

    _IPS = {"alpha": "ip_a", "beta": "ip_b"}
    _OWNER = {"ip_a": "uid_alice", "ip_b": "uid_bob"}

    def get_ip_block_by_name(self, name):
        ip_id = self._IPS.get(name)
        return {"id": ip_id, "ip_name": name} if ip_id else None

    def can_user_access_ip(self, ip_id, user_id, permission="view"):
        return self._OWNER.get(ip_id) == user_id

    def list_accessible_ip_blocks(self, user_id, permission="view"):
        return [
            {"ip_name": name}
            for name, ip_id in self._IPS.items()
            if self._OWNER.get(ip_id) == user_id
        ]


USERS = {
    "alice": {"id": "uid_alice", "username": "alice", "role": "user"},
    "bob": {"id": "uid_bob", "username": "bob", "role": "user"},
    "admin": {"id": "uid_admin", "username": "admin", "role": "admin"},
}


def _make_fs_authz(db):
    def ident(request):
        user = request.scope.get("user") or {}
        return (
            str(user.get("id") or "default"),
            str(user.get("username") or ""),
            user.get("role") == "admin",
        )

    def path(request, rel, permission="view"):
        uid, uname, is_admin = ident(request)
        d = fsz.authorize_path(
            rel, user_id=uid, username=uname, is_admin=is_admin,
            multi_user=True, db=db, permission=permission,
        )
        return None if d.allow else JSONResponse({"error": d.reason}, status_code=d.status)

    def ip(request, ipname, permission="view"):
        uid, uname, is_admin = ident(request)
        d = fsz.authorize_ip(
            ipname, user_id=uid, username=uname, is_admin=is_admin,
            multi_user=True, db=db, permission=permission,
        )
        return None if d.allow else JSONResponse({"error": d.reason}, status_code=d.status)

    def acc(request):
        uid, uname, is_admin = ident(request)
        return fsz.accessible_ip_names(
            user_id=uid, is_admin=is_admin, multi_user=True, db=db
        )

    return SimpleNamespace(path=path, ip=ip, accessible_ips=acc, shared_roots=fsz.SHARED_ROOTS)


@pytest.fixture()
def client(tmp_path: Path):
    root = tmp_path.resolve()
    (root / "alpha").mkdir()
    (root / "alpha" / "top.sv").write_text("module a; endmodule")
    (root / "beta").mkdir()
    (root / "beta" / "top.sv").write_text("module b; endmodule")
    (root / "rtl").mkdir()
    (root / "rtl" / "shared.sv").write_text("shared rtl")
    (root / ".session" / "bob").mkdir(parents=True)
    (root / ".session" / "bob" / "conv.json").write_text('{"secret": true}')

    def safe(rel):
        rel = (rel or "").lstrip("/")
        cand = (root / rel).resolve()
        try:
            cand.relative_to(root)
        except ValueError:
            return None
        return cand

    app = FastAPI()

    @app.middleware("http")
    async def _attach_user(request, call_next):
        request.scope["user"] = USERS.get(request.headers.get("x-test-user"))
        return await call_next(request)

    register_file_routes(
        app,
        safe_path_fn=safe,
        project_root=root,
        skip_dirs=set(),
        is_hidden_artifact_fn=lambda c, t: False,
        max_read_bytes=100_000,
        safe_ip_delete_fn=lambda ip, p: (None, "unsupported"),
        bridge=SimpleNamespace(emit=lambda *a, **k: None),
        fs_authz=_make_fs_authz(FakeDB()),
    )
    return TestClient(app)


def _h(user):
    return {"x-test-user": user} if user else {}


# --- single-file reads --------------------------------------------------- #

def test_owner_reads_own_ip(client):
    r = client.get("/api/file", params={"path": "alpha/top.sv"}, headers=_h("alice"))
    assert r.status_code == 200 and "module a" in r.json()["content"]


def test_cross_user_ip_read_403(client):
    r = client.get("/api/file", params={"path": "beta/top.sv"}, headers=_h("alice"))
    assert r.status_code == 403


def test_cross_user_session_read_403(client):
    r = client.get("/api/file", params={"path": ".session/bob/conv.json"}, headers=_h("alice"))
    assert r.status_code == 403


def test_shared_root_read_200(client):
    r = client.get("/api/file", params={"path": "rtl/shared.sv"}, headers=_h("alice"))
    assert r.status_code == 200


def test_admin_reads_any_ip(client):
    r = client.get("/api/file", params={"path": "beta/top.sv"}, headers=_h("admin"))
    assert r.status_code == 200


def test_unauthenticated_401(client):
    r = client.get("/api/file", params={"path": "alpha/top.sv"})
    assert r.status_code == 401


def test_raw_cross_user_403(client):
    r = client.get("/api/file/raw", params={"path": "beta/top.sv"}, headers=_h("alice"))
    assert r.status_code == 403


def test_fold_symbols_cross_user_403(client):
    r = client.get("/api/fold-symbols", params={"path": "beta/top.sv"}, headers=_h("alice"))
    assert r.status_code == 403


# --- directory listing is filtered, not 403'd ---------------------------- #

def test_root_listing_filtered_for_owner(client):
    r = client.get("/api/files", params={"path": ""}, headers=_h("alice"))
    assert r.status_code == 200
    names = {e["name"] for e in r.json()["entries"]}
    assert "alpha" in names      # own IP visible
    assert "rtl" in names        # shared root visible
    assert "beta" not in names   # other tenant's IP hidden
    assert ".session" not in names  # hidden dotfile never listed


def test_listing_into_other_ip_403(client):
    r = client.get("/api/files", params={"path": "beta"}, headers=_h("alice"))
    assert r.status_code == 403


def test_admin_listing_unfiltered(client):
    r = client.get("/api/files", params={"path": ""}, headers=_h("admin"))
    names = {e["name"] for e in r.json()["entries"]}
    assert {"alpha", "beta", "rtl"} <= names
