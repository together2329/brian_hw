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
- If any worker job is still pending/running, do not terminate with a text-only
  status update. Call yield_run and wait for job/user/timer wake-up.

You have these tools:
1. read_pipeline_state — every stage's state, jobs, artifacts.
2. dispatch_workflow — start one OR many workers (ssot-gen, rtl-gen, lint,
   tb-gen, sim, sim_debug, coverage, goal-audit, syn, sta, pnr, sta-post).
   Use stages=[...] with schedule="dag" to fan out independent stages in
   parallel. The canonical DAG is:
       ssot → {fl-model, cl-model} → equivalence → rtl
       rtl → {lint, tb, syn}     ← parallel fan-out after rtl passes
       tb  → sim → {coverage, sim-debug}
       syn → {sta, pnr} → sta-post
       all evidence → goal-audit
   Prefer one dispatch_workflow(stages=[...], schedule="dag") over multiple
   separate calls whenever stages are independent.
3. wait_job — non-blocking snapshot of one job. Use this for ACTIVE polling
   when you need a status before deciding anything else this turn.
   For passive waiting after fan-out, prefer yield_run (tool 9) — it sleeps
   the loop until an interrupt arrives (worker complete, user message, timer)
   so you do not burn LLM iterations or hit the 50-step / 30-min cap.
4. read_artifact — read canonical evidence for one stage.
5. classify_failure — owner classification for a failed stage.
6. ask_user — pause the run and surface a question to the user chat.
7. write_handoff — durable queue when no live worker is bound.
8. mark_downstream_stale — invalidate downstream evidence after an upstream change.
9. yield_run — park the run until a watched event fires (job done, user message, timer).
10. import_document — extract text from a PDF or text file into req/ for ssot-gen.
    Call this BEFORE dispatch_workflow(ssot-gen) when the user provides a document path.
    Returns a requirement_source_id to include in the ssot-gen dispatch payload.

End-state contract:
- Call dispatch_workflow with workflow="__final__" and payload={"state": "completed"|
  "blocked"|"error", "reason": "..."} when the run should terminate. The loop
  reads that and updates the orchestrator_run row.
- "completed" means the IP flow is actually done or intentionally stopped with
  evidence. Active worker jobs are not a completed orchestrator run.
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
                    "Dispatch one or many workers in a single call. Pass "
                    "`workflow` for a single stage, or `stages` (list) to "
                    "fan out independent stages in parallel — e.g. "
                    "stages=['lint','tb','syn'] with schedule='dag' after "
                    "rtl-gen passes. Use workflow='__final__' with "
                    "payload.state in {completed,blocked,error} to terminate."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow": {
                            "type": "string",
                            "description": "Single workflow id. Mutually exclusive with `stages`.",
                        },
                        "stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "List of stage ids to dispatch together. "
                                "Use with schedule='dag' for parallel fan-out."
                            ),
                        },
                        "ip": {"type": "string"},
                        "payload": {"type": "object"},
                        "prompt": {
                            "type": "string",
                            "description": "Optional worker-visible requirement/task text. Include the user's concrete goal when dispatching SSOT or repair workers.",
                        },
                        "schedule": {
                            "type": "string",
                            "enum": ["auto", "dag", "serial"],
                            "description": "'dag' = run independents in parallel; 'serial' = strict order.",
                        },
                        "reason": {"type": "string"},
                    },
                    "required": ["ip"],
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
                "name": "yield_run",
                "description": (
                    "Park the run until a watched event fires. Use this AFTER "
                    "fan-out dispatch to stop burning LLM iterations on idle "
                    "polling. The loop wakes on (a) any watched job completing "
                    "via interrupt, (b) the user sending a new chat message, "
                    "or (c) the optional timer expiring."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "wake_on": {
                            "type": "object",
                            "properties": {
                                "job_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Wake when any of these jobs completes.",
                                },
                                "user_message": {
                                    "type": "boolean",
                                    "description": "Wake when the user sends a new chat (default true).",
                                },
                                "after_seconds": {
                                    "type": "number",
                                    "description": "Optional timer wake. Omit for no timer.",
                                },
                            },
                        },
                        "reason": {"type": "string"},
                    },
                    "required": ["wake_on"],
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
        {
            "type": "function",
            "function": {
                "name": "import_document",
                "description": (
                    "Import a PDF or text document as the requirement source for an IP. "
                    "Extracts text, writes req/import_manifest.json and req/source/<ip>.md, "
                    "and returns a requirement_source_id for the ssot-gen dispatch payload. "
                    "Call this BEFORE dispatching ssot-gen when the user provides a PDF path."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {
                            "type": "string",
                            "description": "IP name to import the document for.",
                        },
                        "path": {
                            "type": "string",
                            "description": "Absolute or relative path to the PDF/text file.",
                        },
                    },
                    "required": ["ip", "path"],
                },
            },
        },
    ]
