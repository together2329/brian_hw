module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("gray_counter.vcd");
  $dumpvars(0, gray_counter);
end
endmodule
