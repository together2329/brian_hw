`default_nettype none

module pl330_target_engine #(
    parameter integer NUM_CHANNELS       = 8,
    parameter integer ADDR_WIDTH         = 32,
    parameter integer DATA_WIDTH         = 32,
    parameter integer LEN_WIDTH          = 16,
    parameter integer OPCODE_WIDTH       = 8,
    parameter integer CHANNEL_ID_WIDTH   = 3,
    parameter integer OUTSTANDING_WIDTH  = 5,
    parameter integer MAX_OUTSTANDING    = 16
) (
    input  logic                           clk,
    input  logic                           rst_n,

    input  logic                           cmd_valid,
    output logic                           cmd_ready,
    input  logic [CHANNEL_ID_WIDTH-1:0]    cmd_channel,
    input  logic [OPCODE_WIDTH-1:0]        cmd_opcode,
    input  logic [ADDR_WIDTH-1:0]          cmd_src_addr,
    input  logic [ADDR_WIDTH-1:0]          cmd_dst_addr,
    input  logic [LEN_WIDTH-1:0]           cmd_len,
    input  logic                           cmd_secure,
    input  logic                           cmd_privileged,

    output logic                           rsp_valid,
    input  logic                           rsp_ready,
    output logic [CHANNEL_ID_WIDTH-1:0]    rsp_channel,
    output logic [1:0]                     rsp_status,
    output logic [LEN_WIDTH-1:0]           rsp_bytes_remaining,

    output logic                           fetch_req_valid,
    input  logic                           fetch_req_ready,
    output logic [CHANNEL_ID_WIDTH-1:0]    fetch_req_channel,
    output logic [ADDR_WIDTH-1:0]          fetch_req_addr,
    output logic                           fetch_req_secure,
    output logic                           fetch_req_privileged,
    input  logic                           fetch_rsp_valid,
    output logic                           fetch_rsp_ready,
    input  logic [DATA_WIDTH-1:0]          fetch_rsp_data,
    input  logic                           fetch_rsp_error,

    output logic                           rd_req_valid,
    input  logic                           rd_req_ready,
    output logic [CHANNEL_ID_WIDTH-1:0]    rd_req_channel,
    output logic [ADDR_WIDTH-1:0]          rd_req_addr,
    output logic [LEN_WIDTH-1:0]           rd_req_len,
    output logic                           rd_req_secure,
    output logic                           rd_req_privileged,
    input  logic                           rd_rsp_valid,
    output logic                           rd_rsp_ready,
    input  logic                           rd_rsp_error,

    output logic                           wr_req_valid,
    input  logic                           wr_req_ready,
    output logic [CHANNEL_ID_WIDTH-1:0]    wr_req_channel,
    output logic [ADDR_WIDTH-1:0]          wr_req_addr,
    output logic [LEN_WIDTH-1:0]           wr_req_len,
    output logic                           wr_req_secure,
    output logic                           wr_req_privileged,
    input  logic                           wr_rsp_valid,
    output logic                           wr_rsp_ready,
    input  logic                           wr_rsp_error,

    output logic                           busy,
    output logic                           idle,
    output logic                           error_valid,
    output logic [3:0]                     error_code,
    output logic [2:0]                     engine_state,
    output logic [1:0]                     channel_state,
    output logic [OUTSTANDING_WIDTH-1:0]   outstanding_reads,
    output logic [OUTSTANDING_WIDTH-1:0]   outstanding_writes,
    output logic                           stage_s0_valid,
    output logic                           stage_s1_valid,
    output logic                           stage_s2_valid,
    output logic [DATA_WIDTH-1:0]          observed_fetch_data
);

    // Traceability: RTL_MODULE_PL330_TARGET_ENGINE, pl330_target_engine, PL330 TARGET engine.
    // Traceability: sub_modules[0], workflow_todos.rtl-gen[1], rtl_todo_plan, todo_plan_sha256=67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc.
    // Traceability: function_model.transactions.fetch, function_model.transactions.decode, function_model.transactions.execute.
    // Traceability: function_model.invariants.invariant_0 outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS.
    // Traceability: function_model.invariants.invariant_1 outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS.
    // Traceability: function_model.invariants.invariant_3 channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0.
    // Traceability: cycle_model.pipeline.S0_ACCEPT, cycle_model.pipeline.S1_EVALUATE, cycle_model.pipeline.S2_OBSERVE.

    localparam logic [2:0] ENGINE_IDLE        = 3'd0;
    localparam logic [2:0] ENGINE_S0_ACCEPT   = 3'd1;
    localparam logic [2:0] ENGINE_S1_EVALUATE = 3'd2;
    localparam logic [2:0] ENGINE_S2_OBSERVE  = 3'd3;

    localparam logic [1:0] CHANNEL_IDLE       = 2'd0;
    localparam logic [1:0] CHANNEL_ACTIVE     = 2'd1;

    localparam logic [OPCODE_WIDTH-1:0] OPCODE_NOP   = 8'h00;
    localparam logic [OPCODE_WIDTH-1:0] OPCODE_FETCH = 8'h01;
    localparam logic [OPCODE_WIDTH-1:0] OPCODE_READ  = 8'h02;
    localparam logic [OPCODE_WIDTH-1:0] OPCODE_WRITE = 8'h03;
    localparam logic [OPCODE_WIDTH-1:0] OPCODE_COPY  = 8'h04;

    localparam logic [1:0] STATUS_OK          = 2'd0;
    localparam logic [1:0] STATUS_BUS_ERROR   = 2'd1;
    localparam logic [1:0] STATUS_BAD_OPCODE  = 2'd2;
    localparam logic [1:0] STATUS_NO_CREDIT   = 2'd3;

    localparam logic [3:0] ERR_NONE           = 4'd0;
    localparam logic [3:0] ERR_FETCH          = 4'd1;
    localparam logic [3:0] ERR_READ           = 4'd2;
    localparam logic [3:0] ERR_WRITE          = 4'd3;
    localparam logic [3:0] ERR_OPCODE         = 4'd4;
    localparam logic [3:0] ERR_CREDIT         = 4'd5;

    localparam logic [OUTSTANDING_WIDTH-1:0] OUTSTANDING_LIMIT = OUTSTANDING_WIDTH'(MAX_OUTSTANDING);
    localparam logic [OUTSTANDING_WIDTH-1:0] CHANNEL_CREDIT_LIMIT =
        OUTSTANDING_WIDTH'(2 * NUM_CHANNELS);

    logic s0_valid;
    logic [CHANNEL_ID_WIDTH-1:0] s0_channel;
    logic [OPCODE_WIDTH-1:0]     s0_opcode;
    logic [ADDR_WIDTH-1:0]       s0_src_addr;
    logic [ADDR_WIDTH-1:0]       s0_dst_addr;
    logic [LEN_WIDTH-1:0]        s0_len;
    logic                        s0_secure;
    logic                        s0_privileged;

    logic s1_valid;
    logic [CHANNEL_ID_WIDTH-1:0] s1_channel;
    logic [OPCODE_WIDTH-1:0]     s1_opcode;
    logic [ADDR_WIDTH-1:0]       s1_src_addr;
    logic [ADDR_WIDTH-1:0]       s1_dst_addr;
    logic [LEN_WIDTH-1:0]        s1_len;
    logic                        s1_secure;
    logic                        s1_privileged;

    logic s2_valid;
    logic s2_done;
    logic [CHANNEL_ID_WIDTH-1:0] s2_channel;
    logic [LEN_WIDTH-1:0]        s2_len;
    logic [1:0]                  s2_status;
    logic [3:0]                  s2_error_code;
    logic                        s2_wait_fetch;
    logic                        s2_wait_read;
    logic                        s2_wait_write;
    logic                        s2_seen_fetch;
    logic                        s2_seen_read;
    logic                        s2_seen_write;

    logic s1_is_nop;
    logic s1_is_fetch;
    logic s1_is_read;
    logic s1_is_write;
    logic s1_is_copy;
    logic s1_is_legal;
    logic s1_needs_fetch;
    logic s1_needs_read;
    logic s1_needs_write;
    logic s1_needs_response;
    logic s1_credit_blocked;

    logic read_credit_available;
    logic write_credit_available;
    logic op_issue_ready;
    logic s2_ready;
    logic s1_ready;
    logic s0_ready;
    logic s0_accept_fire;
    logic s0_to_s1_fire;
    logic s1_to_s2_fire;
    logic s2_rsp_fire;

    logic fetch_req_fire;
    logic rd_req_fire;
    logic wr_req_fire;
    logic fetch_rsp_fire;
    logic rd_rsp_fire;
    logic wr_rsp_fire;

    logic fetch_observed_next;
    logic read_observed_next;
    logic write_observed_next;
    logic s2_complete_next;
    logic pipeline_empty_now;
    logic pipeline_empty_next;
    logic outstanding_zero_next;

    logic [OUTSTANDING_WIDTH-1:0] reads_after_decrement;
    logic [OUTSTANDING_WIDTH-1:0] writes_after_decrement;
    logic [OUTSTANDING_WIDTH-1:0] outstanding_reads_next;
    logic [OUTSTANDING_WIDTH-1:0] outstanding_writes_next;

    assign s1_is_nop   = (s1_opcode == OPCODE_NOP);
    assign s1_is_fetch = (s1_opcode == OPCODE_FETCH);
    assign s1_is_read  = (s1_opcode == OPCODE_READ);
    assign s1_is_write = (s1_opcode == OPCODE_WRITE);
    assign s1_is_copy  = (s1_opcode == OPCODE_COPY);
    assign s1_is_legal = s1_is_nop | s1_is_fetch | s1_is_read | s1_is_write | s1_is_copy;

    assign s1_needs_fetch   = s1_is_fetch;
    assign s1_needs_read    = s1_is_read | s1_is_copy;
    assign s1_needs_write   = s1_is_write | s1_is_copy;
    assign s1_needs_response = s1_needs_fetch | s1_needs_read | s1_needs_write;

    assign read_credit_available  = (outstanding_reads < OUTSTANDING_LIMIT) &&
                                    (outstanding_reads < CHANNEL_CREDIT_LIMIT);
    assign write_credit_available = (outstanding_writes < OUTSTANDING_LIMIT) &&
                                    (outstanding_writes < CHANNEL_CREDIT_LIMIT);
    assign s1_credit_blocked = s1_valid & s1_is_legal &
                               ((s1_needs_read & (!read_credit_available)) |
                                (s1_needs_write & (!write_credit_available)));

    assign op_issue_ready = (!s1_valid) ? 1'b1 :
                            (!s1_is_legal) ? 1'b1 :
                            (s1_credit_blocked) ? 1'b1 :
                            (s1_is_nop) ? 1'b1 :
                            (s1_is_fetch) ? (fetch_req_ready & read_credit_available) :
                            (s1_is_read) ? (rd_req_ready & read_credit_available) :
                            (s1_is_write) ? (wr_req_ready & write_credit_available) :
                            (s1_is_copy) ? (rd_req_ready & wr_req_ready & read_credit_available & write_credit_available) :
                            1'b0;

    assign rsp_valid = s2_valid & s2_done;
    assign s2_rsp_fire = rsp_valid & rsp_ready;
    assign s2_ready = (!s2_valid) | s2_rsp_fire;
    assign s1_to_s2_fire = s1_valid & s2_ready & op_issue_ready;
    assign s1_ready = (!s1_valid) | s1_to_s2_fire;
    assign s0_to_s1_fire = s0_valid & s1_ready;
    assign s0_ready = (!s0_valid) | s0_to_s1_fire;
    assign cmd_ready = s0_ready;
    assign s0_accept_fire = cmd_valid & cmd_ready;

    assign fetch_req_fire = fetch_req_valid & fetch_req_ready;
    assign rd_req_fire    = rd_req_valid & rd_req_ready;
    assign wr_req_fire    = wr_req_valid & wr_req_ready;
    assign fetch_rsp_fire = fetch_rsp_valid & fetch_rsp_ready;
    assign rd_rsp_fire    = rd_rsp_valid & rd_rsp_ready;
    assign wr_rsp_fire    = wr_rsp_valid & wr_rsp_ready;

    assign fetch_observed_next = (!s2_wait_fetch) | s2_seen_fetch | fetch_rsp_fire;
    assign read_observed_next  = (!s2_wait_read)  | s2_seen_read  | rd_rsp_fire;
    assign write_observed_next = (!s2_wait_write) | s2_seen_write | wr_rsp_fire;
    assign s2_complete_next = fetch_observed_next & read_observed_next & write_observed_next;

    assign pipeline_empty_now = (!s0_valid) & (!s1_valid) & (!s2_valid);
    assign pipeline_empty_next = (!s0_valid | s0_to_s1_fire) & (!s1_valid | s1_to_s2_fire) & (!s2_valid | s2_rsp_fire) & (!s0_accept_fire);

    assign stage_s0_valid = s0_valid;
    assign stage_s1_valid = s1_valid;
    assign stage_s2_valid = s2_valid;

    always_comb begin
        fetch_req_valid      = 1'b0;
        fetch_req_channel    = s1_channel;
        fetch_req_addr       = s1_src_addr;
        fetch_req_secure     = s1_secure;
        fetch_req_privileged = s1_privileged;

        rd_req_valid         = 1'b0;
        rd_req_channel       = s1_channel;
        rd_req_addr          = s1_src_addr;
        rd_req_len           = s1_len;
        rd_req_secure        = s1_secure;
        rd_req_privileged    = s1_privileged;

        wr_req_valid         = 1'b0;
        wr_req_channel       = s1_channel;
        wr_req_addr          = s1_dst_addr;
        wr_req_len           = s1_len;
        wr_req_secure        = s1_secure;
        wr_req_privileged    = s1_privileged;

        if (s1_valid && s2_ready && s1_is_legal) begin
            if (s1_is_fetch && read_credit_available) begin
                fetch_req_valid = 1'b1;
            end
            if ((s1_is_read || s1_is_copy) && read_credit_available) begin
                rd_req_valid = 1'b1;
            end
            if ((s1_is_write || s1_is_copy) && write_credit_available) begin
                wr_req_valid = 1'b1;
            end
        end
    end

    always_comb begin
        fetch_rsp_ready = s2_valid & s2_wait_fetch & (!s2_seen_fetch) & (!s2_done);
        rd_rsp_ready    = s2_valid & s2_wait_read  & (!s2_seen_read)  & (!s2_done);
        wr_rsp_ready    = s2_valid & s2_wait_write & (!s2_seen_write) & (!s2_done);
    end

    always_comb begin
        reads_after_decrement = outstanding_reads;
        if ((fetch_rsp_fire | rd_rsp_fire) && (outstanding_reads != {OUTSTANDING_WIDTH{1'b0}})) begin
            if (fetch_rsp_fire & rd_rsp_fire) begin
                if (outstanding_reads > {{(OUTSTANDING_WIDTH-2){1'b0}}, 2'd1}) begin
                    reads_after_decrement = outstanding_reads - {{(OUTSTANDING_WIDTH-2){1'b0}}, 2'd2};
                end else begin
                    reads_after_decrement = {OUTSTANDING_WIDTH{1'b0}};
                end
            end else begin
                reads_after_decrement = outstanding_reads - {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
            end
        end

        writes_after_decrement = outstanding_writes;
        if (wr_rsp_fire && (outstanding_writes != {OUTSTANDING_WIDTH{1'b0}})) begin
            writes_after_decrement = outstanding_writes - {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
        end

        outstanding_reads_next = reads_after_decrement;
        if ((fetch_req_fire | rd_req_fire) && (reads_after_decrement < OUTSTANDING_LIMIT)) begin
            if (fetch_req_fire & rd_req_fire) begin
                if (reads_after_decrement <= (OUTSTANDING_LIMIT - {{(OUTSTANDING_WIDTH-2){1'b0}}, 2'd2})) begin
                    outstanding_reads_next = reads_after_decrement + {{(OUTSTANDING_WIDTH-2){1'b0}}, 2'd2};
                end else begin
                    outstanding_reads_next = OUTSTANDING_LIMIT;
                end
            end else begin
                outstanding_reads_next = reads_after_decrement + {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
            end
        end

        outstanding_writes_next = writes_after_decrement;
        if (wr_req_fire && (writes_after_decrement < OUTSTANDING_LIMIT)) begin
            outstanding_writes_next = writes_after_decrement + {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
        end

        if (outstanding_reads_next > OUTSTANDING_LIMIT) begin
            outstanding_reads_next = OUTSTANDING_LIMIT;
        end
        if (outstanding_writes_next > OUTSTANDING_LIMIT) begin
            outstanding_writes_next = OUTSTANDING_LIMIT;
        end
    end

    assign outstanding_zero_next = (outstanding_reads_next == {OUTSTANDING_WIDTH{1'b0}}) & (outstanding_writes_next == {OUTSTANDING_WIDTH{1'b0}});

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s0_valid      <= 1'b0;
            s0_channel    <= {CHANNEL_ID_WIDTH{1'b0}};
            s0_opcode     <= {OPCODE_WIDTH{1'b0}};
            s0_src_addr   <= {ADDR_WIDTH{1'b0}};
            s0_dst_addr   <= {ADDR_WIDTH{1'b0}};
            s0_len        <= {LEN_WIDTH{1'b0}};
            s0_secure     <= 1'b0;
            s0_privileged <= 1'b0;
        end else begin
            if (s0_to_s1_fire) begin
                s0_valid <= 1'b0;
            end
            if (s0_accept_fire) begin
                s0_valid      <= 1'b1;
                s0_channel    <= cmd_channel;
                s0_opcode     <= cmd_opcode;
                s0_src_addr   <= cmd_src_addr;
                s0_dst_addr   <= cmd_dst_addr;
                s0_len        <= cmd_len;
                s0_secure     <= cmd_secure;
                s0_privileged <= cmd_privileged;
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s1_valid      <= 1'b0;
            s1_channel    <= {CHANNEL_ID_WIDTH{1'b0}};
            s1_opcode     <= {OPCODE_WIDTH{1'b0}};
            s1_src_addr   <= {ADDR_WIDTH{1'b0}};
            s1_dst_addr   <= {ADDR_WIDTH{1'b0}};
            s1_len        <= {LEN_WIDTH{1'b0}};
            s1_secure     <= 1'b0;
            s1_privileged <= 1'b0;
        end else begin
            if (s1_to_s2_fire) begin
                s1_valid <= 1'b0;
            end
            if (s0_to_s1_fire) begin
                s1_valid      <= 1'b1;
                s1_channel    <= s0_channel;
                s1_opcode     <= s0_opcode;
                s1_src_addr   <= s0_src_addr;
                s1_dst_addr   <= s0_dst_addr;
                s1_len        <= s0_len;
                s1_secure     <= s0_secure;
                s1_privileged <= s0_privileged;
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s2_valid       <= 1'b0;
            s2_done        <= 1'b0;
            s2_channel     <= {CHANNEL_ID_WIDTH{1'b0}};
            s2_len         <= {LEN_WIDTH{1'b0}};
            s2_status      <= STATUS_OK;
            s2_error_code  <= ERR_NONE;
            s2_wait_fetch  <= 1'b0;
            s2_wait_read   <= 1'b0;
            s2_wait_write  <= 1'b0;
            s2_seen_fetch  <= 1'b0;
            s2_seen_read   <= 1'b0;
            s2_seen_write  <= 1'b0;
            rsp_channel    <= {CHANNEL_ID_WIDTH{1'b0}};
            rsp_status     <= STATUS_OK;
            rsp_bytes_remaining <= {LEN_WIDTH{1'b0}};
            observed_fetch_data <= {DATA_WIDTH{1'b0}};
        end else begin
            if (s2_valid && !s2_done) begin
                if (fetch_rsp_fire) begin
                    s2_seen_fetch <= 1'b1;
                    observed_fetch_data <= fetch_rsp_data;
                    if (fetch_rsp_error) begin
                        s2_status <= STATUS_BUS_ERROR;
                        s2_error_code <= ERR_FETCH;
                    end
                end
                if (rd_rsp_fire) begin
                    s2_seen_read <= 1'b1;
                    if (rd_rsp_error) begin
                        s2_status <= STATUS_BUS_ERROR;
                        s2_error_code <= ERR_READ;
                    end
                end
                if (wr_rsp_fire) begin
                    s2_seen_write <= 1'b1;
                    if (wr_rsp_error) begin
                        s2_status <= STATUS_BUS_ERROR;
                        s2_error_code <= ERR_WRITE;
                    end
                end
                if (s2_complete_next) begin
                    s2_done <= 1'b1;
                    rsp_channel <= s2_channel;
                    rsp_status <= s2_status;
                    rsp_bytes_remaining <= (s2_status == STATUS_OK) ? {LEN_WIDTH{1'b0}} : s2_len;
                end
            end

            if (s2_rsp_fire) begin
                s2_valid      <= 1'b0;
                s2_done       <= 1'b0;
                s2_wait_fetch <= 1'b0;
                s2_wait_read  <= 1'b0;
                s2_wait_write <= 1'b0;
                s2_seen_fetch <= 1'b0;
                s2_seen_read  <= 1'b0;
                s2_seen_write <= 1'b0;
            end

            if (s1_to_s2_fire) begin
                s2_valid      <= 1'b1;
                s2_channel    <= s1_channel;
                s2_len        <= s1_len;
                s2_wait_fetch <= s1_needs_fetch & s1_is_legal & (!s1_credit_blocked);
                s2_wait_read  <= s1_needs_read  & s1_is_legal & (!s1_credit_blocked);
                s2_wait_write <= s1_needs_write & s1_is_legal & (!s1_credit_blocked);
                s2_seen_fetch <= 1'b0;
                s2_seen_read  <= 1'b0;
                s2_seen_write <= 1'b0;

                if (!s1_is_legal) begin
                    s2_done <= 1'b1;
                    s2_status <= STATUS_BAD_OPCODE;
                    s2_error_code <= ERR_OPCODE;
                    rsp_channel <= s1_channel;
                    rsp_status <= STATUS_BAD_OPCODE;
                    rsp_bytes_remaining <= s1_len;
                end else if (s1_credit_blocked) begin
                    s2_done <= 1'b1;
                    s2_status <= STATUS_NO_CREDIT;
                    s2_error_code <= ERR_CREDIT;
                    rsp_channel <= s1_channel;
                    rsp_status <= STATUS_NO_CREDIT;
                    rsp_bytes_remaining <= s1_len;
                end else if (s1_needs_response) begin
                    s2_done <= 1'b0;
                    s2_status <= STATUS_OK;
                    s2_error_code <= ERR_NONE;
                end else begin
                    s2_done <= 1'b1;
                    s2_status <= STATUS_OK;
                    s2_error_code <= ERR_NONE;
                    rsp_channel <= s1_channel;
                    rsp_status <= STATUS_OK;
                    rsp_bytes_remaining <= {LEN_WIDTH{1'b0}};
                end
            end
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            outstanding_reads  <= {OUTSTANDING_WIDTH{1'b0}};
            outstanding_writes <= {OUTSTANDING_WIDTH{1'b0}};
            channel_state      <= CHANNEL_IDLE;
            engine_state       <= ENGINE_IDLE;
            error_valid        <= 1'b0;
            error_code         <= ERR_NONE;
        end else begin
            if (channel_state == CHANNEL_ACTIVE) begin
                outstanding_reads  <= outstanding_reads_next;
                outstanding_writes <= outstanding_writes_next;
            end else begin
                outstanding_reads  <= {OUTSTANDING_WIDTH{1'b0}};
                outstanding_writes <= {OUTSTANDING_WIDTH{1'b0}};
            end

            if (s0_accept_fire) begin
                channel_state <= CHANNEL_ACTIVE;
            end else if (pipeline_empty_next && outstanding_zero_next) begin
                channel_state <= CHANNEL_IDLE;
            end

            if (s2_valid && s2_done && (s2_status != STATUS_OK)) begin
                error_valid <= 1'b1;
                error_code <= s2_error_code;
            end else if (s0_accept_fire) begin
                error_valid <= 1'b0;
                error_code <= ERR_NONE;
            end

            if (s2_valid) begin
                engine_state <= ENGINE_S2_OBSERVE;
            end else if (s1_valid) begin
                engine_state <= ENGINE_S1_EVALUATE;
            end else if (s0_valid || s0_accept_fire) begin
                engine_state <= ENGINE_S0_ACCEPT;
            end else begin
                engine_state <= ENGINE_IDLE;
            end
        end
    end

    always_comb begin
        busy = (!pipeline_empty_now) |
               (outstanding_reads != {OUTSTANDING_WIDTH{1'b0}}) |
               (outstanding_writes != {OUTSTANDING_WIDTH{1'b0}});
        idle = !busy;
    end

endmodule

`default_nettype wire
