# Goal Audit Report — pl330realverify

- **IP**: pl330realverify
- **Date**: 2026-05-18
- **Pipeline**: 5091271ebe69
- **Stage**: goal-audit (sim_debug)
- **Auditor**: sim_debug agent

---

## Executive Summary

| Domain | Status | Owner-Classifier |
|--------|--------|-----------------|
| SSOT | ✅ GREEN | — |
| Functional Model | ✅ GREEN | — |
| Cycle Model | ✅ GREEN | — |
| Lint | ✅ GREEN | — |
| RTL Compile | ✅ GREEN | — |
| Synthesis (Yosys) | ✅ GREEN | — |
| PNR (DRC) | ✅ GREEN | — |
| Pre-route STA | 🔴 SETUP FAIL | → human (locked target) |
| Post-route STA | 🔴 SETUP FAIL (worse) | → human (locked target) |
| Simulation | 🟡 PARTIAL | → tb-gen |
| Coverage | 🔴 1/95 bins (1.05%) | → tb-gen |
| FL-vs-RTL Compare | 🔴 MISSING | → sim_debug infrastructure |
| Mismatch Classification | 🔴 MISSING | → sim_debug infrastructure |
| Scoreboard Self-check | 🟡 KeyError in FL model | → fl-model-gen |

---

## 1. SSOT — ✅ GREEN

**Evidence**: `pl330realverify/yaml/pl330realverify.ssot.yaml` (3556 lines)

- `top_module.name`: `pl330realverify` — matches RTL top
- `target.technology`: sky130_fd_sc_hd, 500 MHz
- Full `function_model` with 7 transactions (FM_RESET, FM_APB_WRITE, FM_APB_READ, FM_TRANSFER, FM_WFP, FM_FAULT, FM_IRQ_CLEAR)
- Full `cycle_model` with 8 pipeline stages, 8 handshake rules, 5 ordering rules
- Full `fsm.channel_fsm`: 11 states, 16 transitions, reset_state=STOPPED
- Full `registers.register_list`: 10 register types with fields
- 12 test scenarios (SC01–SC12)
- Coverage goals: function (8 bins) + cycle (11 bins) + line/branch/FSM
- Quality gates declared

**Verdict**: SSOT is comprehensive and internally consistent. No gaps found.

---

## 2. Functional Model — ✅ GREEN

**Evidence**: `pl330realverify/model/fl_model_check.json`

- Self-check: **PASS** (8/8 checks, 0 failures)
- 7/7 transactions pass with correct reset/state/output behavior
- Coverage bins: 95 planned
- Invariants: 4 evaluated (0 failed), 1 skipped (`write_beat_done` — unknown rule name)
- Error cases: 5 planned
- Decomposition: 13 units
- Authority contract correctly declared with locked artifacts

**Minor note**: 1 invariant skipped (`write_beat_done` not a known signal name). Low severity.

---

## 3. Cycle Model — ✅ GREEN

**Evidence**: `pl330realverify/model/cl_model_check.json`

- Self-check: **PASS** (7/7 transactions, 6/6 results observed)
- Coverage bins: 20 planned, 20 hit
- Performance targets: 500 MHz, 1 beat/cycle sustained, single outstanding
- Backend: pymtl3

---

## 4. Lint — ✅ GREEN

**Evidence**: `pl330realverify/lint/dut_lint.json`, `pl330realverify/lint/dut_lint.log`

| Tool | Errors | Warnings | Result |
|------|--------|----------|--------|
| pyslang | 0 | 0 | PASS |
| verilator --lint-only -Wall | 0 | 0 | PASS |

- 7 RTL files + 1 header checked
- Top module: pl330realverify
- No suppressions, no waived warnings
- **Verdict**: Lint-clean. Zero unwaived diagnostics.

---

## 5. RTL Compile — ✅ GREEN

Both pyslang and verilator compile the full filelist without errors.

---

## 6. Synthesis (Yosys) — ✅ GREEN

**Evidence**: `pl330realverify/syn/out/syn.report.md`

- Corner: `sky130_fd_sc_hd__ss_100C_1v40.lib`
- Total cells: 1321 (372 sequential, 949 combinational)
- Total area: 16400.0 μm²
- Top cell types: dfrtp_1 (372), mux2_1 (224), o21ai_0 (92), nor2_1 (84), a21oi_1 (66)
- Warnings: none
- Netlist: `syn/out/synth.v` generated

**Verdict**: Synthesis successful with reasonable cell count for an 8-channel DMA controller.

---

## 7. Pre-route STA — 🔴 SETUP FAIL

**Evidence**: `pl330realverify/sta/out/wns.json`, `pl330realverify/sta/out/sta.report.md`

| Metric | Value |
|--------|-------|
| Clock | dmaclk, period 2.0 ns (500 MHz) |
| Setup WNS | **-15.920 ns** |
| Setup TNS | -79.600 ns |
| Setup violations | 5 |
| Hold WNS | 0.780 ns (no violations) |
| Worst setup path | `paddr[10]` → `u_regs/_631_` (slack -15.92) |

