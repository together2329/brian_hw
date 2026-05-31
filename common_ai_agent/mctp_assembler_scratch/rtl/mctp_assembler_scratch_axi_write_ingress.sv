`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_axi_write_ingress (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             assembly_enable,
    input  logic                                             drop_mode,
    input  logic [12:0]                                      configured_tu_bytes,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_ADDR_WIDTH-1:0] m_axi_awaddr,
    input  logic [7:0]                                       m_axi_awlen,
    input  logic [2:0]                                       m_axi_awsize,
    input  logic [1:0]                                       m_axi_awburst,
    input  logic                                             m_axi_awvalid,
    output logic                                             m_axi_awready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] m_axi_wdata,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] m_axi_wstrb,
    input  logic                                             m_axi_wlast,
    input  logic                                             m_axi_wvalid,
    output logic                                             m_axi_wready,
    output logic [1:0]                                       m_axi_bresp,
    output logic                                             m_axi_bvalid,
    input  logic                                             m_axi_bready,
    output logic                                             tlp_valid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] tlp_word,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] tlp_strb,
    output logic [15:0]                                      tlp_byte_count,
    output logic [15:0]                                      tlp_awaddr,
    output logic [127:0]                                     first_tlp_header,
    output logic [127:0]                                     last_tlp_header,
    output logic [7:0]                                       packet_drop_reason,
    output logic                                             ingress_busy
);
    logic collecting_q;
    logic [7:0] beat_count_q;
    logic [15:0] byte_count_q;
    logic malformed_q;
    logic aw_accept;
    logic w_accept;
    logic unused_inputs;

    assign aw_accept = m_axi_awvalid & m_axi_awready;
    assign w_accept = m_axi_wvalid & m_axi_wready;
    assign ingress_busy = collecting_q;
    assign m_axi_awready = (~collecting_q) & (~m_axi_bvalid);
    assign m_axi_wready = collecting_q | aw_accept;
    assign unused_inputs = ^{configured_tu_bytes, m_axi_awaddr};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            collecting_q <= 1'b0;
            beat_count_q <= 8'd0;
            byte_count_q <= 16'd0;
            malformed_q <= 1'b0;
            m_axi_bresp <= `MCTP_ASSEMBLER_SCRATCH_BRESP_OKAY;
            m_axi_bvalid <= 1'b0;
            tlp_valid <= 1'b0;
            tlp_word <= 256'd0;
            tlp_strb <= 32'd0;
            tlp_byte_count <= 16'd0;
            tlp_awaddr <= 16'd0;
            first_tlp_header <= 128'd0;
            last_tlp_header <= 128'd0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
        end else begin
            tlp_valid <= 1'b0;
            packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            if (m_axi_bvalid & m_axi_bready) begin
                m_axi_bvalid <= 1'b0;
            end
            if (aw_accept) begin
                collecting_q <= 1'b1;
                beat_count_q <= 8'd0;
                byte_count_q <= 16'd0;
                tlp_awaddr <= m_axi_awaddr;
                malformed_q <= (m_axi_awsize != 3'd5) | (m_axi_awburst != 2'd1) | (m_axi_awlen > 8'd128);
            end
            if (w_accept) begin
                tlp_word <= m_axi_wdata;
                tlp_strb <= m_axi_wstrb;
                last_tlp_header <= m_axi_wdata[127:0];
                if (beat_count_q == 8'd0) begin
                    first_tlp_header <= m_axi_wdata[127:0];
                end
                beat_count_q <= beat_count_q + 8'd1;
                if (m_axi_wstrb == 32'd0) begin
                    byte_count_q <= byte_count_q;
                end else begin
                    byte_count_q <= byte_count_q + 16'd32;
                end
                if (m_axi_wlast) begin
                    collecting_q <= 1'b0;
                    tlp_valid <= 1'b1;
                    tlp_byte_count <= (m_axi_wstrb == 32'd0) ? byte_count_q : (byte_count_q + 16'd32);
                    m_axi_bvalid <= 1'b1;
                    m_axi_bresp <= `MCTP_ASSEMBLER_SCRATCH_BRESP_OKAY | {1'b0, unused_inputs & 1'b0};
                    if (!assembly_enable) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                    end else if (drop_mode) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                    end else if (malformed_q | (beat_count_q == 8'd0)) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_MALFORMED_TLP;
                    end
                end
            end
        end
    end
endmodule
