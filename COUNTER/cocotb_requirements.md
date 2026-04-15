# Cocotb Environment Requirements for DMA Verification

## Simulator & Tooling
- Primary HDL simulator: Icarus Verilog 12.0 (existing flow produces `sim/dma_tb` vvp).
- Cocotb must support the chosen simulator (Icarus or alternative such as Verilator). Ensure Python env has matching cocotb package and simulator libraries.

## Design Under Test (DUT)
- Top module: `dma` (rtl/dma.sv) with parameters `ADDR_WIDTH=32`, `DATA_WIDTH=512`, `LEN_WIDTH=16`.
- Interfaces:
  - Control: `start`, `src_addr`, `dst_addr`, `length`, status outputs `busy`, `done`.
  - Memory bus: unified request/ready handshake with `mem_req`, `mem_write`, `mem_addr`, `mem_wdata`, `mem_rdata`, `mem_ready`.

## Supporting Models
- RAM: `ram_model.sv`, 1024 words of DATA_WIDTH bits, single-cycle ready. Need to either co-simulate RTL RAM or replace with Python memory model offering equivalent functionality.
- Clock/reset: 100 MHz clock (`#5` toggled), active-low reset held low for initial cycles.

## Stimulus/Driver Needs
- Drivers for control signals honoring word alignment (`WORD_BYTES = DATA_WIDTH/8 = 64 bytes`).
- Sequence controller to issue transfers, wait for `done`, observe `busy`.
- Ability to configure parameter overrides if testing alternate widths later.

## Data Initialization & Checking
- Equivalent functionality to SV tasks `prepare_regions` and `check_regions` with pattern options (`PAT_ZERO`, `PAT_WORD_INDEX`, `PAT_LANE_SWEEP`, `PAT_ALT_TOGGLE`).
- Need capability to write/read memory contents for verification, either via hierarchical VPI access to `ram_model.mem` or via mirrored Python-side memory that is kept consistent with DUT operations.

## Directed Scenarios to Implement
1. Test1: length=0 no-op.
2. Test2: single word copy.
3. Test3: back-to-back two-word transfers (two immediate commands).
4. Test4: medium length (8 words).
5. Test5: overlapping destination after source.
6. Test6: reverse-overlap (destination before source).
7. Test7: long burst (64 words).
8. Test8: near-boundary transfer near RAM depth limit.

## Randomized Stress
- Repeat ~20 randomized transfers with random source/dest addresses, lengths up to 32 words, random patterns, occasional overlaps.

## Reset/Done Synchronization
- Cocotb coroutines to pulse reset, generate clock, wait for `done` pulses similar to SV `wait_for_done` task.

## Logging & Reporting
- Map `$display/$fatal` semantics to cocotb logging (INFO for pass messages, ERROR for mismatches) to integrate with Python test results.

## Integration Considerations
- Provide configuration layer to select simulator, choose RAM model implementation, and toggle random regression length.
- Determine file list/build flow for cocotb (e.g., `Makefile` invoking Icarus + cocotb tests).
