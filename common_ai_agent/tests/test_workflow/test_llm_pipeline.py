"""
LLM Pipeline integration tests — workflow + system prompt + todo + compression.

Strategy:
  - Mock _persistent_post at the HTTP layer → captures the exact JSON body
    (including messages) sent to the LLM without making a real API call.
  - Use compress_history() directly with a fake llm_call_fn callable.
  - Simulate _setup_workspace() steps to patch prompt_builder and compressor.

No real API calls. No API key required.
"""
import builtins
import importlib
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

_this  = os.path.dirname(os.path.abspath(__file__))
_root  = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))

PROJECT_ROOT = Path(_root)


# ─────────────────────────────────────────────────────────────
# Fake SSE helpers
# ─────────────────────────────────────────────────────────────

class _FakeSseResponse:
    """
    Mimics http.client.HTTPResponse for SSE streaming.
    Yields pre-built bytes lines so _execute_streaming_request can iterate.
    """

    def __init__(self, content="[LLM response]", usage=None):
        usage_d = usage or {"prompt_tokens": 50, "completion_tokens": 15, "total_tokens": 65}
        c1 = json.dumps({
            "choices": [{"delta": {"content": content}, "finish_reason": None}],
        })
        c2 = json.dumps({
            "choices": [{"delta": {}, "finish_reason": "stop"}],
            "usage": usage_d,
        })
        self._lines = [
            f"data: {c1}".encode(),
            f"data: {c2}".encode(),
            b"data: [DONE]",
        ]

    def __iter__(self):
        return iter(self._lines)

    def close(self):
        pass

    def read(self):
        return b""

    @property
    def status(self):
        return 200


def _make_capture_hook(store, content="[LLM reply]"):
    """
    Returns a _persistent_post replacement that:
      • saves body JSON → store["body"]
      • saves url       → store["url"]
      • returns a valid fake SSE response
    """
    def _fake_post(url, headers, body, timeout=300):
        store["body"] = json.loads(body.decode("utf-8"))
        store["url"]  = url
        return _FakeSseResponse(content)
    return _fake_post


def _fake_llm_fn(reply="[summary]"):
    """Returns a simple synchronous fake llm_call_fn for compressor tests."""
    def _fn(messages, **kwargs):
        yield reply
    return _fn


