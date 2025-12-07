"""
CodeReviewAgent - 코드 리뷰 에이전트

코드를 읽고 분석하여 버그, 스타일 이슈, 개선점을 찾습니다.
"""

from typing import Dict, Any, Set

from .base import SubAgent


class CodeReviewAgent(SubAgent):
    """
    코드 리뷰 에이전트

    - 코드 읽기 + 분석
    - 버그 탐지, 스타일 검사
    - 결과: issues, recommendations
    """

    # 읽기 전용 도구 + 분석 도구
    ALLOWED_TOOLS: Set[str] = {
        'read_file',
        'read_lines',
        'grep_file',
        'list_dir',
        'find_files',
        'git_status',
        'git_diff',
        'rag_search',
        'analyze_verilog_module',
        'find_potential_issues',
        'analyze_timing_paths'
    }

    def _get_planning_prompt(self) -> str:
        return """You are a Code Review Agent for a coding assistant.
Your role is to review code for bugs, style issues, and potential improvements.

REVIEW CHECKLIST:
1. Correctness: Logic errors, edge cases, off-by-one errors
2. Style: Naming conventions, formatting, code organization
3. Performance: Inefficiencies, unnecessary operations
4. Security: Input validation, injection risks, data exposure
5. Maintainability: Code clarity, documentation, modularity

AVAILABLE TOOLS:
- read_file(path="...") - Read file content
- grep_file(pattern="...", path="...") - Search for patterns
- git_diff(path=None) - Show changes
- find_potential_issues(path="...") - Find issues in Verilog

OUTPUT FORMAT:
Provide a structured review with:
- Summary: Overall assessment
- Issues: List of problems found
- Recommendations: Suggested improvements"""

    def _get_execution_prompt(self) -> str:
        return """You are a Code Review Agent. Review the code and provide feedback.

FORMAT:
Thought: [what to examine]
Action: tool_name(arg1="value1")

After analysis:
Thought: [what issues were found]
Result:
## Summary
[Overall assessment: Good/Needs Work/Critical Issues]

## Issues Found
### Critical
- [Issue 1]: [Description] (Line X)
  - Fix: [Suggested fix]

### Major
- [Issue 2]: [Description]

### Minor
- [Issue 3]: [Description]

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Code Quality Score: X/10"""

    def _collect_artifacts(self) -> Dict[str, Any]:
        """리뷰 산출물"""
        return {
            "files_reviewed": self._files_read.copy(),
            "tool_calls_count": len(self._tool_calls)
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 리뷰 정보"""
        # 이슈 개수 추출 시도
        import re
        critical_count = len(re.findall(r'### Critical\n(.*?)(?=###|## |$)', output, re.DOTALL))
        major_count = len(re.findall(r'### Major\n(.*?)(?=###|## |$)', output, re.DOTALL))

        return {
            "review_summary": output[:500] if output else "",
            "files_reviewed": self._files_read.copy(),
            "issues_found": {
                "critical": critical_count,
                "major": major_count
            },
            "agent_type": "review"
        }
