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

# ============================================================
# PLAN QUALITY CHECKLIST (All must be ✅)
# ============================================================

Before outputting your plan, verify:
- ✅ Every file change has absolute path (e.g., `brian_coder/src/config.py`)
- ✅ Major changes have line numbers (e.g., "Line 145-160")
- ✅ Steps are grouped into Phases (Phase 1, 2, 3...)
- ✅ Each phase has time estimate (e.g., "10분", "30분")
- ✅ New files marked with "(NEW)"
- ✅ Interface changes show before/after

If ANY ✅ is missing → Your plan is TOO VAGUE → Revise it.

# ============================================================
# OUTPUT FORMAT (Mandatory Structure)
# ============================================================

# [Task Title]

## Overview
[1-2 sentences: What is being done and why]

## Critical Files
1. `path/to/file1.py` - Purpose
2. `path/to/file2.py (NEW)` - Purpose

## Phase 1: [Name] (Time estimate)
**File**: `path/to/file`
**Line X-Y**: Description
**Changes**: [Specific changes]

## Phase 2: [Name] (Time estimate)
...

## Testing Strategy
- Unit tests: [File path + test names]
- Integration: [Scenario]

## Success Criteria
- [ ] Checklist item 1
- [ ] Checklist item 2

Be specific but DO NOT write code - leave that to ExecuteAgent."""

    def _get_execution_prompt(self) -> str:
        return """You are a Planning Agent. Create detailed, specific implementation plans.

# ============================================================
# CRITICAL: PARALLEL EXECUTION (Highly Recommended)
# ============================================================

**YOU CAN SPAWN MULTIPLE EXPLORE AGENTS IN PARALLEL**

When you need context from multiple sources, spawn them ALL AT ONCE:

✅ CORRECT (Parallel - Fast):
Thought: I need to understand modules, tests, and documentation.
@parallel
Action: spawn_explore(query="Find all module definitions", thoroughness="medium")
Action: spawn_explore(query="Find test patterns", thoroughness="quick")
Action: spawn_explore(query="Find documentation structure", thoroughness="quick")
@end_parallel
Observation: [All 3 results arrive together in 20s]

❌ WRONG (Sequential - Slow):
Thought: Let me find modules first.
Action: spawn_explore(query="Find modules")
Observation: [wait 20s...]
Thought: Now tests.
Action: spawn_explore(query="Find tests")
Observation: [wait 20s...]
Total: 60s ← DON'T DO THIS!

**Default to parallel unless truly dependent.**

# ============================================================
# CRITICAL: FILE PATHS & LINE NUMBERS (Mandatory)
# ============================================================

**Your plan MUST include specific file paths and line numbers.**

✅ CORRECT (Specific):
## Phase 1: Add helper function (10분)

**File**: `brian_coder/core/tools.py`
**Location**: Line 545-580 (after validate_args function)

**Change**:
Add _levenshtein_distance() helper function

❌ WRONG (Vague):
## Step 1: Add helper

Add a function to calculate string distance.

**Requirements:**
- Use format: "File: `path/to/file.py`"
- Use format: "Line N-M: description"
- Use format: "(NEW)" for new files

# ============================================================
# GOOD vs BAD PLAN EXAMPLES
# ============================================================

❌ BAD PLAN (Too vague):
## Steps
1. Update the configuration
2. Modify the main file
3. Add tests

Problems: No file paths, no line numbers, no specifics.

✅ GOOD PLAN (Specific):
## Phase 1: Configuration Update (5분)

**File**: `src/config.py`
**Line 145-147**: Replace TIMEOUT value

**Change**:
```
# Before:
TIMEOUT = 100

# After:
TIMEOUT = 200
```

## Phase 2: Main Logic Update (15분)

**File**: `src/main.py`
**Line 320-340**: Refactor error handling

**Changes**:
1. Extract retry logic to separate function
2. Add exponential backoff
3. Update error messages

**Pattern to follow:**
- File path first
- Line numbers for changes
- "Before/After" for replacements
- Phase separation
- Time estimates

# ============================================================
# GATHER CONTEXT FIRST (Critical)
# ============================================================

**ALWAYS explore the codebase BEFORE creating plan.**

Step 1: Spawn 2-3 explore agents in parallel
Step 2: Analyze findings
Step 3: Create specific plan

❌ ANTI-PATTERN:
Thought: I'll plan based on task description.
PLAN_COMPLETE: [plan without exploration]

