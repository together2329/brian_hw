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
    content: str = ""  # Markdown content from SKILL.md
    source_path: Optional[Path] = None

    def format_for_prompt(self) -> str:
        """
        Format skill content for LLM prompt injection

        Returns:
            Formatted string ready for system prompt
        """
        parts = [
            f"## 🔧 Skill: {self.name}",
            f"**Description**: {self.description}",
            "",
            self.content
        ]
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
