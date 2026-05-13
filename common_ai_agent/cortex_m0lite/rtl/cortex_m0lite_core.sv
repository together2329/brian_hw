module cortex_m0lite_core #(
    parameter integer XLEN             = 32,
    parameter integer RESET_PC         = 0,
    parameter integer TRAP_VECTOR      = 128,
    parameter integer STACK_RESET      = 0,
    parameter integer REG_COUNT        = 16,
    parameter integer AHB_ADDR_W       = 32,
    parameter integer AHB_DATA_W       = 32,
    parameter integer CORE_FREQ_MHZ    = 300,
    parameter integer BUS_FREQ_MHZ     = 150,
    parameter integer AHB_HTRANS_IDLE  = 0,
    parameter integer AHB_HTRANS_BUSY  = 1,
    parameter integer AHB_HTRANS_NONSEQ= 2,
    parameter integer AHB_HTRANS_SEQ   = 3,
    parameter integer AHB_HSIZE_WORD   = 2,
    parameter integer AHB_HBURST_SINGLE= 0
) (
    input  logic                     clk,
    input  logic                     rst_n,
    input  logic                     hclk,
    input  logic                     hresetn,
    input  logic                     irq,

    output logic [AHB_ADDR_W-1:0]    i_haddr,
    output logic [1:0]               i_htrans,
    output logic                     i_hwrite,
    output logic [2:0]               i_hsize,
    output logic [2:0]               i_hburst,
    output logic [AHB_DATA_W-1:0]    i_hwdata,
    input  logic [AHB_DATA_W-1:0]    i_hrdata,
    input  logic                     i_hready,
    input  logic                     i_hresp,

    output logic [AHB_ADDR_W-1:0]    d_haddr,
    output logic [1:0]               d_htrans,
    output logic                     d_hwrite,
    output logic [2:0]               d_hsize,
    output logic [2:0]               d_hburst,
    output logic [AHB_DATA_W-1:0]    d_hwdata,
    input  logic [AHB_DATA_W-1:0]    d_hrdata,
    input  logic                     d_hready,
    input  logic                     d_hresp,

    output logic [XLEN-1:0]          pc_dbg,
    output logic [2:0]               state_dbg,
    output logic                     retire,
    output logic                     trap
);

    localparam [2:0] ST_RESET   = 3'd0;
    localparam [2:0] ST_FETCH   = 3'd1;
    localparam [2:0] ST_DECODE  = 3'd2;
    localparam [2:0] ST_EXECUTE = 3'd3;
    localparam [2:0] ST_MEMWAIT = 3'd4;
    localparam [2:0] ST_TRAP    = 3'd5;

    localparam [2:0] OP_ALU     = 3'd0;
    localparam [2:0] OP_MEM     = 3'd1;
    localparam [2:0] OP_BRANCH  = 3'd2;
    localparam [2:0] OP_ILLEGAL = 3'd7;

    localparam [6:0] TRAP_ILLEGAL = 7'd1;
    localparam [6:0] TRAP_BUS     = 7'd2;
    localparam [6:0] TRAP_MISALIGN= 7'd3;

    logic [2:0] fsm_state_q;
    logic [XLEN-1:0] pc_q;
    logic [XLEN-1:0] exc_epc_q;
    logic [6:0] trap_code_q;
    logic [2:0] trap_stage_q;
    logic trap_q;

    logic [3:0] nzcv_q;

    logic [XLEN-1:0] rf_mem_0;
    logic [XLEN-1:0] rf_mem_1;
    logic [XLEN-1:0] rf_mem_2;
    logic [XLEN-1:0] rf_mem_3;
    logic [XLEN-1:0] rf_mem_4;
    logic [XLEN-1:0] rf_mem_5;
    logic [XLEN-1:0] rf_mem_6;
    logic [XLEN-1:0] rf_mem_7;
    logic [XLEN-1:0] rf_mem_8;
    logic [XLEN-1:0] rf_mem_9;
    logic [XLEN-1:0] rf_mem_10;
    logic [XLEN-1:0] rf_mem_11;
    logic [XLEN-1:0] rf_mem_12;
    logic [XLEN-1:0] rf_mem_13;
    logic [XLEN-1:0] rf_mem_14;

    logic if_id_valid_q;
    logic [XLEN-1:0] if_id_pc_q;
    logic [15:0] if_id_instr_q;
    logic if_id_fault_q;

    logic id_ex_valid_q;
    logic [2:0] id_ex_op_class_q;
    logic [XLEN-1:0] id_ex_pc_q;
    logic [3:0] id_ex_rd_q;
    logic [3:0] id_ex_rn_q;
    logic [3:0] id_ex_rm_q;
    logic [XLEN-1:0] id_ex_rn_val_q;
    logic [XLEN-1:0] id_ex_rm_val_q;
    logic [XLEN-1:0] id_ex_imm_q;
    logic id_ex_decode_fault_q;
    logic [2:0] id_ex_alu_subop_q;

    logic ex_wb_valid_q;
    logic [3:0] ex_wb_rd_q;
    logic [XLEN-1:0] ex_wb_result_q;
    logic [3:0] ex_wb_flags_q;
    logic ex_wb_regwrite_q;
    logic ex_wb_retire_ok_q;
    logic ex_wb_trap_q;
    logic [6:0] ex_wb_trap_code_q;
    logic [2:0] ex_wb_trap_stage_q;

    logic [16:0] alu_add_ext;
    logic [16:0] alu_sub_ext;

    logic [XLEN-1:0] rn_val_comb;
    logic [XLEN-1:0] rm_val_comb;

    logic [3:0] dec_rd;
    logic [3:0] dec_rn;
    logic [3:0] dec_rm;
    logic [2:0] dec_alu_subop;
    logic [2:0] dec_op_class;
    logic [XLEN-1:0] dec_imm;
    logic dec_decode_fault;

    logic ex_branch_taken;
    logic [XLEN-1:0] ex_branch_target;

    logic bus_reset_ok;
    logic core_reset_ok;
    logic tx_precond_ok;

    assign core_reset_ok = rst_n;
    assign bus_reset_ok  = hresetn;
    assign tx_precond_ok = core_reset_ok & bus_reset_ok;

    assign pc_dbg   = pc_q;
    assign state_dbg= fsm_state_q;

    always @(*) begin
        i_haddr  = pc_q;
        i_htrans = AHB_HTRANS_IDLE[1:0];
        i_hwrite = 1'b0;
        i_hsize  = AHB_HSIZE_WORD[2:0];
        i_hburst = AHB_HBURST_SINGLE[2:0];
        i_hwdata = {AHB_DATA_W{1'b0}};

        d_haddr  = {AHB_ADDR_W{1'b0}};
        d_htrans = AHB_HTRANS_IDLE[1:0];
        d_hwrite = 1'b0;
        d_hsize  = AHB_HSIZE_WORD[2:0];
        d_hburst = AHB_HBURST_SINGLE[2:0];
        d_hwdata = {AHB_DATA_W{1'b0}};

        if (fsm_state_q == ST_FETCH) begin
            i_haddr[0] = 1'b0;
            i_haddr[1] = 1'b0;
            i_htrans = AHB_HTRANS_NONSEQ[1:0];
        end

        if ((fsm_state_q == ST_EXECUTE) && id_ex_valid_q && (id_ex_op_class_q == OP_MEM) && !ex_wb_trap_q) begin
            d_haddr  = id_ex_rn_val_q + id_ex_imm_q;
            d_htrans = AHB_HTRANS_NONSEQ[1:0];
            d_hwrite = if_id_instr_q[11];
            d_hwdata = id_ex_rm_val_q;
        end
    end

    always @(*) begin
        dec_rd          = if_id_instr_q[2:0];
        dec_rn          = if_id_instr_q[5:3];
        dec_rm          = if_id_instr_q[8:6];
        dec_alu_subop   = if_id_instr_q[12:10];
        dec_op_class    = OP_ILLEGAL;
        dec_imm         = {XLEN{1'b0}};
        dec_decode_fault= 1'b0;

        if (if_id_instr_q[15:13] == 3'b010) begin
            dec_op_class = OP_BRANCH;
            dec_imm[8:0] = if_id_instr_q[8:0];
            if (if_id_instr_q[8]) begin
                dec_imm[31:9] = {23{1'b1}};
            end
        end else if (if_id_instr_q[15:13] == 3'b001) begin
            dec_op_class = OP_MEM;
            dec_imm[6:2] = if_id_instr_q[10:6];
        end else if (if_id_instr_q[15:13] == 3'b000) begin
            dec_op_class = OP_ALU;
            dec_imm[7:0] = if_id_instr_q[7:0];
        end else begin
            dec_op_class = OP_ILLEGAL;
            dec_decode_fault = 1'b1;
        end

        if (dec_rd >= REG_COUNT[3:0]) dec_decode_fault = 1'b1;
        if (dec_rn >= REG_COUNT[3:0]) dec_decode_fault = 1'b1;
        if (dec_rm >= REG_COUNT[3:0]) dec_decode_fault = 1'b1;
    end

    always @(*) begin
        rn_val_comb = {XLEN{1'b0}};
        rm_val_comb = {XLEN{1'b0}};

        case (dec_rn)
            4'd0:  rn_val_comb = rf_mem_0;
            4'd1:  rn_val_comb = rf_mem_1;
            4'd2:  rn_val_comb = rf_mem_2;
            4'd3:  rn_val_comb = rf_mem_3;
            4'd4:  rn_val_comb = rf_mem_4;
            4'd5:  rn_val_comb = rf_mem_5;
            4'd6:  rn_val_comb = rf_mem_6;
            4'd7:  rn_val_comb = rf_mem_7;
            4'd8:  rn_val_comb = rf_mem_8;
            4'd9:  rn_val_comb = rf_mem_9;
            4'd10: rn_val_comb = rf_mem_10;
            4'd11: rn_val_comb = rf_mem_11;
            4'd12: rn_val_comb = rf_mem_12;
            4'd13: rn_val_comb = rf_mem_13;
            4'd14: rn_val_comb = rf_mem_14;
            4'd15: rn_val_comb = pc_q;
            default: rn_val_comb = {XLEN{1'b0}};
        endcase

        case (dec_rm)
            4'd0:  rm_val_comb = rf_mem_0;
            4'd1:  rm_val_comb = rf_mem_1;
            4'd2:  rm_val_comb = rf_mem_2;
            4'd3:  rm_val_comb = rf_mem_3;
            4'd4:  rm_val_comb = rf_mem_4;
            4'd5:  rm_val_comb = rf_mem_5;
            4'd6:  rm_val_comb = rf_mem_6;
            4'd7:  rm_val_comb = rf_mem_7;
            4'd8:  rm_val_comb = rf_mem_8;
            4'd9:  rm_val_comb = rf_mem_9;
            4'd10: rm_val_comb = rf_mem_10;
            4'd11: rm_val_comb = rf_mem_11;
            4'd12: rm_val_comb = rf_mem_12;
            4'd13: rm_val_comb = rf_mem_13;
            4'd14: rm_val_comb = rf_mem_14;
            4'd15: rm_val_comb = pc_q;
            default: rm_val_comb = {XLEN{1'b0}};
        endcase
    end

    always @(*) begin
        ex_branch_taken  = 1'b0;
        ex_branch_target = pc_q + 32'd2;

        if (id_ex_op_class_q == OP_BRANCH) begin
            ex_branch_target = (id_ex_pc_q + 32'd2) + (id_ex_imm_q << 1);
            ex_branch_target[0] = 1'b0;
            if (id_ex_alu_subop_q == 3'b000) ex_branch_taken = 1'b1;                  
            if (id_ex_alu_subop_q == 3'b001) ex_branch_taken = nzcv_q[2];              
            if (id_ex_alu_subop_q == 3'b010) ex_branch_taken = ~nzcv_q[2];             
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fsm_state_q <= ST_RESET;
            pc_q <= RESET_PC;
            pc_q[0] <= 1'b0;
            exc_epc_q <= RESET_PC;
            exc_epc_q[0] <= 1'b0;
            trap_code_q <= 7'd0;
            trap_stage_q <= 3'd0;
            trap_q <= 1'b0;
            nzcv_q <= 4'b0000;

            rf_mem_0  <= {XLEN{1'b0}};
            rf_mem_1  <= {XLEN{1'b0}};
            rf_mem_2  <= {XLEN{1'b0}};
            rf_mem_3  <= {XLEN{1'b0}};
            rf_mem_4  <= {XLEN{1'b0}};
            rf_mem_5  <= {XLEN{1'b0}};
            rf_mem_6  <= {XLEN{1'b0}};
            rf_mem_7  <= {XLEN{1'b0}};
            rf_mem_8  <= {XLEN{1'b0}};
            rf_mem_9  <= {XLEN{1'b0}};
            rf_mem_10 <= {XLEN{1'b0}};
            rf_mem_11 <= {XLEN{1'b0}};
            rf_mem_12 <= {XLEN{1'b0}};
            rf_mem_13 <= STACK_RESET;
            rf_mem_14 <= {XLEN{1'b0}};

            if_id_valid_q <= 1'b0;
            if_id_pc_q <= {XLEN{1'b0}};
            if_id_instr_q <= 16'h0000;
            if_id_fault_q <= 1'b0;

            id_ex_valid_q <= 1'b0;
            id_ex_op_class_q <= OP_ILLEGAL;
            id_ex_pc_q <= {XLEN{1'b0}};
            id_ex_rd_q <= 4'd0;
            id_ex_rn_q <= 4'd0;
            id_ex_rm_q <= 4'd0;
            id_ex_rn_val_q <= {XLEN{1'b0}};
            id_ex_rm_val_q <= {XLEN{1'b0}};
            id_ex_imm_q <= {XLEN{1'b0}};
            id_ex_decode_fault_q <= 1'b0;
            id_ex_alu_subop_q <= 3'd0;

            ex_wb_valid_q <= 1'b0;
            ex_wb_rd_q <= 4'd0;
            ex_wb_result_q <= {XLEN{1'b0}};
            ex_wb_flags_q <= 4'd0;
            ex_wb_regwrite_q <= 1'b0;
            ex_wb_retire_ok_q <= 1'b0;
            ex_wb_trap_q <= 1'b0;
            ex_wb_trap_code_q <= 7'd0;
            ex_wb_trap_stage_q <= 3'd0;

            retire <= 1'b0;
            trap <= 1'b0;
        end else begin
            retire <= 1'b0;
            trap <= 1'b0;

            if (fsm_state_q == ST_RESET) begin
                if (tx_precond_ok) fsm_state_q <= ST_FETCH;
            end else if (fsm_state_q == ST_FETCH) begin
                if (trap_q) begin
                    fsm_state_q <= ST_TRAP;
                end else if (i_hready) begin
                    if_id_valid_q <= 1'b1;
                    if_id_pc_q <= pc_q;
                    if_id_fault_q <= i_hresp;
                    if (pc_q[1]) if_id_instr_q <= i_hrdata[31:16];
                    else         if_id_instr_q <= i_hrdata[15:0];
                    fsm_state_q <= ST_DECODE;
                end
            end else if (fsm_state_q == ST_DECODE) begin
                if (if_id_valid_q && tx_precond_ok) begin
                    id_ex_valid_q <= 1'b1;
                    id_ex_op_class_q <= dec_op_class;
                    id_ex_pc_q <= if_id_pc_q;
                    id_ex_rd_q <= dec_rd;
                    id_ex_rn_q <= dec_rn;
                    id_ex_rm_q <= dec_rm;
                    id_ex_rn_val_q <= rn_val_comb;
                    id_ex_rm_val_q <= rm_val_comb;
                    id_ex_imm_q <= dec_imm;
                    id_ex_decode_fault_q <= dec_decode_fault | if_id_fault_q;
                    id_ex_alu_subop_q <= dec_alu_subop;
                    if_id_valid_q <= 1'b0;
                    fsm_state_q <= ST_EXECUTE;
                end
            end else if (fsm_state_q == ST_EXECUTE) begin
                ex_wb_valid_q <= id_ex_valid_q;
                ex_wb_rd_q <= id_ex_rd_q;
                ex_wb_result_q <= {XLEN{1'b0}};
                ex_wb_flags_q <= nzcv_q;
                ex_wb_regwrite_q <= 1'b0;
                ex_wb_retire_ok_q <= 1'b0;
                ex_wb_trap_q <= 1'b0;
                ex_wb_trap_code_q <= 7'd0;
                ex_wb_trap_stage_q <= 3'd3;

                if (id_ex_valid_q) begin
                    if (id_ex_decode_fault_q || (id_ex_op_class_q == OP_ILLEGAL)) begin
                        ex_wb_trap_q <= 1'b1;
                        ex_wb_trap_code_q <= TRAP_ILLEGAL;
                        ex_wb_retire_ok_q <= 1'b0;
                    end else if (id_ex_op_class_q == OP_ALU) begin
                        if (id_ex_alu_subop_q == 3'b000) begin
                            alu_add_ext = {1'b0,id_ex_rn_val_q[15:0]} + {1'b0,id_ex_rm_val_q[15:0]};
                            ex_wb_result_q <= id_ex_rn_val_q + id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                            ex_wb_flags_q[1] <= alu_add_ext[16];
                            ex_wb_flags_q[0] <= (id_ex_rn_val_q[XLEN-1] == id_ex_rm_val_q[XLEN-1]) && (ex_wb_result_q[XLEN-1] != id_ex_rn_val_q[XLEN-1]);
                        end else if (id_ex_alu_subop_q == 3'b001) begin
                            alu_sub_ext = {1'b0,id_ex_rn_val_q[15:0]} - {1'b0,id_ex_rm_val_q[15:0]};
                            ex_wb_result_q <= id_ex_rn_val_q - id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                            ex_wb_flags_q[1] <= ~alu_sub_ext[16];
                            ex_wb_flags_q[0] <= (id_ex_rn_val_q[XLEN-1] != id_ex_rm_val_q[XLEN-1]) && (ex_wb_result_q[XLEN-1] != id_ex_rn_val_q[XLEN-1]);
                        end else if (id_ex_alu_subop_q == 3'b010) begin
                            ex_wb_result_q <= id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= id_ex_rm_val_q[XLEN-1];
                            ex_wb_flags_q[2] <= (id_ex_rm_val_q == {XLEN{1'b0}});
                        end else if (id_ex_alu_subop_q == 3'b011) begin
                            ex_wb_result_q <= id_ex_rn_val_q & id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                        end else if (id_ex_alu_subop_q == 3'b100) begin
                            ex_wb_result_q <= id_ex_rn_val_q | id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                        end else if (id_ex_alu_subop_q == 3'b101) begin
                            ex_wb_result_q <= id_ex_rn_val_q ^ id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b1;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                        end else if (id_ex_alu_subop_q == 3'b110) begin
                            alu_sub_ext = {1'b0,id_ex_rn_val_q[15:0]} - {1'b0,id_ex_rm_val_q[15:0]};
                            ex_wb_result_q <= id_ex_rn_val_q - id_ex_rm_val_q;
                            ex_wb_regwrite_q <= 1'b0;
                            ex_wb_retire_ok_q <= 1'b1;
                            ex_wb_flags_q[3] <= ex_wb_result_q[XLEN-1];
                            ex_wb_flags_q[2] <= (ex_wb_result_q == {XLEN{1'b0}});
                            ex_wb_flags_q[1] <= ~alu_sub_ext[16];
                            ex_wb_flags_q[0] <= (id_ex_rn_val_q[XLEN-1] != id_ex_rm_val_q[XLEN-1]) && (ex_wb_result_q[XLEN-1] != id_ex_rn_val_q[XLEN-1]);
                        end else begin
                            ex_wb_trap_q <= 1'b1;
                            ex_wb_trap_code_q <= TRAP_ILLEGAL;
                        end
                    end else if (id_ex_op_class_q == OP_MEM) begin
                        if (((id_ex_rn_val_q + id_ex_imm_q) & 32'h00000003) != 32'h00000000) begin
                            ex_wb_trap_q <= 1'b1;
                            ex_wb_trap_code_q <= TRAP_MISALIGN;
                            ex_wb_retire_ok_q <= 1'b0;
                        end else if (!d_hready) begin
                            fsm_state_q <= ST_MEMWAIT;
                        end else if (d_hresp) begin
                            ex_wb_trap_q <= 1'b1;
                            ex_wb_trap_code_q <= TRAP_BUS;
                            ex_wb_retire_ok_q <= 1'b0;
                        end else begin
                            if (if_id_instr_q[11]) begin
                                ex_wb_regwrite_q <= 1'b0;
                                ex_wb_retire_ok_q <= 1'b1;
                            end else begin
                                ex_wb_result_q <= d_hrdata;
                                ex_wb_regwrite_q <= 1'b1;
                                ex_wb_retire_ok_q <= 1'b1;
                            end
                        end
                    end else if (id_ex_op_class_q == OP_BRANCH) begin
                        ex_wb_regwrite_q <= 1'b0;
                        ex_wb_retire_ok_q <= 1'b1;
                    end
                end

                if (fsm_state_q == ST_EXECUTE) begin
                    if (ex_wb_trap_q) fsm_state_q <= ST_TRAP;
                    else fsm_state_q <= ST_FETCH;
                end
            end else if (fsm_state_q == ST_MEMWAIT) begin
                if (d_hready) begin
                    if (d_hresp) begin
                        ex_wb_trap_q <= 1'b1;
                        ex_wb_trap_code_q <= TRAP_BUS;
                        ex_wb_retire_ok_q <= 1'b0;
                        fsm_state_q <= ST_TRAP;
                    end else begin
                        if (!if_id_instr_q[11]) begin
                            ex_wb_result_q <= d_hrdata;
                            ex_wb_regwrite_q <= 1'b1;
                        end else begin
                            ex_wb_regwrite_q <= 1'b0;
                        end
                        ex_wb_retire_ok_q <= 1'b1;
                        fsm_state_q <= ST_FETCH;
                    end
                end
            end else if (fsm_state_q == ST_TRAP) begin
                pc_q <= TRAP_VECTOR;
                pc_q[0] <= 1'b0;
                trap_q <= 1'b0;
                fsm_state_q <= ST_FETCH;
                if_id_valid_q <= 1'b0;
                id_ex_valid_q <= 1'b0;
                ex_wb_valid_q <= 1'b0;
            end

            if (ex_wb_valid_q) begin
                if (ex_wb_trap_q) begin
                    trap <= 1'b1;
                    trap_q <= 1'b1;
                    trap_code_q <= ex_wb_trap_code_q;
                    trap_stage_q <= ex_wb_trap_stage_q;
                    exc_epc_q <= id_ex_pc_q;
                    exc_epc_q[0] <= 1'b0;
                end else if (ex_wb_retire_ok_q && !trap_q) begin
                    retire <= 1'b1;

                    if (id_ex_op_class_q == OP_BRANCH) begin
                        if (ex_branch_taken) begin
                            pc_q <= ex_branch_target;
                            pc_q[0] <= 1'b0;
                            if_id_valid_q <= 1'b0;
                        end else begin
                            pc_q <= pc_q + 32'd2;
                            pc_q[0] <= 1'b0;
                        end
                    end else begin
                        pc_q <= pc_q + 32'd2;
                        pc_q[0] <= 1'b0;
                    end

                    if (ex_wb_flags_q != nzcv_q) nzcv_q <= ex_wb_flags_q;

                    if (ex_wb_regwrite_q) begin
                        if (ex_wb_rd_q == 4'd15) begin
                            trap <= 1'b1;
                            retire <= 1'b0;
                            trap_q <= 1'b1;
                            trap_code_q <= TRAP_ILLEGAL;
                            trap_stage_q <= 3'd4;
                            exc_epc_q <= id_ex_pc_q;
                            exc_epc_q[0] <= 1'b0;
                        end else begin
                            case (ex_wb_rd_q)
                                4'd0:  rf_mem_0  <= ex_wb_result_q;
                                4'd1:  rf_mem_1  <= ex_wb_result_q;
                                4'd2:  rf_mem_2  <= ex_wb_result_q;
                                4'd3:  rf_mem_3  <= ex_wb_result_q;
                                4'd4:  rf_mem_4  <= ex_wb_result_q;
                                4'd5:  rf_mem_5  <= ex_wb_result_q;
                                4'd6:  rf_mem_6  <= ex_wb_result_q;
                                4'd7:  rf_mem_7  <= ex_wb_result_q;
                                4'd8:  rf_mem_8  <= ex_wb_result_q;
                                4'd9:  rf_mem_9  <= ex_wb_result_q;
                                4'd10: rf_mem_10 <= ex_wb_result_q;
                                4'd11: rf_mem_11 <= ex_wb_result_q;
                                4'd12: rf_mem_12 <= ex_wb_result_q;
                                4'd13: rf_mem_13 <= ex_wb_result_q;
                                4'd14: rf_mem_14 <= ex_wb_result_q;
                                default: rf_mem_0 <= rf_mem_0;
                            endcase
                        end
                    end
                end
            end
        end
    end

endmodule
