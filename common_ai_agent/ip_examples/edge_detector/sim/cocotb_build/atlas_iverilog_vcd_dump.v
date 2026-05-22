module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("edge_detector.vcd");
  $dumpvars(0, edge_detector);
end
endmodule
