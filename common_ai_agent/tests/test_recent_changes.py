"""
Comprehensive tests for recent changes:
  1. Compressor — Pass 5 (orphaned tool_calls), keep_recent=4, no tool_call info in text
  2. Session setup — core/session_setup.py directory/config wiring + migration
  3. Agent client — template/workflow params wired through _post_run
  4. Agent server — template/workflow params accepted and dispatched correctly

Run:
    pytest tests/test_recent_changes.py -v
    pytest tests/test_recent_changes.py -v -k "compressor"   # compressor only
    pytest tests/test_recent_changes.py -v -k "session"      # session only
    pytest tests/test_recent_changes.py -v -k "client"       # client only
    pytest tests/test_recent_changes.py -v -k "server"       # server only
"""

import json
import os
import sys
import time
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "lib"))


# ============================================================
# Helpers shared across test classes
# ============================================================

def _make_cfg(**overrides):
    defaults = dict(
        ENABLE_COMPRESSION=True,
        MAX_CONTEXT_TOKENS=100_000,
        PREEMPTIVE_COMPRESSION_THRESHOLD=0.85,
        COMPRESSION_THRESHOLD=0.95,
        COMPRESSION_KEEP_RECENT=4,
        COMPRESSION_MODE="traditional",
        COMPRESSION_CHUNK_SIZE=20,
        ENABLE_TURN_PROTECTION=False,
        TURN_PROTECTION_COUNT=3,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _mock_llm(messages, **kwargs):
    yield "SUMMARY"


def _msgs(n, roles=("user", "assistant")):
    return [{"role": roles[i % len(roles)], "content": f"msg{i}"} for i in range(n)]


# ============================================================
# 1. Compressor — Pass 5 & keep_recent
# ============================================================

class TestCompressorPass5(unittest.TestCase):
    """Pass 5 strips tool_calls from assistant when tool responses are missing post-compression."""

    def setUp(self):
        from core.compressor import _validate_and_repair_sequence
        self._repair = _validate_and_repair_sequence

    # ── Basic orphaned tool_calls ──────────────────────────────

    def test_orphaned_assistant_tool_calls_stripped(self):
        """Assistant with tool_calls but NO following tool messages → strip tool_calls."""
        messages = [
            {"role": "user", "content": "do something"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc_abc", "type": "function",
                                "function": {"name": "read_file", "arguments": "{}"}}],
            },
            # NO tool message follows — simulates post-compression state
            {"role": "user", "content": "next turn"},
        ]
        result = self._repair(messages)
        # The assistant message must not have tool_calls anymore
        asst_msgs = [m for m in result if m.get("role") == "assistant"]
        self.assertEqual(len(asst_msgs), 1)
        self.assertNotIn("tool_calls", asst_msgs[0])

    def test_orphaned_assistant_gets_placeholder_content(self):
        """Stripped assistant message receives a placeholder content string."""
        messages = [
            {"role": "user", "content": "go"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc1", "type": "function",
                                "function": {"name": "foo", "arguments": "{}"}}],
            },
        ]
        result = self._repair(messages)
        asst = next(m for m in result if m.get("role") == "assistant")
        self.assertTrue(str(asst.get("content", "")).strip(),
                        "Orphaned assistant should have non-empty content")

    def test_orphaned_tool_messages_become_user_messages(self):
        """When tool_calls are stripped due to PARTIAL responses, following tool messages
        should be converted to user messages (not left as orphaned tool messages)."""
        # Two tool_calls declared, only one responded → partial → strip
        messages = [
            {"role": "user", "content": "go"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "tc_x", "type": "function", "function": {"name": "bar", "arguments": "{}"}},
                    {"id": "tc_y", "type": "function", "function": {"name": "baz", "arguments": "{}"}},
                ],
            },
            # Only tc_x responded; tc_y is missing → partial → Pass 5 strips tool_calls
            {"role": "tool", "tool_call_id": "tc_x", "content": "result_data"},
        ]
        result = self._repair(messages)
        # After repair, no 'tool' role should remain (orphaned tools → user messages)
        tool_msgs = [m for m in result if m.get("role") == "tool"]
        self.assertEqual(tool_msgs, [],
                         "Orphaned tool messages should be converted to user messages")

    def test_complete_tool_pair_preserved(self):
        """When tool responses ARE present and complete, tool_calls is preserved."""
        messages = [
            {"role": "user", "content": "read file"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc_ok", "type": "function",
                                "function": {"name": "read_file", "arguments": "{}"}}],
            },
            {"role": "tool", "tool_call_id": "tc_ok", "name": "read_file",
             "content": "file content"},
            {"role": "assistant", "content": "Done"},
        ]
        result = self._repair(messages)
        # The first assistant message should still have tool_calls
        tool_call_assts = [m for m in result if m.get("role") == "assistant" and m.get("tool_calls")]
        self.assertEqual(len(tool_call_assts), 1)
        self.assertEqual(tool_call_assts[0]["tool_calls"][0]["id"], "tc_ok")

    def test_partial_tool_responses_stripped(self):
        """When only some tool responses are present, strip tool_calls."""
        messages = [
            {"role": "user", "content": "do two things"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "tc1", "type": "function", "function": {"name": "f1", "arguments": "{}"}},
                    {"id": "tc2", "type": "function", "function": {"name": "f2", "arguments": "{}"}},
                ],
            },
            # Only tc1 is present — tc2 is missing
            {"role": "tool", "tool_call_id": "tc1", "name": "f1", "content": "r1"},
        ]
        result = self._repair(messages)
        asst_msgs = [m for m in result if m.get("role") == "assistant"]
        self.assertEqual(len(asst_msgs), 1)
        self.assertNotIn("tool_calls", asst_msgs[0])

    def test_multiple_sequential_tool_call_groups(self):
        """Multiple valid tool-call groups in sequence are all preserved."""
        messages = [
            {"role": "user", "content": "start"},
            {
                "role": "assistant",
                "tool_calls": [{"id": "tc_a", "type": "function",
                                "function": {"name": "fa", "arguments": "{}"}}],
                "content": None,
            },
            {"role": "tool", "tool_call_id": "tc_a", "name": "fa", "content": "ra"},
            {
                "role": "assistant",
                "tool_calls": [{"id": "tc_b", "type": "function",
                                "function": {"name": "fb", "arguments": "{}"}}],
                "content": None,
            },
            {"role": "tool", "tool_call_id": "tc_b", "name": "fb", "content": "rb"},
            {"role": "assistant", "content": "Done"},
        ]
        result = self._repair(messages)
        asst_with_calls = [m for m in result if m.get("role") == "assistant" and m.get("tool_calls")]
        self.assertEqual(len(asst_with_calls), 2)

    def test_empty_messages_safe(self):
        """Empty list is returned unchanged."""
        result = self._repair([])
        self.assertEqual(result, [])

    def test_no_tool_calls_messages_unchanged(self):
        """Messages without any tool_calls pass through unmodified."""
        messages = [
            {"role": "system", "content": "You are an agent"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = self._repair(messages)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1]["content"], "hello")


class TestCompressorToolCallsNotInSummaryText(unittest.TestCase):
    """Compression text must NOT include raw tool_calls function call info."""

    def setUp(self):
        from core.compressor import _compress_single
        self._fn = _compress_single

    def test_tool_calls_json_not_in_summary_input(self):
        """tool_calls dict should not appear verbatim in text sent to LLM."""
        captured_prompts = []

        def capturing_llm(messages, **kwargs):
            captured_prompts.extend(messages)
            yield "SUMMARY"

        messages = [
            {"role": "user", "content": "do work"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc1", "type": "function",
                                "function": {"name": "read_file", "arguments": '{"path": "/tmp/x"}'}}],
            },
            {"role": "tool", "tool_call_id": "tc1", "name": "read_file",
             "content": "file text"},
            {"role": "assistant", "content": "Found it"},
        ]
        self._fn(messages, llm_call_fn=capturing_llm)

        user_prompt = next(m["content"] for m in captured_prompts if m["role"] == "user")
        # The raw tool_calls structure should NOT appear
        self.assertNotIn('"function": {"name": "read_file"', user_prompt,
                         "Raw tool_calls JSON should not be in compression text")
        # '→ called:' pattern (old format) should not appear
        self.assertNotIn("→ called:", user_prompt,
                         "'→ called: func' should not appear in compression text")

    def test_tool_result_content_is_included(self):
        """Tool result content SHOULD be included in the summary text."""
        captured = []

        def capturing_llm(messages, **kwargs):
            captured.extend(messages)
            yield "DONE"

        messages = [
            {"role": "user", "content": "read something"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"id": "tc2", "type": "function",
                                "function": {"name": "read_file", "arguments": "{}"}}],
            },
            {"role": "tool", "tool_call_id": "tc2", "name": "read_file",
             "content": "UNIQUE_TOOL_RESULT_SENTINEL"},
        ]
        self._fn(messages, llm_call_fn=capturing_llm)
        user_prompt = next(m["content"] for m in captured if m["role"] == "user")
        self.assertIn("UNIQUE_TOOL_RESULT_SENTINEL", user_prompt)


