module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("timer.vcd");
  $dumpvars(0, timer);
end
endmodule
