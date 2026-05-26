#!/usr/bin/env python3
"""
Test /context command
"""
import sys
import os
import json

# Add common_ai_agent paths
common_ai_agent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src_dir = os.path.join(common_ai_agent_dir, "src")
sys.path.insert(0, src_dir)
sys.path.insert(0, common_ai_agent_dir)

# Now import
import config
from core.context_tracker import get_tracker
from core.slash_commands import get_registry


def _write_session_messages(root, session, messages):
    session_dir = root / ".session" / session
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "conversation.json"
    path.write_text(json.dumps(messages, indent=2), encoding="utf-8")
    return path

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


def test_context_verbose_uses_atlas_bridge_session(tmp_path, monkeypatch):
    from core.atlas_multiuser import reset_atlas_bridge_session_id, set_atlas_bridge_session_id
    from core.context_tracker import reset_tracker

    session = "alice/ip_alpha/rtl-gen"
    _write_session_messages(tmp_path, session, [
        {"role": "system", "content": f"[ACTIVE_SESSION: {session}]"},
        {"role": "user", "content": "bridge session question"},
        {"role": "assistant", "content": "bridge session answer"},
    ])
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
    monkeypatch.delenv("ATLAS_SESSION_APPLIED", raising=False)
    monkeypatch.delenv("ATLAS_SESSION_ID", raising=False)
    reset_tracker(max_tokens=200000)

    token = set_atlas_bridge_session_id(session)
    try:
        result = get_registry().execute("/context -v")
    finally:
        reset_atlas_bridge_session_id(token)

    assert "bridge session question" in result
    assert "bridge session answer" in result
    assert "Current context window is empty" not in result


def test_context_verbose_finds_session_from_nested_cwd(tmp_path, monkeypatch):
    from core.context_tracker import reset_tracker

    session = "bob/ip_beta/ssot-gen"
    _write_session_messages(tmp_path, session, [
        {"role": "system", "content": f"[ACTIVE_SESSION: {session}]"},
        {"role": "user", "content": "nested cwd question"},
        {"role": "assistant", "content": "nested cwd answer"},
    ])
    nested = tmp_path / "ip_beta" / "rtl"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.delenv("ATLAS_PROJECT_ROOT", raising=False)
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", session)
    monkeypatch.delenv("ATLAS_SESSION_APPLIED", raising=False)
    monkeypatch.delenv("ATLAS_SESSION_ID", raising=False)
    reset_tracker(max_tokens=200000)

    result = get_registry().execute("/context -v")

    assert "nested cwd question" in result
    assert "nested cwd answer" in result
    assert "Current context window is empty" not in result

if __name__ == "__main__":
    test_context_visualization()
