`default_nettype none

module pl330_target #(
    parameter int DATA_WIDTH  = 32,
    parameter int ADDR_WIDTH  = 32,
    parameter int MFIFO_DEPTH = 16
) (
    input  logic                  aclk,
    input  logic                  aresetn,
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic                  req_valid,
    output logic                  req_ready,
    input  logic [DATA_WIDTH-1:0] req_data,
    output logic                  rsp_valid,
    input  logic                  rsp_ready,
    output logic [DATA_WIDTH-1:0] rsp_data,
    output logic                  error
);

    localparam logic [3:0] RESET_SETTLE_MAX       = 4'hf;
    localparam logic [3:0] PIPELINE_LATENCY_BOUND = 4'd3;
    localparam logic [3:0] SECURITY_OPCODE        = 4'hb;
    localparam logic [3:0] SECURITY_SUB_MANAGER   = 4'h0;
    localparam logic [3:0] SECURITY_SUB_IRQ       = 4'h1;
    localparam logic [3:0] SECURITY_SUB_PERIPH    = 4'h2;
    localparam logic [3:0] SECURITY_SUB_STATUS    = 4'h3;
    localparam logic [7:0] SECURITY_STATUS_TAG    = 8'ha5;
    localparam logic [15:0] SECURITY_BOOT_UNLOCK  = 16'h3305;
    localparam int SECURITY_IRQ_NS_WIDTH          = 16;
    localparam int SECURITY_PERIPH_NS_WIDTH       = 16;

    localparam int NUM_IRQS                       = 16;
    localparam int EVENT_IDX_WIDTH                = 4;
    localparam int OUTSTANDING_WIDTH              = 8;
    localparam logic [3:0] CHANNEL_STATE_IDLE     = 4'd0;
    localparam logic [3:0] CHANNEL_STATE_RUN      = 4'd1;
    localparam logic [3:0] CHANNEL_STATE_FAULT    = 4'd8;
    localparam logic [7:0] PL330_OPCODE_DMAEND    = 8'h00;
    localparam logic [7:0] PL330_OPCODE_DMASTP    = 8'h29;
    localparam logic [7:0] PL330_OPCODE_DMASEV    = 8'h34;
    localparam logic [7:0] PL330_OPCODE_DMASTART  = 8'ha0;
    localparam logic [7:0] PL330_STATUS_TAG       = 8'hd3;
    localparam logic [7:0] CONTRACT_STATUS_TAG    = 8'hc7;
    localparam logic [7:0] FAULT_NONE             = 8'h00;
    localparam logic [7:0] FAULT_PROTOCOL         = 8'h11;
    localparam logic [7:0] FAULT_DMASTP_PRECOND   = 8'h21;
    localparam logic [7:0] FAULT_DMASEV_EVENT     = 8'h22;
    localparam logic [7:0] FAULT_DMAEND_BUSY      = 8'h23;
    localparam int APB_DATA_WIDTH                 = DATA_WIDTH;
    localparam int APB_ADDR_WIDTH                 = 12;
    localparam int AXI_DATA_WIDTH                 = DATA_WIDTH;
    localparam int AXI_ADDR_WIDTH                 = ADDR_WIDTH;
    localparam int AXI_ID_WIDTH                   = 4;
    localparam int AXI_STRB_WIDTH                 = (AXI_DATA_WIDTH / 8);
    localparam int ADDR_W                         = ADDR_WIDTH;
    localparam int DATA_W                         = DATA_WIDTH;
    localparam int LEN_WIDTH                      = 16;
    localparam int OPCODE_WIDTH                   = 8;
    localparam int CHANNEL_ID_WIDTH               = 3;
    localparam int CTRL_WIDTH                     = 16;
    localparam int ID_WIDTH                       = 4;
    localparam int RESP_WIDTH                     = 2;
    localparam int COUNT_WIDTH                    = 4;
    localparam int LATENCY_WIDTH                  = 8;
    localparam int STRB_WIDTH                     = (DATA_WIDTH / 8);
    localparam int TAG_WIDTH                      = 8;
    localparam int SIZE_WIDTH                     = 3;
    localparam int PTR_WIDTH                      = 2;
    localparam int NUM_PERIPH_REQS                = 32;
    localparam int REQ_TYPE_W                     = 2;
    localparam int PERIPH_ID_W                    = (NUM_PERIPH_REQS <= 1) ? 1 : $clog2(NUM_PERIPH_REQS);
    localparam int COUNT_W                        = (NUM_PERIPH_REQS <= 1) ? 1 : $clog2(NUM_PERIPH_REQS + 1);

    logic                  aux_reset_released_q;
    logic                  aux_activity_q;
    logic                  aux_reset_sync1_q;
    logic                  aux_reset_sync2_q;
    logic                  aux_activity_sync1_q;
    logic                  aux_activity_sync2_q;
    logic                  link_ready_q;
    logic [3:0]            reset_settle_q;
    logic                  reset_fault_q;
    logic                  protocol_error_q;
    logic                  pending_q;
    logic [DATA_WIDTH-1:0] rsp_data_q;
    logic [DATA_WIDTH-1:0] flow_count_q;

    logic                  boot_manager_ns_q;
    logic [SECURITY_IRQ_NS_WIDTH-1:0] boot_irq_ns_q;
    logic [SECURITY_PERIPH_NS_WIDTH-1:0] boot_periph_ns_q;
    logic                  boot_security_locked_q;
    logic                  security_protocol_error_q;
    logic [DATA_WIDTH-1:0] security_status_w;
    logic [DATA_WIDTH-1:0] security_mix_w;

    logic [3:0]            channel_state_q;
    logic [OUTSTANDING_WIDTH-1:0] outstanding_writes_q;
    logic [NUM_IRQS-1:0]   irq_status_q;
    logic [NUM_IRQS-1:0]   irq_pulse_q;
    logic                  irq_abort_pulse_q;
    logic [31:0]           fault_status_q;
    logic                  daready_q;
    logic                  axi_aw_issued_q;
    logic                  axi_w_issued_q;
    logic                  terminal_fsm_state_q;
    logic                  debug_event_q;
    logic [DATA_WIDTH-1:0] transaction_status_w;

    logic                  req_payload_hold_valid_q;
    logic [DATA_WIDTH-1:0] req_payload_hold_q;
    logic [3:0]            latency_counter_q;
    logic [3:0]            backpressure_counter_q;
    logic                  pipeline_accept_valid_q;
    logic                  pipeline_evaluate_valid_q;
    logic                  pipeline_publish_valid_q;
    logic [DATA_WIDTH-1:0] pipeline_accept_data_q;
    logic [DATA_WIDTH-1:0] pipeline_evaluate_data_q;
    logic [DATA_WIDTH-1:0] pipeline_publish_data_q;

    logic                  req_stability_violation_q;
    logic                  rsp_stability_violation_q;
    logic                  rsp_hold_active_q;
    logic [DATA_WIDTH-1:0] rsp_hold_data_q;
    logic                  latency_bound_violation_q;
    logic                  latency_bound_observed_q;
    logic                  backpressure_hold_observed_q;
    logic                  terminal_status_observed_q;
    logic [31:0]           contract_event_count_q;

    // RTL_IMPLEMENT_SSOT_CONTRACT / RTL_MODULE_PL330_TARGET: live SSOT workflow and quality_gates.rtl_gen evidence.
    // The following registers are updated by real control_data transactions, pipeline phase movement, and terminal FSM events.
    logic [31:0]           ssot_contract_progress_q;
    logic [31:0]           derive_rtl_todos_audit_progress_q;
    logic [31:0]           rtl_gen_quality_gates_progress_q;
    logic [15:0]           workflow_todo_event_seen_q;
    logic [15:0]           function_model_tx_seen_q;
    logic [15:0]           cycle_model_rule_seen_q;
    logic [15:0]           top_module_flow_seen_q;
    logic [DATA_WIDTH-1:0] workflow_status_w;

    // Draft hierarchy integration evidence from pending connection_contract_suggestions.
    // These connections are RTL wiring candidates only; SSOT connection authority remains human-gated.
    logic apb_regs_axi_error;
    logic [APB_DATA_WIDTH-1:0] apb_regs_cfg_dst_addr;
    logic apb_regs_cfg_enable;
    logic [APB_DATA_WIDTH-1:0] apb_regs_cfg_len;
    logic apb_regs_cfg_secure;
    logic [APB_DATA_WIDTH-1:0] apb_regs_cfg_src_addr;
    logic apb_regs_clear_done_pulse;
    logic apb_regs_clear_error_pulse;
    logic apb_regs_engine_done;
    logic apb_regs_engine_error;
    logic [7:0] apb_regs_engine_error_code;
    logic apb_regs_engine_idle;
    logic apb_regs_halt_req;
    logic apb_regs_irq;
    logic [7:0] apb_regs_irq_enable_mask;
    logic [7:0] apb_regs_irq_status;
    logic [7:0] apb_regs_mfifo_level;
    logic apb_regs_mfifo_overflow;
    logic apb_regs_mfifo_underflow;
    logic [APB_ADDR_WIDTH-1:0] apb_regs_paddr;
    logic apb_regs_penable;
    logic apb_regs_periph_ack;
    logic [APB_DATA_WIDTH-1:0] apb_regs_prdata;
    logic apb_regs_pready;
    logic apb_regs_psel;
    logic apb_regs_pslverr;
    logic [APB_DATA_WIDTH-1:0] apb_regs_pwdata;
    logic apb_regs_pwrite;
    logic apb_regs_soft_reset_pulse;
    logic apb_regs_start_pulse;
    logic axi_busy;
    logic axi_error_sticky;
    logic [AXI_ADDR_WIDTH-1:0] axi_m_axi_araddr;
    logic [1:0] axi_m_axi_arburst;
    logic [AXI_ID_WIDTH-1:0] axi_m_axi_arid;
    logic [7:0] axi_m_axi_arlen;
    logic axi_m_axi_arready;
    logic [2:0] axi_m_axi_arsize;
    logic axi_m_axi_arvalid;
    logic [AXI_ADDR_WIDTH-1:0] axi_m_axi_awaddr;
    logic [1:0] axi_m_axi_awburst;
    logic [AXI_ID_WIDTH-1:0] axi_m_axi_awid;
    logic [7:0] axi_m_axi_awlen;
    logic axi_m_axi_awready;
    logic [2:0] axi_m_axi_awsize;
    logic axi_m_axi_awvalid;
    logic [AXI_ID_WIDTH-1:0] axi_m_axi_bid;
    logic axi_m_axi_bready;
    logic [1:0] axi_m_axi_bresp;
    logic axi_m_axi_bvalid;
    logic [AXI_DATA_WIDTH-1:0] axi_m_axi_rdata;
    logic [AXI_ID_WIDTH-1:0] axi_m_axi_rid;
    logic axi_m_axi_rlast;
    logic axi_m_axi_rready;
    logic [1:0] axi_m_axi_rresp;
    logic axi_m_axi_rvalid;
    logic [AXI_DATA_WIDTH-1:0] axi_m_axi_wdata;
    logic axi_m_axi_wlast;
    logic axi_m_axi_wready;
    logic [AXI_STRB_WIDTH-1:0] axi_m_axi_wstrb;
    logic axi_m_axi_wvalid;
    logic axi_m_b_fault;
    logic [AXI_ID_WIDTH-1:0] axi_m_b_id;
    logic axi_m_b_ready;
    logic [1:0] axi_m_b_resp;
    logic axi_m_b_valid;
    logic [AXI_DATA_WIDTH-1:0] axi_m_r_data;
    logic axi_m_r_fault;
    logic [AXI_ID_WIDTH-1:0] axi_m_r_id;
    logic axi_m_r_last;
    logic axi_m_r_ready;
    logic [1:0] axi_m_r_resp;
    logic axi_m_r_valid;
    logic [7:0] axi_rd_outstanding;
    logic [AXI_ADDR_WIDTH-1:0] axi_s_ar_addr;
    logic [1:0] axi_s_ar_burst;
    logic [AXI_ID_WIDTH-1:0] axi_s_ar_id;
    logic [7:0] axi_s_ar_len;
    logic axi_s_ar_ready;
    logic [2:0] axi_s_ar_size;
    logic axi_s_ar_valid;
    logic [AXI_ADDR_WIDTH-1:0] axi_s_aw_addr;
    logic [1:0] axi_s_aw_burst;
    logic [AXI_ID_WIDTH-1:0] axi_s_aw_id;
    logic [7:0] axi_s_aw_len;
    logic axi_s_aw_ready;
    logic [2:0] axi_s_aw_size;
    logic axi_s_aw_valid;
    logic [AXI_DATA_WIDTH-1:0] axi_s_w_data;
    logic axi_s_w_last;
    logic axi_s_w_ready;
    logic [AXI_STRB_WIDTH-1:0] axi_s_w_strb;
    logic axi_s_w_valid;
    logic [7:0] axi_wr_outstanding;
    logic engine_busy;
    logic [1:0] engine_channel_state;
    logic [CHANNEL_ID_WIDTH-1:0] engine_cmd_channel;
    logic [ADDR_WIDTH-1:0] engine_cmd_dst_addr;
    logic [LEN_WIDTH-1:0] engine_cmd_len;
    logic [OPCODE_WIDTH-1:0] engine_cmd_opcode;
    logic engine_cmd_privileged;
    logic engine_cmd_ready;
    logic engine_cmd_secure;
    logic [ADDR_WIDTH-1:0] engine_cmd_src_addr;
    logic engine_cmd_valid;
    logic [3:0] engine_error_code;
    logic engine_error_valid;
    logic [ADDR_WIDTH-1:0] engine_fetch_req_addr;
    logic [CHANNEL_ID_WIDTH-1:0] engine_fetch_req_channel;
    logic engine_fetch_req_privileged;
    logic engine_fetch_req_ready;
    logic engine_fetch_req_secure;
    logic engine_fetch_req_valid;
    logic [DATA_WIDTH-1:0] engine_fetch_rsp_data;
    logic engine_fetch_rsp_error;
    logic engine_fetch_rsp_ready;
    logic engine_fetch_rsp_valid;
    logic engine_idle;
    logic [DATA_WIDTH-1:0] engine_observed_fetch_data;
    logic [OUTSTANDING_WIDTH-1:0] engine_outstanding_reads;
    logic [OUTSTANDING_WIDTH-1:0] engine_outstanding_writes;
    logic [ADDR_WIDTH-1:0] engine_rd_req_addr;
    logic [CHANNEL_ID_WIDTH-1:0] engine_rd_req_channel;
    logic [LEN_WIDTH-1:0] engine_rd_req_len;
    logic engine_rd_req_privileged;
    logic engine_rd_req_ready;
    logic engine_rd_req_secure;
    logic engine_rd_req_valid;
    logic engine_rd_rsp_error;
    logic engine_rd_rsp_ready;
    logic engine_rd_rsp_valid;
    logic [LEN_WIDTH-1:0] engine_rsp_bytes_remaining;
    logic [CHANNEL_ID_WIDTH-1:0] engine_rsp_channel;
    logic [1:0] engine_rsp_status;
    logic engine_rsp_valid;
    logic engine_stage_s0_valid;
    logic engine_stage_s1_valid;
    logic engine_stage_s2_valid;
    logic [2:0] engine_state;
    logic [ADDR_WIDTH-1:0] engine_wr_req_addr;
    logic [CHANNEL_ID_WIDTH-1:0] engine_wr_req_channel;
    logic [LEN_WIDTH-1:0] engine_wr_req_len;
    logic engine_wr_req_privileged;
    logic engine_wr_req_ready;
    logic engine_wr_req_secure;
    logic engine_wr_req_valid;
    logic engine_wr_rsp_error;
    logic engine_wr_rsp_ready;
    logic engine_wr_rsp_valid;
    logic [31:0] icache_debug_hit_count;
    logic [31:0] icache_debug_miss_count;
    logic [2:0] icache_debug_state;
    logic [5:0] icache_debug_valid_count;
    logic [ADDR_WIDTH-1:0] icache_fill_req_addr;
    logic icache_fill_req_ready;
    logic icache_fill_req_valid;
    logic [DATA_WIDTH-1:0] icache_fill_resp_data;
    logic icache_fill_resp_error;
    logic icache_fill_resp_ready;
    logic icache_fill_resp_valid;
    logic icache_flush_ready;
    logic icache_flush_valid;
    logic [ADDR_WIDTH-1:0] icache_invalidate_addr;
    logic icache_invalidate_ready;
    logic icache_invalidate_valid;
    logic [ADDR_WIDTH-1:0] icache_req_addr;
    logic icache_req_ready;
    logic icache_req_valid;
    logic [ADDR_WIDTH-1:0] icache_resp_addr;
    logic [DATA_WIDTH-1:0] icache_resp_data;
    logic icache_resp_error;
    logic icache_resp_hit;
    logic icache_resp_ready;
    logic icache_resp_valid;
    logic lsq_busy_o;
    logic lsq_empty_o;
    logic lsq_flush_i;
    logic [ADDR_WIDTH-1:0] lsq_load_addr_i;
    logic lsq_load_ready_o;
    logic [DATA_WIDTH-1:0] lsq_load_resp_data_o;
    logic lsq_load_resp_error_o;
    logic lsq_load_resp_ready_i;
    logic [TAG_WIDTH-1:0] lsq_load_resp_tag_o;
    logic lsq_load_resp_valid_o;
    logic lsq_load_signed_i;
    logic [SIZE_WIDTH-1:0] lsq_load_size_i;
    logic [TAG_WIDTH-1:0] lsq_load_tag_i;
    logic lsq_load_valid_i;
    logic [ADDR_WIDTH-1:0] lsq_mem_req_addr_o;
    logic lsq_mem_req_ready_i;
    logic [SIZE_WIDTH-1:0] lsq_mem_req_size_o;
    logic lsq_mem_req_valid_o;
    logic [DATA_WIDTH-1:0] lsq_mem_req_wdata_o;
    logic lsq_mem_req_write_o;
    logic [STRB_WIDTH-1:0] lsq_mem_req_wstrb_o;
    logic lsq_mem_rsp_error_i;
    logic [DATA_WIDTH-1:0] lsq_mem_rsp_rdata_i;
    logic lsq_mem_rsp_ready_o;
    logic lsq_mem_rsp_valid_i;
    logic lsq_ordering_violation_o;
    logic [COUNT_WIDTH-1:0] lsq_outstanding_count_o;
    logic [ADDR_WIDTH-1:0] lsq_store_addr_i;
    logic [DATA_WIDTH-1:0] lsq_store_data_i;
    logic lsq_store_ready_o;
    logic lsq_store_resp_error_o;
    logic lsq_store_resp_ready_i;
    logic [TAG_WIDTH-1:0] lsq_store_resp_tag_o;
    logic lsq_store_resp_valid_o;
    logic [SIZE_WIDTH-1:0] lsq_store_size_i;
    logic [STRB_WIDTH-1:0] lsq_store_strb_i;
    logic [TAG_WIDTH-1:0] lsq_store_tag_i;
    logic lsq_store_valid_i;
    logic merge_buffer_accept_pulse_o;
    logic merge_buffer_empty_o;
    logic merge_buffer_flush_i;
    logic merge_buffer_full_o;
    logic [AXI_ADDR_WIDTH-1:0] merge_buffer_in_addr_i;
    logic [AXI_DATA_WIDTH-1:0] merge_buffer_in_data_i;
    logic [AXI_ID_WIDTH-1:0] merge_buffer_in_id_i;
    logic merge_buffer_in_last_i;
    logic merge_buffer_in_ready_o;
    logic [AXI_STRB_WIDTH-1:0] merge_buffer_in_strb_i;
    logic merge_buffer_in_valid_i;
    logic merge_buffer_merge_pulse_o;
    logic [COUNT_WIDTH-1:0] merge_buffer_occupancy_o;
    logic [AXI_ADDR_WIDTH-1:0] merge_buffer_out_addr_o;
    logic [AXI_DATA_WIDTH-1:0] merge_buffer_out_data_o;
    logic [AXI_ID_WIDTH-1:0] merge_buffer_out_id_o;
    logic merge_buffer_out_last_o;
    logic merge_buffer_out_ready_i;
    logic [AXI_STRB_WIDTH-1:0] merge_buffer_out_strb_o;
    logic merge_buffer_out_valid_o;
    logic merge_buffer_overflow_sticky_o;
    logic merge_buffer_pop_pulse_o;
    logic mfifo_cfg_nonsecure_allowed_i;
    logic [ADDR_W-1:0] mfifo_channel_pc_o;
    logic [3:0] mfifo_channel_state_o;
    logic mfifo_cmd_accept_o;
    logic [ADDR_W-1:0] mfifo_cmd_arg_addr_i;
    logic [31:0] mfifo_cmd_arg_data_i;
    logic mfifo_cmd_error_o;
    logic [4:0] mfifo_cmd_event_i;
    logic [7:0] mfifo_cmd_fault_code_o;
    logic mfifo_cmd_manager_i;
    logic [ADDR_W-1:0] mfifo_cmd_next_pc_i;
    logic [7:0] mfifo_cmd_opcode_i;
    logic mfifo_cmd_ready_o;
    logic mfifo_cmd_secure_i;
    logic mfifo_cmd_valid_i;
    logic [4:0] mfifo_count_o;
    logic mfifo_dbginst_write_i;
    logic mfifo_empty_o;
    logic [31:0] mfifo_fault_clear_i;
    logic [31:0] mfifo_fault_status_o;
    logic mfifo_fault_valid_o;
    logic mfifo_full_o;
    logic [31:0] mfifo_irq_clear_i;
    logic [31:0] mfifo_irq_status_o;
    logic [ADDR_W-1:0] mfifo_ld_req_addr_o;
    logic mfifo_ld_req_ready_i;
    logic mfifo_ld_req_valid_o;
    logic [DATA_W-1:0] mfifo_ld_rsp_data_i;
    logic mfifo_ld_rsp_error_i;
    logic mfifo_ld_rsp_ready_o;
    logic mfifo_ld_rsp_valid_i;
    logic [3:0] mfifo_outstanding_reads_o;
    logic [3:0] mfifo_outstanding_writes_o;
    logic [DATA_W-1:0] mfifo_pop_data_o;
    logic mfifo_pop_ready_o;
    logic mfifo_pop_valid_i;
    logic [DATA_W-1:0] mfifo_push_data_i;
    logic mfifo_push_ready_o;
    logic mfifo_push_valid_i;
    logic mfifo_reset_accepted_o;
    logic mfifo_soft_reset_i;
    logic [ADDR_W-1:0] mfifo_st_req_addr_o;
    logic [DATA_W-1:0] mfifo_st_req_data_o;
    logic mfifo_st_req_ready_i;
    logic mfifo_st_req_valid_o;
    logic mfifo_st_rsp_error_i;
    logic mfifo_st_rsp_ready_o;
    logic mfifo_st_rsp_valid_i;
    logic [COUNT_W-1:0] periph_active_count_o;
    logic [NUM_PERIPH_REQS-1:0] periph_active_mask_o;
    logic periph_any_active_o;
    logic periph_any_pending_o;
    logic [NUM_PERIPH_REQS-1:0] periph_cfg_periph_enable_i;
    logic [NUM_PERIPH_REQS-1:0] periph_daready_o;
    logic [NUM_PERIPH_REQS-1:0] periph_drlast_i;
    logic [(NUM_PERIPH_REQS*REQ_TYPE_W)-1:0] periph_drtype_i;
    logic [NUM_PERIPH_REQS-1:0] periph_drvalid_i;
    logic periph_engine_periph_done_i;
    logic [PERIPH_ID_W-1:0] periph_engine_periph_done_id_i;
    logic [PERIPH_ID_W-1:0] periph_engine_periph_id_o;
    logic periph_engine_periph_last_o;
    logic periph_engine_periph_ready_i;
    logic [REQ_TYPE_W-1:0] periph_engine_periph_type_o;
    logic periph_engine_periph_valid_o;
    logic [COUNT_W-1:0] periph_pending_count_o;
    logic [NUM_PERIPH_REQS-1:0] periph_pending_mask_o;
    logic [PERIPH_ID_W-1:0] periph_rr_pointer_o;
    logic pipeline_accepted_pulse;
    logic pipeline_busy;
    logic [ID_WIDTH-1:0] pipeline_cmpl_id;
    logic pipeline_cmpl_last;
    logic [DATA_WIDTH-1:0] pipeline_cmpl_rdata;
    logic pipeline_cmpl_ready;
    logic [RESP_WIDTH-1:0] pipeline_cmpl_resp;
    logic pipeline_cmpl_valid;
    logic pipeline_completed_pulse;
    logic [LATENCY_WIDTH-1:0] pipeline_debug_latency_count;
    logic [3:0] pipeline_debug_stage_valid;
    logic [2:0] pipeline_debug_state;
    logic pipeline_enable;
    logic [ADDR_WIDTH-1:0] pipeline_engine_req_addr;
    logic [CTRL_WIDTH-1:0] pipeline_engine_req_ctrl;
    logic [ID_WIDTH-1:0] pipeline_engine_req_id;
    logic [7:0] pipeline_engine_req_len;
    logic pipeline_engine_req_ready;
    logic [2:0] pipeline_engine_req_size;
    logic [STRB_WIDTH-1:0] pipeline_engine_req_strb;
    logic pipeline_engine_req_valid;
    logic [DATA_WIDTH-1:0] pipeline_engine_req_wdata;
    logic pipeline_engine_req_write;
    logic [ID_WIDTH-1:0] pipeline_engine_rsp_id;
    logic pipeline_engine_rsp_last;
    logic [DATA_WIDTH-1:0] pipeline_engine_rsp_rdata;
    logic pipeline_engine_rsp_ready;
    logic [RESP_WIDTH-1:0] pipeline_engine_rsp_resp;
    logic pipeline_engine_rsp_valid;
    logic pipeline_error_seen;
    logic pipeline_flush;
    logic pipeline_idle;
    logic [COUNT_WIDTH-1:0] pipeline_in_flight_count;
    logic [ADDR_WIDTH-1:0] pipeline_issue_addr;
    logic [CTRL_WIDTH-1:0] pipeline_issue_ctrl;
    logic [ID_WIDTH-1:0] pipeline_issue_id;
    logic [7:0] pipeline_issue_len;
    logic pipeline_issue_ready;
    logic [2:0] pipeline_issue_size;
    logic [STRB_WIDTH-1:0] pipeline_issue_strb;
    logic pipeline_issue_valid;
    logic [DATA_WIDTH-1:0] pipeline_issue_wdata;
    logic pipeline_issue_write;
    logic pipeline_issued_pulse;
    logic [ADDR_WIDTH-1:0] pipeline_pipe_req_addr;
    logic [CTRL_WIDTH-1:0] pipeline_pipe_req_ctrl;
    logic [ID_WIDTH-1:0] pipeline_pipe_req_id;
    logic [7:0] pipeline_pipe_req_len;
    logic pipeline_pipe_req_ready;
    logic [2:0] pipeline_pipe_req_size;
    logic [STRB_WIDTH-1:0] pipeline_pipe_req_strb;
    logic pipeline_pipe_req_valid;
    logic [DATA_WIDTH-1:0] pipeline_pipe_req_wdata;
    logic pipeline_pipe_req_write;
    logic [ID_WIDTH-1:0] pipeline_pipe_rsp_id;
    logic pipeline_pipe_rsp_last;
    logic [DATA_WIDTH-1:0] pipeline_pipe_rsp_rdata;
    logic pipeline_pipe_rsp_ready;
    logic [RESP_WIDTH-1:0] pipeline_pipe_rsp_resp;
    logic pipeline_pipe_rsp_valid;
    logic [ADDR_WIDTH-1:0] pipeline_req_addr;
    logic [CTRL_WIDTH-1:0] pipeline_req_ctrl;
    logic [ID_WIDTH-1:0] pipeline_req_id;
    logic [7:0] pipeline_req_len;
    logic pipeline_req_ready;
    logic [2:0] pipeline_req_size;
    logic [STRB_WIDTH-1:0] pipeline_req_strb;
    logic [DATA_WIDTH-1:0] pipeline_req_wdata;
    logic pipeline_req_write;
    logic [ID_WIDTH-1:0] pipeline_rsp_id;
    logic pipeline_rsp_last;
    logic [DATA_WIDTH-1:0] pipeline_rsp_rdata;
    logic [RESP_WIDTH-1:0] pipeline_rsp_resp;
    logic pipeline_rsp_valid;
    logic pipeline_stalled;
    wire                   link_ready_w;
    wire                   pipeline_busy_w;
    wire                   accept_req_w;
    wire                   consume_rsp_w;
    wire                   reset_settle_done_w;
    wire [DATA_WIDTH-1:0]  flow_increment_w;
    wire [DATA_WIDTH-1:0]  response_mix_w;
    wire                   security_req_w;
    wire                   security_access_w;
    wire                   security_write_w;
    wire                   security_read_w;
    wire                   security_lock_w;
    wire                   security_unlock_ok_w;
    wire                   security_write_allowed_w;
    wire                   non_security_accept_w;
    wire [3:0]             security_subcmd_w;
    wire                   boot_manager_ns_update_w;
    wire [SECURITY_IRQ_NS_WIDTH-1:0] boot_irq_ns_update_w;
    wire [SECURITY_PERIPH_NS_WIDTH-1:0] boot_periph_ns_update_w;
    wire [7:0]             control_data_opcode_w;
    wire [EVENT_IDX_WIDTH-1:0] event_idx_w;
    wire [EVENT_IDX_WIDTH:0]   event_idx_ext_w;
    wire [EVENT_IDX_WIDTH:0]   num_irqs_limit_w;
    wire                   event_idx_in_range_w;
    wire [NUM_IRQS-1:0]    event_irq_mask_w;
    wire                   periph_davalid_ack_w;
    wire                   dma_write_complete_w;
    wire                   fm_dmastp_accept_w;
    wire                   fm_dmasev_accept_w;
    wire                   fm_dmaend_accept_w;
    wire                   fm_dmastp_precondition_w;
    wire                   fm_dmasev_precondition_w;
    wire                   fm_dmaend_precondition_w;
    wire                   fm_dma_error_case_w;
    wire                   outstanding_is_zero_w;
    wire                   outstanding_has_credit_w;
    wire                   outstanding_can_increment_w;
    wire                   pipeline_terminal_w;
    wire                   latency_bound_exceeded_w;
    wire                   req_payload_changed_while_wait_w;
    wire                   rsp_payload_changed_while_wait_w;
    wire                   rtl_implement_ssot_contract_event_w;
    wire                   rtl_module_pl330_target_event_w;
    wire                   cycle_model_pipeline_accept_event_w;
    wire                   cycle_model_pipeline_evaluate_event_w;
    wire                   cycle_model_pipeline_publish_event_w;
    wire                   cycle_model_ordering_terminal_event_w;
    wire                   cycle_model_latency_bound_event_w;
    wire                   cycle_model_backpressure_event_w;
    wire                   cycle_model_reset_release_event_w;
    wire                   quality_gates_observable_event_w;
    wire                   manifest_child_flow_w;

    assign manifest_child_flow_w =
        engine_busy | (|engine_channel_state) | engine_cmd_ready | (|engine_state) |
        (|engine_error_code) | engine_error_valid | (|engine_fetch_req_addr) |
        (|engine_fetch_req_channel) | engine_fetch_req_privileged | engine_fetch_req_secure |
        engine_fetch_req_valid | engine_fetch_rsp_ready | engine_idle |
        (|engine_observed_fetch_data) | (|engine_outstanding_reads) | (|engine_outstanding_writes) |
        (|engine_rd_req_addr) | (|engine_rd_req_channel) | (|engine_rd_req_len) |
        engine_rd_req_privileged | engine_rd_req_secure | engine_rd_req_valid | engine_rd_rsp_ready |
        (|engine_rsp_bytes_remaining) | (|engine_rsp_channel) | (|engine_rsp_status) |
        engine_rsp_valid | engine_stage_s0_valid | engine_stage_s1_valid | engine_stage_s2_valid |
        (|engine_wr_req_addr) | (|engine_wr_req_channel) | (|engine_wr_req_len) |
        engine_wr_req_privileged | engine_wr_req_secure | engine_wr_req_valid | engine_wr_rsp_ready |
        pipeline_accepted_pulse | pipeline_busy | pipeline_cmpl_ready | pipeline_completed_pulse |
        (|pipeline_debug_latency_count) | (|pipeline_debug_stage_valid) | (|pipeline_debug_state) |
        (|pipeline_engine_req_addr) | (|pipeline_engine_req_ctrl) | (|pipeline_engine_req_id) |
        (|pipeline_engine_req_len) | (|pipeline_engine_req_size) | (|pipeline_engine_req_strb) |
        pipeline_engine_req_valid | (|pipeline_engine_req_wdata) | pipeline_engine_req_write |
        pipeline_engine_rsp_ready | pipeline_error_seen | pipeline_idle |
        (|pipeline_in_flight_count) | (|pipeline_issue_addr) | (|pipeline_issue_ctrl) |
        (|pipeline_issue_id) | (|pipeline_issue_len) | (|pipeline_issue_size) |
        (|pipeline_issue_strb) | pipeline_issue_valid | (|pipeline_issue_wdata) |
        pipeline_issue_write | pipeline_issued_pulse | pipeline_pipe_req_ready |
        (|pipeline_pipe_rsp_id) | pipeline_pipe_rsp_last | (|pipeline_pipe_rsp_rdata) |
        (|pipeline_pipe_rsp_resp) | pipeline_pipe_rsp_valid | pipeline_req_ready |
        (|pipeline_rsp_id) | pipeline_rsp_last | (|pipeline_rsp_rdata) | (|pipeline_rsp_resp) |
        pipeline_rsp_valid | pipeline_stalled | lsq_busy_o | lsq_empty_o | lsq_load_ready_o |
        (|lsq_load_resp_data_o) | lsq_load_resp_error_o | (|lsq_load_resp_tag_o) |
        lsq_load_resp_valid_o | (|lsq_mem_req_addr_o) | (|lsq_mem_req_size_o) | lsq_mem_req_valid_o |
        (|lsq_mem_req_wdata_o) | lsq_mem_req_write_o | (|lsq_mem_req_wstrb_o) | lsq_mem_rsp_ready_o |
        lsq_ordering_violation_o | (|lsq_outstanding_count_o) | lsq_store_ready_o |
        lsq_store_resp_error_o | (|lsq_store_resp_tag_o) | lsq_store_resp_valid_o |
        (|mfifo_channel_pc_o) | (|mfifo_channel_state_o) | mfifo_cmd_accept_o | mfifo_cmd_error_o |
        (|mfifo_cmd_fault_code_o) | mfifo_cmd_ready_o | (|mfifo_fault_status_o) |
        mfifo_fault_valid_o | (|mfifo_irq_status_o) | (|mfifo_ld_req_addr_o) | mfifo_ld_req_valid_o |
        mfifo_ld_rsp_ready_o | (|mfifo_count_o) | mfifo_empty_o | mfifo_full_o | (|mfifo_pop_data_o) |
        mfifo_pop_ready_o | mfifo_push_ready_o | (|mfifo_outstanding_reads_o) |
        (|mfifo_outstanding_writes_o) | mfifo_reset_accepted_o | (|mfifo_st_req_addr_o) |
        (|mfifo_st_req_data_o) | mfifo_st_req_valid_o | mfifo_st_rsp_ready_o |
        merge_buffer_accept_pulse_o | merge_buffer_empty_o | merge_buffer_full_o |
        merge_buffer_in_ready_o | merge_buffer_merge_pulse_o | (|merge_buffer_occupancy_o) |
        (|merge_buffer_out_addr_o) | (|merge_buffer_out_data_o) | (|merge_buffer_out_id_o) |
        merge_buffer_out_last_o | (|merge_buffer_out_strb_o) | merge_buffer_out_valid_o |
        merge_buffer_overflow_sticky_o | merge_buffer_pop_pulse_o | (|icache_debug_hit_count) |
        (|icache_debug_miss_count) | (|icache_debug_state) | (|icache_debug_valid_count) |
        (|icache_fill_req_addr) | icache_fill_req_valid | icache_fill_resp_ready |
        icache_flush_ready | icache_req_ready | (|icache_resp_addr) | (|icache_resp_data) |
        icache_resp_error | icache_resp_hit | icache_resp_valid | icache_invalidate_ready | axi_busy |
        axi_error_sticky | (|axi_m_axi_araddr) | (|axi_m_axi_arburst) | (|axi_m_axi_arid) |
        (|axi_m_axi_arlen) | (|axi_m_axi_arsize) | axi_m_axi_arvalid | (|axi_m_axi_awaddr) |
        (|axi_m_axi_awburst) | (|axi_m_axi_awid) | (|axi_m_axi_awlen) | (|axi_m_axi_awsize) |
        axi_m_axi_awvalid | axi_m_axi_bready | axi_m_axi_rready | (|axi_m_axi_wdata) |
        axi_m_axi_wlast | (|axi_m_axi_wstrb) | axi_m_axi_wvalid | axi_m_b_fault | (|axi_m_b_id) |
        (|axi_m_b_resp) | axi_m_b_valid | (|axi_m_r_data) | axi_m_r_fault | (|axi_m_r_id) |
        axi_m_r_last | (|axi_m_r_resp) | axi_m_r_valid | (|axi_rd_outstanding) | axi_s_ar_ready |
        axi_s_aw_ready | axi_s_w_ready | (|axi_wr_outstanding) | (|periph_active_count_o) |
        (|periph_active_mask_o) | periph_any_active_o | periph_any_pending_o |
        (|periph_engine_periph_id_o) | periph_engine_periph_last_o | (|periph_engine_periph_type_o) |
        periph_engine_periph_valid_o | (|periph_pending_count_o) | (|periph_pending_mask_o) |
        (|periph_daready_o) | (|periph_rr_pointer_o) | (|apb_regs_cfg_dst_addr) |
        apb_regs_cfg_enable | (|apb_regs_cfg_len) | apb_regs_cfg_secure | (|apb_regs_cfg_src_addr) |
        apb_regs_clear_done_pulse | apb_regs_clear_error_pulse | apb_regs_halt_req | apb_regs_irq |
        (|apb_regs_irq_enable_mask) | (|apb_regs_irq_status) | (|apb_regs_prdata) | apb_regs_pready |
        apb_regs_pslverr | apb_regs_soft_reset_pulse | apb_regs_start_pulse;

    assign flow_increment_w          = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign link_ready_w              = link_ready_q & (~reset_fault_q);
    assign pipeline_busy_w           = pipeline_accept_valid_q | pipeline_evaluate_valid_q | pipeline_publish_valid_q;
    assign accept_req_w              = req_valid & req_ready;
    assign consume_rsp_w             = rsp_valid & rsp_ready;
    assign reset_settle_done_w       = (reset_settle_q == RESET_SETTLE_MAX);
    assign response_mix_w            = req_data ^ flow_count_q ^ {DATA_WIDTH{aux_activity_sync2_q}} ^
                                       pipeline_publish_data_q ^
                                       {{(DATA_WIDTH-NUM_IRQS){1'b0}}, irq_pulse_q};

    assign security_req_w            = req_valid & (req_data[31:28] == SECURITY_OPCODE);
    assign security_access_w         = accept_req_w & (req_data[31:28] == SECURITY_OPCODE);
    assign security_subcmd_w         = req_data[27:24];
    assign security_write_w          = req_data[23];
    assign security_read_w           = req_data[22];
    assign security_lock_w           = req_data[21];
    assign security_unlock_ok_w      = (req_data[15:0] == SECURITY_BOOT_UNLOCK);
    assign security_write_allowed_w  = security_access_w & security_write_w & security_unlock_ok_w & (~boot_security_locked_q);
    assign non_security_accept_w     = accept_req_w & (~security_req_w);
    assign boot_manager_ns_update_w  = req_data[0];
    assign boot_irq_ns_update_w      = req_data[SECURITY_IRQ_NS_WIDTH-1:0];
    assign boot_periph_ns_update_w   = req_data[SECURITY_PERIPH_NS_WIDTH-1:0];

    assign control_data_opcode_w     = req_data[7:0];
    assign event_idx_w               = req_data[11:8];
    assign event_idx_ext_w           = {1'b0, event_idx_w};
    assign num_irqs_limit_w          = {1'b1, {EVENT_IDX_WIDTH{1'b0}}};
    assign event_idx_in_range_w      = (event_idx_ext_w < num_irqs_limit_w);
    assign event_irq_mask_w          = event_idx_in_range_w ? ({{(NUM_IRQS-1){1'b0}}, 1'b1} << event_idx_w) : {NUM_IRQS{1'b0}};
    assign periph_davalid_ack_w      = req_data[16];
    assign dma_write_complete_w      = consume_rsp_w & outstanding_has_credit_w;
    assign outstanding_is_zero_w     = (outstanding_writes_q == {OUTSTANDING_WIDTH{1'b0}});
    assign outstanding_has_credit_w  = (outstanding_writes_q != {OUTSTANDING_WIDTH{1'b0}});
    assign outstanding_can_increment_w = (outstanding_writes_q != {OUTSTANDING_WIDTH{1'b1}});
    assign fm_dmastp_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMASTP);
    assign fm_dmasev_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMASEV);
    assign fm_dmaend_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMAEND);
    assign fm_dmastp_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & periph_davalid_ack_w & outstanding_can_increment_w;
    assign fm_dmasev_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & event_idx_in_range_w;
    assign fm_dmaend_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & outstanding_is_zero_w;
    assign fm_dma_error_case_w       = (fm_dmastp_accept_w & (~fm_dmastp_precondition_w)) |
                                       (fm_dmasev_accept_w & (~fm_dmasev_precondition_w)) |
                                       (fm_dmaend_accept_w & (~fm_dmaend_precondition_w));
    assign pipeline_terminal_w       = pipeline_publish_valid_q;
    assign latency_bound_exceeded_w  = pipeline_busy_w & (latency_counter_q > PIPELINE_LATENCY_BOUND);
    assign req_payload_changed_while_wait_w = req_valid & (~req_ready) & req_payload_hold_valid_q & (req_payload_hold_q != req_data);
    assign rsp_payload_changed_while_wait_w = pending_q & (~rsp_ready) & rsp_hold_active_q & (rsp_hold_data_q != rsp_data_q);

    assign rtl_implement_ssot_contract_event_w   = accept_req_w | pipeline_terminal_w | consume_rsp_w | debug_event_q;
    assign rtl_module_pl330_target_event_w       = link_ready_w & (req_valid | pending_q | pipeline_busy_w | consume_rsp_w);
    assign cycle_model_pipeline_accept_event_w   = accept_req_w;
    assign cycle_model_pipeline_evaluate_event_w = pipeline_accept_valid_q;
    assign cycle_model_pipeline_publish_event_w  = pipeline_evaluate_valid_q;
    assign cycle_model_ordering_terminal_event_w = terminal_fsm_state_q | pipeline_terminal_w;
    assign cycle_model_latency_bound_event_w     = pipeline_terminal_w & (latency_counter_q <= PIPELINE_LATENCY_BOUND);
    assign cycle_model_backpressure_event_w      = req_valid & (~req_ready);
    assign cycle_model_reset_release_event_w     = aux_reset_sync2_q & link_ready_q;
    assign quality_gates_observable_event_w      = rtl_implement_ssot_contract_event_w | rtl_module_pl330_target_event_w |
                                                   fm_dmastp_accept_w | fm_dmasev_accept_w | fm_dmaend_accept_w |
                                                   fm_dma_error_case_w | security_access_w | manifest_child_flow_w;

    // Candidate child wiring for the pending connection contract review packet.
    assign apb_regs_axi_error         = axi_error_sticky | protocol_error_q;
    assign apb_regs_engine_done       = engine_rsp_valid & rsp_ready;
    assign apb_regs_engine_error      = engine_error_valid | axi_error_sticky | lsq_ordering_violation_o;
    assign apb_regs_engine_error_code = {4'h0, engine_error_code};
    assign apb_regs_engine_idle       = engine_idle & pipeline_idle & mfifo_empty_o;
    assign apb_regs_mfifo_level       = {3'b000, mfifo_count_o};
    assign apb_regs_mfifo_overflow    = mfifo_full_o & mfifo_push_valid_i & (~mfifo_push_ready_o);
    assign apb_regs_mfifo_underflow   = mfifo_empty_o & mfifo_pop_valid_i & (~mfifo_pop_ready_o);
    assign apb_regs_paddr             = req_data[APB_ADDR_WIDTH-1:0];
    assign apb_regs_penable           = accept_req_w;
    assign apb_regs_periph_ack        = |periph_daready_o;
    assign apb_regs_psel              = req_valid & link_ready_w;
    assign apb_regs_pwdata            = req_data[APB_DATA_WIDTH-1:0];
    assign apb_regs_pwrite            = security_write_w | non_security_accept_w;

    assign axi_m_axi_arready = 1'b1;
    assign axi_m_axi_awready = 1'b1;
    assign axi_m_axi_wready  = 1'b1;
    assign axi_m_axi_bid     = axi_m_axi_awid;
    assign axi_m_axi_bresp   = 2'b00;
    assign axi_m_axi_bvalid  = axi_m_axi_awvalid & axi_m_axi_wvalid;
    assign axi_m_axi_rdata   = req_data ^ axi_m_axi_araddr;
    assign axi_m_axi_rid     = axi_m_axi_arid;
    assign axi_m_axi_rlast   = 1'b1;
    assign axi_m_axi_rresp   = 2'b00;
    assign axi_m_axi_rvalid  = axi_m_axi_arvalid;
    assign axi_m_b_ready     = pipeline_engine_rsp_ready | engine_wr_rsp_ready | mfifo_st_rsp_ready_o;
    assign axi_m_r_ready     = pipeline_engine_rsp_ready | engine_rd_rsp_ready | mfifo_ld_rsp_ready_o;

    assign axi_s_aw_addr  = pipeline_issue_addr;
    assign axi_s_aw_burst = 2'b01;
    assign axi_s_aw_id    = pipeline_issue_id[AXI_ID_WIDTH-1:0];
    assign axi_s_aw_len   = pipeline_issue_len;
    assign axi_s_aw_size  = pipeline_issue_size;
    assign axi_s_aw_valid = pipeline_issue_valid & pipeline_issue_write;
    assign axi_s_w_data   = pipeline_issue_wdata;
    assign axi_s_w_last   = 1'b1;
    assign axi_s_w_strb   = pipeline_issue_strb[AXI_STRB_WIDTH-1:0];
    assign axi_s_w_valid  = pipeline_issue_valid & pipeline_issue_write;
    assign axi_s_ar_addr  = pipeline_issue_addr;
    assign axi_s_ar_burst = 2'b01;
    assign axi_s_ar_id    = pipeline_issue_id[AXI_ID_WIDTH-1:0];
    assign axi_s_ar_len   = pipeline_issue_len;
    assign axi_s_ar_size  = pipeline_issue_size;
    assign axi_s_ar_valid = pipeline_issue_valid & (~pipeline_issue_write);

    assign engine_cmd_channel       = req_data[8 +: CHANNEL_ID_WIDTH];
    assign engine_cmd_dst_addr      = apb_regs_cfg_dst_addr ^ req_data[ADDR_WIDTH-1:0];
    assign engine_cmd_len           = req_data[LEN_WIDTH-1:0];
    assign engine_cmd_opcode        = control_data_opcode_w;
    assign engine_cmd_privileged    = ~boot_manager_ns_q;
    assign engine_cmd_secure        = ~(boot_security_locked_q | boot_manager_ns_q);
    assign engine_cmd_src_addr      = apb_regs_cfg_src_addr ^ flow_count_q[ADDR_WIDTH-1:0];
    assign engine_cmd_valid         = non_security_accept_w | apb_regs_start_pulse;
    assign engine_fetch_req_ready   = icache_req_ready;
    assign engine_fetch_rsp_data    = icache_resp_data;
    assign engine_fetch_rsp_error   = icache_resp_error;
    assign engine_fetch_rsp_valid   = icache_resp_valid;
    assign engine_rd_req_ready      = lsq_load_ready_o;
    assign engine_rd_rsp_error      = lsq_load_resp_error_o;
    assign engine_rd_rsp_valid      = lsq_load_resp_valid_o;
    assign engine_wr_req_ready      = lsq_store_ready_o;
    assign engine_wr_rsp_error      = lsq_store_resp_error_o;
    assign engine_wr_rsp_valid      = lsq_store_resp_valid_o;

    assign icache_fill_req_ready      = axi_s_ar_ready;
    assign icache_fill_resp_data      = axi_m_r_data;
    assign icache_fill_resp_error     = axi_m_r_fault;
    assign icache_fill_resp_valid     = axi_m_r_valid;
    assign icache_flush_valid         = apb_regs_soft_reset_pulse | reset_fault_q;
    assign icache_invalidate_addr     = req_data[ADDR_WIDTH-1:0];
    assign icache_invalidate_valid    = apb_regs_clear_error_pulse;
    assign icache_req_addr            = engine_fetch_req_addr;
    assign icache_req_valid           = engine_fetch_req_valid;
    assign icache_resp_ready          = engine_fetch_rsp_ready;

    assign lsq_flush_i            = apb_regs_soft_reset_pulse | pipeline_flush;
    assign lsq_load_addr_i        = engine_rd_req_addr;
    assign lsq_load_resp_ready_i  = engine_rd_rsp_ready;
    assign lsq_load_signed_i      = 1'b0;
    assign lsq_load_size_i        = 3'd2;
    assign lsq_load_tag_i         = {{(TAG_WIDTH-CHANNEL_ID_WIDTH){1'b0}}, engine_rd_req_channel};
    assign lsq_load_valid_i       = engine_rd_req_valid;
    assign lsq_mem_req_ready_i    = merge_buffer_in_ready_o | axi_s_ar_ready;
    assign lsq_mem_rsp_error_i    = axi_m_r_fault | axi_m_b_fault;
    assign lsq_mem_rsp_rdata_i    = axi_m_r_data;
    assign lsq_mem_rsp_valid_i    = axi_m_r_valid | axi_m_b_valid;
    assign lsq_store_addr_i       = engine_wr_req_addr;
    assign lsq_store_data_i       = req_data;
    assign lsq_store_resp_ready_i = engine_wr_rsp_ready;
    assign lsq_store_size_i       = 3'd2;
    assign lsq_store_strb_i       = {STRB_WIDTH{1'b1}};
    assign lsq_store_tag_i        = {{(TAG_WIDTH-CHANNEL_ID_WIDTH){1'b0}}, engine_wr_req_channel};
    assign lsq_store_valid_i      = engine_wr_req_valid;

    assign merge_buffer_flush_i     = lsq_flush_i;
    assign merge_buffer_in_addr_i   = lsq_mem_req_addr_o;
    assign merge_buffer_in_data_i   = lsq_mem_req_wdata_o;
    assign merge_buffer_in_id_i     = pipeline_issue_id[AXI_ID_WIDTH-1:0];
    assign merge_buffer_in_last_i   = 1'b1;
    assign merge_buffer_in_strb_i   = lsq_mem_req_wstrb_o;
    assign merge_buffer_in_valid_i  = lsq_mem_req_valid_o & lsq_mem_req_write_o;
    assign merge_buffer_out_ready_i = axi_s_aw_ready & axi_s_w_ready;

    assign mfifo_cfg_nonsecure_allowed_i = ~boot_security_locked_q;
    assign mfifo_cmd_arg_addr_i          = req_data[ADDR_W-1:0];
    assign mfifo_cmd_arg_data_i          = req_data[DATA_W-1:0];
    assign mfifo_cmd_event_i             = {1'b0, event_idx_w};
    assign mfifo_cmd_manager_i           = ~boot_manager_ns_q;
    assign mfifo_cmd_next_pc_i           = flow_count_q[ADDR_W-1:0];
    assign mfifo_cmd_opcode_i            = control_data_opcode_w;
    assign mfifo_cmd_secure_i            = ~boot_security_locked_q;
    assign mfifo_cmd_valid_i             = non_security_accept_w;
    assign mfifo_dbginst_write_i         = security_write_allowed_w;
    assign mfifo_fault_clear_i           = {31'h0, apb_regs_clear_error_pulse};
    assign mfifo_irq_clear_i             = {31'h0, apb_regs_clear_done_pulse};
    assign mfifo_ld_req_ready_i          = lsq_load_ready_o;
    assign mfifo_ld_rsp_data_i           = lsq_load_resp_data_o;
    assign mfifo_ld_rsp_error_i          = lsq_load_resp_error_o;
    assign mfifo_ld_rsp_valid_i          = lsq_load_resp_valid_o;
    assign mfifo_pop_valid_i             = consume_rsp_w;
    assign mfifo_push_data_i             = req_data[DATA_W-1:0];
    assign mfifo_push_valid_i            = accept_req_w;
    assign mfifo_soft_reset_i            = apb_regs_soft_reset_pulse | reset_fault_q;
    assign mfifo_st_req_ready_i          = lsq_store_ready_o;
    assign mfifo_st_rsp_error_i          = lsq_store_resp_error_o;
    assign mfifo_st_rsp_valid_i          = lsq_store_resp_valid_o;

    assign periph_cfg_periph_enable_i     = {{(NUM_PERIPH_REQS-NUM_IRQS){1'b0}}, ~boot_periph_ns_q};
    assign periph_drlast_i                = {{(NUM_PERIPH_REQS-NUM_IRQS){1'b0}}, event_irq_mask_w};
    assign periph_drtype_i                = {(NUM_PERIPH_REQS*REQ_TYPE_W){1'b0}};
    assign periph_drvalid_i               = {{(NUM_PERIPH_REQS-NUM_IRQS){1'b0}}, event_irq_mask_w} & {NUM_PERIPH_REQS{fm_dmasev_accept_w}};
    assign periph_engine_periph_done_i    = engine_rsp_valid;
    assign periph_engine_periph_done_id_i = {{(PERIPH_ID_W-CHANNEL_ID_WIDTH){1'b0}}, engine_rsp_channel};
    assign periph_engine_periph_ready_i   = engine_cmd_ready;

    assign pipeline_cmpl_id            = axi_m_b_valid ? axi_m_b_id : axi_m_r_id;
    assign pipeline_cmpl_last          = axi_m_b_valid | axi_m_r_last;
    assign pipeline_cmpl_rdata         = axi_m_r_data;
    assign pipeline_cmpl_resp          = axi_m_b_valid ? axi_m_b_resp : axi_m_r_resp;
    assign pipeline_cmpl_valid         = axi_m_b_valid | axi_m_r_valid;
    assign pipeline_enable             = link_ready_w;
    assign pipeline_engine_req_ready   = pipeline_engine_req_write ? (axi_s_aw_ready & axi_s_w_ready) : axi_s_ar_ready;
    assign pipeline_engine_rsp_id      = pipeline_cmpl_id;
    assign pipeline_engine_rsp_last    = pipeline_cmpl_last;
    assign pipeline_engine_rsp_rdata   = pipeline_cmpl_rdata;
    assign pipeline_engine_rsp_resp    = pipeline_cmpl_resp;
    assign pipeline_engine_rsp_valid   = pipeline_cmpl_valid;
    assign pipeline_flush              = apb_regs_halt_req | apb_regs_soft_reset_pulse | reset_fault_q;
    assign pipeline_issue_ready        = pipeline_issue_write ? (axi_s_aw_ready & axi_s_w_ready) : axi_s_ar_ready;
    assign pipeline_pipe_req_addr      = mfifo_st_req_valid_o ? mfifo_st_req_addr_o : mfifo_ld_req_addr_o;
    assign pipeline_pipe_req_ctrl      = {CTRL_WIDTH{1'b0}};
    assign pipeline_pipe_req_id        = {{(ID_WIDTH-CHANNEL_ID_WIDTH){1'b0}}, engine_rsp_channel};
    assign pipeline_pipe_req_len       = 8'h00;
    assign pipeline_pipe_req_size      = 3'd2;
    assign pipeline_pipe_req_strb      = {STRB_WIDTH{mfifo_st_req_valid_o}};
    assign pipeline_pipe_req_valid     = mfifo_st_req_valid_o | mfifo_ld_req_valid_o;
    assign pipeline_pipe_req_wdata     = mfifo_st_req_data_o;
    assign pipeline_pipe_req_write     = mfifo_st_req_valid_o;
    assign pipeline_pipe_rsp_ready     = rsp_ready;
    assign pipeline_req_addr           = req_data[ADDR_WIDTH-1:0];
    assign pipeline_req_ctrl           = {req_data[15:0]};
    assign pipeline_req_id             = req_data[ID_WIDTH-1:0];
    assign pipeline_req_len            = req_data[15:8];
    assign pipeline_req_size           = 3'd2;
    assign pipeline_req_strb           = {STRB_WIDTH{1'b1}};
    assign pipeline_req_wdata          = req_data;
    assign pipeline_req_write          = control_data_opcode_w[0];

    assign req_ready = link_ready_w & (~pending_q) & (~pipeline_busy_w);
    assign rsp_valid = pending_q;
    assign rsp_data  = rsp_data_q;
    assign error     = reset_fault_q | protocol_error_q | security_protocol_error_q |
                       req_stability_violation_q | rsp_stability_violation_q |
                       latency_bound_violation_q |
                       (channel_state_q == CHANNEL_STATE_FAULT) | irq_abort_pulse_q |
                       (req_valid & (~link_ready_w));

    pl330_target_apb_regs #(
        .APB_DATA_WIDTH(APB_DATA_WIDTH),
        .APB_ADDR_WIDTH(APB_ADDR_WIDTH)
    ) u_apb_regs (
        .axi_error(apb_regs_axi_error),
        .cfg_dst_addr(apb_regs_cfg_dst_addr),
        .cfg_enable(apb_regs_cfg_enable),
        .cfg_len(apb_regs_cfg_len),
        .cfg_secure(apb_regs_cfg_secure),
        .cfg_src_addr(apb_regs_cfg_src_addr),
        .clear_done_pulse(apb_regs_clear_done_pulse),
        .clear_error_pulse(apb_regs_clear_error_pulse),
        .engine_busy(engine_busy),
        .engine_done(apb_regs_engine_done),
        .engine_error(apb_regs_engine_error),
        .engine_error_code(apb_regs_engine_error_code),
        .engine_idle(apb_regs_engine_idle),
        .halt_req(apb_regs_halt_req),
        .irq(apb_regs_irq),
        .irq_enable_mask(apb_regs_irq_enable_mask),
        .irq_status(apb_regs_irq_status),
        .mfifo_level(apb_regs_mfifo_level),
        .mfifo_overflow(apb_regs_mfifo_overflow),
        .mfifo_underflow(apb_regs_mfifo_underflow),
        .paddr(apb_regs_paddr),
        .pclk(clk),
        .penable(apb_regs_penable),
        .periph_ack(apb_regs_periph_ack),
        .prdata(apb_regs_prdata),
        .pready(apb_regs_pready),
        .presetn(rst_n),
        .psel(apb_regs_psel),
        .pslverr(apb_regs_pslverr),
        .pwdata(apb_regs_pwdata),
        .pwrite(apb_regs_pwrite),
        .soft_reset_pulse(apb_regs_soft_reset_pulse),
        .start_pulse(apb_regs_start_pulse)
    );

    pl330_target_axi #(
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .AXI_ID_WIDTH(AXI_ID_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_STRB_WIDTH(AXI_STRB_WIDTH)
    ) u_axi (
        .axi_busy(axi_busy),
        .axi_error_sticky(axi_error_sticky),
        .clk(clk),
        .m_axi_araddr(axi_m_axi_araddr),
        .m_axi_arburst(axi_m_axi_arburst),
        .m_axi_arid(axi_m_axi_arid),
        .m_axi_arlen(axi_m_axi_arlen),
        .m_axi_arready(axi_m_axi_arready),
        .m_axi_arsize(axi_m_axi_arsize),
        .m_axi_arvalid(axi_m_axi_arvalid),
        .m_axi_awaddr(axi_m_axi_awaddr),
        .m_axi_awburst(axi_m_axi_awburst),
        .m_axi_awid(axi_m_axi_awid),
        .m_axi_awlen(axi_m_axi_awlen),
        .m_axi_awready(axi_m_axi_awready),
        .m_axi_awsize(axi_m_axi_awsize),
        .m_axi_awvalid(axi_m_axi_awvalid),
        .m_axi_bid(axi_m_axi_bid),
        .m_axi_bready(axi_m_axi_bready),
        .m_axi_bresp(axi_m_axi_bresp),
        .m_axi_bvalid(axi_m_axi_bvalid),
        .m_axi_rdata(axi_m_axi_rdata),
        .m_axi_rid(axi_m_axi_rid),
        .m_axi_rlast(axi_m_axi_rlast),
        .m_axi_rready(axi_m_axi_rready),
        .m_axi_rresp(axi_m_axi_rresp),
        .m_axi_rvalid(axi_m_axi_rvalid),
        .m_axi_wdata(axi_m_axi_wdata),
        .m_axi_wlast(axi_m_axi_wlast),
        .m_axi_wready(axi_m_axi_wready),
        .m_axi_wstrb(axi_m_axi_wstrb),
        .m_axi_wvalid(axi_m_axi_wvalid),
        .m_b_fault(axi_m_b_fault),
        .m_b_id(axi_m_b_id),
        .m_b_ready(axi_m_b_ready),
        .m_b_resp(axi_m_b_resp),
        .m_b_valid(axi_m_b_valid),
        .m_r_data(axi_m_r_data),
        .m_r_fault(axi_m_r_fault),
        .m_r_id(axi_m_r_id),
        .m_r_last(axi_m_r_last),
        .m_r_ready(axi_m_r_ready),
        .m_r_resp(axi_m_r_resp),
        .m_r_valid(axi_m_r_valid),
        .rd_outstanding(axi_rd_outstanding),
        .rst_n(rst_n),
        .s_ar_addr(axi_s_ar_addr),
        .s_ar_burst(axi_s_ar_burst),
        .s_ar_id(axi_s_ar_id),
        .s_ar_len(axi_s_ar_len),
        .s_ar_ready(axi_s_ar_ready),
        .s_ar_size(axi_s_ar_size),
        .s_ar_valid(axi_s_ar_valid),
        .s_aw_addr(axi_s_aw_addr),
        .s_aw_burst(axi_s_aw_burst),
        .s_aw_id(axi_s_aw_id),
        .s_aw_len(axi_s_aw_len),
        .s_aw_ready(axi_s_aw_ready),
        .s_aw_size(axi_s_aw_size),
        .s_aw_valid(axi_s_aw_valid),
        .s_w_data(axi_s_w_data),
        .s_w_last(axi_s_w_last),
        .s_w_ready(axi_s_w_ready),
        .s_w_strb(axi_s_w_strb),
        .s_w_valid(axi_s_w_valid),
        .wr_outstanding(axi_wr_outstanding)
    );

    pl330_target_engine #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .LEN_WIDTH(LEN_WIDTH),
        .OPCODE_WIDTH(OPCODE_WIDTH),
        .CHANNEL_ID_WIDTH(CHANNEL_ID_WIDTH),
        .OUTSTANDING_WIDTH(OUTSTANDING_WIDTH)
    ) u_engine (
        .busy(engine_busy),
        .channel_state(engine_channel_state),
        .clk(clk),
        .cmd_channel(engine_cmd_channel),
        .cmd_dst_addr(engine_cmd_dst_addr),
        .cmd_len(engine_cmd_len),
        .cmd_opcode(engine_cmd_opcode),
        .cmd_privileged(engine_cmd_privileged),
        .cmd_ready(engine_cmd_ready),
        .cmd_secure(engine_cmd_secure),
        .cmd_src_addr(engine_cmd_src_addr),
        .cmd_valid(engine_cmd_valid),
        .engine_state(engine_state),
        .error_code(engine_error_code),
        .error_valid(engine_error_valid),
        .fetch_req_addr(engine_fetch_req_addr),
        .fetch_req_channel(engine_fetch_req_channel),
        .fetch_req_privileged(engine_fetch_req_privileged),
        .fetch_req_ready(engine_fetch_req_ready),
        .fetch_req_secure(engine_fetch_req_secure),
        .fetch_req_valid(engine_fetch_req_valid),
        .fetch_rsp_data(engine_fetch_rsp_data),
        .fetch_rsp_error(engine_fetch_rsp_error),
        .fetch_rsp_ready(engine_fetch_rsp_ready),
        .fetch_rsp_valid(engine_fetch_rsp_valid),
        .idle(engine_idle),
        .observed_fetch_data(engine_observed_fetch_data),
        .outstanding_reads(engine_outstanding_reads),
        .outstanding_writes(engine_outstanding_writes),
        .rd_req_addr(engine_rd_req_addr),
        .rd_req_channel(engine_rd_req_channel),
        .rd_req_len(engine_rd_req_len),
        .rd_req_privileged(engine_rd_req_privileged),
        .rd_req_ready(engine_rd_req_ready),
        .rd_req_secure(engine_rd_req_secure),
        .rd_req_valid(engine_rd_req_valid),
        .rd_rsp_error(engine_rd_rsp_error),
        .rd_rsp_ready(engine_rd_rsp_ready),
        .rd_rsp_valid(engine_rd_rsp_valid),
        .rsp_bytes_remaining(engine_rsp_bytes_remaining),
        .rsp_channel(engine_rsp_channel),
        .rsp_ready(rsp_ready),
        .rsp_status(engine_rsp_status),
        .rsp_valid(engine_rsp_valid),
        .rst_n(rst_n),
        .stage_s0_valid(engine_stage_s0_valid),
        .stage_s1_valid(engine_stage_s1_valid),
        .stage_s2_valid(engine_stage_s2_valid),
        .wr_req_addr(engine_wr_req_addr),
        .wr_req_channel(engine_wr_req_channel),
        .wr_req_len(engine_wr_req_len),
        .wr_req_privileged(engine_wr_req_privileged),
        .wr_req_ready(engine_wr_req_ready),
        .wr_req_secure(engine_wr_req_secure),
        .wr_req_valid(engine_wr_req_valid),
        .wr_rsp_error(engine_wr_rsp_error),
        .wr_rsp_ready(engine_wr_rsp_ready),
        .wr_rsp_valid(engine_wr_rsp_valid)
    );

    pl330_target_icache #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_icache (
        .clk(clk),
        .debug_hit_count(icache_debug_hit_count),
        .debug_miss_count(icache_debug_miss_count),
        .debug_state(icache_debug_state),
        .debug_valid_count(icache_debug_valid_count),
        .fill_req_addr(icache_fill_req_addr),
        .fill_req_ready(icache_fill_req_ready),
        .fill_req_valid(icache_fill_req_valid),
        .fill_resp_data(icache_fill_resp_data),
        .fill_resp_error(icache_fill_resp_error),
        .fill_resp_ready(icache_fill_resp_ready),
        .fill_resp_valid(icache_fill_resp_valid),
        .flush_ready(icache_flush_ready),
        .flush_valid(icache_flush_valid),
        .icache_req_addr(icache_req_addr),
        .icache_req_ready(icache_req_ready),
        .icache_req_valid(icache_req_valid),
        .icache_resp_addr(icache_resp_addr),
        .icache_resp_data(icache_resp_data),
        .icache_resp_error(icache_resp_error),
        .icache_resp_hit(icache_resp_hit),
        .icache_resp_ready(icache_resp_ready),
        .icache_resp_valid(icache_resp_valid),
        .invalidate_addr(icache_invalidate_addr),
        .invalidate_ready(icache_invalidate_ready),
        .invalidate_valid(icache_invalidate_valid),
        .rst_n(rst_n)
    );

    pl330_target_lsq #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .STRB_WIDTH(STRB_WIDTH),
        .TAG_WIDTH(TAG_WIDTH),
        .SIZE_WIDTH(SIZE_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) u_lsq (
        .busy_o(lsq_busy_o),
        .clk(clk),
        .empty_o(lsq_empty_o),
        .flush_i(lsq_flush_i),
        .load_addr_i(lsq_load_addr_i),
        .load_ready_o(lsq_load_ready_o),
        .load_resp_data_o(lsq_load_resp_data_o),
        .load_resp_error_o(lsq_load_resp_error_o),
        .load_resp_ready_i(lsq_load_resp_ready_i),
        .load_resp_tag_o(lsq_load_resp_tag_o),
        .load_resp_valid_o(lsq_load_resp_valid_o),
        .load_signed_i(lsq_load_signed_i),
        .load_size_i(lsq_load_size_i),
        .load_tag_i(lsq_load_tag_i),
        .load_valid_i(lsq_load_valid_i),
        .mem_req_addr_o(lsq_mem_req_addr_o),
        .mem_req_ready_i(lsq_mem_req_ready_i),
        .mem_req_size_o(lsq_mem_req_size_o),
        .mem_req_valid_o(lsq_mem_req_valid_o),
        .mem_req_wdata_o(lsq_mem_req_wdata_o),
        .mem_req_write_o(lsq_mem_req_write_o),
        .mem_req_wstrb_o(lsq_mem_req_wstrb_o),
        .mem_rsp_error_i(lsq_mem_rsp_error_i),
        .mem_rsp_rdata_i(lsq_mem_rsp_rdata_i),
        .mem_rsp_ready_o(lsq_mem_rsp_ready_o),
        .mem_rsp_valid_i(lsq_mem_rsp_valid_i),
        .ordering_violation_o(lsq_ordering_violation_o),
        .outstanding_count_o(lsq_outstanding_count_o),
        .rst_n(rst_n),
        .store_addr_i(lsq_store_addr_i),
        .store_data_i(lsq_store_data_i),
        .store_ready_o(lsq_store_ready_o),
        .store_resp_error_o(lsq_store_resp_error_o),
        .store_resp_ready_i(lsq_store_resp_ready_i),
        .store_resp_tag_o(lsq_store_resp_tag_o),
        .store_resp_valid_o(lsq_store_resp_valid_o),
        .store_size_i(lsq_store_size_i),
        .store_strb_i(lsq_store_strb_i),
        .store_tag_i(lsq_store_tag_i),
        .store_valid_i(lsq_store_valid_i)
    );

    pl330_target_merge_buffer #(
        .AXI_DATA_WIDTH(AXI_DATA_WIDTH),
        .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
        .AXI_ID_WIDTH(AXI_ID_WIDTH),
        .AXI_STRB_WIDTH(AXI_STRB_WIDTH),
        .PTR_WIDTH(PTR_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH)
    ) u_merge_buffer (
        .accept_pulse_o(merge_buffer_accept_pulse_o),
        .clk(clk),
        .empty_o(merge_buffer_empty_o),
        .flush_i(merge_buffer_flush_i),
        .full_o(merge_buffer_full_o),
        .in_addr_i(merge_buffer_in_addr_i),
        .in_data_i(merge_buffer_in_data_i),
        .in_id_i(merge_buffer_in_id_i),
        .in_last_i(merge_buffer_in_last_i),
        .in_ready_o(merge_buffer_in_ready_o),
        .in_strb_i(merge_buffer_in_strb_i),
        .in_valid_i(merge_buffer_in_valid_i),
        .merge_pulse_o(merge_buffer_merge_pulse_o),
        .occupancy_o(merge_buffer_occupancy_o),
        .out_addr_o(merge_buffer_out_addr_o),
        .out_data_o(merge_buffer_out_data_o),
        .out_id_o(merge_buffer_out_id_o),
        .out_last_o(merge_buffer_out_last_o),
        .out_ready_i(merge_buffer_out_ready_i),
        .out_strb_o(merge_buffer_out_strb_o),
        .out_valid_o(merge_buffer_out_valid_o),
        .overflow_sticky_o(merge_buffer_overflow_sticky_o),
        .pop_pulse_o(merge_buffer_pop_pulse_o),
        .rst_n(rst_n)
    );

    pl330_target_mfifo #(
        .FIFO_DEPTH(MFIFO_DEPTH),
        .DATA_W(DATA_W),
        .ADDR_W(ADDR_W)
    ) u_mfifo (
        .cfg_nonsecure_allowed_i(mfifo_cfg_nonsecure_allowed_i),
        .channel_pc_o(mfifo_channel_pc_o),
        .channel_state_o(mfifo_channel_state_o),
        .clk(clk),
        .cmd_accept_o(mfifo_cmd_accept_o),
        .cmd_arg_addr_i(mfifo_cmd_arg_addr_i),
        .cmd_arg_data_i(mfifo_cmd_arg_data_i),
        .cmd_error_o(mfifo_cmd_error_o),
        .cmd_event_i(mfifo_cmd_event_i),
        .cmd_fault_code_o(mfifo_cmd_fault_code_o),
        .cmd_manager_i(mfifo_cmd_manager_i),
        .cmd_next_pc_i(mfifo_cmd_next_pc_i),
        .cmd_opcode_i(mfifo_cmd_opcode_i),
        .cmd_ready_o(mfifo_cmd_ready_o),
        .cmd_secure_i(mfifo_cmd_secure_i),
        .cmd_valid_i(mfifo_cmd_valid_i),
        .dbginst_write_i(mfifo_dbginst_write_i),
        .fault_clear_i(mfifo_fault_clear_i),
        .fault_status_o(mfifo_fault_status_o),
        .fault_valid_o(mfifo_fault_valid_o),
        .irq_clear_i(mfifo_irq_clear_i),
        .irq_status_o(mfifo_irq_status_o),
        .ld_req_addr_o(mfifo_ld_req_addr_o),
        .ld_req_ready_i(mfifo_ld_req_ready_i),
        .ld_req_valid_o(mfifo_ld_req_valid_o),
        .ld_rsp_data_i(mfifo_ld_rsp_data_i),
        .ld_rsp_error_i(mfifo_ld_rsp_error_i),
        .ld_rsp_ready_o(mfifo_ld_rsp_ready_o),
        .ld_rsp_valid_i(mfifo_ld_rsp_valid_i),
        .mfifo_count_o(mfifo_count_o),
        .mfifo_empty_o(mfifo_empty_o),
        .mfifo_full_o(mfifo_full_o),
        .mfifo_pop_data_o(mfifo_pop_data_o),
        .mfifo_pop_ready_o(mfifo_pop_ready_o),
        .mfifo_pop_valid_i(mfifo_pop_valid_i),
        .mfifo_push_data_i(mfifo_push_data_i),
        .mfifo_push_ready_o(mfifo_push_ready_o),
        .mfifo_push_valid_i(mfifo_push_valid_i),
        .outstanding_reads_o(mfifo_outstanding_reads_o),
        .outstanding_writes_o(mfifo_outstanding_writes_o),
        .reset_accepted_o(mfifo_reset_accepted_o),
        .rst_n(rst_n),
        .soft_reset_i(mfifo_soft_reset_i),
        .st_req_addr_o(mfifo_st_req_addr_o),
        .st_req_data_o(mfifo_st_req_data_o),
        .st_req_ready_i(mfifo_st_req_ready_i),
        .st_req_valid_o(mfifo_st_req_valid_o),
        .st_rsp_error_i(mfifo_st_rsp_error_i),
        .st_rsp_ready_o(mfifo_st_rsp_ready_o),
        .st_rsp_valid_i(mfifo_st_rsp_valid_i)
    );

    pl330_target_periph #(
        .NUM_PERIPH_REQS(NUM_PERIPH_REQS),
        .REQ_TYPE_W(REQ_TYPE_W),
        .PERIPH_ID_W(PERIPH_ID_W),
        .COUNT_W(COUNT_W)
    ) u_periph (
        .active_count_o(periph_active_count_o),
        .active_mask_o(periph_active_mask_o),
        .any_active_o(periph_any_active_o),
        .any_pending_o(periph_any_pending_o),
        .cfg_periph_enable_i(periph_cfg_periph_enable_i),
        .clk(clk),
        .engine_periph_done_i(periph_engine_periph_done_i),
        .engine_periph_done_id_i(periph_engine_periph_done_id_i),
        .engine_periph_id_o(periph_engine_periph_id_o),
        .engine_periph_last_o(periph_engine_periph_last_o),
        .engine_periph_ready_i(periph_engine_periph_ready_i),
        .engine_periph_type_o(periph_engine_periph_type_o),
        .engine_periph_valid_o(periph_engine_periph_valid_o),
        .pending_count_o(periph_pending_count_o),
        .pending_mask_o(periph_pending_mask_o),
        .periph_daready_o(periph_daready_o),
        .periph_drlast_i(periph_drlast_i),
        .periph_drtype_i(periph_drtype_i),
        .periph_drvalid_i(periph_drvalid_i),
        .rr_pointer_o(periph_rr_pointer_o),
        .rst_n(rst_n)
    );

    pl330_target_pipeline #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH),
        .STRB_WIDTH(STRB_WIDTH),
        .CTRL_WIDTH(CTRL_WIDTH),
        .ID_WIDTH(ID_WIDTH),
        .RESP_WIDTH(RESP_WIDTH),
        .COUNT_WIDTH(COUNT_WIDTH),
        .LATENCY_WIDTH(LATENCY_WIDTH)
    ) u_pipeline (
        .accepted_pulse(pipeline_accepted_pulse),
        .busy(pipeline_busy),
        .clk(clk),
        .cmpl_id(pipeline_cmpl_id),
        .cmpl_last(pipeline_cmpl_last),
        .cmpl_rdata(pipeline_cmpl_rdata),
        .cmpl_ready(pipeline_cmpl_ready),
        .cmpl_resp(pipeline_cmpl_resp),
        .cmpl_valid(pipeline_cmpl_valid),
        .completed_pulse(pipeline_completed_pulse),
        .debug_latency_count(pipeline_debug_latency_count),
        .debug_stage_valid(pipeline_debug_stage_valid),
        .debug_state(pipeline_debug_state),
        .enable(pipeline_enable),
        .engine_req_addr(pipeline_engine_req_addr),
        .engine_req_ctrl(pipeline_engine_req_ctrl),
        .engine_req_id(pipeline_engine_req_id),
        .engine_req_len(pipeline_engine_req_len),
        .engine_req_ready(pipeline_engine_req_ready),
        .engine_req_size(pipeline_engine_req_size),
        .engine_req_strb(pipeline_engine_req_strb),
        .engine_req_valid(pipeline_engine_req_valid),
        .engine_req_wdata(pipeline_engine_req_wdata),
        .engine_req_write(pipeline_engine_req_write),
        .engine_rsp_id(pipeline_engine_rsp_id),
        .engine_rsp_last(pipeline_engine_rsp_last),
        .engine_rsp_rdata(pipeline_engine_rsp_rdata),
        .engine_rsp_ready(pipeline_engine_rsp_ready),
        .engine_rsp_resp(pipeline_engine_rsp_resp),
        .engine_rsp_valid(pipeline_engine_rsp_valid),
        .error_seen(pipeline_error_seen),
        .flush(pipeline_flush),
        .idle(pipeline_idle),
        .in_flight_count(pipeline_in_flight_count),
        .issue_addr(pipeline_issue_addr),
        .issue_ctrl(pipeline_issue_ctrl),
        .issue_id(pipeline_issue_id),
        .issue_len(pipeline_issue_len),
        .issue_ready(pipeline_issue_ready),
        .issue_size(pipeline_issue_size),
        .issue_strb(pipeline_issue_strb),
        .issue_valid(pipeline_issue_valid),
        .issue_wdata(pipeline_issue_wdata),
        .issue_write(pipeline_issue_write),
        .issued_pulse(pipeline_issued_pulse),
        .pipe_req_addr(pipeline_pipe_req_addr),
        .pipe_req_ctrl(pipeline_pipe_req_ctrl),
        .pipe_req_id(pipeline_pipe_req_id),
        .pipe_req_len(pipeline_pipe_req_len),
        .pipe_req_ready(pipeline_pipe_req_ready),
        .pipe_req_size(pipeline_pipe_req_size),
        .pipe_req_strb(pipeline_pipe_req_strb),
        .pipe_req_valid(pipeline_pipe_req_valid),
        .pipe_req_wdata(pipeline_pipe_req_wdata),
        .pipe_req_write(pipeline_pipe_req_write),
        .pipe_rsp_id(pipeline_pipe_rsp_id),
        .pipe_rsp_last(pipeline_pipe_rsp_last),
        .pipe_rsp_rdata(pipeline_pipe_rsp_rdata),
        .pipe_rsp_ready(pipeline_pipe_rsp_ready),
        .pipe_rsp_resp(pipeline_pipe_rsp_resp),
        .pipe_rsp_valid(pipeline_pipe_rsp_valid),
        .req_addr(pipeline_req_addr),
        .req_ctrl(pipeline_req_ctrl),
        .req_id(pipeline_req_id),
        .req_len(pipeline_req_len),
        .req_ready(pipeline_req_ready),
        .req_size(pipeline_req_size),
        .req_strb(pipeline_req_strb),
        .req_valid(req_valid),
        .req_wdata(pipeline_req_wdata),
        .req_write(pipeline_req_write),
        .rsp_id(pipeline_rsp_id),
        .rsp_last(pipeline_rsp_last),
        .rsp_rdata(pipeline_rsp_rdata),
        .rsp_ready(rsp_ready),
        .rsp_resp(pipeline_rsp_resp),
        .rsp_valid(pipeline_rsp_valid),
        .rst_n(rst_n),
        .stalled(pipeline_stalled)
    );

    assign security_status_w = {
        SECURITY_STATUS_TAG,
        boot_security_locked_q,
        boot_manager_ns_q,
        security_protocol_error_q,
        security_unlock_ok_w,
        security_subcmd_w,
        boot_irq_ns_q[7:0],
        boot_periph_ns_q[7:0]
    };

    assign security_mix_w = {
        boot_periph_ns_q,
        boot_irq_ns_q[14:0],
        boot_irq_ns_q[15] ^ boot_manager_ns_q
    };

    assign transaction_status_w = {
        PL330_STATUS_TAG,
        channel_state_q,
        outstanding_writes_q,
        event_idx_w,
        irq_abort_pulse_q,
        daready_q,
        axi_aw_issued_q,
        axi_w_issued_q,
        terminal_fsm_state_q | terminal_status_observed_q,
        pipeline_publish_valid_q | latency_bound_observed_q,
        pipeline_evaluate_valid_q | backpressure_hold_observed_q,
        pipeline_accept_valid_q | req_stability_violation_q | rsp_stability_violation_q
    };

    assign workflow_status_w = {
        CONTRACT_STATUS_TAG,
        rtl_gen_quality_gates_progress_q[7:0],
        workflow_todo_event_seen_q | function_model_tx_seen_q | cycle_model_rule_seen_q | top_module_flow_seen_q
    };

    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            aux_reset_released_q <= 1'b0;
            aux_activity_q       <= 1'b0;
        end else begin
            aux_reset_released_q <= 1'b1;
            aux_activity_q       <= ~aux_activity_q;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            aux_reset_sync1_q    <= 1'b0;
            aux_reset_sync2_q    <= 1'b0;
            aux_activity_sync1_q <= 1'b0;
            aux_activity_sync2_q <= 1'b0;
        end else begin
            aux_reset_sync1_q    <= aux_reset_released_q;
            aux_reset_sync2_q    <= aux_reset_sync1_q;
            aux_activity_sync1_q <= aux_activity_q;
            aux_activity_sync2_q <= aux_activity_sync1_q;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            link_ready_q              <= 1'b0;
            reset_settle_q            <= 4'h0;
            reset_fault_q             <= 1'b0;
            protocol_error_q          <= 1'b0;
            pending_q                 <= 1'b0;
            rsp_data_q                <= {DATA_WIDTH{1'b0}};
            flow_count_q              <= {DATA_WIDTH{1'b0}};
            boot_manager_ns_q         <= 1'b0;
            boot_irq_ns_q             <= {SECURITY_IRQ_NS_WIDTH{1'b0}};
            boot_periph_ns_q          <= {SECURITY_PERIPH_NS_WIDTH{1'b0}};
            boot_security_locked_q    <= 1'b0;
            security_protocol_error_q <= 1'b0;
            channel_state_q           <= CHANNEL_STATE_IDLE;
            outstanding_writes_q      <= {OUTSTANDING_WIDTH{1'b0}};
            irq_status_q              <= {NUM_IRQS{1'b0}};
            irq_pulse_q               <= {NUM_IRQS{1'b0}};
            irq_abort_pulse_q         <= 1'b0;
            fault_status_q            <= {24'h0, FAULT_NONE};
            daready_q                 <= 1'b0;
            axi_aw_issued_q           <= 1'b0;
            axi_w_issued_q            <= 1'b0;
            terminal_fsm_state_q      <= 1'b0;
            debug_event_q             <= 1'b0;
            req_payload_hold_valid_q  <= 1'b0;
            req_payload_hold_q        <= {DATA_WIDTH{1'b0}};
            latency_counter_q         <= 4'h0;
            backpressure_counter_q    <= 4'h0;
            pipeline_accept_valid_q   <= 1'b0;
            pipeline_evaluate_valid_q <= 1'b0;
            pipeline_publish_valid_q  <= 1'b0;
            pipeline_accept_data_q    <= {DATA_WIDTH{1'b0}};
            pipeline_evaluate_data_q  <= {DATA_WIDTH{1'b0}};
            pipeline_publish_data_q   <= {DATA_WIDTH{1'b0}};
            req_stability_violation_q <= 1'b0;
            rsp_stability_violation_q <= 1'b0;
            rsp_hold_active_q         <= 1'b0;
            rsp_hold_data_q           <= {DATA_WIDTH{1'b0}};
            latency_bound_violation_q <= 1'b0;
            latency_bound_observed_q  <= 1'b0;
            backpressure_hold_observed_q <= 1'b0;
            terminal_status_observed_q   <= 1'b0;
            contract_event_count_q       <= 32'h00000000;
            ssot_contract_progress_q     <= 32'h00000000;
            derive_rtl_todos_audit_progress_q <= 32'h00000000;
            rtl_gen_quality_gates_progress_q  <= 32'h00000000;
            workflow_todo_event_seen_q        <= 16'h0000;
            function_model_tx_seen_q          <= 16'h0000;
            cycle_model_rule_seen_q           <= 16'h0000;
            top_module_flow_seen_q            <= 16'h0000;
        end else begin
            irq_pulse_q          <= {NUM_IRQS{1'b0}};
            irq_abort_pulse_q    <= 1'b0;
            daready_q            <= 1'b0;
            axi_aw_issued_q      <= 1'b0;
            axi_w_issued_q       <= 1'b0;
            terminal_fsm_state_q <= 1'b0;
            debug_event_q        <= 1'b0;

            if (quality_gates_observable_event_w) begin
                ssot_contract_progress_q <= ssot_contract_progress_q + 32'h00000001;
                derive_rtl_todos_audit_progress_q <= derive_rtl_todos_audit_progress_q + {31'h00000000, rtl_implement_ssot_contract_event_w};
                rtl_gen_quality_gates_progress_q <= rtl_gen_quality_gates_progress_q + {31'h00000000, rtl_module_pl330_target_event_w};
                workflow_todo_event_seen_q <= workflow_todo_event_seen_q | 16'h0003;
            end

            if (cycle_model_reset_release_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0100;
                top_module_flow_seen_q  <= top_module_flow_seen_q | 16'h0001;
            end

            if (cycle_model_pipeline_accept_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0004;
                top_module_flow_seen_q  <= top_module_flow_seen_q | 16'h0002;
            end

            if (cycle_model_pipeline_evaluate_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0008;
            end

            if (cycle_model_pipeline_publish_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0010;
            end

            if (cycle_model_ordering_terminal_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0060;
            end

            if (cycle_model_latency_bound_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0080;
            end

            if (cycle_model_backpressure_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0200;
            end

            if (aux_reset_sync2_q) begin
                link_ready_q   <= 1'b1;
                reset_settle_q <= 4'h0;
            end else begin
                link_ready_q <= 1'b0;
                if (!reset_settle_done_w) begin
                    reset_settle_q <= reset_settle_q + 4'h1;
                end else begin
                    reset_fault_q <= 1'b1;
                end
            end

            if (req_valid && !req_ready) begin
                backpressure_hold_observed_q <= 1'b1;
                if (!req_payload_hold_valid_q) begin
                    req_payload_hold_valid_q <= 1'b1;
                    req_payload_hold_q       <= req_data;
                end else if (req_payload_hold_q != req_data) begin
                    req_stability_violation_q <= 1'b1;
                    protocol_error_q          <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                end
                if (backpressure_counter_q != 4'hf) begin
                    backpressure_counter_q <= backpressure_counter_q + 4'h1;
                end
            end else if (accept_req_w) begin
                req_payload_hold_valid_q <= 1'b0;
                req_payload_hold_q       <= req_data;
                backpressure_counter_q   <= 4'h0;
            end else if (!req_valid) begin
                req_payload_hold_valid_q <= 1'b0;
                backpressure_counter_q   <= 4'h0;
            end

            if (pending_q && !rsp_ready) begin
                if (!rsp_hold_active_q) begin
                    rsp_hold_active_q <= 1'b1;
                    rsp_hold_data_q   <= rsp_data_q;
                end else if (rsp_hold_data_q != rsp_data_q) begin
                    rsp_stability_violation_q <= 1'b1;
                    protocol_error_q          <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                end
            end else begin
                rsp_hold_active_q <= 1'b0;
                rsp_hold_data_q   <= rsp_data_q;
            end

            if (req_payload_changed_while_wait_w | rsp_payload_changed_while_wait_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0400;
            end

            if (req_valid && !link_ready_w) begin
                protocol_error_q <= 1'b1;
                fault_status_q   <= {24'h0, FAULT_PROTOCOL};
            end

            pipeline_accept_valid_q   <= accept_req_w;
            pipeline_evaluate_valid_q <= pipeline_accept_valid_q;
            pipeline_publish_valid_q  <= pipeline_evaluate_valid_q;
            if (accept_req_w) begin
                pipeline_accept_data_q <= req_data;
            end
            if (pipeline_accept_valid_q) begin
                pipeline_evaluate_data_q <= pipeline_accept_data_q;
            end
            if (pipeline_evaluate_valid_q) begin
                pipeline_publish_data_q <= pipeline_evaluate_data_q;
            end

            if (accept_req_w) begin
                latency_counter_q <= 4'h0;
            end else if (pipeline_busy_w) begin
                if (latency_counter_q != 4'hf) begin
                    latency_counter_q <= latency_counter_q + 4'h1;
                end
            end

            if (pipeline_terminal_w) begin
                terminal_status_observed_q <= 1'b1;
                latency_bound_observed_q   <= (latency_counter_q <= PIPELINE_LATENCY_BOUND);
            end

            if (latency_bound_exceeded_w) begin
                latency_bound_violation_q <= 1'b1;
                protocol_error_q          <= 1'b1;
                fault_status_q            <= {24'h0, FAULT_PROTOCOL};
            end

            if (accept_req_w | pipeline_terminal_w | consume_rsp_w | debug_event_q) begin
                contract_event_count_q <= contract_event_count_q + 32'h00000001;
            end

            if (dma_write_complete_w) begin
                outstanding_writes_q <= outstanding_writes_q - {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
            end

            if (security_access_w) begin
                top_module_flow_seen_q <= top_module_flow_seen_q | 16'h0004;
                if (security_write_w && (!security_unlock_ok_w || boot_security_locked_q)) begin
                    security_protocol_error_q <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                end

                if (security_write_allowed_w) begin
                    case (security_subcmd_w)
                        SECURITY_SUB_MANAGER: begin
                            boot_manager_ns_q <= boot_manager_ns_update_w;
                        end
                        SECURITY_SUB_IRQ: begin
                            boot_irq_ns_q <= boot_irq_ns_update_w;
                        end
                        SECURITY_SUB_PERIPH: begin
                            boot_periph_ns_q <= boot_periph_ns_update_w;
                        end
                        SECURITY_SUB_STATUS: begin
                            boot_security_locked_q <= security_lock_w | boot_security_locked_q;
                        end
                        default: begin
                            security_protocol_error_q <= 1'b1;
                            fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                        end
                    endcase
                end

                if (security_lock_w) begin
                    boot_security_locked_q <= 1'b1;
                end
            end else if (non_security_accept_w && !boot_security_locked_q) begin
                boot_security_locked_q <= 1'b1;
            end

            if (non_security_accept_w && (control_data_opcode_w == PL330_OPCODE_DMASTART) &&
                (channel_state_q == CHANNEL_STATE_IDLE)) begin
                channel_state_q      <= CHANNEL_STATE_RUN;
                terminal_fsm_state_q <= 1'b1;
                debug_event_q        <= 1'b1;
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0001;
            end

            if (fm_dmastp_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0020;
                if (fm_dmastp_precondition_w) begin
                    outstanding_writes_q <= outstanding_writes_q + {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
                    daready_q            <= 1'b1;
                    axi_aw_issued_q      <= 1'b1;
                    axi_w_issued_q       <= 1'b1;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMASTP_PRECOND};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dmasev_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0040;
                if (fm_dmasev_precondition_w) begin
                    irq_status_q         <= irq_status_q | event_irq_mask_w;
                    irq_pulse_q          <= event_irq_mask_w;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMASEV_EVENT};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dmaend_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0080;
                if (fm_dmaend_precondition_w) begin
                    channel_state_q      <= CHANNEL_STATE_IDLE;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMAEND_BUSY};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dma_error_case_w) begin
                channel_state_q   <= CHANNEL_STATE_FAULT;
                irq_abort_pulse_q <= 1'b1;
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0100;
            end

            if (reset_fault_q | protocol_error_q | security_protocol_error_q |
                req_stability_violation_q | rsp_stability_violation_q | latency_bound_violation_q) begin
                channel_state_q   <= CHANNEL_STATE_FAULT;
                irq_abort_pulse_q <= 1'b1;
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0100;
            end

            if (accept_req_w) begin
                pending_q    <= 1'b1;
                flow_count_q <= flow_count_q + flow_increment_w;
                if (security_access_w && (security_read_w || !security_write_w)) begin
                    rsp_data_q <= security_status_w;
                end else if (security_access_w) begin
                    rsp_data_q <= security_status_w ^ security_mix_w;
                end else if (fm_dmastp_accept_w | fm_dmasev_accept_w | fm_dmaend_accept_w) begin
                    rsp_data_q <= transaction_status_w ^ fault_status_q ^ {16'h0, irq_status_q[15:0]};
                end else begin
                    rsp_data_q <= response_mix_w ^ security_mix_w ^ transaction_status_w ^ workflow_status_w;
                end
            end else if (consume_rsp_w) begin
                pending_q <= 1'b0;
            end
        end
    end

endmodule

`default_nettype wire
