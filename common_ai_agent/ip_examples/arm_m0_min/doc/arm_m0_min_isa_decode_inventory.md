# arm_m0_min ISA And Decode Inventory

Status: review aid only. This file is not a requirement approval artifact.

This inventory links the locked requirement scope to the current decode and
ALU RTL. It is meant to help a reviewer check that the implemented CPU is the
minimal ARMv6-M-like teaching/reference CPU described in the approval request.

## Locked Instruction Subset

All 15 locked instruction names are present in the SSOT:

| Operation | SSOT present | Decode opcode | RTL behavior |
|---|---:|---:|---|
| `ADD` | yes | `4'h0` | `ALU_ADD` |
| `SUB` | yes | `4'h1` | `ALU_SUB` |
| `AND` | yes | `4'h2` | `ALU_AND` |
| `ORR` | yes | `4'h3` | `ALU_ORR` |
| `EOR` | yes | `4'h4` | `ALU_EOR` |
| `MOV` | yes | `4'h5` | `ALU_MOV` |
| `CMP` | yes | `4'h6` | `ALU_SUB`, `is_cmp=1` |
| `LDR` | yes | `4'h7` | `is_ldr=1` |
| `STR` | yes | `4'h8` | `is_str=1` |
| `B` | yes | `4'h9` | `is_b=1` |
| `BEQ` | yes | `4'hA` | `is_beq=1` when `nzcv[2]` is set |
| `BNE` | yes | `4'hB` | `is_bne=1` when `nzcv[2]` is clear |
| `LSL` | yes | `4'hC` | `ALU_LSL` |
| `LSR` | yes | `4'hD` | `ALU_LSR` |
| `ASR` | yes | `4'hE` | `ALU_ASR` |

Unsupported opcode values drive `is_undef=1`.

## RTL Evidence

Decode file: `arm_m0_min/rtl/arm_m0_min_id.sv`

- Defines `OP_ADD` through `OP_ASR` as 15 high-nibble opcode constants.
- Selects register fields from `instr16[11:8]`, `instr16[7:4]`, and
  `instr16[3:0]`.
- Rejects non-zero upper halfword bits with `is_undef=1`.
- Maps branch condition decisions through `nzcv[2]`.

ALU file: `arm_m0_min/rtl/arm_m0_min_alu.sv`

- Implements add, subtract, bitwise and/or/xor, move, logical shifts, and
  arithmetic shift.
- Exposes `cmp_eq` and `cmp_neg` for compare/flag behavior in execute logic.

Execute file: `arm_m0_min/rtl/arm_m0_min_ex.sv`

- Instantiates `arm_m0_min_alu`, `arm_m0_min_branch`, and
  `arm_m0_min_mem_if`.
- Owns writeback, flags, fault-halt, branch redirect, and data bus handoff.

## Verification Coverage

Current machine evidence:

- Equivalence goals: 39 total, 39 required, 0 blocked.
- FL-vs-RTL compare: 39 checked, 39 passed, 0 failed.
- Function coverage: 19 / 19 through RTL-observed scoreboard rows.
- Cycle coverage: 17 / 17 through RTL-observed scoreboard rows.

The top-level coverage artifact reports `status=blocked` only because the
human-owned requirement approval gate is still open and structural line/branch
coverage is not claimed in this flow. It still records 100% SSOT-derived
function and cycle coverage through RTL-observed evidence.

## Approval Boundary

This document does not broaden the approved scope. If the user needs production
ARM compatibility, interrupts, exception return, privilege, debug, MPU/MMU,
cache, NVIC, or SysTick, reject the approval request and reopen the SSOT scope.
