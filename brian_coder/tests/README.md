# Brian Coder Test Suite

## 📊 테스트 현황

| 카테고리 | 테스트 수 | 설명 |
|---------|----------|------|
| **Unit Tests** | 141 | 개별 함수/클래스 검증 |
| **Integration Tests** | 99 | 컴포넌트 간 연동 검증 (LLM Tool Use + Memory In Context) |
| **E2E Tests** | 6 | 전체 시스템 흐름 |
| **Performance Tests** | 8 | 실행 속도 벤치마크 |
| **LLM API Tests** | 6 | API 연동 (선택적) |
| **Total** | **300** | |

---

## 🚀 빠른 실행

```bash
# 전체 테스트 (API 제외)
./run_tests.sh

# 전체 테스트 (API 포함)
./run_tests.sh --with-api

# 특정 카테고리만
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh e2e
```

---

## 📁 테스트 구조

```
tests/
├── conftest.py              # pytest 설정 및 공통 fixture
├── test_core/               # Core 모듈 단위 테스트
│   ├── test_rag_db.py       # RAG 데이터베이스 (20개)
│   ├── test_graph_lite.py   # Knowledge Graph (28개)
│   └── test_tools.py        # Tool 함수들 (22개)
├── test_lib/                # Lib 모듈 단위 테스트
│   ├── test_memory.py       # Declarative Memory (18개)
│   ├── test_procedural_memory.py  # Procedural Memory (18개)
│   ├── test_curator.py      # Knowledge Curator (11개)
│   └── test_deep_think.py   # Deep Think Engine (13개)
├── test_agents/             # Agent 단위 테스트
│   └── test_sub_agents.py   # SubAgent 권한 테스트 (11개)
├── test_integration/        # 통합 테스트
│   ├── test_rag_graph.py    # RAG ↔ Graph 연동 (4개)
│   ├── test_memory_procedural.py  # Memory 연동 (5개)
│   ├── test_deep_think_pipeline.py  # DeepThink 파이프라인 (9개)
│   ├── test_subagent_pipeline.py   # SubAgent 파이프라인 (12개)
│   ├── test_subagent_deep.py       # SubAgent 딥 연동 (11개)
│   ├── test_llm_tool_use.py        # LLM Tool Use 검증 (42개) ✨ NEW
│   └── test_memory_in_context.py   # Memory In Context 검증 (16개) ✨ NEW
├── test_performance.py      # 성능 벤치마크
├── test_e2e.py              # End-to-End 테스트
└── test_llm_api.py          # LLM API 테스트 (선택적)
```

---

## 🧪 테스트 카테고리 상세

### 1. Unit Tests (단위 테스트)

개별 모듈의 함수/클래스를 격리하여 테스트합니다.

**Core 모듈:**
- `test_rag_db.py`: Verilog/Markdown 청킹, 해시 검증, 검색
- `test_graph_lite.py`: 노드/엣지 CRUD, BM25 검색, 크레딧 추적
- `test_tools.py`: 파일 읽기/쓰기, grep, replace, plan 도구

**Lib 모듈:**
- `test_memory.py`: 선호도 관리, 프로젝트 컨텍스트, 프롬프트 포맷팅
- `test_procedural_memory.py`: 트라젝토리 빌드/검색/업데이트
- `test_curator.py`: 유해 노드 삭제, 미사용 노드 정리
- `test_deep_think.py`: 가설 생성, 병렬 추론, 점수 계산

### 2. Integration Tests (통합 테스트)

컴포넌트 간 연동을 검증합니다.

- `test_rag_graph.py`: RAG 인덱싱 → Graph 저장 → 검색
- `test_memory_procedural.py`: 선호도 → 트라젝토리 검색 영향
- `test_deep_think_pipeline.py`: 점수 계산에 모든 메모리 시스템 활용
- `test_subagent_pipeline.py`: 에이전트 권한 격리, 파이프라인 흐름
- `test_subagent_deep.py`: Mock LLM으로 실제 Agent.run() 실행
- `test_llm_tool_use.py` ✨ **NEW**: LLM이 tool을 올바르게 사용할 수 있는지 검증
  - **Tool 파싱**: 다양한 LLM 출력 형식에서 action 추출 (7개)
  - **인자 처리**: 문자열, 숫자, 이스케이프 문자 등 파싱 (6개)
  - **Tool 실행**: 파일 읽기/쓰기, 명령 실행 (6개)
  - **Multi-turn**: 여러 번의 tool 호출과 observation 처리 (3개)
  - **에러 처리**: 잘못된 tool, 문법 오류, 복구 (5개)
  - **텍스트 정제**: 마크다운, 따옴표 처리 (4개)
  - **LLM 응답**: Thought-Action 패턴, hallucinated observation (4개)
  - **Tool 연쇄**: Read-then-Write, List-then-Read (2개)
  - **Context 관리**: Message history, 대용량 출력 (2개)
  - **Usability**: Tool 등록, 호출 가능성 (3개)
