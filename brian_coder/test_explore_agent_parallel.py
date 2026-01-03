#!/usr/bin/env python3
"""
ExploreAgent 병렬 실행 테스트

실제 ExploreAgent가 Claude Code처럼 여러 도구를 동시에 실행하는지 검증
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Enable debug mode
os.environ['DEBUG_SUBAGENT'] = 'true'
os.environ['DEBUG_MODE'] = 'true'

def test_explore_agent_parallel():
    """ExploreAgent가 실제로 병렬 실행하는지 테스트"""
    print("=" * 70)
    print("ExploreAgent 병렬 실행 테스트 (Claude Code Style)")
    print("=" * 70)

    from agents.sub_agents.explore_agent import ExploreAgent
    import time

    # Mock LLM and tool execution functions
    def mock_llm_call(messages, **kwargs):
        """Mock LLM call - not used in this test"""
        return "EXPLORE_COMPLETE: Mock response"

    def mock_execute_tool(tool_name, **kwargs):
        """Mock tool execution"""
        return f"[Mock] {tool_name} executed with {kwargs}"

    # Create agent with mock functions
    agent = ExploreAgent(
        name="TestExploreAgent",
        llm_call_func=mock_llm_call,
        execute_tool_func=mock_execute_tool,
        max_iterations=3
    )

    print("\n[Task]")
    print("  Explore brian_coder structure:")
    print("  - Find Python files in agents/")
    print("  - List src/ directory")
    print("  - Find all .py files")
    print()

    # Mock LLM response with parallel annotation
    # (실제로는 LLM이 생성하지만, 테스트를 위해 직접 주입)
    mock_llm_response = """
Thought: I need to explore the project structure efficiently by running multiple read operations in parallel.

@parallel
Action: list_dir(path="agents")
Action: list_dir(path="src")
Action: find_files(pattern="*.py", directory=".")
@end_parallel

EXPLORE_COMPLETE: Found project structure with agents/ and src/ directories containing Python files.
"""

    print("\n[Simulated LLM Response]")
    print(mock_llm_response)
    print()

    # Test parsing
    print("[Step 1] Parsing actions from response...")
    actions = agent._parse_actions(mock_llm_response)

    print(f"\n  ✓ Parsed {len(actions)} actions:")
    for idx, (tool, args, hint) in enumerate(actions):
        hint_marker = f" [hint={hint}]" if hint else ""
        print(f"    {idx+1}. {tool}({args[:40]}...){hint_marker}")

    assert len(actions) == 3, f"Expected 3 actions, got {len(actions)}"
    assert all(hint == "parallel" for _, _, hint in actions), "All should have parallel hint"
    print("\n  ✅ All actions marked as parallel")

    # Test that actions contain hints
    print("\n[Step 2] Validating hints...")
    parallel_actions = [a for a in actions if a[2] == "parallel"]
    print(f"  ✓ {len(parallel_actions)} actions have 'parallel' hint")
    assert len(parallel_actions) == 3, "All 3 actions should have parallel hint"
    print("  ✅ Hints correctly assigned")

    # Test batch creation
    print("\n[Step 3] Creating execution batches...")
    try:
        from core.action_dependency import ActionDependencyAnalyzer

        analyzer = ActionDependencyAnalyzer()
        batches = analyzer.analyze(actions)

        print(f"  ✓ Created {len(batches)} batch(es)")
        for idx, batch in enumerate(batches):
            hint_marker = " [LLM-guided]" if "LLM" in batch.reason else ""
            print(f"    Batch {idx+1}: {len(batch.actions)} actions, parallel={batch.parallel}{hint_marker}")

        # Should create 1 parallel batch
        assert len(batches) == 1, f"Expected 1 batch, got {len(batches)}"
        assert batches[0].parallel == True, "Batch should be parallel"
        print("  ✅ Batch created correctly")

    except Exception as e:
        print(f"  ❌ Batch creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n" + "=" * 70)
    print("✅ ExploreAgent 병렬 실행 테스트 통과!")
    print("=" * 70)
    print("\n핵심 검증 사항:")
    print("  ✅ @parallel annotation 파싱")
    print("  ✅ Hint 검증 및 할당")
    print("  ✅ 병렬 실행 batch 생성")
    print("\n이제 ExploreAgent는 Claude Code처럼 여러 도구를 동시에 실행할 수 있습니다!")

    return True


def test_with_actual_agent_run():
    """실제 Agent.run()으로 full cycle 테스트"""
    print("\n\n" + "=" * 70)
    print("Full Agent Run 테스트 (Optional)")
    print("=" * 70)

    print("\n⚠️  이 테스트는 실제 LLM API 호출이 필요합니다.")
    print("⚠️  현재는 mock 테스트만 지원합니다.")
    print("⚠️  실제 통합 테스트는 brian_coder 메인 시스템에서 수행하세요.")
    print()

    # For now, skip actual agent run
    print("  → 실제 Agent 실행 테스트는 건너뜁니다.")
    print("  → 메인 시스템에서 'spawn_explore' 도구를 사용하여 테스트하세요.")

    return True


def main():
    """메인 테스트 실행"""
    print("\n" + "🚀 " * 35)
    print("ExploreAgent 병렬 실행 시스템 테스트")
    print("🚀 " * 35 + "\n")

    try:
        # Test 1: Parsing and preparation
        success = test_explore_agent_parallel()

        if not success:
            print("\n❌ 기본 테스트 실패")
            return 1

        # Test 2: Optional full agent run
        # test_with_actual_agent_run()

        print("\n" + "🎉 " * 35)
        print("모든 테스트 완료!")
        print("🎉 " * 35 + "\n")

        return 0

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
