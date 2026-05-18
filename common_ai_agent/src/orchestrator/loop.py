"""Orchestrator loop engine.

Drives the LLM through one or more iterations of: read context, choose tool,
dispatch, record evidence. Every iteration writes one row to
``orchestrator_steps`` so the loop's history is fully replayable and the UI
can render decisions without re-running the model.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.orchestrator import tools as orch_tools
from src.orchestrator.prompts import build_system_prompt, tool_schemas


FINAL_WORKFLOW = "__final__"


@dataclass
class OrchestratorContext:
    run_id: str
    user_id: str
    ip_id: str
    ip_name: str
    session_id: str = ""
    project_root: Optional[Path] = None


@dataclass
class StepResult:
    tool_name: str
    decision: Dict[str, Any]
    result: Dict[str, Any]
    verdict: str
    terminal: bool = False
    final_state: Optional[str] = None


@dataclass
class RunOutcome:
    status: str
    final_state: Optional[str]
    steps_taken: int
    error: Optional[str] = None


LLMCaller = Callable[[List[Dict[str, Any]], List[Dict[str, Any]]], Dict[str, Any]]


def _default_llm_caller(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Wrap ``call_llm_raw`` so the loop can stay LLM-provider agnostic."""
    from src import llm_client  # local import keeps tests stub-friendly

    raw = llm_client.call_llm_raw(messages=messages, tools=tools, temperature=0.2)
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "tool_calls" in parsed:
                return {"tool_calls": parsed["tool_calls"]}
        except json.JSONDecodeError:
            pass
    return {"content": raw if isinstance(raw, str) else json.dumps(raw)}


