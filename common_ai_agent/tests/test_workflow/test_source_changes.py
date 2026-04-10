"""
Integration / regression tests for the source-file changes on feature_workflow branch.

Covers every behavioral change in:
  src/main.py          — workspace session naming, WORKSPACE_SWITCH signal,
                         dict→str system-prompt conversion, ACTIVE_WORKSPACE_DESC env
  src/llm_client.py    — _resolve_api_key() centralisation
  core/history_manager — empty-file safe load
  core/prompt_builder  — workflow identity injection into system prompt
  core/compressor.py   — workflow identity in compression summary prompt
  core/slash_commands  — /workspace command (show / switch / aliases)
  core/tools_cmux.py   — cmux_restart_modifiable() new workflow/session params,
                         cmux_capture() header

No LLM calls, no network, no subprocess (cmux-dependent paths are unit-tested
via mocking where the logic lives in pure Python).
"""
import builtins
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_this = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))


# ─────────────────────────────────────────────────────────────
# TestResolveApiKey  (src/llm_client.py)
# ─────────────────────────────────────────────────────────────

class TestResolveApiKey(unittest.TestCase):
    """_resolve_api_key() should pick the right key based on the request URL."""

    def setUp(self):
        # Patch config before importing so API_KEY is predictable
        self._orig_env = os.environ.copy()

    def tearDown(self):
        # Restore env changes made during tests
        for k in ["ZAI_API_KEY", "OPENROUTER_API_KEY"]:
            if k in self._orig_env:
                os.environ[k] = self._orig_env[k]
            else:
                os.environ.pop(k, None)

    def _import_fn(self):
        # Re-import each time so patched config is picked up
        import importlib
        import llm_client as lc
        importlib.reload(lc)
        return lc._resolve_api_key

    def test_normal_url_returns_api_key(self):
        fn = self._import_fn()
        import config as cfg
        result = fn("https://api.anthropic.com/v1/messages")
        self.assertEqual(result, cfg.API_KEY)

    def test_zai_url_returns_zai_key(self):
        os.environ["ZAI_API_KEY"] = "zai-test-key"
        fn = self._import_fn()
        result = fn("https://api.z.ai/api/coding/paas/v4/chat/completions")
        self.assertEqual(result, "zai-test-key")

    def test_zai_url_falls_back_to_api_key_when_env_absent(self):
        os.environ.pop("ZAI_API_KEY", None)
        fn = self._import_fn()
        import config as cfg
        result = fn("https://api.z.ai/api/coding/paas/v4/chat/completions")
        self.assertEqual(result, cfg.API_KEY)

    def test_openrouter_url_returns_openrouter_key(self):
        os.environ["OPENROUTER_API_KEY"] = "or-test-key"
        fn = self._import_fn()
        result = fn("https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(result, "or-test-key")

    def test_openrouter_url_falls_back_when_env_absent(self):
        os.environ.pop("OPENROUTER_API_KEY", None)
        fn = self._import_fn()
        import config as cfg
        result = fn("https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(result, cfg.API_KEY)

    def test_unknown_url_returns_default_api_key(self):
        fn = self._import_fn()
        import config as cfg
        result = fn("https://some-other-api.com/v1/chat")
        self.assertEqual(result, cfg.API_KEY)


# ─────────────────────────────────────────────────────────────
# TestLoadHistoryEmptyFile  (core/history_manager.py)
# ─────────────────────────────────────────────────────────────

class TestLoadHistoryEmptyFile(unittest.TestCase):
    """load_conversation_history() should return None for empty files (not crash)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.hist_path = os.path.join(self.tmp, "history.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _cfg(self):
        return types.SimpleNamespace(SAVE_HISTORY=True, HISTORY_FILE=self.hist_path)

    def _load(self):
        from core.history_manager import load_conversation_history
        return load_conversation_history(cfg=self._cfg(), silent=True)

    def test_empty_file_returns_none(self):
        open(self.hist_path, "w").close()          # create empty file
        self.assertIsNone(self._load())

    def test_whitespace_only_file_returns_none(self):
        with open(self.hist_path, "w") as f:
            f.write("   \n\n  ")
        self.assertIsNone(self._load())

    def test_valid_json_still_loads(self):
        messages = [{"role": "user", "content": "hello"}]
        with open(self.hist_path, "w") as f:
            json.dump(messages, f)
        result = self._load()
        self.assertEqual(result, messages)

    def test_invalid_json_returns_none(self):
        with open(self.hist_path, "w") as f:
            f.write("{not valid}")
        self.assertIsNone(self._load())

    def test_missing_file_returns_none(self):
        # file does not exist at all
        self.assertIsNone(self._load())


# ─────────────────────────────────────────────────────────────
# TestPromptBuilderWorkflowIdentity  (core/prompt_builder.py)
# ─────────────────────────────────────────────────────────────

class TestPromptBuilderWorkflowIdentity(unittest.TestCase):
    """build_system_prompt() should prepend [Workflow: X] when ACTIVE_WORKSPACE is set."""

    def setUp(self):
        self._orig_ws   = os.environ.pop("ACTIVE_WORKSPACE", None)
        self._orig_desc = os.environ.pop("ACTIVE_WORKSPACE_DESC", None)

    def tearDown(self):
        if self._orig_ws is not None:
            os.environ["ACTIVE_WORKSPACE"] = self._orig_ws
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)
        if self._orig_desc is not None:
            os.environ["ACTIVE_WORKSPACE_DESC"] = self._orig_desc
        else:
            os.environ.pop("ACTIVE_WORKSPACE_DESC", None)

    def _build(self, **kwargs):
        import importlib
        import core.prompt_builder as pb
        importlib.reload(pb)
        return pb.build_system_prompt(**kwargs)

    def test_no_workspace_no_injection(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)
        result = self._build()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertNotIn("[Workflow:", text)

    def test_workspace_name_injected(self):
        os.environ["ACTIVE_WORKSPACE"] = "mas_gen"
        os.environ.pop("ACTIVE_WORKSPACE_DESC", None)
        result = self._build()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertIn("[Workflow: mas_gen]", text)

    def test_workspace_description_appended(self):
        os.environ["ACTIVE_WORKSPACE"] = "rtl_gen"
        os.environ["ACTIVE_WORKSPACE_DESC"] = "RTL generation agent"
        result = self._build()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertIn("RTL generation agent", text)
        self.assertIn("[Workflow: rtl_gen]", text)

    def test_workspace_identity_at_start_of_prompt(self):
        os.environ["ACTIVE_WORKSPACE"] = "tb_gen"
        os.environ.pop("ACTIVE_WORKSPACE_DESC", None)
        result = self._build()
        if isinstance(result, dict):
            text = result.get("static", "")
        else:
            text = result
        # Identity line should appear near the top (within first 200 chars)
        self.assertIn("[Workflow: tb_gen]", text[:200])


# ─────────────────────────────────────────────────────────────
# TestCompressorWorkflowIdentity  (core/compressor.py)
# ─────────────────────────────────────────────────────────────

class TestCompressorWorkflowIdentity(unittest.TestCase):
    """_compress_single() should prepend [Workflow: X] to summary_prompt when set."""

    def setUp(self):
        self._orig = os.environ.pop("ACTIVE_WORKSPACE", None)

    def tearDown(self):
        if self._orig is not None:
            os.environ["ACTIVE_WORKSPACE"] = self._orig
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)

    def _run_compress(self, workspace):
        """Call _compress_single with a minimal fake LLM that captures the prompt sent to it."""
        captured = {}

        def _fake_llm(messages, **kwargs):
            # summary_prompt is in the *user* message (not system)
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
                if m.get("role") == "system":
                    captured["system"] = m.get("content", "")
            yield "[Summary]"

        if workspace:
            os.environ["ACTIVE_WORKSPACE"] = workspace
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)

        import importlib
        import core.compressor as comp
        importlib.reload(comp)

        sample_messages = [
            {"role": "user", "content": "Write a module"},
            {"role": "assistant", "content": "Sure, here it is."},
        ]
        comp._compress_single(sample_messages, llm_call_fn=_fake_llm)
        return captured

    def test_no_workspace_prompt_unchanged(self):
        captured = self._run_compress(workspace=None)
        # summary_prompt goes into the user message, not system
        user_content = captured.get("user", "")
        self.assertNotIn("[Workflow:", user_content)

    def test_workspace_prepended_to_summary_prompt(self):
        captured = self._run_compress(workspace="mas_gen")
        user_content = captured.get("user", "")
        self.assertIn("[Workflow: mas_gen]", user_content)

    def test_workflow_identity_at_start_of_prompt(self):
        captured = self._run_compress(workspace="sim")
        user_content = captured.get("user", "")
        # Identity should appear near the very beginning of the user message
        idx = user_content.find("[Workflow: sim]")
        self.assertGreaterEqual(idx, 0)
        self.assertLess(idx, 50)


# ─────────────────────────────────────────────────────────────
# TestSlashWorkspaceCommand  (core/slash_commands.py)
# ─────────────────────────────────────────────────────────────

class TestSlashWorkspaceCommand(unittest.TestCase):
    """
    /workspace command:
    - no args  → shows current workspace and available list
    - with name → returns WORKSPACE_SWITCH:<name> signal
    - aliases ws/flow registered
    """

    def setUp(self):
        self._orig_ws = os.environ.pop("ACTIVE_WORKSPACE", None)
        from core.slash_commands import SlashCommandRegistry
        self.reg = SlashCommandRegistry()

    def tearDown(self):
        if self._orig_ws is not None:
            os.environ["ACTIVE_WORKSPACE"] = self._orig_ws
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)

    def _run(self, cmd_line):
        """Use the registry's real execute() method."""
        return self.reg.execute(f"/{cmd_line}")

    def test_workspace_command_registered(self):
        # commands dict uses the command name as key
        self.assertIn("workspace", self.reg.commands)

    def test_ws_alias_registered(self):
        # aliases are stored inside the command entry, not as top-level keys;
        # check via execute routing
        result = self._run("ws rtl_gen")
        self.assertEqual(result, "WORKSPACE_SWITCH:rtl_gen")

    def test_flow_alias_registered(self):
        result = self._run("flow lint")
        self.assertEqual(result, "WORKSPACE_SWITCH:lint")

    def test_no_args_shows_current_workspace(self):
        os.environ["ACTIVE_WORKSPACE"] = "mas_gen"
        result = self._run("workspace")
        self.assertIn("Current workspace:", result)
        self.assertIn("mas_gen", result)

    def test_no_args_shows_available_workspaces(self):
        result = self._run("workspace")
        self.assertIn("Available:", result)

    def test_no_args_active_workspace_marked(self):
        os.environ["ACTIVE_WORKSPACE"] = "default"
        result = self._run("workspace")
        self.assertIn("active", result.lower())

    def test_with_name_returns_switch_signal(self):
        result = self._run("workspace rtl_gen")
        self.assertEqual(result, "WORKSPACE_SWITCH:rtl_gen")

    def test_switch_signal_format(self):
        result = self._run("ws sim")
        self.assertTrue(result.startswith("WORKSPACE_SWITCH:"))
        self.assertEqual(result.split(":", 1)[1], "sim")

    def test_flow_alias_also_switches(self):
        result = self._run("flow lint")
        self.assertEqual(result, "WORKSPACE_SWITCH:lint")

    def test_whitespace_trimmed_in_switch(self):
        # slash command parser splits on first space so args = "  mas_gen  "
        # but _cmd_workspace does args.strip()
        result = self.reg.commands["workspace"]["handler"]("  mas_gen  ")
        self.assertEqual(result, "WORKSPACE_SWITCH:mas_gen")


# ─────────────────────────────────────────────────────────────
# TestCmuxRestartWorkflowParams  (core/tools_cmux.py)
# ─────────────────────────────────────────────────────────────

class TestCmuxRestartWorkflowParams(unittest.TestCase):
    """
    cmux_restart_modifiable() new workflow/session parameters.
    We patch _run() so no real cmux call is made.
    """

    def setUp(self):
        self._orig_ws = os.environ.pop("ACTIVE_WORKSPACE", None)
        self._orig_cmux_ws = os.environ.pop("CMUX_WORKSPACE_ID", None)
        self._orig_cmux_surface = os.environ.pop("CMUX_SURFACE_ID", None)

    def tearDown(self):
        for k, v in [
            ("ACTIVE_WORKSPACE", self._orig_ws),
            ("CMUX_WORKSPACE_ID", self._orig_cmux_ws),
            ("CMUX_SURFACE_ID", self._orig_cmux_surface),
        ]:
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def _import_fn(self):
        import importlib
        import core.tools_cmux as tc
        importlib.reload(tc)
        return tc

    def test_function_accepts_workflow_param(self):
        tc = self._import_fn()
        import inspect
        sig = inspect.signature(tc.cmux_restart_modifiable)
        self.assertIn("workflow", sig.parameters)

    def test_function_accepts_session_param(self):
        tc = self._import_fn()
        import inspect
        sig = inspect.signature(tc.cmux_restart_modifiable)
        self.assertIn("session", sig.parameters)

    def test_workflow_defaults_to_empty_string(self):
        tc = self._import_fn()
        import inspect
        sig = inspect.signature(tc.cmux_restart_modifiable)
        self.assertEqual(sig.parameters["workflow"].default, "")

    def test_session_defaults_to_empty_string(self):
        tc = self._import_fn()
        import inspect
        sig = inspect.signature(tc.cmux_restart_modifiable)
        self.assertEqual(sig.parameters["session"].default, "")


# ─────────────────────────────────────────────────────────────
# TestCmuxCaptureHeader  (core/tools_cmux.py)
# ─────────────────────────────────────────────────────────────

class TestCmuxCaptureHeader(unittest.TestCase):
    """
    cmux_capture() should prepend [workflow=X surface=Y] header.
    We mock _run() to return a known screen string.
    """

    def setUp(self):
        self._orig_ws = os.environ.pop("ACTIVE_WORKSPACE", None)
        self._orig_surface = os.environ.pop("CMUX_SURFACE_ID", None)

    def tearDown(self):
        for k, v in [("ACTIVE_WORKSPACE", self._orig_ws),
                     ("CMUX_SURFACE_ID", self._orig_surface)]:
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    def test_header_prepended_to_screen(self):
        os.environ["ACTIVE_WORKSPACE"] = "mas_gen"
        import importlib
        import core.tools_cmux as tc
        importlib.reload(tc)

        with patch.object(tc, "_run", return_value="screen content here"):
            with patch.object(tc, "_mod_surface", return_value="srf-1"):
                result = tc.cmux_capture()

        self.assertTrue(result.startswith("[workflow="))
        self.assertIn("mas_gen", result)
        self.assertIn("screen content here", result)

    def test_header_contains_surface_id(self):
        os.environ["ACTIVE_WORKSPACE"] = "rtl_gen"
        import importlib
        import core.tools_cmux as tc
        importlib.reload(tc)

        with patch.object(tc, "_run", return_value=""):
            with patch.object(tc, "_mod_surface", return_value="my-surface"):
                result = tc.cmux_capture()

        self.assertIn("surface=my-surface", result)

    def test_header_workflow_key_present(self):
        os.environ["ACTIVE_WORKSPACE"] = "sim"
        import importlib
        import core.tools_cmux as tc
        importlib.reload(tc)

        with patch.object(tc, "_run", return_value="sim output"):
            with patch.object(tc, "_mod_surface", return_value="s1"):
                result = tc.cmux_capture()

        self.assertIn("workflow=sim", result)

    def test_default_workspace_when_env_not_set(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)
        import importlib
        import core.tools_cmux as tc
        importlib.reload(tc)

        with patch.object(tc, "_run", return_value=""):
            with patch.object(tc, "_mod_surface", return_value="s1"):
                result = tc.cmux_capture()

        self.assertIn("[workflow=default", result)


# ─────────────────────────────────────────────────────────────
# TestSetupWorkspaceDictPrompt  (src/main.py patch logic)
# ─────────────────────────────────────────────────────────────

class TestSetupWorkspaceDictPrompt(unittest.TestCase):
    """
    When build_system_prompt returns a dict {static, dynamic},
    _setup_workspace's patched wrapper must merge them into a string
    before calling merge_prompt — otherwise workspace prompt is lost.
    """

    def test_dict_prompt_merged_to_string(self):
        """Simulate the patched _patched_build_system_prompt behaviour."""
        from workflow.loader import merge_prompt

        # Simulate original build returning a dict (new format)
        def orig_build(ctx=None, **kwargs):
            return {"static": "Static part", "dynamic": "Dynamic part"}

        ws_text = "Workspace rules"
        ws_mode = "prepend"

        # This is the logic added in main.py _setup_workspace
        def patched(ctx=None, **kwargs):
            base = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, ws_text, ws_mode)

        result = patched()
        self.assertIsInstance(result, str)
        self.assertIn("Workspace rules", result)
        self.assertIn("Static part", result)
        self.assertIn("Dynamic part", result)

    def test_string_prompt_passes_through(self):
        """When build returns a plain string, logic is unchanged."""
        from workflow.loader import merge_prompt

        def orig_build(ctx=None, **kwargs):
            return "Plain string prompt"

        def patched(ctx=None, **kwargs):
            base = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, "WS rules", "append")

        result = patched()
        self.assertIn("Plain string prompt", result)
        self.assertIn("WS rules", result)

    def test_dict_with_empty_dynamic(self):
        from workflow.loader import merge_prompt

        def orig_build(ctx=None, **kwargs):
            return {"static": "Only static", "dynamic": ""}

        def patched(ctx=None, **kwargs):
            base = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, "WS", "append")

        result = patched()
        self.assertIn("Only static", result)
        self.assertNotIn("\n\n\n", result)


