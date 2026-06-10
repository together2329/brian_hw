---
title: shift_reg_cx1 Development Log
ip: shift_reg_cx1
category: ip-wiki
status: live
---

# shift_reg_cx1 Log

## 2026-06-10

- **sim PASS: cocotb TESTS=1 PASS=1 FAIL=0** `[sim]` (23:32)
  cocotb iverilog 295ns; scoreboard 25 events 0 failures; check_sim_disk PASS; check_truth_coverage PASS 11/11 obligations; evidence_contract_closure PASS

- **tb PASS: stage_gate(tb) all checks passed** `[tb]` (23:32)
  tb_python_compile PASS; scoreboard_source PASS goals=4 rows=25; scoreboard_self_check PASS; pyuvm_structure PASS (layered pyuvm/cocotb)

- **rtl PASS: iverilog RC=0, lint errors=0** `[rtl]` (23:32)
  shift_reg_cx1.sv compiles clean (iverilog -g2012); dut_lint_report.py PASS errors=0 warnings=0

- **req PASS: locked bundle verified** `[req]` (23:32)
  check_locked_truth_bundle.py PASS; 1 req, 3 obligations, 3 contract_refs, 1 structural+3 behavioral contracts, evidence_plan closed

- **lint PASS** `[rtl]` (23:04)
  stage_gate(lint) PASS: pyslang+verilator errors=0 warnings=0 returncode=0

- **rtl PASS** `[rtl]` (23:04)
  iverilog -g2012 RC=0; rtl/shift_reg_cx1.sv compiles clean

- **req PASS** `[req]` (23:01)
  [check_locked_truth_bundle] PASS shift_reg_cx1: mode=locked requirements=1 obligations=3 contract_refs=3 structural_contracts=1 behavioral_contracts=3 evidence=7 closed_contracts=7
