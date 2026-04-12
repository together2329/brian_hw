# Cortex-M0 Core — Micro-Architecture Specification (MAS)

> **IP Name:** `cortex_m0_core`
> **Version:** 1.0
> **Date:** 2025
> **Status:** Draft
> **Source:** `cortex_m0_core/req/` (9 requirement documents)

---

## §1 — Overview

### 1.1 Functional Description

The `cortex_m0_core` is a 32-bit, single-issue, in-order processor core implementing a subset of the ARMv6-M instruction set architecture (Thumb-16 + select Thumb-2), inspired by the ARM Cortex-M0. It features a 3-stage pipeline (Fetch → Decode → Execute) and communicates with external memory and peripherals exclusively through an AHB-Lite (AHB5 subset) bus master interface. The core integrates a Nested Vectored Interrupt Controller (NVIC) supporting 1–240 configurable external interrupt lines with priority-based preemption, tail-chaining, and late-arrival optimization. Internal state is held entirely in flip-flop–based structures (~912 bits for default configuration): a 17-entry × 32-bit general-purpose register file (R0–R12, banked MSP/PSP, LR, PC), five special-purpose registers (APSR, IPSR, EPSR, PRIMASK, CONTROL), NVIC pending/enable/active/priority arrays, and a 24-bit SysTick countdown timer. The core is designed as a minimal, area-optimized embedded processor suitable for IoT endpoints, sensor hubs, and microcontroller subsystems.

### 1.2 Key Design Goals

| Goal | Target | Rationale |
|------|--------|-----------|
| **Area** | Minimize gate count (~10–15K gates FPGA estimate) | Smallest viable ARMv6-M core for cost-sensitive IoT/MCU |
| **Throughput** | 1.0 IPC for sequential single-cycle ALU ops | Full pipeline utilization on common code |
| **Interrupt latency** | ≥16 cycles (IRQ assert → first handler instruction) | Matches ARMv6-M architectural requirement |
| **Clock frequency** | 50 MHz portable target (technology-independent RTL) | Works on low-cost FPGA and ASIC 180nm+ |
| **Power** | No explicit target; clock-gating friendly design | Single clock domain, WFI/WFE sleep support |
| **Verification** | ≥95% line, 100% FSM state, all P0 tests pass | Functional correctness for safety-relevant applications |

### 1.3 Key Features

- **ARMv6-M Instruction Subset** — 16-bit Thumb (most) + 32-bit Thumb-2 (BL, DMB, DSB, ISB, MSR, MRS); excludes IT blocks and unprivileged mode
- **3-Stage Pipeline** — Fetch → Decode → Execute with single-issue in-order execution
- **AHB-Lite Bus Master** — Single shared bus for instruction fetch and data access; registered outputs; HREADY-based stall
- **NVIC (Nested Vectored Interrupt Controller)** — Configurable 1–240 IRQ lines, 4 priority levels (min), tail-chaining (≥6 cycles), late arrival, automatic vector-table fetch
- **7 Exception Types** — Reset, NMI, HardFault, SVCall, PendSV, SysTick, IRQ[n]; fixed and configurable priorities
- **Dual Stack Pointers** — MSP (Handler + default Thread) and PSP (Thread with CONTROL.SPSEL=1)
- **SysTick Timer** — 24-bit down-counter with reload, interrupt on zero-crossing
- **Sleep Modes** — WFI (wait-for-interrupt) and WFE (wait-for-event) with EVTEXEC output
- **Debug Support** — BKPT halt, DBGRQ/DBGACK handshake, HALTED output, single-step capability
- **Core Special Registers** — APSR (N,Z,C,V flags), IPSR (exception number), EPSR (T-bit=1), PRIMASK (interrupt mask), CONTROL (SP select)
- **Reset Strategy** — Asynchronous assert (HRESETn active-low), synchronous deassert; PC initialized from vector table

### 1.4 Intended Use Context

```
┌──────────────────────────────────────────────────────────┐
│                        SoC Top                           │
│                                                          │
│  ┌────────────────┐      AHB-Lite Bus Matrix            │
│  │ cortex_m0_core │◄────────────────────────┐           │
│  │                │ (AHB Master)             │           │
│  │  IRQ[31:0] ◄──┤                         │           │
│  │  NMI ◄────────┤                         ▼           │
│  │               │              ┌──────────────────┐    │
│  │  HALTED ──►   │              │   AHB Slaves     │    │
│  │  DBGACK ──►   │              │  ┌────────────┐  │    │
│  │               │              │  │ Flash/ROM  │  │    │
│  └────────────────┘              │  ├────────────┤  │    │
│                                  │  │ SRAM       │  │    │
│                                  │  ├────────────┤  │    │
│                                  │  │ Peripherals│  │    │
│                                  │  └────────────┘  │    │
│                                  └──────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Role:** Processor core — sole AHB-Lite bus master driving all instruction fetches and data accesses.
**Integration:** Standalone IP initially; integrates into SoC as AHB-Lite master on bus matrix.
**No external dependencies:** All internal storage is FF-based; no SRAM macros, no PLL, no technology primitives.

---

## §2 — Module Hierarchy & Interface

### 2.1 Instantiation Tree

The `cortex_m0_core` is designed as a **flat, monolithic module** — all logic (pipeline, ALU, register file, NVIC, SysTick, debug) is implemented within a single SystemVerilog module for area optimization and timing closure simplicity. No sub-modules are instantiated.

```
cortex_m0_core (top)
├── Pipeline FSM (FETCH / DECODE / EXECUTE / WRITEBACK / STALL)
├── ALU (32-bit add/sub/logic/shift/mul)
├── Barrel Shifter (32-bit, 0–31 shift)
├── Instruction Decoder (Thumb-16 + Thumb-2)
├── Register File (GPRF: 17 × 32-bit, 2R / 1W)
├── Special Registers (APSR, IPSR, EPSR, PRIMASK, CONTROL)
├── NVIC (pending / enable / active / priority arrays, arbitration)
├── SysTick Timer (24-bit down-counter + reload)
├── AHB-Lite Master Interface (address phase / data phase)
├── Synchronizers (IRQ, NMI, DBGRQ — 2-stage FF)
├── Reset Synchronizer (async assert, sync deassert)
└── Debug Logic (BKPT, DBGRQ/DBGACK, HALTED, single-step)
```

**Rationale for flat design:**
- Cortex-M0 is an area-optimized core (~10–15K gates); sub-module overhead (routing, buffering) is disproportionate
- Single clock domain eliminates inter-module CDC concerns
- Simplifies timing analysis — one critical path from register read through ALU to writeback
- If future requirements demand it, sub-modules can be extracted (e.g., `cortex_m0_nvic`, `cortex_m0_alu`)

### 2.2 Parameters

| # | Parameter | Type | Default | Range | Description |
|---|-----------|------|---------|-------|-------------|
| 1 | `IRQ_NUM` | `integer` | 32 | 1–240 | Number of external IRQ input lines. Affects `IRQ` port width and NVIC array sizes. |
| 2 | `INIT_PC` | `logic [31:0]` | `32'h00000004` | Any 32-bit addr | Initial Program Counter after reset (vector table offset +4). |
| 3 | `INIT_SP` | `logic [31:0]` | `32'h00000000` | Any 32-bit addr | Initial Main Stack Pointer after reset (vector table offset +0). |

> **Note:** On actual reset, the core performs a vector table fetch: loads MSP from `vector_table[0x00]` and PC from `vector_table[0x04]`. `INIT_PC` and `INIT_SP` serve as the initial fetch addresses if vector table fetch is not yet implemented, or as fallback values.

### 2.3 Port Table — Clock & Reset

| # | Port | Width | Direction | Clock Domain | Reset | Description |
|---|------|-------|-----------|--------------|-------|-------------|
| 1 | `HCLK` | 1 | input | — (clock) | — | System clock. All logic clocked on rising edge. |
| 2 | `HRESETn` | 1 | input | async assert / HCLK deassert | — | Active-low system reset. Asynchronous assertion, synchronous deassertion. |

### 2.4 Port Table — AHB-Lite Master Interface

| # | Port | Width | Direction | Clock Domain | Default (reset) | Description |
|---|------|-------|-----------|--------------|-----------------|-------------|
| 3 | `HADDR` | 32 | output | HCLK | `32'h00000000` | Address bus. Driven during address phase. |
| 4 | `HBURST` | 3 | output | HCLK | `3'b000` (SINGLE) | Burst type. Cortex-M0 uses SINGLE for most transfers; INCR4 for PUSH/POP. |
| 5 | `HMASTLOCK` | 1 | output | HCLK | `1'b0` | Locked transfer indicator. Asserted during LDREX/STREX (if implemented). |
| 6 | `HPROT` | 4 | output | HCLK | `4'b0011` | Protection control. [0]=Data/Inst, [1]=Privileged, [2]=Bufferable, [3]=Cacheable. |
| 7 | `HSIZE` | 3 | output | HCLK | `3'b010` (WORD) | Transfer size. `000`=Byte, `001`=Halfword, `010`=Word. |
| 8 | `HTRANS` | 2 | output | HCLK | `2'b00` (IDLE) | Transfer type. `00`=IDLE, `01`=BUSY, `10`=NONSEQ, `11`=SEQ. |
| 9 | `HWDATA` | 32 | output | HCLK | `32'h00000000` | Write data bus. Valid during data phase of write transfer. |
| 10 | `HWRITE` | 1 | output | HCLK | `1'b0` | Transfer direction. `1`=Write, `0`=Read. |
| 11 | `HRDATA` | 32 | input | HCLK | — | Read data bus. Sampled when `HREADY`=1 during data phase. |
| 12 | `HREADY` | 1 | input | HCLK | — | Transfer done. `1`=Slave ready (transfer complete). `0`=Wait state. |
| 13 | `HRESP` | 1 | input | HCLK | — | Transfer response. `0`=OKAY, `1`=ERROR (triggers HardFault). |

**AHB-Lite protocol notes:**
- Address phase and data phase are pipelined: `HADDR`, `HTRANS`, `HSIZE`, `HWRITE`, `HBURST`, `HPROT`, `HMASTLOCK` are driven one cycle before the corresponding `HWDATA`/`HRDATA`.
- When `HREADY`=0, the core holds all address-phase and data-phase signals stable (STALL state).
- `HRESP`=ERROR on any transfer causes a HardFault exception.

### 2.5 Port Table — Interrupts (NVIC)

| # | Port | Width | Direction | Clock Domain | Sync | Description |
|---|------|-------|-----------|--------------|------|-------------|
| 14 | `IRQ` | `IRQ_NUM` | input | async → HCLK | 2-stage FF | External interrupt requests. Active-high, level-sensitive. Must remain asserted until serviced. |
| 15 | `NMI` | 1 | input | async → HCLK | 2-stage FF (edge detect) | Non-maskable interrupt. Active-high, rising-edge sensitive. Cannot be masked by PRIMASK. |
| 16 | `EVTEXEC` | 1 | output | HCLK | — | Event executed signal. Pulsed high for 1 cycle when WFE instruction completes (used to wake other cores). |

### 2.6 Port Table — Debug

| # | Port | Width | Direction | Clock Domain | Sync | Description |
|---|------|-------|-----------|--------------|------|-------------|
| 17 | `HALTED` | 1 | output | HCLK | — | Debug halt indicator. `1`=Core is halted (BKPT, DBGRQ, or single-step). |
| 18 | `DBGRQ` | 1 | input | async → HCLK | 2-stage FF | External debug request. When asserted, core halts at next instruction boundary. |
| 19 | `DBGACK` | 1 | output | HCLK | — | Debug acknowledge. `1`=Core has entered debug halted state. |

### 2.7 Port Summary

| Group | Inputs | Outputs | Total |
|-------|--------|---------|-------|
| Clock & Reset | 2 | 0 | 2 |
| AHB-Lite | 34 (`HRDATA`[32] + `HREADY`[1] + `HRESP`[1]) | 77 (`HADDR`[32] + `HBURST`[3] + `HMASTLOCK`[1] + `HPROT`[4] + `HSIZE`[3] + `HTRANS`[2] + `HWDATA`[32] + `HWRITE`[1]) | 111 |
| Interrupts | `IRQ_NUM` + 1 | 1 | `IRQ_NUM` + 2 |
| Debug | 1 | 2 | 3 |
| **Total** | **38 + IRQ_NUM** | **80** | **118 + IRQ_NUM** |

> For default `IRQ_NUM`=32: **150 total signals** (70 inputs, 80 outputs).

### 2.8 Cross-Reference Against Requirements

| Port | Req: interface.md | Req: cortex_m0_core_requirements.md | Match |
|------|-------------------|--------------------------------------|-------|
| HCLK | ✓ 1-bit input | ✓ | ✅ |
| HRESETn | ✓ 1-bit input, active-low | ✓ async assert, sync deassert | ✅ |
| HADDR[31:0] | ✓ 32-bit output | ✓ | ✅ |
| HBURST[2:0] | ✓ 3-bit output | ✓ | ✅ |
| HMASTLOCK | ✓ 1-bit output | ✓ | ✅ |
| HPROT[3:0] | ✓ 4-bit output | ✓ | ✅ |
| HSIZE[2:0] | ✓ 3-bit output | ✓ | ✅ |
| HTRANS[1:0] | ✓ 2-bit output | ✓ | ✅ |
| HWDATA[31:0] | ✓ 32-bit output | ✓ | ✅ |
| HWRITE | ✓ 1-bit output | ✓ | ✅ |
| HRDATA[31:0] | ✓ 32-bit input | ✓ | ✅ |
| HREADY | ✓ 1-bit input | ✓ | ✅ |
| HRESP | ✓ 1-bit input | ✓ | ✅ |
| IRQ[IRQ_NUM-1:0] | ✓ level-sensitive, active-high | ✓ | ✅ |
| NMI | ✓ edge-sensitive, active-high | ✓ | ✅ |
| EVTEXEC | ✓ 1-bit output | ✓ | ✅ |
| HALTED | ✓ 1-bit output | ✓ | ✅ |
| DBGRQ | ✓ 1-bit input | ✓ | ✅ |
| DBGACK | ✓ 1-bit output | ✓ | ✅ |
| IRQ_NUM param | ✓ default 32, range 1–240 | ✓ | ✅ |
| INIT_PC param | ✓ default 0x00000004 | ✓ | ✅ |
| INIT_SP param | ✓ default 0x00000000 | ✓ | ✅ |

