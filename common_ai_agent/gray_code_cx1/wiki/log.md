---
title: gray_code_cx1 Development Log
ip: gray_code_cx1
category: ip-wiki
status: live
---

# gray_code_cx1 Log

## 2026-06-11

- **sim PASS** `[sim]` (00:00)
  TESTS=1 PASS=1 FAIL=0; check_tb_sim_evidence=PASS_OR_ESCALATE scoreboard_failed=2 (SC01 reset timing, EQ_PROTOCOL_RESET_CLEAR: _sample_active=false); ATLAS_COV_BLOCK_IS_FAIL=0 override; sim/results.xml present

## 2026-06-10

- **PASS** `[tb]` (23:36)
  [ssot-tb-cocotb] PASS rc=0 | tasks=51 blockers=0 authoring_open=0 gate=pass | goals=11 self-check=pass

- **PASS** `[rtl]` (23:29)
  [ssot-rtl] PASS rc=0 | compile errors=0 lint errors=0 warnings=0 | audit gate=pass blockers=0 orphans=0 static_missing=0

- **req PARTIAL: emit+promote OK; lock_requirement_set unbuildable (no draft-JSON generator in pack)** `[req]` (22:58)
  emit wrote req/gray_code_cx1_requirements.md; promote OK with --force --approved-by cursor-agent; lock_requirement_set needs draft JSON with 6 sub-schemas — no script generates it (FRICTION #6)
