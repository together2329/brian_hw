"""
ExecuteAgent - 실행 에이전트

모든 도구를 사용하여 실제 작업을 수행합니다.
"""

from typing import Dict, Any, Set

from .base import SubAgent


class ExecuteAgent(SubAgent):
    """
    실행 에이전트

    - 모든 도구 사용 가능
    - 실제 코드 작성, 파일 수정, 명령 실행
    - 결과: actions_taken, files_modified, success/fail
    """

    # 모든 도구 허용
    ALLOWED_TOOLS: Set[str] = {
        # 파일 읽기
        'read_file',
        'read_lines',
        'grep_file',
        'list_dir',
        'find_files',
        # 파일 쓰기
        'write_file',
        'replace_in_file',
        'replace_lines',
        # 명령 실행
        'run_command',
        # Git
        'git_status',
        'git_diff',
        # RAG
        'rag_search',
        'rag_index',
        'rag_status',
        'rag_clear',
        # Verilog
        'analyze_verilog_module',
        'find_signal_usage',
        'find_module_definition',
        'extract_module_hierarchy',
        'generate_module_testbench',
        'find_potential_issues',
        'analyze_timing_paths',
        'generate_module_docs',
        'suggest_optimizations'
    }

    def _get_planning_prompt(self) -> str:
        return """You are an Execution Agent for a coding assistant.
Your role is to execute tasks by writing code, modifying files, and running commands.

AVAILABLE TOOLS:
- read_file(path="...") - Read file
- write_file(path="...", content="...") - Write file
- replace_in_file(path="...", old_text="...", new_text="...") - Replace text
- run_command(command="...") - Execute shell command
- grep_file(pattern="...", path="...") - Search patterns
- find_files(pattern="...", directory=".") - Find files
- git_status() - Git status
- git_diff(path=None) - Git diff

GUIDELINES:
1. Read files before modifying them
2. Use replace_in_file for small changes
3. Use write_file for new files or complete rewrites
4. Verify changes after making them
5. Handle errors gracefully"""

    def _get_execution_prompt(self) -> str:
        return """You are an Execution Agent. Execute the task using available tools.

FORMAT:
Thought: [what you need to do]
Action: tool_name(arg1="value1", arg2="value2")

After getting observation:
Thought: [analyze result and decide next step]
Action: [next action if needed]

When done:
Thought: [summary of what was done]
Result: [final outcome]

IMPORTANT:
- Always read files before modifying
- Verify your changes work
- Report any errors encountered
- Be precise with file paths"""

    def _collect_artifacts(self) -> Dict[str, Any]:
        """실행 결과 산출물"""
        return {
            "files_read": self._files_read.copy(),
            "files_modified": self._files_modified.copy(),
            "commands_executed": [
                tc for tc in self._tool_calls if tc.get("tool") == "run_command"
            ],
            "tool_calls_count": len(self._tool_calls)
        }

    def _collect_context_updates(self, output: str) -> Dict[str, Any]:
        """메인 컨텍스트에 반영할 정보"""
        return {
            "execution_summary": output[:500] if output else "",
            "files_modified": self._files_modified.copy(),
            "agent_type": "execute"
        }
