module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("parity_gen_cx1.vcd");
  $dumpvars(0, parity_gen_cx1);
end
endmodule
