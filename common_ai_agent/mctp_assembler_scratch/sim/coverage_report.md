# mctp_assembler_scratch SSOT coverage report

SSOT: `mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`
Status: `owner_routed`

DV scenarios: 22
Scoreboard checks: 22
Functional bins: 43/100
Function coverage: 19/58 (32.76%) target=100.0
Cycle coverage: 24/42 (57.14%) target=100.0
RTL-observed coverage events: 26/91
Line coverage: 0/0 (None%) target=None
Branch coverage: 0/0 (None%) target=None
FSM-state coverage: 8/8 (100.0%) target=None

## Limitations
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: AD_DESCRIPTOR_FULL_executed, AD_DUPLICATE_SOM_executed, AD_MESSAGE_OVERFLOW_executed, AD_SEQUENCE_MISMATCH_executed, AD_SRAM_OVERFLOW_executed, AD_TIMEOUT_executed, PD_BAD_OR_EXPIRED_TAG_executed, PD_BAD_PAD_OR_ALIGNMENT_executed, PD_DISABLED_DROP_MODE_executed, PD_UNEXPECTED_MIDDLE_END_executed, SC_APB_REGS_PER_Q_executed, SC_AXI_READBACK_TRIM_executed, ... +45

## Owner-routed non-signoff coverage gaps
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: AD_DESCRIPTOR_FULL_executed, AD_DUPLICATE_SOM_executed, AD_MESSAGE_OVERFLOW_executed, AD_SEQUENCE_MISMATCH_executed, AD_SRAM_OVERFLOW_executed, AD_TIMEOUT_executed, PD_BAD_OR_EXPIRED_TAG_executed, PD_BAD_PAD_OR_ALIGNMENT_executed, PD_DISABLED_DROP_MODE_executed, PD_UNEXPECTED_MIDDLE_END_executed, SC_APB_REGS_PER_Q_executed, SC_AXI_READBACK_TRIM_executed, ... +45
