# DMA Simulation Final Results

## Final compile/run command

```bash
make -C sim clean build run | tee sim/final_run.log
```

## Outcome

- Compile completed with **no fatal errors**.
- Directed test count: **6**
- Failures: **0**
- Final status line from simulation:
  - `DMA TB RESULT: PASS`

## Directed scenarios executed

1. Basic aligned copy
2. Zero-length transfer
3. Misalignment error case
4. Start while busy (back-to-back start)
5. Reset during active transfer
6. Boundary-aligned copy near memory end

## Remaining warnings / limitations

1. Icarus emits non-synthesis warnings for `$fatal` inside `always_ff` in the memory model.
   - This is expected in simulation-only code and does not affect test execution.
2. Icarus prints `unique/unique0 qualities are ignored`.
   - Functional simulation still passes; this is a simulator capability note.
3. DMA design scope in this project is a simple single-channel, one-beat-in-flight handshake model.
   - No AXI protocol, bursts, or descriptor queue support in this version.
