module iverilog_dump();
initial begin
    $dumpfile("pl330realverify.fst");
    $dumpvars(0, pl330realverify);
end
endmodule
