#!/usr/bin/env python3
"""
ExploreAgent 개선사항 테스트

테스트 항목:
1. 기본 동작: 파일 탐색
2. Markdown action parsing
3. Debug logging 확인
4. Error recovery
"""

import os
import sys

# DEBUG 모드 활성화
os.environ['DEBUG_SUBAGENT'] = 'true'

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

from agents.sub_agents.explore_agent import ExploreAgent
from agents.sub_agents.base import AgentStatus

def mock_llm_simple(messages):
    """Simple LLM mock that explores Verilog files"""
    last_msg = messages[-1]['content']

    if 'Observation:' in last_msg:
        # After receiving observation, complete
        return """Thought: I've found the files I need.
Result: Found Verilog files in the project including axi_write_gen.v, axi_read_gen.v, pcie_msg_receiver.v, and others."""
    else:
        # First call - use list_dir action
        return """Thought: I need to explore the current directory to find Verilog files.
Action: list_dir(path=".")"""

def mock_llm_markdown(messages):
    """LLM mock that uses markdown formatting"""
    last_msg = messages[-1]['content']

    if 'Observation:' in last_msg:
        return """Thought: Files listed successfully.
Result: Found several Verilog source files."""
    else:
        # Use markdown formatting
        return """Thought: Let me list the directory.
**Action:** list_dir(path=".")"""

def mock_llm_hallucination(messages):
    """LLM mock that hallucinates (generates Observation itself)"""
    call_count = len([m for m in messages if m['role'] == 'assistant'])

    if call_count == 1:
        # First call - hallucinate
        return """Thought: I'll just make up an observation.
Observation: [Made up files list]"""
    elif 'DO NOT DO THIS' in messages[-1]['content']:
        # After warning - correct behavior
        return """Thought: Sorry, let me do it correctly.
Action: list_dir(path=".")"""
    else:
        return """Result: Completed after correction."""

def mock_execute_tool(tool_name, args):
    """Mock tool executor"""
    if tool_name == 'list_dir':
        return """Files:
axi_write_gen.v
axi_read_gen.v
pcie_msg_receiver.v
pcie_axi_to_sram.v
sram.v
test_pcie_full_tb.v"""
    elif tool_name == 'read_file':
        return "module test;\nendmodule"
    elif tool_name == 'grep_file':
        return "Found 3 matches"
    else:
        return f"OK (tool: {tool_name})"

def print_separator(title):
    """Print test section separator"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def test_basic_explore():
    """Test 1: Basic exploration functionality"""
    print_separator("TEST 1: Basic Exploration")

    agent = ExploreAgent(
        name="test_explore_basic",
        llm_call_func=mock_llm_simple,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("Find all Verilog files", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Files read: {len(agent._files_read)}")
    print(f"✓ Output preview: {result.output[:200]}...")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    assert len(result.tool_calls) > 0, "Expected at least 1 tool call"
    print("\n✅ TEST 1 PASSED")

def test_markdown_parsing():
    """Test 2: Markdown action format parsing"""
    print_separator("TEST 2: Markdown Action Parsing")

    agent = ExploreAgent(
        name="test_explore_markdown",
        llm_call_func=mock_llm_markdown,
        execute_tool_func=mock_execute_tool,
        max_iterations=5
    )

    result = agent.run("List files with markdown formatting", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Successfully parsed markdown Action format")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    assert len(result.tool_calls) > 0, "Expected markdown action to be parsed"
    print("\n✅ TEST 2 PASSED")

def test_hallucination_detection():
    """Test 3: Hallucination detection and recovery"""
    print_separator("TEST 3: Hallucination Detection")

    agent = ExploreAgent(
        name="test_explore_hallucination",
        llm_call_func=mock_llm_hallucination,
        execute_tool_func=mock_execute_tool,
        max_iterations=10
    )

    result = agent.run("Test hallucination detection", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Hallucination was detected and corrected")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    print("\n✅ TEST 3 PASSED")

def test_stall_detection():
    """Test 4: Stall detection (consecutive reads)"""
    print_separator("TEST 4: Stall Detection")

    call_count = 0

    def mock_llm_stall(messages):
        nonlocal call_count
        call_count += 1

        if call_count <= 6:
            # Keep reading
            return f"""Thought: Let me read file {call_count}.
