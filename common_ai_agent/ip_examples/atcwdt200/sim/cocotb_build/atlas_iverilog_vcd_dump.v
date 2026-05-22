module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("atcwdt200.vcd");
  $dumpvars(0, atcwdt200);
end
endmodule
