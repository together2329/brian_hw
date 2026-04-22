# ARM Cortex-M0-Style CPU — Module Specification

## 1. Overview

The **arm_m0_cpu** is a 32-bit processor core implementing a minimal subset of the ARMv6-M architecture (Thumb-16 instruction set). It is designed as a teaching and prototyping CPU with multi-cycle execution, supporting 10+ Thumb-16 instructions.

**Key characteristics:**
- Multi-cycle execution (non-pipelined, one instruction at a time)
- 32-bit data path, 16-bit instruction encoding (Thumb)
- Von Neumann bus architecture with separate instruction fetch and data interfaces
- 16 general-purpose registers (R0–R15) with SP, LR, PC aliases
- APSR condition flags (N, Z, C, V) updated by arithmetic instructions
- Single external IRQ input (reserved for future implementation)
- Fully synthesizable SystemVerilog RTL, simulation-verified with Icarus Verilog

---

## 2. Architecture

### 2.1 Block Diagram

```
                    ┌──────────────────────────────────────────┐
                    │              arm_m0_cpu                   │
                    │                                          │
  clk ─────────────►│ clk                                      │
  rst_n ───────────►│ rst_n                                    │
                    │                                          │
                    │  ┌──────────┐   ┌──────────┐            │
  instr_addr ◄──────│──│   FSM    │──►│Instr Reg │            │
  instr_req  ◄──────│──│ (Control)│   │ [15:0]   │            │
  instr_rdata ─────►│──│          │   └────┬─────┘            │
  instr_ack  ──────►│──│          │        │                   │
                    │  │          │   ┌────▼─────┐            │
                    │  │          │──►│  Decode  │            │
                    │  │          │   │ (casez)  │            │
                    │  │          │   └────┬─────┘            │
                    │  │          │        │                   │
                    │  │          │   ┌────▼─────┐   ┌──────┐ │
                    │  │          │──►│   ALU    │──►│ Regs  │ │
                    │  │          │   │(ADD/SUB/ │   │[0:15] │ │
                    │  │          │   │ MOV/CMP) │   │ 32-bit│ │
                    │  │          │   └──────────┘   └──────┘ │
                    │  │          │                          │
  mem_addr   ◄──────│──│          │                          │
  mem_wdata  ◄──────│──│          │                          │
  mem_rdata  ──────►│──│          │                          │
  mem_we     ◄──────│──│          │                          │
  mem_req    ◄──────│──│          │                          │
  mem_ack    ──────►│──│          │                          │
  mem_size   ◄──────│──│          │                          │
                    │  └──────────┘                          │
  irq        ──────►│                                         │
                    └──────────────────────────────────────────┘
```

### 2.2 FSM States

```
                    ┌───────┐
              ┌────►│ RESET │
              │     └───┬───┘
              │         │
              │     ┌───▼───┐
              │     │ FETCH │◄──────────────────────────┐
              │     └───┬───┘                           │
              │         │                               │
              │     ┌───▼────┐                          │
              │     │ DECODE │ (wait for instr_ack)     │
              │     └───┬────┘                          │
              │         │                               │
              │     ┌───▼───┐                           │
              │     │ EXEC  │ (decode + ALU control)    │
              │     └───┬───┘                           │
              │         │                               │
              │     ┌───▼───┐                           │
              │     │  WB   │ (writeback / branch)      │
              │     └───┬───┘                           │
              │         │                               │
              │    ┌────┼────────┐                      │
              │    │    │        │                      │
              │ ┌──▼──┐ │   ┌───▼────┐                 │
              │ │MEM_WR│ │   │MEM_RD  │                 │
              │ └──┬──┘ │   └───┬────┘                 │
              │    │    │       │                      │
              │    └────┴───────┴──────────────────────┘
              │
              └──── (default / rst_n)
```

---

## 3. Supported Instructions

### 3.1 Instruction Summary Table

| # | Instruction | Thumb-16 Encoding | Opcode Bits | Example Hex |
|---|-------------|-------------------|-------------|-------------|
| 1 | MOV Rd, #imm8 | `00100 Rdn[10:8] imm8[7:0]` | [15:11]=00100 | MOV R0,#5 → 0x2005 |
| 2 | CMP Rd, #imm8 | `00101 Rdn[10:8] imm8[7:0]` | [15:11]=00101 | CMP R0,#5 → 0x2805 |
| 3 | ADD Rd, #imm8 | `00110 Rdn[10:8] imm8[7:0]` | [15:11]=00110 | ADD R0,#5 → 0x3005 |
| 4 | SUB Rd, #imm8 | `00111 Rdn[10:8] imm8[7:0]` | [15:11]=00111 | SUB R0,#5 → 0x3805 |
| 5 | ADD Rd, Rn, Rm | `0001100 Rm[8:6] Rn[5:3] Rd[2:0]` | [15:9]=0001100 | ADD R2,R0,R1 → 0x1842 |
| 6 | SUB Rd, Rn, Rm | `0001101 Rm[8:6] Rn[5:3] Rd[2:0]` | [15:9]=0001101 | SUB R2,R0,R1 → 0x1C42 |
| 7 | CMP Rn, Rm (low) | `0100001010 Rm[5:3] Rn[2:0]` | [15:6]=0100001010 | CMP R0,R1 → 0x4288 |
| 8 | STR Rt, [Rn, Rm] | `0101000 Rm[8:6] Rn[5:3] Rt[2:0]` | [15:9]=0101000 | STR R0,[R1,R2] → 0x5088 |
| 9 | LDR Rt, [Rn, Rm] | `0101100 Rm[8:6] Rn[5:3] Rt[2:0]` | [15:9]=0101100 | LDR R0,[R1,R2] → 0x5888 |
| 10 | B (conditional) | `1101 cond[11:8] imm8[7:0]` | [15:12]=1101 | BEQ +2 → 0xD002 |
| 11 | B (unconditional) | `11100 imm11[10:0]` | [15:13]=11100 | B +2 → 0xE001 |
| 12 | NOP | `10111111 00000000` | [15:0]=BF00 | NOP → 0xBF00 |

