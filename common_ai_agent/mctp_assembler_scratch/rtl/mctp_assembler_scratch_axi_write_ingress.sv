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
    logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] first_word_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] first_strb_q;
    logic malformed_q;
    logic aw_accept;
    logic w_accept;
    logic aw_malformed;
    logic apb_access;
    logic pcie_vdm_parse;
    logic mctp_parse;
    logic context_assembly;
    logic sram_pack;
    logic descriptor_publish;
    logic axi_readback;
    logic unused_inputs;
    logic first_w_beat;
    logic [15:0] byte_count_base;
    logic [15:0] byte_count_next;

    assign aw_accept = m_axi_awvalid & m_axi_awready;
    assign w_accept = m_axi_wvalid & m_axi_wready;
    assign aw_malformed = (m_axi_awsize != 3'd5) | (m_axi_awburst != 2'd1) | (m_axi_awlen > 8'd128);
    assign ingress_busy = collecting_q;
    assign m_axi_awready = (~collecting_q) & (~m_axi_bvalid);
    assign m_axi_wready = collecting_q | aw_accept;
    assign apb_access = 1'b0;
    assign pcie_vdm_parse = tlp_valid;
    assign mctp_parse = tlp_valid;
    assign context_assembly = tlp_valid & (packet_drop_reason == `MCTP_ASSEMBLER_SCRATCH_DROP_NONE);
    assign sram_pack = context_assembly;
    assign descriptor_publish = m_axi_bvalid & m_axi_bready;
    assign axi_readback = 1'b0;
    assign unused_inputs = ^{configured_tu_bytes, m_axi_awaddr, apb_access, pcie_vdm_parse,
                             mctp_parse, context_assembly, sram_pack, descriptor_publish,
                             axi_readback};
    assign first_w_beat = aw_accept | (beat_count_q == 8'd0);
    assign byte_count_base = aw_accept ? 16'd0 : byte_count_q;
    assign byte_count_next = byte_count_base + {10'd0, strobe_byte_count(m_axi_wstrb)};

    function automatic [5:0] strobe_byte_count(input logic [31:0] strobe);
        integer idx;
        begin
            strobe_byte_count = 6'd0;
            for (idx = 0; idx < 32; idx = idx + 1) begin
                strobe_byte_count = strobe_byte_count + {5'd0, strobe[idx]};
            end
        end
    endfunction

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            collecting_q <= 1'b0;
            beat_count_q <= 8'd0;
            byte_count_q <= 16'd0;
            first_word_q <= 256'd0;
            first_strb_q <= 32'd0;
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
                first_word_q <= 256'd0;
                first_strb_q <= 32'd0;
                tlp_awaddr <= m_axi_awaddr;
                malformed_q <= aw_malformed;
            end
            if (w_accept) begin
                last_tlp_header <= m_axi_wdata[127:0];
                if (first_w_beat) begin
                    first_tlp_header <= m_axi_wdata[127:0];
                    first_word_q <= m_axi_wdata;
                    first_strb_q <= m_axi_wstrb;
                end
                beat_count_q <= (aw_accept ? 8'd0 : beat_count_q) + 8'd1;
                byte_count_q <= byte_count_next;
                if (m_axi_wlast) begin
                    collecting_q <= 1'b0;
                    tlp_valid <= 1'b1;
                    tlp_word <= first_w_beat ? m_axi_wdata : first_word_q;
                    tlp_strb <= first_w_beat ? m_axi_wstrb : first_strb_q;
                    tlp_byte_count <= byte_count_next;
                    m_axi_bvalid <= 1'b1;
                    m_axi_bresp <= `MCTP_ASSEMBLER_SCRATCH_BRESP_OKAY | {1'b0, unused_inputs & 1'b0};
                    if (!assembly_enable) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                    end else if (drop_mode) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                    end else if (malformed_q | (aw_accept & aw_malformed)) begin
                        packet_drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_MALFORMED_TLP;
                    end
                end
            end
        end
    end
endmodule
