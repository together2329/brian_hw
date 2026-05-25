"""Orchestrator tool layer.

Each tool returns ``(result_dict, evidence_summary)`` where the summary is a
short string (<= 2 KB) suitable for persisting to ``orchestrator_steps``.
Tools wrap existing helpers — they do not re-implement dispatch, state read,
or handoff logic.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Tuple

from src.orchestrator.classify import HUMAN_ESCALATION, classify_failure


ToolResult = Tuple[Dict[str, Any], str]


_EVIDENCE_CAP = 2_000
_IP_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def _truncate(text: str, cap: int = _EVIDENCE_CAP) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= cap:
        return text
    return text[: cap - 20] + "\n…[truncated]"


def _safe_json(value: Any, cap: int = _EVIDENCE_CAP) -> str:
    try:
        return _truncate(json.dumps(value, ensure_ascii=False, sort_keys=True), cap)
    except Exception:
        return _truncate(repr(value), cap)


def _uniq_nonempty(values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values or []:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _one_or_many(values: list[str]) -> Any:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return values


def _dispatch_summary_payload(result: Dict[str, Any]) -> Dict[str, Any]:
    jobs = [j for j in (result.get("jobs") or []) if isinstance(j, dict)]
    job_ids = _uniq_nonempty(j.get("job_id") for j in jobs)
    models = _uniq_nonempty(j.get("model") for j in jobs)
    efforts = _uniq_nonempty(j.get("reasoning_effort") for j in jobs)
    workers = _uniq_nonempty(j.get("worker") for j in jobs)
    return {
        "ok": result.get("ok"),
        "source": result.get("source"),
        "pipeline_run_id": result.get("pipeline_run_id"),
        "job_ids": job_ids,
        "model": _one_or_many(models),
        "reasoning_effort": _one_or_many(efforts),
        "worker": _one_or_many(workers),
        "schedule": result.get("schedule"),
        "run_mode": result.get("run_mode"),
        "exec_mode": result.get("exec_mode"),
        "error": result.get("error"),
    }


def _is_valid_ip_name(ip: str) -> bool:
    return bool(_IP_NAME_RE.fullmatch(str(ip or "")))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _mtime_iso(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _rel_to_ip(path: Path, ip_dir: Path) -> str:
    try:
        return str(path.relative_to(ip_dir))
    except ValueError:
        return path.name


def _annotate_freshness(entry: Dict[str, Any], path: Path, ip_dir: Path) -> None:
    if not path.exists():
        return
    try:
        entry["mtime"] = _mtime_iso(path)
        entry["mtime_ns"] = path.stat().st_mtime_ns
    except OSError:
        return

    rel = _rel_to_ip(path, ip_dir)
    if rel not in {"sim/fl_rtl_compare.json", "sim/mismatch_classification.json"}:
        return

    # These are sim_debug outputs. If a newer sim or equivalence-goal artifact
    # exists, the old classification must not drive owner routing.
    deps = (
        "sim/scoreboard_events.jsonl",
        "sim/results.xml",
        "verify/equivalence_goals.json",
    )
    stale_against = []
    artifact_mtime = path.stat().st_mtime_ns
    for dep in deps:
        dep_path = ip_dir / dep
        if not dep_path.exists():
            continue
        try:
            dep_mtime = dep_path.stat().st_mtime_ns
        except OSError:
            continue
        if artifact_mtime < dep_mtime:
            stale_against.append(
                {
                    "rel": dep,
                    "mtime": _mtime_iso(dep_path),
                    "mtime_ns": dep_mtime,
                }
            )
    if stale_against:
        entry["freshness_status"] = "stale_artifact"
        entry["stale_against"] = stale_against


# ----------------------------------------------------------------------
# Bridge resolution — read_pipeline_state / dispatch_workflow live in
# core.tools as module-level callbacks installed by register_jobs_routes.
# ----------------------------------------------------------------------


def _read_pipeline_state_bridge() -> Optional[Callable]:
    try:
        from core import tools as core_tools  # type: ignore
    except Exception:
        return None
    return getattr(core_tools, "_read_pipeline_state_callback", None)


def _dispatch_workflow_bridge() -> Optional[Callable]:
    try:
        from core import tools as core_tools  # type: ignore
    except Exception:
        return None
    return getattr(core_tools, "_dispatch_workflow_callback", None)


def _atlas_api_jobs_module() -> Optional[ModuleType]:
    """Return the already-loaded jobs module, regardless of import style."""
    module = sys.modules.get("atlas_api_jobs") or sys.modules.get("src.atlas_api_jobs")
    if isinstance(module, ModuleType):
        return module
    try:
        import atlas_api_jobs  # type: ignore

        return atlas_api_jobs
    except Exception:
        pass
    try:
        from src import atlas_api_jobs  # type: ignore

        return atlas_api_jobs
    except Exception:
        return None


def _jobs_registry() -> Optional[Tuple[Dict[str, Any], Any]]:
    """Return the live (_jobs, _jobs_lock) registry from atlas_api_jobs."""
    atlas_api_jobs = _atlas_api_jobs_module()
    if atlas_api_jobs is None:
        return None
    jobs = getattr(atlas_api_jobs, "_jobs", None)
    lock = getattr(atlas_api_jobs, "_jobs_lock", None)
    if jobs is None or lock is None:
        return None
    return jobs, lock


def _pipeline_stage_deps() -> Dict[str, Tuple[str, ...]]:
    atlas_api_jobs = _atlas_api_jobs_module()
    if atlas_api_jobs is None:
        return {}
    return getattr(atlas_api_jobs, "_PIPELINE_STAGE_DEPS", {})


# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------


def read_pipeline_state(ip: str, include_jobs: bool = True) -> ToolResult:
    bridge = _read_pipeline_state_bridge()
    if bridge is None:
        return (
            {"ok": False, "error": "read_pipeline_state bridge not registered"},
            "bridge unavailable",
        )
    result = bridge(ip=ip, scope="", include_jobs=bool(include_jobs))
    summary = _safe_json(
        {
            "ip": ip,
            "passed": result.get("passed") if isinstance(result, dict) else None,
            "failed": result.get("failed") if isinstance(result, dict) else None,
            "running": result.get("running") if isinstance(result, dict) else None,
        }
    )
    return result if isinstance(result, dict) else {"ok": False, "raw": str(result)}, summary


def dispatch_workflow(
    *,
    workflow: str = "",
    ip: str,
    stages: Optional[list] = None,
    payload: Optional[Dict[str, Any]] = None,
    prompt: str = "",
    schedule: str = "auto",
    reason: str = "",
    orchestrator_run_id: str = "",
    model: str = "",
    run_mode: str = "",
    exec_mode: str = "",
) -> ToolResult:
    """Dispatch one or many workers in a single call.

    Pass either ``workflow`` (single stage) or ``stages`` (list, fan-out). When
    multiple independent stages are dispatched together with ``schedule="dag"``
    the underlying dispatcher honours the canonical pipeline DAG and runs
    independent stages (e.g. lint / tb-gen / syn after rtl-gen) in parallel.
    """
    body = dict(payload or {})
    if orchestrator_run_id:
        body.setdefault("orchestrator_run_id", orchestrator_run_id)
        body.setdefault("trigger_source", "orchestrator_chat")
    if reason:
        body.setdefault("reason", reason)

    bridge = _dispatch_workflow_bridge()
    if bridge is None:
        try:
            from core import tools as core_tools  # type: ignore

            direct = getattr(core_tools, "_dispatch_workflow_direct_fallback", None)
            if callable(direct):
                result, skip_reason = direct(
                    workflow=workflow,
                    ip=ip,
                    stages=stages,
                    payload=body,
                    prompt=prompt,
                    schedule=schedule,
                    reason=reason,
                    model=model,
                    run_mode=run_mode,
                    exec_mode=exec_mode,
                )
                if isinstance(result, dict):
                    summary_payload = _dispatch_summary_payload(result)
                    summary_payload.update({
                        "workflow": result.get("workflow"),
                        "status": result.get("status"),
                        "model": summary_payload.get("model") or model or "",
                        "worker": summary_payload.get("worker") or result.get("worker"),
                        "error": (result.get("result") or {}).get("error")
                        if isinstance(result.get("result"), dict)
                        else result.get("error"),
                    })
                    summary = _safe_json(summary_payload)
                    return result, summary
                if skip_reason:
                    return (
                        {
                            "ok": False,
                            "error": "dispatch_workflow bridge not registered",
                            "direct_fallback": skip_reason,
                        },
                        f"bridge unavailable; {skip_reason}",
                    )
        except Exception as exc:
            return (
                {
                    "ok": False,
                    "error": "dispatch_workflow bridge not registered",
                    "direct_fallback": f"{type(exc).__name__}: {exc}",
                },
                f"bridge unavailable; direct fallback failed: {type(exc).__name__}: {exc}",
            )
        return (
            {"ok": False, "error": "dispatch_workflow bridge not registered"},
            "bridge unavailable",
        )

    result = bridge(
        workflow=workflow,
        ip=ip,
        stages=stages,
        payload=body,
        prompt=prompt,
        schedule=schedule,
        reason=reason,
        model=model,
        run_mode=run_mode,
        exec_mode=exec_mode,
    )
    if not isinstance(result, dict):
        return {"ok": False, "raw": str(result)}, "non-dict result"
    summary = _safe_json(_dispatch_summary_payload(result))
    return result, summary


def wait_job(job_id: str) -> ToolResult:
    """Non-blocking snapshot of a job by id.

    Returns the current state immediately. The loop is expected to call this
    again on the next iteration if the job is still running, so a long-running
    worker never holds an orchestrator thread.
    """
    registry = _jobs_registry()
    if registry is None:
        return (
            {"ok": False, "error": "job registry unavailable"},
            "registry unavailable",
        )
    jobs, lock = registry
    with lock:
        job = jobs.get(job_id)
        snapshot = dict(job) if job else None
    if snapshot is None:
        return ({"ok": False, "error": f"unknown job {job_id!r}"}, f"missing {job_id}")
    summary = _safe_json(
        {
            "job_id": snapshot.get("job_id"),
            "status": snapshot.get("status"),
            "workflow": snapshot.get("workflow"),
            "stage_id": snapshot.get("stage_id"),
        }
    )
    return {"ok": True, "job": snapshot}, summary


def _resolve_local_path(
    *,
    ip: str,
    path: str,
    project_root: Optional[Path] = None,
    allow_wiki: bool = True,
    allow_missing: bool = False,
) -> Tuple[Optional[Path], str]:
    pr = Path(project_root) if project_root else Path(
        os.environ.get("ATLAS_PROJECT_ROOT") or "."
    )
    requested = Path(str(path or "").strip())
    if not requested.parts:
        return None, "path is required"
    if requested.is_absolute() or ".." in requested.parts:
        return None, "path must be a safe relative path"

    ip_dir = (pr / ip).resolve()
    allowed_roots = [ip_dir]
    if allow_wiki:
        allowed_roots.extend([(pr / "doc" / "wiki").resolve(), (pr / ".omx" / "wiki").resolve()])
    if requested.parts and requested.parts[0] == ip:
        candidate = (pr / requested).resolve()
    else:
        candidate = (ip_dir / requested).resolve()
        if not candidate.exists() and allow_wiki:
            project_candidate = (pr / requested).resolve()
            if any(_is_relative_to(project_candidate, root) for root in allowed_roots):
                candidate = project_candidate

    if not any(_is_relative_to(candidate, root) for root in allowed_roots):
        return None, "path is outside the active IP or wiki roots"
    if not allow_missing and not candidate.exists():
        return None, "path not found"
    return candidate, ""


def _relative_display(path: Path, project_root: Optional[Path]) -> str:
    pr = Path(project_root) if project_root else Path(os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    try:
        return str(path.relative_to(pr.resolve()))
    except Exception:
        return path.name


def _tool_text_header(path: str, meta: str = "") -> str:
    suffix = f" {meta}" if meta else ""
    return f"path: {path}{suffix}\n---\n"


def _dump_readable(value: Any, cap: int = 20_000) -> str:
    try:
        import yaml  # type: ignore

        if isinstance(value, (dict, list)):
            text = yaml.safe_dump(value, sort_keys=False, allow_unicode=True)
        else:
            text = str(value)
    except Exception:
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            text = str(value)
    return _truncate(text, cap)


def _yaml_selector_parts(selector: str) -> list[Any]:
    parts: list[Any] = []
    for raw in str(selector or "").split("."):
        token = raw.strip()
        if not token:
            continue
        match = re.match(r"^[^\[\]]+", token)
        if match:
            parts.append(match.group(0))
        for idx in re.findall(r"\[(\d+)\]", token):
            parts.append(int(idx))
    return parts


def _select_path(value: Any, selector: str) -> Tuple[bool, Any]:
    cur = value
    for part in _yaml_selector_parts(selector):
        if isinstance(part, int):
            if not isinstance(cur, list) or part >= len(cur):
                return False, None
            cur = cur[part]
        else:
            if not isinstance(cur, dict) or part not in cur:
                return False, None
            cur = cur[part]
    return True, cur


def list_dir(
    *,
    ip: str,
    path: str = ".",
    project_root: Optional[Path] = None,
    max_entries: int = 200,
) -> ToolResult:
    """List a directory under the active IP or project wiki."""
    path_obj, error = _resolve_local_path(ip=ip, path=path or ".", project_root=project_root)
    if path_obj is None:
        return {"ok": False, "error": error, "path": path}, error
    if not path_obj.is_dir():
        return {"ok": False, "error": "path is not a directory", "path": path}, "path is not a directory"
    cap = max(1, min(int(max_entries or 200), 1000))
    entries = []
    try:
        children = sorted(path_obj.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for child in children[:cap]:
            info: Dict[str, Any] = {
                "name": child.name + ("/" if child.is_dir() else ""),
                "type": "dir" if child.is_dir() else "file",
            }
            if child.is_file():
                try:
                    info["size"] = child.stat().st_size
                except OSError:
                    pass
            entries.append(info)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "path": path}, err
    result = {
        "ok": True,
        "ip": ip,
        "path": path,
        "resolved": str(path_obj),
        "entries": entries,
        "truncated": len(entries) == cap,
    }
    body = "\n".join(
        f"- {entry['name']}" + (f" {entry['size']}B" if "size" in entry else "")
        for entry in entries
    )
    if len(entries) == cap:
        body += "\n...[truncated]"
    return result, _tool_text_header(path) + body


def read_file(
    *,
    ip: str,
    path: str,
    project_root: Optional[Path] = None,
    contains: str = "",
    before: int = 2,
    after: int = 80,
    start_line: int = 0,
    end_line: int = 0,
    max_chars: int = 20_000,
    yaml_path: str = "",
) -> ToolResult:
    """Read a safe local file for direct user Q&A.

    This is intentionally simpler than ``read_artifact``: it reads exactly the
    file the orchestrator needs, optionally narrowed to a matching section or
    line range. Scope is limited to the active IP plus project wiki roots.
    """
    path_obj, error = _resolve_local_path(ip=ip, path=path, project_root=project_root)
    if path_obj is None:
        return {"ok": False, "error": error, "path": path}, error
    if not path_obj.exists():
        return {"ok": False, "error": "file not found", "path": path}, "file not found"
    if not path_obj.is_file():
        return {"ok": False, "error": "path is not a file", "path": path}, "path is not a file"

    try:
        text = path_obj.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "path": path}, err

    selector = str(yaml_path or "").strip()
    if selector:
        cap = max(1_000, min(int(max_chars or 20_000), 100_000))
        try:
            import yaml  # type: ignore

            doc = yaml.safe_load(text)
        except Exception as exc:
            err = f"yaml parse failed: {type(exc).__name__}: {exc}"
            return {"ok": False, "error": err, "path": path, "yaml_path": selector}, err
        found, selected_value = _select_path(doc, selector)
        if not found:
            err = f"yaml_path not found: {selector}"
            return {"ok": False, "error": err, "path": path, "yaml_path": selector}, err
        rendered = _dump_readable(selected_value, cap=cap)
        result = {
            "ok": True,
            "ip": ip,
            "path": str(path),
            "resolved": str(path_obj),
            "mode": "yaml_path",
            "yaml_path": selector,
            "data": selected_value,
            "content": rendered,
            "truncated": len(rendered) >= cap,
        }
        return result, _tool_text_header(path, f"yaml_path={selector}") + rendered

    lines = text.splitlines()
    selected = text
    line_start = 1
    line_end = len(lines)
    mode = "full"

    needle = str(contains or "").strip()
    if needle:
        match_idx = next((idx for idx, line in enumerate(lines) if needle in line), -1)
        if match_idx < 0:
            selected = ""
            line_start = 0
            line_end = 0
            mode = "contains_not_found"
        else:
            left = max(0, match_idx - max(0, int(before)))
            right = min(len(lines), match_idx + max(0, int(after)) + 1)
            selected = "\n".join(lines[left:right])
            line_start = left + 1
            line_end = right
            mode = "contains"
    elif start_line or end_line:
        start = max(1, int(start_line or 1))
        end = int(end_line or start + 120)
        end = max(start, min(end, len(lines)))
        selected = "\n".join(lines[start - 1:end])
        line_start = start
        line_end = end
        mode = "lines"

    cap = max(1_000, min(int(max_chars or 20_000), 100_000))
    truncated = len(selected) > cap
    if truncated:
        selected = selected[: cap - 20] + "\n...[truncated]"

    result = {
        "ok": True,
        "ip": ip,
        "path": str(path),
        "resolved": str(path_obj),
        "mode": mode,
        "line_start": line_start,
        "line_end": line_end,
        "truncated": truncated,
        "content": selected,
    }
    meta = f"mode={mode} lines={line_start}-{line_end}"
    if truncated:
        meta += " truncated=true"
    summary = _tool_text_header(path, meta) + selected
    return result, summary


def grep_file(
    *,
    ip: str,
    pattern: str,
    path: str = ".",
    project_root: Optional[Path] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    max_matches: int = 80,
    max_chars: int = 20_000,
) -> ToolResult:
    """Search files under the active IP or wiki roots."""
    path_obj, error = _resolve_local_path(ip=ip, path=path or ".", project_root=project_root)
    if path_obj is None:
        return {"ok": False, "error": error, "path": path}, error
    needle = str(pattern or "")
    if not needle:
        return {"ok": False, "error": "pattern is required"}, "pattern is required"
    flags = 0 if case_sensitive else re.IGNORECASE
    compiled = None
    if regex:
        try:
            compiled = re.compile(needle, flags)
        except re.error as exc:
            return {"ok": False, "error": f"invalid regex: {exc}"}, f"invalid regex: {exc}"
    else:
        cmp_needle = needle if case_sensitive else needle.lower()

    def _candidate_files(root: Path):
        if root.is_file():
            yield root
            return
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", ".session", "__pycache__", "node_modules"}]
            for filename in filenames:
                yield Path(dirpath) / filename

    matches = []
    cap = max(1, min(int(max_matches or 80), 1000))
    for file_path in _candidate_files(path_obj):
        if len(matches) >= cap:
            break
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            hit = bool(compiled.search(line)) if compiled is not None else (
                cmp_needle in (line if case_sensitive else line.lower())
            )
            if not hit:
                continue
            matches.append(
                {
                    "path": _relative_display(file_path, project_root),
                    "line": line_no,
                    "text": line[:500],
                }
            )
            if len(matches) >= cap:
                break
    result = {
        "ok": True,
        "ip": ip,
        "path": path,
        "pattern": pattern,
        "matches": matches,
        "truncated": len(matches) == cap,
    }
    body = "\n".join(f"{m['path']}:{m['line']}: {m['text']}" for m in matches)
    if len(matches) == cap:
        body += "\n...[truncated]"
    return result, _truncate(_tool_text_header(path, f"pattern={pattern}") + body, max(1_000, min(int(max_chars or 20_000), 100_000)))


def write_file(
    *,
    ip: str,
    path: str,
    content: str,
    project_root: Optional[Path] = None,
    create_dirs: bool = True,
    overwrite: bool = True,
) -> ToolResult:
    """Write a file under the active IP directory only."""
    path_obj, error = _resolve_local_path(
        ip=ip,
        path=path,
        project_root=project_root,
        allow_wiki=False,
        allow_missing=True,
    )
    if path_obj is None:
        return {"ok": False, "error": error, "path": path}, error
    if path_obj.exists() and not overwrite:
        return {"ok": False, "error": "file exists", "path": path}, "file exists"
    try:
        if create_dirs:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(str(content or ""), encoding="utf-8")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "path": path}, err
    result = {"ok": True, "ip": ip, "path": path, "bytes": len(str(content or "").encode("utf-8"))}
    return result, f"wrote {result['bytes']} bytes to {path}"


def replace_in_file(
    *,
    ip: str,
    path: str,
    old: str,
    new: str,
    project_root: Optional[Path] = None,
    replace_all: bool = False,
) -> ToolResult:
    """Replace text in a file under the active IP directory only."""
    path_obj, error = _resolve_local_path(ip=ip, path=path, project_root=project_root, allow_wiki=False)
    if path_obj is None:
        return {"ok": False, "error": error, "path": path}, error
    old_text = str(old or "")
    if old_text == "":
        return {"ok": False, "error": "old text is required", "path": path}, "old text is required"
    try:
        original = path_obj.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "path": path}, err
    count = original.count(old_text)
    if count <= 0:
        return {"ok": False, "error": "old text not found", "path": path}, "old text not found"
    limit = count if replace_all else 1
    updated = original.replace(old_text, str(new or ""), limit)
    try:
        path_obj.write_text(updated, encoding="utf-8")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "path": path}, err
    result = {
        "ok": True,
        "ip": ip,
        "path": path,
        "replacements": limit,
        "remaining_matches": max(0, count - limit),
    }
    return result, f"replaced {limit} occurrence(s) in {path}; remaining_matches={max(0, count - limit)}"


def run_command(
    *,
    ip: str,
    command: str,
    project_root: Optional[Path] = None,
    cwd: str = ".",
    timeout: int = 60,
    max_chars: int = 20_000,
) -> ToolResult:
    """Run a shell command with cwd constrained to the active IP directory."""
    cwd_obj, error = _resolve_local_path(
        ip=ip,
        path=cwd or ".",
        project_root=project_root,
        allow_wiki=False,
    )
    if cwd_obj is None:
        return {"ok": False, "error": error, "cwd": cwd}, error
    if not cwd_obj.is_dir():
        return {"ok": False, "error": "cwd is not a directory", "cwd": cwd}, "cwd is not a directory"
    cmd = str(command or "").strip()
    if not cmd:
        return {"ok": False, "error": "command is required"}, "command is required"
    timeout_s = max(1, min(int(timeout or 60), 300))
    cap = max(1_000, min(int(max_chars or 20_000), 100_000))
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd_obj),
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        stdout = _truncate(completed.stdout or "", cap // 2)
        stderr = _truncate(completed.stderr or "", cap // 2)
        result = {
            "ok": completed.returncode == 0,
            "ip": ip,
            "cwd": cwd,
            "command": cmd,
            "returncode": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
        summary = (
            f"returncode: {completed.returncode}\n"
            f"cwd: {cwd}\n"
            f"command: {cmd}\n"
            "--- stdout ---\n"
            f"{stdout}\n"
            "--- stderr ---\n"
            f"{stderr}"
        )
        return result, _truncate(summary, cap)
    except subprocess.TimeoutExpired as exc:
        result = {
            "ok": False,
            "ip": ip,
            "cwd": cwd,
            "command": cmd,
            "error": f"timeout after {timeout_s}s",
            "stdout": _truncate(exc.stdout or "", cap // 2),
            "stderr": _truncate(exc.stderr or "", cap // 2),
        }
        return result, _truncate(
            f"timeout after {timeout_s}s\n--- stdout ---\n{result['stdout']}\n--- stderr ---\n{result['stderr']}",
            cap,
        )
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        return {"ok": False, "error": err, "command": cmd}, err


def read_artifact(ip: str, stage: str, project_root: Optional[Path] = None) -> ToolResult:
    """Read canonical evidence for ``stage`` under ``<ip>/...``.

    Resolves the canonical path map used by the pipeline state reader. If
    ``stage`` is a safe relative artifact path, reads that exact file or
    directory; this lets the loop recover when it asks for
    ``tb/cocotb/tb_blocked.json`` instead of canonical stage ``tb``. JSON files
    are parsed; other files return a head-of-file text slice.
    """
    pr = Path(project_root) if project_root else Path(
        os.environ.get("ATLAS_PROJECT_ROOT") or "."
    )
    ip_dir = pr / ip
    artifact_map: Dict[str, Tuple[str, ...]] = {
        "ssot": ("yaml/{ip}.ssot.yaml",),
        "fl-model": ("model/fl_model_check.json", "cov/fcov_plan.json"),
        "cl-model": ("model/cl_model_check.json",),
        "equivalence": ("verify/equivalence_goals.json",),
        "rtl": (
            "logs/stage_engine/ssot-rtl.json",
            "rtl/rtl_blocked.json",
            "rtl/rtl_blocked_resolved.json",
            "rtl/rtl_contract.json",
            "rtl/rtl_compile.json",
            "lint/dut_lint.json",
            "rtl/rtl_todo_plan.json",
        ),
        "lint": ("lint/dut_lint.json",),
        "tb": ("tb/cocotb/",),
        "sim": ("sim/results.xml", "sim/scoreboard_events.jsonl", "sim/fl_rtl_compare.json"),
        "coverage": ("cov/coverage.json",),
        "sim-debug": ("sim/fl_rtl_compare.json", "sim/mismatch_classification.json"),
        "sim_debug": ("sim/fl_rtl_compare.json", "sim/mismatch_classification.json"),
        "goal-audit": ("sim/fl_rtl_goal_audit.json",),
        "goal_audit": ("sim/fl_rtl_goal_audit.json",),
        "syn": ("syn/out/",),
        "sta": ("sta/out/",),
        "pnr": ("pnr/out/",),
        "sta-post": ("sta-post/out/",),
    }
    relatives = artifact_map.get(stage, ())
    if not relatives:
        requested = Path(str(stage or ""))
        if not requested.is_absolute() and ".." not in requested.parts and requested.parts:
            candidate = ip_dir / requested
            if _is_relative_to(candidate.resolve(), ip_dir.resolve()):
                relatives = (str(requested),)
    def _preview(entry: Dict[str, Any]) -> Dict[str, Any]:
        preview: Dict[str, Any] = {
            "rel": entry.get("rel"),
            "exists": entry.get("exists"),
        }
        for key in ("mtime", "mtime_ns", "freshness_status", "stale_against"):
            if key in entry:
                preview[key] = entry.get(key)
        data = entry.get("data")
        if isinstance(data, dict):
            for key in ("type", "status", "owner", "next_workflow", "reason"):
                if key in data:
                    preview[key] = data.get(key)
            if isinstance(data.get("summary"), dict):
                preview["summary"] = data.get("summary")
            if isinstance(data.get("gate"), dict):
                preview["gate"] = data.get("gate")
            if isinstance(data.get("metadata"), dict):
                metadata_preview: Dict[str, Any] = {}
                rtl_todo_plan = data["metadata"].get("rtl_todo_plan")
                if isinstance(rtl_todo_plan, dict) and isinstance(rtl_todo_plan.get("gate"), dict):
                    metadata_preview["rtl_todo_gate"] = rtl_todo_plan.get("gate")
                if metadata_preview:
                    preview["metadata"] = metadata_preview
            for key in ("headline", "returncode", "blocker"):
                if key in data:
                    preview[key] = data.get(key)
            if isinstance(data.get("message"), str):
                preview["message"] = data.get("message", "")[:1200]
            classifications = data.get("classifications")
            if isinstance(classifications, list):
                preview["classifications"] = classifications[:3]
            if isinstance(data.get("mismatch_classification"), dict):
                preview["mismatch_classification"] = data.get("mismatch_classification")
        elif isinstance(data, list):
            preview["data"] = data[:3]
        if "head" in entry:
            preview["head"] = str(entry.get("head") or "")[:1200]
        if "entries" in entry:
            preview["entries"] = entry.get("entries")
        if "error" in entry:
            preview["error"] = entry.get("error")
        return preview

    artifacts: list = []
    for rel in relatives:
        path = ip_dir / rel.format(ip=ip)
        entry: Dict[str, Any] = {"rel": rel, "path": str(path), "exists": path.exists()}
        _annotate_freshness(entry, path, ip_dir)
        if path.is_file():
            try:
                if path.suffix == ".json":
                    entry["data"] = json.loads(path.read_text(encoding="utf-8"))
                else:
                    entry["head"] = path.read_text(encoding="utf-8", errors="replace")[:8_000]
            except Exception as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
        elif path.is_dir():
            try:
                entry["entries"] = sorted(p.name for p in path.iterdir())[:50]
            except Exception as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
        artifacts.append(entry)
    result = {"ok": True, "ip": ip, "stage": stage, "artifacts": artifacts}
    summary = _safe_json(
        {
            "stage": stage,
            "files": [a["rel"] for a in artifacts if a["exists"]],
            "missing": [a["rel"] for a in artifacts if not a["exists"]],
            "previews": [_preview(a) for a in artifacts if a["exists"]],
        }
    )
    return result, summary


def classify_failure_tool(
    *,
    stage: str,
    evidence: Optional[Dict[str, Any]] = None,
    error_text: str = "",
) -> ToolResult:
    decision = classify_failure(stage, evidence=evidence, error_text=error_text)
    summary = _safe_json(decision)
    return decision, summary


def ask_user(
    *,
    db: Any,
    run_id: str,
    ip_id: str,
    user_id: str,
    session_id: str,
    question: str,
    context: Optional[Dict[str, Any]] = None,
) -> ToolResult:
    """Record a human-decision-required event and mark the run paused.

    The accompanying step (written by the loop) records ``verdict="awaiting_user"``;
    this tool's job is to surface the question on the trace ledger so the UI
    chat stream can render it.
    """
    payload = {
        "run_id": run_id,
        "question": question,
        "context": context or {},
    }
    db.record_trace_event(
        event_type="orchestrator_ask_user",
        payload=payload,
        session_id=session_id,
        ip_id=ip_id,
        actor_user_id=user_id,
        correlation_id=run_id,
    )
    db.update_orchestrator_run(run_id, status="paused")
    return ({"ok": True, "state": "paused", "question": question}, _truncate(question))


def write_handoff(
    *,
    ip: str,
    workflow: str,
    payload: Dict[str, Any],
    reason: str,
    user_id: str,
    session_id: str,
    pipeline_run_id: str,
    orchestrator_run_id: str = "",
    from_workflow: str = "orchestrator",
    project_root: Optional[Path] = None,
) -> ToolResult:
    from src import handoff_queue

    pr = Path(project_root) if project_root else Path(
        os.environ.get("ATLAS_PROJECT_ROOT") or "."
    )
    ip_dir = pr / ip
    scope = handoff_queue.make_scope(
        user_id=user_id,
        session_id=session_id,
        pipeline_run_id=pipeline_run_id,
    )
    handoff_id = handoff_queue.make_handoff_id(
        ip=ip,
        from_workflow=from_workflow,
        to_workflow=workflow,
        suffix=(orchestrator_run_id[:8] if orchestrator_run_id else ""),
    )
    record = {
        "handoff_id": handoff_id,
        "ip": ip,
        "from_workflow": from_workflow,
        "to_workflow": workflow,
        "scope": scope,
        "reason": reason,
        "payload": payload,
    }
    if orchestrator_run_id:
        record["orchestrator_run_id"] = orchestrator_run_id
    written = handoff_queue.write_pending(ip_dir, record)
    summary = _safe_json({"handoff_id": handoff_id, "path": str(written)})
    return ({"ok": True, "handoff_id": handoff_id, "path": str(written)}, summary)


def mark_downstream_stale(
    *,
    db: Any,
    ip_id: str,
    from_stage: str,
    run_id: str = "",
    session_id: str = "",
) -> ToolResult:
    """Emit stage_stale trace events for every downstream stage of from_stage."""
    deps = _pipeline_stage_deps()
    if not deps:
        return (
            {"ok": False, "error": "pipeline stage graph unavailable"},
            "graph missing",
        )
    downstream: list = []
    seen: set = set()
    frontier = [
        s for s, parents in deps.items() if from_stage in parents
    ]
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        downstream.append(cur)
        frontier.extend(
            s for s, parents in deps.items() if cur in parents and s not in seen
        )
    for stage in downstream:
        db.record_trace_event(
            event_type="stage_stale",
            payload={"from_stage": from_stage, "stale_stage": stage, "run_id": run_id},
            ip_id=ip_id,
            session_id=session_id,
            stage_id=stage,
            correlation_id=run_id,
        )
    return (
        {"ok": True, "from_stage": from_stage, "stale": downstream},
        _safe_json({"from": from_stage, "stale": downstream}),
    )


# ----------------------------------------------------------------------
# import_document — PDF / document → req/ extraction
# ----------------------------------------------------------------------


def _decode_pdf_literal(text: str) -> str:
    """Decode a simple PDF literal string used as a last-resort fallback."""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\\":
            out.append(ch)
            i += 1
            continue
        i += 1
        if i >= len(text):
            break
        esc = text[i]
        i += 1
        mapping = {
            "n": "\n",
            "r": "\r",
            "t": "\t",
            "b": "\b",
            "f": "\f",
            "(": "(",
            ")": ")",
            "\\": "\\",
        }
        if esc in mapping:
            out.append(mapping[esc])
        elif esc in "01234567":
            octal = esc
            for _ in range(2):
                if i < len(text) and text[i] in "01234567":
                    octal += text[i]
                    i += 1
                else:
                    break
            try:
                out.append(chr(int(octal, 8)))
            except ValueError:
                pass
        else:
            out.append(esc)
    return "".join(out)


def _extract_pdf_literal_text(raw: bytes) -> str:
    """Fallback extraction for tiny/simple PDFs with literal ``(...) Tj`` text."""
    data = raw.decode("latin-1", errors="ignore")
    chunks = []
    for match in re.finditer(r"\(((?:\\.|[^\\()])*)\)\s*Tj\b", data, flags=re.S):
        decoded = _decode_pdf_literal(match.group(1)).strip()
        if decoded:
            chunks.append(decoded)
    return "\n".join(chunks)


def _extract_pdf_text(path: str) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz).

    Falls back to pdfplumber if PyMuPDF is unavailable.
    Returns concatenated page text.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        pass
    else:
        doc = None
        try:
            doc = fitz.open(path)
            pages = []
            for page in doc:
                pages.append(page.get_text())
            text = "\n\n".join(pages)
            if text.strip():
                return text
        except Exception:
            pass
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

    try:
        import pdfplumber  # type: ignore
    except ImportError:
        pass
    else:
        pages = []
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
            text = "\n\n".join(pages)
            if text.strip():
                return text
        except Exception:
            pass

    try:
        return _extract_pdf_literal_text(Path(path).read_bytes())
    except Exception:
        return ""


def import_document(
    ip: str,
    path: str,
    *,
    project_root=None,
) -> ToolResult:
    """Import a PDF or text document as the requirement source for an IP.

    Writes:
      - ``<ip>/req/import_manifest.json``  (hash, provenance, source_path)
      - ``<ip>/req/source/<ip>.md``        (extracted text)

    Returns a dict with ``ok``, ``requirement_source_id``, ``pages``,
    ``char_count``, and the manifest path.
    """
    import hashlib
    import uuid

    if project_root is None:
        import os as _os
        project_root = _os.getcwd()
    project_root = Path(project_root).expanduser().resolve()

    ip = str(ip or "").strip()
    if not _is_valid_ip_name(ip):
        return (
            {"ok": False, "error": "valid ip required: use letters, digits, and underscores, starting with a letter"},
            "import_document error: invalid ip",
        )

    source_path = Path(path).expanduser().resolve()
    if not source_path.is_file():
        return (
            {"ok": False, "error": f"file not found: {source_path}"},
            f"import_document error: file not found: {source_path}",
        )

    # Read raw bytes for hashing
    raw = source_path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    source_id = f"req_{uuid.uuid4().hex[:12]}"

    # Extract text
    suffix = source_path.suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf_text(str(source_path))
        if not text:
            return (
                {"ok": False, "error": "PDF text extraction returned empty"},
                "import_document error: PDF extraction empty",
            )
        doc_type = "pdf"
    elif suffix in (".md", ".txt", ".rst"):
        text = raw.decode("utf-8", errors="replace")
        doc_type = suffix.lstrip(".")
    else:
        text = raw.decode("utf-8", errors="replace")
        doc_type = "unknown"

    # Write output
    ip_dir = (project_root / ip).resolve()
    if not _is_relative_to(ip_dir, project_root):
        return (
            {"ok": False, "error": "valid ip required: resolved path escapes project root"},
            "import_document error: ip path escaped project root",
        )
    req_dir = ip_dir / "req"
    source_dir = req_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "requirement_source_id": source_id,
        "source_path": str(source_path),
        "source_name": source_path.name,
        "doc_type": doc_type,
        "sha256": sha256,
        "char_count": len(text),
        "page_count": text.count("\n\n") + 1 if doc_type == "pdf" else None,
        "imported_at": time.time(),
        "tool": "import_document",
    }
    manifest_path = req_dir / "import_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md_path = source_dir / f"{ip}.md"
    md_path.write_text(text, encoding="utf-8")

    result = {
        "ok": True,
        "requirement_source_id": source_id,
        "source_name": source_path.name,
        "doc_type": doc_type,
        "char_count": len(text),
        "manifest_path": str(manifest_path.relative_to(project_root)),
        "source_md_path": str(md_path.relative_to(project_root)),
        "sha256": sha256,
    }
    return result, _safe_json(result)


# ----------------------------------------------------------------------
# web_search / web_fetch — direct orchestrator access to the web
# ----------------------------------------------------------------------


def web_search(query: str, limit: int = 5) -> ToolResult:
    """Search the web via cursor-cli and return results as text."""
    try:
        from core.tools_web import web_search as _impl  # type: ignore
        result_text = _impl(query=query, limit=int(limit), lang="en")
        return (
            {"ok": True, "results": result_text},
            f"web_search query={query!r} limit={limit}",
        )
    except Exception as exc:
        return ({"ok": False, "error": str(exc)}, "web_search failed")


def web_fetch(url: str, formats: str = "markdown") -> ToolResult:
    """Fetch a URL and return its content as markdown."""
    try:
        from core.tools_web import web_fetch as _impl  # type: ignore
        result_text = _impl(url=url, formats=formats)
        return (
            {"ok": True, "content": result_text},
            f"web_fetch url={url!r}",
        )
    except Exception as exc:
        return ({"ok": False, "error": str(exc)}, "web_fetch failed")
