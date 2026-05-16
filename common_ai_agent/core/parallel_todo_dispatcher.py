"""Parallel TODO batch dispatcher for background sub-agent workers."""

from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, wait as wait_futures
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

_CORE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CORE_DIR.parent
_SRC_DIR = _PROJECT_ROOT / "src"
for _p in (_PROJECT_ROOT, _SRC_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

try:
    import config
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from src import config  # type: ignore

from core.delegate_runner import DelegateRunner
from lib.model_pricing import get_pricing


@dataclass(frozen=True)
class WorkerModel:
    requested_model: str
    resolved_model: str
    pricing_model: str
    reason: str = ""


@dataclass
class _Job:
    job_id: str
    root: Path
    requested_worker_count: int
    workers: list[WorkerModel]
    chunks: list[list[dict[str, Any]]]
    futures: list[Future] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    # Per-worker extra runtime overrides (e.g. {"CLAUDE_CLI_TOOLS": "WebSearch,WebFetch"}).
    # Pushed onto the thread-local stack via scoped_runtime_extra() inside
    # _run_worker so a single dispatch can grant tools to claude-cli without
    # mutating process-wide config.
    extra_overrides: dict[str, Any] = field(default_factory=dict)


_JOBS: dict[str, _Job] = {}
_JOBS_LOCK = threading.Lock()
_AVAILABILITY_LOCK = threading.Lock()

_MODEL_ENV_KEYS = (
    "LLM_MODEL_NAME",
    "MODEL_NAME",
    "LLM_ACTIVE_MODEL_NAME",
    "LLM_ACTIVE_BASE_NAME",
    "LLM_ACTIVE_BASE_MODEL",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_PROVIDER",
    "LLM_PROFILE",
    "USE_RESPONSES_API",
    "USE_OPENCODE_OAUTH",
    "OPENCODE_ACCOUNT_ID",
    "CURSOR_AGENT_ENABLE",
    "CURSOR_AGENT_MODEL",
    "CLAUDE_CLI_ENABLE",
    "CLAUDE_CLI_MODEL",
    "ENABLE_NATIVE_TOOL_CALLS",
    "LLM_RUNTIME_MODEL_OVERRIDE",
)
_MODEL_ATTR_KEYS = (
    "BASE_URL",
    "API_KEY",
    "LLM_PROVIDER",
    "MODEL_NAME",
    "USE_RESPONSES_API",
    "USE_OPENCODE_OAUTH",
    "OPENCODE_ACCOUNT_ID",
    "CURSOR_AGENT_ENABLE",
    "CURSOR_AGENT_MODEL",
    "CLAUDE_CLI_ENABLE",
    "CLAUDE_CLI_MODEL",
)


class ParallelTodoDispatcher:
    """Dispatch batches of TODOs to bounded background sub-agent workers."""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root or os.getcwd()).resolve()

    def dispatch(
        self,
        todos: Iterable[Any],
        max_workers: int = 3,
        models: list[str] | None = None,
        claude_tools: str | None = None,
        extra_overrides: dict[str, Any] | None = None,
    ) -> str:
        normalized = self._normalize_todos(todos)
        requested_worker_count = max(1, int(max_workers or 1))
        workers = self._resolve_workers(
            requested_worker_count=requested_worker_count,
            explicit_models=models,
            todo_count=len(normalized),
        )

        job_id = f"ptd_{uuid.uuid4().hex[:10]}"
        job_root = self.project_root / ".workers" / job_id
        job_root.mkdir(parents=True, exist_ok=True)

        chunks = self._round_robin_chunks(normalized, len(workers))

        # Compose per-job runtime overrides. `claude_tools` is a shortcut
        # for CLAUDE_CLI_TOOLS (e.g. "WebSearch,WebFetch") which the
        # claude_cli_backend reads via getattr(config, "CLAUDE_CLI_TOOLS", "").
        # When tools are granted we also auto-flip CLAUDE_CLI_PERMISSION_MODE
        # to "bypassPermissions" so headless workers don't stall on
        # confirm-each-tool prompts; if the caller wants stricter
        # behaviour they can override that explicitly via extra_overrides.
        # Generic extra_overrides lets the caller pass anything else in
        # _THREAD_RUNTIME_KEYS for the worker thread to see.
        composed_overrides: dict[str, Any] = {}
        if claude_tools:
            composed_overrides["CLAUDE_CLI_TOOLS"] = str(claude_tools)
            composed_overrides["CLAUDE_CLI_PERMISSION_MODE"] = "bypassPermissions"
        if extra_overrides:
            composed_overrides.update({str(k): v for k, v in extra_overrides.items() if k})

        job = _Job(
            job_id=job_id,
            root=job_root,
            requested_worker_count=(len(models) if models else requested_worker_count),
            workers=workers,
            chunks=chunks,
            extra_overrides=composed_overrides,
        )

        if workers:
            executor = ThreadPoolExecutor(max_workers=len(workers), thread_name_prefix=f"{job_id}_worker")
            for worker_idx, worker in enumerate(workers):
                future = executor.submit(self._run_worker, job, worker_idx, worker, chunks[worker_idx])
                job.futures.append(future)
            executor.shutdown(wait=False)

        self._write_manifest(job, normalized)
        with _JOBS_LOCK:
            _JOBS[job_id] = job
        return job_id

    def wait(self, job_id: str, timeout_s: int = 1800) -> dict[str, Any]:
        with _JOBS_LOCK:
            job = _JOBS.get(job_id)
        if job is None:
            return {"job_id": job_id, "status": "error", "error": "job not found"}

        if job.futures:
            done, not_done = wait_futures(job.futures, timeout=max(0, int(timeout_s or 0)))
            for future in done:
                try:
                    future.result()
                except Exception:
                    pass
            for future in not_done:
                future.cancel()
        return self._aggregate(job)

    def _resolve_workers(
        self,
        requested_worker_count: int,
        explicit_models: list[str] | None,
        todo_count: int,
    ) -> list[WorkerModel]:
        if todo_count <= 0:
            return []
        if explicit_models:
            selected = [m for m in explicit_models if str(m or "").strip()]
            limit = len(selected)
        else:
            selected = self._available_models()
            limit = requested_worker_count
        workers: list[WorkerModel] = []
        for model in selected[: min(limit, todo_count)]:
            if isinstance(model, WorkerModel):
                workers.append(model)
            else:
                requested = str(model).strip()
                workers.append(
                    WorkerModel(
                        requested_model=requested,
                        resolved_model=self._resolved_model_name(requested),
                        pricing_model=self._resolved_model_name(requested),
                    )
                )
        return workers

    def _available_models(self) -> list[WorkerModel]:
        candidates = [
            "cursor-cli",
            "claude-cli",
            "gpt-5.3-codex",
            "glm-5.1",
            "deepseek-v4-pro",
        ]
        candidates.extend(self._kimi_candidates())
        candidates.extend(self._profile_candidates())

        seen: set[str] = set()
        available: list[WorkerModel] = []
        for requested in candidates:
            key = requested.lower()
            if not requested or key in seen:
                continue
            seen.add(key)
            reason = self._availability_reason(requested)
            if reason:
                continue
            resolved = self._resolved_model_name(requested)
            available.append(
                WorkerModel(
                    requested_model=requested,
                    resolved_model=resolved,
                    pricing_model=resolved,
                    reason="",
                )
            )
        available.sort(key=self._price_score)
        return available

    def _availability_reason(self, model: str) -> str:
        with _AVAILABILITY_LOCK:
            attr_snapshot = {k: getattr(config, k, None) for k in _MODEL_ATTR_KEYS}
            env_snapshot = {k: os.environ.get(k) for k in _MODEL_ENV_KEYS}
            try:
                try:
                    from src.headless_workflow import RealLLMProvider
                except ModuleNotFoundError:
                    from headless_workflow import RealLLMProvider  # type: ignore
                reason = RealLLMProvider().available_reason(model)
            except Exception as exc:
                reason = str(exc)
            finally:
                for key, value in attr_snapshot.items():
                    setattr(config, key, value)
                for key, value in env_snapshot.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        if reason == "ATLAS_RUN_REAL_LLM_TDD=1 is not set":
            return self._lightweight_availability_reason(model)
        return reason

    def _lightweight_availability_reason(self, model: str) -> str:
        requested = (model or "").strip()
        low = requested.lower()
        if getattr(config, "is_cli_backend_model", lambda _name: False)(requested):
            if low.startswith("cursor") and not shutil.which("cursor-agent"):
                return "cursor-agent not found in PATH"
            if low.startswith("claude") and not shutil.which("claude"):
                return "claude not found in PATH"
            return ""
        if config.get_profile(requested):
            profile = config.get_profile(requested)
            return "" if profile.get("api_key") or profile.get("base_url") else f"profile {requested} has no API settings"
        profile_name = getattr(config, "_profile_name_for_model", lambda _m: "")(requested)
        if profile_name:
            profile = config.get_profile(profile_name)
            return "" if profile.get("api_key") or profile.get("base_url") else f"profile {profile_name} has no API settings"
        if low.startswith("openrouter/"):
            return "" if os.getenv("OPENROUTER_API_KEY") else "OPENROUTER_API_KEY is not set"
        if low.startswith("zai/") or low.startswith("glm"):
            return "" if (os.getenv("ZAI_API_KEY") or os.getenv("PROFILE_glm_API_KEY")) else "ZAI_API_KEY is not set"
        if low.startswith("deepseek"):
            return "" if (os.getenv("PROFILE_deepseek_API_KEY") or os.getenv("LLM_API_KEY")) else "deepseek API key is not set"
        if low.startswith("kimi"):
            return "" if (os.getenv("PROFILE_kimi_API_KEY") or os.getenv("KIMI_API_KEY")) else "kimi API key is not set"
        if low.startswith("gpt-5") or ("gpt" in low and "codex" in low):
            try:
                from src.opencode_backend import get_credentials
                cred = get_credentials("openai")
            except Exception:
                cred = None
            return "" if (cred and cred.get("access")) or os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY") else "no OpenAI credential found"
        return "" if os.getenv("LLM_API_KEY") else "LLM_API_KEY is not set"

    def _resolved_model_name(self, requested: str) -> str:
        try:
            with config.scoped_model_runtime(requested):
                return str(getattr(config, "MODEL_NAME", requested) or requested)
        except Exception:
            return requested

    def _price_score(self, worker: WorkerModel) -> tuple[float, str]:
        if worker.resolved_model in ("cursor-cli", "claude-cli"):
            return (0.0, worker.requested_model)
        pricing = get_pricing(worker.pricing_model)
        if pricing is None:
            return (1_000_000.0, worker.requested_model)
        return (float(pricing.input) + float(pricing.output), worker.requested_model)

    def _kimi_candidates(self) -> list[str]:
        candidates = []
        for profile_name in getattr(config, "list_profiles", lambda: [])():
            profile = config.get_profile(profile_name)
            model = str(profile.get("model") or "")
            if model.lower().startswith("kimi"):
                candidates.append(profile_name)
        return candidates or ["kimi"]

    def _profile_candidates(self) -> list[str]:
        out = []
        for profile_name in getattr(config, "list_profiles", lambda: [])():
            out.append(profile_name)
        return out

    def _run_worker(self, job: _Job, worker_idx: int, worker: WorkerModel, chunk: list[dict[str, Any]]) -> dict[str, Any]:
        worker_dir = job.root / str(worker_idx)
        worker_dir.mkdir(parents=True, exist_ok=True)
        result_path = worker_dir / "result.json"
        started_at = time.time()
        payload: dict[str, Any] = {
            "job_id": job.job_id,
            "worker_idx": worker_idx,
            "model": worker.resolved_model,
            "requested_model": worker.requested_model,
            "status": "running",
            "todos_assigned": chunk,
            "todos_done": [],
            "result": "",
            "error": "",
            "started_at": started_at,
            "completed_at": None,
        }
        self._write_json(result_path, payload)
        try:
            prompt = self._build_chunk_prompt(job.job_id, worker_idx, chunk)
            # scoped_model_runtime activates the per-worker provider
            # (CLAUDE_CLI_ENABLE, MODEL_NAME, BASE_URL, API_KEY, ...).
            # scoped_runtime_extra pushes any additional per-job overrides
            # on top — e.g. CLAUDE_CLI_TOOLS="WebSearch,WebFetch" so the
            # claude-cli worker can actually browse the web instead of
            # falling back to its knowledge cutoff.
            with config.scoped_model_runtime(worker.requested_model), \
                 config.scoped_runtime_extra(job.extra_overrides):
                output = DelegateRunner(project_root=self.project_root).run(
                    backend="sub-agent",
                    task=prompt,
                    context=f"parallel_todo_dispatch job_id={job.job_id} worker_idx={worker_idx}",
                    model_override=worker.resolved_model,
                )
            payload.update({
                "status": "completed",
                "todos_done": [todo.get("id") or todo.get("index") for todo in chunk],
                "result": output,
                "completed_at": time.time(),
                "duration_s": time.time() - started_at,
            })
        except Exception as exc:
            payload.update({
                "status": "error",
                "error": str(exc),
                "completed_at": time.time(),
                "duration_s": time.time() - started_at,
            })
        self._write_json(result_path, payload)
        return payload

    def _build_chunk_prompt(self, job_id: str, worker_idx: int, chunk: list[dict[str, Any]]) -> str:
        return (
            "You are a parallel TODO worker.\n"
            f"Job: {job_id}\n"
            f"Worker index: {worker_idx}\n\n"
            "Work only on the TODO items assigned below. Decide your internal order "
            "and use available tools as needed. Return a concise result with DONE, "
            "FAILED, and evidence for each assigned item.\n\n"
            "Assigned TODOs:\n"
            f"{json.dumps(chunk, ensure_ascii=False, indent=2)}"
        )

    def _write_manifest(self, job: _Job, todos: list[dict[str, Any]]) -> None:
        self._write_json(
            job.root / "manifest.json",
            {
                "job_id": job.job_id,
                "requested_worker_count": job.requested_worker_count,
                "worker_count": len(job.workers),
                "models": [worker.__dict__ for worker in job.workers],
                "todos": todos,
                "chunks": job.chunks,
                "created_at": job.created_at,
            },
        )

    def _aggregate(self, job: _Job) -> dict[str, Any]:
        workers = []
        running = 0
        for idx, worker in enumerate(job.workers):
            result_path = job.root / str(idx) / "result.json"
            if result_path.is_file():
                try:
                    data = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    data = {
                        "worker_idx": idx,
                        "model": worker.resolved_model,
                        "requested_model": worker.requested_model,
                        "status": "error",
                        "error": f"cannot read result.json: {exc}",
                    }
            else:
                data = {
                    "worker_idx": idx,
                    "model": worker.resolved_model,
                    "requested_model": worker.requested_model,
                    "status": "running",
                    "todos_assigned": job.chunks[idx] if idx < len(job.chunks) else [],
                }
            if data.get("status") == "running":
                running += 1
            workers.append(data)

        completed = sum(1 for w in workers if w.get("status") == "completed")
        failed = sum(1 for w in workers if w.get("status") == "error")
        timed_out = running > 0
        if not job.workers:
            status = "blocked"
        elif timed_out:
            status = "timeout"
        elif failed:
            status = "error" if failed == len(workers) else "partial_error"
        elif len(workers) < job.requested_worker_count:
            status = "partial"
        else:
            status = "completed"

        return {
            "job_id": job.job_id,
            "status": status,
            "requested_worker_count": job.requested_worker_count,
            "worker_count": len(job.workers),
            "completed_workers": completed,
            "failed_workers": failed,
            "running_workers": running,
            "result_dir": str(job.root),
            "todos_assigned": sum(len(chunk) for chunk in job.chunks),
            "todos_done": [
                todo
                for worker in workers
                for todo in (worker.get("todos_done") or [])
            ],
            "workers": workers,
        }

    def _round_robin_chunks(self, todos: list[dict[str, Any]], worker_count: int) -> list[list[dict[str, Any]]]:
        if worker_count <= 0:
            return []
        chunks = [[] for _ in range(worker_count)]
        for idx, todo in enumerate(todos):
            chunks[idx % worker_count].append(todo)
        return chunks

    def _normalize_todos(self, todos: Iterable[Any]) -> list[dict[str, Any]]:
        if todos is None:
            return []
        raw: Any = todos
        if isinstance(raw, str):
            text = raw.strip()
            if not text:
                return []
            try:
                raw = json.loads(text)
            except json.JSONDecodeError:
                raw = [line.strip(" -\t") for line in text.splitlines() if line.strip()]
        if isinstance(raw, dict):
            raw = raw.get("todos") or raw.get("items") or [raw]
        normalized = []
        for idx, item in enumerate(list(raw)):
            if isinstance(item, dict):
                content = item.get("content") or item.get("text") or item.get("title") or item.get("id") or str(item)
                todo_id = item.get("id") or item.get("todo_id") or f"todo-{idx + 1}"
                normalized.append({"index": idx, "id": todo_id, "content": str(content), "raw": item})
            else:
                normalized.append({"index": idx, "id": f"todo-{idx + 1}", "content": str(item)})
        return normalized

    def _write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