# ─────────────────────────────────────────────────────────────
# TestSessionNameDefaulting  (src/main.py / src/textual_main.py)
# ─────────────────────────────────────────────────────────────

class TestSessionNameDefaulting(unittest.TestCase):
    """
    When -s is not given, session name should be the workspace name.
    When neither -w nor -s is given, session name should be 'default'.
    This tests the _session_name = _args.session or _args.workspace or 'default' logic.
    """

    def _compute_session_name(self, session=None, workspace=None):
        """Replicate the logic from main.py __main__ block."""
        return session or workspace or "default"

    def test_explicit_session_takes_priority(self):
        self.assertEqual(
            self._compute_session_name(session="my-session", workspace="mas_gen"),
            "my-session"
        )

    def test_workspace_used_when_no_session(self):
        self.assertEqual(
            self._compute_session_name(session=None, workspace="rtl_gen"),
            "rtl_gen"
        )

    def test_default_when_neither_given(self):
        self.assertEqual(
            self._compute_session_name(session=None, workspace=None),
            "default"
        )

    def test_empty_string_session_falls_through(self):
        # Empty string is falsy → falls through to workspace
        self.assertEqual(
            self._compute_session_name(session="", workspace="tb_gen"),
            "tb_gen"
        )

    def test_workspace_each_has_own_session(self):
        # Each workspace should produce a distinct session name
        sessions = {
            self._compute_session_name(session=None, workspace=ws)
            for ws in ["mas_gen", "rtl_gen", "tb_gen", "sim", "lint"]
        }
        self.assertEqual(len(sessions), 5)


