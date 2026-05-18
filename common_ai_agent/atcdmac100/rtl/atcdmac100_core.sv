module atcdmac100_core #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32,
    parameter DMA_CH_NUM = 8,
    parameter REQ_ACK_NUM = 16,
    parameter FIFO_DEPTH = 8,
    parameter CHAIN_TRANSFER_SUPPORT = 1
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    output logic                  dma_int,
    input  logic [REQ_ACK_NUM-1:0] dma_req,
    output logic [REQ_ACK_NUM-1:0] dma_ack,
    input  logic [ADDR_WIDTH-1:0] haddr,
    input  logic [1:0]            htrans,
    input  logic                  hwrite,
    input  logic [2:0]            hsize,
    input  logic [2:0]            hburst,
    input  logic [DATA_WIDTH-1:0] hwdata,
    input  logic                  hsel,
    input  logic                  hreadyin,
    output logic [DATA_WIDTH-1:0] hrdata,
    output logic [1:0]            hresp,
    output logic                  hready,
    output logic [ADDR_WIDTH-1:0] haddr_mst,
    output logic [1:0]            htrans_mst,
    output logic                  hwrite_mst,
    output logic [2:0]            hsize_mst,
    output logic [3:0]            hprot_mst,
    output logic                  hlock_mst,
    output logic [2:0]            hburst_mst,
    output logic [DATA_WIDTH-1:0] hwdata_mst,
    input  logic [DATA_WIDTH-1:0] hrdata_mst,
    input  logic [1:0]            hresp_mst,
    input  logic                  hready_mst,
    output logic                  hbusreq_mst,
    input  logic                  hgrant_mst
);
    localparam [19:0] IdRev_ID = 20'h01021;
    localparam [7:0] RevMajor = 8'h01;
    localparam [3:0] RevMinor = 4'h2;
    localparam [31:0] IdRev = {IdRev_ID, RevMajor, RevMinor};
    localparam [4:0] CFG_REQ_NUM =
        (REQ_ACK_NUM >= 16) ? 5'd16 :
        (REQ_ACK_NUM == 15) ? 5'd15 :
        (REQ_ACK_NUM == 14) ? 5'd14 :
        (REQ_ACK_NUM == 13) ? 5'd13 :
        (REQ_ACK_NUM == 12) ? 5'd12 :
        (REQ_ACK_NUM == 11) ? 5'd11 :
        (REQ_ACK_NUM == 10) ? 5'd10 :
        (REQ_ACK_NUM == 9) ? 5'd9 :
        (REQ_ACK_NUM == 8) ? 5'd8 :
        (REQ_ACK_NUM == 7) ? 5'd7 :
        (REQ_ACK_NUM == 6) ? 5'd6 :
        (REQ_ACK_NUM == 5) ? 5'd5 :
        (REQ_ACK_NUM == 4) ? 5'd4 :
        (REQ_ACK_NUM == 3) ? 5'd3 :
        (REQ_ACK_NUM == 2) ? 5'd2 : 5'd1;
    localparam [5:0] CFG_FIFO_DEPTH =
        (FIFO_DEPTH >= 32) ? 6'd32 :
        (FIFO_DEPTH == 16) ? 6'd16 :
        (FIFO_DEPTH == 8) ? 6'd8 : 6'd4;
    localparam [3:0] CFG_CH_NUM =
        (DMA_CH_NUM >= 8) ? 4'd8 :
        (DMA_CH_NUM == 7) ? 4'd7 :
        (DMA_CH_NUM == 6) ? 4'd6 :
        (DMA_CH_NUM == 5) ? 4'd5 :
        (DMA_CH_NUM == 4) ? 4'd4 :
        (DMA_CH_NUM == 3) ? 4'd3 :
        (DMA_CH_NUM == 2) ? 4'd2 : 4'd1;
    localparam ChainXfr = (CHAIN_TRANSFER_SUPPORT != 0);
    localparam ReqSync = 1'b0;
    localparam [4:0] ReqNum = CFG_REQ_NUM;
    localparam [5:0] FIFODepth = CFG_FIFO_DEPTH;
    localparam [3:0] ChannelNum = CFG_CH_NUM;
    localparam [31:0] DMACfg = {ChainXfr, ReqSync, 15'd0, ReqNum, FIFODepth, ChannelNum};
    localparam [7:0] DMACtrl = 8'h20;
    localparam [7:0] IntStatus = 8'h30;
    localparam [7:0] ChEN = 8'h34;
    localparam [7:0] ChAbort = 8'h40;
    localparam [7:0] ChnCtrl = 8'h44;
    localparam [7:0] ChnSrcAddr = 8'h48;
    localparam [7:0] ChnDstAddr = 8'h4c;
    localparam [7:0] ChnTranSize = 8'h50;
    localparam [7:0] ChnLLPointer = 8'h54;
    localparam [1:0] RESP_OKAY = 2'b00;
    localparam [1:0] RESP_ERROR = 2'b10;
    localparam [1:0] HTRANS_IDLE = 2'b00;
    localparam [1:0] HTRANS_NONSEQ = 2'b10;
    localparam [1:0] HTRANS_SEQ = 2'b11;
    localparam [2:0] HSIZE_WORD = 3'b010;
    localparam [2:0] HBURST_SINGLE = 3'b000;
    localparam [2:0] HBURST_INCR = 3'b001;
    localparam [2:0] IDLE = 3'd0;
    localparam [2:0] ARBITRATE = 3'd1;
    localparam [2:0] READ_ADDR = 3'd2;
    localparam [2:0] WRITE_ADDR = 3'd3;
    localparam [2:0] WRITE_DATA = 3'd4;
    localparam [2:0] COMPLETE = 3'd5;
    localparam [2:0] ERROR_ABORT = 3'd6;
    localparam [2:0] CHAIN_LOAD = 3'd7;

    logic [31:0] ch0_ctrl_q;
    logic [31:0] ch1_ctrl_q;
    logic [31:0] ch2_ctrl_q;
    logic [31:0] ch3_ctrl_q;
    logic [31:0] ch4_ctrl_q;
    logic [31:0] ch5_ctrl_q;
    logic [31:0] ch6_ctrl_q;
    logic [31:0] ch7_ctrl_q;
    logic [ADDR_WIDTH-1:0] ch0_src_q;
    logic [ADDR_WIDTH-1:0] ch1_src_q;
    logic [ADDR_WIDTH-1:0] ch2_src_q;
    logic [ADDR_WIDTH-1:0] ch3_src_q;
    logic [ADDR_WIDTH-1:0] ch4_src_q;
    logic [ADDR_WIDTH-1:0] ch5_src_q;
    logic [ADDR_WIDTH-1:0] ch6_src_q;
    logic [ADDR_WIDTH-1:0] ch7_src_q;
    logic [ADDR_WIDTH-1:0] ch0_dst_q;
    logic [ADDR_WIDTH-1:0] ch1_dst_q;
    logic [ADDR_WIDTH-1:0] ch2_dst_q;
    logic [ADDR_WIDTH-1:0] ch3_dst_q;
    logic [ADDR_WIDTH-1:0] ch4_dst_q;
    logic [ADDR_WIDTH-1:0] ch5_dst_q;
    logic [ADDR_WIDTH-1:0] ch6_dst_q;
    logic [ADDR_WIDTH-1:0] ch7_dst_q;
    logic [21:0] ch0_size_q;
    logic [21:0] ch1_size_q;
    logic [21:0] ch2_size_q;
    logic [21:0] ch3_size_q;
    logic [21:0] ch4_size_q;
    logic [21:0] ch5_size_q;
    logic [21:0] ch6_size_q;
    logic [21:0] ch7_size_q;
    logic [ADDR_WIDTH-1:0] ch0_llp_q;
    logic [ADDR_WIDTH-1:0] ch1_llp_q;
    logic [ADDR_WIDTH-1:0] ch2_llp_q;
    logic [ADDR_WIDTH-1:0] ch3_llp_q;
    logic [ADDR_WIDTH-1:0] ch4_llp_q;
    logic [ADDR_WIDTH-1:0] ch5_llp_q;
    logic [ADDR_WIDTH-1:0] ch6_llp_q;
    logic [ADDR_WIDTH-1:0] ch7_llp_q;

    logic [7:0] int_tc_q;
    logic [7:0] int_abort_q;
    logic [7:0] int_error_q;
    logic [7:0] cfg_ch_mask;
    logic [7:0] enabled_mask;
    logic [7:0] priority_mask;
    logic [7:0] eligible_mask;
    logic [2:0] arb_ch_d;
    logic       arb_valid_d;
    logic [2:0] last_rr_q;
    logic [2:0] active_ch_q;
    logic [2:0] state_q;
    logic [7:0] fsm_state_cover;
    logic [ADDR_WIDTH-1:0] src_cur_q;
    logic [ADDR_WIDTH-1:0] dst_cur_q;
    logic [ADDR_WIDTH-1:0] llp_cur_q;
    logic [21:0] remaining_q;
    logic [31:0] ctrl_cur_q;
    logic [DATA_WIDTH-1:0] read_data_q;
    logic [REQ_ACK_NUM-1:0] dma_ack_q;
    logic [DATA_WIDTH-1:0] hrdata_d;
    logic       RTL_TODO_1_io_list_done;
    logic       dmac_reset_pulse;
    logic       busy;
    logic       slave_access;
    logic       slave_write;
    logic       slave_read;
    logic       slave_bad;
    logic       master_fire;
    logic       master_error;
    logic       do_core_reset;
    logic       chain_taken;
    logic       chain_pending;
    logic [ADDR_WIDTH-1:0] next_src;
    logic [ADDR_WIDTH-1:0] next_dst;
    logic [21:0] next_remaining;
    logic [21:0] bytes_done;
    logic [REQ_ACK_NUM-1:0] ack_onehot;
    logic [ADDR_WIDTH-1:0] hwdata_addr;
    logic [ADDR_WIDTH-1:0] hwdata_aligned_addr;
    logic       addr_hi_nonzero;
    logic       ctrl_reserved_bad;
    logic [3:0] active_req_sel;
    logic [3:0] active_dst_req_sel;
    logic [1:0] active_src_width;
    logic [1:0] active_dst_width;
    logic [2:0] active_burst_len;
    logic [1:0] active_src_addr_ctrl;
    logic [1:0] active_dst_addr_ctrl;
    logic [2:0] active_int_mask;
    logic       active_enable;
    logic [2:0] read_hsize;
    logic [2:0] write_hsize;
    logic [2:0] active_hburst;
    logic [2:0] SrcBurstSize;
    logic [1:0] SrcWidth;
    logic [1:0] DstWidth;
    logic       SrcMode;
    logic       DstMode;
    logic [1:0] SrcAddrCtrl;
    logic [1:0] DstAddrCtrl;
    logic [3:0] SrcReqSel;
    logic [3:0] DstReqSel;
    logic       IntAbtMask;
    logic       IntErrMask;
    logic       IntTCMask;
    logic [ADDR_WIDTH-1:0] SrcAddr;
    logic [ADDR_WIDTH-1:0] DstAddr;
    logic [21:0] TranSize;
    logic [ADDR_WIDTH-1:0] LLPointer;
    logic [7:0] status_enabled;
    logic [DATA_WIDTH-1:0] ch0_llp_read;
    logic [DATA_WIDTH-1:0] ch1_llp_read;
    logic [DATA_WIDTH-1:0] ch2_llp_read;
    logic [DATA_WIDTH-1:0] ch3_llp_read;
    logic [DATA_WIDTH-1:0] ch4_llp_read;
    logic [DATA_WIDTH-1:0] ch5_llp_read;
    logic [DATA_WIDTH-1:0] ch6_llp_read;
    logic [DATA_WIDTH-1:0] ch7_llp_read;

    assign RTL_TODO_1_io_list_done = hsel & hreadyin;
    assign slave_access = RTL_TODO_1_io_list_done & htrans[1];
    assign slave_write = slave_access & hwrite;
    assign slave_read = slave_access & ~hwrite;
    assign addr_hi_nonzero = |haddr[ADDR_WIDTH-1:8];
    assign slave_bad = slave_access & ((haddr[1:0] != 2'b00) | (hsize > HSIZE_WORD) | (hburst != HBURST_SINGLE) | (htrans == 2'b01) | addr_hi_nonzero);
    assign hready = 1'b1;
    assign hresp = slave_bad ? RESP_ERROR : RESP_OKAY;
    assign cfg_ch_mask =
        (DMA_CH_NUM >= 8) ? 8'hff :
        (DMA_CH_NUM == 7) ? 8'h7f :
        (DMA_CH_NUM == 6) ? 8'h3f :
        (DMA_CH_NUM == 5) ? 8'h1f :
        (DMA_CH_NUM == 4) ? 8'h0f :
        (DMA_CH_NUM == 3) ? 8'h07 :
        (DMA_CH_NUM == 2) ? 8'h03 : 8'h01;
    assign enabled_mask = {
        ch7_ctrl_q[0], ch6_ctrl_q[0], ch5_ctrl_q[0], ch4_ctrl_q[0],
        ch3_ctrl_q[0], ch2_ctrl_q[0], ch1_ctrl_q[0], ch0_ctrl_q[0]
    } & cfg_ch_mask;
    assign priority_mask = {
        ch7_ctrl_q[29], ch6_ctrl_q[29], ch5_ctrl_q[29], ch4_ctrl_q[29],
        ch3_ctrl_q[29], ch2_ctrl_q[29], ch1_ctrl_q[29], ch0_ctrl_q[29]
    } & enabled_mask;
    assign eligible_mask = (priority_mask != 8'h00) ? priority_mask : enabled_mask;
    assign busy = (state_q != IDLE);
    assign fsm_state_cover = {
        state_q == CHAIN_LOAD,
        state_q == ERROR_ABORT,
        state_q == COMPLETE,
        state_q == WRITE_DATA,
        state_q == WRITE_ADDR,
        state_q == READ_ADDR,
        state_q == ARBITRATE,
        state_q == IDLE
    };
    assign status_enabled = int_tc_q | int_abort_q | int_error_q;
    assign dma_int = |status_enabled;
    assign dma_ack = dma_ack_q;
    assign master_fire = hgrant_mst & hready_mst;
    assign master_error = master_fire & (hresp_mst != RESP_OKAY);
    assign hwdata_addr = hwdata[ADDR_WIDTH-1:0];
    assign hwdata_aligned_addr = {hwdata[ADDR_WIDTH-1:2], 2'b00};
    assign ctrl_reserved_bad = |{ctrl_cur_q[31:30], ctrl_cur_q[28:25]};
    assign active_src_width = ctrl_cur_q[21:20];
    assign active_dst_width = ctrl_cur_q[19:18];
    assign active_src_addr_ctrl = ctrl_cur_q[15:14];
    assign active_dst_addr_ctrl = ctrl_cur_q[13:12];
    assign active_burst_len = ctrl_cur_q[24:22];
    assign active_int_mask = ctrl_cur_q[3:1];
    assign active_enable = ctrl_cur_q[0];
    assign SrcBurstSize = active_burst_len;
    assign SrcWidth = active_src_width;
    assign DstWidth = active_dst_width;
    assign SrcMode = ctrl_cur_q[17];
    assign DstMode = ctrl_cur_q[16];
    assign SrcAddrCtrl = active_src_addr_ctrl;
    assign DstAddrCtrl = active_dst_addr_ctrl;
    assign SrcReqSel = ctrl_cur_q[11:8];
    assign DstReqSel = ctrl_cur_q[7:4];
    assign IntAbtMask = active_int_mask[2];
    assign IntErrMask = active_int_mask[1];
    assign IntTCMask = active_int_mask[0];
    assign SrcAddr = src_cur_q;
    assign DstAddr = dst_cur_q;
    assign TranSize = remaining_q;
    assign LLPointer = llp_cur_q;
    assign read_hsize = {1'b0, SrcWidth};
    assign write_hsize = {1'b0, DstWidth};
    assign active_hburst = (SrcBurstSize == 3'b000) ? HBURST_SINGLE : HBURST_INCR;
    assign next_src =
        (SrcAddrCtrl == 2'b01) ? (SrcAddr - {{(ADDR_WIDTH-3){1'b0}}, 3'b100}) :
        (SrcAddrCtrl == 2'b10) ? SrcAddr :
        (SrcAddr + {{(ADDR_WIDTH-3){1'b0}}, 3'b100});
    assign next_dst =
        (DstAddrCtrl == 2'b01) ? (DstAddr - {{(ADDR_WIDTH-3){1'b0}}, 3'b100}) :
        (DstAddrCtrl == 2'b10) ? DstAddr :
        (DstAddr + {{(ADDR_WIDTH-3){1'b0}}, 3'b100});
    assign next_remaining = remaining_q - 22'd1;
    assign active_req_sel = SrcReqSel;
    assign active_dst_req_sel = DstReqSel;
    assign ack_onehot = ({{(REQ_ACK_NUM-1){1'b0}}, 1'b1} << (SrcMode ? active_req_sel : active_dst_req_sel));
    assign chain_taken = (CHAIN_TRANSFER_SUPPORT != 0) & (LLPointer != {ADDR_WIDTH{1'b0}});
    assign do_core_reset = (slave_write & ~slave_bad & (haddr[7:0] == DMACtrl) & hwdata[0]);
    assign ch0_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch0_llp_q};
    assign ch1_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch1_llp_q};
    assign ch2_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch2_llp_q};
    assign ch3_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch3_llp_q};
    assign ch4_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch4_llp_q};
    assign ch5_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch5_llp_q};
    assign ch6_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch6_llp_q};
    assign ch7_llp_read = {{(DATA_WIDTH-ADDR_WIDTH){1'b0}}, ch7_llp_q};

    always @(*) begin
        arb_valid_d = |eligible_mask;
        arb_ch_d = 3'd0;
        case (last_rr_q)
            3'd0: begin
                if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else arb_ch_d = 3'd0;
            end
            3'd1: begin
                if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else arb_ch_d = 3'd1;
            end
            3'd2: begin
                if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else arb_ch_d = 3'd2;
            end
            3'd3: begin
                if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else arb_ch_d = 3'd3;
            end
            3'd4: begin
                if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else arb_ch_d = 3'd4;
            end
            3'd5: begin
                if (eligible_mask[6]) arb_ch_d = 3'd6;
                else if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else arb_ch_d = 3'd5;
            end
            3'd6: begin
                if (eligible_mask[7]) arb_ch_d = 3'd7;
                else if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else arb_ch_d = 3'd6;
            end
            default: begin
                if (eligible_mask[0]) arb_ch_d = 3'd0;
                else if (eligible_mask[1]) arb_ch_d = 3'd1;
                else if (eligible_mask[2]) arb_ch_d = 3'd2;
                else if (eligible_mask[3]) arb_ch_d = 3'd3;
                else if (eligible_mask[4]) arb_ch_d = 3'd4;
                else if (eligible_mask[5]) arb_ch_d = 3'd5;
                else if (eligible_mask[6]) arb_ch_d = 3'd6;
                else arb_ch_d = 3'd7;
            end
        endcase
    end

    always @(*) begin
        hrdata_d = {DATA_WIDTH{1'b0}};
        if (slave_read & ~slave_bad) begin
            case (haddr[7:0])
                8'h00: hrdata_d = IdRev;
                8'h10: hrdata_d = DMACfg;
                IntStatus: hrdata_d = {{(DATA_WIDTH-24){1'b0}}, int_tc_q, int_abort_q, int_error_q};
                ChEN: hrdata_d = {{(DATA_WIDTH-8){1'b0}}, enabled_mask};
                ChnCtrl: hrdata_d = ch0_ctrl_q;
                ChnSrcAddr: hrdata_d = ch0_src_q;
                ChnDstAddr: hrdata_d = ch0_dst_q;
                ChnTranSize: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch0_size_q};
                ChnLLPointer: hrdata_d = ch0_llp_read;
                8'h58: hrdata_d = ch1_ctrl_q;
                8'h5c: hrdata_d = ch1_src_q;
                8'h60: hrdata_d = ch1_dst_q;
                8'h64: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch1_size_q};
                8'h68: hrdata_d = ch1_llp_read;
                8'h6c: hrdata_d = ch2_ctrl_q;
                8'h70: hrdata_d = ch2_src_q;
                8'h74: hrdata_d = ch2_dst_q;
                8'h78: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch2_size_q};
                8'h7c: hrdata_d = ch2_llp_read;
                8'h80: hrdata_d = ch3_ctrl_q;
                8'h84: hrdata_d = ch3_src_q;
                8'h88: hrdata_d = ch3_dst_q;
                8'h8c: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch3_size_q};
                8'h90: hrdata_d = ch3_llp_read;
                8'h94: hrdata_d = ch4_ctrl_q;
                8'h98: hrdata_d = ch4_src_q;
                8'h9c: hrdata_d = ch4_dst_q;
                8'ha0: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch4_size_q};
                8'ha4: hrdata_d = ch4_llp_read;
                8'ha8: hrdata_d = ch5_ctrl_q;
                8'hac: hrdata_d = ch5_src_q;
                8'hb0: hrdata_d = ch5_dst_q;
                8'hb4: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch5_size_q};
                8'hb8: hrdata_d = ch5_llp_read;
                8'hbc: hrdata_d = ch6_ctrl_q;
                8'hc0: hrdata_d = ch6_src_q;
                8'hc4: hrdata_d = ch6_dst_q;
                8'hc8: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch6_size_q};
                8'hcc: hrdata_d = ch6_llp_read;
                8'hd0: hrdata_d = ch7_ctrl_q;
                8'hd4: hrdata_d = ch7_src_q;
                8'hd8: hrdata_d = ch7_dst_q;
                8'hdc: hrdata_d = {{(DATA_WIDTH-22){1'b0}}, ch7_size_q};
                8'he0: hrdata_d = ch7_llp_read;
                default: hrdata_d = {DATA_WIDTH{1'b0}};
            endcase
        end
    end

    always @(posedge hclk) begin
        if (!hresetn) begin
            ch0_ctrl_q <= 32'h000a0000;
            ch1_ctrl_q <= 32'h000a0000;
            ch2_ctrl_q <= 32'h000a0000;
            ch3_ctrl_q <= 32'h000a0000;
            ch4_ctrl_q <= 32'h000a0000;
            ch5_ctrl_q <= 32'h000a0000;
            ch6_ctrl_q <= 32'h000a0000;
            ch7_ctrl_q <= 32'h000a0000;
            ch0_src_q <= {ADDR_WIDTH{1'b0}};
            ch1_src_q <= {ADDR_WIDTH{1'b0}};
            ch2_src_q <= {ADDR_WIDTH{1'b0}};
            ch3_src_q <= {ADDR_WIDTH{1'b0}};
            ch4_src_q <= {ADDR_WIDTH{1'b0}};
            ch5_src_q <= {ADDR_WIDTH{1'b0}};
            ch6_src_q <= {ADDR_WIDTH{1'b0}};
            ch7_src_q <= {ADDR_WIDTH{1'b0}};
            ch0_dst_q <= {ADDR_WIDTH{1'b0}};
            ch1_dst_q <= {ADDR_WIDTH{1'b0}};
            ch2_dst_q <= {ADDR_WIDTH{1'b0}};
            ch3_dst_q <= {ADDR_WIDTH{1'b0}};
            ch4_dst_q <= {ADDR_WIDTH{1'b0}};
            ch5_dst_q <= {ADDR_WIDTH{1'b0}};
            ch6_dst_q <= {ADDR_WIDTH{1'b0}};
            ch7_dst_q <= {ADDR_WIDTH{1'b0}};
            ch0_size_q <= 22'd0;
            ch1_size_q <= 22'd0;
            ch2_size_q <= 22'd0;
            ch3_size_q <= 22'd0;
            ch4_size_q <= 22'd0;
            ch5_size_q <= 22'd0;
            ch6_size_q <= 22'd0;
            ch7_size_q <= 22'd0;
            ch0_llp_q <= {ADDR_WIDTH{1'b0}};
            ch1_llp_q <= {ADDR_WIDTH{1'b0}};
            ch2_llp_q <= {ADDR_WIDTH{1'b0}};
            ch3_llp_q <= {ADDR_WIDTH{1'b0}};
            ch4_llp_q <= {ADDR_WIDTH{1'b0}};
            ch5_llp_q <= {ADDR_WIDTH{1'b0}};
            ch6_llp_q <= {ADDR_WIDTH{1'b0}};
            ch7_llp_q <= {ADDR_WIDTH{1'b0}};
            int_tc_q <= 8'h00;
            int_abort_q <= 8'h00;
            int_error_q <= 8'h00;
            last_rr_q <= 3'd7;
            active_ch_q <= 3'd0;
            state_q <= IDLE;
            src_cur_q <= {ADDR_WIDTH{1'b0}};
            dst_cur_q <= {ADDR_WIDTH{1'b0}};
            llp_cur_q <= {ADDR_WIDTH{1'b0}};
            remaining_q <= 22'd0;
            ctrl_cur_q <= 32'h00000000;
            dmac_reset_pulse <= 1'b0;
            bytes_done <= 22'd0;
            chain_pending <= 1'b0;
            read_data_q <= {DATA_WIDTH{1'b0}};
            dma_ack_q <= {REQ_ACK_NUM{1'b0}};
            hrdata <= {DATA_WIDTH{1'b0}};
            haddr_mst <= {ADDR_WIDTH{1'b0}};
            htrans_mst <= HTRANS_IDLE;
            hwrite_mst <= 1'b0;
            hsize_mst <= HSIZE_WORD;
            hprot_mst <= 4'b0011;
            hlock_mst <= 1'b0;
            hburst_mst <= HBURST_SINGLE;
            hwdata_mst <= {DATA_WIDTH{1'b0}};
            hbusreq_mst <= 1'b0;
        end else begin
            hrdata <= hrdata_d;
            dma_ack_q <= {REQ_ACK_NUM{1'b0}};
            htrans_mst <= HTRANS_IDLE;
            hwrite_mst <= 1'b0;
            hsize_mst <= HSIZE_WORD;
            hprot_mst <= {IntAbtMask, IntErrMask, IntTCMask, active_enable | (|fsm_state_cover) | dmac_reset_pulse};
            hlock_mst <= (chain_pending | chain_taken) & busy & ctrl_cur_q[29];
            hburst_mst <= HBURST_SINGLE;
            hbusreq_mst <= busy;
            dmac_reset_pulse <= do_core_reset;

            if (do_core_reset) begin
                ch0_ctrl_q <= 32'h000a0000;
                ch1_ctrl_q <= 32'h000a0000;
                ch2_ctrl_q <= 32'h000a0000;
                ch3_ctrl_q <= 32'h000a0000;
                ch4_ctrl_q <= 32'h000a0000;
                ch5_ctrl_q <= 32'h000a0000;
                ch6_ctrl_q <= 32'h000a0000;
                ch7_ctrl_q <= 32'h000a0000;
                int_tc_q <= 8'h00;
                int_abort_q <= 8'h00;
                int_error_q <= 8'h00;
                state_q <= IDLE;
                bytes_done <= 22'd0;
                chain_pending <= 1'b0;
                hbusreq_mst <= 1'b0;
            end else begin
                if (slave_write & ~slave_bad) begin
                    case (haddr[7:0])
                        IntStatus: begin
                            int_tc_q <= int_tc_q & ~hwdata[23:16];
                            int_abort_q <= int_abort_q & ~hwdata[15:8];
                            int_error_q <= int_error_q & ~hwdata[7:0];
                        end
                        ChAbort: begin
                            int_abort_q <= int_abort_q | (hwdata[7:0] & enabled_mask);
                            ch0_ctrl_q[0] <= ch0_ctrl_q[0] & ~hwdata[0];
                            ch1_ctrl_q[0] <= ch1_ctrl_q[0] & ~hwdata[1];
                            ch2_ctrl_q[0] <= ch2_ctrl_q[0] & ~hwdata[2];
                            ch3_ctrl_q[0] <= ch3_ctrl_q[0] & ~hwdata[3];
                            ch4_ctrl_q[0] <= ch4_ctrl_q[0] & ~hwdata[4];
                            ch5_ctrl_q[0] <= ch5_ctrl_q[0] & ~hwdata[5];
                            ch6_ctrl_q[0] <= ch6_ctrl_q[0] & ~hwdata[6];
                            ch7_ctrl_q[0] <= ch7_ctrl_q[0] & ~hwdata[7];
                        end
                        ChnCtrl: ch0_ctrl_q <= hwdata;
                        ChnSrcAddr: ch0_src_q <= hwdata_addr;
                        ChnDstAddr: ch0_dst_q <= hwdata_addr;
                        ChnTranSize: ch0_size_q <= hwdata[21:0];
                        ChnLLPointer: ch0_llp_q <= hwdata_aligned_addr;
                        8'h58: ch1_ctrl_q <= hwdata;
                        8'h5c: ch1_src_q <= hwdata_addr;
                        8'h60: ch1_dst_q <= hwdata_addr;
                        8'h64: ch1_size_q <= hwdata[21:0];
                        8'h68: ch1_llp_q <= hwdata_aligned_addr;
                        8'h6c: ch2_ctrl_q <= hwdata;
                        8'h70: ch2_src_q <= hwdata_addr;
                        8'h74: ch2_dst_q <= hwdata_addr;
                        8'h78: ch2_size_q <= hwdata[21:0];
                        8'h7c: ch2_llp_q <= hwdata_aligned_addr;
                        8'h80: ch3_ctrl_q <= hwdata;
                        8'h84: ch3_src_q <= hwdata_addr;
                        8'h88: ch3_dst_q <= hwdata_addr;
                        8'h8c: ch3_size_q <= hwdata[21:0];
                        8'h90: ch3_llp_q <= hwdata_aligned_addr;
                        8'h94: ch4_ctrl_q <= hwdata;
                        8'h98: ch4_src_q <= hwdata_addr;
                        8'h9c: ch4_dst_q <= hwdata_addr;
                        8'ha0: ch4_size_q <= hwdata[21:0];
                        8'ha4: ch4_llp_q <= hwdata_aligned_addr;
                        8'ha8: ch5_ctrl_q <= hwdata;
                        8'hac: ch5_src_q <= hwdata_addr;
                        8'hb0: ch5_dst_q <= hwdata_addr;
                        8'hb4: ch5_size_q <= hwdata[21:0];
                        8'hb8: ch5_llp_q <= hwdata_aligned_addr;
                        8'hbc: ch6_ctrl_q <= hwdata;
                        8'hc0: ch6_src_q <= hwdata_addr;
                        8'hc4: ch6_dst_q <= hwdata_addr;
                        8'hc8: ch6_size_q <= hwdata[21:0];
                        8'hcc: ch6_llp_q <= hwdata_aligned_addr;
                        8'hd0: ch7_ctrl_q <= hwdata;
                        8'hd4: ch7_src_q <= hwdata_addr;
                        8'hd8: ch7_dst_q <= hwdata_addr;
                        8'hdc: ch7_size_q <= hwdata[21:0];
                        8'he0: ch7_llp_q <= hwdata_aligned_addr;
                        default: begin
                            int_error_q <= int_error_q;
                        end
                    endcase
                end

                case (state_q)
                    IDLE: begin
                        hbusreq_mst <= 1'b0;
                        if (arb_valid_d) begin
                            active_ch_q <= arb_ch_d;
                            last_rr_q <= arb_ch_d;
                            state_q <= READ_ADDR;
                            bytes_done <= 22'd0;
                            chain_pending <= 1'b0;
                            hbusreq_mst <= 1'b1;
                            case (arb_ch_d)
                                3'd0: begin
                                    ctrl_cur_q <= ch0_ctrl_q;
                                    src_cur_q <= ch0_src_q;
                                    dst_cur_q <= ch0_dst_q;
                                    remaining_q <= ch0_size_q;
                                    llp_cur_q <= ch0_llp_q;
                                end
                                3'd1: begin
                                    ctrl_cur_q <= ch1_ctrl_q;
                                    src_cur_q <= ch1_src_q;
                                    dst_cur_q <= ch1_dst_q;
                                    remaining_q <= ch1_size_q;
                                    llp_cur_q <= ch1_llp_q;
                                end
                                3'd2: begin
                                    ctrl_cur_q <= ch2_ctrl_q;
                                    src_cur_q <= ch2_src_q;
                                    dst_cur_q <= ch2_dst_q;
                                    remaining_q <= ch2_size_q;
                                    llp_cur_q <= ch2_llp_q;
                                end
                                3'd3: begin
                                    ctrl_cur_q <= ch3_ctrl_q;
                                    src_cur_q <= ch3_src_q;
                                    dst_cur_q <= ch3_dst_q;
                                    remaining_q <= ch3_size_q;
                                    llp_cur_q <= ch3_llp_q;
                                end
                                3'd4: begin
                                    ctrl_cur_q <= ch4_ctrl_q;
                                    src_cur_q <= ch4_src_q;
                                    dst_cur_q <= ch4_dst_q;
                                    remaining_q <= ch4_size_q;
                                    llp_cur_q <= ch4_llp_q;
                                end
                                3'd5: begin
                                    ctrl_cur_q <= ch5_ctrl_q;
                                    src_cur_q <= ch5_src_q;
                                    dst_cur_q <= ch5_dst_q;
                                    remaining_q <= ch5_size_q;
                                    llp_cur_q <= ch5_llp_q;
                                end
                                3'd6: begin
                                    ctrl_cur_q <= ch6_ctrl_q;
                                    src_cur_q <= ch6_src_q;
                                    dst_cur_q <= ch6_dst_q;
                                    remaining_q <= ch6_size_q;
                                    llp_cur_q <= ch6_llp_q;
                                end
                                default: begin
                                    ctrl_cur_q <= ch7_ctrl_q;
                                    src_cur_q <= ch7_src_q;
                                    dst_cur_q <= ch7_dst_q;
                                    remaining_q <= ch7_size_q;
                                    llp_cur_q <= ch7_llp_q;
                                end
                            endcase
                        end
                    end
                    READ_ADDR: begin
                        hbusreq_mst <= 1'b1;
                        htrans_mst <= HTRANS_NONSEQ;
                        hwrite_mst <= 1'b0;
                        haddr_mst <= SrcAddr;
                        hsize_mst <= read_hsize;
                        hburst_mst <= active_hburst;
                        if (master_error | ctrl_reserved_bad) begin
                            int_error_q[active_ch_q] <= 1'b1;
                            state_q <= ERROR_ABORT;
                        end else if (master_fire) begin
                            read_data_q <= hrdata_mst;
                            if ((SrcMode | DstMode) & (|dma_req)) begin
                                dma_ack_q <= ack_onehot;
                            end
                            state_q <= WRITE_ADDR;
                        end
                    end
                    WRITE_ADDR: begin
                        hbusreq_mst <= 1'b1;
                        htrans_mst <= HTRANS_SEQ;
                        hwrite_mst <= 1'b1;
                        haddr_mst <= DstAddr;
                        hsize_mst <= write_hsize;
                        hburst_mst <= active_hburst;
                        hwdata_mst <= read_data_q;
                        if (master_error) begin
                            int_error_q[active_ch_q] <= 1'b1;
                            state_q <= ERROR_ABORT;
                        end else if (master_fire) begin
                            src_cur_q <= next_src;
                            dst_cur_q <= next_dst;
                            remaining_q <= next_remaining;
                            bytes_done <= bytes_done + 22'd4;
                            if (TranSize <= 22'd1) begin
                                int_tc_q[active_ch_q] <= 1'b1;
                                if ((SrcMode | DstMode) & (|dma_req)) begin
                                    dma_ack_q <= ack_onehot;
                                end
                                chain_pending <= chain_taken;
                                state_q <= chain_taken ? CHAIN_LOAD : COMPLETE;
                                case (active_ch_q)
                                    3'd0: begin ch0_ctrl_q[0] <= 1'b0; ch0_src_q <= next_src; ch0_dst_q <= next_dst; ch0_size_q <= 22'd0; end
                                    3'd1: begin ch1_ctrl_q[0] <= 1'b0; ch1_src_q <= next_src; ch1_dst_q <= next_dst; ch1_size_q <= 22'd0; end
                                    3'd2: begin ch2_ctrl_q[0] <= 1'b0; ch2_src_q <= next_src; ch2_dst_q <= next_dst; ch2_size_q <= 22'd0; end
                                    3'd3: begin ch3_ctrl_q[0] <= 1'b0; ch3_src_q <= next_src; ch3_dst_q <= next_dst; ch3_size_q <= 22'd0; end
                                    3'd4: begin ch4_ctrl_q[0] <= 1'b0; ch4_src_q <= next_src; ch4_dst_q <= next_dst; ch4_size_q <= 22'd0; end
                                    3'd5: begin ch5_ctrl_q[0] <= 1'b0; ch5_src_q <= next_src; ch5_dst_q <= next_dst; ch5_size_q <= 22'd0; end
                                    3'd6: begin ch6_ctrl_q[0] <= 1'b0; ch6_src_q <= next_src; ch6_dst_q <= next_dst; ch6_size_q <= 22'd0; end
                                    default: begin ch7_ctrl_q[0] <= 1'b0; ch7_src_q <= next_src; ch7_dst_q <= next_dst; ch7_size_q <= 22'd0; end
                                endcase
                            end else begin
                                state_q <= READ_ADDR;
                            end
                        end
                    end
                    ERROR_ABORT: begin
                        hbusreq_mst <= 1'b0;
                        state_q <= IDLE;
                    end
                    COMPLETE: begin
                        hbusreq_mst <= 1'b0;
                        state_q <= IDLE;
                    end
                    CHAIN_LOAD: begin
                        hbusreq_mst <= 1'b0;
                        state_q <= IDLE;
                    end
                    default: begin
                        state_q <= IDLE;
                    end
                endcase
            end
        end
    end
endmodule
