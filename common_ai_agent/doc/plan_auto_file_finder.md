# 자동 파일 검색 기능 (`/find`) — 상세 구현 계획서

> **Feature**: 사용자가 명령어를 입력하면 자동으로 관련 파일을 찾아주는 기능  
> **Command**: `/find <자연어 쿼리>`  
> **Status**: Planning  
> **Author**: ATLAS Agent  

---

## 1. 개요 (Overview)

사용자가 `/find` 명령어와 함께 자연어 키워드를 입력하면, 프로젝트 내에서 관련성이 높은 파일을 **자동으로 검색·순위화·출력**하는 기능이다. 기존의 `find_files`, `grep_file`, `list_dir` 툴은 개별 호출이 필요하며, 사용자가 "어떤 툴에 어떤 파라미터를 줘야 할지" 알아야 한다. `/find`는 이 과정을 하나의 명령어로 통합한다.

### 예시 사용법

```
/find uart 관련 RTL 파일
/find 테스트벤치
/find 타이머 모듈 중 인터페이스 정의
/find yaml 설정 파일
/find converge loop state
/find DMA 컨트롤러 버스 인터페이스
/find .py 파일 중 리스크 관련
```

### 기대 효과

| Before | After |
|--------|-------|
| `find_files("*.sv")` → 결과 확인 → `grep_file("uart", "src/")` → 수동 필터링 | `/find uart RTL` → 즉시 정렬된 결과 |
| 툴 이름·문법을 알아야 함 | 자연어 한 줄로 검색 |
| 프로젝트 구조를 미리 알아야 함 | 구조 모르더라도 키워드로 탐색 가능 |

---

## 2. 아키텍처 (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                      User Input                             │
│              "/find uart 관련 RTL 파일"                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │   /find Command Handler │  ← core/slash_commands.py
          │   (_cmd_find)           │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Intent Parser         │  ← NEW: core/file_finder.py
          │   ├─ 키워드 추출         │
          │   ├─ 파일 타입 유추      │
          │   ├─ 디렉토리 힌트       │
          │   └─ 검색 전략 결정      │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   File Search Engine    │  ← NEW: core/file_finder.py
          │   ├─ 파일명 패턴 매칭   │
          │   ├─ 내용 그렙 (grepping)│
          │   ├─ 프로젝트 구조 활용  │
          │   └─ 결과 병합 & 중복제거│
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Ranker & Formatter    │  ← NEW: core/file_finder.py
          │   ├─ 관련도 점수 계산    │
          │   ├─ 파일 메타정보 수집  │
          │   └─ 컬러 포맷팅 출력   │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │   Result Display        │
          │   📄 uart_tx.sv         │
          │   📄 uart_rx.sv         │
          │   📄 yaml/uart.ssot.yaml│
          └─────────────────────────┘
```

---

## 3. 구현 단계 (Implementation Phases)

### Phase 1: 명령어 등록 & 기본 스켈레톤 (Command Registration)

**목표**: `/find` 명령어를 슬래시 커맨드로 등록하고, 기본 파싱·검색 루틴을 구현한다.

#### 수정 파일

| 파일 | 변경 내용 |
|------|-----------|
| `core/slash_commands.py` | `_cmd_find()` 핸들러 등록 + 구현 |
| `core/file_finder.py` | **NEW** — 검색 엔진 전체 로직 |

#### 상세 설계

**1) `core/slash_commands.py` — 명령어 등록**

```python
# _register_builtin_commands() 에 추가:
self.register('find', self._cmd_find,
             '스마트 파일 검색: /find <키워드> (자연어 가능)',
             aliases=['f', 'search'])
```

**2) `_cmd_find(self, args: str) -> str` 핸들러**

```python
def _cmd_find(self, args: str) -> str:
    if not args.strip():
        return (
            "Usage: /find <keyword or phrase>\n"
            "Examples:\n"
            "  /find uart RTL\n"
            "  /find testbench\n"
            "  /find yaml config\n"
            "  /find DMA controller interface"
        )
    from core.file_finder import smart_find
    return smart_find(args.strip())
```

---

### Phase 2: 인텐트 파서 (Intent Parser)

**목표**: 자연어 입력에서 검색 의도를 구조화된 쿼리로 변환한다.

#### 설계 (`core/file_finder.py` 내부)

```python
@dataclass
class SearchIntent:
    keywords: List[str]        # 핵심 키워드 ["uart", "rtl"]
    file_extensions: List[str] # 유추된 확장자 [".sv", ".v"]
    directory_hints: List[str] # 디렉토리 힌트 ["rtl", "tb"]
    content_patterns: List[str]# 내용 검색 패턴 ["uart"]
    search_mode: str           # "filename" | "content" | "both"
