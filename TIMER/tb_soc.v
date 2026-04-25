`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_soc
// Description: End-to-end SoC testbench. Drives AHB bus directly into soc_top.
//----------------------------------------------------------------------------

module tb_soc;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;

    // Timer addresses (base 0x0000_0000)
    localparam [31:0] TIMER_CTRL      = 32'h00000000;
    localparam [31:0] TIMER_PERIOD    = 32'h00000004;
    localparam [31:0] TIMER_PRESCALER = 32'h00000008;
    localparam [31:0] TIMER_VALUE     = 32'h0000000C;
    localparam [31:0] TIMER_STATUS    = 32'h00000010;

    // Counter addresses (base 0x0000_1000)
    localparam [31:0] COUNTER_CTRL      = 32'h00001000;
    localparam [31:0] COUNTER_COUNT_LO  = 32'h00001004;
    localparam [31:0] COUNTER_COUNT_HI  = 32'h00001008;
    localparam [31:0] COUNTER_TC_STATUS = 32'h0000100C;

    //--------------------------------------------------------------------------
    // AHB Signals
    //--------------------------------------------------------------------------
    reg         HCLK;
    reg         HRESETn;
    reg  [31:0] HADDR;
    reg  [31:0] HWDATA;
    wire [31:0] HRDATA;
    reg         HWRITE;
    reg  [1:0]  HTRANS;
    reg  [2:0]  HSIZE;
    wire        irq_timer;
    wire        irq_counter;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT
    //--------------------------------------------------------------------------
    soc_top dut (
        .HCLK        (HCLK),
        .HRESETn     (HRESETn),
        .HADDR       (HADDR),
        .HWDATA      (HWDATA),
        .HRDATA      (HRDATA),
        .HWRITE      (HWRITE),
        .HTRANS      (HTRANS),
        .HSIZE       (HSIZE),
        .irq_timer   (irq_timer),
        .irq_counter (irq_counter)
    );

    //--------------------------------------------------------------------------
    // Clock generator
    //--------------------------------------------------------------------------
    initial begin
        HCLK = 1'b0;
        forever #(CLK_PERIOD/2) HCLK = ~HCLK;
    end

    //--------------------------------------------------------------------------
    // Waveform dump
    //--------------------------------------------------------------------------
    initial begin
        $dumpfile("soc.vcd");
        $dumpvars(0, tb_soc);
    end

    //--------------------------------------------------------------------------
    // Check task
    //--------------------------------------------------------------------------
    task check;
        input expected_pass;
        input [512*8-1:0] msg;
        begin
            if (expected_pass) begin
                $display("[PASS] %0s", msg);
                tests_passed = tests_passed + 1;
            end else begin
                $display("[FAIL] %0s", msg);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Write task
    //   Address phase: cycle N (HADDR, HWDATA, HWRITE, HTRANS valid)
    //   Data phase:    cycle N+1 (wait for HREADY from bridge)
    //   Uses #1 delays to avoid race with bridge sampling on posedge.
    //--------------------------------------------------------------------------
    task ahb_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWDATA = data;
            HWRITE = 1'b1;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // Bridge: IDLE->SETUP
            HTRANS = 2'b00;   // IDLE (clear before bridge completes)
            HWRITE = 1'b0;
            @(negedge HCLK);  // Bridge: SETUP->ACCESS
            @(negedge HCLK);  // Bridge: ACCESS->IDLE (APB write happens)
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Read task
    //--------------------------------------------------------------------------
    task ahb_read;
        input  [31:0] addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWRITE = 1'b0;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // Bridge: IDLE->SETUP
            HTRANS = 2'b00;   // IDLE (clear before bridge completes)
            @(negedge HCLK);  // Bridge: SETUP->ACCESS
            @(negedge HCLK);  // Bridge: ACCESS->IDLE (APB read, HRDATA valid)
            data = HRDATA;    // Capture read data
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" SoC End-to-End Testbench Starting...");
        $display("========================================");

        // Initialize
        HRESETn = 1'b0;
        HADDR   = 32'd0;
        HWDATA  = 32'd0;
        HWRITE  = 1'b0;
        HTRANS  = 2'b00;
        HSIZE   = 3'b010;

        repeat(5) @(negedge HCLK);
        HRESETn = 1'b1;
        repeat(2) @(negedge HCLK);

        //======================================================================
        // Test 1: Reset verification
        //======================================================================
        $display("\n--- Test 1: Reset ---");

        ahb_read(TIMER_CTRL, rd_data);
        check(rd_data == 32'd0, "Reset: timer CTRL is zero");

        ahb_read(COUNTER_CTRL, rd_data);
        check(rd_data == 32'd0, "Reset: counter CTRL is zero");

        check(irq_timer == 1'b0, "Reset: timer IRQ low");
        check(irq_counter == 1'b0, "Reset: counter IRQ low");

        //======================================================================
        // Test 2: Timer through bridge
        //======================================================================
        $display("\n--- Test 2: Timer via AHB ---");

        ahb_write(TIMER_PRESCALER, 32'd1);
        ahb_write(TIMER_PERIOD, 32'd100);
        ahb_write(TIMER_CTRL, 32'h4);  // load
        @(negedge HCLK);

        ahb_read(TIMER_VALUE, rd_data);
        $display("[DEBUG] Timer VALUE after load: %0d (expected 98-100)", rd_data);
        check(rd_data >= 32'd90 && rd_data <= 32'd100, "Timer: loaded period near 100");

        // Enable and count
        ahb_write(TIMER_CTRL, 32'h1);  // enable
        repeat(20) @(negedge HCLK);
        ahb_write(TIMER_CTRL, 32'd0);  // stop

        ahb_read(TIMER_VALUE, rd_data);
        check(rd_data < 32'd100, "Timer: value decreased");

        @(negedge HCLK);

        //======================================================================
        // Test 3: Counter through bridge
        //======================================================================
        $display("\n--- Test 3: Counter via AHB ---");

        ahb_write(COUNTER_COUNT_LO, 32'd0);
        ahb_write(COUNTER_COUNT_HI, 32'd0);
        ahb_write(COUNTER_CTRL, 32'h2);  // load
        @(negedge HCLK);

        // Count up
        ahb_write(COUNTER_CTRL, 32'h5);  // enable + up_down
        repeat(20) @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'd0);  // stop

        ahb_read(COUNTER_COUNT_LO, rd_data);
        check(rd_data >= 32'd5, "Counter: counted up from 0");
        ahb_read(COUNTER_COUNT_HI, rd_data);
        $display("[DEBUG] Counter COUNT_HI: %0d (expected 0)", rd_data);
        check(rd_data == 32'd0, "Counter: high word still zero");

        @(negedge HCLK);

        //======================================================================
        // Test 4: Counter underflow + IRQ
        //======================================================================
        $display("\n--- Test 4: Counter underflow + IRQ ---");

        ahb_read(COUNTER_TC_STATUS, rd_data);  // clear sticky

        // Load 1, count down
        ahb_write(COUNTER_COUNT_LO, 32'd1);
        ahb_write(COUNTER_COUNT_HI, 32'd0);
        ahb_write(COUNTER_CTRL, 32'h2);  // load
        @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'h1);  // enable (count down)
        repeat(10) @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'd0);

        check(irq_counter == 1'b1, "Counter IRQ: asserted after underflow");

        ahb_read(COUNTER_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "Counter: tc_sticky set");

        @(negedge HCLK);

        //======================================================================
        // Summary
        //======================================================================
        $display("\n========================================");
        $display(" Tests Passed: %0d", tests_passed);
        $display(" Tests Failed: %0d", tests_failed);
        if (tests_failed == 0)
            $display(" RESULT: ALL TESTS PASSED");
        else
            $display(" RESULT: SOME TESTS FAILED");
        $display("========================================");

        $finish;
    end

endmodule
