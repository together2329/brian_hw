# Multi-IP Audit Findings (2026-05-15)

Ran `derive_rtl_todos.py --audit-rtl` across 6 IPs already on disk to surface
recurring weaknesses in the canonical pipeline. Goal: identify workflow-level
fixes that would lift closure rate across all IPs, not just uart_lite.

## Closure measurements

| IP | SSOT | RTL files | TODOs | Pass | Open | Pass rate |
|---|---|---|---|---|---|---|
| timer            |  24 KB | 1 | 104 | 102 | 2 | 98.1% |
| dma              |   9 KB | 1 | 105 | 103 | 2 | 98.1% |
| simple_gpio_lite |  28 KB | 2 | 171 | 161 | 10 | 94.2% |
| uart_lite        |  69 KB | 8 | 286 | 279 | 7 | 97.6% |
| todo_counter_pipe|  77 KB | 4 | 279 | 275 | 4 | 98.6% |
| cortex_m0lite    |  65 KB | 8 | 189 | 174 | 15 | 92.1% |

All 6 IPs end with `gate=fail`. The interesting question is *which gates*.

## Open-item taxonomy (across all 6 IPs)

| Open ID | Category | IPs hit | Notes |
|---|---|---|---|
| RTL-0006 | `rtl_gate.rtl_gen / common_ai_agent_authoring` | 6/6 | Provenance file missing or has wrong `type` |
| RTL-0007 | `rtl_gate.rtl_gen / static_rtl_evidence` | 3/6 | derive owner-file lookup misses evidence terms |
| RTL-0009 | `rtl_gate.rtl_gen / rtl_placeholder_free_evidence` | 1/6 | gpio: "not implemented" comment-style false positives |
| RTL-0015 | `rtl_gate.rtl_gen / manifest_signal_flow_evidence` | 2/6 | child port output not threaded to top |
| RTL-0016 | `rtl_gate.rtl_gen / manifest_connection_contract_evidence` | 1/6 | cortex: 31 issues |
| RTL-0017 | `rtl_gate.rtl_gen / dut_compile` | 1/6 | compile.json older than RTL source mtime |
| RTL-0018 | `rtl_gate.rtl_gen / dut_lint` | 1/6 | warnings > 0 (no errors) |
| RTL-0019 | `rtl_gate.rtl_gen / dynamic_todo_closure` | 6/6 | cascade — closes when others close |
| RTL-0020 | `rtl_gate.rtl_gen / golden_authority_artifacts` | 2/6 | authority.json + model_signature.json + equivalence_goals.json |
| RTL-0023 | `rtl_gate.rtl_gen / cycle_model_artifacts` | 1/6 | model/cycle_model.py absent |
| RTL-0024 | `rtl_gate.rtl_gen / protocol_assertion_evidence` | 1/6 | verify/protocol_assertions.sva absent |
| RTL-0025 | `rtl_gate.rtl_gen / fl_rtl_goal_audit` | 2/6 | sim/fl_rtl_goal_audit.json absent or fail |
| RTL-0026 | `rtl_gate.rtl_gen / coverage_closure` | 2/6 | cov/coverage.json absent or status≠pass |
| workflow_todo.rtl_gen | various | 2/6 | SSOT `workflow_todos.rtl-gen[]` items not closed |
| function_model.state_update | rf_q, nzcv_q | 1/6 | cortex — derive owner mismatch |
| function_model.side_effect | side_effect_1 | 1/6 | cortex |
| function_model.output_rule | rx_irq | 1/6 | uart_lite |
| cycle_model.handshake_rules | apb_setup, apb_ready | 1/6 | gpio |
| fsm.transition | transition_0 | 1/6 | gpio |

## Identified workflow weaknesses (W1–W7)

### W1 — Provenance auto-emit is missing (6/6 IPs)

`RTL-0006 common_ai_agent_authoring` is open for every IP audited. The
existing helper `workflow/rtl-gen/scripts/refresh_rtl_provenance.py` only
*refreshes* an existing provenance file whose `type` is already
`rtl_authoring_provenance`; if the file does not exist (the IP has never been
authored end-to-end by the canonical pipeline), the script refuses to write.

**Fix.** The `ssot-rtl` stage should emit a fresh provenance file when the
on-disk file is absent or has a foreign `type`, using SSOT path, todo plan
hash, and rtl file list. Stage runs deterministically before LLM authoring.

