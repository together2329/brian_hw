"""
Orchestrator - 서브 에이전트 조율

메인 오케스트레이터:
1. 작업 유형 분석 → 실행 계획 생성
2. 적절한 에이전트 선택/스폰
3. 에이전트 간 의존성 관리 (병렬/순차)
4. 결과 통합 및 메인 컨텍스트 업데이트
5. 메모리 시스템 통합 (GraphLite, ProceduralMemory)
"""

import re
import json
import time
import copy
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import List, Dict, Any, Optional, Callable, Type

from .base import (
    AgentStatus,
    SubAgent,
    SubAgentResult,
    PipelineStep,
    ExecutionPlan,
    OrchestratorResult,
    DEBUG_SUBAGENT,
    debug_log
)


class Orchestrator:
    """
    메인 오케스트레이터 - 모든 서브 에이전트를 조율

    Responsibilities:
    1. 작업 유형 분석 (내장 TaskAnalyzer)
    2. 적절한 에이전트 선택/스폰
    3. 에이전트 간 의존성 관리
    4. 병렬/순차 실행 결정
    5. 결과 통합 및 메인 컨텍스트 업데이트
    """

    def __init__(
        self,
        llm_call_func: Callable,
        execute_tool_func: Callable,
        graph_lite=None,
        procedural_memory=None,
        parallel_enabled: bool = False,
        max_workers: int = 3,
        timeout: int = 60
    ):
        """
        Args:
            llm_call_func: LLM 호출 함수
            execute_tool_func: 도구 실행 함수
            graph_lite: GraphLite 인스턴스 (선택)
            procedural_memory: ProceduralMemory 인스턴스 (선택)
            parallel_enabled: 병렬 실행 활성화 여부 (기본: False)
            max_workers: 병렬 실행 시 최대 워커 수
            timeout: 에이전트 타임아웃 (초)
        """
        self.llm_call_func = llm_call_func
        self.execute_tool_func = execute_tool_func
        self.graph_lite = graph_lite
        self.procedural_memory = procedural_memory
        self.parallel_enabled = parallel_enabled
        self.max_workers = max_workers
        self.timeout = timeout

        # 에이전트 레지스트리 (lazy import로 순환 참조 방지)
        self._agent_classes: Dict[str, Type[SubAgent]] = {}
        self._register_agents()

        # 실행 히스토리 (학습용)
        self._execution_history: List[Dict] = []

    def _register_agents(self):
        """에이전트 클래스 등록"""
        # Lazy import to avoid circular imports
        from .explore_agent import ExploreAgent
        from .plan_agent import PlanAgent
        from .execute_agent import ExecuteAgent
        from .code_review_agent import CodeReviewAgent

        self._agent_classes = {
            "explore": ExploreAgent,
            "plan": PlanAgent,
            "execute": ExecuteAgent,
            "review": CodeReviewAgent
        }

    # ============ 메인 엔트리포인트 ============

    def run(self, task: str, context: Dict[str, Any] = None) -> OrchestratorResult:
        """
        작업 실행 메인 엔트리포인트

        Flow:
        1. 작업 분석 → 실행 계획 생성
        2. 메모리에서 관련 컨텍스트 검색
        3. 에이전트 파이프라인 실행
        4. 결과 통합 및 반환
        """
        start_time = time.time()

        debug_log("Orchestrator", "╔═══════════════════════════════════════════╗")
        debug_log("Orchestrator", "║         ORCHESTRATOR RUN START         ║")
        debug_log("Orchestrator", "╚═══════════════════════════════════════════╝")
        debug_log("Orchestrator", f"Task: {task[:300]}..." if len(task) > 300 else f"Task: {task}")
        debug_log("Orchestrator", "Input context", context if context else {})

        print(f"[Orchestrator] Analyzing task...")

        # Step 1: 작업 분석 및 실행 계획 생성
        debug_log("Orchestrator", "[Step 1/5] Analyzing task and creating execution plan...")
        execution_plan = self._analyze_and_plan(task)
        debug_log("Orchestrator", "Execution plan created", {
            "task_type": execution_plan.task_type,
            "complexity_score": execution_plan.complexity_score,
            "agents_needed": execution_plan.agents_needed,
            "execution_mode": execution_plan.execution_mode,
            "pipeline_steps": len(execution_plan.pipeline),
            "reasoning": execution_plan.reasoning[:150] if execution_plan.reasoning else ""
        })
        print(f"[Orchestrator] Plan: {execution_plan.agents_needed} ({execution_plan.execution_mode})")

        # Step 2: 컨텍스트 강화 (메모리 검색)
        debug_log("Orchestrator", "[Step 2/5] Enriching context from memory...")
        enriched_context = self._enrich_context(task, context)
        debug_log("Orchestrator", "Enriched context keys", list(enriched_context.keys()))

        # Step 3: 에이전트 파이프라인 실행
        debug_log("Orchestrator", "[Step 3/5] Executing agent pipeline...")
        results = self._execute_pipeline(execution_plan, enriched_context)
        debug_log("Orchestrator", f"Pipeline completed with {len(results)} agent results")

        # Step 4: 결과 통합
        debug_log("Orchestrator", "[Step 4/5] Integrating results...")
        final_result = self._integrate_results(results, task)
        debug_log("Orchestrator", "Integration result", {
            "status": final_result.status.value,
            "output_length": len(final_result.output),
            "artifacts_count": len(final_result.artifacts),
            "errors_count": len(final_result.errors)
        })

        # Step 5: 메모리 업데이트
        debug_log("Orchestrator", "[Step 5/5] Updating memory...")
        self._update_memory(task, final_result)

        execution_time = int((time.time() - start_time) * 1000)

        debug_log("Orchestrator", "╔═══════════════════════════════════════════╗")
        debug_log("Orchestrator", "║        ORCHESTRATOR RUN COMPLETE        ║")
        debug_log("Orchestrator", "╚═══════════════════════════════════════════╝")
        debug_log("Orchestrator", "Final summary", {
            "execution_time_ms": execution_time,
            "agents_executed": len(results),
            "final_status": final_result.status.value
        })
        print(f"[Orchestrator] Completed in {execution_time}ms")

        return OrchestratorResult(
            task=task,
            execution_plan=execution_plan,
            agent_results=results,
            final_output=final_result.output,
            context_updates=final_result.context_updates,
            execution_time_ms=execution_time
        )

    # ============ 작업 분석 ============

    def _analyze_and_plan(self, task: str) -> ExecutionPlan:
        """
        LLM을 사용하여 작업 분석 및 실행 계획 생성
        """
        analysis_prompt = """You are a Task Analyzer for a coding agent system.

Analyze the given task and create an execution plan.

Available Agents:
1. explore - 코드베이스 탐색, 파일 검색, 패턴 분석 (읽기 전용)
2. plan - 전략 수립, 단계 분해, 구현 계획 (분석 전용)
3. review - 코드 리뷰, 버그 탐지, 품질 검사
4. execute - 실제 코드 작성, 파일 수정, 명령 실행

Execution Modes:
- sequential: 순차 실행 (이전 결과가 다음에 필요)
- parallel: 병렬 실행 (독립적인 작업)
- pipeline: 순차 + 병렬 혼합

Guidelines:
- Simple tasks (fix typo, add comment) -> execute only
- Search/find tasks -> explore only
- Planning tasks -> plan only
- Complex tasks -> explore -> plan -> execute
- Review requests -> review (+ execute if fixes needed)

Output JSON only:
{
    "task_type": "simple|complex|multi_step",
    "complexity_score": 1-10,
    "agents_needed": ["explore", "plan", "execute"],
    "execution_mode": "sequential",
    "pipeline": [
        {"step": 1, "agents": ["explore"], "parallel": false, "description": "Search codebase"},
        {"step": 2, "agents": ["plan"], "parallel": false, "description": "Create plan"},
        {"step": 3, "agents": ["execute"], "parallel": false, "description": "Execute"}
    ],
    "reasoning": "..."
}"""

        messages = [
            {"role": "system", "content": analysis_prompt},
            {"role": "user", "content": f"Task: {task}"}
        ]

        try:
            response = self.llm_call_func(messages)
            return self._parse_execution_plan(response)
        except Exception as e:
            print(f"[Orchestrator] Analysis failed: {e}, using default plan")
            return self._default_plan()

    def _parse_execution_plan(self, response: str) -> ExecutionPlan:
        """LLM 응답에서 ExecutionPlan 파싱"""
        try:
            # JSON 블록 추출
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return ExecutionPlan.from_dict(data)
        except Exception as e:
            print(f"[Orchestrator] Parse error: {e}")

        return self._default_plan()

    def _default_plan(self) -> ExecutionPlan:
        """기본 실행 계획"""
        return ExecutionPlan(
            task_type="simple",
            complexity_score=3,
            agents_needed=["execute"],
            execution_mode="sequential",
            pipeline=[PipelineStep(step=1, agents=["execute"], parallel=False)],
            reasoning="Default execution plan"
        )

    # ============ 파이프라인 실행 ============

    def _execute_pipeline(
        self,
        plan: ExecutionPlan,
        context: Dict[str, Any]
    ) -> List[SubAgentResult]:
        """
        실행 계획에 따라 에이전트 파이프라인 실행
        """
        all_results = []
        accumulated_context = context.copy()

        debug_log("Orchestrator", f"\n═══ Pipeline execution started ({len(plan.pipeline)} steps) ═══")

        for step in plan.pipeline:
            debug_log("Orchestrator", f"\n▶ Pipeline Step {step.step}: {step.description}")
            debug_log("Orchestrator", "Step config", {
                "agents": step.agents,
                "parallel": step.parallel
            })
            print(f"[Orchestrator] Step {step.step}: {step.agents}")

            # 병렬 실행 여부 결정
            use_parallel = (
                self.parallel_enabled and
                step.parallel and
                len(step.agents) > 1
            )

            debug_log("Orchestrator", f"Execution mode: {'PARALLEL' if use_parallel else 'SEQUENTIAL'}")

            if use_parallel:
                step_results = self._execute_parallel(step.agents, accumulated_context)
            else:
                step_results = self._execute_sequential(step.agents, accumulated_context)

            all_results.extend(step_results)

            # 다음 단계를 위해 컨텍스트 업데이트
            for result in step_results:
                if result.status == AgentStatus.COMPLETED:
                    accumulated_context.update(result.context_updates)
                    # 이전 출력도 전달
                    accumulated_context["previous_output"] = result.output

            debug_log("Orchestrator", f"✓ Step {step.step} completed with {len(step_results)} results")

        debug_log("Orchestrator", f"\n═══ Pipeline execution finished ({len(all_results)} total results) ═══")
        return all_results

    def _execute_parallel(
        self,
        agent_types: List[str],
        context: Dict[str, Any]
    ) -> List[SubAgentResult]:
        """에이전트 병렬 실행 (ThreadPoolExecutor)"""
        results = []

        with ThreadPoolExecutor(max_workers=min(len(agent_types), self.max_workers)) as executor:
            futures = {}
            for agent_type in agent_types:
                agent = self._create_agent(agent_type)
                if agent:
                    # C2 Fix: 각 에이전트에 독립적인 context 사본 전달 (race condition 방지)
                    context_copy = copy.deepcopy(context)
                    future = executor.submit(
                        agent.run,
                        context.get("task", ""),
                        context_copy
                    )
                    futures[future] = agent_type
                else:
                    print(f"[Orchestrator] Warning: Unknown agent type '{agent_type}' skipped")

            for future in as_completed(futures):
                agent_type = futures[future]
                try:
                    result = future.result(timeout=self.timeout)
                    results.append(result)
                    print(f"[Orchestrator] {agent_type} completed")
                except FuturesTimeoutError:
                    # H3 Fix: 타임아웃과 일반 예외 구분
                    print(f"[Orchestrator] {agent_type} timeout after {self.timeout}s")
                    results.append(SubAgentResult(
                        status=AgentStatus.FAILED,
                        output="",
                        errors=[f"{agent_type}: Timeout after {self.timeout}s"]
                    ))
                except Exception as e:
                    print(f"[Orchestrator] {agent_type} failed: {e}")
                    results.append(SubAgentResult(
                        status=AgentStatus.FAILED,
                        output="",
                        errors=[f"{agent_type}: {str(e)}"]
                    ))

        return results

    def _execute_sequential(
        self,
        agent_types: List[str],
        context: Dict[str, Any]
    ) -> List[SubAgentResult]:
        """에이전트 순차 실행"""
        results = []
        current_context = context.copy()

        debug_log("Orchestrator", f"Sequential execution: {agent_types}")

        for agent_type in agent_types:
            agent = self._create_agent(agent_type)
            if not agent:
                debug_log("Orchestrator", f"⚠ Unknown agent type: {agent_type}")
                print(f"[Orchestrator] Unknown agent type: {agent_type}")
                continue

            debug_log("Orchestrator", f"\n  → Spawning {agent_type} agent...")
            print(f"[Orchestrator] Running {agent_type}...")
            result = agent.run(current_context.get("task", ""), current_context)
            results.append(result)

            # 다음 에이전트를 위해 컨텍스트 업데이트
            if result.status == AgentStatus.COMPLETED:
                current_context.update(result.context_updates)
                current_context["previous_output"] = result.output
                debug_log("Orchestrator", f"  ✓ {agent_type} completed")
                print(f"[Orchestrator] {agent_type} completed")
            else:
                debug_log("Orchestrator", f"  ✗ {agent_type} failed", result.errors)
                print(f"[Orchestrator] {agent_type} failed: {result.errors}")

        return results

    def _create_agent(self, agent_type: str) -> Optional[SubAgent]:
        """에이전트 인스턴스 생성"""
        if agent_type not in self._agent_classes:
            return None

        AgentClass = self._agent_classes[agent_type]
        return AgentClass(
            name=f"{agent_type}_agent",
            llm_call_func=self.llm_call_func,
            execute_tool_func=self.execute_tool_func
        )

    # ============ 결과 통합 ============

    def _integrate_results(
        self,
        results: List[SubAgentResult],
        task: str
    ) -> SubAgentResult:
        """
        모든 에이전트 결과를 통합하여 최종 결과 생성
        """
        # 모든 출력 합치기
        outputs = []
        for r in results:
            if r.status == AgentStatus.COMPLETED and r.output:
                strategy = r.action_plan.strategy if r.action_plan else 'Result'
                outputs.append(f"## {strategy}\n{r.output}")

        combined_output = "\n\n---\n\n".join(outputs) if outputs else ""

        # 모든 context_updates 병합
        merged_updates = {}
        for r in results:
            if r.context_updates:
                merged_updates.update(r.context_updates)

        # 모든 artifacts 병합
        merged_artifacts = {}
        for r in results:
            if r.artifacts:
                for key, value in r.artifacts.items():
                    if key in merged_artifacts and isinstance(value, list):
                        merged_artifacts[key].extend(value)
                    else:
                        merged_artifacts[key] = value

        # 에러 수집
        all_errors = []
        for r in results:
            if r.errors:
                all_errors.extend(r.errors)

        # 최종 상태 결정
        if not results:
            final_status = AgentStatus.FAILED
        elif all(r.status == AgentStatus.COMPLETED for r in results):
            final_status = AgentStatus.COMPLETED
        elif any(r.status == AgentStatus.FAILED for r in results):
            final_status = AgentStatus.FAILED
        else:
            final_status = AgentStatus.COMPLETED

        return SubAgentResult(
            status=final_status,
            output=combined_output,
            artifacts=merged_artifacts,
            context_updates=merged_updates,
            errors=all_errors
        )

    # ============ 메모리 통합 ============

    def _enrich_context(
        self,
        task: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """메모리에서 관련 정보 검색하여 컨텍스트 강화"""
        enriched = {"task": task}
        if context:
            enriched.update(context)

        # GraphLite에서 관련 지식 검색
        if self.graph_lite:
            try:
                # hybrid_search 사용 (BM25 + Embedding)
                if hasattr(self.graph_lite, 'hybrid_search'):
                    results = self.graph_lite.hybrid_search(task, limit=3)
                else:
                    results = self.graph_lite.search(task, limit=3)

                if results:
                    enriched["knowledge"] = [
                        {
                            "content": node.data.get("content", "") or node.data.get("description", ""),
                            "quality": self.graph_lite.get_node_quality_score(node)
                            if hasattr(self.graph_lite, 'get_node_quality_score') else 0.5
                        }
                        for score, node in results
                    ]
            except Exception as e:
                print(f"[Orchestrator] GraphLite search failed: {e}")

        # ProceduralMemory에서 유사 경험 검색
        if self.procedural_memory:
            try:
                similar = self.procedural_memory.retrieve(task, limit=2)
                if similar:
                    enriched["past_experiences"] = [
                        {
                            "task": traj.task_type,
                            "outcome": traj.outcome,
                            "actions": traj.actions[:3] if hasattr(traj, 'actions') else []
                        }
                        for score, traj in similar
                    ]
            except Exception as e:
                print(f"[Orchestrator] ProceduralMemory search failed: {e}")

        return enriched

    def _update_memory(self, task: str, result: SubAgentResult):
        """실행 결과를 메모리에 저장"""
        if result.status != AgentStatus.COMPLETED:
            return

        # GraphLite: 주요 발견사항 저장
        if self.graph_lite and result.context_updates:
            try:
                summary = result.context_updates.get("summary", "")
                if summary and hasattr(self.graph_lite, 'add_note_with_auto_linking'):
                    self.graph_lite.add_note_with_auto_linking(
                        content=summary[:500],
                        context={"source": "orchestrator", "task": task[:100]}
                    )
                    self.graph_lite.save()
            except Exception as e:
                print(f"[Orchestrator] Memory update failed: {e}")

        # 실행 히스토리에 추가
        self._execution_history.append({
            "task": task,
            "agents_used": [r.action_plan.strategy if r.action_plan else "unknown"
                           for r in [result]],
            "success": result.status == AgentStatus.COMPLETED,
            "timestamp": time.time()
        })

    # ============ 유틸리티 ============

    def get_execution_history(self) -> List[Dict]:
        """실행 히스토리 반환"""
        return self._execution_history.copy()

    def clear_history(self):
        """실행 히스토리 초기화"""
        self._execution_history.clear()
