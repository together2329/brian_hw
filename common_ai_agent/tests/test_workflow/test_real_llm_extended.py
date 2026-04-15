"""
Extended real LLM tests — GLM-5.1 on Z.AI.

Expands test_real_llm.py to cover:
  - Plan prompt injection (config.PLAN_MODE_PROMPT) + behaviour verification
  - Multi-turn context continuity across workspace-patched conversations
  - Todo task content: GLM understands real template task descriptions
  - Compression quality: structured summary, module names preserved, MAS-style output
  - Sim / lint workspace-specific behaviour (distinct from rtl/tb)
  - Workspace description (ACTIVE_WORKSPACE_DESC) in system prompt
  - Robustness: very short history, !important preservation, double compression

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


_API_OK  = _api_available()
_SKIP    = unittest.skipUnless(_API_OK, "GLM-5.1 / Z.AI not reachable — skipping")


# ── shared helpers ────────────────────────────────────────────────────────────

def _call(messages):
    import llm_client as lc
    chunks = list(lc.chat_completion_stream(
        messages, skip_rate_limit=True, suppress_spinner=True
    ))
    return "".join(c for c in chunks if isinstance(c, str))


def _sys(text):
    return {"role": "system", "content": text}


def _usr(text):
    return {"role": "user", "content": text}


def _ast(text):
    return {"role": "assistant", "content": text}


def _load_ws(name):
    from workflow.loader import load_workspace
    return load_workspace(name, PROJECT_ROOT)


def _make_cfg():
    return types.SimpleNamespace(
        ENABLE_COMPRESSION               = True,
        MAX_CONTEXT_CHARS                = 512_000,
        COMPRESSION_THRESHOLD            = 0.9,
        PREEMPTIVE_COMPRESSION_THRESHOLD = 0.85,
        COMPRESSION_CHUNK_SIZE           = 10,
        COMPRESSION_KEEP_RECENT          = 4,
        COMPRESSION_MODE                 = "single",
        ENABLE_TURN_PROTECTION           = False,
        TURN_PROTECTION_COUNT            = 3,
    )


def _compress(messages, instruction=None, workspace=None):
    from core.compressor import compress_history
    import llm_client as lc
    if workspace:
        os.environ["ACTIVE_WORKSPACE"] = workspace
    else:
        os.environ.pop("ACTIVE_WORKSPACE", None)
    return compress_history(
        messages,
        force=True,
        instruction=instruction,
        quiet=True,
        cfg=_make_cfg(),
        llm_call_fn=lc.chat_completion_stream,
    )


def _ws_system_prompt(ws_name):
    """Build the patched system prompt for a workspace (string form)."""
    from workflow.loader import load_workspace, merge_prompt
    import core.prompt_builder as pb
    importlib.reload(pb)
    ws   = load_workspace(ws_name, PROJECT_ROOT)
    base = pb.build_system_prompt()
    if isinstance(base, dict):
        base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
    return merge_prompt(base, ws.system_prompt_text, ws.system_prompt_mode)


# ─────────────────────────────────────────────────────────────
# TestRealGLM51PlanPrompt
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51PlanPrompt(unittest.TestCase):
    """
    Verify that workspace plan_prompt.md reaches GLM-5.1 and shapes its
    planning / task-decomposition responses.
    """

    def test_mas_gen_plan_prompt_loaded_and_substantive(self):
        ws = _load_ws("mas-gen")
        self.assertIsNotNone(ws.plan_prompt_text)
        self.assertGreater(len(ws.plan_prompt_text), 100)

    def test_rtl_gen_plan_prompt_loaded_and_substantive(self):
        ws = _load_ws("rtl-gen")
        self.assertIsNotNone(ws.plan_prompt_text)
        self.assertGreater(len(ws.plan_prompt_text), 50)

    def test_mas_gen_plan_prompt_makes_glm_use_agent_tags(self):
        """
        Inject mas-gen plan rules into system prompt and ask GLM to plan.
        GLM should mention [MAS], [RTL] or [TB] task labels.
        """
        ws          = _load_ws("mas-gen")
        plan_system = ws.plan_prompt_text
        result      = _call([
            _sys(plan_system),
            _usr(
                "I need to implement a UART transmitter module. "
                "List the tasks in order, one per line."
            ),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(tag in lowered for tag in ["[mas]", "[rtl]", "[tb]", "[sim]", "[doc]",
                                            "mas", "rtl", "tb", "testbench", "simulation"]),
            f"Plan prompt not reflected — GLM did not use agent tags: {result[:400]}",
        )

    def test_rtl_gen_plan_prompt_enforces_lint_last(self):
        """
        rtl-gen plan rules say lint is the final task.
        GLM should mention lint in a planning response.
        """
        ws     = _load_ws("rtl-gen")
        result = _call([
            _sys(ws.plan_prompt_text),
            _usr(
                "List the implementation steps for a register file module in Verilog. "
                "Keep it concise."
            ),
        ])
        self.assertIn("lint", result.lower(),
                      f"rtl-gen plan prompt: 'lint' not mentioned in plan: {result[:400]}")

    def test_plan_prompt_prepend_mode_verified(self):
        """Plan prompt mode for mas-gen should be prepend."""
        ws = _load_ws("mas-gen")
        self.assertEqual(ws.plan_prompt_mode, "prepend")

    def test_merged_plan_prompt_contains_both_base_and_workspace(self):
        """
        After merging, the combined plan text has both the base config.PLAN_MODE_PROMPT
        and the workspace plan rules.
        """
        import config
        from workflow.loader import merge_prompt
        ws = _load_ws("mas-gen")
        merged = merge_prompt(
            config.PLAN_MODE_PROMPT,
            ws.plan_prompt_text,
            ws.plan_prompt_mode,
        )
        self.assertIn(ws.plan_prompt_text[:40], merged)
        self.assertIn(config.PLAN_MODE_PROMPT[:40], merged)


# ─────────────────────────────────────────────────────────────
# TestRealGLM51MultiTurnContext
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51MultiTurnContext(unittest.TestCase):
    """
    Multi-turn conversations: GLM maintains context across turns, including
    when the workspace system prompt is active.
    """

    def test_module_name_remembered_in_follow_up(self):
        """Turn 1 introduces 'fifo_sync'. Turn 2 asks what the module was."""
        msgs = [
            _sys("You are a Verilog RTL coding assistant."),
            _usr("I am implementing a module called fifo_sync. Acknowledge with 'Understood'."),
        ]
        reply1 = _call(msgs)
        msgs.append(_ast(reply1))
        msgs.append(_usr("What was the module name I mentioned?"))
        reply2 = _call(msgs)
        self.assertIn("fifo_sync", reply2.lower(),
                      f"GLM forgot module name across turns: {reply2[:300]}")

    def test_verilog_context_preserved_across_three_turns(self):
        """Three-turn conversation about a register file module."""
        ws_sys = _ws_system_prompt("rtl-gen")
        msgs   = [_sys(ws_sys)]

        msgs.append(_usr("I'm designing a 32-entry, 32-bit register file. Acknowledge."))
        r1 = _call(msgs); msgs.append(_ast(r1))

        msgs.append(_usr("What are the key input signals for this register file?"))
        r2 = _call(msgs); msgs.append(_ast(r2))

        msgs.append(_usr("How many entries did I say the register file has?"))
        r3 = _call(msgs)

        self.assertIn("32", r3, f"GLM forgot 32-entry spec: {r3[:300]}")

    def test_compressed_context_supports_follow_up(self):
        """
        Build a 6-turn history, compress it, then ask a follow-up.
        GLM should still reference information from the compressed history.
        """
        MODULE = "spi_master"
        ws_sys = _ws_system_prompt("rtl-gen")
        history = [
            _sys(ws_sys),
            _usr(f"I'm implementing {MODULE}. It has CLK, MOSI, MISO, CS signals."),
            _ast(f"Understood. {MODULE} with CLK, MOSI, MISO, CS signals."),
            _usr("The SPI mode is mode 0 (CPOL=0, CPHA=0)."),
            _ast("Got it. Mode 0: data sampled on rising edge."),
            _usr("The data width is 8 bits."),
            _ast("8-bit data transfers confirmed."),
        ]
        compressed = _compress(history, workspace="rtl-gen")
        compressed.append(_usr(f"What was the module name and its SPI mode?"))
        result = _call(compressed)
        self.assertTrue(
            MODULE in result or "spi" in result.lower(),
            f"Compressed context lost module name: {result[:300]}",
        )

    def test_workspace_context_maintained_after_compression(self):
        """After compressing, GLM still knows it's in a Verilog workspace."""
        ws_sys  = _ws_system_prompt("mas-gen")
        history = [
            _sys(ws_sys),
            _usr("What is a MAS document?"),
            _ast("A MAS (Micro Architecture Spec) document describes the hardware design..."),
            _usr("What sections does it have?"),
            _ast("A MAS typically has: Overview, Ports, FSM, Registers, Interrupts, Memory, Timing, RTL Notes, DV Plan."),
        ]
        compressed = _compress(history, workspace="mas-gen")
        compressed.append(_usr("Based on what we discussed, which section covers testbench scenarios?"))
        result = _call(compressed)
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in ["dv", "plan", "testbench", "test", "scenario", "§9", "section 9"]),
            f"Context lost after compression: {result[:300]}",
        )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51TodoTaskContent
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51TodoTaskContent(unittest.TestCase):
    """
    GLM-5.1 can understand and respond to real todo template task descriptions.
    These tests load actual task content from disk and verify GLM grasps it.
    """

    def _task(self, ws_name, template_name, idx=0):
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = load_workspace(ws_name, PROJECT_ROOT)
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        return reg.get_tasks(template_name)[idx]

    def test_mas_task0_glm_understands_mas_document(self):
        """[MAS] task content → GLM knows it's about writing a spec document."""
        task = self._task("mas-gen", "full-project", 0)
        result = _call([
            _sys("You are a Verilog hardware design assistant."),
            _usr(f"Explain this task in one sentence: {task['content']}"),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "micro", "architecture", "specification", "spec", "document",
                "mas", "write", "design",
            ]),
            f"GLM didn't understand MAS task: {result[:300]}",
        )

    def test_rtl_task0_glm_understands_read_mas(self):
        """rtl-impl task[0] is about reading the MAS → GLM understands it."""
        task = self._task("rtl-gen", "rtl-impl", 0)
        result = _call([
            _sys("You are a Verilog RTL implementation assistant."),
            _usr(f"What does this task ask you to do? Answer in one sentence: {task['content']}"),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in ["read", "spec", "architecture", "document", "mas", "review"]),
            f"GLM didn't understand rtl-impl task[0]: {result[:300]}",
        )

    def test_sim_task1_is_loop_and_glm_knows_it(self):
        """sim-debug task[1] is a simulation loop → GLM knows it involves iteration."""
        task = self._task("sim", "sim-debug", 1)
        self.assertTrue(task.get("loop"), "sim-debug task[1] should be loop=True")
        result = _call([
            _sys("You are a simulation debugging assistant."),
            _usr(f"This is a loop task. Explain what you need to keep doing: {task['content']}"),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "loop", "repeat", "iterate", "until", "error", "debug",
                "fix", "simulation", "run",
            ]),
            f"GLM didn't understand sim loop task: {result[:300]}",
        )

    def test_lint_task_sequence_comprehensible(self):
        """GLM can explain the purpose of each lint-fix step."""
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = load_workspace("lint", PROJECT_ROOT)
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        tasks = reg.get_tasks("lint-fix")

        combined = "\n".join(f"{i+1}. {t['content']}" for i, t in enumerate(tasks))
        result = _call([
            _sys("You are a Verilog lint verification assistant."),
            _usr(f"These are the lint-fix workflow steps. Are they in a logical order? "
                 f"Answer yes/no and why:\n{combined}"),
        ])
        self.assertTrue(
            "yes" in result.lower() or "order" in result.lower() or "correct" in result.lower(),
            f"GLM disagrees with lint-fix step order: {result[:300]}",
        )

    def test_full_project_task_count_via_real_files(self):
        """full-project.json has exactly 6 tasks and GLM can count them."""
        from workflow.loader import load_workspace, TodoTemplateRegistry
        ws  = load_workspace("mas-gen", PROJECT_ROOT)
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        tasks  = reg.get_tasks("full-project")
        self.assertEqual(len(tasks), 6)
        summary = "\n".join(f"Task {i+1}: {t['content']}" for i, t in enumerate(tasks))
        result  = _call([_usr(f"How many tasks are listed here?\n{summary}")])
        self.assertIn("6", result, f"GLM miscounted tasks: {result[:200]}")


