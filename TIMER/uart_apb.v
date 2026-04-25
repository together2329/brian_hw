
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: uart_apb
// Description: APB3 slave interface wrapping the UART core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  TX_DATA   W    [7:0] data to transmit (write triggers TX)
//   Offset 0x04  RX_DATA   R    [7:0] received data (read clears rx_ready)
//   Offset 0x08  CTRL      R/W  [0]=tx_enable, [1]=rx_enable
//   Offset 0x0C  STATUS    R    [0]=tx_busy, [1]=tx_empty, [2]=rx_ready,
//                                [3]=rx_overflow
//   Offset 0x10  BAUD_DIV  R/W  [15:0] baud rate divisor (clocks per bit)
//
// APB3 Signals:
//   PCLK     - Bus clock
//   PRESETn  - Active-low bus reset
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe
//   PADDR    - Address bus [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Transfer ready (always 1)
//   PSLVERR  - Slave error (always 0)
//----------------------------------------------------------------------------

module uart_apb (
    input  wire         PCLK,
    input  wire         PRESETn,
    input  wire         PSEL,
    input  wire         PENABLE,
    input  wire         PWRITE,
    input  wire [7:0]   PADDR,
    input  wire [31:0]  PWDATA,
    output wire [31:0]  PRDATA,
    output wire         PREADY,
    output wire         PSLVERR,

    // UART serial pins
    input  wire         rx_in,
    output wire         tx_out,

    // UART interrupt output
    output wire         irq,
    output wire         rx_overflow
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_tx_enable;
    reg        ctrl_rx_enable;
    reg [15:0] reg_baud_div;
    reg [7:0]  tx_data_shadow;
    reg        tx_start_pulse;
    reg        rx_read_pulse;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];

    wire sel_tx_data  = (addr_word == 3'd0);
    wire sel_rx_data  = (addr_word == 3'd1);
    wire sel_ctrl     = (addr_word == 3'd2);
    wire sel_status   = (addr_word == 3'd3);
    wire sel_baud_div = (addr_word == 3'd4);

    // APB write/read strobes
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Register write logic
    //--------------------------------------------------------------------------
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            ctrl_tx_enable <= 1'b0;
            ctrl_rx_enable <= 1'b0;
            reg_baud_div   <= 16'd1;  // Default: fastest
            tx_data_shadow <= 8'd0;
            tx_start_pulse <= 1'b0;
            rx_read_pulse  <= 1'b0;
        end else begin
            // Auto-clear pulses after one clock
            tx_start_pulse <= 1'b0;
            rx_read_pulse  <= 1'b0;

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // TX_DATA - write triggers transmission
                        tx_data_shadow <= PWDATA[7:0];
                        tx_start_pulse <= 1'b1;
                    end
                    3'd2: begin // CTRL
                        ctrl_tx_enable <= PWDATA[0];
                        ctrl_rx_enable <= PWDATA[1];
                    end
                    3'd4: begin // BAUD_DIV
                        reg_baud_div <= PWDATA[15:0];
                    end
                    // RX_DATA (0x04): read-only
                    // STATUS (0x0C): read-only
                    default: ;
                endcase
            end

            // RX_DATA read generates rx_read pulse to clear rx_ready
            if (apb_read && sel_rx_data) begin
                rx_read_pulse <= 1'b1;
            end
        end
    end

    //--------------------------------------------------------------------------
    // UART core signals
    //--------------------------------------------------------------------------
    wire [7:0]  uart_rx_data;
    wire        uart_rx_ready;
    wire        uart_tx_busy;
    wire        uart_tx_done;
    wire        uart_rx_overflow;

    //--------------------------------------------------------------------------
    // Instantiate UART core
    //--------------------------------------------------------------------------
    uart u_uart (
        .clk       (PCLK),
        .rst_n     (PRESETn),
        .tx_enable (ctrl_tx_enable),
        .rx_enable (ctrl_rx_enable),
        .tx_data   (tx_data_shadow),
        .tx_start  (tx_start_pulse),
        .rx_in     (rx_in),
        .tx_out    (tx_out),
        .rx_data   (uart_rx_data),
        .rx_ready  (uart_rx_ready),
        .rx_read   (rx_read_pulse),
        .tx_busy   (uart_tx_busy),
        .tx_done   (uart_tx_done),
        .rx_overflow(uart_rx_overflow),
        .baud_div  (reg_baud_div)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0:    prdata_reg = {24'd0, tx_data_shadow};  // TX_DATA (echo shadow)
            3'd1:    prdata_reg = {24'd0, uart_rx_data};    // RX_DATA
            3'd2:    prdata_reg = {30'd0, ctrl_rx_enable, ctrl_tx_enable}; // CTRL
            3'd3:    prdata_reg = {28'd0, uart_rx_overflow, uart_rx_ready, ~uart_tx_busy, uart_tx_busy}; // STATUS
            3'd4:    prdata_reg = {16'd0, reg_baud_div};    // BAUD_DIV
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;   // No wait states
    assign PSLVERR = 1'b0;   // No slave errors

    //--------------------------------------------------------------------------
    // IRQ output: level-sensitive, asserted when rx_ready is set
    //--------------------------------------------------------------------------
    assign irq = uart_rx_ready;
    assign rx_overflow = uart_rx_overflow;

endmodule
