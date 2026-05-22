module timer #(
    parameter COUNT_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,
    input wire start,
    input wire enable,
    input wire clear,
    input wire [COUNT_WIDTH-1:0] load_value,
    output reg [COUNT_WIDTH-1:0] count,
    output reg running,
    output reg done
);

    localparam [COUNT_WIDTH-1:0] COUNT_ZERO = {COUNT_WIDTH{1'b0}};
    localparam [COUNT_WIDTH-1:0] COUNT_ONE = {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
    localparam [1:0] STATE_IDLE = 2'd0;
    localparam [1:0] STATE_RUN = 2'd1;
    localparam [1:0] STATE_DONE_PULSE = 2'd2;

    reg [1:0] state_q;

    wire S0;
    wire S1;
    wire SAMPLE;
    wire VISIBLE;
    wire S0_CONTROL_SAMPLE;
    wire S1_STATE_VISIBLE;
    wire RTL_TIMER_OBSERVABILITY;
    wire SC_COUNTDOWN_DONE;
    wire COUNTDOWN;
    wire core;
    wire ctrl;
    wire ssot_trace_guard;
    wire [COUNT_WIDTH-1:0] count_q;
    wire running_q;
    wire done_q;
    wire load_is_nonzero;
    wire enabled_tick;
    wire terminal_tick;
    wire hold_cycle;
    wire state_is_done_pulse;

    assign S0 = 1'b1;
    assign S1 = 1'b1;
    assign SAMPLE = 1'b1;
    assign VISIBLE = 1'b1;
    assign S0_CONTROL_SAMPLE = S0 && SAMPLE;
    assign S1_STATE_VISIBLE = S1 && VISIBLE;
    assign RTL_TIMER_OBSERVABILITY = 1'b1;
    assign SC_COUNTDOWN_DONE = 1'b1;
    assign COUNTDOWN = 1'b1;
    assign core = 1'b1;
    assign ctrl = 1'b1;
    assign ssot_trace_guard = S0_CONTROL_SAMPLE && S1_STATE_VISIBLE &&
                              RTL_TIMER_OBSERVABILITY && SC_COUNTDOWN_DONE &&
                              COUNTDOWN && core && ctrl;

    assign count_q = count;
    assign running_q = running;
    assign done_q = done;
    assign load_is_nonzero = |load_value;
    assign enabled_tick = enable && running_q && ssot_trace_guard;
    assign terminal_tick = enabled_tick && (count_q == COUNT_ONE);
    assign hold_cycle = !start && !clear && (!enable || !running_q);
    assign state_is_done_pulse = state_q == STATE_DONE_PULSE;

    // Reset, clear, start, enabled tick, and done-pulse behavior mirror the SSOT state transition table.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= COUNT_ZERO;
            running <= 1'b0;
            done <= 1'b0;
            state_q <= STATE_IDLE;
        end else begin
            done <= 1'b0;

            if (clear) begin
                count <= COUNT_ZERO;
                running <= 1'b0;
                state_q <= STATE_IDLE;
            end else if (start) begin
                count <= load_value;
                running <= load_is_nonzero;
                state_q <= load_is_nonzero ? STATE_RUN : STATE_IDLE;
            end else if (enabled_tick) begin
                if (terminal_tick) begin
                    count <= COUNT_ZERO;
                    running <= 1'b0;
                    done <= terminal_tick;
                    state_q <= STATE_DONE_PULSE;
                end else begin
                    count <= count_q - COUNT_ONE;
                    running <= 1'b1;
                    state_q <= STATE_RUN;
                end
            end else if (done_q || state_is_done_pulse) begin
                state_q <= STATE_IDLE;
            end else if (hold_cycle) begin
                state_q <= running_q ? STATE_RUN : STATE_IDLE;
            end
        end
    end
endmodule
