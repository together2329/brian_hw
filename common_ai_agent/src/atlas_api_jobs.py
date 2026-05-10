"""ATLAS jobs API — extracted from atlas_ui.py (phase 6 of split).

Holds the HTTP-worker dispatch tracker: state, helpers, and all
/api/job* + /api/jobs* + /api/pipeline/* routes.  The host
(atlas_ui.py) wires routes via ``register_jobs_routes`` and injects
callables for runtime values so this module never reaches into the
host's mutable globals.

Exposed helpers
---------------
get_jobs_state() -> tuple[dict, threading.Lock]
    Returns (_jobs, _jobs_lock) so atlas_ui.py routes that need to
    read job state (e.g. /api/session/state) can do so without
    reaching into this module's globals directly.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# ── Module-level state ──────────────────────────────────────────────
_jobs_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}   # job_id (uuid hex) → job metadata

_PIPELINE_STAGES = [
    {"id": "ssot",        "workflow": "ssot-gen",    "label": "SSOT gen"},
    {"id": "equivalence", "workflow": "fl-model-gen", "label": "Equiv goals"},
    {"id": "rtl",         "workflow": "rtl-gen",      "label": "RTL gen"},
    {"id": "tb",          "workflow": "tb-gen",        "label": "TB gen"},
    {"id": "sim",         "workflow": "sim",           "label": "Simulation"},
    {"id": "sim-debug",   "workflow": "sim_debug",     "label": "Sim debug"},
    {"id": "coverage",    "workflow": "coverage",      "label": "Coverage"},
    {"id": "goal-audit",  "workflow": "sim_debug",     "label": "Goal audit"},
]
_PIPELINE_BY_ID       = {s["id"]: s       for s in _PIPELINE_STAGES}
_PIPELINE_BY_WORKFLOW = {s["workflow"]: s for s in _PIPELINE_STAGES}


def get_jobs_state() -> tuple[dict[str, dict[str, Any]], threading.Lock]:
    """Return (_jobs, _jobs_lock) for callers in atlas_ui.py that need
    read access to the job tracker (e.g. /api/session/state)."""
    return _jobs, _jobs_lock


# ── Internal helpers ────────────────────────────────────────────────

def _resolve_worker_url(workflow: str) -> str:
    """Same precedence as core.delegate_runner.HTTPWorkerDelegate."""
    if workflow:
        key = "WORKER_URL_" + workflow.upper().replace("-", "_")
        url = os.environ.get(key)
        if url:
            return url
    return os.environ.get("WORKER_URL_DEFAULT", "http://localhost:8001")


def _default_workflow_prompt(workflow: str, ip: str) -> str:
    prompt_for = {
        "architect":  f"review and update the SoC architecture contract for {ip or 'the whole SoC'}; emit handoff notes for ssot-gen",
        "ssot-gen":   f"refresh SSOT for {ip} from the architect handoff and current SoC context",
        "rtl-gen":    f"regenerate RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml",
        "lint":       f"lint {ip}/rtl/*.sv and fix root-cause errors and warnings",
        "tb-gen":     f"generate or update the testbench for {ip}",
        "sim":        f"run simulation for {ip} and report pass/fail counts",
        "syn":        f"synthesise {ip} and emit gate netlist plus area/timing summary",
        "dft":        f"run DFT checks or scan-insertion preparation for {ip}",
        "sta":        f"run pre-route STA for {ip} using the synthesized netlist and SDC",
        "pnr":        f"run PnR for {ip}, producing routed DEF/netlist/SPEF reports",
        "sta-post":   f"run post-route STA for {ip} using routed netlist and SPEF",
    }
    return prompt_for.get(workflow, f"run {workflow}" + (f" on {ip}" if ip else ""))


def _default_todo_template_for_job(workflow: str, stage_id: str, ip: str) -> str:
    if ip and (workflow == "rtl-gen" or stage_id == "rtl"):
        return "ssot-rtl"
    return ""


def _dispatch_job_to_worker(job: dict[str, Any]) -> None:
    try:
        import urllib.request as _u
        body = {
            "task":     job["prompt"],
            "workflow": job["workflow"],
            "session":  job.get("session", ""),
            "model":    job.get("model", ""),
            "context":  job["prompt"].split("\n\n", 1)[0],
            "sync":     False,
        }
        if job.get("template"):
            body["template"] = job["template"]
        if job.get("ip"):
            body["ip"] = job["ip"]
        payload = json.dumps(body).encode("utf-8")
        req = _u.Request(
            f"{job['worker'].rstrip('/')}/run",
            data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with _u.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        run_id = resp_data.get("run_id", "")
        if not run_id:
            raise RuntimeError(f"worker did not return run_id: {resp_data}")
        with _jobs_lock:
            live = _jobs.get(job["job_id"], job)
            live["run_id"]     = run_id
            live["status"]     = "running"
            live["started_at"] = time.time()
            live["error"]      = ""
    except Exception as e:
        with _jobs_lock:
            live = _jobs.get(job["job_id"], job)
            live["status"]      = "error"
            live["error"]       = f"worker dispatch failed at {job.get('worker')}: {e}"
            live["finished_at"] = time.time()


def _advance_pipeline_from(job: dict[str, Any]) -> None:
    pipeline_id = job.get("pipeline_id") or ""
    if not pipeline_id:
        return
    if job.get("status") in ("error", "cancelled"):
        with _jobs_lock:
            for queued in _jobs.values():
                if queued.get("pipeline_id") == pipeline_id and queued.get("status") == "queued":
                    queued["status"]      = "blocked"
                    queued["error"]       = f"blocked by {job.get('workflow')} {job.get('status')}"
                    queued["finished_at"] = time.time()
        return
    if job.get("status") != "completed":
        return
    next_job = None
    with _jobs_lock:
        candidates = [j for j in _jobs.values()
                      if j.get("pipeline_id") == pipeline_id and j.get("status") == "queued"]
        candidates.sort(key=lambda j: j.get("pipeline_index", 0))
        if candidates and candidates[0].get("depends_on") == job.get("job_id"):
            next_job = candidates[0]
            next_job["status"] = "pending"
    if next_job:
        _dispatch_job_to_worker(next_job)


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in job.items() if not k.startswith("_")}


def _job_artifact_recovery(
    job: dict[str, Any],
    project_root: Path,
) -> tuple[bool, str]:
    """Recover UI job state when an HTTP worker forgot an old run_id.

    Worker runs are in-memory, while Architect state is filesystem-backed.
    If a worker restarts or drops a run, /status/{run_id} returns 404 even
    though the stage may have already produced valid artifacts.  Use the same
    coarse filesystem contract as /api/soc so the web UI does not leave
    completed work blinking as "running" forever.
    """
    ip = str(job.get("ip") or "").strip()
    if not ip or ".." in ip or "/" in ip:
        return False, ""
    ip_dir = project_root / ip
    if not ip_dir.is_dir():
        return False, ""
    stage    = str(job.get("stage_id") or job.get("workflow") or "").strip()
    workflow = str(job.get("workflow") or "").strip()
    if stage == "ssot" or workflow == "ssot-gen":
        ok = (ip_dir / "yaml" / f"{ip}.ssot.yaml").is_file()
        return ok, f"recovered from artifact: {ip}/yaml/{ip}.ssot.yaml"
    if stage == "rtl" or workflow == "rtl-gen":
        filelist  = ip_dir / "list" / f"{ip}.f"
        rtl_dir   = ip_dir / "rtl"
        rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
        return bool(filelist.is_file() and rtl_files), f"recovered from artifact: {ip}/list/{ip}.f"
    if stage == "tb" or workflow == "tb-gen":
        tb_dir = ip_dir / "tb"
        if not tb_dir.is_dir():
            return False, ""
        artifacts = (
            list(tb_dir.rglob("*.py"))
            + list(tb_dir.rglob("*.sv"))
            + list(tb_dir.rglob("*.v"))
        )
        return bool(artifacts), f"recovered from artifact: {ip}/tb"
    if stage == "sim-debug" or workflow == "sim_debug":
        sim_dir   = ip_dir / "sim"
        cov_dir   = ip_dir / "cov"
        artifacts: list = []
        if sim_dir.is_dir():
            artifacts.extend(list(sim_dir.rglob("*.vcd")))
            artifacts.extend(list(sim_dir.rglob("coverage_report.*")))
        if cov_dir.is_dir():
            artifacts.extend(list(cov_dir.rglob("coverage.json")))
            artifacts.extend(list(cov_dir.rglob("toggle.json")))
        return bool(artifacts), f"recovered from artifact: {ip}/sim + {ip}/cov"
    return False, ""


# ── Factory ─────────────────────────────────────────────────────────

def register_jobs_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    normalize_session_name: Callable[[str], str],
) -> None:
    """Mount all /api/job* and /api/jobs* and /api/pipeline/* routes onto *app*.

    project_root and normalize_session_name are passed as callables so the
    routes always see the live values — the --root flag in atlas_ui.main()
    rebinds PROJECT_ROOT after this module is imported.
    """

    def _make_job_record(
        *, workflow: str, ip: str, prompt: str, model: str = "",
        session_name: str = "", stage_id: str = "", pipeline_id: str = "",
        pipeline_index: int = 0, depends_on: str = "",
        worker_override: str = "", auto_start: bool = True, template: str = "",
    ) -> dict[str, Any]:
        pr = project_root()
        stage_id    = stage_id or (_PIPELINE_BY_WORKFLOW.get(workflow, {}).get("id") or workflow)
        template    = template or _default_todo_template_for_job(workflow, stage_id, ip)
        session_name = normalize_session_name(session_name or (f"{ip}/{workflow}" if ip else workflow))
        if not session_name:
            raise ValueError("invalid session namespace")
        scope_path = str((pr / ip).resolve()) if ip else str(pr)
        try:
            rel_scope = str(Path(scope_path).relative_to(pr))
        except Exception:
            rel_scope = ip or "."
        session_dir = pr / ".session" / session_name
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        worker_url = worker_override or _resolve_worker_url(workflow)
        boundary = (
            f"[ATLAS ARCHITECT WORKFLOW CONTEXT]\n"
            f"- ip: {ip or '(soc)'}\n"
            f"- workflow: {workflow}\n"
            f"- stage_id: {stage_id or workflow}\n"
            f"- pipeline_id: {pipeline_id or '(single-job)'}\n"
            f"- session_namespace: .session/{session_name}\n"
            f"- scope_path: {rel_scope}\n"
            f"- write_boundary: only modify files under {rel_scope}/, "
            f"except workflow-owned status/session files under .session/{session_name}/. "
            f"Do not edit other IP directories or unrelated workflows.\n"
            f"- parallelism: assume other IP/workflow jobs may be running; never revert or overwrite their files.\n\n"
        )
        job: dict[str, Any] = {
            "job_id":         uuid.uuid4().hex[:12],
            "run_id":         "",
            "worker":         worker_url,
            "workflow":       workflow,
            "stage_id":       stage_id,
            "template":       template,
            "ip":             ip,
            "model":          model,
            "session":        session_name,
            "session_dir":    session_dir.relative_to(pr).as_posix(),
            "scope_path":     rel_scope,
            "worker_command": (
                f"python src/main.py --serve --port {worker_url.rsplit(':', 1)[-1]}"
                f" --worker-name {workflow} --session {session_name}"
            ),
            "prompt":         boundary + (prompt or _default_workflow_prompt(workflow, ip)),
            "started_at":     time.time() if auto_start else 0.0,
            "status":         "pending" if auto_start else "queued",
            "iterations":     0,
            "files_modified": [],
            "result_summary": "",
            "error":          "",
            "pipeline_id":    pipeline_id,
            "pipeline_index": pipeline_index,
            "depends_on":     depends_on,
            "_last_polled":   0.0,
        }
        with _jobs_lock:
            _jobs[job["job_id"]] = job
        if auto_start:
            _dispatch_job_to_worker(job)
        return job

    # ── /api/job/dispatch ──────────────────────────────────────────

    @app.post("/api/job/dispatch")
    async def api_job_dispatch(request: Request):
        """Dispatch a workflow onto an IP via an HTTP worker.

        Body: `{workflow: 'rtl-gen', ip: 'counter', prompt?: '...',
                model?: '...', session?: 'counter/rtl-gen',
                worker?: 'http://127.0.0.1:8001'}`

        Defaults the prompt to a workflow-specific template so the user
        can just click the block menu without typing.  Returns
        `{job_id, run_id, worker, status: 'queued'}` immediately; the
        frontend polls /api/jobs to track progress.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        workflow        = (body.get("workflow") or "").strip()
        ip              = (body.get("ip")       or "").strip()
        prompt          = (body.get("prompt")   or "").strip()
        model           = (body.get("model")    or "").strip()
        template        = (body.get("template") or "").strip()
        session_raw     = (body.get("session")  or "").strip()
        session_name    = normalize_session_name(session_raw)
        worker_override = (body.get("worker")   or "").strip()
        if not workflow:
            return JSONResponse({"error": "missing 'workflow'"}, status_code=400)
        if not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
            return JSONResponse({"error": f"invalid workflow {workflow!r}"}, status_code=400)
        if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
            return JSONResponse({"error": f"invalid template {template!r}"}, status_code=400)
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
            return JSONResponse({"error": f"invalid model {model!r}"}, status_code=400)
        if session_raw and not session_name:
            return JSONResponse({"error": f"invalid session {session_raw!r}"}, status_code=400)
        if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
            return JSONResponse({"error": f"invalid worker {worker_override!r}"}, status_code=400)

        stage_id = (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
        job = _make_job_record(
            workflow=workflow, ip=ip, prompt=prompt, model=model,
            session_name=session_name, stage_id=stage_id,
            worker_override=worker_override, auto_start=True, template=template,
        )
        if job.get("status") == "error":
            return JSONResponse({"error": job.get("error"), "worker": job.get("worker")}, status_code=502)
        return JSONResponse({
            "ok":             True,
            "job_id":         job["job_id"],
            "run_id":         job["run_id"],
            "worker":         job["worker"],
            "session":        job["session"],
            "session_dir":    job["session_dir"],
            "scope_path":     job["scope_path"],
            "model":          model,
            "worker_command": job["worker_command"],
            "status":         job["status"],
        })

    # ── /api/jobs/dispatch_many ────────────────────────────────────

    @app.post("/api/jobs/dispatch_many")
    async def api_jobs_dispatch_many(request: Request):
        """Dispatch multiple independent jobs in parallel.

        Body:
          `{jobs: [{workflow, ip, prompt?, model?, session?, worker?}, ...]}`

        This is the API shape the Architect/orchestrator should use for
        "run ssot/rtl on these IPs with different models" requests.  Each job
        still keeps its own `.session/<ip>/<workflow>` namespace and write
        boundary; the only shared object is this top-level tracker.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        items = body.get("jobs") if isinstance(body, dict) else None
        if not isinstance(items, list) or not items:
            return JSONResponse({"error": "expected non-empty jobs list"}, status_code=400)
        if len(items) > 32:
            return JSONResponse({"error": "too many jobs; max 32"}, status_code=400)

        created: list = []
        errors:  list = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({"index": idx, "error": "job must be an object"})
                continue
            workflow        = (item.get("workflow") or "").strip()
            ip              = (item.get("ip")       or "").strip()
            prompt          = (item.get("prompt")   or "").strip()
            model           = (item.get("model")    or "").strip()
            template        = (item.get("template") or "").strip()
            session_raw     = (item.get("session")  or "").strip()
            session_name    = normalize_session_name(session_raw)
            worker_override = (item.get("worker")   or "").strip()

            if not workflow or not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
                errors.append({"index": idx, "error": f"invalid workflow {workflow!r}"})
                continue
            if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
                errors.append({"index": idx, "error": f"invalid template {template!r}"})
                continue
            if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
                errors.append({"index": idx, "error": f"invalid ip {ip!r}"})
                continue
            if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
                errors.append({"index": idx, "error": f"invalid model {model!r}"})
                continue
            if session_raw and not session_name:
                errors.append({"index": idx, "error": f"invalid session {session_raw!r}"})
                continue
            if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
                errors.append({"index": idx, "error": f"invalid worker {worker_override!r}"})
                continue

            stage_id = (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=prompt, model=model,
                session_name=session_name, stage_id=stage_id,
                worker_override=worker_override, auto_start=True, template=template,
            )
            created.append(_public_job(job))

        status = 207 if errors else 200
        return JSONResponse(
            {"ok": not errors, "jobs": created, "errors": errors, "count": len(created)},
            status_code=status,
        )

    # ── /api/pipeline/stages ───────────────────────────────────────

    @app.get("/api/pipeline/stages")
    async def api_pipeline_stages():
        return JSONResponse({"stages": _PIPELINE_STAGES})

    # ── /api/pipeline/dispatch ─────────────────────────────────────

    @app.post("/api/pipeline/dispatch")
    async def api_pipeline_dispatch(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        ip         = (body.get("ip")     or "").strip()
        model      = (body.get("model")  or "").strip()
        user_prompt = (body.get("prompt") or "").strip()
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        requested = body.get("stages") or [s["id"] for s in _PIPELINE_STAGES]
        if not isinstance(requested, list) or not requested:
            return JSONResponse({"error": "stages must be a non-empty list"}, status_code=400)
        resolved = []
        for item in requested:
            key   = str(item).strip()
            stage = _PIPELINE_BY_ID.get(key) or _PIPELINE_BY_WORKFLOW.get(key)
            if not stage:
                return JSONResponse({"error": f"unknown pipeline stage {key!r}"}, status_code=400)
            if not any(s["id"] == stage["id"] for s in resolved):
                resolved.append(stage)
        pipeline_id      = uuid.uuid4().hex[:12]
        jobs: list       = []
        previous_job_id  = ""
        for idx, stage in enumerate(resolved):
            workflow     = stage["workflow"]
            stage_prompt = _default_workflow_prompt(workflow, ip)
            if user_prompt:
                stage_prompt += f"\n\n[User pipeline goal]\n{user_prompt}"
            session = f"{ip or 'soc'}/pipeline/{pipeline_id}/{idx + 1:02d}-{workflow}"
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=stage_prompt, model=model,
                session_name=session, stage_id=stage["id"], pipeline_id=pipeline_id,
                pipeline_index=idx, depends_on=previous_job_id,
                auto_start=(idx == 0),
            )
            previous_job_id = job["job_id"]
            jobs.append(_public_job(job))
        return JSONResponse({
            "ok":         True,
            "pipeline_id": pipeline_id,
            "ip":          ip,
            "stages":      resolved,
            "jobs":        jobs,
        })

    # ── /api/jobs ──────────────────────────────────────────────────

    @app.get("/api/jobs")
    async def api_jobs():
        """Aggregate job status across all dispatched workers.

        For each tracked job, poll the worker's /status/{run_id} (with a
        small 1.5s per-job cache to avoid hammering during a 2-second
        frontend poll cycle) and return the merged list.  Sorted by
        started_at descending so the most-recent job is first.
        """
        pr  = project_root()
        out = []
        now = time.time()
        with _jobs_lock:
            snapshot = list(_jobs.values())
        for job in snapshot:
            if job["status"] in ("running",) and (now - job.get("_last_polled", 0)) > 1.5:
                # Poll worker for fresh state.
                try:
                    import urllib.request as _u
                    req = _u.Request(
                        f"{job['worker'].rstrip('/')}/status/{job['run_id']}",
                        method="GET",
                    )
                    with _u.urlopen(req, timeout=5) as resp:
                        s = json.loads(resp.read().decode("utf-8"))
                    job["_last_polled"] = now
                    job["status"]       = s.get("status", job["status"])
                    if isinstance(s.get("iterations"), int):
                        job["iterations"] = s["iterations"]
                    if s.get("status") in ("completed", "error", "cancelled"):
                        # Fetch full result body once on completion.
                        try:
                            req2 = _u.Request(
                                f"{job['worker'].rstrip('/')}/result/{job['run_id']}",
                                method="GET",
                            )
                            with _u.urlopen(req2, timeout=5) as r2:
                                rr = json.loads(r2.read().decode("utf-8"))
                            job["files_modified"] = rr.get("files_modified") or []
                            job["result_summary"] = (rr.get("result") or "")[:600]
                            job["error"]          = rr.get("error") or ""
                            job["finished_at"]    = now
                            if rr.get("execution_time_ms"):
                                job["duration_ms"] = rr["execution_time_ms"]
                        except Exception:
                            pass
                        _advance_pipeline_from(job)
                except Exception as e:
                    recovered, detail = _job_artifact_recovery(job, pr)
                    if recovered:
                        job["status"]         = "completed"
                        job["error"]          = ""
                        job["result_summary"] = detail
                        job["finished_at"]    = now
                        _advance_pipeline_from(job)
                    else:
                        job["error"] = f"poll failed: {e}"
            if job.get("status") in ("completed", "error", "cancelled"):
                _advance_pipeline_from(job)
            out.append(_public_job(job))
        out.sort(key=lambda j: j.get("started_at", 0), reverse=True)
        return JSONResponse({"jobs": out, "count": len(out)})

    # ── /api/job/{job_id}/log ──────────────────────────────────────

    @app.get("/api/job/{job_id}/log")
    async def api_job_log(job_id: str, since: int = 0, tail: int = 0):
        """Proxy a worker run transcript into the Architect chat.

        The frontend knows Atlas job ids, not worker run ids.  Keep that
        mapping server-side so users can click a job/status-grid pill and
        inspect the live ReAct transcript without leaving the Architect view.
        """
        pr = project_root()
        with _jobs_lock:
            job = dict(_jobs.get(job_id) or {})
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)

        def _session_history_log():
            session = normalize_session_name(str(job.get("session") or ""))
            if not session:
                return None
            path = pr / ".session" / session / "conversation.json"
            if not path.is_file():
                return None
            try:
                messages = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None
            if isinstance(messages, dict):
                messages = messages.get("messages") or []
            if not isinstance(messages, list):
                return None
            entries = []
            for i, m in enumerate(messages[-120:]):
                if not isinstance(m, dict):
                    continue
                role    = m.get("role") or ""
                content = str(m.get("content") or "")
                stripped = content.strip()
                if not stripped:
                    continue
                typ = "response"
                if role == "user":
                    if stripped.startswith("Observation:"):
                        typ = "observation"
                    elif stripped.startswith("[Context]"):
                        typ = "context"
                    else:
                        typ = "task"
                elif role == "assistant" and stripped.startswith("Action:"):
                    typ = "action"
                entries.append({
                    "index":     i,
                    "type":      typ,
                    "role":      role,
                    "content":   content,
                    "timestamp": m.get("timestamp") or job.get("finished_at") or job.get("started_at") or 0,
                    "source":    "session",
                })
            if since > 0:
                entries = [e for e in entries if e["index"] >= since]
            if tail > 0:
                entries = entries[-tail:]
            return {
                "run_id":        job.get("run_id") or "",
                "status":        job.get("status") or "unknown",
                "total_entries": len(entries),
                "entries":       entries,
                "source":        "session",
                "session_path":  path.relative_to(pr).as_posix(),
                "job":           {k: v for k, v in job.items() if not k.startswith("_")},
            }

        try:
            import urllib.parse as _p
            import urllib.request as _u
            qs  = _p.urlencode({k: v for k, v in {"since": since, "tail": tail}.items() if v})
            url = f"{job['worker'].rstrip('/')}/log/{job['run_id']}" + (f"?{qs}" if qs else "")
            req = _u.Request(url, method="GET")
            with _u.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            fallback = _session_history_log()
            if fallback is not None:
                fallback["worker_log_error"] = str(e)
                return JSONResponse(fallback)
            return JSONResponse({"error": f"log fetch failed: {e}", "job": job}, status_code=502)
        data["job"] = {k: v for k, v in job.items() if not k.startswith("_")}
        return JSONResponse(data)

    # ── /api/job/{job_id}/cancel ───────────────────────────────────

    @app.post("/api/job/{job_id}/cancel")
    async def api_job_cancel(job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)
        if job["status"] != "running":
            return JSONResponse({"error": f"job already {job['status']}"}, status_code=400)
        try:
            import urllib.request as _u
            req = _u.Request(
                f"{job['worker'].rstrip('/')}/cancel/{job['run_id']}",
                method="POST",
            )
            with _u.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            return JSONResponse({"error": f"cancel failed: {e}"}, status_code=502)
        with _jobs_lock:
            job["status"] = "cancelled"
        return JSONResponse({"ok": True})

    # ── /api/jobs/clear ────────────────────────────────────────────

    @app.post("/api/jobs/clear")
    async def api_jobs_clear():
        """Drop completed/cancelled/failed jobs from the tracker."""
        with _jobs_lock:
            for jid in list(_jobs.keys()):
                if _jobs[jid]["status"] != "running":
                    _jobs.pop(jid, None)
        return JSONResponse({"ok": True})
