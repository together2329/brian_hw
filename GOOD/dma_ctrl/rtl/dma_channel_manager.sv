`default_nettype none
module dma_channel_manager #(
    parameter int DATA_WIDTH    = 32,
    parameter int ADDR_WIDTH    = 32,
    parameter int ID_WIDTH      = 4,
    parameter int NUM_CHANNELS  = 8,
    parameter int FIFO_DEPTH    = 16,
    parameter int MAX_BURST_LEN = 16
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // Global control
    input  logic                          dma_enable,
    input  logic                          endian_swap,
    input  logic [NUM_CHANNELS-1:0]       clk_gating,

    // Per-channel registers (from reg_block)
    input  logic [NUM_CHANNELS-1:0][31:0] ch_sar,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_dar,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_len,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_cr,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_sr_w1c_data,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_llp,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_bcr,
    input  logic [NUM_CHANNELS-1:0][31:0] ch_cfg,

    // Per-channel status outputs
    output logic [NUM_CHANNELS-1:0][2:0]  ch_state,
    output logic [NUM_CHANNELS-1:0]       ch_fifo_empty,
    output logic [NUM_CHANNELS-1:0]       ch_fifo_full,
    output logic [NUM_CHANNELS-1:0][2:0]  ch_fifo_count,
    output logic [NUM_CHANNELS-1:0]       channel_active,
    output logic [NUM_CHANNELS-1:0]       channel_idle,
    output logic [NUM_CHANNELS-1:0]       ch_bus_error,
    output logic [NUM_CHANNELS-1:0]       ch_align_error,
    output logic [NUM_CHANNELS-1:0]       ch_desc_error,
    output logic [NUM_CHANNELS-1:0]       ch_xfer_complete,
    output logic [NUM_CHANNELS-1:0][15:0] ch_bcr_bytes,

    // Peripheral interface
    input  logic [NUM_CHANNELS-1:0]       dma_req,
    output logic [NUM_CHANNELS-1:0]       dma_ack,
    input  logic [NUM_CHANNELS-1:0]       dma_eop,

    // Channel requests to arbiter
    output logic [NUM_CHANNELS-1:0]       ch_req,
    output logic [NUM_CHANNELS-1:0][1:0]  ch_priority,

    // AXI read interface to channels
    output logic                          axi_rd_req,
    output logic [ID_WIDTH-1:0]           axi_rd_id,
    output logic [ADDR_WIDTH-1:0]         axi_rd_addr,
    output logic [7:0]                    axi_rd_len,
    output logic [2:0]                    axi_rd_size,
    output logic [1:0]                    axi_rd_burst,
    output logic [2:0]                    axi_rd_prot,
    output logic [3:0]                    axi_rd_cache,

    // AXI write interface from channels
    output logic                          axi_wr_req,
    output logic [ID_WIDTH-1:0]           axi_wr_id,
    output logic [ADDR_WIDTH-1:0]         axi_wr_addr,
    output logic [7:0]                    axi_wr_len,
    output logic [2:0]                    axi_wr_size,
    output logic [1:0]                    axi_wr_burst,
    output logic [2:0]                    axi_wr_prot,
    output logic [3:0]                    axi_wr_cache,
    output logic [DATA_WIDTH-1:0]         axi_wr_data,
    output logic [DATA_WIDTH/8-1:0]       axi_wr_strb,
    output logic                          axi_wr_last,

    // AXI read response to channels
    input  logic                          axi_rd_data_valid,
    input  logic [DATA_WIDTH-1:0]         axi_rd_data,
    input  logic [1:0]                    axi_rd_resp,
    input  logic                          axi_rd_last,
    input  logic [ID_WIDTH-1:0]           axi_rd_data_id,

    // AXI write response to channels
    input  logic                          axi_wr_resp_valid,
    input  logic [ID_WIDTH-1:0]           axi_wr_resp_id,
    input  logic [1:0]                    axi_wr_resp,

    // AXI write data ready feedback
    input  logic                          axi_wr_ready,

    // Arbiter grant
    input  logic [ID_WIDTH-1:0]           arb_grant_id,
    input  logic                          arb_grant_valid,

    // Interrupt outputs
    output logic [NUM_CHANNELS-1:0]       ch_irq_done,
    output logic [NUM_CHANNELS-1:0]       ch_irq_err
);

    // ========================================================================
    // Per-channel wires
    // ========================================================================
    logic [NUM_CHANNELS-1:0]              ch_rd_req;
    logic [NUM_CHANNELS-1:0][ID_WIDTH-1:0]  ch_rd_id;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0] ch_rd_addr;
    logic [NUM_CHANNELS-1:0][7:0]         ch_rd_len;
    logic [NUM_CHANNELS-1:0][2:0]         ch_rd_size;
    logic [NUM_CHANNELS-1:0][1:0]         ch_rd_burst;
    logic [NUM_CHANNELS-1:0][2:0]         ch_rd_prot;
    logic [NUM_CHANNELS-1:0][3:0]         ch_rd_cache;

    logic [NUM_CHANNELS-1:0]              ch_wr_req;
    logic [NUM_CHANNELS-1:0][ID_WIDTH-1:0]  ch_wr_id;
    logic [NUM_CHANNELS-1:0][ADDR_WIDTH-1:0] ch_wr_addr;
    logic [NUM_CHANNELS-1:0][7:0]         ch_wr_len;
    logic [NUM_CHANNELS-1:0][2:0]         ch_wr_size;
    logic [NUM_CHANNELS-1:0][1:0]         ch_wr_burst;
    logic [NUM_CHANNELS-1:0][2:0]         ch_wr_prot;
    logic [NUM_CHANNELS-1:0][3:0]         ch_wr_cache;
    logic [NUM_CHANNELS-1:0][DATA_WIDTH-1:0] ch_wr_data;
    logic [NUM_CHANNELS-1:0][DATA_WIDTH/8-1:0] ch_wr_strb;
    logic [NUM_CHANNELS-1:0]              ch_wr_last;

    // ========================================================================
    // Generate NUM_CHANNELS instances
    // ========================================================================
    for (genvar i = 0; i < NUM_CHANNELS; i++) begin : gen_ch
        dma_channel #(
            .DATA_WIDTH    (DATA_WIDTH),
            .ADDR_WIDTH    (ADDR_WIDTH),
            .ID_WIDTH      (ID_WIDTH),
            .FIFO_DEPTH    (FIFO_DEPTH),
            .MAX_BURST_LEN (MAX_BURST_LEN),
            .CH_INDEX      (i)
        ) u_channel (
            .clk              (clk),
            .rst_n            (rst_n),

            .dma_enable       (dma_enable),
            .endian_swap      (endian_swap),
            .clk_gated        (clk_gating[i]),

            .ch_sar_i         (ch_sar[i]),
            .ch_dar_i         (ch_dar[i]),
            .ch_len_i         (ch_len[i]),
            .ch_cr_i          (ch_cr[i]),
            .ch_sr_w1c_i      (ch_sr_w1c_data[i]),
            .ch_llp_i         (ch_llp[i]),
            .ch_cfg_i         (ch_cfg[i]),

            .ch_state_o       (ch_state[i]),
            .ch_fifo_empty_o  (ch_fifo_empty[i]),
            .ch_fifo_full_o   (ch_fifo_full[i]),
            .ch_fifo_count_o  (ch_fifo_count[i]),
            .ch_bcr_bytes_o   (ch_bcr_bytes[i]),
            .ch_active_o      (channel_active[i]),
            .ch_idle_o        (channel_idle[i]),
            .ch_bus_error_o   (ch_bus_error[i]),
            .ch_align_error_o (ch_align_error[i]),
            .ch_desc_error_o  (ch_desc_error[i]),
            .ch_xfer_complete_o(ch_xfer_complete[i]),

            .dma_req_i        (dma_req[i]),
            .dma_ack_o        (dma_ack[i]),
            .dma_eop_i        (dma_eop[i]),

            .ch_req_o         (ch_req[i]),
            .ch_priority_o    (ch_priority[i]),

            .axi_rd_req_o     (ch_rd_req[i]),
            .axi_rd_id_o      (ch_rd_id[i]),
            .axi_rd_addr_o    (ch_rd_addr[i]),
            .axi_rd_len_o     (ch_rd_len[i]),
            .axi_rd_size_o    (ch_rd_size[i]),
            .axi_rd_burst_o   (ch_rd_burst[i]),
            .axi_rd_prot_o    (ch_rd_prot[i]),
            .axi_rd_cache_o   (ch_rd_cache[i]),

            .axi_wr_req_o     (ch_wr_req[i]),
            .axi_wr_id_o      (ch_wr_id[i]),
            .axi_wr_addr_o    (ch_wr_addr[i]),
            .axi_wr_len_o     (ch_wr_len[i]),
            .axi_wr_size_o    (ch_wr_size[i]),
            .axi_wr_burst_o   (ch_wr_burst[i]),
            .axi_wr_prot_o    (ch_wr_prot[i]),
            .axi_wr_cache_o   (ch_wr_cache[i]),
            .axi_wr_data_o    (ch_wr_data[i]),
            .axi_wr_strb_o    (ch_wr_strb[i]),
            .axi_wr_last_o    (ch_wr_last[i]),

            .axi_rd_data_valid_i (axi_rd_data_valid),
            .axi_rd_data_i    (axi_rd_data),
            .axi_rd_resp_i    (axi_rd_resp),
            .axi_rd_last_i    (axi_rd_last),
            .axi_rd_data_id_i (axi_rd_data_id),

            .axi_wr_resp_valid_i(axi_wr_resp_valid),
            .axi_wr_resp_id_i (axi_wr_resp_id),
            .axi_wr_resp_i    (axi_wr_resp),

            .axi_wr_ready_i   (axi_wr_ready),

            .arb_grant_id_i   (arb_grant_id),
            .arb_grant_valid_i(arb_grant_valid),

            .ch_irq_done_o    (ch_irq_done[i]),
            .ch_irq_err_o     (ch_irq_err[i])
        );
    end

    // ========================================================================
    // MUX: Select granted channel's AXI request
    // ========================================================================
    // Use explicit case statement for reliability with iverilog
    logic [7:0] granted_ch;
    always_comb begin
        granted_ch = '0;
        if (arb_grant_valid) begin
            case (arb_grant_id)
                4'd0: granted_ch = 8'd0;
                4'd1: granted_ch = 8'd1;
                4'd2: granted_ch = 8'd2;
                4'd3: granted_ch = 8'd3;
                4'd4: granted_ch = 8'd4;
                4'd5: granted_ch = 8'd5;
                4'd6: granted_ch = 8'd6;
                4'd7: granted_ch = 8'd7;
                default: granted_ch = '0;
            endcase
        end
    end

    always_comb begin
        axi_rd_req   = 1'b0;
        axi_rd_id    = '0;
        axi_rd_addr  = '0;
        axi_rd_len   = '0;
        axi_rd_size  = '0;
        axi_rd_burst = '0;
        axi_rd_prot  = '0;
        axi_rd_cache = '0;

        axi_wr_req   = 1'b0;
        axi_wr_id    = '0;
        axi_wr_addr  = '0;
        axi_wr_len   = '0;
        axi_wr_size  = '0;
        axi_wr_burst = '0;
        axi_wr_prot  = '0;
        axi_wr_cache = '0;
        axi_wr_data  = '0;
        axi_wr_strb  = '0;
        axi_wr_last  = 1'b0;

        if (arb_grant_valid) begin
            axi_rd_req   = ch_rd_req   [granted_ch];
            axi_rd_id    = ch_rd_id    [granted_ch];
            axi_rd_addr  = ch_rd_addr  [granted_ch];
            axi_rd_len   = ch_rd_len   [granted_ch];
            axi_rd_size  = ch_rd_size  [granted_ch];
            axi_rd_burst = ch_rd_burst [granted_ch];
            axi_rd_prot  = ch_rd_prot  [granted_ch];
            axi_rd_cache = ch_rd_cache [granted_ch];

            axi_wr_req   = ch_wr_req   [granted_ch];
            axi_wr_id    = ch_wr_id    [granted_ch];
            axi_wr_addr  = ch_wr_addr  [granted_ch];
            axi_wr_len   = ch_wr_len   [granted_ch];
            axi_wr_size  = ch_wr_size  [granted_ch];
            axi_wr_burst = ch_wr_burst [granted_ch];
            axi_wr_prot  = ch_wr_prot  [granted_ch];
            axi_wr_cache = ch_wr_cache [granted_ch];
            axi_wr_data  = ch_wr_data  [granted_ch];
            axi_wr_strb  = ch_wr_strb  [granted_ch];
            axi_wr_last  = ch_wr_last  [granted_ch];
        end
    end

endmodule
