# Survivor Classification

- Status: `pass`
- Generated: `2026-06-01T23:07:01Z`
- Total survivors: `16`

| Mutant | Category | Disposition | Next Action |
| --- | --- | --- | --- |
| `MUT_0238_sub_to_add_mctp_assembler_scratch_sram_packer_34` | `operator_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0153_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_29` | `constant_flip` | `test_hole` | Add reset-to-first-packet pulse persistence checks if this diagnostic signal becomes signoff-critical. |
| `MUT_0237_eq_to_ne_mctp_assembler_scratch_sram_packer_34` | `comparator_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0261_add_to_sub_mctp_assembler_scratch_axi_read_egress_41` | `operator_flip` | `test_hole` | Add APB-programmed descriptor readback tests for beat-count boundary lengths. |
| `MUT_0337_zero_to_one_mctp_assembler_scratch_cdc_35` | `constant_flip` | `irrelevant` | Review only if the affected signal is promoted to a required observable. |
| `MUT_0338_zero_to_one_mctp_assembler_scratch_cdc_36` | `constant_flip` | `irrelevant` | Review only if the affected signal is promoted to a required observable. |
| `MUT_0154_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_36` | `constant_flip` | `test_hole` | Add reset-to-first-packet pulse persistence checks if this diagnostic signal becomes signoff-critical. |
| `MUT_0166_sub_to_add_mctp_assembler_scratch_mctp_parser_49` | `operator_flip` | `test_hole` | Add parser-level invalid length and TU-boundary vectors with explicit drop-reason observation. |
| `MUT_0339_zero_to_one_mctp_assembler_scratch_cdc_37` | `constant_flip` | `irrelevant` | Keep as debug-observability follow-up; no functional scenario is blocked by this survivor. |
| `MUT_0169_sub_to_add_mctp_assembler_scratch_mctp_parser_53` | `operator_flip` | `test_hole` | Add parser-level invalid length and TU-boundary vectors with explicit drop-reason observation. |
| `MUT_0239_zero_to_one_mctp_assembler_scratch_sram_packer_38` | `constant_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0071_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_61` | `state_update_drop` | `test_hole` | Add back-to-back queue wrap or long-pack drain checks tied to the mutated state. |
| `MUT_0244_add_to_sub_mctp_assembler_scratch_sram_packer_56` | `operator_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0156_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_39` | `constant_flip` | `test_hole` | Add reset-to-first-packet pulse persistence checks if this diagnostic signal becomes signoff-critical. |
| `MUT_0167_ne_to_eq_mctp_assembler_scratch_mctp_parser_50` | `comparator_flip` | `test_hole` | Add parser-level invalid length and TU-boundary vectors with explicit drop-reason observation. |
| `MUT_0057_state_update_to_self_hold_mctp_assembler_scratch_sram_packer_62` | `state_update_drop` | `test_hole` | Add back-to-back queue wrap or long-pack drain checks tied to the mutated state. |
