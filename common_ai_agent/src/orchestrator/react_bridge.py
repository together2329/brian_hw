"""Bridge: orchestrator → core/react_loop.

Phase 3.5 spike. Builds a ``ReactLoopDeps`` that runs the orchestrator on top
of the production ReAct loop, inheriting compression / per-IP context
injection / streaming UI, while keeping orchestrator-specific concerns
(9-schema tool surface, step persistence, yield_run interrupt) in this file.

Key design decisions (from `[[orchestrator-loop-on-react-loop-plan]]`):

- ``available_tools`` is REPLACED — not merged — with exactly 10 orchestrator
  callables (including import_document). yield_run is a separate LLM-visible
  wrapper, not as a ``dispatch_tool``-resolvable callable.
- No ``src.main`` import. Production helpers come from ``core/*`` modules.
- ``orchestrator_inject_fn`` is built with the explicit ``OrchestratorContext``,
  not the env/contextvar-bound legacy factory, so background threads work.
- Step ordering across parallel tool calls is preserved by recording the
  ``step_index`` claim before the LLM-driven dispatch fans out (see
  ``_OrderedStepCollector``).
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from src.orchestrator import tools as orch_tools
from src.orchestrator.budgets import BudgetTracker
from src.orchestrator.classify import classify_failure
from src.orchestrator.prompts import SYSTEM_PROMPT, build_system_prompt, tool_schemas


# ----------------------------------------------------------------------
# Step collector — preserves LLM-call order across parallel dispatches.
# ----------------------------------------------------------------------


class _OrderedStepCollector:
    """Funnels step writes through a single lock so step_index reflects
    LLM-call order even when tool execution runs in parallel threads."""

    def __init__(self, db: Any, run_id: str) -> None:
        self._db = db
        self._run_id = run_id
        self._lock = threading.Lock()

    def append(
        self,
        *,
        tool_name: str,
        args: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        evidence_summary: str = "",
        verdict: str = "ok",
        dispatched_workflow: str = "",
        dispatched_job_id: str = "",
    ) -> Dict[str, Any]:
        with self._lock:
            return self._db.append_orchestrator_step(
                self._run_id,
                tool_name=tool_name,
                decision={"args": args or {}},
                evidence_read={"summary": evidence_summary, "result": result or {}},
                dispatched_workflow=dispatched_workflow,
                dispatched_job_id=dispatched_job_id,
                verdict=verdict,
            )


# ----------------------------------------------------------------------
# Orchestrator-scoped callables for the available_tools registry.
# ----------------------------------------------------------------------


def _coerce_args(args_str: str, pre_parsed_kwargs: Any) -> Dict[str, Any]:
    if isinstance(pre_parsed_kwargs, dict):
        return pre_parsed_kwargs
    if not args_str:
        return {}
    s = args_str.strip()
    if s.startswith("{"):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return {}
    # Best-effort `k="v", k2=1` parse — minimum viable; tests should prefer
    # pre_parsed_kwargs (native tool calls already do this).
    return {}


def _bind_orchestrator_tools(
    *,
    ctx: Any,
    runner: Any,
    db: Any,
    collector: _OrderedStepCollector,
    budgets: BudgetTracker,
) -> Dict[str, Callable]:
    """Return ``{tool_name: callable(args_str, pre_parsed_kwargs=None) -> str}``.

    Each callable adapts our ``(result_dict, evidence_summary)`` tool layer to
    the string-returning interface ``tool_dispatcher.dispatch_tool`` expects,
    and persists one ``orchestrator_steps`` row per invocation.
    """

    def _wrap(name: str, fn: Callable[..., Tuple[Dict[str, Any], str]]):
        def _call(args_str: str = "", pre_parsed_kwargs: Any = None, **kw: Any) -> str:
            # react_loop's tool_dispatcher passes native tool_call arguments
            # directly as **kwargs (not via pre_parsed_kwargs), so capture them
            # here if pre_parsed wasn't explicitly supplied.
            if not pre_parsed_kwargs and kw:
                pre_parsed_kwargs = kw
            args = _coerce_args(args_str, pre_parsed_kwargs)
            try:
                result, summary = fn(**args)
                verdict = "ok" if result.get("ok", True) else "tool_failed"
            except Exception as exc:
                result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
                summary = result["error"]
                verdict = "tool_error"
            collector.append(
                tool_name=name,
                args=args,
                result=result,
                evidence_summary=summary,
                verdict=verdict,
            )
            return summary

        return _call

    def _read_pipeline_state(**kw):
        return orch_tools.read_pipeline_state(
            ip=kw.get("ip", ctx.ip_name),
            include_jobs=bool(kw.get("include_jobs", True)),
        )

    def _dispatch_workflow(**kw):
        workflow = kw.get("workflow", "")
        stages = kw.get("stages") or []
        # __final__ is the orchestrator declaring terminal state, not a real
        # worker dispatch. Honour ``payload.state`` (completed/blocked/paused)
        # so budget exhaustion / human escalation final calls don't collapse
        # to "completed" — preserves the legacy ``OrchestratorLoop.iterate``
        # short-circuit semantics.
        if workflow == "__final__":
            payload = kw.get("payload") or {}
            state = str(payload.get("state") or "completed")
            db.update_orchestrator_run(
                ctx.run_id,
                status=state,
                final_state=state,
                ended=(state != "paused"),
            )
            return (
                {"ok": True, "final_state": state, "reason": payload.get("reason", "")},
                f"finalised: {state}",
            )
        # Check budget for each workflow about to be dispatched. The LLM may
        # call with `workflow="rtl-gen"` or `stages=["rtl","lint","syn"]` —
        # both must consult the tracker before any worker dispatch fires.
        targets = []
        if workflow:
            targets.append(workflow)
        elif stages:
            targets.extend(str(s) for s in stages)
        rejected = []
        for t in targets:
            decision = budgets.attempt(t)
            if not decision["allowed"]:
                rejected.append(decision)
        if rejected:
            err = "; ".join(
                f"{r['workflow']} attempts={r['attempts']} budget={r['budget']}"
                for r in rejected
            )
            result = {
                "ok": False,
                "error": f"retry budget exhausted: {err}",
                "rejected": rejected,
                "budget_state": budgets.snapshot(),
            }
            return result, f"budget exhausted: {err}"
        return orch_tools.dispatch_workflow(
            workflow=workflow,
            ip=kw.get("ip", ctx.ip_name),
            stages=stages or None,
            payload=kw.get("payload") or {},
            prompt=kw.get("prompt", ""),
            schedule=kw.get("schedule", "auto"),
            reason=kw.get("reason", ""),
            orchestrator_run_id=ctx.run_id,
        )

    def _wait_job(**kw):
        return orch_tools.wait_job(kw.get("job_id", ""))

    def _read_artifact(**kw):
        return orch_tools.read_artifact(
            ip=kw.get("ip", ctx.ip_name),
            stage=kw.get("stage", ""),
            project_root=ctx.project_root,
        )

    def _classify_failure(**kw):
        decision = classify_failure(
            kw.get("stage", ""),
            evidence=kw.get("evidence"),
            error_text=kw.get("error_text", ""),
        )
        return decision, json.dumps(decision)

    def _ask_user(**kw):
        return orch_tools.ask_user(
            db=db,
            run_id=ctx.run_id,
            ip_id=ctx.ip_id,
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            question=kw.get("question", ""),
            context=kw.get("context"),
        )

    def _write_handoff(**kw):
        return orch_tools.write_handoff(
            ip=kw.get("ip", ctx.ip_name),
            workflow=kw.get("workflow", ""),
            payload=kw.get("payload") or {},
            reason=kw.get("reason", ""),
            user_id=ctx.user_id,
            session_id=ctx.session_id,
            pipeline_run_id=ctx.run_id,
            orchestrator_run_id=ctx.run_id,
            project_root=ctx.project_root,
        )

    def _mark_downstream_stale(**kw):
        result, summary = orch_tools.mark_downstream_stale(
            db=db,
            ip_id=ctx.ip_id,
            from_stage=kw.get("from_stage", ""),
            run_id=ctx.run_id,
            session_id=ctx.session_id,
        )
        if isinstance(result, dict) and result.get("ok"):
            for stale_stage in result.get("stale") or []:
                stage = str(stale_stage)
                budgets.reset(stage)
                budgets.reset(stage.replace("-", "_"))
                if stage == "tb":
                    budgets.reset("tb-gen")
                elif stage == "sim-debug":
                    budgets.reset("sim_debug")
        return result, summary

    def _import_document(**kw):
        return orch_tools.import_document(
            ip=ctx.ip_name,
            path=kw.get("path", ""),
            project_root=ctx.project_root,
        )

    return {
        "read_pipeline_state":   _wrap("read_pipeline_state",   _read_pipeline_state),
        "dispatch_workflow":     _wrap("dispatch_workflow",     _dispatch_workflow),
        "wait_job":              _wrap("wait_job",              _wait_job),
        "read_artifact":         _wrap("read_artifact",         _read_artifact),
        "classify_failure":      _wrap("classify_failure",      _classify_failure),
        "ask_user":              _wrap("ask_user",              _ask_user),
        "write_handoff":         _wrap("write_handoff",         _write_handoff),
        "mark_downstream_stale": _wrap("mark_downstream_stale", _mark_downstream_stale),
        "import_document":       _wrap("import_document",       _import_document),
    }


# ----------------------------------------------------------------------
# yield_run — Waker-based interrupt, wired in the execute_tool_fn wrapper.
# ----------------------------------------------------------------------


def _make_yield_run_handler(
    *, ctx: Any, runner: Any, db: Any, collector: _OrderedStepCollector
) -> Callable[[Dict[str, Any]], str]:
    def _handle(args: Dict[str, Any]) -> str:
        if runner is None or not hasattr(runner, "register_waker"):
            collector.append(
                tool_name="yield_run", args=args, verdict="no_waker",
                evidence_summary="yielded (no waker registered)",
            )
            return "yielded (no waker)"
        wake_on = args.get("wake_on") or {}
        waker = runner.register_waker(
            run_id=ctx.run_id,
            user_id=ctx.user_id,
            ip_id=ctx.ip_id,
            job_ids=set(str(j) for j in (wake_on.get("job_ids") or [])),
            user_message=bool(wake_on.get("user_message", True)),
            after_seconds=float(wake_on["after_seconds"])
            if wake_on.get("after_seconds")
            else None,
        )
        db.update_orchestrator_run(ctx.run_id, status="yielded")
        try:
            reason = waker.wait()
        finally:
            runner.unregister_waker(ctx.run_id)
        db.update_orchestrator_run(ctx.run_id, status="running")
        collector.append(
            tool_name="yield_run", args=args, verdict=reason,
            evidence_summary=f"woken: {reason}",
        )
        return f"woken: {reason}"

    return _handle


# ----------------------------------------------------------------------
# Orchestrator-scoped build_prompt_fn — embeds our 9 schemas only.
# ----------------------------------------------------------------------


def _make_build_prompt_fn(ctx: Any) -> Callable:
    schemas_json = json.dumps(tool_schemas(), indent=2, sort_keys=True)
    context_header = (
        f"orchestrator_run_id={ctx.run_id}\n"
        f"ip={ctx.ip_name}\n"
        f"user_id={ctx.user_id}\n"
        f"session_id={ctx.session_id}\n"
    )

    def _build_prompt(messages=None, allowed_tools=None, agent_mode=None) -> str:
        body = build_system_prompt(extra_context=context_header)
        return f"{body}\n\n[AVAILABLE_TOOLS]\n{schemas_json}\n[/AVAILABLE_TOOLS]\n"

    return _build_prompt


# ----------------------------------------------------------------------
# orchestrator_inject_fn — ctx-bound variant (no env / contextvar reliance).
# ----------------------------------------------------------------------


def build_orchestrator_inject_fn_for(db: Any, ctx: Any) -> Callable:
    """ctx-bound replacement for core.orchestrator_inject.build_orchestrator_inject_fn.

    Reads IP/session/user directly from ``ctx`` rather than from env or
    contextvar, so background orchestrator threads (where FastAPI's
    contextvars do not propagate) still inject per-IP context every iteration.
    """

    def _inject(messages, agent_mode: str) -> None:
        if not messages or messages[0].get("role") != "system":
            return
        try:
            block = db.summarize_ip_room_context(ctx.ip_id) if ctx.ip_id else None
        except Exception:
            block = None
        if not block:
            return
        # Compact rendering — orchestrator only needs the live IP snapshot,
        # not the full UI bundle.
        head = messages[0]
        sep = (
            f"\n\n<orchestrator-context ip={ctx.ip_name!r}>"
            f"\n{json.dumps(block, ensure_ascii=False, default=str)[:4_000]}"
            "\n</orchestrator-context>"
        )
        content = head.get("content", "")
        if isinstance(content, str):
            head["content"] = content + sep
        elif isinstance(content, list):
            content.append({"type": "text", "text": sep})

    return _inject


# ----------------------------------------------------------------------
# Top-level factory.
# ----------------------------------------------------------------------


@dataclass
class OrchestratorReactBridge:
    """Return value of ``build_orchestrator_deps`` — bundles the deps with
    the artefacts a caller (loop.run wrapper, spike, tests) needs to drive
    them: the orchestrator's available_tools dict, the yield_run handler,
    the step collector, and the per-stage retry budget tracker."""

    deps: Any
    available_tools: Dict[str, Callable]
    yield_run_handler: Callable
    collector: _OrderedStepCollector
    budgets: BudgetTracker


def build_orchestrator_deps(*, ctx: Any, runner: Any, db: Any) -> OrchestratorReactBridge:
    """Construct a ReactLoopDeps scoped to one orchestrator_run.

    Pure factory — does not touch ``src.main``. Caller decides what to do
    with the result (drive ``run_react_agent_impl`` or assert against the
    structure in a spike).
    """
    # Lazy imports keep this module unit-testable without pulling in
    # heavyweight deps (uvicorn, FastAPI, …) at import time.
    import config  # type: ignore
    from core import compressor  # type: ignore
    from core import parallel_executor  # type: ignore
    from core import tool_dispatcher  # type: ignore
    from core.react_loop import ReactLoopDeps  # type: ignore
    from src import llm_client  # type: ignore

    collector = _OrderedStepCollector(db, ctx.run_id)
    budgets = BudgetTracker()
    tool_callables = _bind_orchestrator_tools(
        ctx=ctx, runner=runner, db=db, collector=collector, budgets=budgets,
    )
    yield_run_handler = _make_yield_run_handler(
        ctx=ctx, runner=runner, db=db, collector=collector
    )

    # execute_tool_fn — intercept yield_run before falling through to the
    # production dispatcher. The dispatcher only ever sees the 8 orchestrator
    # callables; generic agent tools (Read, Write, Edit, web_search, …) are
    # not in `tool_callables`, so they're invisible by construction.
    def _execute_tool(
        tool_name: str,
        args_str: str = "",
        *,
        pre_parsed_kwargs: Any = None,
    ) -> str:
        if tool_name == "yield_run":
            args = _coerce_args(args_str, pre_parsed_kwargs)
            return yield_run_handler(args)
        return tool_dispatcher.dispatch_tool(
            tool_name,
            args_str,
            pre_parsed_kwargs=pre_parsed_kwargs,
            available_tools=tool_callables,
        )

    # llm_call_fn — streaming LLM. react_loop iterates the return value as a
    # generator, so we MUST delegate to chat_completion_stream (a generator
    # that updates llm_client module globals with token counts). After the
    # stream exhausts we write one llm_calls row linked to ctx.run_id so the
    # UI/audit trail can attribute LLM spend back to the orchestrator run.
    def _llm_call(messages, stop=None, **_):
        started = time.monotonic()
        schemas = tool_schemas() if getattr(config, "ENABLE_NATIVE_TOOL_CALLS", False) else None
        try:
            for chunk in llm_client.chat_completion_stream(
                messages=messages, stop=stop, tools=schemas,
            ):
                yield chunk
        finally:
            try:
                db.record_llm_call(
                    session_id=ctx.session_id or "",
                    run_id=ctx.run_id,
                    ip_id=ctx.ip_id or "",
                    workflow="orchestrator",
                    model=getattr(config, "MODEL_NAME", "") or "",
                    provider=getattr(config, "API_PROVIDER", "") or "",
                    call_role="orchestrator",
                    tokens_input=int(getattr(llm_client, "last_input_tokens", 0) or 0),
                    tokens_output=int(getattr(llm_client, "last_output_tokens", 0) or 0),
                    cache_read_tokens=int(getattr(llm_client, "last_cache_read_tokens", 0) or 0),
                    cache_write_tokens=int(getattr(llm_client, "last_cache_creation_tokens", 0) or 0),
                    latency_ms=(time.monotonic() - started) * 1000.0,
                    status="ok",
                )
            except Exception:
                # Accounting must not break the LLM call itself.
                pass

    # compress_history requires cfg + llm_call_fn as keyword-only args (see
    # core/compressor.py:1184). react_loop calls deps.compress_fn with just
    # (messages, todo_tracker=...), so we close over the orchestrator cfg
    # and llm_call_fn here.
    def _compress_fn(messages, todo_tracker=None, **kw):
        return compressor.compress_history(
            messages, todo_tracker=todo_tracker,
            cfg=config, llm_call_fn=_llm_call, **kw,
        )

    # Wrap parallel_executor.execute_actions_parallel: react_loop calls
    # ``deps.execute_parallel_fn(actions, tracker, agent_mode=...)`` (2 positional
    # + 1 kwarg) but the underlying implementation needs ``cfg`` + ``execute_tool_fn``
    # bound — same pattern as ``src/main.py:1072``.
    def _execute_parallel(actions, tracker, agent_mode="normal"):
        return parallel_executor.execute_actions_parallel(
            actions,
            tracker=tracker,
            agent_mode=agent_mode,
            cfg=config,
            execute_tool_fn=_execute_tool,
        )

    deps = ReactLoopDeps(
        cfg=config,
        llm_call_fn=_llm_call,
        compress_fn=_compress_fn,
        build_prompt_fn=_make_build_prompt_fn(ctx),
        process_obs_fn=lambda obs, messages, todo_tracker=None, **kw: messages,
        execute_tool_fn=_execute_tool,
        execute_parallel_fn=_execute_parallel,
        save_trajectory_fn=lambda *a, **kw: None,
        show_context_usage_fn=lambda messages: None,
        show_iteration_warning_fn=lambda *a, **kw: "",
        strip_tokens_fn=lambda text: text,
        strip_thinking_fn=lambda text: text,
        parse_todo_fn=lambda text: [],
        detect_completion_fn=lambda text: False,
        get_turn_id_fn=lambda: 0,
        get_llm_usage_fn=lambda: None,
        get_llm_tokens_fn=lambda: (0, 0),
        available_tools=tool_callables,           # REPLACED, not merged.
        orchestrator=None,
        procedural_memory=None,
        graph_lite=None,
        hook_registry=None,
        inject_strategy_fn=None,
        save_snapshot_fn=None,
        load_snapshot_fn=None,
        build_prompt_str_fn=None,
        get_recovery_state_fn=None,
        # yield_run is its own tool. poll_human_input_fn is reserved for the
        # legacy "is human typing mid-stream" path and stays unused here.
        poll_human_input_fn=None,
        orchestrator_inject_fn=build_orchestrator_inject_fn_for(db, ctx),
        esc_check_fn=None,
        esc_start_fn=None,
        esc_stop_fn=None,
        emit_content_fn=None,
        emit_reasoning_fn=None,
        emit_todo_fn=None,
        emit_flush_fn=None,
        emit_token_fn=None,
        emit_tool_fn=None,
        emit_tool_result_fn=None,
    )
    return OrchestratorReactBridge(
        deps=deps,
        available_tools=tool_callables,
        yield_run_handler=yield_run_handler,
        collector=collector,
        budgets=budgets,
    )


# ----------------------------------------------------------------------
# OrchestratorReactLoop — production-grade loop running on react_loop.
# ----------------------------------------------------------------------


class OrchestratorReactLoop:
    """Drives the orchestrator via ``run_react_agent_impl``.

    Replaces ``OrchestratorLoop`` (the custom mini-loop scaffold from Phase
    3). Inherits compression / TodoTracker sync / per-IP injection /
    streaming UI / ESC interrupt from the production ReAct loop.

    Supports an optional ``llm_caller`` for tests — a dict-returning callable
    matching the legacy ``OrchestratorLoop`` shape. The translation layer
    converts the dict into the streaming chunk format ``run_react_agent_impl``
    expects (``("native_tool_calls", [...])`` + ``("finish_reason", ...)``).
    """

    def __init__(
        self,
        db: Any,
        ctx: Any,
        initial_user_message: str = "",
        llm_caller: Optional[Callable] = None,
    ) -> None:
        self.db = db
        self.ctx = ctx
        self._initial_user_message = initial_user_message
        self._llm_caller = llm_caller

    def _active_worker_job_ids(self) -> list[str]:
        """Return live pending/running job ids for this IP, best-effort."""
        try:
            state, _summary = orch_tools.read_pipeline_state(
                ip=self.ctx.ip_name,
                include_jobs=True,
            )
        except Exception:
            return []
        if not isinstance(state, dict):
            return []
        jobs: list[dict[str, Any]] = []
        for key in ("active_jobs", "jobs"):
            value = state.get(key)
            if isinstance(value, list):
                jobs.extend(item for item in value if isinstance(item, dict))
        ids: list[str] = []
        for job in jobs:
            status = str(job.get("status") or "").lower()
            job_id = str(job.get("job_id") or "")
            if job_id and status in {"pending", "running", "queued"} and job_id not in ids:
                ids.append(job_id)
        return ids

    @staticmethod
    def _translate_caller_to_stream(caller, error_sink: list):
        """Convert ``caller(messages, tools) -> dict`` into a streaming
        ``llm_call_fn(messages, stop=None) -> generator`` so legacy test
        scripts that script dict responses can drive ``run_react_agent_impl``
        without modification.

        ``run_react_agent_impl`` catches exceptions from the LLM stream and
        silently breaks the iteration. To surface them as run errors at the
        orchestrator layer, we record raises into ``error_sink`` so the
        outer ``run()`` can promote them to ``RunOutcome(status="error")``.
        """

        def stream(messages, stop=None, **_):
            try:
                reply = caller(messages, tool_schemas())
            except Exception as exc:
                error_sink.append(exc)
                raise
            if isinstance(reply, dict) and reply.get("tool_calls"):
                native = []
                for i, tc in enumerate(reply["tool_calls"]):
                    args = tc.get("arguments")
                    if isinstance(args, dict):
                        args_str = json.dumps(args, ensure_ascii=False)
                    else:
                        args_str = str(args or "{}")
                    native.append({
                        "id": tc.get("id") or f"call_{i}",
                        "name": str(tc.get("name") or ""),
                        "arguments": args_str,
                    })
                yield ("native_tool_calls", native)
                yield ("finish_reason", "tool_calls")
                return
            content = ""
            if isinstance(reply, dict):
                content = str(reply.get("content") or "")
            elif isinstance(reply, str):
                content = reply
            if content:
                yield content
            yield ("finish_reason", "stop")

        return stream

    def run(self, max_steps: int = 50, max_seconds: int = 1800):
        """Drive the orchestrator until terminal. Returns a ``RunOutcome``
        compatible with ``OrchestratorLoop.run``."""
        # Avoid circular import — OrchestratorLoop lives in loop.py and the
        # production runner imports both.
        from src.orchestrator.loop import RunOutcome
        from core.react_loop import run_react_agent_impl
        from lib.iteration_control import IterationTracker

        bridge = build_orchestrator_deps(ctx=self.ctx, runner=self.ctx.runner, db=self.db)

        # Orchestrator-scoped cfg: native tool calls are required.
        # We mutate a local copy of the cfg namespace by wrapping the global
        # config object — production callers that need extra flags can layer
        # on top via ReactLoopDeps.cfg.
        import config as _global_cfg
        import types
        cfg_overrides = {
            "ENABLE_NATIVE_TOOL_CALLS": True,
            # Background orchestrator never asks for human-typed input mid-stream.
            "ENABLE_HUMAN_IN_THE_LOOP": False,
            # The Pipeline Orchestrator owns progress in orchestrator_runs /
            # orchestrator_steps. Do not let the outer Codex session todo
            # tracker reinterpret a valid text-only orchestrator reply as a
            # stalled implementation turn and nudge it into generic tools.
            "ENABLE_TODO_TRACKING": False,
            "EXECUTION_NO_ACTION_GUARD": False,
            # Limit RAG/skill activity — orchestrator owns its own tool surface.
            "ENABLE_SMART_RAG": False,
            "ENABLE_SKILL_SYSTEM": False,
            "DEBUG_MODE": False,
        }
        scoped_cfg = types.SimpleNamespace(**{
            k: getattr(_global_cfg, k, None) for k in dir(_global_cfg)
            if not k.startswith("_")
        })
        for k, v in cfg_overrides.items():
            setattr(scoped_cfg, k, v)
        bridge.deps.cfg = scoped_cfg

        error_sink: list = []
        if self._llm_caller is not None:
            bridge.deps.llm_call_fn = self._translate_caller_to_stream(
                self._llm_caller, error_sink
            )

        tracker = IterationTracker(max_iterations=max_steps)
        prompt_text = bridge.deps.build_prompt_fn(
            messages=[], allowed_tools=set(bridge.available_tools.keys()),
            agent_mode="normal",
        )
        messages = [
            {"role": "system", "content": prompt_text},
        ]
        if self._initial_user_message:
            messages.append({"role": "user", "content": self._initial_user_message})

        while True:
            try:
                run_react_agent_impl(
                    messages, tracker, "orchestrator", bridge.deps,
                    mode="oneshot", preface_enabled=False,
                )
            except Exception as exc:
                self.db.update_orchestrator_run(
                    self.ctx.run_id, status="error",
                    final_state="llm_error", ended=True,
                )
                return RunOutcome(
                    status="error",
                    final_state="llm_error",
                    steps_taken=tracker.current,
                    error=f"{type(exc).__name__}: {exc}",
                )

            # react_loop catches LLM exceptions silently and breaks iteration.
            # Promote them to a run-level error here.
            if error_sink:
                exc = error_sink[0]
                self.db.update_orchestrator_run(
                    self.ctx.run_id, status="error",
                    final_state="llm_error", ended=True,
                )
                return RunOutcome(
                    status="error",
                    final_state="llm_error",
                    steps_taken=tracker.current,
                    error=f"{type(exc).__name__}: {exc}",
                )

            # Derive outcome from the persisted run row.
            run_row = self.db.get_orchestrator_run(self.ctx.run_id)
            if run_row is None:
                return RunOutcome(
                    status="error", final_state="unknown",
                    steps_taken=tracker.current,
                )
            # If the loop terminated via cap exhaustion, react_loop's tracker
            # has already exceeded; mark the run blocked if it's still running.
            if run_row["status"] == "running" and tracker.current >= max_steps:
                self.db.update_orchestrator_run(
                    self.ctx.run_id, status="blocked",
                    final_state="cap_exceeded", ended=True,
                )
                run_row = self.db.get_orchestrator_run(self.ctx.run_id)
                break
            if run_row["status"] == "running":
                active_job_ids = self._active_worker_job_ids()
                if active_job_ids:
                    bridge.yield_run_handler({
                        "wake_on": {
                            "job_ids": active_job_ids,
                            "user_message": True,
                            "after_seconds": 240,
                        },
                        "reason": (
                            "LLM returned a text-only status while worker jobs "
                            "were still active; auto-yielding instead of "
                            "marking the orchestrator run completed."
                        ),
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            "[orchestrator-auto-wake] Worker jobs are still "
                            "active or just woke the loop. Continue the "
                            "evidence-gated pipeline: read_pipeline_state, "
                            "read artifacts for completed stages, dispatch "
                            "next stages, or yield_run again. Do not finalize "
                            "while active jobs remain."
                        ),
                    })
                    continue
                # LLM returned no more tool calls and no live workers remain.
                self.db.update_orchestrator_run(
                    self.ctx.run_id, status="completed",
                    final_state="completed", ended=True,
                )
                run_row = self.db.get_orchestrator_run(self.ctx.run_id)
            break

        return RunOutcome(
            status=run_row["status"],
            final_state=run_row["final_state"],
            steps_taken=tracker.current,
        )

    def append_user_message(self, text: str) -> None:
        """Compatibility shim for the legacy interface — runner.submit_or_attach
        no longer uses this since react_loop reads user messages from the
        DB ``orchestrator_steps`` table directly via the prompt context."""
        # No-op: react_loop is fed messages at construction time. For mid-run
        # user input, the runner appends a step row and the loop sees it on
        # the next iteration via the system prompt's context block.
        return None
