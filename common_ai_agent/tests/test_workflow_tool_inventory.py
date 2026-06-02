"""
tests/test_workflow_tool_inventory.py

Verifies that every canonical worker workflow exposes the expected baseline
tools, and surfaces the exact bug class described in the task:
  "worker claims I don't have web_search available"

Architecture recap
------------------
- core/tools.py:AVAILABLE_TOOLS  — base dict, built at import time
- core/tools_web.py:WEB_TOOLS   — web_search / websearch / web_fetch / web_extract
  registered via `AVAILABLE_TOOLS.update(WEB_TOOLS)` at the bottom of tools.py
- core/tools.py:filtered_available_tools(extra_disable=None)
  starts from AVAILABLE_TOOLS, removes tools named in the
  WORKFLOW_DISABLED_TOOLS env-var (comma-separated).
- Each workflow sets WORKFLOW_DISABLED_TOOLS in workflow/<wf>/workspace.json.
  None of the canonical worker configs disable web_search/web_fetch.
- The orchestrator uses a SEPARATE 9-tool set from
  src/orchestrator/prompts.py::tool_schemas() — dispatch_workflow lives there.
  Worker workflows do NOT get dispatch_workflow.

What these tests catch
----------------------
1. web_search / web_fetch missing from TOOL_SCHEMAS (registry gap)
2. web_search / web_fetch missing from AVAILABLE_TOOLS (import failure)
3. Any workflow's WORKFLOW_DISABLED_TOOLS accidentally removing a baseline tool
4. Orchestrator tool set missing dispatch_workflow
5. Default chat or worker workflows having orchestrator-only tools
6. Drift between orchestrator dispatch_workflow workflow-enum and
   _DEFAULT_WORKER_PORTS keys in src/atlas_api_jobs.py
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# ── path setup ────────────────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
sys.path.insert(0, str(_PROJECT_ROOT / "src"))
sys.path.insert(0, str(_PROJECT_ROOT / "core"))
sys.path.insert(0, str(_PROJECT_ROOT / "lib"))

# ── Canonical workflow list (mirrors _DEFAULT_WORKER_PORTS in atlas_api_jobs) ─
_CANONICAL_WORKER_WORKFLOWS = [
    "ssot-gen",
    "fl-model-gen",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim_debug",
    "syn",
    "sta",
    "pnr",
    "sta-post",
]

# Tools that MUST be present for every worker workflow
_BASELINE_TOOLS = {
    "read_file",
    "grep_file",
    "replace_in_file",
    "run_command",
    "write_file",
}

# Web tools that MUST be present for every workflow (none of the workspace.json
# files disable these — they only disable ask_user / record_ssot_qa)
_WEB_TOOLS = {"web_search", "web_fetch"}

# Tools that belong ONLY to the orchestrator; default chat must NOT expose them.
_DEFAULT_ORCHESTRATOR_ONLY_TOOLS = {"dispatch_workflow", "read_pipeline_state"}


def _workspace_disabled_tools(workflow: str) -> set:
    """Read WORKFLOW_DISABLED_TOOLS from workflow/<wf>/workspace.json.

    Returns empty set if the file is absent or the key is blank.
    """
    import json
    ws_path = _PROJECT_ROOT / "workflow" / workflow / "workspace.json"
    if not ws_path.exists():
        return set()
    try:
        data = json.loads(ws_path.read_text(encoding="utf-8"))
        raw = (data.get("env") or {}).get("WORKFLOW_DISABLED_TOOLS", "")
        return {t.strip() for t in raw.split(",") if t.strip()}
    except Exception:
        return set()


def _worker_tool_inventory(workflow: str) -> dict:
    """Return the effective AVAILABLE_TOOLS dict that a worker for `workflow`
    would see, by patching WORKFLOW_DISABLED_TOOLS from the workspace.json and
    calling filtered_available_tools().

    Returns a dict {tool_name: func}.
    """
    disabled = _workspace_disabled_tools(workflow)
    disabled_csv = ",".join(sorted(disabled)) if disabled else ""
    with patch.dict(os.environ, {"WORKFLOW_DISABLED_TOOLS": disabled_csv}):
        from core.tools import filtered_available_tools
        # Re-evaluate with the patched env
        return filtered_available_tools()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Registry / schema-level checks (fast, no env patching)
# ══════════════════════════════════════════════════════════════════════════════

class TestToolSchemaRegistry(unittest.TestCase):
    """TOOL_SCHEMAS must contain the canonical tool names."""

    @classmethod
    def setUpClass(cls):
        from core.tool_schema import TOOL_SCHEMAS
        cls.registry = TOOL_SCHEMAS

    def test_web_search_registered_in_schema(self):
        """web_search must be in TOOL_SCHEMAS registry."""
        self.assertIn(
            "web_search", self.registry,
            "web_search missing from TOOL_SCHEMAS — "
            "native tool-call mode will never expose it",
        )

    def test_web_fetch_registered_in_schema(self):
        """web_fetch must be in TOOL_SCHEMAS registry."""
        self.assertIn(
            "web_fetch", self.registry,
            "web_fetch missing from TOOL_SCHEMAS",
        )

    def test_read_file_registered_in_schema(self):
        """read_file must be in TOOL_SCHEMAS registry."""
        self.assertIn("read_file", self.registry)

    def test_grep_file_registered_in_schema(self):
        """grep_file must be in TOOL_SCHEMAS registry."""
        self.assertIn("grep_file", self.registry)

    def test_dispatch_workflow_registered_in_schema(self):
        """dispatch_workflow must be in TOOL_SCHEMAS (used by orchestrator)."""
        self.assertIn(
            "dispatch_workflow", self.registry,
            "dispatch_workflow missing from TOOL_SCHEMAS — "
            "orchestrator native-tool-call mode won't work",
        )

    def test_read_pipeline_state_registered_in_schema(self):
        """read_pipeline_state must be in TOOL_SCHEMAS."""
        self.assertIn("read_pipeline_state", self.registry)

    def test_external_db_query_registered_in_schema(self):
        self.assertIn(
            "external_db_query",
            self.registry,
            "external_db_query missing from TOOL_SCHEMAS — "
            "external-db skill cannot expose a dedicated tool in native tool-call mode",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 2. AVAILABLE_TOOLS runtime presence (web tools depend on successful import)
# ══════════════════════════════════════════════════════════════════════════════

class TestAvailableToolsRuntime(unittest.TestCase):
    """AVAILABLE_TOOLS (the runtime dict) must contain web_search and friends.

    If this test fails it means core/tools_web.py failed to import, which is
    exactly why a worker would say "I don't have web_search available".
    """

    @classmethod
    def setUpClass(cls):
        from core.tools import AVAILABLE_TOOLS
        cls.tools = AVAILABLE_TOOLS

    def _assert_present(self, name: str):
        self.assertIn(
            name, self.tools,
            f"AVAILABLE_TOOLS is missing '{name}' — "
            f"core/tools_web.py may have failed to import (cursor-cli absent?). "
            f"Any worker started in this environment will claim it cannot use {name}.",
        )

    def test_web_search_in_available_tools(self):
        """web_search must be in AVAILABLE_TOOLS at runtime."""
        self._assert_present("web_search")

    def test_web_fetch_in_available_tools(self):
        """web_fetch must be in AVAILABLE_TOOLS at runtime."""
        self._assert_present("web_fetch")

    def test_read_file_in_available_tools(self):
        """read_file must be in AVAILABLE_TOOLS."""
        self._assert_present("read_file")

    def test_grep_file_in_available_tools(self):
        """grep_file must be in AVAILABLE_TOOLS."""
        self._assert_present("grep_file")

    def test_replace_in_file_in_available_tools(self):
        """replace_in_file must be in AVAILABLE_TOOLS."""
        self._assert_present("replace_in_file")

    def test_run_command_in_available_tools(self):
        """run_command must be in AVAILABLE_TOOLS."""
        self._assert_present("run_command")

    def test_dispatch_workflow_in_available_tools(self):
        """dispatch_workflow must be in AVAILABLE_TOOLS (needed by orchestrator text mode)."""
        self._assert_present("dispatch_workflow")

    def test_read_pipeline_state_in_available_tools(self):
        """read_pipeline_state must be in AVAILABLE_TOOLS."""
        self._assert_present("read_pipeline_state")

    def test_external_db_query_in_available_tools(self):
        self._assert_present("external_db_query")


# ══════════════════════════════════════════════════════════════════════════════
# 3. Per-workflow tool inventory — parametrised via subTest
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkflowToolInventory(unittest.TestCase):
    """For each canonical worker workflow, assert the full baseline is present.

    The test prints the full inventory dict for each failing workflow so the
    diagnosis is self-evident in pytest -v --tb=short output.
    """

    def _inventory(self, workflow: str) -> dict:
        return _worker_tool_inventory(workflow)

    def test_baseline_tools_present_in_all_workflows(self):
        """Every worker workflow must expose the full baseline tool set."""
        failures = []
        inventories = {}
        for wf in _CANONICAL_WORKER_WORKFLOWS:
            inv = self._inventory(wf)
            inventories[wf] = sorted(inv.keys())
            missing = _BASELINE_TOOLS - inv.keys()
            if missing:
                failures.append(
                    f"Workflow '{wf}' is missing baseline tools: {sorted(missing)}\n"
                    f"  Available tools: {sorted(inv.keys())}"
                )
        if failures:
            self.fail(
                "One or more workflows are missing baseline tools:\n\n"
                + "\n\n".join(failures)
                + "\n\nFull inventories:\n"
                + "\n".join(f"  {wf}: {tools}" for wf, tools in inventories.items())
            )

    def test_web_search_present_in_all_workflows(self):
        """web_search must be available in every worker workflow.

        If this fails: the worker agent will say 'I don't have web_search
        available' — this is the exact bug the test was written to catch.
        Print workflow name and available tool list for diagnosis.
        """
        failures = []
        inventories = {}
        for wf in _CANONICAL_WORKER_WORKFLOWS:
            inv = self._inventory(wf)
            inventories[wf] = sorted(inv.keys())
            if "web_search" not in inv:
                failures.append(
                    f"Workflow '{wf}' is MISSING web_search — "
                    f"agent will claim it can't search the web.\n"
                    f"  WORKFLOW_DISABLED_TOOLS for this wf: "
                    f"{sorted(_workspace_disabled_tools(wf))}\n"
                    f"  Available tools ({len(inv)}): {sorted(inv.keys())}"
                )
        if failures:
            self.fail(
                "BUG CONFIRMED: web_search hidden in some workflows:\n\n"
                + "\n\n".join(failures)
                + "\n\nFull inventories:\n"
                + "\n".join(f"  {wf}: {tools}" for wf, tools in inventories.items())
            )

    def test_web_fetch_present_in_all_workflows(self):
        """web_fetch must be available in every worker workflow."""
        failures = []
        for wf in _CANONICAL_WORKER_WORKFLOWS:
            inv = self._inventory(wf)
            if "web_fetch" not in inv:
                failures.append(
                    f"Workflow '{wf}' is MISSING web_fetch — "
                    f"agent will claim it can't fetch URLs.\n"
                    f"  WORKFLOW_DISABLED_TOOLS: {sorted(_workspace_disabled_tools(wf))}\n"
                    f"  Available tools: {sorted(inv.keys())}"
                )
        if failures:
            self.fail("\n\n".join(failures))

    def test_dispatch_workflow_absent_from_worker_workflows(self):
        """Worker workflows must NOT expose dispatch_workflow.

        dispatch_workflow is orchestrator-only. If a worker has it, it can
        accidentally start nested pipeline dispatches.
        """
        violations = []
        for wf in _CANONICAL_WORKER_WORKFLOWS:
            inv = self._inventory(wf)
            if "dispatch_workflow" in inv:
                violations.append(wf)

        self.assertEqual(
            violations,
            [],
            f"dispatch_workflow is exposed to worker workflows {violations}. "
            "Workers must finish their own scope and let the orchestrator "
            "decide cross-workflow dispatches.",
        )

    def test_default_chat_hides_orchestrator_only_tools(self):
        """Default chat must not expose orchestrator routing/status tools."""
        inv = self._inventory("default")
        exposed = sorted(_DEFAULT_ORCHESTRATOR_ONLY_TOOLS & inv.keys())
        self.assertEqual(
            exposed,
            [],
            f"default workflow exposes orchestrator-only tools: {exposed}. "
            "Default chat should answer directly, not inspect or route pipeline runs.",
        )

    def test_orchestrator_workspace_disables_ask_user(self):
        """Orchestrator workspace should disable ask_user (it has its own ask_user tool)."""
        disabled = _workspace_disabled_tools("orchestrator")
        self.assertIn(
            "ask_user", disabled,
            "orchestrator/workspace.json should have ask_user in WORKFLOW_DISABLED_TOOLS "
            "(it uses its own ask_user tool implementation)",
        )

    def test_no_workflow_disables_web_search(self):
        """No canonical workflow's workspace.json should disable web_search."""
        all_workflows = _CANONICAL_WORKER_WORKFLOWS + ["orchestrator"]
        violations = []
        for wf in all_workflows:
            disabled = _workspace_disabled_tools(wf)
            if "web_search" in disabled:
                violations.append(wf)
        self.assertEqual(
            violations, [],
            f"These workflows have web_search in WORKFLOW_DISABLED_TOOLS: {violations}\n"
            f"This is almost certainly wrong — remove it from the workspace.json.",
        )

    def test_no_workflow_disables_web_fetch(self):
        """No canonical workflow's workspace.json should disable web_fetch."""
        all_workflows = _CANONICAL_WORKER_WORKFLOWS + ["orchestrator"]
        violations = []
        for wf in all_workflows:
            disabled = _workspace_disabled_tools(wf)
            if "web_fetch" in disabled:
                violations.append(wf)
        self.assertEqual(violations, [])


