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
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Tuple, Set


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

        try:
            # Step 1: 컨텍스트 초기화
            self._initialize_context(task, context)

            # Step 2: 동작 계획 생성
            self._action_plan = self._create_action_plan(task)

            # Step 3: 계획 실행
            self._status = AgentStatus.RUNNING
            output = self._execute_plan()

            # Step 4: 결과 수집
            self._status = AgentStatus.COMPLETED
            return self._build_result(output, start_time)

        except Exception as e:
            self._status = AgentStatus.FAILED
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
            return ""

        # C4 Fix: 순환 의존성 감지
        cycle = self._detect_circular_dependency()
        if cycle:
            error_msg = f"Circular dependency detected: {' -> '.join(map(str, cycle))}"
            self._errors.append(error_msg)
            return f"[ERROR] {error_msg}"

        results = []
        step_outputs = {}  # step_number -> output

        for step in self._action_plan.steps:
            # 의존성 체크
            deps_satisfied = all(
                dep in step_outputs for dep in step.depends_on
            )
            if not deps_satisfied:
                missing = [dep for dep in step.depends_on if dep not in step_outputs]
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
            results.append(f"### Step {step.step_number}: {step.description}\n{step_output}")

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

    def _execute_step(self, step: ActionStep, context: str) -> str:
        """
        단일 단계 실행 (미니 ReAct 루프)
        """
        messages = [
            {"role": "system", "content": self._get_execution_prompt()},
            {"role": "user", "content": f"""
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
"""}
        ]

        # 미니 ReAct 루프
        for i in range(self.max_iterations):
            response = self.llm_call_func(messages)
            messages.append({"role": "assistant", "content": response})

            # 완료 체크 (Result: 가 있으면 완료)
            if "Result:" in response and "Action:" not in response.split("Result:")[-1]:
                return response

            # Action 파싱
            actions = self._parse_actions(response)

            if not actions:
                # 액션 없음 = 완료
                return response

            # 도구 실행 (허용된 도구만)
            observations = []
            for tool_name, args in actions:
                if tool_name not in self.ALLOWED_TOOLS:
                    observations.append(f"[{tool_name}]: Error - Tool not allowed for this agent")
                    continue

                try:
                    result = self.execute_tool_func(tool_name, args)
                    observations.append(f"[{tool_name}]: {result}")

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
                    observations.append(f"[{tool_name}]: Error - {str(e)}")

            messages.append({
                "role": "user",
                "content": f"Observation:\n" + "\n".join(observations)
            })

        return messages[-1]["content"] if messages else ""

    def _parse_actions(self, response: str) -> List[Tuple[str, str]]:
        """
        응답에서 Action 파싱 (C3 Fix: 괄호 매칭 알고리즘)

        기존 정규식은 중첩 괄호를 처리하지 못함.
        예: write_file(content="def foo():\n    pass") → 실패
        """
        actions = []

        # 모든 "Action:" 시작점 찾기
        action_pattern = r'Action:\s*(\w+)\('
        for match in re.finditer(action_pattern, response):
            tool_name = match.group(1)
            start_paren = match.end() - 1  # '(' 위치

            # 괄호 균형 추적으로 종료 위치 찾기
            args = self._extract_balanced_parens(response, start_paren)
            if args is not None:
                actions.append((tool_name, args))

        return actions

    def _extract_balanced_parens(self, text: str, start_pos: int) -> Optional[str]:
        """괄호 균형을 추적하여 내용 추출"""
        if start_pos >= len(text) or text[start_pos] != '(':
            return None

        depth = 0
        in_string = False
        string_char = None
        escape_next = False

        for i in range(start_pos, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == '\\':
                escape_next = True
                continue

            # 문자열 시작/종료 감지
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                in_string = False
                string_char = None

            # 괄호 추적 (문자열 밖에서만)
            if not in_string:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                    if depth == 0:
                        return text[start_pos + 1:i]

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
