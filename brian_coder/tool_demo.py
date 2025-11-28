#!/usr/bin/env python3
"""
Tool Call 동작 원리 데모
"""

import re

# 1. LLM이 생성한 텍스트 (시뮬레이션)
llm_response = """
Thought: I need to read the config.py file to see the API key.
Action: read_file(path="config.py")
"""

print("=" * 60)
print("1. LLM이 생성한 텍스트:")
print("=" * 60)
print(llm_response)

# 2. 정규식으로 패턴 찾기
print("\n" + "=" * 60)
print("2. 정규식 파싱:")
print("=" * 60)

match = re.search(r"Action:\s*(\w+)\((.*)\)", llm_response, re.DOTALL)
if match:
    tool_name = match.group(1)
    args_str = match.group(2)
    print(f"tool_name = '{tool_name}'")
    print(f"args_str = '{args_str}'")

# 3. eval()로 인자 파싱
print("\n" + "=" * 60)
print("3. eval()로 인자 파싱:")
print("=" * 60)

def _proxy(*args, **kwargs):
    """인자를 튜플로 반환하는 헬퍼"""
    return args, kwargs

print(f"실행할 코드: _proxy({args_str})")
parsed_args, parsed_kwargs = eval(f"_proxy({args_str})", {"_proxy": _proxy})
print(f"parsed_args = {parsed_args}")
print(f"parsed_kwargs = {parsed_kwargs}")

# 4. 실제 함수 호출 시뮬레이션
print("\n" + "=" * 60)
print("4. 실제 함수 호출:")
print("=" * 60)

def read_file(path):
    """실제 Tool 함수"""
    return f"[파일 내용: {path}]"

AVAILABLE_TOOLS = {
    "read_file": read_file
}

func = AVAILABLE_TOOLS[tool_name]
result = func(*parsed_args, **parsed_kwargs)
print(f"결과: {result}")

# 5. 복잡한 예시
print("\n" + "=" * 60)
print("5. 복잡한 인자 예시:")
print("=" * 60)

complex_response = """
Action: write_file(path="/tmp/test.py", content="print('Hello')")
"""

match2 = re.search(r"Action:\s*(\w+)\((.*)\)", complex_response, re.DOTALL)
if match2:
    tool_name2 = match2.group(1)
    args_str2 = match2.group(2)
    print(f"tool_name = '{tool_name2}'")
    print(f"args_str = '{args_str2}'")

    parsed_args2, parsed_kwargs2 = eval(f"_proxy({args_str2})", {"_proxy": _proxy})
    print(f"parsed_kwargs = {parsed_kwargs2}")

print("\n" + "=" * 60)
print("데모 완료!")
print("=" * 60)
