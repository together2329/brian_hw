module cocotb_iverilog_dump();
initial begin
    $dumpfile("sim_build/mctp_assembler_v3_axi_wr_ingress.fst");
    $dumpvars(0, mctp_assembler_v3_axi_wr_ingress);
end
endmodule
