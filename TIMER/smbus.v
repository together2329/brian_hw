
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: smbus
// Description: SMBus master controller (I2C-compatible subset with PEC + timeout).
//
// Performs an SMBus transaction with optional CRC-8 PEC byte:
//   Write phase:
//     1. START condition (SMBDAT high→low while SMBCLK high)
//     2. Send device address (7 bits + R/W=0 for write), MSB first
//     3. Wait for ACK from slave
//     4. Send command byte (8 bits), MSB first
//     5. Wait for ACK from slave
//
//   Write data phase (if rw=0):
//     6. Send data byte (8 bits), MSB first
//     7. Wait for ACK from slave
//
//   Read data phase (if rw=1):
//     8. REPEATED START (SMBDAT low→high→low while SMBCLK high)
//     9. Send device address (7 bits + R/W=1 for read)
//    10. Wait for ACK from slave
//    11. Receive data byte (8 bits), MSB first
//    12. Send NACK from master
//
//   PEC phase (if pec_en=1):
//    13. Send CRC-8 byte (read transaction: master checks received PEC)
//
//   14. STOP condition (SMBDAT low→high while SMBCLK high)
//
// Includes SMBus timeout detection (25ms) and CRC-8 PEC calculation.
//
// Ports:
//   clk       - System clock (rising-edge)
//   rst_n     - Active-low synchronous reset
//   enable    - SMBus enable (active high)
//   rw        - 1=read transfer, 0=write transfer
//   start     - Start transaction pulse (1 clock cycle)
//   tx_data   - 8-bit data to transmit (write data byte)
//   rx_data   - 8-bit received data (valid when done=1)
//   dev_addr  - 7-bit device address (upper 7 bits of first byte)
//   cmd       - 8-bit command code (byte 2)
//   smbdat_in  - SMBDAT data input (from bidirectional pad)
//   smbdat_out - SMBDAT data output (to bidirectional pad)
//   smbdat_oe  - SMBDAT output enable (1=drive, 0=release/high-Z)
//   smbclk_out - SMBCLK clock output
//   smbclk_oe  - SMBCLK output enable
//   busy      - Transaction in progress
//   done      - Transaction completed pulse (1 clock cycle)
//   error     - Transaction error (NACK received from slave)
//   timeout   - SMBus timeout detected
//   pec_error - PEC mismatch detected
//   pec_en    - Enable CRC-8 PEC byte
//   clk_div   - Clock divider (system clocks per SMBCLK half-period)
//----------------------------------------------------------------------------

