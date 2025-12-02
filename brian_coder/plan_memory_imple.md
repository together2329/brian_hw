# Brian Coder Memory Feature 구현 계획

## 배경

### 1. 논문 분석 결과 (3가지 Memory 접근법)

**Memp - Procedural Memory (절차적 기억)**
- "어떻게 하는지" 기억
- Build → Retrieve → Update 사이클
- Task-specific knowledge 저장
- 실패에서 학습

**Mem0 - Declarative Memory (선언적 기억)**
- "무슨 일이 있었는지" 기억
- Extract facts → Update (Add/Update/Delete)
- Knowledge Graph로 확장 가능
- User preferences, project context 관리

**A-MEM - Self-Organizing Memory (자가 조직 기억)**
- 자동으로 패턴 발견
- Memory notes + Auto-linking
- 계층적 지식 구축

### 2. Graphiti 분석 결과

**핵심 아키텍처:**
```
Application Layer (graphiti.py)
    ↓
Data Model (EpisodicNode, EntityNode, CommunityNode)
    ↓
Storage Layer (Neo4j, FalkorDB, Kuzu, Neptune)
```

**주요 특징:**
- 실시간 지식 그래프 (Real-time Knowledge Graph)
- Bi-temporal data model (event time + ingestion time)
- Hybrid retrieval (semantic + keyword + graph-based)
- LLM 기반 엔티티/관계 추출

**의존성:**
```
필수:
- pydantic>=2.11.5
- neo4j>=5.26.0 (또는 다른 그래프 DB)
- openai>=1.91.0 (또는 다른 LLM)
- diskcache>=5.6.3
- numpy>=1.0.0

+ 외부 서비스:
- 그래프 데이터베이스 (Neo4j 등)
- LLM API
- 임베딩 서비스
```

**결론:** Graphiti는 완전 Zero-Dependency 불가능

---

## 핵심 질문 (사용자 결정 필요)

구현 전에 다음 사항들을 결정해야 합니다:

### 질문 1: 복잡도 vs 기능
어느 정도 수준의 메모리 시스템을 원하시나요?

**Option A: Simple (파일 기반)**
- JSON/SQLite 파일로 저장
- Zero-dependency 유지
- 기본적인 fact storage
- 빠른 구현

**Option B: Advanced (Graphiti-like)**
- 지식 그래프 기반
- 의존성 추가 필요 (Neo4j 등)
- 복잡한 관계 추론
- 더 강력하지만 복잡함

### 질문 2: 메모리 타입 우선순위
어떤 타입을 먼저 구현할까요?

**Option A: Declarative First (Mem0 스타일)**
- User preferences 저장
- Project context 관리
- 즉시 유용함
- 구현 쉬움

**Option B: Procedural First (Memp 스타일)**
- Tool usage patterns 학습
- Error recovery strategies
- 장기적으로 더 강력
- 사용 패턴 수집 필요

**Option C: Both (Hybrid)**
- 두 가지 모두 구현
- 더 복잡하지만 완전함

### 질문 3: Zero-Dependency 원칙
어떻게 처리할까요?

**Option A: 엄격한 Zero-Dependency**
- 파일 기반 (JSON, SQLite)
- stdlib만 사용
- 제한적 기능

**Option B: 선택적 의존성 (Graphiti 방식)**
```bash
pip install brian-coder              # 기본 (파일 기반)
pip install brian-coder[memory]      # 고급 (그래프 기반)
pip install brian-coder[all]         # 모든 기능
```

**Option C: 외부 서비스 연동**
- LLM API만 사용 (이미 있음)
- 파일로 구조화 저장
- 절충안

---

## 잠정 권장 사항 (사용자 확인 필요)

### Phase 1: Simple Declarative Memory (Mem0 스타일)

**구현 목표:**
- User preferences 저장
- Project context 관리
- Conversation facts 추출
- Zero-dependency 유지

