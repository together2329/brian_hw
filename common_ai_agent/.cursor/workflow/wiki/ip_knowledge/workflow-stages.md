---
title: ATLAS IP Workflow — Knowledge Graph
type: index
tags: [workflow, index, ssot]
status: stable
---

# ATLAS IP Workflow — Knowledge Graph

Entry point for the 11-stage ATLAS hardware-IP generation pipeline: every stage takes the human-approved SSOT YAML as authority and emits traceable, validator-gated artifacts under `<ip>/`. This wiki has one page per stage, distilled from each `workflow/<stage>/system_prompt.md` and `scripts/`.

## Canonical Flow

```
[[ssot-gen]]  →  [[fl-model-gen]]  →  [[rtl-gen]]  →  [[tb-gen]]  →  [[sim]]
   SSOT            FL-Model            RTL            TB             SIM
                                                                      ↓
                              [[lint]]  ←———  (DUT-only, gates TB)
                                                                      ↓
                          [[coverage]]  →  [[syn]]  →  [[sta]]  →  [[pnr]]  →  [[sta-post]]
                            COVERAGE        SYN         STA         PNR         STA-POST
```

The semantic spine is `SSOT → FL-Model → RTL → TB → SIM`; [[lint]] gates RTL DUT-quality, [[coverage]] closes SSOT coverage goals, and the EDA tail (`SYN → STA → PNR → STA-POST`) produces physical/timing sign-off evidence. See `workflow/COMMON_ENGINE_FLOW.md` and `workflow/GUIDE.md` for the engine boundary and control-surface contract.

## Stage Index

| Stage | Page | Produces |
| --- | --- | --- |
| SSOT generation | [[ssot-gen]] | `<ip>/yaml/<ip>.ssot.yaml` (the contract) |
| Functional model | [[fl-model-gen]] | `model/functional_model.py`, `verify/equivalence_goals.json`, `cov/fcov_plan.json` |
| RTL implementation | [[rtl-gen]] | `rtl/*.sv`, `list/<ip>.f`, `rtl/rtl_compile.json` |
| Testbench generation | [[tb-gen]] | `tb/cocotb/*`, `sim/scoreboard_events.jsonl` |
| Simulation | [[sim]] | `sim/sim_report.txt`, `sim/results.xml`, `*.vcd` |
| Lint | [[lint]] | `lint/dut_lint.json`, `lint/dut_lint.log` |
| Coverage | [[coverage]] | `cov/coverage.json`, `cov/coverage.info`, `cov/annotated/` |
| Synthesis | [[syn]] | `syn/out/synth.v`, `syn/out/area.json` |
| Static timing (pre-route) | [[sta]] | `sta/out/wns.json`, `sta/out/<ip>.sdc` |
| Place & route | [[pnr]] | `pnr/out/routed.{def,v,spef}` |
| Post-route STA (sign-off) | [[sta-post]] | `sta-post/out/wns.json`, `sta-post/out/sta.report.md` |

## Cross-cutting rules

- **SSOT is the only semantic authority.** Every stage reads `<ip>/yaml/<ip>.ssot.yaml`; none may invent behavior. Missing facts produce `[SSOT TBD REPORT] -> ssot-gen`, not a guess.
- **Evidence over claims.** Every "PASS / clean / done" must be backed by a real `run_command` whose output is cited verbatim; disk-truth validators (`check_*_disk.sh`) reject fake approvals.
- **LLMs author, validators gate, humans own truth.** RTL/TB/reports are LLM-editable; SSOT behavior, FunctionalModel semantics, coverage goals, timing targets, and final sign-off are human-locked.
