"""
SkillRegistry - Manages active skills

Pattern follows singleton pattern like DescriptionLoader
"""

from typing import Dict, List, Optional
from .loader import SkillLoader
from . import Skill


class SkillRegistry:
    """
    Singleton registry for skills

    Responsibilities:
    - Load skills via SkillLoader
    - Track which skills are currently active
    - Provide skill lookup API
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Create loader
        self._loader = SkillLoader()

        # Loaded skills (name → Skill)
        self._skills: Dict[str, Skill] = {}

        # Auto-load all available skills
        self._auto_load_skills()

        self._initialized = True

    def _auto_load_skills(self):
        """
        Auto-load all available skills from user and builtin directories

        This is called once during initialization to populate the registry
        """
        available_skills = self._loader.list_available_skills()

        for skill_name in available_skills:
            skill = self._loader.load_skill(skill_name)
            if skill:
                self._skills[skill_name] = skill

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Get skill by name

        Args:
            skill_name: Name of the skill

        Returns:
            Skill object if found, None otherwise
        """
        # Check if already loaded
        if skill_name in self._skills:
            return self._skills[skill_name]

        # Try to load it
        skill = self._loader.load_skill(skill_name)
        if skill:
            self._skills[skill_name] = skill
            return skill

        return None

    def list_skills(self) -> List[str]:
        """
        List all loaded skill names

        Returns:
            List of skill names
        """
        return list(self._skills.keys())

    def get_all_skills(self) -> List[Skill]:
        """
        Get all loaded skills

        Returns:
            List of Skill objects
        """
        return list(self._skills.values())

    def get_skills_by_priority(self, descending: bool = True) -> List[Skill]:
        """
        Get skills sorted by priority

        Args:
            descending: If True, highest priority first

        Returns:
            List of Skill objects sorted by priority
        """
        return sorted(
            self._skills.values(),
            key=lambda s: s.priority,
            reverse=descending
        )

    def reload_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Reload a skill from disk (useful for development)

        Args:
            skill_name: Name of the skill to reload

        Returns:
            Reloaded Skill object if successful, None otherwise
        """
        # Clear from cache
        if skill_name in self._skills:
            del self._skills[skill_name]

        self._loader.clear_cache()

        # Reload
        skill = self._loader.load_skill(skill_name)
        if skill:
            self._skills[skill_name] = skill
            return skill

        return None

    def reload_all_skills(self):
        """Reload all skills from disk"""
        self._skills.clear()
        self._loader.clear_cache()
        self._auto_load_skills()

    def register_skill(self, skill: Skill):
        """
        Manually register a skill (for testing or dynamic skills)

        Args:
            skill: Skill object to register
        """
        self._skills[skill.name] = skill

    def unregister_skill(self, skill_name: str):
        """
        Unregister a skill

        Args:
            skill_name: Name of the skill to unregister
        """
        if skill_name in self._skills:
            del self._skills[skill_name]
