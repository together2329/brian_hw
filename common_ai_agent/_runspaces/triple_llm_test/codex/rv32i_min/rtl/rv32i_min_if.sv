module rv32i_min_if #(
    parameter integer XLEN = 32,
    parameter integer RESET_PC = 0,
    parameter integer INST_ALIGN = 4
) (
    input  logic                  clk,
    input  logic                  rst_n,

    input  logic                  run_i,
    input  logic                  hold_i,
    input  logic                  fault_block_retire_i,

    input  logic                  branch_valid_i,
    input  logic                  branch_taken_i,
    input  logic [XLEN-1:0]       branch_imm_i,

    input  logic                  jump_valid_i,
    input  logic                  jump_is_jalr_i,
    input  logic [XLEN-1:0]       jump_rs1_i,
    input  logic [XLEN-1:0]       jump_imm_i,

    input  logic                  is_ecall_i,
    input  logic                  is_ebreak_i,
    input  logic                  illegal_shamt_i,
    input  logic                  misaligned_access_i,

    input  logic [XLEN-1:0]       i_rdata,
    input  logic [XLEN-1:0]       d_rdata,

    output logic [XLEN-1:0]       i_addr,
    output logic                  i_valid,

    output logic [XLEN-1:0]       d_addr,
    output logic [XLEN-1:0]       d_wdata,
    output logic                  d_we,
    output logic [3:0]            d_be,
    output logic                  d_valid,
    output logic                  excpt_o,

    output logic [XLEN-1:0]       pc_o,
    output logic [XLEN-1:0]       next_pc_o,
    output logic [XLEN-1:0]       if_pc_o,
    output logic [XLEN-1:0]       if_instr_o,
    output logic                  if_valid_o,
    output logic                  pc_align_fault_o,
    output logic                  is_branch_o,
    output logic                  branch_taken_o,
    output logic [XLEN-1:0]       branch_imm_o,
    output logic                  is_jump_o,
    output logic                  is_jalr_o,
    output logic [XLEN-1:0]       jump_rs1_o,
    output logic [XLEN-1:0]       jump_imm_o
);

    localparam [XLEN-1:0] INST_ALIGN_XLEN = INST_ALIGN;
    localparam [XLEN-1:0] PC_PLUS4_XLEN   = 32'd4;

    logic [XLEN-1:0] pc_q;
    logic [XLEN-1:0] next_pc_d;
    logic [XLEN-1:0] pc_plus4;
    logic [XLEN-1:0] branch_target;
    logic [XLEN-1:0] jal_target;
    logic [XLEN-1:0] jalr_sum;
    logic [XLEN-1:0] jalr_target;

    logic             pc_mod_align_is_zero;
    logic             fetch_accept;
    logic             system_excpt_req;
    logic             force_pc_advance_system;

    logic             branch_taken_path;
    logic             jump_taken_path;

    logic             id_ex_valid_q;
    logic             mem_wb_valid_q;
    logic [XLEN-1:0] id_ex_pc_q;
    logic [XLEN-1:0] mem_wb_pc_q;

    logic [XLEN-1:0] d_addr_q;
    logic [XLEN-1:0] d_wdata_q;
    logic [3:0]      d_be_q;
    logic            d_valid_q;
    logic            d_we_q;

    logic            system_excpt_pulse_q;

    assign pc_plus4      = pc_q + PC_PLUS4_XLEN;
    assign branch_target = pc_q + branch_imm_i;
    assign jal_target    = pc_q + jump_imm_i;
    assign jalr_sum      = jump_rs1_i + jump_imm_i;
    assign jalr_target   = {jalr_sum[XLEN-1:1], 1'b0};

    assign branch_taken_path = branch_valid_i & branch_taken_i;
    assign jump_taken_path   = jump_valid_i;

    assign pc_mod_align_is_zero = ((pc_q % INST_ALIGN_XLEN) == {XLEN{1'b0}});

    assign system_excpt_req         = is_ecall_i | is_ebreak_i | illegal_shamt_i | misaligned_access_i;
    assign force_pc_advance_system  = is_ecall_i | is_ebreak_i;

    always @(*) begin
        next_pc_d = pc_plus4;

        if (branch_taken_path) begin
            next_pc_d = branch_target;
        end else if (branch_valid_i) begin
            next_pc_d = pc_plus4;
        end else if (jump_taken_path) begin
            if (jump_is_jalr_i) next_pc_d = jalr_target;
            else                next_pc_d = jal_target;
        end else begin
            next_pc_d = pc_plus4;
        end
    end

    assign fetch_accept = run_i & (~hold_i) & pc_mod_align_is_zero;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_q             <= RESET_PC[XLEN-1:0];
            if_pc_o          <= {XLEN{1'b0}};
            if_instr_o       <= {XLEN{1'b0}};
            if_valid_o       <= 1'b0;
            pc_align_fault_o <= 1'b0;
            is_branch_o      <= 1'b0;
            branch_taken_o   <= 1'b0;
            branch_imm_o     <= {XLEN{1'b0}};
            is_jump_o        <= 1'b0;
            is_jalr_o        <= 1'b0;
            jump_rs1_o       <= {XLEN{1'b0}};
            jump_imm_o       <= {XLEN{1'b0}};

            id_ex_valid_q    <= 1'b0;
            mem_wb_valid_q   <= 1'b0;
            id_ex_pc_q       <= {XLEN{1'b0}};
            mem_wb_pc_q      <= {XLEN{1'b0}};

            d_addr_q         <= {XLEN{1'b0}};
            d_wdata_q        <= {XLEN{1'b0}};
            d_be_q           <= 4'b0000;
            d_valid_q        <= 1'b0;
            d_we_q           <= 1'b0;
            system_excpt_pulse_q <= 1'b0;
        end else begin
            if_valid_o       <= 1'b0;
            pc_align_fault_o <= 1'b0;

            id_ex_valid_q    <= if_valid_o;
            mem_wb_valid_q   <= id_ex_valid_q;
            id_ex_pc_q       <= if_pc_o;
            mem_wb_pc_q      <= id_ex_pc_q;

            d_addr_q         <= mem_wb_pc_q;
            d_wdata_q        <= d_rdata;
            d_be_q           <= 4'b1111;
            d_we_q           <= 1'b0;
            d_valid_q        <= mem_wb_valid_q & (~fault_block_retire_i);

            system_excpt_pulse_q <= fetch_accept & system_excpt_req;

            if (fetch_accept) begin
                if_pc_o    <= pc_q;
                if_instr_o <= i_rdata;
                if_valid_o <= 1'b1;

                is_branch_o    <= branch_valid_i;
                branch_taken_o <= branch_taken_i;
                branch_imm_o   <= branch_imm_i;
                is_jump_o      <= jump_valid_i;
                is_jalr_o      <= jump_is_jalr_i;
                jump_rs1_o     <= jump_rs1_i;
                jump_imm_o     <= jump_imm_i;

                if (force_pc_advance_system) begin
                    pc_q <= pc_plus4;
                end else if (!fault_block_retire_i) begin
                    pc_q <= next_pc_d;
                end else begin
                    pc_q <= pc_q;
                end
            end else if (run_i & (~hold_i) & (~pc_mod_align_is_zero)) begin
                pc_align_fault_o <= 1'b1;
                is_branch_o      <= 1'b0;
                branch_taken_o   <= 1'b0;
                branch_imm_o     <= {XLEN{1'b0}};
                is_jump_o        <= 1'b0;
                is_jalr_o        <= 1'b0;
                jump_rs1_o       <= {XLEN{1'b0}};
                jump_imm_o       <= {XLEN{1'b0}};
                pc_q             <= pc_q;
            end
        end
    end

    always @(*) begin
        i_addr    = pc_q;
        i_valid   = run_i & (~hold_i) & pc_mod_align_is_zero;
        next_pc_o = next_pc_d;
        pc_o      = pc_q;

        d_addr    = d_addr_q;
        d_wdata   = d_wdata_q;
        d_be      = d_be_q;
        d_we      = d_we_q;
        d_valid   = d_valid_q;

        excpt_o   = pc_align_fault_o | system_excpt_pulse_q;
    end

endmodule
