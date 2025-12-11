#!/bin/bash
# run_tests_ci.sh - CI/CD용 테스트 스크립트
#
# GitHub Actions 등에서 사용하기 위한 최소화된 스크립트
# 종료 코드로 성공/실패 반환

set -e

echo "=== Brian Coder CI Test Runner ==="
echo ""

# 환경 설정
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src:$(pwd)/core:$(pwd)/lib:$(pwd)/agents"

# 테스트 실행
python3 -m pytest tests/ \
    --ignore=tests/test_llm_api.py \
    --tb=short \
    -q \
    --no-header

# 종료 코드 반환
exit $?
