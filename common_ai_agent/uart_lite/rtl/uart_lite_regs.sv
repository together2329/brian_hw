// uart_lite_regs.sv — APB-lite register decode, W1C interrupt clear, debug counters
// Implements: registers.register_list, interrupts
// APB-lite slave with combinational PREADY (0 wait states)
// 11 registers: TXDATA, RXDATA, STATUS, CONTROL, INT_MASK, INT_PENDING, INT_CLEAR, DEBUG_*

module uart_lite_regs #(
    parameter integer DATA_WIDTH    = 8,
    parameter integer APB_ADDR_W    = 12,
    parameter integer APB_DATA_W    = 32
) (
    input  logic                      clk,
    input  logic                      rst_n,
    // APB-lite slave interface
    input  logic [APB_ADDR_W-1:0]     PADDR,
    input  logic                      PSEL,
    input  logic                      PENABLE,
    input  logic                      PWRITE,
    input  logic [APB_DATA_W-1:0]     PWDATA,
    input  logic [3:0]                PSTRB,
    output logic [APB_DATA_W-1:0]     PRDATA,
    output logic                      PREADY,
    output logic                      PSLVERR,
    // Live FIFO status from FIFO modules
    input  logic                      tx_empty,
    input  logic                      tx_full,
    input  logic                      rx_empty,
    input  logic                      rx_full,
    // Sticky error event pulses from FSM modules
    input  logic                      frame_err_event,
    input  logic                      parity_err_event,
    input  logic                      rx_overrun_event,
    input  logic                      tx_underrun_event,
    input  logic                      break_det_event,
    // Debug counter event pulses
    input  logic                      tx_byte_done,
    input  logic                      rx_byte_done,
    // CONTROL register outputs
    output logic [15:0]               baud_div,
    output logic                      parity_en,
    output logic                      parity_odd,
    output logic                      stop_bits,
    output logic                      loopback,
    output logic                      break_send,
    output logic [2:0]                data_width,
    // Break self-clear from TX FSM
    input  logic                      break_send_clr,
    // TXDATA/RXDATA FIFO access
    output logic                      tx_fifo_wr,
    output logic [DATA_WIDTH-1:0]     tx_fifo_wr_data,
    input  logic                      tx_fifo_full,
    output logic                      rx_fifo_rd,
    input  logic [DATA_WIDTH-1:0]     rx_fifo_rd_data,
    // Interrupt output
    output logic                      irq_o
);

    // Address decode: word-aligned PADDR[7:2]
    wire [5:0] addr_word;
    assign addr_word = PADDR[7:2];

    localparam [5:0] ADDR_TXDATA          = 6'h0;
    localparam [5:0] ADDR_RXDATA          = 6'h1;
    localparam [5:0] ADDR_STATUS          = 6'h2;
    localparam [5:0] ADDR_CONTROL         = 6'h3;
    localparam [5:0] ADDR_INT_MASK        = 6'h4;
    localparam [5:0] ADDR_INT_PENDING     = 6'h5;
    localparam [5:0] ADDR_INT_CLEAR       = 6'h6;
    localparam [5:0] ADDR_DEBUG_TX_BYTES  = 6'h7;
    localparam [5:0] ADDR_DEBUG_RX_BYTES  = 6'h8;
    localparam [5:0] ADDR_DEBUG_FRAME_ERRS = 6'h9;
    localparam [5:0] ADDR_DEBUG_PARITY_ERRS = 6'hA;

    // Valid address check — all upper address bits must be zero
    wire addr_valid;
    assign addr_valid = (addr_word <= ADDR_DEBUG_PARITY_ERRS) && (PADDR[1:0] == 2'b00)
                        && (PADDR[APB_ADDR_W-1:8] == {(APB_ADDR_W-8){1'b0}});

    // APB access phase detection
    wire apb_access;
    assign apb_access = PSEL && PENABLE;
    wire apb_write;
    assign apb_write = apb_access && PWRITE;
    wire apb_read;
    assign apb_read  = apb_access && !PWRITE;

    // --- CONTROL register fields ---
    logic [15:0] baud_div_reg;
    logic        parity_en_reg;
    logic        parity_odd_reg;
    logic        stop_bits_reg;
    logic        loopback_reg;
    logic        break_send_reg;
    logic [2:0]  data_width_reg;

    // --- INT_MASK register fields ---
    logic        tx_empty_en;
    logic        rx_not_empty_en;
    logic        rx_overrun_en;
    logic        frame_err_en;
    logic        parity_err_en;
    logic        tx_underrun_en;
    logic        break_det_en;

    // --- Sticky status/pending flags (set by event, cleared by W1C) ---
    logic        frame_err_sticky;
    logic        parity_err_sticky;
    logic        rx_overrun_sticky;
    logic        tx_underrun_sticky;
    logic        break_det_sticky;

    // --- Debug counters ---
    logic [31:0] bytes_tx;
    logic [31:0] bytes_rx;
    logic [31:0] frames_errored;
    logic [31:0] parities_errored;

    // --- INT_PENDING level signals ---
    wire tx_empty_pending;
    wire rx_not_empty_pending;
    assign tx_empty_pending       = tx_empty;
    assign rx_not_empty_pending   = !rx_empty;

    // --- W1C clear logic ---
    // W1C clear pulses: combinatorial decode of INT_CLEAR write with bit set
    wire w1c_rx_overrun;
    wire w1c_frame_err;
    wire w1c_parity_err;
    wire w1c_tx_underrun;
    wire w1c_break_det;
    assign w1c_rx_overrun    = apb_write && addr_valid && (addr_word == ADDR_INT_CLEAR) && PWDATA[2];
    assign w1c_frame_err     = apb_write && addr_valid && (addr_word == ADDR_INT_CLEAR) && PWDATA[3];
    assign w1c_parity_err    = apb_write && addr_valid && (addr_word == ADDR_INT_CLEAR) && PWDATA[4];
    assign w1c_tx_underrun   = apb_write && addr_valid && (addr_word == ADDR_INT_CLEAR) && PWDATA[5];
    assign w1c_break_det     = apb_write && addr_valid && (addr_word == ADDR_INT_CLEAR) && PWDATA[6];

    // --- CONTROL register ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            baud_div_reg    <= 16'd0;
            parity_en_reg   <= 1'b0;
            parity_odd_reg  <= 1'b0;
            stop_bits_reg   <= 1'b0;
            loopback_reg    <= 1'b0;
            break_send_reg  <= 1'b0;
            data_width_reg  <= 3'd3;  // default 8 bits per SSOT
        end else begin
            // Write
            if (apb_write && addr_valid && addr_word == ADDR_CONTROL) begin
                if (PSTRB[0]) baud_div_reg[7:0]   <= PWDATA[7:0];
                if (PSTRB[1]) baud_div_reg[15:8]  <= PWDATA[15:8];
                if (PSTRB[2]) begin
                    parity_en_reg   <= PWDATA[16];
                    parity_odd_reg  <= PWDATA[17];
                    stop_bits_reg   <= PWDATA[18];
                    loopback_reg    <= PWDATA[19];
                    break_send_reg  <= PWDATA[20];
                    data_width_reg  <= PWDATA[23:21];
                end
                // PSTRB[3] / PWDATA[31:24]: reserved fields — writes ignored per SSOT policy
                if (PSTRB[3]) begin
                    // Prevent unused warning: reference PWDATA[31:24]
                    if (PWDATA[31:24] == 8'h00) begin end
                end
            end
            // break_send self-clears after TX FSM completes break
            if (break_send_clr)
                break_send_reg <= 1'b0;
        end
    end

    // Drive CONTROL outputs
    assign baud_div   = baud_div_reg;
    assign parity_en  = parity_en_reg;
    assign parity_odd = parity_odd_reg;
    assign stop_bits  = stop_bits_reg;
    assign loopback   = loopback_reg;
    assign break_send = break_send_reg;
    assign data_width = data_width_reg;

    // --- INT_MASK register ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_empty_en       <= 1'b0;
            rx_not_empty_en   <= 1'b0;
            rx_overrun_en     <= 1'b0;
            frame_err_en      <= 1'b0;
            parity_err_en     <= 1'b0;
            tx_underrun_en    <= 1'b0;
            break_det_en      <= 1'b0;
        end else if (apb_write && addr_valid && addr_word == ADDR_INT_MASK) begin
            if (PSTRB[0]) begin
                tx_empty_en     <= PWDATA[0];
                rx_not_empty_en <= PWDATA[1];
                rx_overrun_en   <= PWDATA[2];
                frame_err_en    <= PWDATA[3];
                parity_err_en   <= PWDATA[4];
                tx_underrun_en  <= PWDATA[5];
                break_det_en    <= PWDATA[6];
            end
        end
    end

    // --- Sticky flags ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            frame_err_sticky    <= 1'b0;
            parity_err_sticky   <= 1'b0;
            rx_overrun_sticky   <= 1'b0;
            tx_underrun_sticky  <= 1'b0;
            break_det_sticky    <= 1'b0;
        end else begin
            // Set on event pulses
            if (frame_err_event)    frame_err_sticky   <= 1'b1;
            if (parity_err_event)   parity_err_sticky  <= 1'b1;
            if (rx_overrun_event)   rx_overrun_sticky  <= 1'b1;
            if (tx_underrun_event)  tx_underrun_sticky <= 1'b1;
            if (break_det_event)    break_det_sticky   <= 1'b1;
            // Clear on W1C
            if (w1c_frame_err)      frame_err_sticky   <= 1'b0;
            if (w1c_parity_err)     parity_err_sticky  <= 1'b0;
            if (w1c_rx_overrun)     rx_overrun_sticky  <= 1'b0;
            if (w1c_tx_underrun)    tx_underrun_sticky <= 1'b0;
            if (w1c_break_det)      break_det_sticky   <= 1'b0;
        end
    end

    // --- Debug counters ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bytes_tx        <= 32'd0;
            bytes_rx        <= 32'd0;
            frames_errored  <= 32'd0;
            parities_errored <= 32'd0;
        end else begin
            if (tx_byte_done)    bytes_tx        <= bytes_tx + 32'd1;
            if (rx_byte_done)    bytes_rx        <= bytes_rx + 32'd1;
            if (frame_err_event) frames_errored  <= frames_errored + 32'd1;
            if (parity_err_event) parities_errored <= parities_errored + 32'd1;
        end
    end

    // Helper wire for TX FIFO write data — avoid parameterized part-select in procedural block
    wire [DATA_WIDTH-1:0] pwd_data_lsb;
    assign pwd_data_lsb = PWDATA[DATA_WIDTH-1:0];

    // --- TXDATA write: push byte to TX FIFO ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_fifo_wr      <= 1'b0;
            tx_fifo_wr_data <= {DATA_WIDTH{1'b0}};
        end else begin
            // Write to TXDATA pushes byte into TX FIFO if not full
            tx_fifo_wr <= apb_write && addr_valid && (addr_word == ADDR_TXDATA) && !tx_fifo_full;
            if (apb_write && addr_valid && (addr_word == ADDR_TXDATA))
                tx_fifo_wr_data <= pwd_data_lsb;
        end
    end

    // --- RXDATA read: pop byte from RX FIFO ---
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_fifo_rd <= 1'b0;
        end else begin
            // Read from RXDATA pops byte from RX FIFO if not empty
            rx_fifo_rd <= apb_read && addr_valid && (addr_word == ADDR_RXDATA) && !rx_empty;
        end
    end

    // --- APB read mux ---
    // Precompute read data words for each register
    wire [31:0] rd_txdata;
    assign rd_txdata = { {32-DATA_WIDTH{1'b0}}, {DATA_WIDTH{1'b0}} };  // WO register reads 0

    wire [31:0] rd_rxdata;
    assign rd_rxdata = { {32-DATA_WIDTH{1'b0}}, rx_fifo_rd_data };  // Data read from RX FIFO

    wire [31:0] rd_status;
    // STATUS layout per SSOT
    assign rd_status = {23'd0,
                        break_det_sticky,   // [8]
                        tx_underrun_sticky, // [7]
                        rx_overrun_sticky,  // [6]
                        parity_err_sticky,  // [5]
                        frame_err_sticky,   // [4]
                        rx_full,            // [3]
                        rx_empty,           // [2]
                        tx_full,            // [1]
                        tx_empty};          // [0]

    wire [31:0] rd_control;
    assign rd_control = {8'd0,                           // [31:24] reserved
                         data_width_reg,                  // [23:21]
                         break_send_reg,                  // [20]
                         loopback_reg,                    // [19]
                         stop_bits_reg,                   // [18]
                         parity_odd_reg,                  // [17]
                         parity_en_reg,                   // [16]
                         baud_div_reg};                   // [15:0]

    wire [31:0] rd_int_mask;
    assign rd_int_mask = {25'd0,
                          break_det_en,     // [6]
                          tx_underrun_en,   // [5]
                          parity_err_en,    // [4]
                          frame_err_en,     // [3]
                          rx_overrun_en,    // [2]
                          rx_not_empty_en,  // [1]
                          tx_empty_en};     // [0]

    wire [31:0] rd_int_pending;
    assign rd_int_pending = {25'd0,
                             break_det_sticky,       // [6]
                             tx_underrun_sticky,     // [5]
                             parity_err_sticky,      // [4]
                             frame_err_sticky,       // [3]
                             rx_overrun_sticky,      // [2]
                             rx_not_empty_pending,   // [1]
                             tx_empty_pending};      // [0]

    wire [31:0] rd_int_clear;
    assign rd_int_clear = 32'd0;  // WO register reads 0

    // Read mux
    always @(*) begin
        PRDATA = 32'd0;
        if (apb_read && addr_valid) begin
            case (addr_word)
                ADDR_TXDATA:           PRDATA = rd_txdata;
                ADDR_RXDATA:           PRDATA = rd_rxdata;
                ADDR_STATUS:           PRDATA = rd_status;
                ADDR_CONTROL:          PRDATA = rd_control;
                ADDR_INT_MASK:         PRDATA = rd_int_mask;
                ADDR_INT_PENDING:      PRDATA = rd_int_pending;
                ADDR_INT_CLEAR:        PRDATA = rd_int_clear;
                ADDR_DEBUG_TX_BYTES:   PRDATA = bytes_tx;
                ADDR_DEBUG_RX_BYTES:   PRDATA = bytes_rx;
                ADDR_DEBUG_FRAME_ERRS: PRDATA = frames_errored;
                ADDR_DEBUG_PARITY_ERRS: PRDATA = parities_errored;
                default:               PRDATA = 32'd0;
            endcase
        end
    end

    // --- APB control outputs ---
    // PREADY: combinational — assert in access phase for valid address
    assign PREADY = apb_access && addr_valid;

    // PSLVERR: assert only with PREADY for invalid addresses
    assign PSLVERR = apb_access && !addr_valid;

    // --- Interrupt aggregation ---
    wire [6:0] int_pending_vec;
    wire [6:0] int_mask_vec;
    assign int_pending_vec = {break_det_sticky,
                              tx_underrun_sticky,
                              parity_err_sticky,
                              frame_err_sticky,
                              rx_overrun_sticky,
                              rx_not_empty_pending,
                              tx_empty_pending};
    assign int_mask_vec = {break_det_en,
                           tx_underrun_en,
                           parity_err_en,
                           frame_err_en,
                           rx_overrun_en,
                           rx_not_empty_en,
                           tx_empty_en};

    assign irq_o = |(int_pending_vec & int_mask_vec);

endmodule
