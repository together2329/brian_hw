# ARM CPU Microarchitecture Specification (MAS)

---

## §1 — Overview

| Field | Value |
|-------|-------|
| **IP Name** | `arm_cpu` |
| **Revision** | 1.0 |
| **Author** | Auto-generated from RTL |
| **Date** | 2025-01-12 |
| **Language** | SystemVerilog (IEEE 1800) |
| **Target** | FPGA synthesis |
| **RTL Line Count** | ~1,400 lines (11 modules + 1 package) |

### 1.1 Description

`arm_cpu` is a 32-bit ARMv4-compatible processor core. It implements a
**3-stage pipeline** with a 5-state FSM controller and supports a
comprehensive subset of the ARM instruction set including all 16 data
processing operations, load/store with byte access, branch with link,
status register access, and condition-code evaluation.

### 1.2 Key Characteristics

| Parameter | Value |
|-----------|-------|
| Data width | 32 bits |
| Address width | 32 bits |
| Register file | 16 × 32-bit (R0–R15) |
| Instruction memory | 4 KB (1024 × 32-bit), `$readmemh` loaded |
| Data memory | 4 KB (1024 × 32-bit), byte-enable |
| Pipeline stages | 3 (Fetch → Decode/Execute → Memory/Writeback) |
| FSM states | 5 (FETCH, DECODE, EXECUTE, MEMORY, WRITEBACK) |
| ALU operations | 16 (AND, EOR, SUB, RSB, ADD, ADC, SBC, RSC, TST, TEQ, CMP, CMN, ORR, MOV, BIC, MVN) |
| Condition codes | 15 (EQ, NE, CS, CC, MI, PL, VS, VC, HI, LS, GE, LT, GT, LE, AL) |
| Shifter modes | 5 (LSL, LSR, ASR, ROR, RRX) |
| Clock frequency | Up to 100 MHz (typical FPGA) |
| Reset | Active-low asynchronous (`rst_n`) |
| GPIO | Memory-mapped at 0xFFFF_0000 (out) / 0xFFFF_0004 (in) |

### 1.3 Source File Inventory

| # | File | Lines | Role |
|---|------|------:|------|
| 1 | `rtl/arm_decoder.sv` | 166 | Instruction decoder + `arm_defs` package |
| 2 | `rtl/arm_reg_file.sv` | 52 | Register file (16×32, dual-read, single-write) |
| 3 | `rtl/arm_alu.sv` | 174 | Arithmetic Logic Unit (16 operations) |
| 4 | `rtl/arm_barrel_shifter.sv` | 125 | Barrel shifter (LSL/LSR/ASR/ROR/RRX) |
| 5 | `rtl/arm_condition_check.sv` | 39 | Condition code evaluator |
| 6 | `rtl/arm_cpsr.sv` | 87 | Current Program Status Register |
| 7 | `rtl/arm_control.sv` | 184 | Control unit (5-state FSM) |
| 8 | `rtl/arm_imem.sv` | 26 | Instruction memory (4 KB) |
| 9 | `rtl/arm_dmem.sv` | 73 | Data memory (4 KB, byte-enable) |
| 10 | `rtl/arm_cpu_core.sv` | 384 | CPU core datapath integration |
| 11 | `rtl/arm_cpu_top.sv` | 119 | Top-level with memories and GPIO |
| 12 | `tb/arm_cpu_tb.sv` | 308 | Testbench |
| — | **Total RTL** | **1,429** | |

---

## §2 — Interface

### 2.1 Top-Level Module: `arm_cpu_top`

Source: `rtl/arm_cpu_top.sv` (lines 29–46)

#### 2.1.1 Port Table

| Port | Dir | Width | Reset Value | Description |
|------|:---:|------:|:-----------:|-------------|
| `clk` | in | 1 | — | System clock. All registers rising-edge triggered. |
| `rst_n` | in | 1 | — | Active-low asynchronous reset. Initializes PC=0, CPSR=0x000000D3 (SVC mode, IRQ/FIQ disabled), SP(R13)=0x1000, all other regs=0. |
| `gpio_out` | out | 32 | `32'd0` | General-purpose output register. Written via STR to address `0xFFFF_0000`. Latched on posedge `clk` when `dmem_we && dmem_addr==0xFFFF0000`. |
| `gpio_in` | in | 32 | — | General-purpose input. Address `0xFFFF_0004` (read path not implemented in current RTL — no mux in `arm_dmem`). |
| `debug_pc` | out | 32 | `32'h0` | Current Program Counter value (`pc_current` from `arm_cpu_core`). |
| `debug_instr` | out | 32 | `32'hE1A00000` | Currently latched instruction register (`instr` from `arm_cpu_core`). Defaults to NOP after reset. |
| `debug_state` | out | 4 | `3'b000` | Control FSM state encoded as: `000`=FETCH, `001`=DECODE, `010`=EXECUTE, `011`=MEMORY, `100`=WRITEBACK. |
| `debug_reg_r0` | out | 32 | `32'd0` | **⚠ Known issue:** Stubbed to `32'd0` in `arm_cpu_core.sv` (line 382). Not connected to register file. |
| `debug_reg_r1` | out | 32 | `32'd0` | **⚠ Known issue:** Same as above. |
| `debug_reg_r2` | out | 32 | `32'd0` | **⚠ Known issue:** Same as above. |
| `debug_reg_r3` | out | 32 | `32'd0` | **⚠ Known issue:** Same as above. |
| `running` | out | 1 | `1'b0` | CPU active indicator. `running = rst_n`. Deasserted during reset. |

#### 2.1.2 Interface Groups

```
                    arm_cpu_top
                  ┌──────────────┐
  Clock/Reset     │              │
  ──────────────► │ clk          │
  ──────────────► │ rst_n        │
                  │              │
  GPIO            │              │
  ──────────────► │ gpio_in[31]  │
  ◄────────────── │ gpio_out[31] │
                  │              │
  Debug           │              │
  ◄────────────── │ debug_pc[31] │
  ◄────────────── │ debug_instr  │
  ◄────────────── │ debug_state  │
  ◄────────────── │ debug_r0[31] │
  ◄────────────── │ debug_r1[31] │
  ◄────────────── │ debug_r2[31] │
  ◄────────────── │ debug_r3[31] │
  ◄────────────── │ running      │
                  └──────────────┘
```

#### 2.1.3 Internal Interface Buses (not exposed externally)

These signals connect `arm_cpu_core` ↔ `arm_imem` and `arm_cpu_core` ↔ `arm_dmem`
inside `arm_cpu_top`.

**Instruction Memory Bus**

| Signal | Width | Source → Sink | Description |
|--------|------:|:------------:|-------------|
| `imem_addr` | 32 | core → imem | Word-aligned fetch address (from PC) |
| `imem_rdata` | 32 | imem → core | 32-bit instruction word, 1-cycle latency |

**Data Memory Bus**

| Signal | Width | Source → Sink | Description |
|--------|------:|:------------:|-------------|
| `dmem_req` | 1 | core → dmem | Memory request valid |
| `dmem_we` | 1 | core → dmem | Write enable (1=write, 0=read) |
| `dmem_byte` | 1 | core → dmem | Byte access (1=byte, 0=word) |
| `dmem_addr` | 32 | core → dmem | Memory address |
| `dmem_wdata` | 32 | core → dmem | Write data |
| `dmem_rdata` | 32 | dmem → core | Read data, 1-cycle latency |
| `dmem_ready` | 1 | dmem → core | Ready (`= dmem_req`, always single-cycle) |

#### 2.1.4 Reset Behavior

On `rst_n` deassertion (low):
- **PC (R15)** → `32'h0000_0000`
- **CPSR** → `32'h0000_00D3` (SVC mode, IRQ/FIQ disabled, ARM state)
- **SP (R13)** → `32'h0000_1000`
- **R0–R12, R14** → `32'h0000_0000`
- **Instruction register** → `32'hE1A00000` (NOP: `MOV R0, R0`)
- **FSM state** → `FETCH`
- **GPIO output** → `32'd0` (implicit, no explicit reset — relies on no store before reset)

---

## §3 — Architecture & Block Diagram

### 3.1 Top-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           arm_cpu_top                                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        arm_cpu_core                             │    │
│  │                                                                 │    │
│  │  ┌─────┐  ┌──────────┐  ┌──────────┐                          │    │
│  │  │ PC  │  │ Decoder  │  │ Control  │◄── cond_pass              │    │
│  │  │     │  │          │  │   FSM    │                          │    │
│  │  └──┬──┘  └────┬─────┘  └────┬─────┘                          │    │
│  │     │          │             │ control signals                 │    │
│  │     │          ▼             │                                 │    │
│  │     │   ┌──────────────┐    │                                 │    │
│  │     │   │  Condition   │    │                                 │    │
│  │     │   │  Checker     │    │                                 │    │
│  │     │   └──────────────┘    │                                 │    │
│  │     │          ▲             │                                 │    │
│  │     │          │ NZCV        │                                 │    │
│  │     │   ┌──────────────┐    │                                 │    │
│  │     │   │    CPSR      │    │                                 │    │
│  │     │   └──────────────┘    │                                 │    │
│  │     │          ▲ carry       │                                 │    │
│  │     │          │             │                                 │    │
│  │     ▼          ▼             ▼                                 │    │
│  │  ┌──────────────────────────────────┐                         │    │
│  │  │         Register File            │                         │    │
│  │  │   R0–R12, R13(SP), R14(LR),     │                         │    │
│  │  │   R15(PC)                        │                         │    │
│  │  └──────┬───────────┬───────────────┘                         │    │
│  │         │ rdata_a   │ rdata_b                                  │    │
│  │         ▼           ▼                                          │    │
│  │  ┌──────────────────────────────────┐                         │    │
│  │  │       Barrel Shifter             │◄── carry from CPSR      │    │
│  │  │  LSL / LSR / ASR / ROR / RRX    │                         │    │
│  │  └──────────────┬───────────────────┘                         │    │
│  │                 │ shifter_result                              │    │
│  │                 ▼                                             │    │
│  │  ┌──────────────────────────────────┐                         │    │
│  │  │           ALU                    │◄── carry from CPSR      │    │
│  │  │  AND EOR SUB RSB ADD ADC SBC RSC│                         │    │
│  │  │  TST TEQ CMP CMN ORR MOV BIC MVN│                         │    │
│  │  └──────────────┬───────────────────┘                         │    │
│  │                 │ alu_result  ──► NZCV ──► CPSR (if S-bit)   │    │
│  │                 ▼                                             │    │
│  │  ┌──────────────────────────────────┐                         │    │
│  │  │       Write-Back Mux             │                         │    │
│  │  │  00 = ALU result                 │                         │    │
│  │  │  01 = Data memory read           │                         │    │
│  │  │  10 = CPSR (MRS)                 │                         │    │
│  │  └──────────────┬───────────────────┘                         │    │
│  │                 │ wb_result                                   │    │
│  │                 └──────────────────────► RegFile write        │    │
│  │                                                              │    │
│  │  imem_addr ──┐                    ┌── dmem_req/we/byte/addr   │    │
│  │  imem_rdata ◄┘                    └── dmem_wdata             │    │
│  │                                   ──► dmem_rdata ◄──         │    │
│  └──────────┬──────────────────────────────┬─────────────────────┘    │
│             │                              │                          │
│             ▼                              ▼                          │
│  ┌──────────────────┐           ┌──────────────────┐                 │
│  │    arm_imem      │           │    arm_dmem      │                 │
│  │  4KB (1024×32)   │           │  4KB (1024×32)   │                 │
│  │  $readmemh load  │           │  byte-enable     │                 │
│  └──────────────────┘           └──────────────────┘                 │
│                                                                         │
│  GPIO: STR to 0xFFFF0000 ──► gpio_out                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Pipeline Stages

