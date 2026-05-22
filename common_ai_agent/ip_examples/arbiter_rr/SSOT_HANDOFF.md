# SSOT HANDOFF → rtl-gen

Module  : arbiter_rr
SSOT    : arbiter_rr/yaml/arbiter_rr.ssot.yaml
Status  : check_ssot_disk PASS (48001B, 36 sections, 0 TBDs)
Task    : Implement RTL from SSOT
Output  : arbiter_rr/rtl/arbiter_rr.sv, arbiter_rr/rtl/arbiter_rr_core.sv, arbiter_rr/rtl/arbiter_rr_regs.sv, arbiter_rr/rtl/arbiter_rr_param.vh

Key Contracts:
- function_model: transactions FM1 (arbitrate_grant) + FM2 (no_grant_idle)
- cycle_model: 1-cycle latency, S0_SAMPLE_REQ / S1_GRANT pipeline
- registers: CTRL (0x00), REQ_MASK (0x04), STATUS (0x08)
- sub_modules: arbiter_rr_regs (manifest, ssot_gen: true), arbiter_rr_core (manifest, ssot_gen: false)
- clock: PCLK 50MHz; reset: PRESETn active-low async-assert-sync-deassert
- quality_gates.rtl_gen.profile: production
- custom.assumptions: 7 recorded

Unresolved: None blocking
