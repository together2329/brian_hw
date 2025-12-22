"""
Sub-Agent Base Classes

기본 클래스와 데이터 구조 정의:
- AgentStatus: 에이전트 상태
- ActionStep, ActionPlan: 동작 계획
- SubAgentResult: 실행 결과
- SubAgent: 추상 기본 클래스
"""

import re
import json
import time
import os
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple, Set
from functools import wraps


# ============================================================
# Debug Utilities
# ============================================================

# DEBUG 환경 변수로 디버깅 활성화
# Can be set in .config file: DEBUG_SUBAGENT=true
# Or as environment variable: export DEBUG_SUBAGENT=true
DEBUG_SUBAGENT = os.getenv('DEBUG_SUBAGENT', 'false').lower() in ('true', '1', 'yes')


def debug_log(component: str, message: str, data: Any = None):
    """
    DEBUG 모드에서만 로그 출력 (컬러 지원)

    Args:
        component: 컴포넌트 이름 (예: "SubAgent", "ActionPlan")
        message: 로그 메시지
        data: 추가 데이터 (dict, list 등)
    """
    if not DEBUG_SUBAGENT:
        return

    # Color import (lazy to avoid circular imports)
    try:
        from display import Color
    except ImportError:
        # Fallback if display module not available
        class Color:
            DIM = CYAN = MAGENTA = YELLOW = GREEN = RED = RESET = BOLD = ''
            @staticmethod
            def info(t): return t
            @staticmethod
            def warning(t): return t
            @staticmethod
            def success(t): return t

    timestamp = time.strftime("%H:%M:%S")
    
    # Colorized prefix
    time_str = f"{Color.DIM}[{timestamp}]{Color.RESET}"
    debug_str = f"{Color.MAGENTA}[DEBUG]{Color.RESET}"
    comp_str = f"{Color.CYAN}[{component}]{Color.RESET}"
    prefix = f"{time_str}{debug_str}{comp_str}"

    # Colorize special symbols in message
    colored_msg = message
    colored_msg = colored_msg.replace("═══", f"{Color.YELLOW}═══{Color.RESET}")
    colored_msg = colored_msg.replace("───", f"{Color.DIM}───{Color.RESET}")
    colored_msg = colored_msg.replace("╔", f"{Color.YELLOW}╔{Color.RESET}")
    colored_msg = colored_msg.replace("╚", f"{Color.YELLOW}╚{Color.RESET}")
    colored_msg = colored_msg.replace("║", f"{Color.YELLOW}║{Color.RESET}")
    colored_msg = colored_msg.replace("▶", f"{Color.GREEN}▶{Color.RESET}")
    colored_msg = colored_msg.replace("✓", f"{Color.GREEN}✓{Color.RESET}")
    colored_msg = colored_msg.replace("✗", f"{Color.RED}✗{Color.RESET}")
    colored_msg = colored_msg.replace("⚠", f"{Color.YELLOW}⚠{Color.RESET}")
    colored_msg = colored_msg.replace("→", f"{Color.CYAN}→{Color.RESET}")
    colored_msg = colored_msg.replace("←", f"{Color.CYAN}←{Color.RESET}")
    colored_msg = colored_msg.replace("[Phase", f"{Color.BOLD}[Phase{Color.RESET}")
    colored_msg = colored_msg.replace("[Step", f"{Color.BOLD}[Step{Color.RESET}")
    colored_msg = colored_msg.replace("[Tool", f"{Color.MAGENTA}[Tool{Color.RESET}")
    colored_msg = colored_msg.replace("[Iteration", f"{Color.DIM}[Iteration{Color.RESET}")

    if data is not None:
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            # Color the data output
            data_colored = f"{Color.DIM}{data_str}{Color.RESET}"
            print(f"{prefix} {colored_msg}\n{data_colored}")
        else:
            print(f"{prefix} {colored_msg}: {Color.DIM}{data}{Color.RESET}")
    else:
        print(f"{prefix} {colored_msg}")