The CPU uses a **3-stage execution pipeline** implemented as a 5-state FSM.
Unlike a classic pipelined processor where stages overlap, this design
processes one instruction at a time through the FSM states.

#### Stage 1: FETCH (state = `FETCH`)

| Action | Detail |
|--------|--------|
| PC output | `pc_current` drives `imem_addr` |
| Memory read | `arm_imem` returns instruction on next clock edge |
| Instruction latch | `imem_rdata` captured into `instr` register |
| State transition | → DECODE |

Source: `arm_cpu_core.sv` lines 217–235

#### Stage 2: DECODE / EXECUTE (states = `DECODE` → `EXECUTE`)

**DECODE state:**

| Action | Detail |
|--------|--------|
| Decode | `arm_decoder` classifies instruction (data-proc, load/store, branch, etc.) |
| Condition check | `arm_condition_check` evaluates `cond[31:28]` against CPSR flags |
| Shifter setup | `shifter_en` asserted for data-proc / load-store / multiply |
| Register read | RegFile port A reads Rn (`rn_addr`), port B reads Rm (`operand2[3:0]`) |
| State transition | → EXECUTE |

**EXECUTE state:**

| Action | Detail |
|--------|--------|
| Shifter operation | Barrel shifter processes operand2 (immediate rotate or register shift) |
| ALU operation | `arm_alu` computes result based on `opcode[24:21]` |
| Flag update | If `s_bit` set and `cond_pass`, ALU NZCV written to CPSR |
| Branch | If `is_branch && cond_pass`: PC ← branch_target, LR ← PC+4 (if BL) |
| Data-proc write | If `is_data_proc && cond_pass`: regfile_we=1, result_sel=00 |
| MSR/MRS | If `is_msr`: CPSR ← Rn. If `is_mrs`: Rd ← CPSR |
| State transition | → MEMORY (if load/store && cond_pass), else → WRITEBACK |

Source: `arm_cpu_core.sv` lines 238–350, `arm_control.sv` lines 95–142

#### Stage 3: MEMORY / WRITEBACK (states = `MEMORY` → `WRITEBACK`)

**MEMORY state** (load/store only):

| Action | Detail |
|--------|--------|
| Address | `Rn + sign-extend(ls_offset)` or `Rn` (post-index) |
| Store | `dmem_wdata ← rf_rdata_b` (Rm), written to `dmem_addr` |
| Load | `dmem_rdata` returned on next clock edge |
| Stall | `stall = 1` (pipeline held for 1 cycle) |
| State transition | → WRITEBACK |

**WRITEBACK state:**

| Action | Detail |
|--------|--------|
| Load writeback | If `is_load && cond_pass`: regfile_we=1, result_sel=01 (mem data → Rd) |
| PC advance | If not taken branch: PC ← PC+4 |
| State transition | → FETCH |

Source: `arm_control.sv` lines 143–170

### 3.3 FSM State Transition Diagram

```
                    ┌─────────────┐
                    │    FETCH    │
                    └──────┬──────┘
                           │ always
                           ▼
                    ┌─────────────┐
                    │   DECODE    │
                    └──────┬──────┘
                           │ always
                           ▼
                    ┌─────────────┐
               ┌────│   EXECUTE   │────┐
               │    └─────────────┘    │
               │ is_load_store         │ else
               │ && cond_pass          │
               ▼                       ▼
        ┌─────────────┐        ┌─────────────┐
        │   MEMORY    │        │  WRITEBACK  │
        └──────┬──────┘        └──────┬──────┘
               │ always               │ always
               └───────┬──────────────┘
                       │
                       ▼
                 back to FETCH
```

### 3.4 Clock Cycles Per Instruction

| Instruction Class | Path | Cycles |
|-------------------|------|:------:|
| Data Processing (ALU) | FETCH → DECODE → EXECUTE → WRITEBACK | 4 |
| Branch (B/BL) | FETCH → DECODE → EXECUTE → WRITEBACK | 4 |
| MRS / MSR | FETCH → DECODE → EXECUTE → WRITEBACK | 4 |
| SWI | FETCH → DECODE → EXECUTE → WRITEBACK | 4 |
| Load (LDR/LDRB) | FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK | 5 |
| Store (STR/STRB) | FETCH → DECODE → EXECUTE → MEMORY → WRITEBACK | 5 |
| LDM/STM (block) | Decoded only — no execute path | N/A |
| MUL | Decoded only — no execute path | N/A |

**Note:** Branch that is not taken still advances PC through the
WRITEBACK state (PC ← PC+4).

---

## §4 — Module Inventory

### 4.1 Hierarchy Tree

```
arm_cpu_top                          rtl/arm_cpu_top.sv
├── arm_cpu_core                     rtl/arm_cpu_core.sv
│   ├── arm_decoder                  rtl/arm_decoder.sv
│   │   └── (imports arm_defs pkg)
│   ├── arm_condition_check          rtl/arm_condition_check.sv
│   ├── arm_cpsr                     rtl/arm_cpsr.sv
│   ├── arm_control                  rtl/arm_control.sv
│   ├── arm_reg_file                 rtl/arm_reg_file.sv
│   ├── arm_barrel_shifter           rtl/arm_barrel_shifter.sv
│   └── arm_alu                      rtl/arm_alu.sv
├── arm_imem                         rtl/arm_imem.sv
└── arm_dmem                         rtl/arm_dmem.sv
```

### 4.2 Package: `arm_defs`

Source: `rtl/arm_decoder.sv` (lines 12–42) | Lines: 31

Constants for instruction class encoding (bits [27:25]) and ALU operation
codes (bits [24:21]). Imported by `arm_cpu_core`.

| Constant | Value | Description |
|----------|-------|-------------|
| `INST_DATA_PROC` | `3'b000` | Data processing (register operand2) |
| `INST_DATA_PROC_IMM` | `3'b001` | Data processing (immediate operand2) |
| `INST_LOAD_STORE` | `3'b010` | Load/store (register offset) |
| `INST_LOAD_STORE_IMM` | `3'b011` | Load/store (immediate offset) |
| `INST_BRANCH` | `3'b101` | Branch |
| `INST_BLOCK_TRANS` | `3'b100` | Block transfer (LDM/STM) |
| `INST_SWI` | `3'b111` | Software interrupt |
| `ALU_AND` – `ALU_MVN` | `4'h0` – `4'hF` | 16 ALU operation mnemonics |

---

### 4.3 Module: `arm_reg_file`

Source: `rtl/arm_reg_file.sv` | Lines: 52

16 × 32-bit register file with dual asynchronous read ports and single
synchronous write port. R13 (SP) initialized to `0x1000` on reset.
R15 (PC) is readable but not writable through the write port
(handled separately by PC logic).

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `rst_n` | in | 1 | Active-low async reset |
| `raddr_a` | in | 4 | Read port A address (Rn) |
| `rdata_a` | out | 32 | Read port A data (returns PC if addr=15) |
| `raddr_b` | in | 4 | Read port B address (Rm) |
| `rdata_b` | out | 32 | Read port B data (returns PC if addr=15) |
| `we` | in | 1 | Write enable |
| `waddr` | in | 4 | Write address (writes to R15 are blocked) |
| `wdata` | in | 32 | Write data |
| `pc_out` | out | 32 | R15 (PC) direct output |

#### Key Behavior
- **Reset:** R0–R15 = 0, except R13 = `0x1000`
- **Write:** Synchronous, posedge `clk`. Writes to R15 (`waddr==4'd15`) are ignored.
- **Read:** Combinational. If `raddr == 4'd15`, returns `pc_out` (R15).

---

### 4.4 Module: `arm_alu`

Source: `rtl/arm_alu.sv` | Lines: 174

16-operation ALU supporting all ARM data-processing opcodes. Produces
32-bit result plus NZCV flags (flags updated only when `update_flags=1`).

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `op_a` | in | 32 | Operand A (Rn value) |
| `op_b` | in | 32 | Operand B (shifter result) |
| `alu_op` | in | 4 | Operation select (see §5) |
| `carry_in` | in | 1 | CPSR carry flag |
| `update_flags` | in | 1 | S-bit: update NZCV outputs |
| `result` | out | 32 | ALU result |
| `flag_n` | out | 1 | Negative flag out |
| `flag_z` | out | 1 | Zero flag out |
| `flag_c` | out | 1 | Carry flag out |
| `flag_v` | out | 1 | Overflow flag out |

#### Key Behavior
- Addition ops (ADD/ADC/CMN): carry = `add_result[32]`, overflow = sign change
- Subtraction ops (SUB/SBC/RSB/RSC/CMP): carry = `~sub_result[32]` (ARM convention), overflow = sign mismatch
- Logic ops (AND/EOR/ORR/BIC/MOV/MVN/TST/TEQ): carry passed through from shifter
- Flag outputs are `0` when `update_flags=0` (except `flag_c` = `carry_in`)

---

### 4.5 Module: `arm_barrel_shifter`

Source: `rtl/arm_barrel_shifter.sv` | Lines: 125

Barrel shifter supporting 5 shift modes. Used for operand2 preprocessing
in data-processing and load/store address calculation.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `operand` | in | 32 | Value to shift |
| `shift_amount` | in | 12 | Shift amount (5-bit used; upper bits for immediate rotate) |
| `shift_type` | in | 2 | `00`=LSL, `01`=LSR, `10`=ASR, `11`=ROR |
| `shift_carry_in` | in | 1 | CPSR carry flag |
| `is_imm` | in | 1 | Immediate operand mode |
| `result` | out | 32 | Shifted result |
| `carry_out` | out | 1 | Carry output from shifter |