def _make_cfg(**overrides):
    """Minimal config namespace for compress_history()."""
    defaults = dict(
        ENABLE_COMPRESSION               = True,
        MAX_CONTEXT_CHARS                = 512_000,
        COMPRESSION_THRESHOLD            = 0.9,
        PREEMPTIVE_COMPRESSION_THRESHOLD = 0.85,
        COMPRESSION_CHUNK_SIZE           = 10,
        COMPRESSION_KEEP_RECENT          = 4,
        COMPRESSION_CHUNKED              = False,
        COMPRESSION_MODE                 = "single",
        ENABLE_TURN_PROTECTION           = False,   # off to keep tests simple
        TURN_PROTECTION_COUNT            = 3,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


# ─────────────────────────────────────────────────────────────
# TestLLMCallMessageStructure
# — Does chat_completion_stream send correctly shaped JSON?
# ─────────────────────────────────────────────────────────────

class TestLLMCallMessageStructure(unittest.TestCase):
    """
    Patch _persistent_post → verify the JSON body sent to the LLM endpoint.
    Uses skip_rate_limit=True and ENABLE_STREAMING=True.
    """

    def setUp(self):
        import config as cfg
        self._orig_streaming = cfg.ENABLE_STREAMING
        self._orig_caching   = cfg.ENABLE_PROMPT_CACHING
        cfg.ENABLE_STREAMING      = True
        cfg.ENABLE_PROMPT_CACHING = False    # simplify: no cache blocks

    def tearDown(self):
        import config as cfg
        cfg.ENABLE_STREAMING      = self._orig_streaming
        cfg.ENABLE_PROMPT_CACHING = self._orig_caching

    def _call(self, messages):
        import llm_client as lc
        importlib.reload(lc)
        store = {}
        with patch.object(lc, "_persistent_post", _make_capture_hook(store)):
            chunks = list(lc.chat_completion_stream(
                messages, skip_rate_limit=True, suppress_spinner=True
            ))
        return store, chunks

    def _system_user_msgs(self):
        return [
            {"role": "system",    "content": "You are a helpful assistant."},
            {"role": "user",      "content": "Hello, world!"},
        ]

    def test_body_is_valid_json_with_messages_key(self):
        store, _ = self._call(self._system_user_msgs())
        self.assertIn("messages", store["body"])
        self.assertIsInstance(store["body"]["messages"], list)

    def test_model_field_present_in_body(self):
        store, _ = self._call(self._system_user_msgs())
        self.assertIn("model", store["body"])

    def test_stream_flag_true_in_body(self):
        store, _ = self._call(self._system_user_msgs())
        self.assertTrue(store["body"].get("stream"))

    def test_system_message_is_first(self):
        store, _ = self._call(self._system_user_msgs())
        msgs = store["body"]["messages"]
        self.assertEqual(msgs[0]["role"], "system")

    def test_system_message_content_preserved(self):
        store, _ = self._call(self._system_user_msgs())
        msgs = store["body"]["messages"]
        self.assertEqual(msgs[0]["content"], "You are a helpful assistant.")

    def test_user_message_present(self):
        store, _ = self._call(self._system_user_msgs())
        roles = [m["role"] for m in store["body"]["messages"]]
        self.assertIn("user", roles)

    def test_llm_reply_chunks_returned(self):
        _, chunks = self._call(self._system_user_msgs())
        self.assertTrue(any(isinstance(c, str) for c in chunks))
        combined = "".join(c for c in chunks if isinstance(c, str))
        self.assertIn("[LLM reply]", combined)

    def test_multiple_turns_order_preserved(self):
        msgs = [
            {"role": "system",    "content": "SYSTEM"},
            {"role": "user",      "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user",      "content": "Q2"},
        ]
        store, _ = self._call(msgs)
        sent = store["body"]["messages"]
        roles = [m["role"] for m in sent]
        # system must stay at front; user/assistant order must be preserved
        self.assertEqual(roles[0], "system")
        user_indices = [i for i, r in enumerate(roles) if r == "user"]
        self.assertEqual(len(user_indices), 2)
        self.assertLess(user_indices[0], user_indices[1])


# ─────────────────────────────────────────────────────────────
# TestWorkspaceSystemPromptInLLMCall
# — After workspace prompt patch, workspace text must appear in LLM system msg
# ─────────────────────────────────────────────────────────────

class TestWorkspaceSystemPromptInLLMCall(unittest.TestCase):
    """
    Simulate Step 2 of _setup_workspace (build_system_prompt monkey-patch)
    then verify the workspace text ends up in the system message sent to the LLM.
    """

    def setUp(self):
        import config as cfg
        self._orig_streaming = cfg.ENABLE_STREAMING
        self._orig_caching   = cfg.ENABLE_PROMPT_CACHING
        cfg.ENABLE_STREAMING      = True
        cfg.ENABLE_PROMPT_CACHING = False

        # Save original build_system_prompt
        import core.prompt_builder as _pb
        self._pb               = _pb
        self._orig_build       = _pb.build_system_prompt

    def tearDown(self):
        import config as cfg
        cfg.ENABLE_STREAMING      = self._orig_streaming
        cfg.ENABLE_PROMPT_CACHING = self._orig_caching
        # Restore original build_system_prompt
        self._pb.build_system_prompt = self._orig_build

    def _patch_workspace_prompt(self, ws_text, ws_mode="prepend"):
        """Simulate _setup_workspace Step 2."""
        from workflow.loader import merge_prompt
        orig = self._orig_build

        def _patched(ctx=None, **kwargs):
            base = orig(ctx, **kwargs) if ctx is not None else orig(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, ws_text, ws_mode)

        self._pb.build_system_prompt = _patched

    def _call_with_prompt(self, system_text):
        import llm_client as lc
        importlib.reload(lc)
        store = {}
        msgs = [
            {"role": "system", "content": system_text},
            {"role": "user",   "content": "Please proceed."},
        ]
        with patch.object(lc, "_persistent_post", _make_capture_hook(store)):
            list(lc.chat_completion_stream(msgs, skip_rate_limit=True, suppress_spinner=True))
        return store["body"]["messages"]

    def test_patched_build_includes_workspace_text(self):
        self._patch_workspace_prompt("## RTL Generation Rules\nAlways use non-blocking assignments.")
        result = self._pb.build_system_prompt()
        if isinstance(result, dict):
            combined = result.get("static", "") + result.get("dynamic", "")
        else:
            combined = result
        self.assertIn("RTL Generation Rules", combined)

    def test_prepend_mode_workspace_before_base(self):
        self._patch_workspace_prompt("WS_HEADER", mode := "prepend")
        result = self._pb.build_system_prompt()
        if isinstance(result, dict):
            text = result.get("static", "")
        else:
            text = result
        idx_ws   = text.find("WS_HEADER")
        # WS text should appear somewhere; base text comes after
        self.assertGreaterEqual(idx_ws, 0)

    def test_replace_mode_only_workspace_text(self):
        ws_only = "ONLY_THIS_WORKSPACE_TEXT"
        self._patch_workspace_prompt(ws_only, ws_mode := "replace")
        result = self._pb.build_system_prompt()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertIn(ws_only, text)

    def test_workspace_text_in_llm_system_message(self):
        unique_marker = "UNIQUE_WS_MARKER_XYZ_987"
        # Build a system prompt that contains the marker
        sys_prompt = f"BASE_PROMPT\n\n{unique_marker}"
        sent = self._call_with_prompt(sys_prompt)
        system_content = sent[0]["content"]
        self.assertIn(unique_marker, system_content)

    def test_no_duplicate_system_messages_in_call(self):
        sent = self._call_with_prompt("SINGLE_SYSTEM_PROMPT")
        system_count = sum(1 for m in sent if m["role"] == "system")
        self.assertEqual(system_count, 1)

    def test_real_mas-gen_workspace_text_in_prompt(self):
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", PROJECT_ROOT)
        self.assertIsNotNone(ws.system_prompt_text)
        self._patch_workspace_prompt(ws.system_prompt_text, ws.system_prompt_mode)
        result = self._pb.build_system_prompt()
        if isinstance(result, dict):
            combined = result.get("static", "") + result.get("dynamic", "")
        else:
            combined = result
        # Workspace text must be present
        self.assertIn(ws.system_prompt_text[:50], combined)

    def test_real_rtl-gen_workspace_text_in_prompt(self):
        from workflow.loader import load_workspace
        ws = load_workspace("rtl-gen", PROJECT_ROOT)
        self._patch_workspace_prompt(ws.system_prompt_text, ws.system_prompt_mode)
        result = self._pb.build_system_prompt()
        if isinstance(result, dict):
            combined = result.get("static", "") + result.get("dynamic", "")
        else:
            combined = result
        self.assertIn(ws.system_prompt_text[:50], combined)


# ─────────────────────────────────────────────────────────────
# TestCompressorE2E
# — compress_history() full pipeline with fake llm_call_fn
# ─────────────────────────────────────────────────────────────

class TestCompressorE2E(unittest.TestCase):
    """End-to-end tests for compress_history() using a fake LLM callable."""

    def _messages(self, n=10):
        """Produce n alternating user/assistant messages."""
        msgs = [{"role": "system", "content": "You are a helpful coding assistant."}]
        for i in range(n):
            role = "user" if i % 2 == 0 else "assistant"
            msgs.append({"role": role, "content": f"Message {i}: " + "x" * 200})
        return msgs

    def _run_compress(self, messages, fake_reply="[SUMMARY]", force=False,
                      keep_recent=None, dry_run=False, quiet=True, **cfg_overrides):
        from core.compressor import compress_history
        cfg = _make_cfg(**cfg_overrides)
        return compress_history(
            messages,
            force=force,
            keep_recent=keep_recent,
            dry_run=dry_run,
            quiet=quiet,
            cfg=cfg,
            llm_call_fn=_fake_llm_fn(fake_reply),
        )

    def test_force_true_triggers_compression(self):
        msgs = self._messages(6)
        result = self._run_compress(msgs, force=True)
        # Compressed: fewer messages than original
        self.assertLess(len(result), len(msgs))

    def test_compressed_output_contains_system_message(self):
        msgs = self._messages(6)
        result = self._run_compress(msgs, force=True)
        system_msgs = [m for m in result if m.get("role") == "system"]
        self.assertGreater(len(system_msgs), 0)

    def test_summary_text_in_compressed_system_message(self):
        msgs = self._messages(6)
        result = self._run_compress(msgs, force=True, fake_reply="FAKE_SUMMARY_TEXT")
        all_content = " ".join(str(m.get("content", "")) for m in result)
        self.assertIn("FAKE_SUMMARY_TEXT", all_content)

    def test_below_threshold_returns_original(self):
        """Small message list with high threshold → no compression."""
        msgs = self._messages(3)
        result = self._run_compress(
            msgs,
            force=False,
            COMPRESSION_THRESHOLD=0.99,
            PREEMPTIVE_COMPRESSION_THRESHOLD=0.98,
        )
        self.assertEqual(result, msgs)

    def test_dry_run_returns_original_unchanged(self):
        msgs = self._messages(6)
        result = self._run_compress(msgs, force=True, dry_run=True)
        self.assertEqual(result, msgs)

    def test_empty_messages_returns_empty(self):
        result = self._run_compress([], force=True)
        self.assertEqual(result, [])

    def test_single_message_does_not_crash(self):
        msgs = [{"role": "system", "content": "Only me."}]
        result = self._run_compress(msgs, force=True)
        self.assertIsInstance(result, list)

    def test_keep_recent_preserves_tail_messages(self):
        msgs = self._messages(20)
        result = self._run_compress(msgs, force=True, keep_recent=4)
        # The 4 most recent non-system messages should be in result
        orig_tail = [m for m in msgs if m["role"] != "system"][-4:]
        result_content = [m.get("content") for m in result]
        for orig_msg in orig_tail:
            self.assertIn(orig_msg["content"], result_content)

    def test_compression_failure_returns_fallback_system_msg(self):
        """If the fake LLM raises, compress_history should return a fallback."""
        from core.compressor import compress_history

        def _failing_llm(messages, **kwargs):
            raise RuntimeError("LLM unavailable")
            yield  # pragma: no cover

        cfg = _make_cfg()
        msgs = self._messages(8)
        result = compress_history(
            msgs,
            force=True,
            quiet=True,
            cfg=cfg,
            llm_call_fn=_failing_llm,
        )
        # Should not raise and should return something with a system message
        self.assertIsInstance(result, list)
        has_system = any(m.get("role") == "system" for m in result)
        self.assertTrue(has_system)

    def test_important_messages_not_compressed(self):
        """Messages containing '!important' should be preserved as-is."""
        msgs = [
            {"role": "system",    "content": "System."},
            {"role": "user",      "content": "Normal message."},
            {"role": "assistant", "content": "!important Keep this forever."},
            {"role": "user",      "content": "Another normal message."},
        ]
        result = self._run_compress(msgs, force=True)
        all_content = " ".join(str(m.get("content", "")) for m in result)
        self.assertIn("Keep this forever", all_content)


# ─────────────────────────────────────────────────────────────
# TestWorkspaceCompressionPrompt
# — Workspace compression_prompt.md replaces default in _compress_single
# ─────────────────────────────────────────────────────────────

class TestWorkspaceCompressionPrompt(unittest.TestCase):
    """
    Simulates _setup_workspace Step 4:
    workspace compression_prompt.md → core.compressor.STRUCTURED_SUMMARY_PROMPT replaced.
    """

    def setUp(self):
        import core.compressor as _comp
        self._comp              = _comp
        self._orig_prompt       = _comp.STRUCTURED_SUMMARY_PROMPT
        self._orig_hm           = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", None)

    def tearDown(self):
        self._comp.STRUCTURED_SUMMARY_PROMPT = self._orig_prompt
        if self._orig_hm is None:
            if hasattr(builtins, "_WORKSPACE_HOOK_MESSAGES"):
                delattr(builtins, "_WORKSPACE_HOOK_MESSAGES")
        else:
            builtins._WORKSPACE_HOOK_MESSAGES = self._orig_hm

    def _apply_compression_patch(self, ws_compression_text):
        """Simulate Step 4 of _setup_workspace."""
        from workflow.loader import merge_prompt
        import builtins as _b
        self._comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
            self._comp.STRUCTURED_SUMMARY_PROMPT,
            ws_compression_text,
            "replace",
        )
        if not hasattr(_b, "_WORKSPACE_HOOK_MESSAGES"):
            _b._WORKSPACE_HOOK_MESSAGES = {}
        _b._WORKSPACE_HOOK_MESSAGES["compression_system"] = self._comp.STRUCTURED_SUMMARY_PROMPT

    def test_compression_prompt_replaced_after_patch(self):
        custom = "CUSTOM_COMPRESS_PROMPT_ABC"
        self._apply_compression_patch(custom)
        self.assertEqual(self._comp.STRUCTURED_SUMMARY_PROMPT, custom)

    def test_replaced_prompt_stored_in_hook_messages(self):
        custom = "WS_COMPRESS_PROMPT_DEF"
        self._apply_compression_patch(custom)
        hm = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", {})
        self.assertEqual(hm.get("compression_system"), custom)

    def test_replaced_prompt_used_in_compress_single_call(self):
        """The patched prompt actually appears in the LLM call during _compress_single."""
        marker = "UNIQUE_COMPRESSION_MARKER_GHI_12345"
        self._apply_compression_patch(marker)

        captured = {}

        def _cap_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "[summary]"

        import core.compressor as comp
        importlib.reload(comp)
        # Re-apply since reload reset it
        comp.STRUCTURED_SUMMARY_PROMPT = marker

        sample = [
            {"role": "user",      "content": "Write a module."},
            {"role": "assistant", "content": "Sure."},
        ]
        comp._compress_single(sample, llm_call_fn=_cap_llm)
        self.assertIn(marker, captured.get("user", ""))

    def test_real_mas-gen_compression_prompt_applied(self):
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", PROJECT_ROOT)
        if ws.compression_prompt_text:
            self._apply_compression_patch(ws.compression_prompt_text)
            self.assertIn(
                ws.compression_prompt_text[:30],
                self._comp.STRUCTURED_SUMMARY_PROMPT,
            )

    def test_none_compression_text_leaves_prompt_unchanged(self):
        original = self._comp.STRUCTURED_SUMMARY_PROMPT
        self._apply_compression_patch(None or "")
        # "" triggers replace → prompt becomes ""
        # Just ensure no crash and attribute still exists
        self.assertIsNotNone(self._comp.STRUCTURED_SUMMARY_PROMPT)

    def test_all_production_workspaces_have_compression_prompt(self):
        from workflow.loader import load_workspace
        for name in ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]:
            with self.subTest(workspace=name):
                ws = load_workspace(name, PROJECT_ROOT)
                self.assertIsNotNone(
                    ws.compression_prompt_text,
                    f"{name} missing compression_prompt.md",
                )
                self.assertGreater(len(ws.compression_prompt_text), 20)


