# Systematic Quality Gates — Manifest Hygiene + SSOT Validator

**Date**: 2026-05-21

[[multi-cycle-production-wiring-20260520]] 후속. system 차원 quality gate 4 가지 도입
— IP 별 손 없이 모든 IP 적용.

Related: [[multi-cycle-production-wiring-20260520]] · [[hardcoded-strip-honest-baseline-20260520]] · [[silent-pass-exposure-tb-stimulus-gap-20260520]]

## 적용 gate

### ① Manifest hygiene gate
`derive_rtl_todos.py` 의 gate_specs 에 `manifest_hygiene` 추가. cortex_m0lite 같은
stale build 자동 차단.

### ② sim_report.txt 강화
10 IP test_runner.py 일괄 patch — last_compile_status / build_timestamp /
rtl_sources_count 출력.

### ③ Per-goal sample_cycle
Skip — 현 default 일관성 있음.

### ④ validate_ssot.py
14 schema rules. blockers 있으면 `/to-ssot` 차단.

검출 rules:
- transactions.output_rules_required
- transactions.output_rules.expr_required
- transactions.output_rules.port_recommended
- state_variables.reset_numeric
- cycle_model.pipeline.output_rules_required_when_opt_in
- cycle_model.required
- cycle_model.pipeline_required
- scenarios.stimulus_machine_spec_missing
- scenarios.stimulus_machine_spec_shape
- registers.register_list.offset_required
- io_list.required

## 검출 결과 (10 IP)

총 **14 blockers + 75 warnings** 자동 노출. 새로 발견된 silent 결함:
- atcwdt200: apb_write / write_unlock / restart 등 4 transaction output_rules 부재
- dma_scratch_orch_live: FM2 / FM3 output_rules 부재 (이전 0% PASS 는 vacuous)
- uart_lite: RX FSM 7 stage output_rules 부재 (opt-in 만 하고 누락)

## 통합

- `workflow/ssot-gen/system_prompt.md` 에 validate_ssot.py 호출 의무 추가
- `derive_rtl_todos.py` 의 manifest_hygiene gate 가 모든 audit-rtl 에서 검증
- `test_runner.py` 모두 build_timestamp 출력

## 다음 IP 흐름

```
SSOT 작성 → validate_ssot.py → FL/CL emit → RTL gate (manifest hygiene) →
cocotb (fresh sim_report) → 모든 gate 통과 시 production
```

## 남은 work

system 적 infra 완성. 남은 건 **per-IP SSOT 채움**:
- ~~atcwdt200 transaction output_rules~~ ✅ 2026-05-21 (apb_write/write_unlock/restart/timeout_decode 에 wdt_int/wdt_rst rule)
- ~~dma_scratch FM2/FM3/FM4 output_rules~~ ✅ 2026-05-21 (irq/csr_error/mem_req_valid/mem_req_write port mapping)
- ~~uart_lite RX FSM output_rules~~ ✅ 2026-05-21 (RX_IDLE/START_DETECT/START_CONFIRM/DATA/PARITY/STOP1/STOP2 rx_active state rule)
- arm_m0_min per-stage sample_cycle 매핑 (남음, 3h)
- 5 broken IP scenarios.stimulus_machine_spec 채움 (남음, 각 1-2h)

## 2026-05-21 후속 — blocker zero

3 IP blockers 모두 해소 → **system-wide 14 blockers → 0 blockers**.

- dma_scratch_orch_live_20260519b: 36/36 PASS (honest 확인 — FL emit irq/csr_error/mem_req_valid/mem_req_write 채우고 RTL match)
- atcwdt200: 4 blockers → 0 (apb_write 류 4 transaction 에 wdt_int/wdt_rst rule)
- uart_lite: 7 blockers → 0 (RX FSM 7 stage 에 rx_active state-only rule; RX 는 input 이라 port mapping 없음)

이전 dma_scratch 의 `output_rules: []` 는 SSOT validator 가 blocker 로 잡아준 **silent green** 케이스 — vacuous 0% PASS 가 진짜 0% PASS 인지 출력 비교가 비어있었던건지 구분 불가했음. 이제 명시적 port output 으로 honest PASS.
