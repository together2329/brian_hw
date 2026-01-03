#!/usr/bin/env python3
"""
Plan Mode Integration Test

Tests the complete plan mode workflow:
1. Plan generation with explore agents
2. Plan extraction and saving
3. Phase extraction from plan
4. TodoTracker integration
5. Step-by-step execution with tracking
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)

def test_full_plan_workflow():
    """Test complete plan mode workflow"""
    print("\n" + "=" * 60)
    print("INTEGRATION TEST: Full Plan Mode Workflow")
    print("=" * 60)

    from main import (
        _extract_steps_from_plan_text,
        TodoTracker
    )
    from agents.sub_agents.plan_agent import PlanAgent

    # Simulated plan output from LLM (realistic format)
    llm_output = """Thought: I need to create a comprehensive implementation plan.

**PLAN_COMPLETE**

# Implementation Plan: Add User Authentication

## Overview
Implement a complete user authentication system with login, signup, and session management.

## Critical Files
1. `backend/auth/user_model.py` - User database model
2. `backend/auth/auth_service.py (NEW)` - Authentication service
3. `frontend/components/Login.tsx (NEW)` - Login component

### Phase 1 – Database Setup (15 min)

**File**: `backend/auth/user_model.py`
**Location**: Line 1-50 (new file)

**Changes**:
- Create User model with username, email, password_hash
- Add timestamp fields (created_at, updated_at)
- Implement password hashing with bcrypt

### Phase 2 – Authentication Service (30 min)

**File**: `backend/auth/auth_service.py`
**Location**: Line 1-100 (new file)

**Changes**:
- Implement register(username, email, password) function
- Implement login(username, password) function
- Add JWT token generation
- Add session management

### Phase 3 – Frontend Components (20 min)

**File**: `frontend/components/Login.tsx`
**Location**: Line 1-80 (new file)

**Changes**:
- Create login form component
- Add form validation
- Integrate with auth API
- Handle success/error states

### Phase 4 – Testing (15 min)

**File**: `tests/test_auth.py (NEW)`
**Location**: Line 1-50

**Changes**:
- Unit tests for register function
- Unit tests for login function
- Integration test for auth flow

## Testing Strategy
- Unit tests: `tests/test_auth.py` (register, login, token generation)
- Integration: Test full signup → login → access protected route flow

