// dma_real_apb_cfg.sv — APB slave register decode in pclk domain
// v2: STRIDE, GLOBAL_TIMEOUT, PERF_WORDS, PERF_CYCLES registers; CDC FIFO push
module dma_real_apb_cfg #(
    parameter integer ADDR_WIDTH  = 32,
    parameter integer DATA_WIDTH  = 32,
    parameter integer N_CHANNELS  = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [11:0]           paddr,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic                  dma_en,
    output logic [N_CHANNELS-1:0] ch_en,
    output logic [N_CHANNELS-1:0] ch_start_pulse,
    output logic [ADDR_WIDTH-1:0] cfg_src_addr_0, cfg_src_addr_1, cfg_src_addr_2, cfg_src_addr_3,
    output logic [ADDR_WIDTH-1:0] cfg_dst_addr_0, cfg_dst_addr_1, cfg_dst_addr_2, cfg_dst_addr_3,
    output logic [15:0]           cfg_len_0, cfg_len_1, cfg_len_2, cfg_len_3,
    output logic [ADDR_WIDTH-1:0] cfg_stride_0, cfg_stride_1, cfg_stride_2, cfg_stride_3,
    output logic [15:0]           cfg_timeout,
    input  logic [N_CHANNELS-1:0] ch_busy,
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    input  logic [7:0]            ch_err_code,
    input  logic [N_CHANNELS-1:0] int_done,
    input  logic [N_CHANNELS-1:0] int_error,
    output logic [N_CHANNELS-1:0] int_enable_wr,
    output logic [N_CHANNELS-1:0] int_enable_wdata,
    output logic [N_CHANNELS-1:0] int_clear_wr,
    input  logic [N_CHANNELS-1:0] int_status,
    input  logic [N_CHANNELS-1:0] int_enable_rd,
    input  logic [31:0]           perf_words_0, perf_words_1, perf_words_2, perf_words_3,
    input  logic [31:0]           perf_cycles_0, perf_cycles_1, perf_cycles_2, perf_cycles_3
);

    wire apb_wr = psel && penable && pwrite;
    wire apb_rd = psel && penable && !pwrite;
    assign pready = psel && penable;

    localparam [11:0] ADDR_GLOBAL_CTRL   = 12'h000;
    localparam [11:0] ADDR_INT_STATUS    = 12'h004;
    localparam [11:0] ADDR_INT_ENABLE    = 12'h008;
    localparam [11:0] ADDR_INT_CLEAR     = 12'h00C;
    localparam [11:0] ADDR_GLOBAL_TIMEOUT = 12'h010;
    localparam [11:0] CH0_BASE = 12'h100;
    localparam [11:0] CH1_BASE = 12'h140;
    localparam [11:0] CH2_BASE = 12'h180;
    localparam [11:0] CH3_BASE = 12'h1C0;

    wire addr_global_ctrl   = (paddr == ADDR_GLOBAL_CTRL);
    wire addr_int_status    = (paddr == ADDR_INT_STATUS);
    wire addr_int_enable    = (paddr == ADDR_INT_ENABLE);
    wire addr_int_clear     = (paddr == ADDR_INT_CLEAR);
    wire addr_global_timeout = (paddr == ADDR_GLOBAL_TIMEOUT);

    wire addr_ch0 = (paddr >= CH0_BASE && paddr < CH1_BASE);
    wire addr_ch1 = (paddr >= CH1_BASE && paddr < CH2_BASE);
    wire addr_ch2 = (paddr >= CH2_BASE && paddr < CH3_BASE);
    wire addr_ch3 = (paddr >= CH3_BASE && paddr < 12'h200);

    wire addr_known = addr_global_ctrl || addr_int_status || addr_int_enable || addr_int_clear || addr_global_timeout || addr_ch0 || addr_ch1 || addr_ch2 || addr_ch3;
    assign pslverr = (apb_wr || apb_rd) && !addr_known;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) dma_en <= 1'b0;
        else if (apb_wr && addr_global_ctrl) dma_en <= pwdata[0];
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) cfg_timeout <= 16'd1024;
        else if (apb_wr && addr_global_timeout) cfg_timeout <= pwdata[15:0];
    end

    logic [N_CHANNELS-1:0] ch_start_req;
    genvar ch;
    generate
        for (ch = 0; ch < N_CHANNELS; ch = ch + 1) begin : gen_ch
            wire [11:0] ch_base = (ch == 0) ? CH0_BASE : (ch == 1) ? CH1_BASE : (ch == 2) ? CH2_BASE : CH3_BASE;
            wire addr_ctrl   = (paddr == ch_base + 12'h00);
            wire addr_src    = (paddr == ch_base + 12'h04);
            wire addr_dst    = (paddr == ch_base + 12'h08);
            wire addr_len    = (paddr == ch_base + 12'h0C);
            wire addr_status = (paddr == ch_base + 12'h10);
            wire addr_stride = (paddr == ch_base + 12'h14);
            wire addr_perf_w = (paddr == ch_base + 12'h1C);
            wire addr_perf_c = (paddr == ch_base + 12'h20);

            always @(posedge pclk or negedge presetn) begin
                if (!presetn) begin
                    ch_en[ch] <= 1'b0;
                    ch_start_req[ch] <= 1'b0;
                end else begin
                    ch_start_req[ch] <= 1'b0;
                    if (apb_wr && addr_ctrl) begin
                        ch_en[ch] <= pwdata[0];
                        if (pwdata[1]) ch_start_req[ch] <= 1'b1;
                    end
                end
            end
        end
    endgenerate
    assign ch_start_pulse = ch_start_req;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            cfg_src_addr_0 <= 0; cfg_src_addr_1 <= 0; cfg_src_addr_2 <= 0; cfg_src_addr_3 <= 0;
            cfg_dst_addr_0 <= 0; cfg_dst_addr_1 <= 0; cfg_dst_addr_2 <= 0; cfg_dst_addr_3 <= 0;
            cfg_len_0 <= 0; cfg_len_1 <= 0; cfg_len_2 <= 0; cfg_len_3 <= 0;
            cfg_stride_0 <= 32'd4; cfg_stride_1 <= 32'd4; cfg_stride_2 <= 32'd4; cfg_stride_3 <= 32'd4;
        end else if (apb_wr) begin
            if (paddr == CH0_BASE + 12'h04) cfg_src_addr_0 <= pwdata;
            if (paddr == CH0_BASE + 12'h08) cfg_dst_addr_0 <= pwdata;
            if (paddr == CH0_BASE + 12'h0C) cfg_len_0 <= pwdata[15:0];
            if (paddr == CH0_BASE + 12'h14) cfg_stride_0 <= pwdata;
            if (paddr == CH1_BASE + 12'h04) cfg_src_addr_1 <= pwdata;
            if (paddr == CH1_BASE + 12'h08) cfg_dst_addr_1 <= pwdata;
            if (paddr == CH1_BASE + 12'h0C) cfg_len_1 <= pwdata[15:0];
            if (paddr == CH1_BASE + 12'h14) cfg_stride_1 <= pwdata;
            if (paddr == CH2_BASE + 12'h04) cfg_src_addr_2 <= pwdata;
            if (paddr == CH2_BASE + 12'h08) cfg_dst_addr_2 <= pwdata;
            if (paddr == CH2_BASE + 12'h0C) cfg_len_2 <= pwdata[15:0];
            if (paddr == CH2_BASE + 12'h14) cfg_stride_2 <= pwdata;
            if (paddr == CH3_BASE + 12'h04) cfg_src_addr_3 <= pwdata;
            if (paddr == CH3_BASE + 12'h08) cfg_dst_addr_3 <= pwdata;
            if (paddr == CH3_BASE + 12'h0C) cfg_len_3 <= pwdata[15:0];
            if (paddr == CH3_BASE + 12'h14) cfg_stride_3 <= pwdata;
        end
    end

    generate
        for (ch = 0; ch < N_CHANNELS; ch = ch + 1) begin : gen_int
            assign int_enable_wr[ch]    = apb_wr && addr_int_enable;
            assign int_enable_wdata[ch] = pwdata[ch];
            assign int_clear_wr[ch]     = apb_wr && addr_int_clear && pwdata[ch];
        end
    endgenerate

    always @(*) begin
        prdata = {DATA_WIDTH{1'b0}};
        if (apb_rd) begin
            if (addr_global_ctrl)       prdata = {{31{1'b0}}, dma_en};
            else if (addr_int_status)   prdata = {{28{1'b0}}, int_status};
            else if (addr_int_enable)   prdata = {{28{1'b0}}, int_enable_rd};
            else if (addr_global_timeout) prdata = {{16{1'b0}}, cfg_timeout};
            else if (addr_ch0) begin
                case (paddr - CH0_BASE)
                    12'h00: prdata = {{29{1'b0}}, ch_en[0], 1'b0};
                    12'h04: prdata = cfg_src_addr_0;
                    12'h08: prdata = cfg_dst_addr_0;
                    12'h0C: prdata = {{16{1'b0}}, cfg_len_0};
                    12'h10: prdata = {{26{1'b0}}, ch_err_code[2:0], int_error[0], int_done[0], ch_busy[0]};
                    12'h14: prdata = cfg_stride_0;
                    12'h1C: prdata = perf_words_0;
                    12'h20: prdata = perf_cycles_0;
                    default: ;
                endcase
            end
            else if (addr_ch1) begin
                case (paddr - CH1_BASE)
                    12'h00: prdata = {{29{1'b0}}, ch_en[1], 1'b0};
                    12'h04: prdata = cfg_src_addr_1;
                    12'h08: prdata = cfg_dst_addr_1;
                    12'h0C: prdata = {{16{1'b0}}, cfg_len_1};
                    12'h10: prdata = {{26{1'b0}}, 3'b000, int_error[1], int_done[1], ch_busy[1]};
                    12'h14: prdata = cfg_stride_1;
                    12'h1C: prdata = perf_words_1;
                    12'h20: prdata = perf_cycles_1;
                    default: ;
                endcase
            end
            else if (addr_ch2) begin
                case (paddr - CH2_BASE)
                    12'h00: prdata = {{29{1'b0}}, ch_en[2], 1'b0};
                    12'h04: prdata = cfg_src_addr_2;
                    12'h08: prdata = cfg_dst_addr_2;
                    12'h0C: prdata = {{16{1'b0}}, cfg_len_2};
                    12'h10: prdata = {{26{1'b0}}, 3'b000, int_error[2], int_done[2], ch_busy[2]};
                    12'h14: prdata = cfg_stride_2;
                    12'h1C: prdata = perf_words_2;
                    12'h20: prdata = perf_cycles_2;
                    default: ;
                endcase
            end
            else if (addr_ch3) begin
                case (paddr - CH3_BASE)
                    12'h00: prdata = {{29{1'b0}}, ch_en[3], 1'b0};
                    12'h04: prdata = cfg_src_addr_3;
                    12'h08: prdata = cfg_dst_addr_3;
                    12'h0C: prdata = {{16{1'b0}}, cfg_len_3};
                    12'h10: prdata = {{26{1'b0}}, ch_err_code[7:6], int_error[3], int_done[3], ch_busy[3]};
                    12'h14: prdata = cfg_stride_3;
                    12'h1C: prdata = perf_words_3;
                    12'h20: prdata = perf_cycles_3;
                    default: ;
                endcase
            end
        end
    end

endmodule
