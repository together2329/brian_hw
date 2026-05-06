// ============================================================================
// i2c.v — I2C Master Controller (verilog_2001)
// ============================================================================
// SSOT: i2c/yaml/i2c.ssot.yaml
//
// Features:
//   - APB4 slave interface (8-bit address)
//   - I2C master-only: START, STOP, ACK, NACK
//   - 7-bit slave addressing
//   - 8-byte TX FIFO, 8-byte RX FIFO
//   - Standard mode (100kHz) and Fast mode (400kHz)
//   - Interrupts: TX_EMPTY, RX_FULL, ARBITRATION_LOST, NACK_RECEIVED
//   - 100MHz system clock, asynchronous active-low reset
//   - Verilog-2001 dialect
// ============================================================================

module i2c (
    // APB4 slave interface
    input  wire        pclk,
    input  wire        presetn,
    input  wire [7:0]  paddr,
    input  wire        psel,
    input  wire        penable,
    input  wire        pwrite,
    input  wire [31:0] pwdata,
    output reg  [31:0] prdata,
    output reg         pready,
    output reg         pslverr,

    // I2C external interface (open-drain)
    inout  wire        scl,
    inout  wire        sda,

    // Interrupt outputs
    output wire        intr_tx_empty,
    output wire        intr_rx_full,
    output wire        intr_arbitration_lost,
    output wire        intr_nack_received
);

    // ========================================================================
    // Local parameters
    // ========================================================================
    localparam CLK_FREQ       = 100_000_000;
    localparam DIV_STD        = 16'd499;   // 100kHz
    localparam DIV_FAST       = 16'd124;   // 400kHz

    // Register offsets
    localparam ADDR_DATA      = 8'h00;
    localparam ADDR_ADDR      = 8'h04;
    localparam ADDR_STATUS    = 8'h08;
    localparam ADDR_CTRL      = 8'h0C;
    localparam ADDR_CLOCK_DIV = 8'h10;

    // FSM states
    localparam [3:0]
        FSM_IDLE      = 4'd0,
        FSM_START     = 4'd1,
        FSM_ADDR      = 4'd2,
        FSM_ADDR_ACK  = 4'd3,
        FSM_TX_DATA   = 4'd4,
        FSM_TX_ACK    = 4'd5,
        FSM_RX_DATA   = 4'd6,
        FSM_RX_ACK    = 4'd7,
        FSM_STOP      = 4'd8,
        FSM_ARB_LOST  = 4'd9,
        FSM_WAIT      = 4'd10;

    // ========================================================================
    // Reset synchronizer (async assert, sync deassert)
    // ========================================================================
    reg [1:0] reset_sync;
    wire      rst_n_synced;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn)
            reset_sync <= 2'b00;
        else
            reset_sync <= {reset_sync[0], 1'b1};
    end
    assign rst_n_synced = reset_sync[1];

    // ========================================================================
    // Register declarations
    // ========================================================================
    reg [7:0]  data_reg;          // DATA register shadow
    reg [7:0]  addr_reg;          // ADDR register [6:0]=addr, [7]=RW
    reg [15:0] clock_div_reg;     // CLOCK_DIV register
    reg [15:0] clock_div_eff;     // effective divider based on speed

    // CTRL register bit fields
    reg        ctrl_enable;
    reg        ctrl_start;
    reg        ctrl_stop;
    reg        ctrl_ack_en;
    reg        ctrl_speed;
    reg        ctrl_int_tx_empty_en;
    reg        ctrl_int_rx_full_en;
    reg        ctrl_int_arb_lost_en;
    reg        ctrl_int_nack_en;

    // STATUS register latched flags
    reg        status_arbitration_lost;
    reg        status_nack_received;
    reg        status_bus_error;

    // ========================================================================
    // TX FIFO (8 bytes x 8 bits)
    // ========================================================================
    reg [7:0]  tx_fifo [0:7];
    reg [2:0]  tx_wr_ptr;
    reg [2:0]  tx_rd_ptr;
    reg [3:0]  tx_count;
    wire       tx_empty;
    wire       tx_full;
    wire       tx_wr_en;
    wire       tx_rd_en;
    reg  [7:0] tx_rd_data;

    assign tx_empty = (tx_count == 4'd0);
    assign tx_full  = (tx_count == 4'd8);
    assign tx_wr_en = psel && penable && pwrite && (paddr == ADDR_DATA) && !tx_full;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            tx_wr_ptr <= 3'd0;
            tx_rd_ptr <= 3'd0;
            tx_count  <= 4'd0;
        end else if (rst_n_synced) begin
            // Write
            if (tx_wr_en) begin
                tx_fifo[tx_wr_ptr] <= pwdata[7:0];
                tx_wr_ptr <= tx_wr_ptr + 3'd1;
                if (!tx_rd_en)
                    tx_count <= tx_count + 4'd1;
            end
            // Read
            if (tx_rd_en) begin
                tx_rd_ptr <= tx_rd_ptr + 3'd1;
                if (!tx_wr_en)
                    tx_count <= tx_count - 4'd1;
            end
        end
    end

    always @(*) begin
        tx_rd_data = tx_fifo[tx_rd_ptr];
    end

    // ========================================================================
    // RX FIFO (8 bytes x 8 bits)
    // ========================================================================
    reg [7:0]  rx_fifo [0:7];
    reg [2:0]  rx_wr_ptr;
    reg [2:0]  rx_rd_ptr;
    reg [3:0]  rx_count;
    wire       rx_empty;
    wire       rx_full;
    wire       rx_wr_en;
    wire       rx_rd_en;

    assign rx_empty = (rx_count == 4'd0);
    assign rx_full  = (rx_count == 4'd8);
    assign rx_rd_en = psel && penable && !pwrite && (paddr == ADDR_DATA) && !rx_empty;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            rx_wr_ptr <= 3'd0;
            rx_rd_ptr <= 3'd0;
            rx_count  <= 4'd0;
        end else if (rst_n_synced) begin
            // Write from I2C FSM
            if (rx_wr_en) begin
                rx_fifo[rx_wr_ptr] <= rx_shift_reg;
                rx_wr_ptr <= rx_wr_ptr + 3'd1;
                if (!rx_rd_en)
                    rx_count <= rx_count + 4'd1;
            end
            // Read via APB
            if (rx_rd_en) begin
                rx_rd_ptr <= rx_rd_ptr + 3'd1;
                if (!rx_wr_en)
                    rx_count <= rx_count - 4'd1;
            end
        end
    end

    // ========================================================================
    // I2C FSM — Clock Divider
    // ========================================================================
    // Determine effective divider from CTRL.speed and CLOCK_DIV register
    always @(*) begin
        if (ctrl_speed)
            clock_div_eff = DIV_FAST;
        else
            clock_div_eff = clock_div_reg;
    end

    reg [15:0] scl_div_counter;
    wire       scl_tick;        // half-period tick for SCL toggle
    reg        scl_internal;    // internal SCL state
    reg        scl_prev;        // previous SCL for edge detection

    assign scl_tick = (scl_div_counter == clock_div_eff);

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            scl_div_counter <= 16'd0;
            scl_internal    <= 1'b1;
            scl_prev        <= 1'b1;
        end else if (rst_n_synced) begin
            if (scl_div_counter == clock_div_eff) begin
                scl_div_counter <= 16'd0;
                scl_internal    <= ~scl_internal;
            end else begin
                scl_div_counter <= scl_div_counter + 16'd1;
            end
            scl_prev <= scl_internal;
        end
    end

    // SCL edge detection
    wire scl_posedge = (scl_internal && !scl_prev);
    wire scl_negedge = (!scl_internal && scl_prev);

    // ========================================================================
    // I2C FSM — State Machine
    // ========================================================================
    reg [3:0]  fsm_state;
    reg [3:0]  fsm_next;
    reg [3:0]  bit_cnt;
    reg [7:0]  shift_reg;
    reg [7:0]  rx_shift_reg;
    reg        sda_oe;
    reg        scl_oe;
    reg        sda_out;
    reg        scl_out;
    reg        rw_bit;         // captured R/W direction
    reg        start_pending;
    reg        stop_pending;
    reg        tx_rd_en_int;   // internal TX FIFO read
    reg        rx_wr_en_int;   // internal RX FIFO write
    reg        arb_lost_detected;

    // Sampled SDA
    wire sda_in;
    assign sda_in = sda;

    assign tx_rd_en = tx_rd_en_int;
    assign rx_wr_en = rx_wr_en_int;

    // FSM sequential logic
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            fsm_state    <= FSM_IDLE;
            bit_cnt      <= 4'd0;
            shift_reg    <= 8'd0;
            rx_shift_reg <= 8'd0;
            sda_oe       <= 1'b0;
            scl_oe       <= 1'b0;
            sda_out      <= 1'b1;
            scl_out      <= 1'b1;
            rw_bit       <= 1'b0;
            start_pending <= 1'b0;
            stop_pending  <= 1'b0;
            tx_rd_en_int <= 1'b0;
            rx_wr_en_int <= 1'b0;
            arb_lost_detected <= 1'b0;
        end else if (rst_n_synced) begin
            // Default: pulse signals low
            tx_rd_en_int <= 1'b0;
            rx_wr_en_int <= 1'b0;

            case (fsm_state)
                // ------------------------------------------------------------
                FSM_IDLE: begin
                    sda_oe  <= 1'b0;
                    scl_oe  <= 1'b0;
                    sda_out <= 1'b1;
                    scl_out <= 1'b1;
                    bit_cnt <= 4'd0;

                    if (ctrl_enable && (ctrl_start || start_pending)) begin
                        start_pending <= 1'b0;
                        fsm_state <= FSM_START;
                    end else if (ctrl_start && !ctrl_enable) begin
                        // Buffer START until enabled
                        start_pending <= 1'b1;
                    end
                end

                // ------------------------------------------------------------
                FSM_START: begin
                    // START: SDA low, SCL high
                    sda_oe <= 1'b1;
                    sda_out <= 1'b0;
                    scl_oe <= 1'b0;
                    scl_out <= 1'b1;

                    // Wait for SCL to be high, then transition
                    if (scl_posedge) begin
                        // SDA already low while SCL goes high → START complete
                        fsm_state <= FSM_ADDR;
                        bit_cnt   <= 4'd8;  // 8 address bits to send
                        shift_reg <= {addr_reg[6:0], rw_bit};
                    end
                end

                // ------------------------------------------------------------
                FSM_ADDR: begin
                    scl_oe <= 1'b1;  // Drive SCL

                    if (scl_negedge) begin
                        // Update SDA on SCL falling edge
                        sda_out <= shift_reg[7];
                        sda_oe  <= 1'b1;
                        if (bit_cnt == 4'd1) begin
                            // About to shift last bit
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt   <= bit_cnt - 4'd1;
                        end else if (bit_cnt == 4'd0) begin
                            fsm_state <= FSM_ADDR_ACK;
                            bit_cnt   <= 4'd0;
                            sda_oe    <= 1'b0;  // Release SDA for ACK
                        end else begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt   <= bit_cnt - 4'd1;
                        end
                    end

                    // Arbitration check while driving address
                    if (scl_posedge && sda_oe && sda_out && !sda_in) begin
                        arb_lost_detected <= 1'b1;
                        fsm_state <= FSM_ARB_LOST;
                    end
                end

                // ------------------------------------------------------------
                FSM_ADDR_ACK: begin
                    scl_oe <= 1'b1;
                    sda_oe <= 1'b0;  // Release SDA

                    if (scl_posedge) begin
                        if (!sda_in) begin
                            // ACK received
                            if (rw_bit) begin
                                // Read: go to RX_DATA
                                fsm_state <= FSM_RX_DATA;
                                bit_cnt   <= 4'd8;
                            end else begin
                                // Write: need data from TX FIFO
                                if (!tx_empty) begin
                                    tx_rd_en_int <= 1'b1;
                                    // shift_reg will be loaded next cycle
                                    fsm_state <= FSM_TX_DATA;
                                    bit_cnt   <= 4'd8;
                                end else begin
                                    // No data — wait
                                    fsm_state <= FSM_WAIT;
                                end
                            end
                        end else begin
                            // NACK received
                            status_nack_received <= 1'b1;
                            fsm_state <= FSM_STOP;
                        end
                    end
                end

                // ------------------------------------------------------------
                FSM_WAIT: begin
                    scl_oe <= 1'b0;
                    sda_oe <= 1'b0;
                    if (!tx_empty) begin
                        tx_rd_en_int <= 1'b1;
                        fsm_state <= FSM_TX_DATA;
                        bit_cnt   <= 4'd8;
                    end else if (ctrl_stop || stop_pending) begin
                        stop_pending <= 1'b0;
                        fsm_state <= FSM_STOP;
                    end
                end

                // ------------------------------------------------------------
                FSM_TX_DATA: begin
                    scl_oe <= 1'b1;

                    if (scl_negedge) begin
                        // Load TX data on first negedge
                        if (bit_cnt == 4'd8) begin
                            shift_reg <= tx_rd_data;
                        end
                        sda_out <= shift_reg[7];
                        sda_oe  <= 1'b1;
                        if (bit_cnt == 4'd1) begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt   <= bit_cnt - 4'd1;
                        end else if (bit_cnt == 4'd0) begin
                            fsm_state <= FSM_TX_ACK;
                            bit_cnt   <= 4'd0;
                            sda_oe    <= 1'b0;
                        end else begin
                            shift_reg <= {shift_reg[6:0], 1'b0};
                            bit_cnt   <= bit_cnt - 4'd1;
                        end
                    end

                    // Arbitration check
                    if (scl_posedge && sda_oe && sda_out && !sda_in) begin
                        arb_lost_detected <= 1'b1;
                        fsm_state <= FSM_ARB_LOST;
                    end
                end

                // ------------------------------------------------------------
                FSM_TX_ACK: begin
                    scl_oe <= 1'b1;
                    sda_oe <= 1'b0;

                    if (scl_posedge) begin
                        if (!sda_in) begin
                            // ACK received — next byte
                            if (!tx_empty) begin
                                tx_rd_en_int <= 1'b1;
                                fsm_state <= FSM_TX_DATA;
                                bit_cnt   <= 4'd8;
                            end else if (ctrl_stop || stop_pending) begin
                                stop_pending <= 1'b0;
                                fsm_state <= FSM_STOP;
                            end else begin
                                // Wait for more data or STOP
                                fsm_state <= FSM_WAIT;
                            end
                        end else begin
                            // NACK
                            status_nack_received <= 1'b1;
                            fsm_state <= FSM_STOP;
                        end
                    end
                end

                // ------------------------------------------------------------
                FSM_RX_DATA: begin
                    scl_oe <= 1'b1;
                    sda_oe <= 1'b0;  // Release SDA, slave drives

                    if (scl_posedge) begin
                        rx_shift_reg <= {rx_shift_reg[6:0], sda_in};
                        if (bit_cnt == 4'd1) begin
                            bit_cnt <= 4'd0;
                            fsm_state <= FSM_RX_ACK;
                        end else begin
                            bit_cnt <= bit_cnt - 4'd1;
                        end
                    end
                end

                // ------------------------------------------------------------
                FSM_RX_ACK: begin
                    scl_oe <= 1'b1;

                    if (scl_negedge) begin
                        // Drive ACK/NACK
                        sda_oe  <= 1'b1;
                        sda_out <= ~ctrl_ack_en;  // 0=ACK, 1=NACK
                    end

                    if (scl_posedge) begin
                        // Push to RX FIFO if space
                        if (!rx_full) begin
                            rx_wr_en_int <= 1'b1;
                        end
                        sda_oe <= 1'b0;

                        if (!ctrl_ack_en) begin
                            // NACK sent — end read
                            fsm_state <= FSM_STOP;
                        end else begin
                            // ACK sent — continue
                            fsm_state <= FSM_RX_DATA;
                            bit_cnt   <= 4'd8;
                        end
                    end
                end

                // ------------------------------------------------------------
                FSM_STOP: begin
                    // STOP: SDA low→high while SCL high
                    scl_oe <= 1'b0;
                    sda_oe <= 1'b1;
                    sda_out <= 1'b0;

                    if (scl_posedge) begin
                        sda_out <= 1'b1;  // Release SDA while SCL high
                    end

                    // After STOP, go idle
                    if (sda_in && scl_internal) begin
                        sda_oe <= 1'b0;
                        scl_oe <= 1'b0;
                        fsm_state <= FSM_IDLE;
                    end
                end

                // ------------------------------------------------------------
                FSM_ARB_LOST: begin
                    // Release bus
                    sda_oe <= 1'b0;
                    scl_oe <= 1'b0;
                    status_arbitration_lost <= 1'b1;
                    // Wait for software to clear
                    fsm_state <= FSM_IDLE;
                end

                // ------------------------------------------------------------
                default: begin
                    fsm_state <= FSM_IDLE;
                end

            endcase
        end
    end

    // ========================================================================
    // Open-Drain I/O Buffers
    // ========================================================================
    assign scl = scl_oe ? 1'b0 : 1'bz;
    assign sda = sda_oe ? 1'b0 : 1'bz;

    // ========================================================================
    // APB4 Register Read/Write
    // ========================================================================
    wire apb_access = psel && penable;
    wire apb_write  = apb_access && pwrite;
    wire apb_read   = apb_access && !pwrite;

    // Write registers
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            data_reg       <= 8'd0;
            addr_reg       <= 8'd0;
            clock_div_reg  <= DIV_STD;
            ctrl_enable    <= 1'b0;
            ctrl_start     <= 1'b0;
            ctrl_stop      <= 1'b0;
            ctrl_ack_en    <= 1'b1;  // Default: send ACK
            ctrl_speed     <= 1'b0;  // Default: Standard mode
            ctrl_int_tx_empty_en <= 1'b0;
            ctrl_int_rx_full_en  <= 1'b0;
            ctrl_int_arb_lost_en <= 1'b0;
            ctrl_int_nack_en     <= 1'b0;
        end else if (rst_n_synced) begin
            // Self-clearing signals
            ctrl_start <= 1'b0;
            ctrl_stop  <= 1'b0;

            if (apb_write) begin
                case (paddr)
                    ADDR_DATA: begin
                        // Data written via FIFO write enable
                    end
                    ADDR_ADDR: begin
                        addr_reg <= pwdata[7:0];
                    end
                    ADDR_STATUS: begin
                        // STATUS is read-only; writes ignored
                    end
                    ADDR_CTRL: begin
                        ctrl_enable    <= pwdata[0];
                        ctrl_start     <= pwdata[1];
                        ctrl_stop      <= pwdata[2];
                        ctrl_ack_en    <= pwdata[3];
                        ctrl_speed     <= pwdata[4];
                        ctrl_int_tx_empty_en <= pwdata[8];
                        ctrl_int_rx_full_en  <= pwdata[9];
                        ctrl_int_arb_lost_en <= pwdata[10];
                        ctrl_int_nack_en     <= pwdata[11];
                    end
                    ADDR_CLOCK_DIV: begin
                        clock_div_reg <= pwdata[15:0];
                    end
                    default: begin
                        // Invalid address
                    end
                endcase
            end
        end
    end

    // Status flag clear on read
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            status_arbitration_lost <= 1'b0;
            status_nack_received    <= 1'b0;
            status_bus_error        <= 1'b0;
        end else if (rst_n_synced) begin
            if (apb_read && (paddr == ADDR_STATUS)) begin
                status_arbitration_lost <= 1'b0;
                status_nack_received    <= 1'b0;
                status_bus_error        <= 1'b0;
            end
            // Set flags
            if (arb_lost_detected)
                status_arbitration_lost <= 1'b1;
        end
    end

    // Read data
    always @(*) begin
        pready  = 1'b1;
        pslverr = 1'b0;
        prdata  = 32'd0;

        if (apb_read) begin
            case (paddr)
                ADDR_DATA: begin
                    prdata = {24'd0, rx_fifo[rx_rd_ptr]};
                end
                ADDR_ADDR: begin
                    prdata = {24'd0, addr_reg};
                end
                ADDR_STATUS: begin
                    prdata[0] = tx_empty;
                    prdata[1] = tx_full;
                    prdata[2] = rx_empty;
                    prdata[3] = rx_full;
                    prdata[4] = (fsm_state != FSM_IDLE);
                    prdata[5] = status_arbitration_lost;
                    prdata[6] = status_nack_received;
                    prdata[7] = status_bus_error;
                end
                ADDR_CTRL: begin
                    prdata[0]  = ctrl_enable;
                    prdata[1]  = ctrl_start;
                    prdata[2]  = ctrl_stop;
                    prdata[3]  = ctrl_ack_en;
                    prdata[4]  = ctrl_speed;
                    prdata[8]  = ctrl_int_tx_empty_en;
                    prdata[9]  = ctrl_int_rx_full_en;
                    prdata[10] = ctrl_int_arb_lost_en;
                    prdata[11] = ctrl_int_nack_en;
                end
                ADDR_CLOCK_DIV: begin
                    prdata = {16'd0, clock_div_reg};
                end
                default: begin
                    pslverr = 1'b1;
                    prdata  = 32'd0;
                end
            endcase
        end
    end

    // ========================================================================
    // Interrupt Generation
    // ========================================================================
    assign intr_tx_empty        = tx_empty  && ctrl_int_tx_empty_en;
    assign intr_rx_full         = rx_full   && ctrl_int_rx_full_en;
    assign intr_arbitration_lost = status_arbitration_lost && ctrl_int_arb_lost_en;
    assign intr_nack_received    = status_nack_received    && ctrl_int_nack_en;

endmodule
