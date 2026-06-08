"""Shared TODO status transition rules.

This module intentionally contains only tracker state-machine policy. UI,
LLM-tool prose, git checkpoints, and websocket/http transport stay in their
callers so Textual, Atlas web, and worker tools can share the same gates
without sharing side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
import sys
from typing import Any

from lib.todo_tracker import STATUS_ALIASES


VALID_TODO_STATUSES = ("pending", "in_progress", "completed", "approved", "rejected")


@dataclass
class TodoTransitionResult:
    ok: bool
    message: str = ""
    status: str = ""
    code: str = ""
    http_status: int = 200
    changed: bool = False


def normalize_todo_status(status: Any) -> str:
    raw = str(status or "").strip()
    return STATUS_ALIASES.get(raw, raw)


def _consume_pending_completion_credit(todo_tracker: Any, idx: int, item: Any) -> int:
    tools_since_start = int(getattr(item, "tools_since_in_progress", 0) or 0)
    if tools_since_start:
        return tools_since_start

    pending_credit = int(getattr(todo_tracker, "_pending_tool_credit", 0) or 0)
    current_idx = int(getattr(todo_tracker, "current_index", -1) or -1)
    if pending_credit > 0 and (
        current_idx == idx or getattr(item, "status", "") in ("pending", "rejected")
    ):
        item.tools_since_in_progress = pending_credit
        todo_tracker._pending_tool_credit = 0
        try:
            todo_tracker.save()
        except Exception:
            pass
        return pending_credit
    return 0


def _strict_deliverable_error(item: Any) -> str:
    scan_text = " ".join([
        str(getattr(item, "content", "") or ""),
        str(getattr(item, "criteria", "") or ""),
        str(getattr(item, "detail", "") or ""),
    ])
    path_re = re.compile(
        r"(?<![/\w.-])"
        r"((?:[\w.-]+/)+[\w.-]+\."
        r"(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|lib|lef|gds|spef|sdf|vcd|out|netlist))"
        r"(?![\w/.-])"
    )
    candidates = {p for p in path_re.findall(scan_text) if "<" not in p and ">" not in p}
    if not candidates:
        return ""

    cwd = os.getcwd()
    known_artifact_dirs = {
        "rtl", "list", "tb", "tc", "sim", "cov", "lint", "doc",
        "req", "model", "verify", "yaml", "syn", "sta", "pnr", "scripts",
    }
    base_dirs = [cwd]
    main_mod = sys.modules.get("main")
    ip_resolver = getattr(main_mod, "_get_active_ip_str", None) if main_mod else None
    active_ip = (ip_resolver() if ip_resolver else os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
    if active_ip and re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", active_ip):
        ip_base = os.path.join(cwd, active_ip)
        if os.path.isdir(ip_base):
            base_dirs.append(ip_base)
    for rel in candidates:
        parts = [part for part in rel.split("/") if part]
        for part_idx, part in enumerate(parts):
            if part in known_artifact_dirs and part_idx > 0:
                base = os.path.join(cwd, *parts[:part_idx])
                if base not in base_dirs:
                    base_dirs.append(base)
                break

    def resolve_existing(rel: str) -> str | None:
        tries = [rel] if os.path.isabs(rel) else [os.path.join(cwd, rel)]
        if not os.path.isabs(rel):
            tries.extend(os.path.join(base, rel) for base in base_dirs)
        for full in tries:
            if os.path.isfile(full):
                return full
        if os.path.isabs(rel):
            return None
        skip = {".git", ".session", ".rag", ".venv", "__pycache__", ".sisyphus", ".omc", "node_modules", "build"}
        hits = []
        try:
            for name in os.listdir(cwd):
                if name.startswith(".") or name in skip:
                    continue
                sub = os.path.join(cwd, name)
                if not os.path.isdir(sub):
                    continue
                candidate = os.path.join(sub, rel)
                if os.path.isfile(candidate):
                    hits.append(candidate)
        except OSError:
            return None
        return hits[0] if len(hits) == 1 else None

    def filelist_entries_exist(full: str) -> bool:
        root = os.path.dirname(os.path.dirname(full))
        try:
            lines = open(full, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            return False
        entries = []
        for raw in lines:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(("+incdir+", "-I", "-y", "+define+")):
                continue
            entries.append(line)
        if not entries:
            return False
        for entry in entries:
            if not re.search(r"\.(?:sv|v|vh|svh)$", entry):
                continue
            tries = [
                entry if os.path.isabs(entry) else os.path.join(root, entry),
                entry if os.path.isabs(entry) else os.path.join(cwd, entry),
            ]
            if not any(os.path.isfile(candidate) for candidate in tries):
                return False
        return True

    def artifact_is_real(full: str) -> bool:
        try:
            size = os.path.getsize(full)
        except OSError:
            return False
        ext = os.path.splitext(full)[1].lower()
        if ext == ".f":
            return filelist_entries_exist(full)
        if ext in {".sdc", ".upf", ".tcl"}:
            return size > 0
        return size >= 50

    missing = []
    for rel in candidates:
        resolved = resolve_existing(rel)
        if resolved is None or not artifact_is_real(resolved):
            missing.append(rel)
    if not missing:
        return ""
    return (
        "Approval blocked: declared deliverable(s) missing or too small on disk:\n"
        + "\n".join(f"  - {p}" for p in missing[:8])
        + (f"\n  - ... (+{len(missing) - 8} more)" if len(missing) > 8 else "")
        + "\nThe task content references these files but no write/run output produced real artifacts."
    )


def validate_todo_status_transition(
    todo_tracker: Any,
    idx: int,
    status: Any,
    *,
    reason: str = "",
    plan_mode: bool = False,
    cursor_mode: bool = False,
    strict_approval: bool | None = None,
    strict_deliverable_check: bool | None = None,
) -> TodoTransitionResult:
    """Validate a TODO status transition and consume shared gate counters."""

    status = normalize_todo_status(status)
    display_idx = idx + 1
    if status not in VALID_TODO_STATUSES:
        return TodoTransitionResult(
            False,
            f"Error: status must be one of {list(VALID_TODO_STATUSES)} (got '{status}')",
            status,
            "invalid_status",
            400,
        )
    if not getattr(todo_tracker, "todos", None):
        return TodoTransitionResult(False, "Error: No active todo list.", status, "no_todos", 400)
    if not (0 <= idx < len(todo_tracker.todos)):
        return TodoTransitionResult(
            False,
            f"Error: index {display_idx} out of range (1-{len(todo_tracker.todos)})",
            status,
            "index_out_of_range",
            400,
        )

    item = todo_tracker.todos[idx]
    if plan_mode and status != getattr(item, "status", None):
        return TodoTransitionResult(
            False,
            "Error: Changing status is blocked in plan mode. You can update content, detail, criteria, or priority.",
            status,
            "plan_mode_status_blocked",
            409,
        )

    if not cursor_mode and status in ("in_progress", "completed", "approved"):
        blocking = [
            i + 1 for i in range(idx)
            if todo_tracker.todos[i].status not in ("approved",)
            and not (
                todo_tracker.todos[i].status == "rejected"
                and getattr(todo_tracker.todos[i], "on_reject", 0) > (i + 1)
            )
        ]
        if blocking:
            first_blocking_idx = blocking[0] - 1
            if getattr(todo_tracker, "current_index", -1) != first_blocking_idx:
                todo_tracker.current_index = first_blocking_idx
                try:
                    todo_tracker.save()
                except Exception:
                    pass
            blocking_str = ", ".join(str(b) for b in blocking)
            return TodoTransitionResult(
                False,
                (
                    f"Error: Cannot update Task {display_idx} - "
                    f"Task(s) {blocking_str} must be approved first.\n"
                    f"Tasks must be completed in order. Finish Task {blocking[0]} before moving to Task {display_idx}."
                ),
                status,
                "prior_tasks_not_approved",
                409,
            )

    if item.status == "approved" and status in ("completed", "in_progress"):
        return TodoTransitionResult(
            False,
            (
                f"Status Conflict: Task {display_idx} is already 'approved' (fully complete).\n"
                "If you intended to update a DIFFERENT task, please check the 1-based index in the todo list.\n"
                "If you truly need to re-work this task, use status='rejected' with a specific reason."
            ),
            status,
            "approved_downgrade_blocked",
            409,
        )

    if item.status == "completed" and status == "in_progress":
        return TodoTransitionResult(
            False,
            (
                f"Status Conflict: Task {display_idx} is already 'completed' and awaiting review.\n"
                f"-> Approve: todo_update(index={display_idx}, status='approved', reason='<evidence>')\n"
                f"-> Reject:  todo_update(index={display_idx}, status='rejected', reason='<problem>')\n"
                "Do NOT reset to 'in_progress' without going through review."
            ),
            status,
            "completed_reset_blocked",
            409,
        )

    if status == "approved":
        if item.status not in ("completed", "approved"):
            return TodoTransitionResult(
                False,
                (
                    f"Error: Task {display_idx} is currently '{item.status}'. "
                    f"You must call todo_update(index={display_idx}, status='completed') first, "
                    f"then review, then call todo_update(index={display_idx}, status='approved')."
                ),
                status,
                "approval_requires_completed",
                409,
            )
        reason_stripped = (reason or "").strip()
        if not reason_stripped:
            return TodoTransitionResult(
                False,
                (
                    f"Error: You MUST provide a concrete 'reason' when approving Task {display_idx}.\n"
                    "Describe what you actually verified - e.g. 'read output.md: contains all sections, matches spec' "
                    "or 'ran pytest tests/foo.py - 14 passed, 0 failed'.\n"
                    f"-> todo_update(index={display_idx}, status='approved', reason='<specific evidence>')"
                ),
                status,
                "approval_reason_required",
                400,
            )

        if strict_approval is None:
            strict_approval = os.environ.get("STRICT_TODO_APPROVAL", "").lower() in ("1", "true", "yes", "on")
        if strict_approval:
            evidence = int(getattr(item, "tools_since_completed", 0) or 0)
            rej_count = int(getattr(item, "rejection_count", 0) or 0)
            required = 2 if rej_count >= 2 else 1
            if item.status == "completed" and evidence < required:
                esc = (
                    f"\nEscalated requirement: this task has been rejected "
                    f"{rej_count} times - needs >={required} verification calls."
                ) if rej_count >= 2 else ""
                return TodoTransitionResult(
                    False,
                    (
                        f"Approval blocked: Task {display_idx} has only {evidence} verification tool call(s) "
                        f"since review started (need >={required}).{esc}\n"
                        "Self-written summary/report files are NOT trustworthy evidence. Verify against ground-truth artifacts."
                    ),
                    status,
                    "approval_evidence_required",
                    409,
                )
            if len(reason_stripped) < 15:
                return TodoTransitionResult(
                    False,
                    (
                        f"Error: You MUST provide a concrete 'reason' (>=15 chars) when approving Task {display_idx}.\n"
                        "Describe what you actually verified."
                    ),
                    status,
                    "approval_reason_too_short",
                    400,
                )
            if reason_stripped.lower() in {
                "ok", "okay", "done", "good", "fine", "lgtm", "approved",
                "looks good", "all good", "seems ok", "seems good",
                "no issues", "no problems", "complete", "completed",
            }:
                return TodoTransitionResult(
                    False,
                    f"Error: '{reason}' is not concrete evidence for Task {display_idx}.",
                    status,
                    "approval_reason_not_evidence",
                    400,
                )

        if strict_deliverable_check is None:
            strict_deliverable_check = os.environ.get("STRICT_DELIVERABLE_CHECK", "").lower() in ("1", "true", "yes", "on")
        if strict_deliverable_check:
            missing_error = _strict_deliverable_error(item)
            if missing_error:
                return TodoTransitionResult(False, missing_error, status, "approval_missing_deliverable", 409)

    elif status == "completed":
        tools_since_start = _consume_pending_completion_credit(todo_tracker, idx, item)
        if tools_since_start == 0:
            return TodoTransitionResult(
                False,
                (
                    f"Completion blocked: Task {display_idx} cannot be marked completed because no tools were called since starting this task.\n"
                    "Produce a deliverable first (write a file, run a command, read evidence, etc.).\n"
                    "-> Call a tool NOW (write_file, run_command, read_file, etc.)\n"
                    f"-> Then call todo_update(index={display_idx}, status='completed') again."
                ),
                status,
                "completion_requires_tool",
                409,
            )

    elif status == "rejected":
        reason_stripped = (reason or "").strip()
        reason_lower = reason_stripped.lower()
        tracker_block_markers = (
            "no tools were called since starting this task",
            "completion blocked",
            "todo engine refuses completion",
            "todo tracker",
        )
        if item.status != "completed" and any(marker in reason_lower for marker in tracker_block_markers):
            _consume_pending_completion_credit(todo_tracker, idx, item)
            return TodoTransitionResult(
                False,
                (
                    f"Rejection blocked: Task {display_idx} was not rejected because this reason describes "
                    "TodoTracker bookkeeping, not a failed task deliverable.\n"
                    "Retry the valid completion transition now:\n"
                    f"-> todo_update(index={display_idx}, status='completed')\n"
                    "If the actual task output is wrong, reject only after reading/running ground-truth evidence "
                    "and state the concrete unmet criterion."
                ),
                status,
                "tracker_bookkeeping_reject_blocked",
                409,
            )

        evidence = int(getattr(item, "tools_since_completed", 0) or 0)
        rej_count = int(getattr(item, "rejection_count", 0) or 0)
        required = 2 if rej_count >= 2 else 1
        if item.status == "completed" and evidence < required:
            esc = (
                f"\nEscalated requirement: this task has been rejected "
                f"{rej_count} times - needs >={required} verification calls before another reject."
            ) if rej_count >= 2 else ""
            return TodoTransitionResult(
                False,
                (
                    f"Rejection blocked: Task {display_idx} has only {evidence} verification tool call(s) "
                    f"since review started (need >={required}).{esc}\n"
                    "Verify against ground truth before rejecting."
                ),
                status,
                "rejection_evidence_required",
                409,
            )
        if not reason_stripped:
            return TodoTransitionResult(
                False,
                (
                    f"Error: 'reason' is REQUIRED when rejecting Task {display_idx}.\n"
                    "You cannot reject without explaining what failed."
                ),
                status,
                "rejection_reason_required",
                400,
            )
        if len(reason_stripped) < 15:
            return TodoTransitionResult(
                False,
                f"Error: Rejection reason too vague for Task {display_idx} (got: '{reason_stripped}').",
                status,
                "rejection_reason_too_short",
                400,
            )
        if reason_stripped.lower() in {
            "bad", "wrong", "fail", "failed", "error", "broken",
            "no", "nope", "not ok", "not good", "not done", "incomplete",
        }:
            return TodoTransitionResult(
                False,
                f"Error: '{reason}' is not a useful rejection reason for Task {display_idx}.",
                status,
                "rejection_reason_not_actionable",
                400,
            )

    return TodoTransitionResult(True, status=status)


def apply_todo_status_transition(
    todo_tracker: Any,
    idx: int,
    status: Any,
    *,
    reason: str = "",
    plan_mode: bool = False,
    cursor_mode: bool = False,
    strict_approval: bool | None = None,
    strict_deliverable_check: bool | None = None,
    tool_output: str = "",
) -> TodoTransitionResult:
    """Validate and apply a TODO status transition through shared rules."""

    result = validate_todo_status_transition(
        todo_tracker,
        idx,
        status,
        reason=reason,
        plan_mode=plan_mode,
        cursor_mode=cursor_mode,
        strict_approval=strict_approval,
        strict_deliverable_check=strict_deliverable_check,
    )
    if not result.ok:
        return result

    status = result.status
    item = todo_tracker.todos[idx]
    before = getattr(item, "status", "")
    if status == "in_progress":
        todo_tracker.mark_in_progress(idx)
    elif status == "completed":
        item.rejection_reason = ""
        item.tools_since_in_progress = 0
        item.tools_since_completed = 0
        completed = todo_tracker.mark_completed(idx, tool_output=tool_output)
        if not completed:
            return TodoTransitionResult(
                False,
                getattr(item, "rejection_reason", "") or "Task did not satisfy completion validator.",
                status,
                "completion_validator_failed",
                409,
                changed=getattr(item, "status", "") != before,
            )
    elif status == "approved":
        item.rejection_reason = ""
        todo_tracker.mark_approved(idx, (reason or "").strip())
    elif status == "rejected":
        todo_tracker.mark_rejected(idx, (reason or "").strip())
    elif status == "pending":
        item.status = "pending"
        item.completed_at = None
        if getattr(todo_tracker, "current_index", -1) == idx:
            todo_tracker.current_index = -1
        todo_tracker.save()

    return TodoTransitionResult(
        True,
        status=status,
        changed=getattr(item, "status", "") != before,
    )
