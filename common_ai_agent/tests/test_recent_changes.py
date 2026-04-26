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


if __name__ == "__main__":
    unittest.main()