def debug_method(method_name: str = None):
    """
    메소드 호출/반환을 로깅하는 데코레이터
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = method_name or func.__name__
            if DEBUG_SUBAGENT:
                class_name = args[0].__class__.__name__ if args else "Unknown"
                debug_log(class_name, f"→ {name}() called", {"kwargs": kwargs} if kwargs else None)

            result = func(*args, **kwargs)

            if DEBUG_SUBAGENT:
                debug_log(class_name, f"← {name}() returned", {"result_type": type(result).__name__})

            return result
        return wrapper
    return decorator


# ============================================================
# Action Parsing Utilities
# ============================================================

def sanitize_action_text(text: str) -> str:
    """
    Sanitize common LLM output errors in Action calls.

    Fixes:
    - Markdown bold: **Action:** -> Action:
    - Incorrect quotes: end_line=26") -> end_line=26)
    - Extra colons: Action:: -> Action:

    Args:
        text: Raw LLM response

    Returns:
        Sanitized text with common errors corrected

    Examples:
        >>> sanitize_action_text("**Action:** read_file(path='test.py')")
        "Action: read_file(path='test.py')"

        >>> sanitize_action_text("Action: read_lines(end_line=26\")")
        "Action: read_lines(end_line=26)"
    """
    # Remove markdown bold around "Action:"
    text = re.sub(r'\*\*Action:\*\*', 'Action:', text)
    text = re.sub(r'\*\*Action\*\*:', 'Action:', text)
    text = re.sub(r'__Action:__', 'Action:', text)
    text = re.sub(r'__Action__:', 'Action:', text)

    # Fix number followed by quote then closing paren/comma
    # e.g., end_line=26") -> end_line=26)
    text = re.sub(r'=(\d+)"([,\)])', r'=\1\2', text)
    text = re.sub(r"=(\d+)'([,\)])", r'=\1\2', text)

    # Fix extra colons
    text = re.sub(r'Action::+', 'Action:', text)

    return text


# ============================================================
# Enums
# ============================================================

class AgentStatus(Enum):
    """서브 에이전트 실행 상태"""
    PENDING = "pending"        # 대기 중
    PLANNING = "planning"      # 프롬프트 생성 중
    RUNNING = "running"        # 실행 중
    COMPLETED = "completed"    # 완료
    FAILED = "failed"          # 실패
    CANCELLED = "cancelled"    # 취소됨


# ============================================================
# Data Classes
# ============================================================

@dataclass
class ActionStep:
    """단일 동작 단계"""
    step_number: int
    description: str            # 이 단계에서 할 일
    prompt: str                 # 실행할 프롬프트
    required_tools: List[str]   # 필요한 도구 목록
    depends_on: List[int]       # 의존하는 이전 단계 번호
    expected_output: str        # 기대 결과

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionStep':
        return cls(
            step_number=data.get('step_number', 1),
            description=data.get('description', ''),
            prompt=data.get('prompt', ''),
            required_tools=data.get('required_tools', []),
            depends_on=data.get('depends_on', []),
            expected_output=data.get('expected_output', '')
        )


@dataclass
class ActionPlan:
    """에이전트가 생성한 전체 동작 계획"""
    task_understanding: str     # 태스크 이해
    strategy: str               # 전략
    steps: List[ActionStep]     # 동작 단계들
    estimated_tools: List[str]  # 예상 사용 도구
    success_criteria: str       # 성공 기준

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionPlan':
        steps = [ActionStep.from_dict(s) for s in data.get('steps', [])]
        return cls(
            task_understanding=data.get('task_understanding', ''),
            strategy=data.get('strategy', ''),
            steps=steps,
            estimated_tools=data.get('estimated_tools', []),
            success_criteria=data.get('success_criteria', '')
        )


@dataclass
class SubAgentResult:
    """서브 에이전트 실행 결과"""
    status: AgentStatus
    output: str                                              # 최종 결과 텍스트
    action_plan: Optional[ActionPlan] = None                 # 실행한 동작 계획
    artifacts: Dict[str, Any] = field(default_factory=dict)  # 산출물
    context_updates: Dict[str, Any] = field(default_factory=dict)  # 메인 컨텍스트 업데이트
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # 도구 호출 기록
    errors: List[str] = field(default_factory=list)          # 에러 목록
    execution_time_ms: int = 0                               # 실행 시간
    token_usage: Dict[str, int] = field(default_factory=dict)  # 토큰 사용량


# ============================================================
# SubAgent Base Class
# ============================================================

class SubAgent(ABC):
    """
    서브 에이전트 기본 클래스

    각 에이전트는:
    1. 자율적으로 동작 계획(ActionPlan) 생성
    2. 계획에 따라 단계별 실행
    3. 결과를 구조화하여 반환

    서브클래스에서 구현해야 할 메소드:
    - _get_planning_prompt(): 계획 생성용 시스템 프롬프트
    - _get_execution_prompt(): 실행용 시스템 프롬프트
    - _collect_artifacts(): 산출물 수집
    - _collect_context_updates(): 컨텍스트 업데이트 수집
    """

    # 에이전트별 허용 도구 (서브클래스에서 오버라이드)
    ALLOWED_TOOLS: Set[str] = set()

    def __init__(
        self,
        name: str,
        llm_call_func: Callable,
        execute_tool_func: Callable,
        max_iterations: int = 10,
        max_planning_tokens: int = 2000
    ):
        """
        Args:
            name: 에이전트 이름
            llm_call_func: LLM 호출 함수 (messages -> response)
            execute_tool_func: 도구 실행 함수 (tool_name, args_str -> result)
            max_iterations: 최대 반복 횟수
            max_planning_tokens: 계획 생성 최대 토큰
        """
        self.name = name
        self.llm_call_func = llm_call_func
        self.execute_tool_func = execute_tool_func
        self.max_iterations = max_iterations
        self.max_planning_tokens = max_planning_tokens

        # 격리된 컨텍스트 (메인과 독립)
        self._messages: List[Dict[str, Any]] = []
        self._status = AgentStatus.PENDING
        self._action_plan: Optional[ActionPlan] = None
        self._tool_calls: List[Dict] = []
        self._files_read: List[str] = []
        self._files_modified: List[str] = []

    # ============ 추상 메소드 ============

    @abstractmethod
    def _get_planning_prompt(self) -> str:
        """동작 계획 생성을 위한 시스템 프롬프트"""
        pass

    @abstractmethod
    def _get_execution_prompt(self) -> str:
        """동작 실행을 위한 시스템 프롬프트"""
        pass

    @abstractmethod
    def _collect_artifacts(self) -> Dict[str, Any]:
        """에이전트별 산출물 수집"""
        pass

    @abstractmethod
    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 정보 추출"""
        pass

    # ============ 메인 실행 ============

    def run(self, task: str, context: Dict[str, Any] = None) -> SubAgentResult:
        """
        에이전트 실행 메인 엔트리포인트

        Flow:
        1. 컨텍스트 초기화
        2. 동작 계획 생성 (planning phase)
        3. 계획 실행 (execution phase)
        4. 결과 수집 및 반환
        """
        start_time = time.time()
        self._status = AgentStatus.PLANNING
        self._reset_state()

        debug_log(self.name, f"═══════════ RUN START ═══════════")
        debug_log(self.name, f"Task: {task[:200]}..." if len(task) > 200 else f"Task: {task}")

        # Context detailed logging
        if context and context.keys():
            debug_log(self.name, "Context keys", list(context.keys()))
            # Show context details
            context_details = {}
            for key, value in context.items():
                if isinstance(value, str):
                    context_details[key] = value[:100] + "..." if len(value) > 100 else value
                elif isinstance(value, list):
                    context_details[key] = f"List[{len(value)} items]: {str(value[:3])[:100]}"
                elif isinstance(value, dict):
                    context_details[key] = f"Dict[{len(value)} keys]: {list(value.keys())[:5]}"
                else:
                    context_details[key] = str(value)[:100]
            debug_log(self.name, "Context details", context_details)
        else:
            debug_log(self.name, "Context", "Empty (no context provided)")

        try:
            # Step 1: 컨텍스트 초기화
            debug_log(self.name, "[Phase 1/4] Initializing context...")
            self._initialize_context(task, context)

            # Step 2: 동작 계획 생성
            debug_log(self.name, "[Phase 2/4] Creating action plan...")
            self._action_plan = self._create_action_plan(task)
            debug_log(self.name, "Action plan created", {
                "task_understanding": self._action_plan.task_understanding[:100] if self._action_plan.task_understanding else "",
                "strategy": self._action_plan.strategy[:100] if self._action_plan.strategy else "",
                "steps_count": len(self._action_plan.steps),
                "estimated_tools": self._action_plan.estimated_tools
            })

            # Step 3: 계획 실행
            debug_log(self.name, "[Phase 3/4] Executing plan...")
            self._status = AgentStatus.RUNNING
            output = self._execute_plan()

            # Step 4: 결과 수집
            debug_log(self.name, "[Phase 4/4] Building result...")
            self._status = AgentStatus.COMPLETED
            result = self._build_result(output, start_time)

            debug_log(self.name, f"═══════════ RUN COMPLETE ═══════════")
            debug_log(self.name, "Execution summary", {
                "status": result.status.value,
                "output_length": len(result.output),
                "tool_calls_count": len(result.tool_calls),
                "execution_time_ms": result.execution_time_ms
            })
            return result

        except Exception as e:
            self._status = AgentStatus.FAILED
            debug_log(self.name, f"═══════════ RUN FAILED ═══════════")
            debug_log(self.name, f"Error", str(e))
            return SubAgentResult(
                status=AgentStatus.FAILED,
                output="",
                errors=[str(e)],
                execution_time_ms=int((time.time() - start_time) * 1000)
            )

    def _reset_state(self):
        """상태 초기화"""
        self._messages = []
        self._action_plan = None
        self._tool_calls = []
        self._files_read = []
        self._files_modified = []

    def _initialize_context(self, task: str, context: Dict[str, Any] = None):
        """독립적인 컨텍스트 초기화"""
        self._messages = []

        # 컨텍스트 정보가 있으면 포맷팅
        context_str = ""
        if context:
            context_parts = []
            for key, value in context.items():
                if key == "task":
                    continue  # task는 별도 처리
                if isinstance(value, str):
                    context_parts.append(f"- {key}: {value}")
                elif isinstance(value, list):
                    context_parts.append(f"- {key}: {', '.join(str(v) for v in value[:5])}")
                else:
                    context_parts.append(f"- {key}: {value}")
            if context_parts:
                context_str = "\n[Context]\n" + "\n".join(context_parts)

        # 태스크 저장
        self._current_task = task
        self._context = context or {}

    # ============ 계획 생성 ============

    def _create_action_plan(self, task: str) -> ActionPlan:
        """
        LLM을 사용하여 동작 계획 생성

        1. 태스크 분석
        2. 필요한 도구 식별
        3. 단계별 프롬프트 생성
        """
        debug_log(self.name, "Creating action plan via LLM...")
        debug_log(self.name, "Allowed tools", list(self.ALLOWED_TOOLS))

        planning_prompt = self._get_planning_prompt()

        messages = [
            {"role": "system", "content": planning_prompt},
            {"role": "user", "content": f"""
Task: {task}

Available Tools: {list(self.ALLOWED_TOOLS)}

Create an action plan with:
1. Task understanding
2. Strategy
3. Step-by-step actions (each with specific prompt)
4. Success criteria

Output as JSON:
{{
    "task_understanding": "...",
    "strategy": "...",
    "steps": [
        {{
            "step_number": 1,
            "description": "...",
            "prompt": "...",
            "required_tools": ["tool1", "tool2"],
            "depends_on": [],
            "expected_output": "..."
        }}
    ],
    "estimated_tools": ["..."],
    "success_criteria": "..."
}}
"""}
        ]

        response = self.llm_call_func(messages)
        return self._parse_plan(response)

    def _parse_plan(self, response: str) -> ActionPlan:
        """LLM 응답에서 ActionPlan 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return ActionPlan.from_dict(data)
        except Exception as e:
            pass

        # 파싱 실패 시 기본 계획 생성
        return ActionPlan(
            task_understanding=f"Execute task: {self._current_task}",
            strategy="Direct execution",
            steps=[
                ActionStep(
                    step_number=1,
                    description="Execute the task",
                    prompt=self._current_task,
                    required_tools=list(self.ALLOWED_TOOLS)[:3],
                    depends_on=[],
                    expected_output="Task completed"
                )
            ],
            estimated_tools=list(self.ALLOWED_TOOLS)[:3],
            success_criteria="Task completed successfully"
        )

    # ============ 계획 실행 ============

    def _execute_plan(self) -> str:
        """
        ActionPlan의 각 단계 실행

        - 각 step의 prompt를 사용
        - 필요한 도구만 허용
        - 결과를 다음 단계에 전달
        """
        if not self._action_plan:
            debug_log(self.name, "No action plan to execute")
            return ""

        debug_log(self.name, f"─── Executing plan with {len(self._action_plan.steps)} steps ───")

        # C4 Fix: 순환 의존성 감지
        cycle = self._detect_circular_dependency()
        if cycle:
            error_msg = f"Circular dependency detected: {' -> '.join(map(str, cycle))}"
            debug_log(self.name, f"ERROR: {error_msg}")
            self._errors.append(error_msg)
            return f"[ERROR] {error_msg}"

        results = []
        step_outputs = {}  # step_number -> output

        for step in self._action_plan.steps:
            debug_log(self.name, f"\n▶ Step {step.step_number}: {step.description}")
            debug_log(self.name, "Step details", {
                "required_tools": step.required_tools,
                "depends_on": step.depends_on,
                "expected_output": step.expected_output[:80] if step.expected_output else ""
            })

            # 의존성 체크
            deps_satisfied = all(
                dep in step_outputs for dep in step.depends_on
            )
            if not deps_satisfied:
                missing = [dep for dep in step.depends_on if dep not in step_outputs]
                debug_log(self.name, f"⚠ Step {step.step_number} SKIPPED - missing deps: {missing}")
                results.append(f"### Step {step.step_number}: SKIPPED (missing deps: {missing})")
                continue

            # 이전 단계 결과 주입
            context_from_deps = ""
            if step.depends_on:
                context_from_deps = "\n".join([
                    f"[Step {dep} Result]: {step_outputs.get(dep, 'N/A')}"
                    for dep in step.depends_on
                ])

            # 단계 실행
            step_output = self._execute_step(step, context_from_deps)
            step_outputs[step.step_number] = step_output
            debug_log(self.name, f"✓ Step {step.step_number} completed", {
                "output_length": len(step_output)
            })
            results.append(f"### Step {step.step_number}: {step.description}\n{step_output}")

        debug_log(self.name, f"─── Plan execution finished: {len(results)} steps ───")
        return "\n\n".join(results)

    def _detect_circular_dependency(self) -> Optional[List[int]]:
        """
        순환 의존성 감지 (DFS 기반)

        Returns:
            순환 경로 리스트 (없으면 None)
        """
        if not self._action_plan or not self._action_plan.steps:
            return None

        # 그래프 구성
        steps = {step.step_number: step for step in self._action_plan.steps}
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: int) -> Optional[List[int]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            step = steps.get(node)
            if step:
                for dep in step.depends_on:
                    if dep not in visited:
                        result = dfs(dep)
                        if result:
                            return result
                    elif dep in rec_stack:
                        # 순환 발견
                        cycle_start = path.index(dep)
                        return path[cycle_start:] + [dep]

            path.pop()
            rec_stack.remove(node)
            return None

        for step_num in steps:
            if step_num not in visited:
                result = dfs(step_num)
                if result:
                    return result

        return None

    def _create_user_message(self, step: ActionStep, context: str) -> str:
        """
        Create the initial user message for the ReAct loop.
        Can be overridden by subclasses to customize prompt format.
        """
        return f"""
{step.prompt}

