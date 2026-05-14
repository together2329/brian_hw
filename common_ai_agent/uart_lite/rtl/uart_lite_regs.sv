// uart_lite_regs.sv — APB register decode, status aggregation, interrupt combiner
// Implements the complete register map: CTRL, STAT, BAUD, TXDATA, RXDATA,
// INTEN, INTPEND, CLR_STAT, and debug counters DBG_BYTES_TX/RX/FRAMES_ERR/PARITIES_ERR.
// APB4 slave interface with PREADY/PSLVERR handshake.
//
// SSOT: registers.register_list, interrupts, error_handling

`include "uart_lite_param.vh"

module uart_lite_regs #(
    parameter integer DATA_WIDTH      = `UART_LITE_DATA_WIDTH,
    parameter integer FIFO_DEPTH      = `UART_LITE_FIFO_DEPTH,
    parameter integer APB_ADDR_WIDTH  = `UART_LITE_APB_ADDR_WIDTH,
    parameter integer APB_DATA_WIDTH  = `UART_LITE_APB_DATA_WIDTH
) (
    input  logic                     PCLK,
    input  logic                     PRESETn,

    // ---------- APB4 slave interface ----------
    input  logic [APB_ADDR_WIDTH-1:0]  PADDR,
    input  logic                     PSEL,
    input  logic                     PENABLE,
    input  logic                     PWRITE,
    input  logic [APB_DATA_WIDTH-1:0]  PWDATA,
    input  logic [3:0]               PSTRB,
    output logic [APB_DATA_WIDTH-1:0]  PRDATA,
    output logic                     PREADY,
    output logic                     PSLVERR,

    // ---------- Control outputs to core ----------
    output logic                     tx_enable_o,
    output logic                     rx_enable_o,
    output logic                     loopback_o,
    output logic                     parity_en_o,
    output logic                     parity_odd_o,
    output logic                     stop_bits_o,
    output logic [15:0]              baud_div_o,

    // Break send control (self-clearing)
    input  logic                     baud_tick_i,
    output logic                     break_send_o,

    // ---------- Status inputs from core ----------
    input  logic                     tx_full_i,
    input  logic                     tx_empty_i,
    input  logic                     rx_empty_i,
    input  logic                     rx_full_i,
    input  logic                     tx_busy_i,
    input  logic                     rx_busy_i,
    input  logic                     frame_err_i,
    input  logic                     parity_err_i,
    input  logic                     overrun_err_i,
    input  logic                     underrun_err_i,

    // ---------- TXDATA write interface ----------
    output logic                     tx_fifo_wr_en_o,
    output logic [DATA_WIDTH-1:0]    tx_fifo_wr_data_o,

    // ---------- RXDATA read interface ----------
    output logic                     rx_fifo_rd_en_o,
    input  logic [DATA_WIDTH-1:0]    rx_fifo_rd_data_i,

    // ---------- Debug counter inputs from core ----------
    input  logic [31:0]              bytes_tx_i,
    input  logic [31:0]              bytes_rx_i,
    input  logic [31:0]              frames_errored_i,
    input  logic [31:0]              parities_errored_i,

    // ---------- Interrupt output ----------
    output logic                     uart_irq_o
);

    // Register address map (word-aligned, 4-byte offsets)
    localparam [APB_ADDR_WIDTH-1:0] ADDR_CTRL          = 8'h00;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_STAT          = 8'h04;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_BAUD          = 8'h08;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_TXDATA        = 8'h0C;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_RXDATA        = 8'h10;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_INTEN         = 8'h14;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_INTPEND       = 8'h18;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_CLR_STAT      = 8'h1C;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_DBG_BYTES_TX  = 8'h20;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_DBG_BYTES_RX  = 8'h24;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_DBG_FRAMES_ERR = 8'h28;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_DBG_PARITIES_ERR = 8'h2C;

    // APB access phase
    wire access_phase;
    assign access_phase = PSEL && PENABLE;

    // Illegal address: any address >= 0x30
    wire illegal_addr;
    assign illegal_addr = (PADDR >= 8'h30);

    // ---------- APB outputs ----------
    assign PREADY  = access_phase;
    assign PSLVERR = access_phase && illegal_addr;

    // ---------- Internal register storage ----------
    logic tx_enable_reg, rx_enable_reg, loopback_reg;
    logic parity_en_reg, parity_odd_reg, stop_bits_reg;
    logic break_send_reg;
    logic [15:0] baud_div_reg;

    // Sticky error flags
    logic frame_err_sticky, parity_err_sticky, overrun_err_sticky, underrun_err_sticky;

    // Interrupt enable and pending
    logic tx_empty_en, rx_not_empty_en, rx_overrun_en, frame_err_en, parity_err_en;
    logic tx_empty_pend, rx_not_empty_pend, rx_overrun_pend, frame_err_pend, parity_err_pend;

    // Break timer
    logic [7:0] break_timer;
    logic       break_timer_active;

    // ---------- Write/Read strobes ----------
    wire wr_ctrl     = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_CTRL);
    wire wr_baud     = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_BAUD);
    wire wr_txdata   = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_TXDATA);
    wire wr_inten    = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_INTEN);
    wire wr_intpend  = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_INTPEND);
    wire wr_clr_stat = access_phase && PWRITE && !illegal_addr && (PADDR == ADDR_CLR_STAT);
    wire rd_rxdata   = access_phase && !PWRITE && !illegal_addr && (PADDR == ADDR_RXDATA);

    // ---------- Break frame duration (combinational) ----------
    // Frame length in baud ticks: start(1) + DATA_WIDTH + parity(0/1) + stop(1/2)
    wire [2:0] data_width_3b;
    assign data_width_3b = DATA_WIDTH[2:0];
    wire [7:0] break_frame_len;
    // Pad DATA_WIDTH to 8-bit for addition; avoid negative repeat when DATA_WIDTH=8
    wire [7:0] data_width_8b;
    assign data_width_8b = {5'd0, data_width_3b};
    assign break_frame_len = 8'd1
                           + data_width_8b
                           + (parity_en_reg ? 8'd1 : 8'd0)
                           + (stop_bits_reg ? 8'd2 : 8'd1);

    // ---------- Single sequential block for all register state ----------
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            // CTRL
            tx_enable_reg   <= 1'b0;
            rx_enable_reg   <= 1'b0;
            loopback_reg    <= 1'b0;
            parity_en_reg   <= 1'b0;
            parity_odd_reg  <= 1'b0;
            stop_bits_reg   <= 1'b0;
            break_send_reg  <= 1'b0;

            // BAUD
            baud_div_reg    <= 16'd324;  // reset: 9600 baud at 50MHz/16x

            // INTEN
            tx_empty_en     <= 1'b0;
            rx_not_empty_en <= 1'b0;
            rx_overrun_en   <= 1'b0;
            frame_err_en    <= 1'b0;
            parity_err_en   <= 1'b0;

            // INTPEND
            tx_empty_pend    <= 1'b0;
            rx_not_empty_pend <= 1'b0;
            rx_overrun_pend  <= 1'b0;
            frame_err_pend   <= 1'b0;
            parity_err_pend  <= 1'b0;

            // Sticky error flags
            frame_err_sticky    <= 1'b0;
            parity_err_sticky   <= 1'b0;
            overrun_err_sticky  <= 1'b0;
            underrun_err_sticky <= 1'b0;

            // FIFO write/read strobes
            tx_fifo_wr_en_o   <= 1'b0;
            tx_fifo_wr_data_o <= {DATA_WIDTH{1'b0}};
            rx_fifo_rd_en_o   <= 1'b0;

            // Break timer
            break_timer       <= 8'd0;
            break_timer_active <= 1'b0;
        end else begin
            // Default pulse values
            tx_fifo_wr_en_o <= 1'b0;
            rx_fifo_rd_en_o <= 1'b0;

            // --- CTRL write ---
            if (wr_ctrl) begin
                tx_enable_reg  <= PWDATA[0];
                rx_enable_reg  <= PWDATA[1];
                loopback_reg   <= PWDATA[2];
                // break_send: set on 0→1 transition
                if (PWDATA[3] && !break_send_reg)
                    break_send_reg <= 1'b1;
                parity_en_reg  <= PWDATA[4];
                parity_odd_reg <= PWDATA[5];
                stop_bits_reg  <= PWDATA[6];
            end

            // --- BAUD write ---
            if (wr_baud) begin
                baud_div_reg <= PWDATA[15:0];
            end

            // --- TXDATA write (push to TX FIFO) ---
            if (wr_txdata) begin
                if (!tx_full_i) begin
                    tx_fifo_wr_en_o   <= 1'b1;
                    tx_fifo_wr_data_o <= PWDATA[DATA_WIDTH-1:0];
                end
            end

            // --- RXDATA read (pop from RX FIFO) ---
            if (rd_rxdata) begin
                if (!rx_empty_i) begin
                    rx_fifo_rd_en_o <= 1'b1;
                end
            end

            // --- INTEN write ---
            if (wr_inten) begin
                tx_empty_en     <= PWDATA[0];
                rx_not_empty_en <= PWDATA[1];
                rx_overrun_en   <= PWDATA[2];
                frame_err_en    <= PWDATA[3];
                parity_err_en   <= PWDATA[4];
            end

            // --- INTPEND write (W1C) ---
            if (wr_intpend) begin
                if (PWDATA[0]) tx_empty_pend    <= 1'b0;
                if (PWDATA[1]) rx_not_empty_pend <= 1'b0;
                if (PWDATA[2]) rx_overrun_pend  <= 1'b0;
                if (PWDATA[3]) frame_err_pend   <= 1'b0;
                if (PWDATA[4]) parity_err_pend  <= 1'b0;
            end

            // --- CLR_STAT write (W1C) ---
            if (wr_clr_stat) begin
                if (PWDATA[0]) frame_err_sticky    <= 1'b0;
                if (PWDATA[1]) parity_err_sticky   <= 1'b0;
                if (PWDATA[2]) overrun_err_sticky  <= 1'b0;
                if (PWDATA[3]) underrun_err_sticky <= 1'b0;
            end

            // --- Sticky error accumulation ---
            if (frame_err_i)    frame_err_sticky    <= 1'b1;
            if (parity_err_i)   parity_err_sticky   <= 1'b1;
            if (overrun_err_i)  overrun_err_sticky  <= 1'b1;
            if (underrun_err_i) underrun_err_sticky <= 1'b1;

            // --- Interrupt pending set ---
            if (tx_empty_i && tx_empty_en)
                tx_empty_pend <= 1'b1;
            if (!rx_empty_i && rx_not_empty_en)
                rx_not_empty_pend <= 1'b1;
            if (overrun_err_sticky && rx_overrun_en)
                rx_overrun_pend <= 1'b1;
            if (frame_err_sticky && frame_err_en)
                frame_err_pend <= 1'b1;
            if (parity_err_sticky && parity_err_en)
                parity_err_pend <= 1'b1;

            // --- Break timer: self-clear after one frame ---
            if (break_send_reg && !break_timer_active) begin
                break_timer_active <= 1'b1;
                break_timer       <= 8'd0;
            end else if (break_timer_active && baud_tick_i) begin
                if (break_timer >= (break_frame_len - 8'd1)) begin
                    break_send_reg    <= 1'b0;
                    break_timer_active <= 1'b0;
                    break_timer       <= 8'd0;
                end else begin
                    break_timer <= break_timer + 8'd1;
                end
            end
        end
    end

    // ---------- Control outputs (continuous from registers) ----------
    assign tx_enable_o  = tx_enable_reg;
    assign rx_enable_o  = rx_enable_reg;
    assign loopback_o   = loopback_reg;
    assign break_send_o = break_send_reg;
    assign parity_en_o  = parity_en_reg;
    assign parity_odd_o = parity_odd_reg;
    assign stop_bits_o  = stop_bits_reg;
    assign baud_div_o   = baud_div_reg;

    // ---------- Interrupt output (combinational) ----------
    assign uart_irq_o = (tx_empty_pend && tx_empty_en)
                      | (rx_not_empty_pend && rx_not_empty_en)
                      | (rx_overrun_pend && rx_overrun_en)
                      | (frame_err_pend && frame_err_en)
                      | (parity_err_pend && parity_err_en);

    // ---------- Read mux (combinational) ----------
    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};  // default

        if (access_phase && !illegal_addr) begin
            case (PADDR)
                ADDR_CTRL: begin
                    PRDATA[0] = tx_enable_reg;
                    PRDATA[1] = rx_enable_reg;
                    PRDATA[2] = loopback_reg;
                    PRDATA[3] = break_send_reg;
                    PRDATA[4] = parity_en_reg;
                    PRDATA[5] = parity_odd_reg;
                    PRDATA[6] = stop_bits_reg;
                end

                ADDR_STAT: begin
                    PRDATA[0]  = tx_full_i;
                    PRDATA[1]  = tx_empty_i;
                    PRDATA[2]  = rx_empty_i;
                    PRDATA[3]  = rx_full_i;
                    PRDATA[4]  = tx_busy_i;
                    PRDATA[5]  = rx_busy_i;
                    PRDATA[6]  = frame_err_sticky;
                    PRDATA[7]  = parity_err_sticky;
                    PRDATA[8]  = overrun_err_sticky;
                    PRDATA[9]  = underrun_err_sticky;
                end

                ADDR_BAUD: begin
                    PRDATA[15:0] = baud_div_reg;
                end

                ADDR_TXDATA: begin
                    // Write-only — reads return 0 per reserved field policy
                end

                ADDR_RXDATA: begin
                    PRDATA = { {(APB_DATA_WIDTH-DATA_WIDTH){1'b0}}, rx_fifo_rd_data_i };
                end

                ADDR_INTEN: begin
                    PRDATA[0] = tx_empty_en;
                    PRDATA[1] = rx_not_empty_en;
                    PRDATA[2] = rx_overrun_en;
                    PRDATA[3] = frame_err_en;
                    PRDATA[4] = parity_err_en;
                end

                ADDR_INTPEND: begin
                    PRDATA[0] = tx_empty_pend;
                    PRDATA[1] = rx_not_empty_pend;
                    PRDATA[2] = rx_overrun_pend;
                    PRDATA[3] = frame_err_pend;
                    PRDATA[4] = parity_err_pend;
                end

                ADDR_CLR_STAT: begin
                    // W1C register — reads return 0
                end

                ADDR_DBG_BYTES_TX: begin
                    PRDATA = bytes_tx_i;
                end

                ADDR_DBG_BYTES_RX: begin
                    PRDATA = bytes_rx_i;
                end

                ADDR_DBG_FRAMES_ERR: begin
                    PRDATA = frames_errored_i;
                end

                ADDR_DBG_PARITIES_ERR: begin
                    PRDATA = parities_errored_i;
                end

                default: PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

    // APB-lite ports that are intentionally unused by this register bank
    // (PSTRB ignored — word-aligned registers; PWDATA[31:16] ignored —
    //  no register uses upper bits). Sink them to keep verilator quiet.
    wire apb_unused_sink;
    assign apb_unused_sink = (|PSTRB) | (|PWDATA[31:16]) | (|FIFO_DEPTH[0]);

endmodule
