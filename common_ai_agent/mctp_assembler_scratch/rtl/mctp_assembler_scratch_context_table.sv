`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_context_table (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             assembly_enable,
    input  wire                                             drop_mode,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit,
    input  wire                                             descriptor_full,
    input  wire                                             descriptor_pop,
    input  wire                                             fragment_valid,
    input  wire [7:0]                                       source_eid,
    input  wire [7:0]                                       destination_eid,
    input  wire                                             tag_owner,
    input  wire [2:0]                                       message_tag,
    input  wire [1:0]                                       packet_seq,
    input  wire                                             som,
    input  wire                                             eom,
    input  wire [7:0]                                       message_type,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_data_word,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_byte_strobe,
    input  wire [12:0]                                      payload_byte_count,
    input  wire [127:0]                                     first_tlp_header,
    input  wire [127:0]                                     last_tlp_header,
    input  wire [7:0]                                       packet_drop_reason_in,
    output reg                                             payload_write_valid,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_write_data,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_write_strb,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_write_addr,
    output reg [12:0]                                      payload_write_bytes,
    output reg                                             descriptor_push,
    output reg [3:0]                                       descriptor_qid,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    output reg [12:0]                                      descriptor_bytes,
    output reg [17:0]                                      descriptor_key,
    output reg [127:0]                                     descriptor_first_header,
    output reg [127:0]                                     descriptor_last_header,
    output reg                                             packet_drop_pulse,
    output reg                                             assembly_drop_pulse,
    output reg [7:0]                                       drop_reason,
    output reg [1:0]                                       ctx_state,
    output reg                                             ctx_valid,
    output reg                                             ctx_error,
    output reg [17:0]                                      ctx_key,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] ctx_payload_base,
    output reg [12:0]                                      ctx_payload_count,
    output reg [4:0]                                       ctx_partial_next_lane,
    output reg                                             ctx_partial_word_valid,
    output reg [3:0]                                       debug_context_id,
    output reg [17:0]                                      debug_context_key
);
    reg [1:0] state_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1:0] valid_q;
    reg [17:0] key_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] base_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [12:0] count_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [1:0] expected_seq_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    reg [127:0] first_header_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];

    wire [17:0] incoming_key;
    wire match_found;
    wire [3:0] match_idx;
    wire [3:0] selected_idx;
    wire [16:0] selected_base_ext;
    wire [16:0] write_start_ext;
    wire [16:0] next_addr_ext;
    wire [12:0] selected_count;
    wire [12:0] next_payload_count;
    wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] write_start_addr;
    wire [4:0] write_next_lane;
    wire sequence_mismatch;
    wire sram_overflow;
    wire unused_context_inputs;
    wire [`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1:0] match_vec;

    assign incoming_key = {source_eid, tag_owner, 6'd0, message_tag};
    assign unused_context_inputs = ^{message_type, destination_eid, descriptor_pop, selected_base_ext[16]};
    assign match_vec[0] = valid_q[0] & (key_q[0] == incoming_key);
    assign match_vec[1] = valid_q[1] & (key_q[1] == incoming_key);
    assign match_vec[2] = valid_q[2] & (key_q[2] == incoming_key);
    assign match_vec[3] = valid_q[3] & (key_q[3] == incoming_key);
    assign match_vec[4] = valid_q[4] & (key_q[4] == incoming_key);
    assign match_vec[5] = valid_q[5] & (key_q[5] == incoming_key);
    assign match_vec[6] = valid_q[6] & (key_q[6] == incoming_key);
    assign match_vec[7] = valid_q[7] & (key_q[7] == incoming_key);
    assign match_vec[8] = valid_q[8] & (key_q[8] == incoming_key);
    assign match_vec[9] = valid_q[9] & (key_q[9] == incoming_key);
    assign match_vec[10] = valid_q[10] & (key_q[10] == incoming_key);
    assign match_vec[11] = valid_q[11] & (key_q[11] == incoming_key);
    assign match_vec[12] = valid_q[12] & (key_q[12] == incoming_key);
    assign match_vec[13] = valid_q[13] & (key_q[13] == incoming_key);
    assign match_vec[14] = valid_q[14] & (key_q[14] == incoming_key);
    assign match_found = |match_vec;
    assign match_idx = match_vec[0] ? 4'd0 :
        (match_vec[1] ? 4'd1 :
        (match_vec[2] ? 4'd2 :
        (match_vec[3] ? 4'd3 :
        (match_vec[4] ? 4'd4 :
        (match_vec[5] ? 4'd5 :
        (match_vec[6] ? 4'd6 :
        (match_vec[7] ? 4'd7 :
        (match_vec[8] ? 4'd8 :
        (match_vec[9] ? 4'd9 :
        (match_vec[10] ? 4'd10 :
        (match_vec[11] ? 4'd11 :
        (match_vec[12] ? 4'd12 :
        (match_vec[13] ? 4'd13 :
        (match_vec[14] ? 4'd14 : 4'd0))))))))))))));
    assign selected_idx = match_found ? match_idx : {1'b0, message_tag};
    assign selected_base_ext = {1'b0, sram_base} + ({13'd0, selected_idx} << 12);
    assign write_start_addr = som ? selected_base_ext[15:0] : next_addr_q[selected_idx];
    assign write_start_ext = {1'b0, write_start_addr};
    assign next_addr_ext = write_start_ext + {4'd0, payload_byte_count};
    assign selected_count = match_found ? count_q[selected_idx] : 13'd0;
    assign next_payload_count = som ? payload_byte_count : (selected_count + payload_byte_count);
    assign write_next_lane = write_start_addr[4:0] + payload_byte_count[4:0];
    assign sequence_mismatch = match_found & (!som) & (packet_seq != expected_seq_q[selected_idx]);
    assign sram_overflow = next_addr_ext > {1'b0, sram_limit};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            valid_q <= {`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT{1'b0}};
            payload_write_valid <= 1'b0;
            payload_write_data <= 256'd0;
            payload_write_strb <= 32'd0;
            payload_write_addr <= 16'd0;
            payload_write_bytes <= 13'd0;
            descriptor_push <= 1'b0;
            descriptor_qid <= 4'd0;
            descriptor_base <= 16'd0;
            descriptor_bytes <= 13'd0;
            descriptor_key <= 18'd0;
            descriptor_first_header <= 128'd0;
            descriptor_last_header <= 128'd0;
            packet_drop_pulse <= 1'b0;
            assembly_drop_pulse <= 1'b0;
            drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_IDLE;
            ctx_valid <= 1'b0;
            ctx_error <= 1'b0;
            ctx_key <= 18'd0;
            ctx_payload_base <= 16'd0;
            ctx_payload_count <= 13'd0;
            ctx_partial_next_lane <= 5'd0;
            ctx_partial_word_valid <= 1'b0;
            debug_context_id <= 4'd0;
            debug_context_key <= 18'd0;
        end else begin
            payload_write_valid <= 1'b0;
            descriptor_push <= 1'b0;
            packet_drop_pulse <= 1'b0;
            assembly_drop_pulse <= 1'b0;
            drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            if (fragment_valid | (packet_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE)) begin
                debug_context_id <= selected_idx;
                debug_context_key <= incoming_key;
                if (!assembly_enable | drop_mode) begin
                    packet_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                end else if (packet_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE) begin
                    packet_drop_pulse <= 1'b1;
                    drop_reason <= packet_drop_reason_in;
                end else if ((!som) & (!match_found)) begin
                    packet_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_UNEXPECTED_MIDDLE_END;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (som & match_found & (state_q[selected_idx] == `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING)) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_DUPLICATE_SOM;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (sequence_mismatch) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SEQUENCE_MISMATCH;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (descriptor_full & eom) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_DESCRIPTOR_FULL;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (sram_overflow) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SRAM_OVERFLOW;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else begin
                    valid_q[selected_idx] <= 1'b1;
                    key_q[selected_idx] <= incoming_key;
                    if (som | (!match_found)) begin
                        base_q[selected_idx] <= selected_base_ext[15:0];
                        first_header_q[selected_idx] <= first_tlp_header;
                    end
                    count_q[selected_idx] <= next_payload_count;
                    next_addr_q[selected_idx] <= next_addr_ext[15:0];
                    expected_seq_q[selected_idx] <= packet_seq + 2'd1;
                    state_q[selected_idx] <= eom ? `MCTP_ASSEMBLER_SCRATCH_STATE_DONE_WAIT_DESCRIPTOR_POP :
                        `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING;

                    payload_write_valid <= 1'b1;
                    payload_write_data <= payload_data_word;
                    payload_write_strb <= payload_byte_strobe;
                    payload_write_addr <= write_start_addr;
                    payload_write_bytes <= payload_byte_count;
                    ctx_state <= eom ? `MCTP_ASSEMBLER_SCRATCH_STATE_DONE_WAIT_DESCRIPTOR_POP :
                        `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING;
                    ctx_valid <= 1'b1;
                    ctx_error <= 1'b0;
                    ctx_key <= incoming_key;
                    ctx_payload_base <= (som | (!match_found)) ? selected_base_ext[15:0] : base_q[selected_idx];
                    ctx_payload_count <= next_payload_count;
                    ctx_partial_next_lane <= write_next_lane;
                    ctx_partial_word_valid <= (!eom) & |write_next_lane;
                    if (eom) begin
                        descriptor_push <= 1'b1;
                        descriptor_qid <= selected_idx;
                        descriptor_base <= (som | (!match_found)) ? selected_base_ext[15:0] : base_q[selected_idx];
                        descriptor_bytes <= next_payload_count;
                        descriptor_key <= incoming_key | {17'd0, unused_context_inputs & 1'b0};
                        descriptor_first_header <= (som | (!match_found)) ? first_tlp_header : first_header_q[selected_idx];
                        descriptor_last_header <= last_tlp_header;
                    end
                end
            end
        end
    end
endmodule
