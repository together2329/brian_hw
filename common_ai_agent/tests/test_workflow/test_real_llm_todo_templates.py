"""
Real LLM deep tests for todo template application — GLM-5.1 on Z.AI.

Tests are grouped around the actual template workflows:
  - Template Comprehension: LLM reads task list and explains what to do
  - Task Execution Simulation: LLM follows task instructions correctly
  - Loop Simulation: SIM loop iteration count, exit detection, max limit
  - Pipeline Chain: MAS → RTL → TB handoff chain driven by template tasks
  - Legacy IP Constraints: backward-compat rules enforced by LLM

All prompts use _INLINE to suppress tool calls.
Auto-skip when GLM-5.1 / Z.AI is unreachable.
"""
import importlib
import json
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
WORKFLOW_DIR = PROJECT_ROOT / "workflow"


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
_SKIP = unittest.skipUnless(_API_OK, "GLM-5.1 / Z.AI not reachable — skipping")


# ── shared helpers ────────────────────────────────────────────────────────────

def _call(messages) -> str:
    import llm_client as lc
    chunks = list(lc.chat_completion_stream(
        messages, skip_rate_limit=True, suppress_spinner=True
    ))
    return "".join(c for c in chunks if isinstance(c, str))


def _turn(history: list, user_msg: str) -> str:
    history.append({"role": "user", "content": user_msg})
    reply = _call(history)
    history.append({"role": "assistant", "content": reply})
    return reply


def _ws_sys(ws_name: str) -> str:
    from workflow.loader import load_workspace, merge_prompt
    import core.prompt_builder as pb
    importlib.reload(pb)
    ws = load_workspace(ws_name, PROJECT_ROOT)
    base = pb.build_system_prompt()
    if isinstance(base, dict):
        base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
    return merge_prompt(base, ws.system_prompt_text, ws.system_prompt_mode)


def _load_template(workspace: str, stem: str) -> dict:
    p = WORKFLOW_DIR / workspace / "todo_templates" / f"{stem}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _tasks_as_prompt(tasks: list) -> str:
    """Format task list into a numbered prompt string for the LLM."""
    lines = []
    for i, t in enumerate(tasks):
        loop_note = " [LOOP]" if t.get("loop") else ""
        priority = t.get("priority", "high")
        lines.append(f"Task {i+1}{loop_note} [{priority}]: {t['content']}")
    return "\n".join(lines)


