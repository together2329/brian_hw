
module sim_dump_inst;
initial begin
    $dumpfile("gpio_pad_wave.vcd");
    $dumpvars;
end
endmodule
