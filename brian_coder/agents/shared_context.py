"""
Shared Context for Agent Communication

Thread-safe shared memory for SubAgents to communicate
and share information in real-time.
"""

import os
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Debug mode for context flow monitoring
DEBUG_CONTEXT_FLOW = os.getenv('DEBUG_CONTEXT_FLOW', 'false').lower() in ('true', '1', 'yes')


@dataclass
class AgentMemory:
    """Individual agent's contribution to shared memory"""
    agent_name: str
    agent_type: str  # 'explore', 'plan', 'execute'
    timestamp: datetime
    files_examined: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    planned_steps: List[str] = field(default_factory=list)
    findings: str = ""
    execution_time_ms: int = 0
    tool_calls_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SharedContext:
    """
    Thread-safe shared memory for SubAgent communication.

    Features:
    - Real-time information sharing between agents
    - Thread-safe read/write operations
    - Agent execution history tracking
    - Automatic context summarization

    Usage:
        shared_ctx = SharedContext()

        # Agent writes
        shared_ctx.record_exploration(
            agent_name="explore_fifo",
            files_examined=["fifo.v"],
            findings="Found FIFO implementation"
        )

        # Agent reads
        files = shared_ctx.get_all_examined_files()
        summary = shared_ctx.get_summary()
    """

    def __init__(self):
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._memories: List[AgentMemory] = []
        self._files_examined: set = set()
        self._files_modified: set = set()
        self._planned_steps: List[str] = []
        self._exploration_findings: List[str] = []
        self._plan_summaries: List[str] = []

    # ============================================================
    # Write Operations (Thread-safe)
    # ============================================================

    def record_exploration(
        self,
        agent_name: str,
        files_examined: List[str] = None,
        findings: str = "",
        execution_time_ms: int = 0,
        tool_calls_count: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Record exploration results from ExploreAgent"""
        with self._lock:
            memory = AgentMemory(
                agent_name=agent_name,
                agent_type="explore",
                timestamp=datetime.now(),
                files_examined=files_examined or [],
                findings=findings,
                execution_time_ms=execution_time_ms,
                tool_calls_count=tool_calls_count,
                metadata=metadata or {}
            )

            self._memories.append(memory)

            # Update aggregated data
            if files_examined:
                self._files_examined.update(files_examined)
            if findings:
                self._exploration_findings.append(findings)

            # Debug logging
            if DEBUG_CONTEXT_FLOW:
                print(f"\n[🔍 CONTEXT] ExploreAgent '{agent_name}' updated context:")
                print(f"  📁 Files: {files_examined or []}")
                print(f"  🔎 Finding: {findings[:100]}..." if len(findings) > 100 else f"  🔎 Finding: {findings}")
                print(f"  ⏱️  Time: {execution_time_ms}ms | Tools: {tool_calls_count}")

    def record_planning(
        self,
        agent_name: str,
        planned_steps: List[str] = None,
        summary: str = "",
        execution_time_ms: int = 0,
        tool_calls_count: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Record planning results from PlanAgent"""
        with self._lock:
            memory = AgentMemory(
                agent_name=agent_name,
                agent_type="plan",
                timestamp=datetime.now(),
                planned_steps=planned_steps or [],
                findings=summary,
                execution_time_ms=execution_time_ms,
                tool_calls_count=tool_calls_count,
                metadata=metadata or {}
            )

            self._memories.append(memory)

            # Update aggregated data
            if planned_steps:
                self._planned_steps = planned_steps  # Replace with latest
            if summary:
                self._plan_summaries.append(summary)

            # Debug logging
            if DEBUG_CONTEXT_FLOW:
                print(f"\n[📋 CONTEXT] PlanAgent '{agent_name}' updated context:")
                print(f"  📝 Steps: {len(planned_steps or [])} step(s)")
                if planned_steps:
                    for i, step in enumerate(planned_steps[:3], 1):
                        print(f"     {i}. {step}")
                    if len(planned_steps) > 3:
                        print(f"     ... and {len(planned_steps) - 3} more")
                print(f"  ⏱️  Time: {execution_time_ms}ms | Tools: {tool_calls_count}")

    def record_execution(
        self,
        agent_name: str,
        files_modified: List[str] = None,
        execution_time_ms: int = 0,
        tool_calls_count: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Record execution results from ExecuteAgent"""
        with self._lock:
            memory = AgentMemory(
                agent_name=agent_name,
                agent_type="execute",
                timestamp=datetime.now(),
                files_modified=files_modified or [],
                execution_time_ms=execution_time_ms,
                tool_calls_count=tool_calls_count,
                metadata=metadata or {}
            )

            self._memories.append(memory)

            # Update aggregated data
            if files_modified:
                self._files_modified.update(files_modified)

            # Debug logging
            if DEBUG_CONTEXT_FLOW:
                print(f"\n[✏️  CONTEXT] ExecuteAgent '{agent_name}' updated context:")
                print(f"  📝 Modified: {files_modified or []}")
                print(f"  ⏱️  Time: {execution_time_ms}ms | Tools: {tool_calls_count}")

    def update_from_result(self, agent_name: str, result):
        """
        Automatically update SharedContext from SubAgentResult.

        Args:
            agent_name: Name of the agent
            result: SubAgentResult object
        """
        with self._lock:
            context_updates = result.context_updates
            agent_type = context_updates.get("agent_type", "unknown")

            if agent_type == "explore":
                self.record_exploration(
                    agent_name=agent_name,
                    files_examined=context_updates.get("files_examined", []),
                    findings=context_updates.get("exploration_summary", ""),
                    execution_time_ms=result.execution_time_ms,
                    tool_calls_count=len(result.tool_calls),
                    metadata=result.artifacts
                )
            elif agent_type == "plan":
                self.record_planning(
                    agent_name=agent_name,
                    planned_steps=context_updates.get("planned_steps", []),
                    summary=context_updates.get("plan_summary", ""),
                    execution_time_ms=result.execution_time_ms,
                    tool_calls_count=len(result.tool_calls),
                    metadata=result.artifacts
                )
            elif agent_type == "execute":
                # ExecuteAgent would record file modifications
                self.record_execution(
                    agent_name=agent_name,
                    files_modified=context_updates.get("files_modified", []),
                    execution_time_ms=result.execution_time_ms,
                    tool_calls_count=len(result.tool_calls),
                    metadata=result.artifacts
                )

    # ============================================================
    # Read Operations (Thread-safe)
    # ============================================================

    def get_all_examined_files(self) -> List[str]:
        """Get all files examined across all agents"""
        with self._lock:
            return sorted(list(self._files_examined))

    def get_all_modified_files(self) -> List[str]:
        """Get all files modified across all agents"""
        with self._lock:
            return sorted(list(self._files_modified))

    def get_planned_steps(self) -> List[str]:
        """Get current planned steps (from latest PlanAgent)"""
        with self._lock:
            return self._planned_steps.copy()

    def get_exploration_findings(self) -> List[str]:
        """Get all exploration findings"""
        with self._lock:
            return self._exploration_findings.copy()

    def get_plan_summaries(self) -> List[str]:
        """Get all plan summaries"""
        with self._lock:
            return self._plan_summaries.copy()

    def get_agent_history(self, agent_type: Optional[str] = None) -> List[AgentMemory]:
        """
        Get execution history for specific agent type or all agents.

        Args:
            agent_type: Filter by 'explore', 'plan', 'execute', or None for all
        """
        with self._lock:
            if agent_type:
                return [m for m in self._memories if m.agent_type == agent_type]
            return self._memories.copy()

    def get_summary(self, include_history: bool = False) -> str:
        """
        Generate human-readable summary of shared context.

        Args:
            include_history: Include agent execution history

        Returns:
            Formatted summary string
        """
        with self._lock:
            lines = []

            # Files examined
            if self._files_examined:
                lines.append(f"📁 Files Examined: {len(self._files_examined)} file(s)")
                for f in sorted(self._files_examined)[:10]:
                    lines.append(f"   • {f}")
                if len(self._files_examined) > 10:
                    lines.append(f"   ... and {len(self._files_examined) - 10} more")

            # Planned steps
            if self._planned_steps:
                lines.append(f"\n📋 Planned Steps: {len(self._planned_steps)} step(s)")
                for idx, step in enumerate(self._planned_steps[:5], 1):
                    lines.append(f"   {idx}. {step}")
                if len(self._planned_steps) > 5:
                    lines.append(f"   ... and {len(self._planned_steps) - 5} more")

            # Exploration findings
            if self._exploration_findings:
                lines.append(f"\n🔍 Exploration Insights: {len(self._exploration_findings)} finding(s)")
                for finding in self._exploration_findings[-3:]:  # Last 3
                    preview = finding[:100] + "..." if len(finding) > 100 else finding
                    lines.append(f"   • {preview}")

            # Files modified
            if self._files_modified:
                lines.append(f"\n✏️  Files Modified: {len(self._files_modified)} file(s)")
                for f in sorted(self._files_modified)[:10]:
                    lines.append(f"   • {f}")

            # Agent execution history
            if include_history and self._memories:
                lines.append(f"\n📊 Agent Execution History: {len(self._memories)} agent(s)")
                for memory in self._memories[-5:]:  # Last 5
                    time_str = memory.timestamp.strftime("%H:%M:%S")
                    lines.append(
                        f"   [{time_str}] {memory.agent_name} ({memory.agent_type}) "
                        f"- {memory.execution_time_ms}ms, {memory.tool_calls_count} tools"
                    )

            return "\n".join(lines) if lines else "No shared context data yet."

    def get_context_for_llm(self) -> str:
        """
        Get formatted context suitable for LLM injection.

        Returns:
            Formatted context string for system message
        """
        with self._lock:
            lines = ["[Shared Agent Memory]"]

            if self._files_examined:
                files = sorted(self._files_examined)
                lines.append(f"📁 Files examined by agents: {len(files)} file(s)")
                if len(files) <= 10:
                    lines.append(f"   {', '.join(files)}")
                else:
                    lines.append(f"   {', '.join(files[:10])}, ... and {len(files) - 10} more")

            if self._planned_steps:
                steps = self._planned_steps
                lines.append(f"📋 Planned steps: {len(steps)} step(s)")
                for idx, step in enumerate(steps[:5], 1):
                    lines.append(f"   {idx}. {step}")
                if len(steps) > 5:
                    lines.append(f"   ... and {len(steps) - 5} more")

            if self._exploration_findings:
                lines.append(f"🔍 Key findings: {len(self._exploration_findings)} insight(s)")

            if self._files_modified:
                files = sorted(self._files_modified)
                lines.append(f"✏️  Files modified: {len(files)} file(s)")
                if len(files) <= 5:
                    lines.append(f"   {', '.join(files)}")

            return "\n".join(lines)

    def clear(self):
        """Clear all shared context (useful for testing)"""
        with self._lock:
            self._memories.clear()
            self._files_examined.clear()
            self._files_modified.clear()
            self._planned_steps.clear()
            self._exploration_findings.clear()
            self._plan_summaries.clear()

    def __repr__(self):
        with self._lock:
            return (
                f"SharedContext("
                f"files_examined={len(self._files_examined)}, "
                f"planned_steps={len(self._planned_steps)}, "
                f"memories={len(self._memories)})"
            )