class TestCompressorKeepRecent(unittest.TestCase):
    """keep_recent=4 is enforced; turn protection cap prevents runaway preservation."""

    def setUp(self):
        from core.compressor import compress_history
        self._fn = compress_history

    def _call(self, messages, **kwargs):
        defaults = dict(
            cfg=_make_cfg(),
            llm_call_fn=_mock_llm,
            estimate_tokens_fn=lambda m: 100,
            last_input_tokens=0,
        )
        defaults.update(kwargs)
        return self._fn(messages, **defaults)

    def test_keep_recent_4_enforced(self):
        """After compression with keep_recent=4, at most 4+summary non-system msgs remain."""
        msgs = _msgs(40)
        result = self._call(msgs, force=True, keep_recent=4)
        non_system = [m for m in result if m["role"] not in ("system",)]
        self.assertLessEqual(len(non_system), 5,  # summary + 4 recent
                             f"Expected ≤5 non-system messages, got {len(non_system)}")

    def test_default_keep_recent_is_4(self):
        """cfg.COMPRESSION_KEEP_RECENT=4 default is honored."""
        msgs = _msgs(40)
        cfg = _make_cfg(COMPRESSION_KEEP_RECENT=4)
        result = self._call(msgs, force=True, cfg=cfg)
        non_system = [m for m in result if m["role"] not in ("system",)]
        self.assertLessEqual(len(non_system), 6)

    def test_keep_recent_0_not_honored_raw(self):
        """
        keep_recent=0 is treated as 'use default' (safety floor).
        The compressor should not keep 0 messages after compression.
        """
        msgs = _msgs(40)
        result = self._call(msgs, force=True, keep_recent=0)
        # Should still have a summary + some recent messages (floor = 4)
        self.assertGreater(len(result), 1)

    def test_turn_protection_disabled_by_default(self):
        """ENABLE_TURN_PROTECTION=False means keep_recent=4 wins even for big turns."""
        # Create a conversation where the last 'turn' has 30 messages
        msgs = _msgs(36)
        cfg = _make_cfg(ENABLE_TURN_PROTECTION=False, COMPRESSION_KEEP_RECENT=4)
        result = self._call(msgs, force=True, cfg=cfg)
        non_system = [m for m in result if m["role"] not in ("system",)]
        self.assertLessEqual(len(non_system), 6,
                             "Turn protection disabled: keep_recent should cap at 4")

    def test_recent_messages_are_last_n(self):
        """The kept recent messages are always the LAST N messages."""
        msgs = [{"role": "user" if i % 2 == 0 else "assistant",
                 "content": f"UNIQUE_{i}"} for i in range(20)]
        result = self._call(msgs, force=True, keep_recent=4)
        # The last 4 messages (UNIQUE_16 through UNIQUE_19) should be present
        all_content = " ".join(str(m.get("content", "")) for m in result)
        for i in range(16, 20):
            self.assertIn(f"UNIQUE_{i}", all_content,
                          f"UNIQUE_{i} should be in the kept recent messages")

    def test_zero_messages_safe(self):
        """compress_history on empty list returns empty list."""
        result = self._call([], force=True)
        self.assertIsInstance(result, list)


# ============================================================
# 2. Session Setup
# ============================================================

class TestSessionSetup(unittest.TestCase):
    """Tests for core/session_setup.py session directory creation and config patching."""

    def setUp(self):
        # Work in a temp dir to avoid polluting the real project
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_cwd = os.getcwd()
        os.chdir(self._tmpdir.name)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self._tmpdir.cleanup()

    def _call_setup_session(self, project="testproj", workflow=""):
        """Import and call setup_session, returning (session_dir, config)."""
        # Reload config to reset paths
        import importlib
        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])
        import config  # noqa — import to have module reference
        from core.session_setup import setup_session
        session_dir = setup_session(project, workflow)
        return session_dir, config

    def test_creates_session_directory(self):
        session_dir, _ = self._call_setup_session("myproject")
        self.assertTrue(Path(session_dir).is_dir(),
                        "setup_session must create the session directory")

    def test_session_dir_path_format(self):
        session_dir, _ = self._call_setup_session("myproject")
        self.assertTrue(str(session_dir).endswith(".session/myproject"),
                        f"Session dir should be .session/<project>, got: {session_dir}")

    def test_config_history_file_set(self):
        session_dir, cfg = self._call_setup_session("proj1")
        self.assertTrue(cfg.HISTORY_FILE.endswith("conversation.json"),
                        f"HISTORY_FILE should point to conversation.json, got: {cfg.HISTORY_FILE}")
        self.assertIn("proj1", cfg.HISTORY_FILE)

    def test_config_todo_file_set(self):
        _, cfg = self._call_setup_session("proj2")
        self.assertTrue(cfg.TODO_FILE.endswith("todo.json"))
        self.assertIn("proj2", cfg.TODO_FILE)

    def test_config_cost_file_set(self):
        _, cfg = self._call_setup_session("proj3")
        self.assertTrue(cfg.COST_FILE.endswith("cost.json"))

    def test_config_active_project_set(self):
        _, cfg = self._call_setup_session("myproj")
        self.assertEqual(cfg.ACTIVE_PROJECT, "myproj")

    def test_config_session_dir_set(self):
        session_dir, cfg = self._call_setup_session("proj4")
        self.assertEqual(str(session_dir), cfg.SESSION_DIR)

    def test_different_projects_get_different_dirs(self):
        session_dir_a, _ = self._call_setup_session("proj_a")
        session_dir_b, _ = self._call_setup_session("proj_b")
        self.assertNotEqual(str(session_dir_a), str(session_dir_b))

    def test_returns_path_object(self):
        session_dir, _ = self._call_setup_session("pathtest")
        self.assertIsInstance(session_dir, Path)

    def test_idempotent_second_call(self):
        """Calling setup_session twice for the same project must not raise."""
        self._call_setup_session("stable")
        try:
            self._call_setup_session("stable")
        except Exception as e:
            self.fail(f"Second call to setup_session raised: {e}")


