#!/usr/bin/env python3
"""
Simulate actual brian_coder usage with /context command
"""
import sys
import os

# Add brian_coder paths (same as main.py)
_script_dir = os.path.join(os.path.dirname(__file__), "brian_coder", "src")
_project_root = os.path.join(os.path.dirname(__file__), "brian_coder")
sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

import config
from core.context_tracker import get_tracker, reset_tracker
from core.slash_commands import get_registry
import llm_client

def simulate_chat_session():
    """Simulate a chat session with API calls"""

    print("=" * 70)
    print("Simulating Brian Coder Chat Session")
    print("=" * 70)

    # Step 1: Initialize like chat_loop does
    print("\n[1] Initializing context tracker...")
    max_tokens = config.MAX_CONTEXT_CHARS // 4
    print(f"    MAX_CONTEXT_CHARS: {config.MAX_CONTEXT_CHARS}")
    print(f"    max_tokens: {max_tokens}")

    context_tracker = get_tracker(max_tokens=max_tokens)

    # Step 2: Create initial messages
    from main import build_system_prompt

    system_prompt = build_system_prompt()
    print(f"\n[2] System prompt length: {len(system_prompt)} chars")

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Step 3: Update tracker
    print("\n[3] Updating tracker with system prompt...")
    context_tracker.update_system_prompt(system_prompt)
    context_tracker.update_tools("")
    context_tracker.update_memory({})
    context_tracker.update_messages(messages, exclude_system=True)

    print(f"    tracker.system_prompt_tokens: {context_tracker.system_prompt_tokens}")
    print(f"    tracker.messages_tokens: {context_tracker.messages_tokens}")

    # Step 4: Test /context before any API call
    print("\n[4] Testing /context (before API call)...")
    print(f"    llm_client.last_input_tokens: {llm_client.last_input_tokens}")

    slash_registry = get_registry()
    result = slash_registry.execute("/context debug")
    print(result)

    # Step 5: Simulate user message and API response
    print("\n[5] Simulating API call...")
    messages.append({"role": "user", "content": "Hello, can you help me with Verilog?"})
    messages.append({"role": "assistant", "content": "Of course! I'd be happy to help you with Verilog. What specific aspect would you like assistance with?"})

    # Simulate API token count (like what API would return)
    llm_client.last_input_tokens = 55324  # From user's example
    print(f"    Simulated API response: last_input_tokens = {llm_client.last_input_tokens}")

    # Update tracker with new messages
    context_tracker.update_messages(messages, exclude_system=True)
    print(f"    tracker.messages_tokens (estimated): {context_tracker.messages_tokens}")

    # Step 6: Test /context after API call
    print("\n[6] Testing /context (after API call)...")
    result = slash_registry.execute("/context debug")
    print(result)

    # Step 7: Test without debug
    print("\n[7] Testing /context (normal mode)...")
    result = slash_registry.execute("/context")
    print(result)

    print("\n" + "=" * 70)
    print("✅ Simulation complete!")
    print("=" * 70)

if __name__ == "__main__":
    simulate_chat_session()
