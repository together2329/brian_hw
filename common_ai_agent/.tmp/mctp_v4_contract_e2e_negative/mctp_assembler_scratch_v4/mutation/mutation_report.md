# Mutation Guard - mctp_assembler_scratch_v4

- Status: `pass`
- Mode: `advisory`
- Candidates: `32`
- Executed: `32`
- Killed: `16`
- Survived: `16`
- Invalid: `0`
- Kill rate: `0.5`
- Contract unsupported mutation categories: `boundary_flag_flip, interrupt_clear_priority_flip, reset_value_flip`

## Category Kill Rate

| Category | Executed | Killed | Survived | Invalid | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparator_flip` | 8 | 6 | 2 | 0 | `0.75` |
| `constant_flip` | 8 | 1 | 7 | 0 | `0.125` |
| `operator_flip` | 8 | 3 | 5 | 0 | `0.375` |
| `state_update_drop` | 8 | 6 | 2 | 0 | `0.75` |

## Mutants

| Mutant | Status | Location | Rule | Reason |
| --- | --- | --- | --- | --- |
| `MUT_0238_sub_to_add_mctp_assembler_scratch_v4_sram_packer_34` | `survived` | `rtl/mctp_assembler_scratch_v4_sram_packer.sv:34` | `sub_to_add` | test runner returned 0 |
| `MUT_0153_zero_to_one_mctp_assembler_scratch_v4_pcie_vdm_parser_29` | `survived` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:29` | `zero_to_one` | test runner returned 0 |
| `MUT_0237_eq_to_ne_mctp_assembler_scratch_v4_sram_packer_34` | `survived` | `rtl/mctp_assembler_scratch_v4_sram_packer.sv:34` | `eq_to_ne` | test runner returned 0 |
| `MUT_0065_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_55` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:55` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0261_add_to_sub_mctp_assembler_scratch_v4_axi_read_egress_41` | `survived` | `rtl/mctp_assembler_scratch_v4_axi_read_egress.sv:41` | `add_to_sub` | test runner returned 0 |
| `MUT_0337_zero_to_one_mctp_assembler_scratch_v4_cdc_35` | `survived` | `rtl/mctp_assembler_scratch_v4_cdc.sv:35` | `zero_to_one` | test runner returned 0 |
| `MUT_0255_ne_to_eq_mctp_assembler_scratch_v4_descriptor_queue_37` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:37` | `ne_to_eq` | test runner returned 1 |
| `MUT_0066_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_56` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:56` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0263_add_to_sub_mctp_assembler_scratch_v4_axi_read_egress_42` | `killed` | `rtl/mctp_assembler_scratch_v4_axi_read_egress.sv:42` | `add_to_sub` | scoreboard failed rows=4 |
| `MUT_0338_zero_to_one_mctp_assembler_scratch_v4_cdc_36` | `survived` | `rtl/mctp_assembler_scratch_v4_cdc.sv:36` | `zero_to_one` | test runner returned 0 |
| `MUT_0260_eq_to_ne_mctp_assembler_scratch_v4_axi_read_egress_41` | `killed` | `rtl/mctp_assembler_scratch_v4_axi_read_egress.sv:41` | `eq_to_ne` | test runner returned 1 |
| `MUT_0067_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_57` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:57` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0164_sub_to_add_mctp_assembler_scratch_v4_mctp_parser_47` | `killed` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:47` | `sub_to_add` | test runner returned 1 |
| `MUT_0154_zero_to_one_mctp_assembler_scratch_v4_pcie_vdm_parser_36` | `survived` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:36` | `zero_to_one` | test runner returned 0 |
| `MUT_0163_ne_to_eq_mctp_assembler_scratch_v4_mctp_parser_41` | `killed` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:41` | `ne_to_eq` | scoreboard failed rows=2 |
| `MUT_0068_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_58` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:58` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0166_sub_to_add_mctp_assembler_scratch_v4_mctp_parser_49` | `survived` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:49` | `sub_to_add` | test runner returned 0 |
| `MUT_0339_zero_to_one_mctp_assembler_scratch_v4_cdc_37` | `survived` | `rtl/mctp_assembler_scratch_v4_cdc.sv:37` | `zero_to_one` | test runner returned 0 |
| `MUT_0157_ne_to_eq_mctp_assembler_scratch_v4_pcie_vdm_parser_46` | `killed` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:46` | `ne_to_eq` | scoreboard failed rows=26 |
| `MUT_0069_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_59` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:59` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0169_sub_to_add_mctp_assembler_scratch_v4_mctp_parser_53` | `survived` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:53` | `sub_to_add` | test runner returned 0 |
| `MUT_0239_zero_to_one_mctp_assembler_scratch_v4_sram_packer_38` | `survived` | `rtl/mctp_assembler_scratch_v4_sram_packer.sv:38` | `zero_to_one` | test runner returned 0 |
| `MUT_0165_ne_to_eq_mctp_assembler_scratch_v4_mctp_parser_48` | `killed` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:48` | `ne_to_eq` | scoreboard failed rows=3 |
| `MUT_0070_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_60` | `killed` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:60` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0161_sub_to_add_mctp_assembler_scratch_v4_pcie_vdm_parser_55` | `killed` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:55` | `sub_to_add` | scoreboard failed rows=5 |
| `MUT_0155_zero_to_one_mctp_assembler_scratch_v4_pcie_vdm_parser_38` | `killed` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:38` | `zero_to_one` | scoreboard failed rows=4 |
| `MUT_0158_eq_to_ne_mctp_assembler_scratch_v4_pcie_vdm_parser_50` | `killed` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:50` | `eq_to_ne` | scoreboard failed rows=10 |
| `MUT_0071_state_update_to_self_hold_mctp_assembler_scratch_v4_descriptor_queue_61` | `survived` | `rtl/mctp_assembler_scratch_v4_descriptor_queue.sv:61` | `state_update_to_self_hold` | test runner returned 0 |
| `MUT_0244_add_to_sub_mctp_assembler_scratch_v4_sram_packer_56` | `survived` | `rtl/mctp_assembler_scratch_v4_sram_packer.sv:56` | `add_to_sub` | test runner returned 0 |
| `MUT_0156_zero_to_one_mctp_assembler_scratch_v4_pcie_vdm_parser_39` | `survived` | `rtl/mctp_assembler_scratch_v4_pcie_vdm_parser.sv:39` | `zero_to_one` | test runner returned 0 |
| `MUT_0167_ne_to_eq_mctp_assembler_scratch_v4_mctp_parser_50` | `survived` | `rtl/mctp_assembler_scratch_v4_mctp_parser.sv:50` | `ne_to_eq` | test runner returned 0 |
| `MUT_0057_state_update_to_self_hold_mctp_assembler_scratch_v4_sram_packer_62` | `survived` | `rtl/mctp_assembler_scratch_v4_sram_packer.sv:62` | `state_update_to_self_hold` | test runner returned 0 |
