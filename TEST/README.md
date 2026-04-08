# Counter RTL — Parameterized Up/Down Counter

A clean, synthesizable SystemVerilog counter with a self-checking testbench and portable simulation environment.

## Directory Structure

```
├── rtl/
│   └── counter.sv        # Parameterized N-bit up/down counter
├── tb/
│   └── tb_counter.sv     # Self-checking testbench (14 directed tests)
├── run_sim.sh            # Compile & simulate script (iverilog/VCS/Xcelium)
└── README.md             # This file
```

## Module Interface

### Parameters

| Name  | Type | Default | Description          |
|-------|------|---------|----------------------|
| WIDTH | int  | 8       | Counter width (bits) |

### Ports

| Port     | Direction | Width        | Description                                |
|----------|-----------|--------------|--------------------------------------------|
| `clk`    | input     | 1            | Clock                                      |
| `rst_n`  | input     | 1            | Asynchronous active-low reset              |
| `enable` | input     | 1            | Count enable (active-high)                 |
| `up_down`| input     | 1            | Direction: 1 = count up, 0 = count down   |
| `load`   | input     | 1            | Synchronous load enable (active-high)      |
| `data_in`| input     | `[WIDTH-1:0]`| Data to load                               |
| `count`  | output    | `[WIDTH-1:0]`| Current counter value                      |
| `zero`   | output    | 1            | Flag: asserted when count == 0 (combo)     |
| `overflow`| output   | 1            | Flag: pulse on rollover (max→0 or 0→max)   |

### Priority

Inputs are evaluated in this order inside `always_ff`:

1. **Reset** (`rst_n`) — highest priority, asynchronous
2. **Load** (`load`) — synchronous, overrides count
3. **Enable** (`enable`) — count up or down based on `up_down`
4. **Hold** — counter holds value when `enable = 0`

## Simulation

### Prerequisites

- **Icarus Verilog** (`iverilog`) — open source, easily installed
- OR Synopsys VCS, OR Cadence Xcelium

### Quick Start

```bash
# Auto-detect simulator and run
./run_sim.sh

# Force a specific simulator
./run_sim.sh iverilog
./run_sim.sh vcs
./run_sim.sh xcelium

# Clean build artifacts
./run_sim.sh clean
```

### Expected Output

```
==========================================================
  Counter Testbench - WIDTH=8
==========================================================

--- Test 1: Reset ---
[PASS] After reset: count=0, zero=1, overflow=0
...
--- Test 10: Zero flag with load ---
[PASS] Load zero, zero flag=1: count=0, zero=1, overflow=0

==========================================================
  TEST SUMMARY
  Total : 14
  Passed: 14
  Failed: 0
  *** ALL TESTS PASSED ***
==========================================================
```

### Test Coverage

| # | Test                     | What it verifies                           |
|---|--------------------------|--------------------------------------------|
| 1 | Reset                    | Async reset clears count, zero=1           |
| 2 | Count up                 | Increments to 5 over 5 clock cycles        |
| 3 | Count down               | Decrements from 5 to 2                     |
| 4 | Underflow detection      | 0→255 wrap with overflow pulse             |
| 5 | Load                     | Direct load of 0xA5                        |
| 6 | Load overrides enable    | Load takes priority over counting          |
| 7 | Disable                  | Counter holds with enable=0                |
| 8 | Overflow at max          | 255→0 wrap with overflow pulse             |
| 9 | Enable toggling          | Start/stop/start preserves count correctly |
|10 | Zero flag with load      | Loading zero asserts zero flag             |

### Waveform Viewing

A VCD file (`tb_counter.vcd`) is generated in the build directory. View with:

```bash
gtkwave build/tb_counter.vcd &
# or
docker run --rm -v $(pwd):/data -p 8080:8080 ghcr.io/wavedrom/wavedrom
```

## Customization

Change the counter width by modifying the `WIDTH` parameter:

```systemverilog
counter #(.WIDTH(16)) dut (...);  // 16-bit counter
```

Or override from the testbench parameter declaration.

## License

This project is provided as-is for educational and development purposes.
