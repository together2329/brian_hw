module cortex_m0lite #(
    parameter integer XLEN = 16
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             fetch_en,
    input  logic             step_en,
    input  logic             flush,
    input  logic [XLEN-1:0]  instr_data,
    output logic [XLEN-1:0]  pc,
    output logic             busy,
    output logic             retire
);

    // Explicit FSM encoding from SSOT fsm.control.states.
    localparam [1:0] IDLE       = 2'd0;
    localparam [1:0] RUN        = 2'd1;
    localparam [1:0] DONE_PULSE = 2'd2;

    // timer_core architectural state from function_model/state_updates.
    logic [XLEN-1:0] pc_q;
    logic            busy_q;
    logic            retire_q;

    // FSM state tracks IDLE/RUN/DONE_PULSE observability and transition intent.
    logic [1:0]      state_q;
    logic [1:0]      state_next;

    // S0_CONTROL_SAMPLE acceptance qualifier from rtl_contract.sample_condition.
    logic            accept_txn;
    logic            s0_control_sample_fire;

    // S1_STATE_VISIBLE: indicates updated state is observable after the
    // registered update edge (cycle 1 in the pipeline model).  Always active
    // in this single-stage latency-1 design.

    // Next-state wires implement SSOT output_rules/state_updates exactly.
    logic [XLEN-1:0] pc_next;
    logic            busy_next;
    logic            retire_next;

    // sample_condition from rtl_contract: fetch_en or flush or step_en or retire_q.
    assign accept_txn             = fetch_en | flush | step_en | retire_q;
    assign s0_control_sample_fire = accept_txn;

    // ordering_rule_0 + flush_priority: flush has highest priority over all tick behavior.
    // ordering_rule_1 + fetch_en_load: fetch_en load is applied before step_en tick behavior.
    // step_en decrement occurs only while busy and pc_q > 0 (prevents underflow).
    assign pc_next = flush ? {XLEN{1'b0}} :
                     (fetch_en ? instr_data :
                     ((step_en && busy_q && (pc_q > {XLEN{1'b0}})) ?
                     (pc_q - {{(XLEN-1){1'b0}}, 1'b1}) : pc_q));

    // busy drops on terminal step tick when current pc_q <= 1.
    assign busy_next = flush ? 1'b0 :
                       (fetch_en ? (instr_data > {XLEN{1'b0}}) :
                       ((step_en && busy_q && (pc_q <= {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b0 : busy_q));

    // retire is visible on the terminal decrement cycle (pc_q == 1 with step_en && busy_q).
    assign retire_next = flush ? 1'b0 :
                         (fetch_en ? 1'b0 :
                         ((step_en && busy_q && (pc_q == {{(XLEN-1){1'b0}}, 1'b1})) ? 1'b1 : 1'b0));

    // fsm.control.transitions implementation:
    // transition_0: IDLE -> RUN when fetch_en && instr_data != 0
    // transition_1: RUN -> RUN when step_en && pc > 1
    // transition_2: RUN -> DONE_PULSE when step_en && pc == 1
    // transition_3: DONE_PULSE -> IDLE on next control cycle without fetch_en
    // transition_4: RUN -> IDLE when flush
    always @(*) begin
        state_next = state_q;
        case (state_q)
            IDLE: begin
                if (flush) begin
                    state_next = IDLE;
                end else if (fetch_en && (instr_data != {XLEN{1'b0}})) begin
                    state_next = RUN;
                end else begin
                    state_next = IDLE;
                end
            end

            RUN: begin
                if (flush) begin
                    state_next = IDLE;
                end else if (step_en && busy_q && (pc_q == {{(XLEN-1){1'b0}}, 1'b1})) begin
                    state_next = DONE_PULSE;
                end else begin
                    state_next = RUN;
                end
            end

            DONE_PULSE: begin
                // A fresh fetch_en starts the next interval immediately.
                if (flush) begin
                    state_next = IDLE;
                end else if (fetch_en && (instr_data != {XLEN{1'b0}})) begin
                    state_next = RUN;
                end else begin
                    state_next = IDLE;
                end
            end

            default: begin
                state_next = IDLE;
            end
        endcase
    end

    // cycle_model.clock=clk, cycle_model.reset=rst_n(active low), cycle_model.latency=1.
    // S0_CONTROL_SAMPLE (cycle 0): controls are sampled when s0_control_sample_fire is high.
    // S1_STATE_VISIBLE (cycle 1): updated pc/busy/retire become visible after this same edge.
    // No extra input staging is used, so this remains latency=1 rather than latency=2.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q     <= {XLEN{1'b0}};
            busy_q   <= 1'b0;
            retire_q <= 1'b0;
            state_q  <= IDLE;
        end else if (s0_control_sample_fire) begin
            pc_q     <= pc_next;
            busy_q   <= busy_next;
            retire_q <= retire_next;
            state_q  <= state_next;
        end
    end

    // S1_STATE_VISIBLE outputs: registered state is visible to the scoreboard.
    // s1_state_visible marks that these outputs reflect the post-update state.
    assign pc     = pc_q;
    assign busy   = busy_q;
    assign retire = retire_q;

endmodule
