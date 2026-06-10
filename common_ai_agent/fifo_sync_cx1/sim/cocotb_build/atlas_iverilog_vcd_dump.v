module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("fifo_sync_cx1.vcd");
  $dumpvars(0, fifo_sync_cx1);
end
endmodule
