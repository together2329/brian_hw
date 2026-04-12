# Cortex-M0 Core — Interrupt Requirements

## Overview

The Cortex-M0 core does **not generate outbound interrupts** to other IPs.
Instead, it **receives and processes** inbound interrupt requests via its NVIC and internal exception sources.
The core is an interrupt **consumer/handler**, not a source.

---

## 1. External Interrupt Inputs (Consumed by Core)

### 1.1 Input Signal Summary

| Signal | Width | Polarity | Type | Description |
|--------|-------|----------|------|-------------|
| IRQ | IRQ_NUM (default 32) | Active-high | Level-sensitive | Maskable interrupt requests from peripherals |
| NMI | 1 | Active-high | Edge-sensitive (rising) | Non-maskable interrupt — highest priority after Reset |

### 1.2 IRQ Interface Details

| Property | Value |
|----------|-------|
| Min IRQ lines | 1 |
| Max IRQ lines | 240 (parameterized via IRQ_NUM) |
| Default IRQ lines | 32 |
| Trigger type | Level-sensitive (IRQ must remain asserted until serviced) |
| Polarity | Active-high (1 = interrupt pending) |
| Synchronization | IRQ inputs are synchronized to HCLK domain (2-stage sync) |

### 1.3 NMI Interface Details

| Property | Value |
|----------|-------|
| Trigger type | Edge-sensitive (rising edge detected) |
| Polarity | Active-high |
| Priority | Fixed at -2 (second only to Reset) |
| Maskable | No — cannot be disabled by PRIMASK |
| Synchronization | Synchronized to HCLK domain (2-stage sync) |

---

## 2. Internal Exception Sources (Generated Inside Core)

### 2.1 Exception Table

| # | Exception | Source | Trigger Condition | Priority | Maskable |
|---|-----------|--------|-------------------|----------|----------|
| 1 | Reset | External | HRESETn deassertion (rising edge) | -3 (highest) | No |
| 2 | NMI | External (NMI pin) | Rising edge on NMI input | -2 | No |
| 3 | HardFault | Internal | Undefined instruction, invalid memory access, fault during exception handling | -1 | No |
| 11 | SVCall | Software | Execution of `SVC` instruction | Configurable (min 0) | Yes (PRIMASK) |
| 14 | PendSV | Software / System | Set via SCB ICPR register (pendable, asynchronous) | Configurable (min 0) | Yes (PRIMASK) |
| 15 | SysTick | Internal (SysTick timer) | 24-bit down-counter reaches zero | Configurable (min 0) | Yes (PRIMASK) |
| 16+n | IRQ[n] | External (IRQ[n] pin) | IRQ[n] asserted (level-high) | Configurable (min 0) | Yes (PRIMASK) |

### 2.2 HardFault Trigger Conditions

| Trigger | Condition | Clear Path |
|---------|-----------|------------|
| Undefined instruction | Decoded instruction is not a valid ARMv6-M encoding | Auto-clear on exception return |
| Invalid memory access | AHB HRESP=ERROR during instruction fetch or data access | Auto-clear on exception return |
| Stacked fault | Fault occurs during exception entry/exit stacking | Escalates to HardFault (nested) |
| SVCall at wrong priority | SVC executed at priority ≥ SVCall priority | Auto-clear on exception return |

### 2.3 SysTick Timer Interrupt

| Property | Value |
|----------|-------|
| Timer width | 24-bit down-counter |
| Clock source | HCLK (or external reference, implementation choice) |
| Reload | SYST_RVR register (24-bit value) |
| Current | SYST_CVR register (24-bit, reads current count) |
| Trigger | Count reaches zero → asserted for 1 cycle |
| Clear mechanism | Auto-clear (reads SYST_CVR clears pending) or W1C via SCB ICPR |
| Enable | SYST_CSR.ENABLE bit |
| Interrupt enable | SYST_CSR.TICKINT bit |

---