```

#### 키워드 → 파일 타입 매핑 테이블

```python
_TYPE_KEYWORDS = {
    # RTL
    "rtl":           {"ext": [".sv", ".v"],    "dirs": ["rtl"]},
    "verilog":       {"ext": [".sv", ".v"],    "dirs": ["rtl"]},
    "systemverilog": {"ext": [".sv"],          "dirs": ["rtl"]},
    "module":        {"ext": [".sv", ".v"],    "dirs": ["rtl"]},

    # Testbench
    "테스트벤치":     {"ext": [".sv", ".v", ".py"], "dirs": ["tb", "tc"]},
    "testbench":     {"ext": [".sv", ".v", ".py"], "dirs": ["tb", "tc"]},
    "tb":            {"ext": [".sv", ".v"],    "dirs": ["tb"]},

    # Config / YAML
    "yaml":          {"ext": [".yaml", ".yml"],"dirs": ["yaml"]},
    "config":        {"ext": [".yaml", ".yml", ".json", ".toml"], "dirs": ["yaml"]},
    "설정":          {"ext": [".yaml", ".yml"], "dirs": ["yaml"]},
    "ssot":          {"ext": [".yaml", ".yml"], "dirs": ["yaml"]},

    # Python
    "python":        {"ext": [".py"],          "dirs": []},
    "스크립트":       {"ext": [".py", ".sh"],   "dirs": ["scripts"]},
    "script":        {"ext": [".py", ".sh"],   "dirs": ["scripts"]},

    # Docs
    "문서":          {"ext": [".md", ".txt", ".rst"], "dirs": ["doc", "docs"]},
    "doc":           {"ext": [".md", ".txt"],   "dirs": ["doc", "docs"]},
    "markdown":      {"ext": [".md"],           "dirs": ["doc", "docs"]},

    # Simulation
    "simulation":    {"ext": [".sv", ".py"],    "dirs": ["sim", "tb"]},
    "sim":           {"ext": [],                "dirs": ["sim"]},

    # Constraints
    "sdc":           {"ext": [".sdc"],          "dirs": ["sdc"]},
    "constraint":    {"ext": [".sdc", ".xdc"],  "dirs": ["sdc"]},
}
```

#### 파싱 알고리즘 (의사코드)

```
function parse_intent(query: str) -> SearchIntent:
    tokens = query.lower().split()
    
    keywords = []
    extensions = []
    dir_hints = []
    content_patterns = []
    
    for token in tokens:
        if token in _TYPE_KEYWORDS:
            extensions += _TYPE_KEYWORDS[token]["ext"]
            dir_hints += _TYPE_KEYWORDS[token]["dirs"]
        elif token starts with ".":
            extensions.append(token)
        else:
            keywords.append(token)
            content_patterns.append(token)
    
    # 확장자가 없으면 → content 검색 중심
    # 확장자가 있으면 → filename 검색 중심
    search_mode = "filename" if extensions else "both"
    
    return SearchIntent(keywords, extensions, dir_hints, content_patterns, search_mode)
```

---

### Phase 3: 파일 검색 엔진 (File Search Engine)

**목표**: SearchIntent를 기반으로 프로젝트 내 파일을 다각도로 검색한다.

#### 검색 전략

| 전략 | 설명 | 구현 |
|------|------|------|
| **S1: 파일명 패턴** | `glob`으로 파일명에 키워드가 포함된 파일 찾기 | `fnmatch`, `pathlib.glob` |
| **S2: 확장자 필터** | 유추된 확장자로 파일 필터링 | `endswith()` |
| **S3: 디렉토리 힌트** | IP 표준 디렉토리 구조 활용 | `IP_SUBDIRS` 매핑 |
| **S4: 내용 그렙** | 파일 내용에서 키워드 검색 | `open() + readline()` (빠른 라인 스캔) |
| **S5: 프로젝트 구조** | ATLAS IP 표준 레이아웃 인식 | `ATLAS_PROJECT_ROOT`, `ATLAS_ACTIVE_IP` |

#### 검색 범위 결정 로직

```python
def _get_search_roots() -> List[Path]:
    """검색 루트 디렉토리 결정"""
    roots = []
    
    # 1. ATLAS active IP (최우선)
    ip_root = os.environ.get("ATLAS_IP_ROOT", "")
    if ip_root and os.path.isdir(ip_root):
        roots.append(Path(ip_root))
    
    # 2. ATLAS project root
    proj_root = os.environ.get("ATLAS_PROJECT_ROOT", "")
    if proj_root and os.path.isdir(proj_root):
        roots.append(Path(proj_root))
    
    # 3. 현재 작업 디렉토리
    roots.append(Path.cwd())
    
    # 4. ATLAS 소스 트리 (core/, src/, workflow/ 등)
    atlas_home = os.environ.get("COMMON_AI_AGENT_HOME", "")
    if atlas_home and os.path.isdir(atlas_home):
        roots.append(Path(atlas_home))
    
    return roots
