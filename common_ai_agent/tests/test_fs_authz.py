"""Unit tests for core.atlas_fs_authz — the multi-tenant read/write gate (B1).

Covers both halves of a fail-closed gate: it must DENY cross-user access and
must ALLOW legitimate access (own session, shared infra, owned/granted IPs,
admin, single-user mode). A gate that only over-blocks would pass a naive test
suite while breaking the app — so the allow-paths are asserted as carefully as
the deny-paths.
"""

from __future__ import annotations

import pytest

from core.atlas_fs_authz import (
    AuthzDecision,
    accessible_ip_names,
    authorize_ip,
    authorize_path,
    classify_segments,
)


class FakeDB:
    """Minimal AtlasDB stand-in.

    ``ips``    : {ip_name: ip_id}
    ``access`` : set of (ip_id, user_id) pairs allowed at >= the requested rank
    ``boom``   : ip_names whose lookup raises (to prove fail-closed)
    """

    def __init__(self, ips=None, access=None, boom=None):
        self._ips = dict(ips or {})
        self._access = set(access or set())
        self._boom = set(boom or set())

    def get_ip_block_by_name(self, name):
        if name in self._boom:
            raise RuntimeError("simulated DB failure")
        if name in self._ips:
            return {"id": self._ips[name], "ip_name": name}
        return None

    def can_user_access_ip(self, ip_id, user_id, permission="view"):
        return (ip_id, user_id) in self._access

    def list_accessible_ip_blocks(self, user_id, permission="view"):
        return [
            {"ip_name": name}
            for name, ip_id in self._ips.items()
            if (ip_id, user_id) in self._access
        ]


# alice owns ip "alpha"; bob owns "beta"; alice was granted view on "shared_ip".
def _db():
    return FakeDB(
        ips={"alpha": "ip_a", "beta": "ip_b", "shared_ip": "ip_s"},
        access={
            ("ip_a", "uid_alice"),
            ("ip_b", "uid_bob"),
            ("ip_s", "uid_alice"),  # grant
            ("ip_s", "uid_bob"),    # owner
        },
    )


# --------------------------------------------------------------------------- #
# classify_segments (pure)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "path,expected",
    [
        ("", "root"),
        ("/", "root"),
        ("../etc/passwd", "escape"),
        ("alpha/../beta/x", "escape"),
        (".session/alice/alpha/rtl-gen/conv.json", "session"),
        ("rtl/foo.sv", "shared"),
        ("doc/wiki/index.md", "shared"),
        ("soc.ssot.yaml", "shared"),
        ("alpha/rtl/top.sv", "ip"),
        ("beta", "ip"),
    ],
)
def test_classify_segments(path, expected):
    from core.atlas_fs_authz import _segments

    assert classify_segments(_segments(path)) == expected


# --------------------------------------------------------------------------- #
# authorize_path — deny paths
# --------------------------------------------------------------------------- #

def test_cross_user_ip_denied():
    # alice tries to read bob's IP "beta"
    d = authorize_path("beta/rtl/top.sv", user_id="uid_alice", username="alice", db=_db())
    assert not d.allow and d.status == 403


def test_cross_user_session_denied():
    d = authorize_path(
        ".session/bob/beta/rtl-gen/conversation.json",
        user_id="uid_alice",
        username="alice",
        db=_db(),
    )
    assert not d.allow and d.status == 403 and d.kind == "session"


def test_unregistered_ip_denied_fail_closed():
    # directory exists on disk but no ip_blocks row -> deny
    d = authorize_path("ghost_ip/rtl/x.sv", user_id="uid_alice", username="alice", db=_db())
    assert not d.allow and d.status == 403


def test_db_error_denies():
    db = FakeDB(ips={"alpha": "ip_a"}, access=set(), boom={"alpha"})
    d = authorize_path("alpha/x.sv", user_id="uid_alice", username="alice", db=db)
    assert not d.allow and d.status == 403  # fail closed on lookup error


def test_traversal_denied():
    d = authorize_path("../../etc/passwd", user_id="uid_alice", username="alice", db=_db())
    assert not d.allow and d.status == 400


def test_root_denied():
    d = authorize_path("", user_id="uid_alice", username="alice", db=_db())
    assert not d.allow and d.status == 403


def test_unauthenticated_denied():
    for uid in ("", "default"):
        d = authorize_path("alpha/x.sv", user_id=uid, username="", db=_db())
        assert not d.allow and d.status == 401


# --------------------------------------------------------------------------- #
# authorize_path — allow paths (must NOT over-block)
# --------------------------------------------------------------------------- #

def test_own_ip_allowed():
    d = authorize_path("alpha/rtl/top.sv", user_id="uid_alice", username="alice", db=_db())
    assert d.allow and d.kind == "ip"


def test_granted_ip_allowed():
    d = authorize_path("shared_ip/x.sv", user_id="uid_alice", username="alice", db=_db())
    assert d.allow


def test_own_session_allowed():
    d = authorize_path(
        ".session/alice/alpha/rtl-gen/conversation.json",
        user_id="uid_alice",
        username="alice",
        db=_db(),
    )
    assert d.allow and d.kind == "session"


def test_shared_root_allowed():
    for p in ("rtl/foo.sv", "doc/wiki/index.md", "ip_examples/uart/rtl.sv", "soc.ssot.yaml"):
        d = authorize_path(p, user_id="uid_alice", username="alice", db=_db())
        assert d.allow, p


