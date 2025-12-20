`timescale 1ns/1ps
// Testbench for 4‑bit timer
module timer_4bit_tb;

    reg clk;
    reg reset;
    reg enable;
    reg load;
    reg mode;
    reg [3:0] preset;
    wire [3:0] count;
    wire done;

    // Instantiate DUT
    timer_4bit uut (
        .clk(clk),
        .reset(reset),
        .enable(enable),
        .load(load),
        .mode(mode),
        .preset(preset),
        .count(count),
        .done(done)
    );

    // Clock generation: 200 MHz (5 ns period)
    always #5 clk = ~clk;

    // Test sequence
    initial begin
        $dumpfile("timer_4bit_tb.vcd");
        $dumpvars(0, timer_4bit_tb);

        // Initialize signals
        clk = 0;
        reset = 1;
        enable = 0;
        load = 0;
        mode = 0;   // uptime mode default
        preset = 4'b1010;

        // Hold reset for 2 cycles
        #20;
        reset = 0;

        // --- TEST 1: Uptime mode ---
        $display("=== TEST 1: UPTIME MODE ===");
        enable = 1;
        mode = 0;
        #100; // Count from 0 to 15 (20 cycles)

        // Reset and prepare for countdown
        enable = 0;
        load = 1;
        preset = 4'b0100; // Load 4
        #10;
        load = 0;
        #10;

        // --- TEST 2: CountDown mode ---
        $display("=== TEST 2: COUNTDOWN MODE ===");
        enable = 1;
        mode = 1;
        #100; // Count down from 4 to 0 (5 cycles)

        // --- TEST 3: Load again with different preset and restart ---
        $display("=== TEST 3: LOAD 8, COUNT DOWN AGAIN ===");
        enable = 0;
        load = 1;
        preset = 4'b1000;
        #10;
        load = 0;
        enable = 1;
        #100;

        // Finish
        $display("Simulation finished.");
        $finish;
    end

    // Monitor outputs on every clock edge
    always @(posedge clk) begin
        $display("Time: %0t | clk: %b | reset: %b | enable: %b | load: %b | mode: %b | preset: %b | count: %b | done: %b",
                 $time, clk, reset, enable, load, mode, preset, count, done);
    end

endmodule
