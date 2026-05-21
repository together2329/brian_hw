module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("apb_compare.vcd");
  $dumpvars(0, apb_compare);
end
endmodule
