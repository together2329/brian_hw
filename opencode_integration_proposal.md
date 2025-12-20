# OpenCode → Brian_coder 통합 제안서

## Executive Summary

OpenCode의 핵심 아키텍처 패턴을 brian_coder에 적용하여 확장성, 안정성, 유지보수성을 향상시키는 방안을 제시합니다.

---

## 1. Agent System (에이전트 시스템)

### 현재 상태
- brian_coder: `ENABLE_SUB_AGENTS` 플래그로 서브에이전트 활성화
- 단순한 orchestrator 구조

### OpenCode 패턴 적용

```python
# core/agent_system.py (NEW FILE)
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Any
from enum import Enum

class Permission(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"

@dataclass
class AgentPermission:
    """Agent의 권한 설정"""
    edit: Permission = Permission.ALLOW
    bash: Dict[str, Permission] = field(default_factory=lambda: {"*": Permission.ALLOW})
    external_directory: Permission = Permission.ASK
    git_destructive: Permission = Permission.ASK
    file_delete: Permission = Permission.ASK

@dataclass
class AgentInfo:
    """Agent 정보 및 설정"""
    name: str
    mode: Literal["primary", "subagent", "all"]
    description: Optional[str] = None
    prompt: Optional[str] = None
    tools: Dict[str, bool] = field(default_factory=dict)
    permission: AgentPermission = field(default_factory=AgentPermission)
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_steps: Optional[int] = None
    native: bool = False  # Built-in agent
    hidden: bool = False  # Hide from UI
    color: Optional[str] = None

class AgentRegistry:
    """중앙 Agent 관리 레지스트리"""

    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._init_builtin_agents()

    def _init_builtin_agents(self):
        """Built-in agents 초기화"""

        # 1. Build Agent (기본 개발 에이전트)
        self._agents["build"] = AgentInfo(
            name="build",
            mode="primary",
            description="Full-access development agent with file editing capabilities",
            permission=AgentPermission(
                edit=Permission.ALLOW,
                bash={"*": Permission.ALLOW},
                external_directory=Permission.ASK,
                git_destructive=Permission.ASK
            ),
            tools={
                "read_file": True,
                "write_file": True,
                "run_command": True,
                "rag_search": True,
                "edit_file": True
            },
            native=True
        )

        # 2. Plan Agent (읽기 전용 계획 에이전트)
        self._agents["plan"] = AgentInfo(
            name="plan",
            mode="primary",
            description="Read-only agent for analysis and planning",
            permission=AgentPermission(
                edit=Permission.DENY,
                bash={
                    "ls*": Permission.ALLOW,
                    "find*": Permission.ALLOW,
                    "grep*": Permission.ALLOW,
                    "git diff*": Permission.ALLOW,
                    "git log*": Permission.ALLOW,
                    "git status*": Permission.ALLOW,
                    "*": Permission.ASK  # 그 외 명령어는 확인 필요
                },
                external_directory=Permission.ASK
            ),
            tools={
                "read_file": True,
                "write_file": False,
                "run_command": True,  # 제한적
                "rag_search": True,
                "edit_file": False
            },
            native=True
        )

        # 3. Explore Agent (코드베이스 탐색 전문)
        self._agents["explore"] = AgentInfo(
            name="explore",
            mode="subagent",
            description="Fast codebase exploration specialist",
            prompt="""You are a specialized code exploration agent.
Your goal is to quickly navigate codebases and find relevant information.
Focus on:
- File pattern matching
- Code searching
- Architecture understanding
- Dependency analysis

DO NOT modify files. Only read and analyze.""",
            permission=AgentPermission(
                edit=Permission.DENY,
                bash={
                    "find*": Permission.ALLOW,
                    "grep*": Permission.ALLOW,
                    "rg*": Permission.ALLOW,
                    "*": Permission.DENY
                }
            ),
            tools={
                "read_file": True,
                "write_file": False,
                "run_command": True,
                "rag_search": True,
                "edit_file": False,
                "todo_write": False  # 탐색 중에는 todo 작성 안함
            },
            native=True
        )

        # 4. PCIe Expert Agent (도메인 전문 에이전트)
        self._agents["pcie_expert"] = AgentInfo(
            name="pcie_expert",
            mode="subagent",
            description="PCIe and hardware design specialist",
            prompt="""You are a PCIe and hardware design expert.
You have deep knowledge of:
- PCIe protocol (TLP, DLLP, Physical Layer)
- Verilog/SystemVerilog
- AXI protocol
- Hardware verification

Use the RAG system to search PCIe specifications when needed.
Always verify hardware designs for timing and protocol compliance.""",
            permission=AgentPermission(
                edit=Permission.ALLOW,
                bash={
                    "iverilog*": Permission.ALLOW,
                    "vvp*": Permission.ALLOW,
                    "*": Permission.ASK
                }
            ),
            tools={
                "read_file": True,
                "write_file": True,
                "run_command": True,
                "rag_search": True,
                "verilog_lint": True,
                "verilog_sim": True
            },
            temperature=0.3,  # 하드웨어 설계는 정확성 중시
            native=True,
            hidden=False
        )

        # 5. RAG Indexer Agent (인덱싱 전문)
        self._agents["rag_indexer"] = AgentInfo(
            name="rag_indexer",
            mode="subagent",
            description="Specialized agent for RAG index building and optimization",
            permission=AgentPermission(
                edit=Permission.DENY,
                bash={"*": Permission.DENY}
            ),
            tools={
                "read_file": True,
                "rag_rebuild": True,
                "rag_search": True
            },
            native=True,
            hidden=True  # UI에 노출 안함
        )

    def get(self, name: str) -> Optional[AgentInfo]:
        """Agent 조회"""
        return self._agents.get(name)

    def list(self, mode: Optional[Literal["primary", "subagent", "all"]] = None) -> list[AgentInfo]:
        """Agent 목록"""
        agents = list(self._agents.values())
        if mode:
            agents = [a for a in agents if a.mode == mode or a.mode == "all"]
        return [a for a in agents if not a.hidden]

    def register(self, agent: AgentInfo):
        """사용자 정의 agent 등록"""
        self._agents[agent.name] = agent

    def check_permission(self, agent_name: str, action: str, target: str = "*") -> Permission:
        """권한 체크"""
        agent = self.get(agent_name)
        if not agent:
            return Permission.DENY

        if action == "edit":
            return agent.permission.edit
        elif action == "bash":
            # Pattern matching for bash commands
            perms = agent.permission.bash
            # 정확히 일치하는 패턴 찾기
            if target in perms:
                return perms[target]
            # Glob 패턴 매칭
            import fnmatch
            for pattern, perm in perms.items():
                if fnmatch.fnmatch(target, pattern):
                    return perm
            return perms.get("*", Permission.DENY)
        elif action == "external_directory":
            return agent.permission.external_directory
        elif action == "git_destructive":
            return agent.permission.git_destructive

        return Permission.DENY

# Global registry instance
agent_registry = AgentRegistry()
```

