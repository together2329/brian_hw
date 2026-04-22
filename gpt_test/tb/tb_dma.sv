`timescale 1ns/1ps

module tb_dma;

    localparam int MEM_BYTES = 4096;

    logic        clk;
    logic        rst_n;

    logic [31:0] src_addr;
    logic [31:0] dst_addr;
    logic [31:0] len;
    logic        start;
    logic        clear_done;
    logic        clear_error;
    logic        busy;
    logic        done;
    logic        error;

    logic        rd_req_valid;
    logic        rd_req_ready;
    logic [31:0] rd_req_addr;
    logic        rd_rsp_valid;
    logic        rd_rsp_ready;
    logic [31:0] rd_rsp_data;

    logic        wr_req_valid;
    logic        wr_req_ready;
    logic [31:0] wr_req_addr;
    logic [31:0] wr_req_data;
    logic        wr_rsp_valid;
    logic        wr_rsp_ready;

    int failures;
    int tests_run;

    dma dut (
        .clk         (clk),
        .rst_n       (rst_n),
        .src_addr    (src_addr),
        .dst_addr    (dst_addr),
        .len         (len),
        .start       (start),
        .clear_done  (clear_done),
        .clear_error (clear_error),
        .busy        (busy),
        .done        (done),
        .error       (error),
        .rd_req_valid(rd_req_valid),
        .rd_req_ready(rd_req_ready),
        .rd_req_addr (rd_req_addr),
        .rd_rsp_valid(rd_rsp_valid),
        .rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_data (rd_rsp_data),
        .wr_req_valid(wr_req_valid),
        .wr_req_ready(wr_req_ready),
        .wr_req_addr (wr_req_addr),
        .wr_req_data (wr_req_data),
        .wr_rsp_valid(wr_rsp_valid),
        .wr_rsp_ready(wr_rsp_ready)
    );

    dma_mem_model #(
        .MEM_BYTES        (MEM_BYTES),
        .RD_LATENCY_CYCLES(2),
        .WR_LATENCY_CYCLES(1),
        .USE_STALLS       (1),
        .STALL_DIVISOR    (4)
    ) mem0 (
        .clk         (clk),
        .rst_n       (rst_n),
        .rd_req_valid(rd_req_valid),
        .rd_req_ready(rd_req_ready),
        .rd_req_addr (rd_req_addr),
        .rd_rsp_valid(rd_rsp_valid),
        .rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_data (rd_rsp_data),
        .wr_req_valid(wr_req_valid),
        .wr_req_ready(wr_req_ready),
        .wr_req_addr (wr_req_addr),
        .wr_req_data (wr_req_data),
        .wr_rsp_valid(wr_rsp_valid),
        .wr_rsp_ready(wr_rsp_ready)
    );

    // 100MHz clock
    initial clk = 1'b0;
    always #5 clk = ~clk;

    // Optional waveform dump: enable with +WAVES
    initial begin
        if ($test$plusargs("WAVES")) begin
            $display("[TB] Wave dump enabled: dma_tb.vcd");
            $dumpfile("dma_tb.vcd");
            $dumpvars(0, tb_dma);
        end
    end

    task automatic tick(input int cycles);
        int i;
        begin
            for (i = 0; i < cycles; i++) begin
                @(posedge clk);
            end
        end
    endtask

    task automatic check(input logic cond, input string msg);
        begin
            if (!cond) begin
                failures++;
                $display("[FAIL] %s", msg);
            end else begin
                $display("[ OK ] %s", msg);
            end
        end
    endtask

    task automatic clear_status_flags();
        begin
            clear_done  <= 1'b1;
            clear_error <= 1'b1;
            @(posedge clk);
            clear_done  <= 1'b0;
            clear_error <= 1'b0;
        end
    endtask

    task automatic start_dma(
        input logic [31:0] src,
        input logic [31:0] dst,
        input logic [31:0] bytes
    );
        begin
            src_addr <= src;
            dst_addr <= dst;
            len      <= bytes;
            start    <= 1'b1;
            @(posedge clk);
            start    <= 1'b0;
        end
    endtask

    task automatic wait_for_done_or_timeout(input int max_cycles, output bit timeout);
        int c;
        begin
            c = 0;
            while ((done !== 1'b1) && (c < max_cycles)) begin
                @(posedge clk);
                c++;
            end
            timeout = (done !== 1'b1);
        end
    endtask

    task automatic preload_region(
        input logic [31:0] base,
        input int          words,
        input logic [31:0] seed
    );
        int i;
        logic [31:0] data;
        begin
            for (i = 0; i < words; i++) begin
                data = seed ^ (32'h00A5_0000 + i);
                mem0.poke_word(base + (i * 4), data);
            end
        end
    endtask

    task automatic poison_region(
        input logic [31:0] base,
        input int          words,
        input logic [31:0] poison
    );
        int i;
        begin
            for (i = 0; i < words; i++) begin
                mem0.poke_word(base + (i * 4), poison);
            end
        end
    endtask

    task automatic check_copy(
        input logic [31:0] src,
        input logic [31:0] dst,
        input logic [31:0] bytes,
        input string       tag
    );
        int errs;
        begin
            mem0.check_copy_region(src, dst, bytes, errs);
            check((errs == 0), {tag, ": destination matches source"});
        end
    endtask

    task automatic apply_reset();
        begin
            rst_n <= 1'b0;
            start <= 1'b0;
            clear_done <= 1'b0;
            clear_error <= 1'b0;
            src_addr <= 32'h0;
            dst_addr <= 32'h0;
            len <= 32'h0;
            tick(4);
            rst_n <= 1'b1;
            tick(2);
        end
    endtask

    task automatic test_basic_copy();
        bit timeout;
        begin
            tests_run++;
            $display("\n[TEST] basic aligned copy");
            clear_status_flags();

            preload_region(32'h0000_0100, 16, 32'h1111_0000);
            poison_region(32'h0000_0200, 16, 32'hDEAD_BEEF);

            start_dma(32'h0000_0100, 32'h0000_0200, 32'd64);
            wait_for_done_or_timeout(300, timeout);

            check(!timeout, "basic copy completed before timeout");
            check(done == 1'b1, "done asserted for basic copy");
            check(busy == 1'b0, "busy deasserted after basic copy");
            check(error == 1'b0, "error remains clear in basic copy");
            check_copy(32'h0000_0100, 32'h0000_0200, 32'd64, "basic copy");
        end
    endtask

    task automatic test_zero_length();
        bit timeout;
        logic [31:0] before_word;
        logic [31:0] after_word;
        begin
            tests_run++;
            $display("\n[TEST] zero-length transfer");
            clear_status_flags();

            mem0.poke_word(32'h0000_0300, 32'hCAFE_BABE);
            mem0.peek_word(32'h0000_0300, before_word);

            start_dma(32'h0000_0100, 32'h0000_0300, 32'd0);
            wait_for_done_or_timeout(20, timeout);

            mem0.peek_word(32'h0000_0300, after_word);
            check(!timeout, "zero-length completes quickly");
            check(done == 1'b1, "done asserted for zero-length");
            check(busy == 1'b0, "busy stays low for zero-length");
            check(error == 1'b0, "error remains clear for zero-length");
            check(after_word == before_word, "zero-length does not modify destination");
        end
    endtask

    task automatic test_misalignment_error();
        begin
            tests_run++;
            $display("\n[TEST] misalignment error case");
            clear_status_flags();

            start_dma(32'h0000_0102, 32'h0000_0200, 32'd4);
            tick(3);

            check(error == 1'b1, "misaligned source address raises error");
            check(busy == 1'b0, "busy remains low on misaligned start");
            check(done == 1'b0, "done stays low on misaligned start");
        end
    endtask

    task automatic test_start_while_busy();
        bit timeout;
        begin
            tests_run++;
            $display("\n[TEST] start while busy (back-to-back start)");
            clear_status_flags();

            preload_region(32'h0000_0400, 24, 32'h2222_0000);
            poison_region(32'h0000_0500, 24, 32'h1234_5678);

            start_dma(32'h0000_0400, 32'h0000_0500, 32'd96);
            wait (busy == 1'b1);
            tick(2);

            // Illegal second start while busy must raise error.
            start_dma(32'h0000_0600, 32'h0000_0700, 32'd16);

            wait_for_done_or_timeout(500, timeout);
            check(!timeout, "first transfer still completes");
            check(done == 1'b1, "done asserted after first transfer completion");
            check(error == 1'b1, "error asserted on start while busy");
            check_copy(32'h0000_0400, 32'h0000_0500, 32'd96, "start-while-busy primary copy");
        end
    endtask

    task automatic test_reset_during_busy();
        bit timeout;
        begin
            tests_run++;
            $display("\n[TEST] reset during active transfer");
            clear_status_flags();

            preload_region(32'h0000_0800, 20, 32'h3333_0000);
            poison_region(32'h0000_0900, 20, 32'hBEEF_BEEF);

            start_dma(32'h0000_0800, 32'h0000_0900, 32'd80);
            wait (busy == 1'b1);
            tick(2);

            rst_n <= 1'b0;
            #1;
            tick(2);
            rst_n <= 1'b1;
            tick(2);

            check(busy == 1'b0, "busy clears after reset");
            check(done == 1'b0, "done clears after reset");
            check(error == 1'b0, "error clears after reset");

            // Sanity transfer post-reset
            clear_status_flags();
            preload_region(32'h0000_0A00, 8, 32'h4444_0000);
            poison_region(32'h0000_0B00, 8, 32'hA5A5_A5A5);

            start_dma(32'h0000_0A00, 32'h0000_0B00, 32'd32);
            wait_for_done_or_timeout(300, timeout);
            check(!timeout, "post-reset transfer completes");
            check(done == 1'b1, "post-reset transfer done asserted");
            check(error == 1'b0, "post-reset transfer has no error");
            check_copy(32'h0000_0A00, 32'h0000_0B00, 32'd32, "post-reset copy");
        end
    endtask

    task automatic test_boundary_copy();
        bit timeout;
        begin
            tests_run++;
            $display("\n[TEST] boundary-aligned copy near memory end");
            clear_status_flags();

            preload_region(32'h0000_0F00, 16, 32'h5555_0000);
            poison_region(32'h0000_0EC0, 16, 32'h0);

            start_dma(32'h0000_0F00, 32'h0000_0EC0, 32'd64);
            wait_for_done_or_timeout(400, timeout);

            check(!timeout, "boundary copy completes");
            check(done == 1'b1, "done asserted for boundary copy");
            check(error == 1'b0, "no error on valid boundary copy");
            check_copy(32'h0000_0F00, 32'h0000_0EC0, 32'd64, "boundary copy");
        end
    endtask

    initial begin
        failures = 0;
        tests_run = 0;

        apply_reset();

        mem0.clear_mem();
        mem0.init_pattern(32'h1BAD_F00D);

        test_basic_copy();
        test_zero_length();
        test_misalignment_error();
        test_start_while_busy();
        test_reset_during_busy();
        test_boundary_copy();

        $display("\n========================================");
        $display("DMA TB SUMMARY: tests_run=%0d failures=%0d", tests_run, failures);
        if (failures == 0) begin
            $display("DMA TB RESULT: PASS");
        end else begin
            $display("DMA TB RESULT: FAIL");
        end
        $display("========================================\n");

        if (failures != 0) begin
            $fatal(1, "DMA testbench failures detected");
        end

        #20;
        $finish;
    end

endmodule
