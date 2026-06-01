`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_axi_read_egress (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             raw_debug_read_enable,
    input  logic                                             descriptor_valid,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    input  logic [12:0]                                      descriptor_bytes,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_ADDR_WIDTH-1:0] m_axi_araddr,
    input  logic [7:0]                                       m_axi_arlen,
    input  logic [2:0]                                       m_axi_arsize,
    input  logic [1:0]                                       m_axi_arburst,
    input  logic                                             m_axi_arvalid,
    output logic                                             m_axi_arready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] m_axi_rdata,
    output logic [1:0]                                       m_axi_rresp,
    output logic                                             m_axi_rlast,
    output logic                                             m_axi_rvalid,
    input  logic                                             m_axi_rready,
    output logic                                             rd_req_valid,
    input  logic                                             rd_req_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] rd_req_addr,
    input  logic                                             rd_rsp_valid,
    output logic                                             rd_rsp_ready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] rd_rsp_data,
    input  logic                                             rd_rsp_error,
    output logic                                             descriptor_pop,
    output logic                                             read_error_pulse
);
    logic active_q;
    logic wait_rsp_q;
    logic read_has_descriptor_q;
    logic [8:0] beats_left_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q;
    logic [8:0] start_beats;
    logic ar_ok;
    logic unused_inputs;

    assign start_beats = descriptor_valid ? bytes_to_beats(descriptor_bytes) : ({1'b0, m_axi_arlen} + 9'd1);
    assign ar_ok = m_axi_arvalid & m_axi_arready;
    assign m_axi_arready = (!active_q) & (!m_axi_rvalid) & (!rd_req_valid) & (!wait_rsp_q);
    assign rd_rsp_ready = wait_rsp_q & (!m_axi_rvalid | m_axi_rready);
    assign unused_inputs = ^{m_axi_arsize, m_axi_arburst};

    function automatic [8:0] bytes_to_beats(input logic [12:0] byte_count);
        begin
            if (byte_count == 13'd0) begin
                bytes_to_beats = 9'd1;
            end else begin
                bytes_to_beats = {1'b0, byte_count[12:5]} + {8'd0, |byte_count[4:0]};
            end
        end
    endfunction

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