### W2 — `dynamic_todo_closure` is a cascade, not a weakness

`RTL-0019` is open on every IP because at least one other required TODO is
open. It closes mechanically when the other items close. No separate fix.

### W3 — Manifest connection contract validator over-strict on hierarchical IPs

`RTL-0015` / `RTL-0016` are mild on simple IPs but punishing on complex ones:
cortex_m0lite has 31 connection-contract issues. The validator compares
`SSOT.sub_modules[].connections` against RTL top-level instantiation, but for
multi-level hierarchies the connections may legitimately route through a wrapper
without appearing on the top.

**Fix.** Validate connection contract by *RTL-side tracing* (follow signal
through wrappers) rather than requiring a literal `top → child.port` mapping in
SSOT. Or: support a `SSOT.sub_modules[].connections[].via: <wrapper>` field so
the manifest can declare indirection.

### W4 — Static-evidence tie-breaker missing for `function_model.*` variants

The tie-breaker I landed for `fsm.*` and `cycle_model.pipeline.*` in
`derive_rtl_todos._owner_for` does not extend to `function_model.state_update`,
`function_model.side_effect`, or `function_model.output_rule`. cortex
(`rf_q`, `nzcv_q`) and uart_lite (`rx_irq`) hit the same first-match-wins
bug for these categories.

**Fix.** Make the tie-breaker token overlap pass run for *every* ref where
the explicit refs loop returns multiple top-tier matches (already true) and
*also* propagate to the leaf-resolver in `emit_fl_model.py` (already covered
by the parallel fix landed for that file). The fl-model-gen change is in
place; this is the same architectural fix applied symmetrically.

### W5 — Compile/lint freshness uses mtime, not content hash

`RTL-0017 dut_compile` opens whenever any RTL source mtime is newer than
`rtl_compile.json` — even when the RTL semantics did not change (e.g.,
trailing-whitespace edit or rename). todo_counter_pipe hit this.

**Fix.** Stale check should hash the union of (file content + filelist) and
compare against the hash stored inside `rtl_compile.json`. Recompile only when
the hash changes. Same fix for `dut_lint`.

### W6 — Lint cleanliness has no waiver path on disk

`RTL-0018 dut_lint` opens whenever the lint report has any warnings. The
SSOT supports `coding_rules.lint_waivers` but `dut_lint_report.py` does not
actually read them — the audit just looks at the binary `passed` flag.

**Fix.** Have `dut_lint_report.py` read `SSOT.coding_rules.lint_waivers[]`,
subtract waived diagnostics from the count, and recompute `passed`. Each
waiver entry must name the warning code, file, signal, and rationale (already
specified in `workflow/lint/system_prompt.md`).

### W7 — rtl-gen does not auto-emit downstream artifacts before audit

`RTL-0020 / RTL-0023 / RTL-0024 / RTL-0025 / RTL-0026` are all "artifact X
does not exist" failures. Each has a deterministic emit script under
`workflow/fl-model-gen/scripts/` (`emit_authority_manifest.py`,
`emit_cycle_model.py`, `emit_protocol_assertions.py`,
`audit_fl_rtl_equivalence_goal.py`, `ssot_coverage_summary.py`). cortex hits
five of these because it has never run the full canonical pipeline.

**Fix.** rtl-gen stage epilogue should invoke the emit scripts as a
deterministic pre-audit pass:

```
emit_authority_manifest.py <ip>
emit_cycle_model.py <ip>
emit_protocol_assertions.py <ip>
audit_fl_rtl_equivalence_goal.py <ip>
ssot_coverage_summary.py <ip>
refresh_rtl_provenance.py <ip>   # W1
```

When the upstream artifacts (e.g., `cycle_model.py`) require SSOT depth the
IP does not yet have, the emit script reports its own block reason, which
the audit then surfaces as a *specific* SSOT request rather than the generic
"missing artifact". This routes blockers to the correct upstream lane.

## Operational weaknesses observed when scaling to 20 IPs

These three weaknesses surface only when the pipeline is exercised at *batch scale* (more than a handful of IPs in parallel). They do not show up on a single-IP run.

### W8 — API balance is the real batch ceiling

When 12 `ssot-gen` processes were launched in parallel with `--model deepseek`, all 12 terminated with `[LLM] Insufficient Balance` mid-flow at iterations 37-62 (of the 70-ish typically needed for the 5 phases). The agents had already produced 31-52 KB of SSOT content (50-75% of the final size) but Phase 5 handoff and `check_ssot_disk` validation never ran.