### 사용 예시

```python
# main.py에서 사용
from core.agent_system import agent_registry, Permission

# 현재 agent 선택
current_agent = agent_registry.get("build")
print(f"Using agent: {current_agent.name}")
print(f"Description: {current_agent.description}")

# 권한 체크
can_edit = agent_registry.check_permission("plan", "edit")
if can_edit == Permission.DENY:
    print("Plan agent cannot edit files!")

can_run_git = agent_registry.check_permission("build", "bash", "git commit -m 'test'")
if can_run_git == Permission.ALLOW:
    # 실행
    pass

# Agent 전환 (Tab 키 등)
def switch_agent(from_agent: str, to_agent: str):
    print(f"Switching from {from_agent} to {to_agent}")
    return agent_registry.get(to_agent)
```

---

## 2. Tool System (도구 시스템 개선)

### 현재 상태
- brian_coder: 단순 함수 기반 도구 (`tools.py`)
- 검증 없음, 메타데이터 부족

### OpenCode 패턴 적용

```python
# core/tool_system.py (NEW FILE)
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, TypedDict
from dataclasses import dataclass
from pydantic import BaseModel, Field
import asyncio

class ToolContext(TypedDict):
    """Tool 실행 컨텍스트"""
    session_id: str
    message_id: str
    agent: str
    abort_signal: Optional[asyncio.Event]
    call_id: Optional[str]
    metadata_callback: Optional[Callable[[str, Dict], None]]

class ToolResult(BaseModel):
    """Tool 실행 결과"""
    title: str = Field(description="UI에 표시할 짧은 제목")
    output: str = Field(description="Tool의 텍스트 출력")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="구조화된 메타데이터")
    attachments: list = Field(default_factory=list, description="파일 첨부")
    error: Optional[str] = None

class ToolParameters(BaseModel):
    """Base class for tool parameters"""
    pass

class Tool(ABC):
    """Tool 기본 클래스"""

    def __init__(self):
        self.id = self.__class__.__name__.lower().replace("tool", "")

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 설명 (LLM에게 표시)"""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> type[BaseModel]:
        """Pydantic 모델로 파라미터 정의"""
        pass

    @abstractmethod
    async def execute(self, params: BaseModel, ctx: ToolContext) -> ToolResult:
        """Tool 실행"""
        pass

    def format_validation_error(self, error: Exception) -> str:
        """검증 에러 포맷팅 (선택적)"""
        return str(error)

# 구체적인 Tool 구현 예시

class ReadFileParams(BaseModel):
    file_path: str = Field(description="Path to the file to read")
    offset: Optional[int] = Field(None, description="Line number to start reading from")
    limit: Optional[int] = Field(None, description="Number of lines to read")

class ReadFileTool(Tool):
    """파일 읽기 도구"""

    @property
    def description(self) -> str:
        return "Reads content from a file with optional line range"

    @property
    def parameters_schema(self) -> type[BaseModel]:
        return ReadFileParams

    async def execute(self, params: ReadFileParams, ctx: ToolContext) -> ToolResult:
        import os

        # 1. 파일 존재 확인
        if not os.path.exists(params.file_path):
            return ToolResult(
                title=params.file_path,
                output="",
                error=f"File not found: {params.file_path}"
            )

        # 2. Metadata 업데이트 (시작)
        if ctx.get("metadata_callback"):
            ctx["metadata_callback"]("Reading file...", {"path": params.file_path})

        # 3. Abort 체크
        if ctx.get("abort_signal") and ctx["abort_signal"].is_set():
            raise Exception("Operation aborted by user")

        # 4. 파일 읽기
        try:
            with open(params.file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Line range 적용
            total_lines = len(lines)
            if params.offset is not None:
                start = params.offset
                end = start + params.limit if params.limit else len(lines)
                lines = lines[start:end]
            elif params.limit is not None:
                lines = lines[:params.limit]

            content = ''.join(lines)

            # 5. 결과 반환
            return ToolResult(
                title=os.path.basename(params.file_path),
                output=content,
                metadata={
                    "path": params.file_path,
                    "total_lines": total_lines,
                    "lines_read": len(lines),
                    "size_bytes": os.path.getsize(params.file_path)
                }
            )

        except UnicodeDecodeError:
            return ToolResult(
                title=params.file_path,
                output="",
                error="Cannot read binary file",
                metadata={"binary": True}
            )
        except Exception as e:
            return ToolResult(
                title=params.file_path,
                output="",
                error=f"Error reading file: {e}"
            )

class EditFileParams(BaseModel):
    file_path: str = Field(description="Path to the file to edit")
    old_string: str = Field(description="String to replace (must be unique)")
    new_string: str = Field(description="Replacement string")
    replace_all: bool = Field(False, description="Replace all occurrences")

class EditFileTool(Tool):
    """OpenCode 스타일의 파일 편집 (Fuzzy matching 포함)"""

    @property
    def description(self) -> str:
        return "Edits a file by replacing exact string matches with fuzzy matching support"

    @property
    def parameters_schema(self) -> type[BaseModel]:
        return EditFileParams

    async def execute(self, params: EditFileParams, ctx: ToolContext) -> ToolResult:
        import os

        # 1. 파일 읽기
        if not os.path.exists(params.file_path):
            return ToolResult(
                title=params.file_path,
                output="",
                error=f"File not found: {params.file_path}"
            )

        with open(params.file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 2. Fuzzy matching 전략들
        replacers = [
            self._simple_replacer,
            self._line_trimmed_replacer,
            self._whitespace_normalized_replacer,
            self._indentation_flexible_replacer
        ]

        matched = False
        new_content = content

        for replacer in replacers:
            search_string = replacer(params.old_string)
            if search_string in content:
                if params.replace_all:
                    new_content = content.replace(search_string, params.new_string)
                else:
                    # 1회만 치환
                    new_content = content.replace(search_string, params.new_string, 1)
                matched = True
                break

        if not matched:
            return ToolResult(
                title=params.file_path,
                output="",
                error=f"Could not find unique match for old_string in {params.file_path}"
            )

        # 3. 파일 쓰기
        with open(params.file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # 4. Diff 생성
        from lib.display import format_diff
        diff = format_diff(content, new_content)

        return ToolResult(
            title=os.path.basename(params.file_path),
            output=f"Successfully edited {params.file_path}\n\n{diff}",
            metadata={
                "path": params.file_path,
                "old_length": len(content),
                "new_length": len(new_content),
                "diff_lines": diff.count('\n')
            }
        )

    def _simple_replacer(self, s: str) -> str:
        """정확히 일치"""
        return s

    def _line_trimmed_replacer(self, s: str) -> str:
        """각 라인의 공백 trim"""
        lines = s.split('\n')
        return '\n'.join(line.strip() for line in lines)

    def _whitespace_normalized_replacer(self, s: str) -> str:
        """연속 공백을 단일 공백으로"""
        import re
        return re.sub(r'\s+', ' ', s)

    def _indentation_flexible_replacer(self, s: str) -> str:
        """들여쓰기 무시"""
        import re
        return re.sub(r'^[ \t]+', '', s, flags=re.MULTILINE)

class ToolRegistry:
    """Tool 레지스트리"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._init_builtin_tools()

    def _init_builtin_tools(self):
        """Built-in tools 등록"""
        self.register(ReadFileTool())
        self.register(EditFileTool())
        # ... 다른 도구들

    def register(self, tool: Tool):
        """Tool 등록"""
        self._tools[tool.id] = tool

    def get(self, tool_id: str) -> Optional[Tool]:
        """Tool 조회"""
        return self._tools.get(tool_id)

    def list(self) -> list[Tool]:
        """모든 Tool 목록"""
        return list(self._tools.values())

    async def execute_batch(self, tool_calls: list[Dict], ctx: ToolContext) -> list[ToolResult]:
        """병렬 Tool 실행 (OpenCode의 Batch tool)"""
        tasks = []
        for call in tool_calls:
            tool = self.get(call["tool"])
            if not tool:
                tasks.append(asyncio.create_task(
                    self._error_result(f"Tool '{call['tool']}' not found")
                ))
                continue

            # 파라미터 검증
            try:
                params = tool.parameters_schema(**call["parameters"])
            except Exception as e:
                tasks.append(asyncio.create_task(
                    self._error_result(f"Invalid parameters: {e}")
                ))
                continue

            # Tool 실행 task 생성
            tasks.append(tool.execute(params, ctx))

        # 병렬 실행
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Exception을 ToolResult로 변환
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(ToolResult(
                    title="Error",
                    output="",
                    error=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def _error_result(self, error_msg: str) -> ToolResult:
        """에러 결과 생성"""
        return ToolResult(title="Error", output="", error=error_msg)

# Global tool registry
tool_registry = ToolRegistry()
```

