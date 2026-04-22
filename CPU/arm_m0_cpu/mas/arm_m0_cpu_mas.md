# ARM Cortex-M0-Style CPU — Micro Architecture Specification

## 1. Overview

The **arm_m0_cpu** is a 32-bit processor core implementing a minimal subset of the ARMv6-M architecture (Thumb-16 instruction set). It is designed as a teaching and prototyping CPU with ~18 supported Thumb-16 instructions, sufficient to run simple embedded programs.

**Key design goals:**
- Execute a practical subset of Thumb-16 instructions (MOV, ADD, SUB, CMP, LDR, STR, B, BL, BX, PUSH, POP, NOP)
- 3-stage pipeline (Fetch → Decode → Execute) for reasonable throughput
- Simple von Neumann bus (shared instruction fetch and data access)
- 16 general-purpose registers (R0–R15) with SP, LR, PC aliases
- APSR condition flags (N, Z, C, V)
- Single external IRQ with hardware auto-stacking
- Fully synthesizable SystemVerilog RTL, simulation-targeted (Icarus Verilog)

---

## 2. Module Hierarchy + Interface

### 2.1 Instantiation Tree

```
top (testbench or SoC)
└── arm_m0_cpu
    ├── ctrl_fsm        — Pipeline control FSM + interrupt sequencer
    ├── fetch_unit      — PC management, instruction fetch interface
    ├── decode_unit     — Thumb-16 opcode decode, reg read, immediate extract
    ├── execute_unit    — ALU result mux, flag generation, branch resolution
    ├── reg_file        — 16×32-bit register file (2 read + 1 write ports)
    └── alu             — ADD, SUB, MOV, CMP with NZCV flag outputs
```

### 2.2 Top-Level Ports

| Name          | Width | Dir  | Clock Domain | Reset Value | Description                              |
|---------------|-------|------|--------------|-------------|------------------------------------------|
| `clk`         | 1     | in   | —            | —           | System clock                             |
| `rst_n`       | 1     | in   | —            | —           | Active-low synchronous reset             |
| `mem_addr`    | 32    | out  | clk          | 0x00000000  | Memory address bus                       |
| `mem_rdata`   | 32    | in   | clk          | 0x00000000  | Memory read data                         |
| `mem_wdata`   | 32    | out  | clk          | 0x00000000  | Memory write data                        |
| `mem_we`      | 1     | out  | clk          | 0           | Memory write enable (active-high)        |
| `mem_req`     | 1     | out  | clk          | 0           | Memory request (active-high)             |
| `mem_ack`     | 1     | in   | clk          | 0           | Memory acknowledge (active-high)         |
| `mem_size`    | 2     | out  | clk          | 0           | Transfer size: 00=byte, 01=half, 10=word |
| `irq`         | 1     | in   | clk          | 0           | Interrupt request (active-high, level)   |
| `instr_rdata` | 16    | in   | clk          | 0x0000      | Fetched 16-bit Thumb instruction         |
| `instr_req`   | 1     | out  | clk          | 0           | Instruction fetch request                |
| `instr_addr`  | 32    | out  | clk          | 0x00000000  | Instruction fetch address                |

### 2.3 Parameters

| Name              | Default | Description                       |
|-------------------|---------|-----------------------------------|
| `RESET_PC`        | 32'h0   | Initial PC value after reset      |
| `RESET_SP`        | 32'h20004000 | Initial SP value after reset |
| `IRQ_VECTOR_ADDR` | 32'h18  | IRQ handler vector address        |
| `MEM_ADDR_WIDTH`  | 16      | Memory address width (64KB space) |

---

## 3. Feature Operation

### 3.1 Pipeline Operation

The 3-stage pipeline processes one instruction at a time (no overlapping for simplicity in this first implementation). Each instruction flows through:

```
┌─────────┐    ┌─────────┐    ┌─────────┐
│  FETCH  │ →  │ DECODE  │ →  │ EXECUTE │
│         │    │         │    │         │
│ PC→mem  │    │ opcode  │    │ ALU op  │
│ instr   │    │ reg read│    │ mem acc │
│ fetch   │    │ imm ext │    │ flags   │
│         │    │ ctrl sig│    │ wb      │
└─────────┘    └─────────┘    └─────────┘
```

