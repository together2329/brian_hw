`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             pclk,
    input  logic                                             presetn,
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
    input  logic [15:0]                                      paddr,
    input  logic                                             psel,
    input  logic                                             penable,
    input  logic                                             pwrite,
    input  logic [31:0]                                      pwdata,
    input  logic [3:0]                                       pstrb,
    output logic [31:0]                                      prdata,
    output logic                                             pready,
    output logic                                             pslverr,
    output logic                                             sram_wr_valid,
    input  logic                                             sram_wr_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_wr_addr,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_wr_data,
    output logic [31:0]                                      sram_wr_strb,
    output logic                                             sram_rd_req_valid,
    input  logic                                             sram_rd_req_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_rd_req_addr,
    input  logic                                             sram_rd_rsp_valid,
    output logic                                             sram_rd_rsp_ready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_rd_rsp_data,
    input  logic                                             sram_rd_rsp_error,
    output logic                                             irq,
    output logic [3:0]                                       debug_context_id,
    output logic [17:0]                                      debug_context_key,
    output logic                                             debug_drop_pulse,
    output logic                                             debug_vdm_valid
);
    logic enable_pclk;
    logic drop_mode_pclk;
    logic raw_debug_read_enable_pclk;
    logic [12:0] configured_tu_bytes_pclk;
    logic [15:0] sram_base_pclk;
    logic [15:0] sram_limit_pclk;
    logic enable_axi;
    logic drop_mode_axi;
    logic raw_debug_read_enable_axi;
    logic [12:0] configured_tu_bytes_axi;
    logic [15:0] sram_base_axi;
    logic [15:0] sram_limit_axi;
    logic [255:0] tlp_word;
    logic [31:0] tlp_strb;
    logic [15:0] tlp_byte_count;
    logic [15:0] tlp_awaddr;
    logic [127:0] first_tlp_header;
    logic [127:0] last_tlp_header;
    logic [7:0] ingress_drop_reason;
    logic tlp_valid;
    logic ingress_busy;
    logic vdm_valid;
    logic [255:0] vdm_word;
    logic [31:0] vdm_strb;
    logic [12:0] vdm_payload_bytes;
    logic [127:0] vdm_first_header;
    logic [127:0] vdm_last_header;
    logic [7:0] vdm_drop_reason;
    logic fragment_valid;
    logic [7:0] source_eid;
    logic [7:0] destination_eid;
    logic tag_owner;
    logic [2:0] message_tag;
    logic [1:0] packet_seq;
    logic som;
    logic eom;
    logic [7:0] message_type;
    logic [255:0] payload_data_word;
    logic [31:0] payload_byte_strobe;
    logic [12:0] payload_byte_count;
    logic [127:0] fragment_first_header;
    logic [127:0] fragment_last_header;
    logic [7:0] mctp_drop_reason;
    logic payload_write_valid;
    logic [255:0] payload_write_data;
    logic [31:0] payload_write_strb;
    logic [15:0] payload_write_addr;
    logic [12:0] payload_write_bytes;
    logic descriptor_push;
    logic [3:0] descriptor_qid;
    logic [15:0] descriptor_base;
    logic [12:0] descriptor_bytes;
    logic [17:0] descriptor_key;
    logic [127:0] descriptor_first_header;
    logic [127:0] descriptor_last_header;
    logic packet_drop_pulse_axi;
    logic assembly_drop_pulse_axi;
    logic [7:0] drop_reason;
    logic [1:0] ctx_state;
    logic ctx_valid;
    logic ctx_error;
    logic [17:0] ctx_key;
    logic [15:0] ctx_payload_base;
    logic [12:0] ctx_payload_count;
    logic [4:0] ctx_partial_next_lane;
    logic ctx_partial_word_valid;
    logic descriptor_valid;
    logic descriptor_full;
    logic [3:0] descriptor_count;
    logic [3:0] read_qid;
    logic [15:0] read_base;
    logic [12:0] read_bytes;
    logic [17:0] read_key;
    logic [127:0] read_first_header;
    logic [127:0] read_last_header;
    logic descriptor_pop;
    logic read_error_pulse_axi;
    logic pack_wr_valid;
    logic pack_wr_ready;
    logic [15:0] pack_wr_addr;
    logic [255:0] pack_wr_data;
    logic [31:0] pack_wr_strb;
    logic [4:0] pack_next_lane;
    logic pack_partial_valid;
    logic rd_req_valid;
    logic rd_req_ready;
    logic [15:0] rd_req_addr;
    logic rd_rsp_valid;
    logic rd_rsp_ready;
    logic [255:0] rd_rsp_data;
    logic rd_rsp_error;
    logic packet_drop_event_pclk;
    logic assembly_drop_event_pclk;
    logic descriptor_event_pclk;
    logic read_error_event_pclk;
    logic unused_top;

    assign debug_drop_pulse = packet_drop_pulse_axi | assembly_drop_pulse_axi;
    assign unused_top = ^{ingress_busy, read_qid, read_key, read_first_header, read_last_header,
                          pack_next_lane, pack_partial_valid};

    mctp_assembler_scratch_axi_write_ingress u_axi_write_ingress (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .assembly_enable(enable_axi),
        .drop_mode(drop_mode_axi),
        .configured_tu_bytes(configured_tu_bytes_axi),
        .m_axi_awaddr(m_axi_awaddr),
        .m_axi_awlen(m_axi_awlen),
        .m_axi_awsize(m_axi_awsize),
        .m_axi_awburst(m_axi_awburst),
        .m_axi_awvalid(m_axi_awvalid),
        .m_axi_awready(m_axi_awready),
        .m_axi_wdata(m_axi_wdata),
        .m_axi_wstrb(m_axi_wstrb),
        .m_axi_wlast(m_axi_wlast),
        .m_axi_wvalid(m_axi_wvalid),
        .m_axi_wready(m_axi_wready),
        .m_axi_bresp(m_axi_bresp),
        .m_axi_bvalid(m_axi_bvalid),
        .m_axi_bready(m_axi_bready),
        .tlp_valid(tlp_valid),
        .tlp_word(tlp_word),
        .tlp_strb(tlp_strb),
        .tlp_byte_count(tlp_byte_count),
        .tlp_awaddr(tlp_awaddr),
        .first_tlp_header(first_tlp_header),
        .last_tlp_header(last_tlp_header),
        .packet_drop_reason(ingress_drop_reason),
        .ingress_busy(ingress_busy)
    );

    mctp_assembler_scratch_pcie_vdm_parser u_pcie_vdm_parser (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .tlp_valid(tlp_valid),
        .tlp_word(tlp_word),
        .tlp_strb(tlp_strb),
        .tlp_byte_count(tlp_byte_count),
        .tlp_awaddr(tlp_awaddr),
        .first_tlp_header(first_tlp_header),
        .last_tlp_header(last_tlp_header),
        .ingress_drop_reason(ingress_drop_reason),
        .vdm_valid(vdm_valid),
        .vdm_word(vdm_word),
        .vdm_strb(vdm_strb),
        .vdm_payload_bytes(vdm_payload_bytes),
        .vdm_first_header(vdm_first_header),
        .vdm_last_header(vdm_last_header),
        .packet_drop_reason(vdm_drop_reason),
        .debug_vdm_valid(debug_vdm_valid)
    );

    mctp_assembler_scratch_mctp_parser u_mctp_parser (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .vdm_valid(vdm_valid),
        .vdm_word(vdm_word),
        .vdm_strb(vdm_strb),
        .vdm_payload_bytes(vdm_payload_bytes),
        .configured_tu_bytes(configured_tu_bytes_axi),
        .vdm_first_header(vdm_first_header),
        .vdm_last_header(vdm_last_header),
        .parser_drop_reason_in(vdm_drop_reason),
        .fragment_valid(fragment_valid),
        .source_eid(source_eid),
        .destination_eid(destination_eid),
        .tag_owner(tag_owner),
        .message_tag(message_tag),
        .packet_seq(packet_seq),
        .som(som),
        .eom(eom),
        .message_type(message_type),
        .payload_data_word(payload_data_word),
        .payload_byte_strobe(payload_byte_strobe),
        .payload_byte_count(payload_byte_count),
        .first_tlp_header(fragment_first_header),
        .last_tlp_header(fragment_last_header),
        .packet_drop_reason(mctp_drop_reason)
    );

    mctp_assembler_scratch_context_table u_context_table (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .assembly_enable(enable_axi),
        .drop_mode(drop_mode_axi),
        .sram_base(sram_base_axi),
        .sram_limit(sram_limit_axi),
        .descriptor_full(descriptor_full),
        .descriptor_pop(descriptor_pop),
        .fragment_valid(fragment_valid),
        .source_eid(source_eid),
        .destination_eid(destination_eid),
        .tag_owner(tag_owner),
        .message_tag(message_tag),
        .packet_seq(packet_seq),
        .som(som),
        .eom(eom),
        .message_type(message_type),
        .payload_data_word(payload_data_word),
        .payload_byte_strobe(payload_byte_strobe),
        .payload_byte_count(payload_byte_count),
        .first_tlp_header(fragment_first_header),
        .last_tlp_header(fragment_last_header),
        .packet_drop_reason_in(mctp_drop_reason),
        .payload_write_valid(payload_write_valid),
        .payload_write_data(payload_write_data),
        .payload_write_strb(payload_write_strb),
        .payload_write_addr(payload_write_addr),
        .payload_write_bytes(payload_write_bytes),
        .descriptor_push(descriptor_push),
        .descriptor_qid(descriptor_qid),
        .descriptor_base(descriptor_base),
        .descriptor_bytes(descriptor_bytes),
        .descriptor_key(descriptor_key),
        .descriptor_first_header(descriptor_first_header),
        .descriptor_last_header(descriptor_last_header),
        .packet_drop_pulse(packet_drop_pulse_axi),
        .assembly_drop_pulse(assembly_drop_pulse_axi),
        .drop_reason(drop_reason),
        .ctx_state(ctx_state),
        .ctx_valid(ctx_valid),
        .ctx_error(ctx_error),
        .ctx_key(ctx_key),
        .ctx_payload_base(ctx_payload_base),
        .ctx_payload_count(ctx_payload_count),
        .ctx_partial_next_lane(ctx_partial_next_lane),
        .ctx_partial_word_valid(ctx_partial_word_valid),
        .debug_context_id(debug_context_id),
        .debug_context_key(debug_context_key)
    );

    mctp_assembler_scratch_sram_packer u_sram_packer (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .payload_write_valid(payload_write_valid),
        .payload_write_data(payload_write_data),
        .payload_write_strb(payload_write_strb),
        .payload_write_addr(payload_write_addr),
        .payload_write_bytes(payload_write_bytes),
        .sram_wr_valid(pack_wr_valid),
        .sram_wr_ready(pack_wr_ready),
        .sram_wr_addr(pack_wr_addr),
        .sram_wr_data(pack_wr_data),
        .sram_wr_strb(pack_wr_strb),
        .pack_next_lane(pack_next_lane),
        .pack_partial_valid(pack_partial_valid)
    );

    mctp_assembler_scratch_descriptor_queue u_descriptor_queue (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .descriptor_push(descriptor_push),
        .descriptor_qid(descriptor_qid),
        .descriptor_base(descriptor_base),
        .descriptor_bytes(descriptor_bytes),
        .descriptor_key(descriptor_key),
        .descriptor_first_header(descriptor_first_header),
        .descriptor_last_header(descriptor_last_header),
        .descriptor_pop(descriptor_pop),
        .descriptor_valid(descriptor_valid),
        .descriptor_full(descriptor_full),
        .descriptor_count(descriptor_count),
        .read_qid(read_qid),
        .read_base(read_base),
        .read_bytes(read_bytes),
        .read_key(read_key),
        .read_first_header(read_first_header),
        .read_last_header(read_last_header)
    );

    mctp_assembler_scratch_axi_read_egress u_axi_read_egress (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .raw_debug_read_enable(raw_debug_read_enable_axi),
        .descriptor_valid(descriptor_valid),
        .descriptor_base(read_base),
        .descriptor_bytes(read_bytes),
        .m_axi_araddr(m_axi_araddr),
        .m_axi_arlen(m_axi_arlen),
        .m_axi_arsize(m_axi_arsize),
        .m_axi_arburst(m_axi_arburst),
        .m_axi_arvalid(m_axi_arvalid),
        .m_axi_arready(m_axi_arready),
        .m_axi_rdata(m_axi_rdata),
        .m_axi_rresp(m_axi_rresp),
        .m_axi_rlast(m_axi_rlast),
        .m_axi_rvalid(m_axi_rvalid),
        .m_axi_rready(m_axi_rready),
        .rd_req_valid(rd_req_valid),
        .rd_req_ready(rd_req_ready),
        .rd_req_addr(rd_req_addr),
        .rd_rsp_valid(rd_rsp_valid),
        .rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_data(rd_rsp_data),
        .rd_rsp_error(rd_rsp_error),
        .descriptor_pop(descriptor_pop),
        .read_error_pulse(read_error_pulse_axi)
    );

    mctp_assembler_scratch_sram_arbiter u_sram_arbiter (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .pack_wr_valid(pack_wr_valid),
        .pack_wr_ready(pack_wr_ready),
        .pack_wr_addr(pack_wr_addr),
        .pack_wr_data(pack_wr_data),
        .pack_wr_strb(pack_wr_strb),
        .rd_req_valid(rd_req_valid),
        .rd_req_ready(rd_req_ready),
        .rd_req_addr(rd_req_addr),
        .rd_rsp_valid(rd_rsp_valid),
        .rd_rsp_ready(rd_rsp_ready),
        .rd_rsp_data(rd_rsp_data),
        .rd_rsp_error(rd_rsp_error),
        .sram_wr_valid(sram_wr_valid),
        .sram_wr_ready(sram_wr_ready),
        .sram_wr_addr(sram_wr_addr),
        .sram_wr_data(sram_wr_data),
        .sram_wr_strb(sram_wr_strb),
        .sram_rd_req_valid(sram_rd_req_valid),
        .sram_rd_req_ready(sram_rd_req_ready),
        .sram_rd_req_addr(sram_rd_req_addr),
        .sram_rd_rsp_valid(sram_rd_rsp_valid),
        .sram_rd_rsp_ready(sram_rd_rsp_ready),
        .sram_rd_rsp_data(sram_rd_rsp_data),
        .sram_rd_rsp_error(sram_rd_rsp_error)
    );

    mctp_assembler_scratch_cdc u_cdc (
        .axi_aclk(axi_aclk),
        .axi_aresetn(axi_aresetn),
        .pclk(pclk),
        .presetn(presetn),
        .enable_pclk(enable_pclk),
        .drop_mode_pclk(drop_mode_pclk),
        .raw_debug_read_enable_pclk(raw_debug_read_enable_pclk),
        .configured_tu_bytes_pclk(configured_tu_bytes_pclk),
        .sram_base_pclk(sram_base_pclk),
        .sram_limit_pclk(sram_limit_pclk),
        .enable_axi(enable_axi),
        .drop_mode_axi(drop_mode_axi),
        .raw_debug_read_enable_axi(raw_debug_read_enable_axi),
        .configured_tu_bytes_axi(configured_tu_bytes_axi),
        .sram_base_axi(sram_base_axi),
        .sram_limit_axi(sram_limit_axi),
        .packet_drop_axi(packet_drop_pulse_axi),
        .assembly_drop_axi(assembly_drop_pulse_axi),
        .descriptor_event_axi(descriptor_push),
        .read_error_axi(read_error_pulse_axi),
        .packet_drop_pclk(packet_drop_event_pclk),
        .assembly_drop_pclk(assembly_drop_event_pclk),
        .descriptor_event_pclk(descriptor_event_pclk),
        .read_error_pclk(read_error_event_pclk)
    );

    mctp_assembler_scratch_apb_regfile u_apb_regfile (
        .pclk(pclk),
        .presetn(presetn),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .pstrb(pstrb),
        .prdata(prdata),
        .pready(pready),
        .pslverr(pslverr),
        .ctx_state(ctx_state),
        .ctx_valid(ctx_valid),
        .ctx_error(ctx_error),
        .ctx_key(ctx_key),
        .ctx_payload_base(ctx_payload_base),
        .ctx_payload_count(ctx_payload_count),
        .ctx_partial_next_lane(ctx_partial_next_lane),
        .ctx_partial_word_valid(ctx_partial_word_valid),
        .descriptor_count(descriptor_count),
        .descriptor_event(descriptor_event_pclk),
        .packet_drop_event(packet_drop_event_pclk),
        .assembly_drop_event(assembly_drop_event_pclk),
        .read_error_event(read_error_event_pclk),
        .drop_reason(drop_reason),
        .enable_reg(enable_pclk),
        .drop_mode_reg(drop_mode_pclk),
        .raw_debug_read_enable(raw_debug_read_enable_pclk),
        .configured_tu_bytes(configured_tu_bytes_pclk),
        .sram_base(sram_base_pclk),
        .sram_limit(sram_limit_pclk),
        .irq(irq)
    );
endmodule
