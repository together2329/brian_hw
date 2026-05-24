# Requirements Document — real_llm_counter_demo

## 1. Overview

The **real_llm_counter_demo** IP is an 8-bit saturating up/down counter with a
valid-ready command interface. It is intended as a simple, self-contained
demonstration block that exercises ATLAS SSOT-driven RTL generation, testbench
creation, simulation, and lint flows end-to-end.

The counter operates in a single clock domain with an active-low asynchronous
reset. All commands arrive via a simple valid-ready handshake; the sink is
always ready (no backpressure). The counter supports five commands: CLEAR,
LOAD, INC, DEC, and HOLD. Increment saturates at `8'hFF` and decrement
saturates at `8'h00`.

There are no bus interfaces, CSRs, memory arrays, interrupts, clock-domain
crossings, or multi-clock behaviors in this IP.

---

## 2. Functional Requirements

### 2.1 Clock and Reset

| ID    | Requirement |
|-------|-------------|
| FR-01 | The IP shall use a single rising-edge clock input `clk`. |
| FR-02 | The IP shall use an active-low asynchronous reset `rst_n`. When `rst_n` is LOW, the counter value shall be cleared to `8'h00` and the accepted-transaction counter shall be cleared to `32'h00000000` regardless of the clock edge. |
| FR-03 | Reset deassertion shall be synchronous to `clk`. |

### 2.2 Command Interface

| ID    | Requirement |
|-------|-------------|
| FR-04 | The IP shall accept commands through a valid-ready handshake consisting of `cmd_valid` (input), `cmd_ready` (output), and `cmd[2:0]` (input). |
| FR-05 | `cmd_ready` shall be driven HIGH at all times, indicating the sink never applies backpressure. |
| FR-06 | A command is considered **accepted** on any rising clock edge where `rst_n` is HIGH and `cmd_valid` is HIGH. |
| FR-07 | The command encoding shall be: `3'b000` = CLEAR, `3'b001` = LOAD, `3'b010` = INC, `3'b011` = DEC, `3'b100` = HOLD. Values `3'b101` through `3'b111` are reserved and shall be treated as HOLD (count unchanged). |

### 2.3 Counter Operations

| ID    | Requirement |
|-------|-------------|
| FR-08 | **CLEAR**: On an accepted CLEAR command, the counter register shall be set to `8'h00`. |
| FR-09 | **LOAD**: On an accepted LOAD command, the counter register shall be set to the value present on `load_value[7:0]`. |
| FR-10 | **INC**: On an accepted INC command, the counter register shall increment by one. If the current value is `8'hFF`, the counter shall remain at `8'hFF` (saturating increment). |
| FR-11 | **DEC**: On an accepted DEC command, the counter register shall decrement by one. If the current value is `8'h00`, the counter shall remain at `8'h00` (saturating decrement). |
| FR-12 | **HOLD**: On an accepted HOLD command (or an accepted reserved/invalid encoding), the counter register shall remain unchanged. |
| FR-13 | When `cmd_valid` is LOW on a rising clock edge, the counter register shall hold its current value. |

### 2.4 Outputs

| ID    | Requirement |
|-------|-------------|
| FR-14 | `count[7:0]` shall reflect the current value of the counter register. |
| FR-15 | `zero` shall be asserted (HIGH) when `count == 8'h00` and deasserted otherwise. This is a combinational function of the count register. |
| FR-16 | `max` shall be asserted (HIGH) when `count == 8'hFF` and deasserted otherwise. This is a combinational function of the count register. |
| FR-17 | `accepted_count[31:0]` shall be a 32-bit free-running counter that increments by one on every accepted command. It shall wrap naturally at `32'hFFFFFFFF` back to `32'h00000000`. |
| FR-18 | `status[1:0]` shall encode the category of the most recently accepted command: `2'b00` = idle/HOLD, `2'b01` = counting (INC or DEC), `2'b10` = loaded (LOAD or CLEAR). On reset it shall be `2'b10`. |

---

## 3. Non-Functional Requirements

| ID    | Requirement |
|-------|-------------|
| NFR-01 | The IP shall be synthesizable on any generic standard-cell library. |
| NFR-02 | Target operating frequency: 100 MHz (10 ns period). |
| NFR-03 | All outputs shall be registered except `zero`, `max`, and `cmd_ready`, which are combinational. |
| NFR-04 | The design shall contain no latches, no tri-state logic, and no multi-driver nets. |
| NFR-05 | The design shall be lint-clean under Verilator with zero warnings. |

---

## 4. Interface Summary

| Port             | Direction | Width | Description |
|------------------|-----------|-------|-------------|
| `clk`            | input     | 1     | System clock |
| `rst_n`          | input     | 1     | Active-low async reset |
| `cmd_valid`      | input     | 1     | Command valid |
| `cmd`            | input     | 3     | Command encoding |
| `load_value`     | input     | 8     | Load data (sampled during LOAD) |
| `cmd_ready`      | output    | 1     | Always HIGH (no backpressure) |
| `count`          | output    | 8     | Current counter value |
| `zero`           | output    | 1     | Count is zero flag |
| `max`            | output    | 1     | Count is maximum flag |
| `accepted_count` | output    | 32    | Total accepted transactions |
| `status`         | output    | 2     | Last command category |

---

## 5. Verification Goals

- All functional requirements FR-01 through FR-18 shall be verified through
  directed and random stimulus in simulation.
- Toggle coverage on `count[7:0]` and all single-bit outputs shall exceed 95%.
- Saturated INC and DEC corner cases shall be explicitly covered.
- Reset behavior shall be verified with asynchronous assertion at random
  points during active counting.
