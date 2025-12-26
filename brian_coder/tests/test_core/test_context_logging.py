#!/usr/bin/env python3
"""
SubAgent Context Logging 테스트

ExploreAgent가 context를 어떻게 사용하는지 debug log에서 확인
"""

import os
import sys

# DEBUG 모드 활성화
os.environ['DEBUG_SUBAGENT'] = 'true'

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from agents.sub_agents.explore_agent import ExploreAgent
from agents.sub_agents.base import AgentStatus

def mock_llm(messages):
    """Simple LLM mock"""
    return """Thought: I understand the context.
Result: Context was successfully used in the execution."""

def mock_tool(tool_name, args):
    """Mock tool executor"""
    return "OK"

def test_with_context():
    """Test with rich context"""
    print("\n" + "="*80)
    print("  TEST 1: ExploreAgent with Rich Context")
    print("="*80 + "\n")

    agent = ExploreAgent(
        name="test_context_explore",
        llm_call_func=mock_llm,
        execute_tool_func=mock_tool,
        max_iterations=3
    )

    # Provide rich context
    context = {
        "project_type": "Verilog HDL Design",
        "previous_findings": [
            "Found axi_write_gen.v module",
            "Found pcie_msg_receiver.v module",
            "SRAM module exists"
        ],
        "current_focus": "Analyze data flow between AXI and PCIe",
        "constraints": {
            "timing": "100MHz clock",
            "data_width": "256 bits"
        },
        "long_text": "This is a very long description " * 10  # Long text to test truncation
    }

    result = agent.run("Analyze the system architecture", context)

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Context was logged above with details")

def test_without_context():
    """Test without context"""
    print("\n" + "="*80)
    print("  TEST 2: ExploreAgent without Context")
    print("="*80 + "\n")

    agent = ExploreAgent(
        name="test_no_context_explore",
        llm_call_func=mock_llm,
        execute_tool_func=mock_tool,
        max_iterations=3
    )

    result = agent.run("Simple exploration task", None)

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Should show 'Empty (no context provided)'")

def test_context_in_steps():
    """Test context usage in execution steps"""
    print("\n" + "="*80)
    print("  TEST 3: Context in Multi-Step Execution")
    print("="*80 + "\n")

    call_count = 0

    def mock_llm_multi_step(messages):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            return """Thought: Let me check the modules first.
Action: list_dir(path=".")"""
        elif call_count == 2:
            return """Thought: Now I have the context and file list.
Result: Found modules as expected from context."""

    agent = ExploreAgent(
        name="test_multi_step",
        llm_call_func=mock_llm_multi_step,
        execute_tool_func=lambda t, a: "Files: axi_write_gen.v, pcie_msg_receiver.v",
        max_iterations=5
    )

    context = {
        "previous_step": "Initial exploration complete",
        "next_action": "Verify module dependencies"
    }

    result = agent.run("Continue analysis", context)

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Context should be visible in step execution logs")

def main():
    """Run all tests"""
    print("\n" + "█"*80)
    print("  SubAgent Context Logging 테스트")
    print("█"*80)

    print("\n" + "📋 Expected Logging Format:")
    print("  - Context keys: [list of keys]")
    print("  - Context details: {key: preview}")
    print("  - Context in steps: preview of context content")
    print("")

    test_with_context()
    test_without_context()
    test_context_in_steps()

    print("\n" + "█"*80)
    print("  테스트 완료")
    print("  위의 DEBUG 로그에서 context 정보가 명확하게 표시되는지 확인하세요")
    print("█"*80 + "\n")

if __name__ == "__main__":
    main()
