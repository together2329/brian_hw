# Workflow Long-Term Improvements

Captured 2026-05-14 after the `uart_lite` end-to-end shakedown. The goal is to make the canonical pipeline (`ssot-gen → fl-model-gen → rtl-gen → tb-gen → sim → sim-debug → goal-audit`) **drive an IP to sign-off without an external supervisor**. Today, even on a "simple" UART, the run stalled with 42 open required gates, and a human had to interpret whether they were real defects, derive-tool false negatives, or budget exhaustion. That is the symptom this document targets.

## Operating Principle

The pipeline must terminate in one of three machine-readable states. **No "almost done" allowed.**

| Exit state | Meaning |
|---|---|
| `success` | All required gates closed; downstream stage can proceed |
| `blocked` | A specific blocker exists; the next responsible stage/owner is named |
| `failed`  | Unrecoverable error (tool crash, bad SSOT, etc.) |

Anything in between forces a human to read logs and guess. That is the cost the improvements below remove.

## Evidence from the uart_lite Trial

- 279 derived RTL TODOs, agent closed 237 (85%).
- 42 open. After triage:
  - **30** = `derive_rtl_todos.py` owner-file resolver mapping RX-FSM tasks to `uart_lite_tx_fsm.sv` (false negatives — RTL exists, derive looks in wrong file).
  - **1** = placeholder false positive: a legitimate comment *"// Break detect ... not implemented per SSOT"* triggered the *"not implemented"* regex pattern.
  - **2** = compile / lint reports stale relative to last RTL edit (agent forgot to re-run after final edits).
  - **5** = `function_model` / `cycle_model` evidence patterns derive can't recognize in the LLM-authored RTL.
  - **4** = `rtl_gate.rtl_gen` meta-gates (provenance, owner-structure, dynamic closure) blocked by the above.
- Agent hit `max_iterations=150` and stopped at an interactive `Continue? (y/n)` prompt that was unreachable from stdin pipe. Process now idles forever at 0% CPU.
- SSOT contained the literal word *"optional"* (parity, stop-bit count). RTL preflight emitted `rtl_blocked.json` with `OPTIONAL_BEHAVIOR_POLICY` blocker. The agent silently chose the "parameterize" default and continued, but the blocker file was never cleared.

This is a self-driving workflow failure across **four** layers: tool correctness, agent budget, interactive prompts, and SSOT quality gating. Each layer needs its own fix.

## Prioritized Backlog

| # | Item | Touches | Impact | Est. cost |
|---|---|---|---|---|
| 1 | Derive owner-file resolver + placeholder detector | `workflow/rtl-gen/scripts/derive_rtl_todos.py` | +30 closures on every IP | 0.5 d |
| 2 | Real headless mode + structured exit | `src/main.py`, `core/chat_loop.py` | Enables CI / multi-agent driving | 0.5 d |
| 3 | Self-recovery close-open loop | `workflow/rtl-gen/scripts/close_open_todos.py` (new), `src/workflow_stage_engine.py` | gate=pass rate ↑↑ without human | 1 d |
| 4 | SSOT pre-flight word/policy gate | `workflow/ssot-gen/scripts/check_ssot_disk.sh` | Stop wasting RTL run on bad SSOT | 0.5 d |
| 5 | Post-compression TodoTracker snapshot | `core/run_react_agent_impl.py` (compression hook) | Survives 95% context cliff | 0.5 d |
| 6 | `progress.json` per session | new file written each ReAct iter | Externally observable progress | 0.3 d |
| 7 | Shakedown regression for whole pipeline | `tests/test_shakedown.py` + per-IP `expected.json` | Catches workflow regressions before commits | 1 d |
| 8 | Escalation contract | rtl-gen / fl-model-gen / ssot-gen system prompts | Auto-routable blockers | 0.5 d |

Bundle 1 + 2 + 3 closes the "0 human touches per IP" gap. The rest tighten and harden.

## Item 1 — Derive Tool Correctness

`workflow/rtl-gen/scripts/derive_rtl_todos.py` has two demonstrable defects that surface as false negatives every IP it runs against.

**1a. Owner-file resolver.** Today the resolver appears to use fuzzy matching across all `*.sv` files for evidence lookup. Categories like `fsm.transition`, `fsm.state`, `function_model.precondition` should be locked to the file that the SSOT's `sub_modules[]` manifest names. Fix: resolve `source_ref` → owning sub_module → manifest `file` and search only that file. If the manifest does not name a file, the TODO is not auditable here and must be marked `blocked_on=ssot` rather than `open`.

