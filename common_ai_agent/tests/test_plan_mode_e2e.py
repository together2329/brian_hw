#!/usr/bin/env python3
"""
E2E Test for Interactive Plan Mode

Tests the complete flow:
1. /plan command execution
2. Plan Mode entry
3. Plan Agent draft generation
4. Interactive refinement
5. Plan approval and execution

Usage:
    python test_plan_mode_e2e.py

Test scenarios:
- Test 1: Basic plan mode flow (approve immediately)
- Test 2: Plan refinement (modify then approve)
- Test 3: Plan cancellation
- Test 4: Error handling (invalid task)
"""

import sys
import os

# Add common_ai_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent/src'))

import config
from core.plan_mode import plan_mode_loop, PlanModeResult
from lib.display import Color
from core.slash_commands import get_registry


def test_1_basic_plan_mode():
    """Test 1: Basic plan mode flow"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Plan Mode Flow")
    print("=" * 60)

    task = "Create a simple 4-bit up counter with enable signal"
    print(f"Task: {task}")

    # Simulate plan mode with auto-approval
    # In real test, we would mock user input
    print(Color.warning("\n[Test] This test requires manual interaction."))
    print(Color.info("[Test] Run manually with: /plan " + task))
    print(Color.info("[Test] Then type 'approve' to approve the plan"))

    return True


def test_2_slash_command():
    """Test 2: Slash command registry"""
    print("\n" + "=" * 60)
    print("TEST 2: Slash Command Registry")
    print("=" * 60)

    registry = get_registry()

    # Test /plan command exists
    result = registry.execute("/plan Create a counter")
    print(f"Result: {result}")

    if result and result.startswith("PLAN_MODE_REQUEST:"):
        task = result.split(":", 1)[1].strip()
        print(Color.success(f"✅ /plan command works, extracted task: {task}"))
        return True
    else:
        print(Color.error("❌ /plan command failed"))
        return False


def test_3_plan_file_creation():
    """Test 3: Plan file creation"""
    print("\n" + "=" * 60)
    print("TEST 3: Plan File Creation")
    print("=" * 60)

    from core.plan_mode import _save_plan_to_file

    task = "Test task for E2E"
    plan_content = """## Task Analysis
Test plan content

## Implementation Steps
1. Step 1
2. Step 2
3. Step 3

## Success Criteria
- Criterion 1
"""

    try:
        plan_path = _save_plan_to_file(task, plan_content)
        print(f"Plan saved to: {plan_path}")

        # Verify file exists
        if os.path.exists(plan_path):
            print(Color.success("✅ Plan file created successfully"))

            # Read back and verify
            with open(plan_path, 'r') as f:
                content = f.read()

            if "Test plan content" in content:
                print(Color.success("✅ Plan content verified"))

                # Cleanup
                os.remove(plan_path)
                print(Color.info("[Test] Cleaned up test plan file"))
                return True
            else:
                print(Color.error("❌ Plan content mismatch"))
                return False
        else:
            print(Color.error("❌ Plan file not created"))
            return False
    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        return False


def test_4_step_extraction():
    """Test 4: Step extraction from plan"""
    print("\n" + "=" * 60)
    print("TEST 4: Step Extraction from Plan")
    print("=" * 60)

    from main import _extract_steps_from_plan_text

    plan_text = """# Plan

## Task
Create a counter

## Implementation Steps
1. Create module skeleton with parameters
2. Implement counter logic with enable
3. Add testbench with multiple test cases
4. Compile and simulate
5. Verify waveforms

## Success Criteria
- Counter increments correctly
"""

    steps = _extract_steps_from_plan_text(plan_text)
    print(f"Extracted {len(steps)} steps:")
    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")

    if len(steps) == 5 and "module skeleton" in steps[0]:
        print(Color.success("✅ Step extraction works correctly"))
        return True
    else:
        print(Color.error("❌ Step extraction failed"))
        return False


def test_5_error_handling():
    """Test 5: Error handling"""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling")
    print("=" * 60)

    from core.plan_mode import _execute_plan_tool

    # Test 1: Invalid tool name
    result = _execute_plan_tool("invalid_tool", "query='test'")
    if "not allowed" in result:
        print(Color.success("✅ Invalid tool rejection works"))
    else:
        print(Color.error("❌ Invalid tool rejection failed"))
        return False

    # Test 2: Empty query
    result = _execute_plan_tool("spawn_explore", "")
    if "non-empty query" in result:
        print(Color.success("✅ Empty query rejection works"))
    else:
        print(Color.error("❌ Empty query rejection failed"))
        return False

    return True


def test_6_plan_mode_result():
    """Test 6: PlanModeResult dataclass"""
    print("\n" + "=" * 60)
    print("TEST 6: PlanModeResult Dataclass")
    print("=" * 60)

    import tempfile
    test_plan_path = os.path.join(tempfile.gettempdir(), "test.md")
    result = PlanModeResult(
        plan_path=test_plan_path,
        plan_content="Test plan"
    )

    if result.plan_path == test_plan_path and result.plan_content == "Test plan":
        print(Color.success("✅ PlanModeResult works correctly"))
        return True
    else:
        print(Color.error("❌ PlanModeResult failed"))
        return False


def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "PLAN MODE E2E TESTS")
    print("=" * 70)

    tests = [
        ("Slash Command Registry", test_2_slash_command),
        ("Plan File Creation", test_3_plan_file_creation),
        ("Step Extraction", test_4_step_extraction),
        ("Error Handling", test_5_error_handling),
        ("PlanModeResult", test_6_plan_mode_result),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(Color.error(f"❌ Exception in {name}: {e}"))
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Manual test
    print("\n" + "=" * 60)
    print("MANUAL TEST REQUIRED")
    print("=" * 60)
    print(Color.warning("Test 1 (Basic Plan Mode) requires manual interaction:"))
    print(Color.info("  1. Run: python common_ai_agent/src/main.py"))
    print(Color.info("  2. Type: /plan Create a simple 4-bit counter with enable"))
    print(Color.info("  3. Review the generated plan"))
    print(Color.info("  4. Type: approve"))
    print(Color.info("  5. Verify Main Agent executes the plan"))

    # Summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = Color.success("✅ PASS") if result else Color.error("❌ FAIL")
        print(f"{status}  {name}")

    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print(Color.success("\n🎉 All automated tests passed!"))
        print(Color.warning("📝 Don't forget to run the manual test"))
        return 0
    else:
        print(Color.error(f"\n❌ {total - passed} test(s) failed"))
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
