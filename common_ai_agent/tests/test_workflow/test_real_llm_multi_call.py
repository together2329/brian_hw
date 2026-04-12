"""
Real LLM multi-call integration tests — GLM-5.1 on Z.AI.

Each test makes MULTIPLE sequential API calls, simulating real agent workflows:

  - MAS → RTL → TB pipeline: three workspace-aware LLM calls passing output
    from one stage as input to the next.
  - Simulation loop: repeated LLM calls until "0 errors" exit condition met.
  - Todo task chain: execute full-project tasks sequentially, each call
    building on previous output.
  - Plan → implement → review: three-call planning-and-execution cycle.
  - Workspace switch: mid-session context switch between workspaces, verifying
    the new workspace prompt shapes subsequent responses.
  - Compression midway: compress accumulated history, then continue with more
    LLM calls and verify coherent output across the full sequence.

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


# ── shared helpers ────────────────────────────────────────────────────────────

def _call(messages) -> str:
    """Single LLM call → full response string."""
    import llm_client as lc
    chunks = list(lc.chat_completion_stream(
        messages, skip_rate_limit=True, suppress_spinner=True
    ))
    return "".join(c for c in chunks if isinstance(c, str))


def _turn(history: list, user_msg: str) -> str:
    """Append user message, call LLM, append assistant reply, return reply."""
    history.append({"role": "user",      "content": user_msg})
    reply = _call(history)
    history.append({"role": "assistant", "content": reply})
    return reply


def _ws_sys(ws_name: str) -> str:
    """Build the merged system prompt for a workspace."""
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


# ─────────────────────────────────────────────────────────────
# TestMASRTLTBPipeline
# — Three sequential workspace calls: mas-gen → rtl-gen → tb-gen
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestMASRTLTBPipeline(unittest.TestCase):
    """
    Simulate the full MAS → RTL → TB agent hand-off.

    Call 1 (mas-gen): produce a compact MAS spec for a D flip-flop.
    Call 2 (rtl-gen): given the MAS text, implement the RTL module.
    Call 3 (tb-gen):  given the RTL code, generate a testbench.
    """

    MODULE = "dff"

    def setUp(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    # ── helpers ──────────────────────────────────────────────

    def _mas_call(self):
        """Call 1: ask mas-gen to write a compact MAS for dff."""
        os.environ["ACTIVE_WORKSPACE"] = "mas-gen"
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        return _turn(
            history,
            f"Write a compact Micro Architecture Spec (MAS) for a D flip-flop "
            f"module named '{self.MODULE}' with: clk, rst, d inputs; q output. "
            f"Include: interface, functional description, and one DV test scenario. "
            f"Keep it under 200 words.",
        ), history

    def _rtl_call(self, mas_text):
        """Call 2: ask rtl-gen to implement RTL based on the MAS text."""
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        history = [
            {"role": "system", "content": _ws_sys("rtl-gen")},
            {"role": "user",   "content": f"Here is the MAS document:\n\n{mas_text}"},
            {"role": "assistant", "content": "Understood. I will implement the RTL module."},
        ]
        return _turn(
            history,
            f"Implement the Verilog module for '{self.MODULE}' exactly as specified.",
        ), history

    def _tb_call(self, rtl_code):
        """Call 3: ask tb-gen to write a testbench for the RTL module."""
        os.environ["ACTIVE_WORKSPACE"] = "tb-gen"
        history = [
            {"role": "system", "content": _ws_sys("tb-gen")},
            {"role": "user",   "content": f"Here is the RTL implementation:\n\n{rtl_code}"},
            {"role": "assistant", "content": "Understood. I will write a testbench."},
        ]
        return _turn(
            history,
            f"Write a SystemVerilog testbench for '{self.MODULE}' with at least "
            f"one test scenario: apply d=1, check q after clock edge.",
        ), history

    # ── tests ────────────────────────────────────────────────

    def test_call1_mas-gen_produces_spec(self):
        """mas-gen call returns a spec mentioning the module and interface."""
        mas_text, _ = self._mas_call()
        lowered = mas_text.lower()
        self.assertTrue(
            any(w in lowered for w in ["dff", "d flip", "flip-flop", "clk", "port", "interface"]),
            f"MAS call didn't produce a spec: {mas_text[:400]}",
        )

    def test_call2_rtl-gen_produces_verilog(self):
        """rtl-gen call (given MAS) returns Verilog module code."""
        mas_text, _ = self._mas_call()
        rtl_code, _ = self._rtl_call(mas_text)
        lowered = rtl_code.lower()
        self.assertTrue(
            "module" in lowered or "endmodule" in lowered or "always" in lowered,
            f"RTL call didn't produce Verilog: {rtl_code[:400]}",
        )

    def test_call3_tb-gen_produces_testbench(self):
        """tb-gen call (given RTL) returns a testbench."""
        mas_text, _ = self._mas_call()
        rtl_code, _ = self._rtl_call(mas_text)
        tb_code,  _ = self._tb_call(rtl_code)
        lowered = tb_code.lower()
        self.assertTrue(
            any(w in lowered for w in ["testbench", "tb_", "module tb", "initial", "clock", "stimulus"]),
            f"TB call didn't produce a testbench: {tb_code[:400]}",
        )

    def test_rtl_references_mas_module_name(self):
        """RTL output must reference the module name 'dff'."""
        mas_text, _ = self._mas_call()
        rtl_code, _ = self._rtl_call(mas_text)
        self.assertIn(
            self.MODULE, rtl_code.lower(),
            f"RTL didn't reference module name '{self.MODULE}': {rtl_code[:400]}",
        )

    def test_tb_references_rtl_module(self):
        """Testbench must instantiate or reference the DUT module."""
        mas_text, _ = self._mas_call()
        rtl_code, _ = self._rtl_call(mas_text)
        tb_code,  _ = self._tb_call(rtl_code)
        self.assertTrue(
            self.MODULE in tb_code.lower() or "dut" in tb_code.lower(),
            f"Testbench doesn't reference DUT '{self.MODULE}': {tb_code[:400]}",
        )

    def test_three_stage_output_is_coherent_chain(self):
        """The three outputs form a coherent design chain: spec → RTL → TB."""
        mas_text, _ = self._mas_call()
        rtl_code, _ = self._rtl_call(mas_text)
        tb_code,  _ = self._tb_call(rtl_code)

        # All three stages should have non-trivial content
        for label, text in [("MAS", mas_text), ("RTL", rtl_code), ("TB", tb_code)]:
            with self.subTest(stage=label):
                self.assertGreater(len(text.strip()), 30,
                                   f"{label} stage produced trivially short output")


# ─────────────────────────────────────────────────────────────
# TestSimulationDebugLoop
# — Multiple LLM calls simulating the SIM loop task
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestSimulationDebugLoop(unittest.TestCase):
    """
    Simulate the [SIM] loop task:
    - First call: present a buggy module + sim error
    - Subsequent calls: fix the bug, re-check
    - Exit when LLM says "0 errors" or max_iterations reached
    """

    MAX_ITERS = 5

    def _make_buggy_module(self):
        return """\
