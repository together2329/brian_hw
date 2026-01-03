#!/usr/bin/env python3
"""
Test Plan Mode Fixes

Tests for:
1. Phase extraction from plan text
2. Plan extraction from LLM output
3. TodoTracker integration
"""

import sys
import os

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)

def test_phase_extraction():
    """Test Phase extraction from different plan formats"""
    print("\n" + "=" * 60)
    print("TEST 1: Phase Extraction")
    print("=" * 60)

    from main import _extract_steps_from_plan_text

    # Test 1: Phase with "###" headers
    plan1 = """
# Plan

## Task
analyze caliptra subsystem

### Phase 1 – Repository Setup
Clone and build

### Phase 2 – Architecture Extraction
Read top-level files

### Phase 3 – Deep-Dive
Analyze crypto engines
    """

    steps1 = _extract_steps_from_plan_text(plan1)
    print("\n[Test 1] Phase with ### headers:")
    print(f"  Input: {len(plan1)} chars")
    print(f"  Output: {len(steps1)} steps")
    for i, step in enumerate(steps1, 1):
        print(f"    {i}. {step}")

    assert len(steps1) == 3, f"Expected 3 steps, got {len(steps1)}"
    assert "Phase 1" in steps1[0], f"Expected 'Phase 1' in first step"
    print("  ✅ PASS")

    # Test 2: Phase without "###"
    plan2 = """
## Implementation

Phase 1 – Setup (5 min)
Clone repository

Phase 2 – Analysis (15 min)
Read source code

Phase 3 – Report (10 min)
Write findings
    """

    steps2 = _extract_steps_from_plan_text(plan2)
    print("\n[Test 2] Phase without ### headers:")
    print(f"  Input: {len(plan2)} chars")
    print(f"  Output: {len(steps2)} steps")
    for i, step in enumerate(steps2, 1):
        print(f"    {i}. {step}")

    assert len(steps2) >= 3, f"Expected 3+ steps, got {len(steps2)}"
    print("  ✅ PASS")

    # Test 3: Regular numbered list (fallback)
    plan3 = """
## Implementation Steps

1. Clone the repository
2. Analyze source code
3. Write report
4. Submit findings
    """

    steps3 = _extract_steps_from_plan_text(plan3)
    print("\n[Test 3] Regular numbered list:")
    print(f"  Input: {len(plan3)} chars")
    print(f"  Output: {len(steps3)} steps")
    for i, step in enumerate(steps3, 1):
        print(f"    {i}. {step}")

    assert len(steps3) == 4, f"Expected 4 steps, got {len(steps3)}"
    print("  ✅ PASS")

    print("\n✅ All phase extraction tests passed!")


