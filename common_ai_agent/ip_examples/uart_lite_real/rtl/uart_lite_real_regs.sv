// uart_lite_real_regs.sv — APB register decode, status aggregation, interrupt combiner
// SSOT: registers.register_list, interrupts, error_handling

`include "uart_lite_real_param.vh"

module uart_lite_real_regs (
    input  wire                   PCLK,
    input  wire                   PRESETn,
    // APB interface
    input  wire [APB_ADDR_WIDTH-1:0] PADDR,
    input  wire                   PSEL,
    input  wire                   PENABLE,
    input  wire                   PWRITE,
    input  wire [APB_DATA_WIDTH-1:0] PWDATA,
    input  wire [3:0]             PSTRB,
    output reg  [APB_DATA_WIDTH-1:0] PRDATA,
    output wire                   PREADY,
    output wire                   PSLVERR,
    // Register outputs
    output reg                    tx_enable_o,
    output reg                    rx_enable_o,
    output reg                    loopback_o,
    output reg                    break_send_o,
    output reg                    parity_en_o,
    output reg                    parity_odd_o,
    output reg                    stop_bits_o,
    output reg  [15:0]            baud_div_o,
    // TX FIFO interface
    output wire                   tx_fifo_wr_o,
    output wire [DATA_WIDTH-1:0]  tx_fifo_wr_data_o,
    input  wire                   tx_fifo_full_i,
    input  wire                   tx_fifo_empty_i,
    // RX FIFO interface
    output wire                   rx_fifo_rd_o,
    input  wire [DATA_WIDTH-1:0]  rx_fifo_rd_data_i,
    input  wire                   rx_fifo_empty_i,
    // Status inputs
    input  wire                   tx_busy_i,
    input  wire                   rx_busy_i,
    input  wire                   tx_active_i,
    input  wire                   rx_active_i,
    // Error inputs from RX
    input  wire                   frame_err_i,
    input  wire                   parity_err_i,
    input  wire                   overrun_err_i,
    input  wire                   underrun_err_i,
    // Debug counter inputs
    input  wire [31:0]            bytes_tx_i,
    input  wire [31:0]            bytes_rx_i,
    input  wire [31:0]            frames_errored_i,
    input  wire [31:0]            parities_errored_i,
    // Error clear
    output reg                    clear_errors_o,
    // Interrupt
    output wire                   uart_irq_o
);

    // APB handshake
    assign PREADY  = PSEL && PENABLE;
    assign PSLVERR = PSEL && PENABLE && (PADDR >= 8'h30);

    // APB write strobe
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    // Sticky error registers (latched from RX inputs)
    reg sticky_frame_err;
    reg sticky_parity_err;
    reg sticky_overrun_err;
    reg sticky_underrun_err;

    // Interrupt enable registers
    reg tx_empty_en;
    reg rx_not_empty_en;
    reg rx_overrun_en;
    reg frame_err_en;
    reg parity_err_en;

    // Interrupt pending
    reg tx_empty_pend;
    reg rx_not_empty_pend;
    reg rx_overrun_pend;
    reg frame_err_pend;
    reg parity_err_pend;

    // Edge detection for level-triggered sources
    reg tx_fifo_empty_prev;
    reg rx_fifo_empty_prev;

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_fifo_empty_prev <= 1'b1;
            rx_fifo_empty_prev <= 1'b1;
        end else begin
            tx_fifo_empty_prev <= tx_fifo_empty_i;
            rx_fifo_empty_prev <= rx_fifo_empty_i;
        end
    end

    wire tx_became_empty = tx_fifo_empty_i && !tx_fifo_empty_prev;
    wire rx_became_not_empty = !rx_fifo_empty_i && rx_fifo_empty_prev;

    // TX FIFO write from APB
    assign tx_fifo_wr_o       = apb_write && (PADDR == 8'h0C) && !tx_fifo_full_i;
    assign tx_fifo_wr_data_o  = PWDATA[DATA_WIDTH-1:0];

    // RX FIFO read from APB
    assign rx_fifo_rd_o       = apb_read && (PADDR == 8'h10) && !rx_fifo_empty_i;

    // Interrupt output: OR of all enabled pending sources
    assign uart_irq_o = (
        (tx_empty_pend    & tx_empty_en) |
        (rx_not_empty_pend & rx_not_empty_en) |
        (rx_overrun_pend  & rx_overrun_en) |
        (frame_err_pend   & frame_err_en) |
        (parity_err_pend  & parity_err_en)
    );

    // Error clear output
    always @(*) begin
        clear_errors_o = 1'b0;
        if (apb_write && PADDR == 8'h1C) begin
            clear_errors_o = 1'b1;
        end
    end

    // APB read mux
    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};
        if (apb_read) begin
            case (PADDR)
                8'h00: begin // CTRL
                    PRDATA[0] = tx_enable_o;
                    PRDATA[1] = rx_enable_o;
                    PRDATA[2] = loopback_o;
                    PRDATA[3] = break_send_o;
                    PRDATA[4] = parity_en_o;
                    PRDATA[5] = parity_odd_o;
                    PRDATA[6] = stop_bits_o;
                end
                8'h04: begin // STAT
                    PRDATA[0] = tx_fifo_full_i;
                    PRDATA[1] = tx_fifo_empty_i;
                    PRDATA[2] = rx_fifo_empty_i;
                    PRDATA[3] = ~rx_fifo_empty_i; // rx_full (use count)
                    PRDATA[4] = tx_busy_i;
                    PRDATA[5] = rx_busy_i;
                    PRDATA[6] = sticky_frame_err;
                    PRDATA[7] = sticky_parity_err;
                    PRDATA[8] = sticky_overrun_err;
                    PRDATA[9] = sticky_underrun_err;
                end
                8'h08: begin // BAUD
                    PRDATA[15:0] = baud_div_o;
                end
                8'h10: begin // RXDATA
                    PRDATA[DATA_WIDTH-1:0] = rx_fifo_rd_data_i;
                end
                8'h14: begin // INTEN
                    PRDATA[0] = tx_empty_en;
                    PRDATA[1] = rx_not_empty_en;
                    PRDATA[2] = rx_overrun_en;
                    PRDATA[3] = frame_err_en;
                    PRDATA[4] = parity_err_en;
                end
                8'h18: begin // INTPEND
                    PRDATA[0] = tx_empty_pend;
                    PRDATA[1] = rx_not_empty_pend;
                    PRDATA[2] = rx_overrun_pend;
                    PRDATA[3] = frame_err_pend;
                    PRDATA[4] = parity_err_pend;
                end
                8'h20: PRDATA = bytes_tx_i;
                8'h24: PRDATA = bytes_rx_i;
                8'h28: PRDATA = frames_errored_i;
                8'h2C: PRDATA = parities_errored_i;
                default: PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

    // APB write + register updates
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_enable_o   <= 1'b0;
            rx_enable_o   <= 1'b0;
            loopback_o    <= 1'b0;
            break_send_o  <= 1'b0;
            parity_en_o   <= 1'b0;
            parity_odd_o  <= 1'b0;
            stop_bits_o   <= 1'b0;
            baud_div_o    <= 16'd324;
            tx_empty_en   <= 1'b0;
            rx_not_empty_en <= 1'b0;
            rx_overrun_en <= 1'b0;
            frame_err_en  <= 1'b0;
            parity_err_en <= 1'b0;
            tx_empty_pend    <= 1'b0;
            rx_not_empty_pend <= 1'b0;
            rx_overrun_pend  <= 1'b0;
            frame_err_pend   <= 1'b0;
            parity_err_pend  <= 1'b0;
            sticky_frame_err  <= 1'b0;
            sticky_parity_err <= 1'b0;
            sticky_overrun_err <= 1'b0;
            sticky_underrun_err <= 1'b0;
        end else begin
            // Latch error inputs (sticky)
            if (frame_err_i)    sticky_frame_err   <= 1'b1;
            if (parity_err_i)   sticky_parity_err  <= 1'b1;
            if (overrun_err_i)  sticky_overrun_err <= 1'b1;
            if (underrun_err_i) sticky_underrun_err <= 1'b1;

            // Update pending interrupts (edge-triggered for level sources)
            if (tx_became_empty && tx_empty_en) begin
                tx_empty_pend <= 1'b1;
            end
            if (rx_became_not_empty && rx_not_empty_en) begin
                rx_not_empty_pend <= 1'b1;
            end
            if (sticky_overrun_err && rx_overrun_en) begin
                rx_overrun_pend <= 1'b1;
            end
            if (sticky_frame_err && frame_err_en) begin
                frame_err_pend <= 1'b1;
            end
            if (sticky_parity_err && parity_err_en) begin
                parity_err_pend <= 1'b1;
            end

            // APB writes
            if (apb_write) begin
                case (PADDR)
                    8'h00: begin // CTRL
                        tx_enable_o  <= PWDATA[0];
                        rx_enable_o  <= PWDATA[1];
                        loopback_o   <= PWDATA[2];
                        break_send_o <= PWDATA[3];
                        parity_en_o  <= PWDATA[4];
                        parity_odd_o <= PWDATA[5];
                        stop_bits_o  <= PWDATA[6];
                    end
                    8'h08: begin // BAUD
                        baud_div_o <= PWDATA[15:0];
                    end
                    8'h14: begin // INTEN
                        tx_empty_en    <= PWDATA[0];
                        rx_not_empty_en <= PWDATA[1];
                        rx_overrun_en  <= PWDATA[2];
                        frame_err_en   <= PWDATA[3];
                        parity_err_en  <= PWDATA[4];
                    end
                    8'h18: begin // INTPEND W1C
                        if (PWDATA[0]) tx_empty_pend     <= 1'b0;
                        if (PWDATA[1]) rx_not_empty_pend <= 1'b0;
                        if (PWDATA[2]) rx_overrun_pend   <= 1'b0;
                        if (PWDATA[3]) frame_err_pend    <= 1'b0;
                        if (PWDATA[4]) parity_err_pend   <= 1'b0;
                    end
                    8'h1C: begin // CLR_STAT W1C
                        if (PWDATA[0]) sticky_frame_err    <= 1'b0;
                        if (PWDATA[1]) sticky_parity_err   <= 1'b0;
                        if (PWDATA[2]) sticky_overrun_err  <= 1'b0;
                        if (PWDATA[3]) sticky_underrun_err <= 1'b0;
                    end
                    default: begin
                        // TXDATA (0x0C) write handled by fifo_wr logic above
                    end
                endcase
            end

            // RX FIFO read clears rx_not_empty_pend
            if (rx_fifo_rd_o && rx_fifo_empty_i) begin
                rx_not_empty_pend <= 1'b0;
            end
        end
    end

endmodule