### 사용 예시

```python
# main.py에서 사용
from core.tool_system import tool_registry, ToolContext, ToolResult
import asyncio

async def execute_tool_call(tool_name: str, params: dict, session_id: str):
    tool = tool_registry.get(tool_name)
    if not tool:
        print(f"Tool '{tool_name}' not found")
        return

    # Context 생성
    ctx: ToolContext = {
        "session_id": session_id,
        "message_id": "msg_123",
        "agent": "build",
        "abort_signal": None,
        "call_id": "call_456",
        "metadata_callback": lambda title, meta: print(f"[{title}] {meta}")
    }

    # 파라미터 검증 및 실행
    try:
        validated_params = tool.parameters_schema(**params)
        result = await tool.execute(validated_params, ctx)

        print(f"Title: {result.title}")
        print(f"Output: {result.output}")
        print(f"Metadata: {result.metadata}")
        if result.error:
            print(f"Error: {result.error}")

    except Exception as e:
        print(f"Validation error: {e}")

# 병렬 실행 예시
async def batch_read_files():
    ctx: ToolContext = {"session_id": "sess_1", ...}

    tool_calls = [
        {"tool": "read_file", "parameters": {"file_path": "src/main.py"}},
        {"tool": "read_file", "parameters": {"file_path": "src/config.py"}},
        {"tool": "read_file", "parameters": {"file_path": "README.md"}}
    ]

    results = await tool_registry.execute_batch(tool_calls, ctx)
    for result in results:
        print(f"Read {result.title}: {len(result.output)} chars")
```

