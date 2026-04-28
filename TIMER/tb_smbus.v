
`timescale 1ns / 1ps

module tb_smbus;
    localparam CLK_PERIOD = 10;
    localparam CLK_DIV    = 20;

    // SMBus APB register offsets (word-aligned, PADDR[4:2])
    localparam [7:0] CTRL        = 8'h00;
    localparam [7:0] STATUS      = 8'h04;
    localparam [7:0] TX_DATA     = 8'h08;
    localparam [7:0] RX_DATA     = 8'h0C;
    localparam [7:0] CMD         = 8'h10;
    localparam [7:0] DEV_ADDR    = 8'h14;
    localparam [7:0] CLK_DIV_REG = 8'h18;

    reg         PCLK;
    reg         PRESETn;
    reg  [7:0]  PADDR;
    reg  [31:0] PWDATA;
    wire [31:0] PRDATA;
    reg         PSEL;
    reg         PENABLE;
    reg         PWRITE;

    wire        smbdat_in;
    wire        smbdat_out;
    wire        smbdat_oe;
    wire        smbclk_out;
    wire        smbclk_oe;
    wire        irq;

    // Resolved lines
    wire        smbdat_int;
    wire        smbclk_int;
    assign      smbdat_int = (smbdat_oe) ? 1'b0 : (slave_sda_drive ? 1'b0 : 1'b1);
    assign      smbclk_int = (smbclk_oe) ? 1'b0 : 1'b1;
    assign      smbdat_in  = smbdat_int;

    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    // Auto-ACK slave model (same as I3C testbench)
    reg slave_sda_drive;
    always @(posedge PCLK) begin
        if (!PRESETn)
            slave_sda_drive <= 1'b0;
        else
            slave_sda_drive <= !smbdat_oe;
    end

    smbus_apb dut (
        .PCLK        (PCLK),
        .PRESETn     (PRESETn),
        .PSEL        (PSEL),
        .PENABLE     (PENABLE),
        .PWRITE      (PWRITE),
        .PADDR       (PADDR),
        .PWDATA      (PWDATA),
        .PRDATA      (PRDATA),
        .PREADY      (),
        .PSLVERR     (),
        .smbdat_in   (smbdat_in),
        .smbdat_out  (smbdat_out),
        .smbdat_oe   (smbdat_oe),
        .smbclk_out  (smbclk_out),
        .smbclk_oe   (smbclk_oe),
        .irq         (irq)
    );

    initial begin
        PCLK = 1'b0;
        forever #(CLK_PERIOD/2) PCLK = ~PCLK;
    end

    initial begin
        $dumpfile("smbus.vcd");
        $dumpvars(0, tb_smbus);
    end

    `include "apb_tasks.vh"

    task check;
        input expected_pass;
        input [512*8-1:0] msg;
        begin
            if (expected_pass) begin
                $display("[PASS] %0s", msg);
                tests_passed = tests_passed + 1;
            end else begin
                $display("[FAIL] %0s", msg);
                $display("       Time: %0t", $time);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    task poll_irq;
        output ok;
        reg    ok;
        reg [31:0] cnt;
        begin
            ok = 1'b0;
            for (cnt = 0; cnt < 200 * CLK_DIV; cnt = cnt + 1) begin
                @(negedge PCLK);
                if (irq == 1'b1) begin
                    ok = 1'b1;
                    cnt = 32'hFFFFFFFE;
                end
            end
        end
    endtask

    initial begin
        $display("========================================");
        $display(" SMBus APB Testbench Starting...");
        $display("========================================");

        PRESETn = 1'b0; PADDR = 8'd0; PWDATA = 32'd0;
        PSEL = 1'b0; PENABLE = 1'b0; PWRITE = 1'b0;

        repeat(5) @(negedge PCLK);
        PRESETn = 1'b1;
        repeat(2) @(negedge PCLK);

        //======================================================================
        // Test 1: Reset
        //======================================================================
        $display("\n--- Test 1: Reset ---");
        apb_read(CTRL, rd_data);
        check(rd_data[3:0] == 4'b0000, "Reset: CTRL zero");
        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b0, "Reset: not busy");
        check(rd_data[1] == 1'b0, "Reset: done sticky low");
        check(rd_data[2] == 1'b0, "Reset: timeout low");
        check(rd_data[3] == 1'b0, "Reset: pec_error low");
        check(irq == 1'b0, "Reset: IRQ low");

        //======================================================================
        // Test 2: Register R/W
        //======================================================================
        $display("\n--- Test 2: Register R/W ---");
        apb_write(CLK_DIV_REG, CLK_DIV);
        apb_read(CLK_DIV_REG, rd_data);
        check(rd_data[15:0] == CLK_DIV, "CLK_DIV set");
        apb_write(DEV_ADDR, 32'h50);
        apb_read(DEV_ADDR, rd_data);
        check(rd_data[7:0] == 8'h50, "DEV_ADDR set");
        apb_write(CMD, 32'hAB);
        apb_read(CMD, rd_data);
        check(rd_data[7:0] == 8'hAB, "CMD set");
        apb_write(TX_DATA, 32'hCD);
        apb_read(TX_DATA, rd_data);
        check(rd_data[7:0] == 8'hCD, "TX_DATA set");
        // Set CTRL: enable + pec_en
        apb_write(CTRL, 32'h5);  // enable + pec_en
        apb_read(CTRL, rd_data);
        check(rd_data[3:0] == 4'b0101, "CTRL: enable + pec_en set");

        //======================================================================
        // Test 3: Write transfer with PEC
        //======================================================================
        $display("\n--- Test 3: Write transfer with PEC ---");
        apb_write(CTRL, 32'h5);  // enable + pec_en, rw=0 (write)
        apb_write(TX_DATA, 32'h3C);
        apb_write(CMD, 32'h77);
        apb_write(CTRL, 32'h7);  // enable + start + pec_en
        @(negedge PCLK);

        begin
            reg ok;
            poll_irq(ok);
            check(ok, "Wr+PEC: IRQ asserted");
        end
        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b0, "Wr+PEC: not busy");
        check(rd_data[1] == 1'b1, "Wr+PEC: done");
        check(rd_data[3] == 1'b0, "Wr+PEC: no pec_error");
        check(irq == 1'b0, "Wr+PEC: IRQ cleared");

        //======================================================================
        // Test 4: Multiple write transfers
        //======================================================================
        $display("\n--- Test 4: Multiple write transfers ---");
        begin
            reg ok;
            integer i;
            for (i = 0; i < 3; i = i + 1) begin
                apb_write(CTRL, 32'h7);  // enable + start + pec_en
                @(negedge PCLK);
                poll_irq(ok);
                apb_read(STATUS, rd_data);
                check(ok, "Multi: IRQ");
                check(rd_data[1] == 1'b1, "Multi: done");
                check(rd_data[3] == 1'b0, "Multi: no pec_error");
            end
        end

        //======================================================================
        // Test 5: Write without PEC
        //======================================================================
        $display("\n--- Test 5: Write without PEC ---");
        apb_write(CTRL, 32'h1);  // enable only, no pec_en
        apb_write(TX_DATA, 32'h55);
        apb_write(CTRL, 32'h3);  // enable + start
        @(negedge PCLK);
        begin
            reg ok;
            poll_irq(ok);
            check(ok, "WoPEC: IRQ");
        end
        apb_read(STATUS, rd_data);
        check(rd_data[1] == 1'b1, "WoPEC: done");
        check(rd_data[3] == 1'b0, "WoPEC: no pec_error");

        //======================================================================
        // Test 6: Start pulse auto-clear
        //======================================================================
        $display("\n--- Test 6: Start pulse auto-clear ---");
        apb_write(CTRL, 32'h3);
        @(negedge PCLK);
        @(negedge PCLK);
        apb_read(CTRL, rd_data);
        check(rd_data[1] == 1'b0, "Start auto-cleared");

        // Wait for that transfer
        begin
            reg ok;
            poll_irq(ok);
            apb_read(STATUS, rd_data);
        end

        //======================================================================
        // Test 7: Disabled
        //======================================================================
        $display("\n--- Test 7: Disabled ---");
        apb_write(CTRL, 32'h0);
        apb_write(CTRL, 32'h2);
        @(negedge PCLK);
        repeat(50) @(negedge PCLK);
        apb_read(STATUS, rd_data);
        check(rd_data[1] == 1'b0, "Disabled: done 0");
        check(rd_data[0] == 1'b0, "Disabled: busy 0");

        //======================================================================
        // Test 8: Read transfer (rw=1)
        //======================================================================
        $display("\n--- Test 8: Read transfer ---");
        apb_write(CTRL, 32'h9);  // enable + rw=1 (read)
        @(negedge PCLK);
        apb_write(CTRL, 32'hB);  // enable + start + rw=1
        @(negedge PCLK);
        begin
            reg ok;
            poll_irq(ok);
            check(ok, "Read: IRQ");
        end
        apb_read(STATUS, rd_data);
        check(rd_data[1] == 1'b1, "Read: done");
        apb_read(RX_DATA, rd_data);

        //======================================================================
        // Test 9: IRQ from timeout (timeout will not fire with auto-ACK slave,
        // but verify IRQ clears properly)
        //======================================================================
        $display("\n--- Test 9: IRQ clear behavior ---");
        apb_write(CTRL, 32'h7);  // enable + start + pec_en
        @(negedge PCLK);
        begin
            reg ok;
            poll_irq(ok);
            check(ok, "IRQ test: asserts");
            check(irq == 1'b1, "IRQ test: irq high");
            apb_read(STATUS, rd_data);
            check(irq == 1'b0, "IRQ test: cleared after STATUS read");
        end

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
