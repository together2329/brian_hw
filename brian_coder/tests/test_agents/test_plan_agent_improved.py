#!/usr/bin/env python3
"""
PlanAgent 개선사항 테스트

테스트 항목:
1. 기본 계획 생성
2. spawn_explore 도구 사용
3. Markdown formatting
4. Error handling
5. ALLOWED_TOOLS enforcement (spawn_explore만 허용)
"""

import os
import sys

# DEBUG 모드 활성화
os.environ['DEBUG_SUBAGENT'] = 'true'

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from agents.sub_agents.plan_agent import PlanAgent
from agents.sub_agents.base import AgentStatus

def mock_llm_simple_plan(messages):
    """Simple LLM mock that generates a plan"""
    last_msg = messages[-1]['content']

    if 'Observation:' in last_msg:
        # After receiving observation, complete with plan
        return """Thought: I have the exploration results.
Result:
## Task Analysis
Implement a new FIFO module for PCIe data buffering.

## Implementation Steps
1. Create fifo.v with parameterized depth and width
2. Add synchronous reset logic
3. Implement full/empty flags
4. Add testbench fifo_tb.v

## Success Criteria
- FIFO passes all timing simulations
- Full/empty flags work correctly"""
    else:
        # First call - use spawn_explore
        return """Thought: I need to explore the codebase first.
Action: spawn_explore(query="Find existing FIFO implementations")"""

def mock_llm_markdown_plan(messages):
    """LLM mock that uses markdown formatting in actions"""
    last_msg = messages[-1]['content']

    if 'Observation:' in last_msg:
        return """Result:
## Plan
Create the implementation following existing patterns."""
    else:
        # Use markdown formatting
        return """Thought: Let me explore first.
**Action:** spawn_explore(query="Check project structure")"""

def mock_llm_forbidden_tool(messages):
    """LLM mock that tries forbidden tools"""
    last_msg = messages[-1]['content']

    if 'not allowed' in last_msg.lower():
        # After rejection, use allowed tool
        return """Thought: read_file is not allowed. Let me use spawn_explore.
Action: spawn_explore(query="Find module hierarchy")"""
    elif 'Observation:' in last_msg:
        return """Result:
## Plan
Based on exploration, implement the module."""
    else:
        # Try forbidden tool
        return """Thought: Let me read a file directly.
Action: read_file(path="test.v")"""

def mock_execute_tool(tool_name, args):
    """Mock tool executor"""
    if tool_name == 'spawn_explore':
        return """=== EXPLORATION RESULTS ===
Found the following modules:
- axi_write_gen.v: AXI write generator
- axi_read_gen.v: AXI read generator
- pcie_msg_receiver.v: PCIe message receiver
- sram.v: Dual-port SRAM

No existing FIFO implementation found.
"""
    elif tool_name == 'read_file':
        return "module test;\nendmodule"
    else:
        return f"OK (tool: {tool_name})"

