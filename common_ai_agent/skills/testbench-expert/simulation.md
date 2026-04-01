# Compilation & Simulation

> Simulator is configured via `VERILOG_SIMULATOR` env var (default: `vcs`).

## VCS (default — Synopsys commercial)
```bash
vcs -full64 -sverilog -o sim tb.sv dut.sv   # Compile
./sim                                         # Run
./sim -ucli -do wave.tcl                      # Run with waveform dump
```

### VCS Flags
- `-full64`: 64-bit compile
- `-sverilog`: SystemVerilog support
- `-q`: quiet (suppress banner)
- `+incdir+<dir>`: include path
- `-o <output>`: output binary name
- `-debug_all`: enable full debug (needed for waveform)

## Iverilog (open-source fallback — mac/CI)
```bash
iverilog -g2012 -Wall -o sim tb.v dut.v     # Compile
vvp sim                                       # Run
gtkwave waveform.vcd                          # View (optional)
```

### Iverilog Flags
- `-g2012`: SystemVerilog support
- `-Wall`: all warnings
- `-I <dir>`: include path
- `-o <output>`: output file

## Error Recovery
1. Read error line ± 2 lines
2. Fix with replace_in_file
3. Recompile
4. Max 3 attempts, then ask user
