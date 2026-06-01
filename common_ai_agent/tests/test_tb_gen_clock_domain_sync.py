from __future__ import annotations

import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
SYSTEM_PROMPT = REPO / "workflow" / "tb-gen" / "system_prompt.md"
PLAN_PROMPT = REPO / "workflow" / "tb-gen" / "plan_prompt.md"
RULES = REPO / "workflow" / "tb-gen" / "rules" / "tb-gen-rules.md"


def _module_string_constant(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == name:
                return node.value.value
    raise AssertionError(f"{name} string constant not found in {path}")


def test_goal_scoreboard_template_drives_inputs_on_rising_clock_edge() -> None:
    # Given: the production cocotb goal-scoreboard template.
    template = _module_string_constant(SCRIPT, "TEST_PY")

    # When: the generated TB imports and uses cocotb clock triggers.
    trigger_imports = [
        line for line in template.splitlines() if line.startswith("from cocotb.triggers import")
    ]

    # Then: default generated input drives are aligned to the active rising clock edge.
    assert "FallingEdge" not in template
    assert trigger_imports == ["from cocotb.triggers import ClockCycles, ReadOnly, RisingEdge"]


def test_tb_gen_rules_require_clock_domain_synchronization() -> None:
    # Given: the prompt/rule files that control planning and TB generation.
    docs = [SYSTEM_PROMPT, PLAN_PROMPT, RULES]

    # When: the files are checked for the clock-domain synchronization policy.
    text_by_doc = {path: path.read_text(encoding="utf-8") for path in docs}

    # Then: each entry point states the same rule in English.
    for path, text in text_by_doc.items():
        assert "Clock-Domain Synchronization Rule" in text, path
        assert "synchronized to the signal's declared clock domain" in text, path