module counter_bug (
    input clk, rst,
    output reg [3:0] q
);
// BUG: missing posedge — will not synthesize
always @(clk) begin
    if (rst) q <= 4'b0;
    else     q <= q + 1;
end
endmodule"""

    def _make_sim_history(self):
        sys_text = _ws_sys("sim")
        return [{"role": "system", "content": sys_text}]

    def test_sim_call1_identifies_bug(self):
        """First sim call with a buggy module: LLM identifies the issue."""
        history = self._make_sim_history()
        error_msg = (
            "Simulation error: 'always @(clk)' is missing 'posedge'. "
            "The counter does not increment correctly on clock edge."
        )
        reply = _turn(
            history,
            f"Here is the module and the simulation error:\n\n"
            f"```verilog\n{self._make_buggy_module()}\n```\n\n"
            f"Error: {error_msg}\n\n"
            f"Identify the bug and provide the fixed module.",
        )
        lowered = reply.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "posedge", "edge", "clock", "fix", "always", "bug",
            ]),
            f"sim call didn't identify the bug: {reply[:400]}",
        )

    def test_sim_call2_provides_fixed_verilog(self):
        """Second call: LLM provides a Verilog fix with posedge."""
        history = self._make_sim_history()
        reply1 = _turn(
            history,
            f"Fix this buggy Verilog module (missing posedge on clock):\n\n"
            f"```verilog\n{self._make_buggy_module()}\n```",
        )
        self.assertIn("posedge", reply1.lower(),
                      f"Fix call didn't mention posedge: {reply1[:400]}")

    def test_sim_loop_exit_on_no_errors(self):
        """
        Simulate loop: keep calling until LLM reports 0 errors or max_iters.
        Uses a correct module — LLM should confirm 0 errors quickly.
        """
        CORRECT_MODULE = """\