class TestSessionSetupMigration(unittest.TestCase):
    """v0/v1 → v2 migration in _migrate_old_session."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_cwd = os.getcwd()
        os.chdir(self._tmpdir.name)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self._tmpdir.cleanup()

    def _migrate(self, session_dir: Path):
        from core.session_setup import _migrate_old_session
        _migrate_old_session(session_dir)

    def test_v0_conversation_history_renamed(self):
        """v0: conversation_history.json → conversation.json"""
        sd = Path(self._tmpdir.name) / ".session" / "proj"
        sd.mkdir(parents=True)
        (sd / "conversation_history.json").write_text('[]')
        self._migrate(sd)
        self.assertTrue((sd / "conversation.json").exists())
        self.assertFalse((sd / "conversation_history.json").exists())

    def test_v0_current_todos_renamed(self):
        """v0: current_todos.json → todo.json"""
        sd = Path(self._tmpdir.name) / ".session" / "proj"
        sd.mkdir(parents=True)
        (sd / "current_todos.json").write_text('[]')
        self._migrate(sd)
        self.assertTrue((sd / "todo.json").exists())
        self.assertFalse((sd / "current_todos.json").exists())

    def test_v1_primary_conversation_moved(self):
        """v1: primary/conversation.json → conversation.json"""
        sd = Path(self._tmpdir.name) / ".session" / "proj"
        (sd / "primary").mkdir(parents=True)
        (sd / "primary" / "conversation.json").write_text('["v1data"]')
        self._migrate(sd)
        self.assertTrue((sd / "conversation.json").exists())
        # primary/ should be removed
        self.assertFalse((sd / "primary").exists())

    def test_v1_sub_becomes_jobs(self):
        """v1: sub/agent1_wf → jobs/job1"""
        sd = Path(self._tmpdir.name) / ".session" / "proj"
        sub = sd / "sub" / "agent1_wf"
        sub.mkdir(parents=True)
        (sub / "data.txt").write_text("hello")
        self._migrate(sd)
        # jobs dir should exist, sub/ should be gone
        self.assertTrue((sd / "jobs").exists())
        self.assertFalse((sd / "sub").exists())


# ============================================================
# 3. Agent Client — template/workflow wiring
# ============================================================

class TestAgentClientTemplateWorkflow(unittest.TestCase):
    """worker_call passes template/workflow → _post_run → HTTP body."""

    def _mock_worker_call(self, *, template="", workflow=""):
        """Run worker_call with mocked HTTP, capture the POST /run body."""
        import core.agent_client as client_mod
        from core.agent_client import worker_call

        posted_bodies = []
        call_count = [0]

        def mock_urlopen(req, timeout=10):
            call_count[0] += 1
            url = req.full_url if hasattr(req, "full_url") else str(req)

            if url.endswith("/run"):
                # Capture what was POSTed
                try:
                    posted_bodies.append(json.loads(req.data.decode("utf-8")))
                except Exception:
                    pass
                body = json.dumps({"run_id": "run_tmpl_001", "status": "pending"})
                r = MagicMock()
                r.read.return_value = body.encode()
                r.__enter__ = lambda s: s
                r.__exit__ = MagicMock(return_value=False)
                return r

            if "/status/" in url:
                body = json.dumps({"run_id": "run_tmpl_001", "status": "completed"})
                r = MagicMock()
                r.read.return_value = body.encode()
                r.__enter__ = lambda s: s
                r.__exit__ = MagicMock(return_value=False)
                return r

            if "/log/" in url:
                body = json.dumps({"entries": [], "total_entries": 0})
                r = MagicMock()
                r.read.return_value = body.encode()
                r.__enter__ = lambda s: s
                r.__exit__ = MagicMock(return_value=False)
                return r

            if "/result/" in url:
                body = json.dumps({
                    "run_id": "run_tmpl_001",
                    "status": "completed",
                    "result": "done",
                    "files_modified": [],
                    "files_examined": [],
                    "iterations": 1,
                })
                r = MagicMock()
                r.read.return_value = body.encode()
                r.__enter__ = lambda s: s
                r.__exit__ = MagicMock(return_value=False)
                return r

            raise Exception(f"Unexpected URL: {url}")

        with patch("core.agent_client.urllib.request.urlopen", side_effect=mock_urlopen):
            worker_call(
                worker="http://localhost:8001",
                task="do work",
                template=template,
                workflow=workflow,
                timeout=10,
                poll_interval=0.01,
                show_log=False,
            )
        return posted_bodies

    def test_template_sent_in_post_body(self):
        bodies = self._mock_worker_call(template="my-template")
        self.assertTrue(len(bodies) > 0, "At least one POST /run must have been made")
        self.assertEqual(bodies[0].get("template"), "my-template")

    def test_workflow_sent_in_post_body(self):
        bodies = self._mock_worker_call(workflow="rtl-gen")
        self.assertEqual(bodies[0].get("workflow"), "rtl-gen")

    def test_template_and_workflow_both_sent(self):
        bodies = self._mock_worker_call(template="rtl-impl", workflow="rtl-gen")
        self.assertEqual(bodies[0].get("template"), "rtl-impl")
        self.assertEqual(bodies[0].get("workflow"), "rtl-gen")

    def test_empty_template_not_in_body(self):
        """Empty template/workflow should NOT appear in the POST body."""
        bodies = self._mock_worker_call(template="", workflow="")
        body = bodies[0]
        self.assertNotIn("template", body,
                         "Empty template should be omitted from POST body")
        self.assertNotIn("workflow", body,
                         "Empty workflow should be omitted from POST body")

    def test_task_always_in_body(self):
        bodies = self._mock_worker_call(template="tmpl")
        self.assertEqual(bodies[0].get("task"), "do work")

    def test_worker_call_returns_completed(self):
        """Sanity: worker_call with template/workflow still returns a result dict."""
        from core.agent_client import worker_call

        def mock_urlopen(req, timeout=10):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if url.endswith("/run"):
                body = json.dumps({"run_id": "r1", "status": "pending"})
            elif "/status/" in url:
                body = json.dumps({"run_id": "r1", "status": "completed"})
            elif "/log/" in url:
                body = json.dumps({"entries": [], "total_entries": 0})
            elif "/result/" in url:
                body = json.dumps({"run_id": "r1", "status": "completed",
                                   "result": "ok", "files_modified": [],
                                   "files_examined": [], "iterations": 1})
            else:
                raise Exception(f"Unexpected: {url}")
            r = MagicMock()
            r.read.return_value = body.encode()
            r.__enter__ = lambda s: s
            r.__exit__ = MagicMock(return_value=False)
            return r

        with patch("core.agent_client.urllib.request.urlopen", side_effect=mock_urlopen):
            result = worker_call(
                worker="http://localhost:8001",
                task="test",
                template="feature",
                workflow="default",
                timeout=5,
                poll_interval=0.01,
                show_log=False,
            )
        self.assertEqual(result["status"], "completed")


class TestAtlasUiWorkerDispatchTemplateWorkflow(unittest.TestCase):
    """ATLAS UI job dispatch must preserve template/ip for worker /run loading."""

    def _dispatch(self, body: dict) -> tuple[dict, dict]:
        try:
            from fastapi.testclient import TestClient
            import atlas_ui
            import atlas_api_jobs
        except ImportError as e:
            self.skipTest(f"fastapi/atlas_ui unavailable: {e}")

        posted: dict = {}

        def mock_urlopen(req, timeout=10):
            posted.update(json.loads(req.data.decode("utf-8")))
            resp = MagicMock()
            resp.read.return_value = json.dumps({"run_id": "atlas_run_1"}).encode("utf-8")
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        jobs, jobs_lock = atlas_api_jobs.get_jobs_state()
        with jobs_lock:
            jobs.clear()

        with patch.dict(os.environ, {"ATLAS_ADMIN_AUTH_MODE": "local"}):
            app = atlas_ui.create_app()
            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                client = TestClient(app)
                response = client.post("/api/job/dispatch", json=body)

        return response.json(), posted

    def test_rtl_dispatch_defaults_to_dynamic_rtl_driver_and_ip(self):
        response, posted = self._dispatch({
            "workflow": "rtl-gen",
            "ip": "dma330",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertEqual(posted.get("workflow"), "rtl-gen")
        self.assertNotIn("template", posted)
        self.assertEqual(posted.get("ip"), "dma330")

    def test_dispatch_preserves_explicit_template(self):
        response, posted = self._dispatch({
            "workflow": "rtl-gen",
            "ip": "dma330",
            "template": "custom-rtl",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertEqual(posted.get("template"), "custom-rtl")

    def test_dispatch_accepts_worker_direct_trigger_source(self):
        response, posted = self._dispatch({
            "workflow": "ssot-gen",
            "ip": "dma330",
            "session": "admin/dma330/ssot-gen",
            "prompt": "Draft SSOT from this worker view",
            "trigger_source": "worker_direct_chat",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertEqual(response.get("trigger_source"), "worker_direct_chat")
        self.assertEqual(posted.get("session"), "admin/dma330/ssot-gen")

    def test_dispatch_accepts_windows_session_path_as_namespace(self):
        response, posted = self._dispatch({
            "workflow": "rtl-gen",
            "ip": "dma330",
            "session": r"C:\repo\common_ai_agent\.session\dma330\rtl-gen\conversation.json",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertEqual(posted.get("session"), "dma330/rtl-gen")

    def test_dispatch_accepts_windows_scope_path_session(self):
        response, posted = self._dispatch({
            "workflow": "ssot-gen",
            "ip": "SQA",
            "session": r"C:\Users\207\Desktop\SQA/ssot-gen",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertEqual(posted.get("session"), "SQA/ssot-gen")

    def test_session_state_accepts_leading_backslash_namespace(self):
        try:
            from fastapi.testclient import TestClient
            import atlas_ui
        except ImportError as e:
            self.skipTest(f"fastapi/atlas_ui unavailable: {e}")

        with patch.dict(os.environ, {"ATLAS_ADMIN_AUTH_MODE": "local"}):
            client = TestClient(atlas_ui.create_app())
            response = client.get("/api/session/state", params={"session": r"\SQA/ssot-gen"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("session"), "SQA/ssot-gen")

    def test_rtl_dispatch_without_ip_does_not_fallback_to_static_seed(self):
        response, posted = self._dispatch({
            "workflow": "rtl-gen",
            "worker": "http://localhost:8001",
        })

        self.assertTrue(response.get("ok"), response)
        self.assertNotIn("template", posted)

    def test_session_history_accepts_windows_session_artifact_path(self):
        try:
            from fastapi.testclient import TestClient
            import atlas_ui
        except ImportError as e:
            self.skipTest(f"fastapi/atlas_ui unavailable: {e}")

        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            session_dir = root / ".session" / "dma330" / "rtl-gen"
            session_dir.mkdir(parents=True)
            (session_dir / "conversation.json").write_text(
                json.dumps([{"role": "user", "content": "hello"}]),
                encoding="utf-8",
            )

            old_root = atlas_ui.PROJECT_ROOT
            atlas_ui.PROJECT_ROOT = root
            try:
                with patch.dict(os.environ, {"ATLAS_ADMIN_AUTH_MODE": "local"}):
                    client = TestClient(atlas_ui.create_app())
                    response = client.get(
                        "/api/session/history",
                        params={"session": r"C:\repo\common_ai_agent\.session\dma330\rtl-gen\conversation.json"},
                    )
            finally:
                atlas_ui.PROJECT_ROOT = old_root

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session"), "dma330/rtl-gen")
        self.assertEqual(data.get("messages", [])[0].get("content"), "hello")


class TestPostRunFunction(unittest.TestCase):
    """Direct unit tests for _post_run helper."""

    def test_post_run_includes_template(self):
        from core.agent_client import _post_run

        posted = {}

        def mock_post_json(url, data, timeout=30):
            posted.update(data)
            return {"run_id": "r1"}

        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            _post_run("http://w", "task txt", "", 30, template="my-tmpl")
        self.assertEqual(posted.get("template"), "my-tmpl")

    def test_post_run_includes_workflow(self):
        from core.agent_client import _post_run

        posted = {}

        def mock_post_json(url, data, timeout=30):
            posted.update(data)
            return {"run_id": "r1"}

        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            _post_run("http://w", "task txt", "", 30, workflow="rtl-gen")
        self.assertEqual(posted.get("workflow"), "rtl-gen")

    def test_post_run_omits_empty_template(self):
        from core.agent_client import _post_run

        posted = {}

        def mock_post_json(url, data, timeout=30):
            posted.update(data)
            return {"run_id": "r1"}

        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            _post_run("http://w", "task", "", 30, template="", workflow="")
        self.assertNotIn("template", posted)
        self.assertNotIn("workflow", posted)

    def test_post_run_returns_run_id(self):
        from core.agent_client import _post_run

        def mock_post_json(url, data, timeout=30):
            return {"run_id": "run_xyz"}

        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            rid = _post_run("http://w", "task", "", 30)
        self.assertEqual(rid, "run_xyz")

    def test_post_run_empty_response_returns_empty_string(self):
        from core.agent_client import _post_run

        def mock_post_json(url, data, timeout=30):
            return {}

        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            rid = _post_run("http://w", "task", "", 30)
        self.assertEqual(rid, "")

    def test_post_run_includes_todos(self):
        from core.agent_client import _post_run

        posted = {}

        def mock_post_json(url, data, timeout=30):
            posted.update(data)
            return {"run_id": "r1"}

        todos = [{"content": "todo1", "priority": "high"}]
        with patch("core.agent_client._post_json", side_effect=mock_post_json):
            _post_run("http://w", "task", "", 30, todos=todos)
        self.assertEqual(posted.get("todos"), todos)


# ============================================================
# 4. Agent Server — template/workflow accepted
# ============================================================

class TestAgentServerTemplateWorkflow(unittest.TestCase):
    """RunRequest schema and _load_todo_template behavior.

    RunRequest is defined inside create_app() (local class), so we test
    the HTTP layer behavior rather than instantiating the model directly.
    """

    def setUp(self):
        from core import agent_server
        self.server_mod = agent_server
        self.server_mod._runs.clear()

    def test_create_app_creates_app(self):
        """create_app() returns a FastAPI app without errors."""
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi not installed")
        app = self.server_mod.create_app()
        self.assertIsNotNone(app)

    def test_load_todo_template_returns_list_for_valid_template(self):
        """_load_todo_template returns a list (tasks) for a real template."""
        from core.agent_server import _load_todo_template
        # Use a template that actually exists on disk
        import sys
        root = Path(__file__).parent.parent
        tmpl_path = root / "workflow" / "default" / "todo_templates" / "feature.json"
        if not tmpl_path.exists():
            self.skipTest("workflow/default/todo_templates/feature.json not found")
        result = _load_todo_template("feature", workflow="default")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list, "_load_todo_template should return tasks list")
        self.assertGreater(len(result), 0)

    def test_load_todo_template_returns_none_for_missing(self):
        """_load_todo_template returns None for non-existent template."""
        from core.agent_server import _load_todo_template
        result = _load_todo_template("no-such-template-xyz", workflow="no-such-workflow")
        self.assertIsNone(result)

    def test_load_todo_template_returns_none_for_empty_name(self):
        """_load_todo_template returns None for empty name."""
        from core.agent_server import _load_todo_template
        result = _load_todo_template("")
        self.assertIsNone(result)


class TestLoadTodoTemplate(unittest.TestCase):
    """_load_todo_template resolves templates from workflow dir and CWD.

    _load_todo_template returns the TASKS LIST (not the full dict).
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_cwd = os.getcwd()
        os.chdir(self._tmpdir.name)

    def tearDown(self):
        os.chdir(self._orig_cwd)
        self._tmpdir.cleanup()

    def _make_template(self, path: str, tasks: list):
        """Write a template JSON file (new {name, tasks} format)."""
        p = Path(self._tmpdir.name) / path
        p.parent.mkdir(parents=True, exist_ok=True)
        # Use new {name, tasks} format
        name = Path(path).stem
        p.write_text(json.dumps({"name": name, "tasks": tasks}), encoding="utf-8")
        return p

    def _load(self, name: str, workflow: str = ""):
        from core.agent_server import _load_todo_template
        return _load_todo_template(name, workflow=workflow)

    def test_loads_from_cwd_todo_templates(self):
        """Template found in todo_templates/<template>.json in CWD."""
        tasks = [{"content": "local step", "priority": "high", "activeForm": "..."}]
        self._make_template("todo_templates/local-tmpl.json", tasks)

        result = self._load("local-tmpl")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list, "Returns tasks list")
        self.assertEqual(result[0]["content"], "local step")

    def test_loads_from_real_workflow_dir(self):
        """Template found in the actual project workflow directory."""
        from core.agent_server import _load_todo_template
        root = Path(__file__).parent.parent
        tmpl = root / "workflow" / "default" / "todo_templates" / "feature.json"
        if not tmpl.exists():
            self.skipTest("workflow/default/todo_templates/feature.json not found")
        result = _load_todo_template("feature", workflow="default")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_returns_none_for_missing_template(self):
        """Returns None when template file does not exist."""
        result = self._load("nonexistent-template", workflow="nonexistent-workflow")
        self.assertIsNone(result)

    def test_returns_none_for_empty_name(self):
        """Returns None when template name is empty string."""
        result = self._load("")
        self.assertIsNone(result)

    def test_tasks_list_returned_not_dict(self):
        """Return value is a list, not the top-level dict."""
        tasks = [
            {"content": "step A", "priority": "high", "activeForm": "..."},
            {"content": "step B", "priority": "normal", "activeForm": "..."},
        ]
        self._make_template("todo_templates/two-step.json", tasks)
        result = self._load("two-step")
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)


