from __future__ import annotations

from core.skill_system.loader import SkillLoader


def test_external_db_skill_requires_dedicated_query_tool() -> None:
    skill = SkillLoader().load_skill("external-db")

    assert skill is not None
    assert "external_db_query" in skill.requires_tools


def test_external_db_skill_prompt_uses_dedicated_query_tool() -> None:
    skill = SkillLoader().load_skill("external-db")

    assert skill is not None
    prompt = skill.format_for_prompt()
    assert "external_db_query(" in prompt
    assert "wiki_query(ip=\"external-db\"" in prompt