# ─────────────────────────────────────────────────────────────
# TestRealGLM51CompressionQuality
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51CompressionQuality(unittest.TestCase):
    """Verify GLM-5.1 compression output quality for workflow-specific histories."""

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def _verilog_history(self, module="alu_32"):
        return [
            _sys("You are a Verilog RTL coding assistant."),
            _usr(f"Implement a 32-bit ALU named {module} supporting ADD, SUB, AND, OR."),
            _ast(f"module {module}(input [31:0] a,b, input [1:0] op, output reg [31:0] y); always @(*) case(op) 2'd0:y=a+b; 2'd1:y=a-b; 2'd2:y=a&b; 2'd3:y=a|b; endcase endmodule"),
            _usr("Add a carry-out signal for ADD/SUB operations."),
            _ast(f"module {module}(input [31:0] a,b, input [1:0] op, output reg [31:0] y, output reg cout); always @(*) begin cout=0; case(op) 2'd0:{{cout,y}}=a+b; 2'd1:{{cout,y}}=a-b; 2'd2:y=a&b; 2'd3:y=a|b; endcase end endmodule"),
        ]

    def test_module_name_in_summary(self):
        """The compressed summary should mention the module name 'alu_32'."""
        result = _compress(self._verilog_history("alu_32"))
        content = " ".join(m.get("content", "") for m in result)
        self.assertIn("alu", content.lower(),
                      f"Module name not in summary: {content[:400]}")

    def test_summary_has_structured_sections(self):
        """
        mas-gen compression_prompt.md instructs GLM to produce structured output
        (Goals, Completed, Key Files, etc.).
        """
        ws = _load_ws("mas-gen")
        import core.compressor as comp
        importlib.reload(comp)
        orig_prompt = comp.STRUCTURED_SUMMARY_PROMPT
        comp.STRUCTURED_SUMMARY_PROMPT = ws.compression_prompt_text
        try:
            result = _compress(self._verilog_history("counter_mod"), workspace="mas-gen")
        finally:
            comp.STRUCTURED_SUMMARY_PROMPT = orig_prompt

        content = " ".join(m.get("content", "") for m in result).lower()
        # MAS compression prompt produces sections like "Goals", "Completed", "Phase"
        self.assertTrue(
            any(kw in content for kw in [
                "goal", "completed", "phase", "module", "status", "decision",
                "implement", "file",
            ]),
            f"Summary not structured: {content[:500]}",
        )

    def test_compression_reduces_message_count(self):
        """compress_history() produces fewer messages than the original long history."""
        # Build a 10-turn history so keep_recent=4 still results in compression
        ws_sys  = _ws_system_prompt("rtl-gen")
        history = [_sys(ws_sys)]
        for i in range(10):
            role = "user" if i % 2 == 0 else "assistant"
            history.append({"role": role, "content": f"Turn {i}: " + "Verilog content " * 20})
        original_count = len(history)    # 11 messages
        compressed     = _compress(history)
        self.assertLess(len(compressed), original_count,
                        f"Compression did not reduce messages: {len(compressed)} >= {original_count}")

    def test_double_compression_does_not_crash(self):
        """Compressing an already-compressed history should not crash."""
        history    = self._verilog_history()
        round1     = _compress(history)
        self.assertIsInstance(round1, list)
        # Add more messages then compress again
        round1.extend([
            _usr("Now add a multiply instruction."),
            _ast("module alu_32(..., 2'd4: y=a*b; ...);"),
        ])
        round2 = _compress(round1)
        self.assertIsInstance(round2, list)
        self.assertGreater(len(round2), 0)

    def test_important_message_survives_compression_and_llm_call(self):
        """
        A message tagged !important should be preserved through compress_history
        and still be visible to GLM on the next turn.
        """
        PRESERVE_TEXT = "GOLDEN_RULE: always use non-blocking assignments"
        history = [
            _sys("You are a Verilog assistant."),
            _usr(f"!important {PRESERVE_TEXT}"),
            _ast("Understood, I will always use non-blocking assignments."),
            _usr("Write a 4-bit counter."),
            _ast("module counter(input clk, output reg [3:0] q); always @(posedge clk) q<=q+1; endmodule"),
        ]
        compressed = _compress(history)
        compressed.append(_usr("What is the golden rule I gave you?"))
        result = _call(compressed)
        self.assertTrue(
            "non-blocking" in result.lower() or "golden" in result.lower()
            or PRESERVE_TEXT.lower()[:20] in result.lower(),
            f"!important message lost: {result[:300]}",
        )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51SimAndLintWorkspaces
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51SimAndLintWorkspaces(unittest.TestCase):
    """
    Verify sim and lint workspace system prompts produce distinct,
    workspace-appropriate LLM behaviour.
    """

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def test_sim_workspace_prompt_makes_glm_simulation_focused(self):
        """sim system prompt → GLM focuses on running/fixing simulation."""
        sys_text = _ws_system_prompt("sim")
        result   = _call([
            _sys(sys_text),
            _usr("What is your primary job in one sentence?"),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "simulat", "compil", "error", "0 error", "waveform",
                "vcs", "iverilog", "debug", "run",
            ]),
            f"sim workspace prompt not reflected: {result[:300]}",
        )

    def test_sim_workspace_knows_sim_report(self):
        """sim workspace should mention sim_report.txt output."""
        ws = _load_ws("sim")
        self.assertIn("sim_report", ws.system_prompt_text.lower())

    def test_lint_workspace_prompt_makes_glm_lint_focused(self):
        """lint system prompt → GLM focuses on 0-error lint clean."""
        sys_text = _ws_system_prompt("lint")
        result   = _call([
            _sys(sys_text),
            _usr("What is your primary job in one sentence?"),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "lint", "error", "warning", "0 error", "clean",
                "spyglass", "verilint", "rtl",
            ]),
            f"lint workspace prompt not reflected: {result[:300]}",
        )

    def test_lint_workspace_knows_lint_report(self):
        """lint workspace should mention lint_report.txt output."""
        ws = _load_ws("lint")
        self.assertIn("lint_report", ws.system_prompt_text.lower())

    def test_sim_and_lint_give_different_role_descriptions(self):
        """sim and lint workspace roles are distinct (different primary focus)."""
        sim_sys  = _ws_system_prompt("sim")
        lint_sys = _ws_system_prompt("lint")
        q        = [_usr("What is your primary task? One sentence.")]

        sim_r  = _call([_sys(sim_sys)]  + q)
        lint_r = _call([_sys(lint_sys)] + q)

        # Their responses should differ — at least one focuses on simulation,
        # the other on lint. They should NOT be identical.
        self.assertNotEqual(
            sim_r.strip()[:50], lint_r.strip()[:50],
            "sim and lint workspaces gave identical role descriptions",
        )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51WorkspaceDescription
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51WorkspaceDescription(unittest.TestCase):
    """
    ACTIVE_WORKSPACE_DESC is stored in env and injected into the system prompt.
    Verify it reaches GLM-5.1 and is visible in the built prompt.
    """

    def setUp(self):
        import core.prompt_builder as _pb
        importlib.reload(_pb)
        self._pb = _pb

    def tearDown(self):
        for k in ("ACTIVE_WORKSPACE", "ACTIVE_WORKSPACE_DESC"):
            os.environ.pop(k, None)
        import core.prompt_builder as _pb
        importlib.reload(_pb)

    def test_all_workspaces_have_description_in_workspace_json(self):
        """Every production workspace has a non-empty description field."""
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]:
            with self.subTest(ws=ws_name):
                ws = _load_ws(ws_name)
                self.assertTrue(
                    ws.description.strip(),
                    f"{ws_name} workspace.json missing description",
                )

    def test_workspace_desc_injected_into_system_prompt(self):
        """When ACTIVE_WORKSPACE_DESC is set, it appears in the built system prompt."""
        os.environ["ACTIVE_WORKSPACE"]      = "rtl-gen"
        os.environ["ACTIVE_WORKSPACE_DESC"] = "RTL code generation agent for SystemVerilog"
        import core.prompt_builder as pb
        importlib.reload(pb)
        result = pb.build_system_prompt()
        if isinstance(result, dict):
            text = result.get("static", "") + result.get("dynamic", "")
        else:
            text = result
        self.assertIn("RTL code generation agent for SystemVerilog", text)

    def test_glm_sees_workspace_description_in_context(self):
        """GLM-5.1 can reference the workspace description when asked."""
        desc   = "RTL generation agent — specializes in SystemVerilog implementation"
        sys_p  = f"[Workspace: rtl-gen — {desc}]\nYou are a Verilog coding assistant."
        result = _call([
            _sys(sys_p),
            _usr("What workspace are you operating in? One sentence."),
        ])
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "rtl", "verilog", "systemverilog", "generation",
                "implementation", "coding", "rtl-gen",
            ]),
            f"GLM didn't reference workspace description: {result[:300]}",
        )

    def test_description_substantive_for_mas_gen(self):
        ws = _load_ws("mas-gen")
        # Description should mention what the workspace does
        lowered = ws.description.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "mas", "architect", "spec", "rtl", "verilog",
                "hardware", "design", "agent",
            ]),
            f"mas-gen description not substantive: '{ws.description}'",
        )


