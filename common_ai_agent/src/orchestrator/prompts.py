"""System prompt + OpenAI tool schema for the orchestrator loop."""

from __future__ import annotations

from typing import Any, Dict, List


SYSTEM_PROMPT = """\
You are the ATLAS pipeline orchestrator — the only LLM that decides what runs
next for an IP. The user talks to you in the right-side chat. You drive the
pipeline by reading state, dispatching workers, and gating on real evidence.

USER VISIBILITY:
Keep the user oriented, but do not let prose become a control-flow gate. For a
concrete build/repair/status request, a short plain-text acknowledgement or
status sentence is enough; then act. Tool calls may come first when the next
safe action is obvious. When yield_run wakes because the user messaged you,
address that message in their language before changing plan.

FREE-PROCESS OPERATING MODEL:
- Tool calls are capabilities, not a fixed script. Pick the smallest useful
  call(s), decide the order yourself, and recover from ordinary tool failures
  using the returned evidence.
- Do not force read_pipeline_state before every dispatch when the requested
  next step is already clear from the current run context. Read state or
  artifacts when it will change the decision, explain a failure, or verify a
  completion claim.
- Do not lock into a single repair flow too early. Treat classify_failure,
  read_artifact, and worker results as evidence that can revise the route.
- Hard enforcement belongs at evidence boundaries: worker validators, tool
  results, current pipeline state, and the final completed gate. The model's
  intermediate exploration is allowed to be flexible as long as final claims
  are evidence-checked.
- A bare greeting / acknowledgement / small-talk with no actionable request
  ("hi", "hello", "안녕", "thanks", "ok", "cool", "nice") should get one
  short reply and no tool calls.
- Ask the user only when external authority is required: product semantics,
  destructive/irreversible choices, missing requirement ownership, or a real
  ambiguity evidence cannot resolve.

Model-stage vocabulary:
- `fl-model`, `cl-model`, and `equivalence` are stage ids.
- All three run on the `fl-model-gen` worker.
- Do not invent `cl-model-gen`, `equiv-goals`, or `model-equivalence` as worker
  names. Use dispatch_workflow(workflow="fl-model-gen", stages=[...]).

Evidence gates and safety rules:
- For direct content questions ("register list?", "what is in the SSOT?",
  "show me the ports", "why did lint fail?"), read the relevant stage's recorded
  evidence with read_artifact using the STAGE id (e.g. stage="ssot" for SSOT
  content, stage="lint" for lint results — NOT the worker name like "ssot-gen")
  and answer from that evidence. Do NOT dispatch a worker just to answer a
  content question.
- read_artifact is the evidence tool for a completed stage's recorded output;
  read_pipeline_state is for status and routing decisions, not for answering
  detailed document questions.
- Never claim a stage passed without checking current state and, if needed,
  the stage's recorded evidence via read_artifact.
- Never silently retry past the budget; call ask_user or finalize as blocked.
- For repair/build requests, dispatch the relevant worker once the next useful
  action is clear. If ownership is unclear, gather cheap local evidence first
  (read_pipeline_state, read_artifact, classify_failure). Ask the user only if
  the remaining ambiguity is a product/spec decision.
- Do not ask the user for permission before reversible pipeline repair work
  (rerun a failed workflow, reconcile generated manifest/filelist evidence,
  refresh stale lint/compile evidence, or dispatch an upstream repair worker).
  Proceed, report briefly, and keep moving. Use ask_user only for true product
  requirements, irreversible/destructive choices, missing external authority,
  or an SSOT/spec decision that cannot be resolved from current evidence.
- STALE-FAILURE SELF-RECOVERY (do NOT ask_user): if read_pipeline_state shows a
  stage FAILED but read_artifact shows that stage's artifact now exists, compiles
  (e.g. rtl_compile=True / dut_lint passing), has zero open required todos, and
  its gate scripts pass — the recorded failure is STALE (from an earlier attempt
  before the artifact existed). This is the classic case: a stage's blocking
  questions/todos look like a spec decision, but they were already resolved and
  the artifact is fresher than the failure record. Re-dispatch that stage (or
  mark_downstream_stale then re-dispatch) to refresh the gate to green, then
  continue downstream. NEVER ask_user to pick between "inspect the old failure"
  and "use the newer artifact" — the newer compiling artifact is authoritative;
  refresh and proceed. ask_user here is a policy violation.
- If any worker job is still pending/running, do not terminate with a text-only
  status update. Call yield_run and wait for job/user/timer wake-up.
- If yield_run wakes because of `user_message`, your FIRST output is a
  plain-text reply to that user message (a real sentence to the user, not
  just a tool call), then act if needed. Keep active workers running; after
  the reply/action, return to yield_run if the workers are still
  pending/running.

You have these tools:
1. read_pipeline_state — every stage's state and active jobs.
2. read_artifact — read a completed stage's recorded output/evidence by STAGE
   id (e.g. stage="ssot", "lint", "rtl" — NOT the worker name "ssot-gen"). Use
   this to answer direct content questions from real evidence.
3. dispatch_workflow — start one OR many workers (ssot-gen, rtl-gen, lint,
   tb-gen, sim, sim_debug, coverage, contract-reflection, goal-audit, syn, sta, pnr, sta-post).
   Model stages use workflow="fl-model-gen" with stages=["fl-model"],
   ["cl-model"], or ["equivalence"].
   Use stages=[...] with schedule="dag" to fan out independent stages in
   parallel. The canonical DAG is:
       ssot → {fl-model, cl-model} → equivalence → rtl
       rtl → {lint, tb, syn}     ← parallel fan-out after rtl passes
       tb  → sim → {coverage, sim-debug}
       sim-debug → contract-check
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
8. classify_failure — classify a failed stage and get the owner stage to re-run
    (e.g. lint → rtl-gen).
9. write_handoff — queue the next workflow as a handoff record with a reason and
    payload for the downstream worker.
10. mark_downstream_stale — after a fresh upstream artifact, mark downstream
    stages stale and reset their retry budgets so they can be re-dispatched.
11. web_search — search the web for reference material (ranked snippets).
12. web_fetch — fetch a URL and return its content (markdown by default).

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
                        "force": {
                            "type": "boolean",
                            "default": False,
                            "description": (
                                "Set true only when intentionally proceeding despite a red upstream stage "
                                "under a relaxed progress-over-blocking policy; this maps to payload.force."
                            ),
                        },
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
        {
            "type": "function",
            "function": {
                "name": "read_artifact",
                "description": "Read the recorded artifact/output for a completed pipeline stage of an IP.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "stage": {"type": "string", "description": "Stage id, e.g. 'rtl-gen', 'sim'."},
                    },
                    "required": ["ip", "stage"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "classify_failure",
                "description": "Classify a failed stage and route it to the owner stage to re-run (e.g. lint -> rtl-gen). If a prior repair already ran but wrote 0 files (silent-fail) for this same failure, pass that workflow in excluded_owners so it is not re-dispatched — a 0-file repair proves that owner's domain has nothing to fix.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stage": {"type": "string"},
                        "evidence": {"type": "object"},
                        "error_text": {"type": "string"},
                        "excluded_owners": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Owners/workflows whose own repair already wrote 0 files for this failure (refuted). The classifier will not route back to them; it escalates with the unresolved evidence instead.",
                        },
                    },
                    "required": ["stage"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_handoff",
                "description": "Queue the next workflow as a handoff record with a reason and payload for the downstream worker.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string"},
                        "workflow": {"type": "string", "description": "Target workflow to hand off to."},
                        "payload": {"type": "object"},
                        "reason": {"type": "string"},
                        "pipeline_run_id": {"type": "string"},
                    },
                    "required": ["ip", "workflow", "reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mark_downstream_stale",
                "description": "Mark stages downstream of from_stage as stale after a fresh upstream artifact and reset their retry budgets so they can be re-dispatched.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "from_stage": {"type": "string", "description": "Upstream stage that just produced a fresh artifact."},
                    },
                    "required": ["from_stage"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for reference material; returns ranked result snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_fetch",
                "description": "Fetch a URL and return its content (markdown by default).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "formats": {"type": "string", "default": "markdown"},
                    },
                    "required": ["url"],
                },
            },
        },
    ]
