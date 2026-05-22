module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("apb_pulse_counter.vcd");
  $dumpvars(0, apb_pulse_counter);
end
endmodule