**Analysis**: The worst setup path is from input port `paddr[10]` through the register decoder logic to flip-flop `u_regs/_631_`. The input delay budget of 0.2 ns plus combinational logic through the APB register decode exceeds the 2.0 ns clock period by ~16 ns. This is a fundamental frequency-vs-technology mismatch.

**Owner**: **`locked_artifact_change_requires_human`** — The SSOT specifies 500 MHz target (`timing.target_clocks[0].frequency_mhz: 500`). This is extremely aggressive for sky130_fd_sc_hd at the worst-case corner. Closing timing requires either:
  1. Reducing the target frequency (SSOT change → human gate), or
  2. Pipelining the register decode path (RTL architecture change → rtl-gen), or
  3. Both

The input-to-register path has ~18 ns of combinational delay in synthesis, which means even at 50 MHz (20 ns period) this path would barely close. This suggests the register decode RTL may need structural pipelining regardless of frequency target.

---

## 8. PNR — ✅ DRC=0, Artifacts Ready

**Evidence**: `pl330realverify/pnr/out/pnr.report.md`, `pl330realverify/pnr/out/drc.json`

- All artifacts present: floorplan.def, placed.def, cts.def, cts.v, routed.def, routed.v, **routed.spef**
- DRC count: **0**
- Design area / utilization: **null** (not captured — EDA infrastructure gap)
- Tcl scripts: cts.tcl, floorplan.tcl, place.tcl, route.tcl

**Verdict**: PNR completes successfully with DRC=0 and SPEF ready. Missing area metrics is a minor EDA reporting gap.

---

## 9. Post-route STA — 🔴 SETUP FAIL (Worse)

**Evidence**: `pl330realverify/sta-post/out/wns.json`, `pl330realverify/sta-post/out/sta.report.md`

| Metric | Pre-route | Post-route | Δ |
|--------|-----------|------------|---|
| Setup WNS | -15.920 ns | **-30.890 ns** | -14.970 ns |
| Setup TNS | -79.600 ns | -154.370 ns | -74.770 ns |
| Setup violations | 5 | 5 | 0 |
| Hold WNS | 0.780 ns | 0.790 ns | +0.010 ns |
| Hold violations | 0 | 0 | 0 |

**Analysis**: Post-route setup degrades by ~15 ns due to real parasitic net delays. Timing is significantly worse after routing. The same 5 endpoints fail.

**Owner**: Same as pre-route — `locked_artifact_change_requires_human`. Will not close without fundamental architecture or target frequency change.

---

## 10. Simulation — 🟡 PARTIAL

**Evidence**: `pl330realverify/sim/results.xml`, `pl330realverify/sim/sim_report.txt`, `pl330realverify/sim/scoreboard_events.jsonl`

### cocotb Results
- **4/4 tests PASS** (0 failures, 0 errors)
- Tests: `tc_reset_apb_smoke`, `tc_single_beat_copy`, `tc_irq_fault_path`, `tc_ssot_regression_summary`
- Total sim time: ~367 ns across all tests

### Scoreboard Events
- Total: 82 events
- **Passed: 7** (all from SC_AXI_READ_FAULT scenario — register writes and reads for INTEN, SAR, DAR, LOOP_CFG, CONTROL + CSR and INTSTATUS reads)
- **Failed: 75** (all `SIM_ESCALATE_UNEXERCISED_EQ_GOAL` — bounded smoke did not exercise these required goals)

### Waveform
- VCD: `pl330realverify/sim/pl330realverify.vcd` — 1916 lines, 350 signals
- ASCII VCD with `$date`, `$timescale`, `$var` — inspectable
- Time range: #0 to #267 (in 1s timescale units — this is iverilog's default; actual clock periods are 10ns based on TB)
- Signals include: dmaclk, dmacresetn, APB bus, AXI bus, channel_state, status_dp, intstatus, inten, dmac_irq, and internal debug signals
- Reset visible in waveform; APB transactions and AXI handshakes observable

### Gaps
- Only 7/81 equivalence goals closed by scoreboard
- No FL-vs-RTL compare JSON (`fl_rtl_compare.json`) generated
- No mismatch classification (`mismatch_classification.json`) generated
- Bounded smoke covers only AXI read fault path — missing: reset, single-beat copy, multi-beat copy, backpressure, WFP, write fault, W1C, debug command

**Owner**: → **tb-gen** — needs expanded test scenarios to close remaining 74 equivalence goals

---

## 11. Coverage — 🔴 1/95 bins (1.05%)

**Evidence**: `pl330realverify/cov/coverage_functional.json`

- **Total functional bins**: 95
- **Hit**: 1 (`SC_AXI_READ_FAULT_executed`)
- **Miss**: 94
- Breakdown of misses:
  - 8/9 scenario bins missed
  - 6/7 transaction bins missed
  - 18/19 FSM state transition bins missed
  - 6/6 error bins missed
  - 8/8 protocol handshake bins missed
  - 21/21 latency bins missed
  - All backpressure, performance, pipeline stage bins missed