#### Key Behavior
- **Immediate mode** (`is_imm=1`): `actual_shift = shift_amount[3:0]`, ROR operation
- **Register mode** (`is_imm=0`): `actual_shift = shift_amount[4:0]`
- **LSL #0:** No shift, carry = `shift_carry_in`
- **LSR #0 (register):** Treated as LSR #32
- **ASR #0 (register):** Treated as ASR #32
- **ROR with shift=0 (register):** RRX (rotate right extended through carry)
- Shift ≥ 32: LSL/LSR produce 0; ASR produces all-sign-bit

---

### 4.6 Module: `arm_decoder`

Source: `rtl/arm_decoder.sv` (lines 44–166) | Lines: 123

Decodes 32-bit ARM instruction into classified control signals.
Classifies by `instr[27:26]` into data-proc, load/store, branch,
block transfer, or SWI. Detects multiply, MRS, and MSR sub-cases.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `instr` | in | 32 | 32-bit ARM instruction |
| `cond` | out | 4 | Condition code `[31:28]` |
| `opcode` | out | 4 | ALU operation `[24:21]` |
| `s_bit` | out | 1 | Set flags `[20]` |
| `rn` | out | 4 | Rn register `[19:16]` |
| `rd` | out | 4 | Rd register `[15:12]` |
| `operand2` | out | 12 | Operand2 field `[11:0]` |
| `signed_offset` | out | 24 | Branch offset `[23:0]` |
| `rd_ls` | out | 4 | Load/store Rd `[15:12]` |
| `ls_offset` | out | 12 | Load/store offset `[11:0]` |
| `reg_list` | out | 16 | Block transfer register list `[15:0]` |
| `is_data_proc` | out | 1 | Data processing instruction |
| `is_imm_op2` | out | 1 | Immediate operand2 (bit `[25]`) |
| `is_load_store` | out | 1 | Load/Store instruction |
| `is_load` | out | 1 | Load (L-bit `[20]`) |
| `is_store` | out | 1 | Store |
| `is_byte` | out | 1 | Byte access (B-bit `[22]`) |
| `is_pre_index` | out | 1 | Pre-indexed (P-bit `[24]`) |
| `is_writeback` | out | 1 | Writeback (W-bit `[21]`) |
| `is_branch` | out | 1 | Branch instruction |
| `is_branch_link` | out | 1 | Branch with Link (L-bit `[24]`) |
| `is_block_trans` | out | 1 | Block transfer (LDM/STM) |
| `is_swi` | out | 1 | Software interrupt |
| `is_mul` | out | 1 | Multiply instruction |
| `is_msr` | out | 1 | MSR instruction |
| `is_mrs` | out | 1 | MRS instruction |

#### Decode Rules

| `instr[27:26]` | Class | Sub-detection |
|:--------------:|-------|---------------|
| `00` | Data processing | If `[7]=1 && [4]=1` → MUL; if opcode=`2h`, Rd=`Fh` → MSR; if opcode=`Fh`, Rn=`Fh` → MRS |
| `01` | Load/Store | L=`[20]`, B=`[22]`, P=`[24]`, W=`[21]`, I=`~[25]` |
| `10`, `[25]=1` | Branch | L=`[24]` (BL) |
| `10`, `[25]=0` | Block transfer | L=`[20]`, W=`[21]` |
| `11`, `[25]=1` | SWI | — |
| `11`, `[25]=0` | Coprocessor | Not implemented |

---

### 4.7 Module: `arm_condition_check`

Source: `rtl/arm_condition_check.sv` | Lines: 39

Purely combinational. Evaluates 4-bit condition code against CPSR NZCV
flags. Outputs single `cond_pass` bit.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `cond` | in | 4 | Condition field `[31:28]` |
| `flag_n` | in | 1 | CPSR Negative |
| `flag_z` | in | 1 | CPSR Zero |
| `flag_c` | in | 1 | CPSR Carry |
| `flag_v` | in | 1 | CPSR Overflow |
| `cond_pass` | out | 1 | 1 = condition satisfied |

---

### 4.8 Module: `arm_cpsr`

Source: `rtl/arm_cpsr.sv` | Lines: 87

Current Program Status Register. Stores NZCV flags, IRQ/FIQ disable bits,
Thumb state, and processor mode. Updated by ALU flags (when S-bit) or
MSR instruction.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `rst_n` | in | 1 | Active-low async reset |
| `update_flags` | in | 1 | Write NZCV from ALU |
| `flag_n_in` | in | 1 | ALU Negative |
| `flag_z_in` | in | 1 | ALU Zero |
| `flag_c_in` | in | 1 | ALU Carry |
| `flag_v_in` | in | 1 | ALU Overflow |
| `msr_we` | in | 1 | MSR write enable |
| `msr_data` | in | 32 | MSR write data (from Rn) |
| `flag_n` | out | 1 | CPSR N (bit 31) |
| `flag_z` | out | 1 | CPSR Z (bit 30) |
| `flag_c` | out | 1 | CPSR C (bit 29) |
| `flag_v` | out | 1 | CPSR V (bit 28) |
| `cpsr_out` | out | 32 | Full 32-bit CPSR read |
| `mode` | out | 5 | Processor mode (bits 4:0) |
| `thumb` | out | 1 | Thumb state (bit 5) |
| `fiq_disable` | out | 1 | FIQ disable (bit 14) |
| `irq_disable` | out | 1 | IRQ disable (bit 15) |

#### Key Behavior
- **Reset value:** `0x000000D3` = SVC mode (`0x13`), IRQ/FIQ disabled, ARM state
- **MSR priority:** `msr_we` takes precedence over `update_flags`
- **MSR writes:** Only bits [31:28] (NZCV), [15] (I), [14] (F), [5] (T), [4:0] (M)

---

### 4.9 Module: `arm_control`

Source: `rtl/arm_control.sv` | Lines: 184

5-state FSM control unit. Generates all datapath control signals based on
decoded instruction type and condition evaluation. See §7 for full
signal tables.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `rst_n` | in | 1 | Active-low async reset |
| `is_data_proc` | in | 1 | From decoder |
| `is_imm_op2` | in | 1 | From decoder |
| `is_load_store` | in | 1 | From decoder |
| `is_load` | in | 1 | From decoder |
| `is_store` | in | 1 | From decoder |
| `is_byte` | in | 1 | From decoder |
| `is_pre_index` | in | 1 | From decoder |
| `is_writeback` | in | 1 | From decoder |
| `is_branch` | in | 1 | From decoder |
| `is_branch_link` | in | 1 | From decoder |
| `is_block_trans` | in | 1 | From decoder |
| `is_swi` | in | 1 | From decoder |
| `is_mul` | in | 1 | From decoder |
| `is_msr` | in | 1 | From decoder |
| `is_mrs` | in | 1 | From decoder |
| `cond_pass` | in | 1 | From condition checker |
| `regfile_we` | out | 1 | Register file write enable |
| `flags_we` | out | 1 | CPSR flag write enable |
| `pc_we` | out | 1 | PC write enable |
| `pc_sel` | out | 1 | PC source: 0=+4, 1=branch target |
| `lr_we` | out | 1 | Link register write (BL) |
| `mem_req` | out | 1 | Data memory request |
| `mem_we` | out | 1 | Data memory write enable |
| `mem_byte` | out | 1 | Byte access |
| `result_sel` | out | 2 | WB mux: 00=ALU, 01=mem, 10=CPSR |
| `alu_op_en` | out | 1 | ALU operation valid |
| `shifter_en` | out | 1 | Shifter enable |
| `shift_imm_sel` | out | 1 | Immediate shift select |
| `msr_we` | out | 1 | MSR CPSR write |
| `stall` | out | 1 | Pipeline stall |

#### FSM Encoding

| State | Code | Description |
|-------|:----:|-------------|
| `FETCH` | `3'b000` | Instruction fetch from imem |
| `DECODE` | `3'b001` | Decode + register read |
| `EXECUTE` | `3'b010` | ALU/shifter/branch |
| `MEMORY` | `3'b011` | Data memory access (load/store only) |
| `WRITEBACK` | `3'b100` | Register write-back + PC advance |

---

### 4.10 Module: `arm_imem`

Source: `rtl/arm_imem.sv` | Lines: 26

4 KB instruction memory (1024 × 32-bit). Synchronous read with 1-cycle
latency. Loaded via `$readmemh("arm_program.hex", mem)`.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `addr` | in | 32 | Word-aligned address (bits [11:2] used) |
| `instr` | out | 32 | Instruction output (registered) |

---

### 4.11 Module: `arm_dmem`

Source: `rtl/arm_dmem.sv` | Lines: 73

4 KB data memory (1024 × 32-bit). Synchronous read/write with 1-cycle
latency. Supports byte-lane writes and zero-extended byte reads.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `rst_n` | in | 1 | Active-low async reset |
| `mem_req` | in | 1 | Request valid |
| `mem_we` | in | 1 | Write enable |
| `mem_byte` | in | 1 | Byte access |
| `addr` | in | 32 | Address (bits [11:2] + lane from [1:0]) |
| `wdata` | in | 32 | Write data |
| `rdata` | out | 32 | Read data (registered) |
| `mem_ready` | out | 1 | Always `= mem_req` (single-cycle) |

#### Key Behavior
- **Byte write:** Lane selected by `addr[1:0]`, only `wdata[7:0]` used
- **Byte read:** Zero-extended from selected lane
- **Word write/read:** Full 32-bit, `addr[1:0]` ignored
- **Init:** All zeros

---

### 4.12 Module: `arm_cpu_core`

Source: `rtl/arm_cpu_core.sv` | Lines: 384

CPU core datapath integration. Instantiates decoder, condition check,
CPSR, control, register file, barrel shifter, and ALU. Contains PC
logic, branch target calculation, load/store address calculation, and
write-back mux.

#### Ports

| Port | Dir | Width | Description |
|------|:---:|------:|-------------|
| `clk` | in | 1 | System clock |
| `rst_n` | in | 1 | Active-low async reset |
| `imem_addr` | out | 32 | Instruction memory address (PC) |
| `imem_rdata` | in | 32 | Instruction memory data |
| `dmem_req` | out | 1 | Data memory request |
| `dmem_we` | out | 1 | Data memory write enable |
| `dmem_byte` | out | 1 | Byte access |
| `dmem_addr` | out | 32 | Data memory address |
| `dmem_wdata` | out | 32 | Data memory write data |
| `dmem_rdata` | in | 32 | Data memory read data |
| `dmem_ready` | in | 1 | Data memory ready |
| `debug_pc` | out | 32 | Current PC |
| `debug_instr` | out | 32 | Current instruction |
| `debug_state` | out | 4 | FSM state |
| `debug_reg_r0` | out | 32 | ⚠ Stubbed to 0 |
| `debug_reg_r1` | out | 32 | ⚠ Stubbed to 0 |
| `debug_reg_r2` | out | 32 | ⚠ Stubbed to 0 |
| `debug_reg_r3` | out | 32 | ⚠ Stubbed to 0 |

