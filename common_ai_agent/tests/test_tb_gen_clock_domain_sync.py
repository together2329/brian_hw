from __future__ import annotations

import ast
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
SYSTEM_PROMPT = REPO / "workflow" / "tb-gen" / "system_prompt.md"
PLAN_PROMPT = REPO / "workflow" / "tb-gen" / "plan_prompt.md"
RULES = REPO / "workflow" / "tb-gen" / "rules" / "tb-gen-rules.md"
ORCHESTRATION_RULES = REPO / "workflow" / "tb-gen" / "rules" / "ssot-tb-orchestration.md"


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


def _markdown_section(path: Path, heading: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip().endswith(heading))
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    section: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.lstrip("#")
        if line.startswith("#") and stripped.startswith(" ") and len(line) - len(stripped) <= level:
            break
        section.append(line)
    return "\n".join(section)


def test_goal_scoreboard_template_waits_on_clock_or_timer() -> None:
    # Given: the production cocotb goal-scoreboard template.
    template = _module_string_constant(SCRIPT, "TEST_PY")

    # When: the generated TB imports and uses cocotb clock triggers.
    trigger_imports = [
        line for line in template.splitlines() if line.startswith("from cocotb.triggers import")
    ]

    # Then: clocked DUTs use RisingEdge and clockless combinational DUTs use
    # Timer-based settling through the same wait helper.
    assert "FallingEdge" not in template
    assert trigger_imports == ["from cocotb.triggers import ReadOnly, RisingEdge, Timer"]
    assert "async def _wait_cycle" in template
    assert "await Timer(1, units=\"ns\")" in template


def test_tb_gen_rules_require_clock_domain_synchronization() -> None:
    # Given: the prompt/rule files that control planning and TB generation.
    docs = [SYSTEM_PROMPT, PLAN_PROMPT, RULES]

    # When: the files are checked for the clock-domain synchronization policy.
    text_by_doc = {path: path.read_text(encoding="utf-8") for path in docs}

    # Then: each entry point states the same rule in English.
    for path, text in text_by_doc.items():
        assert "Clock-Domain Synchronization Rule" in text, path
        assert "synchronized to the signal's declared clock domain" in text, path


def test_tb_gen_rules_require_layered_transaction_structure_for_complex_ips() -> None:
    # Given: the prompt/rule sections that control complex SSOT TB structure.
    sections = {
        SYSTEM_PROMPT: _markdown_section(SYSTEM_PROMPT, "Generic SSOT Verification Contract"),
        PLAN_PROMPT: _markdown_section(PLAN_PROMPT, "SSOT-Aware Task Decomposition"),
        RULES: _markdown_section(RULES, "Layered Transaction TB Rule"),
        ORCHESTRATION_RULES: _markdown_section(ORCHESTRATION_RULES, "Layered Transaction TB Rule"),
    }

    # When: each section is parsed for the required layered TB concepts.
    required_terms = [
        "transaction",
        "driver",
        "monitor",
        "latency-aware",
        "scoreboard",
        "cycle_model",
        "ssot tbd report",
    ]

    # Then: every entry point carries the same structural rule set.
    for path, section in sections.items():
        normalized = section.lower()
        for term in required_terms:
            assert term in normalized, (path, term)
