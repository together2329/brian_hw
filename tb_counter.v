`timescale 1ns / 1ps

/**
 * Testbench for 8-bit Up Counter
 * 
 * Test cases:
 * 1. Reset functionality
 * 2. Enable control
 * 3. Counting sequence
 * 4. Overflow detection
 */

module tb_counter;

    // Inputs
    reg        clk;
    reg        rst_n;
    reg        en;

    // Outputs
    wire [7:0] count;
    wire       overflow;

    // Instantiate the Unit Under Test (UUT)
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .count(count),
        .overflow(overflow)
    );

    // Clock generation
    // 10ns period = 100MHz
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Test stimulus
    initial begin
        // Initialize inputs
        rst_n = 0;
        en    = 0;

        // Wait for global reset
        #20;

        // Test 1: Release reset and check initial values
        $display("=== Test 1: Reset Release ===");
        @(negedge clk);
        rst_n = 1;
        #1;
        if (count !== 8'h00) $display("ERROR: Count should be 0 after reset, got %h", count);
        else $display("PASS: Count is 0 after reset");
        if (overflow !== 1'b0) $display("ERROR: Overflow should be 0 after reset");
        else $display("PASS: Overflow is 0 after reset");
        repeat(5) @(negedge clk);

        // Test 2: Enable signal - counter should not increment when en=0
        $display("=== Test 2: Enable = 0 (Counter should hold) ===");
        repeat(5) @(negedge clk);
        if (count !== 8'h00) $display("ERROR: Count should still be 0 with en=0, got %h", count);
        else $display("PASS: Count holds at 0 with en=0);

        // Test 3: Enable signal - counter should increment when en=1
        $display("=== Test 3: Enable = 1 (Counter should increment) ===");
        en = 1;
        @(negedge clk);
        #1;
        if (count !== 8'h01) $display("ERROR: Count should be 1 after first increment, got %h", count);
        else $display("PASS: Count incremented to 1");
        
        // Count a few more times
        repeat(10) @(negedge clk);
        if (count !== 8'h0B) $display("ERROR: Count should be 11, got %h", count);
        else $display("PASS: Count reached 11");

        // Test 4: Disable and check hold
        $display("=== Test 4: Disable (Counter should hold again) ===");
        en = 0;
        repeat(5) @(negedge clk);
        if (count !== 8'h0B) $display("ERROR: Count should hold at 11, got %h", count);
        else $display("PASS: Count holds at 11 with en=0);

        // Test 5: Re-enable and continue counting
        $display("=== Test 5: Re-enable and continue ===");
        en = 1;
        repeat(5) @(negedge clk);
        if (count !== 8'h10) $display("ERROR: Count should be 16, got %h", count);
        else $display("PASS: Count reached 16");

        // Test 6: Test overflow - set count close to 255
        $display("=== Test 6: Overflow Detection ===");
        // Force count to 254 (close to overflow)
        en = 0;
        @(negedge clk);
        // Note: We can't directly force internal registers, so we'll just enable
        // and let it count from 16. For a complete overflow test in this simple TB,
        // we'll enable for enough cycles to reach 255 from 16
        en = 1;
        repeat(239) @(negedge clk);  // 16 + 239 = 255
        
        #1;
        if (count !== 8'hFF) $display("ERROR: Count should be 255, got %h", count);
        else $display("PASS: Count reached 255");
        
        // Next cycle should overflow and wrap to 0
        @(negedge clk);
        #1;
        if (count !== 8'h00) $display("ERROR: Count should wrap to 0 after overflow, got %h", count);
        else $display("PASS: Count wrapped to 0");
        if (overflow !== 1'b1) $display("ERROR: Overflow flag should be asserted");
        else $display("PASS: Overflow flag asserted");

        // Overflow flag should be clear next cycle
        @(negedge clk);
        #1;
        if (overflow !== 1'b0) $display("ERROR: Overflow flag should be clear next cycle");
        else $display("PASS: Overflow flag cleared");

        // Test 7: Reset during counting
        $display("=== Test 7: Reset during counting ===");
        repeat(10) @(negedge clk);
        rst_n = 0;
        @(negedge clk);
        #1;
        if (count !== 8'h00) $display("ERROR: Count should be 0 after async reset, got %h", count);
        else $display("PASS: Async reset works during counting");
        if (overflow !== 1'b0) $display("ERROR: Overflow should be 0 after reset");
        else $display("PASS: Overflow cleared by reset");

        // Release reset and finish
        rst_n = 1;
        repeat(5) @(negedge clk);

        $display("=== All Tests Complete ===");
        $display("Simulation time: %0t", $time);
        $finish;
    end

    // Timeout watchdog (prevent infinite simulation)
    initial begin
        #10000;
        $display("ERROR: Simulation timeout!");
        $finish;
    end

    // Waveform dump (for GTKWave)
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, tb_counter);
    end

endmodule