**기술 스택:**
```python
Storage: JSON 파일 또는 SQLite
Extraction: 기존 LLM (OpenAI/Anthropic)
Retrieval: 단순 키워드 매칭 또는 임베딩 (선택적)
```

**파일 구조:**
```
.brian_memory/
  ├── facts.json              # Declarative memory
  ├── preferences.json        # User preferences
  └── project_context.json    # Project-specific context
```

**장점:**
- ✅ 빠른 구현
- ✅ Zero-dependency
- ✅ 즉시 유용함
- ✅ 기존 코드 최소 변경

### Phase 2: Advanced Options (나중에)

사용자 피드백에 따라:
- Procedural memory 추가
- 지식 그래프 옵션
- 벡터 검색 (optional dependency)

---

## 대기 중인 결정사항

1. 복잡도 수준?
2. 메모리 타입 우선순위?
3. Zero-dependency vs 선택적 의존성?
4. 저장 형식 (JSON vs SQLite)?
5. Graphiti 패턴 중 어느 것을 차용할 것인가?

---

## 최종 권장 방안

**Hybrid Approach: Simple Memory + Zero-Dependency Graphiti Lite**

사용자의 Zero-Dependency Graphiti 타당성 분석을 기반으로, 두 가지 접근법을 결합한 하이브리드 방안을 채택합니다.

### 선택된 옵션
- **복잡도**: Hybrid (Simple + Lite Graph)
- **메모리 타입**: Declarative + Graph-based Knowledge
- **의존성 원칙**: 엄격한 Zero-Dependency (stdlib only + API calls)

### 선택 근거
1. ✅ Zero-dependency 철학 100% 유지 (urllib만 사용)
2. ✅ Simple facts 저장 + 복잡한 관계 그래프 모두 지원
3. ✅ 임베딩 기반 검색 (API via urllib, numpy 불필요)
4. ✅ 300-500줄 경량 구현으로 Graphiti 핵심 기능 확보
5. ✅ 소규모/개인 프로젝트에 최적화 (수천 개 노드까지 충분)

### Graphiti Lite vs Original 비교

| 기능 | Graphiti (Original) | Brian Coder Graphiti Lite |
|------|---------------------|---------------------------|
| Graph DB | Neo4j / FalkorDB | In-Memory Dict + JSON 저장 |
| Vector Search | numpy / scikit-learn | Pure Python Cosine Similarity |
| Embeddings | OpenAI SDK / SentenceTransformers | urllib로 API 직접 호출 |
| Schema | Pydantic | Python dataclasses |
| Search Index | HNSW / Vector Index | Brute-force (소규모 충분) |
| Dependencies | 8+ packages | **0 (stdlib only)** |
| Scale | 수백만 노드 | 수천 노드 (개인용) |

---

## 상세 구현 설계

### 1. 파일 구조

```
brian_coder/
├── main.py                    # 기존 파일 (memory 통합)
├── config.py                  # 기존 파일 (memory 설정 추가)
├── memory.py                  # 새 파일 (Simple Memory 시스템)
├── graph_lite.py              # 새 파일 (Zero-Dependency Graphiti Lite)
├── .env.example               # 업데이트 (memory 설정)
└── .brian_memory/             # 새 디렉토리 (사용자 홈 또는 프로젝트)
    ├── facts.json             # Simple facts (legacy)
    ├── preferences.json       # User preferences
    ├── graph_nodes.json       # Graph nodes (id, type, data, embedding)
    ├── graph_edges.json       # Graph edges (source, target, relation, valid_time)
    └── project_context.json   # Project-specific context
```

### 2. Memory 시스템 아키텍처

두 가지 시스템이 협력하여 작동합니다:

#### 2A. Simple Memory System (memory.py)
간단한 fact/preference 저장용:

```python
class MemorySystem:
    """Simple Declarative Memory (Quick facts & preferences)"""

    def __init__(self, memory_dir=".brian_memory"):
        self.memory_dir = Path.home() / memory_dir
        self.preferences_file = self.memory_dir / "preferences.json"
        self._ensure_initialized()

    def update_preference(self, key: str, value: Any) -> None
    def get_preference(self, key: str, default=None) -> Any
    def format_preferences_for_prompt(self) -> str
```

