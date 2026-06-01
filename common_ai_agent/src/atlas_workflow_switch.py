from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import NamedTuple


class WorkflowCheckpointRequest(NamedTuple):
    ip_dir: Path
    previous_workflow: str
    next_workflow: str


class WorkflowCheckpointStatus(NamedTuple):
    scheduled: bool
    reason: str = ""


def schedule_workflow_checkpoint(request: WorkflowCheckpointRequest) -> WorkflowCheckpointStatus:
    if not request.previous_workflow or request.previous_workflow == "default":
        return WorkflowCheckpointStatus(False, "no_previous_workflow")
    if request.previous_workflow == request.next_workflow:
        return WorkflowCheckpointStatus(False, "workflow_unchanged")
    if not (request.ip_dir / ".git").is_dir():
        return WorkflowCheckpointStatus(False, "not_a_git_repo")
    try:
        threading.Thread(
            target=_commit_workflow_checkpoint,
            args=(request,),
            name=f"atlas-workflow-checkpoint:{request.ip_dir.name}",
            daemon=True,
        ).start()
    except RuntimeError as exc:
        return WorkflowCheckpointStatus(False, str(exc))
    return WorkflowCheckpointStatus(True, "scheduled")


def _commit_workflow_checkpoint(request: WorkflowCheckpointRequest) -> None:
    try:
        subprocess.run(
            ["git", "add", "--", "."],
            cwd=str(request.ip_dir),
            capture_output=True,
            timeout=10,
            check=False,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "--allow-empty",
                "-m",
                f"workflow: {request.previous_workflow} -> {request.next_workflow}",
            ],
            cwd=str(request.ip_dir),
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return
