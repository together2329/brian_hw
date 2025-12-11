#!/bin/bash
# run_tests.sh - Brian Coder 테스트 실행 스크립트
#
# 사용법:
#   ./run_tests.sh              # 전체 테스트 (API 제외)
#   ./run_tests.sh --with-api   # 전체 테스트 (API 포함)
#   ./run_tests.sh --coverage   # 전체 테스트 + 커버리지 리포트
#   ./run_tests.sh unit         # 단위 테스트만
#   ./run_tests.sh integration  # 통합 테스트만
#   ./run_tests.sh e2e          # E2E 테스트만
#   ./run_tests.sh performance  # 성능 테스트만
#   ./run_tests.sh quick        # 빠른 테스트 (Core만)

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트로 이동
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 헤더 출력
echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           Brian Coder Test Runner                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 도움말
show_help() {
    echo "사용법: ./run_tests.sh [옵션]"
    echo ""
    echo "옵션:"
    echo "  (없음)        전체 테스트 실행 (API 제외)"
    echo "  --with-api    전체 테스트 실행 (API 포함)"
    echo "  --coverage    전체 테스트 + 커버리지 리포트 생성"
    echo "  unit          단위 테스트만 (test_core, test_lib, test_agents)"
    echo "  integration   통합 테스트만 (test_integration)"
    echo "  e2e           E2E 테스트만"
    echo "  performance   성능 테스트만"
    echo "  quick         빠른 테스트 (test_core만)"
    echo "  --help        이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  ./run_tests.sh                  # 일반 실행"
    echo "  ./run_tests.sh --coverage       # 커버리지 리포트 생성"
    echo "  ./run_tests.sh unit -x          # 단위 테스트, 실패 시 중단"
    echo "  ./run_tests.sh quick -v         # 빠른 테스트, 상세 출력"
}

# 테스트 실행 함수
run_tests() {
    local test_path=$1
    local description=$2
    local enable_coverage=$3
    shift 3
    local extra_args="$@"

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}▶ ${description}${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if [ "$enable_coverage" = "coverage" ]; then
        python3 -m pytest $test_path -v --cov=src --cov=core --cov=lib --cov=agents --cov-report=html --cov-report=term-missing $extra_args
        echo ""
        echo -e "${GREEN}✓ 커버리지 리포트 생성됨: htmlcov/index.html${NC}"
    else
        python3 -m pytest $test_path -v $extra_args
    fi

    echo ""
}

# 인자 처리
CATEGORY="${1:-all}"
shift 2>/dev/null || true

case "$CATEGORY" in
    --help|-h)
        show_help
        exit 0
        ;;

    --with-api)
        echo -e "${GREEN}전체 테스트 실행 (API 포함)${NC}"
        run_tests "tests/" "All Tests (including API)" "" "$@"
        ;;

    --coverage)
        echo -e "${GREEN}전체 테스트 실행 + 커버리지 리포트${NC}"
        run_tests "tests/" "All Tests with Coverage (excluding API)" "coverage" "--ignore=tests/test_llm_api.py" "$@"
        ;;

    unit)
        echo -e "${GREEN}단위 테스트 실행${NC}"
        run_tests "tests/test_core/ tests/test_lib/ tests/test_agents/" "Unit Tests" "" "$@"
        ;;

    integration)
        echo -e "${GREEN}통합 테스트 실행${NC}"
        run_tests "tests/test_integration/" "Integration Tests" "" "$@"
        ;;

    e2e)
        echo -e "${GREEN}E2E 테스트 실행${NC}"
        run_tests "tests/test_e2e.py" "End-to-End Tests" "" "$@"
        ;;

    performance)
        echo -e "${GREEN}성능 테스트 실행${NC}"
        run_tests "tests/test_performance.py" "Performance Tests" "" "$@"
        ;;

    quick)
        echo -e "${GREEN}빠른 테스트 실행 (Core만)${NC}"
        run_tests "tests/test_core/" "Quick Tests (Core only)" "" "$@"
        ;;

    all|*)
        echo -e "${GREEN}전체 테스트 실행 (API 제외)${NC}"
        run_tests "tests/" "All Tests (excluding API)" "" "--ignore=tests/test_llm_api.py" "$@"
        ;;
esac

# 완료 메시지
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    테스트 완료! ✓                             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