## 3. Interrupt Processing Flow

### 3.1 Entry Sequence

```
IRQ[n] asserted (level-high)
    │
    ▼
[HCLK sync — 2 cycles]
    │
    ▼
NVIC: pending bit set for IRQ[n]
    │
    ▼
Priority arbitration (vs. active exceptions)
    │
    ▼ (if highest pending and PRIMASK=0)
Processor completes current instruction
    │
    ▼
EXC_ENTRY state:
    1. Push {R0, R1, R2, R3, R12, LR, PC, xPSR} to active SP
    2. Set LR = EXC_RETURN value
    3. Update IPSR = exception_number
    4. Switch SP to MSP (if in Thread mode)
    │
    ▼
VECTOR_FETCH state:
    Fetch handler address from VectorTable[exception_number * 4]
    │
    ▼
PC = handler address, execution continues
```

### 3.2 Exit Sequence (EXC_RETURN)

```
Handler executes BX LR (or POP {PC}) with EXC_RETURN value
    │
    ▼
EXC_RETURN state:
    1. Detect EXC_RETURN pattern (0xFFFFFFFx)
    2. Pop {R0, R1, R2, R3, R12, LR, PC, xPSR} from SP
    3. Restore SP selection (MSP/PSP) per CONTROL.SPSEL
    4. Clear IPSR
    │
    ▼
Resume execution at restored PC
```

### 3.3 Tail-Chaining

```
Exception A active
    │
    ▼ (Exception B pending with higher/equal priority)
EXC_RETURN from A:
    - Skip unstacking of A
    - Immediately VECTOR_FETCH for B
    - Reuse stacked frame from A
    │
    ▼
Execute handler B (tail-chain latency: ≥6 cycles)
```

### 3.4 Late Arrival

```
Exception A stacking in progress
    │
    ▼ (Exception B has higher priority than A)
Abandon A's stacking
    │
    ▼
Restart stacking for B (overwrites partial A stack frame)
    │
    ▼
VECTOR_FETCH for B instead of A
```

---

## 4. Priority Configuration

### 4.1 Priority Levels

| Exception | Fixed Priority | Configurable? |
|-----------|---------------|---------------|
| Reset | -3 (highest) | No |
| NMI | -2 | No |
| HardFault | -1 | No |
| SVCall | 0–255 | Yes |
| PendSV | 0–255 | Yes |
| SysTick | 0–255 | Yes |
| IRQ[0]–IRQ[n] | 0–255 | Yes |

### 4.2 Priority Register Layout (External NVIC)

> Note: NVIC priority registers are in SCS space (0xE000E000+), accessed via AHB load/store.

| Register | Offset | Width | Description |
|----------|--------|-------|-------------|
| NVIC_IPR0–IPR60 | 0xE000E400+ | 32 (4 × 8-bit fields) | Interrupt Priority Registers, 4 priorities per register |

Priority is implemented as **N-bit priority** (implementation defined, min 2 bits = 4 levels).
Higher priority = lower numerical value.

---

## 5. Latency Summary

| Scenario | Min Cycles | Description |
|----------|-----------|-------------|
| IRQ assert → handler PC fetched | ≥16 | Stacking (8 words) + vector fetch |
| NMI assert → handler PC fetched | ≥16 | Same flow as IRQ |
| Tail-chain (A→B) | ≥6 | Skip stacking, vector fetch only |
| Late arrival | ≥16 | Restart stacking for higher priority |
| SVCall → handler | ≥16 | Same as IRQ (software triggered) |
| SysTick → handler | ≥16 | Same as IRQ (timer triggered) |

---

## 6. Interrupt-Related Output Signals

| Signal | Direction | Polarity | Description |
|--------|-----------|----------|-------------|
| EVTEXEC | output | Active-high | Pulsed when WFE event occurs (can wake other cores) |

> The Cortex-M0 core does NOT drive any IRQ output to other IPs.
> It receives IRQs and handles them internally.