---

## 3. Context Management (컨텍스트 관리)

### OpenCode의 Compaction 전략 적용

```python
# core/context_manager.py (NEW FILE)
from typing import List, Dict, Optional
from dataclasses import dataclass
import time

@dataclass
class TokenUsage:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0

    @property
    def total(self) -> int:
        return self.input + self.cache_read + self.output

@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str
    tokens: Optional[TokenUsage] = None
    timestamp: float = 0
    tool_calls: List[Dict] = None
    compacted: bool = False

class ContextManager:
    """OpenCode 스타일의 컨텍스트 관리"""

    PRUNE_MINIMUM = 20_000  # 최소 토큰 (이하는 pruning 안함)
    PRUNE_PROTECT = 40_000  # 보호 구간 (최근 40k 토큰은 유지)

    def __init__(self, model_context_limit: int = 200_000):
        self.messages: List[Message] = []
        self.model_limit = model_context_limit
        self.output_reserve = 8192  # 출력용 예약

    def add_message(self, role: str, content: str, tokens: Optional[TokenUsage] = None):
        """메시지 추가"""
        self.messages.append(Message(
            role=role,
            content=content,
            tokens=tokens or TokenUsage(),
            timestamp=time.time()
        ))

    def current_usage(self) -> TokenUsage:
        """현재 토큰 사용량"""
        total = TokenUsage()
        for msg in self.messages:
            if msg.tokens:
                total.input += msg.tokens.input
                total.output += msg.tokens.output
                total.cache_read += msg.tokens.cache_read
                total.cache_write += msg.tokens.cache_write
        return total

    def is_overflow(self) -> bool:
        """Context overflow 체크"""
        usage = self.current_usage()
        usable = self.model_limit - self.output_reserve
        return usage.total > usable

    async def prune(self) -> int:
        """
        Tool call 출력 압축 (OpenCode 전략)
        최근 40k 토큰의 tool call은 유지하고, 그 이전 것들은 압축
        """
        usage = self.current_usage()
        if usage.total < self.PRUNE_MINIMUM:
            return 0  # 너무 적으면 pruning 안함

        protected_tokens = 0
        compacted_count = 0

        # 역순으로 순회 (최근부터)
        for msg in reversed(self.messages):
            if msg.role == "assistant" and msg.compacted:
                break  # 이미 압축된 지점까지만

            msg_tokens = msg.tokens.total if msg.tokens else 0
            protected_tokens += msg_tokens

            # 보호 구간 초과 시 tool call 압축
            if protected_tokens > self.PRUNE_PROTECT and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    if "output" in tool_call and len(tool_call["output"]) > 1000:
                        # 출력 압축 (첫 500자 + "..." + 마지막 500자)
                        original = tool_call["output"]
                        tool_call["output"] = original[:500] + "\n\n... [중략] ...\n\n" + original[-500:]
                        tool_call["compacted"] = True
                        compacted_count += 1

        return compacted_count

    async def summarize(self) -> Optional[str]:
        """
        컨텍스트 요약 (OpenCode의 compaction agent)
        """
        if len(self.messages) < 10:
            return None  # 메시지가 적으면 요약 안함

        # Compaction agent 호출 (간단한 버전)
        from llm_client import call_llm_raw

        # 중간 메시지들 선택 (처음 5개와 마지막 5개는 유지)
        to_summarize = self.messages[5:-5]

        if not to_summarize:
            return None

        # 요약 요청
        summary_prompt = f"""Summarize the following conversation history in a concise manner.
Focus on key decisions, important context, and unresolved issues.

Messages:
{self._format_messages(to_summarize)}

Provide a brief summary (2-3 paragraphs):"""

        summary = await call_llm_raw([
            {"role": "user", "content": summary_prompt}
        ])

        # 요약본으로 대체
        self.messages = (
            self.messages[:5] +
            [Message(role="assistant", content=f"[Summary of previous context]\n{summary}", compacted=True)] +
            self.messages[-5:]
        )

        return summary

    def _format_messages(self, messages: List[Message]) -> str:
        """메시지 포맷팅"""
        lines = []
        for msg in messages:
            lines.append(f"{msg.role}: {msg.content[:500]}...")
        return "\n".join(lines)

    async def auto_manage(self) -> Dict[str, int]:
        """
        자동 컨텍스트 관리
        1. Overflow 체크
        2. Pruning 시도
        3. 여전히 overflow면 Summarization
        """
        stats = {"pruned": 0, "summarized": 0}

        if not self.is_overflow():
            return stats

        # 1단계: Pruning
        pruned = await self.prune()
        stats["pruned"] = pruned

        if not self.is_overflow():
            return stats

        # 2단계: Summarization
        summary = await self.summarize()
        if summary:
            stats["summarized"] = 1

        return stats

# Global context manager
context_manager = ContextManager()
```

