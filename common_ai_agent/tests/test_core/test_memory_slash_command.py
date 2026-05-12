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
        config.MEMORY_DIR = self.temp_dir
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        os.environ.pop("ATLAS_ACTIVE_SESSION", None)
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


if __name__ == "__main__":
    unittest.main()
