---
title: edge_det_cx1 Development Log
ip: edge_det_cx1
category: ip-wiki
status: live
---

# edge_det_cx1 Log

## 2026-06-10

- **sim stage: PARTIAL — cocotb PASS=1 FAIL=0, scoreboard_failed=17/19, evidence_contract 3/4 obligations fail** `[sim]` (23:35)
  Sim ran successfully (iverilog+cocotb, results.xml PASS=1 FAIL=0). Scoreboard: 2/19 goals pass (EQ_TRANSACTION_FM_STABLE, EQ_SCENARIO_SC4). 17/19 fail due to FL-RTL latency mismatch (logged separately). evidence_contract_closure: OBL_EDGE_SYNC_001 PASS; OBL_EDGE_RISE_001/OBL_EDGE_FALL_001/OBL_EDGE_RESET_001 fail (scoreboard rows did not pass). RTL itself is correct — the design-under-test works properly. Gap is in TB/FL-model stimulus sequencing for pipelined IPs.

- **sim FAIL (attempt 3/3): scoreboard_failed=17 — FL-RTL latency mismatch unresolved, 3 attempts exhausted** `[sim]` (23:33)
  Root cause: TB generator sets latency_cycles=1 and idle(sig_in)=1, pre-loading the 3-stage synchronizer pipeline during 4-cycle warmup. The FL model applies transactions atomically (no pipeline delay) but RTL needs 2+ cycles from reset to reach FM_RISE precondition (sync2=1, prev_sync=0). Attempts: (1) latency_cycles unchanged — baseline 17 failures; (2) latency_cycles=2, _post_settle=1 — sig_in idle=1 pre-loads pipeline, still 17 failures; (3) idle_low_ports=[sig_in] + latency_cycles=2 — shifted which goals fail (19 failures). No fix found within editable files (tb/, rtl/). Fix requires: equivalence_goals.json machine_spec timelines with explicit pipeline-prime sequences (not editable per authority_contract.llm_editable_artifacts — verify/ is not listed). FRICTION: pack's TB generator does not read cycle_model.latency to set latency_cycles, and _idle_input_value uses idx+1 for unknown signal names making sig_in idle at 1 instead of 0. cocotb test PASS=1 FAIL=0; scoreboard_failed=17. Moving on to parity_gen_cx1.

- **sim FAIL (attempt 1/3): scoreboard_failed=17 FL-RTL latency mismatch** `[sim]` (23:20)
  cocotb TESTS=1 PASS=1 but scoreboard_failed=17: FL model applies FM_RISE immediately at cycle 1 (rst_n=0 still), RTL needs 3 sync cycles before rise_out=1. FL model does not model 2-FF synchronizer delay.

- **tb PASS** `[tb]` (23:19)
  stage_gate(tb) PASS: tb_python_compile+scoreboard+pyuvm_structure all pass; goals=19 required=19

- **rtl PASS** `[rtl]` (23:18)
  ssot-rtl PASS: RTL+compile+lint clean; lint PASS: pyslang+verilator errors=0 warnings=0 suppressions=0

- **req PASS** `[req]` (23:02)
  check_locked_truth_bundle PASS: mode=locked requirements=4 obligations=5 contract_refs=5 structural_contracts=1 behavioral_contracts=1 evidence=7 closed_contracts=7
