// dma_real_apb_cfg.sv — APB slave register decode and configuration distribution
//
// SSOT refs: registers.register_list, io_list.interfaces.apb_slave
//
// FIX: CHx_STATUS readback uses IRQ-latched done/error instead of channel raw pulses,
//   so status survives beyond the 1-cycle channel pulse.

module dma_real_apb_cfg #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // APB slave interface
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [11:0]           paddr,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    // Global control
    output logic                  dma_en,
    // Per-channel config outputs
    output logic [N_CHANNELS-1:0] ch_en,
    output logic [N_CHANNELS-1:0] ch_start_pulse,
    // Per-channel address/length config (individual wires)
    output logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3,
    output logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3,
    output logic [15:0]           cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3,
    // Per-channel status inputs (from channel FSM)
    input  logic [N_CHANNELS-1:0] ch_busy,
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    input  logic [7:0]            ch_err_code,
    // NEW: IRQ-latched done/error for STATUS readback
    input  logic [N_CHANNELS-1:0] int_done,
    input  logic [N_CHANNELS-1:0] int_error,
    // IRQ module interface
    output logic [N_CHANNELS-1:0] int_enable_wr,
    output logic [N_CHANNELS-1:0] int_enable_wdata,
    output logic [N_CHANNELS-1:0] int_clear_wr,
    input  logic [N_CHANNELS-1:0] int_status,
    input  logic [N_CHANNELS-1:0] int_enable_rd
);

    // APB qualifiers
    wire apb_wr = psel && penable && pwrite;
    wire apb_rd = psel && penable && !pwrite;

    // Register offsets from SSOT register map
    localparam [11:0] ADDR_GLOBAL_CTRL = 12'h000;
    localparam [11:0] ADDR_INT_STATUS  = 12'h004;
    localparam [11:0] ADDR_INT_ENABLE  = 12'h008;
    localparam [11:0] ADDR_INT_CLEAR   = 12'h00C;
    // Channel base offsets: CH0=0x080, CH1=0x0A0, CH2=0x0C0, CH3=0x0E0
    localparam [11:0] CH0_BASE = 12'h080;
    localparam [11:0] CH1_BASE = 12'h0A0;
    localparam [11:0] CH2_BASE = 12'h0C0;
    localparam [11:0] CH3_BASE = 12'h0E0;
    localparam [11:0] CH_CTRL_OFF    = 12'h000;
    localparam [11:0] CH_SRC_OFF     = 12'h004;
    localparam [11:0] CH_DST_OFF     = 12'h008;
    localparam [11:0] CH_LEN_OFF     = 12'h00C;
    localparam [11:0] CH_STATUS_OFF  = 12'h010;

    // APB response
    assign pready = psel && penable;

    // Address decode
    wire addr_global_ctrl = (paddr == ADDR_GLOBAL_CTRL);
    wire addr_int_status  = (paddr == ADDR_INT_STATUS);
    wire addr_int_enable  = (paddr == ADDR_INT_ENABLE);
    wire addr_int_clear   = (paddr == ADDR_INT_CLEAR);

    // Channel address decode
    genvar ch;
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_ch_addr
            wire [11:0] ch_base_addr = (ch == 0) ? CH0_BASE : (ch == 1) ? CH1_BASE :
                                      (ch == 2) ? CH2_BASE : CH3_BASE;
            wire addr_ch_ctrl   = (paddr == ch_base_addr + CH_CTRL_OFF);
            wire addr_ch_src    = (paddr == ch_base_addr + CH_SRC_OFF);
            wire addr_ch_dst    = (paddr == ch_base_addr + CH_DST_OFF);
            wire addr_ch_len    = (paddr == ch_base_addr + CH_LEN_OFF);
            wire addr_ch_status = (paddr == ch_base_addr + CH_STATUS_OFF);
            wire addr_ch_any    = addr_ch_ctrl || addr_ch_src || addr_ch_dst || addr_ch_len || addr_ch_status;
        end
    endgenerate

    // Known address check
    wire addr_known = addr_global_ctrl || addr_int_status || addr_int_enable || addr_int_clear;
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_ch_known
            wire addr_ch_any = gen_ch_addr[ch].addr_ch_any;
        end
    endgenerate

    // PSLVERR on unmapped address
    wire all_ch_known = |{gen_ch_known[0].addr_ch_any, gen_ch_known[1].addr_ch_any,
                          gen_ch_known[2].addr_ch_any, gen_ch_known[3].addr_ch_any};
    assign pslverr = (apb_wr || apb_rd) && !(addr_known || all_ch_known);

    // Global DMA enable register
    always @(posedge pclk or negedge presetn) begin
        if (!presetn)
            dma_en <= 1'b0;
        else if (apb_wr && addr_global_ctrl)
            dma_en <= pwdata[0];
    end

    // Per-channel start pulse: self-clearing one-shot
    logic [N_CHANNELS-1:0] ch_start_req;
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_ch_start
            always @(posedge pclk or negedge presetn) begin
                if (!presetn)
                    ch_start_req[ch] <= 1'b0;
                else if (apb_wr && gen_ch_addr[ch].addr_ch_ctrl && pwdata[1])
                    ch_start_req[ch] <= 1'b1;
                else
                    ch_start_req[ch] <= 1'b0;
            end
        end
    endgenerate
    assign ch_start_pulse = ch_start_req;

    // Per-channel enable registers
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_ch_regs
            always @(posedge pclk or negedge presetn) begin
                if (!presetn) begin
                    ch_en[ch] <= 1'b0;
                end else begin
                    if (apb_wr && gen_ch_addr[ch].addr_ch_ctrl)
                        ch_en[ch] <= pwdata[0];
                end
            end
        end
    endgenerate

    // Individual address/len registers
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_src_addr_0 <= {ADDR_WIDTH{1'b0}}; cfg_src_addr_1 <= {ADDR_WIDTH{1'b0}};
            cfg_src_addr_2 <= {ADDR_WIDTH{1'b0}}; cfg_src_addr_3 <= {ADDR_WIDTH{1'b0}};
            cfg_dst_addr_0 <= {ADDR_WIDTH{1'b0}}; cfg_dst_addr_1 <= {ADDR_WIDTH{1'b0}};
            cfg_dst_addr_2 <= {ADDR_WIDTH{1'b0}}; cfg_dst_addr_3 <= {ADDR_WIDTH{1'b0}};
            cfg_len_0 <= 16'd0; cfg_len_1 <= 16'd0; cfg_len_2 <= 16'd0; cfg_len_3 <= 16'd0;
        end else begin
            if (apb_wr && gen_ch_addr[0].addr_ch_src) cfg_src_addr_0 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[0].addr_ch_dst) cfg_dst_addr_0 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[0].addr_ch_len) cfg_len_0 <= pwdata[15:0];
            if (apb_wr && gen_ch_addr[1].addr_ch_src) cfg_src_addr_1 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[1].addr_ch_dst) cfg_dst_addr_1 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[1].addr_ch_len) cfg_len_1 <= pwdata[15:0];
            if (apb_wr && gen_ch_addr[2].addr_ch_src) cfg_src_addr_2 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[2].addr_ch_dst) cfg_dst_addr_2 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[2].addr_ch_len) cfg_len_2 <= pwdata[15:0];
            if (apb_wr && gen_ch_addr[3].addr_ch_src) cfg_src_addr_3 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[3].addr_ch_dst) cfg_dst_addr_3 <= pwdata[ADDR_WIDTH-1:0];
            if (apb_wr && gen_ch_addr[3].addr_ch_len) cfg_len_3 <= pwdata[15:0];
        end
    end

    // Interrupt enable register write signals
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_int_en
            assign int_enable_wr[ch]    = apb_wr && addr_int_enable;
            assign int_enable_wdata[ch] = pwdata[ch];
            assign int_clear_wr[ch]     = apb_wr && addr_int_clear && pwdata[ch];
        end
    endgenerate

    // APB readback mux
    // CHx_STATUS uses IRQ-latched done/error (sticky, cleared by INT_CLEAR)
    always @(*) begin
        prdata = {DATA_WIDTH{1'b0}};
        if (apb_rd) begin
            if (addr_global_ctrl)
                prdata = {{DATA_WIDTH-1{1'b0}}, dma_en};
            else if (addr_int_status)
                prdata = {{DATA_WIDTH-N_CHANNELS{1'b0}}, int_status};
            else if (addr_int_enable)
                prdata = {{DATA_WIDTH-N_CHANNELS{1'b0}}, int_enable_rd};
            // INT_CLEAR is write-only, read returns 0
            else if (gen_ch_known[0].addr_ch_any) begin
                if (gen_ch_addr[0].addr_ch_ctrl)
                    prdata = {{DATA_WIDTH-3{1'b0}}, ch_en[0], 2'b0};
                else if (gen_ch_addr[0].addr_ch_src)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_src_addr_0};
                else if (gen_ch_addr[0].addr_ch_dst)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_dst_addr_0};
                else if (gen_ch_addr[0].addr_ch_len)
                    prdata = {{DATA_WIDTH-16{1'b0}}, cfg_len_0};
                else if (gen_ch_addr[0].addr_ch_status)
                    prdata = {{DATA_WIDTH-8{1'b0}}, ch_err_code[1:0], int_error[0], int_done[0], ch_busy[0]};
            end
            else if (gen_ch_known[1].addr_ch_any) begin
                if (gen_ch_addr[1].addr_ch_ctrl)
                    prdata = {{DATA_WIDTH-3{1'b0}}, ch_en[1], 2'b0};
                else if (gen_ch_addr[1].addr_ch_src)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_src_addr_1};
                else if (gen_ch_addr[1].addr_ch_dst)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_dst_addr_1};
                else if (gen_ch_addr[1].addr_ch_len)
                    prdata = {{DATA_WIDTH-16{1'b0}}, cfg_len_1};
                else if (gen_ch_addr[1].addr_ch_status)
                    prdata = {{DATA_WIDTH-8{1'b0}}, ch_err_code[3:2], int_error[1], int_done[1], ch_busy[1]};
            end
            else if (gen_ch_known[2].addr_ch_any) begin
                if (gen_ch_addr[2].addr_ch_ctrl)
                    prdata = {{DATA_WIDTH-3{1'b0}}, ch_en[2], 2'b0};
                else if (gen_ch_addr[2].addr_ch_src)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_src_addr_2};
                else if (gen_ch_addr[2].addr_ch_dst)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_dst_addr_2};
                else if (gen_ch_addr[2].addr_ch_len)
                    prdata = {{DATA_WIDTH-16{1'b0}}, cfg_len_2};
                else if (gen_ch_addr[2].addr_ch_status)
                    prdata = {{DATA_WIDTH-8{1'b0}}, ch_err_code[5:4], int_error[2], int_done[2], ch_busy[2]};
            end
            else if (gen_ch_known[3].addr_ch_any) begin
                if (gen_ch_addr[3].addr_ch_ctrl)
                    prdata = {{DATA_WIDTH-3{1'b0}}, ch_en[3], 2'b0};
                else if (gen_ch_addr[3].addr_ch_src)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_src_addr_3};
                else if (gen_ch_addr[3].addr_ch_dst)
                    prdata = {{DATA_WIDTH-ADDR_WIDTH{1'b0}}, cfg_dst_addr_3};
                else if (gen_ch_addr[3].addr_ch_len)
                    prdata = {{DATA_WIDTH-16{1'b0}}, cfg_len_3};
                else if (gen_ch_addr[3].addr_ch_status)
                    prdata = {{DATA_WIDTH-8{1'b0}}, ch_err_code[7:6], int_error[3], int_done[3], ch_busy[3]};
            end
        end
    end

endmodule
