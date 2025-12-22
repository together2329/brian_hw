"""
PlanAgent - 전략 수립 및 계획 에이전트

도구 실행 없이 분석만 수행하여 전략과 단계별 계획을 수립합니다.
"""

import re
from typing import Dict, Any, Set

from .base import SubAgent, ActionStep, SubAgentResult, AgentStatus


class PlanAgent(SubAgent):
    """
    전략 수립 및 계획 에이전트

    - 도구 실행 없이 분석만 수행
    - 전략 수립, 단계 분해
    - 결과: strategy, steps, dependencies
    """

    # Explore tool allowed for context gathering during planning
    ALLOWED_TOOLS: Set[str] = {"spawn_explore"}

    def _get_planning_prompt(self) -> str:
        return """You are a Planning Agent for a coding assistant.
Your role is to create TEXT-ONLY implementation plans and specifications.

CRITICAL CONSTRAINTS:
- DO NOT write actual code, modules, or implementations
- DO NOT generate Verilog, Python, or any code snippets
- ONLY create textual descriptions of WHAT to do
- If you need repository context, use spawn_explore(query="...") in the execution phase

OUTPUT FORMAT (TEXT ONLY):
## Task Analysis
[What needs to be done]

## Interface Specification
- Module: ...
- Parameters: ...
- Inputs: ...
- Outputs: ...

## Architecture
[Text description of internal architecture]

## Implementation Steps
1. ...
2. ...

## Verification Strategy
- Test 1: ...
- Test 2: ...

## Success Criteria
- ...

Be specific but DO NOT write code - leave that to ExecuteAgent."""

    def _get_execution_prompt(self) -> str:
        return """You are a Planning Agent. Create a detailed TEXT-ONLY plan for the task.

You MAY use spawn_explore(query="...") to gather repository context if needed.
DO NOT write any code - only text descriptions and specifications.

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
            "tool_calls_count": len(self._tool_calls)
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 계획 정보"""
        # 계획에서 주요 단계 추출 시도
        steps = []
        import re
        if "## Implementation Steps" in output:
            steps_section = output.split("## Implementation Steps")[-1].split("##")[0]
            step_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', steps_section, re.DOTALL)
            steps = [s.strip()[:100] for s in step_matches[:5]]
        elif "## Steps" in output:
            steps_section = output.split("## Steps")[-1].split("##")[0]
            step_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', steps_section, re.DOTALL)
            steps = [s.strip()[:100] for s in step_matches[:5]]
        else:
            step_matches = re.findall(r'^\s*\d+\.\s*(.+)$', output, re.MULTILINE)
            steps = [s.strip()[:100] for s in step_matches[:5]]

        return {
            "plan_summary": output[:500] if output else "",
            "planned_steps": steps,
            "agent_type": "plan"
        }

    def _extract_plan_text(self, output: str) -> str:
        if not output:
            return ""
        if "Result:" in output:
            tail = output.split("Result:", 1)[1].strip()
            if tail:
                return tail
        text = output.strip()
        if text.startswith("Thought:"):
            lines = text.splitlines()
            if len(lines) > 1:
                cleaned = "\n".join(lines[1:]).strip()
                if cleaned:
                    return cleaned
        return text

    def _run_plan_prompt(self, prompt: str) -> SubAgentResult:
        self._reset_state()
        self._status = AgentStatus.RUNNING

        step = ActionStep(
            step_number=1,
            description="Generate plan",
            prompt=prompt,
            required_tools=list(self.ALLOWED_TOOLS),
            depends_on=[],
            expected_output="A detailed text-only implementation plan"
        )

        output = self._execute_step(step, context="")
        plan_text = self._extract_plan_text(output)

        if not plan_text:
            fallback = self._fallback_generate_plan(prompt)
            plan_text = fallback.strip()

        status = AgentStatus.COMPLETED if plan_text else AgentStatus.FAILED
        errors = [] if plan_text else ["No plan content generated"]

        return SubAgentResult(
            status=status,
            output=plan_text,
            artifacts=self._collect_artifacts(),
            context_updates=self._collect_context_updates(plan_text),
            tool_calls=self._tool_calls,
            errors=errors
        )

    def _fallback_generate_plan(self, prompt: str) -> str:
        tool_notes = self._format_tool_observations()
        fallback_prompt = f"""You are a Planning Agent.
Return ONLY the plan content using the required markdown format.
Do NOT include Thought/Action/Result tags.

{prompt}

{tool_notes}

OUTPUT FORMAT:
## Task Analysis
...

## Interface Specification
- Module: ...
- Parameters: ...
- Inputs: ...
- Outputs: ...

## Architecture
...

## Implementation Steps
1. ...
2. ...

## Verification Strategy
- Test 1: ...

## Success Criteria
- ...
"""
        messages = [
            {"role": "system", "content": "Return only the plan text in the required format."},
            {"role": "user", "content": fallback_prompt},
        ]
        return self.llm_call_func(messages) or ""

    def _format_tool_observations(self) -> str:
        if not self._tool_calls:
            return "Tool observations: None"
        lines = ["Tool observations:"]
        for call in self._tool_calls[-5:]:
            tool = call.get("tool", "unknown")
            result = str(call.get("result", "")).strip()
            lines.append(f"- {tool}: {result}")
        return "\n".join(lines)

    def draft_plan(self, task: str, context: str = "") -> SubAgentResult:
        prompt = f"""Task:
{task}

Context:
{context if context else "None"}

Create a detailed plan using the required format.
Use spawn_explore(query="...") only if needed to gather context.
"""
        return self._run_plan_prompt(prompt)

    def refine(self, user_feedback: str, current_plan: str, context: str = "") -> SubAgentResult:
        prompt = f"""Current plan:
{current_plan}

User feedback:
{user_feedback}

Context:
{context if context else "None"}

Revise the plan to address the feedback.
Keep the same format and improve clarity and specificity.
Use spawn_explore(query="...") only if additional context is needed.
"""
        return self._run_plan_prompt(prompt)
