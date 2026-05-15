module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("arbiter_rr.vcd");
  $dumpvars(0, arbiter_rr);
end
endmodule