class TestAgentServerHttpTemplateWorkflow(unittest.TestCase):
    """Integration: /run HTTP endpoint accepts template/workflow in request body."""

    _server = None
    _thread = None
    _port = 18795

    @classmethod
    def setUpClass(cls):
        try:
            import uvicorn
            from core.agent_server import create_app
        except ImportError:
            raise unittest.SkipTest("fastapi/uvicorn not installed")

        cls._base_url = f"http://localhost:{cls._port}"
        ready = threading.Event()

        def _run():
            app = create_app()
            cfg = uvicorn.Config(app, host="127.0.0.1", port=cls._port, log_level="error")
            server = uvicorn.Server(cfg)
            cls._server = server
            ready.set()
            server.run()

        cls._thread = threading.Thread(target=_run, daemon=True)
        cls._thread.start()
        ready.wait(timeout=5)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        if cls._server:
            cls._server.should_exit = True
        if cls._thread:
            cls._thread.join(timeout=5)

    def _post(self, data: dict) -> dict:
        import urllib.request, urllib.error
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/run",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8"))

    def test_run_without_template_returns_run_id(self):
        """POST /run without template just starts a run normally."""
        result = self._post({"task": "test no template", "sync": False})
        self.assertIn("run_id", result, f"Expected run_id, got: {result}")

    def test_run_with_workflow_only_returns_run_id(self):
        """POST /run with workflow but no template starts a run normally."""
        result = self._post({"task": "test workflow only", "workflow": "default", "sync": False})
        self.assertIn("run_id", result, f"Expected run_id, got: {result}")

    def test_run_with_valid_template_and_workflow_returns_run_id(self):
        """POST /run with real template + workflow starts a run."""
        # Use a template that actually exists on disk
        root = PROJECT_ROOT
        tmpl = root / "workflow" / "default" / "todo_templates" / "feature.json"
        if not tmpl.exists():
            self.skipTest("workflow/default/todo_templates/feature.json not found")
        result = self._post({
            "task": "test real template",
            "template": "feature",
            "workflow": "default",
            "sync": False,
        })
        self.assertIn("run_id", result, f"Expected run_id, got: {result}")

    def test_run_missing_task_returns_error(self):
        result = self._post({"template": "feature"})
        # Should get a 422/400 with detail
        self.assertIn("detail", result)