**All ports and parameters match requirements — zero discrepancies.**

## §3 — Pipeline & Datapath Micro-Architecture

### 3.1 Pipeline Overview

The core implements a **3-stage, single-issue, in-order pipeline**:

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  FETCH   │────▶│  DECODE  │────▶│  EXECUTE │
│ (Stage1) │     │ (Stage2) │     │ (Stage3) │
└──────────┘     └──────────┘     └──────────┘
     ▲                                  │
     │            ┌───────────┐         │
     └────────────│ WRITEBACK │◀────────┘
                  └───────────┘
```

- **Fetch (F):** Drive `HADDR`=PC, initiate AHB-Lite read, wait for `HREADY`.
- **Decode (D):** Parse instruction word, determine class, read register operands (2R from GPRF).
- **Execute (E):** ALU operation / memory access / branch resolution. Includes writeback to register file (1W).

The pipeline is **not fully overlapped** — it uses a state-machine-based controller where only one stage is active per cycle (simplified for area). The WRITEBACK sub-phase is absorbed into EXECUTE for single-cycle ALU ops, and into a separate state for multi-cycle operations.

### 3.2 Pipeline Controller FSM

The pipeline is controlled by a single FSM. Every state transition is explicitly defined below.

#### 3.2.1 FSM States

| State | Encoding | Description |
|-------|----------|-------------|
| `RESET` | 3'b000 | Initial state after `HRESETn` assertion. Registers initialized. |
| `FETCH` | 3'b001 | Driving AHB address phase for instruction fetch from PC. |
| `DECODE` | 3'b010 | Instruction word received, parsing opcode, reading register operands. |
| `EXECUTE` | 3'b011 | ALU / memory / branch operation in progress. |
| `MEM_WAIT` | 3'b100 | Awaiting second phase of load/store (data phase, waiting for `HREADY`). |
| `STALL` | 3'b101 | AHB slave deasserted `HREADY` — pipeline frozen, retrying bus transfer. |
| `SLEEP` | 3'b110 | Core in WFI/WFE sleep mode, awaiting wake event. |
| `DEBUG_HALT` | 3'b111 | Core halted for debug (BKPT, DBGRQ, or single-step). |

#### 3.2.2 FSM Transition Table

| Current State | Condition | Next State | Actions |
|---------------|-----------|------------|---------|
| `RESET` | `HRESETn` rises (sync deassert) | `FETCH` | Load `PC` ← `INIT_PC`, `SP` ← `INIT_SP`. Drive first AHB fetch: `HADDR`=PC, `HTRANS`=NONSEQ, `HWRITE`=0, `HSIZE`=WORD. |
| `FETCH` | `HREADY`=1 | `DECODE` | Capture `HRDATA` as instruction word. Increment `PC` ← `PC` + 2 (Thumb) or +4 (Thumb-2). |
| `FETCH` | `HREADY`=0 | `STALL` | Hold all AHB outputs stable. Save `fetch_target` state = `FETCH`. |
| `FETCH` | Exception pending (priority sufficient, `PRIMASK`=0) | `EXC_ENTRY` | Abandon fetch. Begin exception entry sequence (see §5). |
| `DECODE` | Instruction decoded as single-cycle ALU/shift/cmp/move | `EXECUTE` | Read operands from GPRF (2R). Set ALU operation. |
| `DECODE` | Instruction decoded as load/store | `EXECUTE` | Read operands. Calculate memory address (base + offset). |
| `DECODE` | Instruction decoded as branch (taken) | `EXECUTE` | Read operands. Calculate branch target. |
| `DECODE` | Instruction decoded as branch (not-taken) | `FETCH` | No action. Fetch next sequential instruction. |
| `DECODE` | Instruction decoded as WFI/WFE | `SLEEP` | Enter sleep. Set internal `sleep_mode` flag. |
| `DECODE` | Instruction decoded as BKPT | `DEBUG_HALT` | Set `HALTED`=1, `DBGACK`=1. Freeze pipeline. |
| `DECODE` | Instruction decoded as MRS/MSR | `EXECUTE` | Read/write special register. |
| `DECODE` | Instruction decoded as CPSIE/CPSID | `EXECUTE` | Modify `PRIMASK`.PM bit. |
| `DECODE` | Undefined instruction | `EXECUTE` | Generate HardFault (set `hf_cause`=UNDEF_INSTR). |
| `EXECUTE` | ALU result ready, writeback complete | `FETCH` | Write result to GPRF. Update APSR flags (N,Z,C,V). Drive next AHB fetch. |
| `EXECUTE` | Load/store — address phase driven, awaiting data phase | `MEM_WAIT` | Drive `HADDR`=calculated address, `HTRANS`=NONSEQ, `HWRITE`/`HSIZE` per instruction. |
| `EXECUTE` | Branch taken — target resolved | `FETCH` | Update `PC` ← branch_target. Flush pipeline. Drive new AHB fetch. |
| `EXECUTE` | MUL (iterative) — not complete | `EXECUTE` | Continue shift-add iteration. Stall pipeline internally. Counter decrement. |
| `EXECUTE` | MUL (iterative) — complete | `FETCH` | Write result to GPRF. Update N,Z flags. |
| `EXECUTE` | Exception detected during execute | `EXC_ENTRY` | Abandon current instruction. Begin exception entry (see §5). |
| `MEM_WAIT` | `HREADY`=1, `HWRITE`=1 (store complete) | `FETCH` | Write data sent. Resume pipeline — drive next fetch. |
| `MEM_WAIT` | `HREADY`=1, `HWRITE`=0 (load complete) | `FETCH` | Capture `HRDATA`. Write to GPRF. Resume pipeline. |
| `MEM_WAIT` | `HREADY`=1, `HRESP`=ERROR | `EXC_ENTRY` | HardFault due to bus error. `hf_cause`=BUS_FAULT. |
| `MEM_WAIT` | `HREADY`=0 | `STALL` | Hold all AHB outputs stable. Save `fetch_target` state = `MEM_WAIT`. |
| `STALL` | `HREADY` rises to 1 | Return to `fetch_target` | Resume the state that was stalled (`FETCH`, `MEM_WAIT`, or `EXC_STACKING`). |
| `STALL` | `HREADY`=0 (still stalled) | `STALL` | Continue holding. No state change. |
| `SLEEP` | Pending IRQ with sufficient priority AND `PRIMASK`=0 | `EXC_ENTRY` | Wake from sleep. Begin exception entry. |
| `SLEEP` | Pending NMI | `EXC_ENTRY` | Wake from sleep. Begin exception entry. |
| `SLEEP` | `DBGRQ` synchronized = 1 | `DEBUG_HALT` | Wake from sleep. Enter debug halt. |
| `SLEEP` | WFE: `EVTEXEC` event received | `FETCH` | Wake from WFE. Resume execution from current PC. |
| `DEBUG_HALT` | Debug resume command | `FETCH` | Clear `HALTED`=0, `DBGACK`=0. Resume from current PC. |
| `DEBUG_HALT` | Single-step mode, resume | `EXECUTE` | Execute one instruction, then return to `DEBUG_HALT`. |

#### 3.2.3 Exception FSM Overlay

Exception handling uses an overlay on the main FSM, adding sub-states:

| Sub-State | Description |
|-----------|-------------|
| `EXC_ENTRY` | Begin exception processing: determine highest-priority pending exception. |
| `EXC_STACKING` | Push {R0, R1, R2, R3, R12, LR, PC, xPSR} to active SP (8 words, each an AHB write). |
| `EXC_VECTOR_FETCH` | Fetch handler address from vector_table[exception_number × 4]. |
| `EXC_HANDLER` | Handler executing (normal pipeline states, `IPSR` ≠ 0). |
| `EXC_RETURN` | BX/POP with EXC_RETURN value detected. Unstack {R0–R3, R12, LR, PC, xPSR}. |

> Full exception FSM details are in §5.

#### 3.2.4 Undefined State Handling

- The FSM uses `default` case in RTL to transition to `RESET` on any undefined encoding.
- All states have explicit transitions for all conditions — no dangling states.
- `HRESETn` assertion at any state → immediate transition to `RESET` (asynchronous).

### 3.3 Back-Pressure & Stall Logic

```
                  HREADY (from slave)
                       │
                       ▼
              ┌────────────────┐
              │  Stall Control │─────── Freeze all pipeline registers
              │  (HREADY gate) │─────── Hold HADDR, HTRANS, HWDATA stable
              └────────────────┘─────── Prevent PC increment
```

**Stall rules:**
1. `HREADY`=0 during `FETCH` or `MEM_WAIT` → enter `STALL`, freeze entire pipeline
2. During `STALL`: all registered outputs (`HADDR`, `HTRANS`, `HSIZE`, `HWRITE`, `HWDATA`) held stable
3. Internal state (`PC`, register file writes, ALU results) frozen — no state changes
4. On `HREADY` rising edge → resume from saved `fetch_target` state
5. Exception detection is suppressed during `STALL` — exceptions are only evaluated between instructions

### 3.4 Data Path Blocks

#### 3.4.1 Instruction Fetch Datapath

```
PC ──▶ [HADDR mux] ──▶ HADDR (output)
                  │
                  ▼
           HRDATA ◀── AHB Bus
                  │
                  ▼
         instruction_reg ──▶ Decoder
```

- **PC sources:** Sequential (PC + 2/4), Branch target, Exception vector, Unstacked PC
- **Mux select:** FSM state + instruction type
- **PC increment:** +2 for 16-bit Thumb, +4 for 32-bit Thumb-2 (determined after decode)

#### 3.4.2 Decode Datapath

```
instruction_reg ──▶ [Decoder] ──▶ opcode_class
                               ──▶ alu_op
                               ──▶ reg_sel_r1, reg_sel_r2
                               ──▶ reg_sel_w
                               ──▶ imm_val (sign-extended)
                               ──▶ branch_target (PC + offset)
                               ──▶ mem_addr (base + offset)
```

- **Instruction classes:** ALU, SHIFT, COMPARE, MOVE, MUL, LOAD, STORE, LOAD_MULT, STORE_MULT, BRANCH, BRANCH_LINK, SYSTEM (MRS/MSR/CPS), SLEEP, DEBUG
- **Register read:** 2 ports, combinational from GPRF (0-cycle latency)
- **Immediate extraction:** Sign/zero extension per instruction format

#### 3.4.3 Execute Datapath

```
operand_a ◀── GPRF port 1 (Rn)
operand_b ◀── GPRF port 2 (Rm) OR imm_val
     │              │
     ▼              ▼
  ┌──────────────────────┐
  │         ALU          │──▶ alu_result
  │  ADD/SUB/AND/ORR/    │──▶ flags (N,Z,C,V)
  │  EOR/BIC/LSL/LSR/    │
  │  ASR/MUL             │
  └──────────────────────┘
     │
     ├──▶ GPRF write (port W) ──▶ Rd
     ├──▶ Mem addr (for load/store)
     ├──▶ Branch target ──▶ PC mux
     └──▶ Flags ──▶ APSR[N,Z,C,V]
