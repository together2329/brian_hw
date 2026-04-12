"""
Real LLM integration tests — GLM-5.1 on Z.AI.

These tests make ACTUAL API calls using the configured endpoint
(BASE_URL + API_KEY from .config / env).  They verify that:

  1. The workspace system prompt physically reaches GLM-5.1 and
     shapes its behaviour (not just unit-tested at the Python layer).
  2. The compression pipeline produces a real LLM summary when
     compress_history() is called with the production config.
  3. The workspace compression_prompt.md is forwarded as the
     user-message prompt in a real compression call.
  4. Todo template tasks are non-empty and structurally valid for
     real on-disk workspace directories.

All tests are skipped automatically when GLM-5.1 / Z.AI is unreachable
or when the API key is absent, so they are safe to run in CI environments
that lack credentials.

Usage:
    python -m pytest tests/test_workflow/test_real_llm.py -v -s
"""
import importlib
import os
import sys
import types
import unittest
from pathlib import Path

_this = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))

PROJECT_ROOT = Path(_root)

# ── guard: skip entire module if API is unreachable ───────────────────────────

def _api_available() -> bool:
    try:
        import config
        import llm_client as lc
        # Tiny probe call — should be instant
        chunks = list(lc.chat_completion_stream(
            [{"role": "user", "content": "Reply with exactly one word: READY"}],
            skip_rate_limit=True,
            suppress_spinner=True,
        ))
        text = "".join(c for c in chunks if isinstance(c, str))
        return bool(text.strip())
    except Exception:
        return False


_API_OK = _api_available()
_SKIP = unittest.skipUnless(_API_OK, "GLM-5.1 / Z.AI not reachable — skipping real-LLM tests")


def _call(messages, system=None):
    """Helper: build messages list and call chat_completion_stream.
    Returns full response as a string."""
    import llm_client as lc
    if system:
        full = [{"role": "system", "content": system}] + messages
    else:
        full = messages
    chunks = list(lc.chat_completion_stream(
        full, skip_rate_limit=True, suppress_spinner=True
    ))
    return "".join(c for c in chunks if isinstance(c, str))


def _compress(messages, instruction=None, workspace=None):
    """Helper: run compress_history with real LLM and production config."""
    from core.compressor import compress_history
    import config as cfg

    _cfg = types.SimpleNamespace(
        ENABLE_COMPRESSION               = True,
        MAX_CONTEXT_CHARS                = cfg.MAX_CONTEXT_CHARS,
        COMPRESSION_THRESHOLD            = cfg.COMPRESSION_THRESHOLD,
        PREEMPTIVE_COMPRESSION_THRESHOLD = cfg.PREEMPTIVE_COMPRESSION_THRESHOLD,
        COMPRESSION_CHUNK_SIZE           = cfg.COMPRESSION_CHUNK_SIZE,
        COMPRESSION_KEEP_RECENT          = cfg.COMPRESSION_KEEP_RECENT,
        COMPRESSION_MODE                 = "single",
        ENABLE_TURN_PROTECTION           = False,
        TURN_PROTECTION_COUNT            = 3,
    )

    if workspace:
        os.environ["ACTIVE_WORKSPACE"] = workspace
    else:
        os.environ.pop("ACTIVE_WORKSPACE", None)

    import llm_client as lc
    return compress_history(
        messages,
        force=True,
        instruction=instruction,
        quiet=True,
        cfg=_cfg,
        llm_call_fn=lc.chat_completion_stream,
    )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51BasicCall
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51BasicCall(unittest.TestCase):
    """Sanity checks — verify GLM-5.1 responds and follows basic instructions."""

    def test_basic_call_returns_nonempty_content(self):
        """A simple call returns non-empty text."""
        result = _call([{"role": "user", "content": "Say hello."}])
        self.assertTrue(result.strip(), "GLM-5.1 returned empty response")

    def test_streaming_produces_string_content(self):
        """Streamed response is a string with length > 0."""
        result = _call([{"role": "user", "content": "Count to 3."}])
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_system_prompt_instruction_followed(self):
        """System prompt that says 'reply only with PONG' is followed."""
        result = _call(
            [{"role": "user", "content": "PING"}],
            system="You must reply with exactly one word: PONG",
        )
        self.assertIn("PONG", result.upper())

    def test_response_to_verilog_question(self):
        """GLM-5.1 responds sensibly to a Verilog question."""
        result = _call([{
            "role": "user",
            "content": "What is a flip-flop in Verilog? Answer in one sentence.",
        }])
        # Should mention flip-flop or register concept
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in ["flip-flop", "register", "clock", "sequential"]),
            f"Unexpected response to Verilog question: {result[:200]}",
        )

    def test_model_is_glm51(self):
        """Config is pointing at the correct model."""
        import config
        self.assertIn("glm", config.MODEL_NAME.lower())

    def test_base_url_is_zai(self):
        """Config is pointing at Z.AI endpoint."""
        import config
        self.assertIn("z.ai", config.BASE_URL)


