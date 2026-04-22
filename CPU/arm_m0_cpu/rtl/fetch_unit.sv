//============================================================================
// Module : fetch_unit
// Description : Instruction Fetch Stage for ARM M0-style CPU
//               PC management, instruction address output
//               PC increments by 2 (Thumb mode)
//               Supports branch target, IRQ vector, and sequential PC
//============================================================================

module fetch_unit (
    input  logic         clk,
    input  logic         rst_n,

    // PC selection control from ctrl_fsm
    input  logic [1:0]   pc_sel,         // 00=seq, 01=branch, 10=irq_vector, 11=reset
    input  logic [31:0]  branch_target,  // Branch/BX target address
    input  logic         flush,          // Flush pipeline (on branch/IRQ)
    input  logic         de_clear,       // Clear pipeline when instruction is done
    input  logic         fetch_enable,   // Enable fetching (FSM in RESET/FETCH)

    // Instruction fetch interface
    output logic [31:0]  instr_addr,     // Instruction fetch address (= PC)
    output logic         instr_req,      // Instruction fetch request

    // Pipeline register outputs (FETCH → DECODE)
    output logic [15:0]  fd_instr,       // Fetched instruction
    output logic [31:0]  fd_pc,          // PC of this instruction
    output logic         fd_valid,       // Fetch stage has valid output

    // Instruction data input (from memory)
    input  logic [15:0]  instr_rdata,    // Fetched instruction data from memory
    input  logic         instr_ack,      // Instruction memory acknowledge

    // Current PC output (for reg_file PC+4 reads)
    output logic [31:0]  current_pc
);

    // PC selection encoding
    localparam [1:0] PC_SEQ   = 2'b00;
    localparam [1:0] PC_BRANCH = 2'b01;
    localparam [1:0] PC_IRQ   = 2'b10;
    localparam [1:0] PC_RESET = 2'b11;

    logic [31:0] pc_reg;
    logic [31:0] pc_next;

    // ---------------------------------------------------------------
    // PC register
    // ---------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            pc_reg   <= 32'd0;
            fd_instr <= 16'd0;
            fd_pc    <= 32'd0;
            fd_valid <= 1'b0;
        end else begin
            pc_reg <= pc_next;

            if (flush || de_clear) begin
                fd_valid <= 1'b0;
            end else if (instr_ack) begin
                // Capture instruction when memory acknowledges
                fd_instr <= instr_rdata;
                fd_pc    <= pc_reg;
                fd_valid <= 1'b1;
            end
            // Hold fd_valid and fd_instr stable until flush or new ack
        end
    end

    // ---------------------------------------------------------------
    // PC next logic (combinational)
    // ---------------------------------------------------------------
    always_comb begin
        case (pc_sel)
            PC_SEQ: begin
                if (fetch_enable) begin
                    pc_next = pc_reg + 32'd2;     // Sequential: PC + 2 (Thumb)
                end else begin
                    pc_next = pc_reg;             // Hold PC when not fetching
                end
            end
            PC_BRANCH: pc_next = branch_target;       // Branch target
            PC_IRQ:    pc_next = 32'h00000018;        // IRQ vector address
            PC_RESET:  pc_next = 32'd0;               // Reset vector
            default:   pc_next = pc_reg + 32'd2;
        endcase
    end

    // ---------------------------------------------------------------
    // Output assignments
    // ---------------------------------------------------------------
    assign instr_addr  = pc_reg;
    assign instr_req   = fetch_enable;  // Only request when FSM allows
    assign current_pc  = pc_reg;

endmodule
