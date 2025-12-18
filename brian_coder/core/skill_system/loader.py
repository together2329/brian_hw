"""
SkillLoader - Loads skills from SKILL.md files

Pattern follows core/tool_descriptions/DescriptionLoader
"""

from pathlib import Path
from typing import Optional, Dict
import re

try:
    import yaml
except ImportError:
    yaml = None  # Fallback: parse frontmatter manually

from . import Skill, SkillActivation


class SkillLoader:
    """
    Load skills from SKILL.md files

    Supports:
    - User skills (~/.brian_coder/skills/)
    - Built-in skills (brian_coder/skills/)
    - Caching for performance
    """

    def __init__(self, user_skills_dir: str = None, builtin_skills_dir: Path = None):
        """
        Initialize SkillLoader

        Args:
            user_skills_dir: Path to user skills directory (default: ~/.brian_coder/skills)
            builtin_skills_dir: Path to built-in skills directory (auto-detect if None)
        """
        # User skills directory
        if user_skills_dir:
            self.user_dir = Path(user_skills_dir).expanduser()
        else:
            self.user_dir = Path.home() / ".brian_coder" / "skills"

        # Built-in skills directory (auto-detect)
        if builtin_skills_dir:
            self.builtin_dir = Path(builtin_skills_dir)
        else:
            self.builtin_dir = self._detect_builtin_dir()

        # Cache for loaded skills
        self._cache: Dict[str, Skill] = {}

    def _detect_builtin_dir(self) -> Path:
        """Auto-detect built-in skills directory"""
        # Find brian_coder/skills directory
        current_file = Path(__file__)

        # Go up to brian_coder/core/skill_system → brian_coder/core → brian_coder
        brian_coder_dir = current_file.parent.parent.parent

        # Check if brian_coder/skills exists
        builtin_dir = brian_coder_dir / "skills"

        return builtin_dir if builtin_dir.exists() else None

    def load_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Load skill from user or builtin directory

        Args:
            skill_name: Name of the skill (e.g., "verilog-expert")

        Returns:
            Skill object if found, None otherwise
        """
        # Check cache first
        if skill_name in self._cache:
            return self._cache[skill_name]

        # Try user directory first (higher priority)
        user_path = self.user_dir / skill_name / "SKILL.md"
        if user_path.exists():
            skill = self._parse_skill_file(user_path)
            if skill:
                self._cache[skill_name] = skill
                return skill

        # Try builtin directory
        if self.builtin_dir:
            builtin_path = self.builtin_dir / skill_name / "SKILL.md"
            if builtin_path.exists():
                skill = self._parse_skill_file(builtin_path)
                if skill:
                    self._cache[skill_name] = skill
                    return skill

        return None

    def _parse_skill_file(self, path: Path) -> Optional[Skill]:
        """
        Parse SKILL.md file (YAML frontmatter + Markdown body)

        Format:
        ---
        name: skill-name
        description: Skill description
        priority: 90
        activation:
          keywords: [keyword1, keyword2]
          file_patterns: ["*.py", "*.md"]
          auto_detect: true
        requires_tools: [tool1, tool2]
        ---

        # Skill Content
        Markdown content here...

        Args:
            path: Path to SKILL.md file

        Returns:
            Skill object if parsing succeeds, None otherwise
        """
        try:
            content = path.read_text(encoding='utf-8')

            # Check for YAML frontmatter
            if content.startswith('---'):
                # Split frontmatter and body
                parts = content.split('---', 2)

                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    body = parts[2].strip()
                else:
                    # No valid frontmatter
                    frontmatter_text = ""
                    body = content

                # Parse frontmatter
                if yaml and frontmatter_text:
                    frontmatter = yaml.safe_load(frontmatter_text)
                elif frontmatter_text:
                    # Fallback: simple key-value parsing
                    frontmatter = self._parse_simple_yaml(frontmatter_text)
                else:
                    frontmatter = {}
            else:
                # No frontmatter
                frontmatter = {}
                body = content

            # Extract activation info
            activation_data = frontmatter.get('activation', {})
            activation = SkillActivation(
                keywords=activation_data.get('keywords', []),
                file_patterns=activation_data.get('file_patterns', []),
                auto_detect=activation_data.get('auto_detect', True)
            )

            # Create Skill object
            skill = Skill(
                name=frontmatter.get('name', path.parent.name),
                description=frontmatter.get('description', ''),
                version=frontmatter.get('version', '1.0.0'),
                priority=frontmatter.get('priority', 50),
                activation=activation,
                requires_tools=frontmatter.get('requires_tools', []),
                related_skills=frontmatter.get('related_skills', []),
                content=body,
                source_path=path
            )

            return skill

        except Exception as e:
            print(f"[SkillLoader] Error parsing {path}: {e}")
            return None

    def _parse_simple_yaml(self, text: str) -> dict:
        """Simple YAML parser fallback (when PyYAML not available)"""
        result = {}
        current_key = None

        for line in text.split('\n'):
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            # Key-value pair
            if ':' in line and not line.startswith('-'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Parse value
                if value.startswith('[') and value.endswith(']'):
                    # List
                    items = value[1:-1].split(',')
                    result[key] = [item.strip().strip('"').strip("'") for item in items]
                elif value.lower() in ('true', 'false'):
                    # Boolean
                    result[key] = value.lower() == 'true'
                elif value.isdigit():
                    # Integer
                    result[key] = int(value)
                else:
                    # String
                    result[key] = value.strip('"').strip("'")

                current_key = key

            # List item continuation
            elif line.startswith('-') and current_key:
                item = line[1:].strip().strip('"').strip("'")
                if current_key in result:
                    if not isinstance(result[current_key], list):
                        result[current_key] = [result[current_key]]
                    result[current_key].append(item)

        return result

    def list_available_skills(self) -> list:
        """
        List all available skill names

        Returns:
            List of skill names (user skills first, then builtin)
        """
        skills = []

        # User skills
        if self.user_dir.exists():
            for skill_dir in self.user_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    skills.append(skill_dir.name)

        # Builtin skills
        if self.builtin_dir and self.builtin_dir.exists():
            for skill_dir in self.builtin_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                    # Add only if not already in user skills
                    if skill_dir.name not in skills:
                        skills.append(skill_dir.name)

        return skills

    def clear_cache(self):
        """Clear skill cache"""
        self._cache.clear()
