// fifo_sync_ptrs.sv — SSOT-backed pointer, count, and acceptance control.
module fifo_sync_ptrs #(
    parameter integer DEPTH = 16,
    parameter integer ADDR_WIDTH = $clog2(DEPTH),
    parameter integer COUNT_WIDTH = $clog2(DEPTH+1)
) (
    input  logic                   clk_i,
    input  logic                   rst_ni,
    input  logic                   wr_en_i,
    input  logic                   rd_en_i,
    input  logic                   flush_i,
    input  logic                   full_i,
    input  logic                   empty_i,
    output logic                   push_accepted_o,
    output logic                   pop_accepted_o,
    output logic [ADDR_WIDTH-1:0]  wr_ptr_o,
    output logic [ADDR_WIDTH-1:0]  rd_ptr_o,
    output logic [COUNT_WIDTH-1:0] count_o
);

    localparam [COUNT_WIDTH-1:0] COUNT_ZERO = {COUNT_WIDTH{1'b0}};
    localparam [COUNT_WIDTH-1:0] COUNT_ONE  = {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
    localparam [ADDR_WIDTH-1:0]  ADDR_ZERO  = {ADDR_WIDTH{1'b0}};
    localparam [ADDR_WIDTH-1:0]  ADDR_ONE   = {{(ADDR_WIDTH-1){1'b0}}, 1'b1};
    localparam [ADDR_WIDTH-1:0]  ADDR_LAST  = DEPTH[ADDR_WIDTH-1:0] - ADDR_ONE;

    logic [ADDR_WIDTH-1:0]  wr_ptr_q;
    logic [ADDR_WIDTH-1:0]  rd_ptr_q;
    logic [COUNT_WIDTH-1:0] count_q;
    logic [ADDR_WIDTH-1:0]  wr_ptr_inc;
    logic [ADDR_WIDTH-1:0]  rd_ptr_inc;

    // FM1/FM2 acceptance: full and empty gate state updates; flush preempts
    // push/pop so count remains within the SSOT invariant range [0, DEPTH].
    assign push_accepted_o = wr_en_i && !full_i && !flush_i;
    assign pop_accepted_o  = rd_en_i && !empty_i && !flush_i;

    assign wr_ptr_inc = (wr_ptr_q == ADDR_LAST) ? ADDR_ZERO : (wr_ptr_q + ADDR_ONE);
    assign rd_ptr_inc = (rd_ptr_q == ADDR_LAST) ? ADDR_ZERO : (rd_ptr_q + ADDR_ONE);

    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            wr_ptr_q <= ADDR_ZERO;
            rd_ptr_q <= ADDR_ZERO;
            count_q  <= COUNT_ZERO;
        end else if (flush_i) begin
            wr_ptr_q <= ADDR_ZERO;
            rd_ptr_q <= ADDR_ZERO;
            count_q  <= COUNT_ZERO;
        end else begin
            if (push_accepted_o) begin
                wr_ptr_q <= wr_ptr_inc;
            end
            if (pop_accepted_o) begin
                rd_ptr_q <= rd_ptr_inc;
            end
            if (push_accepted_o && !pop_accepted_o) begin
                count_q <= count_q + COUNT_ONE;
            end else if (!push_accepted_o && pop_accepted_o) begin
                count_q <= count_q - COUNT_ONE;
            end else begin
                count_q <= count_q;
            end
        end
    end

    assign wr_ptr_o = wr_ptr_q;
    assign rd_ptr_o = rd_ptr_q;
    assign count_o  = count_q;

endmodule
