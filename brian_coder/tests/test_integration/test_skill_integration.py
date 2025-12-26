#!/usr/bin/env python3
"""
End-to-End Integration Test for Skill System

Simulates actual brian_coder workflow with skill activation
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder', 'src'))

# Import after path setup
import config
from core.skill_system import get_skill_registry, get_skill_activator


def simulate_conversation(user_message):
    """Simulate a conversation turn with skill system"""
    print("=" * 80)
    print(f"USER: {user_message}")
    print("=" * 80)

    # Build message history (simulating conversation)
    messages = [
        {"role": "user", "content": user_message}
    ]

    # Get registry and activator
    registry = get_skill_registry()
    activator = get_skill_activator()

    # Extract recent user context
    user_messages = [m for m in messages if m.get("role") == "user"]
    recent_context = " ".join([
        msg["content"] for msg in user_messages[-5:]
        if isinstance(msg.get("content"), str)
    ])

    print(f"\n📝 Context extracted: \"{recent_context[:80]}...\"")

    # Detect active skills
    active_skill_names = activator.detect_skills(
        context=recent_context,
        allowed_tools=None,
        threshold=config.SKILL_ACTIVATION_THRESHOLD
    )

    if active_skill_names:
        print(f"\n✅ ACTIVATED SKILLS ({len(active_skill_names)}):")
        for skill_name in active_skill_names:
            skill = registry.get_skill(skill_name)
            print(f"  🔧 {skill.name}")
            print(f"     Priority: {skill.priority}")
            print(f"     Description: {skill.description}")

        # Generate skill prompts
        print(f"\n📄 SKILL PROMPTS INJECTED:")
        for skill_name in active_skill_names:
            skill = registry.get_skill(skill_name)
            prompt = skill.format_for_prompt()

            print(f"\n  --- {skill.name} ---")
            print(f"  Length: {len(prompt)} chars")
            print(f"  Preview (first 300 chars):")
            print("  " + "-" * 70)
            for line in prompt[:300].split('\n'):
                print(f"  {line}")
            print("  ...")
            print("  " + "-" * 70)
    else:
        print("\n❌ NO SKILLS ACTIVATED")
        print(f"   Threshold: {config.SKILL_ACTIVATION_THRESHOLD}")

        # Show scores for debugging
        print("\n   Debug - All skill scores:")
        for skill_name in registry.list_skills():
            skill = registry.get_skill(skill_name)
            score = activator._calculate_activation_score(skill, recent_context, None)
            status = "✓" if score >= config.SKILL_ACTIVATION_THRESHOLD else "✗"
            print(f"     {status} {skill_name:25s} score={score:.3f}")

    print("\n" + "=" * 80 + "\n")


def main():
    """Run integration tests"""
    print("\n" + "=" * 80)
    print("SKILL SYSTEM INTEGRATION TEST")
    print("Testing actual brian_coder workflow with skill activation")
    print("=" * 80 + "\n")

    print(f"Configuration:")
    print(f"  ENABLE_SKILL_SYSTEM: {config.ENABLE_SKILL_SYSTEM}")
    print(f"  SKILL_ACTIVATION_THRESHOLD: {config.SKILL_ACTIVATION_THRESHOLD}")
    print(f"  Available skills: {get_skill_registry().list_skills()}")
    print()

    # Test Case 1: Verilog signal search
    simulate_conversation(
        "axi_awready 신호가 어디서 설정되는지 찾아줘. counter.v 파일에서 확인해야 해."
    )

    # Test Case 2: Protocol specification
    simulate_conversation(
        "TDISP 상태머신에서 CONFIG_LOCKED 상태로 전환하는 조건이 뭐야? PCIe 스펙을 확인해줘."
    )

    # Test Case 3: Testbench creation
    simulate_conversation(
        "Create a comprehensive testbench for the AXI slave module. Include clock generation, reset logic, and self-checking mechanisms."
    )

    # Test Case 4: Mixed keywords (should activate verilog-expert)
    simulate_conversation(
        "Analyze the FSM in the state_machine.v file and find potential timing violations."
    )

    # Test Case 5: No skill should activate
    simulate_conversation(
        "Hello, how are you today?"
    )

    print("\n" + "=" * 80)
    print("INTEGRATION TEST COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
