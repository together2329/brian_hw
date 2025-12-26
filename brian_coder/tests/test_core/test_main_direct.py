#!/usr/bin/env python3
"""
Test /context command by directly importing from main.py
"""
import sys
import os

# Add brian_coder paths (same as main.py)
_script_dir = os.path.join(os.path.dirname(__file__), "brian_coder", "src")
_project_root = os.path.join(os.path.dirname(__file__), "brian_coder")
sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

def test_context_in_main():
    """Test /context command using actual main.py setup"""

    print("=" * 70)
    print("Testing /context with actual main.py setup")
    print("=" * 70)

    # Import after path setup
    import config
    from core.context_tracker import get_tracker
    from core.slash_commands import get_registry
    import llm_client
    from main import build_system_prompt

    # Step 1: Simulate chat_loop initialization
    print("\n[Step 1] Initializing like chat_loop...")
    max_tokens = config.MAX_CONTEXT_CHARS // 4
    context_tracker = get_tracker(max_tokens=max_tokens)

    # Create initial messages
    system_prompt_content = build_system_prompt()
    messages = [
        {"role": "system", "content": system_prompt_content}
    ]

    print(f"  System prompt length: {len(system_prompt_content)} chars")
    print(f"  Max tokens: {max_tokens}")

    # Step 2: Update tracker (like chat_loop does)
    print("\n[Step 2] Updating context tracker...")
    if messages and messages[0].get("role") == "system":
        context_tracker.update_system_prompt(messages[0]["content"])

    context_tracker.update_tools("")
    context_tracker.update_memory({})
    context_tracker.update_messages(messages, exclude_system=True)

    print(f"  System tokens: {context_tracker.system_prompt_tokens}")
    print(f"  Messages tokens: {context_tracker.messages_tokens}")

    # Step 3: Test /context BEFORE any API call
    print("\n[Step 3] Testing /context (before API call)...")
    print(f"  llm_client.last_input_tokens: {llm_client.last_input_tokens}")

    slash_registry = get_registry()

    # Update tracker before /context (like main.py does)
    if messages and messages[0].get("role") == "system":
        context_tracker.update_system_prompt(messages[0]["content"])
    context_tracker.update_messages(messages, exclude_system=True)

    result = slash_registry.execute("/context debug")
    print(result)

    # Step 4: Simulate conversation
    print("\n[Step 4] Simulating conversation...")
    messages.append({"role": "user", "content": "Can you help me understand PCIe message system?"})
    messages.append({"role": "assistant", "content": "Of course! The PCIe message system in the Caliptra subsystem involves several components..."})

    # Simulate API response with actual token count
    llm_client.last_input_tokens = 55324
    print(f"  Simulated API call: last_input_tokens = {llm_client.last_input_tokens}")

    # Step 5: Test /context AFTER API call
    print("\n[Step 5] Testing /context (after API call)...")

    # Update tracker (like main.py does when /context is called)
    if messages and messages[0].get("role") == "system":
        context_tracker.update_system_prompt(messages[0]["content"])
    context_tracker.update_messages(messages, exclude_system=True)

    result = slash_registry.execute("/context debug")
    print(result)

    # Step 6: Test normal /context (without debug)
    print("\n[Step 6] Testing /context (normal mode)...")
    result = slash_registry.execute("/context")
    print(result)

    print("\n" + "=" * 70)
    print("✅ Test completed!")
    print("=" * 70)

    # Verification
    print("\n=== VERIFICATION ===")
    print(f"API reported tokens: 55,324")
    print(f"Displayed total: {llm_client.last_input_tokens:,}")
    if llm_client.last_input_tokens == 55324:
        print("✅ Token count matches!")
    else:
        print("❌ Token count mismatch!")

if __name__ == "__main__":
    test_context_in_main()