**Coverage plan**: `pl330realverify/cov/fcov_plan.json` declares 70 bins across 6 classes (scenario: 9, transaction: 7, state_transition: 19, error: 6, protocol_handshake: 8, latency: 21). The 95 reported bins include additional bins from the FL model.

**Owner**: → **tb-gen** — stimulus expansion required to hit coverage targets. Coverage goals require 100% function and 100% cycle coverage per SSOT `test_requirements.coverage_goals`.

---

## 12. Scoreboard Self-check — 🟡 KeyError

**Evidence**: `pl330realverify/sim/scoreboard_selfcheck.log`

```
KeyError: "unresolved output rule dependencies: apb_write_error: 'unknown rule name illegal_apb_access'"
```

The FunctionalModel's `_apply_structured_rules` method raises a KeyError when processing the `FM_APB_WRITE` transaction because `illegal_apb_access` is referenced in output rules but is not defined as a known derived signal/rule name.

**Owner**: → **fl-model-gen** — the FL model's derived signal definitions need to include `illegal_apb_access` or the output rule reference needs correction.

---

## 13. FL-vs-RTL Compare & Mismatch Classification — 🔴 MISSING

- `pl330realverify/sim/fl_rtl_compare.json`: **does not exist**
- `pl330realverify/sim/mismatch_classification.json`: **does not exist**

These are required for the full equivalence pipeline. The scoreboard provides partial evidence but the formal compare script has not been run.

**Owner**: → **sim_debug infrastructure** — run `compare_fl_rtl_results.py` or equivalent to generate these artifacts.

---

## Summary of Blockers by Owner

| Blocker | Owner | Severity | Action Required |
|---------|-------|----------|-----------------|
| Pre-route STA setup WNS=-15.92 ns at 500 MHz | **human** (locked target) | 🔴 Critical | Human decision: reduce target frequency or approve RTL pipelining |
| Post-route STA setup WNS=-30.89 ns | **human** (locked target) | 🔴 Critical | Same root cause as pre-route |
| 74/81 EQ goals unexercised by TB | **tb-gen** | 🔴 High | Expand cocotb tests to cover all 12 SSOT scenarios |
| 94/95 coverage bins missed | **tb-gen** | 🔴 High | Add stimulus for FSM transitions, errors, latency, protocol |
| FL-vs-RTL compare missing | **sim_debug** | 🟡 Medium | Run compare script |
| Mismatch classification missing | **sim_debug** | 🟡 Medium | Run classify script |
| Scoreboard FL KeyError | **fl-model-gen** | 🟡 Medium | Fix `illegal_apb_access` derived signal in FL model |
| PNR area metrics null | **EDA infra** | 🟢 Low | Cosmetic reporting gap |

---

## Evidence Checklist

| Evidence | Path | Present | Status |
|----------|------|---------|--------|
| SSOT | `yaml/pl330realverify.ssot.yaml` | ✅ | Valid, comprehensive |
| FL model check | `model/fl_model_check.json` | ✅ | 8/8 pass |
| CL model check | `model/cl_model_check.json` | ✅ | 7/7 pass |
| Equivalence goals | `verify/equivalence_goals.json` | ✅ | 81 goals, 81 required |
| RTL lint | `lint/dut_lint.json` | ✅ | Clean (0 errors, 0 warnings) |
| Synthesis report | `syn/out/syn.report.md` | ✅ | 1321 cells, 16400 μm² |
| Pre-route STA | `sta/out/wns.json` | ✅ | Setup FAIL (WNS -15.92 ns) |
| PNR report | `pnr/out/pnr.report.md` | ✅ | DRC=0, SPEF ready |
| Post-route STA | `sta-post/out/wns.json` | ✅ | Setup FAIL (WNS -30.89 ns) |
| Waveform (VCD) | `sim/pl330realverify.vcd` | ✅ | 1916 lines, 350 signals |
| cocotb results | `sim/results.xml` | ✅ | 4/4 tests pass |
| Scoreboard events | `sim/scoreboard_events.jsonl` | ✅ | 7 passed, 75 escalated |
| Functional coverage | `cov/coverage_functional.json` | ✅ | 1/95 bins hit |
| Coverage plan | `cov/fcov_plan.json` | ✅ | 70 bins planned |
| FL-vs-RTL compare | `sim/fl_rtl_compare.json` | ❌ | Missing |
| Mismatch classification | `sim/mismatch_classification.json` | ❌ | Missing |

---

**[SIM_DEBUG ESCALATE]**
- **→ human**: Pre-route and post-route STA setup violations at 500 MHz target require human decision on frequency target or RTL architecture change (locked artifact).
- **→ tb-gen**: 74 equivalence goals and 94 coverage bins are unexercised. Bounded smoke test only covers AXI read fault. Need tests for all 12 SSOT scenarios.
- **→ fl-model-gen**: FunctionalModel has KeyError on `illegal_apb_access` derived signal in structured output rules.