module counter (
    input  clk, rst,
    output reg [3:0] q
);
always @(posedge clk) begin
    if (rst) q <= 4'b0;
    else     q <= q + 1;
end
endmodule"""

        history = self._make_sim_history()
        exit_reached = False

        for iteration in range(1, self.MAX_ITERS + 1):
            reply = _turn(
                history,
                f"Simulation attempt {iteration}/{self.MAX_ITERS}. "
                f"The current module is:\n```verilog\n{CORRECT_MODULE}\n```\n"
                f"Compile and run. Report: '0 errors, 0 warnings' if clean, "
                f"or list errors if not.",
            )
            _clean = reply.lower()
            _clean_patterns = [
                "0 error", "no error", "zero error",
                "no issue", "no compilation error",
                "compiles successfully", "compile successfully",
                "no warning", "clean compilation", "successfully compiled",
                "no problems", "looks correct", "is correct",
            ]
            if any(pat in _clean for pat in _clean_patterns):
                exit_reached = True
                break

        self.assertTrue(
            exit_reached,
            f"Sim loop never exited with clean signal after {self.MAX_ITERS} iterations",
        )

    def test_sim_loop_accumulates_fix_history(self):
        """
        Two-iteration fix loop: call 1 identifies bug, call 2 confirms fix.
        The history grows correctly across both calls.
        """
        history = self._make_sim_history()
        initial_len = len(history)

        # Iteration 1: present buggy module
        _turn(history, f"Simulate this module and report errors:\n```verilog\n{self._make_buggy_module()}\n```")
        self.assertEqual(len(history), initial_len + 2)  # user + assistant

        # Iteration 2: ask for fix
        _turn(history, "Apply the fix and re-run. Confirm the result.")
        self.assertEqual(len(history), initial_len + 4)  # two more turns

    def test_sim_max_loop_iterations_config(self):
        """sim-debug template specifies max_loop_iterations = 20."""
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = _load_ws("sim")
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        tasks = reg.get_tasks("sim-debug")
        loop_task = next(t for t in tasks if t.get("loop"))
        self.assertEqual(loop_task["max_loop_iterations"], 20)


# ─────────────────────────────────────────────────────────────
# TestTodoTaskChain
# — Execute full-project todo tasks sequentially across multiple LLM calls
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestTodoTaskChain(unittest.TestCase):
    """
    Load full-project template, execute tasks 1–4 as separate LLM calls.
    Each call's output is passed to the next as context.
    """

    MODULE = "gray_counter"

    def _tasks(self):
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = _load_ws("mas-gen")
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        return reg.get_tasks("full-project")

    def test_task0_mas_produces_spec_document(self):
        """Task 0 ([MAS]): produce a MAS document for gray_counter."""
        tasks   = self._tasks()
        task    = tasks[0]
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        reply   = _turn(
            history,
            f"Execute this task for module '{self.MODULE}':\n{task['content']}\n\n"
            f"Detail: {task.get('detail','')}\n\n"
            f"Keep the MAS under 250 words.",
        )
        lowered = reply.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "gray", "counter", "interface", "clock", "output",
                "spec", "architecture", "overview", "port",
            ]),
            f"MAS task didn't produce a spec: {reply[:400]}",
        )

    def test_task1_rtl_uses_mas_from_task0(self):
        """Task 1 ([RTL]): implement RTL using MAS from task 0."""
        tasks   = self._tasks()
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]

        # Task 0: generate MAS
        mas_reply = _turn(
            history,
            f"Execute task for '{self.MODULE}': {tasks[0]['content']}\n"
            f"Keep under 150 words.",
        )

        # Task 1: generate RTL using the MAS
        rtl_reply = _turn(
            history,
            f"Now execute: {tasks[1]['content']}\n"
            f"Use the MAS you just wrote. Implement the Verilog module.",
        )
        lowered = rtl_reply.lower()
        self.assertTrue(
            "module" in lowered or "always" in lowered or "endmodule" in lowered,
            f"RTL task didn't produce Verilog: {rtl_reply[:400]}",
        )

    def test_tasks_0_to_2_sequential_calls(self):
        """Execute tasks 0, 1, 2 sequentially — each builds on previous."""
        tasks   = self._tasks()
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        outputs = []

        prompts = [
            f"Task 1: {tasks[0]['content']} for module '{self.MODULE}'. Keep under 100 words.",
            f"Task 2: {tasks[1]['content']} for '{self.MODULE}'. Write the Verilog module.",
            f"Task 3: {tasks[2]['content']} — review the above RTL for lint issues.",
        ]
        for prompt in prompts:
            reply = _turn(history, prompt)
            outputs.append(reply)

        # Each output is non-empty
        for i, out in enumerate(outputs):
            with self.subTest(task=i):
                self.assertGreater(len(out.strip()), 20,
                                   f"Task {i} output was trivially short")

        # Task 1 output mentions Verilog or module concept
        self.assertTrue(
            any(w in outputs[1].lower() for w in ["module", "verilog", "always", "wire"]),
            f"Task 1 (RTL) output doesn't look like Verilog: {outputs[1][:300]}",
        )

    def test_history_grows_across_task_calls(self):
        """Each task adds exactly 2 messages (user + assistant)."""
        tasks   = self._tasks()[:3]
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        initial = len(history)   # 1

        for i, task in enumerate(tasks):
            _turn(history, f"Task {i+1}: {task['content']} for '{self.MODULE}'. Be brief.")
            self.assertEqual(len(history), initial + (i + 1) * 2)

    def test_compressed_task_history_supports_next_task(self):
        """Compress after tasks 0-1, then execute task 2 with compressed context."""
        tasks   = self._tasks()
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]

        # Execute tasks 0 and 1
        _turn(history, f"Task 1: {tasks[0]['content']} for '{self.MODULE}'. Be concise.")
        _turn(history, f"Task 2: {tasks[1]['content']} for '{self.MODULE}'. Write the RTL.")

        # Compress
        compressed = _compress(history, workspace="mas-gen")

        # Execute task 2 (lint check) on compressed context
        reply = _turn(
            compressed,
            f"Task 3: {tasks[2]['content']} for '{self.MODULE}'. "
            f"Does the RTL above have obvious lint issues? One sentence.",
        )
        self.assertGreater(len(reply.strip()), 10,
                           f"Task 3 on compressed context returned empty: {reply[:200]}")


# ─────────────────────────────────────────────────────────────
# TestPlanImplementReview
# — Three-call plan → implement → review cycle
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestPlanImplementReview(unittest.TestCase):
    """
    Three sequential calls simulating a plan → implement → review workflow:
    Call 1: Ask GLM to produce a task plan using plan_prompt.md rules
    Call 2: Execute step 1 of the plan
    Call 3: Review the implementation against the plan
    """

    MODULE = "uart_rx"

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def test_plan_call_uses_plan_prompt_rules(self):
        """Call 1: plan prompt → GLM produces a task-tagged plan."""
        from workflow.loader import load_workspace, merge_prompt
        import config
        ws     = _load_ws("mas-gen")
        merged = merge_prompt(
            config.PLAN_MODE_PROMPT, ws.plan_prompt_text, ws.plan_prompt_mode
        )
        history = [
            {"role": "system", "content": merged},
        ]
        reply = _turn(
            history,
            f"Create a task plan for implementing '{self.MODULE}' (UART receiver). "
            f"List 4-6 tasks, one per line, with agent tags.",
        )
        lowered = reply.lower()
        self.assertTrue(
            any(tag in lowered for tag in ["[mas]", "[rtl]", "[tb]", "[sim]", "mas", "rtl", "tb"]),
            f"Plan call didn't produce tagged tasks: {reply[:400]}",
        )

    def test_implement_call_follows_plan(self):
        """Call 2: implement step 1 of the plan (write MAS)."""
        from workflow.loader import load_workspace, merge_prompt
        import config
        ws     = _load_ws("mas-gen")
        merged = merge_prompt(
            config.PLAN_MODE_PROMPT, ws.plan_prompt_text, ws.plan_prompt_mode
        )
        history = [{"role": "system", "content": merged}]

        # Call 1: plan
        plan = _turn(
            history,
            f"Create a task plan for '{self.MODULE}'. List 4 tasks with agent tags.",
        )

        # Call 2: implement first task
        impl = _turn(
            history,
            f"Execute task 1 from the plan. Write a compact MAS for '{self.MODULE}'.",
        )
        self.assertGreater(len(impl.strip()), 30,
                           f"Implementation call returned trivially short response")

    def test_review_call_references_previous_outputs(self):
        """Call 3: review the implementation produced in call 2."""
        from workflow.loader import load_workspace, merge_prompt
        import config
        ws     = _load_ws("mas-gen")
        merged = merge_prompt(
            config.PLAN_MODE_PROMPT, ws.plan_prompt_text, ws.plan_prompt_mode
        )
        history = [{"role": "system", "content": merged}]

        # Call 1
        _turn(history, f"Plan for '{self.MODULE}': list 3 tasks.")
        # Call 2
        _turn(history, f"Execute task 1: write a compact MAS for '{self.MODULE}'.")
        # Call 3: review
        review = _turn(
            history,
            "Review the MAS you just wrote. Does it cover: interface, FSM, and DV plan? "
            "Answer yes/no for each, then give an overall verdict.",
        )
        lowered = review.lower()
        self.assertTrue(
            any(w in lowered for w in ["yes", "no", "interface", "fsm", "dv", "plan", "covered"]),
            f"Review call didn't evaluate the MAS: {review[:400]}",
        )

    def test_three_call_history_has_correct_length(self):
        """Three user turns → history = 1 system + 6 user/assistant messages."""
        ws     = _load_ws("mas-gen")
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]

        _turn(history, f"Plan for '{self.MODULE}': list 3 tasks briefly.")
        _turn(history, f"Execute task 1: write compact MAS for '{self.MODULE}'.")
        _turn(history, "Review the MAS. Is it complete? One sentence verdict.")

        # 1 system + 3 user + 3 assistant = 7
        self.assertEqual(len(history), 7)

    def test_plan_and_implement_outputs_are_distinct(self):
        """Plan output and implementation output should differ in content."""
        ws      = _load_ws("mas-gen")
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        plan    = _turn(history, f"Plan for '{self.MODULE}': list 3 tasks.")
        impl    = _turn(history, f"Execute task 1: write MAS for '{self.MODULE}'.")
        # They should not be identical (plan vs implementation are different)
        self.assertNotEqual(plan[:50], impl[:50],
                            "Plan and implementation outputs are suspiciously identical")


# ─────────────────────────────────────────────────────────────
# TestWorkspaceSwitchMidSession
# — Multiple calls with workspace context switch between them
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestWorkspaceSwitchMidSession(unittest.TestCase):
    """
    Start a conversation in mas-gen, switch to rtl-gen mid-session.
    Verify the second workspace's prompt shapes subsequent responses.
    """

    MODULE = "priority_encoder"

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def test_initial_call_uses_mas-gen_context(self):
        """First call in mas-gen workspace produces spec-focused response."""
        os.environ["ACTIVE_WORKSPACE"] = "mas-gen"
        history = [{"role": "system", "content": _ws_sys("mas-gen")}]
        reply   = _turn(
            history,
            f"What is your primary role? Answer in one sentence.",
        )
        lowered = reply.lower()
        self.assertTrue(
            any(w in lowered for w in ["mas", "spec", "architecture", "coordinate", "rtl", "hardware"]),
            f"mas-gen context not reflected: {reply[:300]}",
        )

    def test_second_call_after_switch_uses_rtl-gen_context(self):
        """After switching to rtl-gen, GLM knows it's an RTL implementation agent."""
        # First call: mas-gen
        os.environ["ACTIVE_WORKSPACE"] = "mas-gen"
        history_mas = [{"role": "system", "content": _ws_sys("mas-gen")}]
        mas_reply   = _turn(
            history_mas,
            f"Write a one-sentence MAS summary for '{self.MODULE}'.",
        )

        # Switch: start new conversation with rtl-gen context
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        history_rtl = [
            {"role": "system", "content": _ws_sys("rtl-gen")},
            # Pass MAS summary as context
            {"role": "user",   "content": f"MAS summary: {mas_reply}"},
            {"role": "assistant", "content": "Understood. I will implement the RTL."},
        ]
        rtl_reply = _turn(
            history_rtl,
            f"Implement the Verilog module for '{self.MODULE}'. "
            f"Keep it concise — just the module definition and one always block.",
        )
        lowered = rtl_reply.lower()
        self.assertTrue(
            "module" in lowered or "always" in lowered or "assign" in lowered,
            f"rtl-gen call didn't produce Verilog: {rtl_reply[:400]}",
        )

    def test_workspace_switch_changes_llm_focus(self):
        """Responses before and after workspace switch have different focus."""
        # mas-gen call
        os.environ["ACTIVE_WORKSPACE"] = "mas-gen"
        mas_reply = _call([
            {"role": "system", "content": _ws_sys("mas-gen")},
            {"role": "user",   "content": "Describe your primary task in one sentence."},
        ])

        # rtl-gen call
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        rtl_reply = _call([
            {"role": "system", "content": _ws_sys("rtl-gen")},
            {"role": "user",   "content": "Describe your primary task in one sentence."},
        ])

        # The two responses should not be identical
        self.assertNotEqual(
            mas_reply.strip()[:60], rtl_reply.strip()[:60],
            "mas-gen and rtl-gen gave identical task descriptions",
        )

    def test_cross_workspace_context_handoff(self):
        """
        mas-gen produces a module spec; rtl-gen receives it and writes RTL;
        tb-gen receives RTL and writes a testbench — three workspace switch calls.
        """
        MODULE = "mux_4to1"
        workspaces = ["mas-gen", "rtl-gen", "tb-gen"]
        prompts    = [
            f"Write a 2-sentence spec for a 4-to-1 multiplexer module '{MODULE}'.",
            f"Given the spec above, write a minimal Verilog module for '{MODULE}'.",
            f"Given the RTL above, write a minimal testbench that applies all 4 input combinations.",
        ]
        outputs = []
        history = []

        for ws_name, prompt in zip(workspaces, prompts):
            os.environ["ACTIVE_WORKSPACE"] = ws_name
            if not history:
                history = [{"role": "system", "content": _ws_sys(ws_name)}]
            else:
                # Replace system prompt with new workspace's
                history[0] = {"role": "system", "content": _ws_sys(ws_name)}

            reply = _turn(history, prompt)
            outputs.append(reply)

        # All three outputs non-trivial
        for i, (ws, out) in enumerate(zip(workspaces, outputs)):
            with self.subTest(stage=ws):
                self.assertGreater(len(out.strip()), 20,
                                   f"{ws} output was empty: {out[:200]}")

        # RTL output should contain Verilog keywords
        self.assertTrue(
            any(w in outputs[1].lower() for w in ["module", "assign", "input", "output"]),
            f"RTL stage didn't produce Verilog: {outputs[1][:300]}",
        )