# ─────────────────────────────────────────────────────────────
# TestSystemPromptRefreshOnHistoryLoad  (src/main.py chat_loop)
# ─────────────────────────────────────────────────────────────

class TestSystemPromptRefreshOnHistoryLoad(unittest.TestCase):
    """
    When loaded history has a stale system message, chat_loop should replace it
    with a freshly built system prompt. Tested as isolated logic (no full
    chat_loop invocation).
    """

    def _refresh_system_prompt(self, messages, new_prompt):
        """Replicate the logic added in chat_loop() for history resume."""
        if messages and messages[0].get("role") == "system":
            messages[0]["content"] = new_prompt
        else:
            messages.insert(0, {"role": "system", "content": new_prompt})
        return messages

    def test_replaces_existing_system_message(self):
        messages = [
            {"role": "system", "content": "OLD STALE PROMPT"},
            {"role": "user", "content": "hello"},
        ]
        result = self._refresh_system_prompt(messages, "NEW FRESH PROMPT")
        self.assertEqual(result[0]["content"], "NEW FRESH PROMPT")
        self.assertEqual(len(result), 2)

    def test_inserts_system_message_when_absent(self):
        messages = [
            {"role": "user", "content": "hello"},
        ]
        result = self._refresh_system_prompt(messages, "NEW PROMPT")
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "NEW PROMPT")
        self.assertEqual(len(result), 2)

    def test_empty_history_gets_system_message(self):
        messages = []
        result = self._refresh_system_prompt(messages, "INIT PROMPT")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "system")

    def test_original_user_messages_preserved(self):
        messages = [
            {"role": "system", "content": "old"},
            {"role": "user", "content": "keep me"},
            {"role": "assistant", "content": "ok"},
        ]
        result = self._refresh_system_prompt(messages, "new prompt")
        self.assertEqual(result[1]["content"], "keep me")
        self.assertEqual(result[2]["content"], "ok")


