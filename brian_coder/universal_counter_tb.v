`timescale 1ns/1ps
// Testbench for universal counter
module universal_counter_tb;

    parameter W = 8;
    reg clk;
    reg rst_n;
    reg en;
    reg load;
    reg mode;
    reg auto_reload;
    reg [15:0] prescale;
    reg [W-1:0] preset;
    wire [W-1:0] count;
    wire done;

    // Instantiate 8-bit version
    universal_counter #(.WIDTH(W)) uut (
        .clk(clk), .rst_n(rst_n), .en(en), .load(load),
        .mode(mode), .auto_reload(auto_reload),
        .prescale(prescale), .preset(preset),
        .count(count), .done(done)
    );

    always #5 clk = ~clk;

    initial begin
        $dumpfile("universal_counter.vcd");
        $dumpvars(0, universal_counter_tb);
        
        // Init
        clk = 0; rst_n = 0; en = 0; load = 0; 
        mode = 1; auto_reload = 1; prescale = 2; // Count every 3 clocks
        preset = 8'h05;

        #25 rst_n = 1;
        #10 load = 1; #10 load = 0;
        
        $display("=== STARTING 8-BIT DOWN-COUNTER (PRESCALE=2) ===");
        en = 1;
        #300; // Let it count and auto-reload several times

        $display("Simulation finished.");
        $finish;
    end

    always @(posedge clk) begin
        if (en)
            $display("Time: %0t | Count: %h | Done: %b | Pre: %d", $time, count, done, uut.prescale_reg);
    end
endmodule
