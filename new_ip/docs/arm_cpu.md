# ARM CPU Microarchitecture

## Overview

A synthesizable 32-bit ARM (ARMv4-compatible) CPU core implemented in SystemVerilog, supporting a comprehensive subset of the ARM instruction set.

## Architecture

### Pipeline
The CPU uses a **3-stage pipeline**:
1. **FETCH** — Instruction fetch from instruction memory
2. **DECODE/EXECUTE** — Instruction decode, condition check, ALU operation
3. **MEMORY/WRITEBACK** — Data memory access, register write-back

### Block Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │                 ARM CPU Core                  │
                    │                                              │
   ┌─────────┐      │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
   │ Instr   │◄─────┤  │   PC     │  │ Decoder  │  │ Control  │  │
   │ Memory  │      │  │ (R15)    │  │          │  │  Unit    │  │
   └─────────┘      │  └────┬─────┘  └────┬─────┘  └──────────┘  │
                    │       │              │                       │
                    │       ▼              ▼                       │
                    │  ┌──────────┐  ┌──────────┐                 │
                    │  │  Reg     │  │Condition │                 │
                    │  │  File    │  │ Checker  │                 │
                    │  │(R0-R14)  │  └──────────┘                 │
                    │  └──┬───┬───┘                               │
                    │     │   │                                    │
                    │     ▼   ▼                                    │
                    │  ┌──────────┐  ┌──────────┐                 │
                    │  │ Barrel   │  │  CPSR    │                 │
                    │  │ Shifter  │  │ (Flags)  │                 │
                    │  └────┬─────┘  └──────────┘                 │
                    │       │                                      │
                    │       ▼                                      │
                    │  ┌──────────┐                                │
                    │  │   ALU    │                                │
                    │  └────┬─────┘                                │
                    │       │                                      │
   ┌─────────┐      │       ▼                                      │
   │  Data   │◄─────┤  ┌──────────┐                               │
   │  Memory │      │  │Write-Back│                               │
   └─────────┘      │  │   Mux    │                               │
                    │  └──────────┘                               │
                    └──────────────────────────────────────────────┘
```

## Supported ARM Instructions

### Data Processing Instructions
| Opcode | Instruction | Description | Encoding |
|--------|------------|-------------|----------|
| 0000 | AND | Rd = Rn AND Op2 | `[cond] 0000 00S Rn Rd shift` |
| 0001 | EOR | Rd = Rn XOR Op2 | `[cond] 0001 00S Rn Rd shift` |
| 0010 | SUB | Rd = Rn - Op2 | `[cond] 0010 00S Rn Rd shift` |
| 0011 | RSB | Rd = Op2 - Rn | `[cond] 0011 00S Rn Rd shift` |
| 0100 | ADD | Rd = Rn + Op2 | `[cond] 0100 00S Rn Rd shift` |
| 0101 | ADC | Rd = Rn + Op2 + C | `[cond] 0101 00S Rn Rd shift` |
| 0110 | SBC | Rd = Rn - Op2 - !C | `[cond] 0110 00S Rn Rd shift` |
| 0111 | RSC | Rd = Op2 - Rn - !C | `[cond] 0111 00S Rn Rd shift` |
| 1000 | TST | Rn AND Op2 (flags) | `[cond] 1000 01S Rn Rd shift` |
| 1001 | TEQ | Rn XOR Op2 (flags) | `[cond] 1001 01S Rn Rd shift` |
| 1010 | CMP | Rn - Op2 (flags) | `[cond] 1010 01S Rn Rd shift` |
| 1011 | CMN | Rn + Op2 (flags) | `[cond] 1011 01S Rn Rd shift` |
| 1100 | ORR | Rd = Rn OR Op2 | `[cond] 1100 00S Rn Rd shift` |
| 1101 | MOV | Rd = Op2 | `[cond] 1101 00S Rn Rd shift` |
| 1110 | BIC | Rd = Rn AND NOT Op2 | `[cond] 1110 00S Rn Rd shift` |
| 1111 | MVN | Rd = NOT Op2 | `[cond] 1111 00S Rn Rd shift` |

### Barrel Shifter Operations
| Shift Type | Code | Description |
|-----------|------|-------------|
| LSL | 00 | Logical Shift Left |
| LSR | 01 | Logical Shift Right |
| ASR | 10 | Arithmetic Shift Right |
| ROR | 11 | Rotate Right |
| RRX | 11 + amt=0 | Rotate Right Extended (through carry) |

### Load/Store Instructions
| Instruction | Description | Encoding |
|-------------|-------------|----------|
| LDR Rd, [Rn, #imm] | Load word | `[cond] 010 P U 0 W 1 Rn Rd offset12` |
| STR Rd, [Rn, #imm] | Store word | `[cond] 010 P U 0 W 0 Rn Rd offset12` |
| LDRB Rd, [Rn, #imm] | Load byte | `[cond] 010 P U 1 W 1 Rn Rd offset12` |
| STRB Rd, [Rn, #imm] | Store byte | `[cond] 010 P U 1 W 0 Rn Rd offset12` |

### Branch Instructions
| Instruction | Description | Encoding |
|-------------|-------------|----------|
| B offset | Branch | `[cond] 1010 offset24` |
| BL offset | Branch with Link | `[cond] 1011 offset24` |

### Status Register Instructions
| Instruction | Description |
|-------------|-------------|
| MRS Rd, CPSR | Move CPSR to register |
| MSR CPSR, Rm | Move register to CPSR |

### Other
| Instruction | Description |
|-------------|-------------|
| SWI imm24 | Software Interrupt |
| NOP | MOV R0, R0 (E1A00000) |

## Condition Codes
| Code | Suffix | Condition |
|------|--------|-----------|
| 0000 | EQ | Z set (Equal) |
| 0001 | NE | Z clear (Not Equal) |
| 0010 | CS/HS | C set (Unsigned Higher or Same) |
| 0011 | CC/LO | C clear (Unsigned Lower) |
| 0100 | MI | N set (Negative) |
| 0101 | PL | N clear (Positive or Zero) |
| 0110 | VS | V set (Overflow) |
| 0111 | VC | V clear (No Overflow) |
| 1000 | HI | C set and Z clear (Unsigned Higher) |
| 1001 | LS | C clear or Z set (Unsigned Lower or Same) |
| 1010 | GE | N == V (Greater or Equal) |
| 1011 | LT | N != V (Less Than) |
| 1100 | GT | Z clear and N == V (Greater Than) |
| 1101 | LE | Z set or N != V (Less or Equal) |
| 1110 | AL | Always |

## CPSR (Current Program Status Register)
```
┌───┬───┬───┬───┬───────┬───────┬───────┬───────┬───────┬───┬───┬───┬───┬───┐
│ N │ Z │ C │ V │  Res  │  Res  │  Res  │  I    │  F    │   │ T │   │ M │
│   │   │   │   │       │       │       │       │       │   │   │   │   │
└───┴───┴───┴───┴───────┴───────┴───────┴───────┴───────┴───┴───┴───┴───┘
 31   30   29   28   27-24   23-20   19-16   15      14       9    5   4:0
