module pl330realverify #(
    parameter integer DATA_WIDTH = 64,
    parameter integer ADDR_WIDTH = 32,
    parameter integer ID_WIDTH = 6,
    parameter integer NUM_CHANNELS = 8,
    parameter integer NUM_EVENTS = 32,
    parameter integer REG_ADDR_WIDTH = 12,
    parameter integer MAX_BURST_LEN = 16,
    parameter integer SUPPORT_UNALIGNED = 0
) (
    input  logic                         dmaclk,
    input  logic                         dmacresetn,

    input  logic [REG_ADDR_WIDTH-1:0]    paddr,
    input  logic                         psel,
    input  logic                         penable,
    input  logic                         pwrite,
    input  logic [31:0]                  pwdata,
    input  logic [3:0]                   pstrb,
    output logic [31:0]                  prdata,
    output logic                         pready,
    output logic                         pslverr,

    output logic [ID_WIDTH-1:0]          arid,
    output logic [ADDR_WIDTH-1:0]        araddr,
    output logic [7:0]                   arlen,
    output logic [2:0]                   arsize,
    output logic [1:0]                   arburst,
    output logic [3:0]                   arcache,
    output logic [2:0]                   arprot,
    output logic                         arvalid,
    input  logic                         arready,
    input  logic [ID_WIDTH-1:0]          rid,
    input  logic [DATA_WIDTH-1:0]        rdata,
    input  logic [1:0]                   rresp,
    input  logic                         rlast,
    input  logic                         rvalid,
    output logic                         rready,

    output logic [ID_WIDTH-1:0]          awid,
    output logic [ADDR_WIDTH-1:0]        awaddr,
    output logic [7:0]                   awlen,
    output logic [2:0]                   awsize,
    output logic [1:0]                   awburst,
    output logic [3:0]                   awcache,
    output logic [2:0]                   awprot,
    output logic                         awvalid,
    input  logic                         awready,
    output logic [DATA_WIDTH-1:0]        wdata,
    output logic [(DATA_WIDTH/8)-1:0]    wstrb,
    output logic                         wlast,
    output logic                         wvalid,
    input  logic                         wready,
    input  logic [ID_WIDTH-1:0]          bid,
    input  logic [1:0]                   bresp,
    input  logic                         bvalid,
    output logic                         bready,

    input  logic [NUM_EVENTS-1:0]        peripheral_events,
    output logic                         dmac_irq
);
    logic [31:0] intstatus;
    logic [31:0] inten;

    logic [ADDR_WIDTH-1:0] sar_ch0;
    logic [ADDR_WIDTH-1:0] dar_ch0;
    logic [7:0] loop_count_ch0;
    logic [3:0] burst_len_ch0;
    logic wfp_enable_ch0;
    logic [4:0] wfp_event_ch0;
    logic fault_inject_ch0;
    logic [ADDR_WIDTH-1:0] pc_ch0;

    logic start_cmd_ch0_pulse;
    logic halt_cmd_ch0_pulse;
    logic debug_execute_pulse;
    logic debug_reject_pulse;
    logic [2:0] dbg_channel;
    logic intstatus_w1c_valid;
    logic [31:0] intstatus_w1c_mask;

    logic [3:0] channel_state;
    logic issue_ar;
    logic accept_r;
    logic issue_aw;
    logic issue_w;
    logic accept_b;
    logic post_complete;
    logic post_fault;
    logic manager_busy;

    logic ar_done;
    logic r_done_ok;
    logic r_done_err;
    logic aw_done;
    logic w_done;
    logic b_done_ok;
    logic b_done_err;

    logic [DATA_WIDTH-1:0] rd_data_from_axi;
    logic [DATA_WIDTH-1:0] wdata_from_axi_wr;
    logic [(DATA_WIDTH/8)-1:0] wstrb_from_axi_wr;
    logic set_dbg_done_from_dp;

    logic [ADDR_WIDTH-1:0] src_addr;
    logic [ADDR_WIDTH-1:0] dst_addr;
    logic [3:0] burst_len_dp;
    logic [DATA_WIDTH-1:0] wr_data_dp;
    logic [(DATA_WIDTH/8)-1:0] wr_strb_dp;
    logic addresses_aligned;
    logic loop_is_last;
    logic [3:0] status_dp;
    logic [3:0] error_code_dp;
    logic [7:0] loop_remaining_dp;
    logic set_complete_pulse;
    logic set_fault_pulse;
    logic set_dbg_done_pulse;

    logic selected_event;
    logic fault_clear;

    logic [3:0] csr_status_ch0;

    // Derive status shown in CSR from FSM and datapath fault/completion classification.
    always @(*) begin
        csr_status_ch0 = channel_state;
        if (status_dp == 4'd8) csr_status_ch0 = 4'd8;
        else if (status_dp == 4'd6) csr_status_ch0 = 4'd6;
    end

    // Debug execute pulse in this subset is observable via dbg_done pending set.
    assign set_dbg_done_pulse = debug_execute_pulse | debug_reject_pulse;

    assign wdata = wdata_from_axi_wr;
    assign wstrb = wstrb_from_axi_wr;

    pl330realverify_regs #(
        .NUM_CHANNELS(NUM_CHANNELS),
        .REG_ADDR_WIDTH(REG_ADDR_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) u_regs (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .paddr_i(paddr),
        .psel_i(psel),
        .penable_i(penable),
        .pwrite_i(pwrite),
        .pwdata_i(pwdata),
        .pstrb_i(pstrb),
        .prdata_o(prdata),
        .pready_o(pready),
        .pslverr_o(pslverr),
        .intstatus_i(intstatus),
        .csr_status_ch0_i(csr_status_ch0),
        .csr_error_ch0_i(error_code_dp),
        .csr_loop_remaining_ch0_i(loop_remaining_dp),
        .manager_busy_i(manager_busy),
        .inten_o(inten),
        .sar_ch0_o(sar_ch0),
        .dar_ch0_o(dar_ch0),
        .loop_count_ch0_o(loop_count_ch0),
        .burst_len_ch0_o(burst_len_ch0),
        .wfp_enable_ch0_o(wfp_enable_ch0),
        .wfp_event_ch0_o(wfp_event_ch0),
        .fault_inject_ch0_o(fault_inject_ch0),
        .pc_ch0_o(pc_ch0),
        .start_cmd_ch0_pulse_o(start_cmd_ch0_pulse),
        .halt_cmd_ch0_pulse_o(halt_cmd_ch0_pulse),
        .debug_execute_pulse_o(debug_execute_pulse),
        .debug_reject_pulse_o(debug_reject_pulse),
        .dbg_channel_o(dbg_channel),
        .intstatus_w1c_valid_o(intstatus_w1c_valid),
        .intstatus_w1c_mask_o(intstatus_w1c_mask)
    );

    pl330realverify_channel_fsm u_channel_fsm (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .start_cmd_i(start_cmd_ch0_pulse),
        .halt_cmd_i(halt_cmd_ch0_pulse),
        .wfp_enable_i(wfp_enable_ch0),
        .selected_event_i(selected_event),
        .fault_inject_i(fault_inject_ch0),
        .addresses_aligned_i(addresses_aligned),
        .ar_done_i(ar_done),
        .r_done_ok_i(r_done_ok),
        .r_done_err_i(r_done_err),
        .aw_done_i(aw_done),
        .w_done_i(w_done),
        .b_done_ok_i(b_done_ok),
        .b_done_err_i(b_done_err),
        .loop_is_last_i(loop_is_last),
        .fault_clear_i(fault_clear),
        .state_o(channel_state),
        .issue_ar_o(issue_ar),
        .accept_r_o(accept_r),
        .issue_aw_o(issue_aw),
        .issue_w_o(issue_w),
        .accept_b_o(accept_b),
        .post_complete_o(post_complete),
        .post_fault_o(post_fault),
        .manager_busy_o(manager_busy)
    );

    pl330realverify_axi_rd #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .ID_WIDTH(ID_WIDTH),
        .MAX_BURST_LEN(MAX_BURST_LEN)
    ) u_axi_rd (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .issue_ar_i(issue_ar),
        .src_addr_i(src_addr),
        .burst_len_cfg_i(burst_len_dp),
        .arid_o(arid),
        .araddr_o(araddr),
        .arlen_o(arlen),
        .arsize_o(arsize),
        .arburst_o(arburst),
        .arcache_o(arcache),
        .arprot_o(arprot),
        .arvalid_o(arvalid),
        .arready_i(arready),
        .rid_i(rid),
        .rdata_i(rdata),
        .rresp_i(rresp),
        .rlast_i(rlast),
        .rvalid_i(rvalid),
        .rready_o(rready),
        .ar_done_o(ar_done),
        .r_done_ok_o(r_done_ok),
        .r_done_err_o(r_done_err),
        .rd_data_o(rd_data_from_axi)
    );

    pl330realverify_axi_wr #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .ID_WIDTH(ID_WIDTH),
        .MAX_BURST_LEN(MAX_BURST_LEN)
    ) u_axi_wr (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .issue_aw_i(issue_aw),
        .issue_w_i(issue_w),
        .dst_addr_i(dst_addr),
        .burst_len_cfg_i(burst_len_dp),
        .wr_data_i(wr_data_dp),
        .awid_o(awid),
        .awaddr_o(awaddr),
        .awlen_o(awlen),
        .awsize_o(awsize),
        .awburst_o(awburst),
        .awcache_o(awcache),
        .awprot_o(awprot),
        .awvalid_o(awvalid),
        .awready_i(awready),
        .wdata_o(wdata_from_axi_wr),
        .wstrb_o(wstrb_from_axi_wr),
        .wlast_o(wlast),
        .wvalid_o(wvalid),
        .wready_i(wready),
        .bid_i(bid),
        .bresp_i(bresp),
        .bvalid_i(bvalid),
        .bready_o(bready),
        .aw_done_o(aw_done),
        .w_done_o(w_done),
        .b_done_ok_o(b_done_ok),
        .b_done_err_o(b_done_err)
    );

    pl330realverify_datapath #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH),
        .SUPPORT_UNALIGNED(SUPPORT_UNALIGNED)
    ) u_datapath (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .start_cmd_i(start_cmd_ch0_pulse),
        .halt_cmd_i(halt_cmd_ch0_pulse),
        .fault_inject_i(fault_inject_ch0),
        .debug_reject_i(debug_reject_pulse),
        .cfg_sar_i(sar_ch0),
        .cfg_dar_i(dar_ch0),
        .cfg_loop_count_i(loop_count_ch0),
        .cfg_burst_len_i(burst_len_ch0),
        .r_done_ok_i(r_done_ok & accept_r),
        .r_done_err_i(r_done_err & accept_r),
        .b_done_ok_i(b_done_ok & accept_b),
        .b_done_err_i(b_done_err & accept_b),
        .rd_data_i(rd_data_from_axi),
        .src_addr_o(src_addr),
        .dst_addr_o(dst_addr),
        .burst_len_o(burst_len_dp),
        .wr_data_o(wr_data_dp),
        .wr_strb_o(wr_strb_dp),
        .addresses_aligned_o(addresses_aligned),
        .loop_is_last_o(loop_is_last),
        .status_o(status_dp),
        .error_code_o(error_code_dp),
        .loop_remaining_o(loop_remaining_dp),
        .set_complete_pulse_o(set_complete_pulse),
        .set_fault_pulse_o(set_fault_pulse),
        .set_dbg_done_pulse_o(set_dbg_done_from_dp)
    );

    pl330realverify_event_irq #(
        .NUM_EVENTS(NUM_EVENTS)
    ) u_event_irq (
        .clk_i(dmaclk),
        .rst_ni(dmacresetn),
        .peripheral_events_i(peripheral_events),
        .wfp_event_sel_i(wfp_event_ch0),
        .inten_i(inten),
        .w1c_valid_i(intstatus_w1c_valid),
        .w1c_mask_i(intstatus_w1c_mask),
        .set_complete_i(set_complete_pulse | post_complete),
        .set_fault_i(set_fault_pulse | post_fault),
        .set_dbg_done_i(set_dbg_done_pulse),
        .intstatus_o(intstatus),
        .selected_event_o(selected_event),
        .irq_o(dmac_irq),
        .fault_clear_o(fault_clear)
    );

    // Consume currently single-channel debug selector to avoid dead configuration in this subset.
    wire _unused_dbg_channel = (^dbg_channel) ^ (^pc_ch0) ^ (^wr_strb_dp) ^ set_dbg_done_from_dp;

endmodule