# ─────────────────────────────────────────────────────────────
# TestCompressionMidSession
# — Compress at various points in a multi-call session
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestCompressionMidSession(unittest.TestCase):
    """
    Multi-call session with compression inserted at specific points.
    Verifies context coherence through compress → continue cycles.
    """

    MODULE = "shift_register"

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def _build_base_history(self, n_turns=4):
        ws_sys  = _ws_sys("rtl-gen")
        history = [{"role": "system", "content": ws_sys}]
        turns   = [
            f"I'm implementing a '{self.MODULE}' in Verilog.",
            "It should be parameterizable width (default 8 bits).",
            "Add a serial-in, parallel-out (SIPO) mode.",
            "The shift direction should be left-to-right.",
        ]
        for t in turns[:n_turns]:
            _turn(history, t)
        return history

    def test_compress_after_4_turns_then_continue(self):
        """Build 4-turn history, compress, then make 2 more calls."""
        history    = self._build_base_history(4)
        compressed = _compress(history, workspace="rtl-gen")

        # Continue with 2 more LLM calls
        r1 = _turn(compressed, f"Implement the '{self.MODULE}' Verilog module now.")
        r2 = _turn(compressed, "Does the module you wrote have a reset signal? Yes or no.")

        self.assertGreater(len(r1.strip()), 20, f"Post-compress call 1 empty: {r1[:200]}")
        self.assertIn(
            r2.lower()[:3], ["yes", "no", "the", "it ", "the", "yes", "no"],
            f"Post-compress call 2 unexpected: {r2[:200]}",
        )

    def test_module_name_remembered_after_compression(self):
        """Module name must survive compression and be referenced in follow-up."""
        history    = self._build_base_history(4)
        compressed = _compress(history, workspace="rtl-gen")
        reply      = _turn(compressed, "What was the module name I asked you to implement?")
        self.assertIn(
            self.MODULE, reply.lower(),
            f"Module name lost after compression: {reply[:300]}",
        )

    def test_two_compress_then_final_call(self):
        """
        6 turns → compress → 3 more turns → compress again → final call.
        Verify the final response is coherent.
        """
        history = self._build_base_history(4)
        _turn(history, "Add an enable signal.")
        _turn(history, "Make the reset synchronous.")

        # First compression
        c1 = _compress(history, workspace="rtl-gen")
        _turn(c1, "Now write the complete Verilog module.")
        _turn(c1, "Add $dumpvars for simulation debug.")
        _turn(c1, "Remove the $dumpvars — keep it synthesis-clean.")

        # Second compression
        c2 = _compress(c1, workspace="rtl-gen")

        # Final call
        final = _turn(c2, f"Summarise the '{self.MODULE}' spec in 2 sentences.")
        self.assertGreater(len(final.strip()), 20,
                           f"Final call after double compress returned empty: {final[:200]}")

    def test_workspace_compression_prompt_used_in_mid_session(self):
        """Compress using mas-gen's compression_prompt.md during a session."""
        ws   = _load_ws("mas-gen")
        import core.compressor as comp
        importlib.reload(comp)
        orig = comp.STRUCTURED_SUMMARY_PROMPT
        comp.STRUCTURED_SUMMARY_PROMPT = ws.compression_prompt_text
        try:
            history    = self._build_base_history(4)
            compressed = _compress(history, workspace="mas-gen")
        finally:
            comp.STRUCTURED_SUMMARY_PROMPT = orig

        # Continue with rtl-gen context
        reply = _turn(
            compressed,
            f"Based on the session so far, implement the '{self.MODULE}' Verilog module.",
        )
        self.assertGreater(len(reply.strip()), 20,
                           f"Post-MAS-compression RTL call empty: {reply[:200]}")

    def test_four_call_cycle_with_compression_in_middle(self):
        """
        Call 1: design decision
        Call 2: implement
        Compress
        Call 3: review
        Call 4: final verdict
        All four calls must return coherent non-empty content.
        """
        history = [{"role": "system", "content": _ws_sys("rtl-gen")}]

        r1 = _turn(history, f"I need a '{self.MODULE}' with 8-bit width and synchronous reset. Acknowledge.")
        r2 = _turn(history, f"Implement the Verilog module for '{self.MODULE}'.")

        compressed = _compress(history, workspace="rtl-gen")

        r3 = _turn(compressed, "Review the RTL for potential lint errors. List any issues.")
        r4 = _turn(compressed, "Give a one-sentence verdict: is this implementation complete?")

        for i, reply in enumerate([r1, r2, r3, r4], 1):
            with self.subTest(call=i):
                self.assertGreater(len(reply.strip()), 5,
                                   f"Call {i} returned empty response")


if __name__ == "__main__":
    unittest.main()
