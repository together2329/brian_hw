"""
Iteration Control for Common AI Agent ReAct Loop

Provides:
- Progress tracking (tool usage patterns)
- Explicit completion signal detection
- Progressive warnings (90%, 100%)
- Dynamic iteration extension

Zero-dependency (stdlib only).
"""
import re
from typing import Dict, List, Tuple


class IterationTracker:
    """
    Tracks ReAct loop progress and provides early termination signals.

    Monitors:
    - Tool usage patterns (read/write/execute ratio)
    - Consecutive read operations (stall detection)
    - Overall progress metrics
    """

    def __init__(self, max_iterations: int = 100):
        """
        Initialize iteration tracker.

        Args:
            max_iterations: Maximum number of iterations allowed
        """
        self.max_iterations = max_iterations
        self.current = 0
        self.tool_history: List[Tuple[int, str]] = []  # [(iteration, tool_name), ...]
        self.consecutive_reads = 0

        # Tool categories
        self.read_tools = {'read_file', 'read_lines', 'grep_file', 'list_dir',
                           'find_files', 'git_diff', 'git_status'}
        self.write_tools = {'write_file', 'replace_in_file', 'replace_lines'}
        self.exec_tools = {'run_command'}
        self.plan_tools = set()  # Plan system removed

    def record_tool(self, tool_name: str):
        """
        Records tool usage and updates metrics.

        Args:
            tool_name: Name of tool executed
        """
        self.tool_history.append((self.current, tool_name))

        # Track consecutive reads
        if tool_name in self.read_tools:
            self.consecutive_reads += 1
        else:
            self.consecutive_reads = 0

    def increment(self):
        """Increments iteration counter"""
        self.current += 1

    def extend(self, amount: int = 20):
        """
        Extends maximum iterations.

        Args:
            amount: Number of iterations to add
        """
        self.max_iterations += amount

    def get_progress_pct(self) -> int:
        """
        Returns progress percentage (0-100).

        Returns:
            Progress percentage
        """
        return int((self.current / self.max_iterations) * 100)

    def is_stalled(self, threshold: int = 5) -> bool:
        """
        Detects if agent is stalled (excessive consecutive reads).

        Args:
            threshold: Number of consecutive reads to consider stalled

        Returns:
            True if stalled
        """
        return self.consecutive_reads >= threshold

    def should_warn(self) -> bool:
        """
        Returns True if should show warning (at 90% threshold).

        Returns:
            True if at 90% mark
        """
        return self.current == int(self.max_iterations * 0.9)

    def is_limit_reached(self) -> bool:
        """
        Returns True if hard limit reached.

        Returns:
            True if at or over limit
        """
        return self.current >= self.max_iterations

    def get_tool_stats(self) -> Dict[str, int]:
        """
        Returns tool usage statistics.

        Returns:
            Dict with counts by category
        """
        read_count = sum(1 for _, t in self.tool_history if t in self.read_tools)
        write_count = sum(1 for _, t in self.tool_history if t in self.write_tools)
        exec_count = sum(1 for _, t in self.tool_history if t in self.exec_tools)
        plan_count = sum(1 for _, t in self.tool_history if t in self.plan_tools)

        return {
            'read': read_count,
            'write': write_count,
            'exec': exec_count,
            'plan': plan_count,
            'total': len(self.tool_history)
        }

    def get_activity_summary(self) -> str:
        """
        Returns human-readable activity summary.

        Returns:
            Summary string
        """
        stats = self.get_tool_stats()
        total = stats['total']

        if total == 0:
            return "No tools used yet"

        summary = f"Tools used: {total} ({stats['read']} reads, {stats['write']} writes, {stats['exec']} executions"

        if stats['plan'] > 0:
            summary += f", {stats['plan']} planning"

        summary += ")"

        return summary


