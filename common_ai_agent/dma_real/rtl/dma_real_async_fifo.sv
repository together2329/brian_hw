// dma_real_async_fifo.sv — Parameterized dual-clock async FIFO with gray-code pointer sync
//
// SSOT refs: memory.internal.ch_async_fifo, cdc_requirements.crossings.config_cdc
//
// Pointer-based circular buffer. Write port in wclk domain, read port in rclk domain.
// Gray-code pointers synchronized via 2-stage CDC sync.
// Almost-full and almost-empty flags for backpressure.

module dma_real_async_fifo #(
    parameter integer DATA_WIDTH = 32,
    parameter integer FIFO_DEPTH = 16
) (
    // Write port (wclk domain)
    input  logic                  wclk,
    input  logic                  wrst_n,
    input  logic                  wren,
    input  logic [DATA_WIDTH-1:0] wdata,
    output logic                  wfull,
    output logic                  almost_full,
    // Read port (rclk domain)
    input  logic                  rclk,
    input  logic                  rrst_n,
    input  logic                  rden,
    output logic [DATA_WIDTH-1:0] rdata,
    output logic                  rempty,
    output logic                  almost_empty
);

    localparam ADDR_WIDTH = $clog2(FIFO_DEPTH);
    localparam ALMOST_FULL_THRESH  = FIFO_DEPTH - 2;
    localparam ALMOST_EMPTY_THRESH = 2;

    // Memory array
    logic [DATA_WIDTH-1:0] mem [FIFO_DEPTH];

    // Binary pointers
    logic [ADDR_WIDTH:0] wr_ptr_bin, rd_ptr_bin;

    // Gray-code pointers
    logic [ADDR_WIDTH:0] wr_ptr_gray, rd_ptr_gray;
    logic [ADDR_WIDTH:0] wr_ptr_gray_sync, rd_ptr_gray_sync;

    // Synchronized gray pointers (crossed to other domain)
    logic [ADDR_WIDTH:0] rd_ptr_gray_to_wr, wr_ptr_gray_to_rd;

    // Binary-to-gray conversion
    function automatic [ADDR_WIDTH:0] bin2gray;
        input [ADDR_WIDTH:0] bin;
        bin2gray = bin ^ (bin >> 1);
    endfunction

    // Gray-to-binary conversion
    function automatic [ADDR_WIDTH:0] gray2bin;
        input [ADDR_WIDTH:0] gray;
        integer i;
        gray2bin[ADDR_WIDTH] = gray[ADDR_WIDTH];
        for (i = ADDR_WIDTH - 1; i >= 0; i = i - 1)
            gray2bin[i] = gray2bin[i + 1] ^ gray[i];
    endfunction

    // Write domain
    logic [ADDR_WIDTH:0] rd_ptr_bin_in_wr;
    assign rd_ptr_bin_in_wr = gray2bin(rd_ptr_gray_to_wr);
    assign wfull  = (wr_ptr_gray == {~rd_ptr_gray_to_wr[ADDR_WIDTH:ADDR_WIDTH-1], rd_ptr_gray_to_wr[ADDR_WIDTH-2:0]});
    assign almost_full = (wr_ptr_bin - rd_ptr_bin_in_wr) >= ALMOST_FULL_THRESH[ADDR_WIDTH:0];

    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wr_ptr_bin  <= {(ADDR_WIDTH + 1){1'b0}};
            wr_ptr_gray <= {(ADDR_WIDTH + 1){1'b0}};
        end else if (wren && !wfull) begin
            mem[wr_ptr_bin[ADDR_WIDTH-1:0]] <= wdata;
            wr_ptr_bin  <= wr_ptr_bin + {(ADDR_WIDTH + 1){1'b1}} + 1'b1;
            wr_ptr_gray <= bin2gray(wr_ptr_bin + {(ADDR_WIDTH + 1){1'b1}} + 1'b1);
        end
    end

    // CDC sync: gray wr_ptr -> read domain
    dma_real_cdc_sync #(.WIDTH(ADDR_WIDTH + 1)) u_wr_sync (
        .clk   (rclk),
        .rst_n (rrst_n),
        .din   (wr_ptr_gray),
        .dout  (wr_ptr_gray_to_rd)
    );

    // Read domain
    logic [ADDR_WIDTH:0] wr_ptr_bin_in_rd;
    assign wr_ptr_bin_in_rd = gray2bin(wr_ptr_gray_to_rd);
    assign rempty = (rd_ptr_gray == wr_ptr_gray_to_rd);
    assign almost_empty = (wr_ptr_bin_in_rd - rd_ptr_bin) <= ALMOST_EMPTY_THRESH[ADDR_WIDTH:0];

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rd_ptr_bin  <= {(ADDR_WIDTH + 1){1'b0}};
            rd_ptr_gray <= {(ADDR_WIDTH + 1){1'b0}};
            rdata       <= {DATA_WIDTH{1'b0}};
        end else if (rden && !rempty) begin
            rdata       <= mem[rd_ptr_bin[ADDR_WIDTH-1:0]];
            rd_ptr_bin  <= rd_ptr_bin + {(ADDR_WIDTH + 1){1'b1}} + 1'b1;
            rd_ptr_gray <= bin2gray(rd_ptr_bin + {(ADDR_WIDTH + 1){1'b1}} + 1'b1);
        end
    end

    // CDC sync: gray rd_ptr -> write domain
    dma_real_cdc_sync #(.WIDTH(ADDR_WIDTH + 1)) u_rd_sync (
        .clk   (wclk),
        .rst_n (wrst_n),
        .din   (rd_ptr_gray),
        .dout  (rd_ptr_gray_to_wr)
    );

endmodule
