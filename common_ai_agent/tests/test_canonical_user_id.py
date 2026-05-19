import pytest

from core.atlas_db import AtlasDB
from src.atlas_api_jobs import _canonical_user_id


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


@pytest.fixture
def user_uuid(db):
    user = db.create_user("testuser", "Test User", "hashed-pw", email="test@example.com")
    return user["id"]


class TestCanonicalUserId:
    def test_uuid_passthrough(self, db, user_uuid):
        assert _canonical_user_id(db, user_uuid) == user_uuid

    def test_username_resolves_to_uuid(self, db, user_uuid):
        assert _canonical_user_id(db, "testuser") == user_uuid

    def test_email_resolves_to_uuid(self, db, user_uuid):
        assert _canonical_user_id(db, "test@example.com") == user_uuid

    def test_all_forms_match(self, db, user_uuid):
        by_uuid = _canonical_user_id(db, user_uuid)
        by_username = _canonical_user_id(db, "testuser")
        by_email = _canonical_user_id(db, "test@example.com")
        assert by_uuid == by_username == by_email

    def test_local_admin_passthrough(self, db):
        assert _canonical_user_id(db, "local-admin") == "local-admin"

    def test_empty_string_passthrough(self, db):
        assert _canonical_user_id(db, "") == ""

    def test_unknown_identifier_passthrough(self, db):
        assert _canonical_user_id(db, "no-such-user") == "no-such-user"

    def test_upsert_workspace_deduplication(self, db, user_uuid):
        ws_by_uuid = db.upsert_workspace(
            "myproject",
            owner_user_id=_canonical_user_id(db, user_uuid),
            local_path="/tmp/myproject",
        )
        ws_by_username = db.upsert_workspace(
            "myproject",
            owner_user_id=_canonical_user_id(db, "testuser"),
            local_path="/tmp/myproject",
        )
        ws_by_email = db.upsert_workspace(
            "myproject",
            owner_user_id=_canonical_user_id(db, "test@example.com"),
            local_path="/tmp/myproject",
        )
        assert ws_by_uuid["id"] == ws_by_username["id"] == ws_by_email["id"]