---

### 4.13 Module: `arm_cpu_top`

Source: `rtl/arm_cpu_top.sv` | Lines: 119

Top-level wrapper. Instantiates `arm_cpu_core`, `arm_imem`, `arm_dmem`.
Contains GPIO memory-mapped IO logic.

#### Ports

See §2.1.1 for full port table.

#### Key Behavior
- GPIO output latched on posedge `clk` when `dmem_req && dmem_we && dmem_addr == 0xFFFF0000`
- `running = rst_n` (active when not in reset)

---

## §5 — Instruction Set Support Matrix

### 5.1 Data Processing Instructions

Encoding: `[31:28] cond | [27:26] 00 | [25] I | [24:21] opcode | [20] S | [19:16] Rn | [15:12] Rd | [11:0] operand2`

| Mnemonic | Opcode [24:21] | Operation | Flags (S=1) | RTL Status |
|----------|:--------------:|-----------|:-----------:|:----------:|
| AND | `4'h0` | Rd = Rn AND Op2 | NZC from shifter | ✅ Full |
| EOR | `4'h1` | Rd = Rn XOR Op2 | NZC from shifter | ✅ Full |
| SUB | `4'h2` | Rd = Rn − Op2 | NZCV | ✅ Full |
| RSB | `4'h3` | Rd = Op2 − Rn | NZCV | ✅ Full |
| ADD | `4'h4` | Rd = Rn + Op2 | NZCV | ✅ Full |
| ADC | `4'h5` | Rd = Rn + Op2 + C | NZCV | ✅ Full |
| SBC | `4'h6` | Rd = Rn − Op2 − !C | NZCV | ✅ Full |
| RSC | `4'h7` | Rd = Op2 − Rn − !C | NZCV | ✅ Full |
| TST | `4'h8` | Rn AND Op2 (no write) | NZC from shifter | ✅ Full |
| TEQ | `4'h9` | Rn XOR Op2 (no write) | NZC from shifter | ✅ Full |
| CMP | `4'hA` | Rn − Op2 (no write) | NZCV | ✅ Full |
| CMN | `4'hB` | Rn + Op2 (no write) | NZCV | ✅ Full |
| ORR | `4'hC` | Rd = Rn OR Op2 | NZC from shifter | ✅ Full |
| MOV | `4'hD` | Rd = Op2 | NZC from shifter | ✅ Full |
| BIC | `4'hE` | Rd = Rn AND NOT Op2 | NZC from shifter | ✅ Full |
| MVN | `4'hF` | Rd = NOT Op2 | NZC from shifter | ✅ Full |

**Operand2 encoding:**

| Bit [25] | Type | Format |
|:--------:|------|--------|
| 1 | Immediate | `{4'b0, rotate_imm[3:0], imm8[7:0]}` → ROR by rotate_imm of imm8 |
| 0 | Register | `{shift_amount[4:0], shift_type[1:0], 0, Rm[3:0]}` |

**Note:** The immediate rotate in the RTL uses `shift_amount[3:0]` directly
instead of `2 * rotate_imm` as specified in the ARM Architecture Reference
Manual. See §8.6 for details.

### 5.2 Load / Store Instructions

Encoding: `[31:28] cond | [27:26] 01 | [25] I | [24] P | [23] U | [22] B | [21] W | [20] L | [19:16] Rn | [15:12] Rd | [11:0] offset`

