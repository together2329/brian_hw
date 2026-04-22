`timescale 1ns/1ps

module counter_tb;
    timeunit 1ns;
    timeprecision 1ps;

    logic       clk;
    logic       rst_n;
    logic       en;
    logic [7:0] count;
    int         errors;

    counter dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .count (count)
    );

    initial clk = 1'b0;
    always #5 clk = ~clk;

    task automatic expect_count(input logic [7:0] expected, input string label);
        begin
            if (count !== expected) begin
                errors++;
                $error("%s failed: expected count=0x%0h, got 0x%0h at time %0t", label, expected, count, $time);
            end
            else begin
                $display("%s passed: count=0x%0h at time %0t", label, count, $time);
            end
        end
    endtask

    initial begin
        errors = 0;
        rst_n  = 1'b1;
        en     = 1'b0;

        // Verify active-low asynchronous reset clears immediately.
        #2;
        rst_n = 1'b0;
        #1;
        expect_count(8'h00, "asynchronous reset clears count to zero");

        // Release reset and verify counter holds when disabled.
        @(negedge clk);
        rst_n = 1'b1;
        repeat (2) begin
            @(posedge clk);
            expect_count(8'h00, "counter holds at zero while disabled");
        end

        // Verify normal up-counting when enabled.
        en = 1'b1;
        @(posedge clk);
        expect_count(8'h01, "first increment");
        @(posedge clk);
        expect_count(8'h02, "second increment");
        @(posedge clk);
        expect_count(8'h03, "third increment");

        // Verify hold behavior when enable is deasserted.
        en = 1'b0;
        repeat (2) begin
            @(posedge clk);
            expect_count(8'h03, "counter holds value when disabled");
        end

        // Drive to 0xFF and verify wraparound to 0x00.
        en = 1'b1;
        repeat (252) @(posedge clk);
        expect_count(8'hFF, "reaches max count before wrap");
        @(posedge clk);
        expect_count(8'h00, "wraps from 0xFF to 0x00");

        if (errors == 0)
            $display("TEST PASSED: all counter checks succeeded");
        else
            $display("TEST FAILED: %0d counter checks failed", errors);

        $finish;
    end

endmodule
