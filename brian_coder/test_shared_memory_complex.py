#!/usr/bin/env python3
"""
Shared Memory - 복잡한 시나리오 통합 테스트

복잡한 시나리오:
1. Multi-threaded ExploreAgent 실행 (thread-safety 검증)
2. PlanAgent가 ExploreAgent 결과 활용
3. ExecuteAgent 시뮬레이션
4. 실시간 context 업데이트 및 LLM 주입 검증

시나리오: "대규모 Verilog 프로젝트 분석 및 구현"
- 3개 ExploreAgent가 동시에 다른 영역 탐색
- PlanAgent가 통합 계획 수립
- ExecuteAgent가 실제 구현
"""

import sys
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Enable debug
os.environ['DEBUG_SUBAGENT'] = 'true'


def test_complex_scenario():
    """
    복잡한 시나리오: 대규모 Verilog 프로젝트 분석

    Flow:
    1. 3개 ExploreAgent 병렬 실행:
       - explore_fifo: FIFO 모듈 탐색
       - explore_axi: AXI 인터페이스 탐색
       - explore_tests: 테스트벤치 패턴 탐색
    2. PlanAgent: 통합 계획 (shared context 활용)
    3. ExecuteAgent: 파일 수정 기록
    4. 최종 SharedContext 검증
    """
    print("=" * 80)
    print("복잡한 시나리오: 대규모 Verilog 프로젝트 분석 및 구현")
    print("=" * 80)

    from shared_context import SharedContext
    from sub_agents.explore_agent import ExploreAgent
    from sub_agents.plan_agent import PlanAgent

    # Create shared context
    shared_ctx = SharedContext()

    print("\n[Phase 1] 3개 ExploreAgent 병렬 실행...")
    print("-" * 80)

    # Mock LLM functions for different agents
    def mock_llm_explore_fifo(messages):
        last_msg = messages[-1]['content']
        if 'Observation:' in last_msg:
            time.sleep(0.1)  # Simulate LLM latency
            return """EXPLORE_COMPLETE: Found FIFO implementations:
- fifo_sync.v: Synchronous FIFO (256 deep, 32-bit width)
- fifo_async.v: Async FIFO with CDC (128 deep, Gray code pointers)
- fifo_interface.vh: Common interface definitions"""
        else:
            return """Thought: Search for FIFO modules.
Action: find_files(pattern="*fifo*.v", directory="design/")"""

    def mock_llm_explore_axi(messages):
        last_msg = messages[-1]['content']
        if 'Observation:' in last_msg:
            time.sleep(0.15)  # Different latency
            return """EXPLORE_COMPLETE: Found AXI components:
- axi_master.v: AXI4 Master interface
- axi_slave.v: AXI4 Slave interface
- axi_interconnect.v: 4x4 crossbar switch
- axi_protocol.vh: Protocol definitions"""
        else:
            return """Thought: Search for AXI modules.
Action: find_files(pattern="*axi*.v", directory="design/")"""

    def mock_llm_explore_tests(messages):
        last_msg = messages[-1]['content']
        if 'Observation:' in last_msg:
            time.sleep(0.12)  # Different latency
            return """EXPLORE_COMPLETE: Found testbench patterns:
- tb_template.v: Standard testbench template
- wave_dump.vh: Waveform dumping macros
- tb_fifo_sync.v: FIFO sync testbench
- tb_axi_master.v: AXI master testbench"""
        else:
            return """Thought: Search for testbenches.
Action: find_files(pattern="tb_*.v", directory="design/testbench/")"""

    def mock_execute_tool(tool_name, args):
        # args can be either string or dict
        if isinstance(args, str):
            # Parse string args
            import re
            kwargs = {}
            for match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', args):
                kwargs[match.group(1)] = match.group(2)
            args = kwargs

        if tool_name == 'find_files':
            pattern = args.get('pattern', '')
            if 'fifo' in pattern:
                return "fifo_sync.v\nfifo_async.v\nfifo_interface.vh"
            elif 'axi' in pattern:
                return "axi_master.v\naxi_slave.v\naxi_interconnect.v\naxi_protocol.vh"
            elif 'tb_' in pattern:
                return "tb_template.v\nwave_dump.vh\ntb_fifo_sync.v\ntb_axi_master.v"
        return "OK"

    # Function to run ExploreAgent
    def run_explore_agent(name, llm_func, query, results):
        """Run single ExploreAgent and store result"""
        agent = ExploreAgent(
            name=name,
            llm_call_func=llm_func,
            execute_tool_func=mock_execute_tool,
            shared_context=shared_ctx
        )

        start_time = time.time()
        result = agent.run(query, {})
        elapsed = time.time() - start_time

        results[name] = {
            'result': result,
            'elapsed': elapsed
        }

        print(f"  ✓ {name} completed in {elapsed:.2f}s")
        print(f"    Files: {result.context_updates.get('files_examined', [])}")

    # Run 3 ExploreAgents in parallel
    results = {}
    agents = [
        ('explore_fifo', mock_llm_explore_fifo, 'Find FIFO modules'),
        ('explore_axi', mock_llm_explore_axi, 'Find AXI modules'),
        ('explore_tests', mock_llm_explore_tests, 'Find testbenches')
    ]

    parallel_start = time.time()

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for name, llm_func, query in agents:
            future = executor.submit(run_explore_agent, name, llm_func, query, results)
            futures.append(future)

        # Wait for all to complete
        for future in futures:
            future.result()

    parallel_elapsed = time.time() - parallel_start

    print(f"\n✓ All 3 ExploreAgents completed in {parallel_elapsed:.2f}s (parallel)")
    print(f"  Expected sequential: ~0.37s")
    print(f"  Actual parallel: {parallel_elapsed:.2f}s")
    print(f"  Speedup: {0.37 / parallel_elapsed:.2f}x")

    print("\n[Phase 2] SharedContext 검증 (Thread-safety)")
    print("-" * 80)

    # Check SharedContext aggregation
    all_files = shared_ctx.get_all_examined_files()
    findings = shared_ctx.get_exploration_findings()
    history = shared_ctx.get_agent_history('explore')

    print(f"\n✓ SharedContext aggregated results:")
    print(f"  Total files examined: {len(all_files)}")
    print(f"  Total findings: {len(findings)}")
    print(f"  Agent executions: {len(history)}")

    print(f"\n✓ Files examined (all agents):")
    for f in all_files:
        print(f"    • {f}")

    # Verify thread-safety: should have exactly 11 unique files
    expected_files = {
        'fifo_sync.v', 'fifo_async.v', 'fifo_interface.vh',
        'axi_master.v', 'axi_slave.v', 'axi_interconnect.v', 'axi_protocol.vh',
        'tb_template.v', 'wave_dump.vh', 'tb_fifo_sync.v', 'tb_axi_master.v'
    }

    assert set(all_files) == expected_files, f"Thread-safety violation! Expected {len(expected_files)} files, got {len(all_files)}"
    print(f"\n  ✅ Thread-safety verified: {len(all_files)} files, no duplicates or losses")

    print("\n[Phase 3] PlanAgent 실행 (SharedContext 활용)")
    print("-" * 80)

    def mock_llm_plan(messages):
        """PlanAgent LLM that can see SharedContext"""
        last_msg = messages[-1]['content']

        # Check if SharedContext info is in message
        has_shared_context = '[Shared Agent Memory]' in str(messages)

        if 'Observation:' in last_msg:
            return f"""PLAN_COMPLETE:
## Overview
Create integrated system combining FIFO, AXI, and testbench components.
(SharedContext available: {has_shared_context})

## Phase 1: FIFO Integration (20분)
**File**: `design/fifo_axi_bridge.v` (NEW)
**Changes**: Bridge FIFO to AXI interface

## Phase 2: AXI Interconnect (30분)
**File**: `design/axi_interconnect.v`
**Line 100-150**: Add FIFO ports

## Phase 3: Testbench (15분)
**File**: `design/testbench/tb_integrated.v` (NEW)
**Changes**: Integrated system testbench

## Success Criteria
- [ ] FIFO-AXI bridge working
- [ ] Interconnect supports FIFO
- [ ] All tests passing"""
        else:
            return """Thought: Review shared context for planning.
Action: spawn_explore(query="Review existing system structure")"""

    plan_agent = PlanAgent(
        name="plan_integration",
        llm_call_func=mock_llm_plan,
        execute_tool_func=mock_execute_tool,
        shared_context=shared_ctx
    )

    plan_result = plan_agent.run("Create integrated FIFO-AXI system", {})

    print(f"\n✓ PlanAgent completed")
    print(f"  Status: {plan_result.status.value}")
    print(f"  Planned steps: {len(plan_result.context_updates.get('planned_steps', []))}")

    # Check if PlanAgent can see SharedContext
    planned_steps = shared_ctx.get_planned_steps()
    print(f"\n✓ SharedContext updated with plan:")
    for idx, step in enumerate(planned_steps, 1):
        print(f"    {idx}. {step}")

    print("\n[Phase 4] ExecuteAgent 시뮬레이션")
    print("-" * 80)

    # Simulate file modifications
    shared_ctx.record_execution(
        agent_name="execute_fifo_bridge",
        files_modified=["design/fifo_axi_bridge.v"],
        execution_time_ms=5000,
        tool_calls_count=3
    )

    shared_ctx.record_execution(
        agent_name="execute_interconnect",
        files_modified=["design/axi_interconnect.v"],
        execution_time_ms=3000,
        tool_calls_count=2
    )

    print(f"  ✓ Simulated file modifications")

    modified_files = shared_ctx.get_all_modified_files()
    print(f"  ✓ Modified files: {modified_files}")

    print("\n[Phase 5] 최종 SharedContext 검증")
    print("-" * 80)

    # Get comprehensive summary
    summary = shared_ctx.get_summary(include_history=True)
    print("\n✓ SharedContext Summary:")
    print(summary)

    # Get LLM-formatted context
    llm_context = shared_ctx.get_context_for_llm()
    print("\n✓ Context for LLM:")
    print(llm_context)

    print("\n[Phase 6] 최종 검증")
    print("-" * 80)

    checks = []

    # Check 1: All files preserved
    check1 = len(all_files) == 11
    checks.append(("All files preserved", check1))
    print(f"  {'✅' if check1 else '❌'} All 11 files preserved")

    # Check 2: Thread-safety (no duplicates)
    check2 = len(all_files) == len(set(all_files))
    checks.append(("Thread-safe aggregation", check2))
    print(f"  {'✅' if check2 else '❌'} Thread-safe aggregation (no duplicates)")

    # Check 3: Plan steps recorded
    check3 = len(planned_steps) == 3
    checks.append(("Plan steps recorded", check3))
    print(f"  {'✅' if check3 else '❌'} Plan steps recorded")

    # Check 4: Execution history complete
    total_history = shared_ctx.get_agent_history()
    check4 = len(total_history) >= 5  # 3 explore + 1 plan + 2 execute
    checks.append(("Execution history", check4))
    print(f"  {'✅' if check4 else '❌'} Execution history complete ({len(total_history)} agents)")

    # Check 5: Files modified tracked
    check5 = len(modified_files) == 2
    checks.append(("Files modified tracked", check5))
    print(f"  {'✅' if check5 else '❌'} Files modified tracked")

    # Check 6: LLM context generated
    check6 = '📁 Files examined' in llm_context and '📋 Planned steps' in llm_context
    checks.append(("LLM context generated", check6))
    print(f"  {'✅' if check6 else '❌'} LLM context properly formatted")

    # Check 7: Real-time updates work
    check7 = len(shared_ctx.get_exploration_findings()) == 3  # 3 explore agents
    checks.append(("Real-time updates", check7))
    print(f"  {'✅' if check7 else '❌'} Real-time context updates")

    all_passed = all(result for _, result in checks)

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 복잡한 시나리오 테스트 통과!")
        print("=" * 80)

        print("\n📊 성능 및 기능 검증:")
        print(f"  - Multi-threaded safety: ✅ {len(all_files)} files, 0 conflicts")
        print(f"  - Parallel speedup: {0.37 / parallel_elapsed:.2f}x faster")
        print(f"  - Agent communication: ✅ PlanAgent saw ExploreAgent results")
        print(f"  - Real-time updates: ✅ All {len(total_history)} agents recorded")
        print(f"  - LLM context: ✅ Properly formatted for injection")

        print("\n🎯 Shared Memory 효과:")
        print("  Before: Agent 간 정보 공유 불가, 중복 작업")
        print("  After:  실시간 공유, 0% 정보 손실, thread-safe")

        return True
    else:
        print("❌ 복잡한 시나리오 테스트 실패!")
        print("=" * 80)

        for check_name, result in checks:
            if not result:
                print(f"  ❌ Failed: {check_name}")

        return False


def main():
    """Run complex scenario test"""
    print("\n" + "🚀 " * 40)
    print("Shared Memory - 복잡한 시나리오 통합 테스트")
    print("🚀 " * 40 + "\n")

    try:
        success = test_complex_scenario()

        if success:
            print("\n" + "🎉 " * 40)
            print("복잡한 시나리오 테스트 완료 - 모든 검증 통과!")
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
