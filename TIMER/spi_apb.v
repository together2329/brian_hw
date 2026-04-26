
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: spi_apb
// Description: APB3 slave interface wrapping the SPI master core.
//
// Register Map (word-aligned, PADDR[7:0]):
//   Offset 0x00  TX_DATA   W    [7:0] data to transmit (write triggers transfer)
//   Offset 0x04  RX_DATA   R    [7:0] received data (read clears rx_ready)
//   Offset 0x08  CTRL      R/W  [0]=enable, [1]=cpol, [2]=cpha
//   Offset 0x0C  STATUS    R    [0]=busy, [1]=rx_ready
//   Offset 0x10  CLK_DIV   R/W  [15:0] SCK half-period divider
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

module spi_apb (
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

    // SPI serial pins
    input  wire         miso,
    output wire         mosi,
    output wire         sck,
    output wire         cs_n,

    // SPI interrupt output
    output wire         irq
);

    //--------------------------------------------------------------------------
    // Internal register storage
    //--------------------------------------------------------------------------
    reg        ctrl_enable;
    reg        ctrl_cpol;
    reg        ctrl_cpha;
    reg [15:0] reg_clk_div;
    reg [7:0]  tx_data_shadow;
    reg        start_pulse;
    reg        rx_read_pulse;
    reg        rx_ready;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];

    wire sel_tx_data  = (addr_word == 3'd0);
    wire sel_rx_data  = (addr_word == 3'd1);
    wire sel_ctrl     = (addr_word == 3'd2);
    wire sel_status   = (addr_word == 3'd3);
    wire sel_clk_div  = (addr_word == 3'd4);

    // APB write/read strobes
    wire apb_write = PSEL && PENABLE && PWRITE;
    wire apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Register write logic
    //--------------------------------------------------------------------------
    always @(posedge PCLK) begin
        if (!PRESETn) begin
            ctrl_enable   <= 1'b0;
            ctrl_cpol     <= 1'b0;
            ctrl_cpha     <= 1'b0;
            reg_clk_div   <= 16'd2;  // Default: fast
            tx_data_shadow<= 8'd0;
            start_pulse   <= 1'b0;
            rx_read_pulse <= 1'b0;
            rx_ready      <= 1'b0;
        end else begin
            // Auto-clear pulses after one clock
            start_pulse   <= 1'b0;
            rx_read_pulse <= 1'b0;

            // Latch rx_ready from done signal
            if (spi_done) begin
                rx_ready <= 1'b1;
            end

            if (apb_write) begin
                case (addr_word)
                    3'd0: begin // TX_DATA - write triggers transfer
                        tx_data_shadow <= PWDATA[7:0];
                        start_pulse    <= 1'b1;
                    end
                    3'd2: begin // CTRL
                        ctrl_enable <= PWDATA[0];
                        ctrl_cpol   <= PWDATA[1];
                        ctrl_cpha   <= PWDATA[2];
                    end
                    3'd4: begin // CLK_DIV
                        reg_clk_div <= PWDATA[15:0];
                    end
                    // RX_DATA (0x04): read-only
                    // STATUS (0x0C): read-only
                    default: ;
                endcase
            end

            // RX_DATA read clears rx_ready
            if (apb_read && sel_rx_data) begin
                rx_read_pulse <= 1'b1;
                rx_ready      <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // SPI core signals
    //--------------------------------------------------------------------------
    wire [7:0]  spi_rx_data;
    wire        spi_busy;
    wire        spi_done;

    //--------------------------------------------------------------------------
    // Instantiate SPI core
    //--------------------------------------------------------------------------
    spi u_spi (
        .clk      (PCLK),
        .rst_n    (PRESETn),
        .enable   (ctrl_enable),
        .start    (start_pulse),
        .tx_data  (tx_data_shadow),
        .rx_data  (spi_rx_data),
        .busy     (spi_busy),
        .done     (spi_done),
        .miso     (miso),
        .mosi     (mosi),
        .sck      (sck),
        .cs_n     (cs_n),
        .cpol     (ctrl_cpol),
        .cpha     (ctrl_cpha),
        .clk_div  (reg_clk_div)
    );

    //--------------------------------------------------------------------------
    // Read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;  // Default: return 0 for unmapped addresses
        case (addr_word)
            3'd0:    prdata_reg = {24'd0, tx_data_shadow};      // TX_DATA (echo shadow)
            3'd1:    prdata_reg = {24'd0, spi_rx_data};         // RX_DATA
            3'd2:    prdata_reg = {29'd0, ctrl_cpha, ctrl_cpol, ctrl_enable}; // CTRL
            3'd3:    prdata_reg = {30'd0, rx_ready, spi_busy};  // STATUS
            3'd4:    prdata_reg = {16'd0, reg_clk_div};         // CLK_DIV
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;   // No wait states
    assign PSLVERR = 1'b0;   // No slave errors

    //--------------------------------------------------------------------------
    // IRQ output: level-sensitive, asserted when rx_ready
    //--------------------------------------------------------------------------
    assign irq = rx_ready;

endmodule
