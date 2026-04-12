# Cortex-M0 Core — Register Map

## Overview

The Cortex-M0 core uses **internal CPU registers** accessed via MRS/MSR instructions.
There is **no APB/AXI-Lite register slave interface** — the core is an AHB-Lite bus master only.
Memory-mapped system registers (NVIC, SysTick, SCB) are in the System Control Space (SCS)
at 0xE000E000–0xE000EFFF but are external to the core itself.

---

## 1. Core Registers (MRS/MSR Accessible)

### 1.1 Register Summary

| # | Register | MRS/MSR Name | Width | Access | Reset Value | Description |
|---|----------|-------------|-------|--------|-------------|-------------|
| 1 | APSR | `APSR` | 32 | RW (partial) | 0x00000000 | Application Program Status Register |
| 2 | IPSR | `IPSR` | 32 | RO | 0x00000000 | Interrupt Program Status Register |
| 3 | EPSR | `EPSR` | 32 | RO | 0x01000000 | Execution Program Status Register |
| 4 | PRIMASK | `PRIMASK` | 32 | RW | 0x00000000 | Interrupt Mask Register |
| 5 | CONTROL | `CONTROL` | 32 | RW | 0x00000000 | Control Register |
| 6 | MSP | `MSP` | 32 | RW | INIT_SP param | Main Stack Pointer |
| 7 | PSP | `PSP` | 32 | RW | 0x00000000 | Process Stack Pointer |

> Note: APSR, IPSR, EPSR can also be read/written collectively as `xPSR` via special access.

---

## 2. Bitfield Definitions

### 2.1 APSR — Application Program Status Register

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [31] | N | RW | 0 | **Negative flag.** Set to the value of bit[31] of the result of the last ALU operation. |
| [30] | Z | RW | 0 | **Zero flag.** Set to 1 if the result of the last ALU operation was zero. |
| [29] | C | RW | 0 | **Carry flag.** Set to 1 if the last operation generated a carry out. |
| [28] | V | RW | 0 | **Overflow flag.** Set to 1 if the last operation generated a signed overflow. |
| [27:0] | — | — | 0 | **Reserved.** Reads-as-zero, writes ignored. |

### 2.2 IPSR — Interrupt Program Status Register

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [8:0] | ISR_NUMBER | RO | 0x000 | **Exception number.** 0=Thread mode, 2=NMI, 3=HardFault, 11=SVCall, 14=PendSV, 15=SysTick, 16+=IRQ[n]. |
| [31:9] | — | — | 0 | **Reserved.** Reads-as-zero. |

**ISR_NUMBER Encoding:**

| Value | Exception |
|-------|-----------|
| 0 | Thread mode (no active exception) |
| 2 | NMI |
| 3 | HardFault |
| 11 | SVCall |
| 14 | PendSV |
| 15 | SysTick |
| 16 | IRQ[0] |
| 16+n | IRQ[n] |

### 2.3 EPSR — Execution Program Status Register

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [24] | T | RO | 1 | **Thumb bit.** Always 1 in ARMv6-M. Reading returns 1, writes ignored. |
| [31:25] | — | — | 0 | **Reserved.** Reads-as-zero. |
| [23:0] | — | — | 0 | **Reserved.** Reads-as-zero. |

### 2.4 PRIMASK — Interrupt Mask Register

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [0] | PM | RW | 0 | **Priority mask.** 0=interrupts enabled, 1=all interrupts masked (except NMI and HardFault). |
| [31:1] | — | — | 0 | **Reserved.** Reads-as-zero, writes ignored. |

**Modification instructions:**
- `CPSIE I` → PRIMASK.PM = 0 (enable interrupts)
- `CPSID I` → PRIMASK.PM = 1 (disable interrupts)

### 2.5 CONTROL — Control Register

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [0] | SPSEL | RW | 0 | **Stack pointer select (Thread mode only).** 0=MSP, 1=PSP. Ignored in Handler mode (always MSP). |
| [1] | — | — | 0 | **Reserved.** Reads-as-zero, writes ignored. |
| [31:2] | — | — | 0 | **Reserved.** Reads-as-zero, writes ignored. |

### 2.6 MSP — Main Stack Pointer

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [31:2] | SP_MAIN | RW | INIT_SP[31:2] | **Main stack pointer.** Bits [1:0] are reserved (always zero, SP is word-aligned). |
| [1:0] | — | — | 0 | **Reserved.** Forced to zero on write. |

### 2.7 PSP — Process Stack Pointer

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| [31:2] | SP_PROCESS | RW | 0x00000000[31:2] | **Process stack pointer.** Only used in Thread mode when CONTROL.SPSEL=1. |
| [1:0] | — | — | 0 | **Reserved.** Forced to zero on write. |

---

## 3. General-Purpose Register File

| Register | Alias | Description |
|----------|-------|-------------|
| R0 | — | General-purpose (argument/result) |
| R1 | — | General-purpose |
| R2 | — | General-purpose |
| R3 | — | General-purpose (argument) |
| R4 | — | General-purpose (callee-saved) |
| R5 | — | General-purpose (callee-saved) |
| R6 | — | General-purpose (callee-saved) |
| R7 | — | General-purpose (callee-saved) |
| R8 | — | General-purpose (callee-saved) |
| R9 | — | General-purpose (callee-saved) |
| R10 | — | General-purpose (callee-saved) |
| R11 | — | General-purpose (callee-saved) |
| R12 | IP | General-purpose (caller-saved, intra-procedure scratch) |
| R13 | SP | Stack pointer (banked: MSP / PSP) |
| R14 | LR | Link register (return address / EXC_RETURN) |
| R15 | PC | Program counter |

---

## 4. Exception Return Values (EXC_RETURN)

The LR is loaded with a special EXC_RETURN value on exception entry. These values are
used by BX/POP to detect exception return.

| EXC_RETURN | Return To | SP Used |
|-----------|----------|---------|
| 0xFFFFFFF1 | Handler mode | MSP |
| 0xFFFFFFF9 | Thread mode | MSP |
| 0xFFFFFFFD | Thread mode | PSP |

Bits [3:0] encode return behavior. All other bits are 1's.

---

## 5. Register Interface Summary

| Property | Value |
|----------|-------|
| Register interface type | Internal CPU registers (MRS/MSR) |
| Memory-mapped base address | N/A (core has no register slave) |
| SCS address range (external) | 0xE000E000–0xE000EFFF |
| Total internal registers | 7 special + 13 GPR (R0–R12) + SP(MSP/PSP) + LR + PC |
| Register width | 32 bits (all) |