---

## 4. 적용 우선순위

### Phase 1: 기본 구조 (1-2주)
✅ **즉시 적용 가능**
1. **Agent System** (`core/agent_system.py`)
   - AgentInfo, AgentPermission 클래스
   - AgentRegistry
   - Built-in agents: build, plan, explore, pcie_expert

2. **Tool System 개선** (`core/tool_system.py`)
   - Tool 기본 클래스
   - ToolContext, ToolResult
   - Pydantic 기반 파라미터 검증

### Phase 2: 고급 기능 (2-3주)
📊 **점진적 적용**
3. **Permission System**
   - 파일 쓰기/삭제 전 확인
   - 위험한 bash 명령어 차단
   - External directory 접근 제어

4. **Context Management**
   - Token overflow 감지
   - Tool output pruning
   - Automatic summarization

5. **Batch Tool Execution**
   - asyncio 기반 병렬 실행
   - 여러 파일 동시 읽기
   - RAG 병렬 검색

### Phase 3: 확장성 (3-4주)
🚀 **장기 개선**
6. **Plugin System**
   - `~/.brian_coder/tools/` 폴더
   - 사용자 정의 tool 동적 로딩
   - 프로젝트별 커스텀 agent

7. **LSP Integration**
   - Python LSP server 연동
   - 코드 작성 후 자동 lint
   - Type error 피드백

