"""
ExploreAgent - 코드베이스 탐색 전용 에이전트

읽기 전용 도구만 사용하여 코드베이스를 탐색하고 정보를 수집합니다.
"""

from typing import Dict, Any, Set

from .base import SubAgent


class ExploreAgent(SubAgent):
    """
    코드베이스 탐색 전용 에이전트

    - 읽기 전용 도구만 사용
    - 파일 검색, 패턴 분석, 구조 파악
    - 결과: files_examined, patterns, findings
    """

    # 읽기 전용 도구만 허용
    ALLOWED_TOOLS: Set[str] = {
        'read_file',
        'read_lines',
        'grep_file',
        'list_dir',
        'find_files',
        'git_status',
        'git_diff',
        'rag_search',
        'rag_status',
        'analyze_verilog_module',
        'find_signal_usage',
        'find_module_definition',
        'extract_module_hierarchy'
    }

    def _get_planning_prompt(self) -> str:
        return """You are an Exploration Agent for a coding assistant.
Your role is ONLY to explore codebases and gather information.

⚠️ CRITICAL CONSTRAINTS:
- You can ONLY use read-only tools (no write, no run_command)
- DO NOT generate any code, modules, or implementations
- DO NOT draft solutions or write code snippets
- ONLY gather information, analyze structure, and summarize findings

AVAILABLE TOOLS:
- read_file(path="...") - Read entire file
- read_lines(path="...", start_line=N, end_line=M) - Read specific lines
- grep_file(pattern="...", path="...", context_lines=2) - Search patterns
- list_dir(path=".") - List directory contents
- find_files(pattern="*.py", directory=".") - Find files by pattern
- git_status() - Show git status
- git_diff(path=None) - Show git diff
- rag_search(query="...", categories="verilog", limit=5) - Semantic search

OUTPUT FOCUS (Information Only):
1. List relevant existing files and their purposes
2. Identify coding conventions and patterns used
3. Find similar implementations for reference
4. Document dependencies and interfaces
5. Summarize directory structure

DO NOT: Generate code, write implementations, create modules, or draft solutions."""

    def _get_execution_prompt(self) -> str:
        return """You are an Exploration Agent. Execute the exploration task using read-only tools.

FORMAT:
Thought: [your reasoning about what to explore next]
Action: tool_name(arg1="value1", arg2="value2")

# ============================================================
# CRITICAL: PARALLEL EXECUTION (Claude Code Style)
# ============================================================

**YOU MUST OUTPUT MULTIPLE ACTIONS PER RESPONSE**

✅ CORRECT (Parallel - Fast):
Thought: Need to explore multiple files simultaneously.
@parallel
Action: find_files(pattern="*.py", directory=".")
Action: list_dir(path="agents")
Action: rag_search(query="ExploreAgent", limit=3)
@end_parallel

✅ CORRECT (Sequential when needed):
@sequential
Action: read_file(path="step1_spec.md")
Action: read_file(path="step2_design.md")
@end_sequential

❌ WRONG (One action at a time - Slow):
Thought: Need to find files.
Action: find_files(pattern="*.py")
[WAIT] ← DON'T DO THIS!

**Tool Classification:**
- Read-only (ALWAYS parallel-safe): read_file, grep_file, list_dir, find_files, rag_search
- Use @parallel for independent read operations
- Use @sequential only when order matters (rare)

When done:
Thought: [summary of findings]
EXPLORE_COMPLETE: [structured findings - FILES FOUND, PATTERNS, CONVENTIONS]

⚠️ CRITICAL RULES:
- Output 3-5 actions per response when exploring
- Use @parallel for simultaneous file operations
- Only use read-only tools
- NEVER generate code or implementations
- Only report what EXISTS in the codebase

Your output should be INFORMATION about the codebase, NOT solutions or code."""

    def _collect_artifacts(self) -> Dict[str, Any]:
        """탐색 결과 산출물 수집"""
        return {
            "files_read": self._files_read.copy(),
            "tool_calls_count": len(self._tool_calls),
            "exploration_depth": len(set(self._files_read))
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 정보 (개선: tool 결과에서 파일 추출)"""
        files_examined = self._files_read.copy()

        # Extract files from tool calls (find_files, grep_file results)
        for tool_call in self._tool_calls:
            tool_name = tool_call.get('tool', '')
            result = tool_call.get('result', '')

            if tool_name == 'find_files' and result:
                # Parse file list from find_files result
                for line in result.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('Error') and '.' in line:
                        if line not in files_examined:
                            files_examined.append(line)

            elif tool_name in ['read_file', 'read_lines', 'grep_file']:
                # Extract file path from args
                args = tool_call.get('args', '')
                import re
                match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', args)
                if match:
                    file_path = match.group(1)
                    if file_path not in files_examined:
                        files_examined.append(file_path)

        return {
            "exploration_summary": output[:500] if output else "",
            "files_examined": files_examined,
            "agent_type": "explore"
        }
