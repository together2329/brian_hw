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
Your role is to IMPLEMENT the plan by writing actual code, creating files, and running commands.

🎯 YOUR RESPONSIBILITY:
- You receive exploration info and a text plan from previous agents
- YOU are the ONLY agent that writes actual code
- Implement the specifications from the plan
- Run simulations and verify results

AVAILABLE TOOLS:
- read_file(path="...") - Read file
- write_file(path="...", content="...") - Write/create file with code
- replace_in_file(path="...", old_text="...", new_text="...") - Replace text
- run_command(command="...") - Execute shell command (compile, simulate)
- grep_file(pattern="...", path="...") - Search patterns
- find_files(pattern="...", directory=".") - Find files
- git_status() - Git status

WORKFLOW:
1. Review the plan/specification provided
2. Write the actual code (Verilog modules, testbenches, etc.)
3. Compile and run simulations
4. Verify results match expected behavior
5. Report success/failure with details"""

    def _get_execution_prompt(self) -> str:
        return """You are an Execution Agent. IMPLEMENT the plan using available tools.

🎯 YOU ARE THE CODE WRITER - Previous agents only gathered info and planned.
Now YOU must write the actual implementation.

FORMAT:
Thought: [what you need to implement based on the plan]
Action: tool_name(arg1="value1", arg2="value2")

After getting observation:
Thought: [analyze result and decide next step]
Action: [next action if needed]

When done:
Thought: [summary of what was implemented]
Result: [final outcome - files created, simulation results]

WORKFLOW:
1. write_file() - Create the actual code files
2. run_command("iverilog ...") - Compile
3. run_command("vvp ...") - Run simulation
4. Analyze output and report results

IMPORTANT:
- YOU must write the actual code - don't skip this step
- Always compile and run to verify
- Report simulation pass/fail status"""

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
