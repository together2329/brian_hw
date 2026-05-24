// real_llm_counter_demo.sv — 8-bit saturating up/down counter with valid-ready command input.
// SSOT authority: yaml/real_llm_counter_demo.ssot.yaml
// Behavior source: function_model.transactions FM_CLEAR..FM_INVALID, cycle_model, features.F001-F009
module real_llm_counter_demo #(
    parameter integer WIDTH = 8     // Counter bit width (SSOT: fixed at 8, min=8, max=8)
) (
    // Clock/reset — source: io_list.clock_domains, io_list.resets
    input  logic                  clk,
    input  logic                  rst_n,
    // Command interface — source: io_list.interfaces.command_if (native_valid_ready, always_ready)
    input  logic                  cmd_valid,
    output logic                  cmd_ready,
    input  logic [2:0]            cmd,
    input  logic [WIDTH-1:0]      load_value,
    // Status outputs — source: io_list.interfaces.status_out
    output logic [WIDTH-1:0]      count,
    output logic                  zero,
    output logic                  max,
    output logic [31:0]           accepted_count,
    output logic [2:0]            status
);
    // Command encoding — source: io_list.interfaces.command_if.ports.cmd description
    localparam [2:0] CMD_CLEAR = 3'd0,
                      CMD_LOAD  = 3'd1,
                      CMD_INC   = 3'd2,
                      CMD_DEC   = 3'd3,
                      CMD_HOLD  = 3'd4;

    // Saturation constants derived from WIDTH — source: parameters.SAT_MAX=255, parameters.SAT_MIN=0
    // SAT_MAX = 2**WIDTH - 1 (all ones); SAT_MIN = 0 (all zeros)
    localparam [WIDTH-1:0] SAT_MAX_VAL = {WIDTH{1'b1}};
    localparam [WIDTH-1:0] SAT_MIN_VAL = {WIDTH{1'b0}};
    // Architectural state registers — source: function_model.state_variables
    logic [WIDTH-1:0]  count_reg;           // 8-bit counter, reset=0
    logic [31:0]       accepted_count_reg;  // 32-bit wrap counter, reset=0
    logic [2:0]        last_cmd_reg;        // last accepted cmd, reset=0

    // Next-state wire for count — computed combinationally from command decode
    logic [WIDTH-1:0] count_next;
    // Combinational command decode — source: decomposition.command_decode, features.F001-F006
    // Produces count_next from current count_reg and the command input.
    // Default is HOLD (no change); INVALID encodings 5-7 also hold — source: FM_INVALID, error_handling
    always @(*) begin
        count_next = count_reg;
        case (cmd)
            CMD_CLEAR: count_next = SAT_MIN_VAL;               // FM_CLEAR: force count to 0
            CMD_LOAD:  count_next = load_value;                 // FM_LOAD: set count to load_value
            CMD_INC:   count_next = (count_reg == SAT_MAX_VAL)  // FM_INC: saturate at SAT_MAX — source: features.F001
                                 ? SAT_MAX_VAL
                                 : count_reg + 1'b1;
            CMD_DEC:   count_next = (count_reg == SAT_MIN_VAL)  // FM_DEC: saturate at SAT_MIN — source: features.F002
                                 ? SAT_MIN_VAL
                                 : count_reg - 1'b1;
            CMD_HOLD:  count_next = count_reg;                  // FM_HOLD: no change — source: features.F005
            default:   count_next = count_reg;                  // FM_INVALID (5-7): treat as HOLD — source: error_handling
        endcase
    end
    // Sequential state update — source: cycle_model.pipeline S0_ACCEPT → S1_UPDATE
    // Async active-low reset — source: io_list.resets.rst_n (async_assert_sync_deassert)
    // Reset clears count, accepted_count, and last_cmd — source: clock_reset_domains.reset_behavior
    // cmd_ready is always 1, so cmd_valid alone triggers acceptance — source: cycle_model.handshake_rules
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_reg          <= SAT_MIN_VAL;  // reset count to 0 — source: clock_reset_domains.reset_behavior
            accepted_count_reg <= 32'd0;
            last_cmd_reg       <= 3'd0;
        end else if (cmd_valid) begin
            count_reg          <= count_next;
            accepted_count_reg <= accepted_count_reg + 32'd1;  // wraps at 2^32 — source: features.F008
            last_cmd_reg       <= cmd;                          // records actual cmd — source: FM_INVALID
        end
    end
    // Output assignments — source: io_list.interfaces.status_out, function_model.invariants
    assign count          = count_reg;
    assign status         = last_cmd_reg;
    assign cmd_ready      = 1'b1;                             // always ready — source: function_model.invariants
    assign zero           = (count_reg == SAT_MIN_VAL);        // combinational — source: features.F007
    assign max            = (count_reg == SAT_MAX_VAL);        // combinational — source: features.F007
    assign accepted_count = accepted_count_reg;
endmodule
