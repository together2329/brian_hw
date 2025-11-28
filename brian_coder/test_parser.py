#!/usr/bin/env python3
"""
개선된 파서 테스트
"""

import sys
import re

# main.py에서 파서 함수 임포트
sys.path.insert(0, '.')
from main import parse_action, parse_tool_arguments, parse_value

print("=" * 70)
print("개선된 파서 테스트")
print("=" * 70)

# 테스트 1: 기본 인자
print("\n[Test 1] 기본 인자 파싱")
args_str = 'path="config.py"'
args, kwargs = parse_tool_arguments(args_str)
print(f"Input: {args_str}")
print(f"Result: args={args}, kwargs={kwargs}")
assert kwargs == {'path': 'config.py'}
print("✅ PASS")

# 테스트 2: 여러 인자
print("\n[Test 2] 여러 인자 파싱")
args_str = 'path="test.txt", content="hello world"'
args, kwargs = parse_tool_arguments(args_str)
print(f"Input: {args_str}")
print(f"Result: args={args}, kwargs={kwargs}")
assert kwargs == {'path': 'test.txt', 'content': 'hello world'}
print("✅ PASS")

# 테스트 3: Triple-quoted string
print("\n[Test 3] Triple-quoted string 파싱")
args_str = '''path="counter.v", content="""
module counter (
    input clk,
    output reg [7:0] count
);
endmodule
"""'''
args, kwargs = parse_tool_arguments(args_str)
print(f"Input: {args_str[:50]}...")
print(f"Result: path={kwargs.get('path')}")
print(f"Content length: {len(kwargs.get('content', ''))}")
assert 'module counter' in kwargs.get('content', '')
print("✅ PASS")

# 테스트 4: Action 파싱 (기본)
print("\n[Test 4] Action 파싱 - 기본")
text = 'Thought: I need to read.\nAction: read_file(path="config.py")'
tool_name, args_str = parse_action(text)
print(f"Input: {text}")
print(f"Result: tool={tool_name}, args={args_str}")
assert tool_name == "read_file"
assert 'path="config.py"' in args_str
print("✅ PASS")

# 테스트 5: Action 파싱 (Triple-quote)
print("\n[Test 5] Action 파싱 - Triple-quote")
text = '''Thought: Create file.
Action: write_file(path="test.v", content="""
module test;
endmodule
""")'''
tool_name, args_str = parse_action(text)
print(f"Input: {text[:50]}...")
print(f"Result: tool={tool_name}, args_len={len(args_str)}")
assert tool_name == "write_file"
assert '"""' in args_str
print("✅ PASS")

# 테스트 6: 중첩 괄호
print("\n[Test 6] 중첩 괄호")
text = 'Action: run_command(command="echo (hello)")'
tool_name, args_str = parse_action(text)
print(f"Input: {text}")
print(f"Result: tool={tool_name}, args={args_str}")
assert tool_name == "run_command"
assert 'echo (hello)' in args_str
print("✅ PASS")

# 테스트 7: Escape sequences
print("\n[Test 7] Escape sequences")
args_str = r'path="test\nfile.txt", content="Line1\nLine2"'
args, kwargs = parse_tool_arguments(args_str)
print(f"Input: {args_str}")
print(f"Result: {kwargs}")
assert '\n' in kwargs['path']
assert '\n' in kwargs['content']
print("✅ PASS")

# 테스트 8: 숫자 인자
print("\n[Test 8] 숫자 인자")
args_str = 'count=42, value=3.14'
args, kwargs = parse_tool_arguments(args_str)
print(f"Input: {args_str}")
print(f"Result: {kwargs}")
assert kwargs['count'] == 42
assert kwargs['value'] == 3.14
print("✅ PASS")

print("\n" + "=" * 70)
print("모든 테스트 통과! ✅")
print("=" * 70)
