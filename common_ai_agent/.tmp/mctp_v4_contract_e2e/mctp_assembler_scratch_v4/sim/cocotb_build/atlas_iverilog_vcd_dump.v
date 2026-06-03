module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("mctp_assembler_scratch_v4.vcd");
  $dumpvars(0, mctp_assembler_scratch_v4);
end
endmodule
