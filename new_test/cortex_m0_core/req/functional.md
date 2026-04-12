# Cortex-M0 Core — Functional Requirements

## 1. Major Features

### F1: Instruction Fetch & Execute
- **Trigger:** Core is running (not halted/sleeping)
- **Data Flow:** PC → AHB fetch → instruction word → decode → execute → result
- **Output:** Register file updated, memory accessed, PC advanced

### F2: ARMv6-M Instruction Subset
- **16-bit Thumb instructions (most):** MOV, ADD, SUB, AND, ORR, EOR, LSL, LSR, CMP, LDR, STR, PUSH, POP, B, BLX, BX, etc.
- **32-bit Thumb-2 instructions:** BL, DMB, DSB, ISB, MSR, MRS, MRS (special registers)
- **Excluded from initial subset:** Unprivileged instructions, IT blocks (simplified)

### F3: Register File
- **Registers:** R0–R12 (general purpose), R13=SP (MSP/PSP banked), R14=LR, R15=PC
- **Special Registers:** xPSR (APSR[31:27], IPSR[8:0], EPSR[24]), PRIMASK, CONTROL

### F4: NVIC (Nested Vectored Interrupt Controller)
- **Trigger:** IRQ[i] asserted AND PRIMASK=0 AND priority allows
- **Data Flow:** IRQ assert → priority arbitrate → push {xPSR, PC, LR, R3-R0} → fetch vector
- **Output:** PC = exception handler address, IPSR updated
- **Features:** Tail-chaining, late arrival, configurable priority levels (min 2, max 8 bits → 256 levels)

### F5: Exception Handling
- **Exceptions (priority order):**
  1. Reset (highest)
  2. NMI
  3. HardFault
  4. SVCall (supervisor call)
  5. PendSV (pendable service call)
  6. SysTick
  7. IRQ[0]–IRQ[n] (lowest)
- **Entry:** Auto-push {R0–R3, R12, LR, PC, xPSR} to SP, fetch vector from vector table
- **Exit:** EXC_RETURN value in LR triggers unstack and return

### F6: Dual Stack Pointers
- **MSP (Main SP):** Used in Handler mode and Thread mode (default after reset)
- **PSP (Process SP):** Used in Thread mode when CONTROL[1]=1
- **Switching:** Automatic on exception entry/exit based on CONTROL register

### F7: SysTick Timer
- **24-bit down-counting timer** with reload value register
- **Triggers SysTick exception** on count-down to zero
- **CSR register controls:** ENABLE, TICKINT, CLKSOURCE

### F8: Sleep Modes (WFI/WFE)
- **WFI:** Core halts until IRQ/NMI or debug event
- **WFE:** Core halts until event (IRQ/NMI or external EVTEXEC signal)
- **Wake condition:** Pending interrupt with sufficient priority

### F9: Debug Support
- **BKPT instruction:** Halts core, asserts HALTED
- **DBGRQ input:** External debug halt request
- **DBGACK output:** Acknowledges debug halt
- **Single-step:** Core halts after each instruction in debug mode

---

## 2. Pipeline FSM

### 2.1 Main Pipeline States

| State | Trigger / Entry Condition | Actions |
|-------|--------------------------|---------|
| **FETCH** | Default state after WRITEBACK or branch flush | Drive HADDR=PC, assert AHB read, wait for HREADY |
| **DECODE** | Instruction word received (HREADY=1 in FETCH) | Parse opcode, determine class (ALU/MEM/BRANCH/SYSTEM), read register operands |
| **EXECUTE** | Decode complete | ALU operation, address calculation, branch resolution, condition check |
| **WRITEBACK** | Execute result ready | Write ALU result to register file, update APSR flags (N,Z,C,V), advance PC |
| **STALL** | HREADY=0 during any AHB transfer | Freeze entire pipeline, hold all state, retry bus transfer next cycle |

### 2.2 Exception Pipeline States

| State | Trigger / Entry Condition | Actions |
|-------|--------------------------|---------|
| **EXC_ENTRY** | Pending exception with sufficient priority | Save {R0–R3, R12, LR, PC, xPSR} to active SP, set LR=EXC_RETURN, update IPSR |
| **VECTOR_FETCH** | Stacking complete | Drive HADDR=VectorTable + (4 × exception_number), fetch handler PC |
| **EXC_RETURN** | BX LR with value in {0xFFFFFFF1..0xFFFFFFFD} | Unstack {R0–R3, R12, LR, PC, xPSR}, restore previous SP, clear IPSR |

