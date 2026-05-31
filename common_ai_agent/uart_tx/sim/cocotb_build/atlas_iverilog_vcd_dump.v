module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("uart_tx.vcd");
  $dumpvars(0, uart_tx);
end
endmodule