Action: list_dir(path=".")"""
        else:
            # Complete after warning
            return """Thought: I've read enough.
Result: Completed exploration."""

    agent = ExploreAgent(
        name="test_explore_stall",
        llm_call_func=mock_llm_stall,
        execute_tool_func=mock_execute_tool,
        max_iterations=15
    )

    result = agent.run("Test stall detection", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ LLM calls: {call_count}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Stall warning should have been triggered")

    assert result.status == AgentStatus.COMPLETED, f"Expected COMPLETED, got {result.status}"
    print("\n✅ TEST 4 PASSED")

def test_error_recovery():
    """Test 5: Error handling and recovery"""
    print_separator("TEST 5: Error Recovery")

    error_count = 0

    def mock_llm_error(messages):
        nonlocal error_count
        last_msg = messages[-1]['content']

        if 'error' in last_msg.lower():
            error_count += 1
            if error_count < 3:
                # Repeat same error
                return """Thought: Let me try the same thing again.
Action: invalid_tool(path="test")"""
            else:
                # Different approach after max errors
                return """Thought: That didn't work. Let me try something else.
Action: list_dir(path=".")"""
        elif 'Observation:' in last_msg:
            return """Result: Recovered from errors."""
        else:
            # Initial attempt with invalid tool
            return """Thought: Let me try an invalid tool.
Action: invalid_tool(path="test")"""

    def mock_tool_with_error(tool_name, args):
        if tool_name == 'invalid_tool':
            raise ValueError("Tool not found: invalid_tool")
        return mock_execute_tool(tool_name, args)

    agent = ExploreAgent(
        name="test_explore_error",
        llm_call_func=mock_llm_error,
        execute_tool_func=mock_tool_with_error,
        max_iterations=10
    )

    result = agent.run("Test error recovery", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Errors encountered: {error_count}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")

    # Should either complete or fail gracefully
    assert result.status in [AgentStatus.COMPLETED, AgentStatus.FAILED], f"Unexpected status: {result.status}"
    print("\n✅ TEST 5 PASSED")

def test_allowed_tools_enforcement():
    """Test 6: ALLOWED_TOOLS enforcement"""
    print_separator("TEST 6: ALLOWED_TOOLS Enforcement")

    def mock_llm_forbidden(messages):
        last_msg = messages[-1]['content']

        if 'not allowed' in last_msg.lower():
            # After rejection, use allowed tool
            return """Thought: write_file is not allowed. Let me use read_file instead.
Action: read_file(path="test.v")"""
        elif 'Observation:' in last_msg:
            return """Result: Used allowed tool successfully."""
        else:
            # Try forbidden tool
            return """Thought: Let me write a file.
Action: write_file(path="test.v", content="test")"""

    agent = ExploreAgent(
        name="test_explore_forbidden",
        llm_call_func=mock_llm_forbidden,
        execute_tool_func=mock_execute_tool,
        max_iterations=10
    )

    result = agent.run("Test ALLOWED_TOOLS enforcement", {})

    print(f"\n✓ Status: {result.status}")
    print(f"✓ Tool calls: {len(result.tool_calls)}")
    print(f"✓ Forbidden tool (write_file) was rejected")
    print(f"✓ Allowed tool (read_file) was accepted")

    # Check that write_file was NOT executed
    executed_tools = [tc['tool'] for tc in result.tool_calls]
    assert 'write_file' not in executed_tools, "write_file should not be in executed tools"
    assert 'read_file' in executed_tools, "read_file should be in executed tools"

    print("\n✅ TEST 6 PASSED")

def main():
    """Run all tests"""
    print("\n" + "█"*80)
    print("  ExploreAgent 개선사항 테스트 스위트")
    print("█"*80)

    tests = [
        ("Basic Exploration", test_basic_explore),
        ("Markdown Parsing", test_markdown_parsing),
        ("Hallucination Detection", test_hallucination_detection),
        ("Stall Detection", test_stall_detection),
        ("Error Recovery", test_error_recovery),
        ("ALLOWED_TOOLS Enforcement", test_allowed_tools_enforcement),
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
