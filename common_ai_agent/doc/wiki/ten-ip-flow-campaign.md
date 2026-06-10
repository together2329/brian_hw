# 10-IP Flow Campaign — Make IP Development Practically Viable (2026-06-10)

User directive: build ~10 IPs through the standard flow
(req-contracts → ssot-gen → fl/cl → dual-fcov → equiv-goals → rtl-gen → lint →
tb-gen → sim), study where the GENERAL flow strains, and bake every needed fix
into the workflow — the goal is practically viable IP development, not demos.

## Method (per IP)

1. Fresh root under `.tmp/`, requirement md authored from scratch (one new
   hardware idiom per IP — the campaign exists to hit DIFFERENT semantics).
2. Run headless, default (relaxed/build-first) mode, `--req-approver brian`,
   `--stage-retries 2`, gpt-5.5 (gpt-5.3-codex needs an API-key route).
3. Count interventions; every intervention must be folded back as a GENERAL
   workflow change (prompt/brief/validator/template/gate), never an IP patch.
4. Regression matrix after machinery changes: pc1 31/31, hx1 57/57, hx2 54/54
   (+ each new green IP joins the matrix).

## Roster (idioms chosen to stress different machinery)

| # | IP | Idiom under test | Status |
|---|---|---|---|
| 1 | pulse_counter_v1 (pc1) | baseline, manual walk | 31/31 ✅ |
| 2 | pulse_counter_hx | headless v1, repairs → machinery | 57/57 ✅ |
| 3 | pulse_counter_hx2 | projection brief + exact-key bundle | 54/54 ✅ |
| 3b | apb_watchdog_v1 (hx3) | write-triggered side effects (KICK) | 47/55 — FL-LLM step-1 acceptance test |
| 4 | pulse_counter_hx4 | build-first flow smoke (advisories, no stops) | running |
| 5 | apb_gpio_w1c | W1C interrupt flags (write-1-to-clear semantics; non-idempotent-looking writes) | todo |
| 6 | apb_fifo_regs | FIFO status (full/empty/level), backpressure semantics in CL | todo |
| 7 | rr_arbiter_4 | LEGITIMATE cycle_model.state_accumulating=true (cross-goal rotation chains) — the only true positive for that flag | todo |
| 8 | apb_uart_tx_lite | baud divider + shift register (deep multi-cycle CL, cosim path) | todo |
| 9 | apb_pwm | period/duty compare, glitch-free update-on-wrap (temporal contracts) | todo |
| 10 | apb_timer_cascade | two timers + cascade enable (multi-module integration.connections for real) | todo |

Re-run hx3 (watchdog) after FL-LLM mutation/provenance gates land; its 8 open
failures are the acceptance test ([[llm-authored-oracle-architecture]]).

## Known open machinery work feeding this campaign

- FL-LLM gates 2 (mutation, criterion unknown==0) and 4 (provenance) are
  `not_implemented` placeholders in check_fl_contract.json.
- CL/TB LLM-authoring migration (steps 2–3 of the oracle architecture).
- ssot-gen guardrail-consumption: the repair loop should read
  `req/ssot_guardrails.json` + `*_advisories.json` as its work queue.
- Todo tab React Flow graph (task #12) — visibility for the loops the
  campaign exercises.

## Ledger (append per IP: interventions + what was generalized)

- hx4: (pending run completion)

Related: [[headless-stage-validation-phase2-20260610]],
[[llm-authored-oracle-architecture]], [[stage-validation-reflections-20260610]].
