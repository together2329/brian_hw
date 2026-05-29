module iverilog_dump();
initial begin
    $dumpfile("mctp_assembler.fst");
    $dumpvars(0, mctp_assembler);
end
endmodule