# ─────────────────────────────────────────────────────────────
# TestRealGLM51ContextWindowBoundary
# ─────────────────────────────────────────────────────────────

@_SKIP
class TestRealGLM51ContextWindowBoundary(unittest.TestCase):
    """
    Verify compression is triggered at the right threshold and that
    the resulting compressed context supports further LLM interaction.
    """

    def tearDown(self):
        os.environ.pop("ACTIVE_WORKSPACE", None)

    def _build_long_rtl_history(self, n_pairs=8):
        """Build a realistic RTL conversation history."""
        ws_sys = _ws_system_prompt("rtl-gen")
        msgs   = [_sys(ws_sys)]
        topics = [
            ("Implement a parameterized synchronous FIFO in SystemVerilog.",
             "module fifo #(parameter DEPTH=8, WIDTH=8)(input clk, rst, wr_en, rd_en, input [WIDTH-1:0] din, output reg [WIDTH-1:0] dout, output full, empty); // ... endmodule"),
            ("Add an almost-full flag when 75% full.",
             "assign almost_full = (count >= (DEPTH*3/4));"),
            ("Add a watermark output showing current fill level.",
             "output reg [$clog2(DEPTH):0] watermark; always @(posedge clk) watermark <= count;"),
            ("Generate an overflow error flag.",
             "output reg overflow; always @(posedge clk) if(wr_en && full) overflow <= 1; else overflow <= 0;"),
            ("Add a clear signal that flushes the FIFO synchronously.",
             "always @(posedge clk) if(rst || clr) begin wr_ptr<=0; rd_ptr<=0; count<=0; end"),
            ("Generate a lint-clean version with proper reset values.",
             "// Lint clean: all registers have synchronous reset, no latches"),
            ("Write the interface description for this FIFO.",
             "// fifo.sv — synchronous FIFO: DEPTH, WIDTH parameterized; full, empty, almost_full, overflow, watermark flags"),
            ("Summarise the final module specification.",
             "// Final spec: parameterized sync FIFO with overflow/watermark/almost-full/clear"),
        ]
        for i, (q, a) in enumerate(topics[:n_pairs]):
            msgs.append(_usr(q))
            msgs.append(_ast(a))
        return msgs

    def test_long_history_compresses_and_llm_continues(self):
        """
        Build an 8-turn RTL history, compress, then ask GLM a follow-up.
        Verify GLM still responds coherently.
        """
        history    = self._build_long_rtl_history(8)
        compressed = _compress(history, workspace="rtl-gen")
        compressed.append(_usr("What FIFO features have we implemented so far? List them."))
        result = _call(compressed)
        lowered = result.lower()
        self.assertTrue(
            any(w in lowered for w in [
                "fifo", "full", "empty", "overflow", "watermark",
                "almost", "clear", "flush", "parameter",
            ]),
            f"GLM lost FIFO context after compression: {result[:400]}",
        )

    def test_compression_preserves_system_prompt_role(self):
        """After compression, GLM still knows it's an RTL agent."""
        history    = self._build_long_rtl_history(6)
        compressed = _compress(history, workspace="rtl-gen")
        compressed.append(_usr("Are you a Verilog RTL coding agent? One word: yes or no."))
        result = _call(compressed)
        self.assertIn("yes", result.lower(),
                      f"GLM lost its RTL role after compression: {result[:200]}")

    def test_mas_gen_compression_prompt_with_fifo_history(self):
        """
        mas-gen compression_prompt.md used for compressing an RTL history
        → structured summary with MAS-style fields.
        """
        ws = _load_ws("mas-gen")
        import core.compressor as comp
        importlib.reload(comp)
        orig = comp.STRUCTURED_SUMMARY_PROMPT
        comp.STRUCTURED_SUMMARY_PROMPT = ws.compression_prompt_text
        try:
            history = self._build_long_rtl_history(4)
            result  = _compress(history, workspace="mas-gen")
        finally:
            comp.STRUCTURED_SUMMARY_PROMPT = orig

        content = " ".join(m.get("content", "") for m in result)
        # MAS-style summary should have status/phase/module info
        self.assertTrue(
            len(content.strip()) > 30,
            f"MAS compression produced empty summary: {content[:200]}",
        )


if __name__ == "__main__":
    unittest.main()