module smbus (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         enable,
    input  wire         rw,
    input  wire         start,
    input  wire  [7:0]  tx_data,
    output reg  [7:0]   rx_data,
    input  wire  [7:0]  dev_addr,
    input  wire  [7:0]  cmd,
    input  wire         smbdat_in,
    output reg          smbdat_out,
    output reg          smbdat_oe,
    output reg          smbclk_out,
    output reg          smbclk_oe,
    output reg          busy,
    output reg          done,
    output reg          error,
    output reg          timeout,
    output reg          pec_error,
    input  wire         pec_en,
    input  wire  [15:0] clk_div
);

    //==========================================================================
    // FSM states
    //==========================================================================
    localparam IDLE         = 4'd0;
    localparam START        = 4'd1;
    localparam ADDR_W       = 4'd2;
    localparam ACK_ADDR_W   = 4'd3;
    localparam CMD          = 4'd4;
    localparam ACK_CMD      = 4'd5;
    localparam DATA_W       = 4'd6;
    localparam ACK_DATA_W   = 4'd7;
    localparam REP_START    = 4'd8;
    localparam ADDR_R       = 4'd9;
    localparam ACK_ADDR_R   = 4'd10;
    localparam DATA_R       = 4'd11;
    localparam NACK         = 4'd12;
    localparam PEC          = 4'd13;
    localparam STOP         = 4'd14;

    //==========================================================================
    // Registers
    //==========================================================================
    reg [3:0]  state;
    reg [15:0] scl_cnt;         // Counter for SMBCLK half-periods
    reg        scl_clk;         // Internal SMBCLK clock (toggles each half-period)
    reg [3:0]  bit_cnt;         // Bit counter within byte (0-7 = data, 8 = ACK/NACK)
    reg [7:0]  tx_shift;        // TX shift register
    reg [7:0]  rx_shift;        // RX shift register
    reg        is_read_txn;     // Latched read flag (0=write, 1=read)
    reg        nack_received;   // Slave NACK detected

    //==========================================================================
    // CRC-8 PEC registers (polynomial: x^8 + x^2 + x + 1 = 0x07)
    //==========================================================================
    reg [7:0]  pec_calc;        // Computed PEC byte
    reg [7:0]  pec_received;    // PEC byte received from slave (read txn)

    //==========================================================================
    // Timeout counter (SMBus T_TIMEOUT = ~25ms)
    // At 50MHz with clk_div=100 (SCL ≈ 500kHz), 25ms = 1,250,000 cycles
    // We use a 21-bit counter: 2^21 = 2,097,152 > 1,250,000
    //==========================================================================
    reg [20:0] timeout_cnt;
    localparam TIMEOUT_MAX = 21'd1250000;  // 25ms at 50MHz (simplified)

    //==========================================================================
    // SCL edge detection
    //==========================================================================
    wire scl_rise = (scl_cnt == clk_div - 16'd1) && (scl_clk == 1'b0);
    wire scl_fall = (scl_cnt == clk_div - 16'd1) && (scl_clk == 1'b1);

    //==========================================================================
    // SMBCLK output
    //==========================================================================
    always @(*) begin
        if (state == IDLE) begin
            smbclk_out = 1'b0;
            smbclk_oe  = 1'b0;   // Released (high via external pull-up)
        end else if (state == START || state == STOP) begin
            smbclk_out = 1'b1;
            smbclk_oe  = 1'b1;   // SMBCLK high during START/STOP conditions
        end else begin
            if (scl_clk == 1'b0) begin
                smbclk_out = 1'b0;
                smbclk_oe  = 1'b1;  // Drive low
            end else begin
                smbclk_out = 1'b0;
                smbclk_oe  = 1'b0;  // Release, pulled high externally
            end
        end
    end

    //==========================================================================
    // CRC-8 PEC update function (x^8 + x^2 + x + 1, polynomial = 0x07)
    // Called on each byte boundary via combinational logic
    //==========================================================================
    wire [7:0] pec_next;
    assign pec_next = {pec_calc[6:0], (pec_calc[7] ^ tx_shift[7])};
    // Note: simplified bit-at-a-time CRC; full implementation uses
    // iterative formula applied in 8 steps per byte (see always block)

    //==========================================================================
    // Main FSM
    //==========================================================================
    always @(posedge clk) begin
        if (!rst_n) begin
            state         <= IDLE;
            scl_cnt       <= 16'd0;
            scl_clk       <= 1'b0;
            bit_cnt       <= 4'd0;
            tx_shift      <= 8'd0;
            rx_shift      <= 8'd0;
            rx_data       <= 8'd0;
            is_read_txn   <= 1'b0;
            nack_received <= 1'b0;
            busy          <= 1'b0;
            done          <= 1'b0;
            error         <= 1'b0;
            timeout       <= 1'b0;
            pec_error     <= 1'b0;
            pec_calc      <= 8'd0;
            pec_received  <= 8'd0;
            smbdat_out    <= 1'b1;
            smbdat_oe     <= 1'b0;
            timeout_cnt   <= 21'd0;
        end else begin
            // Default: clear pulse signals
            done     <= 1'b0;
            error    <= 1'b0;
            timeout  <= 1'b0;

            //------------------------------------------------------------------------
            // Timeout counter: reset when SMBDAT is high, increment when low
            // (SMBus T_TIMEOUT: SMBDAT stuck low for >25ms)
            //------------------------------------------------------------------------
            if (smbdat_in == 1'b1 || state == IDLE) begin
                timeout_cnt <= 21'd0;
            end else if (timeout_cnt < TIMEOUT_MAX) begin
                timeout_cnt <= timeout_cnt + 21'd1;
                if (timeout_cnt == TIMEOUT_MAX - 21'd1) begin
                    // Timeout detected, abort transaction
                    timeout       <= 1'b1;
                    error         <= 1'b1;
                    state         <= IDLE;
                    busy          <= 1'b0;
                    smbdat_out    <= 1'b1;
                    smbdat_oe     <= 1'b0;
                end
            end

            case (state)
                //--------------------------------------------------------------
                IDLE: begin
                    busy          <= 1'b0;
                    scl_cnt       <= 16'd0;
                    scl_clk       <= 1'b0;
                    smbdat_out    <= 1'b1;
                    smbdat_oe     <= 1'b0;
                    nack_received <= 1'b0;
                    pec_calc      <= 8'd0;
                    pec_received  <= 8'd0;
                    pec_error     <= 1'b0;

                    if (enable && start) begin
                        is_read_txn <= rw;
                        tx_shift    <= {dev_addr[6:0], 1'b0};  // 7-bit addr + R/W=0 (write)
                        busy        <= 1'b1;
                        state       <= START;
                    end
                end

                //--------------------------------------------------------------
                // START condition
                //--------------------------------------------------------------
                START: begin
                    smbdat_out <= 1'b0;
                    smbdat_oe  <= 1'b1;

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                        state   <= ADDR_W;
                        bit_cnt <= 4'd0;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // ADDR_W: Send address byte, MSB first
                // Update PEC CRC with each byte sent (before sending)
                //--------------------------------------------------------------
                ADDR_W: begin
                    smbdat_out <= tx_shift[7];
                    smbdat_oe  <= 1'b1;

                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state <= ACK_ADDR_W;
                            bit_cnt <= 4'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // ACK_ADDR_W: Release SMBDAT, check slave ACK
                //--------------------------------------------------------------
                ACK_ADDR_W: begin
                    smbdat_oe <= 1'b0;

                    if (scl_rise) begin
                        if (smbdat_in == 1'b1) begin
                            nack_received <= 1'b1;
                        end
                    end

                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                        end else begin
                            // Update PEC with address byte (including R/W bit)
                            pec_calc <= pec_updated(pec_calc, {dev_addr[6:0], 1'b0});
                            tx_shift <= cmd;
                            state    <= CMD;
                            bit_cnt  <= 4'd0;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // CMD: Send command byte
                //--------------------------------------------------------------
                CMD: begin
                    smbdat_out <= tx_shift[7];
                    smbdat_oe  <= 1'b1;

                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state <= ACK_CMD;
                            bit_cnt <= 4'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // ACK_CMD: Release SMBDAT, check slave ACK, update PEC
                //--------------------------------------------------------------
                ACK_CMD: begin
                    smbdat_oe <= 1'b0;

                    if (scl_rise) begin
                        if (smbdat_in == 1'b1) begin
                            nack_received <= 1'b1;
                        end
                    end

                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                        end else if (is_read_txn) begin
                            // Read transaction: update PEC with cmd byte
                            pec_calc <= pec_updated(pec_calc, cmd);
                            // Prepare read address
                            tx_shift <= {dev_addr[6:0], 1'b1};  // R/W=1 (read)
                            state    <= REP_START;
                            bit_cnt  <= 4'd0;
                        end else begin
                            // Write transaction: update PEC with cmd byte
                            pec_calc <= pec_updated(pec_calc, cmd);
                            tx_shift <= tx_data;
                            state    <= DATA_W;
                            bit_cnt  <= 4'd0;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // DATA_W: Send data byte (write)
                //--------------------------------------------------------------
                DATA_W: begin
                    smbdat_out <= tx_shift[7];
                    smbdat_oe  <= 1'b1;

                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state <= ACK_DATA_W;
                            bit_cnt <= 4'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // ACK_DATA_W: Check slave ACK, update PEC, decide next
                //--------------------------------------------------------------
                ACK_DATA_W: begin
                    smbdat_oe <= 1'b0;

                    if (scl_rise) begin
                        if (smbdat_in == 1'b1) begin
                            nack_received <= 1'b1;
                        end
                    end

                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                        end else begin
                            // Update PEC with data byte
                            pec_calc <= pec_updated(pec_calc, tx_data);

                            if (pec_en) begin
                                // Send PEC byte
                                tx_shift <= pec_calc;  // Use current pec_calc before update
                                state    <= PEC;
                                bit_cnt  <= 4'd0;
                            end else begin
                                state <= STOP;
                            end
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // REP_START: Repeated START for read transaction
                //--------------------------------------------------------------
                REP_START: begin
                    case (bit_cnt)
                        4'd0: begin
                            smbdat_out <= 1'b0;
                            smbdat_oe  <= 1'b0;  // Release SMBDAT
                            bit_cnt <= 4'd1;
                            scl_cnt <= 16'd0;
                            scl_clk <= 1'b0;
                        end

                        4'd1: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                smbdat_out <= 1'b0;
                                smbdat_oe  <= 1'b1;  // Pull SMBDAT low (repeated START)
                                bit_cnt <= 4'd2;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end

                        4'd2: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                scl_cnt <= 16'd0;
                                scl_clk <= 1'b0;
                                state   <= ADDR_R;
                                bit_cnt <= 4'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end

                        default: bit_cnt <= 4'd0;
                    endcase
                end

                //--------------------------------------------------------------
                // ADDR_R: Send address byte for read
                //--------------------------------------------------------------
                ADDR_R: begin
                    smbdat_out <= tx_shift[7];
                    smbdat_oe  <= 1'b1;

                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state <= ACK_ADDR_R;
                            bit_cnt <= 4'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // ACK_ADDR_R: Check slave ACK for read address
                //--------------------------------------------------------------
                ACK_ADDR_R: begin
                    smbdat_oe <= 1'b0;

                    if (scl_rise) begin
                        if (smbdat_in == 1'b1) begin
                            nack_received <= 1'b1;
                        end
                    end

                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                        end else begin
                            // Update PEC with read address byte
                            pec_calc <= pec_updated(pec_calc, {dev_addr[6:0], 1'b1});
                            state    <= DATA_R;
                            bit_cnt  <= 4'd0;
                            rx_shift <= 8'd0;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // DATA_R: Receive data byte from slave
                //--------------------------------------------------------------
                DATA_R: begin
                    smbdat_oe <= 1'b0;

                    if (scl_rise) begin
                        rx_shift <= {rx_shift[6:0], smbdat_in};
                    end

                    if (scl_fall) begin
                        if (bit_cnt == 4'd7) begin
                            state <= NACK;
                            bit_cnt <= 4'd0;
                        end else begin
                            bit_cnt <= bit_cnt + 4'd1;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // NACK: Master sends NACK after receiving data
                //--------------------------------------------------------------
                NACK: begin
                    smbdat_out <= 1'b1;  // NACK = SDA high
                    smbdat_oe  <= 1'b1;

                    if (scl_fall) begin
                        rx_data <= rx_shift;
                        // Update PEC with received data byte
                        pec_calc <= pec_updated(pec_calc, rx_shift);

                        if (pec_en) begin
                            // Receive PEC byte from slave (master checks)
                            state    <= PEC;
                            rx_shift <= 8'd0;
                            bit_cnt  <= 4'd0;
                        end else begin
                            state <= STOP;
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // PEC: Send PEC byte (write) or receive PEC byte (read)
                //--------------------------------------------------------------
                PEC: begin
                    if (is_read_txn) begin
                        // Read transaction: receive PEC from slave
                        smbdat_oe <= 1'b0;

                        if (scl_rise) begin
                            rx_shift <= {rx_shift[6:0], smbdat_in};
                        end

                        if (scl_fall) begin
                            if (bit_cnt == 4'd7) begin
                                pec_received <= rx_shift;
                                // Check PEC: if mismatch, set pec_error
                                if (rx_shift != pec_calc) begin
                                    pec_error <= 1'b1;
                                end
                                state   <= STOP;
                                bit_cnt <= 4'd0;
                            end else begin
                                bit_cnt <= bit_cnt + 4'd1;
                            end
                        end
                    end else begin
                        // Write transaction: send PEC to slave
                        smbdat_out <= tx_shift[7];
                        smbdat_oe  <= 1'b1;

                        if (scl_fall) begin
                            tx_shift <= {tx_shift[6:0], 1'b0};
                            if (bit_cnt == 4'd7) begin
                                state <= STOP;
                                bit_cnt <= 4'd0;
                            end else begin
                                bit_cnt <= bit_cnt + 4'd1;
                            end
                        end
                    end

                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                //--------------------------------------------------------------
                // STOP: SMBDAT low→high while SMBCLK is high
                //--------------------------------------------------------------
                STOP: begin
                    case (bit_cnt)
                        4'd0: begin
                            smbdat_out <= 1'b0;
                            smbdat_oe  <= 1'b1;
                            bit_cnt <= 4'd1;
                            scl_cnt <= 16'd0;
                        end

                        4'd1: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                smbdat_out <= 1'b1;
                                smbdat_oe  <= 1'b1;
                                bit_cnt <= 4'd2;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end

                        4'd2: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                smbdat_out <= 1'b1;
                                smbdat_oe  <= 1'b0;
                                state   <= IDLE;
                                busy    <= 1'b0;
                                done    <= 1'b1;
                                bit_cnt <= 4'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end

                        default: bit_cnt <= 4'd0;
                    endcase
                end

                //--------------------------------------------------------------
                default: state <= IDLE;
            endcase
        end
    end

    //==========================================================================
    // CRC-8 PEC function: polynomial x^8 + x^2 + x + 1 (0x07)
    // Computed over all bytes in the transaction.
    // Called as: pec_calc_next = pec_updated(current_pec, data_byte)
    //==========================================================================
    function [7:0] pec_updated;
        input [7:0] current_pec;
        input [7:0] data_byte;
        reg [7:0]   temp_pec;
        reg [7:0]   temp_data;
        integer     i;
        begin
            temp_pec  = current_pec ^ data_byte;
            for (i = 0; i < 8; i = i + 1) begin
                if (temp_pec[7])
                    temp_pec = ({temp_pec[6:0], 1'b0} ^ 8'h07);
                else
                    temp_pec = {temp_pec[6:0], 1'b0};
            end
            pec_updated = temp_pec;
        end
    endfunction

endmodule
