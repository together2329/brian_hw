"""End-to-end multi-tenant authorization (audit B1) through the real create_app.

Boots the actual FastAPI app, registers two real users, gives each ownership of
their own IP via a session namespace (the authoritative source the gate uses),
and asserts cross-user isolation through the real adapter (_authz_owned_ips ->
db.list_sessions) on the real /api/file* + /git/ handlers — not a hand-built
stub. This is the regression guard for the read/write gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)


def _own_ip(username: str, ip: str, workflow: str = "rtl-gen") -> None:
    from core.atlas_db import AtlasDB

    with AtlasDB() as db:
        user = db.get_user_by_username(username)
        assert user, f"user {username!r} not found"
        sess = db.create_session(user["id"], f"{ip} session")
        db._execute(
            "UPDATE sessions SET namespace = ? WHERE id = ?",
            (f"{username}/{ip}/{workflow}", sess["id"]),
        )


@pytest.fixture()
def app_clients(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("ATLAS_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    for ip in ("alpha", "beta"):
        (tmp_path / ip / "rtl").mkdir(parents=True)
        (tmp_path / ip / "rtl" / "top.sv").write_text(f"module {ip}; endmodule\n")

    app = atlas_ui.create_app()

    alice = TestClient(app)
    assert alice.post("/api/auth/register", json={"username": "alice", "password": "pw"}).status_code == 200
    bob = TestClient(app)
    assert bob.post("/api/auth/register", json={"username": "bob", "password": "pw"}).status_code == 200
    _own_ip("alice", "alpha")
    _own_ip("bob", "beta")
    anon = TestClient(app)
    return alice, bob, anon


def test_owner_reads_own_ip(app_clients):
    alice, _, _ = app_clients
    r = alice.get("/api/file", params={"path": "alpha/rtl/top.sv"})
    assert r.status_code == 200 and "module alpha" in r.json()["content"]


def test_cross_user_read_denied(app_clients):
    alice, bob, _ = app_clients
    # alice cannot read bob's IP
    assert alice.get("/api/file", params={"path": "beta/rtl/top.sv"}).status_code == 403
    # bob CAN read his own
    assert bob.get("/api/file", params={"path": "beta/rtl/top.sv"}).status_code == 200
    # ...and not alice's
    assert bob.get("/api/file", params={"path": "alpha/rtl/top.sv"}).status_code == 403


def test_cross_user_vcd_and_source_denied(app_clients):
    alice, _, _ = app_clients
    assert alice.get("/api/vcd/raw", params={"path": "beta/rtl/top.sv"}).status_code == 403
    assert alice.get("/api/source", params={"path": "beta/rtl/top.sv"}).status_code == 403
    # own IP source is fine
    assert alice.get("/api/source", params={"path": "alpha/rtl/top.sv"}).status_code == 200


def test_listing_filtered_per_user(app_clients):
    alice, _, _ = app_clients
    entries = alice.get("/api/files", params={"path": ""}).json()["entries"]
    names = {e["name"] for e in entries}
    assert "alpha" in names      # own IP
    assert "beta" not in names   # other tenant's IP hidden


def test_unauthenticated_blocked(app_clients):
    _, _, anon = app_clients
    # AuthMiddleware 401s non-public API for anonymous callers
    assert anon.get("/api/file", params={"path": "alpha/rtl/top.sv"}).status_code == 401


def test_git_default_blocks_anon_clone_in_multiuser(app_clients):
    # SECURITY (review [9]): ATLAS_GIT_ANON_READ is UNSET and the fixture runs
    # multi-user, so anonymous fetch/clone of any tenant's bare repo is blocked
    # by default (AuthMiddleware 401) — anonymous cross-tenant read was a leak.
    # PUSH is always gated.
    _, _, anon = app_clients
    assert anon.get("/git/alpha.git/info/refs",
                    params={"service": "git-upload-pack"}).status_code == 401
    assert anon.get("/git/alpha.git/info/refs",
                    params={"service": "git-receive-pack"}).status_code in (401, 403)


def test_git_anon_read_explicit_opt_in_allows_clone(app_clients, monkeypatch):
    # ATLAS_GIT_ANON_READ=1 is an explicit operator opt-in that restores
    # anonymous fetch/clone even in multi-user. The bare repo isn't built in
    # the fixture so the backend 404s, but auth does NOT block -> NOT 401/403.
    # PUSH stays gated.
    _, _, anon = app_clients
    monkeypatch.setenv("ATLAS_GIT_ANON_READ", "1")
    assert anon.get("/git/alpha.git/info/refs",
                    params={"service": "git-upload-pack"}).status_code not in (401, 403)
    assert anon.get("/git/alpha.git/info/refs",
                    params={"service": "git-receive-pack"}).status_code in (401, 403)


def test_symlink_into_other_ip_denied(app_clients, tmp_path):
    # SECURITY (review #1): a symlink inside an OWNED ip pointing at a victim ip
    # must not bypass the gate — the gate authorizes the RESOLVED path.
    alice, _, _ = app_clients
    link = tmp_path / "alpha" / "peek"
    link.symlink_to(tmp_path / "beta", target_is_directory=True)
    r = alice.get("/api/file", params={"path": "alpha/peek/rtl/top.sv"})
    assert r.status_code == 403


def test_git_anon_read_disabled_restores_gating(app_clients, monkeypatch):
    # ATLAS_GIT_ANON_READ=0 -> /git/ requires auth + per-IP authorization again.
    alice, _, anon = app_clients
    monkeypatch.setenv("ATLAS_GIT_ANON_READ", "0")
    fetch = {"service": "git-upload-pack"}
    # anonymous fetch blocked upstream by AuthMiddleware
    assert anon.get("/git/alpha.git/info/refs", params=fetch).status_code == 401
    # authenticated but cross-user (alice does not own beta) -> 403
    assert alice.get("/git/beta.git/info/refs", params=fetch).status_code == 403
    # authenticated owner passes the gate (backend 404 since no bare repo built)
    assert alice.get("/git/alpha.git/info/refs", params=fetch).status_code not in (401, 403)
    # push always gated
    assert anon.get("/git/alpha.git/info/refs",
                    params={"service": "git-receive-pack"}).status_code in (401, 403)


def test_sim_debug_cluster_cross_user_denied(app_clients):
    # SECURITY (review #2): the whole sim_debug cluster must be IP-gated.
    alice, _, _ = app_clients
    assert alice.get("/api/cocotb", params={"ip": "beta"}).status_code == 403
    assert alice.get("/api/debug/scenarios", params={"ip": "beta"}).status_code == 403
    assert alice.get("/api/sim_debug/intent", params={"ip": "beta"}).status_code == 403
    assert alice.get("/api/hierarchy", params={"top": "x", "ip": "beta"}).status_code == 403
    # own IP is not denied by the gate (may 404/400 downstream, but not 403)
    assert alice.get("/api/cocotb", params={"ip": "alpha"}).status_code != 403


def test_ip_git_rest_endpoints_cross_user_denied(app_clients):
    # SECURITY (review [0], critical): the per-IP git REST endpoints resolve
    # the target from an attacker-supplied session_id and previously skipped
    # the ownership gate — a cross-tenant working-tree write (hard reset) /
    # history leak. They must now 403 a non-owner.
    alice, _, _ = app_clients
    victim = {"session_id": "bob/beta/rtl-gen", "hash": "0" * 40}
    assert alice.post("/api/ip/beta/git/revert", json=victim).status_code == 403
    assert alice.post("/api/ip/beta/git/commit", json={"session_id": "bob/beta/rtl-gen"}).status_code == 403
    assert alice.get("/api/ip/beta/git/log", params={"session_id": "bob/beta/rtl-gen"}).status_code == 403
    assert alice.get("/api/ip/beta/git/graph", params={"session_id": "bob/beta/rtl-gen"}).status_code == 403
    # own IP passes the gate (downstream may 404/409, but never 403)
    assert alice.get("/api/ip/alpha/git/log").status_code != 403


def test_ip_report_endpoints_cross_user_denied(app_clients):
    # SECURITY (review [7][8]): per-IP report endpoints must IP-gate so a
    # non-owner can neither read another tenant's artifacts nor trigger
    # compute against their IP.
    alice, _, _ = app_clients
    assert alice.get("/api/lint/report", params={"ip": "beta"}).status_code == 403
    assert alice.get("/api/coverage/report", params={"ip": "beta"}).status_code == 403
    assert alice.get("/api/ssot-gates/beta").status_code == 403
    assert alice.get("/api/lint/report", params={"ip": "alpha"}).status_code != 403


def test_workspace_download_blocks_cross_tenant_and_whole_tree(app_clients):
    # SECURITY (review [2], critical): the zip endpoint streamed any tenant's
    # tree with no ownership check. A subpath into another tenant is denied,
    # and the whole-tree default is refused in multi-user mode.
    alice, _, anon = app_clients
    assert anon.get("/api/workspace/download.zip").status_code == 401
    assert alice.get("/api/workspace/download.zip").status_code == 403
    assert alice.get("/api/workspace/download.zip", params={"subpath": "beta"}).status_code == 403


def test_settings_endpoints_admin_only_in_multiuser(app_clients):
    # SECURITY (review [6]): /api/settings/* persists global LLM config for
    # every tenant, so a non-admin must be rejected in multi-user mode.
    alice, _, _ = app_clients
    assert alice.post("/api/settings/model", json={"key": "profile:kimi"}).status_code in (401, 403)
    assert alice.post("/api/settings/reasoning-effort", json={"effort": "med"}).status_code in (401, 403)
