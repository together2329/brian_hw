# Cortex-M0 Core — Consolidated Requirements Specification

> **IP Name:** `cortex_m0_core`
> **Version:** 1.0
> **Date:** 2025
> **Status:** Final

---

## Table of Contents

1. [Module Context](#1-module-context)
2. [Interface Specification](#2-interface-specification)
3. [Functional Requirements](#3-functional-requirements)
4. [Register Map](#4-register-map)
5. [Interrupt Requirements](#5-interrupt-requirements)
6. [Memory Requirements](#6-memory-requirements)
7. [Timing & Constraints](#7-timing--constraints)
8. [Design Verification Requirements](#8-design-verification-requirements)
9. [Open Items](#9-open-items)

---

## 1. Module Context

### 1.1 Module Name
`cortex_m0_core`

### 1.2 Purpose
A 32-bit CPU core implementing a subset of the ARMv6-M instruction set architecture,
inspired by the ARM Cortex-M0. Designed as a minimal, area-optimized embedded processor
suitable for IoT, sensor hubs, and microcontroller applications.

### 1.3 SoC Position
- **Bus Interface:** AHB-Lite (AHB5 subset) — matches real Cortex-M0 bus
- **Role:** Processor core (bus master) — drives instruction fetches and data accesses
- **Integration:** Standalone initially; integrates into SoC as AHB-Lite master

### 1.4 Technology
- Technology-independent RTL (SystemVerilog)
- Portable across FPGA and ASIC targets
- No technology-specific primitives

### 1.5 Key Characteristics

| Feature              | Value                          |
|----------------------|--------------------------------|
| Architecture         | ARMv6-M (subset)               |
| Data Width           | 32-bit                         |
| Address Space        | 4 GB (32-bit addressing)       |
| Pipeline             | 3-stage (Fetch, Decode, Execute) |
| Bus Protocol         | AHB-Lite                       |
| Interrupts           | NVIC (Nested Vectored Interrupt Controller) |
| Endianness           | Little-endian                  |
| Registers            | R0-R12, SP (MSP/PSP), LR, PC, xPSR |

### 1.6 References
- ARMv6-M Architecture Reference Manual
- Cortex-M0 Technical Reference Manual

---

## 2. Interface Specification

### 2.1 Clock Domains

| Domain | Signal | Frequency | Description |
|--------|--------|-----------|-------------|
| sys_clk | HCLK | Implementation-dependent | Single clock domain — all logic clocked here |

### 2.2 Reset Strategy

| Signal | Polarity | Type | Description |
|--------|----------|------|-------------|
| HRESETn | Active-low | Asynchronous assert, synchronous deassert | System reset. Core initializes PC from INIT_PC, SP from INIT_SP. |

### 2.3 Top-Level Ports

#### 2.3.1 Clock & Reset

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HCLK | 1 | input | sys_clk | System clock |
| HRESETn | 1 | input | sys_clk | Asynchronous active-low reset |

#### 2.3.2 AHB-Lite Bus Interface

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HADDR | 32 | output | sys_clk | Address bus |
| HBURST | 3 | output | sys_clk | Burst type (SINGLE/INCR/WRAP) |
| HMASTLOCK | 1 | output | sys_clk | Locked transfer (for atomic ops) |
| HPROT | 4 | output | sys_clk | Protection control |
| HSIZE | 3 | output | sys_clk | Transfer size (byte/halfword/word) |
| HTRANS | 2 | output | sys_clk | Transfer type (IDLE/BUSY/NONSEQ/SEQ) |
| HWDATA | 32 | output | sys_clk | Write data bus |
| HWRITE | 1 | output | sys_clk | Transfer direction (1=write) |
| HRDATA | 32 | input | sys_clk | Read data bus |
| HREADY | 1 | input | sys_clk | Transfer done (1=ready) |
| HRESP | 1 | input | sys_clk | Transfer response (0=OKAY, 1=ERROR) |

#### 2.3.3 Interrupts (NVIC)

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| IRQ | IRQ_NUM | input | sys_clk | External interrupt requests (active-high, level-sensitive) |
| NMI | 1 | input | sys_clk | Non-maskable interrupt (active-high, edge-sensitive) |
| EVTEXEC | 1 | output | sys_clk | Event executed signal (for WFE instruction) |

#### 2.3.4 Debug

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HALTED | 1 | output | sys_clk | Core is halted for debug |
| DBGRQ | 1 | input | sys_clk | External debug request |
| DBGACK | 1 | output | sys_clk | Debug acknowledge |

### 2.4 Parameters / Generics

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| IRQ_NUM | integer | 32 | Number of external IRQ lines (1–240) |
| INIT_PC | logic [31:0] | 32'h00000004 | Reset vector — initial PC value (vector table + 4) |
| INIT_SP | logic [31:0] | 32'h00000000 | Initial stack pointer (vector table offset 0) |

---

## 3. Functional Requirements

### 3.1 Major Features

| ID | Feature | Description |
|----|---------|-------------|
| F1 | Instruction Fetch & Execute | 3-stage pipeline: Fetch → Decode → Execute |
| F2 | ARMv6-M Instruction Subset | 16-bit Thumb (most) + 32-bit Thumb-2 (BL, DMB, DSB, ISB, MSR, MRS) |
| F3 | Register File | R0–R12, SP (MSP/PSP banked), LR, PC, xPSR (APSR, IPSR, EPSR), PRIMASK, CONTROL |
| F4 | NVIC | Configurable IRQs (1–240), priority levels, tail-chaining, late arrival |
| F5 | Exception Handling | Reset, NMI, HardFault, SVCall, PendSV, SysTick, IRQs — vector table auto-fetch |
| F6 | Dual Stack Pointers | MSP (Handler + default Thread), PSP (Thread when CONTROL.SPSEL=1) |
| F7 | SysTick Timer | 24-bit countdown timer with interrupt |
| F8 | Sleep Modes | WFI (wait for interrupt) / WFE (wait for event) |
| F9 | Debug Support | Halt-on-debug, BKPT, DBGRQ/DBGACK, single-step |

### 3.2 Pipeline FSM

| State | Trigger / Entry Condition | Actions |
|-------|--------------------------|---------|
| **FETCH** | Default after WRITEBACK or branch flush | Drive HADDR=PC, assert AHB read, wait for HREADY |
| **DECODE** | Instruction word received (HREADY=1) | Parse opcode, determine class, read register operands |
| **EXECUTE** | Decode complete | ALU operation, address calc, branch resolution |
| **WRITEBACK** | Execute result ready | Write result to register file, update APSR flags, advance PC |
| **STALL** | HREADY=0 during AHB transfer | Freeze pipeline, hold state, retry bus |
| **EXC_ENTRY** | Pending exception with sufficient priority | Save {R0–R3, R12, LR, PC, xPSR}, set LR=EXC_RETURN |
| **VECTOR_FETCH** | Stacking complete | Fetch handler address from vector table |
| **EXC_RETURN** | BX LR with EXC_RETURN value | Unstack registers, restore SP, clear IPSR |

### 3.3 Instruction Latency (best case, 0 AHB wait states)

| Category | Cycles | Notes |
|----------|--------|-------|
| ALU (ADD, SUB, MOV, AND, ORR, EOR) | 1 | Single-cycle |
| Shift (LSL, LSR, ASR) | 1 | Inline barrel shifter |
| Compare (CMP, CMN, TST) | 1 | Flags only |
| Branch not-taken | 0 | No penalty |
| Branch taken (B, B<cond>) | 2–3 | Pipeline flush |
| Function call (BL) | 3–4 | Flush + LR save |
| Load (LDR/LDRH/LDRB) | 2 | 1 addr + 1 data (N+1 with wait states) |
| Store (STR/STRH/STRB) | 2 | 1 addr + 1 data (N+1 with wait states) |
| PUSH/POP (multiple) | N+1 | N registers + 1 |
| Multiply (MUL) | 1 or 32 | Single-cycle or iterative |
| WFI/WFE | 1 (then sleep) | Core halts until wake |

### 3.4 Interrupt Latency

| Scenario | Cycles |
|----------|--------|
| IRQ assert → first handler instruction | ≥16 |
| Tail-chain (exception → exception) | ≥6 |
| Late arrival | ≥16 |

### 3.5 Throughput

| Scenario | IPC |
|----------|-----|
| Sequential ALU ops | 1.0 |
| Sequential loads (0 wait states) | 0.5 |
| Mixed (70% ALU, 30% MEM) | ~0.77 |

### 3.6 Constraints

| Constraint | Value |
|-----------|-------|
| Pipeline depth | 3 stages |
| Issue width | Single-issue, in-order |
| Branch prediction | None (always not-taken) |
| Data forwarding | None |
| Write buffer | None (blocking stores) |

---

## 4. Register Map

### 4.1 Overview

Internal CPU registers accessed via MRS/MSR instructions. No APB/AXI-Lite register slave interface.

### 4.2 Core Special Registers

| # | Register | Width | Access | Reset Value | Description |
|---|----------|-------|--------|-------------|-------------|
| 1 | APSR | 32 | RW (partial) | 0x00000000 | Application Program Status Register |
| 2 | IPSR | 32 | RO | 0x00000000 | Interrupt Program Status Register |
| 3 | EPSR | 32 | RO | 0x01000000 | Execution Program Status Register |
| 4 | PRIMASK | 32 | RW | 0x00000000 | Interrupt Mask Register |
| 5 | CONTROL | 32 | RW | 0x00000000 | Control Register |
| 6 | MSP | 32 | RW | INIT_SP | Main Stack Pointer |
| 7 | PSP | 32 | RW | 0x00000000 | Process Stack Pointer |

### 4.3 APSR Bitfields

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [31] | N | RW | 0 | Negative flag |
| [30] | Z | RW | 0 | Zero flag |
| [29] | C | RW | 0 | Carry flag |
| [28] | V | RW | 0 | Overflow flag |
| [27:0] | — | — | 0 | Reserved (RAZ, WI) |

### 4.4 IPSR Bitfields

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [8:0] | ISR_NUMBER | RO | 0 | Exception number (0=Thread, 2=NMI, 3=HardFault, 11=SVCall, 14=PendSV, 15=SysTick, 16+=IRQ[n]) |
| [31:9] | — | — | 0 | Reserved |

### 4.5 EPSR Bitfields

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [24] | T | RO | 1 | Thumb bit (always 1) |
| [31:25], [23:0] | — | — | 0 | Reserved |

### 4.6 PRIMASK Bitfields

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [0] | PM | RW | 0 | 0=interrupts enabled, 1=all masked (except NMI/HardFault) |
| [31:1] | — | — | 0 | Reserved |

### 4.7 CONTROL Bitfields

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [0] | SPSEL | RW | 0 | 0=MSP in Thread, 1=PSP in Thread. Handler always uses MSP. |
| [31:1] | — | — | 0 | Reserved |

### 4.8 General-Purpose Registers

| Register | Alias | Description |
|----------|-------|-------------|
| R0–R3 | — | Arguments / results |
| R4–R11 | — | Callee-saved |
| R12 | IP | Caller-saved scratch |
| R13 | SP | Stack pointer (banked MSP/PSP) |
| R14 | LR | Link register / EXC_RETURN |
| R15 | PC | Program counter |

### 4.9 Exception Return Values

| EXC_RETURN | Return To | SP |
|-----------|----------|-----|
| 0xFFFFFFF1 | Handler mode | MSP |
| 0xFFFFFFF9 | Thread mode | MSP |
| 0xFFFFFFFD | Thread mode | PSP |

---

## 5. Interrupt Requirements

### 5.1 Overview

The core is an interrupt **consumer/handler** — it does NOT generate outbound interrupts.

### 5.2 External Interrupt Inputs

| Signal | Width | Polarity | Type | Sync |
|--------|-------|----------|------|------|
| IRQ | IRQ_NUM | Active-high | Level-sensitive | 2-stage FF to HCLK |
| NMI | 1 | Active-high | Edge-sensitive (rising) | 2-stage FF to HCLK |

### 5.3 Exception Table

| # | Exception | Source | Priority | Maskable |
|---|-----------|--------|----------|----------|
| 1 | Reset | HRESETn | -3 (highest) | No |
| 2 | NMI | NMI pin | -2 | No |
| 3 | HardFault | Internal (undef instr, bad access, stacking fault) | -1 | No |
| 11 | SVCall | SVC instruction | Configurable | Yes (PRIMASK) |
| 14 | PendSV | Software pended | Configurable | Yes (PRIMASK) |
| 15 | SysTick | 24-bit timer zero | Configurable | Yes (PRIMASK) |
| 16+n | IRQ[n] | IRQ[n] pin | Configurable | Yes (PRIMASK) |

### 5.4 HardFault Triggers

| Trigger | Condition | Clear Path |
|---------|-----------|------------|
| Undefined instruction | Invalid ARMv6-M encoding | Auto-clear on exception return |
| Invalid memory access | AHB HRESP=ERROR | Auto-clear on exception return |
| Stacking fault | Fault during exception entry/exit | Escalates to HardFault |

### 5.5 Interrupt Processing

- **Entry:** Stack {R0–R3, R12, LR, PC, xPSR} → set LR=EXC_RETURN → vector fetch
- **Exit:** BX LR with EXC_RETURN → unstack → resume
- **Tail-chaining:** Skip unstacking, reuse frame, fetch new vector (≥6 cycles)
- **Late arrival:** Abandon lower-priority stacking, restart for higher priority

---

## 6. Memory Requirements

### 6.1 Internal Memory Instances

| Instance | Type | Entries × Width | Read | Write | Latency | Reset |
|----------|------|----------------|------|-------|---------|-------|
| GPRF | Register File (FF) | 17 × 32-bit | 2 | 1 | 0 cyc | R0–12=0, SP=INIT_SP, LR=0xFFFFFFFF, PC=INIT_PC |
| SPR | Flip-flops | 5 × 32-bit | 1 | 1 | 0 cyc | See Section 4.2 |
| NVIC pending | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 (W1C) | 0 cyc | All zeros (no pending) |
| NVIC enable | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 | 0 cyc | All zeros (all disabled) |
| NVIC active | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 (auto) | 0 cyc | All zeros |
| NVIC priority | Bit array (FF) | IRQ_NUM × N-bit | 1 | 1 | 0 cyc | All zeros |
| SysTick counter | Counter (FF) | 1 × 24-bit | 1 | 1 | 0 cyc | 0 |
| SysTick reload | Register (FF) | 1 × 24-bit | 1 | 1 | 0 cyc | 0 |

**Total internal storage (IRQ_NUM=32, 2-bit priority): ~912 bits (~114 bytes)**

### 6.2 External Memory Map (ARMv6-M Architectural)

| Address Range | Size | Region |
|--------------|------|--------|
| 0x00000000–0x1FFFFFFF | 512 MB | Code (instructions + literals) |
| 0x20000000–0x3FFFFFFF | 512 MB | SRAM |
| 0x40000000–0x5FFFFFFF | 512 MB | Peripheral |
| 0x60000000–0x9FFFFFFF | 1 GB | External RAM |
| 0xA0000000–0xDFFFFFFF | 1 GB | External Device |
| 0xE0000000–0xE00FFFFF | 1 MB | System Control Space (NVIC, SysTick, SCB) |
| 0xE0100000–0xFFFFFFFF | ~16 MB | Vendor System |

### 6.3 Vector Table (Code region, offset 0x00)

| Offset | Content |
|--------|---------|
| 0x00 | Initial MSP |
| 0x04 | Reset vector (initial PC) |
| 0x08 | NMI handler |
| 0x0C | HardFault handler |
| 0x2C | SVCall handler |
| 0x3C | PendSV handler |
| 0x40 | SysTick handler |
| 0x44+ | IRQ[0], IRQ[1], ... |

### 6.4 Bus Access

| Property | Value |
|----------|-------|
| Bus type | Single shared AHB-Lite |
| Endianness | Little-endian |
| Unaligned access | Not supported (HardFault) |
| ECC/Parity | None required (all internal storage is FF-based) |

---

## 7. Timing & Constraints

### 7.1 Target Clock

| Parameter | Value |
|-----------|-------|
| Target frequency | 50 MHz (20 ns period) |
| Clock domain | Single (HCLK) |
| PLL/DLL | Not required |

### 7.2 CDC Paths

| Signal | Synchronizer | Latency |
|--------|-------------|---------|
| IRQ[IRQ_NUM-1:0] | 2-stage FF | 2 cycles |
| NMI | 2-stage FF | 2 cycles |
| DBGRQ | 2-stage FF | 2 cycles |
| HRESETn | Async assert, sync deassert | — |

### 7.3 Critical Path

**Expected critical path:** Register File read → ALU (32-bit add/sub) → condition code generation → APSR writeback (3–4 LUT levels on FPGA)

### 7.4 Multicycle Paths

| Path | Cycles | Condition |
|------|--------|-----------|
| MUL (iterative) | Up to 32 | MUL instruction |
| AHB wait states | N+1 | HREADY=0 |
| Exception stacking | 8+ | EXC_ENTRY |

### 7.5 Timing Summary

| Constraint | Value |
|-----------|-------|
| All outputs registered | Yes (HADDR, HWDATA, HTRANS, HSIZE, etc.) |
| Async inputs synchronized | IRQ, NMI, DBGRQ (2-stage FF) |
| False paths | Reset → functional registers |
| No timing exceptions for | Single-cycle ALU, register file, AHB outputs |

---

## 8. Design Verification Requirements

### 8.1 Test Scenarios Summary

| Category | Tests | Priority |
|----------|-------|----------|
| Core Instructions (T1–T15) | ALU, shift, compare, move, multiply, branch, load/store, MRS/MSR, CPS, WFI/WFE | P0/P1 |
| Exceptions & Interrupts (T16–T27) | IRQ/NMI entry/return, HardFault, SVCall, nested, tail-chain, late arrival, PRIMASK, SysTick | P0/P1 |
| Reset & Initialization (T28–T30) | Cold reset, reset during execution, reset during exception | P0/P1 |
| Pipeline & Bus (T31–T34) | Stall, back-to-back, load-use hazard, branch-after-branch | P0/P1 |
| Debug (T35–T37) | BKPT, DBGRQ/DBGACK, single-step | P1/P2 |

**Total: 37 test scenarios**

### 8.2 Corner Cases

13 corner cases documented (C1–C13): SP wrap, invalid EXC_RETURN, exception during stacking, NMI during HardFault, zero-length PUSH/POP, max MUL overflow, unaligned branch, WFI with pending interrupt, etc.

### 8.3 SVA Assertions

| Category | Count | IDs |
|----------|-------|-----|
| AHB-Lite protocol | 5 | SVA01–SVA05 |
| Microarchitecture | 7 | SVA06–SVA12 |

### 8.4 Cover Points

10 functional cover points (CV01–CV10): all ALU opcodes, all condition codes, all flags, all exception types, tail-chain, late-arrival, bus stall, SP switching, WFI.

### 8.5 Coverage Targets

| Type | Target |
|------|--------|
| Line coverage | ≥ 95% |
| Toggle coverage | ≥ 90% |
| FSM state coverage | 100% |
| FSM transition coverage | ≥ 95% |
| Functional coverage | 100% (CV01–CV10) |
| Branch coverage | ≥ 95% |

### 8.6 Pass/Fail Criteria

| Criterion | Requirement |
|-----------|-------------|
| P0 tests | 100% pass |
| P1 tests | ≥ 95% pass |
| SVA assertions | Zero failures |
| X/Z propagation | Zero in functional paths |
| Regression | < 30 minutes (Verilator) |

---

## 9. Open Items

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | IT blocks (If-Then) | Deferred | Excluded from initial subset for area |
| 2 | Unprivileged mode | Excluded | No nPRIV in Cortex-M0 |
| 3 | Multiplier implementation | TBD at RTL | Single-cycle or iterative (32-cycle) |
| 4 | NVIC priority width | TBD at RTL | Min 2 bits (4 levels), max 8 bits (256 levels) |
| 5 | Separate I/D bus | Deferred | Single shared AHB-Lite; Harvard possible later |

---

## Detailed Requirement Documents

The following individual documents contain full details for each phase:

| Document | File |
|----------|------|
| Module Context | `cortex_m0_core/req/context.md` |
| Interface Specification | `cortex_m0_core/req/interface.md` |
| Functional Requirements | `cortex_m0_core/req/functional.md` |
| Register Map | `cortex_m0_core/req/register_map.md` |
| Interrupt Requirements | `cortex_m0_core/req/interrupts.md` |
| Memory Requirements | `cortex_m0_core/req/memory.md` |
| Timing & Constraints | `cortex_m0_core/req/timing.md` |
| DV Plan | `cortex_m0_core/req/dv_plan.md` |