```

- **ALU operations:** ADD, SUB, RSB, AND, ORR, EOR, BIC, LSL, LSR, ASR, MUL
- **Flag generation:** All ALU ops update N,Z; ADD/SUB also update C,V
- **Result mux:** ALU result, load data, branch target, or immediate

### 3.5 Feature Operation Summary

For each major feature, the trigger → datapath → control → output flow:

#### F1: Instruction Fetch & Execute

| Aspect | Detail |
|--------|--------|
| **Trigger** | Core not in SLEEP, DEBUG_HALT, or RESET |
| **Datapath** | PC → HADDR → AHB → HRDATA → instruction_reg → Decoder → ALU → GPRF write |
| **Control** | FSM cycles through FETCH → DECODE → EXECUTE → FETCH |
| **Output** | Register file updated, memory accessed (for loads/stores), PC advanced |

#### F2: ARMv6-M Instruction Execution

| Aspect | Detail |
|--------|--------|
| **Trigger** | instruction_reg loaded in FETCH state |
| **Datapath** | Decoder classifies into 13 instruction classes; routes to appropriate datapath (ALU / memory / branch / system) |
| **Control** | FSM state determines which execution path is active |
| **Output** | Varies by class: ALU result → GPRF, memory address → HADDR, branch target → PC |

#### F3: Register File Operations

| Aspect | Detail |
|--------|--------|
| **Trigger** | Decode stage reads operands; Execute stage writes result |
| **Datapath** | 2R ports (combinational) → operand_a, operand_b; 1W port → Rd |
| **Control** | R13 banking: MSP or PSP selected by `CONTROL.SPSEL` and handler/thread mode |
| **Output** | Operands to ALU, result from ALU/load to register |

#### F6: Dual Stack Pointer

| Aspect | Detail |
|--------|--------|
| **Trigger** | Any instruction accessing R13 (SP), or exception entry/exit |
| **Datapath** | MSP and PSP are separate physical registers; mux selects active SP |
| **Control** | Handler mode → always MSP. Thread mode → MSP if `CONTROL.SPSEL`=0, PSP if 1 |
| **Output** | Selected SP value to operand path or address calculation |

#### F7: SysTick Timer

| Aspect | Detail |
|--------|--------|
| **Trigger** | Every HCLK rising edge when `SYST_CSR.ENABLE`=1 |
| **Datapath** | 24-bit down-counter: `CVR` ← `CVR` - 1 each tick; on zero → reload from `RVR` |
| **Control** | On zero-crossing: set SysTick pending bit in NVIC; if `TICKINT`=1 and not masked → exception |
| **Output** | SysTick pending bit → NVIC arbitration → potential exception entry |

#### F8: Sleep Modes (WFI/WFE)

| Aspect | Detail |
|--------|--------|
| **Trigger** | WFI or WFE instruction decoded |
| **Datapath** | No data movement — core freezes |
| **Control** | FSM enters `SLEEP`. WFI: wake on pending IRQ/NMI with sufficient priority. WFE: wake on IRQ/NMI or `EVTEXEC` event |
| **Output** | Core stalls. On wake: `SLEEP` → `EXC_ENTRY` (interrupt) or `FETCH` (event) |

#### F9: Debug Support

| Aspect | Detail |
|--------|--------|
| **Trigger** | BKPT instruction decoded, or `DBGRQ` pin asserted, or single-step |
| **Datapath** | No data movement — pipeline frozen |
| **Control** | FSM enters `DEBUG_HALT`. `HALTED`=1, `DBGACK`=1. Resume command → `FETCH` |
| **Output** | `HALTED`, `DBGACK` driven high. Single-step: execute one instruction, return to `DEBUG_HALT` |

## §4 — ALU & Instruction Decoder

### 4.1 ALU Architecture

#### 4.1.1 Supported Operations

| ALU Op Code | Operation | Operands | Result | Flags Updated | Cycles |
|-------------|-----------|----------|--------|---------------|--------|
| `ALU_ADD` | Add | A + B | Sum[31:0] | N, Z, C, V | 1 |
| `ALU_ADC` | Add with Carry | A + B + C_in | Sum[31:0] | N, Z, C, V | 1 |
| `ALU_SUB` | Subtract | A - B | Diff[31:0] | N, Z, C, V | 1 |
| `ALU_SBC` | Subtract with Carry | A - B - ~C_in | Diff[31:0] | N, Z, C, V | 1 |
| `ALU_RSB` | Reverse Subtract | B - A | Diff[31:0] | N, Z, C, V | 1 |
| `ALU_AND` | Bitwise AND | A & B | And[31:0] | N, Z | 1 |
| `ALU_ORR` | Bitwise OR | A \| B | Or[31:0] | N, Z | 1 |
| `ALU_EOR` | Bitwise XOR | A ^ B | Xor[31:0] | N, Z | 1 |
| `ALU_BIC` | Bit Clear | A & ~B | Bic[31:0] | N, Z | 1 |
| `ALU_LSL` | Logical Shift Left | A << B[4:0] | Shifted[31:0] | N, Z, C | 1 |
| `ALU_LSR` | Logical Shift Right | A >> B[4:0] | Shifted[31:0] | N, Z, C | 1 |
| `ALU_ASR` | Arithmetic Shift Right | A >>> B[4:0] | Shifted[31:0] | N, Z, C | 1 |
| `ALU_MUL` | Multiply | A × B | Prod[31:0] | N, Z | 1 or 32 |
| `ALU_MOV` | Move | B | B[31:0] | N, Z | 1 |
| `ALU_MVN` | Move NOT | ~B | Not[31:0] | N, Z | 1 |
| `ALU_NOP` | No Operation | — | — | — | 1 |
| `ALU_CMP` | Compare (SUB, discard) | A - B | — | N, Z, C, V | 1 |
| `ALU_CMN` | Compare Neg (ADD, discard) | A + B | — | N, Z, C, V | 1 |
| `ALU_TST` | Test (AND, discard) | A & B | — | N, Z | 1 |

> **Note:** CMP/CMN/TST perform ALU operations but do NOT write result to register file — only update APSR flags.

#### 4.1.2 Flag Generation Logic

| Flag | Formula | Applies To |
|------|---------|------------|
| **N** (Negative) | `result[31]` | All ALU ops |
| **Z** (Zero) | `result == 32'b0` | All ALU ops |
| **C** (Carry) | ADD: `~(A[31] XOR B[31]) & (result[31] XOR A[31])` — i.e., carry out of bit 31. SUB: `A >= B` (no borrow). Shift: last bit shifted out. | ADD, ADC, SUB, SBC, RSB, CMN, CMP, LSL, LSR, ASR |
| **V** (Overflow) | `(A[31] XOR B[31]) & (result[31] XOR A[31])` for ADD; `(A[31] XOR ~B[31]) & (result[31] XOR A[31])` for SUB | ADD, ADC, SUB, SBC, RSB, CMP, CMN |

#### 4.1.3 Multiplier Implementation Choice

| Option | Cycles | Area | Decision |
|--------|--------|------|----------|
| Single-cycle (hardware) | 1 | ~800 gates | **Default** for initial implementation |
| Iterative (shift-add) | 1–32 | ~200 gates | Fallback if timing not met at 50 MHz |

> At 50 MHz (20 ns period), a 32×32→32 combinational multiply easily meets timing on FPGA and 180nm ASIC.

### 4.2 Instruction Decoder

#### 4.2.1 Instruction Class Encoding

The decoder classifies each 16-bit or 32-bit instruction into an instruction class:

| Class ID | Class Name | ALU Op | Has Mem | Has Branch | Writes Reg |
|----------|-----------|--------|---------|------------|------------|
| `CLS_ALU` | ALU arithmetic/logic | From opcode | No | No | Yes (Rd) |
| `CLS_SHIFT` | Shift operations | LSL/LSR/ASR | No | No | Yes (Rd) |
| `CLS_CMP` | Compare / Test | CMP/CMN/TST | No | No | No (flags only) |
| `CLS_MOVE` | Move / Move NOT | MOV/MVN | No | No | Yes (Rd) |
| `CLS_MUL` | Multiply | MUL | No | No | Yes (Rd, N,Z) |
| `CLS_LOAD` | Load single | — | Yes (read) | No | Yes (Rt) |
| `CLS_STORE` | Store single | — | Yes (write) | No | No |
| `CLS_LOADM` | Load multiple (LDM, POP) | — | Yes (read×N) | No | Yes (multiple) |
| `CLS_STOREM` | Store multiple (STM, PUSH) | — | Yes (write×N) | No | No |
| `CLS_BRANCH` | Conditional / Unconditional | — | No | Yes | No |
| `CLS_BL` | Branch with Link | — | No | Yes | Yes (LR) |
| `CLS_BX` | Branch Exchange | — | No | Yes | No |
| `CLS_SYSTEM` | MRS / MSR / CPS / SVC | — | No | No | Varies |

#### 4.2.2 Thumb-16 Instruction Decode Map

| Bits [15:10] | Bits [9:0] | Instruction | Class | Destination |
|-------------|-----------|-------------|-------|-------------|
| `000000` | `offs5,Rm,Rd` | LSL (immediate) | `CLS_SHIFT` | Rd |
| `000001` | `offs5,Rm,Rd` | LSR (immediate) | `CLS_SHIFT` | Rd |
| `000010` | `offs5,Rm,Rd` | ASR (immediate) | `CLS_SHIFT` | Rd |
| `000011 0` | `Rn,Rm,Rd` | ADD (register) | `CLS_ALU` | Rd |
| `000011 1` | `Rn,Rm,Rd` | SUB (register) | `CLS_ALU` | Rd |
| `000100 0` | `imm3,Rn,Rd` | ADD (imm, 3-bit) | `CLS_ALU` | Rd |
| `000100 1` | `imm3,Rn,Rd` | SUB (imm, 3-bit) | `CLS_ALU` | Rd |
| `000101 0` | `imm8,Rd` | MOV (imm, 8-bit) | `CLS_MOVE` | Rd |
| `000101 1` | `imm8,Rd` | CMP (imm, 8-bit) | `CLS_CMP` | — |
| `000110 0` | `imm8,Rd` | ADD (imm, 8-bit) | `CLS_ALU` | Rd |
| `000110 1` | `imm8,Rd` | SUB (imm, 8-bit) | `CLS_ALU` | Rd |
| `00100` | `Rd,imm8` (shifted) | MOV (imm, wide) | `CLS_MOVE` | Rd |
| `00101` | `Rd,imm8` (shifted) | CMP (imm, wide) | `CLS_CMP` | — |
| `00110` | `Rd,imm8` (shifted) | ADD (imm, wide) | `CLS_ALU` | Rd |
| `00111` | `Rd,imm8` (shifted) | SUB (imm, wide) | `CLS_ALU` | Rd |
| `010000` | `opcode,Rm,Rd` | ALU (data processing) | Various | Varies |
| `010000 0000` | — | AND | `CLS_ALU` | Rd |
| `010000 0001` | — | EOR | `CLS_ALU` | Rd |
| `010000 0010` | — | MOV (shift, reg) | `CLS_SHIFT` | Rd |
| `010000 0011` | — | BX | `CLS_BX` | — |
| `010000 0100` | — | MVN | `CLS_MOVE` | Rd |
| `010000 0110` | — | MUL | `CLS_MUL` | Rd |
| `010000 1000` | — | CMP (register hi) | `CLS_CMP` | — |
| `010000 1001` | — | RSB | `CLS_ALU` | Rd |
| `010000 1010` | — | CMP (register lo) | `CLS_CMP` | — |
| `010000 1011` | — | CMN | `CLS_CMP` | — |
| `010000 1100` | — | ORR | `CLS_ALU` | Rd |
| `010000 1101` | — | MUL (variant) | `CLS_MUL` | Rd |
| `010000 1110` | — | BIC | `CLS_ALU` | Rd |
| `010000 1111` | — | MVN (variant) | `CLS_MOVE` | Rd |
| `010001` | `Rd,Rm` | ADD (register hi) | `CLS_ALU` | Rd |
| `010001 10` | `Rd,Rm` | CMP (register hi) | `CLS_CMP` | — |
| `010001 11` | `Rd,Rm` | MOV (register hi) | `CLS_MOVE` | Rd |
| `01001` | `Rt,imm8` (PC-relative) | LDR (literal) | `CLS_LOAD` | Rt |
| `01010` | `Rt,Rn,imm5` | STR (word, imm) | `CLS_STORE` | — |
| `01011` | `Rt,Rn,imm5` | LDR (word, imm) | `CLS_LOAD` | Rt |
| `01100` | `Rt,Rn,imm5` | STRB (byte, imm) | `CLS_STORE` | — |
| `01101` | `Rt,Rn,imm5` | LDRB (byte, imm) | `CLS_LOAD` | Rt |
| `01110` | `Rt,Rn,imm5` | STRH (halfword, imm) | `CLS_STORE` | — |
| `01111` | `Rt,Rn,imm5` | LDRH (halfword, imm) | `CLS_LOAD` | Rt |
| `10000` | `Rt,Rn,Rm` | STRB (byte, reg) | `CLS_STORE` | — |
| `10001` | `Rt,Rn,Rm` | LDRB (byte, reg) | `CLS_LOAD` | Rt |
| `10010` | `Rt,Rn,Rm` | STRH (halfword, reg) | `CLS_STORE` | — |
| `10011` | `Rt,Rn,Rm` | LDRH (halfword, reg) | `CLS_LOAD` | Rt |
| `10100` | `Rt,Rn,imm5` | STR (SP-relative) | `CLS_STORE` | — |
| `10101` | `Rt,Rn,imm5` | LDR (SP-relative) | `CLS_LOAD` | Rt |
| `10110 0` | `imm8` | ADD Rd=SP,imm | `CLS_ALU` | SP |
| `10110 1` | `imm8` | SUB Rd=SP,imm | `CLS_ALU` | SP |
| `10111` | `imm8` | ADD SP,imm (SP-relative) | `CLS_ALU` | SP |
| `11000` | `register_list` | STM (store multiple) | `CLS_STOREM` | — |
| `11001` | `register_list` | LDM (load multiple) | `CLS_LOADM` | Multiple |
| `1011 0100` | `register_list` | PUSH | `CLS_STOREM` | — |
| `1011 1100` | `register_list` | POP | `CLS_LOADM` | Multiple |
| `1101 0` | `cond,imm8` | B (conditional) | `CLS_BRANCH` | — |
| `11100` | `imm11` | B (unconditional) | `CLS_BRANCH` | — |
| `1011 1110` | — | BKPT | `CLS_SYSTEM` | — |
| `1011 1111` | — | NOP / hint | `CLS_SYSTEM` | — |
| `1101 1111` | — | SVC | `CLS_SYSTEM` | — |
| `1011 0011` | — | CPS (CPSIE/CPSID) | `CLS_SYSTEM` | — |
| `1011 1000` | — | WFI | `CLS_SYSTEM` | — |
| `1011 1001` | — | WFE | `CLS_SYSTEM` | — |

#### 4.2.3 Thumb-2 (32-bit) Instruction Decode Map

| Bits [31:16] | Bits [15:0] | Instruction | Class |
|-------------|-------------|-------------|-------|
| `11110 S imm10` | `11 J1 1 imm11 J2` | BL (long branch with link) | `CLS_BL` |
| `11110 0100 11` | `(sysm,Rd)` | MRS (read special register) | `CLS_SYSTEM` |
| `11110 0100 10` | `(sysm,Rn)` | MSR (write special register) | `CLS_SYSTEM` |
| `11110 0000 00` | — | DMB (data memory barrier) | `CLS_SYSTEM` |
| `11110 0000 01` | — | DSB (data sync barrier) | `CLS_SYSTEM` |
| `11110 0000 10` | — | ISB (instruction sync barrier) | `CLS_SYSTEM` |

