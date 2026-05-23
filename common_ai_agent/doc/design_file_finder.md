# 📋 설계 문서: 스마트 파일 탐색 기능 (Smart File Finder)

## 1. 개요

사용자가 명령어/키워드/자연어를 입력하면 프로젝트 내 관련 파일을 **자동으로 탐색**하여
관련도 순으로 정렬된 파일 목록을 제공하는 기능.

### 사용 예시
```
/find uart
/find "RTL module for AXI interconnect"
/find timer_ip
/find testbench.*\.sv
```

---

## 2. 기존 시스템 분석

### 2.1 기존 검색 인프라

| 컴포넌트 | 위치 | 역할 | 한계 |
|----------|------|------|------|
| `find_files()` | `core/tools.py` | glob 패턴으로 파일명 검색 | 파일명만 검색, 내용 불가 |
| `grep_file()` | `core/tools.py` | 정규식으로 파일 내용 검색 | 패턴을 정확히 알아야 함 |
| `HybridRAG` | `core/hybrid_rag.py` | 임베딩+BM25+그래프 하이브리드 검색 | 인덱싱된 문서만 검색 |
| `SmartRAG` | `core/smart_rag.py` | RAG 결과의 관련도 자동 판단 | RAG 의존, 코드 파일 미인덱싱 |
| `/find` (기존) | `core/slash_commands.py` | 현재 미구현 | N/A |

### 2.2 차별점

**새 FileFinder가 기존 도구와 다른 점:**

1. **통합 검색**: glob(파일명) + grep(내용) + RAG(의미)를 하나의 쿼리로 통합
2. **자동 키워드 추출**: 자연어 입력에서 핵심 키워드를 자동 추출
3. **결과 랭킹**: 여러 소스의 결과를 관련도 점수로 병합/정렬
4. **매치 이유 표시**: 왜 매치되었는지(파일명/내용/의미)를 명시

---

## 3. 아키텍처 설계

```
┌─────────────────────────────────────────────────────┐
│                   사용자 입력                         │
│  /find uart  또는  /find "AXI interconnect module"   │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│            SlashCommandRegistry                       │
│         (/find → _cmd_find_handler)                   │
└──────────────┬───────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│              FileFinder (core/file_finder.py)         │
│                                                       │
│  ┌─────────────┐   ┌──────────────┐   ┌───────────┐ │
│  │ 1. Query     │   │ 2. Multi-    │   │ 3. Merge  │ │
│  │    Parser    │──▶│    Strategy  │──▶│   & Rank  │ │
│  │ (키워드추출) │   │   Search     │   │  (RRF)    │ │
│  └─────────────┘   └──────┬───────┘   └───────────┘ │
│                           │                          │
│         ┌─────────────────┼─────────────────┐        │
│         ▼                 ▼                 ▼        │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐  │
│  │ GlobSearch │   │ GrepSearch │   │  RAGSearch │  │
│  │(find_files)│   │(grep_file) │   │(HybridRAG) │  │
│  └────────────┘   └────────────┘   └────────────┘  │
└──────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────┐
│                  결과 출력 (포맷팅)                    │
│                                                       │
│  🔍 "uart" 검색 결과 (12 files found)                │
│  ─────────────────────────────────────────            │
│  1. [0.95] 📄 uart_top.sv           (파일명 매치)     │
│  2. [0.87] 📄 tb_uart.sv            (내용 매치)      │
│  3. [0.72] 📄 uart_ssot.yaml        (파일명+내용)    │
│  ...                                                  │
└──────────────────────────────────────────────────────┘
```

---

## 4. 상세 설계

### 4.1 QueryParser — 쿼리 파서

```python
@dataclass
class ParsedQuery:
    raw: str                    # 원본 입력
    keywords: List[str]         # 추출된 키워드
    glob_patterns: List[str]    # glob 패턴 (예: *.sv, testbench.*\.sv)
    is_natural_language: bool   # 자연어 여부
    file_extensions: List[str]  # 암시적 확장자 (예: "rtl module" → .sv, .v)

class QueryParser:
    def parse(self, raw_input: str) -> ParsedQuery:
        """
        입력을 분석하여 검색 전략에 필요한 정보를 추출.
        
        처리 규칙:
        1. 따옴표로 감싸진 경우 → 자연어로 처리
        2. *, ?, [가 포함된 경우 → glob 패턴으로 처리
        3. 마침표+확장자가 있는 경우 → 파일명 검색 우선
        4. 나머지 → 키워드 + 내용 검색
        """
```