```

#### 파일 스캔 최적화

```python
# 제외 디렉토리 (검색 속도 향상)
_EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".pytest_cache",
    ".session", ".omx", ".omc", ".rag", ".deep_test",
    "venv", ".venv", "env",
}

# 최대 검색 파일 수 (성능 가드)
_MAX_SCAN_FILES = 2000

# 최대 결과 수
_MAX_RESULTS = 30
```

#### 멀티전략 검색 구현

```python
def _search_by_strategy(intent: SearchIntent, roots: List[Path]) -> List[SearchResult]:
    results = {}  # path -> SearchResult (중복 방지)
    
    # S1: 파일명 패턴 매칭
    for keyword in intent.keywords:
        for root in roots:
            for ext in (intent.file_extensions or _ALL_EXTENSIONS):
                pattern = f"**/*{keyword}*{ext}"
                for match in root.glob(pattern):
                    _add_result(results, match, score=10, strategy="filename")
    
    # S2: 디렉토리 힌트 + 키워드
    for dir_hint in intent.directory_hints:
        for root in roots:
            target_dir = root / dir_hint
            if target_dir.is_dir():
                for f in target_dir.iterdir():
                    if f.is_file():
                        _add_result(results, f, score=5, strategy="dir_hint")
    
    # S3: 내용 그렙 (키워드가 파일 내용에 포함된 경우)
    if intent.search_mode in ("content", "both"):
        for keyword in intent.content_patterns:
            _grep_files(keyword, roots, results, intent.file_extensions)
    
    return sorted(results.values(), key=lambda r: r.score, reverse=True)[:_MAX_RESULTS]
```

---

### Phase 4: 순위 매기기 & 결과 포맷팅 (Ranking & Formatting)

**목표**: 검색 결과를 관련도 순으로 정렬하고, 가독성 높은 형태로 출력한다.

#### 점수 산정 공식

```python
def _compute_score(filepath: Path, intent: SearchIntent) -> float:
    score = 0.0
    name = filepath.name.lower()
    parts = filepath.parts
    
    # 1. 파일명 키워드 매칭 (+15 per keyword in filename)
    for kw in intent.keywords:
        if kw in name:
            score += 15
    
    # 2. 확장자 일치 (+10)
    if any(name.endswith(ext) for ext in intent.file_extensions):
        score += 10
    
    # 3. 디렉토리 힌트 일치 (+8)
    for hint in intent.directory_hints:
        if hint in parts:
            score += 8
    
    # 4. 파일명 시작 부분 매칭 보너스 (+5)
    for kw in intent.keywords:
        if name.startswith(kw):
            score += 5
    
    # 5. ATLAS 표준 경로 보너스 (+3)
    atlas_std_dirs = {"rtl", "tb", "yaml", "tc", "sim", "doc", "sdc"}
    for d in parts:
        if d in atlas_std_dirs:
            score += 3
    
    # 6. 숨김 파일 / 빌드 아티팩트 페널티 (-5)
    if name.startswith(".") or name.endswith(".pyc"):
        score -= 5
    
    # 7. 깊이 페널티 (너무 깊은 경로는 낮은 순위)
    depth = len(parts) - 1
    if depth > 4:
        score -= (depth - 4) * 2
    
    return score
```

#### 결과 포맷팅

```
🔍 Search: "uart RTL" — 5 results

  #  Score  Type  Path
  1  33.0   📄    rtl/uart_tx.sv           (120 lines)
  2  33.0   📄    rtl/uart_rx.sv           (98 lines)
  3  28.0   📄    rtl/uart_top.sv          (245 lines)
  4  23.0   📄    tb/uart_tb.sv            (180 lines)
  5  18.0   📄    yaml/uart.ssot.yaml      (42 lines)

💡 Use: read_file("rtl/uart_tx.sv") to view a file
```

---

### Phase 5: 고급 기능 (Advanced Features)

#### 5a. 검색 히스토리 & 캐싱

```python
# 직전 검색 결과 저장 (빠른 재접근)
_find_cache = {
    "last_query": "",
    "last_results": [],
    "index": {},  # path -> index for quick ref
}

