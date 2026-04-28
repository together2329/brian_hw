
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: i3c
// Description: I3C SDR master controller (I2C-compatible subset).
//
// Performs write or write-then-read I3C SDR transactions.
// Uses open-drain style: sda_oe/scl_oe control tristate pad drivers.
//----------------------------------------------------------------------------

module i3c (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         enable,
    input  wire         read,
    input  wire         start,
    input  wire  [7:0]  tx_data,
    output reg  [7:0]   rx_data,
    input  wire  [7:0]  dev_addr,
    input  wire  [7:0]  cmd,
    input  wire         sda_in,
    output wire         sda_out,
    output wire         sda_oe,
    output wire         scl_out,
    output wire         scl_oe,
    output reg          busy,
    output reg          done,
    output reg          error,
    input  wire         ibi_en,
    output reg          ibi_rcvd,
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
    localparam ACK_DATA     = 4'd7;
    localparam REP_START    = 4'd8;
    localparam ADDR_R       = 4'd9;
    localparam ACK_ADDR_R   = 4'd10;
    localparam DATA_R       = 4'd11;
    localparam NACK         = 4'd12;
    localparam STOP         = 4'd13;

    //==========================================================================
    // Registers
    //==========================================================================
    reg [3:0]  state;
    reg [15:0] scl_cnt;
    reg        scl_clk;
    reg [3:0]  bit_cnt;
    reg [7:0]  tx_shift;
    reg [7:0]  rx_shift;
    reg        is_read_txn;
    reg        nack_received;
    reg        sda_bit_val;    // Value to drive on SDA (1=release, 0=drive low)

    wire scl_rise = (scl_cnt == clk_div - 16'd1) && (scl_clk == 1'b0);
    wire scl_fall = (scl_cnt == clk_div - 16'd1) && (scl_clk == 1'b1);

    //==========================================================================
    // SCL output (combinational)
    //==========================================================================
    assign scl_out = 1'b0;  // Always drive low when oe=1
    assign scl_oe  = (state == IDLE)                     ? 1'b0 :
                     (state == START || state == STOP)   ? 1'b0 :  // Released (high via pull-up)
                     (state == REP_START && bit_cnt < 4'd2) ? 1'b0 :   // Released during rep_start
                     (scl_clk == 1'b0)                   ? 1'b1 :  // Drive low
                                                           1'b0;   // Release (high)

    //==========================================================================
    // SDA output (combinational)
    //==========================================================================
    assign sda_out = 1'b0;  // Drive low when oe=1
    assign sda_oe  = (state == IDLE)                     ? 1'b0 :
                     (state == START || state == STOP)   ? 1'b1 :  // Drive low (START/STOP)
                     (state == REP_START)                 ? (bit_cnt == 4'd1 || bit_cnt == 4'd2) ? 1'b1 : 1'b0 :
                     (state == ACK_ADDR_W || state == ACK_CMD ||
                      state == ACK_DATA || state == ACK_ADDR_R) ? 1'b0 :  // Release for slave ACK
                     (state == DATA_R)                   ? 1'b0 :  // Release for slave data
                     (state == NACK)                     ? 1'b0 :  // Release (NACK = high)
                     (sda_bit_val == 1'b1)               ? 1'b0 :  // Release
                                                           1'b1;   // Drive low

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
            ibi_rcvd      <= 1'b0;
            sda_bit_val   <= 1'b1;
        end else begin
            done     <= 1'b0;
            error    <= 1'b0;
            ibi_rcvd <= 1'b0;

            case (state)
                IDLE: begin
                    busy          <= 1'b0;
                    scl_cnt       <= 16'd0;
                    scl_clk       <= 1'b0;
                    nack_received <= 1'b0;
                    sda_bit_val   <= 1'b1;

                    if (enable && start) begin
                        is_read_txn <= read;
                        tx_shift    <= {dev_addr[6:0], 1'b0};
                        busy        <= 1'b1;
                        state       <= START;
                    end
                end

                START: begin
                    // SDA driven low by sda_oe=1, SCL released (high)
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                        state   <= ADDR_W;
                        bit_cnt <= 4'd0;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                ADDR_W: begin
                    sda_bit_val <= tx_shift[7];
                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state    <= ACK_ADDR_W;
                            bit_cnt  <= 4'd0;
                            scl_cnt  <= 16'd0;
                            scl_clk  <= 1'b0;
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

                ACK_ADDR_W: begin
                    sda_bit_val <= 1'b1;
                    if (scl_rise) begin
                        if (sda_in == 1'b1) nack_received <= 1'b1;
                    end
                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                            bit_cnt <= 4'd0;
                        end else begin
                            tx_shift <= cmd;
                            state    <= CMD;
                            bit_cnt  <= 4'd0;
                        end
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                    end
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                CMD: begin
                    sda_bit_val <= tx_shift[7];
                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state    <= ACK_CMD;
                            bit_cnt  <= 4'd0;
                            scl_cnt  <= 16'd0;
                            scl_clk  <= 1'b0;
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

                ACK_CMD: begin
                    sda_bit_val <= 1'b1;
                    if (scl_rise) begin
                        if (sda_in == 1'b1) nack_received <= 1'b1;
                    end
                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                            bit_cnt <= 4'd0;
                        end else if (is_read_txn) begin
                            tx_shift <= {dev_addr[6:0], 1'b1};
                            state    <= REP_START;
                            bit_cnt  <= 4'd0;
                        end else begin
                            tx_shift <= tx_data;
                            state    <= DATA_W;
                            bit_cnt  <= 4'd0;
                        end
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                    end
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                DATA_W: begin
                    sda_bit_val <= tx_shift[7];
                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state    <= ACK_DATA;
                            bit_cnt  <= 4'd0;
                            scl_cnt  <= 16'd0;
                            scl_clk  <= 1'b0;
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

                ACK_DATA: begin
                    sda_bit_val <= 1'b1;
                    if (scl_rise) begin
                        if (sda_in == 1'b1) nack_received <= 1'b1;
                    end
                    if (scl_fall) begin
                        if (nack_received) error <= 1'b1;
                        state   <= STOP;
                        bit_cnt <= 4'd0;
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                    end
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                REP_START: begin
                    sda_bit_val <= 1'b1;
                    case (bit_cnt)
                        4'd0: begin
                            scl_clk <= 1'b1;
                            bit_cnt <= 4'd1;
                            scl_cnt <= 16'd0;
                        end
                        4'd1: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                bit_cnt <= 4'd2;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end
                        4'd2: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                state   <= ADDR_R;
                                bit_cnt <= 4'd0;
                                scl_clk <= 1'b0;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end
                        default: bit_cnt <= 4'd0;
                    endcase
                end

                ADDR_R: begin
                    sda_bit_val <= tx_shift[7];
                    if (scl_fall) begin
                        tx_shift <= {tx_shift[6:0], 1'b0};
                        if (bit_cnt == 4'd7) begin
                            state    <= ACK_ADDR_R;
                            bit_cnt  <= 4'd0;
                            scl_cnt  <= 16'd0;
                            scl_clk  <= 1'b0;
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

                ACK_ADDR_R: begin
                    sda_bit_val <= 1'b1;
                    if (scl_rise) begin
                        if (sda_in == 1'b1) nack_received <= 1'b1;
                    end
                    if (scl_fall) begin
                        if (nack_received) begin
                            error <= 1'b1;
                            state <= STOP;
                            bit_cnt <= 4'd0;
                        end else begin
                            state    <= DATA_R;
                            bit_cnt  <= 4'd0;
                            rx_shift <= 8'd0;
                        end
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                    end
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                DATA_R: begin
                    sda_bit_val <= 1'b1;
                    if (scl_rise) begin
                        rx_shift <= {rx_shift[6:0], sda_in};
                    end
                    if (scl_fall) begin
                        if (bit_cnt == 4'd7) begin
                            state    <= NACK;
                            bit_cnt  <= 4'd0;
                            scl_cnt  <= 16'd0;
                            scl_clk  <= 1'b0;
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

                NACK: begin
                    sda_bit_val <= 1'b1;
                    if (scl_fall) begin
                        rx_data <= rx_shift;
                        state   <= STOP;
                        bit_cnt <= 4'd0;
                        scl_cnt <= 16'd0;
                        scl_clk <= 1'b0;
                    end
                    if (scl_cnt == clk_div - 16'd1) begin
                        scl_cnt <= 16'd0;
                        scl_clk <= ~scl_clk;
                    end else begin
                        scl_cnt <= scl_cnt + 16'd1;
                    end
                end

                STOP: begin
                    sda_bit_val <= 1'b0;
                    case (bit_cnt)
                        4'd0: begin
                            scl_clk <= 1'b1;
                            bit_cnt <= 4'd1;
                            scl_cnt <= 16'd0;
                        end
                        4'd1: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                bit_cnt <= 4'd2;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end
                        4'd2: begin
                            if (scl_cnt == clk_div - 16'd1) begin
                                state   <= IDLE;
                                busy    <= 1'b0;
                                done    <= 1'b1;
                                bit_cnt <= 4'd0;
                                scl_cnt <= 16'd0;
                            end else begin
                                scl_cnt <= scl_cnt + 16'd1;
                            end
                        end
                        default: bit_cnt <= 4'd0;
                    endcase
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
