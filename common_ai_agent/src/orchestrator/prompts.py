"""System prompt + OpenAI tool schema for the orchestrator loop."""

from __future__ import annotations

from typing import Any, Dict, List


SYSTEM_PROMPT = """\
You are the ATLAS pipeline orchestrator — the only LLM that decides what runs
next for an IP. The user talks to you in the right-side chat. You drive the
pipeline by reading state, dispatching workers, and gating on real evidence.

Hard rules:
- Never claim a stage passed without fresh artifact evidence (use read_artifact).
- Never silently retry past the budget; call ask_user or finalize as blocked.
- Never invent owner classifications — call classify_failure to map failures.
- If no worker is available for a workflow, use write_handoff (durable queue).
- When upstream artifacts change, call mark_downstream_stale before re-dispatch.

You have these tools:
1. read_pipeline_state — every stage's state, jobs, artifacts.
2. dispatch_workflow — start a worker (ssot-gen, rtl-gen, lint, tb-gen, sim,
   sim_debug, coverage, goal-audit, syn, sta, pnr, sta-post).
3. wait_job — non-blocking snapshot. Call this once per loop iteration to
   check on a running job; do not block waiting.
4. read_artifact — read canonical evidence for one stage.
5. classify_failure — owner classification for a failed stage.
6. ask_user — pause the run and surface a question to the user chat.
7. write_handoff — durable queue when no live worker is bound.
8. mark_downstream_stale — invalidate downstream evidence after an upstream change.

End-state contract:
- Call dispatch_workflow with workflow="__final__" and payload={"state": "completed"|
  "blocked"|"error", "reason": "..."} when the run should terminate. The loop
  reads that and updates the orchestrator_run row.
"""


def build_system_prompt(extra_context: str = "") -> str:
    body = SYSTEM_PROMPT
    if extra_context:
        body = body + "\n\n[CONTEXT]\n" + extra_context
    return body


def tool_schemas() -> List[Dict[str, Any]]:
    """OpenAI-compatible function-calling schemas for the 8 orchestrator tools."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_pipeline_state",
                "description": "Read current pipeline state for an IP (stages, jobs, artifacts).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "include_jobs": {"type": "boolean", "default": True},
                    },
                    "required": ["ip"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "dispatch_workflow",
                "description": (
                    "Dispatch a worker for a workflow. Use workflow='__final__' "
                    "to terminate the run."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow": {"type": "string"},
                        "ip": {"type": "string"},
                        "payload": {"type": "object"},
                        "schedule": {"type": "string", "enum": ["auto", "dag", "serial"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["workflow", "ip"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "wait_job",
                "description": "Snapshot a job's current status (non-blocking).",
                "parameters": {
                    "type": "object",
                    "properties": {"job_id": {"type": "string"}},
                    "required": ["job_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "read_artifact",
                "description": "Read canonical evidence files for a stage.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "stage": {"type": "string"},
                    },
                    "required": ["ip", "stage"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "classify_failure",
                "description": "Map a failed stage + evidence to an owner and repair workflow.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string"},
                        "evidence": {"type": "object"},
                        "error_text": {"type": "string"},
                    },
                    "required": ["stage"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "ask_user",
                "description": "Pause the run and ask the user a question in the chat stream.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "context": {"type": "object"},
                    },
                    "required": ["question"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_handoff",
                "description": "Enqueue a durable handoff JSON when no live worker is bound.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow": {"type": "string"},
                        "ip": {"type": "string"},
                        "payload": {"type": "object"},
                        "reason": {"type": "string"},
                    },
                    "required": ["workflow", "ip", "reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mark_downstream_stale",
                "description": "Mark downstream stages stale after an upstream artifact change.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "from_stage": {"type": "string"},
                    },
                    "required": ["ip", "from_stage"],
                },
            },
        },
    ]