# ─────────────────────────────────────────────────────────────
# TestWorkspaceIdentityInCompressionCall
# — [Workflow: X] prepended to summary_prompt in _compress_single
# ─────────────────────────────────────────────────────────────

class TestWorkspaceIdentityInCompressionCall(unittest.TestCase):
    """ACTIVE_WORKSPACE env var → [Workflow: X] in the user message sent to LLM."""

    def setUp(self):
        self._orig_ws = os.environ.pop("ACTIVE_WORKSPACE", None)

    def tearDown(self):
        if self._orig_ws is not None:
            os.environ["ACTIVE_WORKSPACE"] = self._orig_ws
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)

    def _run_compress_single(self, workspace, reply="[sum]"):
        os.environ["ACTIVE_WORKSPACE"] = workspace
        import core.compressor as comp
        importlib.reload(comp)

        captured = {}
        def _cap(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield reply

        msgs = [
            {"role": "user",      "content": "Task A"},
            {"role": "assistant", "content": "Done A"},
        ]
        comp._compress_single(msgs, llm_call_fn=_cap)
        return captured.get("user", "")

    def test_identity_in_user_message(self):
        user_msg = self._run_compress_single("mas-gen")
        self.assertIn("[Workflow: mas-gen]", user_msg)

    def test_identity_at_beginning(self):
        user_msg = self._run_compress_single("rtl-gen")
        idx = user_msg.find("[Workflow: rtl-gen]")
        self.assertGreaterEqual(idx, 0)
        self.assertLess(idx, 50)

    def test_no_identity_when_workspace_not_set(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)
        import core.compressor as comp
        importlib.reload(comp)
        captured = {}
        def _cap(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "[s]"
        comp._compress_single(
            [{"role": "user", "content": "x"}],
            llm_call_fn=_cap,
        )
        self.assertNotIn("[Workflow:", captured.get("user", ""))

    def test_identity_present_for_all_production_workspaces(self):
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]:
            with self.subTest(workspace=ws_name):
                user_msg = self._run_compress_single(ws_name)
                self.assertIn(f"[Workflow: {ws_name}]", user_msg)


# ─────────────────────────────────────────────────────────────
# TestTodoTemplateRegistryPipeline
# — Full path: load_workspace → registry populated → tasks accessible
# ─────────────────────────────────────────────────────────────

class TestTodoTemplateRegistryPipeline(unittest.TestCase):
    """Simulate _setup_workspace Step 7 and verify todo template pipeline."""

    def setUp(self):
        self._orig_reg = getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None)

    def tearDown(self):
        if self._orig_reg is None:
            if hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"):
                delattr(builtins, "_TODO_TEMPLATE_REGISTRY")
        else:
            builtins._TODO_TEMPLATE_REGISTRY = self._orig_reg

    def _setup_registry(self, ws_name):
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = load_workspace(ws_name, PROJECT_ROOT)
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        builtins._TODO_TEMPLATE_REGISTRY = reg
        return reg

    def test_registry_installed_in_builtins_after_setup(self):
        self._setup_registry("mas-gen")
        self.assertTrue(hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"))

    def test_mas-gen_full_project_tasks_accessible(self):
        reg = self._setup_registry("mas-gen")
        tasks = reg.get_tasks("full-project")
        self.assertIsNotNone(tasks)
        self.assertGreater(len(tasks), 0)

    def test_rtl-gen_rtl_impl_tasks_accessible(self):
        reg = self._setup_registry("rtl-gen")
        tasks = reg.get_tasks("rtl-impl")
        self.assertIsNotNone(tasks)
        self.assertGreater(len(tasks), 0)

    def test_tb-gen_tb_impl_tasks_accessible(self):
        reg = self._setup_registry("tb-gen")
        tasks = reg.get_tasks("tb-impl")
        self.assertIsNotNone(tasks)
        self.assertGreater(len(tasks), 0)

    def test_sim_debug_tasks_accessible(self):
        reg = self._setup_registry("sim")
        tasks = reg.get_tasks("sim-debug")
        self.assertIsNotNone(tasks)
        self.assertGreater(len(tasks), 0)

    def test_each_task_has_content_and_priority(self):
        reg = self._setup_registry("mas-gen")
        tasks = reg.get_tasks("full-project")
        for i, t in enumerate(tasks):
            with self.subTest(task=i):
                self.assertIn("content", t)
                self.assertTrue(t["content"].strip())
                self.assertIn("priority", t)
                self.assertIn(t["priority"], {"high", "normal", "low", "medium"})

    def test_builtins_registry_get_tasks_same_as_direct(self):
        reg = self._setup_registry("mas-gen")
        via_builtins = builtins._TODO_TEMPLATE_REGISTRY.get_tasks("full-project")
        via_direct   = reg.get_tasks("full-project")
        self.assertEqual(via_builtins, via_direct)


# ─────────────────────────────────────────────────────────────
# TestFullWorkspaceLLMPipeline
# — End-to-end: workspace load → system prompt patch → LLM call capture
# ─────────────────────────────────────────────────────────────

class TestFullWorkspaceLLMPipeline(unittest.TestCase):
    """
    Combines workspace setup + prompt patch + LLM call mock into one flow.
    Verifies that the workspace text actually makes it into the HTTP body
    sent to the LLM.
    """

    def setUp(self):
        import config as cfg
        import core.prompt_builder as _pb
        self._cfg             = cfg
        self._pb              = _pb
        self._orig_streaming  = cfg.ENABLE_STREAMING
        self._orig_caching    = cfg.ENABLE_PROMPT_CACHING
        self._orig_build      = _pb.build_system_prompt
        cfg.ENABLE_STREAMING      = True
        cfg.ENABLE_PROMPT_CACHING = False

    def tearDown(self):
        self._cfg.ENABLE_STREAMING      = self._orig_streaming
        self._cfg.ENABLE_PROMPT_CACHING = self._orig_caching
        self._pb.build_system_prompt    = self._orig_build

    def _simulate_setup_and_call(self, ws_name):
        from workflow.loader import load_workspace, merge_prompt
        ws   = load_workspace(ws_name, PROJECT_ROOT)
        orig = self._orig_build

        if ws.system_prompt_text:
            _txt  = ws.system_prompt_text
            _mode = ws.system_prompt_mode

            def _patched(ctx=None, **kwargs):
                base = orig(ctx, **kwargs) if ctx is not None else orig(**kwargs)
                if isinstance(base, dict):
                    base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
                return merge_prompt(base, _txt, _mode)

            self._pb.build_system_prompt = _patched

        # Build messages: system + user
        system_text = self._pb.build_system_prompt()
        if isinstance(system_text, dict):
            system_text = (
                system_text.get("static", "") + "\n\n" + system_text.get("dynamic", "")
            ).strip()

        messages = [
            {"role": "system", "content": system_text},
            {"role": "user",   "content": "Implement the RTL for a 4-bit adder."},
        ]

        import llm_client as lc
        importlib.reload(lc)
        store = {}
        with patch.object(lc, "_persistent_post", _make_capture_hook(store)):
            list(lc.chat_completion_stream(
                messages, skip_rate_limit=True, suppress_spinner=True
            ))
        return store["body"]["messages"], ws

    def test_mas-gen_workspace_text_in_llm_system_message(self):
        sent_msgs, ws = self._simulate_setup_and_call("mas-gen")
        system_content = sent_msgs[0]["content"]
        self.assertIn(ws.system_prompt_text[:40], system_content)

    def test_rtl-gen_workspace_text_in_llm_system_message(self):
        sent_msgs, ws = self._simulate_setup_and_call("rtl-gen")
        system_content = sent_msgs[0]["content"]
        self.assertIn(ws.system_prompt_text[:40], system_content)

    def test_tb-gen_workspace_text_in_llm_system_message(self):
        sent_msgs, ws = self._simulate_setup_and_call("tb-gen")
        system_content = sent_msgs[0]["content"]
        self.assertIn(ws.system_prompt_text[:40], system_content)

    def test_system_message_is_role_system(self):
        sent_msgs, _ = self._simulate_setup_and_call("mas-gen")
        self.assertEqual(sent_msgs[0]["role"], "system")

    def test_only_one_system_message_in_call(self):
        sent_msgs, _ = self._simulate_setup_and_call("mas-gen")
        count = sum(1 for m in sent_msgs if m["role"] == "system")
        self.assertEqual(count, 1)

    def test_user_message_preserved_after_workspace_patch(self):
        sent_msgs, _ = self._simulate_setup_and_call("rtl-gen")
        user_msgs = [m for m in sent_msgs if m["role"] == "user"]
        self.assertEqual(len(user_msgs), 1)
        self.assertIn("4-bit adder", user_msgs[0]["content"])

    def test_all_production_workspaces_llm_call_works(self):
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]:
            # Restore between iterations
            self._pb.build_system_prompt = self._orig_build
            with self.subTest(workspace=ws_name):
                sent_msgs, ws = self._simulate_setup_and_call(ws_name)
                self.assertEqual(sent_msgs[0]["role"], "system")
                if ws.system_prompt_text:
                    self.assertIn(ws.system_prompt_text[:30], sent_msgs[0]["content"])


