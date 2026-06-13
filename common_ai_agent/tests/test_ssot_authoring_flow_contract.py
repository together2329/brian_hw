from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def test_default_ssot_authoring_flow_uses_llm_edits_and_validator_checks_only():
    """Default SSOT generation must not ask a broad schema-repair script to
    author semantics before validation.

    `/repair-ssot` can remain as an explicit rescue command, but the default
    worker/todo/template path should be: LLM writes YAML, validator reports
    blockers, LLM edits YAML again.
    """
    files = {
        "workflow/ssot-gen/system_prompt.md": _read("workflow/ssot-gen/system_prompt.md"),
        "workflow/ssot-gen/system_prompt_pipeline.md": _read(
            "workflow/ssot-gen/system_prompt_pipeline.md"
        ),
        "workflow/ssot-gen/todo_templates/atlas-pipeline-ssot.json": _read(
            "workflow/ssot-gen/todo_templates/atlas-pipeline-ssot.json"
        ),
        "workflow/ssot-gen/rules/ssot-template.yaml": _read(
            "workflow/ssot-gen/rules/ssot-template.yaml"
        ),
        "workflow/ssot-gen/skills/to-ssot/SKILL.md": _read(
            "workflow/ssot-gen/skills/to-ssot/SKILL.md"
        ),
        "src/atlas_ui.py": _read("src/atlas_ui.py"),
        "src/atlas_api_jobs.py": _read("src/atlas_api_jobs.py"),
        "workflow/ssot-gen/scripts/verify_ssot.py": _read(
            "workflow/ssot-gen/scripts/verify_ssot.py"
        ),
    }
    forbidden = [
        re.compile(r"repair_ssot_schema\.py[^\n]*&&[^\n]*verify_ssot\.py"),
        re.compile(r"first\s+run\s+`?python3\s+[^`\n]*repair_ssot_schema\.py", re.I),
        re.compile(r"Run\s+repair_ssot_schema\.py\s+and\s+verify_ssot\.py", re.I),
        re.compile(r"repair\s+and\s+validate\s+on\s+disk", re.I),
        re.compile(r"repair,\s*validate,\s*handoff", re.I),
    ]
    violations: list[str] = []
    for relpath, text in files.items():
        for pattern in forbidden:
            if pattern.search(text):
                violations.append(f"{relpath}: {pattern.pattern}")
    assert violations == []
