# Cortex-M0 Core — Memory Requirements

## Overview

The Cortex-M0 core has **no large SRAM or FIFO** memories. It contains two internal memory structures:
1. **Register File** — general-purpose and special-purpose registers
2. **NVIC Register Arrays** — interrupt pending/enable/priority bit arrays

All instruction and data memory is **external**, accessed via the AHB-Lite bus interface.

---

## 1. Memory Instances

### 1.1 General-Purpose Register File (GPRF)

| Property | Value |
|----------|-------|
| Type | Register File (flip-flop based) |
| Depth | 16 entries (R0–R12, SP, LR, PC) |
| Width | 32 bits per entry |
| Read ports | 2 (simultaneous 32-bit reads for ALU source operands) |
| Write ports | 1 (single 32-bit write for ALU result / load result) |
| Latency | 0 cycles (combinational read, synchronous write) |
| Reset state | R0–R12 = 0x00000000; SP = INIT_SP; LR = 0xFFFFFFFF; PC = INIT_PC |

**Banking notes:**
- R13 (SP) is banked: MSP and PSP (2 physical registers, selected by CONTROL.SPSEL)
- R14 (LR) stores return address or EXC_RETURN value
- R15 (PC) is read-only via register file (written by PC increment logic / branch logic)

**Total register count:** 16 GPR + 1 PSP = 17 physical 32-bit registers

### 1.2 Special-Purpose Registers (SPR)

| Property | Value |
|----------|-------|
| Type | Flip-flop based |
| Count | 5 registers |
| Width | 32 bits each |
| Read ports | 1 (MRS instruction) |
| Write ports | 1 (MSR instruction) |
| Latency | 0 cycles (combinational read, synchronous write) |

| Register | Reset Value | Notes |
|----------|-------------|-------|
| APSR | 0x00000000 | Flags: N,Z,C,V |
| IPSR | 0x00000000 | Exception number |
| EPSR | 0x01000000 | T-bit = 1 |
| PRIMASK | 0x00000000 | Interrupt mask |
| CONTROL | 0x00000000 | SPSEL bit |

### 1.3 NVIC Register Arrays

| Property | Value |
|----------|-------|
| Type | Flip-flop based bit arrays |
| Width | IRQ_NUM bits |
| Depth | 1 bit per IRQ line |
| Reset state | All zeros (no pending, all disabled) |

| Array | Width | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| IRQ pending | IRQ_NUM | RW (W1C to clear) | 0 | Pending state for each IRQ |
| IRQ enable | IRQ_NUM | RW | 0 | Enable mask for each IRQ |
| IRQ active | IRQ_NUM | RW (auto-set/clear) | 0 | Active state (set on entry, cleared on return) |
| IRQ priority | IRQ_NUM × N bits | RW | 0 | N-bit priority per IRQ (min 2 bits) |

> For default IRQ_NUM=32: 32-bit pending, 32-bit enable, 32-bit active, 32×2-bit priority = 320 bits total.

### 1.4 SysTick Timer Registers

| Property | Value |
|----------|-------|
| Type | Flip-flop based counters |
| Width | 24-bit counter + 24-bit reload |
| Depth | 2 registers |
| Reset state | CSR=0, RVR=0, CVR=0 |
| Latency | 0 cycles (combinational read) |

---

## 2. Memory Map (External — via AHB-Lite)

The core accesses all instruction and data memory through the AHB-Lite bus.
The ARMv6-M memory map is **architecturally defined** as follows:

| Address Range | Size | Name | Description |
|--------------|------|------|-------------|
| 0x00000000–0x1FFFFFFF | 512 MB | Code | Instruction fetch and literal data |
| 0x20000000–0x3FFFFFFF | 512 MB | SRAM | Data RAM |
| 0x40000000–0x5FFFFFFF | 512 MB | Peripheral | Device registers |
| 0x60000000–0x9FFFFFFF | 1 GB | External RAM | Off-chip memory |
| 0xA0000000–0xDFFFFFFF | 1 GB | External Device | Off-chip device registers |
| 0xE0000000–0xE00FFFFF | 1 MB | System Control Space (SCS) | NVIC, SysTick, SCB registers |
| 0xE0100000–0xFFFFFFFF | ~16 MB | Vendor System | Vendor-specific system space |

### 2.1 Vector Table (in Code region)

| Offset | Content | Reset Value |
|--------|---------|-------------|
| 0x00 | Initial SP value (MSP) | Loaded from memory on reset |
| 0x04 | Reset vector (initial PC) | Loaded from memory on reset |
| 0x08 | NMI handler address | — |
| 0x0C | HardFault handler address | — |
| 0x10–0x28 | Reserved | — |
| 0x2C | SVCall handler address | — |
| 0x30–0x38 | Reserved | — |
| 0x3C | PendSV handler address | — |
| 0x40 | SysTick handler address | — |
| 0x44+ | IRQ[0] handler address, IRQ[1], ... | — |

### 2.2 Bus Access Characteristics

| Property | Value |
|----------|-------|
| Instruction fetch bus | AHB-Lite read, 32-bit |
| Data access bus | AHB-Lite read/write, 32-bit (supports byte/halfword/word) |
| Shared bus or separate | Single shared AHB-Lite bus (instructions and data share HADDR/HDATA) |
| Endianness | Little-endian |
| Unaligned access | Not supported (generates HardFault on unaligned access) |

---

## 3. ECC / Parity Requirements

| Memory | ECC/Parity | Notes |
|--------|-----------|-------|
| GPRF (R0–R15) | None | Flip-flop based, no ECC needed |
| SPR (APSR/IPSR/EPSR/PRIMASK/CONTROL) | None | Flip-flop based |
| NVIC arrays | None | Flip-flop based |
| SysTick counter | None | Flip-flop based |
| External SRAM/Flash | Implementation-dependent | Not part of core; handled by memory controller |

**No ECC or parity is required for any internal memory structure.**

---

## 4. Memory Summary

| Instance | Type | Entries × Width | Read Ports | Write Ports | Latency |
|----------|------|----------------|------------|-------------|---------|
| GPRF | Register File (FF) | 17 × 32-bit | 2 | 1 | 0 cycles |
| SPR | Flip-flops | 5 × 32-bit | 1 | 1 | 0 cycles |
| NVIC pending | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 | 0 cycles |
| NVIC enable | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 | 0 cycles |
| NVIC active | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 | 0 cycles |
| NVIC priority | Bit array (FF) | IRQ_NUM × N-bit | 1 | 1 | 0 cycles |
| SysTick counter | Counter (FF) | 1 × 24-bit | 1 | 1 | 0 cycles |
| SysTick reload | Register (FF) | 1 × 24-bit | 1 | 1 | 0 cycles |

**Total internal storage (default IRQ_NUM=32, 2-bit priority):**
- GPRF: 17 × 32 = 544 bits
- SPR: 5 × 32 = 160 bits
- NVIC: 32 + 32 + 32 + 64 = 160 bits
- SysTick: 24 + 24 = 48 bits
- **Grand total: ~912 bits (~114 bytes) of internal storage**
