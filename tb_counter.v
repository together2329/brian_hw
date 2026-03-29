`timescale 1ns/1ps

module tb_counter;

    parameter WIDTH = 8;
    parameter MAX_VAL = 8'h0A; // Set small for quick test

    reg             clk;
    reg             rst_n;
    reg             enable;
    wire [WIDTH-1:0] count;

    // Instantiate the Unit Under Test (UUT)
    counter #(
        .WIDTH(WIDTH),
        .MAX_VAL(MAX_VAL)
    ) uut (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .count(count)
    );

    // Clock generation (10ns period -> 100MHz)
    initial clk = 0;
    always #5 clk = ~clk;

    initial begin
        // Dump waves for visualization
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);

        // Initialize signals
        rst_n = 0;
        enable = 0;

        // Reset sequence
        #20 rst_n = 1;

        // Test normal counting
        #10 enable = 1;
        repeat (15) @(posedge clk);
        
        // Test disable
        enable = 0;
        repeat (5) @(posedge clk);
        
        // Test re-enable
        enable = 1;
        repeat (5) @(posedge clk);

        // Test reset mid-count
        rst_n = 0;
        #10 rst_n = 1;
        repeat (5) @(posedge clk);

        $finish;
    end

    // Monitor for debug
    initial begin
        $monitor("Time=%0t ns, rst_n=%b, enable=%b, count=%h", $time, rst_n, enable, count);
    end

endmodule
