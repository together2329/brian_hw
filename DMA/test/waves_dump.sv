// =============================================================================
// waves_dump.sv — Waveform dump wrapper for Icarus Verilog
//
// Included when WAVES=1 is set via the Makefile. Generates a waveform dump
// file viewable with GTKWave, Surfer, or any compatible viewer.
//
// Format selection (controlled by WAVES_FMT in Makefile):
//   WAVES_FMT=vcd  — Value Change Dump (default, universally supported)
//   WAVES_FMT=fst  — Fast Signal Trace (smaller files, requires FST support)
//
// Output: dump.vcd or dump.fst in the test work directory.
// =============================================================================

`ifdef WAVES
initial begin
    `ifdef WAVES_FST
        $dumpfile("dump.fst");
    `else
        $dumpfile("dump.vcd");
    `endif
    $dumpvars(0);
end
`endif
