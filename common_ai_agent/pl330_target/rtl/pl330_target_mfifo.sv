`default_nettype none

module pl330_target_mfifo #(
    parameter integer FIFO_DEPTH = 16,
    parameter integer DATA_W = 32,
    parameter integer ADDR_W = 32
) (
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  soft_reset_i,
    input  wire [31:0]           irq_clear_i,
    input  wire [31:0]           fault_clear_i,

    input  wire                  cmd_valid_i,
    output wire                  cmd_ready_o,
    input  wire [7:0]            cmd_opcode_i,
    input  wire [ADDR_W-1:0]     cmd_arg_addr_i,
    input  wire [31:0]           cmd_arg_data_i,
    input  wire [4:0]            cmd_event_i,
    input  wire                  cmd_manager_i,
    input  wire                  cmd_secure_i,
    input  wire                  dbginst_write_i,
    input  wire                  cfg_nonsecure_allowed_i,
    input  wire [ADDR_W-1:0]     cmd_next_pc_i,

    output logic                 cmd_accept_o,
    output logic                 cmd_error_o,
    output logic [7:0]           cmd_fault_code_o,

    output wire                  ld_req_valid_o,
    input  wire                  ld_req_ready_i,
    output wire [ADDR_W-1:0]     ld_req_addr_o,
    input  wire                  ld_rsp_valid_i,
    output wire                  ld_rsp_ready_o,
    input  wire [DATA_W-1:0]     ld_rsp_data_i,
    input  wire                  ld_rsp_error_i,

    output wire                  st_req_valid_o,
    input  wire                  st_req_ready_i,
    output wire [ADDR_W-1:0]     st_req_addr_o,
    output wire [DATA_W-1:0]     st_req_data_o,
    input  wire                  st_rsp_valid_i,
    output wire                  st_rsp_ready_o,
    input  wire                  st_rsp_error_i,

    input  wire                  mfifo_push_valid_i,
    output wire                  mfifo_push_ready_o,
    input  wire [DATA_W-1:0]     mfifo_push_data_i,
    input  wire                  mfifo_pop_valid_i,
    output wire                  mfifo_pop_ready_o,
    output wire [DATA_W-1:0]     mfifo_pop_data_o,

    output wire                  mfifo_full_o,
    output wire                  mfifo_empty_o,
    output wire [4:0]            mfifo_count_o,
    output wire [3:0]            channel_state_o,
    output wire [ADDR_W-1:0]     channel_pc_o,
    output wire [3:0]            outstanding_reads_o,
    output wire [3:0]            outstanding_writes_o,
    output wire [31:0]           irq_status_o,
    output wire [31:0]           fault_status_o,
    output logic                 reset_accepted_o,
    output logic                 fault_valid_o
);

    localparam [3:0] CH_STOPPED             = 4'd0;
    localparam [3:0] CH_EXECUTING           = 4'd1;
    localparam [3:0] CH_CACHE_MISS          = 4'd2;
    localparam [3:0] CH_UPDATING_PC         = 4'd3;
    localparam [3:0] CH_WAITING_FOR_EVENT   = 4'd4;
    localparam [3:0] CH_AT_BARRIER          = 4'd5;
    localparam [3:0] CH_KILLING             = 4'd6;
    localparam [3:0] CH_COMPLETING          = 4'd7;
    localparam [3:0] CH_FAULTING            = 4'd8;
    localparam [3:0] CH_FAULTING_COMPLETING = 4'd9;

    localparam [7:0] OP_DMAEND  = 8'h00;
    localparam [7:0] OP_DMAKILL = 8'h01;
    localparam [7:0] OP_DMALD   = 8'h04;
    localparam [7:0] OP_DMAST   = 8'h08;
    localparam [7:0] OP_DMALDP  = 8'h25;
    localparam [7:0] OP_DMASTP  = 8'h29;
    localparam [7:0] OP_DMAWFP  = 8'h30;
    localparam [7:0] OP_DMASEV  = 8'h34;
    localparam [7:0] OP_DMAWFE  = 8'h36;
    localparam [7:0] OP_DMAGO   = 8'ha0;
    localparam [7:0] OP_FAULT   = 8'hff;

    localparam [4:0] FIFO_DEPTH_COUNT       = 5'd16;
    localparam [4:0] MFIFO_DEPTH            = 5'd16;
    localparam [4:0] FIFO_ALMOST_FULL_COUNT = 5'd15;
    localparam integer NUM_IRQS = 32;
    localparam [5:0] NUM_IRQS_LIMIT = 6'(NUM_IRQS);
    localparam [4:0] IRQ_ABORT_IDX = 5'd31;

    logic [3:0]        channel_state;
    logic [ADDR_W-1:0] channel_pc;
    logic [3:0]        outstanding_reads;
    logic [3:0]        outstanding_writes;
    logic [4:0]        mfifo_count;
    logic [31:0]       irq_status;
    logic [31:0]       fault_status;
    logic [4:0]        wait_event_id;
    logic [DATA_W-1:0] fifo_mem [0:FIFO_DEPTH-1];
    logic [3:0]        wr_ptr;
    logic [3:0]        rd_ptr;

    integer fifo_i;

    wire cmd_is_dmaend  = (cmd_opcode_i == OP_DMAEND);
    wire cmd_is_dmakill = (cmd_opcode_i == OP_DMAKILL);
    wire cmd_is_dmald   = (cmd_opcode_i == OP_DMALD);
    wire cmd_is_dmast   = (cmd_opcode_i == OP_DMAST);
    wire cmd_is_dmaldp  = (cmd_opcode_i == OP_DMALDP);
    wire cmd_is_dmastp  = (cmd_opcode_i == OP_DMASTP);
    wire cmd_is_dmasev  = (cmd_opcode_i == OP_DMASEV);
    wire cmd_is_dmawfe  = (cmd_opcode_i == OP_DMAWFE);
    wire cmd_is_dmawfp  = (cmd_opcode_i == OP_DMAWFP);
    wire cmd_is_dmago   = (cmd_opcode_i == OP_DMAGO);
    wire cmd_is_fault   = (cmd_opcode_i == OP_FAULT);
    wire cmd_is_known   = cmd_is_dmaend | cmd_is_dmakill | cmd_is_dmald | cmd_is_dmast | cmd_is_dmaldp | cmd_is_dmastp | cmd_is_dmasev | cmd_is_dmawfe | cmd_is_dmawfp | cmd_is_dmago | cmd_is_fault;
    wire cmd_is_load    = cmd_is_dmald | cmd_is_dmaldp;
    wire cmd_is_store   = cmd_is_dmast | cmd_is_dmastp;

    wire channel_stopped             = (channel_state == CH_STOPPED);
    wire channel_executing           = (channel_state == CH_EXECUTING);
    wire channel_cache_miss          = (channel_state == CH_CACHE_MISS);
    wire channel_updating_pc         = (channel_state == CH_UPDATING_PC);
    wire channel_waiting_for_event   = (channel_state == CH_WAITING_FOR_EVENT);
    wire channel_at_barrier          = (channel_state == CH_AT_BARRIER);
    wire channel_killing             = (channel_state == CH_KILLING);
    wire channel_completing          = (channel_state == CH_COMPLETING);
    wire channel_faulting            = (channel_state == CH_FAULTING);
    wire channel_faulting_completing = (channel_state == CH_FAULTING_COMPLETING);

    wire fifo_full  = (mfifo_count == FIFO_DEPTH_COUNT);
    wire fifo_empty = (mfifo_count == 5'd0);

    wire fifo_pop_store_pre = cmd_valid_i & cmd_is_store & channel_executing & ~fifo_empty & (outstanding_writes != 4'd15) & st_req_ready_i;
    wire fifo_pop_ext_pre   = mfifo_pop_valid_i & ~fifo_empty & ~fifo_pop_store_pre;
    wire fifo_space_avail   = ~fifo_full | fifo_pop_store_pre | fifo_pop_ext_pre;

    wire load_backpressure  = (outstanding_reads == 4'd15) | (mfifo_count >= FIFO_ALMOST_FULL_COUNT) | ~ld_req_ready_i;
    wire store_backpressure = fifo_empty | (outstanding_writes == 4'd15) | ~st_req_ready_i;
    wire command_blocked    = (channel_completing | channel_faulting | channel_faulting_completing | channel_killing) & ~(cmd_is_dmakill & dbginst_write_i & cmd_manager_i);

    assign cmd_ready_o = ~command_blocked & ~(cmd_valid_i & ((cmd_is_load & load_backpressure) | (cmd_is_store & store_backpressure)));

    wire cmd_accept = cmd_valid_i & cmd_ready_o;
    wire secure_violation = cmd_accept & ~cmd_secure_i & ~cfg_nonsecure_allowed_i;

    wire [4:0] event_idx = cmd_event_i;
    wire [5:0] event_idx_ext = {1'b0, event_idx};
    wire event_idx_in_range = (event_idx_ext < NUM_IRQS_LIMIT);

    wire fm_reset_precondition_0_cycle_model_accept = soft_reset_i;
    wire fm_reset_accept = fm_reset_precondition_0_cycle_model_accept;

    wire fm_dmago_precondition_0_channel_state_eq_0 = channel_stopped;
    wire fm_dmago_precondition_1_manager_apb_write_to_dbginst = dbginst_write_i & cmd_manager_i;
    wire dmago_pre_ok = fm_dmago_precondition_0_channel_state_eq_0 & fm_dmago_precondition_1_manager_apb_write_to_dbginst;
    wire fm_dmago_output_1_channel_pc_arg_addr_valid = cmd_accept & cmd_is_dmago & dmago_pre_ok & ~secure_violation;
    wire [ADDR_W-1:0] fm_dmago_output_1_channel_pc_arg_addr = cmd_arg_addr_i;
    wire dmago_accept = fm_dmago_output_1_channel_pc_arg_addr_valid;
    wire dmago_fault  = cmd_accept & cmd_is_dmago & (~dmago_pre_ok | secure_violation);

    wire fm_dmald_precondition_0_channel_executing = channel_executing;
    wire fm_dmald_precondition_1_mfifo_credit = ~load_backpressure;
    wire load_pre_ok = fm_dmald_precondition_0_channel_executing & fm_dmald_precondition_1_mfifo_credit;
    wire dmald_accept = cmd_accept & cmd_is_dmald & load_pre_ok & ~secure_violation;
    wire dmaldp_accept = cmd_accept & cmd_is_dmaldp & load_pre_ok & ~secure_violation;
    wire load_fault = cmd_accept & cmd_is_load & (~load_pre_ok | secure_violation);

    wire fm_store_precondition_channel_executing = channel_executing;
    wire fm_store_precondition_mfifo_data_available = ~store_backpressure;
    wire store_pre_ok = fm_store_precondition_channel_executing & fm_store_precondition_mfifo_data_available;
    wire dmast_accept = cmd_accept & cmd_is_dmast & store_pre_ok & ~secure_violation;
    wire dmastp_accept = cmd_accept & cmd_is_dmastp & store_pre_ok & ~secure_violation;
    wire store_fault = cmd_accept & cmd_is_store & (~store_pre_ok | secure_violation);

    wire dmasev_state_pre_ok = channel_executing | channel_waiting_for_event;
    wire dmasev_pre_ok = dmasev_state_pre_ok & event_idx_in_range;
    wire dmasev_accept = cmd_accept & cmd_is_dmasev & dmasev_pre_ok & ~secure_violation;
    wire dmasev_fault = cmd_accept & cmd_is_dmasev & (~dmasev_pre_ok | secure_violation);

    wire dmawfe_pre_ok = channel_executing;
    wire dmawfe_accept = cmd_accept & cmd_is_dmawfe & dmawfe_pre_ok & ~secure_violation;
    wire dmawfe_fault = cmd_accept & cmd_is_dmawfe & (~dmawfe_pre_ok | secure_violation);

    wire dmawfp_pre_ok = channel_executing;
    wire dmawfp_accept = cmd_accept & cmd_is_dmawfp & dmawfp_pre_ok & ~secure_violation;
    wire dmawfp_fault = cmd_accept & cmd_is_dmawfp & (~dmawfp_pre_ok | secure_violation);

    wire all_outstanding_drained = (outstanding_reads == 4'd0) & (outstanding_writes == 4'd0);

    wire dmaend_pre_ok = channel_executing & all_outstanding_drained;
    wire dmaend_accept = cmd_accept & cmd_is_dmaend & dmaend_pre_ok & ~secure_violation;
    wire dmaend_error_case_0_outstanding_gt_0 = cmd_accept & cmd_is_dmaend & ((outstanding_reads != 4'd0) | (outstanding_writes != 4'd0));
    wire dmaend_fault = cmd_accept & cmd_is_dmaend & (~dmaend_pre_ok | secure_violation);

    wire dmakill_pre_ok = dbginst_write_i & cmd_manager_i;
    wire dmakill_accept = cmd_accept & cmd_is_dmakill & dmakill_pre_ok & ~secure_violation;
    wire dmakill_fault = cmd_accept & cmd_is_dmakill & (~dmakill_pre_ok | secure_violation);

    wire explicit_fault_accept = cmd_accept & cmd_is_fault;
    wire illegal_fault_accept = cmd_accept & ~cmd_is_known;

    wire [ADDR_W-1:0] pc_plus_four = channel_pc + {{(ADDR_W-3){1'b0}}, 3'd4};
    wire [ADDR_W-1:0] next_pc_value = (cmd_next_pc_i != {ADDR_W{1'b0}}) ? cmd_next_pc_i : pc_plus_four;

    wire fm_dmald_output_0_ld_req_valid = dmald_accept;
    wire fm_dmaldp_output_0_ld_req_valid = dmaldp_accept;
    assign ld_req_valid_o = fm_dmald_output_0_ld_req_valid | fm_dmaldp_output_0_ld_req_valid;
    assign ld_req_addr_o = channel_pc;
    assign ld_rsp_ready_o = fifo_space_avail;

    wire fm_dmast_output_st_req_valid = dmast_accept;
    wire fm_dmastp_output_st_req_valid = dmastp_accept;
    assign st_req_valid_o = fm_dmast_output_st_req_valid | fm_dmastp_output_st_req_valid;
    assign st_req_addr_o = channel_pc;
    assign st_req_data_o = fifo_mem[rd_ptr];
    assign st_rsp_ready_o = 1'b1;

    wire fm_dmald_output_0_ld_req_fire = fm_dmald_output_0_ld_req_valid & ld_req_ready_i;
    wire fm_dmaldp_output_0_ld_req_fire = fm_dmaldp_output_0_ld_req_valid & ld_req_ready_i;
    wire ld_req_fire = fm_dmald_output_0_ld_req_fire | fm_dmaldp_output_0_ld_req_fire;
    wire st_req_fire = st_req_valid_o & st_req_ready_i;
    wire ld_rsp_fire = ld_rsp_valid_i & ld_rsp_ready_o;
    wire st_rsp_fire = st_rsp_valid_i & st_rsp_ready_o;

    wire fm_dmald_side_effect_0_outstanding_reads_increment = fm_dmald_output_0_ld_req_fire;
    wire fm_dmaldp_side_effect_0_outstanding_reads_increment = fm_dmaldp_output_0_ld_req_fire;
    wire fm_load_side_effect_outstanding_reads_increment =
        fm_dmald_side_effect_0_outstanding_reads_increment |
        fm_dmaldp_side_effect_0_outstanding_reads_increment |
        ld_req_fire;
    wire fm_load_side_effect_outstanding_reads_decrement = ld_rsp_fire;

    wire fm_dmast_side_effect_0_outstanding_writes_increment = dmast_accept & st_req_ready_i;
    wire fm_dmastp_side_effect_0_outstanding_writes_increment = dmastp_accept & st_req_ready_i;
    wire fm_store_side_effect_outstanding_writes_increment = fm_dmast_side_effect_0_outstanding_writes_increment | fm_dmastp_side_effect_0_outstanding_writes_increment;
    wire fm_store_side_effect_outstanding_writes_decrement = st_rsp_fire;

    wire fm_dmald_side_effect_1_channel_pc_update = dmald_accept;
    wire fm_dmaldp_side_effect_1_channel_pc_update = dmaldp_accept;
    wire fm_load_side_effect_channel_pc_update = fm_dmald_side_effect_1_channel_pc_update | fm_dmaldp_side_effect_1_channel_pc_update;
    wire fm_store_side_effect_channel_pc_update = dmast_accept | dmastp_accept;

    wire dmago_error_case_fired = dmago_fault;
    wire dmald_error_case_fired = load_fault;
    wire dmast_error_case_fired = store_fault;
    wire dmasev_error_case_fired = dmasev_fault;
    wire dmaend_error_case_fired = dmaend_fault;
    wire dmawfe_error_case_fired = dmawfe_fault;
    wire dmawfp_error_case_fired = dmawfp_fault;
    wire dmakill_error_case_fired = dmakill_fault;
    wire explicit_fault_error_case_fired = explicit_fault_accept;
    wire illegal_opcode_error_case_fired = illegal_fault_accept;
    wire ld_rsp_error_case_fired = ld_rsp_fire & ld_rsp_error_i;
    wire st_rsp_error_case_fired = st_rsp_fire & st_rsp_error_i;

    wire fm_fault_precondition_0_error_case_vector_any = dmago_error_case_fired |
                                                        dmald_error_case_fired |
                                                        dmast_error_case_fired |
                                                        dmasev_error_case_fired |
                                                        dmaend_error_case_fired |
                                                        dmawfe_error_case_fired |
                                                        dmawfp_error_case_fired |
                                                        dmakill_error_case_fired |
                                                        explicit_fault_error_case_fired |
                                                        illegal_opcode_error_case_fired |
                                                        ld_rsp_error_case_fired |
                                                        st_rsp_error_case_fired;
    wire fm_fault_precondition_0_any_error_case_fired = fm_fault_precondition_0_error_case_vector_any;
    wire fm_fault_error_case_fired = fm_fault_precondition_0_any_error_case_fired;
    wire irq_abort = fm_fault_error_case_fired;
    wire irq_abort_pulse = irq_abort;

    wire fifo_push_rsp = ld_rsp_valid_i & ld_rsp_ready_o & ~ld_rsp_error_i;
    assign mfifo_push_ready_o = fifo_space_avail & ~(ld_rsp_valid_i & ~ld_rsp_error_i);
    wire fifo_push_ext = mfifo_push_valid_i & mfifo_push_ready_o;
    wire fifo_push = fifo_push_rsp | fifo_push_ext;
    wire [DATA_W-1:0] fifo_push_data = fifo_push_rsp ? ld_rsp_data_i : mfifo_push_data_i;

    wire fifo_pop_store = st_req_fire;
    assign mfifo_pop_ready_o = ~fifo_empty & ~fifo_pop_store;
    wire fifo_pop_ext = mfifo_pop_valid_i & mfifo_pop_ready_o;
    wire fifo_pop = fifo_pop_store | fifo_pop_ext;

    wire event_signaled = channel_waiting_for_event & (irq_status[wait_event_id] | (dmasev_accept & (event_idx == wait_event_id)));
    wire barrier_cleared = channel_at_barrier & all_outstanding_drained;
    wire kill_complete = channel_killing & all_outstanding_drained;
    wire fault_drain_complete = channel_faulting & all_outstanding_drained;
    wire fault_clear_to_stopped = channel_faulting_completing & (|fault_clear_i) & ((fault_status & ~fault_clear_i) == 32'h00000000);
    wire cache_miss_all_reads_returned = channel_cache_miss & ((outstanding_reads == 4'd0) | (ld_rsp_fire & ~ld_rsp_error_i & (outstanding_reads <= 4'd1)));

    assign mfifo_pop_data_o = fifo_mem[rd_ptr];
    assign mfifo_full_o = fifo_full;
    assign mfifo_empty_o = fifo_empty;
    assign mfifo_count_o = mfifo_count;
    assign channel_state_o = channel_state;
    assign channel_pc_o = channel_pc;
    assign outstanding_reads_o = outstanding_reads;
    assign outstanding_writes_o = outstanding_writes;
    assign irq_status_o = irq_status;
    assign fault_status_o = fault_status;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            channel_state <= CH_STOPPED;
            channel_pc <= {ADDR_W{1'b0}};
            outstanding_reads <= 4'd0;
            outstanding_writes <= 4'd0;
            mfifo_count <= 5'd0;
            irq_status <= 32'h00000000;
            fault_status <= 32'h00000000;
            wait_event_id <= 5'd0;
            wr_ptr <= 4'd0;
            rd_ptr <= 4'd0;
            cmd_accept_o <= 1'b0;
            cmd_error_o <= 1'b0;
            cmd_fault_code_o <= 8'h00;
            reset_accepted_o <= 1'b0;
            fault_valid_o <= 1'b0;
            for (fifo_i = 0; fifo_i < FIFO_DEPTH; fifo_i = fifo_i + 1) begin
                fifo_mem[fifo_i] <= {DATA_W{1'b0}};
            end
        end else begin
            cmd_accept_o <= 1'b0;
            cmd_error_o <= 1'b0;
            cmd_fault_code_o <= 8'h00;
            reset_accepted_o <= 1'b0;
            fault_valid_o <= 1'b0;

            if (fm_reset_accept) begin
                channel_state <= CH_STOPPED;
                channel_pc <= {ADDR_W{1'b0}};
                outstanding_reads <= 4'd0;
                outstanding_writes <= 4'd0;
                mfifo_count <= 5'd0;
                irq_status <= 32'h00000000;
                fault_status <= 32'h00000000;
                wait_event_id <= 5'd0;
                wr_ptr <= 4'd0;
                rd_ptr <= 4'd0;
                reset_accepted_o <= 1'b1;
                for (fifo_i = 0; fifo_i < FIFO_DEPTH; fifo_i = fifo_i + 1) begin
                    fifo_mem[fifo_i] <= {DATA_W{1'b0}};
                end
            end else begin
                case ({fm_load_side_effect_outstanding_reads_increment, fm_load_side_effect_outstanding_reads_decrement})
                    2'b10: begin
                        if (outstanding_reads != 4'd15) begin
                            outstanding_reads <= outstanding_reads + 4'd1;
                        end
                    end
                    2'b01: begin
                        if (outstanding_reads != 4'd0) begin
                            outstanding_reads <= outstanding_reads - 4'd1;
                        end
                    end
                    default: begin
                        outstanding_reads <= outstanding_reads;
                    end
                endcase

                case ({fm_store_side_effect_outstanding_writes_increment, fm_store_side_effect_outstanding_writes_decrement})
                    2'b10: begin
                        if (outstanding_writes != 4'd15) begin
                            outstanding_writes <= outstanding_writes + 4'd1;
                        end
                    end
                    2'b01: begin
                        if (outstanding_writes != 4'd0) begin
                            outstanding_writes <= outstanding_writes - 4'd1;
                        end
                    end
                    default: begin
                        outstanding_writes <= outstanding_writes;
                    end
                endcase

                if (fifo_push) begin
                    fifo_mem[wr_ptr] <= fifo_push_data;
                    wr_ptr <= wr_ptr + 4'd1;
                end
                if (fifo_pop) begin
                    rd_ptr <= rd_ptr + 4'd1;
                end
                case ({fifo_push, fifo_pop})
                    2'b10: begin
                        if (mfifo_count != MFIFO_DEPTH) begin
                            mfifo_count <= mfifo_count + 5'd1;
                        end
                    end
                    2'b01: begin
                        if (mfifo_count != 5'd0) begin
                            mfifo_count <= mfifo_count - 5'd1;
                        end
                    end
                    default: begin
                        mfifo_count <= mfifo_count;
                    end
                endcase

                if (|irq_clear_i) begin
                    irq_status <= irq_status & ~irq_clear_i;
                end
                if (|fault_clear_i) begin
                    fault_status <= fault_status & ~fault_clear_i;
                end

                if (irq_abort_pulse) begin
                    irq_status[IRQ_ABORT_IDX] <= 1'b1;
                end

                if (cmd_accept) begin
                    cmd_accept_o <= 1'b1;
                end

                if (dmago_accept) begin
                    channel_state <= CH_EXECUTING;
                    channel_pc <= fm_dmago_output_1_channel_pc_arg_addr;
                end

                if (fm_load_side_effect_channel_pc_update) begin
                    channel_state <= CH_CACHE_MISS;
                    channel_pc <= next_pc_value;
                end

                if (fm_store_side_effect_channel_pc_update) begin
                    channel_state <= CH_UPDATING_PC;
                    channel_pc <= next_pc_value;
                end

                if (dmasev_accept) begin
                    irq_status[event_idx] <= 1'b1;
                    channel_pc <= next_pc_value;
                    if (channel_executing) begin
                        channel_state <= CH_EXECUTING;
                    end
                end

                if (dmawfe_accept) begin
                    wait_event_id <= event_idx;
                    channel_state <= CH_WAITING_FOR_EVENT;
                    channel_pc <= next_pc_value;
                end

                if (event_signaled) begin
                    channel_state <= CH_EXECUTING;
                end

                if (dmawfp_accept) begin
                    channel_state <= CH_AT_BARRIER;
                    channel_pc <= next_pc_value;
                end

                if (barrier_cleared) begin
                    channel_state <= CH_EXECUTING;
                end

                if (dmaend_accept) begin
                    channel_state <= CH_STOPPED;
                    channel_pc <= next_pc_value;
                end

                if (channel_completing && all_outstanding_drained) begin
                    channel_state <= CH_STOPPED;
                end

                if (dmakill_accept) begin
                    channel_state <= CH_KILLING;
                    fault_status[19] <= 1'b0;
                end

                if (kill_complete) begin
                    channel_state <= CH_STOPPED;
                    channel_pc <= {ADDR_W{1'b0}};
                    mfifo_count <= 5'd0;
                    wr_ptr <= 4'd0;
                    rd_ptr <= 4'd0;
                end

                if (cache_miss_all_reads_returned) begin
                    channel_state <= CH_EXECUTING;
                end

                if (st_rsp_fire && !st_rsp_error_i && channel_updating_pc) begin
                    channel_state <= CH_EXECUTING;
                end

                if (channel_updating_pc && (outstanding_writes == 4'd0)) begin
                    channel_state <= CH_EXECUTING;
                end

                if (fault_drain_complete) begin
                    channel_state <= CH_FAULTING_COMPLETING;
                end

                if (fault_clear_to_stopped) begin
                    channel_state <= CH_STOPPED;
                end

                if (dmago_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[0] <= secure_violation;
                    fault_status[1] <= ~dmago_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h11;
                    fault_valid_o <= 1'b1;
                end

                if (dmald_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[2] <= secure_violation;
                    fault_status[3] <= ~load_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h21;
                    fault_valid_o <= 1'b1;
                end

                if (dmast_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[4] <= secure_violation;
                    fault_status[5] <= ~store_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h31;
                    fault_valid_o <= 1'b1;
                end

                if (dmasev_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[6] <= secure_violation;
                    fault_status[7] <= ~dmasev_state_pre_ok;
                    fault_status[12] <= ~event_idx_in_range;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : ((!event_idx_in_range) ? 8'h42 : 8'h41);
                    fault_valid_o <= 1'b1;
                end

                if (dmaend_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[8] <= ~channel_executing;
                    fault_status[9] <= dmaend_error_case_0_outstanding_gt_0;
                    fault_status[10] <= secure_violation;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : (dmaend_error_case_0_outstanding_gt_0 ? 8'h52 : 8'h51);
                    fault_valid_o <= 1'b1;
                end

                if (dmawfe_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[11] <= secure_violation | ~dmawfe_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h61;
                    fault_valid_o <= 1'b1;
                end

                if (dmawfp_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[13] <= secure_violation | ~dmawfp_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h71;
                    fault_valid_o <= 1'b1;
                end

                if (dmakill_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[14] <= secure_violation | ~dmakill_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h81;
                    fault_valid_o <= 1'b1;
                end

                if (explicit_fault_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[15] <= 1'b1;
                    fault_status[17] <= |cmd_arg_data_i[31:8];
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= cmd_arg_data_i[7:0];
                    fault_valid_o <= 1'b1;
                end

                if (illegal_opcode_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[16] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'he0;
                    fault_valid_o <= 1'b1;
                end

                if (ld_rsp_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[17] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'he1;
                    fault_valid_o <= 1'b1;
                end

                if (st_rsp_error_case_fired) begin
                    channel_state <= CH_FAULTING;
                    fault_status[18] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'he2;
                    fault_valid_o <= 1'b1;
                end

                if (channel_killing && fm_fault_error_case_fired) begin
                    fault_status[19] <= 1'b1;
                end
            end
        end
    end

endmodule

`default_nettype wire
