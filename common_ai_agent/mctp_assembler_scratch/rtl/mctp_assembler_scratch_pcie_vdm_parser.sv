`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_pcie_vdm_parser (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             tlp_valid,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] tlp_word,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] tlp_strb,
    input  logic [15:0]                                      tlp_byte_count,
    input  logic [15:0]                                      tlp_awaddr,
    input  logic [127:0]                                     first_tlp_header,
    input  logic [127:0]                                     last_tlp_header,
    input  logic [7:0]                                       ingress_drop_reason,
    output logic                                             vdm_valid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] vdm_word,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] vdm_strb,
    output logic [12:0]                                      vdm_payload_bytes,
    output logic [127:0]                                     vdm_first_header,
    output logic [127:0]                                     vdm_last_header,
    output logic [7:0]                                       packet_drop_reason,
    output logic                                             debug_vdm_valid
);
    logic unused_inputs;

    assign unused_inputs = ^tlp_awaddr;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            vdm_valid <= 1'b0;
            vdm_word <= 256'd0;
            vdm_strb <= 32'd0;
            vdm_payload_bytes <= 13'd0;
            vdm_first_header <= 128'd0;
            vdm_last_header <= 128'd0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            debug_vdm_valid <= 1'b0;
        end else begin
            vdm_valid <= 1'b0;
            debug_vdm_valid <= 1'b0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            if (tlp_valid) begin
                vdm_word <= tlp_word;
                vdm_strb <= tlp_strb;
                vdm_first_header <= first_tlp_header;
                vdm_last_header <= last_tlp_header;
                if (ingress_drop_reason != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE) begin
                    packet_drop_reason <= ingress_drop_reason;
                end else if (tlp_byte_count < 16'd20) begin
                    packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_MALFORMED_TLP;
                end else if (tlp_strb == 32'd0) begin
                    packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_UNSUPPORTED_VDM;
                end else begin
                    vdm_valid <= 1'b1;
                    debug_vdm_valid <= 1'b1;
                    vdm_payload_bytes <= (tlp_byte_count[12:0] - 13'd16) | {12'd0, unused_inputs & 1'b0};
                end
            end
        end
    end
endmodule
