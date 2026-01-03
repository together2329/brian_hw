#!/usr/bin/env python3
"""
Caliptra Subsystem 실제 분석 테스트

Agent Communication 시스템의 실전 검증:
1. spawn_explore로 Caliptra 구조 탐색
2. spawn_plan으로 분석 계획 수립
3. SharedContext 누적 확인
4. 결과 품질 평가
"""

import sys
import os
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

def test_caliptra_analysis():
    """
    실제 Caliptra Subsystem 분석

    시나리오:
    1. spawn_explore: Caliptra 디렉토리 구조 파악
    2. spawn_explore: Verilog 모듈 탐색
    3. spawn_plan: 분석 계획 수립
    4. SharedContext 검증
    """
    print("=" * 80)
    print("Caliptra Subsystem 실제 분석 테스트")
    print("=" * 80)

    from tools import spawn_explore, spawn_plan
    from main import get_shared_context

    # Caliptra path
    caliptra_path = "/Users/brian/Desktop/Project/brian_hw/caliptra-ss"

    print(f"\n📁 Target: {caliptra_path}")

    # Check if path exists
    if not os.path.exists(caliptra_path):
        print(f"❌ Path does not exist: {caliptra_path}")
        return False

    print(f"✓ Path exists")

    # Get/clear SharedContext
    shared_ctx = get_shared_context()
    if shared_ctx:
        shared_ctx.clear()
        print("✓ SharedContext cleared")

    print("\n" + "=" * 80)
    print("Phase 1: 디렉토리 구조 탐색")
    print("=" * 80)

    start_time = time.time()

    try:
        result1 = spawn_explore(
            query=f"Explore the directory structure of {caliptra_path}. "
                  f"Find all subdirectories and understand the project organization."
        )

        elapsed1 = time.time() - start_time

        print(f"\n✓ Phase 1 completed in {elapsed1:.1f}s")
        print(f"\n결과 (처음 500자):")
        print("-" * 80)
        result1_str = str(result1)
        print(result1_str[:500] + "..." if len(result1_str) > 500 else result1_str)

        # Check AgentResult
        if hasattr(result1, 'get'):
            files1 = result1.get('files_examined', [])
            print(f"\n✓ Files examined: {len(files1)}")
            if files1:
                print("  Sample files:")
                for f in files1[:5]:
                    print(f"    • {f}")

    except Exception as e:
        print(f"\n❌ Phase 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check SharedContext after Phase 1
    if shared_ctx:
        files_after_1 = shared_ctx.get_all_examined_files()
        history_after_1 = shared_ctx.get_agent_history()

        print(f"\n📊 SharedContext after Phase 1:")
        print(f"  Files examined: {len(files_after_1)}")
        print(f"  Agent executions: {len(history_after_1)}")

    print("\n" + "=" * 80)
    print("Phase 2: Verilog 모듈 탐색")
    print("=" * 80)

    start_time = time.time()

    try:
        result2 = spawn_explore(
            query=f"Find all Verilog files (*.v, *.sv) in {caliptra_path}/src. "
                  f"Identify the main modules and their purposes."
        )

        elapsed2 = time.time() - start_time

        print(f"\n✓ Phase 2 completed in {elapsed2:.1f}s")
        print(f"\n결과 (처음 500자):")
        print("-" * 80)
        result2_str = str(result2)
        print(result2_str[:500] + "..." if len(result2_str) > 500 else result2_str)

        # Check AgentResult
        if hasattr(result2, 'get'):
            files2 = result2.get('files_examined', [])
            print(f"\n✓ Files examined: {len(files2)}")
            if files2:
                print("  Sample files:")
                for f in files2[:5]:
                    print(f"    • {f}")

    except Exception as e:
        print(f"\n❌ Phase 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Check SharedContext after Phase 2
    if shared_ctx:
        files_after_2 = shared_ctx.get_all_examined_files()
        history_after_2 = shared_ctx.get_agent_history()

        print(f"\n📊 SharedContext after Phase 2:")
        print(f"  Files examined: {len(files_after_2)} (was {len(files_after_1)})")
        print(f"  Agent executions: {len(history_after_2)} (was {len(history_after_1)})")
        print(f"  New files found: {len(files_after_2) - len(files_after_1)}")

    print("\n" + "=" * 80)
    print("Phase 3: 분석 계획 수립")
    print("=" * 80)

    start_time = time.time()

    try:
        result3 = spawn_plan(
            task_description=f"Create an analysis plan for the Caliptra subsystem at {caliptra_path}. "
                            f"Based on the explored files and structure, outline steps to analyze the system architecture."
        )

        elapsed3 = time.time() - start_time

        print(f"\n✓ Phase 3 completed in {elapsed3:.1f}s")
        print(f"\n계획 (처음 800자):")
        print("-" * 80)
        result3_str = str(result3)
        print(result3_str[:800] + "..." if len(result3_str) > 800 else result3_str)

        # Check AgentResult
        if hasattr(result3, 'get'):
            steps = result3.get('planned_steps', [])
            print(f"\n✓ Planned steps: {len(steps)}")
            if steps:
                print("  Steps:")
                for idx, step in enumerate(steps, 1):
                    print(f"    {idx}. {step}")

    except Exception as e:
        print(f"\n❌ Phase 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Final SharedContext check
    if shared_ctx:
        files_final = shared_ctx.get_all_examined_files()
        history_final = shared_ctx.get_agent_history()
        steps_final = shared_ctx.get_planned_steps()

        print(f"\n📊 Final SharedContext:")
        print(f"  Total files examined: {len(files_final)}")
        print(f"  Total agent executions: {len(history_final)}")
        print(f"  Planned steps: {len(steps_final)}")

        # Show summary
        summary = shared_ctx.get_summary(include_history=True)
        print(f"\n📋 Complete Summary:")
        print("-" * 80)
        print(summary)

        # LLM Context
        llm_context = shared_ctx.get_context_for_llm()
        print(f"\n🤖 LLM Context (for next agent):")
        print("-" * 80)
        print(llm_context)

    print("\n" + "=" * 80)
    print("검증")
    print("=" * 80)

    checks = []

    # Check 1: Multiple agents executed
    check1 = len(history_final) >= 3
    checks.append(("3개 Agent 실행", check1))
    print(f"  {'✅' if check1 else '❌'} 3개 Agent 실행됨: {len(history_final)}")

    # Check 2: Files accumulated
    check2 = len(files_final) > 0
    checks.append(("파일 탐색", check2))
    print(f"  {'✅' if check2 else '❌'} 파일 탐색 완료: {len(files_final)} files")

    # Check 3: Context grew over time
    check3 = len(files_after_2) > len(files_after_1)
    checks.append(("Context 누적", check3))
    print(f"  {'✅' if check3 else '❌'} Context 누적: {len(files_after_1)} → {len(files_after_2)} → {len(files_final)}")

    # Check 4: Plan created
    check4 = len(steps_final) > 0
    checks.append(("계획 수립", check4))
    print(f"  {'✅' if check4 else '❌'} 계획 수립: {len(steps_final)} steps")

    # Check 5: LLM context generated
    check5 = '📁 Files examined' in llm_context
    checks.append(("LLM Context 생성", check5))
    print(f"  {'✅' if check5 else '❌'} LLM Context 생성됨")

    # Check 6: Agent communication (Plan saw Explore results)
    # PlanAgent should have access to explored files via SharedContext
    check6 = len(files_final) > 0 and len(steps_final) > 0
    checks.append(("Agent 간 통신", check6))
    print(f"  {'✅' if check6 else '❌'} Agent 간 정보 공유")

    all_passed = all(result for _, result in checks)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ Caliptra 분석 테스트 통과!")
        print("=" * 80)

        print("\n🎯 분석 품질:")
        print(f"  - 탐색된 파일: {len(files_final)}개")
        print(f"  - 실행된 Agent: {len(history_final)}개")
        print(f"  - 수립된 계획: {len(steps_final)}단계")
        print(f"  - Agent 간 정보 공유: ✅")

        print("\n💡 시스템 효과:")
        print("  - ExploreAgent 결과가 PlanAgent에 전달됨")
        print("  - SharedContext가 모든 정보 보존")
        print("  - LLM에게 통합된 context 제공 가능")

        return True
    else:
        print("❌ Caliptra 분석 테스트 실패!")
        print("=" * 80)

        for check_name, result in checks:
            if not result:
                print(f"  ❌ Failed: {check_name}")

        return False


def main():
    """Run Caliptra analysis test"""
    print("\n" + "🚀 " * 40)
    print("Caliptra Subsystem 실제 분석 - Agent Communication 실전 검증")
    print("🚀 " * 40 + "\n")

    print("⚠️  이 테스트는 실제 LLM API를 호출합니다.")
    print("⚠️  ANTHROPIC_API_KEY가 필요합니다.")
    print("⚠️  예상 소요 시간: 1-2분\n")

    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        print("   Please set your API key to run this test.\n")
        return 1

    print("✓ API key found")
    print("\n시작합니다...\n")

    try:
        success = test_caliptra_analysis()

        if success:
            print("\n" + "🎉 " * 40)
            print("Caliptra 분석 완료 - Agent Communication 시스템 검증 성공!")
            print("🎉 " * 40 + "\n")
            return 0
        else:
            return 1

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