# ============================================================
# 5. EDA Template Schema Validation
# ============================================================

class TestEdaTemplateSchema(unittest.TestCase):
    """Ensure eda/eda-full-loop.json uses the new {name, tasks} format."""

    def setUp(self):
        self._path = PROJECT_ROOT / "workflow" / "eda" / "todo_templates" / "eda-full-loop.json"
        if not self._path.exists():
            self.skipTest("eda-full-loop.json not found")
        self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def test_is_dict_not_list(self):
        self.assertIsInstance(self._data, dict, "eda-full-loop.json must be a dict, not a list")

    def test_has_name_field(self):
        self.assertIn("name", self._data)
        self.assertEqual(self._data["name"], "eda-full-loop")

    def test_has_tasks_list(self):
        self.assertIn("tasks", self._data)
        self.assertIsInstance(self._data["tasks"], list)

    def test_has_six_tasks(self):
        self.assertEqual(len(self._data["tasks"]), 6)

    def test_all_tasks_have_content(self):
        for i, t in enumerate(self._data["tasks"]):
            with self.subTest(i=i):
                self.assertIn("content", t)
                self.assertTrue(t["content"].strip())

    def test_all_tasks_have_priority(self):
        valid = {"high", "normal", "low", "medium"}
        for i, t in enumerate(self._data["tasks"]):
            with self.subTest(i=i):
                self.assertIn("priority", t)
                self.assertIn(t["priority"], valid)

    def test_loop_tasks_have_activeform_with_loop_count(self):
        for i, t in enumerate(self._data["tasks"]):
            if not t.get("loop"):
                continue
            with self.subTest(i=i):
                self.assertIn("activeForm", t)
                self.assertIn("{loop_count}", t["activeForm"],
                              f"Task {i}: loop task activeForm must contain {{loop_count}}")

    def test_loop_tasks_have_max_iterations(self):
        for i, t in enumerate(self._data["tasks"]):
            if not t.get("loop"):
                continue
            with self.subTest(i=i):
                self.assertIn("max_loop_iterations", t)
                self.assertIsInstance(t["max_loop_iterations"], int)
                self.assertGreater(t["max_loop_iterations"], 0)

    def test_loop_tasks_have_exit_condition(self):
        for i, t in enumerate(self._data["tasks"]):
            if not t.get("loop"):
                continue
            with self.subTest(i=i):
                self.assertIn("exit_condition", t)
                self.assertTrue(t["exit_condition"].strip())

    def test_loop_tasks_have_validator(self):
        for i, t in enumerate(self._data["tasks"]):
            if not t.get("loop"):
                continue
            with self.subTest(i=i):
                self.assertIn("validator", t)
                self.assertTrue(t["validator"].strip())

    def test_has_description(self):
        self.assertIn("description", self._data)
        self.assertTrue(self._data["description"].strip())


# ═══════════════════════════════════════════════════════════════════════════════
# Fix 1: Compressor — tool-call annotation in summary text
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompressorToolCallAnnotation(unittest.TestCase):
    """Tool-calling assistant turns (content=None) should be annotated as
    [func_name(arg=val)] so the summarizing LLM knows what was called and
    with what arguments, without emitting raw tool_calls JSON."""

    def _capture_llm(self):
        """Returns (holder_dict, mock_llm_fn).  holder['text'] is the user content
        passed to the LLM (the conversation text to be summarized)."""
        holder = {"text": ""}

        def _mock_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    holder["text"] = m.get("content", "")
            yield "summary"

        return holder, _mock_llm

    def test_tool_call_shows_func_name_and_args(self):
        """content=None + tool_calls → [func(arg=val)] annotation in summary."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Do something"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "function": {"name": "read_file", "arguments": '{"path": "src/main.py"}'},
                    "id": "tc1", "type": "function",
                }],
            },
            {"role": "tool", "tool_call_id": "tc1", "name": "read_file", "content": "result"},
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertIn("read_file", holder["text"])
        self.assertIn("src/main.py", holder["text"])
        self.assertIn("[", holder["text"])

    def test_multiple_tool_calls_all_annotated(self):
        """Multiple tool_calls → all func(args) pairs appear in annotation."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Go"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": '{"path": "a.py"}'}, "id": "t1", "type": "function"},
                    {"function": {"name": "write_file", "arguments": '{"path": "b.py", "content": "x"}'}, "id": "t2", "type": "function"},
                ],
            },
            {"role": "tool", "tool_call_id": "t1", "name": "read_file", "content": "r1"},
            {"role": "tool", "tool_call_id": "t2", "name": "write_file", "content": "r2"},
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertIn("read_file", holder["text"])
        self.assertIn("write_file", holder["text"])
        self.assertIn("a.py", holder["text"])
        self.assertIn("b.py", holder["text"])

    def test_tool_result_still_included(self):
        """Tool result content appears alongside the annotation."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Go"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"function": {"name": "write_file", "arguments": "{}"}, "id": "tc1", "type": "function"}],
            },
            {"role": "tool", "tool_call_id": "tc1", "name": "write_file", "content": "wrote ok"},
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertIn("wrote ok", holder["text"])

    def test_assistant_with_real_content_not_overridden(self):
        """When assistant has actual text, it appears as-is (no annotation)."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "I will help you."},
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertIn("I will help you.", holder["text"])

    def test_no_raw_tool_calls_json_in_text(self):
        """Raw tool_calls JSON structure must not leak into summary input."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Run"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [{"function": {"name": "bash", "arguments": '{"cmd": "ls"}'}, "id": "tc1", "type": "function"}],
            },
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertNotIn('"type": "function"', holder["text"])
        self.assertNotIn("tool_call_id", holder["text"])
        self.assertIn("bash", holder["text"])

    def test_empty_content_no_tool_calls_skipped(self):
        """Assistant with content=None and NO tool_calls → skipped entirely."""
        from core.compressor import _compress_single
        holder, llm = self._capture_llm()
        messages = [
            {"role": "user", "content": "Hmm"},
            {"role": "assistant", "content": None},
        ]
        _compress_single(messages, llm_call_fn=llm)
        self.assertNotIn("assistant:", holder["text"])


# ═══════════════════════════════════════════════════════════════════════════════
# Fix 2: Worker workspace activation — full main-agent parity
# ═══════════════════════════════════════════════════════════════════════════════

class TestWorkerWorkspaceActivation(unittest.TestCase):
    """Verify that _run_react_task activates workspace with the same steps as
    main agent's _setup_workspace."""

    def test_workspace_activation_code_imports_merge_prompt(self):
        """The new activation block must import merge_prompt from workflow.loader."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("merge_prompt", src)

    def test_workspace_activation_patches_compression_prompt(self):
        """Compression prompt patching must be present in _run_react_task source."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("STRUCTURED_SUMMARY_PROMPT", src)
        self.assertIn("compression_prompt_text", src)

    def test_workspace_activation_registers_todo_templates(self):
        """Todo template registry must be set up in _run_react_task source."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("get_todo_template_registry", src)
        self.assertIn("load_from_dir", src)

    def test_workspace_activation_handles_script_hooks(self):
        """Script hook registry must be wired into ReactLoopDeps."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("register_script_hooks", src)
        self.assertIn("_ws_hook_registry", src)

    def test_workspace_activation_registers_slash_commands(self):
        """Worker mode must register workflow slash commands for ATLAS drivers."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("register_workspace_commands", src)
        self.assertIn("_extract_direct_slash_commands", src)

    def test_workspace_activation_patches_todo_rules(self):
        """patch_todo_rules must be called."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("patch_todo_rules", src)

    def test_workspace_activation_handles_force_disable_skills(self):
        """FORCE_SKILLS and DISABLE_SKILLS env vars must be managed."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        self.assertIn("FORCE_SKILLS", src)
        self.assertIn("DISABLE_SKILLS", src)

    def test_ws_hook_registry_passed_to_react_loop_deps(self):
        """ReactLoopDeps must receive _ws_hook_registry, not hardcoded None."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        # Should NOT have bare hook_registry=None anymore
        self.assertNotIn("hook_registry=None", src)
        self.assertIn("hook_registry=_ws_hook_registry", src)

    def test_no_workflow_leaves_hook_registry_none(self):
        """When workflow='', _ws_hook_registry stays None (no activation)."""
        import inspect
        from core import agent_server
        src = inspect.getsource(agent_server._run_react_task)
        # _ws_hook_registry initialized to None before the if-block
        self.assertIn("_ws_hook_registry = None", src)