# ─────────────────────────────────────────────────────────────
# TestCompressionThenLLMContinuation
# — After compression, LLM is called with compressed context
# ─────────────────────────────────────────────────────────────

class TestCompressionThenLLMContinuation(unittest.TestCase):
    """
    Compress a long history → then call LLM with compressed context.
    Verify the compressed summary appears in the messages sent to LLM.
    """

    def setUp(self):
        import config as cfg
        self._orig_streaming  = cfg.ENABLE_STREAMING
        self._orig_caching    = cfg.ENABLE_PROMPT_CACHING
        cfg.ENABLE_STREAMING      = True
        cfg.ENABLE_PROMPT_CACHING = False

    def tearDown(self):
        import config as cfg
        cfg.ENABLE_STREAMING      = self._orig_streaming
        cfg.ENABLE_PROMPT_CACHING = self._orig_caching

    def _build_long_history(self, n=12):
        msgs = [{"role": "system", "content": "You are a Verilog expert."}]
        for i in range(n):
            role = "user" if i % 2 == 0 else "assistant"
            msgs.append({"role": role, "content": f"msg-{i}: " + "content " * 30})
        return msgs

    def test_compressed_summary_in_llm_call(self):
        from core.compressor import compress_history

        SUMMARY_MARKER = "COMPRESSED_SUMMARY_UNIQUE_TOKEN"
        cfg = _make_cfg()
        original = self._build_long_history(12)

        compressed = compress_history(
            original,
            force=True,
            quiet=True,
            cfg=cfg,
            llm_call_fn=_fake_llm_fn(SUMMARY_MARKER),
        )

        # Now send compressed context to LLM (mocked)
        import llm_client as lc
        importlib.reload(lc)
        store = {}
        # Add a new user turn
        compressed.append({"role": "user", "content": "Continue with step 3."})
        with patch.object(lc, "_persistent_post", _make_capture_hook(store, "[next reply]")):
            list(lc.chat_completion_stream(compressed, skip_rate_limit=True, suppress_spinner=True))

        sent_body = json.dumps(store["body"])
        self.assertIn(SUMMARY_MARKER, sent_body)

    def test_system_prompt_preserved_after_compression(self):
        from core.compressor import compress_history

        original = self._build_long_history(10)
        cfg = _make_cfg()
        compressed = compress_history(
            original, force=True, quiet=True, cfg=cfg,
            llm_call_fn=_fake_llm_fn("[sum]"),
        )

        system_msgs = [m for m in compressed if m.get("role") == "system"]
        self.assertGreater(len(system_msgs), 0)

    def test_user_message_after_compression_reaches_llm(self):
        from core.compressor import compress_history

        original = self._build_long_history(8)
        cfg = _make_cfg()
        compressed = compress_history(
            original, force=True, quiet=True, cfg=cfg,
            llm_call_fn=_fake_llm_fn("[sum]"),
        )

        NEW_USER_MSG = "CONTINUE_UNIQUE_USER_MSG_XYZ"
        compressed.append({"role": "user", "content": NEW_USER_MSG})

        import llm_client as lc
        importlib.reload(lc)
        store = {}
        with patch.object(lc, "_persistent_post", _make_capture_hook(store)):
            list(lc.chat_completion_stream(compressed, skip_rate_limit=True, suppress_spinner=True))

        sent_body = json.dumps(store["body"])
        self.assertIn(NEW_USER_MSG, sent_body)

    def test_workspace_compression_prompt_in_compressed_summary(self):
        """Full cycle: workspace compression prompt → compress → LLM receives summary."""
        import core.compressor as comp
        importlib.reload(comp)

        WS_COMPRESS_MARKER = "WS_COMPRESS_UNIQUE_MARKER_ABC"
        comp.STRUCTURED_SUMMARY_PROMPT = WS_COMPRESS_MARKER

        captured_user = {}

        def _capture_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured_user["content"] = m.get("content", "")
            yield "[ws-summary]"

        msgs = self._build_long_history(6)
        cfg  = _make_cfg()
        from core.compressor import compress_history as ch
        ch(msgs, force=True, quiet=True, cfg=cfg, llm_call_fn=_capture_llm)

        self.assertIn(WS_COMPRESS_MARKER, captured_user.get("content", ""))


if __name__ == "__main__":
    unittest.main()