> **Excluded from initial implementation:** IT (If-Then) blocks, unprivileged instructions, LDREX/STREX.

#### 4.2.4 Decoder Output Signals

| Signal | Width | Description |
|--------|-------|-------------|
| `decoded_class` | 4 | Instruction class (`CLS_ALU`..`CLS_SYSTEM`) |
| `decoded_alu_op` | 5 | ALU operation select (`ALU_ADD`..`ALU_TST`) |
| `decoded_rd_sel` | 4 | Destination register index (R0–R15) |
| `decoded_rn_sel` | 4 | Source register 1 index |
| `decoded_rm_sel` | 4 | Source register 2 index |
| `decoded_imm` | 32 | Sign/zero-extended immediate value |
| `decoded_shift_amt` | 5 | Shift amount (0–31) |
| `decoded_mem_size` | 2 | Transfer size: 00=byte, 01=halfword, 10=word |
| `decoded_mem_sign` | 1 | Sign-extend for byte/halfword loads |
| `decoded_write_en` | 1 | Register file write enable |
| `decoded_flag_en` | 1 | APSR flag update enable |
| `decoded_branch_en` | 1 | Branch taken flag |
| `decoded_branch_cond` | 4 | Condition code (EQ/NE/CS/CC/MI/PL/VS/VC/HI/LS/GE/LT/GT/LE) |
| `decoded_is_32bit` | 1 | 1=Thumb-2 (32-bit), 0=Thumb-16 (16-bit) |

#### 4.2.5 Condition Code Evaluation

| Code | Suffix | Flags Test | Meaning |
|------|--------|-----------|---------|
| `0000` | EQ | Z=1 | Equal |
| `0001` | NE | Z=0 | Not equal |
| `0010` | CS/HS | C=1 | Carry set / unsigned higher or same |
| `0011` | CC/LO | C=0 | Carry clear / unsigned lower |
| `0100` | MI | N=1 | Minus / negative |
| `0101` | PL | N=0 | Plus / positive or zero |
| `0110` | VS | V=1 | Overflow |
| `0111` | VC | V=0 | No overflow |
| `1000` | HI | C=1 AND Z=0 | Unsigned higher |
| `1001` | LS | C=0 OR Z=1 | Unsigned lower or same |
| `1010` | GE | N=V | Signed greater than or equal |
| `1011` | LT | N≠V | Signed less than |
| `1100` | GT | Z=0 AND N=V | Signed greater than |
| `1101` | LE | Z=1 OR N≠V | Signed less than or equal |
| `1110` | AL | — | Always (unconditional) |

> Condition evaluated as: `cond_result = f(APSR_N, APSR_Z, APSR_C, APSR_V)` — combinational logic, 1 gate level.

### 4.3 Internal Register Map (CPU Registers)

> **Note:** These are internal CPU registers accessed via MRS/MSR instructions — NOT memory-mapped.
> There is no APB/AXI-Lite register slave interface. The core is an AHB-Lite bus master only.

#### 4.3.1 General-Purpose Register File (GPRF)

| Index | Name | Width | Access | Reset | Description |
|-------|------|-------|--------|-------|-------------|
| 0 | R0 | 32 | RW | `32'h00000000` | Argument / result |
| 1 | R1 | 32 | RW | `32'h00000000` | General purpose |
| 2 | R2 | 32 | RW | `32'h00000000` | General purpose |
| 3 | R3 | 32 | RW | `32'h00000000` | Argument |
| 4 | R4 | 32 | RW | `32'h00000000` | Callee-saved |
| 5 | R5 | 32 | RW | `32'h00000000` | Callee-saved |
| 6 | R6 | 32 | RW | `32'h00000000` | Callee-saved |
| 7 | R7 | 32 | RW | `32'h00000000` | Callee-saved |
| 8 | R8 | 32 | RW | `32'h00000000` | Callee-saved |
| 9 | R9 | 32 | RW | `32'h00000000` | Callee-saved |
| 10 | R10 | 32 | RW | `32'h00000000` | Callee-saved |
| 11 | R11 | 32 | RW | `32'h00000000` | Callee-saved |
| 12 | R12 (IP) | 32 | RW | `32'h00000000` | Caller-saved scratch |
| 13 | SP (R13) | 32 | RW | See MSP/PSP below | Stack pointer (banked) |
| 14 | LR (R14) | 32 | RW | `32'hFFFFFFFF` | Link register / EXC_RETURN |
| 15 | PC (R15) | 32 | RO* | `INIT_PC` param | Program counter (*written by branch/exception logic only) |

**Banked SP (R13):**

| Physical Register | Condition Active | Access |
|-------------------|-----------------|--------|
| MSP | Handler mode OR (Thread mode AND `CONTROL.SPSEL`=0) | RW via MRS/MSR or SP instructions |
| PSP | Thread mode AND `CONTROL.SPSEL`=1 | RW via MRS/MSR or SP instructions |

#### 4.3.2 Special-Purpose Registers (SPR)

| # | Register | MRS/MSR Name | Width | Access | Reset | `sysm` Code |
|---|----------|-------------|-------|--------|-------|-------------|
| 1 | APSR | `0'b APRS` | 32 | RW (partial) | `32'h00000000` | `5'b00000` |
| 2 | IPSR | `IPSR` | 32 | RO | `32'h00000000` | `5'b00001` |
| 3 | EPSR | `EPSR` | 32 | RO | `32'h01000000` | `5'b00010` |
| 4 | PRIMASK | `PRIMASK` | 32 | RW | `32'h00000000` | `5'b10000` |
| 5 | CONTROL | `CONTROL` | 32 | RW | `32'h00000000` | `5'b10010` |
| 6 | MSP | `MSP` | 32 | RW | `INIT_SP` param | `5'b10001` |
| 7 | PSP | `PSP` | 32 | RW | `32'h00000000` | `5'b10010` |

#### 4.3.3 APSR Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [31] | N | RW | 0 | Negative flag — set to result[31] of last flagged ALU op |
| [30] | Z | RW | 0 | Zero flag — set if result == 0 |
| [29] | C | RW | 0 | Carry flag — set if carry out of bit 31 (ADD) or no borrow (SUB) |
| [28] | V | RW | 0 | Overflow flag — set if signed overflow |
| [27:0] | RSVD | RO | 0 | Reserved — reads as zero, writes ignored |

#### 4.3.4 IPSR Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [8:0] | ISR_NUMBER | RO | 0 | Exception number: 0=Thread, 2=NMI, 3=HardFault, 11=SVCall, 14=PendSV, 15=SysTick, 16+=IRQ[n] |
| [31:9] | RSVD | RO | 0 | Reserved — reads as zero |

#### 4.3.5 EPSR Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [24] | T | RO | 1 | Thumb bit — always 1 in ARMv6-M. Writes ignored. |
| [31:25] | RSVD | RO | 0 | Reserved — reads as zero |
| [23:0] | RSVD | RO | 0 | Reserved — reads as zero |

#### 4.3.6 PRIMASK Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [0] | PM | RW | 0 | Priority mask: 0=interrupts enabled, 1=all IRQs masked (except NMI/HardFault) |
| [31:1] | RSVD | RO | 0 | Reserved — reads as zero, writes ignored |

> Modified by: `CPSIE I` → PM=0; `CPSID I` → PM=1; `MSR PRIMASK` → direct write.

#### 4.3.7 CONTROL Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [0] | SPSEL | RW | 0 | Stack pointer select (Thread mode only): 0=MSP, 1=PSP. Handler mode always uses MSP. |
| [1] | RSVD | RO | 0 | Reserved |
| [31:2] | RSVD | RO | 0 | Reserved — reads as zero, writes ignored |

#### 4.3.8 MSP / PSP Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [31:2] | SP_VAL | RW | INIT_SP / 0 | Stack pointer value (word-aligned) |
| [1:0] | RSVD | — | 0 | Forced to zero on write — SP always word-aligned |

#### 4.3.9 EXC_RETURN Values (loaded into LR on exception entry)

| Value | Name | Return Mode | SP |
|-------|------|-------------|-----|
| `0xFFFFFFF1` | `EXC_RET_HANDLER_MSP` | Handler mode | MSP |
| `0xFFFFFFF9` | `EXC_RET_THREAD_MSP` | Thread mode | MSP |
| `0xFFFFFFFD` | `EXC_RET_THREAD_PSP` | Thread mode | PSP |

> Detection: `LR[31:4] == 28'hFFFFFFF` → exception return sequence triggered by BX LR or POP {PC}.

### 4.4 Internal Storage Summary

| Structure | Entries | Width | Total Bits | Reset |
|-----------|---------|-------|------------|-------|
| GPRF (R0–R12) | 13 | 32 | 416 | All zeros |
| MSP | 1 | 32 | 32 | INIT_SP |
| PSP | 1 | 32 | 32 | Zero |
| LR | 1 | 32 | 32 | 0xFFFFFFFF |
| PC | 1 | 32 | 32 | INIT_PC |
| APSR | 1 | 32 | 32 | Zero |
| IPSR | 1 | 32 | 32 | Zero |
| EPSR | 1 | 32 | 32 | 0x01000000 |
| PRIMASK | 1 | 32 | 32 | Zero |
| CONTROL | 1 | 32 | 32 | Zero |
| NVIC pending | IRQ_NUM | 1 | IRQ_NUM | Zero |
| NVIC enable | IRQ_NUM | 1 | IRQ_NUM | Zero |
| NVIC active | IRQ_NUM | 1 | IRQ_NUM | Zero |
| NVIC priority | IRQ_NUM | N | IRQ_NUM × N | Zero |
| SysTick CSR | 1 | 32 | 32 | Zero |
| SysTick RVR | 1 | 24 | 24 | Zero |
| SysTick CVR | 1 | 24 | 24 | Zero |
| **Total (default)** | — | — | **~912** | — |

> For `IRQ_NUM`=32, `N`=2 (priority bits): NVIC arrays = 32+32+32+64 = 160 bits.

## §5 — NVIC & Exception Handling

### 5.1 Overview

The `cortex_m0_core` **receives and processes** inbound interrupt requests via its NVIC. It does **not generate** outbound interrupts to other IPs. The NVIC provides:

- Configurable external IRQ inputs (1–240 lines, level-sensitive, active-high)
- Non-maskable interrupt (NMI, edge-sensitive, active-high)
- 5 internal exception sources (Reset, HardFault, SVCall, PendSV, SysTick)
- Priority-based preemption with tail-chaining and late-arrival optimization

### 5.2 Exception Source Table

| Exception # | Source | Type | Trigger | Polarity | Priority (fixed) | Maskable | Clear Mechanism |
|-------------|--------|------|---------|----------|-------------------|----------|-----------------|
| 1 | Reset | External | `HRESETn` rising (sync deassert) | Active-low | -3 (highest) | No | Auto — loads vector table |
| 2 | NMI | External (pin) | Rising edge on `NMI` input | Active-high | -2 | No | Auto-clear on exception return |
| 3 | HardFault | Internal | Undefined instruction / AHB error / stacking fault | — | -1 | No | Auto-clear on exception return |
| 11 | SVCall | Software | `SVC` instruction execution | — | Configurable (min 0) | Yes (PRIMASK) | Auto-clear on exception return |
| 14 | PendSV | Software | Pended via `SCB_ICSR.PENDSVSET` bit (AHB write to SCS) | — | Configurable (min 0) | Yes (PRIMASK) | W1C via `SCB_ICSR.PENDSVCLR` |
| 15 | SysTick | Internal | 24-bit down-counter reaches zero | — | Configurable (min 0) | Yes (PRIMASK) | Auto-clear (reads `SYST_CVR`) or W1C |
| 16+n | IRQ[n] | External (pin) | `IRQ[n]` asserted, level-high | Active-high | Configurable (min 0) | Yes (PRIMASK) | Auto-clear on exception entry (level must drop) |

> **Note:** IRQ pins are level-sensitive — the IRQ line must remain asserted until the ISR services it. If the line deasserts before ISR entry, the pending bit may clear automatically.

### 5.3 NVIC Internal Registers

> These are memory-mapped in the System Control Space (SCS) at `0xE000E000+`. Accessed via normal AHB load/store by the core.

#### 5.3.1 NVIC Register Array Summary

| Array | Width | Entries | Access | Reset | Purpose |
|-------|-------|---------|--------|-------|---------|
| `nvic_pending[IRQ_NUM-1:0]` | 1 bit per IRQ | IRQ_NUM | RW (W1C to clear) | All 0 | Pending state for each IRQ |
| `nvic_enable[IRQ_NUM-1:0]` | 1 bit per IRQ | IRQ_NUM | RW | All 0 | Enable mask — only enabled IRQs can become pending |
| `nvic_active[IRQ_NUM-1:0]` | 1 bit per IRQ | IRQ_NUM | Auto | All 0 | Active state — set on exception entry, cleared on return |
| `nvic_priority[IRQ_NUM-1:0]` | N bits per IRQ (min 2) | IRQ_NUM | RW | All 0 | Priority level — lower value = higher priority |

#### 5.3.2 NVIC Priority Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| Priority bits per IRQ | N (implementation-defined, min 2, max 8) | N=2 → 4 levels; N=8 → 256 levels |
| Default | N=2 (4 priority levels: 0, 64, 128, 192) | Area-optimized minimum |
| Priority ordering | Lower numerical value = higher priority | 0 is highest configurable priority |
| Priority registers | `NVIC_IPR0`–`NVIC_IPR60` at `0xE000E400+` | 4 priorities per 32-bit register |

### 5.4 Interrupt Input Synchronization

All asynchronous inputs pass through a **2-stage flip-flop synchronizer**:

```
async_input ──▶ [FF1] ──▶ [FF2] ──▶ synchronized_output
                HCLK      HCLK
```

