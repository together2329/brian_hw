module atlas_vcd_dump();
initial begin
  $dumpfile("/Users/brian/Desktop/Project/brian_hw/common_ai_agent/pl330realverify/sim/pl330realverify.vcd");
  $dumpvars(0, pl330realverify);
end
endmodule
