#!/usr/bin/env python3
"""
Sub-Agent System Test Script

간단한 테스트 케이스들을 실행하여 Sub-Agent 시스템이 제대로 작동하는지 확인합니다.
"""

import os
import sys

# Common AI Agent 디렉토리를 Python path에 추가 (tests 폴더의 상위 디렉토리)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_react_agent
import config
from iteration_control import IterationTracker

def test_sub_agents():
    """Sub-Agent 시스템 테스트"""

    print("=" * 60)
    print("Sub-Agent System Test")
    print("=" * 60)
    print(f"ENABLE_SUB_AGENTS: {config.ENABLE_SUB_AGENTS}")
    print(f"SUB_AGENT_PARALLEL_ENABLED: {config.SUB_AGENT_PARALLEL_ENABLED}")
    print(f"SUB_AGENT_MAX_ITERATIONS: {config.SUB_AGENT_MAX_ITERATIONS}")
    print("=" * 60)
    print()

    if not config.ENABLE_SUB_AGENTS:
        print("❌ ENABLE_SUB_AGENTS is False. Please set it to True in .env file.")
        return

    # Test Case 1: Simple Exploration Task
    print("📝 Test Case 1: Exploration Task")
    print("-" * 60)
    test_input_1 = "sub_agents 디렉토리에 어떤 파일들이 있는지 확인하고 각 파일의 역할을 요약해줘"

    print(f"Input: {test_input_1}")
    print()

    try:
        tracker = IterationTracker(max_iterations=config.SUB_AGENT_MAX_ITERATIONS)
        messages = [{"role": "user", "content": test_input_1}]
        
        updated_messages = run_react_agent(messages, tracker, test_input_1)
        
        # Extract last message content
        result = updated_messages[-1]["content"] if updated_messages else "No result"
        
        print("\n✅ Test Case 1 Completed")
        print(f"Result preview: {result[:200]}...")
    except Exception as e:
        print(f"\n❌ Test Case 1 Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

    # Test Case 2: Planning Task
    print("\n📝 Test Case 2: Planning Task")
    print("-" * 60)
    test_input_2 = "새로운 기능을 추가하려면 어떤 단계로 진행해야 할지 계획을 세워줘: 사용자가 명령어를 입력하면 자동으로 관련 파일을 찾아주는 기능"

    print(f"Input: {test_input_2}")
    print()

    try:
        tracker = IterationTracker(max_iterations=config.SUB_AGENT_MAX_ITERATIONS)
        messages = [{"role": "user", "content": test_input_2}]
        
        updated_messages = run_react_agent(messages, tracker, test_input_2)
        
        # Extract last message content
        result = updated_messages[-1]["content"] if updated_messages else "No result"
        
        print("\n✅ Test Case 2 Completed")
        print(f"Result preview: {result[:200]}...")
    except Exception as e:
        print(f"\n❌ Test Case 2 Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_sub_agents()
