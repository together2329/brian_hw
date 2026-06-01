`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_context_table (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             assembly_enable,
    input  logic                                             drop_mode,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit,
    input  logic                                             descriptor_full,
    input  logic                                             descriptor_pop,
    input  logic                                             fragment_valid,
    input  logic [7:0]                                       source_eid,
    input  logic [7:0]                                       destination_eid,
    input  logic                                             tag_owner,
    input  logic [2:0]                                       message_tag,
    input  logic [1:0]                                       packet_seq,
    input  logic                                             som,
    input  logic                                             eom,
    input  logic [7:0]                                       message_type,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_data_word,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_byte_strobe,
    input  logic [12:0]                                      payload_byte_count,
    input  logic [127:0]                                     first_tlp_header,
    input  logic [127:0]                                     last_tlp_header,
    input  logic [7:0]                                       packet_drop_reason_in,
    output logic                                             payload_write_valid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_write_data,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_write_strb,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_write_addr,
    output logic [12:0]                                      payload_write_bytes,
    output logic                                             descriptor_push,
    output logic [3:0]                                       descriptor_qid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    output logic [12:0]                                      descriptor_bytes,
    output logic [17:0]                                      descriptor_key,
    output logic [127:0]                                     descriptor_first_header,
    output logic [127:0]                                     descriptor_last_header,
    output logic                                             packet_drop_pulse,
    output logic                                             assembly_drop_pulse,
    output logic [7:0]                                       drop_reason,
    output logic [1:0]                                       ctx_state,
    output logic                                             ctx_valid,
    output logic                                             ctx_error,
    output logic [17:0]                                      ctx_key,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] ctx_payload_base,
    output logic [12:0]                                      ctx_payload_count,
    output logic [4:0]                                       ctx_partial_next_lane,
    output logic                                             ctx_partial_word_valid,
    output logic [3:0]                                       debug_context_id,
    output logic [17:0]                                      debug_context_key
);
    logic [1:0] state_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic valid_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic error_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [17:0] key_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] base_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [12:0] count_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [1:0] expected_seq_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];
    logic [127:0] first_header_q [0:`MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT-1];

    logic [17:0] incoming_key;
    logic match_found;
    logic free_found;
    logic [3:0] match_idx;
    logic [3:0] free_idx;
    logic [3:0] selected_idx;
    logic [16:0] selected_base_ext;
    logic [16:0] write_start_ext;
    logic [16:0] next_addr_ext;
    logic [12:0] selected_count;
    logic [12:0] next_payload_count;
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] write_start_addr;
    logic [4:0] write_next_lane;
    logic sequence_mismatch;
    logic sram_overflow;
    logic unused_context_inputs;
    integer find_i;
    integer reset_i;

    assign incoming_key = {source_eid, tag_owner, 6'd0, message_tag};
    assign unused_context_inputs = ^{message_type, destination_eid, descriptor_pop};

    always @(*) begin
        match_found = 1'b0;
        free_found = 1'b0;
        match_idx = 4'd0;
        free_idx = 4'd0;
        for (find_i = 0; find_i < `MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT; find_i = find_i + 1) begin
            if ((!match_found) & valid_q[find_i] & (key_q[find_i] == incoming_key)) begin
                match_found = 1'b1;
                match_idx = find_i[3:0];
            end
            if ((!free_found) & (!valid_q[find_i])) begin
                free_found = 1'b1;
                free_idx = find_i[3:0];
            end
        end
        selected_idx = match_found ? match_idx : {1'b0, message_tag};
        selected_base_ext = {1'b0, sram_base} + ({13'd0, selected_idx} << 12);
        write_start_addr = som ? selected_base_ext[15:0] : next_addr_q[selected_idx];
        write_start_ext = {1'b0, write_start_addr};
        next_addr_ext = write_start_ext + {4'd0, payload_byte_count};
        selected_count = match_found ? count_q[selected_idx] : 13'd0;
        next_payload_count = som ? payload_byte_count : (selected_count + payload_byte_count);
        write_next_lane = write_start_addr[4:0] + payload_byte_count[4:0];
        sequence_mismatch = match_found & (!som) & (packet_seq != expected_seq_q[selected_idx]);
        sram_overflow = next_addr_ext > {1'b0, sram_limit};
    end

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            for (reset_i = 0; reset_i < `MCTP_ASSEMBLER_SCRATCH_CONTEXT_COUNT; reset_i = reset_i + 1) begin
                state_q[reset_i] <= `MCTP_ASSEMBLER_SCRATCH_STATE_IDLE;
                valid_q[reset_i] <= 1'b0;
                error_q[reset_i] <= 1'b0;
                key_q[reset_i] <= 18'd0;
                base_q[reset_i] <= 16'd0;
                next_addr_q[reset_i] <= 16'd0;
                count_q[reset_i] <= 13'd0;
                expected_seq_q[reset_i] <= 2'd0;
                first_header_q[reset_i] <= 128'd0;
            end
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
                    error_q[selected_idx] <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (sequence_mismatch) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SEQUENCE_MISMATCH;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    error_q[selected_idx] <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (descriptor_full & eom) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_DESCRIPTOR_FULL;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    error_q[selected_idx] <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else if (sram_overflow) begin
                    assembly_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SRAM_OVERFLOW;
                    state_q[selected_idx] <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    error_q[selected_idx] <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                end else begin
                    valid_q[selected_idx] <= 1'b1;
                    error_q[selected_idx] <= 1'b0;
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
                    ctx_partial_word_valid <= |write_next_lane;
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