**Implication.** Workflow throughput is not just iter/wall-time gated — it is *provider-balance* gated. The pipeline must either:

- Detect insufficient balance and *checkpoint* the partial SSOT cleanly (so the agent can resume on the next session) — currently it just terminates with `exit.json.status=ok` even though work is incomplete.
- Support *fallback model rotation*: when the primary model returns 402/quota error, the workflow should reconfigure to a secondary profile (`glm`, `kimi`) and continue.
- Or surface batch-runner concurrency as a top-level config so users can split the 20-IP run across multiple sessions/days.

### W9 — Incomplete SSOTs cascade into a known failure pattern

When the 12 truncated SSOTs were fed through the rest of the canonical chain:

- `emit_fl_model.py`: `SyntaxError: unexpected EOF while parsing` on the lower-quality SSOTs.
- `derive_rtl_todos.py`: emits the plan but `gate=blocked` for IPs missing required SSOT sections.
- `rtl_compile_report.py`: passes trivially because only scaffold `<ip>.sv` stubs exist.
- `dut_lint_report.py`: passes trivially for the same reason.
- Audit closure 18-50% — far below the 92-98% range observed when SSOT is mature.

So the pipeline *does run end-to-end* (no crash) but the closure number is misleading: a 30% pass rate on a partial SSOT is not a 30% production-quality result, it is a 30% derivation-coverage result with no real RTL behind it.

**Implication.** Closure% should be paired with a *SSOT maturity score* before being treated as a workflow signal — otherwise an IP with a half-finished SSOT looks like it has 50% real coverage when in fact it has 0% real RTL. Add a `ssot.maturity = mature | partial | scaffold` field to the audit summary.

### W10 — Headless cleanup is verified at scale

Despite W8 killing 12 processes mid-flow, the `--headless` exit path worked correctly for every one of them. Each session wrote a valid `exit.json`, closed the cocotb / pyslang / verilator subprocesses, and the watcher script that polled the 12 processes detected termination cleanly and proceeded to run the audit chain on the partial state.

This is the load test for Item 2 (Phase A headless mode). No zombies, no manual `kill` needed, no `(y/n)` prompts blocking. The mechanism that this session built holds up under batch failure, which is the regime where it matters most.

## 20-IP closure table (2026-05-15 measurement)

```
IP                       pass / total     gate     rtl     SSOT maturity
─────────────────────────────────────────────────────────────────────────
todo_counter_pipe        276 / 279 = 98.9% fail    4 sv    mature
timer                    102 / 104 = 98.1% fail    1 sv    mature (missing pnr)
dma                      103 / 105 = 98.1% fail    1 sv    partial (13/34 sections)
uart_lite                279 / 286 = 97.6% fail    8 sv    mature
simple_gpio_lite         161 / 171 = 94.2% fail    2 sv    mature (missing pnr)
cortex_m0lite            174 / 189 = 92.1% fail    8 sv    mature
todo_demo_ip              14 /  20 = 70.0% blocked 1 sv    scaffold (138 B SSOT)
spi                        6 / 258 =  2.3% fail    0 sv    mature SSOT, no RTL
─────────────────────────────────────────────────────────────────────────
[12 new IPs — deepseek Insufficient Balance, partial SSOT, then re-launched on glm]
mux_4to1                  60 / 120 = 50.0% fail    1 sv    partial
edge_detector             71 / 150 = 47.3% fail    1 sv    partial
arbiter_rr                54 / 128 = 42.2% fail    1 sv    partial
debouncer                 49 / 127 = 38.6% blocked 1 sv    partial (FL SyntaxError)
pulse_gen                 58 / 157 = 36.9% fail    1 sv    partial
adder_kogge_stone         63 / 174 = 36.2% fail    1 sv    partial
lfsr                      44 / 140 = 31.4% fail    1 sv    partial
fifo_sync                 53 / 200 = 26.5% fail    1 sv    partial
priority_enc              39 / 167 = 23.4% fail    1 sv    partial
shift_reg                 35 / 165 = 21.2% fail    1 sv    partial
clkdiv                    34 / 184 = 18.5% fail    1 sv    partial
parity_gen                 5 / 155 =  3.2% fail    0 sv    partial (FL emit failed)
```