- `test_memory_in_context.py` ✨ **NEW**: 메모리가 main.py 실행 환경에서 올바르게 동작하는지 검증
  - **System Prompt 통합**: 선호도 포맷팅, 프로젝트 컨텍스트 (4개)
  - **자동 추출**: 사용자 입력에서 선호도 감지 (2개)
  - **Procedural Memory**: 유사 작업 검색, 사용량 추적, 트라젝토리 저장 (3개)
  - **Graph Memory**: 자동 링킹, 저장 및 로드 (2개)
  - **실제 메시지 흐름**: 다중 턴 대화, 작업 완료 흐름 (2개)
  - **에러 처리**: 잘못된 키, 손상된 파일, 빈 상태 (3개)

### 3. E2E Tests (End-to-End)

전체 시스템 워크플로우를 테스트합니다.

- Verilog 프로젝트 인덱싱 → 검색
- 메모리 다중 세션 영속성
- 도구 체인 실행 (read → process → write)
- SubAgent 순차 워크플로우 (Explore → Execute)

### 4. Performance Tests (성능 테스트)

주요 작업의 실행 시간을 측정합니다.

- RAG 청킹 속도 (< 5초)
- Graph 노드 조회 (100개 < 0.1초)
- BM25 검색 (50개 < 0.5초)
- Memory 읽기/쓰기 성능

### 5. LLM API Tests (API 테스트)

실제 LLM API 연동을 테스트합니다. API 키가 없으면 자동 스킵됩니다.

- API 연결 테스트
- JSON 응답 파싱
- 에러 핸들링
- 임베딩 생성

---

## 🔧 사용 방법

### 기본 실행

```bash
# 전체 테스트
pytest tests/ -v

# 특정 파일
pytest tests/test_core/test_rag_db.py -v

# 특정 클래스
pytest tests/test_core/test_rag_db.py::TestVerilogChunking -v

# 특정 테스트
pytest tests/test_core/test_rag_db.py::TestVerilogChunking::test_module_extraction -v
```

### 유용한 옵션

```bash
# 실패 시 즉시 중단
pytest tests/ -x

# 마지막 실패 테스트만 재실행
pytest tests/ --lf

# 병렬 실행 (pytest-xdist 필요)
pytest tests/ -n auto

# 커버리지 리포트
pytest tests/ --cov=. --cov-report=html

# 출력 표시
pytest tests/ -v -s
```

### 카테고리별 실행

```bash
# 단위 테스트만 (빠름)
pytest tests/test_core/ tests/test_lib/ tests/test_agents/ -v

# 통합 테스트만
pytest tests/test_integration/ -v

# E2E만
pytest tests/test_e2e.py -v

# 성능 테스트만
pytest tests/test_performance.py -v

# API 테스트 제외
pytest tests/ --ignore=tests/test_llm_api.py -v
```

---

## 📝 테스트 작성 가이드

### 새 단위 테스트 추가

```python
# tests/test_core/test_new_module.py
import unittest
from new_module import NewClass

class TestNewClass(unittest.TestCase):
    def setUp(self):
        self.instance = NewClass()
    
    def tearDown(self):
        # 정리 로직
        pass
    
    def test_feature(self):
        result = self.instance.do_something()
        self.assertEqual(result, expected)
```

### 새 통합 테스트 추가

```python
# tests/test_integration/test_new_integration.py
import unittest
from module_a import A
from module_b import B

class TestABIntegration(unittest.TestCase):
    def test_a_and_b_work_together(self):
        a = A()
        b = B()
        
        result_a = a.process("data")
        result_b = b.consume(result_a)
        
        self.assertIsNotNone(result_b)
```

---

## ⚙️ 환경 설정

### 필수 패키지

```bash
pip install pytest pytest-benchmark
```

### 선택 패키지

```bash
pip install pytest-cov        # 커버리지
pip install pytest-xdist      # 병렬 실행
```

### 환경 변수

```bash
# .env 파일
EMBEDDING_DIMENSION=1024      # RAG 테스트 필수
OPENROUTER_API_KEY=...        # LLM API 테스트용 (선택)
```

---

## 🐛 트러블슈팅

### Import 에러

```bash
# conftest.py가 경로를 자동 설정합니다
# 그래도 안되면:
export PYTHONPATH=$PYTHONPATH:/path/to/brian_coder/src:/path/to/brian_coder/core:/path/to/brian_coder/lib
```

### 테스트가 너무 느림

```bash
# 임베딩 API 호출을 스킵하는 테스트 사용
pytest tests/test_core/ -v  # API 호출 없음

# 또는 skip_embeddings=True로 테스트 작성
```

### LLM API 테스트 스킵

```bash
# API 키 없으면 자동 스킵됨
# 강제 스킵하려면:
pytest tests/ --ignore=tests/test_llm_api.py
```

---

## 📈 CI/CD 통합

GitHub Actions 예시:

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: pytest tests/ --ignore=tests/test_llm_api.py -v
```
