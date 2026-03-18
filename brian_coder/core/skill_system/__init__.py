"""
Skill System for Brian Coder

Claude Code-style skill system with:
- Plugin-based skill loading (SKILL.md files)
- Auto-detection based on keywords and file patterns
- Dynamic prompt injection

Author: Brian
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class SkillActivation:
    """Skill activation configuration"""
    keywords: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=list)
    auto_detect: bool = True


@dataclass
class Skill:
    """Skill definition loaded from SKILL.md"""
    name: str
    description: str
    version: str = "1.0.0"
    priority: int = 50  # Higher = activated first (0-100)
    activation: SkillActivation = field(default_factory=SkillActivation)
    requires_tools: List[str] = field(default_factory=list)
    related_skills: List[str] = field(default_factory=list)
    content: str = ""  # Hub content only (spoke files excluded)
    source_path: Optional[Path] = None
    # Claude Code compatible fields
    disable_model_invocation: bool = False  # True = manual /skill only
    user_invocable: bool = True             # False = hidden from / menu
    allowed_tools: List[str] = field(default_factory=list)
    model_override: Optional[str] = None
    argument_hint: Optional[str] = None
    skill_dir: Optional[Path] = None        # ${CLAUDE_SKILL_DIR}
    spoke_files: List[str] = field(default_factory=list)

    def format_for_prompt(self) -> str:
        """
        Format skill for LLM prompt injection.
        Hub only — spoke files listed as references for on-demand read.
        """
        parts = [f"## Skill: {self.name}", "", self.content]
        if self.spoke_files and self.skill_dir:
            parts.append(f"\n> Reference files in `{self.skill_dir}/`: {', '.join(self.spoke_files)}")
        return "\n".join(parts)


# Singleton accessors (lazy import to avoid circular dependency)
_registry_instance = None
_activator_instance = None


def get_skill_registry():
    """Get singleton SkillRegistry instance"""
    global _registry_instance
    if _registry_instance is None:
        from .registry import SkillRegistry
        _registry_instance = SkillRegistry()
    return _registry_instance


def get_skill_activator():
    """Get singleton SkillActivator instance"""
    global _activator_instance
    if _activator_instance is None:
        from .activator import SkillActivator
        _activator_instance = SkillActivator()
    return _activator_instance


__all__ = [
    "Skill",
    "SkillActivation",
    "get_skill_registry",
    "get_skill_activator",
]
