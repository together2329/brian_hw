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
Your role is to create TEXT-ONLY implementation plans and specifications.

⚠️ CRITICAL CONSTRAINTS:
- YOU DO NOT EXECUTE ANY TOOLS
- DO NOT write actual code, modules, or implementations
- DO NOT generate Verilog, Python, or any code snippets
- ONLY create textual descriptions of WHAT to do, not HOW in code

OUTPUT FORMAT (TEXT ONLY):
1. Task Analysis: What needs to be done (text description)
2. Interface Specification:
   - Module name, parameters, ports (as a list, NOT code)
   - Signal names and widths
3. Architecture Description:
   - Block diagram in text form
   - Data flow description
4. Implementation Steps: Detailed numbered steps with:
   - Description of what to implement
   - Files to create/modify
   - Key design decisions
5. Verification Strategy:
   - What tests to write
   - Expected behaviors to verify
6. Success Criteria: How to verify completion

Be specific but DO NOT write actual code - leave that to ExecuteAgent."""

    def _get_execution_prompt(self) -> str:
        return """You are a Planning Agent. Create a detailed TEXT-ONLY plan for the task.

DO NOT use any tools. Just analyze and provide your plan.
⚠️ DO NOT write any code - only text descriptions and specifications.

FORMAT:
Thought: [your analysis]
Result:
## Task Analysis
[What needs to be done - text description]

## Interface Specification
- Module: [name]
- Parameters: [list of parameters with descriptions]
- Inputs: [list of input signals with widths]
- Outputs: [list of output signals with widths]

## Architecture
[Text description of internal architecture]
[Block diagram in ASCII or description]

## Implementation Steps
1. [First step - what to do, not code]
2. [Second step - what to do, not code]
...

## Verification Strategy
- Test 1: [what to test]
- Test 2: [what to test]

## Success Criteria
- [Criterion 1]
- [Criterion 2]

Remember: NO CODE - ExecuteAgent will write the actual implementation."""

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
