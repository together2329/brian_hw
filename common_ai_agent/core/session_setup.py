"""core/session_setup.py — Shared session initialization for main agent and worker servers.

Extracted from src/main.py so that agent_server.py can share the same
session/todo setup logic without duplication.

Public API:
    setup_session(project, workflow) -> Path
"""
from __future__ import annotations

import shutil
import os
from pathlib import Path


def _migrate_old_session(session_dir: Path) -> None:
    """Migrate old .session/ layouts to v2 flat project structure.

    v0 (original flat):
      .session/<name>/conversation_history.json
      .session/<name>/current_todos.json

    v1 (primary/sub):
      .session/<name>/primary/conversation.json
      .session/<name>/primary/<workflow>/todo.json
      .session/<name>/sub/agent<N>_<wf>/...

    v2 (target — flat project):
      .session/<name>/conversation.json
      .session/<name>/todo.json
      .session/<name>/jobs/job<N>/...
    """
    # ── v1 → v2: move files out of primary/ ──
    primary_dir = session_dir / 'primary'
    if primary_dir.is_dir():
        for fname in ('conversation.json', 'full_conversation.json'):
            src = primary_dir / fname
            dst = session_dir / fname
            if src.exists():
                if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                    shutil.move(str(src), str(dst))

        if primary_dir.is_dir():
            for wf_dir in primary_dir.iterdir():
                if not wf_dir.is_dir():
                    continue
                for data_name in ('todo.json', 'todo_error.json', 'input_history.txt'):
                    src = wf_dir / data_name
                    dst = session_dir / data_name
                    if src.exists():
                        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                            shutil.move(str(src), str(dst))

        try:
            shutil.rmtree(primary_dir, ignore_errors=True)
        except Exception:
            pass

    # ── v1 → v2: rename sub/ → jobs/ ──
    sub_dir = session_dir / 'sub'
    jobs_dir = session_dir / 'jobs'
    if sub_dir.is_dir():
        jobs_dir.mkdir(parents=True, exist_ok=True)
        existing_jobs = [d for d in jobs_dir.iterdir() if d.is_dir() and d.name.startswith('job')]
        counter = len(existing_jobs) + 1
        for agent_dir in sorted(sub_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name == '.counter':
                continue
            job_dir = jobs_dir / f'job{counter}'
            counter += 1
            if not job_dir.exists():
                shutil.move(str(agent_dir), str(job_dir))
        try:
            shutil.rmtree(sub_dir, ignore_errors=True)
        except Exception:
            pass

    # ── v0 → v2: rename old flat filenames ──
    for old_name, new_name in [
        ('conversation_history.json',      'conversation.json'),
        ('full_conversation_history.json', 'full_conversation.json'),
        ('current_todos.json',             'todo.json'),
        ('current_todos_error.json',       'todo_error.json'),
    ]:
        old = session_dir / old_name
        if old.exists() and not (session_dir / new_name).exists():
            shutil.move(str(old), str(session_dir / new_name))
        elif old.exists():
            old.unlink()


def setup_session(project: str = 'default', workflow: str = '') -> Path:
    """Create .session/<session>/ layout and redirect config paths.

    Layout (v2 — flat session namespace):
      .session/<session>/conversation.json       ← HISTORY_FILE
      .session/<session>/full_conversation.json  ← append-only history
      .session/<session>/todo.json               ← TODO_FILE
      .session/<session>/todo_error.json         ← TODO_ERROR_FILE
      .session/<session>/jobs/job<N>/            ← sub-agent persistence

    Args:
        project:  Session namespace (maps to .session/<session>/).
        workflow: Ignored (kept for backward compat with v1 callers).

    Returns:
        Path to the session directory.
    """
    import config

    session_dir_env = str(os.environ.get('ATLAS_SESSION_DIR') or '').strip()
    if session_dir_env:
        session_dir = Path(session_dir_env).expanduser().resolve()
    else:
        project_root = Path(os.environ.get('ATLAS_PROJECT_ROOT') or Path.cwd()).resolve()
        session_dir = project_root / '.session' / project.strip('/')
    session_dir.mkdir(parents=True, exist_ok=True)

    _migrate_old_session(session_dir)

    config.HISTORY_FILE    = str(session_dir / 'conversation.json')
    config.TODO_FILE       = str(session_dir / 'todo.json')
    config.TODO_ERROR_FILE = str(session_dir / 'todo_error.json')
    config.COST_FILE       = str(session_dir / 'cost.json')
    config.SESSION_DIR     = str(session_dir)
    config.ACTIVE_PROJECT  = project

    # Patch lib.todo_tracker module-level TODO_FILE so TodoTracker.load()
    # without an explicit path uses the right file.
    try:
        import lib.todo_tracker as _tt
        _tt.TODO_FILE = session_dir / 'todo.json'
    except Exception:
        pass

    return session_dir


def workflow_switch_target(active_session: str, workflow_name: str) -> tuple[str, str]:
    """Rebuild the active session key with only the workflow segment swapped.

    Returns ``(target_session, prev_workflow)``. Namespace shapes:

      4-seg v2:    <owner>/<workspace_session>/<ip>/<workflow>
      3-seg legacy: <owner>/<ip>/<workflow>

    The 4-seg shape must keep its workspace_session segment intact — treating
    segment[1] as the IP (the old 3-seg assumption) silently drops the real IP
    and collapses the namespace, so the switched workflow lands in the wrong
    session directory and the canonical key never reflects the new workflow.
    Missing segments pad with "default" so the switch works before an IP is
    picked.
    """
    parts = [p for p in str(active_session or "").split("/") if p]
    workflow = str(workflow_name or "").strip() or "default"
    if len(parts) >= 4:
        owner, workspace_session, ip = parts[0], parts[1], parts[2]
        prev_workflow = parts[3]
        return f"{owner}/{workspace_session}/{ip}/{workflow}", prev_workflow
    owner = parts[0] if len(parts) >= 1 and parts[0] else "default"
    ip = parts[1] if len(parts) >= 2 and parts[1] else "default"
    prev_workflow = parts[2] if len(parts) >= 3 else ""
    return f"{owner}/{ip}/{workflow}", prev_workflow
