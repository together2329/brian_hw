# Mutation Guard - mctp_assembler_scratch

- Status: `pass`
- Mode: `advisory`
- Candidates: `32`
- Executed: `32`
- Killed: `19`
- Survived: `13`
- Invalid: `0`
- Kill rate: `0.5938`
- Contract unsupported mutation categories: `boundary_flag_flip, interrupt_clear_priority_flip, reset_value_flip`

## Category Kill Rate

| Category | Executed | Killed | Survived | Invalid | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparator_flip` | 8 | 5 | 3 | 0 | `0.625` |
| `constant_flip` | 8 | 3 | 5 | 0 | `0.375` |
| `operator_flip` | 8 | 4 | 4 | 0 | `0.5` |
| `state_update_drop` | 8 | 7 | 1 | 0 | `0.875` |

## Mutants

| Mutant | Status | Location | Rule | Reason |
| --- | --- | --- | --- | --- |
| `MUT_0213_sub_to_add_mctp_assembler_scratch_sram_packer_40` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:40` | `sub_to_add` | test runner returned 0 |
| `MUT_0130_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_29` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:29` | `zero_to_one` | test runner timed out after 30s |
| `MUT_0212_eq_to_ne_mctp_assembler_scratch_sram_packer_37` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:37` | `eq_to_ne` | test runner returned 0 |
| `MUT_0069_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_64` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:64` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0236_add_to_sub_mctp_assembler_scratch_axi_read_egress_40` | `killed` | `rtl/mctp_assembler_scratch_axi_read_egress.sv:40` | `add_to_sub` | scoreboard failed rows=4 |
| `MUT_0211_zero_to_one_mctp_assembler_scratch_sram_packer_29` | `killed` | `rtl/mctp_assembler_scratch_sram_packer.sv:29` | `zero_to_one` | scoreboard failed rows=1 |
| `MUT_0230_ne_to_eq_mctp_assembler_scratch_descriptor_queue_38` | `survived` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:38` | `ne_to_eq` | test runner returned 0 |
| `MUT_0070_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_65` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:65` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0142_sub_to_add_mctp_assembler_scratch_mctp_parser_47` | `survived` | `rtl/mctp_assembler_scratch_mctp_parser.sv:47` | `sub_to_add` | test runner returned 0 |
| `MUT_0313_zero_to_one_mctp_assembler_scratch_cdc_35` | `survived` | `rtl/mctp_assembler_scratch_cdc.sv:35` | `zero_to_one` | test runner returned 0 |
| `MUT_0140_ne_to_eq_mctp_assembler_scratch_mctp_parser_40` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:40` | `ne_to_eq` | scoreboard failed rows=2 |
| `MUT_0071_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_66` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:66` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0239_add_to_sub_mctp_assembler_scratch_axi_read_egress_51` | `survived` | `rtl/mctp_assembler_scratch_axi_read_egress.sv:51` | `add_to_sub` | test runner returned 0 |
| `MUT_0314_zero_to_one_mctp_assembler_scratch_cdc_36` | `survived` | `rtl/mctp_assembler_scratch_cdc.sv:36` | `zero_to_one` | test runner returned 0 |
| `MUT_0134_ne_to_eq_mctp_assembler_scratch_pcie_vdm_parser_46` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:46` | `ne_to_eq` | scoreboard failed rows=26 |
| `MUT_0072_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_67` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:67` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0231_add_to_sub_mctp_assembler_scratch_descriptor_queue_51` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:51` | `add_to_sub` | test runner timed out after 30s |
| `MUT_0131_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_36` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:36` | `zero_to_one` | test runner returned 0 |
| `MUT_0141_ne_to_eq_mctp_assembler_scratch_mctp_parser_46` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:46` | `ne_to_eq` | scoreboard failed rows=3 |
| `MUT_0073_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_68` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:68` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0138_sub_to_add_mctp_assembler_scratch_pcie_vdm_parser_55` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:55` | `sub_to_add` | test runner returned 0 |
| `MUT_0315_zero_to_one_mctp_assembler_scratch_cdc_37` | `survived` | `rtl/mctp_assembler_scratch_cdc.sv:37` | `zero_to_one` | test runner returned 0 |
| `MUT_0238_eq_to_ne_mctp_assembler_scratch_axi_read_egress_48` | `survived` | `rtl/mctp_assembler_scratch_axi_read_egress.sv:48` | `eq_to_ne` | test runner returned 0 |
| `MUT_0074_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_69` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:69` | `state_update_to_self_hold` | test runner returned 1 |
| `MUT_0145_sub_to_add_mctp_assembler_scratch_mctp_parser_58` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:58` | `sub_to_add` | test runner timed out after 30s |
| `MUT_0132_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_38` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:38` | `zero_to_one` | scoreboard failed rows=2 |
| `MUT_0143_ne_to_eq_mctp_assembler_scratch_mctp_parser_48` | `killed` | `rtl/mctp_assembler_scratch_mctp_parser.sv:48` | `ne_to_eq` | test runner timed out after 30s |
| `MUT_0075_state_update_to_self_hold_mctp_assembler_scratch_descriptor_queue_70` | `killed` | `rtl/mctp_assembler_scratch_descriptor_queue.sv:70` | `state_update_to_self_hold` | test runner timed out after 30s |
| `MUT_0219_add_to_sub_mctp_assembler_scratch_sram_packer_65` | `killed` | `rtl/mctp_assembler_scratch_sram_packer.sv:65` | `add_to_sub` | test runner timed out after 30s |
| `MUT_0133_zero_to_one_mctp_assembler_scratch_pcie_vdm_parser_39` | `survived` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:39` | `zero_to_one` | test runner returned 0 |
| `MUT_0135_eq_to_ne_mctp_assembler_scratch_pcie_vdm_parser_50` | `killed` | `rtl/mctp_assembler_scratch_pcie_vdm_parser.sv:50` | `eq_to_ne` | test runner timed out after 30s |
| `MUT_0055_state_update_to_self_hold_mctp_assembler_scratch_sram_packer_71` | `survived` | `rtl/mctp_assembler_scratch_sram_packer.sv:71` | `state_update_to_self_hold` | test runner returned 0 |
