"""
PlanAgent - 전략 수립 및 계획 에이전트

도구 실행 없이 분석만 수행하여 전략과 단계별 계획을 수립합니다.
"""

from typing import Dict, Any, Set

from .base import SubAgent


class PlanAgent(SubAgent):
    """
    전략 수립 및 계획 에이전트

    - 도구 실행 없이 분석만 수행
    - 전략 수립, 단계 분해
    - 결과: strategy, steps, dependencies
    """

    # 도구 없음 - 순수 분석
    ALLOWED_TOOLS: Set[str] = set()

    def _get_planning_prompt(self) -> str:
        return """You are a Planning Agent for a coding assistant.
Your role is to analyze tasks and create detailed implementation plans.

YOU DO NOT EXECUTE ANY TOOLS. You only analyze and plan.

OUTPUT FORMAT:
1. Task Analysis: What needs to be done
2. Strategy: High-level approach
3. Steps: Detailed numbered steps with:
   - Description
   - Files to modify
   - Expected changes
4. Dependencies: What needs to exist/work first
5. Risks: Potential issues and mitigations
6. Success Criteria: How to verify completion

Be specific and actionable in your plans."""

    def _get_execution_prompt(self) -> str:
        return """You are a Planning Agent. Create a detailed plan for the task.

DO NOT use any tools. Just analyze and provide your plan.

FORMAT:
Thought: [your analysis]
Result:
## Task Analysis
[What needs to be done]

## Strategy
[High-level approach]

## Steps
1. [First step with details]
2. [Second step with details]
...

## Dependencies
- [Dependency 1]
- [Dependency 2]

## Risks
- [Risk 1]: [Mitigation]

## Success Criteria
- [Criterion 1]
- [Criterion 2]"""

    def _collect_artifacts(self) -> Dict[str, Any]:
        """계획 산출물"""
        return {
            "plan_generated": True,
            "tool_calls_count": 0
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 계획 정보"""
        # 계획에서 주요 단계 추출 시도
        steps = []
        if "## Steps" in output:
            steps_section = output.split("## Steps")[-1].split("##")[0]
            import re
            step_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', steps_section, re.DOTALL)
            steps = [s.strip()[:100] for s in step_matches[:5]]

        return {
            "plan_summary": output[:500] if output else "",
            "planned_steps": steps,
            "agent_type": "plan"
        }
