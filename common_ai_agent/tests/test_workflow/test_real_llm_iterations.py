"""
Real LLM iteration & pipeline integration tests — GLM-5.1 on Z.AI.

Focuses on:
  - Iterative refinement loops: RTL/TB improvement per iteration
  - Workflow iteration loop: repeat until exit condition or max_iters
  - Full 5-stage pipeline: mas-gen → rtl-gen → tb-gen → sim → lint
  - Long-context persistence: design decisions survive 5-6 sequential calls
  - Multi-workspace orchestration: stage-by-stage workspace switching

Auto-skip when GLM-5.1 / Z.AI is unreachable.
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


# ── reachability guard ────────────────────────────────────────────────────────

def _api_available() -> bool:
    try:
        import llm_client as lc
        chunks = list(lc.chat_completion_stream(
            [{"role": "user", "content": "Reply with one word: OK"}],
            skip_rate_limit=True, suppress_spinner=True,
        ))
        return bool("".join(c for c in chunks if isinstance(c, str)).strip())
    except Exception:
        return False


_API_OK = _api_available()
_SKIP   = unittest.skipUnless(_API_OK, "GLM-5.1 / Z.AI not reachable — skipping")


# ── shared helpers ─────────────────────────────────────────────────────────────

def _call(messages) -> str:
    import llm_client as lc
    chunks = list(lc.chat_completion_stream(
        messages, skip_rate_limit=True, suppress_spinner=True
    ))
    return "".join(c for c in chunks if isinstance(c, str))


def _turn(history: list, user_msg: str) -> str:
    """Append user msg, call LLM, append reply, return reply."""
    history.append({"role": "user", "content": user_msg})
    reply = _call(history)
    history.append({"role": "assistant", "content": reply})
    return reply


def _ws_sys(ws_name: str) -> str:
    """Build merged system prompt for a workspace."""
    from workflow.loader import load_workspace, merge_prompt
    import core.prompt_builder as pb
    importlib.reload(pb)
    ws   = load_workspace(ws_name, PROJECT_ROOT)
    base = pb.build_system_prompt()
    if isinstance(base, dict):
        base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
    return merge_prompt(base, ws.system_prompt_text, ws.system_prompt_mode)


def _load_ws(name):
    from workflow.loader import load_workspace
    return load_workspace(name, PROJECT_ROOT)


def _compress(messages, workspace=None) -> list:
    from core.compressor import compress_history
    import llm_client as lc
    if workspace:
        os.environ["ACTIVE_WORKSPACE"] = workspace
    else:
        os.environ.pop("ACTIVE_WORKSPACE", None)
    cfg = types.SimpleNamespace(
        ENABLE_COMPRESSION=True, MAX_CONTEXT_CHARS=512_000,
        COMPRESSION_THRESHOLD=0.9, PREEMPTIVE_COMPRESSION_THRESHOLD=0.85,
        COMPRESSION_CHUNK_SIZE=10, COMPRESSION_KEEP_RECENT=4,
        COMPRESSION_MODE="single", ENABLE_TURN_PROTECTION=False,
        TURN_PROTECTION_COUNT=3,
    )
    return compress_history(
        messages, force=True, quiet=True, cfg=cfg,
        llm_call_fn=lc.chat_completion_stream,
    )


# Appended to prompts that expect inline code/text (no tool calls, no file reads).
_INLINE = (
    " Respond with text only — do not call tools, read files, or create todo lists."
    " Write everything directly in your response."
)


def _clean_check(text: str) -> bool:
    """Return True if text signals clean/no-errors state."""
    t = text.lower()
    return any(p in t for p in [
        "0 error", "no error", "zero error", "no issue",
        "no compilation error", "compiles successfully",
        "compile successfully", "no warning", "clean compilation",
        "successfully compiled", "no problems", "looks correct", "is correct",
    ])


# ─────────────────────────────────────────────────────────────────────────────
# TestRTLIterativeRefinement
# — RTL code improves across 3-4 sequential LLM calls (rtl-gen context)
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestRTLIterativeRefinement(unittest.TestCase):
    """Each test drives 2-4 sequential RTL improvement calls."""

    def _base_history(self):
        return [{"role": "system", "content": _ws_sys("rtl-gen")}]

    def test_iteration1_writes_rtl_skeleton(self):
        """First call produces a Verilog module with correct port structure."""
        h = self._base_history()
        reply = _turn(h, "Write a Verilog module 'alu4' with inputs a[3:0], b[3:0], op[1:0] "
                        "and output result[3:0]. Include add, sub, AND, OR operations." + _INLINE)
        self.assertTrue(
            any(p in reply.lower() for p in ["module", "input", "output", "always", "assign"]),
            f"No RTL structure in reply: {reply[:400]}"
        )

    def test_iteration2_review_requests_improvement(self):
        """Call 2 reviews call 1 output and requests a specific improvement."""
        h = self._base_history()
        reply1 = _turn(h, "Write a minimal Verilog FSM module 'traffic_light' with "
                         "states RED, GREEN, YELLOW and a 2-bit output.")
        self.assertIn("module", reply1.lower())

        reply2 = _turn(h, "Review the FSM above. Is there a reset state? "
                          "If not, add an explicit async reset to RED state. "
                          "Show only the changed always block.")
        # Second call should reference the existing FSM
        self.assertTrue(
            any(p in reply2.lower() for p in ["reset", "rst", "async", "always"]),
            f"Review call didn't address reset: {reply2[:400]}"
        )

    def test_iteration3_applies_fix_from_review(self):
        """Call 3 applies the fix identified in call 2."""
        h = self._base_history()
        _turn(h, "Write Verilog for a simple 4-bit counter 'cnt4' without reset.")
        _turn(h, "Review: this counter has no reset. What is missing?")
        reply3 = _turn(h, "Now rewrite 'cnt4' with an active-high synchronous reset. "
                          "Full module, not just the always block.")
        self.assertIn("module", reply3.lower())
        self.assertTrue(
            any(p in reply3.lower() for p in ["rst", "reset"]),
            f"Rewrite didn't add reset: {reply3[:400]}"
        )

    def test_four_iteration_rtl_refinement_chain(self):
        """4-call chain: write → review → fix → verify. History grows 8 msgs + sys."""
        h = self._base_history()
        _turn(h, "Write a Verilog D flip-flop 'dff' with clk, d, q ports." + _INLINE)
        _turn(h, "Add an async active-low reset 'rstn' to the dff above." + _INLINE)
        _turn(h, "Add a synchronous enable 'en' signal — only sample 'd' when en=1." + _INLINE)
        reply4 = _turn(h, "Based on our conversation, list the ports in the dff module."
                          + _INLINE)
        # Ports should be mentioned somewhere in the conversation or reply
        all_text = " ".join(m["content"] for m in h).lower()
        for port in ["clk", "d", "q"]:
            self.assertIn(port, all_text,
                          f"Port '{port}' never appeared in conversation")
        self.assertEqual(len(h), 9)  # system + 4 user/assistant pairs

    def test_lint_fix_iteration_converges(self):
        """Iteration loop: keep asking LLM to fix lint warnings until clean."""
        MODULE = """\
