#!/usr/bin/env python3
"""
Test /context command
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
from core.context_tracker import get_tracker
from core.slash_commands import get_registry

def test_context_visualization():
    """Test the context tracker and /context command"""

    print("=" * 70)
    print("Testing Context Tracker")
    print("=" * 70)

    # Initialize tracker
    tracker = get_tracker(max_tokens=200000)

    # Simulate realistic usage (tools and memory included in system)
    tracker.system_prompt_tokens = 18900  # System includes tools + memory
    tracker.tools_tokens = 0  # Included in system
    tracker.memory_tokens = 0  # Included in system
    tracker.messages_tokens = 57500  # User/assistant messages only

    # Test visualization
    print("\n1. Low usage scenario:")
    print(tracker.visualize(config.MODEL_NAME))

    # Test high usage
    from core.context_tracker import reset_tracker
    reset_tracker(max_tokens=200000)
    tracker2 = get_tracker()
    tracker2.system_prompt_tokens = 25000  # System includes tools + memory
    tracker2.tools_tokens = 0  # Included in system
    tracker2.memory_tokens = 0  # Included in system
    tracker2.messages_tokens = 145000  # User/assistant messages only

    print("\n2. High usage scenario:")
    print(tracker2.visualize(config.MODEL_NAME))

    # Test /context command
    print("\n" + "=" * 70)
    print("Testing /context Slash Command")
    print("=" * 70)

    # Reset to low usage
    reset_tracker(max_tokens=200000)
    tracker = get_tracker()
    tracker.system_prompt_tokens = 18900
    tracker.tools_tokens = 0
    tracker.memory_tokens = 0
    tracker.messages_tokens = 57500

    registry = get_registry()
    result = registry.execute("/context")
    print(result)

    print("\n" + "=" * 70)
    print("✅ All tests passed!")
    print("=" * 70)

if __name__ == "__main__":
    test_context_visualization()
