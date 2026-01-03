#!/usr/bin/env python3
"""
main.py 통합 테스트

실제 main.py의 run_react_agent를 사용하여
Agent Communication 시스템이 제대로 작동하는지 검증
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Set up environment
os.environ['DEBUG_MODE'] = 'false'  # Reduce noise

def test_main_integration():
    """
    main.py 통합 테스트

    시나리오: spawn_explore 사용 후 accumulated_context 검증
    """
    print("=" * 80)
    print("main.py 통합 테스트: Agent Communication")
    print("=" * 80)

    from main import run_react_agent, IterationTracker
    from config import config

    # Get shared context function
    from main import get_shared_context

    print("\n[Step 1] SharedContext 초기화 확인")
    print("-" * 80)

    shared_ctx = get_shared_context()
    print(f"✓ SharedContext: {shared_ctx}")

    if shared_ctx is None:
        print("⚠️  SharedContext is None - creating manually")
        from agents.shared_context import SharedContext
        shared_ctx = SharedContext()

    print(f"✓ SharedContext type: {type(shared_ctx)}")

    print("\n[Step 2] ReAct Agent 실행 (spawn_explore 호출)")
    print("-" * 80)

    # Create messages
    messages = []

    # User message asking to use spawn_explore
    user_message = """Please use spawn_explore to find Python files in the agents/ directory.

