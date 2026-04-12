# Cortex-M0 Core — Timing & Constraints

## 1. Target Clock Frequency

| Parameter | Value | Notes |
|-----------|-------|-------|
| Target frequency | 50 MHz | Technology-independent target; representative of typical FPGA implementation |
| Clock period | 20 ns | At 50 MHz |
| Max achievable (FPGA) | Up to 100+ MHz | Platform dependent (e.g., Xilinx Artix-7, Intel Cyclone IV) |
| Max achievable (ASIC 180nm) | Up to 200 MHz | Process dependent |

> The RTL is designed to meet 50 MHz as a portable baseline.
> Higher frequencies achievable on faster technologies without RTL changes.

---

## 2. Pipeline Latency

### 2.1 Input-to-Output Latency (Single Instruction)

| Path | Cycles | Description |
|------|--------|-------------|
| Min latency (ALU instruction) | 3 cycles | Fetch → Decode → Execute (full pipeline) |
| Max latency (load with N wait states) | 3 + N cycles | Pipeline + AHB wait states |
| Max latency (multi-cycle MUL) | 3 + 32 cycles | Iterative 32-cycle multiplier (if used) |

### 2.2 Sustained Throughput (Steady State)

| Scenario | Throughput | Description |
|----------|-----------|-------------|
| Single-cycle ALU (steady) | 1 IPC | One instruction completes per cycle once pipeline is full |
| Load/Store (0 wait states) | 0.5 IPC | 2 cycles per memory operation |

---

## 3. Clock Domain Crossing (CDC)

### 3.1 CDC Paths

| Source Domain | Destination Domain | Signal | Synchronizer Type |
|---------------|-------------------|--------|-------------------|
| External (asynchronous) | HCLK | IRQ[IRQ_NUM-1:0] | 2-stage flip-flop synchronizer |
| External (asynchronous) | HCLK | NMI | 2-stage flip-flop synchronizer |
| External (asynchronous) | HCLK | DBGRQ | 2-stage flip-flop synchronizer |
| External (asynchronous) | HCLK | HRESETn | Asynchronous assert, synchronous deassert |

### 3.2 Synchronizer Details

**IRQ / NMI / DBGRQ Synchronizer:**
```
async_input ──▶ [FF1] ──▶ [FF2] ──▶ synchronized_output
                HCLK      HCLK
```
- 2-stage metastability hardening
- Adds 2-cycle latency to interrupt detection
- MTBF calculated per technology (target: >10 years at operating frequency)

**Reset Synchronizer:**
```
HRESETn ──▶ [FF1 (async assert)] ──▶ [FF2 (sync deassert)] ──▶ internal_reset_n
             HCLK                    HCLK
```
- Asynchronous assertion (immediate reset entry)
- Synchronous deassertion (avoids metastability on release)
- Reset is active-low: assertion = HRESETn goes low (async), release = HRESETn goes high (sync)

### 3.3 No-CDC Paths

All other signals (HADDR, HWDATA, HRDATA, HREADY, HRESP, HBURST, HMASTLOCK, HPROT, HSIZE, HTRANS, HWRITE, HALTED, DBGACK, EVTEXEC) are synchronous to HCLK — no CDC required.

---

## 4. Critical Path Analysis

### 4.1 Estimated Critical Paths

| Priority | Path | Description | Estimated Logic Depth |
|----------|------|-------------|----------------------|
| 1 | ALU result → flag generation → NZCV writeback | 32-bit add/sub → condition flags → register write | 3–4 LUT levels (FPGA) |
| 2 | PC + offset → branch target → HADDR mux | PC + sign-extended offset → mux with increment → AHB address | 2–3 LUT levels |
| 3 | Instruction decode → register read → ALU operand mux | Opcode decode → 2R register file → operand selection | 3–4 LUT levels |
| 4 | NVIC priority arbitration | IRQ_NUM inputs → priority compare → highest pending select | log2(IRQ_NUM) levels |
| 5 | Barrel shifter (32-bit) | Shift amount decode → 5-stage mux | 5 LUT levels |

### 4.2 Critical Path Location

The expected critical path is the **Execute stage**:
```
Register File read → ALU (32-bit add/sub) → condition code generation → APSR writeback
```

This path determines the maximum achievable clock frequency.

---

## 5. Timing Exceptions & Multicycle Paths

### 5.1 Multicycle Paths

| Path | Cycles | Condition | Description |
|------|--------|-----------|-------------|
| MUL (iterative) | Up to 32 | MUL instruction active | Iterative multiplier completes over 1–32 cycles; pipeline stalled during operation |
| AHB wait states | N+1 | HREADY=0 | External bus stall — pipeline freezes, no timing violation |
| Exception stacking | 8+ | EXC_ENTRY state | 8 push operations to memory; each may take N cycles (AHB wait states) |
| Vector fetch | 1+ | VECTOR_FETCH state | One AHB read for handler address; may take N cycles |

### 5.2 False Paths

| From | To | Reason |
|------|----|--------|
| HRESETn (async) | All registers | Reset is timing-exclusive with functional clocks |
| DBGRQ (async sync) | Debug state machine | Synchronized signal, no timing requirement to functional path |

### 5.3 No Timing Exceptions Required For

- Single-cycle ALU operations (must meet timing in 1 clock)
- Register file read/write (combinational read, synchronous write)
- AHB-Lite output signals (registered outputs, meet output timing)
- All flip-flop based internal storage

---

## 6. I/O Timing

### 6.1 Input Setup/Hold Requirements

| Signal | Setup Time | Hold Time | Notes |
|--------|-----------|-----------|-------|
| HRDATA[31:0] | Tsu (technology) | Th (technology) | Synchronous to HCLK rising edge |
| HREADY | Tsu (technology) | Th (technology) | Synchronous to HCLK rising edge |
| HRESP | Tsu (technology) | Th (technology) | Synchronous to HCLK rising edge |
| IRQ[N:0] | N/A | N/A | Asynchronous — 2-stage synchronizer |
| NMI | N/A | N/A | Asynchronous — 2-stage synchronizer |
| DBGRQ | N/A | N/A | Asynchronous — 2-stage synchronizer |

### 6.2 Output Clock-to-Q Delays

| Signal | Output Delay | Notes |
|--------|-------------|-------|
| HADDR[31:0] | Tco (technology) | Registered output |
| HWDATA[31:0] | Tco (technology) | Registered output |
| HWRITE | Tco (technology) | Registered output |
| HTRANS[1:0] | Tco (technology) | Registered output |
| HSIZE[2:0] | Tco (technology) | Registered output |
| HBURST[2:0] | Tco (technology) | Registered output |
| HPROT[3:0] | Tco (technology) | Registered output |
| HMASTLOCK | Tco (technology) | Registered output |
| HALTED | Tco (technology) | Registered output |
| DBGACK | Tco (technology) | Registered output |
| EVTEXEC | Tco (technology) | Registered output |

---

## 7. Constraints Summary

| Constraint | Value |
|-----------|-------|
| Target clock frequency | 50 MHz (20 ns period) |
| Single clock domain | HCLK only |
| Async inputs synchronized | IRQ, NMI, DBGRQ (2-stage FF) |
| Reset | Async assert, sync deassert (HRESETn) |
| Critical path | ALU execute → flag writeback |
| Multicycle paths | MUL (up to 32 cycles), exception stacking |
| False paths | Reset → functional registers |
| No PLL/DLL required | Single clock, no frequency synthesis |
