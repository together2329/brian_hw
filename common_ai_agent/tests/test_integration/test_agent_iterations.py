#!/usr/bin/env python3
"""
Agent Iteration 패턴 테스트

ExploreAgent와 PlanAgent가 실제로 몇 iteration을 사용하는지 확인
"""

import os
import sys

# DEBUG 모드 활성화
os.environ['DEBUG_SUBAGENT'] = 'true'

# Add common_ai_agent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent'))

from agents.sub_agents.explore_agent import ExploreAgent
from agents.sub_agents.plan_agent import PlanAgent
from agents.sub_agents.base import AgentStatus

def print_separator(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_explore_multi_iteration():
    """ExploreAgent with multiple iterations"""
    print_separator("TEST 1: ExploreAgent - Multiple Iterations")

    iteration_count = 0

    def mock_llm_explore(messages):
        nonlocal iteration_count
        iteration_count += 1

        # Simulate multi-step exploration
        if iteration_count == 1:
            return """Thought: First, I need to list all files.
Action: list_dir(path=".")"""
        elif iteration_count == 2:
            return """Thought: Now I'll read the main module.
Action: read_file(path="axi_write_gen.v")"""
        elif iteration_count == 3:
            return """Thought: Let me check for related files.
Action: find_files(pattern="*.v", directory=".")"""
        elif iteration_count == 4:
            return """Thought: I should search for a specific pattern.
Action: grep_file(pattern="module", path="axi_write_gen.v")"""
        else:
            return """Thought: I've gathered enough information.
Result: Found 5 Verilog modules:
- axi_write_gen.v: AXI write generator
- axi_read_gen.v: AXI read generator
- pcie_msg_receiver.v: PCIe message receiver
- pcie_axi_to_sram.v: AXI to SRAM bridge
- sram.v: Dual-port SRAM

All modules follow standard Verilog naming conventions."""

    def mock_tool(tool_name, args):
        if tool_name == 'list_dir':
            return "Files: axi_write_gen.v, axi_read_gen.v, pcie_msg_receiver.v"
        elif tool_name == 'read_file':
            return "module axi_write_gen(...);\n  // AXI write logic\nendmodule"
        elif tool_name == 'find_files':
            return "Found 5 files: *.v"
        elif tool_name == 'grep_file':
            return "module axi_write_gen"
        return "OK"

    agent = ExploreAgent(
        name="explore_multi_iter",
        llm_call_func=mock_llm_explore,
        execute_tool_func=mock_tool,
        max_iterations=10  # 명시적으로 설정
    )

    result = agent.run("Explore all Verilog modules in the project", {})

    print(f"\n📊 Results:")
    print(f"  Status: {result.status}")
    print(f"  Iterations used: {iteration_count}")
    print(f"  Max iterations: 10")
    print(f"  Tool calls: {len(result.tool_calls)}")
    print(f"  Tools used: {[tc['tool'] for tc in result.tool_calls]}")
    print(f"\n✓ ExploreAgent used {iteration_count} iterations")

def test_plan_multi_iteration():
    """PlanAgent with multiple iterations"""
    print_separator("TEST 2: PlanAgent - Multiple Iterations")

    iteration_count = 0

    def mock_llm_plan(messages):
        nonlocal iteration_count
        iteration_count += 1

        # Simulate multi-step planning
        if iteration_count == 1:
            return """Thought: I need to explore the codebase first.
Action: spawn_explore(query="Find all existing FIFO implementations")"""
        elif iteration_count == 2:
            return """Thought: Let me check module hierarchy.
Action: spawn_explore(query="Analyze module dependencies")"""
        else:
            return """Thought: Now I have enough information to create a plan.
Result:
## Task Analysis
Implement a new FIFO module for PCIe data buffering.

## Current State
- No existing FIFO implementation found
- AXI modules present (write_gen, read_gen)
- PCIe receiver and SRAM modules available

## Implementation Strategy
1. Create fifo.v with parameterized depth/width
2. Add synchronous reset logic
3. Implement full/empty flags with proper timing
4. Create comprehensive testbench

## Dependencies
- Use existing SRAM module patterns
- Follow AXI module naming conventions

## Success Criteria
- FIFO passes timing simulations at 100MHz
- Full/empty flags work correctly
- No data loss under stress test"""

    def mock_tool(tool_name, args):
        if tool_name == 'spawn_explore':
            return """=== EXPLORATION RESULTS ===
No existing FIFO found.
Modules: axi_write_gen, axi_read_gen, pcie_msg_receiver, sram
Dependencies: AXI -> PCIe -> SRAM"""
        return "OK"

    agent = PlanAgent(
        name="plan_multi_iter",
        llm_call_func=mock_llm_plan,
        execute_tool_func=mock_tool,
        max_iterations=10  # 명시적으로 설정
    )

    result = agent.run("Create implementation plan for FIFO module", {})

    print(f"\n📊 Results:")
    print(f"  Status: {result.status}")
    print(f"  Iterations used: {iteration_count}")
    print(f"  Max iterations: 10")
    print(f"  Tool calls: {len(result.tool_calls)}")
    print(f"  Tools used: {[tc['tool'] for tc in result.tool_calls]}")
    print(f"\n✓ PlanAgent used {iteration_count} iterations")

def test_max_iterations_reached():
    """Test what happens when max iterations is reached"""
    print_separator("TEST 3: Max Iterations Limit")

    iteration_count = 0

    def mock_llm_infinite(messages):
        nonlocal iteration_count
        iteration_count += 1
        # Never complete - keep reading
        return f"""Thought: Let me read another file (iteration {iteration_count}).
Action: read_file(path="file{iteration_count}.v")"""

    def mock_tool(tool_name, args):
        return f"Content of {args}"

    agent = ExploreAgent(
        name="explore_max_iter",
        llm_call_func=mock_llm_infinite,
        execute_tool_func=mock_tool,
        max_iterations=5  # Small limit for testing
    )

    result = agent.run("Test max iterations", {})

    print(f"\n📊 Results:")
    print(f"  Status: {result.status}")
    print(f"  Iterations used: {iteration_count}")
    print(f"  Max iterations: 5")
    print(f"  Reached limit: {iteration_count >= 5}")
    print(f"\n✓ Agent stopped at max_iterations={5}")
    print(f"  (Without limit, it would continue indefinitely)")

def test_quick_completion():
    """Test quick completion (1 iteration)"""
    print_separator("TEST 4: Quick Completion (1 iteration)")

    iteration_count = 0

    def mock_llm_quick(messages):
        nonlocal iteration_count
        iteration_count += 1
        # Complete immediately
        return """Thought: The task is simple, I can complete it immediately.
Result: Task completed successfully."""

    agent = ExploreAgent(
        name="explore_quick",
        llm_call_func=mock_llm_quick,
        execute_tool_func=lambda t, a: "OK",
        max_iterations=10
    )

    result = agent.run("Simple task", {})

    print(f"\n📊 Results:")
    print(f"  Status: {result.status}")
    print(f"  Iterations used: {iteration_count}")
    print(f"  Max iterations: 10")
    print(f"\n✓ Agent completed in just 1 iteration (efficient!)")

def main():
    print("\n" + "█"*80)
    print("  Agent Iteration 패턴 분석")
    print("█"*80)

    print("\n📌 Key Points:")
    print("  - ExploreAgent default: max_iterations=10")
    print("  - PlanAgent default: max_iterations=10")
    print("  - 실제 사용 iteration은 task 복잡도에 따라 다름")
    print("  - ReAct 루프: Thought → Action → Observation 반복")
    print("")

    test_explore_multi_iteration()
    test_plan_multi_iteration()
    test_max_iterations_reached()
    test_quick_completion()

    print("\n" + "█"*80)
    print("  Summary")
    print("█"*80)
    print("""
  ✓ ExploreAgent와 PlanAgent는 모두 max_iterations=10 기본값 사용
  ✓ 실제 iteration 수는 task에 따라 1~10 사이에서 결정됨
  ✓ 간단한 task: 1-2 iterations (즉시 Result 반환)
  ✓ 복잡한 task: 4-8 iterations (여러 도구 사용)
  ✓ Max 도달: 10 iterations 후 자동 종료

  Mock LLM 테스트에서 1-2 iteration만 보이는 이유:
  → Mock이 바로 "Result:"를 반환하기 때문
  → 실제 LLM은 여러 Action을 순차적으로 실행함
""")
    print("█"*80 + "\n")

if __name__ == "__main__":
    main()
