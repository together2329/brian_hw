---
title: watchdog_cx1 Development Log
ip: watchdog_cx1
category: ip-wiki
status: live
---

# watchdog_cx1 Log

## 2026-06-10

- **sim PASS (cocotb iverilog)** `[sim]` (23:49)
  TESTS=1 PASS=1 FAIL=0 175ns; 9 scoreboard events 0 failures; 4 goals covered; sim_run sub-gate broken (pre-existing: sim.py treats IP name as verilog source path); truth_coverage 13/13 PASS; evidence_contract_closure PASS

- **sim PASS** `[sim]` (23:40)
  TESTS=1 PASS=1 FAIL=0; scoreboard 9 events 0 failures; all 4 goals covered; evidence_contract PASS

- **tb PASS** `[tb]` (23:34)
  pyuvm/cocotb TB: 4 goals, UVM layers, stage_gate(tb) PASS

- **rtl+lint PASS** `[rtl]` (23:16)
  iverilog compile clean; dut_lint_report PASS: errors=0 warnings=0 style_violations=0; stage_gate(lint) PASS

- **req PASS** `[req]` (23:05)
  check_locked_truth_bundle PASS: mode=locked requirements=1 obligations=5 contract_refs=5 structural_contracts=1 behavioral_contracts=5 evidence=11 closed_contracts=11
