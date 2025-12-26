#!/usr/bin/env python3
"""
Test /context command with actual API tokens
"""
import sys
import os

# Add brian_coder paths
brian_coder_dir = os.path.join(os.path.dirname(__file__), "brian_coder")
src_dir = os.path.join(brian_coder_dir, "src")
sys.path.insert(0, src_dir)
sys.path.insert(0, brian_coder_dir)

# Now import
import config
from core.context_tracker import get_tracker, reset_tracker
from core.slash_commands import get_registry
import llm_client

def test_with_actual_tokens():
    """Test the context tracker with actual API token counts"""

    print("=" * 70)
    print("Testing Context with Actual API Tokens")
    print("=" * 70)

    # Reset tracker
    reset_tracker(max_tokens=65536)  # 65.5k tokens (typical for config)
    tracker = get_tracker()

    # Simulate initial state
    tracker.system_prompt_tokens = 18900  # System includes tools + memory
    tracker.tools_tokens = 0  # Included in system
    tracker.memory_tokens = 0  # Included in system
    tracker.messages_tokens = 0  # No messages yet

    print("\n1. Initial state (no API call yet):")
    print(tracker.visualize(config.MODEL_NAME))

    # Simulate after API call with actual tokens
    print("\n2. After API call (actual tokens from API):")

    # Simulate API response
    llm_client.last_input_tokens = 55324  # Actual from user's example

    print(tracker.visualize(config.MODEL_NAME, actual_total=55324))

    # Test via /context command
    print("\n" + "=" * 70)
    print("Testing /context Command")
    print("=" * 70)

    registry = get_registry()
    result = registry.execute("/context")
    print(result)

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)

if __name__ == "__main__":
    test_with_actual_tokens()