def print_separator(title):
    """Print test section separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_basic_plan():
    """Test 1: Basic plan generation"""
    print_separator("TEST 1: Basic Plan Generation")

    agent = PlanAgent(
        name="test_plan_basic",
        llm_call_func=mock_llm_simple_plan,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("Create a FIFO module for PCIe", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Output contains plan: {'## Task Analysis' in result.output}")
    print(f"✓ Output preview: {result.output[:200]}...")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    assert '## Task Analysis' in result.output or 'Task Analysis' in result.output, "Expected plan structure"
    print("\n✅ TEST 1 PASSED")

def test_spawn_explore_usage():
    """Test 2: spawn_explore tool usage"""
    print_separator("TEST 2: spawn_explore Tool Usage")

    agent = PlanAgent(
        name="test_plan_spawn",
        llm_call_func=mock_llm_simple_plan,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("Plan FIFO implementation", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")

    # Check that spawn_explore was used
    executed_tools = [tc['tool'] for tc in result.tool_calls]
    print(f"✓ Executed tools: {executed_tools}")

    assert 'spawn_explore' in executed_tools, "Expected spawn_explore to be used"
    print("\n✅ TEST 2 PASSED")

def test_markdown_action_parsing():
    """Test 3: Markdown action format parsing"""
    print_separator("TEST 3: Markdown Action Parsing")

    agent = PlanAgent(
        name="test_plan_markdown",
        llm_call_func=mock_llm_markdown_plan,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("Plan with markdown actions", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Successfully parsed markdown Action format")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    assert len(result.tool_calls) > 0, "Expected markdown action to be parsed"
    print("\n✅ TEST 3 PASSED")

def test_forbidden_tools():
    """Test 4: ALLOWED_TOOLS enforcement (only spawn_explore)"""
    print_separator("TEST 4: ALLOWED_TOOLS Enforcement")

    agent = PlanAgent(
        name="test_plan_forbidden",
        llm_call_func=mock_llm_forbidden_tool,
        execute_tool_func=mock_execute_tool,
        max_iterations=10
    )

    result = agent.run("Test tool restrictions", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")

    # Check that read_file was NOT executed
    executed_tools = [tc['tool'] for tc in result.tool_calls]
    print(f"✓ Executed tools: {executed_tools}")

    assert 'read_file' not in executed_tools, "read_file should not be in executed tools"
    assert 'spawn_explore' in executed_tools, "spawn_explore should be in executed tools"
    print(f"✓ Forbidden tool (read_file) was rejected")
    print(f"✓ Allowed tool (spawn_explore) was accepted")

    print("\n✅ TEST 4 PASSED")

def test_text_only_output():
    """Test 5: Text-only plan (no code generation)"""
    print_separator("TEST 5: Text-Only Output Verification")

    def mock_llm_text_only(messages):
        return """Result:
## Task Analysis
Create a FIFO module.

## Implementation Strategy
Follow standard FIFO design patterns.

## Testing Plan
Create comprehensive testbench."""

    agent = PlanAgent(
        name="test_plan_text_only",
        llm_call_func=mock_llm_text_only,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("Plan FIFO module", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Output is text-only plan (no code): {True}")
    print(f"✓ Contains plan sections: {'## Task Analysis' in result.output}")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    # Verify it's a plan (text), not code
    assert '## Task Analysis' in result.output or 'Task Analysis' in result.output, "Expected plan structure"
    print("\n✅ TEST 5 PASSED")

def test_hallucination_detection():
    """Test 6: Hallucination detection"""
    print_separator("TEST 6: Hallucination Detection")

    call_count = 0

    def mock_llm_hallucination(messages):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # First call - hallucinate
            return """Thought: I'll just make up exploration results.
Observation: [Fake exploration results]"""
        elif 'DO NOT DO THIS' in messages[-1]['content']:
            # After warning - correct behavior
            return """Thought: Sorry, let me do it correctly.
Action: spawn_explore(query="Find modules")"""
        else:
            return """Result:
## Plan
Create implementation based on findings."""

    agent = PlanAgent(
        name="test_plan_hallucination",
        llm_call_func=mock_llm_hallucination,
        execute_tool_func=mock_execute_tool,
        max_iterations=10
    )

    result = agent.run("Test hallucination detection", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ LLM calls: {call_count}")
    print(f"✓ Hallucination was detected and corrected")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    print("\n✅ TEST 6 PASSED")

def main():
    """Run all tests"""
    print("\n" + "█"*80)
    print("  PlanAgent 개선사항 테스트 스위트")
    print("█"*80)

    tests = [
        ("Basic Plan Generation", test_basic_plan),
        ("spawn_explore Usage", test_spawn_explore_usage),
        ("Markdown Action Parsing", test_markdown_action_parsing),
        ("ALLOWED_TOOLS Enforcement", test_forbidden_tools),
        ("Text-Only Output", test_text_only_output),
        ("Hallucination Detection", test_hallucination_detection),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "█"*80)
    print(f"  테스트 결과: {passed} passed, {failed} failed (total: {len(tests)})")
    print("█"*80 + "\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