8. **Snapshot-based Diff Tracking**
   - 각 단계별 파일 변경 추적
   - Undo/Redo 지원

---

## 5. 즉시 적용 가능한 Quick Wins

### 5.1. 현재 tools.py 개선

```python
# core/tools.py에 즉시 추가 가능
def check_permission(agent_name: str, action: str) -> bool:
    """간단한 권한 체크"""
    PERMISSIONS = {
        "build": {"edit": True, "delete": True, "bash": True},
        "plan": {"edit": False, "delete": False, "bash": "limited"},
        "explore": {"edit": False, "delete": False, "bash": "readonly"}
    }

    perms = PERMISSIONS.get(agent_name, {})
    return perms.get(action, False)

def edit_file_fuzzy(path: str, old_string: str, new_string: str) -> str:
    """Fuzzy matching으로 파일 편집"""
    import re

    with open(path, 'r') as f:
        content = f.read()

    # 여러 전략 시도
    strategies = [
        lambda s: s,  # 정확히 일치
        lambda s: '\n'.join(line.strip() for line in s.split('\n')),  # trim
        lambda s: re.sub(r'\s+', ' ', s),  # 공백 정규화
    ]

    for strategy in strategies:
        search = strategy(old_string)
        if search in content:
            content = content.replace(search, new_string, 1)
            with open(path, 'w') as f:
                f.write(content)
            return f"Successfully edited {path}"

    return f"Error: Could not find '{old_string}' in {path}"
```

