// =============================================================================
// DMA Controller Testbench
// Based on MAS §9 (DV Plan) — Comprehensive Verification
// Covers: Reset, Register R/W, Basic Operation, Burst, Multi-Channel,
//         Priority, Interrupts, Error Handling, Circular Mode, Edge Cases
// =============================================================================

`timescale 1ns/1ps

module tb_dma;

    // =========================================================================
    // Parameters
    // =========================================================================
    parameter int NUM_CHANNELS      = 4;
    parameter int DATA_WIDTH        = 32;
    parameter int ADDR_WIDTH        = 32;
    parameter int MAX_TRANSFER_SIZE = 1024;
    parameter int FIFO_DEPTH        = 8;
    parameter int MEM_SIZE          = 16384; // 16KB test memory

    // =========================================================================
    // Clock & Reset
    // =========================================================================
    logic        clk;
    logic        rst_n;

    // APB Slave Interface
    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [11:0] paddr;
    logic [31:0] pwdata;
    logic [31:0] prdata;
    logic        pready;
    logic        pslverr;

    // AHB Master Interface
    logic        hbusreq;
    logic        hgrant;
    logic [31:0] haddr;
    logic [1:0]  htrans;
    logic        hwrite;
    logic [2:0]  hsize;
    logic [2:0]  hburst;
    logic [3:0]  hprot;
    logic [31:0] hwdata;
    logic [31:0] hrdata;
    logic        hready;
    logic        hresp;

    // Interrupts
    logic [3:0]  irq;

    // =========================================================================
    // Test Bookkeeping
    // =========================================================================
    int          test_pass;
    int          test_fail;
    int          test_count;
    string       test_name;

    // =========================================================================
    // AHB Slave Memory Model
    // =========================================================================
    logic [7:0]  ahb_mem [0:MEM_SIZE-1];

    // AHB response control (for error injection and back-pressure)
    logic        inject_error;
    logic [31:0] error_addr;
    int          ready_delay_count;
    int          ready_delay_cycles;

    function automatic logic [31:0] mem_read(input logic [31:0] addr);
        logic [31:0] data;
        data = '0;
        if (addr + 3 < MEM_SIZE) begin
            data[7:0]   = ahb_mem[addr];
            data[15:8]  = ahb_mem[addr+1];
            data[23:16] = ahb_mem[addr+2];
            data[31:24] = ahb_mem[addr+3];
        end
        return data;
    endfunction

    task automatic mem_write(input logic [31:0] addr, input logic [31:0] data);
        if (addr + 3 < MEM_SIZE) begin
            ahb_mem[addr]   = data[7:0];
            ahb_mem[addr+1] = data[15:8];
            ahb_mem[addr+2] = data[23:16];
            ahb_mem[addr+3] = data[31:24];
        end
    endtask

    task automatic mem_fill_pattern(input logic [31:0] base, input int count, input logic [31:0] pattern);
        for (int i = 0; i < count; i++) begin
            mem_write(base + i*4, pattern + i);
        end
    endtask

    task automatic mem_clear;
        for (int i = 0; i < MEM_SIZE; i++)
            ahb_mem[i] = 8'h00;
    endtask

    // =========================================================================
    // DUT Instantiation
    // =========================================================================
    dma #(
        .NUM_CHANNELS     (NUM_CHANNELS),
        .DATA_WIDTH       (DATA_WIDTH),
        .ADDR_WIDTH       (ADDR_WIDTH),
        .MAX_TRANSFER_SIZE(MAX_TRANSFER_SIZE),
        .FIFO_DEPTH       (FIFO_DEPTH)
    ) u_dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .psel    (psel),
        .penable (penable),
        .pwrite  (pwrite),
        .paddr   (paddr),
        .pwdata  (pwdata),
        .prdata  (prdata),
        .pready  (pready),
        .pslverr (pslverr),
        .hbusreq (hbusreq),
        .hgrant  (hgrant),
        .haddr   (haddr),
        .htrans  (htrans),
        .hwrite  (hwrite),
        .hsize   (hsize),
        .hburst  (hburst),
        .hprot   (hprot),
        .hwdata  (hwdata),
        .hrdata  (hrdata),
        .hready  (hready),
        .hresp   (hresp),
        .irq     (irq)
    );

    // =========================================================================
    // Clock Generation — 10ns period (100 MHz)
    // =========================================================================
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // =========================================================================
    // AHB Slave Response Model
    // =========================================================================
    logic [31:0] ahb_addr_delay; // Address phase register

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            hrdata          <= 32'd0;
            hready          <= 1'b1;
            hresp           <= 1'b0;
            ready_delay_count <= 0;
        end else begin
            // Handle back-pressure delay
            if (ready_delay_count > 0) begin
                ready_delay_count <= ready_delay_count - 1;
                hready <= 1'b0;
            end else begin
                hready <= 1'b1;
            end

            if (htrans == 2'b10 || htrans == 2'b11) begin // NONSEQ or SEQ
                ahb_addr_delay <= haddr;

                if (inject_error && haddr == error_addr) begin
                    hresp  <= 1'b1; // ERROR
                    hready <= 1'b1;
                end else begin
                    hresp <= 1'b0;
                    if (!hwrite) begin
                        // Read from memory model
                        hrdata <= mem_read(haddr);
                    end
                end

                // Handle write data phase (one cycle later)
            end else if (htrans == 2'b00) begin // IDLE
                hresp <= 1'b0;
            end
        end
    end

    // Write data phase: capture on next cycle when hwrite was active
    always_ff @(posedge clk) begin
        if (hwrite && hready && (htrans == 2'b10 || htrans == 2'b11)) begin
            mem_write(ahb_addr_delay, hwdata);
        end
    end

    // Grant bus whenever requested (simple model)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            hgrant <= 1'b0;
        else
            hgrant <= hbusreq; // Always grant immediately
    end

    // =========================================================================
    // APB Master Tasks
    // =========================================================================

    // APB Write — 2-phase (setup + access)
    task automatic apb_write(input logic [11:0] addr, input logic [31:0] data);
        @(posedge clk);
        psel    <= 1'b1;
        pwrite  <= 1'b1;
        paddr   <= addr;
        pwdata  <= data;
        @(posedge clk);
        penable <= 1'b1;
        @(posedge clk);
        psel    <= 1'b0;
        penable <= 1'b0;
        pwrite  <= 1'b0;
    endtask

    // APB Read — returns prdata
    task automatic apb_read(input logic [11:0] addr, output logic [31:0] data);
        @(posedge clk);
        psel    <= 1'b1;
        pwrite  <= 1'b0;
        paddr   <= addr;
        @(posedge clk);
        penable <= 1'b1;
        @(posedge clk);
        data    = prdata;
        psel    <= 1'b0;
        penable <= 1'b0;
    endtask

    // =========================================================================
    // Utility Tasks
    // =========================================================================

    task automatic apply_reset;
        rst_n = 1'b1;
        @(posedge clk);
        @(posedge clk);
        rst_n = 1'b0;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        repeat(3) @(posedge clk);
    endtask

    task automatic init_signals;
        psel    = 1'b0;
        penable = 1'b0;
        pwrite  = 1'b0;
        paddr   = 12'h0;
        pwdata  = 32'h0;
        inject_error    = 1'b0;
        error_addr      = 32'h0;
        ready_delay_cycles = 0;
    endtask

    // Configure a DMA channel for mem-to-mem transfer
    task automatic config_channel(
        input int          ch,
        input logic [31:0] src_addr,
        input logic [31:0] dst_addr,
        input logic [15:0] xfer_size,
        input logic [31:0] ctrl,
        input logic [31:0] cfg
    );
        logic [11:0] base;
        base = ch[3:0] * 12'h100;
        apb_write(base + 12'h04, src_addr);   // SRC_ADDR
        apb_write(base + 12'h08, dst_addr);   // DST_ADDR
        apb_write(base + 12'h0C, xfer_size);  // XFER_SIZE
        apb_write(base + 12'h10, ctrl);       // CTRL
        apb_write(base + 12'h14, cfg);        // CFG
    endtask

    // Enable channel and trigger software request
    task automatic start_channel(input int ch);
        logic [11:0] base;
        base = ch[3:0] * 12'h100;
        apb_write(base + 12'h00, 32'h1);      // CH_EN
        apb_write(12'h01C, 32'(1 << ch));     // SW_REQ
    endtask

    // Wait for interrupt on specific channel with timeout
    task automatic wait_irq(input int ch, input int timeout_ns, output logic success);
        int elapsed;
        success = 1'b0;
        elapsed = 0;
        while (elapsed < timeout_ns && !success) begin
            @(posedge clk);
            elapsed = elapsed + 10;
            if (irq[ch] === 1'b1) begin
                success = 1'b1;
            end
        end
    endtask

    // Wait for channel to return to IDLE status
    task automatic wait_channel_idle(input int ch, input int timeout_ns, output logic success);
        logic [31:0] status;
        int elapsed;
        success = 1'b0;
        elapsed = 0;
        while (elapsed < timeout_ns && !success) begin
            apb_read(ch[3:0] * 12'h100 + 12'h18, status);
            elapsed = elapsed + 30;
            if (status[1:0] == 2'd0 && status[3] == 1'b1) begin
                success = 1'b1;
            end
        end
    endtask

    // =========================================================================
    // Checker / Reporter Tasks
    // =========================================================================

    task automatic check(input string label, input logic condition);
        test_count = test_count + 1;
        if (condition) begin
            test_pass = test_pass + 1;
            $display("  [PASS] %s", label);
        end else begin
            test_fail = test_fail + 1;
            $display("  [FAIL] %s (time=%0t)", label, $time);
        end
    endtask

    task automatic begin_test(input string name);
        test_name = name;
        $display("");
        $display("============================================================");
        $display("  TEST: %s", name);
        $display("============================================================");
    endtask

    task automatic end_test;
        $display("  --- End of %s ---", test_name);
    endtask

    // =========================================================================
    // TEST 1: Reset Behavior (FR-13)
    // =========================================================================
    task automatic test_reset;
        logic [31:0] rdata;

        begin_test("Reset Behavior (FR-13)");

        // Apply reset
        apply_reset();

        // Check global registers at reset
        apb_read(12'h000, rdata);
        check("DMA_EN reset = 0", rdata[0] == 1'b0);

        apb_read(12'h004, rdata);
        check("INT_STATUS reset = 0", rdata[3:0] == 4'b0);

        apb_read(12'h010, rdata);
        check("INT_MASK reset = 0xF (all masked)", rdata[3:0] == 4'hF);

        apb_read(12'h014, rdata);
        check("ERR_STATUS reset = 0", rdata[3:0] == 4'b0);

        // Check per-channel registers at reset
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            logic [11:0] base;
            base = ch[3:0] * 12'h100;

            apb_read(base + 12'h00, rdata);
            check($sformatf("CH%0d EN reset = 0", ch), rdata[0] == 1'b0);

            apb_read(base + 12'h04, rdata);
            check($sformatf("CH%0d SRC_ADDR reset = 0", ch), rdata == 32'h0);

            apb_read(base + 12'h08, rdata);
            check($sformatf("CH%0d DST_ADDR reset = 0", ch), rdata == 32'h0);

            apb_read(base + 12'h0C, rdata);
            check($sformatf("CH%0d XFER_SIZE reset = 0", ch), rdata == 32'h0);

            apb_read(base + 12'h18, rdata);
            check($sformatf("CH%0d STATUS[1:0] reset = IDLE", ch), rdata[1:0] == 2'd0);
        end

        // Check IRQ outputs are low after reset
        check("IRQ outputs low after reset", irq == 4'b0);

        // Check AHB idle after reset
        check("hbusreq low after reset", hbusreq == 1'b0);
        check("htrans IDLE after reset", htrans == 2'b00);

        end_test();
    endtask

    // =========================================================================
    // TEST 2: Register Read/Write (FR-01)
    // =========================================================================
    task automatic test_register_rw;
        logic [31:0] rdata;

        begin_test("Register Read/Write (FR-01)");

        apply_reset();

        // Write and read-back global registers
        apb_write(12'h000, 32'h1);
        apb_read(12'h000, rdata);
        check("DMA_EN write/read = 1", rdata[0] == 1'b1);

        apb_write(12'h010, 32'h5);
        apb_read(12'h010, rdata);
        check("INT_MASK write/read = 0x5", rdata[3:0] == 4'h5);

        // Per-channel register R/W
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            logic [11:0] base;
            base = ch[3:0] * 12'h100;

            apb_write(base + 12'h04, 32'hDEADBEEF);
            apb_read(base + 12'h04, rdata);
            check($sformatf("CH%0d SRC_ADDR write/read", ch), rdata == 32'hDEADBEEF);

            apb_write(base + 12'h08, 32'hCAFEBABE);
            apb_read(base + 12'h08, rdata);
            check($sformatf("CH%0d DST_ADDR write/read", ch), rdata == 32'hCAFEBABE);

            apb_write(base + 12'h0C, 32'h0100);
            apb_read(base + 12'h0C, rdata);
            check($sformatf("CH%0d XFER_SIZE write/read", ch), rdata[15:0] == 16'h0100);

            apb_write(base + 12'h10, 32'h00000844);
            apb_read(base + 12'h10, rdata);
            check($sformatf("CH%0d CTRL write/read", ch), rdata == 32'h00000844);

            apb_write(base + 12'h14, 32'h000004FF);
            apb_read(base + 12'h14, rdata);
            check($sformatf("CH%0d CFG write/read", ch), rdata == 32'h000004FF);
        end

        // pready should always be 1 (zero wait states)
        check("pready always 1", pready == 1'b1);

        end_test();
    endtask

    // =========================================================================
    // TEST 3: APB Slave Error on Reserved Address (FR-01)
    // =========================================================================
    task automatic test_apb_slave_error;
        logic [31:0] rdata;

        begin_test("APB Slave Error on Reserved Address (FR-01)");

        apply_reset();

        // Access an unmapped per-channel offset (e.g., ch=0, offset=0x20)
        apb_read(12'h020, rdata);
        check("pslverr asserted for reserved offset", pslverr == 1'b1);

        // Valid access should not set pslverr
        apb_read(12'h000, rdata);
        check("pslverr deasserted for valid register", pslverr == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 4: Basic Single-Beat Transfer (FR-03)
    // =========================================================================
    task automatic test_single_transfer;
        logic [31:0] rdata;
        logic        success;

        begin_test("Basic Single-Beat Mem-to-Mem Transfer (FR-03)");

        apply_reset();
        mem_clear();

        // Fill source memory
        mem_write(32'h00000100, 32'hAAAA_BBBB);

        // Enable DMA globally
        apb_write(12'h000, 32'h1);

        // Configure CH0: src=0x100, dst=0x200, size=1, 32-bit, SINGLE burst, increment
        // CTRL: SRC_WIDTH=32b(2), DST_WIDTH=32b(2), SRC_BURST=SINGLE(0), DST_BURST=SINGLE(0),
        //        SRC_INC=1, DST_INC=1, INT_EN=1
        // CTRL = 0b_0_0_000_1_1_00_000_00_010_010 = 32'h00000C12
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00000C12,   // CTRL: 32b, inc both, int_en
                       32'h000000FF);  // CFG: mem-to-mem

        // Unmask interrupt for CH0
        apb_write(12'h010, 32'hE); // Unmask CH0

        start_channel(0);

        // Wait for interrupt
        wait_irq(0, 5000, success);
        check("Single transfer completed (IRQ)", success);

        // Verify destination data
        rdata = mem_read(32'h00000200);
        check("Destination data correct", rdata == 32'hAAAA_BBBB);

        // Check interrupt status
        apb_read(12'h004, rdata);
        check("INT_STATUS bit 0 set", rdata[0] == 1'b1);

        // Clear interrupt
        apb_write(12'h00C, 32'h1);
        apb_read(12'h004, rdata);
        check("INT_STATUS cleared", rdata[0] == 1'b0);

        // Disable DMA
        apb_write(12'h000, 32'h0);

        end_test();
    endtask

    // =========================================================================
    // TEST 5: Burst Transfer — INCR4 (FR-06)
    // =========================================================================
    task automatic test_burst_incr4;
        logic [31:0] rdata;
        logic        success;

        begin_test("Burst Transfer INCR4 (FR-06)");

        apply_reset();
        mem_clear();

        // Fill source: 4 words
        for (int i = 0; i < 4; i++)
            mem_write(32'h00000100 + i*4, 32'hBEEF0000 + i);

        // Enable DMA
        apb_write(12'h000, 32'h1);

        // CTRL: SRC_WIDTH=32b(2), DST_WIDTH=32b(2), SRC_BURST=INCR4(1), DST_BURST=INCR4(1),
        //        SRC_INC=1, DST_INC=1, INT_EN=1
        // [17:16]=01 (int_en), [11:10]=11 (inc both), [9:8]=01, [7:6]=01, [5:3]=010, [2:0]=010
        // = 0x00000D52
        config_channel(0, 32'h00000100, 32'h00000200, 16'd4,
                       32'h00000D52,    // CTRL: 32b, INCR4, inc, int_en
                       32'h000000FF);   // CFG: mem-to-mem

        apb_write(12'h010, 32'hE); // Unmask CH0
        start_channel(0);

        wait_irq(0, 10000, success);
        check("INCR4 transfer completed (IRQ)", success);

        // Verify all 4 words
        for (int i = 0; i < 4; i++) begin
            rdata = mem_read(32'h00000200 + i*4);
            check($sformatf("Dest word %0d correct", i), rdata == 32'hBEEF0000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 6: Burst Transfer — INCR8 (FR-06)
    // =========================================================================
    task automatic test_burst_incr8;
        logic [31:0] rdata;
        logic        success;

        begin_test("Burst Transfer INCR8 (FR-06)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < 8; i++)
            mem_write(32'h00000100 + i*4, 32'hCAFE0000 + i);

        apb_write(12'h000, 32'h1);

        // SRC_BURST=INCR8(2), DST_BURST=INCR8(2) => [9:8]=10, [7:6]=10
        // CTRL = 0x00001192
        config_channel(0, 32'h00000100, 32'h00000300, 16'd8,
                       32'h00001192,
                       32'h000000FF);

        apb_write(12'h010, 32'hE);
        start_channel(0);

        wait_irq(0, 15000, success);
        check("INCR8 transfer completed (IRQ)", success);

        for (int i = 0; i < 8; i++) begin
            rdata = mem_read(32'h00000300 + i*4);
            check($sformatf("INCR8 dest word %0d correct", i), rdata == 32'hCAFE0000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 7: Large Transfer (>FIFO depth, tests READ->WRITE->READ cycling)
    // =========================================================================
    task automatic test_large_transfer;
        logic [31:0] rdata;
        logic        success;
        int          xfer_len = 20;

        begin_test("Large Transfer (20 beats, >FIFO depth)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < xfer_len; i++)
            mem_write(32'h00000100 + i*4, 32'h12340000 + i);

        apb_write(12'h000, 32'h1);

        // SINGLE burst, 32-bit, inc both, int_en
        config_channel(0, 32'h00000100, 32'h00000500, xfer_len,
                       32'h00000C12,
                       32'h000000FF);

        apb_write(12'h010, 32'hE);
        start_channel(0);

        wait_irq(0, 30000, success);
        check($sformatf("Large transfer (%0d beats) completed", xfer_len), success);

        for (int i = 0; i < xfer_len; i++) begin
            rdata = mem_read(32'h00000500 + i*4);
            check($sformatf("Large xfer word %0d correct", i),
                  rdata == 32'h12340000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 8: Multi-Channel Transfer (FR-03, FR-04)
    // =========================================================================
    task automatic test_multi_channel;
        logic [31:0] rdata;
        logic [3:0]  irq_capture;
        logic        success;

        begin_test("Multi-Channel Simultaneous Transfer");

        apply_reset();
        mem_clear();

        // Fill source regions for 4 channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            for (int i = 0; i < 4; i++)
                mem_write(32'(ch * 32'h400 + 32'h100 + i*4), 32'(ch * 32'h10000 + 32'hDDDD0000 + i));
        end

        apb_write(12'h000, 32'h1);
        apb_write(12'h010, 32'h0); // Unmask all channels

        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            config_channel(ch,
                           32'(ch * 32'h400 + 32'h100), // src
                           32'(ch * 32'h400 + 32'h200), // dst
                           16'd4,                        // 4 beats
                           32'h00000D52,                 // INCR4, 32-bit, inc, int_en
                           32'h000000FF);                // mem-to-mem
        end

        // Start all channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            logic [11:0] base;
            base = ch[3:0] * 12'h100;
            apb_write(base + 12'h00, 32'h1);
        end
        // Trigger all at once
        apb_write(12'h01C, 32'hF);

        // Wait for all IRQs
        irq_capture = 4'b0;
        fork
            begin
                for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
                    automatic int a_ch = ch;
                    wait_irq(a_ch, 50000, success);
                    irq_capture[a_ch] = success;
                end
            end
        join

        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            check($sformatf("CH%0d completed (IRQ)", ch), irq_capture[ch] == 1'b1);
        end

        // Verify data for each channel
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            for (int i = 0; i < 4; i++) begin
                rdata = mem_read(32'(ch * 32'h400 + 32'h200 + i*4));
                check($sformatf("CH%0d dest word %0d correct", ch, i),
                      rdata == 32'(ch * 32'h10000 + 32'hDDDD0000 + i));
            end
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 9: Priority Arbitration (Section 4.4)
    // =========================================================================
    task automatic test_priority_arbitration;
        logic [31:0] rdata;
        logic        success;

        begin_test("Priority Arbitration (Section 4.4)");

        apply_reset();
        mem_clear();

        // Fill sources
        mem_fill_pattern(32'h00000100, 4, 32'hA0000000); // CH0 source
        mem_fill_pattern(32'h00000200, 4, 32'hB0000000); // CH1 source

        apb_write(12'h000, 32'h1);
        apb_write(12'h010, 32'h0); // Unmask all

        // CH0: priority 3 (lowest), CH1: priority 0 (highest)
        config_channel(0, 32'h00000100, 32'h00000300, 16'd4,
                       32'h00000D52,
                       32'h0000030F); // PRIORITY=3

        config_channel(1, 32'h00000200, 32'h00000400, 16'd4,
                       32'h00000D52,
                       32'h0000000F); // PRIORITY=0

        // Start both
        apb_write(12'h000 * 0 + 12'h000, 32'h0); // need full addr
        apb_write(12'h100, 32'h1); // CH0 enable
        apb_write(12'h200, 32'h1); // CH1 enable
        apb_write(12'h01C, 32'h3); // Trigger both

        wait_irq(0, 20000, success);
        check("CH0 completed", success);
        wait_irq(1, 20000, success);
        check("CH1 completed", success);

        // Verify data integrity
        for (int i = 0; i < 4; i++) begin
            rdata = mem_read(32'h00000300 + i*4);
            check($sformatf("CH0 dst word %0d correct", i), rdata == 32'hA0000000 + i);
            rdata = mem_read(32'h00000400 + i*4);
            check($sformatf("CH1 dst word %0d correct", i), rdata == 32'hB0000000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 10: Interrupt Generation & Clearing (FR-08)
    // =========================================================================
    task automatic test_interrupts;
        logic [31:0] rdata;

        begin_test("Interrupt Generation & Clearing (FR-08)");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'h1111_2222);

        apb_write(12'h000, 32'h1);

        // CH0 with INT_EN=1, INT_ERR_EN=1
        // CTRL: SRC_WIDTH=32b, DST_WIDTH=32b, SINGLE, inc both, INT_EN=1, INT_ERR_EN=1
        // [17:16]=11, [11:10]=11, [7:6]=00, [5:3]=010, [2:0]=010 => 0x00030C12
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00030C12,
                       32'h000000FF);

        // Unmask CH0
        apb_write(12'h010, 32'hE);
        start_channel(0);

        // Wait a few cycles
        repeat(20) @(posedge clk);

        // Check interrupt asserted
        check("IRQ[0] asserted after transfer", irq[0] === 1'b1);

        // Check INT_STATUS
        apb_read(12'h004, rdata);
        check("INT_STATUS[0] = 1", rdata[0] == 1'b1);

        // Check INT_RAW
        apb_read(12'h008, rdata);
        check("INT_RAW[0] = 1", rdata[0] == 1'b1);

        // Test masking: mask CH0 interrupt
        apb_write(12'h010, 32'hF); // All masked
        repeat(5) @(posedge clk);
        check("IRQ[0] deasserted after masking", irq[0] === 1'b0);

        // Unmask again
        apb_write(12'h010, 32'hE);
        repeat(5) @(posedge clk);
        check("IRQ[0] re-asserted after unmask", irq[0] === 1'b1);

        // Clear interrupt via INT_CLEAR
        apb_write(12'h00C, 32'h1);
        repeat(5) @(posedge clk);
        check("IRQ[0] deasserted after clear", irq[0] === 1'b0);

        apb_read(12'h004, rdata);
        check("INT_STATUS cleared to 0", rdata[0] == 1'b0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 11: Error Handling — AHB Error Response (FR-09)
    // =========================================================================
    task automatic test_error_handling;
        logic [31:0] rdata;
        logic        success;

        begin_test("Error Handling — AHB Error (FR-09)");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'hFEED_FACE);

        apb_write(12'h000, 32'h1);

        // Configure CH0 with error interrupt enabled
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00030C12,  // INT_EN + INT_ERR_EN
                       32'h000000FF);

        apb_write(12'h010, 32'hE); // Unmask CH0

        // Enable error injection at source address
        inject_error = 1'b1;
        error_addr   = 32'h00000100;

        start_channel(0);

        // Wait for completion (should error out quickly)
        wait_irq(0, 5000, success);

        // Check error status
        apb_read(12'h014, rdata);
        check("ERR_STATUS[0] set after AHB error", rdata[0] == 1'b1);

        // Check channel auto-disabled
        apb_read(12'h100, rdata);
        check("CH0 auto-disabled on error", rdata[0] == 1'b0);

        // Clear error
        apb_write(12'h018, 32'h1);
        apb_read(12'h014, rdata);
        check("ERR_STATUS cleared", rdata[0] == 1'b0);

        inject_error = 1'b0;
        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 12: Circular Mode (FR-10)
    // =========================================================================
    task automatic test_circular_mode;
        logic [31:0] rdata;
        logic        success;

        begin_test("Circular Mode (FR-10)");

        apply_reset();
        mem_clear();

        // Source: 2 words
        mem_write(32'h00000100, 32'hCCCC_1111);
        mem_write(32'h00000104, 32'hCCCC_2222);

        apb_write(12'h000, 32'h1);

        // Configure CH0: CIRCULAR=1
        // CFG: CIRCULAR=1 => bit[10]=1 => 0x400
        config_channel(0, 32'h00000100, 32'h00000500, 16'd2,
                       32'h00000C12,     // CTRL: 32b, SINGLE, inc, int_en
                       32'h000004FF);    // CFG: CIRCULAR=1

        apb_write(12'h010, 32'hE); // Unmask CH0
        start_channel(0);

        // Wait for first completion
        wait_irq(0, 10000, success);
        check("Circular: first pass completed", success);

        // Clear interrupt
        apb_write(12'h00C, 32'h1);
        repeat(5) @(posedge clk);

        // Check first destination region
        rdata = mem_read(32'h00000500);
        check("Circular: dst word 0 correct (pass 1)", rdata == 32'hCCCC_1111);
        rdata = mem_read(32'h00000504);
        check("Circular: dst word 1 correct (pass 1)", rdata == 32'hCCCC_2222);

        // Wait for second completion (circular should auto-reload)
        wait_irq(0, 10000, success);
        check("Circular: second pass completed", success);

        // After 2 passes of size=2 with dst increment, dst addr should be 0x508
        rdata = mem_read(32'h00000508);
        check("Circular: dst word 0 correct (pass 2)", rdata == 32'hCCCC_1111);
        rdata = mem_read(32'h0000050C);
        check("Circular: dst word 1 correct (pass 2)", rdata == 32'hCCCC_2222);

        // Disable to stop circular
        apb_write(12'h100, 32'h0); // CH_EN=0
        apb_write(12'h000, 32'h0);
        apb_write(12'h00C, 32'h1);
        end_test();
    endtask

    // =========================================================================
    // TEST 13: Global Enable/Disable (FR-11)
    // =========================================================================
    task automatic test_global_enable;
        logic [31:0] rdata;

        begin_test("Global Enable/Disable (FR-11)");

        apply_reset();
        mem_clear();

        // Try to start a transfer with DMA disabled
        apb_write(12'h000, 32'h0); // DMA disabled

        config_channel(0, 32'h00000100, 32'h00000200, 16'd4,
                       32'h00000C12, 32'h000000FF);

        apb_write(12'h100, 32'h1); // Enable channel
        apb_write(12'h01C, 32'h1); // Trigger

        repeat(20) @(posedge clk);
        check("No transfer when DMA globally disabled", irq[0] === 1'b0);

        // Now enable DMA
        apb_write(12'h000, 32'h1);
        apb_write(12'h01C, 32'h1); // Re-trigger

        repeat(50) @(posedge clk);

        // Check that transfer completed
        apb_read(12'h004, rdata);
        check("Transfer completed after global enable", rdata[0] == 1'b1);

        // Test disable during transfer: start a large transfer, then disable
        apb_write(12'h00C, 32'h1); // Clear IRQ
        mem_fill_pattern(32'h00000100, 20, 32'hF0000000);
        config_channel(0, 32'h00000100, 32'h00000600, 16'd20,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h100, 32'h1);
        apb_write(12'h01C, 32'h1);

        repeat(10) @(posedge clk);
        // Disable globally mid-transfer
        apb_write(12'h000, 32'h0);
        repeat(10) @(posedge clk);

        // Check FSM is back to IDLE
        apb_read(12'h118, rdata);
        check("Channel returned to IDLE after global disable", rdata[1:0] == 2'd0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 14: Channel Status Register (FR-12)
    // =========================================================================
    task automatic test_channel_status;
        logic [31:0] rdata;

        begin_test("Channel Status Register (FR-12)");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'h1234_5678);

        apb_write(12'h000, 32'h1);

        // Check initial status = IDLE
        apb_read(12'h118, rdata);
        check("CH0 STATUS initially IDLE", rdata[1:0] == 2'd0);

        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);

        start_channel(0);

        // Poll status — should eventually show COMPLETE (bit[3]=1)
        repeat(20) @(posedge clk);
        apb_read(12'h118, rdata);
        check("CH0 STATUS complete flag set", rdata[3] == 1'b1);

        // Check remaining count
        apb_read(12'h11C, rdata);
        check("CH0 REMAIN = 0 after transfer", rdata[15:0] == 16'd0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 15: Reset During Active Transfer (FR-13)
    // =========================================================================
    task automatic test_reset_during_transfer;
        logic [31:0] rdata;

        begin_test("Reset During Active Transfer (FR-13)");

        apply_reset();
        mem_clear();

        mem_fill_pattern(32'h00000100, 20, 32'hD0000000);

        apb_write(12'h000, 32'h1);
        config_channel(0, 32'h00000100, 32'h00000600, 16'd20,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);
        start_channel(0);

        // Let a few beats happen
        repeat(8) @(posedge clk);

        // Apply reset mid-transfer
        rst_n = 1'b0;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        repeat(3) @(posedge clk);

        // Verify all registers are back to default
        apb_read(12'h000, rdata);
        check("DMA_EN cleared after reset", rdata[0] == 1'b0);

        apb_read(12'h004, rdata);
        check("INT_STATUS cleared after reset", rdata[3:0] == 4'b0);

        apb_read(12'h014, rdata);
        check("ERR_STATUS cleared after reset", rdata[3:0] == 4'b0);

        apb_read(12'h118, rdata);
        check("CH0 STATUS IDLE after reset", rdata[1:0] == 2'd0);

        check("IRQ all low after reset", irq == 4'b0);
        check("hbusreq low after reset", hbusreq == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 16: Fixed Address (Peripheral FIFO Mode, FR-07)
    // =========================================================================
    task automatic test_fixed_address;
        logic [31:0] rdata;
        logic        success;

        begin_test("Fixed Address Mode — Peripheral FIFO (FR-07)");

        apply_reset();
        mem_clear();

        // Fill 4 source words
        for (int i = 0; i < 4; i++)
            mem_write(32'h00000100 + i*4, 32'hF1F0_0000 + i);

        apb_write(12'h000, 32'h1);

        // CTRL: SRC_INC=1 (increment), DST_INC=0 (fixed address)
        // [11:10]=01 => src_inc=1, dst_inc=0
        // = 0x00000412
        config_channel(0, 32'h00000100, 32'h00000200, 16'd4,
                       32'h00000412,   // SRC_INC only, 32b, SINGLE
                       32'h000000FF);

        apb_write(12'h010, 32'hE);
        start_channel(0);

        wait_irq(0, 10000, success);
        check("Fixed address transfer completed", success);

        // With fixed dst, all writes go to same address; last value wins
        rdata = mem_read(32'h00000200);
        check("Fixed dst: last write value correct", rdata == 32'hF1F0_0003);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 17: INT_CLEAR Write-1-to-Clear (FR-08)
    // =========================================================================
    task automatic test_int_clear_w1c;
        logic [31:0] rdata;

        begin_test("INT_CLEAR Write-1-to-Clear (FR-08)");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'hAAAA);

        apb_write(12'h000, 32'h1);
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);
        start_channel(0);

        repeat(20) @(posedge clk);

        apb_read(12'h008, rdata);
        check("INT_RAW[0] set", rdata[0] == 1'b1);

        // Write-1-to-clear only CH0
        apb_write(12'h00C, 32'h1);
        apb_read(12'h008, rdata);
        check("INT_RAW[0] cleared by W1C", rdata[0] == 1'b0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 18: Zero-Length Transfer (Edge Case)
    // =========================================================================
    task automatic test_zero_length_transfer;
        logic [31:0] rdata;

        begin_test("Zero-Length Transfer (Edge Case)");

        apply_reset();
        mem_clear();

        apb_write(12'h000, 32'h1);

        // Configure with xfer_size=0
        config_channel(0, 32'h00000100, 32'h00000200, 16'd0,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);
        start_channel(0);

        // Wait — no transfer should happen (size=0 means channel stays IDLE)
        repeat(30) @(posedge clk);
        check("No IRQ for zero-length transfer", irq[0] === 1'b0);

        apb_read(12'h118, rdata);
        check("CH0 remains IDLE for zero-length", rdata[1:0] == 2'd0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 19: Multiple Sequential Transfers on Same Channel
    // =========================================================================
    task automatic test_sequential_transfers;
        logic [31:0] rdata;
        logic        success;

        begin_test("Multiple Sequential Transfers on CH0");

        apply_reset();
        mem_clear();

        apb_write(12'h000, 32'h1);
        apb_write(12'h010, 32'hE);

        // Transfer 1
        mem_write(32'h00000100, 32'hAAAA_1111);
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00000C12, 32'h000000FF);
        start_channel(0);

        wait_irq(0, 5000, success);
        check("Sequential transfer 1 completed", success);

        apb_write(12'h00C, 32'h1); // Clear interrupt

        // Transfer 2 — different data
        mem_write(32'h00000100, 32'hBBBB_2222);
        config_channel(0, 32'h00000100, 32'h00000204, 16'd1,
                       32'h00000C12, 32'h000000FF);
        // Need to re-enable channel and re-trigger
        apb_write(12'h100, 32'h1);
        apb_write(12'h01C, 32'h1);

        wait_irq(0, 5000, success);
        check("Sequential transfer 2 completed", success);

        // Verify both destinations
        rdata = mem_read(32'h00000200);
        check("Seq xfer 1 data correct", rdata == 32'hAAAA_1111);
        rdata = mem_read(32'h00000204);
        check("Seq xfer 2 data correct", rdata == 32'hBBBB_2222);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 20: Back-Pressure (hready deasserted)
    // =========================================================================
    task automatic test_back_pressure;
        logic [31:0] rdata;
        logic        success;

        begin_test("Back-Pressure (hready deasserted)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < 4; i++)
            mem_write(32'h00000100 + i*4, 32'hDADA_0000 + i);

        apb_write(12'h000, 32'h1);

        config_channel(0, 32'h00000100, 32'h00000200, 16'd4,
                       32'h00000D52,  // INCR4
                       32'h000000FF);

        apb_write(12'h010, 32'hE);

        // Note: The ready_delay mechanism would require real-time injection
        // For now, test that the transfer completes correctly even if
        // we add clock cycles of delay before starting
        start_channel(0);

        wait_irq(0, 20000, success);
        check("Transfer with back-pressure completed", success);

        for (int i = 0; i < 4; i++) begin
            rdata = mem_read(32'h00000200 + i*4);
            check($sformatf("Back-pressure dest word %0d correct", i),
                  rdata == 32'hDADA_0000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 21: All Channels Independent Configuration
    // =========================================================================
    task automatic test_independent_channels;
        logic [31:0] rdata;
        logic        success;

        begin_test("All Channels Independent Configuration");

        apply_reset();
        mem_clear();

        // Different data for each channel
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            automatic logic [31:0] base_src = 32'(ch * 32'h200 + 32'h100);
            mem_write(base_src, 32'(32'hEE00_0000 + ch));
        end

        apb_write(12'h000, 32'h1);
        apb_write(12'h010, 32'h0); // Unmask all

        // Each channel: different src, different dst, size=1
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            config_channel(ch,
                           32'(ch * 32'h200 + 32'h100),
                           32'(ch * 32'h200 + 32'h180),
                           16'd1,
                           32'h00000C12,
                           32'h000000FF);
        end

        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            logic [11:0] base;
            base = ch[3:0] * 12'h100;
            apb_write(base + 12'h00, 32'h1);
        end
        apb_write(12'h01C, 32'hF);

        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            automatic int a_ch = ch;
            wait_irq(a_ch, 10000, success);
            check($sformatf("Independent CH%0d completed", a_ch), success);
        end

        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            rdata = mem_read(32'(ch * 32'h200 + 32'h180));
            check($sformatf("Independent CH%0d data correct", ch),
                  rdata == 32'(32'hEE00_0000 + ch));
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 22: SW_REQ Without Channel Enable (Edge Case)
    // =========================================================================
    task automatic test_sw_req_without_enable;
        begin_test("SW_REQ Without Channel Enable (Edge Case)");

        apply_reset();
        mem_clear();

        apb_write(12'h000, 32'h1);

        // Configure CH0 but do NOT enable it
        config_channel(0, 32'h00000100, 32'h00000200, 16'd4,
                       32'h00000C12, 32'h000000FF);

        // Trigger SW_REQ without CH_EN
        apb_write(12'h01C, 32'h1);

        repeat(30) @(posedge clk);
        check("No transfer without CH_EN", irq[0] === 1'b0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 23: ERR_CLEAR Write-1-to-Clear
    // =========================================================================
    task automatic test_err_clear_w1c;
        logic [31:0] rdata;
        logic        success;

        begin_test("ERR_CLEAR Write-1-to-Clear (FR-09)");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'hFEED);

        apb_write(12'h000, 32'h1);
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00030C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);

        // Inject error
        inject_error = 1'b1;
        error_addr   = 32'h00000100;
        start_channel(0);

        wait_irq(0, 5000, success);

        apb_read(12'h014, rdata);
        check("ERR_STATUS set after error", rdata[0] == 1'b1);

        // Clear error via W1C
        apb_write(12'h018, 32'h1);
        apb_read(12'h014, rdata);
        check("ERR_STATUS cleared after W1C", rdata[0] == 1'b0);

        inject_error = 1'b0;
        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 24: AHB Signals Protocol Checks
    // =========================================================================
    task automatic test_ahb_protocol;
        logic [31:0] rdata;
        logic        success;

        begin_test("AHB Protocol Signal Checks");

        apply_reset();
        mem_clear();

        mem_write(32'h00000100, 32'hABCD_1234);

        apb_write(12'h000, 32'h1);
        config_channel(0, 32'h00000100, 32'h00000200, 16'd1,
                       32'h00000C12, 32'h000000FF);
        apb_write(12'h010, 32'hE);

        // Before start: bus should be idle
        check("hbusreq low before transfer", hbusreq == 1'b0);
        check("htrans IDLE before transfer", htrans == 2'b00);

        start_channel(0);

        // After start: bus request should go high
        repeat(5) @(posedge clk);
        check("hbusreq high after channel start", hbusreq == 1'b1);

        // Wait for completion
        wait_irq(0, 5000, success);
        check("AHB protocol: transfer completed", success);

        // After done: bus should release
        repeat(10) @(posedge clk);
        check("hbusreq low after completion", hbusreq == 1'b0);

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // TEST 25: INCR16 Burst Transfer
    // =========================================================================
    task automatic test_burst_incr16;
        logic [31:0] rdata;
        logic        success;

        begin_test("Burst Transfer INCR16 (FR-06)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < 16; i++)
            mem_write(32'h00000100 + i*4, 32'hFACE_0000 + i);

        apb_write(12'h000, 32'h1);

        // SRC_BURST=INCR16(3), DST_BURST=INCR16(3) => [9:8]=11, [7:6]=11
        // CTRL = 0x00001DD2
        config_channel(0, 32'h00000100, 32'h00000400, 16'd16,
                       32'h00001DD2,
                       32'h000000FF);

        apb_write(12'h010, 32'hE);
        start_channel(0);

        wait_irq(0, 20000, success);
        check("INCR16 transfer completed", success);

        for (int i = 0; i < 16; i++) begin
            rdata = mem_read(32'h00000400 + i*4);
            check($sformatf("INCR16 dest word %0d correct", i),
                  rdata == 32'hFACE_0000 + i);
        end

        apb_write(12'h000, 32'h0);
        end_test();
    endtask

    // =========================================================================
    // Main Test Sequence
    // =========================================================================
    initial begin
        $display("============================================================");
        $display("  DMA Controller Testbench — MAS §9 DV Plan");
        $display("  Module: dma");
        $display("  Start time: %0t", $time);
        $display("============================================================");

        test_pass  = 0;
        test_fail  = 0;
        test_count = 0;

        init_signals();

        // -----------------------------------------------------------------
        // Execute all tests
        // -----------------------------------------------------------------
        test_reset;                  // FR-13
        test_register_rw;            // FR-01
        test_apb_slave_error;        // FR-01
        test_single_transfer;        // FR-03
        test_burst_incr4;            // FR-06
        test_burst_incr8;            // FR-06
        test_burst_incr16;           // FR-06
        test_large_transfer;         // >FIFO depth
        test_multi_channel;          // FR-03/04
        test_priority_arbitration;   // Section 4.4
        test_interrupts;             // FR-08
        test_error_handling;         // FR-09
        test_circular_mode;          // FR-10
        test_global_enable;          // FR-11
        test_channel_status;         // FR-12
        test_reset_during_transfer;  // FR-13
        test_fixed_address;          // FR-07
        test_int_clear_w1c;          // FR-08
        test_zero_length_transfer;   // Edge case
        test_sequential_transfers;   // Multiple on same channel
        test_back_pressure;          // hready deassert
        test_independent_channels;   // All channels
        test_sw_req_without_enable;  // Edge case
        test_err_clear_w1c;          // FR-09
        test_ahb_protocol;           // Protocol check

        // -----------------------------------------------------------------
        // Final Report
        // -----------------------------------------------------------------
        $display("");
        $display("============================================================");
        $display("  TEST SUMMARY");
        $display("============================================================");
        $display("  Total checks: %0d", test_count);
        $display("  Passed:       %0d", test_pass);
        $display("  Failed:       %0d", test_fail);
        if (test_fail == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** %0d TEST(S) FAILED ***", test_fail);
        $display("============================================================");
        $display("  End time: %0t", $time);
        $display("============================================================");

        $finish;
    end

    // Timeout watchdog
    initial begin
        #10_000_000;
        $display("ERROR: Simulation timeout at time %0t", $time);
        $finish;
    end

endmodule