# ══════════════════════════════════════════════════════════════════════════════
# 4. Orchestrator tool set checks
# ══════════════════════════════════════════════════════════════════════════════

class TestOrchestratorToolSet(unittest.TestCase):
    """Verify the orchestrator's 9-tool schema includes dispatch_workflow and
    that it lists all canonical worker workflows as valid dispatch targets.
    """

    @classmethod
    def setUpClass(cls):
        from src.orchestrator.prompts import tool_schemas
        cls.schemas = tool_schemas()
        cls.schema_names = {s["function"]["name"] for s in cls.schemas}

    def test_dispatch_workflow_in_orchestrator_tools(self):
        """dispatch_workflow must be in the orchestrator tool schema list."""
        self.assertIn(
            "dispatch_workflow", self.schema_names,
            "dispatch_workflow missing from orchestrator tool_schemas() — "
            "orchestrator cannot dispatch any worker",
        )

    def test_read_pipeline_state_in_orchestrator_tools(self):
        """read_pipeline_state must be in the orchestrator tool schema list."""
        self.assertIn("read_pipeline_state", self.schema_names)

    def test_orchestrator_dispatch_workflow_lists_all_canonical_workflows(self):
        """The dispatch_workflow schema's workflow enum must cover every port in
        _DEFAULT_WORKER_PORTS.  Drift here means the orchestrator cannot reach
        a worker it was dispatched to.

        This test reads _DEFAULT_WORKER_PORTS from src/atlas_api_jobs.py and
        compares it to the enum values in the dispatch_workflow schema.
        """
        # Load _DEFAULT_WORKER_PORTS
        from src.atlas_api_jobs import _DEFAULT_WORKER_PORTS
        port_workflows = set(_DEFAULT_WORKER_PORTS.keys())

        # Find dispatch_workflow schema and extract workflow enum
        dw_schema = next(
            (s for s in self.schemas if s["function"]["name"] == "dispatch_workflow"),
            None,
        )
        self.assertIsNotNone(dw_schema, "dispatch_workflow schema not found")

        props = dw_schema["function"]["parameters"].get("properties", {})
        workflow_prop = props.get("workflow", {})
        # The schema may not list an explicit enum — only assert if it does
        enum_values = workflow_prop.get("enum")
        if enum_values is not None:
            schema_workflows = set(enum_values)
            missing_from_schema = port_workflows - schema_workflows
            self.assertEqual(
                missing_from_schema, set(),
                f"These worker workflows appear in _DEFAULT_WORKER_PORTS but "
                f"NOT in dispatch_workflow schema enum:\n  {sorted(missing_from_schema)}\n"
                f"Orchestrator cannot dispatch to them via native tool call mode.\n"
                f"Port map: {sorted(port_workflows)}\n"
                f"Schema enum: {sorted(schema_workflows)}",
            )
        else:
            # No explicit enum — schema accepts any string; document this as OK.
            pass

    def test_orchestrator_schema_count_at_least_twelve(self):
        """Orchestrator schema list should have at least 12 tools (as documented)."""
        self.assertGreaterEqual(
            len(self.schemas), 12,
            f"Expected >= 12 orchestrator tools, got {len(self.schemas)}: "
            f"{sorted(self.schema_names)}",
        )

    def test_orchestrator_exposes_web_search(self):
        """web_search and web_fetch must be in the orchestrator tool schema list."""
        self.assertIn(
            "web_search", self.schema_names,
            "web_search missing from orchestrator tool_schemas() — "
            "orchestrator cannot search the web directly",
        )
        self.assertIn(
            "web_fetch", self.schema_names,
            "web_fetch missing from orchestrator tool_schemas()",
        )


