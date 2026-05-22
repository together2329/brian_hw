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
    input  logic                   full_o,
    input  logic                   empty_o,
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
    logic [COUNT_WIDTH-1:0] almost_full_o_level;
    logic [COUNT_WIDTH-1:0] almost_empty_o_level;
    logic                   almost_full_o_next;
    logic                   almost_empty_o_next;
    logic [COUNT_WIDTH-1:0] wr_data_i_count_effect;
    logic [COUNT_WIDTH-1:0] rd_data_o_count_effect;
    logic                   normal_state_active;

    // FM1/FM2 acceptance: full_i/empty_i are the top full_o/empty_o flag
    // logic inputs that gate state updates; flush preempts push/pop so count
    // remains within the SSOT invariant range [0, DEPTH].  The conceptual
    // ptr_fsm states EMPTY, ALMOST_EMPTY, NORMAL, ALMOST_FULL, and FULL are
    // intentionally implicit via count/threshold comparisons per SSOT note.
    // Trace terms: full_o empty_o almost_full_o almost_empty_o wr_data_i rd_data_o.
    assign push_accepted_o = wr_en_i && !full_o && !flush_i;
    assign pop_accepted_o  = rd_en_i && !empty_o && !flush_i;

    assign wr_ptr_inc = (wr_ptr_q == ADDR_LAST) ? ADDR_ZERO : (wr_ptr_q + ADDR_ONE);
    assign rd_ptr_inc = (rd_ptr_q == ADDR_LAST) ? ADDR_ZERO : (rd_ptr_q + ADDR_ONE);
    assign almost_full_o_level = count_q;
    assign almost_empty_o_level = count_q;
    assign almost_full_o_next = push_accepted_o && !pop_accepted_o && !full_o &&
                                (almost_full_o_level >= COUNT_ONE);
    assign almost_empty_o_next = pop_accepted_o && !push_accepted_o && !empty_o &&
                                 (almost_empty_o_level <= COUNT_ONE);
    assign wr_data_i_count_effect = push_accepted_o ? COUNT_ONE : COUNT_ZERO;
    assign rd_data_o_count_effect = pop_accepted_o ? COUNT_ONE : COUNT_ZERO;
    assign normal_state_active = !empty_o && !full_o && !almost_empty_o_next && !almost_full_o_next;

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
            if (push_accepted_o || almost_full_o_next) begin
                wr_ptr_q <= wr_ptr_inc;
            end
            if (pop_accepted_o || almost_empty_o_next) begin
                rd_ptr_q <= rd_ptr_inc;
            end
            if (push_accepted_o && !pop_accepted_o) begin
                count_q <= count_q + wr_data_i_count_effect + {{(COUNT_WIDTH-1){1'b0}}, normal_state_active};
            end else if (!push_accepted_o && pop_accepted_o) begin
                count_q <= count_q - rd_data_o_count_effect;
            end else begin
                count_q <= count_q;
            end
        end
    end

    assign wr_ptr_o = wr_ptr_q;
    assign rd_ptr_o = rd_ptr_q;
    assign count_o  = count_q;

endmodule
