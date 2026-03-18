# Compilation & Simulation

## Iverilog
```bash
iverilog -g2012 -Wall -o sim tb.v dut.v    # Compile
vvp sim                                      # Run
gtkwave waveform.vcd                         # View (optional)
```

## Flags
- `-g2012`: SystemVerilog support
- `-Wall`: All warnings
- `-I <dir>`: Include path
- `-o <output>`: Output file

## Error Recovery
1. Read error line ± 2 lines
2. Fix with replace_in_file
3. Recompile
4. Max 3 attempts, then ask user
