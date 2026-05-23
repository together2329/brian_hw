module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("atlas_flow_gpio_demo.vcd");
  $dumpvars(0, atlas_flow_gpio_demo);
end
endmodule