#### 2B. Graph Lite System (graph_lite.py)
Graphiti-inspired 지식 그래프 (Zero-Dependency):

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import urllib.request
import math

@dataclass
class Node:
    id: str
    type: str  # "Entity", "Episodic", "Community"
    data: Dict
    embedding: Optional[List[float]] = None
    created_at: str = ""

@dataclass
class Edge:
    source: str
    target: str
    relation: str
    valid_time: str  # ISO format
    confidence: float = 1.0

class GraphLite:
    """
    Zero-Dependency Knowledge Graph (Graphiti-inspired)
    - In-memory graph + JSON persistence
    - Embedding-based search (via urllib API calls)
    - Pure Python cosine similarity (no numpy)
    - Temporal graph support
    """

    def __init__(self, memory_dir=".brian_memory"):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.nodes_file = Path.home() / memory_dir / "graph_nodes.json"
        self.edges_file = Path.home() / memory_dir / "graph_edges.json"
        self._load()

    # Core Graph Operations
    def add_node(self, node: Node) -> None
    def add_edge(self, edge: Edge) -> None
    def get_node(self, node_id: str) -> Optional[Node]
    def find_neighbors(self, node_id: str, relation: str = None) -> List[Node]

    # Embedding & Search (Zero-Dependency)
    def get_embedding(self, text: str) -> List[float]:
        """Call OpenAI/Ollama API via urllib (no SDK)"""

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Pure Python cosine similarity (no numpy)"""
        dot_product = sum(a*b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a*a for a in v1))
        norm_b = math.sqrt(sum(b*b for b in v2))
        return dot_product / (norm_a * norm_b)

    def search(self, query: str, limit: int = 10) -> List[Node]:
        """Semantic search using embeddings"""
        query_embedding = self.get_embedding(query)
        results = []
        for node in self.nodes.values():
            if node.embedding:
                score = self.cosine_similarity(query_embedding, node.embedding)
                results.append((score, node))
        results.sort(reverse=True, key=lambda x: x[0])
        return [node for score, node in results[:limit]]

    # LLM Integration
    def extract_entities_from_text(self, text: str) -> List[Node]:
        """Use LLM to extract entities from text"""

    def extract_relations_from_text(self, text: str, nodes: List[Node]) -> List[Edge]:
        """Use LLM to extract relations between entities"""

    # Persistence
    def save(self) -> None
    def _load(self) -> None
```

### 3. 데이터 스키마

#### preferences.json (Simple Memory)
```json
{
  "language": "korean",
  "compression_mode": "single",
  "keep_recent": 4,
  "default_llm": "gpt-4o-mini",
  "code_style": {
    "indent": "spaces",
    "indent_size": 4
  }
}
```

#### graph_nodes.json (Graph Lite)
```json
{
  "node_1": {
    "id": "node_1",
    "type": "Entity",
    "data": {
      "name": "Brian",
      "role": "User",
      "description": "Prefers Korean explanations"
    },
    "embedding": [0.123, -0.456, 0.789, ...],
    "created_at": "2025-12-02T10:30:00"
  },
  "node_2": {
    "id": "node_2",
    "type": "Episodic",
    "data": {
      "event": "Implemented compression feature",
      "details": "Added chunked compression mode"
    },
    "embedding": [0.234, -0.567, 0.890, ...],
    "created_at": "2025-12-02T11:00:00"
  },
  "node_3": {
    "id": "node_3",
    "type": "Entity",
    "data": {
      "name": "brian_coder",
      "type": "Project",
      "tech_stack": "Python, zero-dependency"
    },
    "embedding": [0.345, -0.678, 0.901, ...],
    "created_at": "2025-12-02T09:00:00"
  }
}
```

#### graph_edges.json (Graph Lite)
```json
[
  {
    "source": "node_1",
    "target": "node_3",
    "relation": "WORKS_ON",
    "valid_time": "2025-12-02T09:00:00",
    "confidence": 1.0
  },
  {
    "source": "node_2",
    "target": "node_3",
    "relation": "PART_OF",
    "valid_time": "2025-12-02T11:00:00",
    "confidence": 0.95
  },
  {
    "source": "node_1",
    "target": "node_2",
    "relation": "PERFORMED",
    "valid_time": "2025-12-02T11:00:00",
    "confidence": 1.0
  }
]
```

### 4. LLM 통합 방식

#### 4.1 Entity Extraction (Graph Lite)
```python
ENTITY_EXTRACTION_PROMPT = """
Extract entities from the following text.
Return JSON array with format: [{"name": "...", "type": "Person|Project|Tool|Concept", "description": "..."}]