def detect_completion_signal(content: str) -> bool:
    """
    Detects explicit completion signals in agent's response.

    Only matches strict sentinel tokens or unambiguous narrative-end phrases.
    Casual conversation about completion (e.g. discussing what a "done" todo
    means) must not trigger the loop exit, so all narrative phrases require
    sentence-boundary anchors and an explicit "pipeline/workflow/run/loop"
    subject. Korean "완료" alone does NOT trigger completion.

    Args:
        content: Agent's response text

    Returns:
        True if task appears complete
    """
    completion_sentinels = [
        r'\[COMPLETED\]',
        r'\[TASK_DONE\]',
        r'\[DONE\]',
        r'===\s*TASK\s+COMPLETED\s*===',
        r'===\s*COMPLETED\s*===',
        r'===\s*DONE\s*===',
        # Worker/coordinator prompts require this exact terminal marker.
        # Treat only a line-start marker as completion so incidental prose
        # such as "include Final Answer later" does not stop the loop.
        r'(?im)^\s*Final Answer\s*:',
        r'"status"\s*:\s*"completed"',
        r'"status"\s*:\s*"done"',
    ]

    for pattern in completion_sentinels:
        if re.search(pattern, content):
            return True

    # Narrative-end phrases observed in real pipeline runs that should also
    # exit the loop. Each pattern requires a clear subject so chat-style usage
    # ("I'm done reading the file") does not match.
    narrative_completion = [
        r'(?i)\b(?:pipeline|workflow|run|loop|task)\s+(?:is\s+)?(?:complete|completed|finished|done)\b',
        r'(?i)\ball\s+(?:tasks|todos|steps|stages|workflows|tests)\s+(?:are\s+)?(?:complete|completed|finished|passed|approved|done)\b',
        r'(?i)\beverything\s+(?:is\s+)?(?:complete|completed|finished|done)\b',
        r'(?i)\bnothing\s+(?:more\s+)?(?:left|remaining)?\s*to\s+do\b',
        r'(?i)^\s*✓\s+(?:loop\s+ended|done|complete|completed|finished)\b',
    ]
    for pattern in narrative_completion:
        if re.search(pattern, content):
            return True

    return False


def show_iteration_warning(tracker: IterationTracker, mode: str = 'interactive') -> str:
    """
    Shows warning when approaching or reaching iteration limit.

    Args:
        tracker: IterationTracker instance
        mode: 'interactive' or 'oneshot'

    Returns:
        Action to take: 'continue' | 'stop' | 'extend'
    """
    from main import Color  # Import here to avoid circular dependency

    progress_pct = tracker.get_progress_pct()
    stats = tracker.get_tool_stats()

    if tracker.should_warn():
        # 90% warning
        print(Color.warning(f"\n[System] ⚠️  Approaching iteration limit ({tracker.current}/{tracker.max_iterations})"))
        print(Color.info(f"  {tracker.get_activity_summary()}"))
        print(Color.info("  Please wrap up the task or request more iterations.\n"))
        return 'continue'

    elif tracker.is_limit_reached():
        # 100% limit reached
        print(Color.error(f"\n[System] ❌ Maximum iterations reached ({tracker.current}/{tracker.max_iterations})"))
        print(Color.info(f"  {tracker.get_activity_summary()}"))

        if mode == 'interactive':
            print(Color.warning("  Task appears incomplete."))
            try:
                response = input(Color.user("  Continue with 20 more iterations? (y/n): ")).strip().lower()
                if response in ['y', 'yes']:
                    print(Color.success("  Extended iteration limit by 20.\n"))
                    return 'extend'
                else:
                    print(Color.info("  Stopping as requested.\n"))
                    return 'stop'
            except (EOFError, KeyboardInterrupt):
                print(Color.info("\n  Stopping.\n"))
                return 'stop'
        else:
            # One-shot mode: just stop
            print(Color.warning("  Stopping (one-shot mode).\n"))
            return 'stop'

    return 'continue'


# Convenience function
def create_tracker(max_iterations: int = 100) -> IterationTracker:
    """
    Create iteration tracker instance.

    Args:
        max_iterations: Maximum iterations

    Returns:
        IterationTracker instance
    """
    return IterationTracker(max_iterations=max_iterations)