### 5.2. main.py에서 Agent 전환

```python
# main.py에 추가
CURRENT_AGENT = "build"  # Global state

def switch_agent(new_agent: str):
    """Agent 전환"""
    global CURRENT_AGENT
    valid_agents = ["build", "plan", "explore", "pcie_expert"]

    if new_agent not in valid_agents:
        print(f"Unknown agent: {new_agent}")
        return

    print(Color.system(f"Switching from {CURRENT_AGENT} to {new_agent}"))
    CURRENT_AGENT = new_agent

    # System prompt 변경
    if new_agent == "plan":
        # 읽기 전용 프롬프트
        pass
    elif new_agent == "pcie_expert":
        # PCIe 전문가 프롬프트
        pass

# 메시지 처리 시 agent 확인
def process_tool_call(tool_name: str, params: dict):
    # 권한 체크
    if tool_name == "write_file":
        if not check_permission(CURRENT_AGENT, "edit"):
            return "Error: Current agent does not have edit permission"

    # Tool 실행
    return tools.AVAILABLE_TOOLS[tool_name](**params)
```

---

## 6. 마이그레이션 체크리스트

### 준비 단계
- [ ] 현재 brian_coder 백업
- [ ] 테스트 케이스 작성
- [ ] 새로운 디렉토리 구조 설계

### Phase 1
- [ ] `core/agent_system.py` 작성
- [ ] `core/tool_system.py` 작성
- [ ] 기존 `tools.py`를 새 시스템으로 마이그레이션
- [ ] Unit 테스트 작성

### Phase 2
- [ ] Permission system 통합
- [ ] Context manager 통합
- [ ] Batch execution 구현

### Phase 3
- [ ] Plugin system
- [ ] LSP integration
- [ ] Documentation

---

## 7. 예상 효과

### 즉시 얻을 수 있는 장점
1. **타입 안정성**: Pydantic으로 파라미터 검증
2. **확장성**: 새 tool/agent 추가가 쉬움
3. **안전성**: Permission system으로 실수 방지
4. **성능**: Batch execution으로 latency 감소

### 장기적 이점
1. **유지보수성**: 명확한 구조
2. **협업**: 다른 개발자가 이해하기 쉬움
3. **테스트**: Unit test 작성 용이
4. **확장**: Plugin으로 기능 추가

---

## 8. 다음 단계

### 옵션 A: 점진적 통합
기존 brian_coder를 유지하면서 새 기능을 하나씩 추가

### 옵션 B: 전면 리팩토링
새로운 구조로 완전히 재설계 (brian_coder_v2)

### 옵션 C: 하이브리드
핵심 기능만 포팅하고 나머지는 기존 유지

---

**추천: 옵션 A (점진적 통합)**
- 위험이 적음
- 즉시 사용 가능
- 테스트하면서 진행

이 문서를 기반으로 어떤 부분부터 시작할지 결정하시면 됩니다!