**Pipeline Registers:**
- `FETCH→DECODE`: `fd_instr[15:0]`, `fd_pc[31:0]`, `fd_valid`
- `DECODE→EXECUTE`: `de_reg_read1_data[31:0]`, `de_reg_read2_data[31:0]`, `de_reg_write_addr[3:0]`, `de_reg_write_en`, `de_alu_op[3:0]`, `de_imm[31:0]`, `de_use_imm`, `de_mem_we`, `de_mem_req`, `de_is_branch`, `de_branch_cond[3:0]`, `de_branch_target[31:0]`, `de_is_bx`, `de_bx_reg[31:0]`, `de_is_push`, `de_is_pop`, `de_push_reg_list[8:0]`, `de_pop_reg_list[8:0]`, `de_is_ldr_literal`, `de_is_bl`, `de_pc_plus4[31:0]`, `de_valid`

### 3.2 Feature A: ALU Operations (MOV, ADD, SUB, CMP)

- **Trigger**: Decode stage identifies opcode as MOV/ADD/SUB/CMP
- **Datapath**:
  1. Register file provides Rn and Rm values on read ports
  2. For immediate forms, sign/zero-extend the immediate value
  3. ALU performs: ADD (Rn + Rm/imm), SUB (Rn − Rm/imm), MOV (Rm/imm → Rd), CMP (Rn − Rm/imm, result discarded)
  4. NZCV flags computed from ALU result
  5. Result written back to Rd (except CMP which discards result)
- **Control**: FSM in EXECUTE state, `reg_write_en=1` for MOV/ADD/SUB, `reg_write_en=0` for CMP
- **Output**: Rd updated, APSR flags updated for all four operations

### 3.3 Feature B: Branch (B conditional, B unconditional, BL, BX)

- **Trigger**: Decode stage identifies branch opcode
- **Datapath**:
  1. **B unconditional**: PC ← PC + sign_extended(imm11 << 1)
  2. **B conditional**: Check APSR against condition code; if pass, PC ← PC + sign_extended(imm8 << 1)
  3. **BL**: LR ← (PC of BL instruction + 3) with Thumb bit set; PC ← PC + sign_extended(imm11 << 12 then imm11 << 1). BL is a 32-bit instruction (two 16-bit halves)
  4. **BX**: PC ← Rm, with bit[0] must be 1 for Thumb mode
- **Control**: FSM flushes FETCH and DECODE pipeline stages on taken branch; `pc_sel` mux selects branch target
- **Output**: PC updated, LR updated (BL only)

### 3.4 Feature C: Load/Store (LDR, STR)

- **Trigger**: Decode stage identifies LDR or STR opcode
- **Datapath**:
  1. **STR register**: mem_addr ← Rn + Rm, mem_wdata ← Rt, mem_we ← 1
  2. **LDR register**: mem_addr ← Rn + Rm, Rt ← mem_rdata, mem_we ← 0
  3. **LDR literal**: mem_addr ← (PC & ~3) + (imm8 << 2), Rt ← mem_rdata
- **Control**: FSM enters memory access phase, waits for `mem_ack=1`; for LDR, writes result to register file after ack
- **Output**: Memory written (STR) or register loaded (LDR)

### 3.5 Feature D: Stack Operations (PUSH, POP)

- **Trigger**: Decode stage identifies PUSH or POP opcode
- **Datapath**:
  1. **PUSH {reglist, LR}**: SP ← SP − 4×N (N = popcount of register list); sequentially store each register at SP+4i
  2. **POP {reglist, PC}**: Sequentially load each register from SP+4i; SP ← SP + 4×N
- **Control**: FSM iterates through register list, performing one memory access per register; `push/pop_count` tracks progress
- **Output**: Stack memory updated (PUSH) or registers restored (POP); SP adjusted; PC may be loaded from stack (POP {PC})

### 3.6 Feature E: Interrupt Handling

- **Trigger**: `irq=1` AND FSM is in FETCH state AND interrupts not masked
- **Datapath**:
  1. Hardware auto-stacks: R0, R1, R2, R3, R12, LR, PC, xPSR onto stack (SP decremented by 32)
  2. PC ← value at IRQ vector address (0x00000018)
  3. LR ← EXC_RETURN value (0xFFFFFFF9)
- **Control**: FSM transitions to IRQ_ENTRY state, performs 8 sequential stores, then transitions to IRQ_FETCH
- **Output**: PC points to IRQ handler; context saved on stack; LR holds EXC_RETURN
- **Return**: Handler executes `BX LR` which detects EXC_RETURN pattern and triggers context restore (POP from stack)

