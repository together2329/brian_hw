# arm_m0_min CPU Handoff Approval README Status

Current project-level entry point for `arm_m0_min/README.md`, CPU handoff,
approval, `req` signoff state, and the `approve_locked_scope` human decision.
Use this page when an agent or human asks for "cpu approval req",
"arm m0 handoff", or "readme cpu" from the project wiki instead of the
IP-local wiki.

Related: [[arm-m0-min-pipeline-run]] · [[human-review-and-escalation]] ·
[[golden-todo-evidence]] · [[rtl-version-run-history]]

## Current State

- The generated CPU evidence is present under `arm_m0_min/`: SSOT, FL model,
  cycle model, RTL, filelist, cocotb TB, scoreboard, FL-vs-RTL compare,
  coverage, and review packets.
- The current real final audit is green:
  `status=pass passed=16/16 blockers=none`.
- The human-owned requirement approval was promoted into `arm_m0_min/req/`.
- Function/cycle coverage is closed by scoreboard-backed RTL observations
  (`19/19` function bins and `17/17` cycle bins). The aggregate
  `cov/coverage.json` status can still read `blocked` because structural
  line/branch instrumentation is not part of this pre-approval signoff packet.
- The review path starts at `arm_m0_min/README.md`, then
  `arm_m0_min/doc/arm_m0_min_user_handoff.md`, then
  `arm_m0_min/review/approval_request.md`.
- For tool-driven completion checks, use the machine-readable map at
  `arm_m0_min/review/prompt_to_artifact_checklist.json`.
- To validate that map against current artifacts, run
  `python3 workflow/req-gen/scripts/audit_prompt_to_artifact_checklist.py arm_m0_min --root . --json`.
  The correct post-approval result is `status=pass`, `completion_ready=true`,
  and no blocked items.
- The accepted human decision text was `approve_locked_scope`; promotion wrote
  the approved requirement and approval manifest.

## Why This Page Exists

The IP-local wiki already finds the handoff well, but project-level queries were
only finding `doc/wiki/log.md` or no page at all. This page makes the current
CPU approval state discoverable from the normal project wiki entry point without
rewriting any `arm_m0_min/req/` artifact.

## Verification

Known current validation for this handoff state:

- IP-local `wiki_query(ip="arm_m0_min", topic="CPU handoff approval req")`
  returns the IP wiki index before log entries.
- Project-level `wiki_query(topic="cpu approval req")` should return this page.
- Project-level `wiki_query(topic="arm m0 handoff")` should return this page.
- Project-level `wiki_query(topic="readme cpu")` should return this page.
- `/api/pipeline/state?ip=arm_m0_min` should expose no open review decisions
  and `goal-audit` as passed.
- `python3 workflow/wiki/build_graph.py --check` must stay at
  `broken_refs=0`.
- Latest focused approval/audit/wiki/API regression passed in the latest
  verification run.
- Real approval promotion wrote `arm_m0_min/req/arm_m0_min_requirements.md`
  and `arm_m0_min/req/approval_manifest.json`.
- Prompt-to-artifact checklist audit now passes with `completion_ready=true`.