Text: {text}

Entities (JSON only):
"""
```

#### 4.2 Relation Extraction (Graph Lite)
```python
RELATION_EXTRACTION_PROMPT = """
Given entities: {entities}

Find relationships in the text: {text}

Return JSON array: [{"source": "entity1", "target": "entity2", "relation": "WORKS_ON|USES|PART_OF|...", "confidence": 0.0-1.0}]

Relations (JSON only):
"""
```

#### 4.3 Embedding API Call (Zero-Dependency)
```python
def get_embedding_via_urllib(text: str) -> List[float]:
    """
    Call OpenAI embedding API using urllib (no SDK)
    Alternative: Ollama for local embeddings
    """
    import urllib.request
    import json

    # OpenAI API
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "input": text,
        "model": "text-embedding-3-small"  # 1536 dimensions
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=headers
    )

    with urllib.request.urlopen(request) as response:
        result = json.loads(response.read())
        return result["data"][0]["embedding"]
```

#### 4.4 Context Injection to System Prompt
```python
def build_memory_context() -> str:
    """Combine preferences + graph knowledge"""
    context = "=== KNOWN CONTEXT ===\n\n"

    # Simple preferences
    prefs = memory.get_all_preferences()
    context += f"User Preferences:\n{prefs}\n\n"

    # Graph knowledge (semantic search)
    # Get current conversation topic
    recent_nodes = graph.search(current_topic, limit=5)
    context += "Relevant Knowledge:\n"
    for node in recent_nodes:
        context += f"- {node.data}\n"

    context += "=====================\n"
    return context
```

### 5. config.py 추가 설정

```python
# Memory Settings
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in ("true", "1", "yes")
MEMORY_DIR = os.getenv("MEMORY_DIR", ".brian_memory")

# Graph Lite Settings
ENABLE_GRAPH = os.getenv("ENABLE_GRAPH", "true").lower() in ("true", "1", "yes")
GRAPH_AUTO_EXTRACT = os.getenv("GRAPH_AUTO_EXTRACT", "true").lower() in ("true", "1", "yes")
GRAPH_SEARCH_LIMIT = int(os.getenv("GRAPH_SEARCH_LIMIT", "5"))

# Embedding Settings (for Graph Lite)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai or ollama
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", API_KEY)  # Reuse LLM key
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", "https://api.openai.com/v1")
```

### 6. main.py 통합 포인트

#### 6.1 초기화 (startup)
```python
# Global instances
memory = None
graph = None

if config.ENABLE_MEMORY:
    from memory import MemorySystem
    memory = MemorySystem(config.MEMORY_DIR)

if config.ENABLE_GRAPH:
    from graph_lite import GraphLite
    graph = GraphLite(config.MEMORY_DIR)
```

#### 6.2 System Prompt 생성
```python
def build_system_prompt():
    base_prompt = config.SYSTEM_PROMPT

    if config.ENABLE_MEMORY or config.ENABLE_GRAPH:
        context = "\n\n=== KNOWN CONTEXT ===\n\n"

        # Add preferences
        if memory:
            prefs = memory.get_all_preferences()
            context += f"User Preferences:\n{prefs}\n\n"

        # Add graph knowledge (semantic search based on recent conversation)
        if graph:
            # Get topic from last user message
            recent_topic = messages[-1].get("content", "")[:200] if messages else ""
            relevant_nodes = graph.search(recent_topic, limit=config.GRAPH_SEARCH_LIMIT)
            if relevant_nodes:
                context += "Relevant Knowledge:\n"
                for node in relevant_nodes:
                    context += f"- {node.data.get('name', 'Unknown')}: {node.data.get('description', '')}\n"

        context += "\n=====================\n"
        return base_prompt + context

    return base_prompt
```

#### 6.3 대화 종료 시 Knowledge Extraction
```python
def on_conversation_end(messages):
    """Extract and save knowledge after conversation"""
    if not (config.ENABLE_GRAPH and config.GRAPH_AUTO_EXTRACT):
        return

    # Get last 10 messages for context
    recent_messages = messages[-10:]
    conversation_text = "\n".join([
        f"{m.get('role')}: {m.get('content', '')[:500]}"
        for m in recent_messages
    ])

    try:
        # Extract entities
        entities = graph.extract_entities_from_text(conversation_text)

        # Add nodes to graph
        for entity_data in entities:
            node = Node(
                id=f"entity_{uuid.uuid4().hex[:8]}",
                type="Entity",
                data=entity_data,
                embedding=graph.get_embedding(entity_data.get("description", "")),
                created_at=datetime.now().isoformat()
            )
            graph.add_node(node)

        # Extract relations
        relations = graph.extract_relations_from_text(conversation_text, entities)

        # Add edges to graph
        for relation_data in relations:
            edge = Edge(
                source=relation_data["source"],
                target=relation_data["target"],
                relation=relation_data["relation"],
                valid_time=datetime.now().isoformat(),
                confidence=relation_data.get("confidence", 0.8)
            )
            graph.add_edge(edge)

        # Save to disk
        graph.save()
        print(f"[Memory] Saved {len(entities)} entities and {len(relations)} relations")

    except Exception as e:
        print(f"[Memory] Failed to extract knowledge: {e}")
```

### 7. 구현 체크리스트

**Phase 1A: Simple Memory System (2-3 hours)**
- [ ] `memory.py` 파일 생성
- [ ] `MemorySystem` 클래스 기본 구조
- [ ] Preferences 읽기/쓰기 (JSON)
- [ ] 디렉토리 초기화 로직
- [ ] `update_preference()` / `get_preference()` 구현
- [ ] `format_preferences_for_prompt()` 구현

**Phase 1B: Graph Lite Core (3-4 hours)**
- [ ] `graph_lite.py` 파일 생성
- [ ] `Node` / `Edge` dataclass 정의
- [ ] `GraphLite` 클래스 기본 구조
- [ ] In-memory graph storage (Dict + List)
- [ ] JSON persistence (`save()` / `_load()`)
- [ ] `add_node()` / `add_edge()` / `get_node()` 구현
- [ ] `find_neighbors()` 구현 (relation 필터링)

**Phase 1C: Zero-Dependency Embedding & Search (3-4 hours)**
- [ ] `get_embedding()` 구현 (urllib로 API 호출)
- [ ] OpenAI API 지원
- [ ] Ollama API 지원 (optional)
- [ ] `cosine_similarity()` 구현 (Pure Python, no numpy)
- [ ] `search()` 구현 (Brute-force semantic search)
- [ ] Embedding cache (메모리 절약)

**Phase 1D: LLM Knowledge Extraction (2-3 hours)**
- [ ] Entity extraction prompt 작성
- [ ] `extract_entities_from_text()` 구현
- [ ] Relation extraction prompt 작성
- [ ] `extract_relations_from_text()` 구현
- [ ] JSON parsing 및 에러 핸들링

**Phase 1E: Main.py Integration (2-3 hours)**
- [ ] `config.py`에 memory & graph 설정 추가
- [ ] `main.py`에서 MemorySystem & GraphLite 초기화
- [ ] `build_system_prompt()` 수정 (memory context 포함)
- [ ] `on_conversation_end()` 구현 (knowledge extraction)
- [ ] 대화 종료 시 자동 저장

**Phase 1F: Testing & Documentation (2-3 hours)**
- [ ] Unit tests for GraphLite operations
- [ ] Test cosine similarity accuracy
- [ ] Test embedding API calls (urllib)
- [ ] Integration test with real conversation
- [ ] `.env.example` 업데이트 (graph settings)
- [ ] README에 Graph Lite 설명 추가
- [ ] 성능 테스트 (1000 nodes 검색 속도)

**Total Estimate: 14-20 hours**

### 8. 핵심 구현 포인트

**8.1 Zero-Dependency 유지 전략**
- ✅ stdlib만 사용: `json`, `urllib.request`, `dataclasses`, `math`, `uuid`
- ✅ numpy 대체: Pure Python cosine similarity
- ✅ OpenAI SDK 대체: urllib로 직접 API 호출
- ✅ Neo4j 대체: In-memory Dict + JSON 파일

**8.2 성능 최적화**
- Embedding cache: 같은 텍스트 재사용
- Lazy loading: 필요시에만 임베딩 생성
- Brute-force search: 수천 노드까지 충분히 빠름 (< 100ms)

**8.3 확장성 고려**
- 노드 수 제한: 5,000개 이하 권장
- 파일 크기: JSON 파일 1MB 이하 권장
- 검색 속도: O(N) brute-force (N < 5,000 → acceptable)

### 9. 향후 확장 계획 (Phase 2+)

**Phase 2A: Procedural Memory 추가**
- Tool usage patterns 학습
- Error recovery strategies 저장
- Command success/failure 기록
- "How-to" knowledge base

**Phase 2B: Advanced Search**
- HNSW index (optional dependency)
- Hybrid search (keyword + semantic)
- Community detection (clustering)

**Phase 2C: Graph Algorithms**
- Shortest path 찾기
- PageRank for node importance
- Temporal queries (시간 범위 검색)

**Phase 2D: 선택적 의존성 지원**
```bash
pip install brian-coder              # Zero-dependency (current)
pip install brian-coder[graph]       # + faiss-cpu (HNSW)
pip install brian-coder[all]         # + 모든 최적화
```

---

## 최종 요약

### 구현 방안
**Hybrid Memory System: Simple Preferences + Zero-Dependency Graph Lite**

1. **Simple Memory (`memory.py`)**: 빠른 preferences 저장/조회
2. **Graph Lite (`graph_lite.py`)**: Graphiti-inspired 지식 그래프
   - Zero-dependency (stdlib only)
   - 임베딩 기반 검색 (urllib API 호출)
   - Pure Python cosine similarity
   - 300-500줄 경량 구현

### 핵심 장점
- ✅ 100% Zero-Dependency 유지
- ✅ Graphiti의 핵심 기능 확보 (Entity, Relation, Temporal, Search)
- ✅ 소규모 프로젝트에 최적화 (수천 노드)
- ✅ 투명한 JSON 저장 (사람이 읽고 수정 가능)
- ✅ 빠른 구현 (14-20시간)

### 제한 사항
- 노드 수: 5,000개 이하 권장
- 검색 속도: O(N) brute-force (HNSW 없음)
- 복잡한 그래프 알고리즘: Phase 2에서 추가

### 다음 단계

**Plan 승인 후 실행 순서:**
1. Phase 1A: Simple Memory System (2-3h)
2. Phase 1B: Graph Lite Core (3-4h)
3. Phase 1C: Embedding & Search (3-4h)
4. Phase 1D: LLM Knowledge Extraction (2-3h)
5. Phase 1E: Main.py Integration (2-3h)
6. Phase 1F: Testing & Documentation (2-3h)

**Total: 14-20 hours**

---

**구현 준비 완료. 승인 시 즉시 작업 시작 가능합니다.**