| Input | Synchronizer Type | Additional Logic | Latency |
|-------|-------------------|------------------|---------|
| `IRQ[IRQ_NUM-1:0]` | 2-stage FF | Level detect (value sampling) | 2 cycles |
| `NMI` | 2-stage FF | Edge detect (rising edge = FF2 & ~FF2_delayed) | 2 cycles |
| `DBGRQ` | 2-stage FF | Level detect | 2 cycles |

**NMI edge detection:**
```verilog
nmi_sync     <= nmi_ff2;
nmi_edge     <= nmi_ff2 & ~nmi_sync_delayed;  // rising edge pulse
```

### 5.5 Interrupt Masking Logic

```
                    ┌──────────────────┐
                    │    PRIMASK.PM    │
                    └────────┬─────────┘
                             │
               ┌─────────────▼──────────────┐
               │  Mask Gate (AND condition) │
               │  interrupt_allowed =       │
               │    (exception_num ≥ 16)    │
               │    AND (!PRIMASK.PM)        │
               │    AND (nvic_enable[i])     │
               │    AND (nvic_pending[i])    │
               │    AND (priority > active)  │
               └─────────────┬──────────────┘
                             │
                    ┌────────▼─────────┐
                    │ Priority Arbiter │
                    │ (find highest    │
                    │  pending+enabled │
                    │  with sufficient │
                    │  priority)       │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ Exception Entry  │
                    │ (FSM transition) │
                    └──────────────────┘
```

**Masking rules:**

| Exception | Masked by PRIMASK? | Masked by priority? |
|-----------|-------------------|-------------------|
| Reset | No | No (highest) |
| NMI | No | No (priority -2) |
| HardFault | No | No (priority -1) |
| SVCall | Yes | Yes (configurable priority) |
| PendSV | Yes | Yes |
| SysTick | Yes | Yes |
| IRQ[n] | Yes | Yes |

**Exception can preempt when:**
```
exception_pending == 1
AND exception_enabled == 1 (for IRQs)
AND (PRIMASK.PM == 0 OR exception_num < 16)  // NMI/HardFault ignore PRIMASK
AND (exception_priority < active_priority)     // higher priority = lower number
AND (FSM not in STALL or EXC_STACKING)         // evaluate between instructions only
```

### 5.6 Exception Processing FSM

This section expands the exception overlay sub-states introduced in §3.2.3.

#### 5.6.1 Exception Entry Sequence

```
Exception detected (highest priority pending, mask allows)
    │
    ▼ (1) Complete current instruction (if any)
    │
    ▼ (2) EXC_ENTRY
    │   - Determine exception number
    │   - Set IPSR = exception_number
    │   - If Thread mode → switch SP to MSP
    │   - Set LR = EXC_RETURN value (based on mode/SP)
    │
    ▼ (3) EXC_STACKING (8 AHB write cycles)
    │   - SP = SP - 4; write xPSR  → [SP+0x1C]
    │   - SP = SP - 4; write PC   → [SP+0x18]
    │   - SP = SP - 4; write LR   → [SP+0x14]
    │   - SP = SP - 4; write R12  → [SP+0x10]
    │   - SP = SP - 4; write R3   → [SP+0x0C]
    │   - SP = SP - 4; write R2   → [SP+0x08]
    │   - SP - 4; write R1   → [SP+0x04]
    │   - SP = SP - 4; write R0   → [SP+0x00]
    │
    ▼ (4) EXC_VECTOR_FETCH (1 AHB read cycle)
    │   - HADDR = vector_table_base + (4 × exception_number)
    │   - Capture HRDATA → handler_PC
    │
    ▼ (5) Set PC = handler_PC
    │   Set nvic_active[exception_bit] = 1
    │   Clear nvic_pending[exception_bit] = 0
    │
    ▼ (6) Resume pipeline → FETCH with new PC
```

**Stacking timing:**
- 8 sequential AHB writes (address phase + data phase each)
- Each write: 2 cycles minimum (0 wait states)
- Total stacking: ≥16 cycles
- Each write may stall on `HREADY`=0

#### 5.6.2 Exception Return Sequence

```
BX LR or POP {PC} with EXC_RETURN pattern detected
    │   (LR[31:4] == 28'hFFFFFFF)
    │
    ▼ (1) EXC_RETURN
    │   - Determine return mode from EXC_RETURN[3:0]:
    │     F1 → Handler mode, MSP
    │     F9 → Thread mode, MSP
    │     FD → Thread mode, PSP
    │
    ▼ (2) EXC_UNSTACKING (8 AHB read cycles)
    │   - Read [SP+0x00] → R0;  SP = SP + 4
    │   - Read [SP+0x04] → R1;  SP = SP + 4
    │   - Read [SP+0x08] → R2;  SP = SP + 4
    │   - Read [SP+0x0C] → R3;  SP = SP + 4
    │   - Read [SP+0x10] → R12; SP = SP + 4
    │   - Read [SP+0x14] → LR;  SP = SP + 4
    │   - Read [SP+0x18] → PC;  SP = SP + 4
    │   - Read [SP+0x1C] → xPSR;SP = SP + 4
    │
    ▼ (3) Restore state
    │   - Clear IPSR = 0 (or restore from stacked xPSR)
    │   - Set SP selection per EXC_RETURN
    │   - Clear nvic_active[exception_bit] = 0
    │
    ▼ (4) Resume pipeline → FETCH with restored PC
```

#### 5.6.3 Tail-Chaining

```
Exception A handler executing
    │
    ▼ Exception B pending with priority ≥ A's priority
    │
    ▼ Handler A executes BX LR (EXC_RETURN)
    │
    ▼ EXC_RETURN detected:
    │   - Skip unstacking of A
    │   - Do NOT pop {R0-R3, R12, LR, PC, xPSR}
    │   - Clear active bit for A
    │   - Reuse the stacked frame (still on stack)
    │
    ▼ EXC_VECTOR_FETCH for B (1 AHB read)
    │   - HADDR = vector_table_base + (4 × exception_B_number)
    │
    ▼ Set PC = handler_B_PC, IPSR = B_number
    │   Set nvic_active[B_bit] = 1
    │
    ▼ Resume pipeline → FETCH
```

**Tail-chain latency: ≥6 cycles** (vector fetch only, no stacking/unstacking)

#### 5.6.4 Late Arrival

```
Exception A stacking in progress (EXC_STACKING, partial writes)
    │
    ▼ Exception B detected with higher priority than A
    │
    ▼ Abandon A's partial stacking:
    │   - SP reset to pre-stacking value (saved on entry)
    │   - Partial stack writes are garbage (will be overwritten)
    │
    ▼ Restart EXC_STACKING for B:
    │   - Push {R0, R1, R2, R3, R12, LR, PC, xPSR} for B
    │   - Set LR = EXC_RETURN for B
    │   - IPSR = B_number
    │
    ▼ EXC_VECTOR_FETCH for B
    │
    ▼ Execute handler B
```

**Late-arrival latency: ≥16 cycles** (same as normal entry — restart stacking)

### 5.7 HardFault Triggers

| Trigger | Condition | Detection Point | Priority |
|---------|-----------|-----------------|----------|
| Undefined instruction | Decoded instruction not in valid ARMv6-M subset | DECODE state | -1 |
| Invalid memory access | `HRESP`=ERROR during any AHB transfer | FETCH or MEM_WAIT state | -1 |
| Unaligned access | `HADDR[1:0]` ≠ `00` for word, `HADDR[0]` ≠ `0` for halfword | EXECUTE state (before bus) | -1 |
| Stacking fault | `HRESP`=ERROR during EXC_STACKING | EXC_STACKING state | -1 (escalates) |
| SVC at wrong priority | SVC executed at priority ≥ SVCall configured priority | EXECUTE state | -1 |

> HardFault cannot be masked by PRIMASK. If HardFault occurs during another HardFault handler, the core enters a locked state (implementation defined — may require reset).

### 5.8 SysTick Timer

| Register | Offset (SCS) | Width | Access | Reset | Description |
|----------|-------------|-------|--------|-------|-------------|
| `SYST_CSR` | `0xE000E010` | 32 | RW | `32'h00000000` | Control and Status Register |
| `SYST_RVR` | `0xE000E014` | 24 (of 32) | RW | `24'h000000` | Reload Value Register |
| `SYST_CVR` | `0xE000E018` | 24 (of 32) | RW | `24'h000000` | Current Value Register |
| `SYST_CALIB` | `0xE000E01C` | 32 | RO | Implementation-defined | Calibration Value Register |

#### SYST_CSR Bitfields

| Bits | Name | Access | Reset | Description |
|------|------|--------|-------|-------------|
| [0] | ENABLE | RW | 0 | SysTick counter enable. 1=counter running. |
| [1] | TICKINT | RW | 0 | SysTick interrupt enable. 1=exception on count-down to zero. |
| [2] | CLKSOURCE | RW | 0 | Clock source: 0=external reference, 1=HCLK. Default implementation: tied to HCLK. |
| [16] | COUNTFLAG | RO | 0 | Returns 1 if counter reached zero since last read. Self-clearing on read. |
| [31:17] | RSVD | — | 0 | Reserved |
| [15:3] | RSVD | — | 0 | Reserved |

#### SysTick Operation

```
if (SYST_CSR.ENABLE == 1)
    every HCLK rising edge:
        if (SYST_CVR == 0) {
            SYST_CVR = SYST_RVR;           // reload
            SYST_CSR.COUNTFLAG = 1;        // flag
            if (SYST_CSR.TICKINT == 1) {
                nvic_pending[15] = 1;      // pend SysTick exception (#15)
            }
        } else {
            SYST_CVR = SYST_CVR - 1;      // count down
        }
```

### 5.9 Interrupt Latency Summary

| Scenario | Minimum Cycles | Description |
|----------|---------------|-------------|
| IRQ assert → first handler instruction | ≥16 | 2 (sync) + 1 (detect) + 8×2 (stacking) + 2 (vector fetch) |
| NMI edge → first handler instruction | ≥16 | Same flow as IRQ |
| Tail-chain (A → B) | ≥6 | Skip stacking/unstacking, vector fetch only |
| Late arrival (B preempts A stacking) | ≥16 | Restart stacking for B |
| SVCall → handler | ≥16 | Same as IRQ (software triggered) |
| SysTick → handler | ≥16 | Same as IRQ (timer triggered) |

## §6 — Memory Map & Bus Protocol

### 6.1 Internal Memory Instances

The `cortex_m0_core` contains **no large SRAM or FIFO memories**. All internal storage is flip-flop based. All instruction and data memory is external, accessed via the AHB-Lite bus.

#### 6.1.1 Memory Instance Table

| # | Instance | Type | Depth × Width | Read Ports | Write Ports | Read Latency | Write Latency | Reset State | ECC |
|---|----------|------|---------------|------------|-------------|-------------|--------------|-------------|-----|
| 1 | GPRF | Register File (FF) | 17 × 32-bit | 2 (simultaneous) | 1 | 0 cycles (comb) | 0 cycles (sync edge) | R0–R12=0, MSP=INIT_SP, PSP=0, LR=0xFFFFFFFF, PC=INIT_PC | None |
| 2 | SPR — APSR | Flip-flop | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x00000000 | None |
| 3 | SPR — IPSR | Flip-flop | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x00000000 | None |
| 4 | SPR — EPSR | Flip-flop | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x01000000 | None |
| 5 | SPR — PRIMASK | Flip-flop | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x00000000 | None |
| 6 | SPR — CONTROL | Flip-flop | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x00000000 | None |
| 7 | NVIC pending | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 (W1C) | 0 cycles | 0 cycles | All 0 | None |
| 8 | NVIC enable | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 | 0 cycles | 0 cycles | All 0 | None |
| 9 | NVIC active | Bit array (FF) | IRQ_NUM × 1-bit | 1 | 1 (auto) | 0 cycles | 0 cycles | All 0 | None |
| 10 | NVIC priority | Bit array (FF) | IRQ_NUM × N-bit | 1 | 1 | 0 cycles | 0 cycles | All 0 | None |
| 11 | SysTick CSR | Register (FF) | 1 × 32-bit | 1 | 1 | 0 cycles | 0 cycles | 0x00000000 | None |
| 12 | SysTick RVR | Register (FF) | 1 × 24-bit | 1 | 1 | 0 cycles | 0 cycles | 0x000000 | None |
| 13 | SysTick CVR | Counter (FF) | 1 × 24-bit | 1 | 1 | 0 cycles | 0 cycles | 0x000000 | None |

> **Total internal storage (IRQ_NUM=32, N=2):** ~912 bits (~114 bytes)

#### 6.1.2 GPRF Port Details

```
              ┌──────────────────────────┐
   reg_r1_sel──▶│                          │──▶ reg_r1_data[31:0]
   reg_r2_sel──▶│      GPRF (17 × 32)      │──▶ reg_r2_data[31:0]
              │   R0–R12, MSP, PSP, LR, PC │
   reg_w_sel ──▶│                          │◀── reg_w_data[31:0]
   reg_w_en  ──▶│                          │
              └──────────────────────────┘

   SP selection:
   handler_mode ? MSP : (CONTROL.SPSEL ? PSP : MSP)
```

| Port | Signal | Width | Type | Description |
|------|--------|-------|------|-------------|
| Read 1 select | `reg_r1_sel` | 4 | input | Register index for operand A |
| Read 1 data | `reg_r1_data` | 32 | output | Operand A data (combinational) |
| Read 2 select | `reg_r2_sel` | 4 | input | Register index for operand B |
| Read 2 data | `reg_r2_data` | 32 | output | Operand B data (combinational) |
| Write select | `reg_w_sel` | 4 | input | Register index for write |
| Write data | `reg_w_data` | 32 | input | Data to write |
| Write enable | `reg_w_en` | 1 | input | Write strobe |