**1b. Placeholder detector.** The current detector trips on the string `not implemented` anywhere in RTL. The uart_lite case hit a *correct* comment explaining a deliberate SSOT-driven omission. Fix: limit the detector to (a) RTL outside `// ... ` and `/* ... */` comment regions, and (b) require the pattern to neighbor a tokenizable identifier (a real placeholder is usually `assign x = 'x;` or `// TODO ...` next to assignment, not prose). Better: use the pyslang-backed lexer the project already invokes for lint.

**Acceptance test.** Add `tests/test_derive_rtl_todos.py` with two fixtures: one IP with an FSM split across files (must close cleanly), one IP with a legitimate `// not implemented per SSOT` comment (must not raise placeholder failure).

## Item 2 — Headless Mode and Structured Exit

`src/main.py` `chat_loop()` and the `Continue with N more iterations? (y/n)` prompt assume an interactive operator. Two concrete changes:

**2a. `--headless` flag.** When set:
- `Continue? (y/n)` at max_iterations is replaced with a heuristic auto-decision: if `tools_used` grew in the last 10 iterations and `open_required_todos` dropped, auto-extend by 20 iters up to a hard cap (`--max-total-iters`, default 300). Otherwise terminate with `status=max_iters`.
- All `ask_user` calls (already suppressed by `/mode pipeline`) confirmed silenced in headless mode regardless of mode setting.
- `EOFError` on stdin is treated as a normal end-of-input, not a kill signal; the agent finishes whatever ReAct task is in flight first.

**2b. Structured exit JSON.** On termination, write `.omc/state/sessions/<session>/exit.json`:

```json
{
  "status": "success | blocked | failed | max_iters",
  "stage": "rtl-gen",
  "iters_used": 150,
  "tools_used": 199,
  "tokens_uncached": 183000,
  "todos_total": 279,
  "todos_pass": 237,
  "todos_open_required": 42,
  "blockers": [{"id": "RTL-0009", "owner": "derive-tool", "reason": "..."}],
  "next_action": "fix derive_rtl_todos.py placeholder detector"
}
```

Make `_setup_session` write a stub `exit.json` with `status=running` so callers can poll while alive.

**2c. `--prompt-file` instead of stdin pipe.** The current stdin pipe pattern (used in the uart_lite trial) is fragile: appending `exit` kills the agent mid-ReAct, long single-line prompts get visually mangled, and there is no way to inject a second prompt after the first task completes. Replace with `--prompt-file path` that is read once at startup, then chat_loop is bypassed entirely.

## Item 3 — Self-Recovery Close-Open Loop

After the bulk authoring phase, the agent often leaves ≤ 50 open TODOs that are individually narrow and cheaply closable, but it has no scripted reason to revisit them. Add `workflow/rtl-gen/scripts/close_open_todos.py`:

1. Read `rtl_todo_plan.json`, extract `required & status=open`.
2. Group by `category` and `source_ref`.
3. Format a structured prompt — *one batch per group, ≤ 20 items each* — naming the file, the line range, and the criteria text.
4. Spawn a short ReAct loop (max 20 iters, headless mode) with that prompt.
5. After each batch: re-run `derive_rtl_todos.py --audit-rtl`, drop closed items, re-batch.
6. Exit when either: no open items left, or two consecutive batches close nothing.

Wire it into `_run_rtl` in `src/workflow_stage_engine.py`: if first audit comes back with `open_required > 0` and `gate=fail` *and* no blocker requires SSOT repair, auto-invoke this script before returning. Treat the script's own ReAct iters as part of the rtl-gen budget so it cannot grow unboundedly.

## Item 4 — SSOT Pre-Flight Quality Gate

Today's `check_ssot_disk.sh` validates structure (sections present, no literal `TBD`). It does not catch *semantic* gaps that bite downstream. Add these checks before declaring PASS:

- **Moveable wording scan.** Reject literal `optional`, `maybe`, `configurable but`, `if needed`, `TODO`, `to be decided` in SSOT body (case-insensitive, outside `description:` / `pass:` policy strings). Either lock the policy in YAML or list it in `custom.assumptions`.
- **Assumption parity.** If SSOT contains conditional features (`if`, `when`, `mode`, `param.*controls`), `custom.assumptions[]` must be non-empty. Empty assumptions on a conditional IP is a code smell, not a clean SSOT.
- **Quality gate target scale.** Either `quality_gates.rtl_gen.target_scale` is set with positive minima, or `quality_gates.rtl_gen.target_scale_waiver.approved=true` with a non-empty reason.

Failing any of these returns non-zero from the validator and blocks `rtl-gen` from starting. Cheaper than discovering it 15 minutes into an RTL run.

## Item 5 — Post-Compression TodoTracker Snapshot