### 3.7 Control FSM

| State        | Next State     | Condition                    | Output Actions                                    |
|--------------|----------------|------------------------------|---------------------------------------------------|
| RESET        | FETCH          | rst_n rising edge            | PC←RESET_PC, SP←RESET_SP, all regs←0, APSR←0     |
| FETCH        | DECODE         | instr_req && instr_ack       | fd_instr←instr_rdata, fd_pc←PC, fd_valid←1, PC←PC+2 |
| FETCH        | IRQ_ENTRY      | irq=1                        | Save PC, enter interrupt sequence                 |
| DECODE       | EXECUTE        | fd_valid=1                   | Parse opcode, read regs, generate control signals |
| EXECUTE      | WRITEBACK      | ALU done, no mem access      | Compute result, update flags                       |
| EXECUTE      | EXECUTE        | Memory access in progress    | Wait for mem_ack=1                                |
| EXECUTE      | BRANCH_TAKEN   | Branch condition met         | PC←branch_target, flush pipeline                  |
| WRITEBACK    | FETCH          | reg_write_en                 | Write result to register file                     |
| WRITEBACK    | FETCH          | No write                     | Proceed to next fetch                             |
| IRQ_ENTRY    | IRQ_STACK_PUSH | Entry                        | SP←SP−32, set push count=0                        |
| IRQ_STACK_PUSH| IRQ_FETCH     | All 8 words pushed           | Store context onto stack, iterate                 |
| IRQ_FETCH    | FETCH          | Vector loaded                | PC←irq_handler_addr                               |

---

## 4. Registers (Programmer's Model)

### 4.1 General Purpose Registers

| Register | Alias | Width | Reset Value  | Description                    |
|----------|-------|-------|--------------|--------------------------------|
| R0       | —     | 32    | 0x00000000   | General purpose                 |
| R1       | —     | 32    | 0x00000000   | General purpose                 |
| R2       | —     | 32    | 0x00000000   | General purpose                 |
| R3       | —     | 32    | 0x00000000   | General purpose                 |
| R4       | —     | 32    | 0x00000000   | General purpose                 |
| R5       | —     | 32    | 0x00000000   | General purpose                 |
| R6       | —     | 32    | 0x00000000   | General purpose                 |
| R7       | —     | 32    | 0x00000000   | General purpose                 |
| R8       | —     | 32    | 0x00000000   | General purpose                 |
| R9       | —     | 32    | 0x00000000   | General purpose                 |
| R10      | —     | 32    | 0x00000000   | General purpose                 |
| R11      | —     | 32    | 0x00000000   | General purpose                 |
| R12      | IP    | 32    | 0x00000000   | Intra-procedure scratch register|
| R13      | SP    | 32    | 0x20004000   | Stack pointer (auto-adjust)     |
| R14      | LR    | 32    | 0x00000000   | Link register (set by BL)       |
| R15      | PC    | 32    | 0x00000000   | Program counter (read = PC+4)   |

### 4.2 Application Program Status Register (APSR)

| Bits   | Name | Access | Reset | Description                        |
|--------|------|--------|-------|------------------------------------|
| [31]   | N    | RW     | 0     | Negative flag (result bit[31]=1)   |
| [30]   | Z    | RW     | 0     | Zero flag (result == 0)            |
| [29]   | C    | RW     | 0     | Carry flag (unsigned overflow out) |
| [28]   | V    | RW     | 0     | Overflow flag (signed overflow)    |
| [27:0] | RES  | —      | 0     | Reserved                           |

### 4.3 Internal Control Registers (Not programmer-visible)

| Name           | Width | Reset       | Description                          |
|----------------|-------|-------------|--------------------------------------|
| `irq_masked`   | 1     | 0           | IRQ masking during handler execution |
| `exc_return`   | 1     | 0           | Flag: currently in exception handler |
| `push_counter` | 4     | 0           | Tracks multi-cycle PUSH/POP progress |
| `bl_first_half`| 1     | 0           | Tracks first half of BL instruction  |
| `bl_offset_hi` | 32    | 0           | Stores high offset of BL instruction |

---

## 5. Interrupt

### 5.1 Interrupt Configuration

