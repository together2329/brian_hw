`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_mctp_parser (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             vdm_valid,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] vdm_word,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] vdm_strb,
    input  logic [12:0]                                      vdm_payload_bytes,
    input  logic [12:0]                                      configured_tu_bytes,
    input  logic [127:0]                                     vdm_first_header,
    input  logic [127:0]                                     vdm_last_header,
    input  logic [7:0]                                       parser_drop_reason_in,
    output logic                                             fragment_valid,
    output logic [7:0]                                       source_eid,
    output logic [7:0]                                       destination_eid,
    output logic                                             tag_owner,
    output logic [2:0]                                       message_tag,
    output logic [1:0]                                       packet_seq,
    output logic                                             som,
    output logic                                             eom,
    output logic [7:0]                                       message_type,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_data_word,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_byte_strobe,
    output logic [12:0]                                      payload_byte_count,
    output logic [127:0]                                     first_tlp_header,
    output logic [127:0]                                     last_tlp_header,
    output logic [7:0]                                       packet_drop_reason
);
    logic bad_mctp_len;
    logic nonfinal_bad_align;
    logic unused_inputs;
    logic [12:0] encoded_payload_len;
    logic [12:0] decoded_payload_len;
    logic [17:0] context_key;
    logic [17:0] debug_context_key;

    assign bad_mctp_len = vdm_payload_bytes < 13'd4;
    assign nonfinal_bad_align = (~vdm_word[150]) & (vdm_payload_bytes[1:0] != 2'd0);
    assign context_key = {source_eid, tag_owner, 6'd0, message_tag};
    assign debug_context_key = context_key;
    assign unused_inputs = ^{configured_tu_bytes, vdm_strb[31], vdm_strb[19:0],
                             vdm_word[255:237], vdm_word[127:0], debug_context_key};
    assign encoded_payload_len = vdm_word[236:224];
    assign decoded_payload_len = (encoded_payload_len != 13'd0) ? encoded_payload_len :
        ((vdm_payload_bytes > 13'd4) ? (vdm_payload_bytes - 13'd4) : 13'd0);

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            fragment_valid <= 1'b0;
            source_eid <= 8'd0;
            destination_eid <= 8'd0;
            tag_owner <= 1'b0;
            message_tag <= 3'd0;
            packet_seq <= 2'd0;
            som <= 1'b0;
            eom <= 1'b0;
            message_type <= 8'd0;
            payload_data_word <= 256'd0;
            payload_byte_strobe <= 32'd0;
            payload_byte_count <= 13'd0;
            first_tlp_header <= 128'd0;
            last_tlp_header <= 128'd0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
        end else begin
            fragment_valid <= 1'b0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            if (vdm_valid | (parser_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE)) begin
                source_eid <= vdm_word[143:136];
                destination_eid <= vdm_word[135:128];
                message_tag <= vdm_word[146:144];
                tag_owner <= vdm_word[147];
                packet_seq <= vdm_word[149:148];
                eom <= vdm_word[150];
                som <= vdm_word[151];
                message_type <= vdm_word[159:152];
                payload_data_word <= {160'd0, 32'd0, vdm_word[223:160]};
                payload_byte_strobe <= {20'd0, vdm_strb[31:20]};
                first_tlp_header <= vdm_first_header;
                last_tlp_header <= vdm_last_header;
                payload_byte_count <= decoded_payload_len;
                if (parser_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE) begin
                    packet_drop_reason <= parser_drop_reason_in;
                end else if (bad_mctp_len) begin
                    packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_BAD_MCTP_HEADER;
                end else if (nonfinal_bad_align) begin
                    packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_BAD_PAD_OR_ALIGNMENT;
                end else begin
                    fragment_valid <= 1'b1;
                    payload_byte_count <= (decoded_payload_len | {12'd0, unused_inputs & 1'b0});
                end
            end
        end
    end
endmodule
