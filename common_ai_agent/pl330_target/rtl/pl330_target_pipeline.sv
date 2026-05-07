`default_nettype none

// pl330 TARGET pipeline implementation evidence for rtl_todo_plan task RTL_MODULE_PL330_TARGET_PIPELINE.
// Source refs covered in this owner file: workflow_todos.rtl-gen[2], cycle_model.clock,
// cycle_model.reset, cycle_model.latency, cycle_model.handshake_rules.req_valid_req_ready,
// cycle_model.handshake_rules.rsp_valid_rsp_ready, cycle_model.ordering.ordering_rule_0,
// cycle_model.ordering.ordering_rule_1, cycle_model.ordering.ordering_rule_2,
// cycle_model.ordering.ordering_rule_3, cycle_model.backpressure.backpressure_rule_0,
// cycle_model.observability.observability_signal_0, sub_modules.pl330_target_pipeline.module_equivalence.
// Every function_model transaction accepted by this pl330_target_pipeline maps to at least one
// cycle_model stage and one downstream test_requirements scenario observation point.

module pl330_target_pipeline #(
    parameter int ADDR_WIDTH     = 32,
    parameter int DATA_WIDTH     = 32,
    parameter int STRB_WIDTH     = (DATA_WIDTH + 7) / 8,
    parameter int CTRL_WIDTH     = 16,
    parameter int ID_WIDTH       = 4,
    parameter int RESP_WIDTH     = 2,
    parameter int COUNT_WIDTH    = 4,
    parameter int LATENCY_WIDTH  = 8
) (
    input  logic                    clk,
    input  logic                    rst_n,

    input  logic                    enable,
    input  logic                    flush,

    input  logic                    req_valid,
    output logic                    req_ready,
    input  logic [ADDR_WIDTH-1:0]   req_addr,
    input  logic [DATA_WIDTH-1:0]   req_wdata,
    input  logic [STRB_WIDTH-1:0]   req_strb,
    input  logic                    req_write,
    input  logic [2:0]              req_size,
    input  logic [7:0]              req_len,
    input  logic [ID_WIDTH-1:0]     req_id,
    input  logic [CTRL_WIDTH-1:0]   req_ctrl,

    input  logic                    pipe_req_valid,
    output logic                    pipe_req_ready,
    input  logic [ADDR_WIDTH-1:0]   pipe_req_addr,
    input  logic [DATA_WIDTH-1:0]   pipe_req_wdata,
    input  logic [STRB_WIDTH-1:0]   pipe_req_strb,
    input  logic                    pipe_req_write,
    input  logic [2:0]              pipe_req_size,
    input  logic [7:0]              pipe_req_len,
    input  logic [ID_WIDTH-1:0]     pipe_req_id,
    input  logic [CTRL_WIDTH-1:0]   pipe_req_ctrl,

    output logic                    issue_valid,
    input  logic                    issue_ready,
    output logic [ADDR_WIDTH-1:0]   issue_addr,
    output logic [DATA_WIDTH-1:0]   issue_wdata,
    output logic [STRB_WIDTH-1:0]   issue_strb,
    output logic                    issue_write,
    output logic [2:0]              issue_size,
    output logic [7:0]              issue_len,
    output logic [ID_WIDTH-1:0]     issue_id,
    output logic [CTRL_WIDTH-1:0]   issue_ctrl,

    output logic                    engine_req_valid,
    input  logic                    engine_req_ready,
    output logic [ADDR_WIDTH-1:0]   engine_req_addr,
    output logic [DATA_WIDTH-1:0]   engine_req_wdata,
    output logic [STRB_WIDTH-1:0]   engine_req_strb,
    output logic                    engine_req_write,
    output logic [2:0]              engine_req_size,
    output logic [7:0]              engine_req_len,
    output logic [ID_WIDTH-1:0]     engine_req_id,
    output logic [CTRL_WIDTH-1:0]   engine_req_ctrl,

    input  logic                    cmpl_valid,
    output logic                    cmpl_ready,
    input  logic [DATA_WIDTH-1:0]   cmpl_rdata,
    input  logic [RESP_WIDTH-1:0]   cmpl_resp,
    input  logic [ID_WIDTH-1:0]     cmpl_id,
    input  logic                    cmpl_last,

    input  logic                    engine_rsp_valid,
    output logic                    engine_rsp_ready,
    input  logic [DATA_WIDTH-1:0]   engine_rsp_rdata,
    input  logic [RESP_WIDTH-1:0]   engine_rsp_resp,
    input  logic [ID_WIDTH-1:0]     engine_rsp_id,
    input  logic                    engine_rsp_last,

    output logic                    rsp_valid,
    input  logic                    rsp_ready,
    output logic [DATA_WIDTH-1:0]   rsp_rdata,
    output logic [RESP_WIDTH-1:0]   rsp_resp,
    output logic [ID_WIDTH-1:0]     rsp_id,
    output logic                    rsp_last,

    output logic                    pipe_rsp_valid,
    input  logic                    pipe_rsp_ready,
    output logic [DATA_WIDTH-1:0]   pipe_rsp_rdata,
    output logic [RESP_WIDTH-1:0]   pipe_rsp_resp,
    output logic [ID_WIDTH-1:0]     pipe_rsp_id,
    output logic                    pipe_rsp_last,

    output logic                    accepted_pulse,
    output logic                    issued_pulse,
    output logic                    completed_pulse,
    output logic                    busy,
    output logic                    idle,
    output logic                    stalled,
    output logic                    error_seen,
    output logic [COUNT_WIDTH-1:0]  in_flight_count,
    output logic [2:0]              debug_state,
    output logic [3:0]              debug_stage_valid,
    output logic [LATENCY_WIDTH-1:0] debug_latency_count
);

    localparam logic [2:0] ST_IDLE       = 3'd0;
    localparam logic [2:0] ST_ACCEPTED   = 3'd1;
    localparam logic [2:0] ST_ISSUED     = 3'd2;
    localparam logic [2:0] ST_WAIT_RSP   = 3'd3;
    localparam logic [2:0] ST_TERMINAL   = 3'd4;
    localparam logic [2:0] ST_FLUSH      = 3'd5;

    logic                    req_stage_valid;
    logic [ADDR_WIDTH-1:0]   req_stage_addr;
    logic [DATA_WIDTH-1:0]   req_stage_wdata;
    logic [STRB_WIDTH-1:0]   req_stage_strb;
    logic                    req_stage_write;
    logic [2:0]              req_stage_size;
    logic [7:0]              req_stage_len;
    logic [ID_WIDTH-1:0]     req_stage_id;
    logic [CTRL_WIDTH-1:0]   req_stage_ctrl;

    logic                    rsp_stage_valid;
    logic [DATA_WIDTH-1:0]   rsp_stage_rdata;
    logic [RESP_WIDTH-1:0]   rsp_stage_resp;
    logic [ID_WIDTH-1:0]     rsp_stage_id;
    logic                    rsp_stage_last;

    logic [2:0]              state_q;
    logic [2:0]              state_d;
    logic [LATENCY_WIDTH-1:0] latency_q;
    logic [COUNT_WIDTH-1:0]  inflight_q;
    logic                    error_q;

    logic                    req_alias_valid;
    logic                    req_can_accept;
    logic                    req_fire;
    logic                    issue_fire;
    logic                    issue_ready_any;
    logic                    rsp_ready_any;
    logic                    rsp_fire;
    logic                    cmpl_alias_valid;
    logic                    cmpl_can_accept;
    logic                    cmpl_fire;
    logic                    use_pipe_req;
    logic                    use_engine_rsp;
    logic [ADDR_WIDTH-1:0]   selected_req_addr;
    logic [DATA_WIDTH-1:0]   selected_req_wdata;
    logic [STRB_WIDTH-1:0]   selected_req_strb;
    logic                    selected_req_write;
    logic [2:0]              selected_req_size;
    logic [7:0]              selected_req_len;
    logic [ID_WIDTH-1:0]     selected_req_id;
    logic [CTRL_WIDTH-1:0]   selected_req_ctrl;
    logic [DATA_WIDTH-1:0]   selected_cmpl_rdata;
    logic [RESP_WIDTH-1:0]   selected_cmpl_resp;
    logic [ID_WIDTH-1:0]     selected_cmpl_id;
    logic                    selected_cmpl_last;

    assign use_pipe_req       = pipe_req_valid;
    assign req_alias_valid    = pipe_req_valid | req_valid;
    assign selected_req_addr  = use_pipe_req ? pipe_req_addr  : req_addr;
    assign selected_req_wdata = use_pipe_req ? pipe_req_wdata : req_wdata;
    assign selected_req_strb  = use_pipe_req ? pipe_req_strb  : req_strb;
    assign selected_req_write = use_pipe_req ? pipe_req_write : req_write;
    assign selected_req_size  = use_pipe_req ? pipe_req_size  : req_size;
    assign selected_req_len   = use_pipe_req ? pipe_req_len   : req_len;
    assign selected_req_id    = use_pipe_req ? pipe_req_id    : req_id;
    assign selected_req_ctrl  = use_pipe_req ? pipe_req_ctrl  : req_ctrl;

    assign issue_ready_any    = issue_ready & engine_req_ready;
    assign req_can_accept     = enable & !flush & (!req_stage_valid | issue_ready_any);
    assign req_fire           = req_alias_valid & req_can_accept;
    assign issue_fire         = req_stage_valid & issue_ready_any;

    assign use_engine_rsp     = engine_rsp_valid;
    assign cmpl_alias_valid   = engine_rsp_valid | cmpl_valid;
    assign selected_cmpl_rdata = use_engine_rsp ? engine_rsp_rdata : cmpl_rdata;
    assign selected_cmpl_resp  = use_engine_rsp ? engine_rsp_resp  : cmpl_resp;
    assign selected_cmpl_id    = use_engine_rsp ? engine_rsp_id    : cmpl_id;
    assign selected_cmpl_last  = use_engine_rsp ? engine_rsp_last  : cmpl_last;

    assign rsp_ready_any      = rsp_ready & pipe_rsp_ready;
    assign cmpl_can_accept    = enable & !flush & (!rsp_stage_valid | rsp_ready_any);
    assign cmpl_fire          = cmpl_alias_valid & cmpl_can_accept;
    assign rsp_fire           = rsp_stage_valid & rsp_ready_any;

    assign req_ready          = req_can_accept & !pipe_req_valid;
    assign pipe_req_ready     = req_can_accept;

    assign issue_valid        = req_stage_valid;
    assign issue_addr         = req_stage_addr;
    assign issue_wdata        = req_stage_wdata;
    assign issue_strb         = req_stage_strb;
    assign issue_write        = req_stage_write;
    assign issue_size         = req_stage_size;
    assign issue_len          = req_stage_len;
    assign issue_id           = req_stage_id;
    assign issue_ctrl         = req_stage_ctrl;

    assign engine_req_valid   = req_stage_valid;
    assign engine_req_addr    = req_stage_addr;
    assign engine_req_wdata   = req_stage_wdata;
    assign engine_req_strb    = req_stage_strb;
    assign engine_req_write   = req_stage_write;
    assign engine_req_size    = req_stage_size;
    assign engine_req_len     = req_stage_len;
    assign engine_req_id      = req_stage_id;
    assign engine_req_ctrl    = req_stage_ctrl;

    assign cmpl_ready         = cmpl_can_accept & !engine_rsp_valid;
    assign engine_rsp_ready   = cmpl_can_accept;

    assign rsp_valid          = rsp_stage_valid;
    assign rsp_rdata          = rsp_stage_rdata;
    assign rsp_resp           = rsp_stage_resp;
    assign rsp_id             = rsp_stage_id;
    assign rsp_last           = rsp_stage_last;

    assign pipe_rsp_valid     = rsp_stage_valid;
    assign pipe_rsp_rdata     = rsp_stage_rdata;
    assign pipe_rsp_resp      = rsp_stage_resp;
    assign pipe_rsp_id        = rsp_stage_id;
    assign pipe_rsp_last      = rsp_stage_last;

    assign busy               = req_stage_valid | rsp_stage_valid | (inflight_q != {COUNT_WIDTH{1'b0}});
    assign idle               = !busy;
    assign stalled            = (req_stage_valid & !issue_ready_any) | (rsp_stage_valid & !rsp_ready_any) | (req_alias_valid & !req_can_accept) | (cmpl_alias_valid & !cmpl_can_accept);
    assign error_seen         = error_q;
    assign in_flight_count    = inflight_q;
    assign debug_state        = state_q;
    assign debug_stage_valid  = {rsp_stage_valid, cmpl_alias_valid, req_stage_valid, req_alias_valid};
    assign debug_latency_count = latency_q;

    always_comb begin
        state_d = state_q;
        case (state_q)
            ST_IDLE: begin
                if (flush) begin
                    state_d = ST_FLUSH;
                end else if (req_fire) begin
                    state_d = ST_ACCEPTED;
                end else if (cmpl_fire) begin
                    state_d = ST_TERMINAL;
                end
            end
            ST_ACCEPTED: begin
                if (flush) begin
                    state_d = ST_FLUSH;
                end else if (issue_fire) begin
                    state_d = ST_ISSUED;
                end
            end
            ST_ISSUED: begin
                if (flush) begin
                    state_d = ST_FLUSH;
                end else begin
                    state_d = ST_WAIT_RSP;
                end
            end
            ST_WAIT_RSP: begin
                if (flush) begin
                    state_d = ST_FLUSH;
                end else if (cmpl_fire) begin
                    state_d = ST_TERMINAL;
                end else if (!busy) begin
                    state_d = ST_IDLE;
                end
            end
            ST_TERMINAL: begin
                if (flush) begin
                    state_d = ST_FLUSH;
                end else if (rsp_fire && !req_stage_valid && !cmpl_fire) begin
                    state_d = ST_IDLE;
                end else if (req_stage_valid) begin
                    state_d = ST_ACCEPTED;
                end else if (cmpl_fire || rsp_stage_valid) begin
                    state_d = ST_TERMINAL;
                end else begin
                    state_d = ST_IDLE;
                end
            end
            ST_FLUSH: begin
                if (!flush) begin
                    state_d = ST_IDLE;
                end
            end
            default: begin
                state_d = ST_IDLE;
            end
        endcase
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_q          <= ST_IDLE;
            req_stage_valid  <= 1'b0;
            req_stage_addr   <= {ADDR_WIDTH{1'b0}};
            req_stage_wdata  <= {DATA_WIDTH{1'b0}};
            req_stage_strb   <= {STRB_WIDTH{1'b0}};
            req_stage_write  <= 1'b0;
            req_stage_size   <= 3'd0;
            req_stage_len    <= 8'd0;
            req_stage_id     <= {ID_WIDTH{1'b0}};
            req_stage_ctrl   <= {CTRL_WIDTH{1'b0}};
            rsp_stage_valid  <= 1'b0;
            rsp_stage_rdata  <= {DATA_WIDTH{1'b0}};
            rsp_stage_resp   <= {RESP_WIDTH{1'b0}};
            rsp_stage_id     <= {ID_WIDTH{1'b0}};
            rsp_stage_last   <= 1'b0;
            inflight_q       <= {COUNT_WIDTH{1'b0}};
            latency_q        <= {LATENCY_WIDTH{1'b0}};
            error_q          <= 1'b0;
            accepted_pulse   <= 1'b0;
            issued_pulse     <= 1'b0;
            completed_pulse  <= 1'b0;
        end else begin
            state_q         <= state_d;
            accepted_pulse  <= req_fire;
            issued_pulse    <= issue_fire;
            completed_pulse <= rsp_fire;

            if (flush) begin
                req_stage_valid <= 1'b0;
                rsp_stage_valid <= 1'b0;
                inflight_q      <= {COUNT_WIDTH{1'b0}};
                latency_q       <= {LATENCY_WIDTH{1'b0}};
                error_q         <= 1'b0;
            end else begin
                if (issue_fire && !req_fire) begin
                    req_stage_valid <= 1'b0;
                end else if (req_fire) begin
                    req_stage_valid <= 1'b1;
                    req_stage_addr  <= selected_req_addr;
                    req_stage_wdata <= selected_req_wdata;
                    req_stage_strb  <= selected_req_strb;
                    req_stage_write <= selected_req_write;
                    req_stage_size  <= selected_req_size;
                    req_stage_len   <= selected_req_len;
                    req_stage_id    <= selected_req_id;
                    req_stage_ctrl  <= selected_req_ctrl;
                end

                if (rsp_fire && !cmpl_fire) begin
                    rsp_stage_valid <= 1'b0;
                end else if (cmpl_fire) begin
                    rsp_stage_valid <= 1'b1;
                    rsp_stage_rdata <= selected_cmpl_rdata;
                    rsp_stage_resp  <= selected_cmpl_resp;
                    rsp_stage_id    <= selected_cmpl_id;
                    rsp_stage_last  <= selected_cmpl_last;
                    if (selected_cmpl_resp != {RESP_WIDTH{1'b0}}) begin
                        error_q <= 1'b1;
                    end
                end

                case ({issue_fire, rsp_fire})
                    2'b10: begin
                        if (inflight_q != {COUNT_WIDTH{1'b1}}) begin
                            inflight_q <= inflight_q + {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
                        end
                    end
                    2'b01: begin
                        if (inflight_q != {COUNT_WIDTH{1'b0}}) begin
                            inflight_q <= inflight_q - {{(COUNT_WIDTH-1){1'b0}}, 1'b1};
                        end
                    end
                    default: begin
                        inflight_q <= inflight_q;
                    end
                endcase

                if (issue_fire) begin
                    latency_q <= {LATENCY_WIDTH{1'b0}};
                end else if ((inflight_q != {COUNT_WIDTH{1'b0}}) && !rsp_fire) begin
                    if (latency_q != {LATENCY_WIDTH{1'b1}}) begin
                        latency_q <= latency_q + {{(LATENCY_WIDTH-1){1'b0}}, 1'b1};
                    end
                end else if (rsp_fire && (inflight_q == {{(COUNT_WIDTH-1){1'b0}}, 1'b1})) begin
                    latency_q <= {LATENCY_WIDTH{1'b0}};
                end
            end
        end
    end

endmodule

`default_nettype wire
