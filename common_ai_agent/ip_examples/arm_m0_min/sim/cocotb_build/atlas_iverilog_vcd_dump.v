module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("arm_m0_min.vcd");
  $dumpvars(0, arm_m0_min);
end
endmodule
