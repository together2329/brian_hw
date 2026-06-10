---
title: debounce_cx1 Development Log
ip: debounce_cx1
category: ip-wiki
status: live
---

# debounce_cx1 Log

## 2026-06-10

- **SIM PARTIAL — TESTS=1 PASS=1 FAIL=0, scoreboard_failed=19 (registered-output warmup gap)** `[sim]` (23:43)
  iverilog/cocotb: TESTS=1 PASS=1 FAIL=0; scoreboard_events: total=21 failed=19; FRICTION: debounce db_out is registered state — FL model warmup mismatch vs RTL; db_out observed=1 vs FL fl_db=0 because TB drives btn_in=1 during reset warmup (4 stable cycles => db_q=1) but FL model starts cold; SOFT_EQ_MISMATCH only (not hard fail)

- **TB PASS — emit_goal_scoreboard_cocotb generated 21 goals, py-compile clean** `[tb]` (23:43)
  emit_goal_scoreboard_cocotb: goals=21 rtl_sources=1; tb_manifest.json generated; all 8 TB files emitted

- **RTL PASS — iverilog errors=0 style=0, pyslang+verilator errors=0 warnings=0** `[rtl]` (23:35)
  rtl_compile_report: errors=0 diagnostics=0 style_violations=0; dut_lint_report: errors=0 warnings=0; debounce_cx1/rtl/debounce_cx1.sv

- **REQ PASS — bundle check: requirements=4 obligations=5 contracts=4 evidence=10** `[req]` (23:26)
  check_contract_bundle.py: mode=locked requirements=4 obligations=5 contract_refs=5 structural_contracts=1 behavioral_contracts=4 evidence=10 closed_contracts=10