The uart_lite trial hit context compression at 95% (190 k tokens) on rtl-gen iter 85. The agent then forgot which TODOs were still open — RTL-0009 (placeholder) was likely flagged earlier and dropped by compression. Add a hook in `core/run_react_agent_impl.py` (or wherever `[Compress] triggered` originates):

- Immediately after compression completes, inject a synthetic user message:

```
[TODO STATE SNAPSHOT — autogenerated after compression]
gate.status: fail
open_required: 42 of 279
remaining items (truncate to first 30):
  RTL-0009 (rtl_placeholder_free_evidence): uart_lite_rx_fsm.sv:233 has 'not implemented'
  RTL-0017 (dut_compile freshness): rtl_compile.json older than uart_lite_tx_fsm.sv
  ...
Resume closing these items.
```

The agent then resumes with a fresh, full view of work-in-progress instead of a stale compressed summary.

## Item 6 — `progress.json` per Session

Make the workflow externally monitorable. Each ReAct iter writes:

```
.omc/state/sessions/<session>/progress.json
```

Atomic temp-write + rename. Fields: iter, max_iter, tokens_used_total, tokens_uncached_total, tools_used, todos_total, todos_pass, todos_open_required, last_action_kind, last_file_touched, stage, status, started_at, updated_at.

This lets any external driver — CI job, dashboard, a higher-level Claude orchestrator — poll progress without parsing terminal ANSI logs. Combined with `exit.json` (item 2b), the workflow becomes fully scriptable.

## Item 7 — Shakedown Regression

Pick three reference IPs that exercise the pipeline at different complexities:

- `simple_gpio_lite` — minimal CSR + IO IP (smoke)
- `uart_lite` — single-domain, serial, FSMs, FIFOs (medium)
- `todo_counter_pipe` — already used by the team as a complex CDC example (heavy)

Per IP, commit an `expected.json`:

```json
{
  "ssot_yaml_bytes_range": [60000, 90000],
  "ssot_sections": 36,
  "fl_decomposition_units": [8, 20],
  "fcov_bins_min": 50,
  "rtl_files_min": 5,
  "rtl_compile_errors": 0,
  "rtl_lint_errors": 0,
  "rtl_required_pass_min": 0.90
}
```

`tests/test_shakedown.py` reads the expected file, runs the headless pipeline against the IP (using items 2 + 3 + 6), and asserts. Run in CI on every PR that touches `workflow/**` or `src/workflow_*.py`.

## Item 8 — Escalation Contract

Every workflow's system prompt must require any blocker to be surfaced in one of three forms:

```
[ESCALATE: ssot-gen] yaml_path=<dotted.path> reason=<concrete> required_change=<concrete>
[ESCALATE: tool-fix] tool=<script_path> pattern=<observed false pos/neg> example=<minimal repro>
[ESCALATE: human] decision=<one-line> options=[a, b, c] recommended=<a|b|c> reason=<why>
```

These show up in `exit.json.blockers[]` and become the upstream router's input. Without this contract, blockers today are free-form prose and an external system has no way to act on them.

## Suggested First Cycle

1. Land item 1 (derive tool fixes) with regression test on uart_lite + todo_counter_pipe.
2. Land item 2 (headless + structured exit) so the next runs do not stall on `(y/n)`.
3. Land item 3 (self-recovery loop) so item 1's fix gets fully exercised on the long tail.
4. Re-run uart_lite end-to-end. Expected outcome: `exit.json.status=success` with zero human touches between launching ssot-gen and rtl-gen reporting `gate=pass`.

If that cycle lands clean, the workflow has crossed the line from "useful with supervision" to "self-driving on simple IPs."

## Out of Scope (for Now)

- TB-gen / sim-debug / coverage closure self-recovery — fix the rtl-gen layer first, then mirror the pattern.
- Multi-IP scheduler / parallel runs — premature until single-IP closure is reliable.
- Cost ceiling enforcement — token tracking exists; ceiling is an additional gate that can be layered on top of `progress.json` later.
- Web UI / dashboard — the data is in `progress.json` / `exit.json`; UI is downstream.

## Reference Files

- `doc/ip_workflow_guide.md` — canonical pipeline reference (what should happen).
- `doc/uart_lite_trial_notes.md` — concrete trial log this document is responding to.
- `workflow/COMMON_ENGINE_FLOW.md` — engine ordering authority.
- `workflow/rtl-gen/scripts/derive_rtl_todos.py` — primary target for item 1.
- `src/main.py` + `core/chat_loop.py` — primary target for item 2.
- `src/workflow_stage_engine.py` — wiring point for item 3 and progress emission.