# ─────────────────────────────────────────────────────────────
# TestWorkspaceSwitchSignal  (WORKSPACE_SWITCH: handling logic)
# ─────────────────────────────────────────────────────────────

class TestWorkspaceSwitchSignal(unittest.TestCase):
    """
    The WORKSPACE_SWITCH: signal parsing and workspace name extraction.
    Tests the parsing logic used in main.py chat_loop.
    """

    def _parse_signal(self, result):
        """Replicate: ws_name = result.split(':', 1)[1].strip()"""
        if result.startswith("WORKSPACE_SWITCH:"):
            return result.split(":", 1)[1].strip()
        return None

    def test_signal_detected(self):
        self.assertIsNotNone(self._parse_signal("WORKSPACE_SWITCH:mas_gen"))

    def test_workspace_name_extracted(self):
        self.assertEqual(self._parse_signal("WORKSPACE_SWITCH:rtl_gen"), "rtl_gen")

    def test_whitespace_stripped(self):
        self.assertEqual(self._parse_signal("WORKSPACE_SWITCH:  sim  "), "sim")

    def test_non_signal_returns_none(self):
        self.assertIsNone(self._parse_signal("MODEL_SWITCH:1"))
        self.assertIsNone(self._parse_signal("some other result"))

    def test_workspace_with_underscore(self):
        self.assertEqual(self._parse_signal("WORKSPACE_SWITCH:tb_gen"), "tb_gen")

    def test_workspace_default(self):
        self.assertEqual(self._parse_signal("WORKSPACE_SWITCH:default"), "default")


if __name__ == "__main__":
    unittest.main()
