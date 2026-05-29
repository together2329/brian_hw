module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("mctp_assembler.vcd");
  $dumpvars(0, mctp_assembler);
end
endmodule