### 4.2 SearchStrategy — 검색 전략

```python
class SearchResult:
    path: str           # 파일 경로
    score: float        # 관련도 점수 (0.0~1.0)
    match_type: str     # "filename" | "content" | "semantic"
    match_detail: str   # 매치된 내용 미리보기
    source: str         # "glob" | "grep" | "rag"

class GlobStrategy:
    """find_files 기반 파일명 패턴 검색"""
    
class GrepStrategy:
    """grep_file 기반 파일 내용 키워드 검색"""
    
class RAGStrategy:
    """HybridRAG 기반 의미적 검색 (인덱싱된 경우만)"""
```

### 4.3 ResultMerger — 결과 병합 및 랭킹

```python
class ResultMerger:
    """
    RRF (Reciprocal Rank Fusion)으로 여러 전략의 결과를 병합.
    
    score = Σ (1 / (k + rank_i))  for each strategy i
    k = 60 (표준 RRF 상수)
    """
```

### 4.4 FileFinder — 메인 클래스

```python
class FileFinder:
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.parser = QueryParser()
        self.strategies = [GlobStrategy(), GrepStrategy(), RAGStrategy()]
        self.merger = ResultMerger()
    
    def find(self, query: str, max_results: int = 20) -> List[SearchResult]:
        """
        통합 파일 검색.
        
        Args:
            query: 검색어 (키워드, glob 패턴, 자연어)
            max_results: 최대 결과 수
            
        Returns:
            관련도 순으로 정렬된 SearchResult 리스트
        """
        parsed = self.parser.parse(query)
        
        all_results = []
        for strategy in self.strategies:
            try:
                results = strategy.search(parsed, self.project_root)
                all_results.extend(results)
            except Exception:
                continue  # 실패한 전략은 건너뛰기
        
        merged = self.merger.merge(all_results)
        return merged[:max_results]
```

---

## 5. 통합 지점

### 5.1 SlashCommandRegistry 통합

```python
# core/slash_commands.py → _register_builtin_commands()에 추가
self.register('find', self._cmd_find,
             '관련 파일 자동 탐색: /find <키워드|명령어|자연어>',
             usage='/find <query> [-t type] [-n N]')
```

### 5.2 Tool Dispatcher 통합 (LLM용)

```python
# core/tool_dispatcher.py → available_tools에 추가
available_tools["find_related_files"] = find_related_files

# 도구 스키마
{
    "name": "find_related_files",
    "description": "Search for files related to a keyword, command, or natural language query",
    "parameters": {
        "query": {"type": "string", "description": "Search query"},
        "max_results": {"type": "integer", "default": 20}
    }
}
```

---

## 6. 파일 변경 목록

| 파일 | 작업 | 설명 |
|------|------|------|
| `core/file_finder.py` | **신규** | FileFinder 핵심 모듈 |
| `core/slash_commands.py` | 수정 | `/find` 명령어 등록 |
| `core/tool_dispatcher.py` | 수정 | `find_related_files` 도구 등록 |
| `tests/test_file_finder.py` | **신규** | 단위 테스트 |
| `doc/design_file_finder.md` | **신규** | 본 설계 문서 |

---

## 7. 고려사항

### 7.1 성능
- 대규모 프로젝트(10K+ 파일)에서는 glob → grep → RAG 순으로 실행
- RAG는 인덱싱된 경우만 실행 (미인덱싱 시 스킵)
- 타임아웃: 전체 검색 5초 이내

### 7.2 확장성
- 새로운 검색 전략을 SearchStrategy 인터페이스로 쉽게 추가 가능
- 향후 Git history 검색, 심볼 검색(cscope/ctags) 전략 추가 가능

### 7.3 UX
- 결과가 없을 경우 대안 검색어 제안
- 이전 검색 기록 유지 (/find history)
- 파이프라인 지원: `/find uart | grep testbench`
