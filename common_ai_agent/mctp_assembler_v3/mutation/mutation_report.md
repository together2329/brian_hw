# Mutation Guard - mctp_assembler_v3

- Status: `pass`
- Mode: `advisory`
- Candidates: `12`
- Executed: `12`
- Killed: `7`
- Survived: `5`
- Invalid: `0`
- Kill rate: `0.5833`
- Contract unsupported mutation categories: `boundary_flag_flip, interrupt_clear_priority_flip, reset_value_flip`

## Category Kill Rate

| Category | Executed | Killed | Survived | Invalid | Kill rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `comparator_flip` | 3 | 2 | 1 | 0 | `0.6667` |
| `constant_flip` | 3 | 2 | 1 | 0 | `0.6667` |
| `operator_flip` | 3 | 1 | 2 | 0 | `0.3333` |
| `state_update_drop` | 3 | 2 | 1 | 0 | `0.6667` |

## Mutants

| Mutant | Status | Location | Rule | Reason |
| --- | --- | --- | --- | --- |
| `MUT_0408_sub_to_add_mctp_assembler_v3_sram_packer_72` | `survived` | `rtl/mctp_assembler_v3_sram_packer.sv:72` | `sub_to_add` | test runner returned 0 |
| `MUT_0404_zero_to_one_mctp_assembler_v3_sram_packer_56` | `killed` | `rtl/mctp_assembler_v3_sram_packer.sv:56` | `zero_to_one` | test runner returned 1 |
| `MUT_0405_eq_to_ne_mctp_assembler_v3_sram_packer_70` | `killed` | `rtl/mctp_assembler_v3_sram_packer.sv:70` | `eq_to_ne` | test runner returned 1 |
| `MUT_0001_state_update_to_self_hold_mctp_assembler_v3_axi_wr_ingress_96` | `killed` | `rtl/mctp_assembler_v3_axi_wr_ingress.sv:96` | `state_update_to_self_hold` | scoreboard failed rows=28 |
| `MUT_0457_add_to_sub_mctp_assembler_v3_axi_rd_payload_82` | `killed` | `rtl/mctp_assembler_v3_axi_rd_payload.sv:82` | `add_to_sub` | test runner returned 1 |
| `MUT_0406_zero_to_one_mctp_assembler_v3_sram_packer_70` | `survived` | `rtl/mctp_assembler_v3_sram_packer.sv:70` | `zero_to_one` | test runner returned 0 |
| `MUT_0456_eq_to_ne_mctp_assembler_v3_axi_rd_payload_75` | `survived` | `rtl/mctp_assembler_v3_axi_rd_payload.sv:75` | `eq_to_ne` | test runner returned 0 |
| `MUT_0055_state_update_to_self_hold_mctp_assembler_v3_axi_rd_payload_121` | `killed` | `rtl/mctp_assembler_v3_axi_rd_payload.sv:121` | `state_update_to_self_hold` | scoreboard failed rows=5 |
| `MUT_0458_sub_to_add_mctp_assembler_v3_axi_rd_payload_83` | `survived` | `rtl/mctp_assembler_v3_axi_rd_payload.sv:83` | `sub_to_add` | test runner returned 0 |
| `MUT_0407_one_to_zero_mctp_assembler_v3_sram_packer_71` | `killed` | `rtl/mctp_assembler_v3_sram_packer.sv:71` | `one_to_zero` | test runner returned 1 |
| `MUT_0082_eq_to_ne_mctp_assembler_v3_axi_wr_ingress_83` | `killed` | `rtl/mctp_assembler_v3_axi_wr_ingress.sv:83` | `eq_to_ne` | scoreboard failed rows=28 |
| `MUT_0056_state_update_to_self_hold_mctp_assembler_v3_axi_rd_payload_134` | `survived` | `rtl/mctp_assembler_v3_axi_rd_payload.sv:134` | `state_update_to_self_hold` | test runner returned 0 |