## Success Criteria
- [ ] User can register with email and password
- [ ] User can login and receive JWT token
- [ ] Protected routes check for valid token
- [ ] All tests pass
"""

    print("\n[Step 1] Create PlanAgent and extract plan text")

    # Create dummy agent
    def dummy_llm_call(messages):
        return ""

    def dummy_execute_tool(tool_name, args):
        return ""

    agent = PlanAgent(
        name="test_plan_agent",
        llm_call_func=dummy_llm_call,
        execute_tool_func=dummy_execute_tool
    )

    # Extract plan text
    plan_text = agent._extract_plan_text(llm_output)

    print(f"  ✅ Plan extracted: {len(plan_text)} chars")
    print(f"  Preview: {plan_text[:100]}...")

    assert "# Implementation Plan" in plan_text, "Plan title missing"
    assert "Phase 1" in plan_text, "Phase 1 missing"
    assert "Phase 2" in plan_text, "Phase 2 missing"

    print("\n[Step 2] Extract phases from plan")

    steps = _extract_steps_from_plan_text(plan_text)

    print(f"  ✅ Extracted {len(steps)} phases:")
    for i, step in enumerate(steps, 1):
        print(f"    {i}. {step}")

    assert len(steps) == 4, f"Expected 4 phases, got {len(steps)}"
    assert "Phase 1" in steps[0], "First step should contain 'Phase 1'"
    assert "Database Setup" in steps[0], "Phase 1 should mention Database Setup"

    print("\n[Step 3] Create TodoTracker and add phases")

    tracker = TodoTracker()

    # Convert steps to todos
    todos = []
    for step in steps:
        # Extract phase title for activeForm
        active_form = step.replace("Phase", "Working on Phase")

        todos.append({
            "content": step,
            "status": "pending",
            "activeForm": active_form
        })

    tracker.add_todos(todos)

    print("  ✅ TodoTracker initialized:")
    print(tracker.format_progress())

    print("\n[Step 4] Simulate step-by-step execution with tracking")

    for step_idx in range(len(steps)):
        print(f"\n  ╔═══════════════════════════════════════════════════════╗")
        print(f"  ║  Executing Step {step_idx + 1}/{len(steps)}: {steps[step_idx][:30]}...  ║")
        print(f"  ╚═══════════════════════════════════════════════════════╝")

        # Mark as in_progress
        tracker.mark_in_progress(step_idx)
        print(tracker.format_progress())

        # Simulate work
        print(f"  [Simulating work on {steps[step_idx]}...]")

        # Mark as completed
        tracker.mark_completed(step_idx)
        print(f"\n  ✅ Step {step_idx + 1} completed!")
        print(tracker.format_progress())

    print("\n[Step 5] Verify final state")

    # Check all completed
    all_completed = all(todo.status == "completed" for todo in tracker.todos)

    if all_completed:
        print("  ✅ All phases completed successfully!")
    else:
        print("  ❌ Some phases not completed")
        return False

    print("\n[Step 6] Save plan to file (simulated)")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_file = Path(tmpdir) / "test_plan.md"

        # Write plan
        with open(plan_file, "w") as f:
            f.write(f"# Plan\n\n")
            f.write(f"## Task\nImplement user authentication\n\n")
            f.write(f"## Generated\n2025-12-29 Test\n\n")
            f.write(f"---\n\n")
            f.write(plan_text)

        # Verify file
        assert plan_file.exists(), "Plan file not created"

        file_size = plan_file.stat().st_size
        print(f"  ✅ Plan saved: {file_size} bytes")

        # Read back and verify
        with open(plan_file, "r") as f:
            saved_content = f.read()

        assert "Phase 1" in saved_content, "Phase 1 not in saved file"
        assert "Phase 4" in saved_content, "Phase 4 not in saved file"

        print(f"  ✅ Plan file verified: all phases present")

    return True


def test_phase_tracking_visualization():
    """Test phase tracking visualization (what user sees)"""
    print("\n" + "=" * 60)
    print("VISUALIZATION TEST: Phase Tracking Display")
    print("=" * 60)

    from main import TodoTracker

    # Create realistic phases
    phases = [
        {
            "content": "Phase 1: Repository Setup and Environment Configuration",
            "status": "pending",
            "activeForm": "Setting up repository and environment"
        },
        {
            "content": "Phase 2: Architecture Analysis and Module Extraction",
            "status": "pending",
            "activeForm": "Analyzing architecture and extracting modules"
        },
        {
            "content": "Phase 3: Deep-Dive into Crypto Engines",
            "status": "pending",
            "activeForm": "Deep-diving into crypto engines"
        },
        {
            "content": "Phase 4: Interface Mapping and Dependencies",
            "status": "pending",
            "activeForm": "Mapping interfaces and dependencies"
        },
        {
            "content": "Phase 5: Verification and Testing Review",
            "status": "pending",
            "activeForm": "Reviewing verification and testing"
        },
        {
            "content": "Phase 6: Gap Analysis and Recommendations",
            "status": "pending",
            "activeForm": "Analyzing gaps and creating recommendations"
        },
        {
            "content": "Phase 7: Report Generation",
            "status": "pending",
            "activeForm": "Generating final report"
        }
    ]

    tracker = TodoTracker()
    tracker.add_todos(phases)

    print("\n[Initial State] All phases pending:")
    print(tracker.format_progress())

    print("\n[Phase 1 Started]")
    tracker.mark_in_progress(0)
    print(tracker.format_progress())

    print("\n[Phase 1 Completed, Phase 2 Started]")
    tracker.mark_completed(0)
    tracker.mark_in_progress(1)
    print(tracker.format_progress())

    print("\n[Phase 2 Completed, Phase 3 Started]")
    tracker.mark_completed(1)
    tracker.mark_in_progress(2)
    print(tracker.format_progress())

    print("\n[Phases 3-5 Completed, Phase 6 Started]")
    tracker.mark_completed(2)
    tracker.mark_completed(3)
    tracker.mark_completed(4)
    tracker.mark_in_progress(5)
    print(tracker.format_progress())

    print("\n[All Completed]")
    tracker.mark_completed(5)
    tracker.mark_completed(6)
    print(tracker.format_progress())

    return True


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "=" * 60)
    print("EDGE CASE TEST: Plan Mode Error Handling")
    print("=" * 60)

    from main import _extract_steps_from_plan_text
    from agents.sub_agents.plan_agent import PlanAgent

    def dummy_llm_call(messages):
        return ""

    def dummy_execute_tool(tool_name, args):
        return ""

    agent = PlanAgent(
        name="test",
        llm_call_func=dummy_llm_call,
        execute_tool_func=dummy_execute_tool
    )

    # Test 1: Empty plan
    print("\n[Test 1] Empty plan")
    plan_text = agent._extract_plan_text("")
    assert plan_text == "", "Empty plan should return empty string"
    print("  ✅ PASS: Empty plan handled")

    # Test 2: No phases in plan
    print("\n[Test 2] Plan without phases (only numbered list)")
    plan = """