**R13 (SP) banking logic:**
- `reg_r1_sel == 4'd13` → mux output from MSP or PSP based on mode/SPSEL
- `reg_w_sel == 4'd13` → write to MSP or PSP based on mode/SPSEL
- R15 (PC) reads return current PC; writes to R15 are ignored (PC updated by branch/exception logic only)

### 6.2 External Memory Map (ARMv6-M Architectural)

The core accesses all external memory via AHB-Lite. The ARMv6-M architecture defines the following fixed memory map:

| Address Range | Size | Region Name | Access | Description |
|--------------|------|-------------|--------|-------------|
| `0x00000000` – `0x1FFFFFFF` | 512 MB | **Code** | Execute + Read/Write | Instruction fetch, literal pools, constant data |
| `0x20000000` – `0x3FFFFFFF` | 512 MB | **SRAM** | Read/Write | Data RAM, stack, heap |
| `0x40000000` – `0x5FFFFFFF` | 512 MB | **Peripheral** | Read/Write | Device registers (bit-band alias at `0x42000000`) |
| `0x60000000` – `0x9FFFFFFF` | 1 GB | **External RAM** | Read/Write | Off-chip memory |
| `0xA0000000` – `0xDFFFFFFF` | 1 GB | **External Device** | Read/Write | Off-chip device registers |
| `0xE0000000` – `0xE00FFFFF` | 1 MB | **System Control Space (SCS)** | Read/Write | NVIC, SysTick, SCB registers |
| `0xE0100000` – `0xFFFFFFFF` | ~16 MB | **Vendor System** | Read/Write | Vendor-specific system space |

> The core does **not** enforce memory map access restrictions in hardware — it drives the address on AHB-Lite and the bus infrastructure decodes it. `HPROT` signals indicate the access type for external protection.

### 6.3 Vector Table

Located at the base of Code region (`0x00000000` by default):

| Offset | Content | Description |
|--------|---------|-------------|
| `0x00` | Initial MSP value | Loaded into SP on reset |
| `0x04` | Reset vector (initial PC) | First instruction address |
| `0x08` | NMI handler | — |
| `0x0C` | HardFault handler | — |
| `0x10` – `0x28` | Reserved | — |
| `0x2C` | SVCall handler | — |
| `0x30` – `0x38` | Reserved | — |
| `0x3C` | PendSV handler | — |
| `0x40` | SysTick handler | — |
| `0x44` | IRQ[0] handler | — |
| `0x48` | IRQ[1] handler | — |
| `0x44 + 4×n` | IRQ[n] handler | Up to IRQ[IRQ_NUM-1] |

**Vector fetch address:** `vector_table_base + (4 × exception_number)`

### 6.4 AHB-Lite Bus Protocol

#### 6.4.1 Transfer Phases

The core uses a simplified AHB-Lite master protocol with two pipelined phases:

```
Cycle N:     Address Phase ──▶ Data Phase
             HADDR, HTRANS    HRDATA/HWDATA
             HSIZE, HWRITE    HREADY
             HBURST, HPROT    HRESP
             HMASTLOCK
```

| Phase | Signals | Direction | Description |
|-------|---------|-----------|-------------|
| Address Phase | `HADDR`, `HTRANS`, `HSIZE`, `HWRITE`, `HBURST`, `HPROT`, `HMASTLOCK` | Core → Bus | Driven in cycle N |
| Data Phase | `HWDATA` (write) or `HRDATA` (read), `HREADY`, `HRESP` | Core ↔ Bus | Sampled/driven in cycle N+1 |

#### 6.4.2 Transfer Types Used

| `HTRANS` | Name | When Used |
|----------|------|-----------|
| `2'b00` (IDLE) | No transfer | After reset, or when core has no pending bus request |
| `2'b01` (BUSY) | Insert wait | Not used in initial implementation (simplified) |
| `2'b10` (NONSEQ) | Single transfer | First beat of every instruction fetch, load, store, stacking, unstacking |
| `2'b11` (SEQ) | Sequential beat | Continuation of PUSH/POP multi-word transfers (same burst) |

#### 6.4.3 Burst Behavior

| Operation | Burst Type | Beats | `HBURST` |
|-----------|-----------|-------|----------|
| Single load/store | SINGLE | 1 | `3'b000` |
| Instruction fetch | SINGLE | 1 | `3'b000` |
| PUSH (N registers) | INCR4 or individual | N | `3'b000` (simplified) |
| POP (N registers) | INCR4 or individual | N | `3'b000` (simplified) |

> **Implementation note:** PUSH/POP may be implemented as individual SINGLE transfers (one AHB beat per register) for simplicity. This is architecturally correct but not optimal. Future optimization: use INCR4 burst for 4-register groups.

#### 6.4.4 Transfer Size Encoding

| `HSIZE` | Size | Instructions |
|---------|------|-------------|
| `3'b000` (BYTE) | 8-bit | `LDRB`, `STRB` |
| `3'b001` (HALFWORD) | 16-bit | `LDRH`, `STRH` |
| `3'b010` (WORD) | 32-bit | `LDR`, `STR`, instruction fetch, stacking, unstacking |

#### 6.4.5 Protection Signals (`HPROT`)

| Bit | Name | Default | When Changed |
|-----|------|---------|-------------|
| [0] | Data/Opcode | 1 (data) | 0 for instruction fetch |
| [1] | Privileged | 1 (privileged) | Always 1 in Cortex-M0 (no unprivileged mode) |
| [2] | Bufferable | 0 | — |
| [3] | Cacheable | 0 | — |

> `HPROT` is set to `4'b0011` for data accesses and `4'b0001` for instruction fetches.

#### 6.4.6 Error Response

```
AHB Transfer: HRESP = ERROR (1)
    │
    ▼
Core detection: MEM_WAIT or FETCH state
    │
    ▼
Action:
    - Abandon current transfer
    - Generate HardFault exception
    - hf_cause = BUS_FAULT
    - Transition to EXC_ENTRY
```

- `HRESP`=ERROR during instruction fetch → HardFault (instruction fetch fault)
- `HRESP`=ERROR during data load/store → HardFault (data access fault)
- `HRESP`=ERROR during exception stacking → HardFault (escalates, possible lockup)

### 6.5 Bus Access Characteristics

| Property | Value |
|----------|-------|
| Bus type | Single shared AHB-Lite (instructions and data share same bus) |
| Endianness | Little-endian |
| Unaligned access | **Not supported** — generates HardFault if `HADDR[1:0]` ≠ `00` for word or `HADDR[0]` ≠ `0` for halfword |
| Atomicity | Single transfers are atomic; no LDREX/STREX in initial implementation |
| Write buffer | **None** — stores are blocking (core stalls until `HREADY`=1) |
| Read latency | N+1 cycles (N = number of wait states from slave) |
| Write latency | N+1 cycles (N = number of wait states from slave) |

## §7 — Timing & Reset Strategy

### 7.1 Clock Configuration

| Parameter | Value | Notes |
|-----------|-------|-------|
| Target frequency | **50 MHz** | Technology-independent portable target |
| Clock period | **20 ns** | At 50 MHz |
| Clock domain | **Single (HCLK)** | All logic in one domain |
| PLL/DLL required | **No** | Single clock, no frequency synthesis |
| Max achievable (FPGA) | 100+ MHz | Platform dependent (Xilinx Artix-7, Intel Cyclone IV) |
| Max achievable (ASIC 180nm) | ~200 MHz | Process dependent |

### 7.2 Pipeline Latency

#### 7.2.1 Single-Instruction End-to-End Latency

| Path | Cycles | Description |
|------|--------|-------------|
| Min latency (ALU instruction) | **3 cycles** | FETCH(1) → DECODE(1) → EXECUTE(1) |
| Max latency (load, 0 wait states) | **4 cycles** | FETCH(1) → DECODE(1) → EXECUTE(1) → MEM_WAIT(1) |
| Max latency (load, N wait states) | **4 + N cycles** | Above + N cycles stalled on HREADY=0 |
| Max latency (iterative MUL) | **3 + 32 cycles** | 32-cycle shift-add multiplier |
| Max latency (branch taken) | **3 cycles** | FETCH → DECODE → EXECUTE(flush+refetch) |
| Max latency (BL, Thumb-2) | **4 cycles** | FETCH(2, 32-bit instr) → DECODE(1) → EXECUTE(1) |

#### 7.2.2 Sustained Throughput

| Scenario | Throughput | Description |
|----------|-----------|-------------|
| Back-to-back ALU ops (0 wait states) | **1.0 IPC** | One instruction per cycle once pipeline is full |
| Back-to-back loads (0 wait states) | **0.5 IPC** | 2 cycles per load (addr + data phase) |
| Mixed (70% ALU, 30% MEM, 0 WS) | **~0.77 IPC** | Weighted average |
| All stores (0 wait states) | **0.5 IPC** | Same as loads |
| Interrupt-heavy workload | **< 0.5 IPC** | Stacking/unstacking overhead dominates |

#### 7.2.3 Instruction Timing Detail

| Instruction | Best Case | Worst Case | Notes |
|-------------|-----------|------------|-------|
| ALU (ADD/SUB/MOV/AND/ORR/EOR/BIC) | 1 cycle | 1 cycle | Always single-cycle |
| Shift (LSL/LSR/ASR) | 1 cycle | 1 cycle | Inline barrel shifter |
| Compare (CMP/CMN/TST) | 1 cycle | 1 cycle | Flags only, no writeback |
| Move (MOV/MVN) | 1 cycle | 1 cycle | |
| Branch not-taken | 0 penalty | 0 penalty | Next fetch already valid |
| Branch taken (B/B<cond>) | 2 cycles | 3 cycles | Pipeline flush + refetch |
| Branch with link (BL) | 3 cycles | 4 cycles | Flush + LR save + refetch |
| BX/BLX | 2 cycles | 3 cycles | Register-indirect |
| LDR/STR (word) | 2 cycles | 2+N cycles | 1 addr + 1 data + N wait states |
| LDRB/STRB (byte) | 2 cycles | 2+N cycles | |
| LDRH/STRH (halfword) | 2 cycles | 2+N cycles | |
| PUSH (N registers) | N+1 cycles | (N+1)×(1+WS) cycles | Sequential AHB writes |
| POP (N registers) | N+1 cycles | (N+1)×(1+WS) cycles | Sequential AHB reads |
| MUL (single-cycle) | 1 cycle | 1 cycle | Hardware multiplier |
| MUL (iterative) | 1 cycle | 32 cycles | Shift-add, area-optimized |
| MRS/MSR | 1 cycle | 1 cycle | Special register access |
| CPSIE/CPSID | 1 cycle | 1 cycle | PRIMASK modification |
| WFI/WFE | 1 cycle (then sleep) | Indefinite | Until wake event |
| BKPT | ∞ | ∞ | Until debug resume |
| NOP | 1 cycle | 1 cycle | |
| SVC | — | — | Triggers exception (≥16 cycles to handler) |
| DMB/DSB/ISB | 1 cycle | 1 cycle | No-op in single-master system |

### 7.3 Critical Path Analysis

#### 7.3.1 Expected Critical Path

```
GPRF read (2R, combinational)
    → Operand mux (sel from 17 registers)
        → ALU (32-bit add/sub)
            → Condition code generator (N,Z,C,V)
                → APSR write (flag registers)

Estimated: 3–4 LUT levels on FPGA
```

#### 7.3.2 Path Ranking

| Priority | Path | Logic Depth (FPGA LUT levels) | Timing Risk |
|----------|------|------|------------|
| 1 | GPRF read → ALU → flags → APSR writeback | 3–4 | **Critical** — determines Fmax |
| 2 | Instruction decode → register read → operand mux | 3–4 | High — decode + mux chain |
| 3 | PC + offset → branch target → HADDR mux → output | 2–3 | Medium — adder + mux |
| 4 | NVIC priority arbitration (log₂(IRQ_NUM) compares) | log₂(IRQ_NUM) | Medium — scales with IRQ_NUM |
| 5 | Barrel shifter (32-bit, 5-stage mux) | 5 | Medium — shifter cascade |

> At 50 MHz (20 ns), paths 1–5 should comfortably meet timing on any FPGA or ASIC ≥180nm.

#### 7.3.3 Multicycle Paths

| Path | Cycles | Condition | Handling |
|------|--------|-----------|----------|
| MUL (iterative) | 1–32 | MUL instruction active | Pipeline stalls internally, counter decrements |
| AHB wait states | N+1 | HREADY=0 | STALL state, all outputs held stable |
| Exception stacking | ≥16 | EXC_STACKING state | 8 sequential AHB writes |
| Vector fetch | 1+N | EXC_VECTOR_FETCH state | 1 AHB read + N wait states |

### 7.4 Clock Domain Crossing (CDC)

#### 7.4.1 CDC Paths

| Source → Destination | Signal | Width | Synchronizer | Latency | MTBF Target |
|---------------------|--------|-------|-------------|---------|-------------|
| External async → HCLK | `IRQ[IRQ_NUM-1:0]` | IRQ_NUM | 2-stage FF | 2 cycles | >10 years |
| External async → HCLK | `NMI` | 1 | 2-stage FF + edge detect | 2 cycles | >10 years |
| External async → HCLK | `DBGRQ` | 1 | 2-stage FF | 2 cycles | >10 years |
| External async → HCLK | `HRESETn` | 1 | Async assert, sync deassert | — | — |

#### 7.4.2 Synchronizer Implementation

**IRQ / NMI / DBGRQ Synchronizer (2-stage):**
```verilog
// Per bit
always @(posedge HCLK or negedge HRESETn) begin
    if (!HRESETn) begin
        sync_ff1 <= 1'b0;
        sync_ff2 <= 1'b0;
    end else begin
        sync_ff1 <= async_input;  // Stage 1 — may be metastable
        sync_ff2 <= sync_ff1;     // Stage 2 — stable output
    end
end
assign synced_output = sync_ff2;
```

