# Verilog Workflow Rules

## Design Phase
- Always read existing files before modifying (grep for port names, module hierarchy)
- Search for existing modules before creating new ones
- Keep module interfaces stable — changes propagate to all instantiation sites

## Simulation Phase
- Run simulation with `bash scripts/sim.sh <testbench.sv>`
- Check exit code: 0 = pass, non-zero = fail
- Capture waveforms with `$dumpfile`/`$dumpvars` for debugging
- Never mark simulation task complete if warnings exist

## Lint Phase
- Run lint with `bash scripts/lint.sh [file.v]`
- Fix all errors before warnings
- Common lint rules: no implicit nets, no unused ports, no width mismatch

## Benchmark Tracking
- Simulation attempts logged to `.benchmark` file
- Use `/sim` command to run simulation and log result
- Use `/lint` command to run lint check
- `/report` shows session benchmark summary

## Loop Task Protocol
- Simulation loop tasks auto-restart on failure (up to max_loop_iterations)
- exit_condition checked against last tool output — must be exact substring match
- If max iterations reached, task is auto-approved with loop_exit_reason set