{context if context else ""}

Expected Output: {step.expected_output}
Available Tools: {step.required_tools}

Use the ReAct format:
Thought: [your reasoning]
Action: tool_name(args)

Or if done:
Thought: [your reasoning]
Result: [your final answer]
"""

    def _execute_step(self, step: ActionStep, context: str) -> str:
        """
        단일 단계 실행 (미니 ReAct 루프)

        개선사항:
        - Hallucination 감지 (LLM이 "Observation:" 자가 생성 방지)
        - 연속 에러 추적 (동일 에러 3회 반복 시 중단)
        - Stall 감지 (연속 5회 읽기 작업 시 경고)
        """
        debug_log(self.name, f"\n  → Executing step {step.step_number} with ReAct loop")
        debug_log(self.name, f"  Max iterations: {self.max_iterations}")

        # Context logging
        if context:
            context_preview = context[:200] + "..." if len(context) > 200 else context
            debug_log(self.name, f"  Context provided ({len(context)} chars): {context_preview}")
        else:
            debug_log(self.name, "  Context: None (no dependencies)")

        # Error tracking variables
        consecutive_errors = 0
        last_error_observation = None
        MAX_CONSECUTIVE_ERRORS = 3

        # Stall detection variables
        consecutive_reads = 0
        MAX_CONSECUTIVE_READS = 5

        messages = [
            {"role": "system", "content": self._get_execution_prompt()},
            {"role": "user", "content": self._create_user_message(step, context)}
        ]

        # 미니 ReAct 루프
        for i in range(self.max_iterations):
            debug_log(self.name, f"  [Iteration {i+1}/{self.max_iterations}] Calling LLM...")
            response = self.llm_call_func(messages)
            messages.append({"role": "assistant", "content": response})

            # Hallucination detection: LLM이 "Observation:"을 자가 생성하는지 확인
            if "Observation:" in response and "Action:" not in response.split("Observation:")[-1]:
                debug_log(self.name, f"  ⚠ [Iteration {i+1}] Hallucination detected: LLM generated 'Observation:' itself")
                warning = "[System] You generated 'Observation:' yourself. DO NOT DO THIS. You must output an Action, wait for me to execute it, and then I will give you the Observation. Now, please output the correct Action."
                messages.append({"role": "user", "content": warning})
                continue  # Skip to next iteration

            # 완료 체크 (Result: 또는 명시적 종료 토큰 감지)
            completion_tokens = ["Result:", "EXPLORE_COMPLETE", "PLAN_COMPLETE"]
            is_complete = False
            for token in completion_tokens:
                if token in response and "Action:" not in response.split(token)[-1]:
                    is_complete = True
                    debug_log(self.name, f"  [Iteration {i+1}] ✓ Found {token}, completing step")
                    break
            
            if is_complete:
                return response

            # Action 파싱
            actions = self._parse_actions(response)
            debug_log(self.name, f"  [Iteration {i+1}] Parsed actions: {len(actions)}")

            if not actions:
                debug_log(self.name, f"  [Iteration {i+1}] No actions found, completing step")
                return response

            # 도구 실행 (허용된 도구만)
            observations = []
            for tool_name, args in actions:
                debug_log(self.name, f"  [Tool Call] {tool_name}({args[:100]}...)" if len(args) > 100 else f"  [Tool Call] {tool_name}({args})")

                if tool_name not in self.ALLOWED_TOOLS:
                    debug_log(self.name, f"  [Tool Error] {tool_name} not in ALLOWED_TOOLS")
                    observations.append(f"[{tool_name}]: Error - Tool not allowed for this agent")
                    continue

                try:
                    result = self.execute_tool_func(tool_name, args)
                    result_preview = str(result)[:200] if result else "(empty)"
                    debug_log(self.name, f"  [Tool Result] {result_preview}...")
                    observations.append(f"[{tool_name}]: {result}")

                    # Stall detection: Track consecutive read operations
                    read_tools = {'read_file', 'read_lines', 'grep_file', 'list_dir',
                                  'find_files', 'git_diff', 'git_status', 'rag_search'}
                    if tool_name in read_tools:
                        consecutive_reads += 1
                        debug_log(self.name, f"  [Stall Check] Consecutive reads: {consecutive_reads}/{MAX_CONSECUTIVE_READS}")
                    else:
                        consecutive_reads = 0  # Reset on non-read operation

                    # 파일 읽기/수정 추적
                    if 'read' in tool_name.lower():
                        self._files_read.append(args)
                    if 'write' in tool_name.lower() or 'replace' in tool_name.lower():
                        self._files_modified.append(args)

                    # 도구 호출 기록
                    self._tool_calls.append({
                        "tool": tool_name,
                        "args": args,
                        "result": str(result)[:500]  # 결과 요약
                    })
                except Exception as e:
                    debug_log(self.name, f"  [Tool Error] {tool_name}: {str(e)}")
                    observations.append(f"[{tool_name}]: Error - {str(e)}")

            # Combine observations
            observation = "\n".join(observations)

            # Consecutive error detection
            is_error = "error" in observation.lower() or "exception" in observation.lower()
            if is_error:
                if observation == last_error_observation:
                    consecutive_errors += 1
                    debug_log(self.name, f"  ⚠ [Error Check] Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")

                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        debug_log(self.name, f"  ❌ [Error Check] Same error {MAX_CONSECUTIVE_ERRORS} times. Stopping.")
                        error_msg = f"[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times consecutively. This suggests the current approach is not working. Please try a different strategy or ask the user for help."
                        messages.append({
                            "role": "user",
                            "content": f"Observation:\n{observation}\n\n{error_msg}"
                        })
                        break  # Exit ReAct loop
                else:
                    consecutive_errors = 0
                    last_error_observation = observation
            else:
                consecutive_errors = 0
                last_error_observation = None

            # Stall warning
            if consecutive_reads >= MAX_CONSECUTIVE_READS:
                debug_log(self.name, f"  ⚠ [Stall Check] Detected {consecutive_reads} consecutive reads. Agent may be stalled.")
                stall_msg = "[System] Detected excessive read operations without progress. You've read {consecutive_reads} times in a row. Please analyze your findings and either move to the next action or complete the task."
                messages.append({
                    "role": "user",
                    "content": f"Observation:\n{observation}\n\n{stall_msg}"
                })
                consecutive_reads = 0  # Reset after warning
            else:
                messages.append({
                    "role": "user",
                    "content": f"Observation:\n{observation}"
                })

        debug_log(self.name, f"  Max iterations reached for step {step.step_number}")
        return messages[-1]["content"] if messages else ""

    def _parse_actions(self, response: str) -> List[Tuple[str, str]]:
        """
        응답에서 Action 파싱 (개선: Markdown, triple-quotes, truncated output)

        개선 사항:
        - Markdown 형식 지원 (**Action:**, `tool_name`)
        - Triple-quoted strings 처리
        - Truncated output 자동 복구
        - LLM 일반 오류 수정 (sanitize)

        Examples:
            >>> _parse_actions("**Action:** read_file(path='test.py')")
            [('read_file', "path='test.py'")]

            >>> _parse_actions("Action: `read_file`(path='test.py')")
            [('read_file', "path='test.py'")]
        """
        # STEP 1: Sanitize common LLM errors first
        response = sanitize_action_text(response)

        actions = []

        # STEP 2: Updated pattern to support markdown and formatting
        # 기존: r'Action:\s*(\w+)\('
        # 개선: Markdown bold/italic/code blocks 지원
        action_pattern = r'(?:\*\*|__)?Action(?:\*\*|__)?::*\s*[`*_]*\s*(\w+)\s*[`*_]*\s*\('
        # 설명:
        # (?:\*\*|__)? - Optional markdown bold/italic prefix
        # Action - Literal "Action"
        # (?:\*\*|__)? - Optional markdown bold/italic suffix
        # ::* - Optional extra colons (some LLMs add them)
        # \s*[`*_]*\s* - Optional markdown formatting around tool name
        # (\w+) - Tool name (captured group)
        # \s*[`*_]*\s* - Optional markdown after tool name
        # \( - Opening paren

        for match in re.finditer(action_pattern, response):
            tool_name = match.group(1)
            start_paren = match.end() - 1  # '(' 위치

            debug_log(self.name, f"  [Parse] Found action: {tool_name}")

            # 괄호 균형 추적으로 종료 위치 찾기 (triple-quotes 지원)
            args = self._extract_balanced_parens(response, start_paren)
            if args is not None:
                actions.append((tool_name, args))
                debug_log(self.name, f"  [Parse] Extracted args: {args[:100]}{'...' if len(args) > 100 else ''}")
            else:
                debug_log(self.name, f"  ⚠ [Parse] Failed to extract args for {tool_name}")

        return actions

    def _extract_balanced_parens(self, text: str, start_pos: int) -> Optional[str]:
        """
        괄호 균형을 추적하여 내용 추출 (개선: triple-quotes, truncated recovery)

        개선 사항:
        - Triple-quoted strings 처리 (triple double/single quotes)
        - Truncated output 자동 복구 (미완성 문자열 자동 마감)
        - 상세 디버그 로깅

        Args:
            text: 전체 텍스트
            start_pos: '(' 시작 위치

        Returns:
            괄호 안의 내용 (괄호 제외) 또는 None

        Examples:
            Simple args: '(path="test.py")' -> 'path="test.py"'
            Triple quotes: '(content=TRIPLE_QUOTE_code_TRIPLE_QUOTE)' works too
        """
        if start_pos >= len(text) or text[start_pos] != '(':
            return None

        depth = 0
        in_single_quote = False
        in_double_quote = False
        in_triple_single = False
        in_triple_double = False
        escape_next = False

        i = start_pos
        while i < len(text):
            char = text[i]

            # Escape handling
            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == '\\':
                escape_next = True
                i += 1
                continue

            # Check for triple quotes FIRST (only if not in other quotes)
            if not in_single_quote and not in_double_quote:
                if i + 2 < len(text):
                    three_chars = text[i:i+3]
                    if three_chars == '"""':
                        if not in_triple_single:
                            in_triple_double = not in_triple_double
                            debug_log(self.name, f"  [Parse] Triple-double quote {'opened' if in_triple_double else 'closed'} at pos {i}")
                            i += 3
                            continue
                    elif three_chars == "'" * 3:  # Triple single quote
                        if not in_triple_double:
                            in_triple_single = not in_triple_single
                            debug_log(self.name, f"  [Parse] Triple-single quote {'opened' if in_triple_single else 'closed'} at pos {i}")
                            i += 3
                            continue

            # Regular quote handling (only if not in triple quotes)
            if not in_triple_single and not in_triple_double:
                if char == '"' and not in_single_quote:
                    in_double_quote = not in_double_quote
                elif char == "'" and not in_double_quote:
                    in_single_quote = not in_single_quote

            # Parenthesis tracking (only outside all quotes)
            in_any_quote = in_single_quote or in_double_quote or in_triple_single or in_triple_double
            if not in_any_quote:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        result = text[start_pos + 1:i]
                        debug_log(self.name, f"  [Parse] ✓ Balanced parens extracted ({len(result)} chars)")
                        return result

            i += 1

        # Truncated output recovery
        if depth > 0:
            debug_log(self.name, f"  ⚠ [Parse] Unmatched parens (depth={depth}), attempting recovery...")

            # Extract what we have
            args_str = text[start_pos + 1:]

            # Close open quotes
            if in_triple_double:
                args_str += '"""'
                debug_log(self.name, f"  🔧 [Parse] Auto-closed triple-double quote")
            elif in_triple_single:
                args_str += "'" * 3  # Triple single quote
                debug_log(self.name, f"  🔧 [Parse] Auto-closed triple-single quote")
            elif in_double_quote:
                args_str += '"'
                debug_log(self.name, f"  🔧 [Parse] Auto-closed double quote")
            elif in_single_quote:
                args_str += "'"
                debug_log(self.name, f"  🔧 [Parse] Auto-closed single quote")

            debug_log(self.name, f"  🔧 [Parse] Recovered truncated args: {args_str[:100]}{'...' if len(args_str) > 100 else ''}")
            return args_str

        return None

    # ============ 결과 빌드 ============

    def _build_result(self, output: str, start_time: float) -> SubAgentResult:
        """최종 결과 객체 생성"""
        return SubAgentResult(
            status=self._status,
            output=output,
            action_plan=self._action_plan,
            artifacts=self._collect_artifacts(),
            context_updates=self._collect_context_updates(output),
            tool_calls=self._tool_calls,
            execution_time_ms=int((time.time() - start_time) * 1000)
        )


