// Simple testbench for simple_pwm — verifies FL-vs-RTL equivalence
`timescale 1ns / 1ps

module tb_simple_pwm;

    parameter COUNTER_WIDTH = 8;

    logic                      clk;
    logic                      rst_n;
    logic                      enable;
    logic [COUNTER_WIDTH-1:0]  duty_cycle;
    logic [COUNTER_WIDTH-1:0]  period;
    logic                      pwm_out;

    // DUT
    simple_pwm #(.COUNTER_WIDTH(COUNTER_WIDTH)) dut (
        .clk(clk), .rst_n(rst_n), .enable(enable),
        .duty_cycle(duty_cycle), .period(period), .pwm_out(pwm_out)
    );

    // Clock generation: 100MHz (10ns period)
    initial clk = 0;
    always #5 clk = ~clk;

    integer pass_count;
    integer fail_count;
    integer cycle;

    // FL model state
    reg [COUNTER_WIDTH-1:0] fl_counter;
    reg                     fl_pwm_out;

    // FL step: compute expected next pwm_out from current state, then update counter
    task fl_step;
        input en;
        input [COUNTER_WIDTH-1:0] dcy;
        input [COUNTER_WIDTH-1:0] per;
    begin
        if (!en) begin
            fl_counter = 0;
            fl_pwm_out = 0;
        end else begin
            // Output based on current counter
            fl_pwm_out = (fl_counter < dcy) ? 1'b1 : 1'b0;
            // Counter update
            if (fl_counter >= per - 1)
                fl_counter = 0;
            else
                fl_counter = fl_counter + 1;
        end
    end
    endtask

    // Reset task
    task apply_reset;
    begin
        rst_n = 0; enable = 0; duty_cycle = 0; period = 0;
        #50;
        rst_n = 1;
        @(posedge clk);
        #1;
        fl_counter = 0;
        fl_pwm_out = 0;
    end
    endtask

    // Check task
    task check;
        input [255:0] test_name;
    begin
        if (pwm_out !== fl_pwm_out) begin
            $display("[FAIL] cycle=%0d %0s: expected=%0d got=%0d fl_counter=%0d",
                     cycle, test_name, fl_pwm_out, pwm_out, fl_counter);
            fail_count = fail_count + 1;
        end else begin
            pass_count = pass_count + 1;
        end
    end
    endtask

    // Main test
    initial begin
        pass_count = 0;
        fail_count = 0;

        // ============================================================
        // SC1: Basic PWM — period=10, duty_cycle=3, 30 cycles
        // ============================================================
        $display("--- SC1: Basic PWM generation ---");
        apply_reset();
        period = 10; duty_cycle = 3; enable = 1;
        for (cycle = 0; cycle < 30; cycle = cycle + 1) begin
            fl_step(1, 3, 10);
            @(posedge clk);
            #1;
            check("SC1");
        end

        // ============================================================
        // SC2: Duty variation — duty=3 then duty=7
        // ============================================================
        $display("--- SC2: Duty cycle variation ---");
        apply_reset();
        period = 10; duty_cycle = 3; enable = 1;
        for (cycle = 0; cycle < 10; cycle = cycle + 1) begin
            fl_step(1, 3, 10);
            @(posedge clk);
            #1;
            check("SC2a:duty=3");
        end
        duty_cycle = 7;
        for (cycle = 0; cycle < 10; cycle = cycle + 1) begin
            fl_step(1, 7, 10);
            @(posedge clk);
            #1;
            check("SC2b:duty=7");
        end

        // ============================================================
        // SC3: Period rollover — period=5, duty_cycle=2, 15 cycles
        // ============================================================
        $display("--- SC3: Period rollover ---");
        apply_reset();
        period = 5; duty_cycle = 2; enable = 1;
        for (cycle = 0; cycle < 15; cycle = cycle + 1) begin
            fl_step(1, 2, 5);
            @(posedge clk);
            #1;
            check("SC3");
        end

        // ============================================================
        // SC4: Disable behavior
        // ============================================================
        $display("--- SC4: Disable behavior ---");
        apply_reset();
        period = 10; duty_cycle = 2; enable = 1;
        // Enable for 5 clocks
        for (cycle = 0; cycle < 5; cycle = cycle + 1) begin
            fl_step(1, 2, 10);
            @(posedge clk);
            #1;
            check("SC4a:enabled");
        end
        // Disable for 5 clocks
        enable = 0;
        for (cycle = 0; cycle < 5; cycle = cycle + 1) begin
            fl_step(0, 2, 10);
            @(posedge clk);
            #1;
            check("SC4b:disabled");
        end
        // Re-enable for 10 clocks
        enable = 1;
        for (cycle = 0; cycle < 10; cycle = cycle + 1) begin
            fl_step(1, 2, 10);
            @(posedge clk);
            #1;
            check("SC4c:re-enabled");
        end

        // ============================================================
        // Summary
        // ============================================================
        $display("");
        $display("========================================");
        $display("  SIM RESULTS: PASS=%0d FAIL=%0d TOTAL=%0d",
                 pass_count, fail_count, pass_count + fail_count);
        if (fail_count == 0)
            $display("  STATUS: ALL TESTS PASSED");
        else
            $display("  STATUS: %0d FAILURES DETECTED", fail_count);
        $display("========================================");

        $finish;
    end

endmodule
