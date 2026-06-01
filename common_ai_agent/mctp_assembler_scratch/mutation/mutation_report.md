# Mutation Guard - mctp_assembler_scratch

- Status: `pass`
- Mode: `advisory`
- Candidates: `32`
- Executed: `32`
- Killed: `9`
- Survived: `23`
- Invalid: `0`
- Kill rate: `0.2812`
- Contract unsupported mutation categories: `boundary_flag_flip, interrupt_clear_priority_flip, reset_value_flip`

## Category Kill Rate

| Category | Executed | Killed | Survived | Invalid | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparator_flip` | 7 | 5 | 2 | 0 | `0.7143` |
| `constant_flip` | 7 | 1 | 6 | 0 | `0.1429` |
| `handshake_hold_drop` | 3 | 0 | 3 | 0 | `0.0` |
| `operator_flip` | 8 | 2 | 6 | 0 | `0.25` |
| `state_update_drop` | 7 | 1 | 6 | 0 | `0.1429` |

## Mutants

| Mutant | Status | Location | Rule | Reason |
| --- | --- | --- | --- | --- |
| `MUT_0078_add_to_sub_mctp_assembler_scratch_pcie_vdm_parser_34` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:34` | `add_to_sub` | test runner returned 0 |
| `MUT_0147_zero_to_one_mctp_assembler_scratch_sram_packer_24` | `killed` | `rtl/mctp_assembler_scratch_sram_packer.sv:24` | `zero_to_one` | scoreboard failed rows=1 |
| `MUT_0076_eq_to_ne_mctp_assembler_scratch_pcie_vdm_parser_30` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:30` | `eq_to_ne` | test runner returned 0 |
| `MUT_0030_full_pop_ready_drop_mctp_assembler_scratch_axi_read_egress_37` | `survived` | `rtl/mctp_assembler_scratch_axi_read_egress.sv:37` | `full_pop_ready_drop` | test runner returned 0 |
| `MUT_0035_state_update_to_self_hold_mctp_assembler_scratch_axi_read_egress_76` | `survived` | `rtl/mctp_assembler_scratch_axi_read_egress.sv:76` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0153_add_to_sub_mctp_assembler_scratch_sram_packer_44` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:44` | `add_to_sub` | test runner returned 0 |
| `MUT_0148_zero_to_one_mctp_assembler_scratch_sram_packer_29` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:29` | `zero_to_one` | test runner returned 0 |
| `MUT_0089_ne_to_eq_mctp_assembler_scratch_mctp_parser_39` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:39` | `ne_to_eq` | scoreboard failed rows=2 |
| `MUT_0028_full_pop_ready_drop_mctp_assembler_scratch_sram_packer_39` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:39` | `full_pop_ready_drop` | test runner returned 0 |
| `MUT_0008_state_update_to_self_hold_mctp_assembler_scratch_axi_write_ingress_93` | `survived` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:93` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0091_sub_to_add_mctp_assembler_scratch_mctp_parser_46` | `survived` | `rtl/mctp_assembler_scratch_mctp_parser.sv:46` | `sub_to_add` | test runner returned 0 |
| `MUT_0077_one_to_zero_mctp_assembler_scratch_pcie_vdm_parser_31` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:31` | `one_to_zero` | test runner returned 0 |
| `MUT_0090_ne_to_eq_mctp_assembler_scratch_mctp_parser_45` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:45` | `ne_to_eq` | scoreboard failed rows=3 |
| `MUT_0029_full_pop_ready_drop_mctp_assembler_scratch_descriptor_queue_55` | `survived` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:55` | `full_pop_ready_drop` | test runner returned 0 |
| `MUT_0015_state_update_to_self_hold_mctp_assembler_scratch_context_table_96` | `killed` | `rtl/mctp_assembler_scratch_context_table.sv:96` | `state_update_to_self_hold` | scoreboard failed rows=1 |
| `MUT_0101_add_to_sub_mctp_assembler_scratch_context_table_67` | `killed` | `rtl/mctp_assembler_scratch_context_table.sv:67` | `add_to_sub` | scoreboard failed rows=1 |
| `MUT_0154_zero_to_one_mctp_assembler_scratch_descriptor_queue_31` | `survived` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:31` | `zero_to_one` | test runner returned 0 |
| `MUT_0055_ne_to_eq_mctp_assembler_scratch_axi_write_ingress_51` | `killed` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:51` | `ne_to_eq` | scoreboard failed rows=10 |
| `MUT_0009_state_update_to_self_hold_mctp_assembler_scratch_axi_write_ingress_102` | `survived` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:102` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0087_sub_to_add_mctp_assembler_scratch_pcie_vdm_parser_67` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:67` | `sub_to_add` | test runner returned 0 |
| `MUT_0149_zero_to_one_mctp_assembler_scratch_sram_packer_34` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:34` | `zero_to_one` | test runner returned 0 |
| `MUT_0083_ne_to_eq_mctp_assembler_scratch_pcie_vdm_parser_58` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:58` | `ne_to_eq` | scoreboard failed rows=26 |
| `MUT_0010_state_update_to_self_hold_mctp_assembler_scratch_axi_write_ingress_106` | `survived` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:106` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0102_add_to_sub_mctp_assembler_scratch_context_table_68` | `survived` | `rtl/mctp_assembler_scratch_context_table.sv:68` | `add_to_sub` | test runner returned 0 |
| `MUT_0227_zero_to_one_mctp_assembler_scratch_cdc_35` | `survived` | `rtl/mctp_assembler_scratch_cdc.sv:35` | `zero_to_one` | test runner returned 0 |
| `MUT_0057_eq_to_ne_mctp_assembler_scratch_axi_write_ingress_58` | `survived` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:58` | `eq_to_ne` | test runner returned 0 |
| `MUT_0016_state_update_to_self_hold_mctp_assembler_scratch_context_table_113` | `survived` | `rtl/mctp_assembler_scratch_context_table.sv:113` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0103_add_to_sub_mctp_assembler_scratch_context_table_70` | `killed` | `rtl/mctp_assembler_scratch_context_table.sv:70` | `add_to_sub` | scoreboard failed rows=1 |
| `MUT_0228_zero_to_one_mctp_assembler_scratch_cdc_36` | `survived` | `rtl/mctp_assembler_scratch_cdc.sv:36` | `zero_to_one` | test runner returned 0 |
| `MUT_0084_eq_to_ne_mctp_assembler_scratch_pcie_vdm_parser_62` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:62` | `eq_to_ne` | scoreboard failed rows=10 |
| `MUT_0017_state_update_to_self_hold_mctp_assembler_scratch_context_table_129` | `survived` | `rtl/mctp_assembler_scratch_context_table.sv:129` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0067_add_to_sub_mctp_assembler_scratch_axi_write_ingress_102` | `survived` | `rtl/mctp_assembler_scratch_axi_write_ingress.sv:102` | `add_to_sub` | test runner returned 0 |