### 3.2 Instruction Class Details

#### Immediate Operations (MOV, ADD, SUB, CMP #imm8)
- **Format**: `0xx_xxx Rdn[10:8] imm8[7:0]`
- **Operands**: 3-bit register (R0–R7) + 8-bit unsigned immediate
- **Register read**: `exec_rdd` mux reads `regs[{0, Rdn}]` (or PC+4 if R15)
- **ALU input**: `dec_op_a` = register value (for ADD/SUB/CMP) or zero-extended imm8 (for MOV); `dec_op_b` = zero-extended imm8
- **Flag update**: N, Z, C, V updated for ADD/SUB/CMP; not updated for MOV
- **Writeback**: Result written to Rdn for MOV/ADD/SUB; no writeback for CMP

#### Register Operations (ADD, SUB, CMP reg)
- **Format**: `000110x Rm[8:6] Rn[5:3] Rd[2:0]` or `0100001010 Rm[5:3] Rn[2:0]`
- **Operands**: Three 3-bit registers (R0–R7)
- **Register reads**: `exec_rd1` reads Rn, `exec_rd2` reads Rm, `exec_rd3` reads Rd/Rt
- **ALU operation**: ADD/SUB compute Rn ± Rm; CMP computes Rn − Rm
- **Flag update**: N, Z, C, V always updated

#### Memory Operations (LDR, STR)
- **Format**: `010x_xxx Rm[8:6] Rn[5:3] Rt[2:0]`
- **Address calculation**: `mem_addr = regs[Rn] + regs[Rm]` (register + register offset)
- **STR**: Writes `regs[Rt]` to computed address; FSM enters MEM_WR state
- **LDR**: Reads from computed address into `regs[Rt]`; FSM enters MEM_RD state
- **Bus protocol**: Asserts `mem_req`, waits for `mem_ack`, then deasserts
- **Transfer size**: Always 32-bit word (`mem_size = 2'b10`)

#### Branch Operations
- **B unconditional** (`11100 imm11[10:0]`):
  - Target = PC + 4 + SignExtend(imm11) << 1
  - Range: ±2048 halfwords (±4096 bytes)
- **B conditional** (`1101 cond[11:8] imm8[7:0]`):
  - Target = PC + 4 + SignExtend(imm8) << 1
  - Range: ±128 halfwords (±256 bytes)
  - Condition codes: EQ(0), NE(1), CS(2), CC(3), MI(4), PL(5), AL(E)
  - Branch taken only if `cond_met` evaluates true based on APSR flags
- **Pipeline effect**: Branch taken → PC loaded with target, next fetch from new address

---

## 4. Performance Summary

| Instruction Type | Cycles | Notes |
|-----------------|--------|-------|
| NOP | 4 | FETCH + DECODE + EXEC + WB |
| MOV/ADD/SUB imm | 4 | FETCH + DECODE + EXEC + WB |
| ADD/SUB/CMP reg | 4 | FETCH + DECODE + EXEC + WB |
| B (not taken) | 4 | FETCH + DECODE + EXEC + WB |
| B (taken) | 4 | FETCH + DECODE + EXEC + WB (PC jumps) |
| STR | 5+ | FETCH + DECODE + EXEC + WB + MEM_WR(+ack) |
| LDR | 5+ | FETCH + DECODE + EXEC + WB + MEM_RD(+ack+wb) |

**Throughput**: 1 instruction every 4–5+ clock cycles (multi-cycle, non-overlapping)

**Clock frequency**: Not targeted; simulation uses 100 MHz (10 ns period) as reference.

---

## 5. Condition Code Evaluation

| cond | Suffix | Test | Description |
|------|--------|------|-------------|
| 0000 | EQ | Z == 1 | Equal |
| 0001 | NE | Z == 0 | Not equal |
| 0010 | CS | C == 1 | Carry set / unsigned higher or same |
| 0011 | CC | C == 0 | Carry clear / unsigned lower |
| 0100 | MI | N == 1 | Minus / negative |
| 0101 | PL | N == 0 | Plus / positive or zero |
| 1110 | AL | Always | Unconditional |

---

## 6. Design Limitations (Current Implementation)

1. **No high-register operations**: Only R0–R7 supported in most instructions
2. **No PUSH/POP**: Not implemented in current RTL
3. **No BL/BX**: Subroutine call/return not implemented
4. **No LDR literal**: PC-relative load not implemented
5. **No interrupt handler**: IRQ input present but not serviced
6. **No pipeline overlap**: Multi-cycle execution, one instruction at a time
7. **No unaligned access**: All memory accesses must be word-aligned
8. **Unknown opcodes → NOP**: No illegal instruction trap
