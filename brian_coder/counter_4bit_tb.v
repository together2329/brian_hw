module counter_4bit_tb;

    // Signals
    reg clk;
    reg reset;
    wire [3:0] count;

    // Instantiate DUT
    counter_4bit uut (
        .clk(clk),
        .reset(reset),
        .count(count)
    );

    // Clock generation
    always #5 clk = ~clk;

    // Test sequence
    initial begin
        // Initialize signals
        clk = 0;
        reset = 1;

        // Hold reset for 2 cycles
        #20;
        reset = 0;

        // Run simulation for 32 cycles (full count cycle + extras)
        #160;

        // Finish simulation
        $finish;
    end

    // Monitor output
    always @(posedge clk) begin
        $display("Time: %0t | clk: %b | reset: %b | count: %b", $time, clk, reset, count);
    end

endmodule
