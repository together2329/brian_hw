module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("atcdmac100.vcd");
  $dumpvars(0, atcdmac100);
end
endmodule