| Property        | Value                                  |
|-----------------|----------------------------------------|
| Input signal    | `irq` (active-high, level-sensitive)   |
| Vector address  | 0x00000018                             |
| Priority        | Single priority level (no nesting)     |
| Auto-stacked    | R0, R1, R2, R3, R12, LR, PC, xPSR (8 words) |
| EXC_RETURN      | 0xFFFFFFF9 (loaded into LR on entry)   |
| Return mechanism| `BX LR` or `POP {PC}` with EXC_RETURN  |

### 5.2 Interrupt Entry Sequence

1. **Detect**: `irq=1` sampled at FETCH state
2. **Mask**: Set `irq_masked=1` to prevent re-entry
3. **Push context** (8 sequential stores):
   - Store R0 at SP−32, R1 at SP−28, R2 at SP−24, R3 at SP−20
   - Store R12 at SP−16, LR at SP−12, PC at SP−8, xPSR at SP−4
   - SP ← SP − 32
4. **Set LR**: LR ← 0xFFFFFFF9 (EXC_RETURN)
5. **Jump**: PC ← memory[0x00000018] (IRQ vector)

### 5.3 Interrupt Return Sequence

1. Handler executes `BX LR` (LR = 0xFFFFFFF9)
2. CPU detects EXC_RETURN pattern (upper 4 bits = 0xF)
3. **Pop context** (8 sequential loads):
   - Restore xPSR, PC, LR, R12, R3, R2, R1, R0 from stack
   - SP ← SP + 32
4. **Unmask**: Clear `irq_masked=0`
5. Resume execution at restored PC

---

## 6. Memory

### 6.1 Memory Map

| Address Range          | Region      | Access | Description                  |
|------------------------|-------------|--------|------------------------------|
| 0x00000000–0x07FFFFFF  | Code        | R/X    | Program code and vector table|
| 0x08000000–0x0FFFFFFF  | Reserved    | —      | —                            |
| 0x10000000–0x1FFFFFFF  | Reserved    | —      | —                            |
| 0x20000000–0x3FFFFFFF  | SRAM        | R/W    | Data and stack               |
| 0x40000000–0x5FFFFFFF  | Peripheral  | R/W    | Memory-mapped I/O            |
| 0x60000000–0xDFFFFFFF  | Reserved    | —      | —                            |
| 0xE0000000–0xE00FFFFF  | PPB         | R/W    | Private peripheral bus (internal) |
| 0xE0100000–0xFFFFFFFF  | Reserved    | —      | —                            |

### 6.2 Vector Table Layout

| Offset | Contents               | Description              |
|--------|-------------------------|--------------------------|
| 0x00   | Initial SP value        | Loaded into R13 on reset |
| 0x04   | Reset vector            | Loaded into PC on reset  |
| 0x08   | NMI handler             | Not used in this design  |
| 0x0C   | HardFault handler       | Not used in this design  |
| 0x10–0x14 | Reserved            | —                        |
| 0x18   | IRQ handler             | Interrupt service routine|

### 6.3 Bus Protocol

Simple synchronous req/ack protocol:

```
Cycle 1: CPU asserts mem_req=1, mem_addr, mem_wdata (for writes), mem_we
Cycle 2+: Memory asserts mem_ack=1 when data is ready
          For reads: mem_rdata valid on same cycle as mem_ack
Cycle N:  CPU deasserts mem_req after mem_ack received
```

- All signals sampled on rising clock edge
- `mem_size`: 00=byte(8), 01=halfword(16), 10=word(32)
- Instruction fetch uses separate `instr_req`/`instr_addr`/`instr_rdata` port

### 6.4 Memory Sizes for Simulation

| Instance    | Type  | Depth  | Width | R ports | W ports | Description          |
|-------------|-------|--------|-------|---------|---------|----------------------|
| prog_mem    | SRAM  | 32768  | 16    | 1       | 0       | Instruction memory (64KB) |
| data_mem    | SRAM  | 16384  | 32    | 1       | 1       | Data memory (64KB)   |

---

## 7. Timing

### 7.1 Clock

- No specific frequency target (simulation-only design)
- Testbench uses 10ns period (100 MHz nominal) for reference

### 7.2 Instruction Timing