# ═══════════════════════════════════════════════════════════════════════════════
# Fix 3: Markdown rendering — tree block fencing
# ═══════════════════════════════════════════════════════════════════════════════

class TestFixMdTreeFencing(unittest.TestCase):
    """_fix_md() should wrap directory-tree lines in code fences so Rich's
    Markdown parser doesn't misinterpret box-drawing characters."""

    def _fix(self, text: str) -> str:
        # _fix_md is a module-level function in lib.textual_ui
        # Import it safely (it may fail if Textual is not installed; skip then)
        try:
            from lib.textual_ui import _fix_md
            return _fix_md(text)
        except ImportError:
            self.skipTest("lib.textual_ui not importable (Textual not installed)")

    def test_tree_lines_get_fenced(self):
        """Lines with ├── / └── box-drawing chars should be wrapped in ```."""
        text = "Here is the tree:\n├── src\n│   └── main.py\n└── tests\n"
        result = self._fix(text)
        self.assertIn("```", result)
        # The tree content should be inside the fence
        lines = result.splitlines()
        fence_idx = [i for i, l in enumerate(lines) if l.strip() == "```"]
        self.assertGreaterEqual(len(fence_idx), 2, "Expected at least one open+close fence pair")

    def test_tree_content_preserved_inside_fence(self):
        """Tree content must not be lost — still present after fencing."""
        text = "├── src\n└── tests\n"
        result = self._fix(text)
        self.assertIn("src", result)
        self.assertIn("tests", result)

    def test_existing_fence_not_double_wrapped(self):
        """Content already inside ``` should NOT be wrapped again."""
        text = "```\n├── src\n└── tests\n```\n"
        result = self._fix(text)
        # Count fence markers — should remain 2 (open + close), not 4
        fence_count = sum(1 for l in result.splitlines() if l.strip() == "```")
        self.assertEqual(fence_count, 2)

    def test_normal_markdown_not_fenced(self):
        """Regular markdown (headings, bullets) must not be wrapped in fences."""
        text = "## Title\n\n- item one\n- item two\n"
        result = self._fix(text)
        self.assertNotIn("```", result)

    def test_mixed_content_fences_only_tree_part(self):
        """Only the tree block gets fenced; surrounding markdown text stays clean."""
        text = "Here are the files:\n\n├── a.py\n└── b.py\n\nAnd that's it.\n"
        result = self._fix(text)
        self.assertIn("```", result)
        self.assertIn("Here are the files:", result)
        self.assertIn("And that's it.", result)

    def test_no_tree_chars_no_fence_added(self):
        """Text with no box-drawing chars should not gain any new code fences."""
        text = "Some text.\nAnother line.\n"
        result = self._fix(text)
        self.assertNotIn("```", result)

    def test_horizontal_line_chars_fenced(self):
        """Lines with ─ (horizontal box-drawing) should also be fenced."""
        text = "─────────────\n"
        result = self._fix(text)
        self.assertIn("```", result)

    def test_inline_tree_entries_split_before_fencing(self):
        """Collapsed tree output should become one tree entry per line."""
        text = "simple_pwm/\n├── yaml/simple_pwm.ssot.yaml ├── rtl/simple_pwm.sv └── sim/results.xml\n"
        result = self._fix(text)
        lines = result.splitlines()
        tree_lines = [line for line in lines if "──" in line]
        self.assertEqual(len(tree_lines), 3)
        self.assertTrue(all(line.count("──") == 1 for line in tree_lines))
        self.assertIn("```", result)

    def test_dense_pipeline_box_row_becomes_markdown_list(self):
        """One-line boxed pipeline summaries should render as clean bullets."""
        text = (
            "│ simple_pwm Pipeline Results │ │ Stage │ Result │ │ "
            "1. 디렉토리 생성 │ ✅ 14 subdirs │ │ "
            "2. SSOT 검증 │ ✅ check_ssot_disk.sh PASS │"
        )
        result = self._fix(text)
        self.assertIn("**simple_pwm Pipeline Results**", result)
        self.assertIn("- **1. 디렉토리 생성:** ✅ 14 subdirs", result)
        self.assertIn("- **2. SSOT 검증:** ✅ check_ssot_disk.sh PASS", result)
        self.assertNotIn("│", result)

    def test_accidentally_indented_markdown_summary_is_not_code_fenced(self):
        """Indented prose summaries should stay Markdown, not render as code."""
        text = (
            "The key mental model:\n"
            "    SSOT YAML = the contract/spec\n"
            "    Workflow = factory assembly line\n"
            "    LLM = worker on the line\n"
            "\n"
            "    # The Pipeline (14 stages)\n"
            "\n"
            "    requirement -> ssot-gen -> rtl-gen -> tb-gen -> sim\n"
            "\n"
            "    | Component | Status |\n"
            "    | - | - |\n"
            "    | Core pipeline | ✅ Shipped |\n"
        )
        result = self._fix(text)
        self.assertNotIn("```", result)
        self.assertIn("# The Pipeline (14 stages)", result)
        self.assertIn("SSOT YAML = the contract/spec", result)
        self.assertIn("| Component | Status |", result)
        self.assertNotIn("    # The Pipeline", result)

    def test_colon_intro_with_indented_markdown_keeps_following_markdown(self):
        """A colon-introduced LLM summary must not swallow later Markdown."""
        text = (
            '테스트가 통과한 건 사실상 "APB 레지스터 파일" 테스트입니다:\n'
            "    test_reset -> 리셋 핀 체크\n"
            "    test_iddev_read -> ID 레지스터 읽기\n"
            "\n"
            "    **검증되지 않은 것 (I2C의 핵심):**\n"
            "    - ❌ SCL/SDA 파형 생성\n"
            "    - ❌ ACK/NACK 핸들링\n"
            "\n"
            "    ## 🔧 왜 이렇게 됐나요?\n"
            "\n"
            "    1. **Reference RTL을 거의 그대로 옮겨적었습니다**\n"
        )
        result = self._fix(text)
        self.assertIn("테스트입니다:", result)
        self.assertIn("test_reset -> 리셋 핀 체크", result)
        self.assertIn("**검증되지 않은 것 (I2C의 핵심):**", result)
        self.assertIn("- ❌ SCL/SDA 파형 생성", result)
        self.assertIn("## 🔧 왜 이렇게 됐나요?", result)
        self.assertIn("1. **Reference RTL을 거의 그대로 옮겨적었습니다**", result)
        self.assertNotIn("    ## 🔧", result)
        self.assertNotIn("    - ❌", result)


