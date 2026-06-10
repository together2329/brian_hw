module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("pwm_gen_cx1.vcd");
  $dumpvars(0, pwm_gen_cx1);
end
endmodule
