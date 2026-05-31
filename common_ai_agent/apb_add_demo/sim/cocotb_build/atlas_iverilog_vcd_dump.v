module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("apb_add_demo.vcd");
  $dumpvars(0, apb_add_demo);
end
endmodule
