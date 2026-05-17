module pl330realverify_channel_fsm (
    input  logic        clk_i,
    input  logic        rst_ni,
    input  logic        start_cmd_i,
    input  logic        halt_cmd_i,
    input  logic        wfp_enable_i,
    input  logic        selected_event_i,
    input  logic        fault_inject_i,
    input  logic        addresses_aligned_i,
    input  logic        ar_done_i,
    input  logic        r_done_ok_i,
    input  logic        r_done_err_i,
    input  logic        aw_done_i,
    input  logic        w_done_i,
    input  logic        b_done_ok_i,
    input  logic        b_done_err_i,
    input  logic        loop_is_last_i,
    input  logic        fault_clear_i,
    output logic [3:0]  state_o,
    output logic        issue_ar_o,
    output logic        accept_r_o,
    output logic        issue_aw_o,
    output logic        issue_w_o,
    output logic        accept_b_o,
    output logic        post_complete_o,
    output logic        post_fault_o,
    output logic        manager_busy_o
);
    localparam [3:0] ST_STOPPED  = 4'd0;
    localparam [3:0] ST_EXEC     = 4'd1;
    localparam [3:0] ST_WFP      = 4'd2;
    localparam [3:0] ST_ISSUE_RD = 4'd3;
    localparam [3:0] ST_WAIT_RD  = 4'd4;
    localparam [3:0] ST_ISSUE_WR = 4'd5;
    localparam [3:0] ST_WAIT_B   = 4'd6;
    localparam [3:0] ST_COMP     = 4'd7;
    localparam [3:0] ST_FAULT    = 4'd8;
    localparam [3:0] ST_DONE     = 4'd9;

    logic [3:0] state_q;
    logic [3:0] state_d;

    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) state_q <= ST_STOPPED;
        else state_q <= state_d;
    end

    always @(*) begin
        state_d = state_q;

        issue_ar_o = 1'b0;
        accept_r_o = 1'b0;
        issue_aw_o = 1'b0;
        issue_w_o = 1'b0;
        accept_b_o = 1'b0;
        post_complete_o = 1'b0;
        post_fault_o = 1'b0;

        case (state_q)
            ST_STOPPED: begin
                if (start_cmd_i) begin
                    if (fault_inject_i || !addresses_aligned_i) state_d = ST_FAULT;
                    else state_d = ST_EXEC;
                end
            end

            ST_EXEC: begin
                if (halt_cmd_i) state_d = ST_STOPPED;
                else if (wfp_enable_i && !selected_event_i) state_d = ST_WFP;
                else state_d = ST_ISSUE_RD;
            end

            ST_WFP: begin
                if (halt_cmd_i) state_d = ST_STOPPED;
                else if (selected_event_i) state_d = ST_ISSUE_RD;
            end

            ST_ISSUE_RD: begin
                issue_ar_o = 1'b1;
                if (ar_done_i) state_d = ST_WAIT_RD;
            end

            ST_WAIT_RD: begin
                accept_r_o = 1'b1;
                if (r_done_err_i) state_d = ST_FAULT;
                else if (r_done_ok_i) state_d = ST_ISSUE_WR;
            end

            ST_ISSUE_WR: begin
                issue_aw_o = 1'b1;
                issue_w_o = 1'b1;
                if (aw_done_i && w_done_i) state_d = ST_WAIT_B;
            end

            ST_WAIT_B: begin
                accept_b_o = 1'b1;
                if (b_done_err_i) state_d = ST_FAULT;
                else if (b_done_ok_i) begin
                    if (loop_is_last_i) state_d = ST_COMP;
                    else state_d = ST_ISSUE_RD;
                end
            end

            ST_COMP: begin
                post_complete_o = 1'b1;
                state_d = ST_DONE;
            end

            ST_FAULT: begin
                post_fault_o = 1'b1;
                if (fault_clear_i) state_d = ST_STOPPED;
            end

            ST_DONE: begin
                if (!start_cmd_i && !halt_cmd_i) state_d = ST_STOPPED;
            end

            default: begin
                state_d = ST_STOPPED;
            end
        endcase
    end

    always @(*) begin
        state_o = 4'd0;
        case (state_q)
            ST_STOPPED:  state_o = 4'd0;
            ST_EXEC:     state_o = 4'd1;
            ST_WFP:      state_o = 4'd2;
            ST_COMP:     state_o = 4'd6;
            ST_FAULT:    state_o = 4'd8;
            ST_DONE:     state_o = 4'd6;
            default:     state_o = 4'd1;
        endcase
    end

    assign manager_busy_o = (state_q != ST_STOPPED) && (state_q != ST_DONE);

endmodule
