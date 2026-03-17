"""
Sub-Agents Module (v2 - Deprecated Legacy Compatibility)

Legacy sub_agents have been replaced by:
- core/agent_runner.py - Lightweight ReAct loop runner
- core/background.py - Background agent manager
- agents/prompts/ - Agent-specific system prompts

This module provides stub imports for backward compatibility.
"""

# Stub for backward compatibility
class Orchestrator:
    """Deprecated: Use core.background.BackgroundManager instead."""
    def __init__(self, *args, **kwargs):
        pass
    def run(self, *args, **kwargs):
        return None

__all__ = ['Orchestrator']