| Mnemonic | L [20] | B [22] | Operation | RTL Status |
|----------|:------:|:------:|-----------|:----------:|
| LDR Rd, [Rn, #imm12] | 1 | 0 | Load word, immediate offset | ✅ Full |
| STR Rd, [Rn, #imm12] | 0 | 0 | Store word, immediate offset | ✅ Full |
| LDRB Rd, [Rn, #imm12] | 1 | 1 | Load byte, zero-extended | ✅ Full |
| STRB Rd, [Rn, #imm12] | 0 | 1 | Store byte | ✅ Full |
| LDR Rd, [Rn, Rm] | 1 | 0 | Load word, register offset | ⚠ Decoded only — shifter path not connected for register offset |
| STR Rd, [Rn, Rm] | 0 | 0 | Store word, register offset | ⚠ Same |

**Addressing mode bits:**

| Bit | Name | Value | Meaning in RTL |
|:---:|:----:|:-----:|----------------|
| [24] P | Pre/Post | 1=Pre, 0=Post | Pre: add offset before access. Post: use base directly. ⚠ Post-index offset not applied after access. |
| [23] U | Up/Down | 1=Up, 0=Down | ⚠ Named `is_pre_index` in decoder — misleading. Offset direction always Up in current address calc. |
| [21] W | Writeback | 1=W, 0=no W | Decoded as `is_writeback`. No writeback logic in datapath. |
| [25] I | Immediate | 0=imm, 1=reg | Inverted in decoder: `is_imm_op2 = ~instr[25]` |

### 5.3 Branch Instructions

Encoding: `[31:28] cond | [27:25] 101 | [24] L | [23:0] signed_offset`

| Mnemonic | L [24] | Operation | RTL Status |
|----------|:------:|-----------|:----------:|
| B {offset} | 0 | PC ← PC + 8 + (offset << 2) | ✅ Branch works |
| BL {offset} | 1 | LR ← PC + 4, then branch | ⚠ **BUG:** `lr_we` block is empty — LR never written (see §8.1) |

**Branch target calculation (from `arm_cpu_core.sv`):**
```
branch_target = pc_plus8 + sign_extend(signed_offset) << 2
```

### 5.4 Block Transfer Instructions (LDM / STM)

Encoding: `[31:28] cond | [27:25] 100 | [24] P | [23] U | [22] S | [21] W | [20] L | [19:16] Rn | [15:0] register_list`

| Mnemonic | L [20] | Operation | RTL Status |
|----------|:------:|-----------|:----------:|
| STM Rn, {reg_list} | 0 | Store multiple | ❌ Decoded only — no execute/writeback logic in control |
| LDM Rn, {reg_list} | 1 | Load multiple | ❌ Decoded only — same |

**Note:** `is_block_trans` is decoded and `reg_list[15:0]` is extracted, but
`arm_control` has no handling for block transfer in any FSM state.

### 5.5 Multiply Instructions

Encoding: `[31:28] cond | [27:22] 000000 | [21] A | [20] S | [19:16] Rd | [15:12] Rn | [11:8] Rs | [7:4] 1001 | [3:0] Rm`

| Mnemonic | Operation | RTL Status |
|----------|-----------|:----------:|
| MUL | Rd = Rm × Rs | ❌ Decoded only — no execute logic |
| MLA | Rd = Rm × Rs + Rn | ❌ Decoded only |

**Note:** `is_mul` is detected by the decoder (pattern: `[7]=1 && [4]=1`),
but `arm_control` has no handling for multiply in any FSM state.

### 5.6 Status Register Instructions

| Mnemonic | Encoding | Operation | RTL Status |
|----------|----------|-----------|:----------:|
| MRS Rd, CPSR | opcode=`Fh`, Rn=`Fh`, S=0 | Rd ← CPSR | ⚠ Partial — uses `result_sel=00` (ALU path), CPSR should use `result_sel=10` |
| MSR CPSR, Rm | opcode=`2h`, Rd=`Fh`, S=0 | CPSR ← Rn | ✅ Works via `msr_we` → CPSR write |

### 5.7 Software Interrupt

Encoding: `[31:28] cond | [27:24] 1111 | [23:0] comment`

| Mnemonic | Operation | RTL Status |
|----------|-----------|:----------:|
| SWI imm24 | Jump to SWI vector | ⚠ Partial — control sets `pc_sel=1` but `branch_target` is not the SWI vector (0x08) |

### 5.8 Condition Codes

All 15 condition codes are fully implemented in `arm_condition_check`:

| Code [31:28] | Suffix | Condition | Test |
|:------------:|:------:|-----------|------|
| `0000` | EQ | Equal | Z = 1 |
| `0001` | NE | Not equal | Z = 0 |
| `0010` | CS / HS | Carry set / unsigned higher or same | C = 1 |
| `0011` | CC / LO | Carry clear / unsigned lower | C = 0 |
| `0100` | MI | Minus / negative | N = 1 |
| `0101` | PL | Plus / positive or zero | N = 0 |
| `0110` | VS | Overflow / V set | V = 1 |
| `0111` | VC | No overflow / V clear | V = 0 |
| `1000` | HI | Unsigned higher | C = 1 AND Z = 0 |
| `1001` | LS | Unsigned lower or same | C = 0 OR Z = 1 |
| `1010` | GE | Signed greater or equal | N = V |
| `1011` | LT | Signed less than | N ≠ V |
| `1100` | GT | Signed greater than | Z = 0 AND N = V |
| `1101` | LE | Signed less than or equal | Z = 1 OR N ≠ V |
| `1110` | AL | Always | 1 |
| `1111` | NV | Never (reserved) | 0 |

### 5.9 Barrel Shifter Modes

| Shift Type | Code [6:5] | Description | RTL Status |
|:----------:|:----------:|-------------|:----------:|
| LSL | `00` | Logical Shift Left | ✅ Full |
| LSR | `00` + amt=0 | Treated as LSR #32 | ✅ Full |
| LSR | `01` | Logical Shift Right | ✅ Full |
| ASR | `00` + amt=0 | Treated as ASR #32 | ✅ Full |
| ASR | `10` | Arithmetic Shift Right | ✅ Full |
| ROR | `11` | Rotate Right | ✅ Full |
| RRX | `11` + amt=0 | Rotate Right Extended through carry | ✅ Full |

### 5.10 Summary

| Category | Total | ✅ Full | ⚠ Partial / Buggy | ❌ Decoded Only |
|----------|:-----:|:-------:|:-----------------:|:--------------:|
| Data Processing | 16 | 16 | — | — |
| Load / Store | 6 | 4 | 2 (reg offset) | — |
| Branch | 2 | 1 (B) | 1 (BL bug) | — |
| Block Transfer | 2 | — | — | 2 |
| Multiply | 2 | — | — | 2 |
| Status Register | 2 | 1 (MSR) | 1 (MRS path) | — |
| SWI | 1 | — | 1 (no vector) | — |
| Condition Codes | 15+1 | 16 | — | — |
| Shifter Modes | 5 | 5 | — | — |

---

## §6 — Datapath Description

### 6.1 Overview

The datapath is organized around a register file with two read ports and one
write port. Data flows from registers through the barrel shifter and ALU,
with a write-back multiplexer selecting the final result destination.

All datapath logic is **combinational** between pipeline registers (PC,
instruction register, CPSR, and register file). The only sequential elements
are clocked by the single `clk` domain with async `rst_n` reset.

### 6.2 Key Muxes and Routing

#### Register Read Address Muxes

```
rf_raddr_a = rn_addr              // always instr[19:16] = Rn
rf_raddr_b = operand2[3:0]        // always instr[3:0] = Rm
```

Source: `arm_cpu_core.sv` lines 281–282

#### Shifter Operand Mux

```
shifter_operand = is_imm_op2 ? {24'd0, operand2[7:0]}    // immediate: zero-pad imm8
                              : rf_rdata_b;               // register: Rm value
```

```
shifter_amount = is_imm_op2 ? {7'd0, operand2[11:8]}     // immediate: rotate_imm[3:0]
                            : {7'd0, operand2[11:7]};    // register: shift_imm[4:0]
shifter_type   = is_imm_op2 ? 2'b11                       // immediate: always ROR
                            : operand2[6:5];              // register: from instruction
```

Source: `arm_cpu_core.sv` lines 297–305

#### Write-Back Result Mux

```
case (result_sel)
    2'b00: wb_result = alu_result;      // ALU output (data proc, MRS-buggy)
    2'b01: wb_result = dmem_rdata;      // Memory load data
    2'b10: wb_result = cpsr_out;        // MRS: CPSR read
    default: wb_result = alu_result;
endcase
```

Source: `arm_cpu_core.sv` lines 362–369

#### PC Source Mux

```
pc_next = pc_sel ? branch_target      // branch taken
                 : pc_plus4;          // sequential
```

Source: `arm_cpu_core.sv` lines 220–228

### 6.3 Datapath Paths

#### Path 1: Data Processing (Register Operand)

```
instr[19:16]──►rf_raddr_a──►registers[Rn]──►rf_rdata_a──►alu_op_a──┐
instr[3:0]───►rf_raddr_b──►registers[Rm]──►rf_rdata_b──►shifter──►alu_op_b──►ALU
                                                                    │
ALU result──►wb_result (sel=00)──►rf_wdata──►registers[Rd] ◄──instr[15:12]
ALU NZCV──►CPSR (if S-bit && cond_pass)
```

**Example:** `ADD R2, R0, R1` → `R2 = R0 + R1`

#### Path 2: Data Processing (Immediate Operand)

```
instr[7:0]──►{24'd0, imm8}──►shifter_operand──►barrel_shifter──►alu_op_b
instr[11:8]──►rotate_imm──►shifter_amount     (type=ROR)
                                                          │
instr[19:16]──►rf_rdata_a──►alu_op_a─────────────────────►ALU
                                                          │
ALU result──►wb_result (sel=00)──►registers[Rd]
```

**Example:** `MOV R0, #5` → `R0 = 5` (rotate_imm=0, imm8=5, ROR by 0 = 5)

#### Path 3: Branch

```
instr[23:0]──►sign_extend──►<< 2──►+ pc_plus8──►branch_target
                                               │
                              pc_sel=1 ────────►PC ◄── pc_we=1
```

Branch target formula:
```
branch_target = (pc_current + 8) + sign_extend_30({signed_offset, 2'b00})
```

Source: `arm_cpu_core.sv` line 238

**BL additional path (intended but buggy):**
```
lr_we=1 ──► should write pc_plus4 to R14, but always_ff block is empty
```

#### Path 4: Load

```
EXECUTE state:
  instr[19:16]──►rf_rdata_a──►ls_base_addr──┐
  instr[11:0]──►sign_extend──►offset───────►├──+──►mem_addr_calc──►dmem_addr

MEMORY state:
  dmem_rdata ◄── dmem (1 cycle latency)

WRITEBACK state:
  dmem_rdata──►wb_result (sel=01)──►registers[Rd] ◄── instr[15:12]
```

Source: `arm_cpu_core.sv` lines 352–354, `arm_control.sv` lines 152–155

#### Path 5: Store

```
EXECUTE state:
  instr[19:16]──►rf_rdata_a──►ls_base_addr──┐
  instr[11:0]──►sign_extend──►offset───────►├──+──►mem_addr_calc──►dmem_addr

MEMORY state:
  instr[3:0]──►rf_raddr_b──►registers[Rm]──►rf_rdata_b──►dmem_wdata──►dmem
```

Source: `arm_cpu_core.sv` lines 352–354, 359

**Note:** Store data (`dmem_wdata`) always comes from `rf_rdata_b` which is
`registers[operand2[3:0]]`. For store instructions, this should be
`registers[Rd]` (instr[15:12]) for `STR Rd, [Rn, #off]`. Current RTL reads
`operand2[3:0]` which is `instr[3:0]` — the bottom of the offset field, not Rd.

#### Path 6: MRS (Move CPSR to Register)

```
cpsr_out──►wb_result (sel=10)──►registers[Rd]
```

**Bug:** Control sets `result_sel=00` instead of `10` for MRS, so the ALU
result is written instead of CPSR. See §8.

Source: `arm_control.sv` lines 138–140

#### Path 7: MSR (Move Register to CPSR)

```
instr[19:16]──►rf_raddr_a──►rf_rdata_a──►msr_data──►CPSR (msr_we=1)
```

CPSR writes: NZCV [31:28], I [15], F [14], T [5], Mode [4:0].

Source: `arm_cpsr.sv` lines 56–63

### 6.4 Carry Flag Feedback Paths

```
CPSR.flag_c ──┬──► shifter_carry_in ──► barrel_shifter ──► shifter_carry_out
              │                                                    │
              └──► alu_carry_in ──► ALU ──► alu_flag_c ──► CPSR.flag_c (if S-bit)
```

- Logic ops (AND, EOR, ORR, BIC, MOV, MVN, TST, TEQ): carry = shifter_carry_out
- Add ops (ADD, ADC, CMN): carry = add_result[32]
- Sub ops (SUB, SBC, RSB, RSC, CMP): carry = ~sub_result[32]

Source: `arm_alu.sv` lines 28–165

### 6.5 PC Read Behavior

When an instruction reads R15, the register file returns `pc_out` (the value
of `registers[15]`). In the ARM architecture, reading R15 should return
PC+8 (current instruction + 8). The current RTL returns the raw `registers[15]`
value which is `pc_current` — this is PC, not PC+8.

Source: `arm_reg_file.sv` lines 36–37

---

## §7 — Control FSM & Signal Table

### 7.1 FSM State Encoding

Source: `arm_control.sv` lines 55–61

| State | Code | Description |
|-------|:----:|-------------|
| `FETCH` | `3'b000` | Drive PC to instruction memory, latch instruction |
| `DECODE` | `3'b001` | Decode instruction, read registers, set up shifter |
| `EXECUTE` | `3'b010` | ALU operation, branch resolution, address calculation |
| `MEMORY` | `3'b011` | Data memory access (load/store only) |
| `WRITEBACK` | `3'b100` | Register write-back, PC advance |

### 7.2 State Transition Table

Source: `arm_control.sv` lines 68–93

| Current State | Condition | Next State | stall |
|:------------:|-----------|:----------:|:-----:|
| FETCH | always | DECODE | 0 |
| DECODE | always | EXECUTE | 0 |
| EXECUTE | `is_load_store && cond_pass` | MEMORY | 0 |
| EXECUTE | `!(is_load_store && cond_pass)` | WRITEBACK | 0 |
| MEMORY | always | WRITEBACK | **1** |
| WRITEBACK | always | FETCH | 0 |

### 7.3 Control Signal Defaults

All control signals are set to their default values at the start of every
combinational block, then overridden by specific states.

Source: `arm_control.sv` lines 97–112

| Signal | Default | Width | Description |
|--------|:-------:|:-----:|-------------|
| `regfile_we` | 0 | 1 | Register file write enable |
| `flags_we` | 0 | 1 | CPSR NZCV flag write enable |
| `pc_we` | 0 | 1 | Program counter write enable |
| `pc_sel` | 0 | 1 | PC source: 0=PC+4, 1=branch_target |
| `lr_we` | 0 | 1 | Link register (R14) write enable |
| `mem_req` | 0 | 1 | Data memory request |
| `mem_we` | 0 | 1 | Data memory write enable |
| `mem_byte` | 0 | 1 | Byte access enable |
| `result_sel` | 00 | 2 | Write-back mux select |
| `alu_op_en` | 0 | 1 | ALU operation valid |
| `shifter_en` | 0 | 1 | Barrel shifter enable |
| `shift_imm_sel` | 0 | 1 | Immediate shift encoding select |
| `msr_we` | 0 | 1 | MSR CPSR write enable |
| `stall` | 0 | 1 | Pipeline stall |

### 7.4 Control Signals Per State

#### FETCH State

Source: `arm_control.sv` — not explicitly listed; all signals remain at defaults.

| Signal | Value | Notes |
|--------|:-----:|-------|
| *(all)* | defaults | No control signals asserted. PC drives `imem_addr`. Instruction latched into `instr` register. |

#### DECODE State

Source: `arm_control.sv` lines 113–116

| Signal | Value | Condition | Notes |
|--------|:-----:|-----------|-------|
| `shifter_en` | 1 | `is_data_proc \| is_load_store \| is_mul` | Enable barrel shifter setup |
| `shift_imm_sel` | 1 | `is_imm_op2` | Select immediate shift encoding |

#### EXECUTE State

Source: `arm_control.sv` lines 118–142

| Signal | Value | Condition | Notes |
|--------|:-----:|-----------|-------|
| `alu_op_en` | 1 | always | ALU performs operation |
| **Branch:** | | | |
| `pc_sel` | 1 | `is_branch && cond_pass` | Select branch target |
| `pc_we` | 1 | `is_branch && cond_pass` | Write branch target to PC |
| `lr_we` | 1 | `is_branch && is_branch_link && cond_pass` | Write PC+4 to R14 ⚠ (buggy in core — empty block) |
| **SWI:** | | | |
| `pc_sel` | 1 | `is_swi && cond_pass` | Attempt branch (target not SWI vector) |
| `pc_we` | 1 | `is_swi && cond_pass` | — |
| **Data Processing:** | | | |
| `regfile_we` | 1 | `is_data_proc && cond_pass` | Write ALU result to Rd |
| `result_sel` | 00 | `is_data_proc && cond_pass` | Select ALU result |
| **MSR:** | | | |
| `msr_we` | 1 | `is_msr && cond_pass` | Write Rn to CPSR |
| **MRS:** | | | |
| `regfile_we` | 1 | `is_mrs && cond_pass` | Write to Rd |
| `result_sel` | 00 | `is_mrs && cond_pass` | ⚠ Bug: should be `10` for CPSR |

**Note:** `flags_we` is not directly driven by `arm_control`. The S-bit
propagation happens in `arm_cpu_core` via `alu_update_flags = s_bit & cond_pass`.

#### MEMORY State

Source: `arm_control.sv` lines 144–150

| Signal | Value | Condition | Notes |
|--------|:-----:|-----------|-------|
| `mem_req` | 1 | `is_load_store && cond_pass` | Assert memory request |
| `mem_we` | `is_store` | `is_load_store && cond_pass` | Direction: 1=write, 0=read |
| `mem_byte` | `is_byte` | `is_load_store && cond_pass` | Access width: 1=byte, 0=word |
| `stall` | 1 | always | Assert stall during memory access |

#### WRITEBACK State

Source: `arm_control.sv` lines 152–165

| Signal | Value | Condition | Notes |
|--------|:-----:|-----------|-------|
| **Load writeback:** | | | |
| `regfile_we` | 1 | `is_load && cond_pass` | Write memory data to Rd |
| `result_sel` | 01 | `is_load && cond_pass` | Select data memory output |
| **PC advance:** | | | |
| `pc_we` | 1 | `!is_branch \|\| !cond_pass` | Advance PC+4 (unless branch taken) |
| `pc_sel` | 0 | `!is_branch \|\| !cond_pass` | Select sequential PC+4 |

### 7.5 Signal Dependency Map

```
                  ┌──────────────┐
                  │   Decoder    │
                  │ (arm_decoder)│
                  └──────┬───────┘
                         │ 17 decoded signals
                         ▼
              ┌──────────────────────┐
              │  Condition Checker   │
              │(arm_condition_check) │
              └──────────┬───────────┘
                         │ cond_pass
                         ▼
              ┌──────────────────────┐
              │    Control FSM       │──── 15 control signals ────┐
              │  (arm_control)       │                            │
              └──────────────────────┘                            ▼
                                                      Datapath muxes & enables:
                                                      • regfile_we, result_sel
                                                      • pc_we, pc_sel, lr_we
                                                      • mem_req, mem_we, mem_byte
                                                      • alu_op_en, shifter_en
                                                      • shift_imm_sel, msr_we
```

---

## §8 — RTL Notes, Issues & Warnings

### 8.1 Bug: BL Link Register Not Written (Critical)

**File:** `arm_cpu_core.sv` lines 339–345

The `lr_we` signal is correctly generated by `arm_control` when a BL
instruction is executed. However, the `always_ff` block that should write
`pc_plus4` to R14 is **empty**:

```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // LR will be reset by reg_file
    end else if (lr_we && cond_pass) begin
        // Write PC+4 to LR (R14)    ← EMPTY: no assignment here
    end
end
```

**Impact:** BL instruction branches correctly but never saves the return
address in R14. Subroutine returns via `MOV PC, LR` will jump to address 0.

**Fix:** Add `registers[14] <= pc_plus4;` or route through register file
write port with `waddr=4'd14`, `wdata=pc_plus4`.

---

### 8.2 Bug: CPSR Flags Never Updated (Critical)

**File:** `arm_control.sv`

The `flags_we` control signal is **always 0**. It is set to its default
value and never overridden in any FSM state. Meanwhile, `arm_cpu_core.sv`
connects `flags_we` to `arm_cpsr.update_flags`, and the ALU generates
correct NZCV outputs. But since `update_flags` is never asserted, the
CPSR flags are never written.

```systemverilog
// arm_control.sv: flags_we defaults to 0, never assigned
flags_we = 1'b0;   // default, line 99

// arm_cpu_core.sv: alu_update_flags drives ALU, not CPSR directly
assign alu_update_flags = s_bit & cond_pass;  // line 306
// This drives ALU flag outputs, but CPSR needs flags_we from control
```

**Impact:** CMP, CMN, TST, TEQ produce ALU flags but CPSR never stores
them. Conditional branches after CMP will always use the reset flag
values (NZCV=0000). Effectively: **all conditional branches behave as
EQ (Z=0 → NE) after reset since Z=0**.

**Fix:** In `arm_control.sv` EXECUTE state, add:
```systemverilog
flags_we = (is_data_proc || is_mul) && s_bit && cond_pass;
```
Note: `s_bit` is not currently an input to `arm_control`. It would need
to be added as an input from the decoder, or passed from `arm_cpu_core`.

---

### 8.3 Bug: MRS Uses Wrong Write-Back Mux Select (Medium)

**File:** `arm_control.sv` lines 138–140

MRS instruction sets `result_sel = 2'b00` (ALU result) instead of
`2'b10` (CPSR output). The write-back mux at `arm_cpu_core.sv` line 366
maps `2'b10` to `cpsr_out`.

**Impact:** MRS Rd, CPSR writes the ALU result (Rn XOR Op2 with
opcode=Fh) instead of the CPSR value.

**Fix:** Change `result_sel` to `2'b10` in the MRS branch of EXECUTE state.

---

### 8.4 Bug: Store Data Source Incorrect (Medium)

**File:** `arm_cpu_core.sv` line 359

```systemverilog
assign dmem_wdata = rf_rdata_b; // Rm for store
```

`rf_rdata_b` reads from `registers[operand2[3:0]]` = `registers[instr[3:0]]`.
For `STR Rd, [Rn, #imm12]` with immediate offset (I=0), `instr[3:0]` is
the **bottom 4 bits of the offset**, not Rd. The store data should come
from `registers[instr[15:12]]` (Rd field).

**Impact:** STR with immediate offset stores the wrong register value
(or a register determined by the offset field).

**Fix:** For store instructions, use a separate read port or mux
`rf_raddr_b` to `rd_addr` when `is_store`.

---

### 8.5 Bug: Debug Register Outputs Stubbed (Low)

**File:** `arm_cpu_core.sv` line 382–385

```systemverilog
assign debug_reg_r0 = 32'd0; // Placeholder
assign debug_reg_r1 = 32'd0;
assign debug_reg_r2 = 32'd0;
assign debug_reg_r3 = 32'd0;
```

These outputs are not connected to the register file, making it impossible
to observe register values during simulation.

**Fix:** Add debug read ports to `arm_reg_file` or use a scan register
to read any register.

---

### 8.6 Deviation: Immediate Rotate Amount (Medium)

**File:** `arm_barrel_shifter.sv` line 28

The ARM Architecture Reference Manual specifies that the 8-bit immediate
is rotated right by `2 * rotate_imm`. The RTL uses only `rotate_imm`
directly (4 bits, not doubled):

```systemverilog
actual_shift = shift_amount[3:0]; // Should be {shift_amount[3:0], 1'b0}
```

**Impact:** Immediate constants are wrong for any rotate_imm > 0.
Only `MOV Rd, #imm8` (rotate_imm=0) produces correct results.
For example: `MOV R0, #0x100` (which uses rotate_imm=1, imm8=1) should
produce 0x100 but produces ROR(1, 1) = 0x80000001.

**Fix:** Change to `actual_shift = {shift_amount[3:0], 1'b0};`

---

### 8.7 Naming Mismatch: U-bit / P-bit (Low)

**File:** `arm_decoder.sv` line 134

```systemverilog
is_pre_index = instr[24];  // Comment says "P-bit: 1=pre, 0=post"
```

This correctly reads the P-bit (Pre/Post index). However:

```systemverilog
// U-bit (bit 23) is NOT decoded separately at all
// The offset direction (Up/Down) is not implemented
```

The decoder reads P-bit into `is_pre_index` but there is no separate
signal for the U-bit (offset direction). The address calculation in
`arm_cpu_core.sv` always adds the offset, never subtracts.

**Impact:** Load/Store with negative offsets (U=0) are broken — the
offset is always added.

**Fix:** Add `is_offset_up = instr[23]` to decoder and use it in
address calculation to conditionally subtract.

---

### 8.8 Missing: LDM/STM Execute Path (Feature Gap)

**Files:** `arm_decoder.sv` (decoded), `arm_control.sv` (not handled)

Block transfer instructions (LDM, STM) are fully decoded with
`is_block_trans`, `reg_list[15:0]`, load/store direction, and writeback.
However, `arm_control` has no case for block transfer in any FSM state.

**Impact:** LDM/STM instructions are decoded but silently execute as NOPs.

**Fix:** Would require a multi-cycle loop in the FSM to transfer up to
16 registers, with address increment/decrement per register.

---

### 8.9 Missing: MUL Execute Path (Feature Gap)

**Files:** `arm_decoder.sv` (decoded), `arm_control.sv` (not handled)

Multiply is detected (`is_mul`) but has no execute logic. `arm_alu` even
declares `mul_result[63:0]` (unused).

**Impact:** MUL/MLA instructions silently execute as NOPs.

---

### 8.10 Missing: SWI Vector (Feature Gap)

**File:** `arm_control.sv` line 127

SWI sets `pc_sel=1` which uses `branch_target`. But `branch_target` is
computed from `signed_offset[23:0]` of the current instruction, not from
the SWI exception vector at address `0x00000008`.

**Impact:** SWI jumps to an unpredictable address.

**Fix:** When `is_swi && cond_pass`, set `branch_target = 32'h0000_0008`.

---

### 8.11 Missing: Post-Index Offset Application (Feature Gap)

**File:** `arm_cpu_core.sv` lines 352–354

```systemverilog
assign mem_addr_calc = is_pre_index ?
                       (ls_base_addr + sign_extend(ls_offset)) :
                       ls_base_addr;  // Post-index: uses base directly
```

For post-index mode (P=0), only the base address is used. The offset is
never applied to the base register after the memory access.

**Impact:** Post-indexed load/store is broken (address is always base,
and base is never updated).

**Fix:** In WRITEBACK state, if `!is_pre_index && is_writeback`, update
Rn with `Rn + offset`.

---

### 8.12 Missing: Offset Direction (U-bit) (Feature Gap)

**File:** `arm_cpu_core.sv` line 353

The address calculation always adds the offset:
```systemverilog
ls_base_addr + sign_extend(ls_offset)  // always positive offset
```

But `ls_offset[11:0]` is an **unsigned** 12-bit value. The sign-extension
`{{20{ls_offset[11]}}, ls_offset}` treats bit 11 as a sign bit, but ARM's
immediate offset is unsigned. The U-bit (bit 23) determines direction.

**Impact:** Offsets 0x800–0xFFF are incorrectly sign-extended to negative.
There is no subtract path for U=0.

---

### 8.13 Unconnected: Register File PC Output (Low)

**File:** `arm_cpu_core.sv` line 291

```systemverilog
.pc_out ()   // Left unconnected
```

The `pc_out` port of `arm_reg_file` (which provides `registers[15]`) is
not connected. Reading R15 returns `pc_out` via the read ports, but the
unconnected port itself means the raw PC value is not available as a
separate signal in the core.

**Impact:** No functional impact since `pc_current` serves the same purpose,
but the unconnected output may cause lint warnings.

---

### 8.14 Unused Signals (Low)

| Signal | File | Line | Issue |
|--------|------|------|-------|
| `pc_next` | `arm_cpu_core.sv` | 213 | Declared but never assigned or used |
| `mul_result` | `arm_alu.sv` | 41 | Declared `logic [63:0]` but never used |
| `rf_wdata` | `arm_cpu_core.sv` | 199 | Declared but never assigned (wb_result goes directly to reg file) |

---

### 8.15 PC Read Returns PC, Not PC+8 (Low)

**File:** `arm_reg_file.sv` lines 36–37

```systemverilog
assign rdata_a = (raddr_a == 4'd15) ? pc_out : registers[raddr_a];
```

`pc_out` = `registers[15]` = `pc_current`. In ARM, reading R15 should
return `PC + 8` (the address of the current instruction plus 8). This
affects instructions like `SUB R0, PC, #4` which should compute addresses
relative to the current instruction.

**Impact:** Any instruction that reads R15 gets the wrong value.

---

### 8.16 Compilation Warnings (Informational)

Source: `sv_compile` — 0 errors, 18 warnings across 11 files

| # | Type | File | Description |
|---|------|------|-------------|
| 1 | Truncation | `arm_barrel_shifter.sv:28` | Implicit 6→5 bit truncation in shift assignment |
| 2 | Missing default | `arm_barrel_shifter.sv:39` | case missing default |
| 3 | Type mismatch | `arm_barrel_shifter.sv:53` | Arithmetic int vs logic[4:0] |
| 4–6 | Vector literal | `arm_barrel_shifter.sv:55,57,94` | Literal too large for given bits |
| 7–8 | Vector literal | `arm_barrel_shifter.sv:75,77` | Same |
| 9–12 | Signedness | `arm_barrel_shifter.sv:89-92` | $signed to unsigned conversion |
| 13 | Type mismatch | `arm_barrel_shifter.sv:115` | Arithmetic int vs logic[4:0] |
| 14 | Missing default | `arm_barrel_shifter.sv:110` | case missing default |
| 15–16 | Missing default | `arm_condition_check.sv:42`, `arm_alu.sv:60` | case missing default |
| 17 | Bit expansion | `arm_cpu_core.sv:293` | Implicit 11→12 bit expansion |
| 18 | Truncation | `arm_cpu_core.sv:302` | Port connection 13→12 bit truncation |

All warnings are non-functional but should be cleaned for production quality.

---

### 8.17 Issue Summary

| # | ID | Severity | Category | Description |
|---|-----|:--------:|----------|-------------|
| 1 | 8.1 | 🔴 Critical | Bug | BL: LR never written |
| 2 | 8.2 | 🔴 Critical | Bug | CPSR flags never updated (flags_we always 0) |
| 3 | 8.3 | 🟡 Medium | Bug | MRS uses wrong result_sel (00 instead of 10) |
| 4 | 8.4 | 🟡 Medium | Bug | STR data source is instr[3:0] not Rd |
| 5 | 8.5 | 🟢 Low | Bug | debug_reg_r0–r3 stubbed to 0 |
| 6 | 8.6 | 🟡 Medium | Deviation | Immediate rotate not doubled |
| 7 | 8.7 | 🟢 Low | Naming | U-bit not decoded, P-bit name confusing |
| 8 | 8.8 | 🔵 Gap | Missing | LDM/STM no execute path |
| 9 | 8.9 | 🔵 Gap | Missing | MUL no execute path |
| 10 | 8.10 | 🔵 Gap | Missing | SWI no vector table |
| 11 | 8.11 | 🔵 Gap | Missing | Post-index offset not applied |
| 12 | 8.12 | 🔵 Gap | Missing | U-bit offset direction not implemented |
| 13 | 8.13 | 🟢 Low | Unconnected | reg_file pc_out floating |
| 14 | 8.14 | 🟢 Low | Unused | pc_next, mul_result, rf_wdata |
| 15 | 8.15 | 🟢 Low | Deviation | R15 read returns PC not PC+8 |
| 16 | 8.16 | ⚪ Info | Warnings | 18 pyslang warnings |

---

## §9 — DV Plan

### 9.1 Existing Testbench

**File:** `tb/arm_cpu_tb.sv` (308 lines)

The testbench generates a test program at simulation runtime via `$fwrite`
into `arm_program.hex`, then resets the CPU and runs for 200 clock cycles.

#### Current Test Coverage

| # | Test Group | Instructions | Address | Hex Encoding |
|---|------------|-------------|:-------:|:------------:|
| 1 | MOV imm | `MOV R0, #5` | 0x00 | `E3A00005` |
| 2 | MOV imm | `MOV R1, #10` | 0x04 | `E3A0100A` |
| 3 | ADD reg | `ADD R2, R0, R1` | 0x08 | `E0802001` |
| 4 | SUB reg | `SUB R3, R1, R0` | 0x0C | `E0413000` |
| 5 | MOV imm | `MOV R4, #0xFF` | 0x10 | `E3A040FF` |
| 6 | MOV imm | `MOV R5, #0x0F` | 0x14 | `E3A0500F` |
| 7 | AND reg | `AND R6, R4, R5` | 0x18 | `E0046005` |
| 8 | ORR reg | `ORR R7, R4, R5` | 0x1C | `E1847005` |
| 9 | CMP imm | `CMP R0, #5` | 0x20 | `E3500005` |
| 10 | BEQ | `BEQ +2` | 0x24 | `0A000001` |
| 11 | MOV (skip) | `MOV R8, #0` | 0x28 | `E3A08000` |
| 12 | MOV (target) | `MOV R8, #1` | 0x2C | `E3A08001` |
| 13 | BL | `BL subroutine` | 0x30 | `EB000002` |
| 14 | NOP | `NOP` | 0x34 | `E1A00000` |
| 15 | NOP | `NOP` | 0x38 | `E1A00000` |
| 16 | B | `B end_test` | 0x3C | `EA000008` |
| 17 | MOV imm | `MOV R9, #42` | 0x40 | `E3A0902A` |
| 18 | MOV imm | `MOV R10, #99` | 0x44 | `E3A0A063` |
| 19 | MOV PC,LR | `MOV PC, LR` | 0x48 | `E1A0F00E` |
| 20 | MOV imm | `MOV R0, #1` | 0x60 | `E3A00001` |
| 21 | MOV shifted | `MOV R12, #0x100` | 0x64 | `E3A0C801` |
| 22 | STR imm | `STR R0, [R12, #0]` | 0x68 | `E58C0000` |
| 23 | LDR imm | `LDR R3, [R12, #0]` | 0x6C | `E59C3000` |
| 24 | EOR reg | `EOR R4, R0, R0` | 0x70 | `E0204000` |
| 25 | MVN imm | `MVN R5, #0` | 0x74 | `E3E05000` |
| 26 | BIC reg | `BIC R6, R5, R0` | 0x78 | `E1C56000` |
| 27 | B self | `B .` | 0x80 | `EAFFFFFE` |

**Total:** ~27 unique test instructions

#### Known TB Limitations

| # | Limitation | Impact |
|---|------------|--------|
| 1 | `debug_reg_r0–r3` tied to 0 | **Cannot observe any register values** — testbench has no visibility into computation results |
| 2 | No timed assertion checks | Tests run for 200 cycles blindly with no pass/fail per instruction |
| 3 | No NZCV flag checks | Condition code behavior after CMP/ALU never verified |
| 4 | No `check_result` calls | The `check_result` task is defined but never called with actual values |
| 5 | No GPIO tests | Memory-mapped IO at 0xFFFF0000 never exercised |
| 6 | No byte access tests | LDRB/STRB never tested |
| 7 | No shift boundary tests | LSL #0, LSR #32, ASR #32, ROR #16 never tested |
| 8 | No negative conditional tests | Only BEQ tested; NE, GT, LT, GE, LE never tested |

### 9.2 RTL Bug Impact on Test Results

Given the critical bugs identified in §8, the following test results are
expected to be incorrect even after fixing TB visibility:

| Test | Expected (ARM spec) | Actual (with bugs) | Blocking Bug |
|------|:-------------------:|:------------------:|:------------:|
| CMP R0, #5 → BEQ | Z=1, branch taken | Z never updated (flags_we=0), BEQ uses reset Z=0 → not taken | §8.2 |
| MOV R8, #0 skipped | R8 = 1 | BEQ not taken → R8 = 0 then R8 = 1 | §8.2 |
| BL subroutine | LR = 0x34, returns | LR never written (lr_we empty) → MOV PC,LR jumps to 0 | §8.1 |
| MOV R12, #0x100 | R12 = 256 | Immediate rotate not doubled → wrong value | §8.6 |
| STR R0, [R12] | Mem[0x100] = 1 | Stores from registers[instr[3:0]] = registers[0] = 1 (lucky) | §8.4 |

### 9.3 Recommended RTL Fixes Before DV

These RTL fixes are prerequisites for meaningful verification:

| Priority | Bug | Fix |
|:--------:|-----|-----|
| P0 | §8.2 flags_we always 0 | Add `flags_we = s_bit` in EXECUTE state; route `s_bit` from decoder |
| P0 | §8.1 BL lr_we empty | Write `pc_plus4` to register file when `lr_we && cond_pass` |
| P1 | §8.4 STR data source | Mux `rf_raddr_b` to `rd_addr` for store instructions |
| P1 | §8.6 Rotate not doubled | Change to `actual_shift = {shift_amount[3:0], 1'b0}` |
| P1 | §8.3 MRS result_sel | Change to `result_sel = 2'b10` for MRS |

### 9.4 Recommended DV Improvements

#### 9.4.1 TB Infrastructure

| # | Enhancement | Description |
|---|-------------|-------------|
| 1 | Debug register port | Add 4 debug outputs to `arm_reg_file` (or a scan interface) and connect through `arm_cpu_core` and `arm_cpu_top` |
| 2 | Timed assertion checks | After each instruction group, wait N cycles then check register values |
| 3 | Flag observation | Add `debug_nzcv` outputs to `arm_cpu_top` from CPSR |
| 4 | Per-test pass/fail | Call `check_result()` with expected register values after each test group |

#### 9.4.2 Required New Test Cases

| # | Category | Test | Expected Result |
|---|----------|------|-----------------|
| 1 | ALU | `RSB R0, R1, R2` | Reverse subtract |
| 2 | ALU | `ADC R0, R1, R2` (carry=1) | Add with carry |
| 3 | ALU | `SBC R0, R1, R2` (carry=0) | Sub with borrow |
| 4 | ALU | `RSC R0, R1, R2` | Reverse sub with carry |
| 5 | Logic | `EOR R0, R1, #0xFF` | XOR with immediate |
| 6 | Shift | `MOV R0, R1, LSL #0` | No shift, carry = CPSR.C |
| 7 | Shift | `MOV R0, R1, LSR #32` | All zero, carry = R1[31] |
| 8 | Shift | `MOV R0, R1, ASR #32` | All sign, carry = R1[31] |
| 9 | Shift | `MOV R0, R1, ROR #16` | Half-rotate |
| 10 | Shift | `MOV R0, R1, RRX` | Rotate through carry |
| 11 | Imm rotate | `MOV R0, #0x100` | rotate_imm=1 → ROR(1,1) → should be 0x100 |
| 12 | Condition | `CMP; BNE` | Branch when not equal |
| 13 | Condition | `CMP; BGT` | Signed greater than |
| 14 | Condition | `CMP; BLT` | Signed less than |
| 15 | Condition | `CMP; BGE` | Signed greater or equal |
| 16 | Condition | `CMP; BLE` | Signed less or equal |
| 17 | Condition | `CMP; BHI` | Unsigned higher |
| 18 | Condition | `CMP; BLS` | Unsigned lower or same |
| 19 | Load/Store | `LDRB` / `STRB` | Byte access |
| 20 | Load/Store | `LDR Rd, [Rn, #-4]` | Negative offset (needs U-bit fix) |
| 21 | Branch | Nested BL (subroutine calls another) | LR stacking |
| 22 | Branch | `B .` (infinite loop) | PC unchanged |
| 23 | MRS/MSR | `MRS R0, CPSR; MSR CPSR, R0` | Read/write status |
| 24 | GPIO | `STR R0, [0xFFFF0000]` then check `gpio_out` | Memory-mapped IO |
| 25 | Flags S-bit | `ADDS R0, R1, R2` then check NZCV | Flag update |
| 26 | TST | `TST R0, #0xFF` then check Z | Test without write |
| 27 | TEQ | `TEQ R0, R0` then check Z=1 | Test equivalent |
| 28 | CMN | `CMN R0, #1` then check flags | Compare negative |

#### 9.4.3 Regression Test Plan

| Phase | Focus | Tests | Prerequisite |
|-------|-------|:-----:|:------------:|
| Phase 0 | RTL bug fixes | — | All P0/P1 bugs from §9.3 |
| Phase 1 | TB infrastructure | Debug ports, assertion framework | Phase 0 |
| Phase 2 | Basic datapath | MOV, ADD, SUB, AND, ORR, EOR, BIC, MVN | Phase 1 |
| Phase 3 | Flags & conditions | CMP, CMN, TST, TEQ, all 15 B-cond | Phase 1 (needs §8.2 fix) |
| Phase 4 | Load/Store | LDR, STR, LDRB, STRB, negative offset | Phase 1 (needs §8.4 fix) |
| Phase 5 | Branch & link | B, BL, nested BL, MOV PC,LR | Phase 0 (needs §8.1 fix) |
| Phase 6 | Immediate encoding | Rotated immediates, shifted registers | Phase 0 (needs §8.6 fix) |
| Phase 7 | Shift boundaries | LSL #0, LSR #32, ASR #32, ROR, RRX | Phase 1 |
| Phase 8 | MRS/MSR | Status register access | Phase 0 (needs §8.3 fix) |
| Phase 9 | GPIO/IO | Memory-mapped store/load | Phase 1 |
| Phase 10 | Coverage closure | Constrained random, edge cases | Phases 2–9 |

---

## §10 — Hierarchy Tree & File List

### 10.1 Module Hierarchy

```
arm_cpu_top                              (rtl/arm_cpu_top.sv)
├── u_core: arm_cpu_core                 (rtl/arm_cpu_core.sv)
│   ├── u_decoder: arm_decoder           (rtl/arm_decoder.sv)
│   │   └── imports: arm_defs package    (rtl/arm_decoder.sv lines 12–42)
│   ├── u_cond_check: arm_condition_check (rtl/arm_condition_check.sv)
│   ├── u_cpsr: arm_cpsr                 (rtl/arm_cpsr.sv)
│   ├── u_control: arm_control           (rtl/arm_control.sv)
│   ├── u_reg_file: arm_reg_file         (rtl/arm_reg_file.sv)
│   ├── u_shifter: arm_barrel_shifter    (rtl/arm_barrel_shifter.sv)
│   └── u_alu: arm_alu                   (rtl/arm_alu.sv)
├── u_imem: arm_imem                     (rtl/arm_imem.sv)
└── u_dmem: arm_dmem                     (rtl/arm_dmem.sv)
```

### 10.2 File List

| # | File | Path | Lines | Type | Contains |
|---|------|------|------:|------|----------|
| 1 | `arm_decoder.sv` | `rtl/` | 166 | Module + Package | `arm_defs` package + `arm_decoder` module |
| 2 | `arm_reg_file.sv` | `rtl/` | 52 | Module | Register file |
| 3 | `arm_alu.sv` | `rtl/` | 174 | Module | ALU |
| 4 | `arm_barrel_shifter.sv` | `rtl/` | 125 | Module | Barrel shifter |
| 5 | `arm_condition_check.sv` | `rtl/` | 39 | Module | Condition checker |
| 6 | `arm_cpsr.sv` | `rtl/` | 87 | Module | CPSR |
| 7 | `arm_control.sv` | `rtl/` | 184 | Module | Control FSM |
| 8 | `arm_imem.sv` | `rtl/` | 26 | Module | Instruction memory |
| 9 | `arm_dmem.sv` | `rtl/` | 73 | Module | Data memory |
| 10 | `arm_cpu_core.sv` | `rtl/` | 384 | Module | CPU core datapath |
| 11 | `arm_cpu_top.sv` | `rtl/` | 119 | Module | Top-level integration |
| 12 | `arm_cpu_tb.sv` | `tb/` | 308 | Testbench | Self-checking TB |
| 13 | `arm_cpu_mas.md` | `mas/` | — | Document | This specification |
| 14 | `arm_cpu.md` | `docs/` | 238 | Document | User documentation |
| — | **RTL Total** | | **1,429** | | |

### 10.3 Compile Order

The `arm_defs` package (inside `arm_decoder.sv`) must be compiled before
any file that imports it (`arm_cpu_core.sv`). All leaf modules have no
cross-dependencies and can be compiled in any order.

| Order | File | Reason |
|:-----:|------|--------|
| 1 | `rtl/arm_decoder.sv` | Contains `arm_defs` package — must be first |
| 2 | `rtl/arm_reg_file.sv` | Leaf module, no dependencies |
| 3 | `rtl/arm_barrel_shifter.sv` | Leaf module, no dependencies |
| 4 | `rtl/arm_alu.sv` | Leaf module, no dependencies |
| 5 | `rtl/arm_condition_check.sv` | Leaf module, no dependencies |
| 6 | `rtl/arm_cpsr.sv` | Leaf module, no dependencies |
| 7 | `rtl/arm_control.sv` | Leaf module, no dependencies |
| 8 | `rtl/arm_imem.sv` | Leaf module, no dependencies |
| 9 | `rtl/arm_dmem.sv` | Leaf module, no dependencies |
| 10 | `rtl/arm_cpu_core.sv` | Imports `arm_defs`, instantiates modules 1–7 |
| 11 | `rtl/arm_cpu_top.sv` | Instantiates `arm_cpu_core`, `arm_imem`, `arm_dmem` |
| 12 | `tb/arm_cpu_tb.sv` | Testbench — instantiates `arm_cpu_top` |

### 10.4 Quick Compile Commands

**Icarus Verilog:**
```bash
iverilog -g2012 -o arm_cpu_sim \
    rtl/arm_decoder.sv \
    rtl/arm_reg_file.sv \
    rtl/arm_barrel_shifter.sv \
    rtl/arm_alu.sv \
    rtl/arm_condition_check.sv \
    rtl/arm_cpsr.sv \
    rtl/arm_control.sv \
    rtl/arm_imem.sv \
    rtl/arm_dmem.sv \
    rtl/arm_cpu_core.sv \
    rtl/arm_cpu_top.sv \
    tb/arm_cpu_tb.sv

vvp arm_cpu_sim
```

**Synopsys VCS:**
```bash
vcs -full64 -sverilog -debug_access+all \
    +incdir+rtl \
    rtl/arm_decoder.sv \
    rtl/arm_reg_file.sv \
    rtl/arm_barrel_shifter.sv \
    rtl/arm_alu.sv \
    rtl/arm_condition_check.sv \
    rtl/arm_cpsr.sv \
    rtl/arm_control.sv \
    rtl/arm_imem.sv \
    rtl/arm_dmem.sv \
    rtl/arm_cpu_core.sv \
    rtl/arm_cpu_top.sv \
    tb/arm_cpu_tb.sv

./simv
```

**Cadence Xcelium:**
```bash
xrun -sverilog -access +rwc \
    rtl/arm_decoder.sv \
    rtl/arm_reg_file.sv \
    rtl/arm_barrel_shifter.sv \
    rtl/arm_alu.sv \
    rtl/arm_condition_check.sv \
    rtl/arm_cpsr.sv \
    rtl/arm_control.sv \
    rtl/arm_imem.sv \
    rtl/arm_dmem.sv \
    rtl/arm_cpu_core.sv \
    rtl/arm_cpu_top.sv \
    tb/arm_cpu_tb.sv
```

### 10.5 Dependency Graph

```
arm_defs (package)
    │
    └──► arm_cpu_core ──► arm_cpu_top ──► tb_arm_cpu
              ▲                  ▲
              │                  │
    ┌─────────┼──────────────────┼─────────────┐
    │         │                  │             │
    │    arm_decoder         arm_imem      arm_dmem
    │    arm_condition_check
    │    arm_cpsr
    │    arm_control
    │    arm_reg_file
    │    arm_barrel_shifter
    │    arm_alu
    │
    └── All leaf modules (no cross-deps)
```

---

*End of ARM CPU Microarchitecture Specification*
*Generated from RTL source analysis — 1,845 lines across 10 sections*