✅ CORRECT PATTERN:
Thought: Need to explore first.
@parallel
Action: spawn_explore(query="Find existing modules")
Action: spawn_explore(query="Find test patterns")
@end_parallel
Observation: [findings]
Thought: Now I have complete context.
PLAN_COMPLETE: [specific plan with file paths]

# ============================================================
# Planning Output Format
# ============================================================

After gathering context, create your plan:

PLAN_COMPLETE: [Your detailed implementation plan in markdown]

**Plan should include:**
1. Overview
2. Critical files to modify (with paths!)
3. Step-by-step implementation (with line numbers!)
4. Verification strategy

**Remember:**
- Text descriptions only (no code)
- Specify interfaces and architecture
- List files and their purposes
- Describe what to do, not how to code it
"""

    def _create_user_message(self, step: ActionStep, context: str) -> str:
        """Custom user message for PlanAgent to avoid checking ReAct format conflicts."""
        return f"""
{step.prompt}

{context if context else ""}

Expected Output: A detailed text-only implementation plan
Available Tools: {step.required_tools}

Make sure to use the format:
Thought: ...
PLAN_COMPLETE: ...
"""

    def _collect_artifacts(self) -> Dict[str, Any]:
        """계획 산출물"""
        return {
            "plan_generated": True,
            "tool_calls_count": len(self._tool_calls)
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 계획 정보 (개선: Phase 추출)"""
        # 계획에서 주요 단계 추출 시도
        steps = []
        import re

        # Try Phase pattern first (most specific)
        phase_matches = re.findall(r'## Phase \d+[:\s]+(.+?)(?:\(|$)', output, re.MULTILINE)
        if phase_matches:
            steps = [f"Phase {idx+1}: {match.strip()}" for idx, match in enumerate(phase_matches)]
        # Try Implementation Steps section
        elif "## Implementation Steps" in output:
            steps_section = output.split("## Implementation Steps")[-1].split("##")[0]
            step_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', steps_section, re.DOTALL)
            steps = [s.strip()[:100] for s in step_matches[:5]]
        elif "## Steps" in output:
            steps_section = output.split("## Steps")[-1].split("##")[0]
            step_matches = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n##|$)', steps_section, re.DOTALL)
            steps = [s.strip()[:100] for s in step_matches[:5]]
        else:
            # Generic numbered list
            step_matches = re.findall(r'^\s*\d+\.\s*(.+)$', output, re.MULTILINE)
            steps = [s.strip()[:100] for s in step_matches[:5]]

        return {
            "plan_summary": output[:500] if output else "",
            "planned_steps": steps,
            "agent_type": "plan"
        }

    def _extract_plan_text(self, output: str) -> str:
        """
        Extract plan text from agent output.

        Supports multiple formats:
        - "PLAN_COMPLETE: ..."
        - "**PLAN_COMPLETE**" (markdown bold)
        - "[CONTENT] .**PLAN_COMPLETE**" (with content marker)
        """
        if not output:
            return ""

        # Try all PLAN_COMPLETE variants
        plan_markers = [
            "**PLAN_COMPLETE**",  # Most common (markdown bold)
            "PLAN_COMPLETE:",     # Old format
            "PLAN_COMPLETE",      # Without colon
        ]

        for marker in plan_markers:
            if marker in output:
                tail = output.split(marker, 1)[1].strip()
                if tail:
                    return tail

        # Try "Result:" marker
        if "Result:" in output:
            tail = output.split("Result:", 1)[1].strip()
            if tail:
                return tail

        # Try extracting from [CONTENT] block (some models wrap it)
        if "[CONTENT]" in output:
            # Pattern: "[CONTENT] .**PLAN_COMPLETE**\n\n[actual plan]"
            content_start = output.find("[CONTENT]")
            if content_start != -1:
                tail = output[content_start + len("[CONTENT]"):].strip()
                # Remove any leading markers
                for marker in plan_markers:
                    if tail.startswith(marker):
                        tail = tail[len(marker):].strip()
                if tail:
                    return tail

        # Fallback: remove leading "Thought:" lines
        text = output.strip()
        if text.startswith("Thought:"):
            lines = text.splitlines()
            if len(lines) > 1:
                cleaned = "\n".join(lines[1:]).strip()
                if cleaned:
                    return cleaned

        # Return as-is if no pattern matched
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
