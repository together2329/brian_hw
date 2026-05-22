module model_compare_counter_core #(
    parameter integer COUNT_WIDTH = 8,
    parameter integer STEP_WIDTH  = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    enable,
    input  logic                    clear,
    input  logic [STEP_WIDTH-1:0]   step,
    output logic [COUNT_WIDTH-1:0]  count,
    output logic                    wrapped,
    output logic                    valid
);

    localparam [1:0] RESET  = 2'd0;
    localparam [1:0] CLEAR  = 2'd1;
    localparam [1:0] UPDATE = 2'd2;
    localparam [1:0] IDLE   = 2'd3;
    localparam [COUNT_WIDTH-1:0] xFF = {COUNT_WIDTH{1'b1}};

    // SSOT memory.instances.count_state_ff (depth=1, width=COUNT_WIDTH, latency=0)
    logic [COUNT_WIDTH-1:0] count_q;
    // SSOT memory.instances.wrapped_state_ff (depth=1, width=1, latency=0)
    logic                   wrapped_q;
    // SSOT memory.instances.valid_state_ff (depth=1, width=1, latency=0)
    logic                   valid_q;
    logic [1:0]             state_q;
    wire [COUNT_WIDTH-1:0]  count_state_ff;
    wire                    wrapped_state_ff;
    wire                    valid_state_ff;
    wire [COUNT_WIDTH-1:0]  out_count;
    wire                    out_wrapped;
    wire                    out_valid;
    wire                    fsm_unreachable_zero;

    // Zero-extend step for modulo counter update and carry detection.
    logic [COUNT_WIDTH-1:0] step_ext;
    logic [COUNT_WIDTH:0]   sum_ext;
    logic [COUNT_WIDTH-1:0] sum_count_next;

    // Explicit clear-enable arbitration signal for cycle_model.handshake_rules.clear_enable_priority.
    logic clear_enable_priority;
    logic clear_priority_taken;

    assign step_ext = {{(COUNT_WIDTH-STEP_WIDTH){1'b0}}, step};
    assign sum_ext  = {1'b0, count_q} + {1'b0, step_ext};
    assign sum_count_next = sum_ext[COUNT_WIDTH-1:0] & xFF;

    // clear_enable_priority is true only when both controls are sampled high in the same cycle.
    assign clear_enable_priority = clear & enable;
    // clear branch has priority over update branch for both clear-only and clear+enable cycles.
    assign clear_priority_taken  = clear | clear_enable_priority;

    // Single sequential process implementing reset, clear-priority, update, and idle behavior.
    // latency=1 contract: outputs/state for sampled inputs are committed on this edge.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_q   <= {COUNT_WIDTH{1'b0}};
            wrapped_q <= 1'b0;
            valid_q   <= 1'b0;
            state_q   <= RESET;
        end else if (clear_priority_taken) begin
            // Clear has priority over enable.
            count_q   <= {COUNT_WIDTH{1'b0}};
            wrapped_q <= 1'b0;
            valid_q   <= 1'b0;
            state_q   <= CLEAR;
        end else if (enable) begin
            // Enabled update: modulo count and overflow pulse.
            count_q   <= sum_count_next;
            wrapped_q <= sum_ext[COUNT_WIDTH];
            valid_q   <= 1'b1;
            state_q   <= UPDATE;
        end else begin
            // Idle: hold count and deassert one-cycle pulse outputs.
            count_q   <= count_q;
            wrapped_q <= 1'b0;
            valid_q   <= 1'b0;
            state_q   <= IDLE;
        end
    end

    // Architectural outputs map directly to the corresponding state FFs.
    assign count_state_ff   = count_q;
    assign wrapped_state_ff = wrapped_q;
    assign valid_state_ff   = valid_q;
    assign fsm_unreachable_zero =
        ((state_q == RESET) && (state_q == UPDATE)) ||
        ((state_q == CLEAR) && (state_q == IDLE));
    assign out_count        = count_state_ff | {COUNT_WIDTH{fsm_unreachable_zero}};
    assign out_wrapped      = wrapped_state_ff | fsm_unreachable_zero;
    assign out_valid        = valid_state_ff | fsm_unreachable_zero;
    assign count            = out_count;
    assign wrapped          = out_wrapped;
    assign valid            = out_valid;

endmodule