# ============================================================
# Pipeline Data Classes (Orchestrator용)
# ============================================================

@dataclass
class PipelineStep:
    """파이프라인의 단일 단계"""
    step: int
    agents: List[str]
    parallel: bool = False
    description: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PipelineStep':
        return cls(
            step=data.get('step', 1),
            agents=data.get('agents', []),
            parallel=data.get('parallel', False),
            description=data.get('description', '')
        )


@dataclass
class ExecutionPlan:
    """실행 계획"""
    task_type: str              # simple, complex, multi_step
    complexity_score: int       # 1-10
    agents_needed: List[str]    # 필요한 에이전트 목록
    execution_mode: str         # sequential, parallel, pipeline
    pipeline: List[PipelineStep]
    reasoning: str              # 분석 근거

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionPlan':
        pipeline = [PipelineStep.from_dict(p) for p in data.get('pipeline', [])]
        return cls(
            task_type=data.get('task_type', 'simple'),
            complexity_score=data.get('complexity_score', 5),
            agents_needed=data.get('agents_needed', ['execute']),
            execution_mode=data.get('execution_mode', 'sequential'),
            pipeline=pipeline,
            reasoning=data.get('reasoning', '')
        )


@dataclass
class OrchestratorResult:
    """오케스트레이터 최종 결과"""
    task: str
    execution_plan: ExecutionPlan
    agent_results: List[SubAgentResult]
    final_output: str
    context_updates: Dict[str, Any]
    execution_time_ms: int