# Suppress tool calls and file reads in all prompts
_INLINE = (
    " Respond with text only — do not call tools, read files, or create todo lists."
    " Write everything directly in your response."
)


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoTemplateComprehension
# — LLM correctly understands a template's structure and intent
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoTemplateComprehension(unittest.TestCase):
    """LLM reads template task lists and describes them accurately."""

    def _base_history(self, ws="mas-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_new_ip_task_count_and_order(self):
        """LLM can count and order tasks in new-ip template."""
        tmpl = _load_template("mas-gen", "new-ip")
        task_text = _tasks_as_prompt(tmpl["tasks"])
        h = self._base_history()
        reply = _turn(
            h,
            f"Here is a todo task list for generating a new IP:\n\n{task_text}\n\n"
            f"How many tasks are there total? Which task has a [LOOP] marker? "
            f"What is the very last task?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(n in r for n in ["9", "nine"]),
            f"Should say 9 total tasks, got: {reply[:300]}"
        )
        self.assertIn("[sim]", r, "Should identify the SIM task as the loop task")

    def test_legacy_ip_user_confirmation_step(self):
        """LLM identifies the mandatory user sign-off step in legacy-ip template."""
        tmpl = _load_template("mas-gen", "legacy-ip")
        task_text = _tasks_as_prompt(tmpl["tasks"])
        h = self._base_history()
        reply = _turn(
            h,
            f"Here is a todo task list for updating a legacy IP:\n\n{task_text}\n\n"
            f"Which task requires explicit user confirmation before proceeding? "
            f"Why is this step necessary?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["task 3", "third", "confirm", "sign-off", "user"]),
            f"Should identify the user confirmation task: {reply[:300]}"
        )

    def test_rtl_new_ip_section_mapping(self):
        """LLM maps each rtl-gen task to the MAS section it implements."""
        tmpl = _load_template("rtl-gen", "new-ip-rtl")
        task_text = _tasks_as_prompt(tmpl["tasks"])
        h = self._base_history("rtl-gen")
        reply = _turn(
            h,
            f"Here is the RTL generation task list:\n\n{task_text}\n\n"
            f"Which task implements the FSM? Which task implements the register map? "
            f"Which MAS section does each map to?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["task 3", "third", "fsm"]),
            f"Should identify FSM task: {reply[:300]}"
        )
        self.assertTrue(
            any(p in r for p in ["task 5", "fifth", "register", "csr"]),
            f"Should identify register map task: {reply[:300]}"
        )

    def test_tb-gen_sequence_naming_convention(self):
        """LLM knows tc_ tasks are named after MAS §9 sequence IDs."""
        tmpl = _load_template("tb-gen", "new-ip-tb")
        task_text = _tasks_as_prompt(tmpl["tasks"])
        h = self._base_history("tb-gen")
        reply = _turn(
            h,
            f"Here is the TB generation task list:\n\n{task_text}\n\n"
            f"What naming convention should test case tasks follow? "
            f"Give an example name for the reset sequence task." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["tc_s1", "tc_", "s1_reset"]),
            f"Should mention tc_S1_reset naming: {reply[:300]}"
        )

    def test_new_vs_legacy_workflow_difference(self):
        """LLM correctly explains the difference between new-ip and legacy-ip."""
        new_tmpl = _load_template("mas-gen", "new-ip")
        leg_tmpl = _load_template("mas-gen", "legacy-ip")
        new_tasks = _tasks_as_prompt(new_tmpl["tasks"])
        leg_tasks = _tasks_as_prompt(leg_tmpl["tasks"])
        h = self._base_history()
        reply = _turn(
            h,
            f"Here are two task lists:\n\n"
            f"LIST A (new-ip):\n{new_tasks}\n\n"
            f"LIST B (legacy-ip):\n{leg_tasks}\n\n"
            f"What is the key difference in approach? "
            f"Why does List B have a user confirmation step that List A does not?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["backward", "existing", "delta", "compatibility"]),
            f"Should mention backward compat or delta approach: {reply[:400]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoTaskExecutionSimulation
# — LLM correctly executes the content of individual tasks
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoTaskExecutionSimulation(unittest.TestCase):
    """LLM performs the actual work described in each task."""

    def _base_history(self, ws="mas-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_task1_requirements_gathering(self):
        """Task 1 (new-ip): LLM gathers port/feature requirements for a module."""
        task = _load_template("mas-gen", "new-ip")["tasks"][0]
        h = self._base_history()
        reply = _turn(
            h,
            f"Execute this task: {task['content']}\n\n"
            f"Context: We are designing a module called 'edge_detector' that detects "
            f"rising and falling edges of an input signal. "
            f"Apply the task's checklist to confirm what we need." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["port", "clock", "input", "output", "edge", "module"]),
            f"Should extract port/interface requirements: {reply[:400]}"
        )

    def test_task_read_rtl_extracts_ports(self):
        """Legacy RTL task[0]: LLM extracts port info from given RTL snippet."""
        h = self._base_history("rtl-gen")
        rtl_snippet = """\
module counter8 (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        en,
    output logic [7:0]  count
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) count <= 8'd0;
        else if (en) count <= count + 1;
    end
endmodule"""
        reply = _turn(
            h,
            f"Read this RTL and extract: module name, all port names/widths/directions. "
            f"This is the first step of a legacy-ip update workflow — "
            f"identify the current interface as a baseline.\n\n"
            f"```systemverilog\n{rtl_snippet}\n```" + _INLINE
        )
        r = reply.lower()
        for port in ["clk", "rst_n", "en", "count"]:
            self.assertIn(port, r, f"Should identify port '{port}'")

    def test_task_dv_plan_to_sequence_list(self):
        """TB task[0]: LLM maps a DV Plan section to S1-SN test sequence names."""
        h = self._base_history("tb-gen")
        dv_plan = """\
§9 DV Plan — edge_detector
Test Sequences:
  S1: reset — assert rst for 3 cycles, verify rise/fall outputs = 0
  S2: rising_edge — toggle data 0→1, verify rise=1 on next cycle, fall=0
  S3: falling_edge — toggle data 1→0, verify fall=1 on next cycle, rise=0
  S4: back_to_back — consecutive edges, verify both outputs independent
Coverage: line ≥90%, branch ≥85%
SVA: rise and fall never assert simultaneously"""
        reply = _turn(
            h,
            f"Given this DV Plan section:\n\n{dv_plan}\n\n"
            f"List all tc_ task names you need to implement (one per sequence). "
            f"Follow the naming convention tc_<SequenceID>_<name>." + _INLINE
        )
        r = reply.lower()
        for seq in ["tc_s1", "tc_s2", "tc_s3", "tc_s4"]:
            self.assertIn(seq, r, f"Should produce task name '{seq}'")

    def test_task_write_s1_reset_sequence(self):
        """TB task[1] (new-ip-tb): LLM writes a reset verification sequence."""
        h = self._base_history("tb-gen")
        reply = _turn(
            h,
            "Write the SystemVerilog task tc_S1_reset() for a module 'edge_detector' "
            "with ports: clk, rst_n, data_in, rise_out, fall_out. "
            "The task should: (1) assert rst_n=0 for 3 cycles, (2) deassert rst_n=1, "
            "(3) verify rise_out=0 and fall_out=0. "
            "Use pass_cnt/fail_cnt and print [PASS]/[FAIL]." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["task tc_s1_reset", "tc_s1_reset", "pass_cnt", "fail_cnt"]),
            f"Should produce tc_S1_reset task: {reply[:400]}"
        )
        self.assertTrue(
            any(p in r for p in ["rst_n", "3", "rise_out", "fall_out"]),
            f"Should check reset behavior: {reply[:400]}"
        )

    def test_task_write_mas_overview_section(self):
        """MAS task[1] (new-ip): LLM writes §1 Overview for a simple module."""
        h = self._base_history()
        reply = _turn(
            h,
            "Execute MAS task: Write §1 Overview and §2 Module Interface for a module called "
            "'pwm_gen' — a simple PWM signal generator with an 8-bit duty cycle register, "
            "a period counter, and an active-high output. "
            "Include: one-paragraph description (§1), and port table with clk/rst_n/duty_cycle[7:0]/"
            "pwm_out (§2)." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["§1", "overview", "description"]),
            f"Should produce §1 section: {reply[:400]}"
        )
        self.assertTrue(
            any(p in r for p in ["§2", "port", "interface"]),
            f"Should produce §2 port section: {reply[:400]}"
        )
        for port in ["clk", "duty_cycle", "pwm_out"]:
            self.assertIn(port, r, f"Port '{port}' should be in §2")

    def test_task_delta_list_for_legacy_update(self):
        """Legacy-ip task[1]: LLM extracts a delta list of changes needed."""
        h = self._base_history("rtl-gen")
        reply = _turn(
            h,
            "You have an existing 8-bit counter (counter8) with ports: clk, rst_n, en, count[7:0]. "
            "The new MAS delta requires: (1) add a 'load' input for preset value, "
            "(2) add a 'load_val[7:0]' input, (3) add a 'overflow' output. "
            "Build the delta list following the legacy-ip-rtl template task 1: "
            "list (A) new ports, (B) modified logic, (C) new FSM states if any, "
            "(D) new registers if any." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["(a)", "new port", "load", "load_val"]),
            f"Should list new ports in delta: {reply[:400]}"
        )
        self.assertTrue(
            any(p in r for p in ["overflow", "(c)", "(b)"]),
            f"Should list modified logic: {reply[:400]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoLoopSimulation
# — SIM loop task: iteration counting, exit detection, max limit
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoLoopSimulation(unittest.TestCase):
    """LLM correctly manages loop iteration state and exit conditions."""

    def _base_history(self, ws="tb-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def _loop_task_prompt(self, tmpl_ws: str, tmpl_stem: str) -> str:
        """Return the loop task from the template as a formatted string."""
        tasks = _load_template(tmpl_ws, tmpl_stem)["tasks"]
        loop_task = next(t for t in tasks if t.get("loop"))
        return (
            f"Loop task: {loop_task['content']}\n"
            f"Exit condition: {loop_task['exit_condition']}\n"
            f"Max iterations: {loop_task['max_loop_iterations']}"
        )

    def test_loop_not_done_on_errors(self):
        """LLM says loop must continue when simulator output has errors."""
        loop_info = self._loop_task_prompt("tb-gen", "new-ip-tb")
        _max = next(
            t for t in _load_template("tb-gen", "new-ip-tb")["tasks"] if t.get("loop")
        )["max_loop_iterations"]
        h = self._base_history()
        reply = _turn(
            h,
            f"{loop_info}\n\n"
            f"Iteration 1/{_max}: "
            f"Simulator output:\n"
            f"  tb_edge_detector.sv:42: ERROR — undeclared signal 'data_in'\n"
            f"  tb_edge_detector.sv:58: ERROR — width mismatch on port 'count'\n"
            f"  2 errors, 0 warnings\n\n"
            f"Has the exit condition been met? What should happen next?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["not met", "not done", "continue", "not yet",
                                  "still", "errors remain", "fix", "iteration"]),
            f"Should say loop not done: {reply[:300]}"
        )

    def test_loop_done_on_zero_errors(self):
        """LLM recognizes exit condition met when output says 0 errors, 0 warnings."""
        loop_info = self._loop_task_prompt("tb-gen", "new-ip-tb")
        max_iters = next(
            t for t in _load_template("tb-gen", "new-ip-tb")["tasks"] if t.get("loop")
        )["max_loop_iterations"]
        h = self._base_history()
        reply = _turn(
            h,
            f"{loop_info}\n\n"
            f"Iteration 3/{max_iters}: Simulator output:\n"
            f"  Compilation: OK\n"
            f"  [PASS] tc_S1_reset\n"
            f"  [PASS] tc_S2_rising_edge\n"
            f"  [PASS] tc_S3_falling_edge\n"
            f"  Result: 3/3 tests passed\n"
            f"  0 errors, 0 warnings\n\n"
            f"Has the exit condition been met? Should we proceed to the next task?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["exit condition met", "condition met", "passed",
                                  "proceed", "complete", "done", "met"]),
            f"Should say exit condition met: {reply[:300]}"
        )

    def test_loop_iteration_counter_tracking(self):
        """LLM tracks iteration count across multiple loop turns."""
        loop_task = next(
            t for t in _load_template("tb-gen", "new-ip-tb")["tasks"] if t.get("loop")
        )
        max_iters = loop_task["max_loop_iterations"]
        h = self._base_history()

        # Feed 3 iterations with errors
        for i in range(1, 4):
            _turn(
                h,
                f"Loop iteration {i}/{max_iters}. "
                f"Simulator: 2 errors in tb_pwm.sv. Fix in progress." + _INLINE
            )

        # 4th turn: ask what iteration we're on
        reply = _turn(h, "What iteration of the SIM loop are we currently on?" + _INLINE)
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["4", "four", "iteration 4", "3", "three"]),
            f"Should track iteration count: {reply[:300]}"
        )

    def test_loop_exit_on_fuzzy_clean_signal(self):
        """Exit condition triggers on fuzzy 'no errors' phrasing, not just exact '0 errors'."""
        loop_info = self._loop_task_prompt("mas-gen", "new-ip")
        max_iters = next(
            t for t in _load_template("mas-gen", "new-ip")["tasks"] if t.get("loop")
        )["max_loop_iterations"]
        h = self._base_history()
        reply = _turn(
            h,
            f"{loop_info}\n\n"
            f"Iteration 2/{max_iters}: Simulator output:\n"
            f"  Compilation successful. No issues found.\n"
            f"  All test sequences pass.\n\n"
            f"Does 'Compilation successful. No issues found.' satisfy the exit condition "
            f"'0 errors, 0 warnings'?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["yes", "satisfied", "met", "equivalent", "passes",
                                  "successful", "effectively"]),
            f"Should accept fuzzy clean signal: {reply[:300]}"
        )

    def test_loop_max_iteration_escalation(self):
        """LLM reports escalation path when max iterations is reached without exit."""
        max_iters = 15
        h = self._base_history()
        reply = _turn(
            h,
            f"We are running the SIM loop task with max_loop_iterations={max_iters}. "
            f"We have just completed iteration {max_iters} and the simulator still shows errors:\n"
            f"  3 errors in tb_counter.sv\n\n"
            f"The exit condition (0 errors, 0 warnings) has not been met. "
            f"What should happen now that we have reached the maximum iteration limit?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["escalate", "report", "maximum", "max", "limit",
                                  "investigate", "cannot", "stuck", "review"]),
            f"Should report max iteration reached: {reply[:300]}"
        )

    def test_legacy_regression_loop_distinguishes_old_vs_new_failures(self):
        """Legacy IP SIM loop: LLM distinguishes regression in old sequences vs new sequence fails."""
        h = self._base_history()
        reply = _turn(
            h,
            "We are running the legacy-ip regression SIM loop. "
            "Simulator output:\n"
            "  [FAIL] tc_S1_reset — expected count=0 after reset, got count=255\n"
            "  [PASS] tc_S2_normal_op\n"
            "  [PASS] tc_S_NEW_1_load_preset\n"
            "  1 error (in original sequence S1)\n\n"
            "The legacy-ip template says: 'Any regression in original sequences = RTL bug'. "
            "What is the correct action? Should we fix the TB or the RTL?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["rtl", "dut", "rtl bug", "not the tb", "fix rtl"]),
            f"Should say RTL bug, not TB bug: {reply[:300]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoTemplatePipelineChain
# — Multi-stage handoff: MAS → RTL → TB driven by template task content
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoTemplatePipelineChain(unittest.TestCase):
    """LLM follows template pipeline: each stage outputs input for the next."""

    def test_mas_task5_produces_rtl_handoff(self):
        """MAS task[5] ([RTL]) produces a [MAS HANDOFF] → rtl-gen message."""
        h = [{"role": "system", "content": _ws_sys("mas-gen")}]
        task5 = _load_template("mas-gen", "new-ip")["tasks"][5]
        reply = _turn(
            h,
            f"Execute this task: {task5['content']}\n\n"
            f"Module: edge_detector. MAS is complete. "
            f"Produce the handoff message to rtl-gen with all required fields: "
            f"Module, MAS, Task, Input, Output, Criteria." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["mas handoff", "rtl-gen", "handoff"]),
            f"Should produce MAS HANDOFF message: {reply[:400]}"
        )
        self.assertIn("edge_detector", r, "Module name should be in handoff")

    def test_rtl_task8_produces_mas_result(self):
        """RTL lint task ([MAS RESULT] rtl-gen DONE) sends completion signal."""
        h = [{"role": "system", "content": _ws_sys("rtl-gen")}]
        lint_task = _load_template("rtl-gen", "new-ip-rtl")["tasks"][-1]
        reply = _turn(
            h,
            f"Execute: {lint_task['content']}\n\n"
            f"Module: edge_detector. Lint output: 0 errors, 0 warnings. "
            f"Produce the completion report back to mas-gen as described in the task detail: "
            f"{lint_task.get('detail', '')}" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["mas result", "[mas result]", "rtl-gen done", "done"]),
            f"Should produce [MAS RESULT] signal: {reply[:400]}"
        )

    def test_tb_task_receives_mas_handoff_and_responds(self):
        """TB agent receives [MAS HANDOFF] message and acknowledges correctly."""
        h = [{"role": "system", "content": _ws_sys("tb-gen")}]
        handoff = """\
[MAS HANDOFF] → tb-gen
Module  : edge_detector
MAS     : edge_detector_mas.md
Task    : Generate testbench and simulate
Input   : edge_detector_mas.md, edge_detector.sv
Output  : tb_edge_detector.sv, tc_edge_detector.sv
Criteria: 0 errors, 0 warnings; all S1-SN sequences PASS"""
        reply = _turn(
            h,
            f"{handoff}\n\n"
            f"You received this MAS HANDOFF. Based on the TB gen system prompt, "
            f"what are your first steps? What files do you need to read?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["edge_detector_mas.md", "mas.md", "edge_detector.sv", ".sv"]),
            f"Should identify input files from handoff: {reply[:400]}"
        )
        self.assertIn("edge_detector", r, "Module name should be recognized")

    def test_full_new_ip_chain_module_name_consistent(self):
        """Module name 'fifo8' stays consistent across MAS → RTL → TB tasks."""
        module = "fifo8"
        h = [{"role": "system", "content": _ws_sys("mas-gen")}]

        # Turn 1: MAS overview
        _turn(h, f"Write a one-sentence §1 Overview for module '{module}': "
                 f"an 8-entry FIFO with 8-bit data, push/pop interface, full/empty flags." + _INLINE)

        # Turn 2: RTL handoff
        _turn(h, f"Now produce the [MAS HANDOFF] → rtl-gen message for '{module}'." + _INLINE)

        # Turn 3: RTL task context — still refers to same module
        reply3 = _turn(h, f"Based on this conversation, what is the module name "
                          f"for the RTL implementation task?" + _INLINE)

        all_text = " ".join(m["content"] for m in h).lower()
        self.assertIn(module, all_text, "Module name must be consistent across all turns")
        self.assertIn(module, reply3.lower(), "RTL task should still reference fifo8")

    def test_mas_to_rtl_port_preservation(self):
        """Ports defined in MAS §2 are reflected in the RTL task output."""
        h = [{"role": "system", "content": _ws_sys("mas-gen")}]

        # Define ports in MAS
        _turn(h, "Write §2 Interface for 'pwm_gen' with ports: "
                 "clk (input, 1b), rst_n (input, 1b), duty[7:0] (input, 8b), pwm_out (output, 1b). "
                 "Show as a port table." + _INLINE)

        # Ask RTL task to use those ports
        reply2 = _turn(h, "Based on the §2 port table above, write the SystemVerilog module header "
                          "for pwm_gen with all four ports declared." + _INLINE)

        r = reply2.lower()
        for port in ["clk", "rst_n", "duty", "pwm_out"]:
            self.assertIn(port, r, f"Port '{port}' must appear in module header")


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoLegacyIpConstraints
# — LLM enforces backward-compatibility rules from legacy IP templates
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoLegacyIpConstraints(unittest.TestCase):
    """LLM applies legacy-IP backward-compat constraints when executing tasks."""

    def _base_history(self, ws="rtl-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_new_port_added_at_end_of_list(self):
        """Legacy RTL task[1]: LLM adds new port at END, not in middle."""
        task = _load_template("rtl-gen", "legacy-ip-rtl")["tasks"][1]
        h = self._base_history()
        reply = _turn(
            h,
            f"Task: {task['content']}\n\nRule: {task['detail']}\n\n"
            f"Existing port list for 'counter8':\n"
            f"  input  logic clk,\n"
            f"  input  logic rst_n,\n"
            f"  input  logic en,\n"
            f"  output logic [7:0] count\n\n"
            f"Add a new 'overflow' output port. Show the updated port list." + _INLINE
        )
        r = reply.lower()
        # 'overflow' must appear AFTER 'count' in reply
        count_pos = r.find("count")
        overflow_pos = r.find("overflow")
        self.assertGreater(count_pos, -1, "Should still have 'count' port")
        self.assertGreater(overflow_pos, -1, "Should add 'overflow' port")
        self.assertGreater(overflow_pos, count_pos,
                           "overflow must come AFTER count (end of list rule)")

    def test_existing_register_offset_preserved(self):
        """Legacy RTL task[4]: LLM adds new register at NEW offset, preserves old offsets."""
        task = _load_template("rtl-gen", "legacy-ip-rtl")["tasks"][4]
        h = self._base_history()
        reply = _turn(
            h,
            f"Task: {task['content']}\n\nRule: {task['detail']}\n\n"
            f"Existing register map:\n"
            f"  0x00: CTRL  (R/W) — enable/mode bits\n"
            f"  0x04: STATUS (RO) — busy/done flags\n"
            f"  0x08: DATA   (R/W) — payload register\n\n"
            f"Add a new 'THRESHOLD' (R/W) register. What offset should it use? "
            f"Confirm the existing offsets are unchanged." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["0x0c", "0x10", "0x12", "new offset", "next offset"]),
            f"Should use a new (non-conflicting) offset: {reply[:400]}"
        )
        # Old offsets should still be present
        for addr in ["0x00", "0x04", "0x08"]:
            self.assertIn(addr, r, f"Existing offset {addr} must be preserved")

    def test_changed_annotation_added_to_modified_logic(self):
        """Legacy RTL task[3]: LLM adds // CHANGED: vX.Y comment to modified lines."""
        task = _load_template("rtl-gen", "legacy-ip-rtl")["tasks"][3]
        h = self._base_history()
        reply = _turn(
            h,
            f"Task: {task['content']}\n\nRule from detail: {task['detail']}\n\n"
            f"Modify this always_ff block to add enable behavior (en signal):\n"
            f"```\nalways_ff @(posedge clk or negedge rst_n) begin\n"
            f"    if (!rst_n) count <= 0;\n"
            f"    else count <= count + 1;\n"
            f"end\n```\n"
            f"Add // CHANGED: v2.1 comment next to every line you modify." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["changed:", "// changed", "changed: v"]),
            f"Should add CHANGED annotation: {reply[:400]}"
        )

    def test_removing_port_breaks_backward_compat(self):
        """LLM correctly identifies that removing an existing port breaks backward compat."""
        h = self._base_history()
        reply = _turn(
            h,
            "We are updating a legacy IP module 'uart_rx'. "
            "A developer proposes to REMOVE the existing 'parity_en' input port "
            "because the new design hardcodes even parity. "
            "According to the legacy-ip-rtl template rule: "
            "'Add new ports at the END of the port list — never reorder or remove existing ports.' "
            "Is this proposed change acceptable? What is the correct approach?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["not acceptable", "breaks", "backward", "cannot remove",
                                  "should not remove", "violation", "incompatible"]),
            f"Should flag removal as backward-compat violation: {reply[:300]}"
        )

    def test_fsm_new_state_preserves_existing_transitions(self):
        """Legacy RTL task[2]: LLM adds new FSM state without touching existing transitions."""
        task = _load_template("rtl-gen", "legacy-ip-rtl")["tasks"][2]
        h = self._base_history()
        reply = _turn(
            h,
            f"Task: {task['content']}\n\nRule: {task['detail']}\n\n"
            f"Existing FSM states: IDLE, ACTIVE, DONE.\n"
            f"Transitions: IDLE → ACTIVE (on start), ACTIVE → DONE (on finish), DONE → IDLE (always).\n"
            f"Add a new 'ERROR' state that ACTIVE transitions to when an err signal fires.\n"
            f"Show only the new/changed case clauses. Do NOT touch IDLE→ACTIVE or ACTIVE→DONE." + _INLINE
        )
        r = reply.lower()
        self.assertIn("error", r, "Should add ERROR state")
        self.assertTrue(
            any(p in r for p in ["idle", "active", "done"]),
            f"Existing states should still be present: {reply[:400]}"
        )
        self.assertTrue(
            any(p in r for p in ["err", "error state", "active → error", "active: begin"]),
            f"Should show new ACTIVE → ERROR transition: {reply[:400]}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# TestTodoTemplateTaskCompletion
# — LLM understands task completion signals and transitions to the next task
# ─────────────────────────────────────────────────────────────────────────────

@_SKIP
class TestTodoTemplateTaskCompletion(unittest.TestCase):
    """LLM correctly recognizes task done state and transitions to next step."""

    def _base_history(self, ws="mas-gen"):
        return [{"role": "system", "content": _ws_sys(ws)}]

    def test_task_completes_on_success_criteria(self):
        """A non-loop task is done when its success criteria is met."""
        h = self._base_history()
        reply = _turn(
            h,
            "We are on Task 2 of the new-ip template: "
            "'[MAS] Write §1 Overview and §2 Module Hierarchy + Interface'. "
            "We have produced:\n"
            "  §1: A brief overview paragraph.\n"
            "  §2: A port table with 4 ports.\n\n"
            "Is Task 2 complete? What is the next task?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["task 2 is complete", "complete", "done", "yes",
                                  "proceed", "next", "task 3"]),
            f"Should confirm task 2 done and move to task 3: {reply[:300]}"
        )

    def test_high_priority_tasks_before_normal(self):
        """LLM correctly respects that high-priority tasks must finish before normal."""
        tmpl = _load_template("mas-gen", "new-ip")
        task_text = _tasks_as_prompt(tmpl["tasks"])
        h = self._base_history()
        reply = _turn(
            h,
            f"Here is the new-ip task list:\n\n{task_text}\n\n"
            f"If Task 8 ([SIM] loop) is still running with errors, "
            f"can we skip ahead to Task 9 ([DOC]) since it has 'normal' priority? "
            f"Explain." + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["no", "should not", "cannot", "must complete",
                                  "sim", "before", "prerequisite", "not skip"]),
            f"Should say can't skip to DOC before SIM passes: {reply[:300]}"
        )

    def test_loop_task_transitions_after_exit(self):
        """After SIM loop exit condition is met, LLM transitions to coverage task."""
        h = self._base_history("tb-gen")
        tmpl = _load_template("tb-gen", "new-ip-tb")
        tasks = tmpl["tasks"]
        loop_idx = next(i for i, t in enumerate(tasks) if t.get("loop"))
        next_task = tasks[loop_idx + 1]

        reply = _turn(
            h,
            f"We just completed the SIM loop task: '{tasks[loop_idx]['content']}'\n"
            f"Exit condition 'O errors, 0 warnings' was met on iteration 4/15.\n\n"
            f"What is the NEXT task to execute? Here is the full task list:\n"
            f"{_tasks_as_prompt(tasks)}" + _INLINE
        )
        r = reply.lower()
        self.assertIn(
            next_task["content"].lower()[:30],
            r + reply.lower(),
            f"Should transition to: {next_task['content']}"
        )
        self.assertTrue(
            any(p in r for p in ["coverage", "next", "proceed", "last"]),
            f"Should move to coverage review: {reply[:300]}"
        )

    def test_mas_escalation_when_dut_bug_found(self):
        """TB agent correctly escalates to rtl-gen when a DUT bug is found."""
        h = [{"role": "system", "content": _ws_sys("tb-gen")}]
        reply = _turn(
            h,
            "We are running the SIM loop for edge_detector. "
            "tc_S2_rising_edge fails: rise_out stays 0 even after data_in goes 0→1. "
            "We have verified the TB stimulus is correct (data_in toggled at posedge clk). "
            "According to the TB gen rules, what is the correct action?\n\n"
            "Options:\n"
            "  A) Fix tc_S2_rising_edge to change the stimulus\n"
            "  B) Report [MAS ESCALATE] rtl-gen — DUT bug\n"
            "  C) Modify edge_detector.sv to fix the RTL\n"
            "  D) Skip this test case\n\n"
            "Which option is correct and why?" + _INLINE
        )
        r = reply.lower()
        self.assertTrue(
            any(p in r for p in ["option b", "(b)", "mas escalate", "escalate",
                                  "rtl-gen", "dut bug"]),
            f"Should choose option B escalation: {reply[:400]}"
        )


if __name__ == "__main__":
    unittest.main()
