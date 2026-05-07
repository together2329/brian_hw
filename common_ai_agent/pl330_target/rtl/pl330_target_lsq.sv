`default_nettype none

// Traceability: PL330 TARGET LSQ pl330 target lsq pl330_target_lsq plan rtl_todo_plan sub sub_modules modules RTL_MODULE_PL330_TARGET_LSQ.
// Source refs covered by this owner file: workflow_todos.rtl-gen[3], sub_modules[2], function_model.transactions.load, function_model.transactions.store, cycle_model.ordering.lsq_order.
// Equivalence intent: accepted load and store transactions are issued to the memory boundary in first-in first-out LSQ order; load and store response tags preserve FunctionalModel.apply transaction order.
module pl330_target_lsq #(
    parameter int ADDR_WIDTH  = 32,
    parameter int DATA_WIDTH  = 32,
    parameter int STRB_WIDTH  = (DATA_WIDTH / 8),
    parameter int TAG_WIDTH   = 8,
    parameter int SIZE_WIDTH  = 3,
    parameter int LSQ_DEPTH   = 8,
    parameter int COUNT_WIDTH = 4
) (
    input  logic                         clk,
    input  logic                         rst_n,
    input  logic                         flush_i,

    input  logic                         load_valid_i,
    output logic                         load_ready_o,
    input  logic [ADDR_WIDTH-1:0]        load_addr_i,
    input  logic [SIZE_WIDTH-1:0]        load_size_i,
    input  logic                         load_signed_i,
    input  logic [TAG_WIDTH-1:0]         load_tag_i,
    output logic                         load_resp_valid_o,
    input  logic                         load_resp_ready_i,
    output logic [DATA_WIDTH-1:0]        load_resp_data_o,
    output logic [TAG_WIDTH-1:0]         load_resp_tag_o,
    output logic                         load_resp_error_o,

    input  logic                         store_valid_i,
    output logic                         store_ready_o,
    input  logic [ADDR_WIDTH-1:0]        store_addr_i,
    input  logic [SIZE_WIDTH-1:0]        store_size_i,
    input  logic [DATA_WIDTH-1:0]        store_data_i,
    input  logic [STRB_WIDTH-1:0]        store_strb_i,
    input  logic [TAG_WIDTH-1:0]         store_tag_i,
    output logic                         store_resp_valid_o,
    input  logic                         store_resp_ready_i,
    output logic [TAG_WIDTH-1:0]         store_resp_tag_o,
    output logic                         store_resp_error_o,

    output logic                         mem_req_valid_o,
    input  logic                         mem_req_ready_i,
    output logic                         mem_req_write_o,
    output logic [ADDR_WIDTH-1:0]        mem_req_addr_o,
    output logic [DATA_WIDTH-1:0]        mem_req_wdata_o,
    output logic [STRB_WIDTH-1:0]        mem_req_wstrb_o,
    output logic [SIZE_WIDTH-1:0]        mem_req_size_o,
    input  logic                         mem_rsp_valid_i,
    output logic                         mem_rsp_ready_o,
    input  logic [DATA_WIDTH-1:0]        mem_rsp_rdata_i,
    input  logic                         mem_rsp_error_i,

    output logic                         busy_o,
    output logic                         empty_o,
    output logic [COUNT_WIDTH-1:0]       outstanding_count_o,
    output logic                         ordering_violation_o
);

    localparam logic ENTRY_LOAD  = 1'b0;
    localparam logic ENTRY_STORE = 1'b1;
    localparam logic [31:0] LSQ_DEPTH_U32 = LSQ_DEPTH;
    localparam logic [31:0] LSQ_LAST_U32  = LSQ_DEPTH_U32 - 32'd1;

    logic [31:0]                  head_q;
    logic [31:0]                  tail_q;
    logic [31:0]                  count_q;

    logic                         q_is_store [0:LSQ_DEPTH-1];
    logic [ADDR_WIDTH-1:0]        q_addr     [0:LSQ_DEPTH-1];
    logic [SIZE_WIDTH-1:0]        q_size     [0:LSQ_DEPTH-1];
    logic [DATA_WIDTH-1:0]        q_wdata    [0:LSQ_DEPTH-1];
    logic [STRB_WIDTH-1:0]        q_wstrb    [0:LSQ_DEPTH-1];
    logic [TAG_WIDTH-1:0]         q_tag      [0:LSQ_DEPTH-1];
    logic                         q_signed   [0:LSQ_DEPTH-1];

    logic                         active_q;
    logic                         active_is_store_q;
    logic                         active_signed_q;
    logic [SIZE_WIDTH-1:0]        active_size_q;
    logic [TAG_WIDTH-1:0]         active_tag_q;

    logic                         load_resp_valid_q;
    logic [DATA_WIDTH-1:0]        load_resp_data_q;
    logic [TAG_WIDTH-1:0]         load_resp_tag_q;
    logic                         load_resp_error_q;

    logic                         store_resp_valid_q;
    logic [TAG_WIDTH-1:0]         store_resp_tag_q;
    logic                         store_resp_error_q;

    logic                         ordering_violation_q;

    wire                          full_w;
    wire                          issue_ready_w;
    wire                          issue_fire_w;
    wire                          load_enq_w;
    wire                          store_enq_w;
    wire                          enq_fire_w;
    wire                          response_slot_free_w;
    wire                          rsp_fire_w;

    assign full_w               = (count_q >= LSQ_DEPTH_U32);
    assign store_ready_o        = (!full_w) && (!flush_i);
    assign load_ready_o         = (!full_w) && (!flush_i) && (!store_valid_i);
    assign store_enq_w          = store_valid_i && store_ready_o;
    assign load_enq_w           = load_valid_i && load_ready_o;
    assign enq_fire_w           = store_enq_w || load_enq_w;
    assign response_slot_free_w = (!load_resp_valid_q) && (!store_resp_valid_q);
    assign issue_ready_w        = (count_q != 32'd0) && (!active_q) && response_slot_free_w && (!flush_i);
    assign issue_fire_w         = issue_ready_w && mem_req_ready_i;
    assign mem_rsp_ready_o      = active_q && response_slot_free_w && (!flush_i);
    assign rsp_fire_w           = mem_rsp_valid_i && mem_rsp_ready_o;

    assign load_resp_valid_o    = load_resp_valid_q;
    assign load_resp_data_o     = load_resp_data_q;
    assign load_resp_tag_o      = load_resp_tag_q;
    assign load_resp_error_o    = load_resp_error_q;
    assign store_resp_valid_o   = store_resp_valid_q;
    assign store_resp_tag_o     = store_resp_tag_q;
    assign store_resp_error_o   = store_resp_error_q;
    assign busy_o               = (count_q != 32'd0) || active_q || load_resp_valid_q || store_resp_valid_q;
    assign empty_o              = (count_q == 32'd0) && (!active_q) && (!load_resp_valid_q) && (!store_resp_valid_q);
    assign outstanding_count_o  = count_q[COUNT_WIDTH-1:0];
    assign ordering_violation_o = ordering_violation_q;

    always_comb begin
        mem_req_valid_o = issue_ready_w;
        mem_req_write_o = ENTRY_LOAD;
        mem_req_addr_o  = {ADDR_WIDTH{1'b0}};
        mem_req_wdata_o = {DATA_WIDTH{1'b0}};
        mem_req_wstrb_o = {STRB_WIDTH{1'b0}};
        mem_req_size_o  = {SIZE_WIDTH{1'b0}};

        if (issue_ready_w) begin
            mem_req_write_o = q_is_store[head_q];
            mem_req_addr_o  = q_addr[head_q];
            mem_req_wdata_o = q_wdata[head_q];
            mem_req_wstrb_o = q_is_store[head_q] ? q_wstrb[head_q] : {STRB_WIDTH{1'b0}};
            mem_req_size_o  = q_size[head_q];
        end
    end

    integer i;
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            head_q               <= 32'd0;
            tail_q               <= 32'd0;
            count_q              <= 32'd0;
            active_q             <= 1'b0;
            active_is_store_q    <= ENTRY_LOAD;
            active_signed_q      <= 1'b0;
            active_size_q        <= {SIZE_WIDTH{1'b0}};
            active_tag_q         <= {TAG_WIDTH{1'b0}};
            load_resp_valid_q    <= 1'b0;
            load_resp_data_q     <= {DATA_WIDTH{1'b0}};
            load_resp_tag_q      <= {TAG_WIDTH{1'b0}};
            load_resp_error_q    <= 1'b0;
            store_resp_valid_q   <= 1'b0;
            store_resp_tag_q     <= {TAG_WIDTH{1'b0}};
            store_resp_error_q   <= 1'b0;
            ordering_violation_q <= 1'b0;
            for (i = 0; i < LSQ_DEPTH; i = i + 1) begin
                q_is_store[i] <= ENTRY_LOAD;
                q_addr[i]     <= {ADDR_WIDTH{1'b0}};
                q_size[i]     <= {SIZE_WIDTH{1'b0}};
                q_wdata[i]    <= {DATA_WIDTH{1'b0}};
                q_wstrb[i]    <= {STRB_WIDTH{1'b0}};
                q_tag[i]      <= {TAG_WIDTH{1'b0}};
                q_signed[i]   <= 1'b0;
            end
        end else begin
            ordering_violation_q <= 1'b0;

                if (flush_i) begin
                    head_q             <= 32'd0;
                    tail_q             <= 32'd0;
                    count_q            <= 32'd0;
                    active_q           <= 1'b0;
                    active_signed_q    <= 1'b0;
                    active_size_q      <= {SIZE_WIDTH{1'b0}};
                    load_resp_valid_q  <= 1'b0;
                    store_resp_valid_q <= 1'b0;
            end else begin
                if (load_resp_valid_q && load_resp_ready_i) begin
                    load_resp_valid_q <= 1'b0;
                end
                if (store_resp_valid_q && store_resp_ready_i) begin
                    store_resp_valid_q <= 1'b0;
                end

                if (mem_rsp_valid_i && (!active_q)) begin
                    ordering_violation_q <= 1'b1;
                end

                if (rsp_fire_w) begin
                    active_q <= 1'b0;
                    if (active_is_store_q) begin
                        store_resp_valid_q <= 1'b1;
                        store_resp_tag_q   <= active_tag_q;
                        store_resp_error_q <= mem_rsp_error_i;
                    end else begin
                        load_resp_valid_q <= 1'b1;
                        if (active_signed_q && (active_size_q == 3'd0)) begin
                            load_resp_data_q <= {{(DATA_WIDTH-8){mem_rsp_rdata_i[7]}}, mem_rsp_rdata_i[7:0]};
                        end else if (active_signed_q && (active_size_q == 3'd1)) begin
                            load_resp_data_q <= {{(DATA_WIDTH-16){mem_rsp_rdata_i[15]}}, mem_rsp_rdata_i[15:0]};
                        end else begin
                            load_resp_data_q <= mem_rsp_rdata_i;
                        end
                        load_resp_tag_q   <= active_tag_q;
                        load_resp_error_q <= mem_rsp_error_i;
                    end
                end

                if (issue_fire_w) begin
                    active_q          <= 1'b1;
                    active_is_store_q <= q_is_store[head_q];
                    active_signed_q   <= q_signed[head_q];
                    active_size_q     <= q_size[head_q];
                    active_tag_q      <= q_tag[head_q];
                    if (head_q == LSQ_LAST_U32) begin
                        head_q <= 32'd0;
                    end else begin
                        head_q <= head_q + 32'd1;
                    end
                end

                if (store_enq_w) begin
                    q_is_store[tail_q] <= ENTRY_STORE;
                    q_addr[tail_q]     <= store_addr_i;
                    q_size[tail_q]     <= store_size_i;
                    q_wdata[tail_q]    <= store_data_i;
                    q_wstrb[tail_q]    <= store_strb_i;
                    q_tag[tail_q]      <= store_tag_i;
                    q_signed[tail_q]   <= 1'b0;
                    if (tail_q == LSQ_LAST_U32) begin
                        tail_q <= 32'd0;
                    end else begin
                        tail_q <= tail_q + 32'd1;
                    end
                end else if (load_enq_w) begin
                    q_is_store[tail_q] <= ENTRY_LOAD;
                    q_addr[tail_q]     <= load_addr_i;
                    q_size[tail_q]     <= load_size_i;
                    q_wdata[tail_q]    <= {DATA_WIDTH{1'b0}};
                    q_wstrb[tail_q]    <= {STRB_WIDTH{1'b0}};
                    q_tag[tail_q]      <= load_tag_i;
                    q_signed[tail_q]   <= load_signed_i;
                    if (tail_q == LSQ_LAST_U32) begin
                        tail_q <= 32'd0;
                    end else begin
                        tail_q <= tail_q + 32'd1;
                    end
                end

                case ({enq_fire_w, issue_fire_w})
                    2'b10: count_q <= count_q + 32'd1;
                    2'b01: count_q <= count_q - 32'd1;
                    default: count_q <= count_q;
                endcase
            end
        end
    end

endmodule

`default_nettype wire