class TestFixMdLoneBacktickPairing(unittest.TestCase):
    """A lone ``\\``` line is only a fence delimiter when it has a matching
    partner. An UNPAIRED straggler must not be promoted to a ``` fence — else
    Pass 3b auto-closes it at EOF and the whole rest of the message renders as
    one giant grey code block with raw markdown leaking out verbatim."""

    def _fix(self, text: str) -> str:
        try:
            from lib.textual_ui import _fix_md
            return _fix_md(text)
        except ImportError:
            self.skipTest("lib.textual_ui not importable (Textual not installed)")

    @staticmethod
    def _fence_count(result: str) -> int:
        return sum(1 for l in result.splitlines() if l.strip().startswith("```"))

    def test_unpaired_lone_backtick_does_not_open_fence(self):
        """The reported bug: a single stray ``\\``` swallowed the rest of the doc."""
        text = "mental model:\n`\n즉, 이 시스템은:\n\n# 소유권 규칙\n\n| A | B |\n|-|-|\n| x | y |\n"
        result = self._fix(text)
        self.assertEqual(self._fence_count(result), 0, "stray backtick must not open a fence")
        # Heading + table must remain real markdown, not fenced code content
        self.assertIn("# 소유권 규칙", result)

    def test_paired_lone_backticks_become_balanced_fence(self):
        """Two lone backticks intended as a code fence still work, balanced."""
        text = "예시:\n`\ndef foo():\n    return 1\n`\n다음.\n"
        result = self._fix(text)
        self.assertEqual(self._fence_count(result), 2)
        self.assertIn("def foo():", result)

    def test_three_lone_backticks_pair_then_drop_straggler(self):
        """One pair fences; the odd trailing straggler is dropped, not promoted."""
        text = "a\n`\ncode\n`\nb\n`\nc\n\n# Heading\n"
        result = self._fix(text)
        self.assertEqual(self._fence_count(result), 2)
        self.assertIn("# Heading", result)

    def test_real_triple_fence_unaffected(self):
        """A genuine ```python block is untouched by the lone-backtick logic."""
        text = "```python\nprint(1)\n```\n\n# Heading\n"
        result = self._fix(text)
        self.assertEqual(self._fence_count(result), 2)
        self.assertIn("print(1)", result)


class TestReactLoopPromptOnlyReminder(unittest.TestCase):
    """Prompt-only reminders should not rewrite saved conversation history."""

    def test_pre_llm_reminder_uses_llm_message_copy(self):
        import inspect
        from core import react_loop

        src = inspect.getsource(react_loop.run_react_agent_impl)

        self.assertIn("llm_messages = list(llm_messages)", src)
        self.assertIn("llm_messages[_ui][\"content\"] = _uc + _pre_llm_reminder", src)
        self.assertIn("deps.llm_call_fn(llm_messages", src)
        self.assertIn("deps.orchestrator_inject_fn(llm_messages", src)
        self.assertIn("_copy_system_prompt_overlay(llm_messages)", src)
        self.assertNotRegex(src, r"(?m)^\s+messages\[_ui\] = dict\(messages\[_ui\]\)")
        self.assertNotIn("deps.orchestrator_inject_fn(messages", src)


class TestAtlasPipelineOrchestratorNamespace(unittest.TestCase):
    """Pipeline chat should be tracked as the orchestrator workflow."""

    def test_app_treats_orchestrator_as_session_workflow(self):
        src = (PROJECT_ROOT / "frontend/atlas/app.jsx").read_text(encoding="utf-8")
        workspace_src = (PROJECT_ROOT / "frontend/atlas/workspace.jsx").read_text(encoding="utf-8")
        data_src = (PROJECT_ROOT / "frontend/atlas/data.jsx").read_text(encoding="utf-8")
        jobs_src = (PROJECT_ROOT / "src/atlas_api_jobs.py").read_text(encoding="utf-8")

        self.assertIn("'orchestrator'", src)
        self.assertIn("'orchestrator'", data_src)
        self.assertIn("const TOP_WORKFLOWS", src)
        self.assertIn("return ['orchestrator', WORKFLOW_DEFAULT].concat(sorted);", src)
        self.assertIn("wf === 'orchestrator' && execMode !== 'orchestrator'", src)
        self.assertIn("wfParam || normalizeSession(parsed.workflow", src)
        self.assertIn("const defaultWorkflow = execMode === 'orchestrator' ? 'orchestrator' : WORKFLOW_DEFAULT;", src)
        self.assertIn("activateNamespace(owner, ip, 'orchestrator', true, { preserveRunning: true });", src)
        self.assertIn("activeWorkflow={currentWorkflow()}", src)
        self.assertIn("const parsedWf = normalizeSession(parsed.workflow || '');", src)
        self.assertIn("if (parsedWf && parsedWf !== WORKFLOW_DEFAULT) return;", src)
        self.assertIn("const preserveRunning = execMode === 'orchestrator';", src)
        self.assertIn("window.dispatchEvent(new CustomEvent('atlas-workflow-view-request'", src)
        self.assertIn("showNotice(`Viewing ${wf}; orchestrator remains active.`);", src)
        self.assertIn("activateNamespace(owner, ip, wf, true, { preserveRunning });", src)
        self.assertIn("workspace: 'orchestrator',\n        view_workspace: viewWorkflow", workspace_src)
        self.assertIn("Worker chips are a transcript/artifact", workspace_src)
        self.assertIn("session: orchSession", workspace_src)
        self.assertIn("viewOnly: true", workspace_src)
        self.assertIn("if (workflow === 'orchestrator')", workspace_src)
        self.assertIn("worker_direct_chat", workspace_src)
        self.assertIn("setInterval(tick, 2500)", workspace_src)
        self.assertIn("trigger_source", jobs_src)
        self.assertIn("allowInactiveConversation", data_src)
        self.assertIn('raw_workflow and raw_workflow != "orchestrator"', jobs_src)
        self.assertIn("const ORCHESTRATOR_FLOW_STAGE", data_src)
        self.assertIn("return [ORCHESTRATOR_FLOW_STAGE].concat(deduped);", data_src)


class TestGlmCacheDebugOutput(unittest.TestCase):
    """GLM debug output should expose real cache-hit signals."""

    def test_llm_client_debug_reports_prompt_reuse_and_cache_hit(self):
        import inspect
        from src import llm_client

        src = inspect.getsource(llm_client.chat_completion_stream)

        self.assertIn("Cache blocks:", src)
        self.assertIn("Prompt reuse:", src)
        self.assertIn("First diff:", src)
        self.assertIn("Cache hit:", src)
        self.assertIn("Effort cfg:", src)
        self.assertIn("reasoning_effort", src)
        self.assertIn("global _last_debug_prompt_text, _last_debug_messages", src)
        self.assertNotIn("Caching:     {has_structured}", src)