# ══════════════════════════════════════════════════════════════════════════════
# 5. Meta: worker port map vs canonical workflow list parity
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkerPortMapParity(unittest.TestCase):
    """_DEFAULT_WORKER_PORTS must match the canonical workflow list used by
    this test module and by the orchestrator.
    """

    def test_canonical_workflow_list_matches_default_worker_ports(self):
        """All canonical workflows in this test must have a port in
        _DEFAULT_WORKER_PORTS, and vice versa."""
        from src.atlas_api_jobs import _DEFAULT_WORKER_PORTS
        port_set = set(_DEFAULT_WORKER_PORTS.keys())
        test_set = set(_CANONICAL_WORKER_WORKFLOWS)

        missing_from_ports = test_set - port_set
        missing_from_test = port_set - test_set

        msgs = []
        if missing_from_ports:
            msgs.append(
                f"Workflows in this test file but NOT in _DEFAULT_WORKER_PORTS: "
                f"{sorted(missing_from_ports)}"
            )
        if missing_from_test:
            msgs.append(
                f"Workflows in _DEFAULT_WORKER_PORTS but NOT in this test's "
                f"_CANONICAL_WORKER_WORKFLOWS: {sorted(missing_from_test)}\n"
                f"Add them so they are tested."
            )
        if msgs:
            self.fail("\n".join(msgs))


