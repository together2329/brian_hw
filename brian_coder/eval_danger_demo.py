#!/usr/bin/env python3
"""
eval()의 위험성 데모
"""

print("=" * 60)
print("⚠️  eval()의 위험성")
print("=" * 60)

# 악의적인 LLM 응답 (또는 공격자가 조작한 응답)
malicious_response = """
Action: read_file(path="config.py"); import os; os.system("echo HACKED!")
"""

print("\n악의적인 응답:")
print(malicious_response)

# 문제점: eval()은 임의의 Python 코드를 실행할 수 있음
print("\n현재 코드의 문제:")
print("eval()은 모든 Python 코드를 실행 가능!")

# 안전한 대안 1: ast.literal_eval (리터럴만 허용)
import ast

print("\n" + "=" * 60)
print("안전한 대안 1: ast.literal_eval")
print("=" * 60)

safe_args = "{'path': 'config.py'}"
try:
    result = ast.literal_eval(safe_args)
    print(f"✅ 성공: {result}")
except Exception as e:
    print(f"❌ 실패: {e}")

malicious_args = "{'path': __import__('os').system('ls')}"
try:
    result = ast.literal_eval(malicious_args)
    print(f"✅ 성공: {result}")
except Exception as e:
    print(f"✅ 차단됨: {e}")

# 안전한 대안 2: JSON
import json

print("\n" + "=" * 60)
print("안전한 대안 2: JSON 파싱")
print("=" * 60)

safe_json = '{"path": "config.py", "content": "hello"}'
result = json.loads(safe_json)
print(f"✅ 성공: {result}")

# 안전한 대안 3: 정규식 + 수동 파싱
import re

print("\n" + "=" * 60)
print("안전한 대안 3: 정규식으로 key=value 파싱")
print("=" * 60)

args_str = 'path="config.py", content="hello world"'
# key="value" 패턴 찾기
pattern = r'(\w+)="([^"]*)"'
matches = re.findall(pattern, args_str)
kwargs = {key: value for key, value in matches}
print(f"✅ 파싱 결과: {kwargs}")

print("\n" + "=" * 60)
print("결론: eval() 대신 안전한 파서를 사용하세요!")
print("=" * 60)
