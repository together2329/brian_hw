# atcwdt200 - Andes Watchdog Timer Pipeline Run (2026-05-17)

Run snapshot for building an `atcwdt200` watchdog-timer IP from the legacy
Andes reference at `/Users/brian/Desktop/andes/atcwdt200/` through the
common_ai_agent flow: requirements import, SSOT, FL/CL, RTL, TB, sim, and lint.

This page is intentionally a **stop-condition record**, not a completion claim.
The flow has clean SSOT/model/RTL/TB/lint evidence, but sim still emits a
scoreboard escalation with 11 FL-vs-RTL unresolved rows.

Related wiki:

- [[full-flow-pipeline]] - canonical stage order.
- [[workflow-ownership-and-boundaries]] - owner classification before repair.
- [[rtl-gen-ssot-contract]] - RTL must implement the locked SSOT contract.
- [[deterministic-emit-stages]] - FL/CL/equivalence stages are deterministic.
- [[gpio-serial-pipeline-run]] - earlier soft-cocotb-pass escalation pattern.
- [[atcuart100-pipeline-run]] - larger Andes peripheral reference run.
- [[wiki-curation-policy]] - why this page captures only recurring lessons.

## Locked design

| Item | Value |
|---|---|
| Source | `/Users/brian/Desktop/andes/atcwdt200/` |
| IP | `atcwdt200`, APB-accessed watchdog timer |
| Top | `atcwdt200` |
| Clock/reset | `pclk`, active-low `presetn`; `extclk` synchronized into `pclk` |
| APB surface | `psel`, `penable`, `paddr[4:2]`, `pwrite`, `pwdata`, `prdata`; no `pready`/`pslverr` |
| Outputs | `wdt_int = SR_INTZERO & CR_INTEN`, `wdt_rst = SR_RSTZERO & CR_RSTEN` |
| Parameters | 16-bit counter by default; optional 32-bit timer mode recorded in SSOT |
| Registers | `VER` 0x00, `CR` 0x10, `RES` 0x14, `WEN` 0x18, `SR` 0x1c |
| Magic writes | unlock `0x5aa5`, restart `0xcafe` |
| FSM | `ST_INTTIME`, `ST_RSTTIME` |
| External dependency | `nds_sync_l2l` behavior replaced locally by generated sync logic |

## Stage evidence

| Stage | Result | Evidence |
|---|---|---|
| req/import | PASS | `atcwdt200/req/import_manifest.json` captures the legacy RTL/syn inputs and extracted facts |
| ssot-gen | PASS | `atcwdt200/yaml/atcwdt200.ssot.yaml`, 918 lines, no open QA/TBDs after this run |
| fl-model-gen | PASS | `atcwdt200/model/fl_model_check.json` `passed=true`; 6 transactions, 48 fcov bins |
| cl-model-gen | PASS | `atcwdt200/model/cl_model_check.json` and `atcwdt200/model/cycle_model.py` emitted |
| equiv-goals | PASS | `atcwdt200/verify/equivalence_goals.json` summary total=41 required=41 blocked=0 |
| rtl-gen | PASS | 5 RTL files; `atcwdt200/rtl/rtl_compile.json` errors=0 diagnostics=0 |
| rtl audit | PASS | `atcwdt200/rtl/rtl_authoring_provenance.json` records 16 packets and todo hash `3348ddb6018966555eeb963ff7b9aa4ed0d14e6293df5093c73330b07393340c` |
| tb-gen | PASS | `atcwdt200/tb/cocotb/tb_generation.json` status=`pass`, 41 goals, runner `test_runner.py` |
| sim | INFRA PASS / SCOREBOARD ESCALATE | `atcwdt200/sim/sim_report.txt` reports `TESTS=1 PASS=1 FAIL=0` plus `[SIM ESCALATE] scoreboard_failed=11` |
| lint | PASS | `atcwdt200/lint/dut_lint.json` errors=0 warnings=0 |

