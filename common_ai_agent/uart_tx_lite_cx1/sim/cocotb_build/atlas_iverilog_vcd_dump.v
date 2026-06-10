module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("uart_tx_lite_cx1.vcd");
  $dumpvars(0, uart_tx_lite_cx1);
end
endmodule
