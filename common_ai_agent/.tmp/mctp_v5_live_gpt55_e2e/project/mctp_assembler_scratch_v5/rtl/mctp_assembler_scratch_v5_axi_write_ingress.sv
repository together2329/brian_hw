`include "mctp_assembler_scratch_v5_param.vh"

module mctp_assembler_scratch_v5_axi_write_ingress (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             assembly_enable,
    input  wire                                             drop_mode,
    input  wire [12:0]                                      configured_tu_bytes,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_ADDR_WIDTH-1:0] m_axi_awaddr,
    input  wire [7:0]                                       m_axi_awlen,
    input  wire [2:0]                                       m_axi_awsize,
    input  wire [1:0]                                       m_axi_awburst,
    input  wire                                             m_axi_awvalid,
    output wire                                             m_axi_awready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] m_axi_wdata,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] m_axi_wstrb,
    input  wire                                             m_axi_wlast,
    input  wire                                             m_axi_wvalid,
    output wire                                             m_axi_wready,
    output reg [1:0]                                       m_axi_bresp,
    output reg                                             m_axi_bvalid,
    input  wire                                             m_axi_bready,
    output reg                                             tlp_valid,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] tlp_word,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] tlp_strb,
    output reg [15:0]                                      tlp_byte_count,
    output reg [15:0]                                      tlp_awaddr,
    output reg [127:0]                                     first_tlp_header,
    output reg [127:0]                                     last_tlp_header,
    output reg [7:0]                                       packet_drop_reason,
    input  wire                                             payload_commit_valid,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_commit_addr,
    input  wire [12:0]                                      payload_commit_bytes,
    output wire                                             payload_replay_valid,
    input  wire                                             payload_replay_ready,
    output wire [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_replay_data,
    output wire [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_replay_strb,
    output wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_replay_addr,
    output wire [12:0]                                      payload_replay_bytes,
    output wire                                             payload_replay_busy,
    output wire                                             ingress_busy
);
    localparam [12:0] HEADER_BYTES = 13'd20;

    reg collecting_q;
    reg [7:0] beat_count_q;
    reg [15:0] byte_count_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] first_word_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] first_strb_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] beat_data_q [0:128];
    reg legacy_single_beat_q;
    reg replay_active_q;
    reg [12:0] replay_offset_q;
    reg [12:0] replay_total_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] replay_base_q;
    reg malformed_q;
    wire aw_accept;
    wire w_accept;
    wire aw_malformed;
    wire apb_access;
    wire pcie_vdm_parse;
    wire mctp_parse;
    wire context_assembly;
    wire sram_pack;
    wire descriptor_publish;
    wire axi_readback;
    wire unused_inputs;
    wire first_w_beat;
    wire [15:0] byte_count_base;
    wire [15:0] byte_count_next;
    wire [5:0] wstrb_count;
    wire [12:0] replay_remaining;
    wire [12:0] replay_emit_bytes;
    wire [12:0] payload_replay_header_skip;
    wire [7:0] store_beat_idx;

    assign aw_accept = m_axi_awvalid & m_axi_awready;
    assign w_accept = m_axi_wvalid & m_axi_wready;
    assign aw_malformed = (m_axi_awsize != 3'd5) | (m_axi_awburst != 2'd1) | (m_axi_awlen > 8'd128);
    assign ingress_busy = collecting_q;
    assign m_axi_awready = (~collecting_q) & (~m_axi_bvalid) & (~replay_active_q) & (~payload_commit_valid);
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
    assign byte_count_next = byte_count_base + {10'd0, wstrb_count};
    assign store_beat_idx = aw_accept ? 8'd0 : beat_count_q;
    assign replay_remaining = replay_total_q - replay_offset_q;
    assign replay_emit_bytes = (replay_remaining >= 13'd32) ? 13'd32 : replay_remaining;
    assign payload_replay_header_skip = legacy_single_beat_q ? 13'd0 : HEADER_BYTES;
    assign payload_replay_valid = replay_active_q;
    assign payload_replay_busy = replay_active_q;
    assign payload_replay_addr = replay_base_q + {3'd0, replay_offset_q};
    assign payload_replay_bytes = replay_emit_bytes;
    assign payload_replay_strb = (replay_emit_bytes >= 13'd32) ? 32'hffff_ffff :
        ((replay_emit_bytes == 13'd0) ? 32'd0 : ((32'h0000_0001 << replay_emit_bytes[4:0]) - 32'd1));

    assign wstrb_count = {5'd0, m_axi_wstrb[0]} + {5'd0, m_axi_wstrb[1]} +
        {5'd0, m_axi_wstrb[2]} + {5'd0, m_axi_wstrb[3]} +
        {5'd0, m_axi_wstrb[4]} + {5'd0, m_axi_wstrb[5]} +
        {5'd0, m_axi_wstrb[6]} + {5'd0, m_axi_wstrb[7]} +
        {5'd0, m_axi_wstrb[8]} + {5'd0, m_axi_wstrb[9]} +
        {5'd0, m_axi_wstrb[10]} + {5'd0, m_axi_wstrb[11]} +
        {5'd0, m_axi_wstrb[12]} + {5'd0, m_axi_wstrb[13]} +
        {5'd0, m_axi_wstrb[14]} + {5'd0, m_axi_wstrb[15]} +
        {5'd0, m_axi_wstrb[16]} + {5'd0, m_axi_wstrb[17]} +
        {5'd0, m_axi_wstrb[18]} + {5'd0, m_axi_wstrb[19]} +
        {5'd0, m_axi_wstrb[20]} + {5'd0, m_axi_wstrb[21]} +
        {5'd0, m_axi_wstrb[22]} + {5'd0, m_axi_wstrb[23]} +
        {5'd0, m_axi_wstrb[24]} + {5'd0, m_axi_wstrb[25]} +
        {5'd0, m_axi_wstrb[26]} + {5'd0, m_axi_wstrb[27]} +
        {5'd0, m_axi_wstrb[28]} + {5'd0, m_axi_wstrb[29]} +
        {5'd0, m_axi_wstrb[30]} + {5'd0, m_axi_wstrb[31]};

`define MCTP_REPLAY_BYTE(ID, OFFSET, LOW) \
    wire [12:0] payload_offset_``ID; \
    wire [12:0] raw_byte_offset_``ID; \
    wire [7:0] raw_beat_idx_``ID; \
    wire [4:0] raw_lane_idx_``ID; \
    wire [7:0] raw_shift_``ID; \
    wire [255:0] raw_beat_``ID; \
    wire legacy_header_byte_``ID; \
    assign payload_offset_``ID = replay_offset_q + OFFSET; \
    assign raw_byte_offset_``ID = payload_offset_``ID + payload_replay_header_skip; \
    assign raw_beat_idx_``ID = raw_byte_offset_``ID[12:5]; \
    assign raw_lane_idx_``ID = raw_byte_offset_``ID[4:0]; \
    assign raw_shift_``ID = {raw_lane_idx_``ID, 3'd0}; \
    assign raw_beat_``ID = beat_data_q[raw_beat_idx_``ID]; \
    assign legacy_header_byte_``ID = legacy_single_beat_q & (payload_offset_``ID >= 13'd16); \
    assign payload_replay_data[LOW +: 8] = ((payload_offset_``ID < replay_total_q) & (!legacy_header_byte_``ID)) ? raw_beat_``ID[raw_shift_``ID +: 8] : 8'd0;

    `MCTP_REPLAY_BYTE(00, 13'd0, 0)
    `MCTP_REPLAY_BYTE(01, 13'd1, 8)
    `MCTP_REPLAY_BYTE(02, 13'd2, 16)
    `MCTP_REPLAY_BYTE(03, 13'd3, 24)
    `MCTP_REPLAY_BYTE(04, 13'd4, 32)
    `MCTP_REPLAY_BYTE(05, 13'd5, 40)
    `MCTP_REPLAY_BYTE(06, 13'd6, 48)
    `MCTP_REPLAY_BYTE(07, 13'd7, 56)
    `MCTP_REPLAY_BYTE(08, 13'd8, 64)
    `MCTP_REPLAY_BYTE(09, 13'd9, 72)
    `MCTP_REPLAY_BYTE(10, 13'd10, 80)
    `MCTP_REPLAY_BYTE(11, 13'd11, 88)
    `MCTP_REPLAY_BYTE(12, 13'd12, 96)
    `MCTP_REPLAY_BYTE(13, 13'd13, 104)
    `MCTP_REPLAY_BYTE(14, 13'd14, 112)
    `MCTP_REPLAY_BYTE(15, 13'd15, 120)
    `MCTP_REPLAY_BYTE(16, 13'd16, 128)
    `MCTP_REPLAY_BYTE(17, 13'd17, 136)
    `MCTP_REPLAY_BYTE(18, 13'd18, 144)
    `MCTP_REPLAY_BYTE(19, 13'd19, 152)
    `MCTP_REPLAY_BYTE(20, 13'd20, 160)
    `MCTP_REPLAY_BYTE(21, 13'd21, 168)
    `MCTP_REPLAY_BYTE(22, 13'd22, 176)
    `MCTP_REPLAY_BYTE(23, 13'd23, 184)
    `MCTP_REPLAY_BYTE(24, 13'd24, 192)
    `MCTP_REPLAY_BYTE(25, 13'd25, 200)
    `MCTP_REPLAY_BYTE(26, 13'd26, 208)
    `MCTP_REPLAY_BYTE(27, 13'd27, 216)
    `MCTP_REPLAY_BYTE(28, 13'd28, 224)
    `MCTP_REPLAY_BYTE(29, 13'd29, 232)
    `MCTP_REPLAY_BYTE(30, 13'd30, 240)
    `MCTP_REPLAY_BYTE(31, 13'd31, 248)
`undef MCTP_REPLAY_BYTE

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            collecting_q <= 1'b0;
            beat_count_q <= 8'd0;
            byte_count_q <= 16'd0;
            first_word_q <= 256'd0;
            first_strb_q <= 32'd0;
            legacy_single_beat_q <= 1'b0;
            replay_active_q <= 1'b0;
            replay_offset_q <= 13'd0;
            replay_total_q <= 13'd0;
            replay_base_q <= 16'd0;
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
                legacy_single_beat_q <= (m_axi_awlen == 8'd0);
                tlp_awaddr <= m_axi_awaddr;
                malformed_q <= aw_malformed;
            end
            if (w_accept) begin
                beat_data_q[store_beat_idx] <= m_axi_wdata;
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
            if (payload_commit_valid & (payload_commit_bytes != 13'd0)) begin
                replay_active_q <= 1'b1;
                replay_offset_q <= 13'd0;
                replay_total_q <= payload_commit_bytes;
                replay_base_q <= payload_commit_addr;
            end else if (replay_active_q & payload_replay_ready) begin
                if (replay_remaining <= 13'd32) begin
                    replay_active_q <= 1'b0;
                    replay_offset_q <= 13'd0;
                    replay_total_q <= 13'd0;
                end else begin
                    replay_offset_q <= replay_offset_q + 13'd32;
                end
            end
        end
    end
endmodule