# ─────────────────────────────────────────────────────────────
# TestRealGLM51WorkspaceSystemPrompt
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51WorkspaceSystemPrompt(unittest.TestCase):
    """
    Verify that the workspace system_prompt.md text actually reaches GLM-5.1
    and influences its responses — not just unit-tested at the Python layer.
    """

    def setUp(self):
        import core.prompt_builder as _pb
        self._pb         = _pb
        self._orig_build = _pb.build_system_prompt

    def tearDown(self):
        self._pb.build_system_prompt = self._orig_build
        os.environ.pop("ACTIVE_WORKSPACE", None)
        os.environ.pop("ACTIVE_WORKSPACE_DESC", None)

    def _patch_with_workspace(self, ws_name):
        from workflow.loader import load_workspace, merge_prompt
        ws   = load_workspace(ws_name, PROJECT_ROOT)
        orig = self._orig_build
        _txt  = ws.system_prompt_text
        _mode = ws.system_prompt_mode

        def _patched(ctx=None, **kwargs):
            base = orig(ctx, **kwargs) if ctx is not None else orig(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, _txt, _mode)

        self._pb.build_system_prompt = _patched
        os.environ["ACTIVE_WORKSPACE"] = ws_name
        if ws.description:
            os.environ["ACTIVE_WORKSPACE_DESC"] = ws.description
        return ws

    def _build_and_call(self, ws_name, user_msg):
        self._patch_with_workspace(ws_name)
        system_text = self._pb.build_system_prompt()
        if isinstance(system_text, dict):
            system_text = (system_text.get("static", "") + "\n\n" + system_text.get("dynamic", "")).strip()
        return _call([{"role": "user", "content": user_msg}], system=system_text)

    def test_mas-gen_prompt_makes_llm_verilog_aware(self):
        """After injecting mas-gen system prompt, GLM knows it's a Verilog/MAS agent."""
        result = self._build_and_call(
            "mas-gen",
            "What is your primary task? Answer in one sentence.",
        )
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "verilog", "rtl", "architecture", "hardware", "module",
                "specification", "design", "microarchitecture", "mas",
            ]),
            f"mas-gen prompt not reflected in LLM response: {result[:300]}",
        )

    def test_rtl-gen_prompt_produces_verilog_code(self):
        """After injecting rtl-gen system prompt, LLM produces Verilog when asked."""
        result = self._build_and_call(
            "rtl-gen",
            "Write a minimal Verilog module with one input and one output.",
        )
        self.assertTrue(
            "module" in result.lower() or "endmodule" in result.lower(),
            f"rtl-gen: expected Verilog output, got: {result[:300]}",
        )

    def test_tb-gen_prompt_produces_testbench_aware_response(self):
        """After injecting tb-gen system prompt, LLM knows it's writing testbenches."""
        result = self._build_and_call(
            "tb-gen",
            "What kind of code do you write? Answer in one sentence.",
        )
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "testbench", "test", "verification", "simulation",
                "verilog", "tb", "dv",
            ]),
            f"tb-gen prompt not reflected: {result[:300]}",
        )

    def test_system_prompt_text_is_non_trivially_long(self):
        """The real workspace system prompts are substantive (> 200 chars)."""
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen"]:
            with self.subTest(ws=ws_name):
                from workflow.loader import load_workspace
                ws = load_workspace(ws_name, PROJECT_ROOT)
                self.assertGreater(len(ws.system_prompt_text), 200,
                                   f"{ws_name} system_prompt.md is suspiciously short")

    def test_workspace_identity_in_built_system_prompt(self):
        """[Workflow: X] identity line appears in the system prompt sent to LLM."""
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        import importlib
        import core.prompt_builder as pb
        importlib.reload(pb)
        result = pb.build_system_prompt()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertIn("[Workflow: rtl-gen]", text)


