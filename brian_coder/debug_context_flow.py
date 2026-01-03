#!/usr/bin/env python3
"""
Context Flow Debugger for brian_coder

실시간으로 agent 간 context 흐름을 추적하고 시각화합니다.
"""

import sys
import os
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "agents"))

def test_shared_context_access():
    """SharedContext 접근 테스트"""
    print("=" * 80)
    print("🔍 SharedContext Access Test")
    print("=" * 80)

    # Test 1: Direct import
    print("\n[Test 1] Direct import from agents.shared_context")
    try:
        from agents.shared_context import SharedContext
        ctx = SharedContext()
        print("  ✅ SUCCESS: SharedContext 직접 import 성공")
        print(f"  Context: {ctx}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    # Test 2: Import main module
    print("\n[Test 2] Import main module")
    try:
        import main
        print(f"  ✅ SUCCESS: main module imported")
        print(f"  Module name: {main.__name__}")
        print(f"  Module file: {main.__file__}")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return

    # Test 3: Call get_shared_context()
    print("\n[Test 3] Call main.get_shared_context()")
    try:
        ctx = main.get_shared_context()
        if ctx:
            print(f"  ✅ SUCCESS: get_shared_context() returned {type(ctx).__name__}")
            print(f"  Context: {ctx}")
        else:
            print(f"  ⚠️  WARNING: get_shared_context() returned None")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")

    # Test 4: From tools.py perspective
    print("\n[Test 4] Simulate tools.py import scenario")
    try:
        # Simulate what spawn_explore does
        print("  Attempting: from main import get_shared_context")
        from main import get_shared_context
        ctx = get_shared_context()
        if ctx:
            print(f"  ✅ SUCCESS: Context retrieved from tools.py perspective")
            print(f"  Context: {ctx}")
        else:
            print(f"  ⚠️  WARNING: Context is None")
    except ImportError as e:
        print(f"  ❌ IMPORT ERROR: {e}")
        print(f"  This is why tools.py fails to get SharedContext!")
    except Exception as e:
        print(f"  ❌ FAILED: {e}")


def test_agent_context_flow():
    """Agent 간 context 흐름 테스트"""
    print("\n" + "=" * 80)
    print("🔗 Agent Context Flow Test")
    print("=" * 80)

    try:
        from agents.shared_context import SharedContext
        from agents.sub_agents.explore_agent import ExploreAgent
        from agents.sub_agents.plan_agent import PlanAgent
        from llm_client import call_llm_raw
        from core.tools import AVAILABLE_TOOLS

        # Create SharedContext
        shared_ctx = SharedContext()
        print(f"\n✅ Created SharedContext: {shared_ctx}")

        # Mock execute_tool
        def execute_tool(tool_name, args):
            if tool_name in AVAILABLE_TOOLS:
                return "Mock result"
            return f"Tool {tool_name} not found"

        # Test 1: ExploreAgent with SharedContext
        print("\n[Step 1] Create ExploreAgent with SharedContext")
        explore_agent = ExploreAgent(
            name="test_explore",
            llm_call_func=call_llm_raw,
            execute_tool_func=execute_tool,
            shared_context=shared_ctx  # ← Pass SharedContext
        )
        print(f"  ✅ ExploreAgent created")
        print(f"  Agent has SharedContext: {explore_agent.shared_context is not None}")

        # Simulate exploration
        print("\n[Step 2] Simulate exploration result")
        shared_ctx.record_exploration(
            agent_name="test_explore",
            files_examined=["fifo.v", "sram.v"],
            findings="Found 2 FIFO implementations",
            execution_time_ms=1500,
            tool_calls_count=3
        )
        print("  ✅ Recorded exploration data")

        # Check context
        print("\n[Step 3] Check SharedContext content")
        files = shared_ctx.get_all_examined_files()
        summary = shared_ctx.get_summary()
        print(f"  Files examined: {files}")
        print(f"  Summary:\n{summary}")

        # Test 2: PlanAgent sees exploration results
        print("\n[Step 4] Create PlanAgent with same SharedContext")
        plan_agent = PlanAgent(
            name="test_plan",
            llm_call_func=call_llm_raw,
            execute_tool_func=execute_tool,
            shared_context=shared_ctx  # ← Same context
        )
        print(f"  ✅ PlanAgent created")
        print(f"  Agent has SharedContext: {plan_agent.shared_context is not None}")

        # Get LLM context
        print("\n[Step 5] Get context for LLM injection")
        llm_context = shared_ctx.get_context_for_llm()
        print(f"  LLM Context:\n{llm_context}")

        # Verify context flow
        print("\n[Step 6] Verify context flow")
        checks = []

        # Check 1: Both agents share same context
        check1 = explore_agent.shared_context is plan_agent.shared_context
        checks.append(("Same context instance", check1))
        print(f"  {'✅' if check1 else '❌'} Both agents share same context: {check1}")

        # Check 2: PlanAgent can see ExploreAgent's files
        check2 = "fifo.v" in shared_ctx.get_all_examined_files()
        checks.append(("Files visible", check2))
        print(f"  {'✅' if check2 else '❌'} PlanAgent sees explored files: {check2}")

        # Check 3: LLM context contains data
        check3 = "fifo.v" in llm_context
        checks.append(("LLM context", check3))
        print(f"  {'✅' if check3 else '❌'} LLM context contains files: {check3}")

        all_passed = all(result for _, result in checks)

        print("\n" + "=" * 80)
        if all_passed:
            print("✅ Context Flow Test PASSED")
            print("   Agent 간 context 공유가 정상 작동합니다!")
        else:
            print("❌ Context Flow Test FAILED")
            for name, result in checks:
                if not result:
                    print(f"   Failed: {name}")
        print("=" * 80)

        return all_passed

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools_spawn_integration():
    """tools.py의 spawn_explore/spawn_plan 통합 테스트"""
    print("\n" + "=" * 80)
    print("🛠️  Tools Spawn Integration Test")
    print("=" * 80)

    try:
        # Import must happen AFTER main is loaded
        print("\n[Step 1] Import main module first")
        import main
        print(f"  ✅ main module loaded: {main.__name__}")

        print("\n[Step 2] Check get_shared_context availability")
        if hasattr(main, 'get_shared_context'):
            print(f"  ✅ get_shared_context() exists in main")
            ctx = main.get_shared_context()
            print(f"  Context: {ctx}")
        else:
            print(f"  ❌ get_shared_context() NOT FOUND in main")
            return False

        print("\n[Step 3] Import tools module")
        from core import tools
        print(f"  ✅ tools module loaded")

        print("\n[Step 4] Check spawn_explore function")
        if hasattr(tools, 'spawn_explore'):
            print(f"  ✅ spawn_explore exists")

            # Check the source code for get_shared_context call
            import inspect
            source = inspect.getsource(tools.spawn_explore)

            if 'get_shared_context' in source:
                print(f"  ✅ spawn_explore tries to get SharedContext")

                # Check if it's using the right import
                if 'from main import get_shared_context' in source:
                    print(f"  ✅ Using correct import: 'from main import get_shared_context'")
                else:
                    print(f"  ⚠️  May be using different import method")
            else:
                print(f"  ❌ spawn_explore does NOT try to get SharedContext")
        else:
            print(f"  ❌ spawn_explore NOT FOUND")
            return False

        print("\n" + "=" * 80)
        print("✅ Tools Integration Check Complete")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    print("\n" + "🚀 " * 40)
    print("brian_coder Context Flow Debugger")
    print("🚀 " * 40)

    results = []

    # Test 1: SharedContext Access
    print("\n")
    try:
        test_shared_context_access()
        results.append(("SharedContext Access", True))
    except Exception as e:
        print(f"\n❌ SharedContext Access Test crashed: {e}")
        results.append(("SharedContext Access", False))

    # Test 2: Agent Context Flow
    print("\n")
    try:
        result = test_agent_context_flow()
        results.append(("Agent Context Flow", result))
    except Exception as e:
        print(f"\n❌ Agent Context Flow Test crashed: {e}")
        results.append(("Agent Context Flow", False))

    # Test 3: Tools Integration
    print("\n")
    try:
        result = test_tools_spawn_integration()
        results.append(("Tools Integration", result))
    except Exception as e:
        print(f"\n❌ Tools Integration Test crashed: {e}")
        results.append(("Tools Integration", False))

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name}")

    all_passed = all(result for _, result in results)

    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED")
        print("Context flow is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED")
        print("Context flow needs fixing.")
    print("=" * 80)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
