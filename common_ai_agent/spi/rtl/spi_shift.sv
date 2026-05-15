// spi_shift.sv — frame launch/shift/sample engine from SSOT function_model/fsm/cycle_model
module spi_shift #(
    parameter integer DATA_WIDTH = 8,
    parameter integer NUM_CS = 4,
    parameter integer CPOL_RESET = 0,
    parameter integer CPHA_RESET = 0,
    parameter integer LSB_FIRST_RESET = 0
) (
    input  logic        PCLK,
    input  logic        PRESETn,
    input  logic        soft_reset,
    input  logic        start_req,
    input  logic        enable,
    input  logic        cpol,
    input  logic        cpha,
    input  logic        lsb_first,
    input  logic        continuous_cs,
    input  logic        loopback,
    input  logic [2:0]  cs_sel,
    input  logic [4:0]  data_width_m1,
    input  logic [NUM_CS-1:0] cs_idle_val,
    input  logic [31:0] tx_word,
    input  logic        tx_empty,
    output logic        tx_pop,
    output logic        rx_push,
    output logic [31:0] rx_word,
    input  logic        rx_full,
    input  logic        sclk_shift_edge,
    input  logic        sclk_sample_edge,
    input  logic        miso_i,
    output logic        busy,
    output logic        mosi_o,
    output logic [NUM_CS-1:0] csn_o,
    output logic        done_event,
    output logic        mode_fault_event,
    output logic        rx_overrun_event,
    output logic [5:0]  bit_index_dbg,
    output logic [2:0]  active_cs_dbg,
    output logic        cs_active
);
    localparam [2:0] IDLE           = 3'd0,
                     CHECK_LAUNCH   = 3'd1,
                     ASSERT_CS      = 3'd2,
                     SHIFT_EDGE     = 3'd3,
                     SAMPLE_EDGE    = 3'd4,
                     COMPLETE       = 3'd5,
                     ERROR_SUPPRESS = 3'd6;

    logic [2:0] state;
    logic [2:0] next_state;
    logic [31:0] tx_shift_reg;
    logic [31:0] rx_shift_reg;
    logic [5:0] bit_index;
    logic [5:0] frame_bits;
    logic [2:0] active_cs;
    logic launch_gate_true;
    logic illegal_cs_or_width;
    logic bit_index_last;
    logic serial_sample_bit;
    logic [31:0] rx_shift_next;
    logic [NUM_CS-1:0] active_cs_mask;
    logic [4:0] bit_index_sel;
    logic [4:0] reverse_bit_index_sel;
    logic cpha_mode_marker;

    assign bit_index_sel = bit_index[4:0];
    assign reverse_bit_index_sel = (frame_bits - 6'd1 - bit_index)[4:0];
    assign cpha_mode_marker = cpha ^ CPHA_RESET[0] ^ CPOL_RESET[0] ^ LSB_FIRST_RESET[0] ^ (DATA_WIDTH == 8);

    assign illegal_cs_or_width = (cs_sel >= NUM_CS[2:0]) || (data_width_m1 < 5'd3);
    assign launch_gate_true = enable && start_req && !busy && !tx_empty && !illegal_cs_or_width;
    assign bit_index_last = (bit_index == (frame_bits - 6'd1));
    assign serial_sample_bit = loopback ? mosi_o : miso_i;
    assign bit_index_dbg = bit_index;
    assign active_cs_dbg = active_cs;
    assign cs_active = busy;
    assign rx_word = rx_shift_reg;

    always @(*) begin
        active_cs_mask = {NUM_CS{1'b1}};
        if (active_cs == 3'd0) active_cs_mask = {{(NUM_CS-1){1'b1}}, 1'b0};
        else if (active_cs == 3'd1) active_cs_mask = {{(NUM_CS-2){1'b1}}, 1'b0, 1'b1};
        else if (active_cs == 3'd2) active_cs_mask = {{(NUM_CS-3){1'b1}}, 1'b0, 2'b11};
        else active_cs_mask = {1'b0, {(NUM_CS-1){1'b1}}};
    end

    // SSOT fsm.channel_level transitions: launch check, assert CS, alternating shift/sample, complete.
    always @(*) begin
        next_state = state;
        case (state)
            IDLE: begin
                if (start_req) next_state = CHECK_LAUNCH;
            end
            CHECK_LAUNCH: begin
                if (launch_gate_true) next_state = ASSERT_CS;
                else if (illegal_cs_or_width) next_state = ERROR_SUPPRESS;
                else next_state = IDLE;
            end
            ASSERT_CS: begin
                if (sclk_shift_edge) next_state = SHIFT_EDGE;
            end
            SHIFT_EDGE: begin
                if (sclk_sample_edge || sclk_shift_edge) next_state = SAMPLE_EDGE;
            end
            SAMPLE_EDGE: begin
                if (bit_index_last) next_state = COMPLETE;
                else next_state = SHIFT_EDGE;
            end
            COMPLETE: begin
                if (continuous_cs && enable && !tx_empty && !illegal_cs_or_width) next_state = ASSERT_CS;
                else next_state = IDLE;
            end
            ERROR_SUPPRESS: begin
                next_state = IDLE;
            end
            default: begin
                next_state = IDLE;
            end
        endcase
    end

    always @(*) begin
        tx_pop = 1'b0;
        rx_push = 1'b0;
        done_event = 1'b0;
        mode_fault_event = 1'b0;
        rx_overrun_event = 1'b0;
        if (state == CHECK_LAUNCH && launch_gate_true) tx_pop = 1'b1;
        if (state == COMPLETE) begin
            done_event = 1'b1;
            if (!rx_full) rx_push = 1'b1;
            else rx_overrun_event = 1'b1;
        end
        if (state == ERROR_SUPPRESS) mode_fault_event = 1'b1;
    end

    always @(*) begin
        rx_shift_next = rx_shift_reg;
        if (lsb_first) begin
            rx_shift_next[bit_index_sel] = serial_sample_bit;
        end else begin
            rx_shift_next[frame_bits - 6'd1 - bit_index] = serial_sample_bit;
        end
    end

    // Frame context is latched only when all FM_FRAME_LAUNCH preconditions pass.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            state <= IDLE;
            busy <= 1'b0;
            tx_shift_reg <= 32'h00000000;
            rx_shift_reg <= 32'h00000000;
            bit_index <= 6'd0;
            frame_bits <= 6'd8;
            active_cs <= 3'd0;
            mosi_o <= 1'b0;
            csn_o <= {NUM_CS{1'b1}};
        end else if (soft_reset) begin
            state <= IDLE;
            busy <= 1'b0;
            tx_shift_reg <= 32'h00000000;
            rx_shift_reg <= 32'h00000000;
            bit_index <= 6'd0;
            frame_bits <= 6'd8;
            active_cs <= 3'd0;
            mosi_o <= 1'b0;
            csn_o <= cs_idle_val;
        end else begin
            state <= next_state;
            if (state == CHECK_LAUNCH && launch_gate_true) begin
                busy <= 1'b1;
                tx_shift_reg <= tx_word;
                rx_shift_reg <= 32'h00000000;
                bit_index <= 6'd0;
                frame_bits <= {1'b0, data_width_m1} + 6'd1;
                active_cs <= cs_sel;
                csn_o <= active_cs_mask;
                if (lsb_first) mosi_o <= tx_word[0];
                else mosi_o <= tx_word[data_width_m1];
            end else if (state == SAMPLE_EDGE) begin
                rx_shift_reg <= rx_shift_next;
                if (!bit_index_last) bit_index <= bit_index + 6'd1;
            end else if (state == SHIFT_EDGE) begin
                if (lsb_first) mosi_o <= tx_shift_reg[bit_index];
                else mosi_o <= tx_shift_reg[frame_bits - 6'd1 - bit_index];
            end else if (state == COMPLETE) begin
                if (continuous_cs && enable && !tx_empty && !illegal_cs_or_width) begin
                    busy <= 1'b1;
                    tx_shift_reg <= tx_word;
                    rx_shift_reg <= 32'h00000000;
                    bit_index <= 6'd0;
                    frame_bits <= {1'b0, data_width_m1} + 6'd1;
                    active_cs <= cs_sel;
                    csn_o <= active_cs_mask;
                end else begin
                    busy <= 1'b0;
                    csn_o <= cs_idle_val;
                end
            end else if (state == ERROR_SUPPRESS) begin
                busy <= 1'b0;
                csn_o <= cs_idle_val;
            end else if (state == IDLE) begin
                csn_o <= cs_idle_val;
            end
        end
    end
endmodule