| Instruction Type       | Cycles | Description                        |
|------------------------|--------|------------------------------------|
| NOP                    | 3      | Fetch + Decode + Execute (no-op)   |
| MOV Rd, #imm8          | 3      | Fetch + Decode + Execute + WB      |
| MOV Rd, Rm             | 3      | Fetch + Decode + Execute + WB      |
| ADD Rd, Rn, #imm       | 3      | Fetch + Decode + Execute + WB      |
| ADD Rd, Rn, Rm         | 3      | Fetch + Decode + Execute + WB      |
| SUB Rd, Rn, #imm       | 3      | Fetch + Decode + Execute + WB      |
| SUB Rd, Rn, Rm         | 3      | Fetch + Decode + Execute + WB      |
| CMP Rn, #imm           | 3      | Fetch + Decode + Execute (no WB)   |
| CMP Rn, Rm             | 3      | Fetch + Decode + Execute (no WB)   |
| STR Rt, [Rn, Rm]       | 4+     | Fetch + Decode + Execute + Mem ack |
| LDR Rt, [Rn, Rm]       | 4+     | Fetch + Decode + Execute + Mem ack + WB |
| LDR Rt, [PC, #imm]     | 4+     | Fetch + Decode + Execute + Mem ack + WB |
| B (unconditional)      | 3+2    | Normal + pipeline flush + refetch  |
| B (conditional taken)  | 3+2    | Normal + pipeline flush + refetch  |
| B (conditional not taken)| 3    | Normal execution                   |
| BL                     | 6+     | Two fetches + Decode + Execute + WB|
| BX Rm                  | 3+2    | Normal + pipeline flush + refetch  |
| PUSH {reglist}         | 3+4×N  | Fetch + Decode + N×(Execute+Mem)   |
| POP {reglist}          | 3+4×N  | Fetch + Decode + N×(Execute+Mem+WB)|

### 7.3 Critical Path

- ALU 32-bit addition + flag generation + register file write
- Pipeline register setup/hold between stages

### 7.4 CDC Crossings

- None — single clock domain design

---

## 8. RTL Implementation Notes

### 8.1 Coding Style

- **Language**: SystemVerilog (`.sv` files)
- **Sequential logic**: `always_ff @(posedge clk)` with nonblocking assignments (`<=`)
- **Combinational logic**: `always_comb` with blocking assignments (`=`)
- **Reset**: Synchronous, active-low (`if (!rst_n) ...`)
- **No latches**: Every `always_comb` block assigns all outputs in every branch

### 8.2 Pipeline Register Convention

Pipeline registers use the naming pattern `<source>_<dest>_<signal>`:
- `fd_` prefix: FETCH → DECODE pipeline registers
- `de_` prefix: DECODE → EXECUTE pipeline registers

### 8.3 Signal Naming Convention

| Prefix     | Meaning                   | Example             |
|------------|---------------------------|---------------------|
| `fd_`      | Fetch-to-Decode pipeline  | `fd_instr`          |
| `de_`      | Decode-to-Execute pipeline| `de_alu_op`         |
| `mem_`     | External memory interface | `mem_addr`          |
| `instr_`   | Instruction fetch interface| `instr_rdata`      |
| `pc_`      | PC selection signals      | `pc_sel`            |
| `reg_`     | Register file signals     | `reg_write_en`      |
| `_n` suffix| Active-low signal         | `rst_n`             |

### 8.4 ALU Operation Encoding

| `alu_op` | Operation | Description              |
|----------|-----------|--------------------------|
| 4'b0000  | ADD       | Result = A + B           |
| 4'b0001  | SUB       | Result = A − B           |
| 4'b0010  | MOV       | Result = B               |
| 4'b0011  | CMP       | Flags = A − B, no write  |
| 4'b0100  | AND       | Result = A & B (reserved)|
| 4'b0101  | ORR       | Result = A \| B (reserved)|
| 4'b0110  | NOP       | No operation             |
| 4'b0111  | BX        | PC = B                   |

### 8.5 Condition Code Encoding

| cond | Suffix | Flags Test                    |
|------|--------|-------------------------------|
| 0000 | EQ     | Z == 1                        |
| 0001 | NE     | Z == 0                        |
| 0010 | CS/HS  | C == 1                        |
| 0011 | CC/LO  | C == 0                        |
| 0100 | MI     | N == 1                        |
| 0101 | PL     | N == 0                        |
| 0110 | VS     | V == 1                        |
| 0111 | VC     | V == 0                        |
| 1000 | HI     | C == 1 AND Z == 0            |
| 1001 | LS     | C == 0 OR Z == 1             |
| 1010 | GE     | N == V                        |
| 1011 | LT     | N != V                        |
| 1100 | GT     | Z == 0 AND N == V            |
| 1101 | LE     | Z == 1 OR N != V             |
| 1110 | AL     | Always (unconditional)       |
| 1111 | —      | Undefined                     |

### 8.6 Design Constraints

- All flip-flops use synchronous reset tied to `rst_n`
- No `always_latch` constructs — use `always_ff` with enable logic
- No `casex` — use `casez` only where needed for opcode decode
- All reserved/unused opcode bits decoded as NOP with `default:` in case statements
- Tie-off: unused register file write addresses write to R0 (harmless)

---

## 9. DV Plan

### 9.1 Supported Thumb-16 Instruction Reference

| #  | Instruction        | Encoding (binary)                   | Format             |
|----|--------------------|--------------------------------------|--------------------|
| 1  | MOV Rd, Rm         | 01000110 D Rm(4) Rdn(3)             | High reg           |
| 2  | ADD Rd, Rn, Rm     | 01000100 D Rm(4) Rdn(3)             | High reg           |
| 3  | SUB Rd, Rn, Rm     | 0001101 1 Rm(3) Rn(3) Rd(3)        | Low reg            |
| 4  | ADD Rd, Rn, #imm3  | 0001110 imm3(3) Rn(3) Rd(3)        | Low reg, 3-bit imm |
| 5  | SUB Rd, Rn, #imm3  | 0001111 imm3(3) Rn(3) Rd(3)        | Low reg, 3-bit imm |
| 6  | ADD Rdn, #imm8     | 00110 Rdn(3) imm8(8)               | Low reg, 8-bit imm |
| 7  | MOV Rdn, #imm8     | 00100 Rdn(3) imm8(8)               | Low reg, 8-bit imm |
| 8  | CMP Rdn, #imm8     | 00101 Rdn(3) imm8(8)               | Low reg, 8-bit imm |
| 9  | LDR Rt, [PC, #imm] | 01001 Rt(3) imm8(8)                | PC-relative literal|
| 10 | LDR Rt, [Rn, Rm]   | 0101100 Rm(3) Rn(3) Rt(3)          | Register offset    |
| 11 | STR Rt, [Rn, Rm]   | 0101000 Rm(3) Rn(3) Rt(3)          | Register offset    |
| 12 | B{cond} label      | 1101 cond(4) imm8(8)               | Conditional branch |
| 13 | B label            | 11100 imm11(11)                     | Unconditional branch|
| 14 | BL label           | 11110 imm11(11) then 11111 imm11(11)| 32-bit subroutine |
| 15 | NOP                | 10111111 00000000                   | No operation       |
| 16 | BX Rm              | 01000111 0 Rm(4) 000               | Branch exchange    |
| 17 | PUSH {Rlist, LR}   | 1011 0 M(1) Rlist(8)               | M=1 includes LR   |
| 18 | POP {Rlist, PC}    | 1011 1 M(1) Rlist(8)               | M=1 includes PC   |

### 9.2 Test Sequences

| ID  | Sequence Name          | Steps                                                                                    | Expected Result                                  | Priority |
|-----|------------------------|------------------------------------------------------------------------------------------|--------------------------------------------------|----------|
| S1  | Power-on Reset         | 1. Assert rst_n=0 for 5 cycles 2. Deassert rst_n 3. Check all R0-R15, APSR              | All regs=0 (except SP=0x20004000, PC=0), APSR=0  | High     |
| S2  | MOV Immediate          | 1. MOV R0, #5 2. MOV R1, #10 3. Check R0, R1                                            | R0=5, R1=10                                      | High     |
| S3  | ADD/SUB Immediate      | 1. MOV R0, #10 2. ADD R0, #5 3. MOV R1, #8 4. SUB R1, #3 5. Check R0, R1               | R0=15, R1=5                                      | High     |
| S4  | ADD Register           | 1. MOV R0, #7 2. MOV R1, #8 3. ADD R2, R0, R1 4. Check R2                               | R2=15                                            | High     |
| S5  | CMP + Conditional Branch | 1. MOV R0, #5 2. MOV R1, #5 3. CMP R0, R1 4. BEQ target 5. NOP 6. target: NOP 7. Check PC | PC reached target (BEQ taken), Z=1               | High     |
| S6  | Unconditional Branch   | 1. B forward (skip 2 NOPs) 2. MOV R0, #1 (skipped) 3. target: MOV R0, #2 4. Check R0     | R0=2 (branch taken, MOV #1 skipped)             | High     |
| S7  | LDR/STR                | 1. MOV R0, #0xAB 2. MOV R1, #addr 3. STR R0, [R1, #0] 4. MOV R0, #0 5. LDR R2, [R1, #0] 6. Check R2 | R2=0xAB (memory round-trip)                     | High     |
| S8  | PUSH/POP               | 1. MOV R0, #1 2. MOV R1, #2 3. MOV R2, #3 4. PUSH {R0-R2, LR} 5. MOV R0, #0; MOV R1, #0; MOV R2, #0 6. POP {R0-R2, PC} 7. Check R0, R1, R2 | R0=1, R1=2, R2=3 (restored from stack)         | High     |
| S9  | BL + BX                | 1. BL subroutine 2. continue: MOV R0, #42 3. subroutine: MOV R1, #99 4. BX LR 5. Check R0, R1 | R1=99 (sub ran), R0=42 (continued after return) | High     |
| S10 | NOP                    | 1. MOV R0, #5 2. NOP 3. NOP 4. Check R0                                                | R0=5 (unchanged by NOPs)                         | Medium   |
| S11 | IRQ                    | 1. MOV R0, #1 2. loop: NOP 3. B loop 4. [assert irq during loop] 5. handler: store marker 6. Return  | IRQ handler entered, context saved/restored      | High     |
| S12 | Back-to-back ALU       | 1. MOV R0, #0 2. ADD R0, #1 3. ADD R0, #2 4. ADD R0, #3 5. ADD R0, #4 6. Check R0      | R0=10 (all additions accumulated correctly)      | Medium   |

### 9.3 Test Program Hex Opcodes

Each test sequence uses pre-assembled Thumb-16 machine code loaded into instruction memory at offset 0x00000000. Example hex for S2 (MOV immediate):

```
// MOV R0, #5    → 0010 0 000 00000101 → 0x2005
// MOV R1, #10   → 0010 1 001 00001010 → 0x290A
```

Test programs will be loaded via `$readmemh` into the testbench memory model.

### 9.4 Coverage Goals

**Functional Coverage:**
- [ ] All FSM states visited (RESET, FETCH, DECODE, EXECUTE, WRITEBACK, IRQ_ENTRY, IRQ_STACK_PUSH, IRQ_FETCH)
- [ ] All 18 instructions executed at least once
- [ ] All condition codes tested (EQ, NE at minimum)
- [ ] NZCV flags toggled: N=0/1, Z=0/1, C=0/1, V=0/1
- [ ] Register file: all 16 registers written and read back
- [ ] Memory: successful STR + LDR round-trip
- [ ] Stack: PUSH and POP with varying register list sizes
- [ ] Interrupt: entry, handler execution, return with context restore
- [ ] Back-to-back: no data loss on consecutive operations

**Code Coverage Targets:**
- Line coverage: ≥ 90%
- Branch coverage: ≥ 85%
- Toggle coverage: ≥ 80%

### 9.5 SVA Assertions

- `assert_no_illegal_fsm_state`: FSM never enters undefined state
- `assert_irq_deassert_after_mask`: irq_masked prevents re-entry during handler
- `assert_pc_even`: PC[0] always 0 (Thumb alignment)
- `assert_sp_aligned`: SP[1:0] always 0 (word-aligned)
- `assert_reg_write_one_hot`: At most one write to register file per cycle
- `assert_mem_no_simultaneous_rw`: No simultaneous read and write to same address

### 9.6 Known Corner Cases / Hazards

1. **Read-after-write hazard**: Instruction reads a register that was just written by the previous instruction. Since the pipeline does not overlap, no forwarding needed — the write completes before the next read.
2. **BL 32-bit instruction**: Two consecutive 16-bit fetches required. If interrupt occurs between the two halves, the partial BL must be abandoned or completed atomically. Implementation choice: complete BL atomically (mask IRQ during first half).
3. **SP alignment**: PUSH/POP must maintain word alignment. If SP is not 4-byte aligned, behavior is unpredictable.
4. **Conditional branch offset**: imm8 is sign-extended and shifted left by 1. Range: −256 to +254 bytes relative to PC+4.
5. **LDR literal alignment**: PC is word-aligned (PC & ~3) before adding offset.
6. **EXC_RETURN detection**: BX LR where LR=0xFFFFFFF9 must be detected as exception return, not a normal branch. Pattern: upper nibble of value = 0xF.
7. **Unimplemented instructions**: Any opcode not in the supported set is decoded as NOP (safe execution, no illegal instruction fault in this minimal design).
