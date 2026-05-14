module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("uart_lite.vcd");
  $dumpvars(0, uart_lite);
end
endmodule