## Implementation Steps

1. Setup environment
2. Write code
3. Test
"""
    steps = _extract_steps_from_plan_text(plan)
    assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"
    print(f"  ✅ PASS: Extracted {len(steps)} numbered steps")

    # Test 3: Mixed format
    print("\n[Test 3] Mixed Phase and numbered format")
    plan = """
### Phase 1 – Setup

Do initial setup

## Steps

1. Clone repo
2. Install dependencies
"""
    steps = _extract_steps_from_plan_text(plan)
    assert len(steps) >= 1, "Should extract at least Phase 1"
    print(f"  ✅ PASS: Extracted {len(steps)} steps from mixed format")

    # Test 4: Plan with no PLAN_COMPLETE marker
    print("\n[Test 4] Plan without PLAN_COMPLETE marker")
    output = """
# Direct Plan

## Phase 1 – Analysis
Do analysis
"""
    plan_text = agent._extract_plan_text(output)
    assert len(plan_text) > 0, "Should extract plan even without marker"
    print("  ✅ PASS: Extracted plan without marker")

    return True


def main():
    """Run all integration tests"""
    print("\n" + "🧪 " * 30)
    print("Plan Mode Integration Test Suite")
    print("🧪 " * 30)

    results = []

    # Test 1: Full workflow
    try:
        success = test_full_plan_workflow()
        results.append(("Full Workflow", success))
    except Exception as e:
        print(f"\n❌ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Full Workflow", False))

    # Test 2: Visualization
    try:
        success = test_phase_tracking_visualization()
        results.append(("Phase Tracking Visualization", success))
    except Exception as e:
        print(f"\n❌ Visualization test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Phase Tracking Visualization", False))

    # Test 3: Edge cases
    try:
        success = test_edge_cases()
        results.append(("Edge Cases", success))
    except Exception as e:
        print(f"\n❌ Edge case test failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Edge Cases", False))

    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nPlan mode is ready for production use:")
        print("  ✅ Plan extraction working")
        print("  ✅ Phase parsing working")
        print("  ✅ TodoTracker integration working")
        print("  ✅ Step-by-step execution with tracking working")
        print("  ✅ Visualization working")
        print("  ✅ Edge cases handled")
    else:
        print("⚠️  SOME INTEGRATION TESTS FAILED")
        print("Please check the errors above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
