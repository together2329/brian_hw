// =============================================================================
// uart_regs.sv — APB4 register decode and read-back
// =============================================================================
// Register map (word-aligned, paddr[3:2] selects register):
//   0x00 CTRL    R/W  [0] tx_en, [1] rx_en, [2] fifo_en, [3] parity_en,
//                     [4] parity_odd, [5] stop_bits, [15:8] baud_div
//   0x04 STATUS  RO   [0] tx_empty, [1] tx_full, [2] rx_empty, [3] rx_full,
//                     [4] tx_busy, [5] rx_busy, [6] framing_err, [7] overrun_err
//   0x08 TX_DATA WO   [7:0] tx_data (push into TX FIFO)
//   0x0C RX_DATA RO   [7:0] rx_data, [8] rx_valid (pop from RX FIFO)
// =============================================================================

module uart_regs #(
    parameter integer APB_ADDR_WIDTH = 4
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

    // Control outputs (from CTRL register)
    output logic                          tx_en_o,
    output logic                          rx_en_o,
    output logic                          fifo_en_o,
    output logic                          parity_en_o,
    output logic                          parity_odd_o,
    output logic                          stop_bits_o,
    output logic [7:0]                    baud_div_o,

    // TX data interface
    output logic                          tx_push_o,
    output logic [7:0]                    tx_data_o,

    // RX data interface
    output logic                          rx_pop_o,
    input  logic [7:0]                    rx_data_i,
    input  logic                          rx_valid_i,

    // Status inputs (from TX/RX modules)
    input  logic                          tx_empty_i,
    input  logic                          tx_full_i,
    input  logic                          rx_empty_i,
    input  logic                          rx_full_i,
    input  logic                          tx_busy_i,
    input  logic                          rx_busy_i,
    input  logic                          framing_err_i,
    input  logic                          overrun_err_i,

    // Error clear output (pulses on STATUS read)
    output logic                          err_clear_o
);

    // ========================================================================
    // Address decode — word-aligned, use upper 2 bits of 4-bit address
    // ========================================================================
    logic [1:0] reg_sel;
    assign reg_sel = paddr[3:2];

    localparam logic [1:0] REG_CTRL    = 2'd0,
                           REG_STATUS  = 2'd1,
                           REG_TX_DATA = 2'd2,
                           REG_RX_DATA = 2'd3;

    // APB access phase qualification
    logic apb_access;
    logic apb_write;
    logic apb_read;

    assign apb_access = psel & penable;
    assign apb_write  = apb_access & pwrite;
    assign apb_read   = apb_access & ~pwrite;

    // ========================================================================
    // CTRL register — R/W
    // ========================================================================
    logic [31:0] ctrl_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctrl_q <= 32'h0000_1000;   // baud_div = 16 default
        end else begin
            if (apb_write && (reg_sel == REG_CTRL)) begin
                ctrl_q <= pwdata;
            end
        end
    end

    // Control field extractions
    assign tx_en_o       = ctrl_q[0];
    assign rx_en_o       = ctrl_q[1];
    assign fifo_en_o     = ctrl_q[2];
    assign parity_en_o   = ctrl_q[3];
    assign parity_odd_o  = ctrl_q[4];
    assign stop_bits_o   = ctrl_q[5];
    assign baud_div_o    = ctrl_q[15:8];

    // ========================================================================
    // TX_DATA write — push pulse generation
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_push_o <= 1'b0;
        end else begin
            tx_push_o <= apb_write && (reg_sel == REG_TX_DATA) && !tx_full_i;
        end
    end

    assign tx_data_o = pwdata[7:0];

    // ========================================================================
    // RX_DATA read — pop pulse generation
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_pop_o <= 1'b0;
        end else begin
            rx_pop_o <= apb_read && (reg_sel == REG_RX_DATA);
        end
    end

    // ========================================================================
    // Error clear — pulse on STATUS register read
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            err_clear_o <= 1'b0;
        end else begin
            err_clear_o <= apb_read && (reg_sel == REG_STATUS);
        end
    end

    // ========================================================================
    // Read data mux
    // ========================================================================
    always_comb begin
        prdata = 32'h0000_0000;
        case (reg_sel)
            REG_CTRL: begin
                prdata = ctrl_q;
            end
            REG_STATUS: begin
                prdata[0] = tx_empty_i;
                prdata[1] = tx_full_i;
                prdata[2] = rx_empty_i;
                prdata[3] = rx_full_i;
                prdata[4] = tx_busy_i;
                prdata[5] = rx_busy_i;
                prdata[6] = framing_err_i;
                prdata[7] = overrun_err_i;
            end
            REG_TX_DATA: begin
                prdata = 32'h0000_0000;   // write-only
            end
            REG_RX_DATA: begin
                prdata[7:0] = rx_data_i;
                prdata[8]   = rx_valid_i;
            end
            default: begin
                prdata = 32'h0000_0000;
            end
        endcase
    end

    // ========================================================================
    // pready — insert wait states when TX FIFO full on TX_DATA write
    // ========================================================================
    always_comb begin
        pready = 1'b1;   // default: zero wait states
        if (apb_write && (reg_sel == REG_TX_DATA) && tx_full_i) begin
            pready = 1'b0;   // stall until FIFO has space
        end
    end

    // ========================================================================
    // pslverr — no slave errors in this implementation
    // ========================================================================
    assign pslverr = 1'b0;

endmodule
