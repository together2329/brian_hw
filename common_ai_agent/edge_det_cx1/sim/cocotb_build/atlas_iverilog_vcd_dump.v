module atlas_iverilog_vcd_dump();
initial begin
  $dumpfile("edge_det_cx1.vcd");
  $dumpvars(0, edge_det_cx1);
end
endmodule