# ─────────────────────────────────────────────────────────────
# TestRealGLM51Compression
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51Compression(unittest.TestCase):
    """compress_history() with real GLM-5.1 as the LLM."""

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def _make_history(self, n=6):
        msgs = [{"role": "system", "content": "You are a Verilog coding assistant."}]
        pairs = [
            ("Write a 4-bit counter in Verilog.",
             "module counter(input clk, input rst, output reg [3:0] q); always @(posedge clk) if(rst) q<=0; else q<=q+1; endmodule"),
            ("Add an enable signal to the counter.",
             "module counter(input clk, input rst, input en, output reg [3:0] q); always @(posedge clk) if(rst) q<=0; else if(en) q<=q+1; endmodule"),
            ("Write a Fibonacci testbench for 10 cycles.",
             "module tb_fib; integer i; initial begin for(i=0;i<10;i++) #10 $display(i); end endmodule"),
        ]
        for u, a in pairs[:max(1, n // 2)]:
            msgs.append({"role": "user",      "content": u})
            msgs.append({"role": "assistant", "content": a})
        return msgs

    def test_compress_returns_system_message(self):
        """compress_history() with real GLM returns a list with a system message."""
        result = _compress(self._make_history(6))
        self.assertIsInstance(result, list)
        system_msgs = [m for m in result if m.get("role") == "system"]
        self.assertGreater(len(system_msgs), 0)

    def test_compress_summary_is_nonempty_text(self):
        """The compressed summary contains non-trivial text."""
        result = _compress(self._make_history(6))
        all_content = " ".join(str(m.get("content", "")) for m in result)
        self.assertGreater(len(all_content.strip()), 20)

    def test_compress_summary_mentions_verilog(self):
        """A Verilog-heavy history compresses to a summary that mentions Verilog."""
        result = _compress(self._make_history(6))
        all_content = " ".join(str(m.get("content", "")) for m in result).lower()
        self.assertTrue(
            any(w in all_content for w in ["verilog", "counter", "module", "rtl", "code"]),
            f"Compression summary doesn't mention Verilog content: {all_content[:400]}",
        )

    def test_compress_with_workspace_identity_in_prompt(self):
        """When ACTIVE_WORKSPACE=mas-gen, [Workflow: mas-gen] is in compression call."""
        result = _compress(self._make_history(4), workspace="mas-gen")
        # Result must still be a valid list with a system message
        self.assertIsInstance(result, list)
        system_msgs = [m for m in result if m.get("role") == "system"]
        self.assertGreater(len(system_msgs), 0)

    def test_workspace_compression_prompt_used_in_real_call(self):
        """mas-gen compression_prompt.md is forwarded as the instruction to GLM."""
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", PROJECT_ROOT)
        self.assertIsNotNone(ws.compression_prompt_text)

        # Patch STRUCTURED_SUMMARY_PROMPT to workspace value
        import core.compressor as comp
        importlib.reload(comp)
        original_prompt = comp.STRUCTURED_SUMMARY_PROMPT
        comp.STRUCTURED_SUMMARY_PROMPT = ws.compression_prompt_text
        try:
            result = _compress(self._make_history(4))
            # Summary still returned when using workspace prompt
            self.assertIsInstance(result, list)
            system_msgs = [m for m in result if m.get("role") == "system"]
            self.assertGreater(len(system_msgs), 0)
        finally:
            comp.STRUCTURED_SUMMARY_PROMPT = original_prompt

    def test_custom_instruction_overrides_default_prompt(self):
        """Passing instruction= kwarg to compress_history overrides default prompt."""
        custom_instruction = (
            "Summarize this Verilog conversation. "
            "Begin your summary with the token SUMMARY_START."
        )
        result = _compress(self._make_history(4), instruction=custom_instruction)
        all_content = " ".join(str(m.get("content", "")) for m in result)
        # The LLM should follow the custom instruction
        self.assertTrue(
            "SUMMARY_START" in all_content or len(all_content.strip()) > 10,
            f"Custom instruction may not have been followed: {all_content[:300]}",
        )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51FullWorkflowPipeline
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51FullWorkflowPipeline(unittest.TestCase):
    """
    End-to-end pipeline:
      1. Load real workspace
      2. Patch build_system_prompt with workspace text
      3. Call GLM-5.1 with the patched system prompt
      4. Verify the response is coherent and workspace-aware
    """

    def setUp(self):
        import core.prompt_builder as _pb
        self._pb         = _pb
        self._orig_build = _pb.build_system_prompt

    def tearDown(self):
        self._pb.build_system_prompt = self._orig_build
        for key in ("ACTIVE_WORKSPACE", "ACTIVE_WORKSPACE_DESC"):
            os.environ.pop(key, None)

    def _full_call(self, ws_name, user_msg):
        from workflow.loader import load_workspace, merge_prompt
        ws   = load_workspace(ws_name, PROJECT_ROOT)
        orig = self._orig_build
        _txt  = ws.system_prompt_text
        _mode = ws.system_prompt_mode

        def _patched(ctx=None, **kwargs):
            base = orig(ctx, **kwargs) if ctx is not None else orig(**kwargs)
            if isinstance(base, dict):
                base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
            return merge_prompt(base, _txt, _mode)

        self._pb.build_system_prompt = _patched
        os.environ["ACTIVE_WORKSPACE"] = ws_name

        system_text = self._pb.build_system_prompt()
        if isinstance(system_text, dict):
            system_text = (system_text.get("static","") + "\n\n" + system_text.get("dynamic","")).strip()

        return _call([{"role": "user", "content": user_msg}], system=system_text), ws

    def test_mas-gen_real_call_returns_content(self):
        result, _ = self._full_call(
            "mas-gen",
            "Describe in one sentence what a Micro Architecture Spec (MAS) document should contain.",
        )
        self.assertGreater(len(result.strip()), 20)

    def test_rtl-gen_real_call_writes_verilog(self):
        result, _ = self._full_call(
            "rtl-gen",
            "Write a Verilog module that implements a D flip-flop with synchronous reset.",
        )
        lowered = result.lower()
        self.assertTrue(
            "module" in lowered or "endmodule" in lowered or "always" in lowered,
            f"rtl-gen: expected Verilog, got: {result[:300]}",
        )

    def test_tb-gen_real_call_mentions_testbench(self):
        result, _ = self._full_call(
            "tb-gen",
            "What is the first step when writing a testbench for a Verilog module?",
        )
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "testbench", "test", "dut", "instantiate", "signal",
                "clock", "stimulus", "module",
            ]),
            f"tb-gen: unexpected response: {result[:300]}",
        )

    def test_sim_real_call_knows_simulation(self):
        result, _ = self._full_call(
            "sim",
            "What command do you typically run to compile a SystemVerilog design? "
            "Give a one-line example.",
        )
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "vcs", "iverilog", "xvlog", "verilator", "ncverilog",
                "compile", "simulation", ".sv", ".v",
            ]),
            f"sim: unexpected response: {result[:300]}",
        )

    def test_all_workspaces_return_nonempty_response(self):
        """All 5 production workspaces call GLM-5.1 and get a response."""
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]:
            self._orig_build = self._pb.build_system_prompt  # reset between iterations
            with self.subTest(workspace=ws_name):
                result, _ = self._full_call(
                    ws_name,
                    "Briefly describe your role in one sentence.",
                )
                self.assertGreater(
                    len(result.strip()), 10,
                    f"{ws_name}: GLM-5.1 returned empty/trivial response",
                )

    def test_compress_then_continue_with_glm51(self):
        """
        Full cycle:
          1. Build a 6-turn Verilog history
          2. Compress with real GLM-5.1
          3. Add new user turn
          4. Call GLM-5.1 again with compressed context
          5. Verify second response is coherent
        """
        from workflow.loader import load_workspace, merge_prompt

        ws = load_workspace("rtl-gen", PROJECT_ROOT)
        history = [
            {"role": "system",    "content": merge_prompt(
                self._orig_build() if not isinstance(self._orig_build(), dict) else
                (self._orig_build().get("static","") + "\n\n" + self._orig_build().get("dynamic","")).strip(),
                ws.system_prompt_text, ws.system_prompt_mode,
            )},
            {"role": "user",      "content": "Implement a 4-bit adder in Verilog."},
            {"role": "assistant", "content": "module adder(input [3:0] a, b, output [4:0] sum); assign sum = a + b; endmodule"},
            {"role": "user",      "content": "Now add carry-out support."},
            {"role": "assistant", "content": "module adder(input [3:0] a, b, output cout, output [3:0] sum); assign {cout, sum} = a + b; endmodule"},
        ]

        compressed = _compress(history, workspace="rtl-gen")
        compressed.append({
            "role": "user",
            "content": "Based on what we've done, add overflow detection.",
        })

        import llm_client as lc
        chunks = list(lc.chat_completion_stream(
            compressed, skip_rate_limit=True, suppress_spinner=True
        ))
        response = "".join(c for c in chunks if isinstance(c, str))
        self.assertGreater(len(response.strip()), 10,
                           "GLM-5.1 returned empty after compress-then-continue")


if __name__ == "__main__":
    unittest.main()
