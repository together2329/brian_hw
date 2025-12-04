"""
Simple Memory System for Brian Coder

Stores user preferences and project context in JSON files.
Zero-dependency (stdlib only).
"""
import json
from pathlib import Path
from typing import Any, Dict, Optional


class MemorySystem:
    """
    Simple Declarative Memory system.

    Stores:
    - User preferences (coding style, naming conventions, etc.)
    - Project context (file structure, main modules, etc.)

    Storage: JSON files in ~/.brian_memory/
    """

    def __init__(self, memory_dir: str = ".brian_memory"):
        """
        Initialize memory system.

        Args:
            memory_dir: Directory name (relative to home)
        """
        self.memory_dir = Path.home() / memory_dir
        self.preferences_file = self.memory_dir / "preferences.json"
        self.project_context_file = self.memory_dir / "project_context.json"

        self._preferences: Dict[str, Any] = {}
        self._project_context: Dict[str, Any] = {}

        self._ensure_initialized()
        self._load()

    def _ensure_initialized(self):
        """Create memory directory and files if they don't exist"""
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        if not self.preferences_file.exists():
            self._save_preferences()

        if not self.project_context_file.exists():
            self._save_project_context()

    def _load(self):
        """Load memories from disk"""
        try:
            with open(self.preferences_file, 'r') as f:
                self._preferences = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._preferences = {}

        try:
            with open(self.project_context_file, 'r') as f:
                self._project_context = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._project_context = {}

    def _save_preferences(self):
        """Save preferences to disk"""
        with open(self.preferences_file, 'w') as f:
            json.dump(self._preferences, f, indent=2)

    def _save_project_context(self):
        """Save project context to disk"""
        with open(self.project_context_file, 'w') as f:
            json.dump(self._project_context, f, indent=2)

    # ========== Preferences Management ==========

    def update_preference(self, key: str, value: Any) -> None:
        """
        Update user preference.

        Args:
            key: Preference key (e.g., "variable_naming", "indentation")
            value: Preference value

        Examples:
            memory.update_preference("variable_naming", "snake_case")
            memory.update_preference("add_comments", False)
        """
        self._preferences[key] = value
        self._save_preferences()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """
        Get user preference.

        Args:
            key: Preference key
            default: Default value if key not found

        Returns:
            Preference value or default
        """
        return self._preferences.get(key, default)

    def remove_preference(self, key: str) -> bool:
        """
        Remove user preference.

        Args:
            key: Preference key

        Returns:
            True if removed, False if not found
        """
        if key in self._preferences:
            del self._preferences[key]
            self._save_preferences()
            return True
        return False

    def list_preferences(self) -> Dict[str, Any]:
        """Get all preferences"""
        return self._preferences.copy()

    def format_preferences_for_prompt(self) -> str:
        """
        Format preferences as text for LLM prompt.

        Returns:
            Formatted string ready to inject into system prompt
        """
        if not self._preferences:
            return ""

        lines = ["User Preferences:"]
        for key, value in self._preferences.items():
            # Convert key from snake_case to Title Case
            display_key = key.replace('_', ' ').title()
            lines.append(f"- {display_key}: {value}")

        return "\n".join(lines)

    # ========== Project Context Management ==========

    def update_project_context(self, key: str, value: Any) -> None:
        """
        Update project context.

        Args:
            key: Context key (e.g., "project_type", "main_modules")
            value: Context value

        Examples:
            memory.update_project_context("project_type", "Verilog PCIe system")
            memory.update_project_context("main_modules", ["pcie_msg_receiver", "pcie_axi_to_sram"])
        """
        self._project_context[key] = value
        self._save_project_context()

    def get_project_context(self, key: str, default: Any = None) -> Any:
        """Get project context"""
        return self._project_context.get(key, default)

    def remove_project_context(self, key: str) -> bool:
        """Remove project context"""
        if key in self._project_context:
            del self._project_context[key]
            self._save_project_context()
            return True
        return False

    def list_project_context(self) -> Dict[str, Any]:
        """Get all project context"""
        return self._project_context.copy()

    def format_project_context_for_prompt(self) -> str:
        """
        Format project context as text for LLM prompt.

        Returns:
            Formatted string ready to inject into system prompt
        """
        if not self._project_context:
            return ""

        lines = ["Project Context:"]
        for key, value in self._project_context.items():
            display_key = key.replace('_', ' ').title()

            # Handle lists
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            lines.append(f"- {display_key}: {value_str}")

        return "\n".join(lines)

    # ========== Combined Formatting ==========

    def format_all_for_prompt(self) -> str:
        """
        Format all memories for LLM prompt.

        Returns:
            Complete formatted string with preferences and context
        """
        sections = []

        pref = self.format_preferences_for_prompt()
        if pref:
            sections.append(pref)

        ctx = self.format_project_context_for_prompt()
        if ctx:
            sections.append(ctx)

        if sections:
            return "\n\n".join(sections)
        else:
            return ""

    # ========== Utility ==========

    def clear_all(self):
        """Clear all memories (use with caution!)"""
        self._preferences = {}
        self._project_context = {}
        self._save_preferences()
        self._save_project_context()

    def export_to_dict(self) -> Dict[str, Any]:
        """Export all memories as dictionary"""
        return {
            "preferences": self._preferences,
            "project_context": self._project_context
        }

    def import_from_dict(self, data: Dict[str, Any]):
        """Import memories from dictionary"""
        if "preferences" in data:
            self._preferences = data["preferences"]
            self._save_preferences()

        if "project_context" in data:
            self._project_context = data["project_context"]
            self._save_project_context()

    # ========== Mem0-style Auto Update ==========

    def auto_extract_and_update(self, user_message: str, llm_call_func=None) -> Dict[str, Any]:
        """
        Mem0-style automatic fact extraction and update.

        Extracts preferences from user messages and automatically updates memory.
        Uses LLM to detect preference changes and resolve conflicts.

        Args:
            user_message: User's message
            llm_call_func: LLM call function (if None, will try to import from main)

        Returns:
            Dictionary with extraction results
        """
        if llm_call_func is None:
            try:
                from main import call_llm_raw
                llm_call_func = call_llm_raw
            except ImportError:
                return {"error": "No LLM call function available"}

        try:
            # Extract facts using LLM
            facts = self._llm_extract_facts(user_message, llm_call_func)

            if not facts:
                return {"extracted": 0, "actions": []}

            actions_taken = []

            # Process each extracted fact
            for fact in facts:
                key = fact.get("key", "")
                value = fact.get("value", "")
                confidence = fact.get("confidence", 0.5)

                if not key or not value:
                    continue

                # Check if fact already exists
                existing_value = self.get_preference(key)

                if existing_value is None:
                    # ADD: New preference
                    self.update_preference(key, value)
                    actions_taken.append({
                        "action": "ADD",
                        "key": key,
                        "value": value,
                        "confidence": confidence
                    })

                elif existing_value != value:
                    # CONFLICT: Decide whether to update
                    decision = self._llm_resolve_conflict(
                        key, existing_value, value, llm_call_func
                    )

                    if decision == "UPDATE":
                        self.update_preference(key, value)
                        actions_taken.append({
                            "action": "UPDATE",
                            "key": key,
                            "old_value": existing_value,
                            "new_value": value,
                            "confidence": confidence
                        })
                    elif decision == "DELETE":
                        self.remove_preference(key)
                        actions_taken.append({
                            "action": "DELETE",
                            "key": key,
                            "old_value": existing_value
                        })
                    else:
                        # KEEP: No action
                        actions_taken.append({
                            "action": "KEEP",
                            "key": key,
                            "value": existing_value
                        })
                else:
                    # SAME: Already have this preference
                    pass

            return {
                "extracted": len(facts),
                "actions": actions_taken
            }

        except Exception as e:
            return {"error": str(e)}

    def _llm_extract_facts(self, message: str, llm_call_func) -> list:
        """
        Extract preference facts from message using LLM.

        Args:
            message: User message
            llm_call_func: LLM call function

        Returns:
            List of extracted facts
        """
        prompt = f"""Extract user preferences from this message.
Look for:
- Coding style preferences (snake_case, camelCase, etc.)
- Language preferences (Korean, English, etc.)
- Tool preferences (which tools to use/avoid)
- Response format preferences
- Any explicit "from now on" or "always" statements

Message: "{message}"

Return JSON array with format:
[{{"key": "preference_name", "value": "preference_value", "confidence": 0.0-1.0}}]

If no preferences found, return empty array: []

Preferences (JSON only):"""

        try:
            response = llm_call_func(prompt)

            # Parse JSON from response
            start_idx = response.find('[')
            end_idx = response.rfind(']') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                facts = json.loads(json_str)
                return facts if isinstance(facts, list) else []

            return []

        except Exception:
            return []

    def _llm_resolve_conflict(self, key: str, old_value: Any, new_value: Any,
                             llm_call_func) -> str:
        """
        Resolve conflict between old and new preference values using LLM.

        Args:
            key: Preference key
            old_value: Existing value
            new_value: New value
            llm_call_func: LLM call function

        Returns:
            Decision: "UPDATE", "DELETE", or "KEEP"
        """
        prompt = f"""Resolve preference conflict.

Preference: {key}
Current value: {old_value}
New value: {new_value}

Decide what to do:
- UPDATE: Replace old value with new value (user changed their mind)
- DELETE: Remove this preference (user wants to disable it)
- KEEP: Keep old value (new value is not a replacement)

Return ONLY one word: UPDATE, DELETE, or KEEP

Decision:"""

        try:
            response = llm_call_func(prompt).strip().upper()

            if "UPDATE" in response:
                return "UPDATE"
            elif "DELETE" in response:
                return "DELETE"
            else:
                return "KEEP"

        except Exception:
            # Default to UPDATE on error
            return "UPDATE"


# Convenience function for quick access
def get_memory_system(memory_dir: str = ".brian_memory") -> MemorySystem:
    """
    Get or create memory system instance.

    Args:
        memory_dir: Memory directory name

    Returns:
        MemorySystem instance
    """
    return MemorySystem(memory_dir=memory_dir)
