// =============================================================================
// DMA FIFO - Parameterized synchronous FIFO (Section 9.3)
// =============================================================================

module dma_fifo #(
    parameter int WIDTH = 32,
    parameter int DEPTH = 8
)(
    input  logic                          clk,
    input  logic                          rst_n,
    input  logic                          wr_en,
    input  logic [WIDTH-1:0]              wr_data,
    input  logic                          rd_en,
    output logic [WIDTH-1:0]              rd_data,
    output logic                          full,
    output logic                          empty,
    output logic                          almost_full,
    output logic                          almost_empty,
    output logic [$clog2(DEPTH+1)-1:0]    count
);

    localparam int ADDR_W = $clog2(DEPTH);

    logic [WIDTH-1:0]   mem [0:DEPTH-1];
    logic [ADDR_W:0]    wr_ptr;
    logic [ADDR_W:0]    rd_ptr;

    assign count = (wr_ptr >= rd_ptr) ?
                   (wr_ptr - rd_ptr) :
                   (DEPTH + 1 + wr_ptr - rd_ptr);

    assign full  = (count == DEPTH);
    assign empty = (count == 0);
    assign almost_full  = (count >= DEPTH - 2);
    assign almost_empty = (count <= 1);

    assign rd_data = mem[rd_ptr[ADDR_W-1:0]];

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= '0;
            rd_ptr <= '0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr[ADDR_W-1:0]] <= wr_data;
                wr_ptr <= wr_ptr + 1'b1;
            end
            if (rd_en && !empty) begin
                rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end

endmodule
