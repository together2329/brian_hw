`default_nettype none

// RTL_MODULE_PL330_TARGET_MERGE_BUFFER
// SSOT traceability: sub_modules[4], workflow_todos.rtl-gen[5], memory.instances.merge_buffer,
// parameters.MERGE_BUFFER_DEPTH, sub_modules.pl330_target_merge_buffer.module_equivalence.
// This module implements the PL330 target merge buffer as a real ready/valid transaction buffer.

module pl330_target_merge_buffer #(
    parameter int AXI_DATA_WIDTH     = 32,
    parameter int AXI_ADDR_WIDTH     = 32,
    parameter int AXI_ID_WIDTH       = 4,
    parameter int AXI_STRB_WIDTH     = (AXI_DATA_WIDTH / 8),
    parameter int MERGE_BUFFER_DEPTH = 4,
    parameter int PTR_WIDTH          = (MERGE_BUFFER_DEPTH <= 1) ? 1 : $clog2(MERGE_BUFFER_DEPTH),
    parameter int COUNT_WIDTH        = (MERGE_BUFFER_DEPTH <= 1) ? 1 : $clog2(MERGE_BUFFER_DEPTH + 1),
    parameter int BYTE_OFFSET_WIDTH  = (AXI_STRB_WIDTH <= 1) ? 0 : $clog2(AXI_STRB_WIDTH)
) (
    input  wire                         clk,
    input  wire                         rst_n,

    input  wire                         flush_i,

    input  wire                         in_valid_i,
    output wire                         in_ready_o,
    input  wire [AXI_ADDR_WIDTH-1:0]    in_addr_i,
    input  wire [AXI_DATA_WIDTH-1:0]    in_data_i,
    input  wire [AXI_STRB_WIDTH-1:0]    in_strb_i,
    input  wire [AXI_ID_WIDTH-1:0]      in_id_i,
    input  wire                         in_last_i,

    output wire                         out_valid_o,
    input  wire                         out_ready_i,
    output wire [AXI_ADDR_WIDTH-1:0]    out_addr_o,
    output wire [AXI_DATA_WIDTH-1:0]    out_data_o,
    output wire [AXI_STRB_WIDTH-1:0]    out_strb_o,
    output wire [AXI_ID_WIDTH-1:0]      out_id_o,
    output wire                         out_last_o,

    output wire                         empty_o,
    output wire                         full_o,
    output wire [COUNT_WIDTH-1:0]       occupancy_o,
    output reg                          accept_pulse_o,
    output reg                          pop_pulse_o,
    output reg                          merge_pulse_o,
    output reg                          overflow_sticky_o
);

    localparam [PTR_WIDTH-1:0]   PTR_ZERO   = {PTR_WIDTH{1'b0}};
    localparam [PTR_WIDTH-1:0]   DEPTH_LAST = PTR_WIDTH'(MERGE_BUFFER_DEPTH - 1);
    localparam [COUNT_WIDTH-1:0] COUNT_ZERO = {COUNT_WIDTH{1'b0}};
    localparam [COUNT_WIDTH-1:0] COUNT_ONE  = {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
    localparam [COUNT_WIDTH-1:0] COUNT_MAX  = COUNT_WIDTH'(MERGE_BUFFER_DEPTH);

    reg [AXI_DATA_WIDTH-1:0] merge_buffer [0:MERGE_BUFFER_DEPTH-1];
    reg [AXI_ADDR_WIDTH-1:0] addr_buffer  [0:MERGE_BUFFER_DEPTH-1];
    reg [AXI_STRB_WIDTH-1:0] strb_buffer  [0:MERGE_BUFFER_DEPTH-1];
    reg [AXI_ID_WIDTH-1:0]   id_buffer    [0:MERGE_BUFFER_DEPTH-1];
    reg                      last_buffer  [0:MERGE_BUFFER_DEPTH-1];

    reg [PTR_WIDTH-1:0]   rd_ptr_q;
    reg [PTR_WIDTH-1:0]   wr_ptr_q;
    reg [COUNT_WIDTH-1:0] count_q;

    wire [PTR_WIDTH-1:0] tail_ptr_w;
    wire                 empty_w;
    wire                 full_w;
    wire                 out_fire_w;
    wire                 tail_valid_for_merge_w;
    wire                 same_word_w;
    wire                 same_id_w;
    wire                 merge_possible_w;
    wire                 do_accept_w;
    wire                 do_merge_w;
    wire                 do_push_w;
    wire                 do_pop_w;
    wire [AXI_DATA_WIDTH-1:0] in_strobe_mask_w;
    wire [AXI_DATA_WIDTH-1:0] merged_tail_data_w;
    wire [AXI_STRB_WIDTH-1:0] merged_tail_strb_w;

    genvar byte_idx;
    generate
        for (byte_idx = 0; byte_idx < AXI_STRB_WIDTH; byte_idx = byte_idx + 1) begin : gen_strobe_mask
            assign in_strobe_mask_w[(byte_idx*8) +: 8] = {8{in_strb_i[byte_idx]}};
        end
    endgenerate

    function automatic [PTR_WIDTH-1:0] inc_ptr;
        input [PTR_WIDTH-1:0] ptr;
        begin
            if (ptr == DEPTH_LAST) begin
                inc_ptr = PTR_ZERO;
            end else begin
                inc_ptr = ptr + 1'b1;
            end
        end
    endfunction

    function automatic [PTR_WIDTH-1:0] dec_ptr;
        input [PTR_WIDTH-1:0] ptr;
        begin
            if (ptr == PTR_ZERO) begin
                dec_ptr = DEPTH_LAST;
            end else begin
                dec_ptr = ptr - 1'b1;
            end
        end
    endfunction

    assign empty_w = (count_q == COUNT_ZERO);
    assign full_w  = (count_q == COUNT_MAX);

    assign out_valid_o = !empty_w;
    assign out_fire_w  = out_valid_o && out_ready_i;
    assign do_pop_w    = out_fire_w;

    assign tail_ptr_w = empty_w ? wr_ptr_q : dec_ptr(wr_ptr_q);

    assign tail_valid_for_merge_w = (!empty_w) && !((count_q == COUNT_ONE) && out_fire_w);

    generate
        if (BYTE_OFFSET_WIDTH == 0) begin : gen_same_word_no_offset
            assign same_word_w = (in_addr_i == addr_buffer[tail_ptr_w]);
        end else begin : gen_same_word_with_offset
            wire [AXI_ADDR_WIDTH-BYTE_OFFSET_WIDTH-1:0] in_addr_word_w;
            wire [AXI_ADDR_WIDTH-BYTE_OFFSET_WIDTH-1:0] tail_addr_word_w;
            assign in_addr_word_w   = in_addr_i[AXI_ADDR_WIDTH-1:BYTE_OFFSET_WIDTH];
            assign tail_addr_word_w = addr_buffer[tail_ptr_w][AXI_ADDR_WIDTH-1:BYTE_OFFSET_WIDTH];
            assign same_word_w = (in_addr_word_w == tail_addr_word_w);
        end
    endgenerate

    assign same_id_w = (in_id_i == id_buffer[tail_ptr_w]);

    assign merge_possible_w = tail_valid_for_merge_w && same_word_w && same_id_w && !last_buffer[tail_ptr_w];
    assign in_ready_o       = !flush_i && (merge_possible_w || !full_w || out_fire_w);

    assign do_accept_w = in_valid_i && in_ready_o;
    assign do_merge_w  = do_accept_w && merge_possible_w;
    assign do_push_w   = do_accept_w && !merge_possible_w;

    assign merged_tail_data_w = (merge_buffer[tail_ptr_w] & ~in_strobe_mask_w) | (in_data_i & in_strobe_mask_w);
    assign merged_tail_strb_w = strb_buffer[tail_ptr_w] | in_strb_i;

    assign out_addr_o = addr_buffer[rd_ptr_q];
    assign out_data_o = merge_buffer[rd_ptr_q];
    assign out_strb_o = strb_buffer[rd_ptr_q];
    assign out_id_o   = id_buffer[rd_ptr_q];
    assign out_last_o = last_buffer[rd_ptr_q];

    assign empty_o      = empty_w;
    assign full_o       = full_w;
    assign occupancy_o  = count_q;

    integer reset_idx;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr_q          <= PTR_ZERO;
            wr_ptr_q          <= PTR_ZERO;
            count_q           <= COUNT_ZERO;
            accept_pulse_o    <= 1'b0;
            pop_pulse_o       <= 1'b0;
            merge_pulse_o     <= 1'b0;
            overflow_sticky_o <= 1'b0;
            for (reset_idx = 0; reset_idx < MERGE_BUFFER_DEPTH; reset_idx = reset_idx + 1) begin
                merge_buffer[reset_idx] <= {AXI_DATA_WIDTH{1'b0}};
                addr_buffer[reset_idx]  <= {AXI_ADDR_WIDTH{1'b0}};
                strb_buffer[reset_idx]  <= {AXI_STRB_WIDTH{1'b0}};
                id_buffer[reset_idx]    <= {AXI_ID_WIDTH{1'b0}};
                last_buffer[reset_idx]  <= 1'b0;
            end
        end else begin
            accept_pulse_o <= do_accept_w;
            pop_pulse_o    <= do_pop_w;
            merge_pulse_o  <= do_merge_w;

            if (flush_i) begin
                rd_ptr_q <= PTR_ZERO;
                wr_ptr_q <= PTR_ZERO;
                count_q  <= COUNT_ZERO;
            end else begin
                if (in_valid_i && !in_ready_o) begin
                    overflow_sticky_o <= 1'b1;
                end

                if (do_merge_w) begin
                    merge_buffer[tail_ptr_w] <= merged_tail_data_w;
                    strb_buffer[tail_ptr_w]  <= merged_tail_strb_w;
                    last_buffer[tail_ptr_w]  <= last_buffer[tail_ptr_w] | in_last_i;
                end

                if (do_push_w) begin
                    merge_buffer[wr_ptr_q] <= in_data_i;
                    addr_buffer[wr_ptr_q]  <= in_addr_i;
                    strb_buffer[wr_ptr_q]  <= in_strb_i;
                    id_buffer[wr_ptr_q]    <= in_id_i;
                    last_buffer[wr_ptr_q]  <= in_last_i;
                    wr_ptr_q               <= inc_ptr(wr_ptr_q);
                end

                if (do_pop_w) begin
                    rd_ptr_q <= inc_ptr(rd_ptr_q);
                end

                case ({do_push_w, do_pop_w})
                    2'b10: count_q <= count_q + COUNT_ONE;
                    2'b01: count_q <= count_q - COUNT_ONE;
                    default: count_q <= count_q;
                endcase
            end
        end
    end

endmodule

`default_nettype wire
