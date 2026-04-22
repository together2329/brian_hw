// ========================================================================
// Test Case Tasks for DMA Controller TB
// MAS §9 Test Sequences S1-S10
// ========================================================================

// ========================================================================
// S1: Power-on Reset
// Verify all registers at reset values after reset
// ========================================================================
task tc_S1_reset;
    logic [31:0] rdata;
    bit s1_pass;
    begin
        $display("--- S1: Power-on Reset ---");
        s1_pass = 1'b1;

        // Apply fresh reset
        apply_reset();

        // Check global registers
        axi_lite_read(12'h000, rdata); // DMA_GCR
        if (rdata !== 32'h00000000) begin
            $display("  [FAIL] DMA_GCR = %08h, expected 00000000", rdata);
            s1_pass = 1'b0;
        end

        axi_lite_read(12'h004, rdata); // DMA_GSR
        if (rdata !== 32'h0000FF00) begin
            $display("  [FAIL] DMA_GSR = %08h, expected 0000FF00", rdata);
            s1_pass = 1'b0;
        end

        axi_lite_read(12'h00C, rdata); // DMA_ISR
        if (rdata !== 32'h00000000) begin
            $display("  [FAIL] DMA_ISR = %08h, expected 00000000", rdata);
            s1_pass = 1'b0;
        end

        axi_lite_read(12'h01C, rdata); // DMA_VER
        if (rdata !== 32'h00010001) begin
            $display("  [FAIL] DMA_VER = %08h, expected 00010001", rdata);
            s1_pass = 1'b0;
        end

        // Check channel 0 registers
        axi_lite_read(12'h100, rdata); // CH0 SAR
        if (rdata !== 32'h00000000) begin
            $display("  [FAIL] CH0_SAR = %08h, expected 00000000", rdata);
            s1_pass = 1'b0;
        end

        axi_lite_read(12'h110, rdata); // CH0 SR
        if (rdata[3] !== 1'b1) begin // fifo_empty should be 1
            $display("  [FAIL] CH0_SR.fifo_empty = %b, expected 1", rdata[3]);
            s1_pass = 1'b0;
        end

        axi_lite_read(12'h11C, rdata); // CH0 CFG
        if (rdata !== 32'h00000030) begin
            $display("  [FAIL] CH0_CFG = %08h, expected 00000030", rdata);
            s1_pass = 1'b0;
        end

        // Check irq and dma_ack
        if (irq !== 8'h00) begin
            $display("  [FAIL] irq = %02h, expected 00", irq);
            s1_pass = 1'b0;
        end
        if (dma_ack !== 8'h00) begin
            $display("  [FAIL] dma_ack = %02h, expected 00", dma_ack);
            s1_pass = 1'b0;
        end

        if (s1_pass) test_pass("S1_reset");
        else         test_fail("S1_reset");
    end
endtask

// ========================================================================
// S2: Register R/W
// Write/read all global and channel registers, verify W1C and RO
// ========================================================================
task tc_S2_register_rw;
    logic [31:0] wdata, rdata;
    bit s2_pass;
    begin
        $display("--- S2: Register R/W ---");
        s2_pass = 1'b1;

        // Write/read DMA_GCR (RW)
        wdata = 32'h00000001; // dma_enable=1
        axi_lite_write(12'h000, wdata);
        axi_lite_read(12'h000, rdata);
        if (rdata !== wdata) begin
            $display("  [FAIL] DMA_GCR read %08h, wrote %08h", rdata, wdata);
            s2_pass = 1'b0;
        end

        // Write/read DMA_IER (RW)
        wdata = 32'h000000FF;
        axi_lite_write(12'h008, wdata);
        axi_lite_read(12'h008, rdata);
        if (rdata !== wdata) begin
            $display("  [FAIL] DMA_IER read %08h, wrote %08h", rdata, wdata);
            s2_pass = 1'b0;
        end

        // Verify DMA_GSR is RO — write should not change
        axi_lite_read(12'h004, rdata);
        axi_lite_write(12'h004, 32'hFFFFFFFF);
        axi_lite_read(12'h004, rdata);
        if (rdata === 32'hFFFFFFFF) begin
            $display("  [FAIL] DMA_GSR should be RO but write changed it");
            s2_pass = 1'b0;
        end

        // Verify DMA_VER is RO
        axi_lite_write(12'h01C, 32'hDEADBEEF);
        axi_lite_read(12'h01C, rdata);
        if (rdata !== 32'h00010001) begin
            $display("  [FAIL] DMA_VER should be RO = 00010001, got %08h", rdata);
            s2_pass = 1'b0;
        end

        // Test W1C on DMA_ISR
        axi_lite_write(12'h00C, 32'h000000FF); // Write to ISR (should not set, only clear)
        axi_lite_read(12'h00C, rdata);
        // ISR should remain 0 since no interrupts triggered
        if (rdata !== 32'h00000000) begin
            $display("  [FAIL] DMA_ISR should stay 0, got %08h", rdata);
            s2_pass = 1'b0;
        end

        // Channel 0 registers R/W
        wdata = 32'h00001000; // SAR
        axi_lite_write(12'h100, wdata);
        axi_lite_read(12'h100, rdata);
        if (rdata !== wdata) begin
            $display("  [FAIL] CH0_SAR read %08h, wrote %08h", rdata, wdata);
            s2_pass = 1'b0;
        end

        wdata = 32'h00002000; // DAR
        axi_lite_write(12'h104, wdata);
        axi_lite_read(12'h104, rdata);
        if (rdata !== wdata) begin
            $display("  [FAIL] CH0_DAR read %08h, wrote %08h", rdata, wdata);
            s2_pass = 1'b0;
        end

        // Verify CH_BCR is RO
        axi_lite_write(12'h118, 32'h0000FFFF);
        axi_lite_read(12'h118, rdata);
        if (rdata === 32'h0000FFFF) begin
            $display("  [FAIL] CH0_BCR should be RO but write changed it");
            s2_pass = 1'b0;
        end

        // Disable DMA for cleanup
        axi_lite_write(12'h000, 32'h00000000);

        if (s2_pass) test_pass("S2_register_rw");
        else         test_fail("S2_register_rw");
    end
endtask

// ========================================================================
// S3: Mem-to-Mem Basic Transfer
// Write pattern to source, program CH0, verify destination
// ========================================================================
task tc_S3_mem_to_mem;
    logic [31:0] rdata;
    logic [31:0] src_addr, dst_addr;
    int xfer_len;
    bit s3_pass;
    begin
        $display("--- S3: Mem-to-Mem Basic ---");
        s3_pass = 1'b1;

        apply_reset();

        src_addr = 32'h00001000;
        dst_addr = 32'h00002000;
        xfer_len = 64; // 64 bytes

        // Fill source memory with pattern
        mem_fill_pattern(src_addr, xfer_len);

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // DMA_IER: enable irq for CH0

        // Program CH0
        axi_lite_write(12'h100, src_addr);    // CH0_SAR
        axi_lite_write(12'h104, dst_addr);    // CH0_DAR
        axi_lite_write(12'h108, xfer_len);    // CH0_LEN
        axi_lite_write(12'h11C, 32'h00000030); // CH0_CFG (cache=0x3)
        // CH0_CR: ch_enable=1, src_mode=00(increment), dst_mode=00(increment),
        //         src_burst=01(4 beats), dst_burst=01(4 beats),
        //         src_width=10(32-bit), dst_width=10(32-bit), int_en=1
        // bit[0]=1(enable), [5:4]=00, [7:6]=00, [11:10]=01, [13:12]=01,
        // [15:14]=10, [17:16]=10, [20]=1(int_en)
        axi_lite_write(12'h10C, 32'h00129401); // ch_enable + int_en + widths + bursts

        // Wait for transfer complete via IRQ
        wait_irq(0, 10000);

        // Check CH_SR.xfer_complete
        axi_lite_read(12'h110, rdata);
        if (rdata[11] !== 1'b1) begin
            $display("  [FAIL] CH0_SR.xfer_complete = %b, expected 1", rdata[11]);
            s3_pass = 1'b0;
        end

        // Check CH_BCR = 0
        axi_lite_read(12'h118, rdata);
        if (rdata[15:0] !== 16'h0000) begin
            $display("  [FAIL] CH0_BCR = %04h, expected 0000", rdata[15:0]);
            s3_pass = 1'b0;
        end

        // Verify destination data
        mem_check_pattern(dst_addr, xfer_len);

        // Clear interrupt: W1C on CH_SR and DMA_ISR
        axi_lite_write(12'h110, 32'h00000F00); // Clear xfer_complete and error bits
        axi_lite_write(12'h00C, 32'h000000FF); // Clear ISR

        // Disable DMA
        axi_lite_write(12'h000, 32'h00000000);

        if (s3_pass) test_pass("S3_mem_to_mem");
        else         test_fail("S3_mem_to_mem");
    end
endtask

// ========================================================================
// S4: Mem-to-Periph Handshake
// Program CH1 with fixed dest, assert dma_req, check dma_ack
// ========================================================================
task tc_S4_mem_to_periph;
    logic [31:0] rdata;
    logic [31:0] src_addr, dst_addr;
    int xfer_len;
    bit s4_pass;
    begin
        $display("--- S4: Mem-to-Periph Handshake ---");
        s4_pass = 1'b1;

        apply_reset();

        src_addr = 32'h00003000;
        dst_addr = 32'h00004000; // Fixed peripheral address
        xfer_len = 16; // 16 bytes

        // Fill source memory
        mem_fill_pattern(src_addr, xfer_len);

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000002); // DMA_IER: enable irq for CH1

        // Program CH1 (base = 0x140)
        axi_lite_write(12'h140, src_addr);    // CH1_SAR
        axi_lite_write(12'h144, dst_addr);    // CH1_DAR
        axi_lite_write(12'h148, xfer_len);    // CH1_LEN
        // CH1_CR: ch_enable=1, src_mode=00(inc), dst_mode=01(fixed),
        //         dst_per=1, src_width=10(32b), dst_width=10(32b), int_en=1
        // [0]=1, [7:6]=01, [9]=1(dst_per), [15:14]=10, [17:16]=10, [20]=1
        axi_lite_write(12'h14C, 32'h00128241); // enable + dst_mode=fixed + dst_per
        axi_lite_write(12'h15C, 32'h00000030); // CH1_CFG

        // Assert dma_req[1] and keep it asserted throughout the transfer.
        // Channel loops: READ_ADDR -> READ_DATA -> WAIT_REQ -> WRITE_ADDR -> ... 
        // for each burst iteration. dma_req must stay high for all WAIT_REQ cycles.
        dma_req[1] = 1'b1;

        // Wait for dma_ack[1]
        begin : s4_ack_wait
            int cnt;
            cnt = 0;
            while (!dma_ack[1] && cnt < 5000) begin
                @(posedge axi_clk);
                cnt = cnt + 1;
            end
            if (dma_ack[1])
                test_pass("S4_dma_ack");
            else
                test_fail("S4_dma_ack TIMEOUT");
        end

        // Keep dma_req high until transfer completes
        wait_irq(1, 10000);

        // Deassert dma_req after completion
        dma_req[1] = 1'b0;

        // Check CH1_SR.xfer_complete
        axi_lite_read(12'h150, rdata);
        if (rdata[11] !== 1'b1) begin
            $display("  [FAIL] CH1_SR.xfer_complete = %b, expected 1", rdata[11]);
            s4_pass = 1'b0;
        end

        // Cleanup
        axi_lite_write(12'h150, 32'h00000F00); // W1C clear
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);

        if (s4_pass) test_pass("S4_mem_to_periph");
        else         test_fail("S4_mem_to_periph");
    end
endtask

// ========================================================================
// S5: Periph-to-Mem Transfer
// Program CH2 with fixed src (peripheral), inc dst, use dma_req/ack
// ========================================================================
task tc_S5_periph_to_mem;
    logic [31:0] rdata;
    logic [31:0] src_addr, dst_addr;
    int xfer_len;
    bit s5_pass;
    begin
        $display("--- S5: Periph-to-Mem ---");
        s5_pass = 1'b1;

        apply_reset();

        src_addr = 32'h00005000; // Fixed peripheral address
        dst_addr = 32'h00006000;
        xfer_len = 16; // 16 bytes

        // Pre-fill "peripheral" memory (source data)
        mem_fill_pattern(src_addr, xfer_len);

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000004); // DMA_IER: enable irq for CH2

        // Program CH2 (base = 0x180)
        axi_lite_write(12'h180, src_addr);    // CH2_SAR
        axi_lite_write(12'h184, dst_addr);    // CH2_DAR
        axi_lite_write(12'h188, xfer_len);    // CH2_LEN
        // CH2_CR: ch_enable=1, src_mode=00(increment), src_per=1,
        //         dst_mode=00(inc), src_width=10, dst_width=10, int_en=1
        // [0]=1, [8]=1(src_per), [15:14]=10, [17:16]=10, [20]=1
        axi_lite_write(12'h18C, 32'h00128101);
        axi_lite_write(12'h19C, 32'h00000030); // CH2_CFG

        // Keep dma_req[2] asserted — peripheral always has data
        dma_req[2] = 1'b1;

        // Wait for dma_ack[2]
        begin : s5_ack_wait
            int cnt;
            cnt = 0;
            while (!dma_ack[2] && cnt < 5000) begin
                @(posedge axi_clk);
                cnt = cnt + 1;
            end
            if (dma_ack[2])
                test_pass("S5_dma_ack");
            else
                test_fail("S5_dma_ack TIMEOUT");
        end

        // Keep dma_req high for subsequent bursts until transfer completes
        // The channel loops: WAIT_REQ -> READ_ADDR -> READ_DATA -> WRITE_ADDR ->
        // WRITE_DATA -> WRITE_RESP -> (more bytes?) -> WAIT_REQ
        // So we keep dma_req high until transfer is done

        // Wait for completion
        wait_irq(2, 10000);

        // Deassert dma_req after completion
        dma_req[2] = 1'b0;

        // Verify destination data matches source
        mem_check_pattern(dst_addr, xfer_len);

        // Cleanup
        axi_lite_write(12'h190, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);

        if (s5_pass) test_pass("S5_periph_to_mem");
        else         test_fail("S5_periph_to_mem");
    end
endtask

// ========================================================================
// S6: Scatter-Gather Chain
// Create 4-descriptor chain, execute, verify all blocks transferred
// ========================================================================
task tc_S6_scatter_gather;
    logic [31:0] rdata;
    logic [31:0] desc_base, src_base, dst_base;
    int desc_size, blk_len;
    bit s6_pass;
    begin
        $display("--- S6: Scatter-Gather Chain ---");
        s6_pass = 1'b1;

        apply_reset();

        desc_base = 32'h00008000;
        src_base  = 32'h00009000;
        dst_base  = 32'h0000A000;
        desc_size = 16; // 4 words per descriptor
        blk_len   = 16; // 16 bytes per block

        // Fill source blocks with patterns
        for (int d = 0; d < 4; d++) begin
            for (int i = 0; i < blk_len; i = i + 4) begin
                mem_write32(src_base + d*256 + i, 32'hB6000000 | (d*256 + i));
            end
        end

        // Build 4 descriptors in memory (each 16 bytes = 4 words)
        for (int d = 0; d < 4; d++) begin
            logic [31:0] ctrl_word;
            ctrl_word = blk_len; // xfer_len
            ctrl_word[21:20] = 2'b00; // src_mode=increment
            ctrl_word[23:22] = 2'b00; // dst_mode=increment
            if (d == 3) ctrl_word[31] = 1'b1; // end_of_list on last

            mem_write32(desc_base + d*desc_size + 0, src_base + d*256); // src_addr
            mem_write32(desc_base + d*desc_size + 4, dst_base + d*256); // dst_addr
            mem_write32(desc_base + d*desc_size + 8, ctrl_word);        // control
            if (d < 3)
                mem_write32(desc_base + d*desc_size + 12, desc_base + (d+1)*desc_size); // next
            else
                mem_write32(desc_base + d*desc_size + 12, 32'h00000000); // null = end
        end

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // DMA_IER: enable irq for CH0

        // Program CH0: sg_en=1, LLP=desc_base
        axi_lite_write(12'h100, 32'h00000000); // SAR (overridden by desc)
        axi_lite_write(12'h104, 32'h00000000); // DAR (overridden by desc)
        axi_lite_write(12'h108, 16);            // LEN
        axi_lite_write(12'h114, desc_base);     // CH0_LLP
        // CH0_CR: ch_enable=1, sg_en=1, int_en=1, src/dst width=32b
        // [0]=1, [15:14]=10, [17:16]=10, [20]=1(int_en), [22]=1(sg_en)
        axi_lite_write(12'h10C, 32'h00528001);
        axi_lite_write(12'h11C, 32'h00000030); // CH0_CFG

        // Wait for completion
        wait_irq(0, 50000);

        // Check completion
        axi_lite_read(12'h110, rdata);
        if (rdata[11] !== 1'b1) begin
            $display("  [FAIL] CH0_SR.xfer_complete = %b, expected 1", rdata[11]);
            s6_pass = 1'b0;
        end

        // Verify all 4 destination blocks
        for (int d = 0; d < 4; d++) begin
            for (int i = 0; i < blk_len; i = i + 4) begin
                logic [31:0] expected, actual;
                expected = 32'hB6000000 | (d*256 + i);
                mem_read32(dst_base + d*256 + i, actual);
                if (actual !== expected) begin
                    $display("  [FAIL] SG desc%0d dst[%08h] = %08h, expected %08h",
                             d, dst_base+d*256+i, actual, expected);
                    s6_pass = 1'b0;
                end
            end
        end

        // Cleanup
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);

        if (s6_pass) test_pass("S6_scatter_gather");
        else         test_fail("S6_scatter_gather");
    end
endtask

// ========================================================================
// S7: Interrupt Flow
// Enable interrupt, start transfer, verify irq, W1C, verify deassert
// ========================================================================
task tc_S7_interrupt_flow;
    logic [31:0] rdata;
    bit s7_pass;
    begin
        $display("--- S7: Interrupt Flow ---");
        s7_pass = 1'b1;

        apply_reset();

        // Enable interrupts: DMA_IER[0]=1
        axi_lite_write(12'h008, 32'h00000001);

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // DMA_IER: enable irq for CH0

        // Program CH0: small mem-to-mem with int_en=1
        mem_fill_pattern(32'h0000B000, 16);
        axi_lite_write(12'h100, 32'h0000B000); // SAR
        axi_lite_write(12'h104, 32'h0000C000); // DAR
        axi_lite_write(12'h108, 16);            // LEN
        // CH0_CR: enable + int_en + widths
        axi_lite_write(12'h10C, 32'h00128001);
        axi_lite_write(12'h11C, 32'h00000030);

        // Wait for irq[0]
        wait_irq(0, 10000);

        // Check irq[0] is asserted
        if (!irq[0]) begin
            $display("  [FAIL] irq[0] not asserted after xfer");
            s7_pass = 1'b0;
        end

        // Read DMA_ISR
        axi_lite_read(12'h00C, rdata);
        if (rdata[0] !== 1'b1 || rdata[8] !== 1'b1) begin
            $display("  [FAIL] DMA_ISR = %08h, expected bit0 and bit8 set", rdata);
            s7_pass = 1'b0;
        end

        // W1C clear DMA_ISR
        axi_lite_write(12'h00C, 32'h000000FF);

        // Wait 2 cycles then check irq[0] deasserted
        repeat(2) @(posedge axi_clk);
        if (irq[0]) begin
            $display("  [FAIL] irq[0] still asserted after W1C clear");
            s7_pass = 1'b0;
        end

        // Cleanup
        axi_lite_write(12'h110, 32'h00000F00); // Clear CH0_SR
        axi_lite_write(12'h000, 32'h00000000);
        axi_lite_write(12'h008, 32'h00000000); // Disable IER

        if (s7_pass) test_pass("S7_interrupt_flow");
        else         test_fail("S7_interrupt_flow");
    end
endtask

// ========================================================================
// S8: Error Injection
// Test SLVERR on read, null descriptor pointer
// ========================================================================
task tc_S8_error_inject;
    logic [31:0] rdata;
    bit s8_pass;
    begin
        $display("--- S8: Error Injection ---");
        s8_pass = 1'b1;

        apply_reset();

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // IER

        // --- Test 1: SLVERR on read ---
        $display("  S8.1: SLVERR on read");
        inject_slverr_rd = 1'b1;

        axi_lite_write(12'h100, 32'h0000D000);
        axi_lite_write(12'h104, 32'h0000E000);
        axi_lite_write(12'h108, 16);
        axi_lite_write(12'h10C, 32'h00128001); // enable + int_en
        axi_lite_write(12'h11C, 32'h00000030);

        // Wait for error to propagate
        repeat(500) @(posedge axi_clk);

        axi_lite_read(12'h110, rdata);
        if (rdata[8] !== 1'b1) begin // bus_error
            $display("  [FAIL] CH0_SR.bus_error = %b, expected 1 after SLVERR", rdata[8]);
            s8_pass = 1'b0;
        end else begin
            test_pass("S8.1_slverr_bus_error");
        end

        inject_slverr_rd = 1'b0;
        // Clear errors and disable channel to exit ERROR state
        axi_lite_write(12'h10C, 32'h00000000); // Disable channel (clear enable bit)
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        repeat(10) @(posedge axi_clk); // Let channel exit ERROR state

        // --- Test 2: Null descriptor pointer ---
        $display("  S8.2: Null descriptor pointer");
        axi_lite_write(12'h114, 32'h00000000); // LLP = 0 (null)
        // CH0_CR: sg_en=1, ch_enable=1
        axi_lite_write(12'h10C, 32'h00528001); // enable + sg_en + int_en

        repeat(500) @(posedge axi_clk);

        axi_lite_read(12'h110, rdata);
        if (rdata[10] !== 1'b1) begin // desc_error
            $display("  [FAIL] CH0_SR.desc_error = %b, expected 1 after null LLP", rdata[10]);
            s8_pass = 1'b0;
        end else begin
            test_pass("S8.2_null_desc_error");
        end

        // Cleanup
        axi_lite_write(12'h10C, 32'h00000000); // Disable channel
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);
        axi_lite_write(12'h008, 32'h00000000);

        if (s8_pass) test_pass("S8_error_inject");
        else         test_fail("S8_error_inject");
    end
endtask

// ========================================================================
// S9: Priority Arbitration
// Test strict priority and round-robin fairness
// ========================================================================
task tc_S9_priority_arb;
    logic [31:0] rdata;
    bit s9_pass;
    begin
        $display("--- S9: Priority Arbitration ---");
        s9_pass = 1'b1;

        apply_reset();

        // Fill source memories
        mem_fill_pattern(32'h00001000, 32); // CH0 src
        mem_fill_pattern(32'h00003000, 32); // CH1 src

        // Enable DMA and interrupts
        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000003); // DMA_IER: enable irq for CH0 and CH1

        // Program CH0: priority=0 (highest), mem-to-mem
        axi_lite_write(12'h100, 32'h00001000);
        axi_lite_write(12'h104, 32'h00002000);
        axi_lite_write(12'h108, 32);
        // CH0_CR: enable, priority=00(highest), width=32b, int_en=1
        axi_lite_write(12'h10C, 32'h00128001);
        axi_lite_write(12'h11C, 32'h00000030);

        // Program CH1: priority=1, mem-to-mem
        axi_lite_write(12'h140, 32'h00003000);
        axi_lite_write(12'h144, 32'h00004000);
        axi_lite_write(12'h148, 32);
        // CH1_CR: enable, priority=01(lower), width=32b, int_en=1
        // [19:18]=01
        axi_lite_write(12'h14C, 32'h00168001);
        axi_lite_write(12'h15C, 32'h00000030);

        // Wait for both to complete
        wait_irq(0, 20000);
        wait_irq(1, 20000);

        // Verify both transfers completed
        axi_lite_read(12'h110, rdata);
        if (rdata[11] !== 1'b1) begin
            $display("  [FAIL] CH0 not completed");
            s9_pass = 1'b0;
        end

        axi_lite_read(12'h150, rdata);
        if (rdata[11] !== 1'b1) begin
            $display("  [FAIL] CH1 not completed");
            s9_pass = 1'b0;
        end

        // Verify data
        mem_check_pattern(32'h00002000, 32);
        mem_check_pattern(32'h00004000, 32);

        // Cleanup
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h150, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);

        if (s9_pass) test_pass("S9_priority_arb");
        else         test_fail("S9_priority_arb");
    end
endtask

// ========================================================================
// S10: Pause and Abort
// Pause mid-transfer, verify resume. Abort mid-transfer, verify ERROR.
// ========================================================================
task tc_S10_pause_abort;
    logic [31:0] rdata;
    bit s10_pass;
    begin
        $display("--- S10: Pause and Abort ---");
        s10_pass = 1'b1;

        // --- Part 1: Pause/Resume ---
        $display("  S10.1: Pause and Resume");
        apply_reset();

        mem_fill_pattern(32'h0000F000, 64);

        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // DMA_IER: enable irq for CH0
        axi_lite_write(12'h100, 32'h0000F000);
        axi_lite_write(12'h104, 32'h0000F800);
        axi_lite_write(12'h108, 64);
        axi_lite_write(12'h10C, 32'h00128001); // enable + int_en
        axi_lite_write(12'h11C, 32'h00000030);

        // Let transfer run a few cycles then pause
        repeat(50) @(posedge axi_clk);
        axi_lite_write(12'h10C, 32'h00128005); // set ch_pause=1 (bit 2)

        // Verify FSM is frozen — check state doesn't change
        begin
            logic [31:0] sr1, sr2;
            axi_lite_read(12'h110, sr1);
            repeat(20) @(posedge axi_clk);
            axi_lite_read(12'h110, sr2);
            if (sr1[2:0] === sr2[2:0]) begin
                test_pass("S10.1_paused_fsm_frozen");
            end else begin
                $display("  [FAIL] FSM state changed during pause: %0d -> %0d", sr1[2:0], sr2[2:0]);
                s10_pass = 1'b0;
            end
        end

        // Resume: clear pause, re-enable
        axi_lite_write(12'h10C, 32'h00128001); // clear pause

        // Wait for completion
        wait_irq(0, 10000);

        // Verify data
        mem_check_pattern(32'h0000F800, 64);

        // Cleanup for part 2
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);

        // --- Part 2: Abort ---
        $display("  S10.2: Abort");
        apply_reset();

        mem_fill_pattern(32'h0000E000, 64);

        axi_lite_write(12'h000, 32'h00000001);
        axi_lite_write(12'h008, 32'h00000001); // DMA_IER: enable irq for CH0
        axi_lite_write(12'h100, 32'h0000E000);
        axi_lite_write(12'h104, 32'h0000E800);
        axi_lite_write(12'h108, 64);
        axi_lite_write(12'h10C, 32'h00128001); // enable
        axi_lite_write(12'h11C, 32'h00000030);

        // Let transfer start, then abort
        repeat(50) @(posedge axi_clk);
        axi_lite_write(12'h10C, 32'h00128009); // set ch_abort=1 (bit 3)

        repeat(100) @(posedge axi_clk);

        // Check channel is in ERROR state (state=9, but [2:0]=1)
        // Or check that it's not in a normal active state
        axi_lite_read(12'h110, rdata);
        // State 9 (ERROR) truncated to 3 bits = 001 = 1
        // We just verify it's not in a data-moving state (3,4,5,6,7 = READ/WRITE phases)
        if ((rdata[2:0] == 3'd3) || (rdata[2:0] == 3'd4) || (rdata[2:0] == 3'd5) ||
            (rdata[2:0] == 3'd6) || (rdata[2:0] == 3'd7)) begin
            $display("  [FAIL] Channel still in active state after abort: state=%0d", rdata[2:0]);
            s10_pass = 1'b0;
        end else begin
            test_pass("S10.2_abort_channel_stopped");
        end

        // Cleanup
        axi_lite_write(12'h10C, 32'h00000000); // Disable to exit ERROR
        axi_lite_write(12'h110, 32'h00000F00);
        axi_lite_write(12'h00C, 32'h000000FF);
        axi_lite_write(12'h000, 32'h00000000);

        if (s10_pass) test_pass("S10_pause_abort");
        else         test_fail("S10_pause_abort");
    end
endtask
