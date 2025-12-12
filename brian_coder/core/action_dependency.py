"""
Action Dependency Analyzer for Parallel Execution

Claude Code 스타일의 병렬 실행을 위한 의존성 분석 시스템.
Actions를 분석하여 병렬 실행 가능한 batch로 분류합니다.
"""

from dataclasses import dataclass
from typing import List, Tuple, Set, Optional, Dict
import re


@dataclass
class FileAccess:
    """파일 접근 패턴을 표현하는 클래스"""
    access_type: str  # "read" or "write"
    file_path: Optional[str] = None  # 특정 파일 경로
    glob_pattern: Optional[str] = None  # glob 패턴 (예: "*.v")

    def conflicts_with(self, other: 'FileAccess') -> bool:
        """다른 FileAccess와 충돌하는지 확인 (write 간 충돌만)"""
        # 둘 다 write이고 같은 파일을 접근하면 충돌
        if self.access_type == "write" and other.access_type == "write":
            if self.file_path and other.file_path:
                return self.file_path == other.file_path
        return False


@dataclass
class ActionBatch:
    """병렬 실행 가능한 action들의 batch"""
    actions: List[Tuple[int, str, str]]  # (index, tool_name, args_str)
    parallel: bool  # True면 병렬 실행, False면 순차 실행
    reason: str = ""  # 분류 이유 (디버깅용)


class ActionDependencyAnalyzer:
    """
    Action 간 의존성 분석기

    Claude Code의 병렬 실행 전략 구현:
    1. Read-only tools → 병렬 실행
    2. Write tools → Barrier (순차 실행)
    3. 같은 파일 접근하는 Write → 순차 실행
    """

    # Read-only 도구들 (병렬 실행 가능)
    READ_ONLY_TOOLS = {
        # 기본 읽기 도구
        "read_file", "read_lines", "grep_file", "list_dir", "find_files",
        # Git 도구
        "git_status", "git_diff",
        # RAG 도구 (read-only)
        "rag_search", "rag_status",
        # Verilog 분석 도구 (read-only)
        "analyze_verilog_module", "find_signal_usage", "find_module_definition",
        "extract_module_hierarchy", "find_potential_issues", "analyze_timing_paths",
        # Meta 도구
        "spawn_explore",  # 여러 explore agent 병렬 실행 가능
    }

    # Write 도구들 (barrier 필요)
    WRITE_TOOLS = {
        "write_file", "replace_in_file", "replace_lines",
        "run_command",  # 외부 부작용 가능
        "rag_index", "rag_clear",  # RAG DB 수정
        "create_plan", "mark_step_done",  # Plan 파일 수정
    }

    def analyze(self, actions: List[Tuple[str, str]]) -> List[ActionBatch]:
        """
        Actions를 분석하여 병렬 실행 가능한 batch로 분리

        전략:
        1. Read-only actions를 batch에 추가
        2. Write action을 만나면 이전 batch flush + barrier 생성
        3. Write 후 다시 read-only batch 시작

        Args:
            actions: List of (tool_name, args_str)

        Returns:
            List[ActionBatch]: 각 batch는 병렬 또는 순차 실행
        """
        if not actions:
            return []

        batches = []
        current_batch = []

        for idx, (tool_name, args_str) in enumerate(actions):
            # Read-only 도구인지 확인
            is_read_only = tool_name in self.READ_ONLY_TOOLS

            if is_read_only:
                # Read-only는 현재 batch에 추가
                current_batch.append((idx, tool_name, args_str))
            else:
                # Write 도구: 이전 batch flush
                if current_batch:
                    batches.append(ActionBatch(
                        actions=current_batch,
                        parallel=True,
                        reason="Read-only batch"
                    ))
                    current_batch = []

                # Write 도구는 단독 batch (barrier)
                batches.append(ActionBatch(
                    actions=[(idx, tool_name, args_str)],
                    parallel=False,
                    reason=f"Write barrier ({tool_name})"
                ))

        # 마지막 batch flush
        if current_batch:
            batches.append(ActionBatch(
                actions=current_batch,
                parallel=True,
                reason="Final read-only batch"
            ))

        return batches

    def extract_file_access(self, tool_name: str, args_str: str) -> Optional[FileAccess]:
        """
        도구와 인자에서 접근하는 파일 추출

        Args:
            tool_name: 도구 이름
            args_str: 인자 문자열

        Returns:
            FileAccess 객체 또는 None
        """
        # 파일 경로 추출
        file_path = self._parse_path_from_args(args_str)

        # Access type 결정
        if tool_name in self.READ_ONLY_TOOLS:
            access_type = "read"
        elif tool_name in self.WRITE_TOOLS:
            access_type = "write"
        else:
            # 알 수 없는 도구는 write로 간주 (보수적)
            access_type = "write"

        # Glob 패턴 확인
        glob_pattern = None
        if file_path and ('*' in file_path or '?' in file_path):
            glob_pattern = file_path
            file_path = None

        return FileAccess(
            access_type=access_type,
            file_path=file_path,
            glob_pattern=glob_pattern
        )

    def _parse_path_from_args(self, args_str: str) -> Optional[str]:
        """
        인자 문자열에서 path 파라미터 추출

        지원 형식:
        - path="foo.v"
        - path='foo.v'
        - path=foo.v
        - "foo.v" (positional)

        Args:
            args_str: 인자 문자열

        Returns:
            파일 경로 또는 None
        """
        # Keyword argument: path="..."
        match = re.search(r'path\s*=\s*["\']([^"\']+)["\']', args_str)
        if match:
            return match.group(1)

        # Keyword argument: path=... (without quotes)
        match = re.search(r'path\s*=\s*([^\s,)]+)', args_str)
        if match:
            return match.group(1)

        # Positional argument (first quoted string)
        match = re.search(r'^["\']([^"\']+)["\']', args_str.strip())
        if match:
            return match.group(1)

        return None


