`include "mctp_assembler_scratch_v4_param.vh"

module mctp_assembler_scratch_v4_mctp_parser (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             vdm_valid,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] vdm_word,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] vdm_strb,
    input  wire [12:0]                                      vdm_payload_bytes,
    input  wire [12:0]                                      configured_tu_bytes,
    input  wire [127:0]                                     vdm_first_header,
    input  wire [127:0]                                     vdm_last_header,
    input  wire [7:0]                                       parser_drop_reason_in,
    output reg                                             fragment_valid,
    output reg [7:0]                                       source_eid,
    output reg [7:0]                                       destination_eid,
    output reg                                             tag_owner,
    output reg [2:0]                                       message_tag,
    output reg [1:0]                                       packet_seq,
    output reg                                             som,
    output reg                                             eom,
    output reg [7:0]                                       message_type,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_data_word,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_byte_strobe,
    output reg [12:0]                                      payload_byte_count,
    output reg [127:0]                                     first_tlp_header,
    output reg [127:0]                                     last_tlp_header,
    output reg [7:0]                                       packet_drop_reason
);
    wire bad_mctp_len;
    wire nonfinal_bad_align;
    wire unused_inputs;
    wire [12:0] encoded_payload_len;
    wire [12:0] decoded_payload_len;
    wire payload_tu_overflow;
    wire [31:0] decoded_payload_strobe;
    wire [17:0] context_key;
    wire [17:0] debug_context_key;

    assign bad_mctp_len = vdm_payload_bytes < 13'd4;
    assign nonfinal_bad_align = (~vdm_word[150]) & (vdm_payload_bytes[1:0] != 2'd0);
    assign context_key = {source_eid, tag_owner, 6'd0, message_tag};
    assign debug_context_key = context_key;
    assign unused_inputs = ^{configured_tu_bytes, vdm_strb,
                             vdm_word[255:237], vdm_word[127:0], debug_context_key};
    assign encoded_payload_len = vdm_word[236:224];
    assign decoded_payload_len = (vdm_payload_bytes > 13'd36) ? (vdm_payload_bytes - 13'd4) :
        ((encoded_payload_len != 13'd0) ? encoded_payload_len :
        ((vdm_payload_bytes > 13'd4) ? (vdm_payload_bytes - 13'd4) : 13'd0));
    assign payload_tu_overflow = (configured_tu_bytes != 13'd0) &
        (decoded_payload_len > configured_tu_bytes);
    assign decoded_payload_strobe = (decoded_payload_len >= 13'd32) ? 32'hffff_ffff :
        ((decoded_payload_len == 13'd0) ? 32'd0 : ((32'h0000_0001 << decoded_payload_len[4:0]) - 32'd1));

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
                payload_data_word <= vdm_word;
                payload_byte_strobe <= decoded_payload_strobe;
                first_tlp_header <= vdm_first_header;
                last_tlp_header <= vdm_last_header;
                payload_byte_count <= decoded_payload_len;
                if (parser_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE) begin
                    packet_drop_reason <= parser_drop_reason_in;
                end else if (bad_mctp_len) begin
                    packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_BAD_MCTP_HEADER;
                end else if (payload_tu_overflow) begin
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
