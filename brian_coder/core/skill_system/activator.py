"""
SkillActivator - Detects which skills should be active

Based on:
- Keyword matching in user messages
- File pattern matching
- Tool requirements
"""

from typing import List, Set, Optional
import re
from fnmatch import fnmatch
from . import Skill


class SkillActivator:
    """
    Automatically detect which skills should be activated

    Activation scoring:
    - Keyword matching (40%)
    - Tool requirements (30%)
    - File pattern matching (30%)
    """

    def __init__(self):
        """Initialize SkillActivator"""
        pass

    def detect_skills(
        self,
        context: str,
        allowed_tools: Optional[Set[str]] = None,
        threshold: float = 0.7
    ) -> List[str]:
        """
        Detect which skills should be activated based on context

        Args:
            context: Recent user messages (concatenated)
            allowed_tools: Set of allowed tool names (for sub-agents)
            threshold: Minimum activation score (0.0-1.0)

        Returns:
            List of skill names that should be activated, sorted by priority
        """
        from . import get_skill_registry

        registry = get_skill_registry()
        all_skills = registry.get_all_skills()

        # Score each skill
        scored_skills = []

        for skill in all_skills:
            if not skill.activation.auto_detect:
                # Skip skills with auto_detect=false
                continue

            score = self._calculate_activation_score(skill, context, allowed_tools)

            if score >= threshold:
                scored_skills.append((score, skill.priority, skill.name))

        # Sort by: score (descending), then priority (descending), then name
        scored_skills.sort(key=lambda x: (-x[0], -x[1], x[2]))

        # Return skill names
        return [skill_name for score, priority, skill_name in scored_skills]

    def _calculate_activation_score(
        self,
        skill: Skill,
        context: str,
        allowed_tools: Optional[Set[str]] = None
    ) -> float:
        """
        Calculate activation score for a skill (0.0-1.0)

        Scoring:
        - Keyword matching: 50%
        - Tool requirements: 20%
        - File pattern matching: 30%

        Args:
            skill: Skill to evaluate
            context: User message context
            allowed_tools: Set of allowed tool names

        Returns:
            Activation score (0.0-1.0)
        """
        score = 0.0

        # 1. Keyword matching (50% - primary signal)
        keyword_score = self._keyword_match_score(skill.activation.keywords, context)
        score += keyword_score * 0.5

        # 2. Tool requirements (20%)
        if allowed_tools and skill.requires_tools:
            required_tools = set(skill.requires_tools)
            overlap = len(required_tools & allowed_tools)
            tool_score = overlap / len(required_tools) if required_tools else 0.0
            score += tool_score * 0.2
        else:
            # Give partial credit for keyword match
            if keyword_score > 0:
                score += 0.1

        # 3. File pattern matching (30%)
        file_score = self._file_pattern_match_score(skill.activation.file_patterns, context)
        score += file_score * 0.3

        # CRITICAL: Require at least one signal (keyword OR file pattern OR tool)
        # This prevents activation on completely irrelevant queries
        if keyword_score == 0.0 and file_score == 0.0 and (not allowed_tools or not skill.requires_tools):
            return 0.0

        return min(score, 1.0)

    def _keyword_match_score(self, keywords: List[str], context: str) -> float:
        """
        Calculate keyword matching score

        Args:
            keywords: List of keywords to match
            context: User message context

        Returns:
            Score (0.0-1.0)
        """
        if not keywords:
            return 0.0

        context_lower = context.lower()

        # Count keyword matches
        matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()

            # Exact word match (word boundaries)
            if re.search(r'\b' + re.escape(keyword_lower) + r'\b', context_lower):
                matches += 1
            # Partial match (substring)
            elif keyword_lower in context_lower:
                matches += 0.5

        # Normalize by number of keywords, but cap at first 10 keywords
        # This prevents score dilution when there are many keywords
        effective_keyword_count = min(len(keywords), 10)
        score = matches / effective_keyword_count

        return min(score, 1.0)

    def _file_pattern_match_score(self, file_patterns: List[str], context: str) -> float:
        """
        Calculate file pattern matching score

        Looks for file extensions or patterns in context

        Args:
            file_patterns: List of file patterns (e.g., ["*.v", "*.sv"])
            context: User message context

        Returns:
            Score (0.0-1.0)
        """
        if not file_patterns:
            return 0.0

        # Extract potential filenames from context
        # Pattern: word.extension (e.g., "counter.v", "test.py")
        filename_pattern = r'\b[\w\-]+\.\w+\b'
        filenames = re.findall(filename_pattern, context)

        if not filenames:
            return 0.0

        # Check if any filename matches any pattern
        matches = 0
        for filename in filenames:
            for pattern in file_patterns:
                if fnmatch(filename, pattern):
                    matches += 1
                    break  # Count each filename once

        # Normalize by number of filenames found
        score = matches / len(filenames) if filenames else 0.0

        return min(score, 1.0)

    def force_activate_skill(self, skill_name: str, context: str = "") -> bool:
        """
        Force activate a skill regardless of threshold

        Args:
            skill_name: Name of the skill to activate
            context: Optional context (for logging)

        Returns:
            True if skill exists, False otherwise
        """
        from . import get_skill_registry

        registry = get_skill_registry()
        skill = registry.get_skill(skill_name)

        return skill is not None