# ══════════════════════════════════════════════════════════════════════════════
# 6. Diagnostic: print full inventory for all workflows (always runs, no assert)
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkflowToolInventoryDiagnostic(unittest.TestCase):
    """Diagnostic test that prints the complete tool inventory for every workflow.

    This test never fails on its own — it exists so that `pytest -v --tb=short`
    shows the full tool set for each workflow in the captured output, making
    any other failure self-diagnosable.
    """

    def test_print_full_inventory_all_workflows(self):
        """Print tool inventory for all canonical worker workflows."""
        lines = ["\n" + "=" * 70]
        lines.append("WORKFLOW TOOL INVENTORY DIAGNOSTIC")
        lines.append("=" * 70)

        web_missing = []
        for wf in _CANONICAL_WORKER_WORKFLOWS:
            inv = _worker_tool_inventory(wf)
            disabled = _workspace_disabled_tools(wf)
            tool_names = sorted(inv.keys())
            has_web = "web_search" in inv and "web_fetch" in inv
            status = "OK" if has_web else "MISSING WEB TOOLS"
            lines.append(f"\n[{wf}]  status={status}  tools={len(tool_names)}")
            lines.append(f"  disabled_by_workspace: {sorted(disabled) or '(none)'}")
            lines.append(f"  tool_list: {tool_names}")
            if not has_web:
                web_missing.append(wf)
                missing = sorted(_WEB_TOOLS - inv.keys())
                lines.append(f"  MISSING: {missing}")

        lines.append("\n" + "=" * 70)
        if web_missing:
            lines.append(f"BUG: web tools missing from workflows: {web_missing}")
        else:
            lines.append("All workflows have web_search and web_fetch.")
        lines.append("=" * 70)
        print("\n".join(lines))
        # Always passes — diagnostic only
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
