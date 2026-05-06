// =============================================================================
// uart_rx.sv — UART Receiver with RX FIFO and deserializer
// =============================================================================
// RX FSM: IDLE → START → DATA → PARITY → STOP → PUSH → IDLE
// Features:
//   - 2-stage synchronizer on rx input
//   - Mid-bit sampling with configurable baud divisor
//   - Inline FIFO (pointer-based, parameterized depth)
//   - Framing error and overrun error detection (latched, clearable)
//   - LSB-first deserialization
//   - Optional parity checking
// =============================================================================

module uart_rx #(
    parameter integer DATA_WIDTH = 8,
    parameter integer FIFO_DEPTH = 16
) (
    input  logic                      clk,
    input  logic                      rst_n,

    // Control from CTRL register
    input  logic                      rx_en_i,
    input  logic                      fifo_en_i,
    input  logic                      parity_en_i,
    input  logic                      parity_odd_i,
    input  logic                      stop_bits_i,

    // Baud divisor for mid-bit sampling
    input  logic [7:0]                baud_div_i,

    // FIFO pop interface (from APB RX_DATA read)
    input  logic                      rx_pop_i,
    output logic [DATA_WIDTH-1:0]     rx_data_o,
    output logic                      rx_valid_o,     // 1 = FIFO was not empty

    // Status outputs (to register file)
    output logic                      rx_empty_o,
    output logic                      rx_full_o,
    output logic                      rx_busy_o,
    output logic                      framing_err_o,
    output logic                      overrun_err_o,

    // Error clear (on STATUS register read)
    input  logic                      err_clear_i,

    // Serial input
    input  logic                      rx_i
);

    // ========================================================================
    // FSM state encoding
    // ========================================================================
    localparam logic [2:0] RX_IDLE   = 3'd0,
                           RX_START  = 3'd1,
                           RX_DATA   = 3'd2,
                           RX_PARITY = 3'd3,
                           RX_STOP   = 3'd4,
                           RX_PUSH   = 3'd5;

    logic [2:0] state_q;

    // ========================================================================
    // Input synchronizer (2-stage)
    // ========================================================================
    logic rx_sync1, rx_sync2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync1 <= 1'b1;
            rx_sync2 <= 1'b1;
        end else begin
            rx_sync1 <= rx_i;
            rx_sync2 <= rx_sync1;
        end
    end

    // Edge detection for start bit
    logic rx_sync2_d;   // delayed by 1 clock
    logic rx_falling;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rx_sync2_d <= 1'b1;
        else
            rx_sync2_d <= rx_sync2;
    end

    assign rx_falling = ~rx_sync2 & rx_sync2_d;

    // ========================================================================
    // Sample counter — counts system clock cycles for mid-bit timing
    // ========================================================================
    logic [7:0] sample_cnt;
    logic       sample_tick;   // 1 cycle at terminal count

    // Half-bit and full-bit thresholds
    logic [7:0] half_div;
    logic [7:0] full_div;

    // Effective divisor: treat 0 as 256 (max 8-bit counter ≈ 255)
    always_comb begin
        if (baud_div_i == 8'd0) begin
            full_div = 8'd255;
            half_div = 8'd127;
        end else begin
            full_div = baud_div_i;
            half_div = baud_div_i >> 1;  // divide by 2
        end
    end

    // Counter logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_cnt <= 8'd0;
        end else begin
            if (state_q == RX_IDLE) begin
                sample_cnt <= 8'd0;
            end else if (sample_tick) begin
                sample_cnt <= 8'd0;
            end else begin
                sample_cnt <= sample_cnt + 8'd1;
            end
        end
    end

    // Sample tick — asserts when counter reaches threshold
    always_comb begin
        case (state_q)
            RX_START:  sample_tick = (sample_cnt >= half_div);
            RX_DATA,
            RX_PARITY,
            RX_STOP:   sample_tick = (sample_cnt >= full_div);
            default:   sample_tick = 1'b0;
        endcase
    end

    // ========================================================================
    // Deserializer — shift register + bit counter
    // ========================================================================
    logic [DATA_WIDTH-1:0] shift_reg;
    logic [2:0]            bit_count;
    logic                  parity_calc;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg   <= {DATA_WIDTH{1'b0}};
            bit_count   <= 3'd0;
            parity_calc <= 1'b0;
        end else begin
            case (state_q)
                RX_DATA: begin
                    if (sample_tick) begin
                        shift_reg   <= {rx_sync2, shift_reg[DATA_WIDTH-1:1]};
                        bit_count   <= bit_count + 3'd1;
                        parity_calc <= parity_calc ^ rx_sync2;
                    end
                end
                default: ;  // hold
            endcase
        end
    end

    // ========================================================================
    // FIFO — push/pop with pointer-based circular buffer
    // ========================================================================
    logic [DATA_WIDTH-1:0]   fifo_mem [FIFO_DEPTH-1:0];
    logic [$clog2(FIFO_DEPTH):0]    fifo_count;
    logic [$clog2(FIFO_DEPTH)-1:0]  fifo_wr_ptr;
    logic [$clog2(FIFO_DEPTH)-1:0]  fifo_rd_ptr;
    logic                      fifo_not_empty;
    logic                      fifo_push;

    // FIFO push pointer + count
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fifo_wr_ptr <= {$clog2(FIFO_DEPTH){1'b0}};
            fifo_count  <= {($clog2(FIFO_DEPTH)+1){1'b0}};
        end else begin
            if (fifo_push && !rx_full_o) begin
                fifo_mem[fifo_wr_ptr] <= shift_reg;
                fifo_wr_ptr <= fifo_wr_ptr + {{$clog2(FIFO_DEPTH){1'b0}}, 1'b1};
                fifo_count  <= fifo_count + {{($clog2(FIFO_DEPTH)){1'b0}}, 1'b1};
            end
            if (rx_pop_i && fifo_not_empty) begin
                fifo_count <= fifo_count - {{($clog2(FIFO_DEPTH)){1'b0}}, 1'b1};
            end
            if (fifo_push && !rx_full_o && rx_pop_i && fifo_not_empty) begin
                fifo_count <= fifo_count;  // simultaneous push+pop
            end
        end
    end

    // FIFO read pointer
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fifo_rd_ptr <= {$clog2(FIFO_DEPTH){1'b0}};
        end else begin
            if (rx_pop_i && fifo_not_empty) begin
                fifo_rd_ptr <= fifo_rd_ptr + {{$clog2(FIFO_DEPTH){1'b0}}, 1'b1};
            end
        end
    end

    // FIFO combinational outputs
    assign fifo_not_empty = (fifo_count > {($clog2(FIFO_DEPTH)+1){1'b0}});
    assign rx_empty_o     = ~fifo_not_empty;
    assign rx_full_o      = (fifo_count >= FIFO_DEPTH[($clog2(FIFO_DEPTH)):0]);

    // FIFO data output (combinational read)
    assign rx_data_o = fifo_mem[fifo_rd_ptr];
    assign rx_valid_o = fifo_not_empty;

    // ========================================================================
    // Error flags — latched, cleared on err_clear_i
    // ========================================================================
    logic framing_err_set, overrun_err_set;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            framing_err_o  <= 1'b0;
            overrun_err_o  <= 1'b0;
        end else begin
            if (err_clear_i) begin
                framing_err_o <= 1'b0;
                overrun_err_o <= 1'b0;
            end else begin
                if (framing_err_set)
                    framing_err_o <= 1'b1;
                if (overrun_err_set)
                    overrun_err_o <= 1'b1;
            end
        end
    end

    // ========================================================================
    // FSM — state register
    // ========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q <= RX_IDLE;
        end else begin
            if (!rx_en_i) begin
                state_q <= RX_IDLE;
            end else begin
                case (state_q)
                    RX_IDLE: begin
                        if (rx_falling)
                            state_q <= RX_START;
                    end

                    RX_START: begin
                        if (sample_tick) begin
                            if (rx_sync2 == 1'b0)
                                state_q <= RX_DATA;    // valid start bit
                            else
                                state_q <= RX_IDLE;    // glitch, abort
                        end
                    end

                    RX_DATA: begin
                        if (sample_tick && (bit_count == 3'd7)) begin
                            if (parity_en_i)
                                state_q <= RX_PARITY;
                            else
                                state_q <= RX_STOP;
                        end
                    end

                    RX_PARITY: begin
                        if (sample_tick)
                            state_q <= RX_STOP;
                    end

                    RX_STOP: begin
                        if (sample_tick) begin
                            state_q <= RX_PUSH;
                        end
                    end

                    RX_PUSH: begin
                        state_q <= RX_IDLE;
                    end

                    default: state_q <= RX_IDLE;
                endcase
            end
        end
    end

    // ========================================================================
    // FIFO push + error detection in RX_PUSH state
    // ========================================================================
    // Push when entering PUSH state (1-cycle pulse)
    assign fifo_push = (state_q == RX_PUSH) && rx_en_i;

    // Framing error: stop bit is not 1
    always_comb begin
        framing_err_set = 1'b0;
        overrun_err_set = 1'b0;
        if (state_q == RX_STOP && sample_tick) begin
            if (rx_sync2 == 1'b0)
                framing_err_set = 1'b1;   // missing stop bit
        end
        if (fifo_push && rx_full_o)
            overrun_err_set = 1'b1;       // FIFO full, data lost
    end

    // ========================================================================
    // Busy flag
    // ========================================================================
    assign rx_busy_o = (state_q != RX_IDLE);

endmodule
