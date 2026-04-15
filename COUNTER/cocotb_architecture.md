# Cocotb Testbench Architecture Outline for DMA

## File/Directory Structure
- `sim/cocotb/Makefile`: invokes cocotb with chosen simulator (Icarus/Verilator) and includes rtl/dma.sv + ram_model.sv.
- `sim/cocotb/tests/`:
  - `test_dma.py`: top-level testcase using cocotb `@cocotb.test()`.
  - `drivers.py`: Bus driver classes (control interface, memory agent if needed).
  - `scoreboard.py`: Comparison utilities and coverage tracking.
  - `patterns.py`: Pattern generators mirroring SV helper modes.
  - `config.py`: Centralized parameters (DATA_WIDTH, Word bytes, RAM depth, random trial count).

## Core Components
1. **Clock & Reset**
   - `Clock(dut.clk, 10, units="ns")` to match 100 MHz.
   - Reset coroutine drives `rst_n` low for N cycles, then high.

2. **Control Driver**
   - Class `DMADriver` with methods `start_transfer(src_addr, dst_addr, length)` ensuring alignment.
   - Handles `dut.start`, `dut.src_addr`, `dut.dst_addr`, `dut.length`, waits for `done`.

3. **Memory Agent**
   - Option A: use RTL `ram_model` and access internal array via VPI for init/check.
   - Option B: replace with Python memory model that services bus transactions by monitoring `mem_req` signals and responding via cocotb coroutine.
   - Provide `write_region`, `read_region`, `prepare_region(pattern_mode)` APIs.

4. **Pattern Utilities**
   - Functions generating 512-bit words based on pattern enums (zero, word-index, lane-sweep, alt-toggle).
   - Reused by directed tests and random trials.

5. **Scoreboard / Monitors**
   - Monitor memory bus transactions for debugging.
   - Scoreboard compares expected destination contents against memory model after each test.
   - Logging via cocotb `logging` module to replicate `$display`/`$fatal` semantics.

6. **Test Sequencer**
   - Python coroutines implementing each directed test (Test1–Test8) plus `run_random_trials(count=20)`.
   - Use helper functions to prepare source/dest memory, issue DMA command, and check results.
   - Provide fixture to reset memory between tests.

7. **Configuration Hooks**
   - Allow overriding DATA_WIDTH/DEPTH/random trial count via environment variables or config file.
   - Provide CLI entry (Makefile variables) to select simulator and wave dumping options.

8. **Coverage Hooks (Optional)**
   - Basic coverage counters (e.g., lengths exercised, overlap types) recorded in scoreboard.
   - Option to export JSON stats after run.

## Execution Flow
1. Build: `make SIM=icarus` compiles rtl + cocotb libs.
2. Cocotb test entry resets DUT, runs directed suite sequentially, then random loop.
3. Failures raise `TestFailure` with descriptive messages.
4. Summary printed via cocotb logging; optional JUnit XML produced by cocotb.