**NMI Edge Detection (additional logic after synchronizer):**
```verilog
always @(posedge HCLK or negedge HRESETn) begin
    if (!HRESETn)
        nmi_delayed <= 1'b0;
    else
        nmi_delayed <= nmi_sync;  // sync_ff2 from above
end
assign nmi_edge = nmi_sync & ~nmi_delayed;  // rising edge pulse
```

**Reset Synchronizer (async assert, sync deassert):**
```verilog
always @(posedge HCLK or negedge HRESETn) begin
    if (!HRESETn)
        rst_sync <= 1'b0;           // Async assert — immediate
    else
        rst_sync <= 1'b1;           // Sync deassert — one cycle delay
end
assign internal_reset_n = rst_sync;  // Used by all internal logic
```

#### 7.4.3 No-CDC Paths

All other signals are synchronous to HCLK — no synchronizer needed:
- AHB outputs: `HADDR`, `HWDATA`, `HTRANS`, `HSIZE`, `HWRITE`, `HBURST`, `HPROT`, `HMASTLOCK`
- AHB inputs: `HRDATA`, `HREADY`, `HRESP`
- Debug outputs: `HALTED`, `DBGACK`, `EVTEXEC`

### 7.5 I/O Timing

#### 7.5.1 Input Timing (Synchronous)

| Signal | Setup Time | Hold Time | Notes |
|--------|-----------|-----------|-------|
| `HRDATA[31:0]` | Technology-dependent | Technology-dependent | Synchronous to HCLK rising edge |
| `HREADY` | Technology-dependent | Technology-dependent | Synchronous to HCLK rising edge |
| `HRESP` | Technology-dependent | Technology-dependent | Synchronous to HCLK rising edge |

#### 7.5.2 Input Timing (Asynchronous)

| Signal | Setup/Hold | Notes |
|--------|-----------|-------|
| `IRQ[IRQ_NUM-1:0]` | N/A | Asynchronous — 2-stage synchronizer absorbs metastability |
| `NMI` | N/A | Asynchronous — 2-stage synchronizer + edge detect |
| `DBGRQ` | N/A | Asynchronous — 2-stage synchronizer |

#### 7.5.3 Output Timing

All outputs are registered (clock-to-Q only, no combinational output paths):

| Signal | Output Type | Notes |
|--------|------------|-------|
| `HADDR[31:0]` | Registered (Tco) | Driven from address phase register |
| `HWDATA[31:0]` | Registered (Tco) | Driven from data phase register |
| `HWRITE` | Registered (Tco) | |
| `HTRANS[1:0]` | Registered (Tco) | |
| `HSIZE[2:0]` | Registered (Tco) | |
| `HBURST[2:0]` | Registered (Tco) | |
| `HPROT[3:0]` | Registered (Tco) | |
| `HMASTLOCK` | Registered (Tco) | |
| `HALTED` | Registered (Tco) | |
| `DBGACK` | Registered (Tco) | |
| `EVTEXEC` | Registered (Tco) | Pulsed for 1 cycle |

### 7.6 Timing Exceptions & Constraints

| Exception Type | Path | Cycles | Constraint |
|---------------|------|--------|------------|
| **False path** | `HRESETn` → all registers | — | Reset is timing-exclusive with functional clocks |
| **False path** | Synchronized `DBGRQ` → debug FSM | — | Already synchronized, no cross-domain timing |
| **Multicycle** | Iterative MUL path | 32 | When MUL instruction is active |
| **Multicycle** | Exception stacking | ≥16 | During EXC_STACKING state |
| **No exception** | Single-cycle ALU path | 1 | Must meet 20 ns timing |
| **No exception** | Register file read/write | 1 | Combinational read, synchronous write |
| **No exception** | AHB output signals | 1 | Registered outputs |

### 7.7 Reset Strategy

#### 7.7.1 Reset Sequencing

```
HRESETn asserted (goes LOW)
    │
    ▼ Asynchronous — takes effect immediately
    │
    ├─ All registers forced to reset values (see §4.3, §6.1)
    ├─ FSM state ← RESET
    ├─ HTRANS ← IDLE
    ├─ All AHB outputs ← defaults (see §2.4)
    ├─ NVIC: all pending/enable/active cleared
    ├─ PRIMASK ← 0
    ├─ CONTROL ← 0
    ├─ IPSR ← 0
    ├─ EPSR.T ← 1
    └─ SysTick: CSR/RVR/CVR ← 0
    
HRESETn deasserted (goes HIGH)
    │
    ▼ Synchronous — core waits for HCLK rising edge
    │
    ├─ Internal reset synchronizer releases (1 cycle)
    │
    ▼ FSM transitions: RESET → FETCH
    │
    ├─ PC ← INIT_PC
    ├─ SP ← INIT_SP
    ├─ Drive first AHB fetch: HADDR=PC, HTRANS=NONSEQ
    │
    ▼ Normal operation begins
```

#### 7.7.2 Reset During Execution

| Scenario | Behavior |
|----------|----------|
| Reset during ALU execution | Immediate — all state discarded, pipeline flushed |
| Reset during AHB transfer | Transfer abandoned, HTRANS←IDLE on next cycle |
| Reset during exception stacking | Partial stack frame abandoned, SP reset to INIT_SP |
| Reset during exception handler | Handler aborted, all NVIC state cleared |
| Reset during SLEEP | Core wakes, enters RESET state |

#### 7.7.3 Reset Recovery Time

| Parameter | Cycles | Description |
|-----------|--------|-------------|
| `HRESETn` assertion → all registers reset | 0 (async) | Immediate |
| `HRESETn` deassertion → internal reset release | 1 | Sync deassert |
| `HRESETn` deassertion → first instruction fetch | 2 | 1 (sync) + 1 (FETCH drive) |
| `HRESETn` deassertion → first instruction complete | 4–5 | 2 (above) + 2–3 (pipeline) |

## §8 — RTL Implementation Notes

### 8.1 Coding Style

| Rule | Convention | Rationale |
|------|-----------|-----------|
| Sequential logic | `always_ff @(posedge HCLK or negedge HRESETn)` with nonblocking assignments (`<=`) | Standard synchronous design, prevents simulation race conditions |
| Combinational logic | `always_comb` with blocking assignments (`=`) | SystemVerilog best practice, auto-sensitivity |
| Latch prevention | Every `always_comb` must assign **all** outputs in **every** branch; use `default` in all `case` statements | Latches are design errors in this core |
| Module boundaries | Single flat module `cortex_m0_core` — no sub-module instantiation | Area optimization (see §2.1) |
| Parameter usage | `IRQ_NUM`, `INIT_PC`, `INIT_SP` as module parameters | Configurable at elaboration time |
| Signal naming | `snake_case` for signals, `UPPER_CASE` for parameters, `_n` suffix for active-low | Consistency, readability |
| Reset values | Explicit reset in every `always_ff` — no uninitialized state | Deterministic power-on behavior |

### 8.2 Reset Convention

| Property | Value |
|----------|-------|
| Reset signal | `HRESETn` (active-low) |
| Reset type | **Asynchronous assert, synchronous deassert** |
| Internal reset | `internal_reset_n` — output of 2-stage reset synchronizer |
| Register reset | All registers reset asynchronously on `!HRESETn` |
| Reset polarity in RTL | `if (!HRESETn) ... else ...` pattern in every `always_ff` |

**Template for every sequential block:**
```verilog
always_ff @(posedge HCLK or negedge HRESETn) begin
    if (!HRESETn) begin
        reg_name <= RESET_VALUE;  // Explicit reset value
    end else begin
        // Functional logic
    end
end
```

**Reset priority:** `HRESETn` assertion at any FSM state → immediate transition to `RESET` state, overriding all other conditions.

### 8.3 Pipeline Register Insertion

The FSM-based pipeline requires specific register stages to isolate clock domains and meet timing:

| Register Stage | Signal | Purpose |
|---------------|--------|---------|
| Address phase register | `HADDR_r`, `HTRANS_r`, `HSIZE_r`, `HWRITE_r`, `HBURST_r`, `HPROT_r` | Registered AHB outputs — driven on clock edge, held stable during stall |
| Data phase register | `HWDATA_r` | Registered write data — driven one cycle after address phase |
| Instruction register | `instr_reg` | Captured `HRDATA` from fetch — held during decode/execute |
| PC register | `pc_reg` | Current program counter — updated by fetch increment, branch, or exception |
| FSM state register | `fsm_state` | Pipeline controller state — one-hot or encoded |
| Synchronizer FFs | `irq_sync`, `nmi_sync`, `dbgrq_sync` | 2-stage metastability hardening for async inputs |
| Reset synchronizer | `rst_sync` | Async assert, sync deassert for clean reset release |

**Registered outputs:** All AHB outputs (`HADDR`, `HTRANS`, `HSIZE`, `HWRITE`, `HBURST`, `HPROT`, `HMASTLOCK`, `HWDATA`) and debug outputs (`HALTED`, `DBGACK`, `EVTEXEC`) are registered. No combinational paths from internal logic to output ports.

### 8.4 Tie-Off Rules for Unused Inputs

| Signal | Tie-Off | Justification |
|--------|---------|---------------|
| `HRDATA[31:0]` | No tie-off — always used when `HREADY`=1 | Sampled during data phase |
| `HREADY` | No tie-off — always sampled | Controls pipeline stall |
| `HRESP` | No tie-off — always sampled | Triggers HardFault on ERROR |
| `IRQ[IRQ_NUM-1:0]` | Tie to `0` if not connected | No spurious interrupts |
| `NMI` | Tie to `0` if not connected | No spurious NMI |
| `DBGRQ` | Tie to `0` if not connected | No spurious debug halt |

**Tie-off at SoC integration:** Unconnected IRQ lines should be tied low at the SoC level. The core itself does not generate internal pull-ups/pull-downs.

### 8.5 Expected Lint Warnings & Waivers

| Warning ID | Description | Waiver Justification |
|------------|-------------|---------------------|
| Width mismatch | PC increment by 2 or 4 may generate "constant truncated" warnings | Intentional — Thumb-16 uses PC+2, Thumb-2 uses PC+4 |
| Unused bits | `EPSR[31:25]` and `EPSR[23:0]` are reserved and never driven | Intentional — reads as zero per ARMv6-M spec |
| Unused bits | `IPSR[31:9]` reserved, always zero | Intentional |
| Unused bits | `PRIMASK[31:1]` reserved, always zero | Intentional |
| Unused bits | `CONTROL[31:1]` reserved, always zero | Intentional |
| One-bit signal unused | `EVTEXEC` may be unconnected in some integrations | Functional — only used with WFE, tie-off at SoC level |
| Case default | FSM `default` case may trigger "unreachable" warnings | Intentional — defensive coding for undefined state recovery |
| Signal not read | Synchronizer `sync_ff1` is only written, not directly used | Intentional — metastability capture stage, `sync_ff2` is the used output |

### 8.6 Synthesis Considerations

| Consideration | Guidance |
|---------------|----------|
| Technology | Technology-independent RTL — no FPGA primitives, no ASIC macros |
| Clock gating | Not required for initial implementation; WFI/WFE sleep reduces dynamic power naturally |
| Operand isolation | ALU operand isolation optional — power optimization, not functional |
| Multiplier | Default: single-cycle hardware multiplier. Fallback: iterative shift-add (32 cycles) if area-constrained |
| Register file | Flip-flop based, no SRAM macro — 17×32 = 544 FFs. Acceptable for FPGA and small ASIC |
| Reset fanout | `HRESETn` feeds all ~1500 FFs — ensure reset buffer tree in synthesis |
| Scan insertion | All FFs should be scannable for production test — no `always_latch`, no multi-clock domains |

### 8.7 Port Consistency Check (§2 Cross-Reference)

Every output port listed in §2 must be driven. Every input port must be sampled.

| Port (from §2) | Driven/Sampled | Implementation |
|----------------|----------------|----------------|
| `HCLK` | Input — clock | Direct to all `always_ff` |
| `HRESETn` | Input — async reset | Direct to all `always_ff` + reset synchronizer |
| `HADDR[31:0]` | Output — registered | `HADDR_r` address phase register |
| `HBURST[2:0]` | Output — registered | `HBURST_r` = `3'b000` (SINGLE) default |
| `HMASTLOCK` | Output — registered | `HMASTLOCK_r` = `1'b0` always (no exclusive access) |
| `HPROT[3:0]` | Output — registered | `HPROT_r` = `4'b0011` (data+privileged) or `4'b0001` (fetch) |
| `HSIZE[2:0]` | Output — registered | `HSIZE_r` — driven per instruction class |
| `HTRANS[1:0]` | Output — registered | `HTRANS_r` — IDLE/NONSEQ/SEQ per FSM state |
| `HWDATA[31:0]` | Output — registered | `HWDATA_r` — driven during write data phase |
| `HWRITE` | Output — registered | `HWRITE_r` — 1 for store, 0 for fetch/load |
| `HRDATA[31:0]` | Input — sampled | Captured when `HREADY`=1 |
| `HREADY` | Input — sampled | Controls STALL logic |
| `HRESP` | Input — sampled | ERROR → HardFault trigger |
| `IRQ[IRQ_NUM-1:0]` | Input — async sync | 2-stage FF synchronizer → NVIC pending |
| `NMI` | Input — async sync | 2-stage FF synchronizer + edge detect |
| `EVTEXEC` | Output — registered | Pulsed 1 cycle on WFE event |
| `HALTED` | Output — registered | Set when core in DEBUG_HALT state |
| `DBGRQ` | Input — async sync | 2-stage FF synchronizer → debug logic |
| `DBGACK` | Output — registered | Acknowledges debug halt |

**All 19 ports accounted for — zero unconnected signals.**

