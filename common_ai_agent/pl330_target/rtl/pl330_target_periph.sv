`default_nettype none

// PL330 TARGET periph behavior-owner module.
// Traceability evidence: RTL_MODULE_PL330_TARGET_PERIPH, workflow_todos.rtl-gen[8],
// sub_modules[7], rtl_todo_plan, parameters.NUM_PERIPH_REQS,
// sub_modules.pl330_target_periph.module_equivalence.
// This module implements the PL330 peripheral_request transaction and the
// periph_dr_da handshake rule by latching DR requests, arbitrating them fairly,
// presenting one request at a time to the target engine, and pulsing DA when the
// request is accepted at the RTL module boundary observed by equivalence tests.

module pl330_target_periph #(
    parameter integer NUM_PERIPH_REQS = 32,
    parameter integer REQ_TYPE_W      = 2,
    parameter integer PERIPH_ID_W     = (NUM_PERIPH_REQS <= 1) ? 1 : $clog2(NUM_PERIPH_REQS),
    parameter integer COUNT_W         = (NUM_PERIPH_REQS <= 1) ? 1 : $clog2(NUM_PERIPH_REQS + 1)
) (
    input  wire                                 clk,
    input  wire                                 rst_n,

    input  wire [NUM_PERIPH_REQS-1:0]           cfg_periph_enable_i,

    input  wire [NUM_PERIPH_REQS-1:0]           periph_drvalid_i,
    input  wire [NUM_PERIPH_REQS-1:0]           periph_drlast_i,
    input  wire [(NUM_PERIPH_REQS*REQ_TYPE_W)-1:0] periph_drtype_i,
    output reg  [NUM_PERIPH_REQS-1:0]           periph_daready_o,

    output reg                                  engine_periph_valid_o,
    input  wire                                 engine_periph_ready_i,
    output reg  [PERIPH_ID_W-1:0]               engine_periph_id_o,
    output reg  [REQ_TYPE_W-1:0]                engine_periph_type_o,
    output reg                                  engine_periph_last_o,

    input  wire                                 engine_periph_done_i,
    input  wire [PERIPH_ID_W-1:0]               engine_periph_done_id_i,

    output wire [NUM_PERIPH_REQS-1:0]           pending_mask_o,
    output wire [NUM_PERIPH_REQS-1:0]           active_mask_o,
    output reg                                  any_pending_o,
    output reg                                  any_active_o,
    output reg  [COUNT_W-1:0]                   pending_count_o,
    output reg  [COUNT_W-1:0]                   active_count_o,
    output wire [PERIPH_ID_W-1:0]               rr_pointer_o
);

    localparam [REQ_TYPE_W-1:0] REQ_TYPE_ZERO = {REQ_TYPE_W{1'b0}};
    localparam [PERIPH_ID_W-1:0] PERIPH_ID_ZERO = {PERIPH_ID_W{1'b0}};

    reg  [NUM_PERIPH_REQS-1:0] pending_q;
    reg  [NUM_PERIPH_REQS-1:0] active_q;
    reg  [NUM_PERIPH_REQS-1:0] last_q;
    reg  [PERIPH_ID_W-1:0]     rr_ptr_q;

    wire [NUM_PERIPH_REQS-1:0] enabled_dr_w;
    wire [NUM_PERIPH_REQS-1:0] capture_w;
    wire                       request_fire_w;

    wire [REQ_TYPE_W-1:0] dr_type_w [0:NUM_PERIPH_REQS-1];
    reg  [REQ_TYPE_W-1:0] type_q    [0:NUM_PERIPH_REQS-1];

    reg                       grant_valid_c;
    reg  [PERIPH_ID_W-1:0]    grant_id_c;
    reg  [REQ_TYPE_W-1:0]     grant_type_c;
    reg                       grant_last_c;

    integer ch;
    integer scan_offset;
    integer scan_index;
    integer count_index;

    wire [PERIPH_ID_W-1:0] scan_index_id_w = scan_index[PERIPH_ID_W-1:0];

    genvar g;
    generate
        for (g = 0; g < NUM_PERIPH_REQS; g = g + 1) begin : gen_dr_type_unpack
            assign dr_type_w[g] = periph_drtype_i[(g*REQ_TYPE_W) +: REQ_TYPE_W];
        end
    endgenerate

    assign enabled_dr_w   = periph_drvalid_i & cfg_periph_enable_i;
    assign capture_w      = enabled_dr_w & ~pending_q & ~active_q;
    assign request_fire_w = grant_valid_c & engine_periph_ready_i;
    assign pending_mask_o = pending_q;
    assign active_mask_o  = active_q;
    assign rr_pointer_o   = rr_ptr_q;

    always @(*) begin
        grant_valid_c = 1'b0;
        grant_id_c    = PERIPH_ID_ZERO;
        grant_type_c  = REQ_TYPE_ZERO;
        grant_last_c  = 1'b0;
        scan_index    = 0;

        for (scan_offset = 0; scan_offset < NUM_PERIPH_REQS; scan_offset = scan_offset + 1) begin
            scan_index = {{(32-PERIPH_ID_W){1'b0}}, rr_ptr_q} + scan_offset;
            if (scan_index >= NUM_PERIPH_REQS) begin
                scan_index = scan_index - NUM_PERIPH_REQS;
            end

            if ((grant_valid_c == 1'b0) && (pending_q[scan_index] == 1'b1)) begin
                grant_valid_c = 1'b1;
                grant_id_c    = scan_index_id_w;
                grant_type_c  = type_q[scan_index];
                grant_last_c  = last_q[scan_index];
            end
        end
    end

    always @(*) begin
        engine_periph_valid_o = grant_valid_c;
        engine_periph_id_o    = grant_id_c;
        engine_periph_type_o  = grant_type_c;
        engine_periph_last_o  = grant_last_c;

        periph_daready_o = {NUM_PERIPH_REQS{1'b0}};
        if (request_fire_w == 1'b1) begin
            for (count_index = 0; count_index < NUM_PERIPH_REQS; count_index = count_index + 1) begin
                if ({{(32-PERIPH_ID_W){1'b0}}, grant_id_c} == count_index) begin
                    periph_daready_o[count_index] = 1'b1;
                end
            end
        end
    end

    always @(*) begin
        any_pending_o   = 1'b0;
        any_active_o    = 1'b0;
        pending_count_o = {COUNT_W{1'b0}};
        active_count_o  = {COUNT_W{1'b0}};

        for (count_index = 0; count_index < NUM_PERIPH_REQS; count_index = count_index + 1) begin
            if (pending_q[count_index] == 1'b1) begin
                any_pending_o   = 1'b1;
                pending_count_o = pending_count_o + {{(COUNT_W-1){1'b0}}, 1'b1};
            end
            if (active_q[count_index] == 1'b1) begin
                any_active_o   = 1'b1;
                active_count_o = active_count_o + {{(COUNT_W-1){1'b0}}, 1'b1};
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (rst_n == 1'b0) begin
            pending_q <= {NUM_PERIPH_REQS{1'b0}};
            active_q  <= {NUM_PERIPH_REQS{1'b0}};
            last_q    <= {NUM_PERIPH_REQS{1'b0}};
            rr_ptr_q  <= PERIPH_ID_ZERO;
            for (ch = 0; ch < NUM_PERIPH_REQS; ch = ch + 1) begin
                type_q[ch] <= REQ_TYPE_ZERO;
            end
        end else begin
            for (ch = 0; ch < NUM_PERIPH_REQS; ch = ch + 1) begin
                if (capture_w[ch] == 1'b1) begin
                    pending_q[ch] <= 1'b1;
                    last_q[ch]    <= periph_drlast_i[ch];
                    type_q[ch]    <= dr_type_w[ch];
                end

                if ((engine_periph_done_i == 1'b1) && ({{(32-PERIPH_ID_W){1'b0}}, engine_periph_done_id_i} == ch)) begin
                    active_q[ch] <= 1'b0;
                end

                if ((request_fire_w == 1'b1) && ({{(32-PERIPH_ID_W){1'b0}}, grant_id_c} == ch)) begin
                    pending_q[ch] <= 1'b0;
                    active_q[ch]  <= 1'b1;
                end
            end

            if (request_fire_w == 1'b1) begin
                if (grant_id_c == PERIPH_ID_W'(NUM_PERIPH_REQS - 1)) begin
                    rr_ptr_q <= PERIPH_ID_ZERO;
                end else begin
                    rr_ptr_q <= grant_id_c + {{(PERIPH_ID_W-1){1'b0}}, 1'b1};
                end
            end
        end
    end

endmodule

`default_nettype wire
