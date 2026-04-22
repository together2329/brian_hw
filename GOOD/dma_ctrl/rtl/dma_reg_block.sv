`default_nettype none
module dma_reg_block #(
    parameter int NUM_CHANNELS = 8
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // AXI4-Lite Slave Interface
    input  logic [11:0]                   s_axi_awaddr,
    input  logic [2:0]                    s_axi_awprot,
    input  logic                          s_axi_awvalid,
    output logic                          s_axi_awready,
    input  logic [31:0]                   s_axi_wdata,
    input  logic [3:0]                    s_axi_wstrb,
    input  logic                          s_axi_wvalid,
    output logic                          s_axi_wready,
    output logic [1:0]                    s_axi_bresp,
    output logic                          s_axi_bvalid,
    input  logic                          s_axi_bready,
    input  logic [11:0]                   s_axi_araddr,
    input  logic [2:0]                    s_axi_arprot,
    input  logic                          s_axi_arvalid,
    output logic                          s_axi_arready,
    output logic [31:0]                   s_axi_rdata,
    output logic [1:0]                    s_axi_rresp,
    output logic                          s_axi_rvalid,
    input  logic                          s_axi_rready,

    // Global register outputs
    output logic                          dma_enable,
    output logic                          endian_swap,
    output logic [NUM_CHANNELS-1:0]       clk_gating,

    // Per-channel register outputs (write side)
    output logic [NUM_CHANNELS-1:0][31:0] ch_sar,
    output logic [NUM_CHANNELS-1:0][31:0] ch_dar,
    output logic [NUM_CHANNELS-1:0][31:0] ch_len,
    output logic [NUM_CHANNELS-1:0][31:0] ch_cr,
    output logic [NUM_CHANNELS-1:0][31:0] ch_sr,
    output logic [NUM_CHANNELS-1:0][31:0] ch_llp,
    output logic [NUM_CHANNELS-1:0][31:0] ch_bcr,
    output logic [NUM_CHANNELS-1:0][31:0] ch_cfg,
    output logic [NUM_CHANNELS-1:0][31:0] ch_sr_w1c_data, // W1C write data to channels

    // Per-channel status inputs (read side)
    input  logic [NUM_CHANNELS-1:0][2:0]  ch_state,
    input  logic [NUM_CHANNELS-1:0]       ch_fifo_empty,
    input  logic [NUM_CHANNELS-1:0]       ch_fifo_full,
    input  logic [NUM_CHANNELS-1:0][2:0]  ch_fifo_count,
    input  logic [NUM_CHANNELS-1:0][15:0] ch_bcr_bytes,
    input  logic [NUM_CHANNELS-1:0]       ch_bus_error,
    input  logic [NUM_CHANNELS-1:0]       ch_align_error,
    input  logic [NUM_CHANNELS-1:0]       ch_desc_error,
    input  logic [NUM_CHANNELS-1:0]       ch_xfer_complete,

    // Global status inputs
    input  logic [NUM_CHANNELS-1:0]       channel_active,
    input  logic [NUM_CHANNELS-1:0]       channel_idle,

    // Interrupt register interface
    output logic [31:0]                   dma_ier,
    input  logic [31:0]                   dma_isr_in,
    output logic [31:0]                   dma_err,
    output logic [31:0]                   isr_w1c
);

    // ========================================================================
    // Global Registers
    // ========================================================================
    logic [31:0] reg_gcr;    // 0x000
    logic [31:0] reg_ier;    // 0x008
    logic [31:0] reg_err;    // 0x014 - RO (set by channels, cleared by errc)
    logic [31:0] isr_w1c_q;  // Captured W1C write data for ISR

    // Per-channel register storage (RW fields)
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_sar;
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_dar;
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_len;
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_cr;
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_sr_w1c;  // W1C bits [11:8]
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_llp;
    logic [NUM_CHANNELS-1:0][31:0] reg_ch_cfg;

    // ISR W1C capture
    logic [31:0] isr_w1c_next;

    // ========================================================================
    // Extract global register fields
    // ========================================================================
    assign dma_enable  = reg_gcr[0];
    assign endian_swap = reg_gcr[1];
    assign clk_gating  = reg_gcr[7:4];

    // ========================================================================
    // Build channel status reads and BCR
    // ========================================================================
    genvar g_sr;
    generate
        for (g_sr = 0; g_sr < NUM_CHANNELS; g_sr++) begin : gen_ch_status
            assign ch_sr[g_sr] = {20'd0,
                        ch_xfer_complete[g_sr],
                        ch_desc_error[g_sr],
                        ch_align_error[g_sr],
                        ch_bus_error[g_sr],
                        ch_fifo_count[g_sr],
                        ch_fifo_full[g_sr],
                        ch_fifo_empty[g_sr],
                        ch_state[g_sr]};
            assign ch_bcr[g_sr] = {16'd0, ch_bcr_bytes[g_sr]};
        end
    endgenerate

    // Channel register pass-through
    assign ch_sar = reg_ch_sar;
    assign ch_dar = reg_ch_dar;
    assign ch_len = reg_ch_len;
    assign ch_cr  = reg_ch_cr;
    assign ch_llp = reg_ch_llp;
    assign ch_cfg = reg_ch_cfg;

    // W1C data for channels — holds the last SR write data per channel
    // Cleared to 0 after one cycle (pulse) so channels see the W1C data once
    logic [NUM_CHANNELS-1:0][31:0] ch_sr_w1c_pulse;

    // Interrupt register pass-through
    assign dma_ier = reg_ier;
    assign dma_err = reg_err;

    // ========================================================================
    // AXI4-Lite Write FSM
    // ========================================================================
    logic [11:0] wr_addr;
    logic        wr_active;

    // Register Write Decode
    logic [11:0] wr_addr_q;
    logic        wr_en;
    logic [31:0] wr_data;
    logic [3:0]  wr_strb;

    // Channel index and offset decode helpers
    logic [$clog2(NUM_CHANNELS)-1:0] wr_ch_idx;
    logic [5:0] wr_ch_offset;
    logic       wr_ch_sel;

    // AXI4-Lite Read FSM
    logic [11:0] rd_addr;
    logic        rd_active;

    // Read Data Mux
    logic [$clog2(NUM_CHANNELS)-1:0] rd_ch_idx;
    logic [5:0] rd_ch_offset;
    logic       rd_ch_sel;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_active     <= 1'b0;
            s_axi_awready <= 1'b1;
            s_axi_wready  <= 1'b0;
            s_axi_bvalid  <= 1'b0;
            s_axi_bresp   <= 2'b00;
            wr_addr       <= 12'd0;
        end else begin
            // Write Address Phase
            if (!wr_active && s_axi_awvalid && s_axi_awready) begin
                s_axi_awready <= 1'b0;
                wr_addr       <= s_axi_awaddr;
                wr_active     <= 1'b1;
                s_axi_wready  <= 1'b1;
            end

            // Write Data Phase
            if (wr_active && s_axi_wvalid && s_axi_wready) begin
                s_axi_wready <= 1'b0;
                s_axi_bvalid <= 1'b1;
                s_axi_bresp  <= 2'b00; // OKAY
                wr_active    <= 1'b0;
            end

            // Write Response Phase
            if (s_axi_bvalid && s_axi_bready) begin
                s_axi_bvalid  <= 1'b0;
                s_axi_awready <= 1'b1;
            end
        end
    end

    // ========================================================================
    // Register Write Decode
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_addr_q <= 12'd0;
            wr_en     <= 1'b0;
            wr_data   <= 32'd0;
            wr_strb   <= 4'd0;
        end else begin
            wr_en <= 1'b0;
            if (wr_active && s_axi_wvalid && s_axi_wready) begin
                wr_addr_q <= wr_addr;
                wr_en     <= 1'b1;
                wr_data   <= s_axi_wdata;
                wr_strb   <= s_axi_wstrb;
                $display("[REG_WR] addr=%03h data=%08h ch_sel=%b ch_idx=%0d ch_off=%02h",
                         wr_addr, s_axi_wdata, (wr_addr[11:8] >= 4'd1),
                         (NUM_CHANNELS > 1) ? wr_addr[7:6] : 0, wr_addr[5:0]);
            end
        end
    end

    always_comb begin
        wr_ch_sel = (wr_addr_q[11:8] >= 4'd1);  // Channel space: 0x100-0x2FF
        if (NUM_CHANNELS > 1)
            wr_ch_idx = wr_addr_q[7:6]; // 0x40 stride per channel
        else
            wr_ch_idx = '0;
        wr_ch_offset = wr_addr_q[5:0];
    end

    // Debug: monitor register writes
    wire wr_en_rise = wr_en;
    always @(posedge clk) begin
        if (wr_en && wr_ch_sel)
            $display("[REG_WR] addr=%03h data=%08h ch_idx=%0d ch_off=%02h",
                     wr_addr_q, wr_data, wr_addr_q[7:6], wr_addr_q[5:0]);
    end

    // ========================================================================
    // Global and Channel register writes + W1C pulse generation
    // ========================================================================
    // W1C pulse: one-cycle pulse to channels and ISR when SR/ISR registers written
    logic [31:0] isr_w1c_pulse;
    logic [NUM_CHANNELS-1:0][31:0] ch_sr_w1c_pulse_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_gcr <= '0;
            reg_ier <= '0;
            isr_w1c_pulse <= '0;
            for (int j = 0; j < NUM_CHANNELS; j++) begin
                reg_ch_sar[j]     <= '0;
                reg_ch_dar[j]     <= '0;
                reg_ch_len[j]     <= '0;
                reg_ch_cr[j]      <= '0;
                reg_ch_llp[j]     <= '0;
                reg_ch_cfg[j]     <= 32'h00000030; // Default CFG: cache=0x3
                ch_sr_w1c_pulse_reg[j] <= '0;
            end
        end else begin
            // Default: clear all W1C pulses after one cycle
            isr_w1c_pulse <= '0;
            for (int j = 0; j < NUM_CHANNELS; j++)
                ch_sr_w1c_pulse_reg[j] <= '0;

            // Auto-clear CR.enable on transfer completion or error
            for (int j = 0; j < NUM_CHANNELS; j++) begin
                if (ch_xfer_complete[j] || ch_bus_error[j] || ch_desc_error[j] || ch_align_error[j])
                    reg_ch_cr[j] <= reg_ch_cr[j] & ~32'b1; // Clear bit 0
            end

            if (wr_en && !wr_ch_sel) begin
                case (wr_addr_q)
                    12'h000: reg_gcr <= wr_data;
                    12'h008: reg_ier <= wr_data;
                    12'h00C: isr_w1c_pulse <= wr_data; // ISR W1C
                    default: ;
                endcase
            end
            else if (wr_en && wr_ch_sel) begin
                for (int j = 0; j < NUM_CHANNELS; j++) begin
                    if (wr_ch_idx == j) begin
                        case (wr_ch_offset)
                            6'h00: begin reg_ch_sar[j]  <= wr_data; $display("[REG] CH%0d SAR <= %08h", j, wr_data); end
                            6'h04: begin reg_ch_dar[j]  <= wr_data; $display("[REG] CH%0d DAR <= %08h", j, wr_data); end
                            6'h08: reg_ch_len[j]  <= wr_data;
                            6'h0C: begin reg_ch_cr[j]   <= wr_data; $display("[REG] CH%0d CR <= %08h (enable=%b)", j, wr_data, wr_data[0]); end
                            6'h10: ch_sr_w1c_pulse_reg[j] <= wr_data; // W1C pulse to channel
                            6'h14: reg_ch_llp[j]  <= wr_data;
                            6'h1C: reg_ch_cfg[j]  <= wr_data;
                            default: ;
                        endcase
                    end
                end
            end
        end
    end

    // Drive W1C outputs
    assign isr_w1c        = isr_w1c_pulse;
    assign ch_sr_w1c_data = ch_sr_w1c_pulse_reg;

    // ========================================================================
    // AXI4-Lite Read FSM
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_active     <= 1'b0;
            s_axi_arready <= 1'b1;
            s_axi_rvalid  <= 1'b0;
            s_axi_rresp   <= 2'b00;
            rd_addr       <= 12'd0;
            s_axi_rdata   <= 32'd0;
        end else begin
            // Read Address Phase
            if (!rd_active && s_axi_arvalid && s_axi_arready) begin
                s_axi_arready <= 1'b0;
                rd_addr       <= s_axi_araddr;
                rd_active     <= 1'b1;
            end

            // Read Data Phase
            if (rd_active) begin
                s_axi_rvalid <= 1'b1;
                s_axi_rresp  <= 2'b00; // OKAY
                rd_active    <= 1'b0;
            end

            // Read Response Phase
            if (s_axi_rvalid && s_axi_rready) begin
                s_axi_rvalid  <= 1'b0;
                s_axi_arready <= 1'b1;
            end
        end
    end

    // ========================================================================
    // Read Data Mux
    // ========================================================================
    always_comb begin
        rd_ch_sel = (rd_addr[11:8] >= 4'd1);
        if (NUM_CHANNELS > 1)
            rd_ch_idx = rd_addr[7:6]; // 0x40 stride per channel
        else
            rd_ch_idx = '0;
        rd_ch_offset = rd_addr[5:0];
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_rdata <= 32'd0;
        end else if (rd_active) begin
            s_axi_rdata <= 32'd0; // default
            if (!rd_ch_sel) begin
                case (rd_addr[11:0])
                    12'h000: s_axi_rdata <= reg_gcr;
                    12'h004: s_axi_rdata <= {16'd0, channel_idle, channel_active};
                    12'h008: s_axi_rdata <= reg_ier;
                    12'h00C: s_axi_rdata <= dma_isr_in;
                    12'h010: s_axi_rdata <= {24'd0, dma_isr_in[7:0] & reg_ier[7:0]}; // IIR
                    12'h014: s_axi_rdata <= reg_err;
                    12'h018: s_axi_rdata <= reg_err; // ERRC reads back error status
                    12'h01C: s_axi_rdata <= 32'h00010001; // VER: major=1, minor=1
                    default: s_axi_rdata <= 32'd0;
                endcase
            end else begin
                for (int j = 0; j < NUM_CHANNELS; j++) begin
                    if (rd_ch_idx == j) begin
                        case (rd_ch_offset)
                            6'h00: s_axi_rdata <= reg_ch_sar[j];
                            6'h04: s_axi_rdata <= reg_ch_dar[j];
                            6'h08: s_axi_rdata <= reg_ch_len[j];
                            6'h0C: s_axi_rdata <= reg_ch_cr[j];
                            6'h10: s_axi_rdata <= ch_sr[j];  // Computed status
                            6'h14: s_axi_rdata <= reg_ch_llp[j];
                            6'h18: s_axi_rdata <= ch_bcr[j]; // RO byte count
                            6'h1C: s_axi_rdata <= reg_ch_cfg[j];
                            default: s_axi_rdata <= 32'd0;
                        endcase
                    end
                end
            end
        end
    end

endmodule