class TestReasoningEffortRouting(unittest.TestCase):
    """Reasoning effort aliases should normalize before request construction."""

    def test_reasoning_effort_aliases_normalize(self):
        from src.llm_client import _normalize_reasoning_effort

        cases = {
            "l": "low",
            "low": "low",
            "m": "medium",
            "med": "medium",
            "mid": "medium",
            "medium": "medium",
            "h": "high",
            "hi": "high",
            "high": "high",
            "x": "xhigh",
            "xh": "xhigh",
            "xhi": "xhigh",
            "max": "xhigh",
            "xhigh": "xhigh",
            "none": "none",
            "off": "medium",
            "bogus": "medium",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertEqual(_normalize_reasoning_effort(raw), expected)

    def test_provider_specific_chat_reasoning_controls(self):
        from unittest.mock import patch
        from src.llm_client import _apply_chat_reasoning_controls

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "medium"
            mock_config.REASONING_EFFORT = "medium"
            mock_config.GLM_THINKING_TYPE = "enabled"
            mock_config.GLM_CLEAR_THINKING = False
            data = {}
            effort, note = _apply_chat_reasoning_controls(data, "deepseek-v4-pro", "https://api.deepseek.com")
            self.assertEqual(effort, "medium")
            self.assertEqual(data["thinking"], {"type": "enabled"})
            self.assertEqual(data["reasoning_effort"], "high")
            self.assertIn("medium->high", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "xhigh"
            mock_config.REASONING_EFFORT = "xhigh"
            data = {}
            effort, note = _apply_chat_reasoning_controls(data, "deepseek-v4-pro", "https://api.deepseek.com")
            self.assertEqual(effort, "xhigh")
            self.assertEqual(data["reasoning_effort"], "max")
            self.assertIn("max", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "none"
            mock_config.REASONING_EFFORT = "none"
            data = {}
            effort, note = _apply_chat_reasoning_controls(data, "deepseek-v4-pro", "https://api.deepseek.com")
            self.assertEqual(effort, "none")
            self.assertEqual(data["thinking"], {"type": "disabled"})
            self.assertNotIn("reasoning_effort", data)
            self.assertIn("disabled", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "high"
            mock_config.REASONING_EFFORT = "high"
            mock_config.GLM_THINKING_TYPE = "enabled"
            mock_config.GLM_CLEAR_THINKING = False
            data = {}
            effort, note = _apply_chat_reasoning_controls(data, "glm-5.1", "https://api.z.ai/api/paas/v4/chat/completions")
            self.assertEqual(effort, "high")
            self.assertEqual(data["thinking"], {"type": "enabled", "clear_thinking": False})
            self.assertNotIn("reasoning_effort", data)
            self.assertIn("no provider effort tier", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "none"
            mock_config.REASONING_EFFORT = "none"
            mock_config.GLM_THINKING_TYPE = "enabled"
            mock_config.GLM_CLEAR_THINKING = False
            data = {}
            effort, note = _apply_chat_reasoning_controls(data, "glm-5.1", "https://api.z.ai/api/paas/v4/chat/completions")
            self.assertEqual(effort, "none")
            self.assertEqual(data["thinking"], {"type": "disabled", "clear_thinking": False})
            self.assertIn("disabled", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "high"
            mock_config.REASONING_EFFORT = "high"
            data = {"reasoning_effort": "stale"}
            effort, note = _apply_chat_reasoning_controls(data, "kimi-2.6", "https://api.kimi.com/coding/v1/chat/completions")
            self.assertEqual(effort, "high")
            self.assertEqual(data["thinking"], {"type": "enabled"})
            self.assertNotIn("reasoning_effort", data)
            self.assertIn("no provider effort tier", note)

        with patch("src.llm_client.config") as mock_config:
            mock_config.REASONING_MODE = "none"
            mock_config.REASONING_EFFORT = "none"
            data = {"reasoning_effort": "stale"}
            effort, note = _apply_chat_reasoning_controls(data, "kimi-2.6", "https://api.moonshot.ai/v1/chat/completions")
            self.assertEqual(effort, "none")
            self.assertEqual(data["thinking"], {"type": "disabled"})
            self.assertNotIn("reasoning_effort", data)
            self.assertIn("disabled", note)


# ═══════════════════════════════════════════════════════════════════════════════
# Fix: Compression accumulation — prior summaries merged, not stacked
# ═══════════════════════════════════════════════════════════════════════════════

class TestCompressorNoSummaryAccumulation(unittest.TestCase):
    """On the second+ compression, the prior summary must be incorporated as
    context into the new compression — not preserved verbatim and stacked.
    Result: always exactly ONE summary in the final history."""

    def _make_cfg(self):
        class Cfg:
            ENABLE_COMPRESSION = True
            COMPRESSION_MODE = "traditional"
            MAX_CONTEXT_TOKENS = 200_000
            COMPRESSION_THRESHOLD = 0.8
            PREEMPTIVE_COMPRESSION_THRESHOLD = 0.7
            COMPRESSION_KEEP_RECENT = 2
            COMPRESSION_CHUNK_SIZE = 10
            COMPRESSION_PRE_ANALYSIS = False
            ENABLE_TURN_PROTECTION = False
            TURN_PROTECTION_COUNT = 2
        return Cfg()

    def _make_llm(self, reply="merged summary"):
        captured = {"texts": []}
        def _llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["texts"].append(m.get("content", ""))
            yield reply
        return captured, _llm

    def _make_messages_with_prior_summary(self, n_new=6):
        """Returns a message list that already contains a previous summary."""
        msgs = [
            {"role": "system", "content": "You are an agent."},
            {"role": "system", "content": "[Previous Conversation Summary (100 messages)]: Earlier the user asked to write a parser."},
            {"role": "user", "content": "Now add error handling"},
            {"role": "assistant", "content": None,
             "tool_calls": [{"function": {"name": "read_file", "arguments": '{"path":"a.py"}'}, "id": "t1", "type": "function"}]},
            {"role": "tool", "tool_call_id": "t1", "name": "read_file", "content": "import json"},
            {"role": "assistant", "content": "Final Answer: done"},
            {"role": "user", "content": "Next task"},
            {"role": "assistant", "content": "Final Answer: ok"},
        ]
        return msgs

    def test_second_compression_produces_single_summary(self):
        """After second compression, only ONE summary system message exists."""
        from core.compressor import compress_history
        cfg = self._make_cfg()
        captured, llm = self._make_llm("unified summary covering everything")
        msgs = self._make_messages_with_prior_summary()

        result = compress_history(msgs, cfg=cfg, llm_call_fn=llm, force=True)

        summary_msgs = [
            m for m in result
            if m.get("role") == "system"
            and "[Previous Conversation Summary" in str(m.get("content", ""))
        ]
        self.assertEqual(len(summary_msgs), 1, f"Expected 1 summary, got {len(summary_msgs)}")

    def test_prior_summary_content_fed_into_new_compression(self):
        """Prior summary text must appear in the conversation_text sent to the LLM."""
        from core.compressor import compress_history
        cfg = self._make_cfg()
        captured, llm = self._make_llm()
        msgs = self._make_messages_with_prior_summary()

        compress_history(msgs, cfg=cfg, llm_call_fn=llm, force=True)

        all_text = " ".join(captured["texts"])
        self.assertIn("Earlier the user asked to write a parser", all_text,
                      "Prior summary content must be passed to new LLM call")

    def test_no_frozen_summary_tag_in_result(self):
        """[FROZEN SUMMARY] tags must not appear in the result."""
        from core.compressor import compress_history
        cfg = self._make_cfg()
        _, llm = self._make_llm()
        msgs = self._make_messages_with_prior_summary()

        result = compress_history(msgs, cfg=cfg, llm_call_fn=llm, force=True)

        for m in result:
            self.assertNotIn("[FROZEN SUMMARY", str(m.get("content", "")))

    def test_triple_compression_still_single_summary(self):
        """After three compressions the result has exactly one summary."""
        from core.compressor import compress_history
        cfg = self._make_cfg()

        # First compression
        msgs1 = [
            {"role": "system", "content": "You are an agent."},
            {"role": "user", "content": "Task 1"},
            {"role": "assistant", "content": "Final Answer: done 1"},
            {"role": "user", "content": "Task 2"},
            {"role": "assistant", "content": "Final Answer: done 2"},
            {"role": "user", "content": "Task 3"},
            {"role": "assistant", "content": "Final Answer: done 3"},
        ]
        _, llm1 = self._make_llm("summary1")
        result1 = compress_history(msgs1, cfg=cfg, llm_call_fn=llm1, force=True)

        # Add new messages and second compression
        result1 += [
            {"role": "user", "content": "Task 4"},
            {"role": "assistant", "content": "Final Answer: done 4"},
            {"role": "user", "content": "Task 5"},
            {"role": "assistant", "content": "Final Answer: done 5"},
        ]
        _, llm2 = self._make_llm("summary2")
        result2 = compress_history(result1, cfg=cfg, llm_call_fn=llm2, force=True)

        # Third compression
        result2 += [
            {"role": "user", "content": "Task 6"},
            {"role": "assistant", "content": "Final Answer: done 6"},
        ]
        _, llm3 = self._make_llm("summary3")
        result3 = compress_history(result2, cfg=cfg, llm_call_fn=llm3, force=True)

        summary_count = sum(
            1 for m in result3
            if m.get("role") == "system"
            and "[Previous Conversation Summary" in str(m.get("content", ""))
        )
        self.assertEqual(summary_count, 1, f"Expected 1 summary after 3 compressions, got {summary_count}")


if __name__ == "__main__":
    unittest.main()