## §9 — Verification Strategy

### 9.1 Test Scenarios

#### 9.1.1 Core Smoke Tests (S1–S6)

| ID | Sequence Name | Steps | Expected Result | Priority |
|----|--------------|-------|-----------------|----------|
| S1 | **Power-on reset** | 1. Assert `HRESETn`=0 for 10 cycles. 2. Deassert `HRESETn`. 3. Wait for first AHB fetch. | PC=`INIT_PC`, SP=`INIT_SP`, all GPRs=0, `HTRANS`=NONSEQ, `HADDR`=INIT_PC. FSM=FETCH. | P0 |
| S2 | **Basic ALU operation** | 1. Load ADD R0, R1, #5 into instruction memory. 2. Set R1=10. 3. Execute. | R0=15, APSR.Z=0, APSR.N=0, PC advances by 2. | P0 |
| S3 | **Interrupt flow** | 1. Configure NVIC: enable IRQ[0], set priority. 2. Execute NOP loop. 3. Assert IRQ[0] for 5 cycles. 4. Wait for handler. 5. Handler clears pending via write to NVIC. | Exception entry: {R0–R3,R12,LR,PC,xPSR} stacked to MSP. Handler executes. EXC_RETURN unstacks. IPSR returns to 0. | P0 |
| S4 | **Memory R/W** | 1. STR R0, [R1] with R0=0xDEADBEEF, R1=0x20000000. 2. LDR R2, [R1]. | R2=0xDEADBEEF. AHB: write then read at same address. HWDATA=0xDEADBEEF, HRDATA captured correctly. | P0 |
| S5 | **Back-to-back ALU** | 1. Execute 100 sequential ADD instructions (ADD R0, R0, #1). 2. Compare final R0. | R0=100. Sustained 1.0 IPC (no stalls between instructions). | P0 |
| S6 | **Error injection** | 1. Execute undefined instruction (e.g., 0xDEAD). 2. Force `HRESP`=ERROR during a load. | Undefined instruction → HardFault (IPSR=3). HRESP=ERROR → HardFault. Both: stacking + vector fetch + handler executes. | P0 |

#### 9.1.2 Extended Test Matrix (T1–T37)

| Category | Tests | IDs | Priority |
|----------|-------|-----|----------|
| **Core Instructions** | ALU arithmetic, logic, shift, compare, move, multiply, branch, load/store, MRS/MSR, CPS, WFI/WFE | T1–T15 | P0/P1 |
| **Exceptions & Interrupts** | IRQ entry/return, NMI, HardFault (3 triggers), SVCall, nested, tail-chain, late-arrival, PRIMASK, SysTick, multiple IRQs | T16–T27 | P0/P1 |
| **Reset & Initialization** | Cold reset, reset during execution, reset during exception | T28–T30 | P0/P1 |
| **Pipeline & Bus** | Stall, back-to-back, load-use hazard, branch-after-branch | T31–T34 | P0/P1 |
| **Debug** | BKPT, DBGRQ/DBGACK, single-step | T35–T37 | P1/P2 |

**Total: 37 test scenarios + 6 smoke tests = 43 tests**

### 9.2 Corner Cases & Hazard Conditions

| ID | Corner Case | Risk | Expected Behavior | Test |
|----|-----------|------|-------------------|------|
| C1 | SP overflow (PUSH near 0x00000000) | Stack wraps to 0xFFFFFFFF | Memory write wraps, no exception | Directed |
| C2 | SP underflow (POP near 0xFFFFFFFF) | Stack wraps to 0x00000000 | Memory read wraps, no exception | Directed |
| C3 | Invalid EXC_RETURN | BX LR with non-EXC_RETURN value | Treated as normal branch, not exception return | Directed |
| C4 | Exception during stacking | Fault during EXC_STACKING | Escalates to HardFault | Directed |
| C5 | NMI during HardFault handler | Double fault condition | NMI preempts HardFault (NMI priority > HardFault) | Directed |
| C6 | Zero-length PUSH/POP | Empty register list | Unpredictable — trap as NOP or HardFault | Directed |
| C7 | MUL overflow (0xFFFFFFFF × 0xFFFFFFFF) | Maximum multiplication | Lower 32 bits returned, N,Z flags updated | Directed |
| C8 | Branch to unaligned address | BX with addr[0]=0 | HardFault (T-bit must be 1) | Directed |
| C9 | WFI with pending interrupt | WFI when IRQ already pending | Core does NOT sleep — immediately handles pending IRQ | Directed |
| C10 | SP not word-aligned | SP[1:0] ≠ 0 due to corruption | SP[1:0] forced to 0 on write | Directed |
| C11 | Reset during interrupt sync | HRESETn rises while IRQ being synchronized | Reset takes priority, sync state discarded | Directed |
| C12 | Unaligned LDR/STR | HADDR[1:0] ≠ 00 for word access | HardFault generated | Directed |
| C13 | HardFault during HardFault | Double HardFault condition | Lockup — core requires external reset | Directed |

### 9.3 SystemVerilog Assertions (SVA)

#### 9.3.1 AHB-Lite Protocol Assertions

| ID | Assertion | Description |
|----|-----------|-------------|
| SVA01 | `assert property: @(posedge HCLK) disable iff (!HRESETn) HTRANS != 2'b00 \|-> eventually HREADY==1` | Non-IDLE transfers must eventually complete |
| SVA02 | `assert property: @(posedge HCLK) $fell(internal_reset_n) \|=> HTRANS == 2'b00` | After reset, bus starts in IDLE |
| SVA03 | `assert property: @(posedge HCLK) disable iff (!HRESETn) !HREADY |-> $stable(HWDATA)` | Write data held stable during wait states |
| SVA04 | `assert property: @(posedge HCLK) disable iff (!HRESETn) !HREADY |-> $stable(HADDR)` | Address held stable during wait states |
| SVA05 | `assert property: @(posedge HCLK) disable iff (!HRESETn) HWRITE |-> HTRANS inside {2'b10, 2'b11}` | Write only during active (NONSEQ/SEQ) transfers |

#### 9.3.2 Microarchitecture Assertions

| ID | Assertion | Description |
|----|-----------|-------------|
| SVA06 | `assert property: @(posedge HCLK) disable iff (!HRESETn) EPSR_T == 1'b1` | Thumb bit always 1 in ARMv6-M |
| SVA07 | `assert property: @(posedge HCLK) disable iff (!HRESETn) sp_active[1:0] == 2'b00` | Active SP always word-aligned |
| SVA08 | `assert property: @(posedge HCLK) disable iff (!HRESETn) pc_reg[0] == 1'b0` | PC always halfword-aligned |
| SVA09 | `assert property: @(posedge HCLK) disable iff (!HRESETn) (IPSR != 0) |-> in_handler_mode` | Non-zero IPSR implies handler mode |
| SVA10 | `assert property: @(posedge HCLK) disable iff (!HRESETn) HALTED |-> $stable(pc_reg)` | When halted, PC does not change |
| SVA11 | `assert property: @(posedge HCLK) disable iff (!HRESETn) exc_entry |-> (exc_return_lr inside {32'hFFFFFFF1, 32'hFFFFFFF9, 32'hFFFFFFFD})` | LR loaded with valid EXC_RETURN on entry |
| SVA12 | `assert property: @(posedge HCLK) disable iff (!HRESETn) (PRIMASK[0] == 1'b1 && irq_active) |-> !exception_entry` | Masked IRQ must not trigger exception entry |

#### 9.3.3 FSM Assertions

| ID | Assertion | Description |
|----|-----------|-------------|
| SVA13 | `assert property: fsm_state inside {RESET, FETCH, DECODE, EXECUTE, MEM_WAIT, STALL, SLEEP, DEBUG_HALT, EXC_ENTRY, EXC_STACKING, EXC_VECTOR_FETCH, EXC_RETURN}` | FSM always in valid state |
| SVA14 | `assert property: @(posedge HCLK) disable iff (!HRESETn) $onehot0(fsm_state_oh)` | One-hot encoding valid (at most 1 bit set) |

### 9.4 Functional Coverage Points

| ID | Cover Point | Description | Target |
|----|------------|-------------|--------|
| CV01 | Each ALU opcode executed | All 18 ALU ops (ADD, SUB, AND, ORR, EOR, BIC, LSL, LSR, ASR, MUL, MOV, MVN, CMP, CMN, TST, ADC, SBC, RSB) | 100% |
| CV02 | Each condition code evaluated | All 15 conditions (EQ/NE/CS/CC/MI/PL/VS/VC/HI/LS/GE/LT/GT/LE/AL) both true and false | 100% |
| CV03 | APSR flags individually | N=1, Z=1, C=1, V=1 each set independently | 100% |
| CV04 | APSR all flags set | N=Z=C=V=1 simultaneously | ≥1 occurrence |
| CV05 | All exception types entered | Reset, NMI, HardFault, SVCall, PendSV, SysTick, IRQ[n] all triggered | 100% |
| CV06 | Tail-chain event | Exception A return → exception B without unstacking | ≥1 occurrence |
| CV07 | Late-arrival event | Higher-priority exception during stacking | ≥1 occurrence |
| CV08 | Bus stall | HREADY=0 for ≥1 cycle during active transfer | ≥1 occurrence |
| CV09 | SP switching | MSP→PSP via CONTROL.SPSEL=1 and back | Both directions |
| CV10 | WFI entry and wakeup | WFI executed, core sleeps, wakes on IRQ | ≥1 occurrence |

### 9.5 Coverage Targets

| Coverage Type | Target | Notes |
|---------------|--------|-------|
| Line coverage | ≥ 95% | All RTL lines executed |
| Toggle coverage | ≥ 90% | All bits of all signals toggled 0→1 and 1→0 |
| FSM state coverage | 100% | All pipeline and exception states visited |
| FSM transition coverage | ≥ 95% | All valid state transitions exercised |
| Functional coverage | 100% of CV01–CV10 | All cover points hit |
| Branch coverage | ≥ 95% | All if/else and case branches taken |

### 9.6 Test Execution Phases

| Phase | Tests | Goal | Duration Est. |
|-------|-------|------|---------------|
| **A: Smoke** | S1–S6 | Basic fetch/execute, reset, ALU, memory, interrupt, error | < 1 min |
| **B: ALU** | T1–T6, T12, T13 | All ALU operations correct | < 2 min |
| **C: Memory** | T10, T11, T12 | All load/store formats work | < 3 min |
| **D: Branch** | T7–T9 | All branch types correct | < 2 min |
| **E: Exceptions** | T16–T27 | Full exception/interrupt handling | < 5 min |
| **F: Reset** | T28–T30 | Reset during all states | < 1 min |
| **G: Pipeline** | T31–T34 | Stall, hazard, throughput | < 2 min |
| **H: Debug** | T35–T37 | Debug halt/resume | < 2 min |
| **I: Corner Cases** | C1–C13 | Edge cases and hazard conditions | < 3 min |
| **J: Stress** | Random instruction mix, back-to-back exceptions | Sustained throughput, regression | < 5 min |
| **K: Coverage** | Close all CV01–CV10 holes | Meet coverage targets | < 5 min |
| **Total** | 43 tests + 13 corners | Full regression | **< 30 min** |

### 9.7 Pass/Fail Criteria

| Criterion | Requirement | Blocking? |
|-----------|-------------|-----------|
| All P0 tests (S1–S6, T1–T34 P0) pass | **100% mandatory** | Yes |
| All P1 tests pass | ≥ 95% (known waivers documented) | Partial |
| All P2 tests pass | ≥ 80% (nice-to-have) | No |
| All SVA assertions (SVA01–SVA14) | **Zero failures** | Yes |
| Zero X/Z propagation | No unknowns in functional paths | Yes |
| Line coverage | ≥ 95% | Yes |
| FSM state coverage | 100% | Yes |
| Functional coverage (CV01–CV10) | 100% | Yes |
| Regression duration | < 30 minutes (Verilator) | No (guideline) |

### 9.8 Testbench Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Testbench (tb_cortex_m0_core)       │
│                                                         │
│  ┌──────────┐   AHB-Lite    ┌──────────────────┐       │
│  │  Memory  │◄─────────────►│   DUT             │       │
│  │  Model   │  (HADDR/HRDA  │  cortex_m0_core   │       │
│  │  (ROM +  │   TA/HWDATA/  │                   │       │
│  │   RAM)   │   HREADY/     │  IRQ[N:0] ◄── IRQ │       │
│  │          │   HRESP)      │  NMI      ◄── NMI │       │
│  └──────────┘               │  DBGRQ    ◄── DBG │       │
│       │                     │  HALTED   ──►      │       │
│       │                     └──────────────────┘       │
│       │                             │                   │
│       ▼                             ▼                   │
│  ┌───────────────────────────────────────────────┐     │
│  │         Scoreboard + ISA Reference Model       │     │
│  │  Compare register + memory state per instruction│     │
│  └───────────────────────────────────────────────┘     │
│                                                         │
│  ┌───────────────────┐  ┌─────────────────────────┐    │
│  │  SVA Bindings     │  │  Coverage Collectors     │    │
│  │  (SVA01-SVA14)    │  │  (CV01-CV10 + structural)│    │
│  └───────────────────┘  └─────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 9.9 Tools & Environment

| Item | Choice | Notes |
|------|--------|-------|
| Language | SystemVerilog | TB and DUT |
| Simulator | Verilator (regression) / VCS or Questa (SVA + coverage) | Verilator for speed; VCS/Questa for formal features |
| Reference model | C/C++ ISA simulator or instruction-level reference | Compare register + memory state after each instruction |
| AHB slave model | Custom — configurable latency (0–7 wait states), error injection | Simple memory model with address-based decode |
| Test generation | Directed (P0) + constrained random (P1/P2) | Hand-written for critical paths; random for coverage closure |