### 2.3 FSM Diagram

```
                 ┌────────────────────────────────────────────┐
                 │        (branch taken / exception return)    │
                 ▼                                            │
           ┌──────────┐   HREADY    ┌──────────┐  ready  ┌──────────┐  done  ┌───────────┐
    ──────▶│  FETCH   │───────────▶│  DECODE  │───────▶│  EXECUTE │──────▶│ WRITEBACK │
           └──────────┘            └──────────┘         └──────────┘       └───────────┘
                │ ▲                                          │
                │ │ HREADY=0                                 │ (exception
                ▼ │                                          │  detected)
           ┌──────────┐                                     │
           │  STALL   │                                     │
           └──────────┘                                     │
                                                            ▼
                                                     ┌──────────────┐
                                                     │  EXC_ENTRY   │
                                                     └──────┬───────┘
                                                            │
                                                     ┌──────▼───────┐
                                                     │ VECTOR_FETCH │
                                                     └──────┬───────┘
                                                            │ (handler runs, then BX EXC_RETURN)
                                                     ┌──────▼───────┐
                                                     │  EXC_RETURN  │──▶ FETCH
                                                     └──────────────┘
```

---

## 3. Latency & Throughput

### 3.1 Instruction Latency (best case, 0 AHB wait states)

| Instruction Category | Cycles | Notes |
|---------------------|--------|-------|
| ALU (ADD, SUB, MOV, AND, ORR, EOR) | 1 | Single-cycle execute |
| Shift (LSL, LSR, ASR) | 1 | Barrel shifter inline |
| Compare (CMP, CMN, TST) | 1 | Flags only, no register writeback |
| Branch not-taken | 0 | No penalty (next fetch already valid) |
| Branch taken (B, B<cond>) | 2–3 | Pipeline flush + refetch |
| Function call (BL) | 3–4 | Pipeline flush + LR save + refetch |
| Load (LDR/LDRH/LDRB) | 2 | 1 address + 1 data (N+1 with wait states) |
| Store (STR/STRH/STRB) | 2 | 1 address + 1 data (N+1 with wait states) |
| PUSH (multiple) | N+1 | N registers + 1 (incremental AHB beats) |
| POP (multiple) | N+1 | N registers + 1 |
| Multiply (MUL) | 1 or 32 | Single-cycle (hardware) or iterative |
| MRS/MSR (special regs) | 1 | System register read/write |
| WFI/WFE | 1 (then sleep) | Core halts until wake event |
| BKPT | ∞ | Core halts until debug resume |

### 3.2 Interrupt Latency

| Metric | Cycles | Description |
|--------|--------|-------------|
| IRQ assert → first handler instruction | ≥16 | Per ARMv6-M spec: stacking + vector fetch |
| Tail-chain (exception → exception) | ≥6 | Reuses stacked frame, fetches new vector only |
| Late arrival (higher-priority preempts during stacking) | ≥16 | Aborts current stacking, restarts for higher priority |

### 3.3 Throughput

| Scenario | Throughput | Notes |
|----------|-----------|-------|
| Sequential ALU ops | 1 IPC | Single-issue, in-order, no hazards |
| Sequential loads (0 wait states) | 0.5 IPC | 2 cycles per load |
| Best-case mixed (70% ALU, 30% MEM) | ~0.77 IPC | Pipeline interleaving |
| Interrupt-heavy workload | < 0.5 IPC | Stacking/unstacking overhead |

---

## 4. Instruction Encoding Summary

| Encoding | Size | Bits |
|----------|------|------|
| Thumb-16 | 16 bits | Most common instructions |
| Thumb-32 | 32 bits | BL, MSR, MRS, DMB, DSB, ISB |

All instructions are little-endian and halfword-aligned.

---

## 5. Constraint Summary

| Constraint | Value |
|-----------|-------|
| Pipeline depth | 3 stages (Fetch, Decode, Execute) |
| Issue width | Single-issue, in-order |
| Branch prediction | None (static: always not-taken) |
| Data forwarding | None (pipeline simplified for area) |
| Write buffer | None (stores are blocking) |