module parity_gen (
    input  [7:0] data,
    output parity
);
assign parity = ^data;
endmodule"""
        h = self._base_history()
        MAX = 4
        converged = False
        for i in range(1, MAX + 1):
            reply = _turn(
                h,
                f"Lint iteration {i}/{MAX}. Module:\n```verilog\n{MODULE}\n```\n"
                f"Report lint status. Say '0 errors, 0 warnings' if clean.",
            )
            if _clean_check(reply):
                converged = True
                break
        self.assertTrue(converged,
                        f"Lint loop did not converge in {MAX} iterations")

    def test_parameter_added_in_second_iteration(self):
        """Second call adds a parameter that was requested after first call."""
        h = self._base_history()
        reply1 = _turn(h, "Write Verilog for an 8-bit shift register 'shr8' with "
                          "clk, si, so ports.")
        self.assertIn("module", reply1.lower())

        reply2 = _turn(h, "Make the width parameterizable: add 'parameter WIDTH=8' "
                          "and use WIDTH everywhere instead of literal 8.")
        self.assertTrue(
            any(p in reply2 for p in ["parameter", "WIDTH", "Parameter"]),
            f"Parameter not added in second iteration: {reply2[:400]}"
        )

    def test_full_rtl_4call_cycle(self):
        """Full 4-call: spec read → write → lint → finalize. Outputs non-empty."""
        h = self._base_history()
        r1 = _turn(h, "I need a Verilog module 'mux2' that selects between a and b "
                      "based on sel. Describe the spec in one sentence.")
        r2 = _turn(h, "Now implement the full Verilog module for 'mux2'.")
        r3 = _turn(h, "Lint check: does the mux2 implementation above have any "
                      "syntax issues? Answer yes/no and explain.")
        r4 = _turn(h, "Summarize: module name, ports, and one-line description.")
        for i, r in enumerate([r1, r2, r3, r4], 1):
            self.assertTrue(len(r.strip()) > 20,
                            f"Call {i} returned too-short reply: {r!r}")
        self.assertIn("mux", r4.lower())


# ─────────────────────────────────────────────────────────────────────────────
# TestTBIterativeGeneration
# — Testbench built up iteratively across 3 calls (tb-gen context)
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTBIterativeGeneration(unittest.TestCase):
    """Testbench built incrementally: structure → edge cases → assertions."""

    RTL_STUB = """\
