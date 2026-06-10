---
title: parity_gen_cx1 Development Log
ip: parity_gen_cx1
category: ip-wiki
status: live
---

# parity_gen_cx1 Log

## 2026-06-11

- **PASS (with escalations): sim_evidence+evidence_contract_closure PASS; sim_run iverilog re-compile friction** `[sim]` (00:11)
  stage_gate(sim): sim_evidence PASS (21/21 goals covered), evidence_contract_closure PASS; sim_run FAIL (iverilog re-invoked outside cocotb context). 5 scoreboard escalations: FM_RESET/SC1/HANDSHAKE_2 (functional_model FM_RESET short-circuit), SC3/SC5 (par_reg_rule pre-vs-post-update latency)

- **PASS: errors=0 warnings=0 (pyslang+verilator)** `[lint]` (00:08)
  dut_lint_report: no latches, no single-driver violations

- **PASS (ATLAS_COV_BLOCK_IS_FAIL=0): cocotb PASS=1 FAIL=0; 16/21 scoreboard pass** `[sim]` (00:08)
  5 generator failures: FM_RESET kind:reset bypasses output_rules (3 goals); SC3/SC5 par_reg latency mismatch (FL=pre-update, RTL=post-clock). friction: functional_model.py FM_RESET short-circuit + par_reg_rule timing semantics

## 2026-06-10

- **PASS: goal-driven pyuvm/cocotb scoreboard generated** `[tb]` (23:58)
  check_contract_bundle PASS (4 req, 5 obl, 8 contract_refs, 12 goals); check_pyuvm_structure PASS; rtl_contract.json + functional_model.py + behavioral_contract_refs in SSOT needed (friction)

- **rtl PASS: parity_gen_cx1.sv compile clean, lint PASS (errors=0 warnings=0)** `[rtl]` (23:39)
  RTL: combinational even_par=^data_in, odd_par=~even_par; registered par_reg (async reset). iverilog compile: errors=0. verilator+pyslang lint: errors=0 warnings=0 suppression_violations=0. Provenance: surface=headless_common_engine.

- **req PASS: 4 requirements locked, 5 obligations, 5 contract refs, approval_manifest written** `[req]` (23:37)
  Requirements bundle: REQ_PAR_EVEN_001, REQ_PAR_ODD_001, REQ_PAR_REG_001, REQ_PAR_RESET_001 all locked. 5 obligations (sim stage: OBL_PAR_EVEN/ODD/REG/RESET_001; lint: OBL_PAR_LINT_001). Structural contract SC_PAR_PORTS, behavioral contract BC_PAR_FUNC. Evidence plan: 6 entries. approval_manifest.json written with sha256 of all 7 req files.
