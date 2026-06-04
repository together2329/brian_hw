# Survivor Classification

- Status: `pass`
- Generated: `2026-06-04T01:00:39Z`
- Total survivors: `5`

| Mutant | Category | Disposition | Next Action |
| --- | --- | --- | --- |
| `MUT_0408_sub_to_add_mctp_assembler_v3_sram_packer_72` | `operator_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0406_zero_to_one_mctp_assembler_v3_sram_packer_70` | `constant_flip` | `test_hole` | Add targeted unaligned first/last-word cases around the mutated expression. |
| `MUT_0456_eq_to_ne_mctp_assembler_v3_axi_rd_payload_75` | `comparator_flip` | `test_hole` | Add a targeted scenario or explicitly waive after human review. |
| `MUT_0458_sub_to_add_mctp_assembler_v3_axi_rd_payload_83` | `operator_flip` | `test_hole` | Add a targeted scenario or explicitly waive after human review. |
| `MUT_0056_state_update_to_self_hold_mctp_assembler_v3_axi_rd_payload_134` | `state_update_drop` | `test_hole` | Add back-to-back queue wrap or long-pack drain checks tied to the mutated state. |
