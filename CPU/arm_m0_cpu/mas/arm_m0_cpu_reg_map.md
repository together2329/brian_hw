# ARM Cortex-M0-Style CPU — Register Map

## 1. Programmer's Model — General Purpose Registers

The CPU implements 16 × 32-bit general-purpose registers as defined by the ARMv6-M architecture.

| Register | Alias | Reset Value | Access | Description |
|----------|-------|-------------|--------|-------------|
| R0 | — | 0x00000000 | RW | General-purpose scratch register |
| R1 | — | 0x00000000 | RW | General-purpose scratch register |
| R2 | — | 0x00000000 | RW | General-purpose scratch register |
| R3 | — | 0x00000000 | RW | General-purpose scratch register |
| R4 | — | 0x00000000 | RW | General-purpose scratch register |
| R5 | — | 0x00000000 | RW | General-purpose scratch register |
| R6 | — | 0x00000000 | RW | General-purpose scratch register |
| R7 | — | 0x00000000 | RW | General-purpose scratch register |
| R8 | — | 0x00000000 | RW | General-purpose scratch register (not accessible by Thumb-16 low-reg ops) |
| R9 | — | 0x00000000 | RW | General-purpose scratch register (not accessible by Thumb-16 low-reg ops) |
| R10 | — | 0x00000000 | RW | General-purpose scratch register (not accessible by Thumb-16 low-reg ops) |
| R11 | — | 0x00000000 | RW | General-purpose scratch register (not accessible by Thumb-16 low-reg ops) |
| R12 | IP | 0x00000000 | RW | Intra-procedure scratch register |
| R13 | SP | 0x20004000 | RW | Stack Pointer. Word-aligned (bits [1:0] should be 00). |
| R14 | LR | 0x00000000 | RW | Link Register. Stores return address from BL. |
| R15 | PC | 0x00000000 | RW* | Program Counter. Read returns PC+4. Write causes branch. |

**\* PC Special Behavior:**
- Reading R15 via register read port returns `PC + 4` (ARM architectural behavior)
- PC increments by 2 per instruction (16-bit Thumb encoding)
- Direct writes to PC only occur via branch instructions (B, BL, BX)
- PC[0] is always 0 (Thumb mode alignment)

### Register Access by Instruction Type

| Instruction Type | Accessible Registers | Notes |
|-----------------|---------------------|-------|
| MOV/ADD/SUB/CMP #imm8 | R0–R7 (via 3-bit Rdn field) | Low registers only |
| ADD/SUB Rd, Rn, Rm | R0–R7 (via 3-bit fields) | Low registers only |
| CMP Rn, Rm (low) | R0–R7 (via 3-bit fields) | Low registers only |
| STR/LDR Rt, [Rn, Rm] | R0–R7 (via 3-bit fields) | Low registers only |
| B/BEQ/BNE | PC (implicit) | No explicit register field |

---

## 2. Application Program Status Register (APSR)

The APSR contains condition flags set by arithmetic instructions (ADD, SUB, CMP).

```
  31  30  29  28  27                           0
┌───┬───┬───┬───┬───────────────────────────────┐
│ N │ Z │ C │ V │          Reserved              │
└───┴───┴───┴───┴───────────────────────────────┘
```

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [31] | N (Negative) | RW | 0 | Set to 1 when the result of an operation has bit[31] = 1 (negative in signed interpretation). |
| [30] | Z (Zero) | RW | 0 | Set to 1 when the result of an operation equals zero. |
| [29] | C (Carry) | RW | 0 | **ADD**: Set to 1 when 32-bit unsigned addition overflows (carry out = 1). **SUB/CMP**: Set to 1 when the subtraction did NOT borrow (unsigned Rn ≥ Rm). Cleared to 0 when subtraction borrows. |
| [28] | V (Overflow) | RW | 0 | Set to 1 when signed overflow occurs. **ADD**: both inputs same sign, result different sign. **SUB/CMP**: inputs different sign, result different sign from first input. |
| [27:0] | Reserved | — | 0 | Reserved. Reads as 0. |

### Flag Update Rules

| Instruction | N | Z | C | V | Notes |
|-------------|---|---|---|---|-------|
| ADD Rd, Rn, #imm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn + imm8 |
| ADD Rd, Rn, Rm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn + Rm |
| SUB Rd, Rn, #imm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn − imm8 |
| SUB Rd, Rn, Rm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn − Rm |
| CMP Rn, #imm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn − imm8 (result discarded) |
| CMP Rn, Rm | ✓ | ✓ | ✓ | ✓ | Flags set from Rn − Rm (result discarded) |
| MOV Rd, #imm | — | — | — | — | Flags NOT updated by MOV |
| STR / LDR | — | — | — | — | Flags NOT updated by memory ops |
| B / NOP | — | — | — | — | Flags NOT updated |

### Condition Code Usage

| Condition | Suffix | Test | Example |
|-----------|--------|------|---------|
| 0000 | EQ | Z == 1 | After CMP where operands are equal |
| 0001 | NE | Z == 0 | After CMP where operands differ |
| 0010 | CS/HS | C == 1 | Unsigned greater or same |
| 0011 | CC/LO | C == 0 | Unsigned lower |
| 0100 | MI | N == 1 | Result was negative |
| 0101 | PL | N == 0 | Result was positive or zero |
| 1110 | AL | Always | Unconditional branch |

---

## 3. Internal Registers (Not Programmer-Visible)

These registers are used internally by the CPU and are not part of the programmer's model.

| Register | Width | Reset | Description |
|----------|-------|-------|-------------|
| `pc` | 32 | 0x00000000 | Internal program counter (always even, increment by 2) |
| `instr_reg` | 16 | 0x0000 | Latched instruction from fetch stage |
| `state` | 3 | RESET (0) | FSM state register |
| `dec_rd` | 4 | 0 | Decoded destination register number |
| `dec_op_a` | 32 | 0 | ALU operand A (registered) |
| `dec_op_b` | 32 | 0 | ALU operand B (registered) |
| `alu_op` | 4 | 0 (NOP) | ALU operation select (registered) |
| `dec_wen` | 1 | 0 | Register write enable (registered) |
| `dec_is_branch` | 1 | 0 | Branch instruction flag (registered) |
| `dec_is_mem_rd` | 1 | 0 | Memory read flag (registered) |
| `dec_is_mem_wr` | 1 | 0 | Memory write flag (registered) |
| `branch_target` | 32 | 0 | Computed branch target address |
| `branch_taken` | 1 | 0 | Branch was taken this cycle |
| `n_flag` | 1 | 0 | Negative flag register |
| `z_flag` | 1 | 0 | Zero flag register |
| `c_flag` | 1 | 0 | Carry flag register |
| `v_flag` | 1 | 0 | Overflow flag register |

---

## 4. ALU Operation Encoding

| alu_op | Mnemonic | Description |
|--------|----------|-------------|
| 4'd0 | ADD | Result = dec_op_a + dec_op_b; flags updated |
| 4'd1 | SUB | Result = dec_op_a − dec_op_b; flags updated |
| 4'd2 | MOV | Result = dec_op_a; no flag update |
| 4'd3 | CMP | Result = dec_op_a − dec_op_b; flags updated, no register write |
| 4'd4 | AND | Result = dec_op_a & dec_op_b (reserved) |
| 4'd5 | ORR | Result = dec_op_a \| dec_op_b (reserved) |
| 4'd6 | NOP | No operation |
| 4'd7 | LDR | Memory load (ALU computes address) |
| 4'd8 | STR | Memory store (ALU computes address) |
| 4'd9 | B | Branch (no ALU computation) |