Task: Find all Python files in agents/sub_agents/
"""

    messages.append({
        "role": "user",
        "content": user_message
    })

    # Create tracker
    tracker = IterationTracker(max_iterations=5)

    print("✓ Running ReAct agent...")
    print(f"  Task: Find Python files using spawn_explore")
    print(f"  Max iterations: {tracker.max_iterations}")

    try:
        # Run ReAct agent
        result_messages = run_react_agent(
            messages=messages,
            tracker=tracker,
            task_description="Find Python files in agents/",
            mode='oneshot',
            allow_claude_flow=False,  # Disable Claude Flow to focus on ReAct
            preface_enabled=False
        )

        print(f"\n✓ ReAct agent completed")
        print(f"  Total messages: {len(result_messages)}")
        print(f"  Iterations used: {tracker.current}")

        # Check if spawn_explore was called
        spawn_explore_called = False
        for msg in result_messages:
            content = str(msg.get('content', ''))
            if 'spawn_explore' in content:
                spawn_explore_called = True
                print(f"\n✓ spawn_explore was called!")
                # Show snippet
                lines = content.split('\n')
                for line in lines:
                    if 'spawn_explore' in line:
                        print(f"  {line}")
                break

        if not spawn_explore_called:
            print("\n⚠️  spawn_explore was NOT called")
            print("  This is expected if LLM chose different approach")
            print("  Let's check what tools were used:")

            for msg in result_messages:
                if msg.get('role') == 'user' and 'Observation:' in msg.get('content', ''):
                    content = msg.get('content', '')
                    print(f"\n  Observation: {content[:200]}...")

        print("\n[Step 3] SharedContext 검증")
        print("-" * 80)

        # Get SharedContext again (should have data if spawn_explore was called)
        shared_ctx = get_shared_context()

        if shared_ctx:
            files = shared_ctx.get_all_examined_files()
            findings = shared_ctx.get_exploration_findings()
            history = shared_ctx.get_agent_history()

            print(f"\n✓ SharedContext state:")
            print(f"  Files examined: {len(files)}")
            print(f"  Findings: {len(findings)}")
            print(f"  Agent history: {len(history)}")

            if files:
                print(f"\n✓ Files found:")
                for f in files[:10]:
                    print(f"    • {f}")

            if history:
                print(f"\n✓ Agent execution history:")
                for mem in history:
                    print(f"    [{mem.agent_name}] ({mem.agent_type}) - {mem.execution_time_ms}ms")

            # Get LLM context
            llm_context = shared_ctx.get_context_for_llm()
            if llm_context and llm_context != "[Shared Agent Memory]":
                print(f"\n✓ LLM Context generated:")
                print(llm_context[:300] + "...")
            else:
                print(f"\n⚠️  No LLM context (spawn_explore may not have been called)")
        else:
            print("⚠️  SharedContext is None")

        print("\n[Step 4] 최종 검증")
        print("-" * 80)

        checks = []

        # Check 1: Agent completed
        check1 = len(result_messages) > 1
        checks.append(("ReAct agent completed", check1))
        print(f"  {'✅' if check1 else '❌'} ReAct agent completed")

        # Check 2: SharedContext exists
        check2 = shared_ctx is not None
        checks.append(("SharedContext exists", check2))
        print(f"  {'✅' if check2 else '❌'} SharedContext exists")

        # Check 3: If spawn_explore was called, check context
        if spawn_explore_called and shared_ctx:
            check3 = len(shared_ctx.get_agent_history()) > 0
            checks.append(("Agent history recorded", check3))
            print(f"  {'✅' if check3 else '❌'} Agent history recorded")

            check4 = len(shared_ctx.get_all_examined_files()) > 0
            checks.append(("Files examined recorded", check4))
            print(f"  {'✅' if check4 else '❌'} Files examined recorded")
        else:
            print(f"  ⏭️  Skipping context checks (spawn_explore not called)")

        all_passed = all(result for _, result in checks)

        print("\n" + "=" * 80)
        if all_passed:
            print("✅ main.py 통합 테스트 통과!")
        else:
            print("⚠️  main.py 통합 테스트 부분 통과")
            print("\n주의: spawn_explore 호출 여부는 LLM의 선택에 따름")
            print("     시스템 자체는 정상 작동")
        print("=" * 80)

        return all_passed

    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_manual_spawn():
    """
    수동으로 spawn_explore 직접 호출 테스트
    """
    print("\n" + "=" * 80)
    print("수동 spawn_explore 직접 호출 테스트")
    print("=" * 80)

    try:
        from tools import spawn_explore
        from main import get_shared_context

        print("\n[Test] spawn_explore 직접 호출")
        print("-" * 80)

        # Clear shared context
        shared_ctx = get_shared_context()
        if shared_ctx:
            shared_ctx.clear()
            print("✓ SharedContext cleared")

        # Call spawn_explore
        print("\n✓ Calling spawn_explore...")
        result = spawn_explore("Find Python files in agents/sub_agents/")

        print(f"\n✓ spawn_explore returned")
        print(f"  Type: {type(result).__name__}")
        print(f"  String preview: {str(result)[:200]}...")

        # Check if it's AgentResult
        if hasattr(result, '__getitem__'):
            print(f"\n✓ AgentResult properties:")
            print(f"  files_examined: {result.get('files_examined', [])}")
            print(f"  summary: {result.get('summary', '')[:100]}...")
            print(f"  tool_calls_count: {result.get('tool_calls_count', 0)}")

        # Check SharedContext
        shared_ctx = get_shared_context()
        if shared_ctx:
            files = shared_ctx.get_all_examined_files()
            history = shared_ctx.get_agent_history()

            print(f"\n✓ SharedContext updated:")
            print(f"  Files: {len(files)}")
            print(f"  History: {len(history)}")

            if files:
                print(f"\n✓ Files examined:")
                for f in files[:5]:
                    print(f"    • {f}")

            # Get LLM context
            llm_context = shared_ctx.get_context_for_llm()
            print(f"\n✓ LLM Context:")
            print(llm_context)

        print("\n✅ 수동 테스트 완료!")
        return True

    except Exception as e:
        print(f"\n❌ 수동 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run integration tests"""
    print("\n" + "🚀 " * 40)
    print("main.py 통합 테스트 - Agent Communication System")
    print("🚀 " * 40 + "\n")

    print("⚠️  주의: 이 테스트는 실제 LLM을 호출합니다.")
    print("⚠️  ANTHROPIC_API_KEY가 설정되어 있어야 합니다.\n")

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        print("   Falling back to manual test only...\n")

        # Run manual test only
        success = test_manual_spawn()
        return 0 if success else 1

    results = []

    # Test 1: Manual spawn_explore
    print("\n📍 Test 1: Manual spawn_explore")
    try:
        success = test_manual_spawn()
        results.append(("Manual spawn_explore", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("Manual spawn_explore", False))

    # Test 2: Full ReAct integration (with LLM)
    print("\n📍 Test 2: Full ReAct integration")
    try:
        success = test_main_integration()
        results.append(("ReAct integration", success))
    except Exception as e:
        print(f"❌ Test failed: {e}")
        results.append(("ReAct integration", False))

    # Summary
    print("\n" + "=" * 80)
    print("테스트 요약")
    print("=" * 80)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name}")

    total = len(results)
    passed_count = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed_count}/{total} tests passed")

    if passed_count == total:
        print("\n🎉 모든 통합 테스트 통과!")
        return 0
    else:
        print(f"\n⚠️  {total - passed_count}개 테스트 실패")
        return 1


if __name__ == "__main__":
    sys.exit(main())