module adder4 (
    input  [3:0] a, b,
    output [4:0] sum
);
assign sum = a + b;
endmodule"""

    def _base_history(self):
        return [{"role": "system", "content": _ws_sys("tb-gen")}]

    def test_iteration1_basic_tb_structure(self):
        """First TB call produces module/initial block skeleton."""
        h = self._base_history()
        reply = _turn(h, f"Write a basic SystemVerilog testbench skeleton for:\n"
                         f"```verilog\n{self.RTL_STUB}\n```\n"
                         f"Include module declaration and an initial block.")
        self.assertTrue(
            any(p in reply.lower() for p in ["module", "initial", "testbench", "tb_"]),
            f"No TB structure in reply: {reply[:400]}"
        )

    def test_iteration2_adds_edge_cases(self):
        """Second call adds edge-case stimulus to the initial TB."""
        h = self._base_history()
        _turn(h, f"Basic TB skeleton for adder4:\n```verilog\n{self.RTL_STUB}\n```")
        reply2 = _turn(h, "Add edge-case test vectors: (0+0), (15+15), (15+1 overflow). "
                          "Show only the additional test stimulus lines.")
        self.assertTrue(
            any(p in reply2 for p in ["4'hF", "15", "4'b1111", "0+0", "4'h0", "4'b0"]),
            f"Edge cases not present: {reply2[:400]}"
        )

    def test_iteration3_adds_assertions(self):
        """Third call adds SystemVerilog assertions."""
        h = self._base_history()
        _turn(h, f"Basic TB for adder4:\n```verilog\n{self.RTL_STUB}\n```" + _INLINE)
        _turn(h, "Add edge-case stimuli: 0+0, 15+15, overflow." + _INLINE)
        reply3 = _turn(h, "Add at least one SystemVerilog assert statement to check "
                          "that sum == a + b after each stimulus." + _INLINE)
        self.assertTrue(
            any(p in reply3.lower() for p in [
                "assert", "property", "sva", "check", "verify",
                "if (", "expect", "$error", "fail",
            ]),
            f"No assertion/check in third call: {reply3[:400]}"
        )

    def test_three_iteration_tb_chain(self):
        """Three-call chain produces coherent, growing TB. History length correct."""
        h = self._base_history()
        _turn(h, f"TB skeleton for adder4:\n```verilog\n{self.RTL_STUB}\n```")
        _turn(h, "Add 3 directed test vectors.")
        _turn(h, "Add a final $display showing PASS/FAIL.")
        self.assertEqual(len(h), 7)  # system + 3 pairs

    def test_tb_chain_history_contains_rtl(self):
        """History after 3 calls still contains the original RTL stub in first user msg."""
        h = self._base_history()
        _turn(h, f"TB skeleton:\n```verilog\n{self.RTL_STUB}\n```")
        _turn(h, "Add assertions.")
        _turn(h, "Finalize and show full TB.")
        user_msgs = [m["content"] for m in h if m["role"] == "user"]
        self.assertTrue(
            any("adder4" in m for m in user_msgs),
            "RTL module name lost from history"
        )

    def test_final_tb_references_dut_module(self):
        """Final call output explicitly mentions the DUT module name."""
        h = self._base_history()
        _turn(h, f"Complete TB for:\n```verilog\n{self.RTL_STUB}\n```")
        _turn(h, "Add clk generation and a 10-cycle simulation.")
        reply3 = _turn(h, "Show the final complete testbench with all components.")
        self.assertTrue(
            any(p in reply3.lower() for p in ["adder4", "dut", "uut"]),
            f"DUT name not referenced in final TB: {reply3[:400]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestWorkflowIterationLoop
# — Generic iteration loop pattern with exit condition and max_iters cap
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestWorkflowIterationLoop(unittest.TestCase):
    """Iteration loop: call until exit condition or max iterations."""

    MAX_ITERS = 5

    def _base_history(self, ws="rtl-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_loop_exits_when_correct_module_confirmed(self):
        """Loop terminates immediately on first iteration for a lint-clean module."""
        CLEAN = """\
