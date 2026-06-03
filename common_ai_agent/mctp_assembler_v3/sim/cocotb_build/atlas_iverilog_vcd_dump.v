module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("mctp_assembler_v3.vcd");
  $dumpvars(0, mctp_assembler_v3);
end
endmodule