The 12 new IPs are being re-run with `glm-5.1` after the deepseek run hit Insufficient Balance. Updated numbers will replace the partial row when the second pass completes.

## Predicted closure impact

| Fix | IPs improved | Estimated absolute closure gain |
|---|---|---|
| W1 provenance auto-emit | 6/6 | +1 task per IP |
| W3 connection validator (RTL-side tracing) | cortex-class | +20–30 cortex tasks |
| W4 tie-breaker for function_model.* | 3/6 | +2–5 per IP |
| W5 hash-based freshness | as triggered | +1–2 per IP |
| W6 lint waivers from SSOT | warning-bearing IPs | +1 per IP |
| W7 auto-emit downstream | 5/6 | +3–5 per IP |

Aggregate: cortex_m0lite would move from 92.1% → ~99%, simple_gpio_lite
94.2% → ~99%, others 98% → ~99.7%.

## Recommended next-cycle order

1. **W7** (auto-emit) — single stage change, immediate effect on 5 IPs
2. **W1** (provenance auto-emit) — same area as W7, trivial addition
3. **W4** (tie-breaker propagation) — already landed pattern, copy to remaining categories
4. **W5** (hash-based freshness) — single function rewrite in compile+lint reports
5. **W6** (lint waivers) — needs SSOT schema entry + reader
6. **W3** (connection validator RTL-tracing) — heavier; new validator pass

Items 1–5 are 1–2 days of work in total. Item 6 is its own cycle.

After this batch, the realistic ceiling becomes ~99% closure across the
audited IP class, with the remaining 1% being the genuinely scope-dependent
items (sim-required evidence for production sign-off).

## Out of scope (Phase B)

- `fl_rtl_compare`: 68/68 goal match requires authored SSOT DSL `output_rules` +
  `state_updates` per transaction. Not derivable from the canonical
  deterministic emitter alone.
- TB protocol fidelity (APB handshake, baud cycles): needs LLM TB authoring or
  hand-tuned cocotb.
- Coverage RTL-observed evidence: requires the TB above to capture
  per-goal signals.

These three remain Phase B work regardless of W1–W7.

## 20-IP run ceiling (2026-05-15)

Strict goal "20개 IP에 대해서 SSOT → LINT 쭉" hit an operational ceiling
at **7/20 (35%) LINT-passing** before all three LLM profiles ran out.

### Final state
| Tier | Count | IPs |
|---|---|---|
| ✅ LINT pass | 7 | timer, dma, simple_gpio_lite, uart_lite, todo_counter_pipe, cortex_m0lite, todo_demo_ip (stub) |
| 🟡 SSOT mature, RTL plan ready | 2 | lfsr, spi |
| 🟠 SSOT mature, blocked by structural orphan refs | 6 | fifo_sync, arbiter_rr, edge_detector, pulse_gen, priority_enc, adder_kogge_stone |
| 🟠 SSOT mature, no RTL plan yet | 1 | parity_gen |
| ❌ SSOT incomplete (0 KB yaml) | 4 | clkdiv, debouncer, mux_4to1, shift_reg |

### API capacity exhaustion (W8)
Confirmed via direct probe:
- `deepseek`: balance = **−$1.48 USD**, `is_available=false`
- `kimi`: HTTP 401 `Invalid Authentication` — key expired
- `glm`: HTTP 400 on probe model (production code uses `glm-5.1`;
  glm console verification needed for the configured model id)

### Restart playbook (no API needed)
The orange-tier IPs have **structural SSOT blockers** that are deterministic
to fix without LLM calls:
- 6 IPs (fifo_sync, arbiter_rr, edge_detector, pulse_gen, priority_enc,
  adder_kogge_stone) have orphan `decomposition.units.*` refs that need
  `function_model_refs` / `decomposition_refs` assignment to candidate
  modules already named in `rtl/rtl_blocked.json`.
- Fixing these unblocks rtl planning so rtl-gen can proceed immediately
  when API capacity returns.

### Restart playbook (needs API)
After API is restored:
1. lfsr + spi → rtl-gen authoring directly (plans ready)
2. parity_gen → rtl planning + authoring
3. The 6 SSOT-fixed orange IPs → rtl planning + authoring
4. clkdiv / debouncer / mux_4to1 / shift_reg → ssot-gen from scratch

Sequential rate (1 IP / 30 min on a healthy profile) puts full 20/20
at ~6 h of LLM time after refill.
