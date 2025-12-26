#!/usr/bin/env python3
"""
DEBUG_SUBAGENT 설정 테스트

.config 파일의 DEBUG_SUBAGENT 설정이 제대로 로드되는지 확인
"""

import os
import sys

# Add brian_coder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brian_coder'))

print("="*80)
print("  DEBUG_SUBAGENT 설정 테스트")
print("="*80)

# Test 1: Check .config file
print("\n[TEST 1] .config 파일 확인")
config_path = os.path.join(os.path.dirname(__file__), 'brian_coder', '.config')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config_content = f.read()
        if 'DEBUG_SUBAGENT=true' in config_content:
            print("✅ .config 파일에 DEBUG_SUBAGENT=true 설정 존재")
        else:
            print("❌ .config 파일에 DEBUG_SUBAGENT 설정이 없음")
else:
    print("❌ .config 파일을 찾을 수 없음")

# Test 2: Check config.py
print("\n[TEST 2] config.py 모듈 확인")
try:
    from src import config
    if hasattr(config, 'DEBUG_SUBAGENT'):
        print(f"✅ config.DEBUG_SUBAGENT 존재: {config.DEBUG_SUBAGENT}")
    else:
        print("❌ config.DEBUG_SUBAGENT 속성이 없음")
except ImportError as e:
    print(f"❌ config.py import 실패: {e}")

# Test 3: Check base.py
print("\n[TEST 3] base.py 모듈 확인")
try:
    from agents.sub_agents import base
    print(f"✅ base.DEBUG_SUBAGENT: {base.DEBUG_SUBAGENT}")
except ImportError as e:
    print(f"❌ base.py import 실패: {e}")

# Test 4: Check debug_log function
print("\n[TEST 4] debug_log 함수 테스트")
try:
    from agents.sub_agents.base import debug_log

    print("\n--- debug_log 출력 테스트 ---")
    debug_log("TEST", "이것은 테스트 메시지입니다")
    debug_log("TEST", "데이터와 함께", {"key": "value", "number": 123})
    print("--- debug_log 테스트 완료 ---")

    if base.DEBUG_SUBAGENT:
        print("\n✅ DEBUG_SUBAGENT=true이므로 위에 색상 로그가 출력되어야 합니다")
    else:
        print("\n⚠️  DEBUG_SUBAGENT=false이므로 로그가 출력되지 않았습니다")
        print("    .config 파일에서 DEBUG_SUBAGENT=true로 설정하세요")

except Exception as e:
    print(f"❌ debug_log 테스트 실패: {e}")

print("\n" + "="*80)
print("  테스트 완료")
print("="*80 + "\n")
