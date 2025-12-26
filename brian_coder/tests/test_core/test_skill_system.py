"""
Test script for brian_coder Skill System

Tests:
1. Skill loading from SKILL.md files
2. Skill registry initialization
3. Skill activation based on context
4. Prompt generation
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

def test_skill_loader():
    """Test SkillLoader"""
    print("=" * 60)
    print("TEST 1: SkillLoader")
    print("=" * 60)

    from core.skill_system.loader import SkillLoader

    loader = SkillLoader()

    # List available skills
    skills = loader.list_available_skills()
    print(f"✓ Found {len(skills)} skills: {skills}")

    # Load verilog-expert
    skill = loader.load_skill("verilog-expert")

    if skill:
        print(f"✓ Loaded skill: {skill.name}")
        print(f"  Description: {skill.description}")
        print(f"  Priority: {skill.priority}")
        print(f"  Keywords: {skill.activation.keywords[:5]}...")
        print(f"  Requires tools: {skill.requires_tools}")
        print(f"  Content length: {len(skill.content)} chars")
    else:
        print("✗ Failed to load verilog-expert")
        return False

    print("\nTEST 1: PASSED ✓\n")
    return True


def test_skill_registry():
    """Test SkillRegistry"""
    print("=" * 60)
    print("TEST 2: SkillRegistry")
    print("=" * 60)

    from core.skill_system import get_skill_registry

    registry = get_skill_registry()

    # List all skills
    skill_names = registry.list_skills()
    print(f"✓ Registry contains {len(skill_names)} skills")

    for name in skill_names:
        skill = registry.get_skill(name)
        print(f"  - {name} (priority: {skill.priority})")

    # Get by priority
    sorted_skills = registry.get_skills_by_priority()
    print(f"\n✓ Skills sorted by priority:")
    for skill in sorted_skills:
        print(f"  {skill.priority}: {skill.name}")

    print("\nTEST 2: PASSED ✓\n")
    return True


def test_skill_activator():
    """Test SkillActivator"""
    print("=" * 60)
    print("TEST 3: SkillActivator")
    print("=" * 60)

    from core.skill_system import get_skill_activator

    activator = get_skill_activator()

    # Test 1: Verilog context
    context1 = "axi_awready 신호가 어디서 설정되는지 찾아줘. counter.v 파일을 분석해야 해."
    active_skills1 = activator.detect_skills(context1, threshold=0.5)

    print(f"Context: \"{context1}\"")
    print(f"✓ Activated skills: {active_skills1}")

    success = True
    if "verilog-expert" in active_skills1:
        print("  ✓ verilog-expert activated correctly!")
    else:
        print("  ✗ verilog-expert should be activated")
        success = False

    # Test 2: Protocol spec context
    context2 = "TDISP 상태머신에서 CONFIG_LOCKED로 전환하는 조건이 뭐야?"
    active_skills2 = activator.detect_skills(context2, threshold=0.5)

    print(f"\nContext: \"{context2}\"")
    print(f"✓ Activated skills: {active_skills2}")

    if "protocol-spec-expert" in active_skills2:
        print("  ✓ protocol-spec-expert activated correctly!")
    else:
        print("  ✗ protocol-spec-expert should be activated")
        success = False

    # Test 3: Testbench context
    context3 = "Create a testbench for the FIFO module with clock and reset."
    active_skills3 = activator.detect_skills(context3, threshold=0.5)

    print(f"\nContext: \"{context3}\"")
    print(f"✓ Activated skills: {active_skills3}")

    if "testbench-expert" in active_skills3:
        print("  ✓ testbench-expert activated correctly!")
    else:
        print("  ✗ testbench-expert should be activated")
        success = False

    if success:
        print("\nTEST 3: PASSED ✓\n")
        return True
    else:
        print("\nTEST 3: FAILED ✗\n")
        return False


def test_prompt_generation():
    """Test prompt generation"""
    print("=" * 60)
    print("TEST 4: Prompt Generation")
    print("=" * 60)

    from core.skill_system import get_skill_registry

    registry = get_skill_registry()
    skill = registry.get_skill("verilog-expert")

    if skill:
        prompt = skill.format_for_prompt()
        print(f"✓ Generated prompt ({len(prompt)} chars)")
        print("\nFirst 500 chars:")
        print("-" * 60)
        print(prompt[:500])
        print("...")
        print("-" * 60)
    else:
        print("✗ Failed to load skill")
        return False

    print("\nTEST 4: PASSED ✓\n")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("BRIAN CODER SKILL SYSTEM TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        test_skill_loader,
        test_skill_registry,
        test_skill_activator,
        test_prompt_generation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
