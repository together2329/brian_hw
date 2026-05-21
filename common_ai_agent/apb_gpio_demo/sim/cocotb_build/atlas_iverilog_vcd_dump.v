module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("apb_gpio_demo.vcd");
  $dumpvars(0, apb_gpio_demo);
end
endmodule