class FileConflictDetector:
    """
    파일 충돌 감지기

    여러 Write action이 같은 파일을 수정하려 할 때 경고합니다.
    """

    def check_conflicts(
        self,
        actions: List[Tuple[int, str, str]],
        analyzer: ActionDependencyAnalyzer
    ) -> List[str]:
        """
        Action 간 파일 충돌 감지

        Args:
            actions: List of (index, tool_name, args_str)
            analyzer: ActionDependencyAnalyzer 인스턴스

        Returns:
            경고 메시지 리스트
        """
        warnings = []
        file_accesses: Dict[str, List[Tuple[int, str]]] = {}  # file_path -> [(index, tool_name)]

        for idx, tool_name, args_str in actions:
            access = analyzer.extract_file_access(tool_name, args_str)

            if access and access.access_type == "write" and access.file_path:
                file_path = access.file_path

                if file_path not in file_accesses:
                    file_accesses[file_path] = []

                file_accesses[file_path].append((idx, tool_name))

        # 같은 파일을 여러 write가 수정하는지 확인
        for file_path, accesses in file_accesses.items():
            if len(accesses) > 1:
                tools_str = ", ".join(f"{tool}(idx={idx})" for idx, tool in accesses)
                warnings.append(
                    f"⚠️  File conflict detected: '{file_path}' modified by multiple actions: {tools_str}. "
                    f"These will be executed sequentially to prevent conflicts."
                )

        return warnings


# ============================================================
# Utility Functions
# ============================================================

def analyze_and_warn_conflicts(actions: List[Tuple[str, str]]) -> List[ActionBatch]:
    """
    편의 함수: Action 분석 + 충돌 경고 출력

    Args:
        actions: List of (tool_name, args_str)

    Returns:
        List[ActionBatch]
    """
    analyzer = ActionDependencyAnalyzer()
    batches = analyzer.analyze(actions)

    # 충돌 감지
    detector = FileConflictDetector()
    all_indexed_actions = []
    for batch in batches:
        all_indexed_actions.extend(batch.actions)

    warnings = detector.check_conflicts(all_indexed_actions, analyzer)

    # 경고 출력
    for warning in warnings:
        print(warning)

    return batches
