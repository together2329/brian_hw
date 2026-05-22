module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("atcuart_mini.vcd");
  $dumpvars(0, atcuart_mini);
end
endmodule
