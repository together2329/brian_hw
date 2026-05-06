// =============================================================================
// uart_core.sv — UART integration core (LLM-written glue logic)
// =============================================================================
// Instantiates and wires:
//   uart_regs   — APB4 register decode
//   uart_baud   — baud-rate tick generator
//   uart_tx     — transmitter with TX FIFO
//   uart_rx     — receiver with RX FIFO
// Generates combined interrupt output.
// =============================================================================

module uart_core #(
    parameter integer DATA_WIDTH     = 8,
    parameter integer BAUD_DIV       = 16,
    parameter integer FIFO_DEPTH     = 16,
    parameter integer APB_ADDR_WIDTH = 4,
    parameter bit     HAS_IRQ        = 1'b1
) (
    input  logic                          clk,
    input  logic                          rst_n,

    // APB4 slave interface
    input  logic [APB_ADDR_WIDTH-1:0]     paddr,
    input  logic                          psel,
    input  logic                          penable,
    input  logic                          pwrite,
    input  logic [31:0]                   pwdata,
    output logic [31:0]                   prdata,
    output logic                          pready,
    output logic                          pslverr,

    // UART serial pins
    output logic                          tx_o,
    input  logic                          rx_i,

    // Interrupt
    output logic                          irq_o
);

    // ========================================================================
    // Internal wires — control from register file
    // ========================================================================
    logic       tx_en;
    logic       rx_en;
    logic       fifo_en;
    logic       parity_en;
    logic       parity_odd;
    logic       stop_bits;
    logic [7:0] baud_div;

    // ========================================================================
    // Internal wires — TX data interface
    // ========================================================================
    logic       tx_push;
    logic [7:0] tx_data;

    // ========================================================================
    // Internal wires — RX data interface
    // ========================================================================
    logic       rx_pop;
    logic [7:0] rx_data;
    logic       rx_valid;

    // ========================================================================
    // Internal wires — status from TX/RX
    // ========================================================================
    logic       tx_empty;
    logic       tx_full;
    logic       rx_empty;
    logic       rx_full;
    logic       tx_busy;
    logic       rx_busy;
    logic       framing_err;
    logic       overrun_err;

    // ========================================================================
    // Internal wires — baud tick
    // ========================================================================
    logic       baud_tick;

    // ========================================================================
    // Internal wires — error clear
    // ========================================================================
    logic       err_clear;

    // ========================================================================
    // Module instantiation — uart_regs
    // ========================================================================
    uart_regs #(
        .APB_ADDR_WIDTH (APB_ADDR_WIDTH)
    ) u_regs (
        .clk          (clk),
        .rst_n        (rst_n),

        // APB interface
        .paddr        (paddr),
        .psel         (psel),
        .penable      (penable),
        .pwrite       (pwrite),
        .pwdata       (pwdata),
        .prdata       (prdata),
        .pready       (pready),
        .pslverr      (pslverr),

        // Control outputs
        .tx_en_o      (tx_en),
        .rx_en_o      (rx_en),
        .fifo_en_o    (fifo_en),
        .parity_en_o  (parity_en),
        .parity_odd_o (parity_odd),
        .stop_bits_o  (stop_bits),
        .baud_div_o   (baud_div),

        // TX data
        .tx_push_o    (tx_push),
        .tx_data_o    (tx_data),

        // RX data
        .rx_pop_o     (rx_pop),
        .rx_data_i    (rx_data),
        .rx_valid_i   (rx_valid),

        // Status inputs
        .tx_empty_i   (tx_empty),
        .tx_full_i    (tx_full),
        .rx_empty_i   (rx_empty),
        .rx_full_i    (rx_full),
        .tx_busy_i    (tx_busy),
        .rx_busy_i    (rx_busy),
        .framing_err_i(framing_err),
        .overrun_err_i(overrun_err),

        // Error clear
        .err_clear_o  (err_clear)
    );

    // ========================================================================
    // Module instantiation — uart_baud
    // ========================================================================
    uart_baud #(
        .BAUD_DIV (BAUD_DIV)
    ) u_baud (
        .clk         (clk),
        .rst_n       (rst_n),
        .baud_div_i  (baud_div),
        .baud_tick_o (baud_tick)
    );

    // ========================================================================
    // Module instantiation — uart_tx
    // ========================================================================
    uart_tx #(
        .DATA_WIDTH (DATA_WIDTH),
        .FIFO_DEPTH (FIFO_DEPTH)
    ) u_tx (
        .clk           (clk),
        .rst_n         (rst_n),

        .baud_tick_i   (baud_tick),

        .tx_en_i       (tx_en),
        .fifo_en_i     (fifo_en),
        .parity_en_i   (parity_en),
        .parity_odd_i  (parity_odd),
        .stop_bits_i   (stop_bits),

        .tx_push_i     (tx_push),
        .tx_data_i     (tx_data),

        .tx_empty_o    (tx_empty),
        .tx_full_o     (tx_full),
        .tx_busy_o     (tx_busy),

        .tx_o          (tx_o)
    );

    // ========================================================================
    // Module instantiation — uart_rx
    // ========================================================================
    uart_rx #(
        .DATA_WIDTH (DATA_WIDTH),
        .FIFO_DEPTH (FIFO_DEPTH)
    ) u_rx (
        .clk           (clk),
        .rst_n         (rst_n),

        .rx_en_i       (rx_en),
        .fifo_en_i     (fifo_en),
        .parity_en_i   (parity_en),
        .parity_odd_i  (parity_odd),
        .stop_bits_i   (stop_bits),

        .baud_div_i    (baud_div),

        .rx_pop_i      (rx_pop),
        .rx_data_o     (rx_data),
        .rx_valid_o    (rx_valid),

        .rx_empty_o    (rx_empty),
        .rx_full_o     (rx_full),
        .rx_busy_o     (rx_busy),
        .framing_err_o (framing_err),
        .overrun_err_o (overrun_err),

        .err_clear_i   (err_clear),

        .rx_i          (rx_i)
    );

    // ========================================================================
    // Interrupt generation — simple OR of active sources
    //   Bit 0: RX FIFO not empty
    //   Bit 2: Framing error
    //   Bit 3: Overrun error
    // TX empty interrupt omitted (would fire constantly at idle).
    // Full INT_ENABLE masking can be added in a later revision.
    // ========================================================================
    always_comb begin
        if (HAS_IRQ) begin
            irq_o = (~rx_empty) | framing_err | overrun_err;
        end else begin
            irq_o = 1'b0;
        end
    end

endmodule
