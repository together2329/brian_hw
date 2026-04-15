"""
core/job.py — Job model with converge context fields

Wraps the existing AgentResult pattern from core/agent_runner.py with
converge-loop-specific fields. Each job corresponds to one sub-agent
execution within a converge loop iteration.

Compatibility:
  - to_dict() output includes all fields from existing result.json format
  - from_dict() can load both old (pre-converge) and new result.json files
  - Factory method from_agent_result() bridges from AgentResult to Job

Persistence: .session/<project>/jobs/job<N>/result.json
  (same file format as _persist_job_result(), with extra converge fields)
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ============================================================
# Job Lifecycle States
# ============================================================

class JobStatus:
    """Job lifecycle states — matches existing result.json 'status' values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

    @classmethod
    def is_terminal(cls, status: str) -> bool:
        return status in (cls.COMPLETED, cls.ERROR, cls.TIMEOUT, cls.CANCELLED)


# ============================================================
# Job Model
# ============================================================

@dataclass
class Job:
    """
    A single sub-agent execution within a converge loop.

    Extends the existing AgentResult + result.json pattern with:
      - stage_id: which pipeline stage this job belongs to
      - iteration_in_stage: retry count within this stage
      - loop_score: score at the time of this job
      - classification_label: bug classifier output (e.g., "tb_bug", "rtl_bug")
      - parsed_metrics: structured metrics extracted from output
        (e.g., {"lint.errors": 3, "sim.pass": 5})
      - retry_count: how many times this stage has been retried
      - converge_context: extra context from the converge engine
    """

    # ── Identity ──────────────────────────────
    job_id: str = ""                    # "job5", "job6", etc.
    agent_name: str = ""                # "execute", "explore", "review"
    workflow: str = ""                  # workspace name used

    # ── Lifecycle ─────────────────────────────
    status: str = JobStatus.PENDING
    created_at: float = 0.0            # time.time() when created
    started_at: float = 0.0
    finished_at: float = 0.0
    execution_time_ms: int = 0

    # ── Result (mirrors AgentResult) ──────────
    output: str = ""                    # compressed result text
    raw_output: str = ""                # uncompressed
    error: Optional[str] = None
    iterations: int = 0                # ReAct iterations used
    tool_calls: List[Dict[str, str]] = field(default_factory=list)
    files_examined: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    token_usage: Dict[str, int] = field(default_factory=dict)

    # ── Converge Context Fields ───────────────
    stage_id: str = ""                  # pipeline stage (e.g., "lint", "sim")
    iteration_in_stage: int = 0         # retry count within this stage
    loop_score: float = -999.0          # score at time of execution
    classification_label: str = ""      # classifier output (e.g., "tb_bug")
    retry_count: int = 0                # total retries for this stage so far
    converge_action: str = ""           # what action (e.g., "lint-fix", "tb-fix")
    parsed_metrics: Dict[str, Any] = field(default_factory=dict)
    converge_context: Dict[str, Any] = field(default_factory=dict)

    # ============================================================
    # Lifecycle Methods
    # ============================================================

    def start(self) -> None:
        """Mark job as running."""
        self.status = JobStatus.RUNNING
        self.started_at = time.time()

    def complete(self, output: str = "", raw_output: str = "",
                 error: Optional[str] = None) -> None:
        """Mark job as completed or errored."""
        self.output = output
        self.raw_output = raw_output
        self.error = error
        self.finished_at = time.time()
        self.execution_time_ms = int((self.finished_at - self.started_at) * 1000)
        self.status = JobStatus.ERROR if error else JobStatus.COMPLETED

    def cancel(self, reason: str = "") -> None:
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.error = reason
        self.finished_at = time.time()

    def is_terminal(self) -> bool:
        return JobStatus.is_terminal(self.status)

    # ============================================================
    # Result Capture
    # ============================================================

    def capture_metrics(self, metrics: Dict[str, Any]) -> None:
        """Merge parsed metrics into this job's metrics dict."""
        self.parsed_metrics.update(metrics)

    def set_classification(self, label: str) -> None:
        """Set the classification label from the bug classifier."""
        self.classification_label = label

    def set_score(self, score: float) -> None:
        """Record the loop score at the time of this job."""
        self.loop_score = score

    # ============================================================
    # Serialization
    # ============================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dict. Includes all existing result.json fields
        plus converge-specific fields (under 'converge' key for backward compat).
        """
        return {
            # Existing result.json format (compatible with _persist_job_result)
            "agent_name": self.agent_name,
            "status": self.status,
            "iterations": self.iterations,
            "execution_time_ms": self.execution_time_ms,
            "tool_calls": len(self.tool_calls),
            "files_examined": self.files_examined[:20],
            "files_modified": self.files_modified[:20],
            "output_preview": self.output[:2000] if self.output else "",
            "error": self.error,

            # Converge-specific fields
            "converge": {
                "job_id": self.job_id,
                "workflow": self.workflow,
                "stage_id": self.stage_id,
                "iteration_in_stage": self.iteration_in_stage,
                "loop_score": self.loop_score,
                "classification_label": self.classification_label,
                "retry_count": self.retry_count,
                "converge_action": self.converge_action,
                "parsed_metrics": dict(self.parsed_metrics),
                "converge_context": dict(self.converge_context),
            },

            # Timing
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        """
        Deserialize from dict. Handles both old format (pre-converge)
        and new format (with 'converge' key).
        """
        converge_data = data.get("converge", {})

        # Handle both old and new format for tool_calls
        raw_tool_calls = data.get("tool_calls", [])
        if isinstance(raw_tool_calls, int):
            # Old format: tool_calls was a count
            tool_calls = []
        else:
            tool_calls = raw_tool_calls

        return cls(
            job_id=converge_data.get("job_id", data.get("job_id", "")),
            agent_name=data.get("agent_name", ""),
            workflow=converge_data.get("workflow", ""),
            status=data.get("status", JobStatus.PENDING),
            created_at=float(data.get("created_at", 0)),
            started_at=float(data.get("started_at", 0)),
            finished_at=float(data.get("finished_at", 0)),
            execution_time_ms=int(data.get("execution_time_ms", 0)),
            output=data.get("output_preview", data.get("output", "")),
            raw_output=data.get("raw_output", ""),
            error=data.get("error"),
            iterations=int(data.get("iterations", 0)),
            tool_calls=tool_calls,
            files_examined=data.get("files_examined", []),
            files_modified=data.get("files_modified", []),
            token_usage=data.get("token_usage", {}),
            stage_id=converge_data.get("stage_id", ""),
            iteration_in_stage=int(converge_data.get("iteration_in_stage", 0)),
            loop_score=float(converge_data.get("loop_score", -999.0)),
            classification_label=converge_data.get("classification_label", ""),
            retry_count=int(converge_data.get("retry_count", 0)),
            converge_action=converge_data.get("converge_action", ""),
            parsed_metrics=converge_data.get("parsed_metrics", {}),
            converge_context=converge_data.get("converge_context", {}),
        )

    # ============================================================
    # Persistence
    # ============================================================

    def save(self, job_dir: Path) -> None:
        """Save job to result.json in the given directory."""
        job_dir.mkdir(parents=True, exist_ok=True)
        result_path = job_dir / "result.json"
        result_path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, job_dir: Path) -> Optional["Job"]:
        """Load job from result.json. Returns None if not found."""
        result_path = job_dir / "result.json"
        if not result_path.exists():
            return None
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    # ============================================================
    # Display
    # ============================================================

    def format_summary(self) -> str:
        """Format a one-line summary for REPL display."""
        status_icon = {
            JobStatus.COMPLETED: "+",
            JobStatus.ERROR: "X",
            JobStatus.RUNNING: "...",
            JobStatus.PENDING: "-",
            JobStatus.TIMEOUT: "T",
            JobStatus.CANCELLED: "C",
        }.get(self.status, "?")

        parts = [f"[{status_icon}] {self.job_id or '?'}"]
        if self.stage_id:
            parts.append(f"stage={self.stage_id}")
        if self.converge_action:
            parts.append(self.converge_action)
        parts.append(self.status)
        if self.execution_time_ms:
            parts.append(f"{self.execution_time_ms}ms")
        if self.loop_score > -999.0:
            parts.append(f"score={self.loop_score:.1f}")
        if self.classification_label:
            parts.append(f"cls={self.classification_label}")
        if self.parsed_metrics:
            metrics_str = ", ".join(f"{k}={v}" for k, v in sorted(self.parsed_metrics.items()))
            parts.append(f"({metrics_str})")

        return " ".join(parts)


# ============================================================
# Factory: Create Job from AgentResult
# ============================================================

def job_from_agent_result(
    result: Any,  # AgentResult from core.agent_runner
    job_id: str = "",
    stage_id: str = "",
    workflow: str = "",
    iteration_in_stage: int = 0,
    loop_score: float = -999.0,
    classification_label: str = "",
    converge_action: str = "",
    parsed_metrics: Optional[Dict[str, Any]] = None,
) -> Job:
    """
    Create a Job from an existing AgentResult, adding converge context.

    This bridges the existing agent_runner pattern with the converge loop.
    The converge engine calls this after each sub-agent execution to create
    a properly annotated Job for tracking.

    Args:
        result: AgentResult from run_agent_session()
        job_id: Job ID (e.g., "job5")
        stage_id: Pipeline stage that produced this job
        workflow: Workspace used
        iteration_in_stage: Retry count within stage
        loop_score: Score at time of execution
        classification_label: Bug classifier output
        converge_action: What action was performed
        parsed_metrics: Structured metrics from output

    Returns:
        Job with all fields populated
    """
    job = Job(
        job_id=job_id,
        agent_name=getattr(result, 'agent_name', 'execute'),
        workflow=workflow,
        status=getattr(result, 'status', JobStatus.COMPLETED),
        output=getattr(result, 'output', ''),
        raw_output=getattr(result, 'raw_output', ''),
        error=getattr(result, 'error'),
        iterations=getattr(result, 'iterations', 0),
        tool_calls=getattr(result, 'tool_calls', []),
        files_examined=getattr(result, 'files_examined', []),
        files_modified=getattr(result, 'files_modified', []),
        token_usage=getattr(result, 'token_usage', {}),
        execution_time_ms=getattr(result, 'execution_time_ms', 0),
        # Converge fields
        stage_id=stage_id,
        iteration_in_stage=iteration_in_stage,
        loop_score=loop_score,
        classification_label=classification_label,
        retry_count=iteration_in_stage,
        converge_action=converge_action,
        parsed_metrics=parsed_metrics or {},
    )
    job.created_at = time.time()
    job.started_at = job.created_at - (job.execution_time_ms / 1000.0)
    job.finished_at = job.created_at
    return job