def test_admin_bypass_allowed():
    # admin reads bob's IP
    d = authorize_path(
        "beta/rtl/top.sv", user_id="uid_admin", username="admin", is_admin=True, db=_db()
    )
    assert d.allow and d.kind == "admin"


def test_multiuser_off_allows_everything():
    d = authorize_path(
        ".session/bob/beta/x.json", user_id="", username="", multi_user=False, db=_db()
    )
    assert d.allow and d.kind == "multiuser_off"


# --------------------------------------------------------------------------- #
# authorize_ip
# --------------------------------------------------------------------------- #

def test_authorize_ip_owner_and_cross_user():
    db = _db()
    assert authorize_ip("alpha", user_id="uid_alice", db=db).allow
    assert not authorize_ip("beta", user_id="uid_alice", db=db).allow
    assert authorize_ip("beta", user_id="uid_bob", db=db).allow


def test_authorize_ip_shared_scope_allowed():
    assert authorize_ip("rtl", user_id="uid_alice", db=_db()).allow


def test_authorize_ip_unregistered_denied():
    assert not authorize_ip("ghost", user_id="uid_alice", db=_db()).allow


def test_authorize_ip_admin_and_multiuser_off():
    assert authorize_ip("beta", user_id="x", is_admin=True, db=_db()).allow
    assert authorize_ip("beta", user_id="", multi_user=False, db=_db()).allow


# --------------------------------------------------------------------------- #
# accessible_ip_names (listing filter)
# --------------------------------------------------------------------------- #

def test_accessible_ip_names():
    db = _db()
    assert accessible_ip_names(user_id="uid_alice", is_admin=False, multi_user=True, db=db) == {
        "alpha",
        "shared_ip",
    }
    assert accessible_ip_names(user_id="uid_bob", is_admin=False, multi_user=True, db=db) == {
        "beta",
        "shared_ip",
    }


def test_accessible_ip_names_no_restriction():
    db = _db()
    assert accessible_ip_names(user_id="x", is_admin=True, multi_user=True, db=db) is None
    assert accessible_ip_names(user_id="x", is_admin=False, multi_user=False, db=db) is None


def test_accessible_ip_names_db_error_fails_closed():
    class BoomDB:
        def list_accessible_ip_blocks(self, *a, **k):
            raise RuntimeError("boom")

    assert accessible_ip_names(
        user_id="uid_alice", is_admin=False, multi_user=True, db=BoomDB()
    ) == set()


# --------------------------------------------------------------------------- #
# owned_ips — session-namespace ownership (the primary multi-user model)
# --------------------------------------------------------------------------- #

def test_session_owned_ip_allowed_without_ip_block():
    # "gamma" has NO ip_blocks row, but the user owns it via a .session
    # namespace -> allowed (mirrors /api/ip/list). This is the over-block the
    # ip_blocks-only check caused.
    d = authorize_path(
        "gamma/rtl/x.sv", user_id="uid_alice", username="alice",
        db=_db(), owned_ips={"gamma"},
    )
    assert d.allow and d.kind == "ip"


def test_session_owned_ip_allows_write():
    d = authorize_path(
        "gamma/x.sv", user_id="uid_alice", username="alice",
        db=_db(), owned_ips={"gamma"}, permission="write",
    )
    assert d.allow  # owner has full read+write


def test_not_owned_not_granted_denied():
    d = authorize_path(
        "gamma/x.sv", user_id="uid_alice", username="alice",
        db=_db(), owned_ips=set(),
    )
    assert not d.allow and d.status == 403


def test_authorize_ip_owned_set():
    assert authorize_ip("gamma", user_id="uid_alice", db=_db(), owned_ips={"gamma"}).allow
    assert not authorize_ip("gamma", user_id="uid_alice", db=_db(), owned_ips=set()).allow


def test_accessible_ip_names_unions_owned_and_granted():
    got = accessible_ip_names(
        user_id="uid_alice", is_admin=False, multi_user=True,
        db=_db(), owned_ips={"gamma", "alpha"},
    )
    assert got == {"gamma", "alpha", "shared_ip"}  # owned ∪ granted


# --------------------------------------------------------------------------- #
# per-model session owner (owner_aliases) — ATLAS_SESSION_PER_MODEL
# --------------------------------------------------------------------------- #

def test_per_model_session_owner_allowed_via_alias():
    # On-disk owner segment becomes "alice__gpt5" when per-model isolation is on.
    d = authorize_path(
        ".session/alice__gpt5/alpha/rtl-gen/conv.json",
        user_id="uid_alice", username="alice",
        owner_aliases={"alice", "alice__gpt5"}, db=_db(),
    )
    assert d.allow and d.kind == "session"


def test_per_model_session_without_alias_denied():
    # Without the alias the bare-username compare would lock the owner out;
    # confirm a DIFFERENT user's per-model segment is still denied.
    d = authorize_path(
        ".session/bob__gpt5/beta/x.json",
        user_id="uid_alice", username="alice",
        owner_aliases={"alice", "alice__gpt5"}, db=_db(),
    )
    assert not d.allow and d.status == 403


def test_decision_truthiness():
    assert bool(AuthzDecision(True))
    assert not bool(AuthzDecision(False))