```

## File Structure

```
├── rtl/
│   ├── arm_reg_file.sv         # Register file (16x32-bit, dual-read, single-write)
│   ├── arm_alu.sv              # Arithmetic Logic Unit (16 operations)
│   ├── arm_barrel_shifter.sv   # Barrel shifter (LSL, LSR, ASR, ROR, RRX)
│   ├── arm_decoder.sv          # Instruction decoder + arm_defs package
│   ├── arm_condition_check.sv  # Condition code evaluator
│   ├── arm_cpsr.sv             # Current Program Status Register
│   ├── arm_control.sv          # Control unit (FSM + control signals)
│   ├── arm_imem.sv             # Instruction memory (4KB)
│   ├── arm_dmem.sv             # Data memory (4KB, byte-enable)
│   ├── arm_cpu_core.sv         # CPU core integration
│   └── arm_cpu_top.sv          # Top-level with memories and GPIO
├── tb/
│   └── arm_cpu_tb.sv           # Testbench with self-checking tests
├── docs/
│   └── arm_cpu.md              # This documentation
└── arm_program.hex             # Generated test program (hex)
```

## Module Hierarchy

```
arm_cpu_top
├── arm_cpu_core
│   ├── arm_decoder
│   ├── arm_condition_check
│   ├── arm_cpsr
│   ├── arm_control
│   ├── arm_reg_file
│   ├── arm_barrel_shifter
│   └── arm_alu
├── arm_imem
└── arm_dmem
```

## Design Parameters
| Parameter | Value |
|-----------|-------|
| Data width | 32 bits |
| Address space | 32 bits |
| Instruction memory | 4 KB (1024 × 32-bit) |
| Data memory | 4 KB (1024 × 32-bit) |
| Register file | 16 × 32-bit (R0–R15) |
| Clock frequency | Up to 100 MHz (typical FPGA) |
| Pipeline stages | 3 (Fetch, Decode/Execute, Writeback) |

## Quick Start

### Running Simulation
```bash
# Using Icarus Verilog
iverilog -g2012 -o arm_cpu_sim \
    rtl/arm_reg_file.sv \
    rtl/arm_barrel_shifter.sv \
    rtl/arm_alu.sv \
    rtl/arm_condition_check.sv \
    rtl/arm_cpsr.sv \
    rtl/arm_decoder.sv \
    rtl/arm_control.sv \
    rtl/arm_imem.sv \
    rtl/arm_dmem.sv \
    rtl/arm_cpu_core.sv \
    rtl/arm_cpu_top.sv \
    tb/arm_cpu_tb.sv

vvp arm_cpu_sim
```

### Test Program Format
The test program is a plain hex file (`arm_program.hex`) with one 32-bit instruction per line:
```
E3A00005    // MOV R0, #5
E3A0100A    // MOV R1, #10
E0802001    // ADD R2, R0, R1
```

## GPIO / Memory-Mapped IO
| Address | Direction | Description |
|---------|-----------|-------------|
| 0xFFFF0000 | Output | GPIO output register |
| 0xFFFF0004 | Input | GPIO input register |

## Limitations (Current Version)
- Single-cycle execution for most instructions (load/store is multi-cycle)
- No coprocessor support
- No Thumb instruction support
- Single processor mode (SVC only)
- No exception vectors (reset only)
- Block transfer (LDM/STM) partially implemented

## Future Extensions
- [ ] Full 5-stage pipeline (IF, ID, EX, MEM, WB)
- [ ] Thumb instruction support
- [ ] Exception handling (IRQ, FIQ, Undefined, Abort)
- [ ] Multi-cycle multiply (MUL, MLA, UMULL, SMULL)
- [ ] Coprocessor interface
- [ ] Cache controller
- [ ] MMU support
- [ ] MPU (Memory Protection Unit)
