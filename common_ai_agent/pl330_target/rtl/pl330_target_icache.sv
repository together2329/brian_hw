`default_nettype none

module pl330_target_icache #(
    parameter integer ADDR_WIDTH        = 32,
    parameter integer DATA_WIDTH        = 32,
    parameter integer CACHE_DEPTH       = 32,
    parameter integer ICACHE_LINE_SIZE  = 32
) (
    input  logic                    clk,
    input  logic                    rst_n,

    input  logic                    icache_req_valid,
    output logic                    icache_req_ready,
    input  logic [ADDR_WIDTH-1:0]   icache_req_addr,

    output logic                    icache_resp_valid,
    input  logic                    icache_resp_ready,
    output logic [ADDR_WIDTH-1:0]   icache_resp_addr,
    output logic [DATA_WIDTH-1:0]   icache_resp_data,
    output logic                    icache_resp_hit,
    output logic                    icache_resp_error,

    output logic                    fill_req_valid,
    input  logic                    fill_req_ready,
    output logic [ADDR_WIDTH-1:0]   fill_req_addr,

    input  logic                    fill_resp_valid,
    output logic                    fill_resp_ready,
    input  logic [DATA_WIDTH-1:0]   fill_resp_data,
    input  logic                    fill_resp_error,

    input  logic                    invalidate_valid,
    input  logic [ADDR_WIDTH-1:0]   invalidate_addr,
    output logic                    invalidate_ready,

    input  logic                    flush_valid,
    output logic                    flush_ready,

    output logic [2:0]              debug_state,
    output logic [5:0]              debug_valid_count,
    output logic [31:0]             debug_hit_count,
    output logic [31:0]             debug_miss_count
);
    // Traceability: PL330 TARGET ICACHE module pl330_target_icache.
    // Source refs: RTL_MODULE_PL330_TARGET_ICACHE, rtl_todo_plan, sub_modules[5],
    // memory.instances.icache, parameters.ICACHE_LINE_SIZE, cycle_model.handshake_rules.icache_fill.

    localparam integer INDEX_WIDTH      = 5;
    localparam integer LINE_BYTES       = (ICACHE_LINE_SIZE / 8);
    localparam integer OFFSET_WIDTH     = (LINE_BYTES <= 1) ? 0 : $clog2(LINE_BYTES);
    localparam integer TAG_LSB          = OFFSET_WIDTH + INDEX_WIDTH;
    localparam integer TAG_WIDTH        = ADDR_WIDTH - TAG_LSB;

    localparam logic [2:0] ST_IDLE      = 3'd0;
    localparam logic [2:0] ST_LOOKUP    = 3'd1;
    localparam logic [2:0] ST_MISS_REQ  = 3'd2;
    localparam logic [2:0] ST_REFILL    = 3'd3;
    localparam logic [2:0] ST_RESP      = 3'd4;

    logic [2:0]                    state_q;
    logic [ADDR_WIDTH-1:0]         pending_addr_q;

    logic [DATA_WIDTH-1:0]         data_mem [0:CACHE_DEPTH-1];
    logic [TAG_WIDTH-1:0]          tag_mem  [0:CACHE_DEPTH-1];
    logic [CACHE_DEPTH-1:0]        valid_mem;

    logic [INDEX_WIDTH-1:0]        pending_index;
    logic [TAG_WIDTH-1:0]          pending_tag;
    logic [INDEX_WIDTH-1:0]        invalidate_index;
    logic [TAG_WIDTH-1:0]          invalidate_tag;
    logic [ADDR_WIDTH-1:0]         pending_addr_aligned;
    logic                          invalidate_unaligned;

    logic [DATA_WIDTH-1:0]         lookup_data;
    logic [TAG_WIDTH-1:0]          lookup_tag;
    logic                          lookup_valid;
    logic                          lookup_hit;
    logic                          invalidate_hit;

    integer                        cache_i;

    assign pending_index    = pending_addr_q[OFFSET_WIDTH +: INDEX_WIDTH];
    assign pending_tag      = pending_addr_q[ADDR_WIDTH-1:TAG_LSB];
    assign invalidate_index = invalidate_addr[OFFSET_WIDTH +: INDEX_WIDTH];
    assign invalidate_tag   = invalidate_addr[ADDR_WIDTH-1:TAG_LSB];

    generate
        if (OFFSET_WIDTH > 0) begin : gen_aligned_fill_addr
            assign pending_addr_aligned = {pending_addr_q[ADDR_WIDTH-1:OFFSET_WIDTH], {OFFSET_WIDTH{1'b0}}};
            assign invalidate_unaligned = |invalidate_addr[OFFSET_WIDTH-1:0];
        end else begin : gen_unaligned_fill_addr
            assign pending_addr_aligned = pending_addr_q;
            assign invalidate_unaligned = 1'b0;
        end
    endgenerate

    assign lookup_data       = data_mem[pending_index];
    assign lookup_tag        = tag_mem[pending_index];
    assign lookup_valid      = valid_mem[pending_index];
    assign lookup_hit        = lookup_valid && (lookup_tag == pending_tag);
    assign invalidate_hit    = valid_mem[invalidate_index] && (tag_mem[invalidate_index] == invalidate_tag);

    always_comb begin
        icache_req_ready  = (state_q == ST_IDLE) && !flush_valid && !invalidate_valid;
        fill_req_valid    = (state_q == ST_MISS_REQ);
        fill_req_addr     = pending_addr_aligned;
        fill_resp_ready   = (state_q == ST_REFILL);
        invalidate_ready  = (state_q == ST_IDLE);
        flush_ready       = (state_q == ST_IDLE);
        debug_state       = state_q;
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q           <= ST_IDLE;
            pending_addr_q    <= {ADDR_WIDTH{1'b0}};
            icache_resp_valid <= 1'b0;
            icache_resp_addr  <= {ADDR_WIDTH{1'b0}};
            icache_resp_data  <= {DATA_WIDTH{1'b0}};
            icache_resp_hit   <= 1'b0;
            icache_resp_error <= 1'b0;
            debug_valid_count <= 6'd0;
            debug_hit_count   <= 32'd0;
            debug_miss_count  <= 32'd0;
            valid_mem         <= {CACHE_DEPTH{1'b0}};
            for (cache_i = 0; cache_i < CACHE_DEPTH; cache_i = cache_i + 1) begin
                data_mem[cache_i] <= {DATA_WIDTH{1'b0}};
                tag_mem[cache_i]  <= {TAG_WIDTH{1'b0}};
            end
        end else begin
            case (state_q)
                ST_IDLE: begin
                    icache_resp_valid <= 1'b0;
                    icache_resp_hit   <= 1'b0;
                    icache_resp_error <= 1'b0;

                    if (flush_valid) begin
                        valid_mem         <= {CACHE_DEPTH{1'b0}};
                        debug_valid_count <= 6'd0;
                    end else if (invalidate_valid) begin
                        if (invalidate_hit) begin
                            valid_mem[invalidate_index] <= 1'b0;
                            if (debug_valid_count != 6'd0) begin
                                debug_valid_count <= debug_valid_count - 6'd1;
                            end
                        end
                        if (invalidate_unaligned) begin
                            debug_miss_count <= debug_miss_count + 32'd1;
                        end
                    end else if (icache_req_valid) begin
                        pending_addr_q <= icache_req_addr;
                        state_q        <= ST_LOOKUP;
                    end
                end

                ST_LOOKUP: begin
                    icache_resp_addr <= pending_addr_q;
                    if (lookup_hit) begin
                        icache_resp_valid <= 1'b1;
                        icache_resp_data  <= lookup_data;
                        icache_resp_hit   <= 1'b1;
                        icache_resp_error <= 1'b0;
                        debug_hit_count   <= debug_hit_count + 32'd1;
                        state_q           <= ST_RESP;
                    end else begin
                        icache_resp_hit  <= 1'b0;
                        debug_miss_count <= debug_miss_count + 32'd1;
                        state_q          <= ST_MISS_REQ;
                    end
                end

                ST_MISS_REQ: begin
                    if (fill_req_ready) begin
                        state_q <= ST_REFILL;
                    end
                end

                ST_REFILL: begin
                    if (fill_resp_valid) begin
                        icache_resp_valid <= 1'b1;
                        icache_resp_addr  <= pending_addr_q;
                        icache_resp_data  <= fill_resp_error ? {DATA_WIDTH{1'b0}} : fill_resp_data;
                        icache_resp_hit   <= 1'b0;
                        icache_resp_error <= fill_resp_error;

                        if (!fill_resp_error) begin
                            data_mem[pending_index] <= fill_resp_data;
                            tag_mem[pending_index]  <= pending_tag;
                            if (!valid_mem[pending_index]) begin
                                debug_valid_count <= debug_valid_count + 6'd1;
                            end
                            valid_mem[pending_index] <= 1'b1;
                        end

                        state_q <= ST_RESP;
                    end
                end

                ST_RESP: begin
                    if (icache_resp_ready) begin
                        icache_resp_valid <= 1'b0;
                        icache_resp_hit   <= 1'b0;
                        icache_resp_error <= 1'b0;
                        state_q           <= ST_IDLE;
                    end
                end

                default: begin
                    state_q           <= ST_IDLE;
                    icache_resp_valid <= 1'b0;
                    icache_resp_hit   <= 1'b0;
                    icache_resp_error <= 1'b0;
                end
            endcase
        end
    end
endmodule

`default_nettype wire
