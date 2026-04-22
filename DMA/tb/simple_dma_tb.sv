`timescale 1ns/1ps

module simple_dma_tb;
    localparam int unsigned ADDR_WIDTH = 32;
    localparam int unsigned DATA_WIDTH = 32;
    localparam int unsigned LEN_WIDTH  = 16;
    localparam int unsigned MEM_WORDS  = 256;
    localparam int unsigned WORD_BYTES = DATA_WIDTH / 8;
    localparam int unsigned ADDR_LSB   = $clog2(WORD_BYTES);

    localparam logic [ADDR_WIDTH-1:0] SRC_BASE = 32'h0000_0010;
    localparam logic [ADDR_WIDTH-1:0] DST_BASE = 32'h0000_0080;

    logic                  clk;
    logic                  rst_n;
    logic                  start;
    logic [ADDR_WIDTH-1:0] src_addr;
    logic [ADDR_WIDTH-1:0] dst_addr;
    logic [LEN_WIDTH-1:0]  len;
    logic                  busy;
    logic                  done;
    logic                  error;
    logic                  rd_req_valid;
    logic [ADDR_WIDTH-1:0] rd_req_addr;
    logic                  rd_req_ready;
    logic                  rd_data_valid;
    logic [DATA_WIDTH-1:0] rd_data;
    logic                  rd_data_ready;
    logic                  wr_req_valid;
    logic [ADDR_WIDTH-1:0] wr_req_addr;
    logic [DATA_WIDTH-1:0] wr_req_data;
    logic                  wr_req_ready;

    logic [DATA_WIDTH-1:0] mem [0:MEM_WORDS-1];

    logic                  rd_pending_valid;
    logic [ADDR_WIDTH-1:0] rd_pending_addr;
    integer                rd_pending_delay;
    integer                rd_response_delay_cycles;
    integer                rd_req_count;
    integer                wr_req_count;

    simple_dma #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .LEN_WIDTH(LEN_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .src_addr(src_addr),
        .dst_addr(dst_addr),
        .len(len),
        .busy(busy),
        .done(done),
        .error(error),
        .rd_req_valid(rd_req_valid),
        .rd_req_addr(rd_req_addr),
        .rd_req_ready(rd_req_ready),
        .rd_data_valid(rd_data_valid),
        .rd_data(rd_data),
        .rd_data_ready(rd_data_ready),
        .wr_req_valid(wr_req_valid),
        .wr_req_addr(wr_req_addr),
        .wr_req_data(wr_req_data),
        .wr_req_ready(wr_req_ready)
    );

    initial begin
        clk = 1'b0;
    end

    always #5 clk = ~clk;

    function automatic integer word_index(input logic [ADDR_WIDTH-1:0] addr);
        word_index = addr[ADDR_WIDTH-1:ADDR_LSB];
    endfunction

    task automatic clear_memory;
        integer i;
        begin
            for (i = 0; i < MEM_WORDS; i = i + 1) begin
                mem[i] = '0;
            end
        end
    endtask

    task automatic seed_regions(
        input logic [ADDR_WIDTH-1:0] src_base,
        input logic [ADDR_WIDTH-1:0] dst_base,
        input integer                words,
        input integer                seed
    );
        integer i;
        logic [ADDR_WIDTH-1:0] offset;
        begin
            for (i = 0; i < words; i = i + 1) begin
                offset = ADDR_WIDTH'((i * WORD_BYTES));
                mem[word_index(src_base + offset)] = 32'h1000_0000 + seed + i;
                mem[word_index(dst_base + offset)] = 32'hDEAD_0000 + seed + i;
            end
        end
    endtask

    task automatic reset_counters;
        begin
            rd_req_count = 0;
            wr_req_count = 0;
        end
    endtask

    task automatic apply_reset;
        begin
            rst_n                   = 1'b0;
            start                   = 1'b0;
            src_addr                = '0;
            dst_addr                = '0;
            len                     = '0;
            rd_req_ready            = 1'b1;
            wr_req_ready            = 1'b1;
            rd_data_valid           = 1'b0;
            rd_data                 = '0;
            rd_pending_valid        = 1'b0;
            rd_pending_addr         = '0;
            rd_pending_delay        = 0;
            rd_response_delay_cycles = 0;
            reset_counters();
            repeat (4) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
        end
    endtask

    task automatic launch_transfer(
        input logic [ADDR_WIDTH-1:0] src_base,
        input logic [ADDR_WIDTH-1:0] dst_base,
        input logic [LEN_WIDTH-1:0]  words
    );
        begin
            src_addr <= src_base;
            dst_addr <= dst_base;
            len      <= words;
            start    <= 1'b1;
            @(posedge clk);
            start    <= 1'b0;
        end
    endtask

    task automatic wait_for_done(input integer max_cycles);
        integer cycles;
        bit     seen_done;
        begin
            seen_done = 1'b0;
            for (cycles = 0; cycles < max_cycles; cycles = cycles + 1) begin
                @(posedge clk);
                if (done) begin
                    seen_done = 1'b1;
                    cycles    = max_cycles;
                end
            end

            if (!seen_done) begin
                $fatal(1, "Timed out waiting for done after %0d cycles", max_cycles);
            end

            @(posedge clk);
            if (done !== 1'b0) begin
                $fatal(1, "done must be a one-cycle pulse");
            end
        end
    endtask

    task automatic check_copy(
        input logic [ADDR_WIDTH-1:0] src_base,
        input logic [ADDR_WIDTH-1:0] dst_base,
        input integer                words
    );
        integer i;
        logic [ADDR_WIDTH-1:0] offset;
        begin
            for (i = 0; i < words; i = i + 1) begin
                offset = ADDR_WIDTH'((i * WORD_BYTES));
                if (mem[word_index(dst_base + offset)] !== mem[word_index(src_base + offset)]) begin
                    $fatal(1, "Copy mismatch at word %0d: dst=0x%08h src=0x%08h",
                           i,
                           mem[word_index(dst_base + offset)],
                           mem[word_index(src_base + offset)]);
                end
            end
        end
    endtask

    task automatic test_basic_copy;
        begin
            $display("TEST 1: basic multi-word copy");
            clear_memory();
            seed_regions(SRC_BASE, DST_BASE, 8, 32);
            reset_counters();
            rd_req_ready             = 1'b1;
            wr_req_ready             = 1'b1;
            rd_response_delay_cycles = 0;

            launch_transfer(SRC_BASE, DST_BASE, 8);
            wait_for_done(100);
            check_copy(SRC_BASE, DST_BASE, 8);

            if (rd_req_count != 8) begin
                $fatal(1, "Expected 8 read requests, saw %0d", rd_req_count);
            end
            if (wr_req_count != 8) begin
                $fatal(1, "Expected 8 write requests, saw %0d", wr_req_count);
            end
            if (error !== 1'b0) begin
                $fatal(1, "error asserted during basic copy test");
            end
        end
    endtask

    task automatic test_zero_length;
        logic [DATA_WIDTH-1:0] dst_before0;
        logic [DATA_WIDTH-1:0] dst_before1;
        begin
            $display("TEST 2: zero-length transfer");
            clear_memory();
            seed_regions(SRC_BASE, DST_BASE, 2, 64);
            reset_counters();
            rd_req_ready             = 1'b1;
            wr_req_ready             = 1'b1;
            rd_response_delay_cycles = 0;
            dst_before0              = mem[word_index(DST_BASE)];
            dst_before1              = mem[word_index(DST_BASE + WORD_BYTES)];

            launch_transfer(SRC_BASE, DST_BASE, '0);
            wait_for_done(20);

            if (rd_req_count != 0) begin
                $fatal(1, "Zero-length transfer should not issue read requests, saw %0d", rd_req_count);
            end
            if (wr_req_count != 0) begin
                $fatal(1, "Zero-length transfer should not issue write requests, saw %0d", wr_req_count);
            end
            if (mem[word_index(DST_BASE)] !== dst_before0 || mem[word_index(DST_BASE + WORD_BYTES)] !== dst_before1) begin
                $fatal(1, "Zero-length transfer modified destination memory");
            end
            if (error !== 1'b0) begin
                $fatal(1, "error asserted during zero-length test");
            end
        end
    endtask

    task automatic test_backpressure;
        begin
            $display("TEST 3: stalled handshake path");
            clear_memory();
            seed_regions(SRC_BASE, DST_BASE, 4, 96);
            reset_counters();
            rd_response_delay_cycles = 2;
            rd_req_ready             = 1'b0;
            wr_req_ready             = 1'b0;

            launch_transfer(SRC_BASE, DST_BASE, 4);
            repeat (3) @(posedge clk);
            rd_req_ready = 1'b1;
            repeat (9) @(posedge clk);
            wr_req_ready = 1'b1;
            wait_for_done(120);
            check_copy(SRC_BASE, DST_BASE, 4);

            if (rd_req_count != 4) begin
                $fatal(1, "Expected 4 read requests in backpressure test, saw %0d", rd_req_count);
            end
            if (wr_req_count != 4) begin
                $fatal(1, "Expected 4 write requests in backpressure test, saw %0d", wr_req_count);
            end
            if (error !== 1'b0) begin
                $fatal(1, "error asserted during backpressure test");
            end
            rd_req_ready = 1'b1;
            wr_req_ready = 1'b1;
        end
    endtask

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_data_valid    <= 1'b0;
            rd_data          <= '0;
            rd_pending_valid <= 1'b0;
            rd_pending_addr  <= '0;
            rd_pending_delay <= 0;
            rd_req_count     <= 0;
            wr_req_count     <= 0;
        end else begin
            if (rd_req_valid && rd_req_ready) begin
                if (rd_pending_valid || rd_data_valid) begin
                    $display("FATAL: Testbench memory model only supports one pending read response");
                    $fatal(1);
                end
                rd_pending_valid <= 1'b1;
                rd_pending_addr  <= rd_req_addr;
                rd_pending_delay <= rd_response_delay_cycles;
                rd_req_count     <= rd_req_count + 1;
            end

            if (rd_pending_valid && !rd_data_valid) begin
                if (rd_pending_delay == 0) begin
                    rd_data          <= mem[word_index(rd_pending_addr)];
                    rd_data_valid    <= 1'b1;
                    rd_pending_valid <= 1'b0;
                end else begin
                    rd_pending_delay <= rd_pending_delay - 1;
                end
            end

            if (rd_data_valid && rd_data_ready) begin
                rd_data_valid <= 1'b0;
            end

            if (wr_req_valid && wr_req_ready) begin
                mem[word_index(wr_req_addr)] <= wr_req_data;
                wr_req_count                 <= wr_req_count + 1;
            end
        end
    end

    initial begin
        clear_memory();
        apply_reset();

        test_basic_copy();
        test_zero_length();
        test_backpressure();

        $display("PASS: simple_dma_tb completed all directed tests");
        $finish;
    end

endmodule
