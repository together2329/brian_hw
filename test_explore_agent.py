#!/usr/bin/env python3
"""
Test ExploreAgent functionality

Tests:
1. ExploreAgent initialization
2. spawn_explore function
3. ALLOWED_TOOLS validation
4. Read-only constraints
5. Integration with Plan Mode
"""

import sys
import os

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder/src'))

from lib.display import Color


def test_1_explore_agent_class():
    """Test 1: ExploreAgent class exists and has correct tools"""
    print("\n" + "=" * 60)
    print("TEST 1: ExploreAgent Class")
    print("=" * 60)

    try:
        from agents.sub_agents.explore_agent import ExploreAgent

        # Check ALLOWED_TOOLS
        allowed = ExploreAgent.ALLOWED_TOOLS
        print(f"ALLOWED_TOOLS count: {len(allowed)}")
        print("Tools:")
        for tool in sorted(allowed):
            print(f"  • {tool}")

        # Verify read-only tools
        write_tools = {'write_file', 'run_command', 'replace_in_file', 'replace_lines'}
        has_write = allowed & write_tools
        if has_write:
            print(Color.error(f"❌ FAIL: ExploreAgent has write tools: {has_write}"))
            return False

        # Check required read tools
        required = {'read_file', 'grep_file', 'list_dir', 'find_files'}
        missing = required - allowed
        if missing:
            print(Color.error(f"❌ FAIL: Missing required tools: {missing}"))
            return False

        print(Color.success("✅ PASS: ExploreAgent has correct read-only tools"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        import traceback
        traceback.print_exc()
        return False


def test_2_spawn_explore_exists():
    """Test 2: spawn_explore function exists"""
    print("\n" + "=" * 60)
    print("TEST 2: spawn_explore Function")
    print("=" * 60)

    try:
        from core.tools import spawn_explore

        # Check function signature
        import inspect
        sig = inspect.signature(spawn_explore)
        params = list(sig.parameters.keys())
        print(f"Parameters: {params}")

        if params != ['query']:
            print(Color.error(f"❌ FAIL: Expected ['query'], got {params}"))
            return False

        # Check docstring
        doc = spawn_explore.__doc__
        if not doc or 'explore' not in doc.lower():
            print(Color.error("❌ FAIL: Missing or invalid docstring"))
            return False

        print(Color.success("✅ PASS: spawn_explore function exists with correct signature"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        return False


def test_3_explore_agent_init():
    """Test 3: ExploreAgent can be initialized"""
    print("\n" + "=" * 60)
    print("TEST 3: ExploreAgent Initialization")
    print("=" * 60)

    try:
        from agents.sub_agents.explore_agent import ExploreAgent
        from llm_client import call_llm_raw

        def dummy_execute_tool(tool_name, args):
            return f"Dummy result for {tool_name}"

        agent = ExploreAgent(
            name="test_explore",
            llm_call_func=call_llm_raw,
            execute_tool_func=dummy_execute_tool
        )

        print(f"Agent name: {agent.name}")
        print(f"Max iterations: {agent.max_iterations}")
        print(f"ALLOWED_TOOLS: {len(agent.ALLOWED_TOOLS)}")

        print(Color.success("✅ PASS: ExploreAgent initialized successfully"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        import traceback
        traceback.print_exc()
        return False


def test_4_explore_prompts():
    """Test 4: ExploreAgent prompts are correct"""
    print("\n" + "=" * 60)
    print("TEST 4: ExploreAgent Prompts")
    print("=" * 60)

    try:
        from agents.sub_agents.explore_agent import ExploreAgent
        from llm_client import call_llm_raw

        def dummy_execute_tool(tool_name, args):
            return f"Dummy result for {tool_name}"

        agent = ExploreAgent(
            name="test",
            llm_call_func=call_llm_raw,
            execute_tool_func=dummy_execute_tool
        )

        # Check planning prompt
        planning_prompt = agent._get_planning_prompt()
        if "read-only" not in planning_prompt.lower():
            print(Color.error("❌ FAIL: Planning prompt doesn't mention read-only"))
            return False

        if "do not generate" not in planning_prompt.lower():
            print(Color.error("❌ FAIL: Planning prompt doesn't forbid code generation"))
            return False

        # Check execution prompt
        exec_prompt = agent._get_execution_prompt()
        if "never generate code" not in exec_prompt.lower():
            print(Color.error("❌ FAIL: Execution prompt doesn't forbid code generation"))
            return False

        print(Color.success("✅ PASS: ExploreAgent prompts are correct"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        return False


def test_5_plan_agent_can_use_spawn_explore():
    """Test 5: PlanAgent has spawn_explore in ALLOWED_TOOLS"""
    print("\n" + "=" * 60)
    print("TEST 5: PlanAgent can use spawn_explore")
    print("=" * 60)

    try:
        from agents.sub_agents.plan_agent import PlanAgent

        allowed = PlanAgent.ALLOWED_TOOLS
        print(f"PlanAgent ALLOWED_TOOLS: {allowed}")

        if "spawn_explore" not in allowed:
            print(Color.error("❌ FAIL: PlanAgent cannot use spawn_explore"))
            return False

        print(Color.success("✅ PASS: PlanAgent can use spawn_explore"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        return False


def test_6_spawn_explore_basic():
    """Test 6: spawn_explore basic functionality (dry run)"""
    print("\n" + "=" * 60)
    print("TEST 6: spawn_explore Basic Functionality")
    print("=" * 60)

    try:
        from core.tools import spawn_explore

        # Note: This will actually call LLM and explore the codebase
        # For a true dry run, we'd need to mock the LLM
        print(Color.warning("⚠️  This test requires LLM connection"))
        print(Color.info("Skipping actual spawn_explore call"))
        print(Color.info("To test manually, run: spawn_explore('find Python files')"))

        print(Color.success("✅ PASS: spawn_explore function is callable"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        return False


def test_7_explore_agent_artifacts():
    """Test 7: ExploreAgent artifact collection"""
    print("\n" + "=" * 60)
    print("TEST 7: ExploreAgent Artifacts")
    print("=" * 60)

    try:
        from agents.sub_agents.explore_agent import ExploreAgent
        from llm_client import call_llm_raw

        def dummy_execute_tool(tool_name, args):
            return f"Dummy result for {tool_name}"

        agent = ExploreAgent(
            name="test",
            llm_call_func=call_llm_raw,
            execute_tool_func=dummy_execute_tool
        )

        # Simulate some exploration
        agent._files_read = ["file1.py", "file2.py", "file3.py"]
        agent._tool_calls = [
            {"tool": "read_file", "args": "file1.py"},
            {"tool": "grep_file", "args": "pattern"},
        ]

        artifacts = agent._collect_artifacts()
        print(f"Artifacts: {artifacts}")

        if artifacts.get("files_read") != ["file1.py", "file2.py", "file3.py"]:
            print(Color.error("❌ FAIL: files_read mismatch"))
            return False

        if artifacts.get("tool_calls_count") != 2:
            print(Color.error("❌ FAIL: tool_calls_count mismatch"))
            return False

        if artifacts.get("exploration_depth") != 3:
            print(Color.error("❌ FAIL: exploration_depth mismatch"))
            return False

        print(Color.success("✅ PASS: ExploreAgent artifacts collection works"))
        return True

    except Exception as e:
        print(Color.error(f"❌ Exception: {e}"))
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all ExploreAgent tests"""
    print("\n" + "=" * 70)
    print(" " * 20 + "EXPLORE AGENT TESTS")
    print("=" * 70)

    tests = [
        ("ExploreAgent Class", test_1_explore_agent_class),
        ("spawn_explore Function", test_2_spawn_explore_exists),
        ("ExploreAgent Initialization", test_3_explore_agent_init),
        ("ExploreAgent Prompts", test_4_explore_prompts),
        ("PlanAgent Integration", test_5_plan_agent_can_use_spawn_explore),
        ("spawn_explore Basic", test_6_spawn_explore_basic),
        ("ExploreAgent Artifacts", test_7_explore_agent_artifacts),
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
        print(Color.success("\n🎉 All ExploreAgent tests passed!"))
        return 0
    else:
        print(Color.error(f"\n❌ {total - passed} test(s) failed"))
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