# /find #3 → 마지막 검색 결과의 3번째 파일 열기
# /find -l  → 마지막 검색 결과 다시 보기
```

#### 5b. 프로젝트 컨텍스트 인식

```python
def _get_project_context() -> dict:
    """현재 프로젝트 구조를 분석하여 검색 컨텍스트 제공"""
    return {
        "ip_name": os.environ.get("ATLAS_ACTIVE_IP", ""),
        "project_root": os.environ.get("ATLAS_PROJECT_ROOT", ""),
        "known_modules": _scan_module_names(),  # .sv 파일에서 module 이름 스캔
        "ip_subdirs": _detect_ip_layout(),       # 존재하는 IP 서브디렉토리 감지
    }
```

#### 5c. 퍼지 매칭 (Fuzzy Matching)

```python
def _fuzzy_match(query: str, target: str) -> float:
    """Levenshtein 거리 기반 퍼지 매칭 (오타 허용)"""
    # 간단한 구현: 시퀀스 매칭比率
    from difflib import SequenceMatcher
    return SequenceMatcher(None, query.lower(), target.lower()).ratio()
```

---

## 4. 파일 변경 요약 (File Change Summary)

### 신규 파일

| 파일 | 설명 | 예상 라인 수 |
|------|------|------------|
| `core/file_finder.py` | 검색 엔진 전체 (인텐트 파서 + 검색 + 랭킹 + 포맷) | ~400 lines |

### 수정 파일

| 파일 | 변경 내용 | 예상 변경 라인 수 |
|------|----------|-----------------|
| `core/slash_commands.py` | `_cmd_find()` 핸들러 등록 + 구현 | ~25 lines |

### 수정 없음 (참조만)

| 파일 | 이유 |
|------|------|
| `core/tools.py` | `_resolve_asset_path()`, `_IP_SUBDIRS` 참조 |
| `core/tool_dispatcher.py` | `/find`는 툴이 아닌 슬래시 커맨드이므로 변경 불필요 |
| `src/config.py` | 검색 관련 설정 추가 가능 (선택) |

---

## 5. 의존성 (Dependencies)

### 외부 라이브러리 — **없음**

모든 기능이 Python 표준 라이브러리로 구현 가능하다:
- `pathlib` — 파일 시스템 순회
- `fnmatch` — 파일명 패턴 매칭
- `difflib` — 퍼지 매칭 (SequenceMatcher)
- `os`, `re` — 경로 처리, 정규식
- `dataclasses` — 구조체 정의

### 내부 의존

```python
# core/file_finder.py
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import os
import re
import fnmatch
from difflib import SequenceMatcher

