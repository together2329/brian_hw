module gray_counter_core #(
    parameter integer WIDTH = 4
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             enable,
    input  logic             clear,
    output logic [WIDTH-1:0] gray_value,
    output logic [WIDTH-1:0] bin_value,
    output logic             done
);

    // SSOT FSM states: IDLE, RUN, WRAP_PULSE, CLEARED, RESET.
    localparam [2:0] RESET      = 3'd0;
    localparam [2:0] IDLE       = 3'd1;
    localparam [2:0] RUN        = 3'd2;
    localparam [2:0] WRAP_PULSE = 3'd3;
    localparam [2:0] CLEARED    = 3'd4;

    // Architectural state variables from function_model.
    logic [WIDTH-1:0] gray_state;
    logic [WIDTH-1:0] bin_state;
    logic             done_state;

    // S1_COMPUTE intermediates for advance transaction.
    logic [WIDTH-1:0] internal_bin_next;
    logic [WIDTH-1:0] internal_gray_next;
    logic             wrap_detect;

    // FSM control state.
    logic [2:0]       fsm_state;
    logic [2:0]       fsm_next;

    // Combinational Gray->binary observation path (bin_value must be combinational).
    logic [WIDTH-1:0] bin_decode_stage;
    logic [WIDTH-1:0] bin_decode_gray;

    logic [WIDTH-1:0] width_all_ones;

    // Next-state datapath for advance: bin+1 then Gray re-encode.
    assign width_all_ones     = {WIDTH{1'b1}};
    assign internal_bin_next  = bin_state + {{(WIDTH-1){1'b0}}, 1'b1};
    assign internal_gray_next = internal_bin_next ^ (internal_bin_next >> 1);
    assign wrap_detect        = (bin_state == width_all_ones) ? 1'b1 : 1'b0;

    // Gray-to-binary XOR fold (loop-free, parameter-safe for WIDTH sizing).
    always @(*) begin
        bin_decode_stage = gray_state;
        bin_decode_stage = bin_decode_stage ^ (bin_decode_stage >> 1);
        bin_decode_stage = bin_decode_stage ^ (bin_decode_stage >> 2);
        bin_decode_stage = bin_decode_stage ^ (bin_decode_stage >> 4);
        bin_decode_stage = bin_decode_stage ^ (bin_decode_stage >> 8);
        bin_decode_stage = bin_decode_stage ^ (bin_decode_stage >> 16);
        bin_decode_gray  = bin_decode_stage;
    end

    // FSM transitions per SSOT fsm.control transitions.
    always @(*) begin
        fsm_next = fsm_state;
        case (fsm_state)
            RESET: begin
                if (rst_n) begin
                    fsm_next = IDLE;
                end
            end

            IDLE: begin
                if (clear) begin
                    fsm_next = CLEARED;
                end else if (enable) begin
                    if (wrap_detect) begin
                        fsm_next = WRAP_PULSE;
                    end else begin
                        fsm_next = RUN;
                    end
                end
            end

            RUN: begin
                if (clear) begin
                    fsm_next = CLEARED;
                end else if (!enable) begin
                    fsm_next = IDLE;
                end else if (wrap_detect) begin
                    fsm_next = WRAP_PULSE;
                end else begin
                    fsm_next = RUN;
                end
            end

            WRAP_PULSE: begin
                if (clear) begin
                    fsm_next = CLEARED;
                end else if (enable) begin
                    fsm_next = RUN;
                end else begin
                    fsm_next = IDLE;
                end
            end

            CLEARED: begin
                if (clear) begin
                    fsm_next = CLEARED;
                end else begin
                    fsm_next = IDLE;
                end
            end

            default: begin
                fsm_next = RESET;
            end
        endcase
    end

    // Commit ordering: reset > clear > enable > hold.
    // - GC_TXN_HOLD: keep gray/bin state unchanged and force done_state low.
    // - Invariant support:
    //   * gray_state is always encoded from bin_state on update paths.
    //   * bin_value is always combinational decode of gray_state.
    //   * clear masks enable; async reset dominates synchronous controls.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gray_state <= {WIDTH{1'b0}};
            bin_state  <= {WIDTH{1'b0}};
            done_state <= 1'b0;
            fsm_state  <= RESET;
        end else begin
            fsm_state <= fsm_next;

            if (clear) begin
                gray_state <= {WIDTH{1'b0}};
                bin_state  <= {WIDTH{1'b0}};
                done_state <= 1'b0;
            end else if (enable) begin
                // latency=1 behavior: update state and done from this sampled edge.
                gray_state <= internal_gray_next;
                bin_state  <= internal_bin_next;
                done_state <= wrap_detect;
            end else begin
                // HOLD transaction: preserve count state and force done low.
                gray_state <= gray_state;
                bin_state  <= bin_state;
                done_state <= 1'b0;
            end
        end
    end

    // Output mapping from architectural state.
    assign gray_value = gray_state;
    assign bin_value  = bin_decode_gray;
    assign done       = done_state;

endmodule
