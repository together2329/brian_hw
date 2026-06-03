`include "mctp_assembler_scratch_v5_param.vh"

module mctp_assembler_scratch_v5_axi_read_egress (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             raw_debug_read_enable,
    input  wire                                             descriptor_valid,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    input  wire [12:0]                                      descriptor_bytes,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_ADDR_WIDTH-1:0] m_axi_araddr,
    input  wire [7:0]                                       m_axi_arlen,
    input  wire [2:0]                                       m_axi_arsize,
    input  wire [1:0]                                       m_axi_arburst,
    input  wire                                             m_axi_arvalid,
    output wire                                             m_axi_arready,
    output reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] m_axi_rdata,
    output reg [1:0]                                       m_axi_rresp,
    output reg                                             m_axi_rlast,
    output reg                                             m_axi_rvalid,
    input  wire                                             m_axi_rready,
    output reg                                             rd_req_valid,
    input  wire                                             rd_req_ready,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] rd_req_addr,
    input  wire                                             rd_rsp_valid,
    output wire                                             rd_rsp_ready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] rd_rsp_data,
    input  wire                                             rd_rsp_error,
    output reg                                             descriptor_pop,
    output reg                                             read_error_pulse
);
    reg active_q;
    reg wait_rsp_q;
    reg read_has_descriptor_q;
    reg [8:0] beats_left_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q;
    wire [8:0] start_beats;
    wire ar_ok;
    wire unused_inputs;

    assign start_beats = descriptor_valid ?
        ((descriptor_bytes == 13'd0) ? 9'd1 : ({1'b0, descriptor_bytes[12:5]} + {8'd0, |descriptor_bytes[4:0]})) :
        ({1'b0, m_axi_arlen} + 9'd1);
    assign ar_ok = m_axi_arvalid & m_axi_arready;
    assign m_axi_arready = (!active_q) & (!m_axi_rvalid) & (!rd_req_valid) & (!wait_rsp_q);
    assign rd_rsp_ready = wait_rsp_q & (!m_axi_rvalid | m_axi_rready);
    assign unused_inputs = ^{m_axi_arsize, m_axi_arburst};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            active_q <= 1'b0;
            wait_rsp_q <= 1'b0;
            read_has_descriptor_q <= 1'b0;
            beats_left_q <= 9'd0;
            next_addr_q <= 16'd0;
            m_axi_rdata <= 256'd0;
            m_axi_rresp <= `MCTP_ASSEMBLER_SCRATCH_RESP_OKAY;
            m_axi_rlast <= 1'b0;
            m_axi_rvalid <= 1'b0;
            rd_req_valid <= 1'b0;
            rd_req_addr <= 16'd0;
            descriptor_pop <= 1'b0;
            read_error_pulse <= 1'b0;
        end else begin
            descriptor_pop <= 1'b0;
            read_error_pulse <= 1'b0;
            if (m_axi_rvalid & m_axi_rready) begin
                m_axi_rvalid <= 1'b0;
                if (m_axi_rlast) begin
                    active_q <= 1'b0;
                    if (read_has_descriptor_q) begin
                        descriptor_pop <= 1'b1;
                    end
                end else begin
                    rd_req_valid <= 1'b1;
                    rd_req_addr <= next_addr_q;
                    next_addr_q <= next_addr_q + 16'd32;
                end
            end
            if (rd_req_valid & rd_req_ready) begin
                rd_req_valid <= 1'b0;
                wait_rsp_q <= 1'b1;
            end
            if (wait_rsp_q & rd_rsp_valid & rd_rsp_ready) begin
                wait_rsp_q <= 1'b0;
                m_axi_rvalid <= 1'b1;
                m_axi_rlast <= beats_left_q <= 9'd1;
                m_axi_rdata <= rd_rsp_data;
                m_axi_rresp <= rd_rsp_error ? `MCTP_ASSEMBLER_SCRATCH_RESP_SLVERR : `MCTP_ASSEMBLER_SCRATCH_RESP_OKAY;
                read_error_pulse <= rd_rsp_error;
                if (beats_left_q != 9'd0) begin
                    beats_left_q <= beats_left_q - 9'd1;
                end
            end
            if (ar_ok) begin
                read_has_descriptor_q <= descriptor_valid;
                if (descriptor_valid | raw_debug_read_enable) begin
                    active_q <= 1'b1;
                    beats_left_q <= start_beats;
                    rd_req_valid <= 1'b1;
                    rd_req_addr <= descriptor_valid ? descriptor_base : m_axi_araddr;
                    next_addr_q <= (descriptor_valid ? descriptor_base : m_axi_araddr) + 16'd32;
                end else begin
                    m_axi_rvalid <= 1'b1;
                    m_axi_rlast <= 1'b1;
                    m_axi_rdata <= {255'd0, unused_inputs & 1'b0};
                    m_axi_rresp <= `MCTP_ASSEMBLER_SCRATCH_RESP_SLVERR;
                    read_error_pulse <= 1'b1;
                end
            end
        end
    end
endmodule
