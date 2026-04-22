# DMA RTL / Simulation Assumptions

## 1) Scope

This project implements a **single-channel memory-to-memory DMA** for RTL simulation.

- One descriptor at a time (no queue)
- Software-programmable source address, destination address, and transfer length
- Byte-addressed memory space
- 32-bit data path (4 bytes per beat)
- Simple request/response memory handshake (not AXI)

The intent is to provide a clean, deterministic reference RTL + TB environment.

---

## 2) Clock / Reset Conventions

- `clk`: primary rising-edge clock
- `rst_n`: active-low asynchronous reset input

Reset behavior:

- Control state returns to `IDLE`
- `busy` clears to `0`
- `done` clears to `0`
- `error` clears to `0`
- Internal counters/pointers clear to `0`

---

## 3) DMA Programming / Register Model (logical)

The DMA module exposes direct config signals in RTL (instead of a bus slave), but behavior maps to this register model:

| Name      | Bits  | Access | Description |
|-----------|-------|--------|-------------|
| `src_addr`| 31:0  | RW     | Source base byte address |
| `dst_addr`| 31:0  | RW     | Destination base byte address |
| `len`     | 31:0  | RW     | Number of bytes to copy |
| `start`   | 0     | WO/pulse | Start transfer when in IDLE |
| `busy`    | 0     | RO     | 1 while transfer is active |
| `done`    | 0     | RO/W1C-like via `clear_done` input | Set for one completed transfer, cleared by software/testbench |
| `error`   | 0     | RO/W1C-like via `clear_error` input | Set on illegal start/invalid length alignment/timeout checks (if enabled) |

Additional control assumptions:

- `start` is sampled in `IDLE` only.
- If `start` is asserted while `busy=1`, request is ignored and `error` is set.
- `done` is sticky until cleared by `clear_done` or reset.
- `error` is sticky until cleared by `clear_error` or reset.

---

## 4) Memory Handshake Interface

To keep RTL/testbench simple and simulator-friendly, DMA uses a lightweight split read/write handshake:

### Read channel

- `rd_req_valid` / `rd_req_ready`
- `rd_req_addr[31:0]`
- `rd_rsp_valid` / `rd_rsp_ready`
- `rd_rsp_data[31:0]`

### Write channel

- `wr_req_valid` / `wr_req_ready`
- `wr_req_addr[31:0]`
- `wr_req_data[31:0]`
- `wr_rsp_valid` / `wr_rsp_ready` (single-cycle write response/ack)

Protocol assumptions:

- DMA issues one read then one write per 32-bit beat.
- Only one beat in flight at a time (no outstanding queue).
- Backpressure can be applied via any `*_ready` / delayed `*_valid` response from memory model.

---

## 5) Transfer Semantics

- Transfer length unit: **bytes** (`len`)
- Supported transfer granularity: **word-aligned 32-bit beats only**
- Valid transfer requires:
  - `src_addr[1:0] == 2'b00`
  - `dst_addr[1:0] == 2'b00`
  - `len[1:0] == 2'b00`

Behavior:

1. On `start` in `IDLE`, DMA validates parameters.
2. If invalid alignment, DMA sets `error`, stays/returns `IDLE`, `busy=0`.
3. If valid and `len > 0`, DMA copies `len/4` words from `src_addr` to `dst_addr`.
4. Source and destination addresses increment by 4 bytes each completed beat.
5. When all beats complete, DMA deasserts `busy` and sets `done`.

Zero-length behavior:

- If `len == 0`, no memory traffic occurs.
- DMA immediately sets `done` (successful no-op), `busy` remains/deasserts to `0`.

Done condition:

- Beat counter reaches configured number of beats (`len/4`) and final write response is accepted.

Error condition:

- Misaligned source/destination/length on start.
- Start requested while DMA is busy.
- (Optional in TB stress) read/write response timeout if enabled by parameter.

---

## 6) Verification Intent (for upcoming TB)

Planned directed tests:

1. Basic aligned copy (nominal)
2. Zero-length start
3. Misalignment error
4. Start while busy
5. Reset during active transfer
6. Backpressure/random ready/valid stalls

Pass criteria:

- Destination memory contents match expected copied source data for successful transfers.
- `done`/`busy`/`error` flags behave per above rules.
- No unknown (`X`) in key control path after reset deassertion.