class OrchestratorLoop:
    """One LLM-driven control loop bound to a single orchestrator_run row."""

    def __init__(
        self,
        db: Any,
        ctx: OrchestratorContext,
        llm_caller: Optional[LLMCaller] = None,
        initial_user_message: str = "",
    ) -> None:
        self.db = db
        self.ctx = ctx
        self._llm = llm_caller or _default_llm_caller
        self._messages: List[Dict[str, Any]] = [
            {"role": "system", "content": build_system_prompt(self._initial_context())}
        ]
        if initial_user_message:
            self._messages.append({"role": "user", "content": initial_user_message})

    def append_user_message(self, text: str) -> None:
        if text:
            self._messages.append({"role": "user", "content": text})

    def _initial_context(self) -> str:
        return (
            f"orchestrator_run_id={self.ctx.run_id}\n"
            f"ip={self.ctx.ip_name}\n"
            f"user_id={self.ctx.user_id}\n"
            f"session_id={self.ctx.session_id}\n"
        )

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------

    def _dispatch_tool(self, name: str, args: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        ip = args.get("ip") or self.ctx.ip_name
        if name == "read_pipeline_state":
            return orch_tools.read_pipeline_state(
                ip=ip, include_jobs=bool(args.get("include_jobs", True))
            )
        if name == "dispatch_workflow":
            return orch_tools.dispatch_workflow(
                workflow=args.get("workflow", ""),
                ip=ip,
                payload=args.get("payload") or {},
                schedule=args.get("schedule", "auto"),
                reason=args.get("reason", ""),
                orchestrator_run_id=self.ctx.run_id,
            )
        if name == "wait_job":
            return orch_tools.wait_job(args.get("job_id", ""))
        if name == "read_artifact":
            return orch_tools.read_artifact(
                ip=ip,
                stage=args.get("stage", ""),
                project_root=self.ctx.project_root,
            )
        if name == "classify_failure":
            return orch_tools.classify_failure_tool(
                stage=args.get("stage", ""),
                evidence=args.get("evidence"),
                error_text=args.get("error_text", ""),
            )
        if name == "ask_user":
            return orch_tools.ask_user(
                db=self.db,
                run_id=self.ctx.run_id,
                ip_id=self.ctx.ip_id,
                user_id=self.ctx.user_id,
                session_id=self.ctx.session_id,
                question=args.get("question", ""),
                context=args.get("context"),
            )
        if name == "write_handoff":
            return orch_tools.write_handoff(
                ip=ip,
                workflow=args.get("workflow", ""),
                payload=args.get("payload") or {},
                reason=args.get("reason", ""),
                user_id=self.ctx.user_id,
                session_id=self.ctx.session_id,
                pipeline_run_id=self.ctx.run_id,
                orchestrator_run_id=self.ctx.run_id,
                project_root=self.ctx.project_root,
            )
        if name == "mark_downstream_stale":
            return orch_tools.mark_downstream_stale(
                db=self.db,
                ip_id=self.ctx.ip_id,
                from_stage=args.get("from_stage", ""),
                run_id=self.ctx.run_id,
                session_id=self.ctx.session_id,
            )
        return ({"ok": False, "error": f"unknown tool {name!r}"}, f"unknown:{name}")

    # ------------------------------------------------------------------
    # One iteration
    # ------------------------------------------------------------------

    def iterate(self) -> StepResult:
        response = self._llm(self._messages, tool_schemas())
        tool_calls = response.get("tool_calls") or []
        if not tool_calls:
            # No tool call → the model wants to say something. Persist as a
            # finalization step (no dispatch) and terminate as completed.
            text = response.get("content") or ""
            self._messages.append({"role": "assistant", "content": text})
            step = self.db.append_orchestrator_step(
                self.ctx.run_id,
                tool_name="",
                decision={"content": text},
                verdict="final_text",
            )
            return StepResult(
                tool_name="",
                decision={"content": text},
                result={"ok": True, "text": text},
                verdict="final_text",
                terminal=True,
                final_state="completed",
            )

        call = tool_calls[0]
        name = call.get("name") or ""
        raw_args = call.get("arguments")
        if isinstance(raw_args, str):
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {}
        else:
            args = raw_args or {}

        if name == "dispatch_workflow" and args.get("workflow") == FINAL_WORKFLOW:
            payload = args.get("payload") or {}
            final_state = str(payload.get("state") or "completed")
            self.db.append_orchestrator_step(
                self.ctx.run_id,
                tool_name="__final__",
                decision={"args": args},
                verdict=final_state,
            )
            return StepResult(
                tool_name="__final__",
                decision={"args": args},
                result={"ok": True, "final_state": final_state},
                verdict=final_state,
                terminal=True,
                final_state=final_state,
            )

        try:
            result, evidence_summary = self._dispatch_tool(name, args)
            verdict = "ok" if result.get("ok", True) else "tool_failed"
        except Exception as exc:
            result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            evidence_summary = result["error"]
            verdict = "tool_error"

        dispatched_workflow = ""
        dispatched_job_id = ""
        if name == "dispatch_workflow" and isinstance(result, dict):
            dispatched_workflow = args.get("workflow", "")
            jobs = result.get("jobs") or []
            if jobs and isinstance(jobs[0], dict):
                dispatched_job_id = jobs[0].get("job_id", "") or ""

        terminal = name == "ask_user" and result.get("state") == "paused"
        if terminal:
            verdict = "awaiting_user"
        self.db.append_orchestrator_step(
            self.ctx.run_id,
            tool_name=name,
            decision={"args": args},
            evidence_read={"summary": evidence_summary, "result": result},
            dispatched_workflow=dispatched_workflow,
            dispatched_job_id=dispatched_job_id,
            verdict=verdict,
        )
        self._messages.append(
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{"name": name, "arguments": args}],
            }
        )
        self._messages.append(
            {
                "role": "tool",
                "name": name,
                "content": evidence_summary,
            }
        )
        return StepResult(
            tool_name=name,
            decision={"args": args},
            result=result,
            verdict=verdict,
            terminal=terminal,
            final_state="paused" if terminal else None,
        )

    # ------------------------------------------------------------------
    # Multi-iteration run with caps
    # ------------------------------------------------------------------

    def run(self, max_steps: int = 50, max_seconds: int = 1800) -> RunOutcome:
        started = time.monotonic()
        steps = 0
        try:
            while steps < max_steps:
                if time.monotonic() - started > max_seconds:
                    self.db.update_orchestrator_run(
                        self.ctx.run_id,
                        status="blocked",
                        final_state="cap_exceeded",
                        ended=True,
                    )
                    return RunOutcome(
                        status="blocked",
                        final_state="cap_exceeded",
                        steps_taken=steps,
                    )
                step = self.iterate()
                steps += 1
                if step.terminal:
                    final = step.final_state or "completed"
                    new_status = "paused" if final == "paused" else (
                        "error" if final == "error" else (
                            "blocked" if final == "blocked" else "completed"
                        )
                    )
                    self.db.update_orchestrator_run(
                        self.ctx.run_id,
                        status=new_status,
                        final_state=final,
                        ended=(new_status != "paused"),
                    )
                    return RunOutcome(
                        status=new_status, final_state=final, steps_taken=steps
                    )
            self.db.update_orchestrator_run(
                self.ctx.run_id,
                status="blocked",
                final_state="cap_exceeded",
                ended=True,
            )
            return RunOutcome(
                status="blocked", final_state="cap_exceeded", steps_taken=steps
            )
        except Exception as exc:
            self.db.update_orchestrator_run(
                self.ctx.run_id,
                status="error",
                final_state="llm_error",
                ended=True,
            )
            return RunOutcome(
                status="error",
                final_state="llm_error",
                steps_taken=steps,
                error=f"{type(exc).__name__}: {exc}",
            )
