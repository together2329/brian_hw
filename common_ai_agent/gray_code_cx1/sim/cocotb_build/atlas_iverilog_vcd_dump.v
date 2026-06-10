module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("gray_code_cx1.vcd");
  $dumpvars(0, gray_code_cx1);
end
endmodule
