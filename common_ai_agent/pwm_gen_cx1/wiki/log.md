---
title: pwm_gen_cx1 Development Log
ip: pwm_gen_cx1
category: ip-wiki
status: live
---

# pwm_gen_cx1 Log

## 2026-06-10

- **SIM PASS — TESTS=1 PASS=1 FAIL=0, scoreboard_failed=0** `[sim]` (23:20)
  iverilog/cocotb: TESTS=1 PASS=1 FAIL=0; scoreboard_events: total=18 failed=0; pwm_gen_cx1/sim/results.xml

- **TB PASS — emit_goal_scoreboard_cocotb generated 18 goals, py-compile clean** `[tb]` (23:20)
  emit_goal_scoreboard_cocotb: goals=18 rtl_sources=1; tb_py_compile.json: 0 errors; all 8 TB files emitted

- **rtl PASS** `[rtl]` (23:11)
  ssot-rtl PASS rc=0; lint PASS rc=0: pyslang+verilator errors=0 warnings=0

- **req PASS** `[req]` (23:04)
  check_locked_truth_bundle PASS: mode=locked requirements=4 obligations=5 contract_refs=5 structural_contracts=1 behavioral_contracts=4 evidence=10 closed_contracts=10
