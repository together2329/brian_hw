module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("debounce_cx1.vcd");
  $dumpvars(0, debounce_cx1);
end
endmodule
