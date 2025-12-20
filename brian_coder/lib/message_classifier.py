"""
Message Classifier for Smart Compression

Classifies messages by importance to determine what should be
preserved vs summarized during context compression.

Zero-dependency (uses regex for pattern matching).
"""
import re
from typing import Dict, List, Tuple


class MessageImportance:
    """Message importance levels"""
    CRITICAL = 3  # Must preserve (user preferences, explicit requirements)
    HIGH = 2      # Should preserve (error solutions, successful patterns)
    MEDIUM = 1    # Can summarize (regular conversation)
    LOW = 0       # Can heavily summarize (failed attempts, exploration)


class MessageClassifier:
    """
    Classifies messages by importance for smart compression.

    Uses regex patterns (zero API cost) to identify:
    - User preferences and explicit requirements
    - Successful tool executions and error solutions
    - Project context and important decisions
    """

    def __init__(self):
        # Critical patterns (user preferences and explicit requirements)
        self.critical_patterns = [
            # Explicit preferences
            r'\b(always|never|must|should|don\'t)\s+(use|add|include|exclude)\b',
            r'\b(prefer|preference|convention|style)\b',

            # Naming conventions
            r'\b(snake_case|camelCase|PascalCase|kebab-case)\b',

            # Code style directives
            r'\b(indentation|tabs?|spaces?|comments?|docstrings?)\b',

            # Project requirements
            r'\b(requirement|spec|specification|must have)\b',
            # Korean requirements/preferences (unicode escapes to keep source ASCII)
            r'(?:\uBC18\uB4DC\uC2DC|\uC808\uB300|\uD574\uC57C|\uD558\uC9C0\s*\uB9C8|\uAE08\uC9C0|\uD544\uC218|\uC694\uAD6C\uC0AC\uD56D|\uC0AC\uC591|\uC2A4\uD399|\uADDC\uCE59|\uCEE8\uBCA4\uC158|\uC2A4\uD0C0\uC77C|\uD45C\uC900)',
        ]

        # High importance patterns (errors and solutions)
        self.high_patterns = [
            # Error resolution
            r'\b(fixed|solved|resolved|corrected)\b.*\b(error|bug|issue|problem)\b',
            r'\bsolution:?\s',

            # Successful completion
            r'\b(successfully|completed|done|finished)\b.*\b(task|work|implementation)\b',

            # Important discoveries
            r'\b(found|discovered|identified)\b.*\b(root cause|solution|fix)\b',
            # Decisions and changes
            r'\b(decided|decision|choose|chosen|switch(?:ed)?|rename(?:d)?|deprecate(?:d)?|workaround|mitigation|root cause|rca)\b',
            r'(?:\uACB0\uC815|\uC120\uD0DD|\uBCC0\uACBD|\uC804\uD658|\uCC44\uD0DD|\uD569\uC758|\uC6D0\uC778|\uD574\uACB0|\uC218\uC815)',
        ]

        # Low importance patterns (exploration and failures)
        self.low_patterns = [
            # Failed attempts
            r'\b(failed|error|exception|traceback)\b',
            r'\b(trying|attempt|investigating)\b',

            # Exploration
            r'\b(reading|checking|looking|searching)\b',
            r'\b(let me|I will|I\'ll)\s+(read|check|look|search)\b',
        ]

        # Compile patterns
        self.critical_regex = [re.compile(p, re.IGNORECASE) for p in self.critical_patterns]
        self.high_regex = [re.compile(p, re.IGNORECASE) for p in self.high_patterns]
        self.low_regex = [re.compile(p, re.IGNORECASE) for p in self.low_patterns]
        
        # System error pattern (for protecting error logs)
        self.error_regex = re.compile(r'\b(Error|Exception|Traceback|Fail|Failed)\b', re.IGNORECASE)
        self.observation_regex = re.compile(r'^\s*Observation:', re.IGNORECASE)
        self.tool_output_regex = re.compile(r'^\s*(STDOUT|STDERR):', re.IGNORECASE)


    def classify_message(self, message: Dict) -> int:
        """
        Classify a single message by importance.

        Args:
            message: Message dict with "role" and "content"

        Returns:
            Importance level (0-3)
        """
        role = message.get("role", "")
        content = str(message.get("content", ""))

        # Determine base importance
        base_importance = MessageImportance.LOW
        is_observation = False
        if role == "user":
            is_observation = bool(self.observation_regex.match(content)) or bool(self.tool_output_regex.match(content))
        
        # 1. System Messages (Refined Heuristic)
        if role == "system":
            # Check for explicit Error/Traceback patterns first (HIGH)
            if self.error_regex.search(content):
                base_importance = MessageImportance.HIGH
            # Keep short status messages (HIGH)
            elif len(content) < 1000:
                base_importance = MessageImportance.HIGH
            else:
                # Large non-error outputs (LOW)
                base_importance = MessageImportance.LOW
                
        # 2. User Messages (MEDIUM)
        elif role == "user":
            base_importance = MessageImportance.LOW if is_observation else MessageImportance.MEDIUM
            
        # 3. Assistant Messages (MEDIUM) matches default logic
        else:
            base_importance = MessageImportance.MEDIUM

        # Check critical patterns (Only for User/Assistant, avoid System tool outputs matching 'spec')
        if role != "system":
            for pattern in self.critical_regex:
                if pattern.search(content):
                    return MessageImportance.CRITICAL

        # Check high patterns (Errors/Success) - Apply to all (including system for errors)
        for pattern in self.high_regex:
            if pattern.search(content):
                return max(base_importance, MessageImportance.HIGH)

        # Check low patterns (only for assistant messages)
        # We don't check low patterns for system messages, they default to LOW anyway
        if role == "assistant":
            for pattern in self.low_regex:
                if pattern.search(content):
                    return MessageImportance.LOW

        return base_importance

    def classify_messages(self, messages: List[Dict]) -> List[Tuple[Dict, int]]:
        """
        Classify multiple messages.

        Args:
            messages: List of message dicts

        Returns:
            List of (message, importance) tuples
        """
        return [(msg, self.classify_message(msg)) for msg in messages]

    def partition_by_importance(self, messages: List[Dict],
                                keep_recent: int = 4) -> Dict[str, List[Dict]]:
        """
        Partition messages into groups by importance.

        Args:
            messages: List of message dicts
            keep_recent: Number of recent messages to always keep

        Returns:
            Dict with keys: "system", "critical", "high", "medium", "low", "recent"
        """
        # Preserve initial system messages (system prompt) as a separate bucket.
        system_prefix = []
        idx = 0
        while idx < len(messages) and messages[idx].get("role") == "system":
            system_prefix.append(messages[idx])
            idx += 1
        remaining = messages[idx:]

        # Keep recent messages separate
        if len(remaining) > keep_recent:
            recent_msgs = remaining[-keep_recent:]
            old_msgs = remaining[:-keep_recent]
        else:
            recent_msgs = remaining
            old_msgs = []

        # Classify old messages
        classified = self.classify_messages(old_msgs)

        # Partition by importance
        critical = [m for m, imp in classified if imp == MessageImportance.CRITICAL]
        high = [m for m, imp in classified if imp == MessageImportance.HIGH]
        medium = [m for m, imp in classified if imp == MessageImportance.MEDIUM]
        low = [m for m, imp in classified if imp == MessageImportance.LOW]

        return {
            "system": system_prefix,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "recent": recent_msgs
        }

    def get_compression_summary(self, partitions: Dict[str, List[Dict]]) -> str:
        """
        Get summary of compression plan.

        Args:
            partitions: Result from partition_by_importance()

        Returns:
            Human-readable summary
        """
        counts = {k: len(v) for k, v in partitions.items()}

        summary = f"""Compression Plan:
  System:   {counts['system']} (always keep)
  Critical: {counts['critical']} (preserve)
  High:     {counts['high']} (preserve)
  Medium:   {counts['medium']} (summarize)
  Low:      {counts['low']} (heavily summarize)
  Recent:   {counts['recent']} (always keep)

  Total preserved: {counts['system'] + counts['critical'] + counts['high'] + counts['recent']}
  Total to summarize: {counts['medium'] + counts['low']}
"""
        return summary


# Convenience function
def get_classifier() -> MessageClassifier:
    """Get message classifier instance"""
    return MessageClassifier()