# lib/display.py (기존)
from lib.display import Color
```

---

## 6. 테스트 계획 (Test Plan)

### 단위 테스트

| 테스트 케이스 | 입력 | 기대 결과 |
|--------------|------|----------|
| 빈 입력 | `/find` | 사용법 안내 출력 |
| 단일 키워드 | `/find uart` | 파일명에 "uart" 포함된 파일 |
| 파일타입 키워드 | `/find RTL` | .sv/.v 파일 우선 |
| 복합 키워드 | `/find uart RTL` | uart + RTL 교집합 |
| 한글 키워드 | `/find 테스트벤치` | tb/ 디렉토리 내 파일 |
| 확장자 명시 | `/find .yaml` | yaml 파일만 |
| 내용 검색 | `/find converge loop` | 내용에 converge 포함 파일 |
| 존재하지 않는 키워드 | `/find xyzabc123` | "결과 없음" 메시지 |
| ATLAS IP 컨텍스트 | `/find ssot` (IP 세션 내) | yaml/*.ssot.yaml 우선 |
| 퍼지 매칭 | `/find uart_tx` (오타: uatr_tx) | uart_tx.sv 여전히 검색 |

### 통합 테스트

| 시나리오 | 설명 |
|----------|------|
| 실제 IP 디렉토리에서 검색 | `uart/` IP 내에서 `/find uart` 실행 |
| 대규모 프로젝트 | 파일 수 > 1000개일 때 성능 확인 |
| 다중 루트 | ATLAS_PROJECT_ROOT + cwd 가 다른 경우 |
| `/find` 후 `read_file` 연동 | 결과 경로를 그대로 `read_file`에 사용 |

---

## 7. 성능 목표 (Performance Targets)

| 지표 | 목표 | 근거 |
|------|------|------|
| 검색 시간 (파일 < 500) | < 1초 | `pathlib.glob` + 라인 스캔 |
| 검색 시간 (파일 500~2000) | < 3초 | 디렉토리 제외 + `_MAX_SCAN_FILES` 가드 |
| 메모리 사용 | < 50MB | 결과는 경로+메타만 유지 |
| 결과 수 | 최대 30개 | `_MAX_RESULTS = 30` |

---

## 8. 확장 가능성 (Future Enhancements)

| 기능 | Phase | 설명 |
|------|-------|------|
| RAG 연동 | v2 | `core/smart_rag.py` / `core/hybrid_rag.py` 활용한 시맨틱 검색 |
| 파일 인덱스 캐시 | v2 | `.rag/` 디렉토리에 파일 인덱스 저장, 증분 업데이트 |
| LLM 기반 인텐트 파싱 | v3 | 복잡한 자연어 → LLM 호출로 검색 쿼리 생성 |
| 대화형 탐색 | v3 | `/find` 결과에서 ↑↓ 선택 → 자동 `read_file` |
| 워크스페이스별 검색 | v3 | `/find --workspace=uart` 멀티 IP 검색 |
| 검색 결과 필터링 | v2 | `/find uart | grep tx` 파이프라인 |

---

## 9. 수용 기준 (Acceptance Criteria)

### 필수 (Must Have)

- [ ] `/find <키워드>` 명령어가 정상 등록되고 `/help`에 표시됨
- [ ] `/find uart` 입력 시 파일명에 "uart"가 포함된 파일이 관련도 순으로 출력됨
- [ ] `/find RTL` 입력 시 `.sv`, `.v` 확장자 파일이 우선 검색됨
- [ ] 한글 키워드 입력이 정상 동작함 (예: `/find 테스트벤치`)
- [ ] ATLAS IP 세션에서 `/find` 실행 시 올바른 루트에서 검색됨
- [ ] 검색 결과에 파일 경로, 줄 수, 관련도 점수가 표시됨
- [ ] 빈 입력 시 사용법 안내가 출력됨
- [ ] 결과가 없을 때 명확한 "결과 없음" 메시지가 출력됨
- [ ] 성능 목표 달성 (1000개 파일 기준 < 3초)
- [ ] 외부 라이브러리 의존성 없음 (Python 표준 라이브러리만 사용)

### 권장 (Should Have)

- [ ] `/find -l` (마지막 검색 결과 재표시) 지원
- [ ] 퍼지 매칭으로 오타 허용
- [ ] 디렉토리 힌트 자동 적용 (예: "testbench" → `tb/` 우선 검색)
- [ ] 숨김 파일 / 빌드 아티팩트 자동 제외

### 선택 (Nice to Have)

- [ ] 검색 결과 캐싱 (반복 검색 최적화)
- [ ] `/find #N` 으로 N번째 결과 파일 바로 열기
- [ ] 프로젝트 구조 자동 인식 (IP 서브디렉토리 감지)

---

## 10. 마일스톤 (Milestones)

```
Phase 1 (2h)  ── 명령어 등록 + 스켈레톤 + 기본 glob 검색
     │
Phase 2 (2h)  ── 인텐트 파서 + 키워드→타입 매핑
     │
Phase 3 (3h)  ── 멀티전략 검색 엔진 (파일명 + 내용 + 디렉토리)
     │
Phase 4 (1h)  ── 순위 매기기 + 컬러 포맷팅 출력
     │
Phase 5 (2h)  ── 고급 기능 (히스토리, 퍼지, 컨텍스트 인식)
     │
Test (2h)     ── 단위 + 통합 테스트
     │
─────────────
Total: ~12h
```

---

## 11. 구현 우선순위 (Implementation Priority)

| 순위 | 항목 | 이유 |
|------|------|------|
| **P0** | `/find` 커맨드 등록 | 기본 진입점 없으면 시작 불가 |
| **P0** | Intent Parser (키워드 추출) | 검색 품질의 핵심 |
| **P0** | 파일명 glob 검색 | 가장 직관적인 검색 방식 |
| **P1** | 결과 랭킹 & 포맷팅 | 사용자 경험 직결 |
| **P1** | 내용 그렙 검색 | 파일명만으로 부족한 경우 대응 |
| **P2** | 디렉토리 힌트 | ATLAS IP 구조 활용 |
| **P2** | 퍼지 매칭 | 오타 허용으로 사용성 향상 |
| **P3** | 검색 히스토리 | 편의 기능 |
| **P3** | RAG 연동 | 시맨틱 검색 (향후) |