def test_plan_extraction():
    """Test plan extraction from LLM output with **PLAN_COMPLETE** marker"""
    print("\n" + "=" * 60)
    print("TEST 2: Plan Text Extraction")
    print("=" * 60)

    from agents.sub_agents.plan_agent import PlanAgent

    # Create dummy agent to access _extract_plan_text method
    agent = PlanAgent(
        name="test",
        llm_call_func=lambda x: "",
        execute_tool_func=lambda x, y: ""
    )

    # Test 1: **PLAN_COMPLETE** (markdown bold)
    llm_output1 = """Thought: I'll create a comprehensive plan.
Action: spawn_explore(query="find modules")
Observation: Found 15 modules
Thought: Now I have complete context.

**PLAN_COMPLETE**

# Detailed Analysis Plan

## Phase 1 – Setup (5 min)
Clone repository and verify build

## Phase 2 – Analysis (30 min)
Read source files and extract architecture

## Phase 3 – Report (10 min)
Write comprehensive findings
    """

    plan1 = agent._extract_plan_text(llm_output1)
    print("\n[Test 1] **PLAN_COMPLETE** marker:")
    print(f"  Input: {len(llm_output1)} chars")
    print(f"  Output: {len(plan1)} chars")
    print(f"  Preview: {plan1[:100]}...")

    assert "# Detailed Analysis Plan" in plan1, "Plan title missing"
    assert "Phase 1" in plan1, "Phase 1 missing"
    assert "Phase 2" in plan1, "Phase 2 missing"
    print("  ✅ PASS")

    # Test 2: PLAN_COMPLETE: (old format)
    llm_output2 = """Thought: Creating plan...

PLAN_COMPLETE: # Quick Plan

1. Setup
2. Execute
3. Test
    """

    plan2 = agent._extract_plan_text(llm_output2)
    print("\n[Test 2] PLAN_COMPLETE: (old format):")
    print(f"  Input: {len(llm_output2)} chars")
    print(f"  Output: {len(plan2)} chars")
    print(f"  Preview: {plan2[:100]}...")

    assert "# Quick Plan" in plan2, "Plan title missing"
    print("  ✅ PASS")

    # Test 3: [CONTENT] wrapper
    llm_output3 = """[CONTENT] .**PLAN_COMPLETE**

# Analysis Plan

## Overview
This is a test plan
    """

    plan3 = agent._extract_plan_text(llm_output3)
    print("\n[Test 3] [CONTENT] wrapper:")
    print(f"  Input: {len(llm_output3)} chars")
    print(f"  Output: {len(plan3)} chars")
    print(f"  Preview: {plan3[:100]}...")

    assert "# Analysis Plan" in plan3, "Plan title missing"
    assert "## Overview" in plan3, "Overview section missing"
    print("  ✅ PASS")

    print("\n✅ All plan extraction tests passed!")


def test_todotracker_integration():
    """Test TodoTracker integration with phases"""
    print("\n" + "=" * 60)
    print("TEST 3: TodoTracker Integration")
    print("=" * 60)

    from main import TodoTracker

    # Create TodoTracker
    tracker = TodoTracker()

    # Add phases as todos
    todos = [
        {
            "content": "Phase 1: Repository Setup",
            "status": "pending",
            "activeForm": "Setting up repository"
        },
        {
            "content": "Phase 2: Architecture Extraction",
            "status": "pending",
            "activeForm": "Extracting architecture"
        },
        {
            "content": "Phase 3: Deep-Dive",
            "status": "pending",
            "activeForm": "Deep-diving into code"
        }
    ]

    tracker.add_todos(todos)
    print("\n[Test] TodoTracker with 3 phases:")
    print(f"  Added: {len(todos)} todos")

    # Format progress
    progress = tracker.format_progress()
    print(f"\n{progress}")

    # Mark first as in_progress
    tracker.mark_in_progress(0)
    print("\n[Test] Mark Phase 1 as in_progress:")
    print(tracker.format_progress())

    # Mark first as completed
    tracker.mark_completed(0)
    print("\n[Test] Mark Phase 1 as completed:")
    print(tracker.format_progress())

    # Mark second as in_progress
    tracker.mark_in_progress(1)
    print("\n[Test] Mark Phase 2 as in_progress:")
    print(tracker.format_progress())

    print("\n✅ TodoTracker integration test passed!")


def main():
    """Run all tests"""
    print("\n" + "🧪 " * 30)
    print("Plan Mode Fixes - Test Suite")
    print("🧪 " * 30)

    results = []

    # Test 1: Phase Extraction
    try:
        test_phase_extraction()
        results.append(("Phase Extraction", True))
    except Exception as e:
        print(f"\n❌ Phase extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase Extraction", False))

    # Test 2: Plan Extraction
    try:
        test_plan_extraction()
        results.append(("Plan Extraction", True))
    except Exception as e:
        print(f"\n❌ Plan extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Plan Extraction", False))

    # Test 3: TodoTracker Integration
    try:
        test_todotracker_integration()
        results.append(("TodoTracker Integration", True))
    except Exception as e:
        print(f"\n❌ TodoTracker test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("TodoTracker Integration", False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Plan mode fixes are working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Please check the errors above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