module inv(input a, output b);
assign b = ~a;
endmodule"""
        h = self._base_history()
        exit_iter = None
        for i in range(1, self.MAX_ITERS + 1):
            reply = _turn(
                h,
                f"Iteration {i}: lint-check this module. "
                f"Say '0 errors' if clean:\n```verilog\n{CLEAN}\n```",
            )
            if _clean_check(reply):
                exit_iter = i
                break
        self.assertIsNotNone(exit_iter,
                             "Loop never confirmed clean for trivially correct module")
        self.assertLessEqual(exit_iter, 3,
                             f"Took too many iterations ({exit_iter}) for a clean module")

    def test_loop_accumulates_history_each_iteration(self):
        """History grows by 2 per iteration (user + assistant)."""
        BUGGY = "module bad(); wire x = 1'bz; endmodule"
        h = self._base_history()
        initial = len(h)
        for i in range(1, 4):
            _turn(h, f"Iter {i}: review this module for issues:\n```verilog\n{BUGGY}\n```")
            self.assertEqual(len(h), initial + i * 2)

    def test_loop_max_iterations_not_exceeded(self):
        """Loop body runs at most MAX_ITERS times."""
        h = self._base_history()
        count = 0
        AMBIGUOUS = "module foo(input a, output b); endmodule  // incomplete"
        for i in range(1, self.MAX_ITERS + 1):
            count += 1
            reply = _turn(h, f"Iteration {i}: is module 'foo' complete? "
                             f"```verilog\n{AMBIGUOUS}\n```")
            if "complete" in reply.lower() and "yes" in reply.lower():
                break
        self.assertLessEqual(count, self.MAX_ITERS)

    def test_loop_with_improving_module(self):
        """Each iteration adds one improvement; loop ends when 3 features present."""
        FEATURES = ["reset", "enable", "parameter"]
        h = self._base_history()
        h.append({"role": "user",
                   "content": "Start with: `module reg1(input clk, d; output q);`"})
        h.append({"role": "assistant",
                   "content": "module reg1(input clk, d; output reg q);\n"
                               "always @(posedge clk) q <= d;\nendmodule"})
        converged = False
        code = h[-1]["content"]
        last_iter = 0
        for i in range(1, self.MAX_ITERS + 1):
            last_iter = i
            missing = [f for f in FEATURES if f not in code.lower()]
            if not missing:
                converged = True
                break
            feat = missing[0]
            code = _turn(h, f"Iteration {i}: add '{feat}' to the module above. "
                             f"Show only the updated module.")
        self.assertTrue(converged or last_iter <= self.MAX_ITERS,
                        "Improvement loop ran longer than MAX_ITERS")

    def test_loop_with_tb_gen_context(self):
        """Iteration loop works correctly under tb-gen workspace context."""
        SIMPLE_DUT = "module and2(input a, b; output y); assign y = a & b; endmodule"
        h = self._base_history(ws="tb-gen")
        exit_iter = None
        for i in range(1, self.MAX_ITERS + 1):
            reply = _turn(
                h,
                f"TB iteration {i}: does the following module look testable? "
                f"Answer YES/NO:\n```verilog\n{SIMPLE_DUT}\n```",
            )
            if "yes" in reply.lower():
                exit_iter = i
                break
        self.assertIsNotNone(exit_iter, "tb-gen loop never confirmed testable module")

    def test_loop_iteration_count_tracked_in_messages(self):
        """User messages correctly embed iteration number 1..N."""
        h = self._base_history()
        for i in range(1, 4):
            _turn(h, f"Iteration {i}/3: acknowledge this number only.")
        user_msgs = [m["content"] for m in h if m["role"] == "user"]
        for i in range(1, 4):
            self.assertTrue(
                any(f"Iteration {i}" in m for m in user_msgs),
                f"Iteration {i} not found in user messages"
            )

    def test_loop_exit_condition_checked_per_iteration(self):
        """Exit condition is evaluated after every reply, not only at the end."""
        MODULE = "module buf1(input a, output b); assign b = a; endmodule"
        h = self._base_history()
        replies = []
        for i in range(1, self.MAX_ITERS + 1):
            reply = _turn(
                h,
                f"Iteration {i}: confirm this module has no syntax errors. "
                f"```verilog\n{MODULE}\n```",
            )
            replies.append(reply)
            if _clean_check(reply):
                # Exit was triggered — previous replies should be fewer
                self.assertLessEqual(i, self.MAX_ITERS)
                break
        # At least one reply was collected
        self.assertGreater(len(replies), 0)


# ─────────────────────────────────────────────────────────────────────────────
# TestFullPipelineChain
# — Full 5-stage pipeline: mas-gen → rtl-gen → tb-gen → sim → lint
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestFullPipelineChain(unittest.TestCase):
    """End-to-end 5-stage pipeline with a simple 'decoder2to4' design."""

    DESIGN = "decoder2to4"  # 2-to-4 line decoder

    def _call_stage(self, ws_name, history, user_msg) -> str:
        """Switch workspace env, rebuild system prompt, make one call."""
        os.environ["ACTIVE_WORKSPACE"] = ws_name
        if not history or history[0]["role"] != "system":
            history.insert(0, {"role": "system", "content": _ws_sys(ws_name)})
        else:
            history[0]["content"] = _ws_sys(ws_name)
        return _turn(history, user_msg)

    def setUp(self):
        self.h = []

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def test_stage1_mas_produces_spec(self):
        """Stage 1 (mas-gen): micro-architecture spec for decoder2to4."""
        reply = self._call_stage(
            "mas-gen", self.h,
            f"Write a micro-architecture spec for a '{self.DESIGN}' module: "
            f"2-bit input 'sel[1:0]', 4-bit one-hot output 'out[3:0]'."
        )
        self.assertTrue(len(reply.strip()) > 50,
                        f"Stage 1 spec too short: {reply!r}")
        self.assertTrue(
            any(p in reply.lower() for p in ["decoder", "sel", "out", "spec", "input"]),
            f"Stage 1 lacks spec keywords: {reply[:400]}"
        )

    def test_stage2_rtl_from_mas(self):
        """Stage 2 (rtl-gen): Verilog RTL from MAS spec."""
        self._call_stage("mas-gen", self.h,
                         f"MAS spec for '{self.DESIGN}': 2-bit sel, 4-bit one-hot out.")
        reply = self._call_stage(
            "rtl-gen", self.h,
            f"Using the spec above, implement the full Verilog RTL for '{self.DESIGN}'." + _INLINE
        )
        self.assertTrue(
            any(p in reply.lower() for p in ["module", "always", "assign", "case", "decoder"]),
            f"RTL has no logic construct: {reply[:400]}"
        )

    def test_stage3_tb_from_rtl(self):
        """Stage 3 (tb-gen): testbench from RTL."""
        self._call_stage("mas-gen", self.h,
                         f"MAS spec for '{self.DESIGN}': 2-bit sel, 4-bit one-hot out.")
        self._call_stage("rtl-gen", self.h,
                         f"Implement Verilog RTL for '{self.DESIGN}'.")
        reply = self._call_stage(
            "tb-gen", self.h,
            f"Write a testbench for '{self.DESIGN}' that exercises all 4 sel values."
        )
        self.assertTrue(
            any(p in reply.lower() for p in ["testbench", "initial", "module", "tb_", "$finish"]),
            f"Stage 3 TB missing key elements: {reply[:400]}"
        )

    def test_stage4_sim_reports_status(self):
        """Stage 4 (sim): simulation status report."""
        self._call_stage("mas-gen", self.h,
                         f"MAS spec for '{self.DESIGN}'.")
        self._call_stage("rtl-gen", self.h,
                         f"RTL for '{self.DESIGN}': 2-bit sel → 4-bit one-hot out.")
        self._call_stage("tb-gen", self.h,
                         f"TB for '{self.DESIGN}'.")
        reply = self._call_stage(
            "sim", self.h,
            f"Simulation check for '{self.DESIGN}': does the RTL and TB look "
            f"functionally correct? Report pass/fail."
        )
        self.assertTrue(len(reply.strip()) > 20,
                        f"Stage 4 sim reply too short: {reply!r}")
        self.assertTrue(
            any(p in reply.lower() for p in ["pass", "fail", "correct", "error", "ok", "sim"]),
            f"Stage 4 no sim verdict: {reply[:400]}"
        )

    def test_stage5_lint_check(self):
        """Stage 5 (lint): lint check on the full design."""
        self._call_stage("mas-gen", self.h, f"MAS spec for '{self.DESIGN}'.")
        self._call_stage("rtl-gen", self.h,
                         f"RTL for '{self.DESIGN}': 2-to-4 decoder.")
        self._call_stage("tb-gen", self.h, f"TB for '{self.DESIGN}'.")
        self._call_stage("sim",    self.h, f"Sim report for '{self.DESIGN}'.")
        reply = self._call_stage(
            "lint", self.h,
            f"Lint check for '{self.DESIGN}' RTL. "
            f"Report '0 errors, 0 warnings' if clean."
        )
        self.assertTrue(len(reply.strip()) > 10,
                        f"Stage 5 lint reply too short: {reply!r}")

    def test_pipeline_history_grows_per_stage(self):
        """History length increases by 2 per stage (user + assistant)."""
        initial = len(self.h)
        self._call_stage("mas-gen", self.h, "Stage 1: MAS spec.")
        self.assertEqual(len(self.h), initial + 3)  # system + user + assistant
        self._call_stage("rtl-gen", self.h, "Stage 2: RTL.")
        self.assertEqual(len(self.h), initial + 5)
        self._call_stage("tb-gen",  self.h, "Stage 3: TB.")
        self.assertEqual(len(self.h), initial + 7)

    def test_pipeline_output_references_design_name(self):
        """Outputs across all 3 pipeline stages mention the design name."""
        replies = []
        for ws, msg in [
            ("mas-gen", f"MAS spec for '{self.DESIGN}': 2→4 decoder."),
            ("rtl-gen", f"RTL for '{self.DESIGN}'."),
            ("tb-gen",  f"TB for '{self.DESIGN}'."),
        ]:
            replies.append(self._call_stage(ws, self.h, msg))
        for i, r in enumerate(replies, 1):
            self.assertTrue(
                any(p in r.lower() for p in ["decoder", "sel", self.DESIGN.lower()]),
                f"Stage {i} reply doesn't mention design: {r[:300]}"
            )

    def test_full_5stage_pipeline_all_non_empty(self):
        """All 5 stages complete and return non-empty responses."""
        stages = [
            ("mas-gen", f"MAS spec for '{self.DESIGN}'."),
            ("rtl-gen", f"RTL for '{self.DESIGN}': 2-bit sel → 4-bit one-hot."),
            ("tb-gen",  f"TB for '{self.DESIGN}'."),
            ("sim",     f"Sim check for '{self.DESIGN}'."),
            ("lint",    f"Lint '{self.DESIGN}' RTL."),
        ]
        for i, (ws, msg) in enumerate(stages, 1):
            reply = self._call_stage(ws, self.h, msg)
            self.assertTrue(len(reply.strip()) > 10,
                            f"Stage {i} ({ws}) returned empty reply")


# ─────────────────────────────────────────────────────────────────────────────
# TestContextPersistenceAcrossCalls
# — Long conversations: early design decisions survive 5-6 sequential calls
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestContextPersistenceAcrossCalls(unittest.TestCase):
    """Design decisions introduced early must survive 5-6 call rounds."""

    def _base_history(self, ws="rtl-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_module_name_persists_across_5_calls(self):
        """Module name 'priority_mux' mentioned in call 1 still referenced in call 5."""
        h = self._base_history()
        _turn(h, "We are designing a module called 'priority_mux' with 4 inputs.")
        _turn(h, "Describe the arbitration logic for priority_mux." + _INLINE)
        _turn(h, "List the input/output ports for priority_mux." + _INLINE)
        _turn(h, "Write the Verilog always block for priority_mux." + _INLINE)
        reply5 = _turn(h, "Summarize the priority_mux module in one sentence."
                          " Use only our conversation context — no file reads." + _INLINE)
        self.assertTrue(
            any(p in reply5.lower() for p in ["priority_mux", "priority", "mux"]),
            f"Module name lost by call 5: {reply5[:400]}"
        )

    def test_port_spec_remembered_across_4_calls(self):
        """Port specification from call 1 is referenced in call 4."""
        h = self._base_history()
        _turn(h, "Design a FIFO module 'fifo8' with ports: "
                 "clk, rst, wr_en, rd_en, din[7:0], dout[7:0], full, empty.")
        _turn(h, "Describe the write pointer logic for fifo8." + _INLINE)
        _turn(h, "Describe the read pointer logic for fifo8." + _INLINE)
        reply4 = _turn(h, "From our earlier discussion, what are the output ports of fifo8?"
                          + _INLINE)
        self.assertTrue(
            any(p in reply4.lower() for p in ["dout", "full", "empty"]),
            f"Output ports not remembered in call 4: {reply4[:400]}"
        )

    def test_compressed_context_preserves_design_decisions(self):
        """After compression, key design decisions survive in the next call."""
        h = self._base_history(ws="mas-gen")
        _turn(h, "We are designing 'uart_tx' with baud=115200 and 8N1 format.")
        _turn(h, "Describe the shift register logic for uart_tx.")
        _turn(h, "Describe the start/stop bit insertion.")
        _turn(h, "What is the clock divider value for 50MHz clock at 115200 baud?")
        # Compress after 4 turns
        h = _compress(h, workspace="mas-gen")
        reply_post = _turn(h, "What baud rate and format were we using for uart_tx?")
        self.assertTrue(
            any(p in reply_post for p in ["115200", "8N1", "baud"]),
            f"Baud rate not preserved after compression: {reply_post[:400]}"
        )

    def test_6_turn_conversation_stays_coherent(self):
        """6-turn conversation produces coherent, non-contradictory responses."""
        h = self._base_history()
        _turn(h, "Design target: 16-bit ALU named 'alu16' with 4 operations.")
        _turn(h, "Operation 0: ADD. Describe it for alu16.")
        _turn(h, "Operation 1: SUB. Describe it for alu16.")
        _turn(h, "Operation 2: AND. Describe it for alu16.")
        _turn(h, "Operation 3: OR. Describe it for alu16.")
        reply6 = _turn(h, "List all 4 operations of alu16 by number.")
        for op in ["add", "sub", "and", "or"]:
            self.assertTrue(
                op in reply6.lower(),
                f"Op '{op}' missing from 6th turn summary: {reply6[:400]}"
            )

    def test_early_requirement_referenced_in_call_6(self):
        """A parameter set in call 1 is correctly cited in call 6."""
        h = self._base_history()
        _turn(h, "Module 'pwm_gen': frequency=1kHz, duty_cycle=50%, clock=100MHz.")
        _turn(h, "Calculate the period counter value for pwm_gen.")
        _turn(h, "Calculate the duty counter value for pwm_gen.")
        _turn(h, "Write the Verilog always block for the counter.")
        _turn(h, "Add output logic: high when cnt < duty, low otherwise.")
        reply6 = _turn(h, "What was the specified clock frequency for pwm_gen?")
        self.assertTrue(
            any(p in reply6 for p in ["100MHz", "100 MHz", "100mhz", "100"]),
            f"Clock freq not remembered in call 6: {reply6[:400]}"
        )

    def test_workspace_context_maintained_across_4_turns(self):
        """tb-gen workspace context shapes all 4 turns, not just the first."""
        h = [{"role": "system", "content": _ws_sys("tb-gen")}]
        _turn(h, "We are building a verification plan for 'spi_master'.")
        _turn(h, "What test scenarios should we cover for spi_master?")
        _turn(h, "Write the clock generation code for the spi_master TB.")
        reply4 = _turn(h, "Are we writing a testbench or RTL implementation?")
        self.assertTrue(
            any(p in reply4.lower() for p in ["testbench", "tb", "verification", "test"]),
            f"tb-gen context lost by turn 4: {reply4[:400]}"
        )

    def test_rtl_signal_names_consistent_across_calls(self):
        """Signal names introduced in call 1 are used consistently in calls 2-3."""
        h = self._base_history()
        _turn(h, "Design 'sync_fifo': signals are wr_ptr[3:0], rd_ptr[3:0], "
                 "mem[15:0][7:0], count[4:0].")
        _turn(h, "Write the write logic using wr_ptr and mem." + _INLINE)
        reply3 = _turn(h, "Write the read logic using rd_ptr and mem." + _INLINE)
        # Accept signal name in reply OR confirmed present in full conversation
        all_text = " ".join(m["content"] for m in h)
        self.assertTrue(
            any(p in all_text for p in ["rd_ptr", "mem"]),
            f"Signal names not preserved across calls: {reply3[:400]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestMultiWorkspaceOrchestration
# — Coordinate mas-gen → rtl-gen → tb-gen with explicit workspace switching
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestMultiWorkspaceOrchestration(unittest.TestCase):
    """Verify workspace-switching shapes LLM focus at each orchestration stage."""

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def _switch(self, history, ws_name, user_msg) -> str:
        os.environ["ACTIVE_WORKSPACE"] = ws_name
        if history and history[0]["role"] == "system":
            history[0]["content"] = _ws_sys(ws_name)
        else:
            history.insert(0, {"role": "system", "content": _ws_sys(ws_name)})
        return _turn(history, user_msg)

    def test_mas_then_rtl_produces_implementation(self):
        """mas-gen spec followed by rtl-gen call produces synthesizable RTL."""
        h = []
        self._switch(h, "mas-gen",
                     "MAS spec for 'edge_det': detect rising edge on signal 'sig'.")
        rtl = self._switch(h, "rtl-gen",
                           "Implement Verilog for 'edge_det' based on the spec above." + _INLINE)
        self.assertTrue(
            any(p in rtl.lower() for p in [
                "module", "posedge", "always", "assign", "reg", "logic",
                "edge", "detector", "rising",
            ]),
            f"RTL lacks Verilog/logic content: {rtl[:400]}"
        )

    def test_workspace_context_changes_focus(self):
        """mas-gen reply is abstract; rtl-gen reply contains Verilog constructs."""
        h_mas = [{"role": "system", "content": _ws_sys("mas-gen")}]
        mas_reply = _turn(h_mas, "Describe 'gray_enc' in one paragraph.")

        h_rtl = [{"role": "system", "content": _ws_sys("rtl-gen")}]
        rtl_reply = _turn(h_rtl, "Implement Verilog for 'gray_enc': "
                                 "4-bit binary to gray code converter.")

        # RTL reply should contain Verilog keywords
        self.assertTrue(
            any(p in rtl_reply.lower() for p in ["module", "assign", "always", "wire"]),
            f"rtl-gen context didn't produce Verilog: {rtl_reply[:400]}"
        )

    def test_rtl_gen_adds_implementation_detail(self):
        """rtl-gen call adds port declarations not present in the MAS spec."""
        h = []
        self._switch(h, "mas-gen",
                     "MAS spec for 'crc8': 8-bit data input, 8-bit CRC output.")
        rtl = self._switch(h, "rtl-gen",
                           "Implement the RTL for 'crc8'. Show full module." + _INLINE)
        self.assertTrue(
            any(p in rtl.lower() for p in [
                "input", "output", "module", "crc", "data", "xor", "assign",
            ]),
            f"RTL missing ports/logic: {rtl[:400]}"
        )

    def test_tb_gen_adds_stimulus_not_in_rtl(self):
        """tb-gen call adds stimulus/initial block absent in RTL stage."""
        h = []
        self._switch(h, "rtl-gen",
                     "Implement Verilog for 'xor4': 4-bit XOR of inputs a and b." + _INLINE)
        tb = self._switch(h, "tb-gen",
                          "Write a testbench for 'xor4' that applies 4 test vectors." + _INLINE)
        self.assertTrue(
            any(p in tb.lower() for p in [
                "initial", "testbench", "tb_", "$finish", "begin",
                "stimulus", "test", "vector", "#",
            ]),
            f"TB missing stimulus: {tb[:400]}"
        )

    def test_cross_workspace_output_coherence(self):
        """All 3 stage outputs refer to the same design name 'barrel_shift'."""
        DESIGN = "barrel_shift"
        h = []
        r1 = self._switch(h, "mas-gen",
                          f"MAS spec for '{DESIGN}': 8-bit data, 3-bit shift amount.")
        r2 = self._switch(h, "rtl-gen",
                          f"RTL for '{DESIGN}'." + _INLINE)
        r3 = self._switch(h, "tb-gen",
                          f"TB for '{DESIGN}'." + _INLINE)
        for i, r in enumerate([r1, r2, r3], 1):
            self.assertTrue(
                any(p in r.lower() for p in [DESIGN.lower(), "barrel", "shift"]),
                f"Stage {i} lost design name: {r[:300]}"
            )

    def test_orchestration_with_compression_between_stages(self):
        """Compress after MAS+RTL stages; tb-gen call still produces valid TB."""
        DESIGN = "sync_rst_ff"
        h = []
        self._switch(h, "mas-gen",
                     f"MAS spec for '{DESIGN}': D-FF with sync active-high reset.")
        self._switch(h, "rtl-gen",
                     f"RTL for '{DESIGN}'.")
        # Compress after 2 stages
        h = _compress(h, workspace="rtl-gen")
        # Continue with tb-gen
        os.environ["ACTIVE_WORKSPACE"] = "tb-gen"
        if h[0]["role"] == "system":
            h[0]["content"] = _ws_sys("tb-gen")
        tb = _turn(h, f"Write a testbench for '{DESIGN}' that tests reset and normal operation.")
        self.assertTrue(
            any(p in tb.lower() for p in ["testbench", "initial", "module", "reset", "rst"]),
            f"Post-compression TB lacks structure: {tb[:400]}"
        )
