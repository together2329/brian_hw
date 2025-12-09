#!/usr/bin/env python3
"""
Sub-Agents Debug Test Script
DEBUG_SUBAGENT 환경변수가 true일 때 상세 로그가 출력되는지 테스트
"""

import os
import sys

# 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 강제로 DEBUG 모드 활성화 (테스트용)
os.environ['DEBUG_SUBAGENT'] = 'true'

from brian_coder.sub_agents import (
    DEBUG_SUBAGENT, 
    debug_log,
    Orchestrator,
    ExploreAgent,
    PlanAgent,
    ExecuteAgent
)

print("=" * 60)
print(f"DEBUG_SUBAGENT = {DEBUG_SUBAGENT}")
print("=" * 60)

# 간단한 mock 함수들
def mock_llm_call(messages):
    """가짜 LLM 응답"""
    return """Thought: I need to analyze the task.
Result: This is a test response from mock LLM."""

def mock_execute_tool(tool_name, args):
    """가짜 도구 실행"""
    debug_log("MockTool", f"Executing: {tool_name}({args})")
    return f"Mock result for {tool_name}"

print("\n" + "=" * 60)
print("TEST 1: ExploreAgent.run() with DEBUG")
print("=" * 60)

explore_agent = ExploreAgent(
    name="test_explore",
    llm_call_func=mock_llm_call,
    execute_tool_func=mock_execute_tool
)

result = explore_agent.run(
    task="Find all Verilog files in the project",
    context={"project_path": "/test/path"}
)

print(f"\n[Result Status]: {result.status}")
print(f"[Result Output Length]: {len(result.output)}")

print("\n" + "=" * 60)
print("TEST 2: PlanAgent.run() with DEBUG")
print("=" * 60)

plan_agent = PlanAgent(
    name="test_plan",
    llm_call_func=mock_llm_call,
    execute_tool_func=mock_execute_tool
)

result = plan_agent.run(
    task="Create a plan for implementing async FIFO",
    context={}
)

print(f"\n[Result Status]: {result.status}")

print("\n" + "=" * 60)
print("TEST 3: Orchestrator.run() with DEBUG")
print("=" * 60)

orchestrator = Orchestrator(
    llm_call_func=mock_llm_call,
    execute_tool_func=mock_execute_tool
)

result = orchestrator.run(
    task="Simple test task",
    context={}
)

print(f"\n[Final Status]: {result.final_output[:200] if result.final_output else 'No output'}...")
print("\n" + "=" * 60)
print("DEBUG TEST COMPLETE")
print("=" * 60)
