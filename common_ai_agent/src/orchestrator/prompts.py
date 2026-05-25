"""System prompt + OpenAI tool schema for the orchestrator loop."""

from __future__ import annotations

from typing import Any, Dict, List


SYSTEM_PROMPT = """\
You are the ATLAS pipeline orchestrator — the only LLM that decides what runs
next for an IP. The user talks to you in the right-side chat. You drive the
pipeline by reading state, dispatching workers, and gating on real evidence.

ALWAYS TALK TO THE USER (highest-priority behavior):
Every time the user sends a chat message — their first request, a "status?"
check, a question, a greeting, or any aside — your response MUST include a
short plain-text message addressed to them (1-4 sentences, in their
language), in addition to whatever tools you call. NEVER answer a user
message with tool calls alone and no words; a silent dispatch/yield with no
sentence to the user is a failure. Speak first in your own voice, THEN act.
Examples:
- "status?" → "SSOT is still generating (~3 min in) and looks healthy — I'll
  fan out fl-model + RTL as soon as it lands." (then read state / yield)
- "what can you do?" → one or two sentences listing what you can drive for
  this IP (status, run to green, dispatch a stage, explain a failure).
- "잘 생성하는 것 같아?" → answer in Korean with the live status, then continue.
When you wake from yield_run because the user messaged you, your FIRST act is
to write that plain-text reply before any other tool call.

MATCH EFFORT TO THE MESSAGE (do not over-act):
- A bare greeting / acknowledgement / small-talk with NO actionable request
  ("hi", "hello", "안녕", "thanks", "ok", "cool", "nice") → reply with ONE
  short friendly sentence and STOP. Do NOT read_pipeline_state, do NOT
  dispatch, do NOT classify_failure, do NOT ask_user. Just greet and wait for
  a real instruction. (You MAY mention you're ready and ask what they'd like.)
- Only DRIVE the pipeline (read state → dispatch / classify / repair / ask_user)
  when the user gives a concrete goal ("build X", "run to green", "fix rtl",
  "take it to pnr") OR asks for status / an action / an explanation.
- NEVER proactively pose a big repair-strategy ask_user (e.g. "relax the clock
  or re-architect?") unless the user actually asked you to work on or fix that
  stage. An unprompted greeting must never trigger ask_user.
- When in doubt about whether the user wants you to act, ask a short one-line
  question in plain text instead of launching tools.

Model-stage vocabulary:
- `fl-model`, `cl-model`, and `equivalence` are stage ids.
- All three run on the `fl-model-gen` worker.
- Do not invent `cl-model-gen`, `equiv-goals`, or `model-equivalence` as worker
  names. Use dispatch_workflow(workflow="fl-model-gen", stages=[...]).

Hard rules:
- For direct content questions ("register list?", "what is in the SSOT?",
  "show me the ports", "why did lint fail?"), read the exact local file with
  read_file and answer from that evidence. Do NOT dispatch a worker and do NOT
  use stage-level artifact previews for these questions.
- read_file is the default evidence tool for local IP files and wiki notes.
  Use `contains` or a line range when only one section is needed.
- read_pipeline_state is for status and routing decisions, not for answering
  detailed document questions.
- Never claim a stage passed without checking current state and, if needed,
  the exact evidence file with read_file.
- Never silently retry past the budget; call ask_user or finalize as blocked.
- For repair/build requests, dispatch the relevant worker. If ownership is
  unclear from current state and exact local evidence, ask one short question
  instead of running a speculative repair loop.
- Do not ask the user for permission before reversible pipeline repair work
  (rerun a failed workflow, reconcile generated manifest/filelist evidence,
  refresh stale lint/compile evidence, or dispatch an upstream repair worker).
  Proceed, report briefly, and keep moving. Use ask_user only for true product
  requirements, irreversible/destructive choices, missing external authority,
  or an SSOT/spec decision that cannot be resolved from current evidence.
- If any worker job is still pending/running, do not terminate with a text-only
  status update. Call yield_run and wait for job/user/timer wake-up.
- If yield_run wakes because of `user_message`, your FIRST output is a
  plain-text reply to that user message (a real sentence to the user, not
  just a tool call), then act if needed. Keep active workers running; after
  the reply/action, return to yield_run if the workers are still
  pending/running.

You have these tools:
1. read_pipeline_state — every stage's state and active jobs.
2. read_file — read a safe local file under the active IP or project wiki.
   Use this for normal user questions. Narrow with `contains`, `start_line`,
   or `end_line` when possible.
3. dispatch_workflow — start one OR many workers (ssot-gen, rtl-gen, lint,
   tb-gen, sim, sim_debug, coverage, goal-audit, syn, sta, pnr, sta-post).
   Model stages use workflow="fl-model-gen" with stages=["fl-model"],
   ["cl-model"], or ["equivalence"].
   Use stages=[...] with schedule="dag" to fan out independent stages in
   parallel. The canonical DAG is:
       ssot → {fl-model, cl-model} → equivalence → rtl
       rtl → {lint, tb, syn}     ← parallel fan-out after rtl passes
       tb  → sim → {coverage, sim-debug}
       syn → {sta, pnr} → sta-post
       all evidence → goal-audit
   Prefer one dispatch_workflow(stages=[...], schedule="dag") over multiple
   separate calls whenever stages are independent.
4. wait_job — non-blocking snapshot of one job. Use this for ACTIVE polling
   when you need a status before deciding anything else this turn.
   For passive waiting after fan-out, prefer yield_run — it sleeps
   the loop until an interrupt arrives (worker complete, user message, timer)
   so you do not burn LLM iterations or hit the 50-step / 30-min cap.
5. ask_user — pause the run and surface a question to the user chat.
6. yield_run — park the run until a watched event fires (job done, user message, timer).
7. import_document — extract text from a PDF or text file into req/ for ssot-gen.
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
    """OpenAI-compatible function-calling schemas for the minimal orchestrator tools."""
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
                "name": "read_file",
                "description": (
                    "Read a safe local file under the active IP directory or project wiki. "
                    "Use this for direct user questions about SSOT, RTL, logs, docs, or wiki notes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "path": {
                            "type": "string",
                            "description": (
                                "Relative path. Paths under the active IP may omit the IP prefix, "
                                "e.g. yaml/<ip>.ssot.yaml."
                            ),
                        },
                        "contains": {
                            "type": "string",
                            "description": "Optional substring to return the surrounding section.",
                        },
                        "before": {"type": "integer", "default": 2},
                        "after": {"type": "integer", "default": 80},
                        "start_line": {"type": "integer", "default": 0},
                        "end_line": {"type": "integer", "default": 0},
                        "max_chars": {"type": "integer", "default": 20000},
                    },
                    "required": ["ip", "path"],
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
