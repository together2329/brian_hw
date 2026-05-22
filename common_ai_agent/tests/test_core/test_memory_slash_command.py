import os
import shutil
import sys
import tempfile
import unittest

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, "core"))
sys.path.insert(0, os.path.join(_project_root, "src"))
sys.path.insert(0, os.path.join(_project_root, "lib"))

import config
from memory import MemorySystem
from slash_commands import SlashCommandRegistry


class TestMemorySlashCommand(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.old_memory_dir = getattr(config, "MEMORY_DIR", ".memory")
        self.old_active_workspace = os.environ.get("ACTIVE_WORKSPACE")
        self.old_active_session = os.environ.get("ATLAS_ACTIVE_SESSION")
        self.old_db_path = os.environ.get("ATLAS_DB_PATH")
        self.old_memory_backend = os.environ.get("ATLAS_MEMORY_BACKEND")
        config.MEMORY_DIR = self.temp_dir
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        os.environ.pop("ATLAS_ACTIVE_SESSION", None)
        os.environ.pop("ATLAS_DB_PATH", None)
        os.environ.pop("ATLAS_MEMORY_BACKEND", None)
        self.registry = SlashCommandRegistry()

    def tearDown(self):
        config.MEMORY_DIR = self.old_memory_dir
        if self.old_active_workspace is None:
            os.environ.pop("ACTIVE_WORKSPACE", None)
        else:
            os.environ["ACTIVE_WORKSPACE"] = self.old_active_workspace
        if self.old_active_session is None:
            os.environ.pop("ATLAS_ACTIVE_SESSION", None)
        else:
            os.environ["ATLAS_ACTIVE_SESSION"] = self.old_active_session
        if self.old_db_path is None:
            os.environ.pop("ATLAS_DB_PATH", None)
        else:
            os.environ["ATLAS_DB_PATH"] = self.old_db_path
        if self.old_memory_backend is None:
            os.environ.pop("ATLAS_MEMORY_BACKEND", None)
        else:
            os.environ["ATLAS_MEMORY_BACKEND"] = self.old_memory_backend
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_memory_workflow_add_uses_active_workflow(self):
        result = self.registry.execute("/memory workflow add Prefer input logic/output logic ports")

        self.assertIn("workflow [rtl-gen]", result.lower())
        memory = MemorySystem(memory_dir=self.temp_dir)
        rules = memory.list_rules(workflow="rtl-gen")
        self.assertEqual(rules["workflow"]["rules"], ["Prefer input logic/output logic ports"])

    def test_memory_global_and_specific_workflow_add(self):
        self.registry.execute("/memory add Keep comments clear")
        self.registry.execute("/memory workflow ssot-gen add Resolve TBDs before generation")

        memory = MemorySystem(memory_dir=self.temp_dir)
        self.assertEqual(memory.list_rules()["global"], ["Keep comments clear"])
        self.assertEqual(
            memory.list_rules(workflow="ssot-gen")["workflow"]["rules"],
            ["Resolve TBDs before generation"],
        )

    def test_memory_rules_are_scoped_by_active_user(self):
        os.environ["ATLAS_ACTIVE_SESSION"] = "alice/new_axi/ssot-gen"
        alice_result = self.registry.execute("/memory add Alice prefers strict SSOT")
        self.assertIn("User: alice", alice_result)

        os.environ["ATLAS_ACTIVE_SESSION"] = "bob/new_axi/ssot-gen"
        bob_result = self.registry.execute("/memory add Bob prefers compact output")
        self.assertIn("User: bob", bob_result)

        alice = MemorySystem(memory_dir=self.temp_dir, user="alice")
        bob = MemorySystem(memory_dir=self.temp_dir, user="bob")
        self.assertEqual(alice.list_rules()["global"], ["Alice prefers strict SSOT"])
        self.assertEqual(bob.list_rules()["global"], ["Bob prefers compact output"])

    def test_memory_slash_uses_db_when_user_and_db_are_active(self):
        from core.atlas_db import AtlasDB

        db_path = os.path.join(self.temp_dir, "atlas.db")
        os.environ["ATLAS_DB_PATH"] = db_path
        os.environ["ATLAS_ACTIVE_SESSION"] = "alice/new_axi/ssot-gen"

        result = self.registry.execute('/memory a "Prefer DB-backed rules"')

        self.assertIn("Source: AtlasDB:", result)
        with AtlasDB(db_path) as db:
            user = db.get_user_by_username("alice")
            self.assertIsNotNone(user)
            rules = db.list_user_memory_rules(user["id"])
        self.assertEqual([row["rule"] for row in rules], ["Prefer DB-backed rules"])


if __name__ == "__main__":
    unittest.main()
