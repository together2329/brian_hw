module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("watchdog_cx1.vcd");
  $dumpvars(0, watchdog_cx1);
end
endmodule
