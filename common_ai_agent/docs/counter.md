# Counter Module Documentation

## Overview

A parameterizable synchronous up/down counter with parallel load, enable/disable control, and overflow/underflow detection. Designed for clean synthesis and easy integration.

**File**: `rtl/counter.v`

---

## Parameters

| Name  | Default | Description                    |
|-------|---------|--------------------------------|
| WIDTH | 8       | Counter bit width (1–32 typical) |

## Ports

| Name        | Direction | Width     | Description                                      |
|-------------|-----------|-----------|--------------------------------------------------|
| `clk`       | input     | 1         | Clock (posedge active)                           |
| `rst_n`     | input     | 1         | Synchronous active-low reset                     |
| `en`        | input     | 1         | Count enable (active high)                       |
| `up_down`   | input     | 1         | Direction: `1` = count up, `0` = count down     |
| `load`      | input     | 1         | Parallel load enable (active high)               |
| `data_in`   | input     | `WIDTH`   | Parallel data input for load                     |
| `count`     | output    | `WIDTH`   | Current counter value                            |
| `overflow`  | output    | 1         | Pulse (1 cycle) when rolling over MAX → 0 (up)   |
| `underflow` | output    | 1         | Pulse (1 cycle) when rolling under 0 → MAX (down)|

---

## Functional Description

### Priority Scheme

The counter follows this priority on each rising clock edge:

```
1. Reset (rst_n = 0)    → count = 0, flags = 0    (highest)
2. Load  (load = 1)     → count = data_in, flags = 0
3. Enable (en = 1)      → count +/- 1, flags updated
4. Hold  (en = 0)       → count unchanged, flags = 0 (lowest)
```

### Count Up Mode (`up_down = 1`, `en = 1`)

- Increments `count` by 1 each clock cycle.
- When `count == MAX_VAL` (all 1s), the next cycle:
  - `overflow` pulses high for **1 clock cycle**
  - `count` wraps to 0

### Count Down Mode (`up_down = 0`, `en = 1`)

- Decrements `count` by 1 each clock cycle.
- When `count == 0`, the next cycle:
  - `underflow` pulses high for **1 clock cycle**
  - `count` wraps to MAX_VAL

### Parallel Load (`load = 1`)

- Loads `data_in` into `count` on the next clock edge.
- Clears both `overflow` and `underflow` flags.
- **Overrides** the `en` signal (load has higher priority).

### Hold (`en = 0`, `load = 0`)

- Counter value is held steady.
- Both `overflow` and `underflow` are cleared to 0.

---

## Timing Diagram

```
          ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐  ┌──┐
clk    ───┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──┘  └──

rst_n  ─────────────────────────────────────────────────────────────

en     ─────────────────────────────────────────────────────────────

up_down ────────────────────────────────────────────────────────────

load   ─────────────────────────────────────────────────────────────

count   0    1    2    3    4    5    6    7    8    9
                  (counting up)
```

---

## Testbench

**File**: `tb/counter_tb.sv`

### Test Coverage

| # | Test Case                | What's Verified                            |
|---|--------------------------|--------------------------------------------|
| 1 | Reset                    | count=0, flags=0 after reset              |
| 2 | Count Up (0→5)           | Sequential increment                      |
| 3 | Count Down (5→2)         | Sequential decrement                      |
| 4 | Hold (en=0)              | Value unchanged, flags cleared            |
| 5 | Parallel Load            | count=data_in, flags cleared              |
| 6 | Load overrides Enable    | load priority > enable                    |
| 7 | Overflow (MAX→0)         | 1-cycle overflow pulse, wrap to 0         |
| 8 | Underflow (0→MAX)        | 1-cycle underflow pulse, wrap to MAX      |
| 9 | Mid-operation Reset      | Reset clears everything during counting   |
| 10 | Continuous Count (10 cyc)| 10-cycle sustained count up               |

### Running Tests

```bash
# Compile
iverilog -g2012 -o counter_tb rtl/counter.v tb/counter_tb.sv

# Simulate
vvp counter_tb

# View waveforms
gtkwave counter_tb.vcd &
```

### Expected Output

```
=========================================================
  TEST SUMMARY: 25 PASSED, 0 FAILED
  *** ALL TESTS PASSED ***
=========================================================
```

---

## Design Metrics

| Metric              | Value  |
|---------------------|--------|
| Always blocks       | 1      |
| Assign statements   | 0      |
| Total lines (RTL)   | 68     |
| Parameters          | 1      |
| Input ports         | 6      |
| Output ports        | 3      |
| Combo logic depth   | 0 (purely synchronous) |

---

## Static Analysis Results

| Check                | Result                                              |
|----------------------|-----------------------------------------------------|
| Potential issues     | ✅ Clean (false-positive undriven warnings only)    |
| Timing paths         | ✅ No combinational paths                           |
| Optimizations        | ✅ No expensive operators                           |
| Compile (pyslang)    | ✅ No errors, no warnings                           |

---

## Directory Structure

```
project/
├── rtl/
│   └── counter.v           # Counter RTL module
├── tb/
│   └── counter_tb.sv       # SystemVerilog testbench (10 tests)
├── docs/
│   └── counter.md          # This documentation
└── Makefile                # Build/sim/clean automation
```
