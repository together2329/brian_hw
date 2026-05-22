module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("cortex_m0lite.vcd");
  $dumpvars(0, cortex_m0lite);
end
endmodule