## Current blocker

The simulator infrastructure is working, but FL-vs-RTL signoff is not green:

```text
TESTS=1 PASS=1 FAIL=0
[SIM ESCALATE] scoreboard_failed=11 owner=sim_debug
```

`atcwdt200/sim/scoreboard_events.jsonl` has 41 rows, 11 failed rows:

```text
EQ_TRANSACTION_APB_READ
EQ_TRANSACTION_WRITE_UNLOCK
EQ_TRANSACTION_RESTART
EQ_TRANSACTION_TIMEOUT_DECODE
EQ_SCENARIO_APB_REGISTER_ACCESS
EQ_SCENARIO_RESTART_COMMAND
EQ_REGISTER_VER
EQ_STATE_WATCHDOG_ST_INTTIME_TO_ST_RSTTIME_0
EQ_STATE_WATCHDOG_ST_RSTTIME_TO_ST_INTTIME_1
EQ_STATE_WATCHDOG_ST_INTTIME_TO_ST_INTTIME_2
EQ_STATE_WATCHDOG_ST_RSTTIME_TO_ST_RSTTIME_3
```

The first concrete mismatch is APB read/version data:

```text
prdata expected=0 observed=50339842
```

`50339842` is `0x03002002`, matching the observed `VER` register value. That
means the next repair must classify whether the SSOT/FL `apb_read.prdata_rule`
is underspecified, whether the TB stimulus is reading the wrong address phase,
or whether the RTL read behavior is intentionally broader than the current FL
rule. Do not patch RTL or TB directly until sim-debug routes the owner.

The other failures are mostly "no comparable RTL observable for FunctionalModel
result" on unlock/restart/timeout/state goals. Those are likely observability or
contract-binding gaps: the FL exposes internal state updates such as `COUNTER`
and `STATE`, while the current top-level scoreboard only observes APB data,
status/control fields, and watchdog outputs.

## Lessons to carry forward

1. **Cocotb PASS is not signoff.** This run repeats the GPIO lesson:
   `TESTS=1 PASS=1` can coexist with `[SIM ESCALATE]`. Treat the scoreboard
   rows as the signoff surface, not the cocotb process exit alone.
2. **Generated TB needs an RTL contract artifact.** `tb-gen` required
   `atcwdt200/rtl/rtl_contract.json`; for manually authored or repaired RTL,
   make sure the contract exists before invoking the cocotb generator.
3. **RTL audit evidence must survive comment stripping.** Required evidence
   should be visible as live identifiers, assignments, constants, or reachable
   expressions. Comments are not reliable proof for gate closure.
4. **Zero-warning lint is only one gate.** This run has Verilator/lint clean
   evidence, but sim still blocks on FL-vs-RTL semantics.
5. **Version-register reads need explicit FL rules.** If a register has a fixed
   hardware value like `VER = 0x03002002`, the FL/TB contract must say so. A
   default `prdata_rule=0` creates a false mismatch or an owner ambiguity.
6. **Internal state goals need explicit observability policy.** If
   equivalence goals include `COUNTER`, `STATE`, or timeout predicates, the flow
   must either bind them through an RTL harness or classify them as non-public
   observables before sim signoff.

## Next owner step

Run sim-debug / mismatch classification before any repair:

```bash
python3 workflow/sim_debug/scripts/compare_fl_rtl_results.py atcwdt200 --root .
```

Expected triage:

- `apb_read`, `EQ_REGISTER_VER`: likely `ssot-gen` or FL contract ownership if
  `VER` read data was locked in the legacy facts but not encoded in
  `function_model.transactions[].output_rules`.
- unlock/restart/timeout/state rows: likely `tb-gen` / harness observability
  ownership unless the classifier finds an actual RTL-visible behavior mismatch.

Stop condition remains: no final IP completion claim until the scoreboard has
0 failed required rows or the failed rows are owner-routed into repair evidence.
