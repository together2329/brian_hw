module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("mctp_assembler_scratch.vcd");
  $dumpvars(0, mctp_assembler_scratch);
end
endmodule
