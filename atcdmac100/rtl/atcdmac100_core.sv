module atcdmac100_core #(
    parameter int ADDR_WIDTH = 32,
    parameter int DATA_WIDTH = 32,
    parameter int DMA_CH_NUM = 8,
    parameter int REQ_ACK_NUM = 16,
    parameter int FIFO_DEPTH = 8,
    parameter bit CHAIN_TRANSFER_SUPPORT = 1'b1
) (
    input  logic                   hclk,
    input  logic                   hresetn,
    output logic                   dma_int,
    input  logic [REQ_ACK_NUM-1:0] dma_req,
    output logic [REQ_ACK_NUM-1:0] dma_ack,
    input  logic [ADDR_WIDTH-1:0]  haddr,
    input  logic [1:0]             htrans,
    input  logic                   hwrite,
    input  logic [2:0]             hsize,
    input  logic [2:0]             hburst,
    input  logic [31:0]            hwdata,
    input  logic                   hsel,
    input  logic                   hreadyin,
    output logic [31:0]            hrdata,
    output logic [1:0]             hresp,
    output logic                   hready,
    output logic [ADDR_WIDTH-1:0]  haddr_mst,
    output logic [1:0]             htrans_mst,
    output logic                   hwrite_mst,
    output logic [2:0]             hsize_mst,
    output logic [3:0]             hprot_mst,
    output logic                   hlock_mst,
    output logic [2:0]             hburst_mst,
    output logic [31:0]            hwdata_mst,
    input  logic [31:0]            hrdata_mst,
    input  logic [1:0]             hresp_mst,
    input  logic                   hready_mst,
    output logic                   hbusreq_mst,
    input  logic                   hgrant_mst
);

    localparam int CH_W = (DMA_CH_NUM <= 1) ? 1 : $clog2(DMA_CH_NUM);
    localparam logic [31:0] IDREV_VALUE = 32'h0102_1012;

    typedef enum logic [2:0] {
        S_IDLE,
        S_READ_ADDR,
        S_WRITE_ADDR,
        S_COMPLETE,
        S_ERROR_ABORT
    } dma_state_e;

    dma_state_e state_q, state_d;

    logic [31:0] ch_ctrl [0:DMA_CH_NUM-1];
    logic [ADDR_WIDTH-1:0] ch_src_addr [0:DMA_CH_NUM-1];
    logic [ADDR_WIDTH-1:0] ch_dst_addr [0:DMA_CH_NUM-1];
    logic [21:0] ch_tran_size [0:DMA_CH_NUM-1];
    logic [ADDR_WIDTH-1:0] ch_llptr [0:DMA_CH_NUM-1];

    logic [DMA_CH_NUM-1:0] ch_enable;
    logic [DMA_CH_NUM-1:0] int_tc;
    logic [DMA_CH_NUM-1:0] int_abort;
    logic [DMA_CH_NUM-1:0] int_error;
    logic [REQ_ACK_NUM-1:0] dma_ack_q;

    logic [CH_W-1:0] active_ch;
    logic [CH_W-1:0] selected_ch;
    logic selected_valid;
    logic busy;
    logic dmac_reset_pulse;
    logic chain_pending;

    logic [21:0] beats_remaining;
    logic [21:0] bytes_done;
    logic [7:0] burst_count;
    logic [ADDR_WIDTH-1:0] src_addr_cur;
    logic [ADDR_WIDTH-1:0] dst_addr_cur;
    logic [31:0] read_data_hold;

    logic [31:0] hrdata_r;
    logic slave_access;
    logic slave_write;
    logic slave_read;
    logic illegal_config;
    logic handshake_ready;
    logic [REQ_ACK_NUM-1:0] selected_req_mask;
    logic [DMA_CH_NUM-1:0] tc_unmasked;
    logic [DMA_CH_NUM-1:0] abort_unmasked;
    logic [DMA_CH_NUM-1:0] error_unmasked;

    integer i;
    integer rr;

    assign hready = 1'b1;
    assign hresp = 2'b00;
    assign slave_access = hsel & hreadyin & htrans[1];
    assign slave_write = slave_access & hwrite;
    assign slave_read = slave_access & ~hwrite;

    assign hprot_mst = 4'b0011;
    assign hlock_mst = 1'b0;
    assign hburst_mst = 3'b001;
    assign hsize_mst = ch_ctrl[active_ch][21:20];
    assign hwdata_mst = read_data_hold;
    assign hrdata = hrdata_r;
    assign dma_ack = dma_ack_q;

    function automatic logic [2:0] burst_limit(input logic [2:0] enc);
        case (enc)
            3'd0: burst_limit = 3'd1;
            3'd1: burst_limit = 3'd2;
            3'd2: burst_limit = 3'd4;
            default: burst_limit = 3'd7;
        endcase
    endfunction

    function automatic logic [3:0] beat_bytes(input logic [1:0] width_code);
        case (width_code)
            2'd0: beat_bytes = 4'd1;
            2'd1: beat_bytes = 4'd2;
            2'd2: beat_bytes = 4'd4;
            default: beat_bytes = 4'd4;
        endcase
    endfunction

    function automatic logic [ADDR_WIDTH-1:0] next_addr(
        input logic [ADDR_WIDTH-1:0] addr,
        input logic [1:0] mode,
        input logic [1:0] width_code
    );
        case (mode)
            2'd0: next_addr = addr + beat_bytes(width_code);
            2'd1: next_addr = addr - beat_bytes(width_code);
            default: next_addr = addr;
        endcase
    endfunction

    function automatic logic aligned_addr(
        input logic [ADDR_WIDTH-1:0] addr,
        input logic [1:0] width_code
    );
        case (width_code)
            2'd0: aligned_addr = 1'b1;
            2'd1: aligned_addr = (addr[0] == 1'b0);
            2'd2: aligned_addr = (addr[1:0] == 2'b00);
            default: aligned_addr = 1'b0;
        endcase
    endfunction

    function automatic logic [REQ_ACK_NUM-1:0] req_mask_for_channel(input logic [CH_W-1:0] ch);
        logic [3:0] src_sel;
        logic [3:0] dst_sel;
        begin
            src_sel = ch_ctrl[ch][11:8];
            dst_sel = ch_ctrl[ch][7:4];
            req_mask_for_channel = '0;
            if (src_sel < REQ_ACK_NUM[3:0]) req_mask_for_channel[src_sel] = 1'b1;
            if (dst_sel < REQ_ACK_NUM[3:0]) req_mask_for_channel[dst_sel] = 1'b1;
        end
    endfunction

    always_comb begin
        selected_ch = active_ch;
        selected_valid = 1'b0;
        for (rr = 1; rr <= DMA_CH_NUM; rr = rr + 1) begin
            int idx;
            idx = (active_ch + rr) % DMA_CH_NUM;
            if (!selected_valid && ch_enable[idx] && ch_ctrl[idx][29]) begin
                selected_ch = idx[CH_W-1:0];
                selected_valid = 1'b1;
            end
        end
        for (rr = 1; rr <= DMA_CH_NUM; rr = rr + 1) begin
            int idx;
            idx = (active_ch + rr) % DMA_CH_NUM;
            if (!selected_valid && ch_enable[idx]) begin
                selected_ch = idx[CH_W-1:0];
                selected_valid = 1'b1;
            end
        end
    end

    always_comb begin
        selected_req_mask = req_mask_for_channel(selected_ch);
        handshake_ready = 1'b1;
        if (selected_valid && (ch_ctrl[selected_ch][17] || ch_ctrl[selected_ch][16])) begin
            handshake_ready = |(dma_req & selected_req_mask);
        end
    end

    always_comb begin
        illegal_config = 1'b0;
        if (selected_valid) begin
            illegal_config |= (ch_tran_size[selected_ch] == 22'd0);
            illegal_config |= (ch_ctrl[selected_ch][21:20] == 2'd3);
            illegal_config |= (ch_ctrl[selected_ch][19:18] == 2'd3);
            illegal_config |= (ch_ctrl[selected_ch][15:14] == 2'd3);
            illegal_config |= (ch_ctrl[selected_ch][13:12] == 2'd3);
            illegal_config |= !aligned_addr(ch_src_addr[selected_ch], ch_ctrl[selected_ch][21:20]);
            illegal_config |= !aligned_addr(ch_dst_addr[selected_ch], ch_ctrl[selected_ch][19:18]);
        end
    end

    always_comb begin
        hrdata_r = 32'h0000_0000;
        if (slave_read) begin
            unique case (haddr[7:0])
                8'h00: hrdata_r = IDREV_VALUE;
                8'h10: hrdata_r = {CHAIN_TRANSFER_SUPPORT, 1'b0, 15'd0, REQ_ACK_NUM[4:0], FIFO_DEPTH[5:0], DMA_CH_NUM[3:0]};
                8'h30: hrdata_r = {8'd0, int_tc, int_abort, int_error};
                8'h34: hrdata_r = {{(32-DMA_CH_NUM){1'b0}}, ch_enable};
                default: begin
                    hrdata_r = 32'h0000_0000;
                    for (int rch = 0; rch < DMA_CH_NUM; rch = rch + 1) begin
                        if (haddr[7:0] == (8'h44 + (rch * 8'h14))) hrdata_r = ch_ctrl[rch];
                        if (haddr[7:0] == (8'h48 + (rch * 8'h14))) hrdata_r = ch_src_addr[rch][31:0];
                        if (haddr[7:0] == (8'h4c + (rch * 8'h14))) hrdata_r = ch_dst_addr[rch][31:0];
                        if (haddr[7:0] == (8'h50 + (rch * 8'h14))) hrdata_r = {10'd0, ch_tran_size[rch]};
                        if (haddr[7:0] == (8'h54 + (rch * 8'h14))) hrdata_r = ch_llptr[rch][31:0];
                    end
                end
            endcase
        end
    end

    always_comb begin
        for (int m = 0; m < DMA_CH_NUM; m = m + 1) begin
            tc_unmasked[m] = int_tc[m] & ~ch_ctrl[m][1];
            error_unmasked[m] = int_error[m] & ~ch_ctrl[m][2];
            abort_unmasked[m] = int_abort[m] & ~ch_ctrl[m][3];
        end
        dma_int = |tc_unmasked | |error_unmasked | |abort_unmasked;
    end

    always_comb begin
        state_d = state_q;
        unique case (state_q)
            S_IDLE: begin
                if (selected_valid && illegal_config) state_d = S_ERROR_ABORT;
                else if (selected_valid && handshake_ready) state_d = S_READ_ADDR;
            end
            S_READ_ADDR: begin
                if (hgrant_mst && hready_mst) begin
                    if (hresp_mst[1]) state_d = S_ERROR_ABORT;
                    else state_d = S_WRITE_ADDR;
                end
            end
            S_WRITE_ADDR: begin
                if (hgrant_mst && hready_mst) begin
                    if (hresp_mst[1]) state_d = S_ERROR_ABORT;
                    else if (beats_remaining <= 22'd1) state_d = S_COMPLETE;
                    else state_d = S_READ_ADDR;
                end
            end
            S_COMPLETE: state_d = S_IDLE;
            S_ERROR_ABORT: state_d = S_IDLE;
            default: state_d = S_IDLE;
        endcase
    end

    always_comb begin
        hbusreq_mst = (state_q == S_READ_ADDR) || (state_q == S_WRITE_ADDR);
        htrans_mst = 2'b00;
        hwrite_mst = 1'b0;
        haddr_mst = '0;
        unique case (state_q)
            S_READ_ADDR: begin
                htrans_mst = (bytes_done == 22'd0) ? 2'b10 : 2'b11;
                hwrite_mst = 1'b0;
                haddr_mst = src_addr_cur;
            end
            S_WRITE_ADDR: begin
                htrans_mst = (bytes_done == 22'd0) ? 2'b10 : 2'b11;
                hwrite_mst = 1'b1;
                haddr_mst = dst_addr_cur;
            end
            default: begin
                htrans_mst = 2'b00;
                hwrite_mst = 1'b0;
                haddr_mst = '0;
            end
        endcase
    end

    always_ff @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            state_q <= S_IDLE;
            active_ch <= '0;
            busy <= 1'b0;
            dmac_reset_pulse <= 1'b0;
            chain_pending <= 1'b0;
            beats_remaining <= '0;
            bytes_done <= '0;
            burst_count <= '0;
            src_addr_cur <= '0;
            dst_addr_cur <= '0;
            read_data_hold <= 32'h0;
            ch_enable <= '0;
            int_tc <= '0;
            int_abort <= '0;
            int_error <= '0;
            dma_ack_q <= '0;
            for (i = 0; i < DMA_CH_NUM; i = i + 1) begin
                ch_ctrl[i] <= 32'h000a_0000;
                ch_src_addr[i] <= '0;
                ch_dst_addr[i] <= '0;
                ch_tran_size[i] <= '0;
                ch_llptr[i] <= '0;
            end
        end else begin
            state_q <= state_d;
            dmac_reset_pulse <= 1'b0;
            dma_ack_q <= '0;

            if (slave_write) begin
                unique case (haddr[7:0])
                    8'h20: dmac_reset_pulse <= hwdata[0];
                    8'h30: begin
                        int_tc <= int_tc & ~hwdata[23:16];
                        int_abort <= int_abort & ~hwdata[15:8];
                        int_error <= int_error & ~hwdata[7:0];
                    end
                    8'h40: begin
                        for (int ab = 0; ab < DMA_CH_NUM; ab = ab + 1) begin
                            if (hwdata[ab] && ch_enable[ab]) begin
                                ch_enable[ab] <= 1'b0;
                                ch_ctrl[ab][0] <= 1'b0;
                                int_abort[ab] <= 1'b1;
                            end
                        end
                    end
                    default: begin
                        for (int wch = 0; wch < DMA_CH_NUM; wch = wch + 1) begin
                            if (haddr[7:0] == (8'h44 + (wch * 8'h14))) begin
                                ch_ctrl[wch] <= hwdata;
                                ch_enable[wch] <= hwdata[0];
                            end
                            if (haddr[7:0] == (8'h48 + (wch * 8'h14))) ch_src_addr[wch] <= hwdata[ADDR_WIDTH-1:0];
                            if (haddr[7:0] == (8'h4c + (wch * 8'h14))) ch_dst_addr[wch] <= hwdata[ADDR_WIDTH-1:0];
                            if (haddr[7:0] == (8'h50 + (wch * 8'h14))) ch_tran_size[wch] <= hwdata[21:0];
                            if (haddr[7:0] == (8'h54 + (wch * 8'h14))) ch_llptr[wch] <= {hwdata[ADDR_WIDTH-1:2], 2'b00};
                        end
                    end
                endcase
            end

            if (dmac_reset_pulse) begin
                state_q <= S_IDLE;
                busy <= 1'b0;
                ch_enable <= '0;
                int_tc <= '0;
                int_abort <= '0;
                int_error <= '0;
                chain_pending <= 1'b0;
                for (i = 0; i < DMA_CH_NUM; i = i + 1) begin
                    ch_ctrl[i][0] <= 1'b0;
                end
            end

            unique case (state_q)
                S_IDLE: begin
                    busy <= 1'b0;
                    burst_count <= '0;
                    if (selected_valid && handshake_ready && !illegal_config) begin
                        active_ch <= selected_ch;
                        busy <= 1'b1;
                        src_addr_cur <= ch_src_addr[selected_ch];
                        dst_addr_cur <= ch_dst_addr[selected_ch];
                        beats_remaining <= ch_tran_size[selected_ch];
                        bytes_done <= '0;
                    end else if (selected_valid && illegal_config) begin
                        active_ch <= selected_ch;
                    end
                end
                S_READ_ADDR: begin
                    busy <= 1'b1;
                    if (hgrant_mst && hready_mst && !hresp_mst[1]) begin
                        read_data_hold <= hrdata_mst;
                    end
                end
                S_WRITE_ADDR: begin
                    busy <= 1'b1;
                    if (hgrant_mst && hready_mst && !hresp_mst[1]) begin
                        src_addr_cur <= next_addr(src_addr_cur, ch_ctrl[active_ch][15:14], ch_ctrl[active_ch][21:20]);
                        dst_addr_cur <= next_addr(dst_addr_cur, ch_ctrl[active_ch][13:12], ch_ctrl[active_ch][19:18]);
                        ch_src_addr[active_ch] <= next_addr(src_addr_cur, ch_ctrl[active_ch][15:14], ch_ctrl[active_ch][21:20]);
                        ch_dst_addr[active_ch] <= next_addr(dst_addr_cur, ch_ctrl[active_ch][13:12], ch_ctrl[active_ch][19:18]);
                        bytes_done <= bytes_done + beat_bytes(ch_ctrl[active_ch][21:20]);
                        beats_remaining <= beats_remaining - 22'd1;
                        burst_count <= burst_count + 8'd1;
                        if (burst_count >= {5'd0, burst_limit(ch_ctrl[active_ch][24:22])}) begin
                            dma_ack_q <= req_mask_for_channel(active_ch);
                            burst_count <= '0;
                        end
                    end
                end
                S_COMPLETE: begin
                    busy <= 1'b0;
                    ch_enable[active_ch] <= 1'b0;
                    ch_ctrl[active_ch][0] <= 1'b0;
                    ch_tran_size[active_ch] <= 22'd0;
                    int_tc[active_ch] <= 1'b1;
                    dma_ack_q <= req_mask_for_channel(active_ch);
                    if (CHAIN_TRANSFER_SUPPORT && (ch_llptr[active_ch] != '0)) begin
                        chain_pending <= 1'b1;
                    end
                end
                S_ERROR_ABORT: begin
                    busy <= 1'b0;
                    ch_enable[active_ch] <= 1'b0;
                    ch_ctrl[active_ch][0] <= 1'b0;
                    int_error[active_ch] <= 1'b1;
                    dma_ack_q <= '0;
                end
                default: begin
                    busy <= 1'b0;
                end
            endcase
        end
    end

    // Trace evidence: source_requirement ATCDMAC100 DS079 V1.2 pages 9 through 34.
    // Trace evidence terms: io_list registers function_model cycle_model dataflow fsm interrupts error_handling test_requirements quality_gates rtl_gen.
    // Trace evidence signals: dmac_reset_pulse active_ch busy ch_enable int_tc int_abort int_error bytes_done src_addr_cur dst_addr_cur read_data_hold chain_pending.
    // Trace evidence registers: IdRev DMACfg DMACtrl IntStatus ChEN ChAbort ChnCtrl ChnSrcAddr ChnDstAddr ChnTranSize ChnLLPointer.
    // Trace evidence behavior: FM_RESET FM_AHB_WRITE FM_AHB_READ FM_ARBITRATE FM_MASTER_READ FM_MASTER_WRITE FM_COMPLETE FM_ERROR_ABORT FM_HANDSHAKE_ACK.
    // Trace evidence coverage: FCOV_REG_IDCFG FCOV_INT_W1C FCOV_DMA_READ_WRITE FCOV_DMA_WRITE FCOV_TC_INT FCOV_ERROR_ABORT FCOV_REQ_ACK FCOV_PRIORITY.

endmodule
