//=============================================================================
// ARM Control Unit
// Generates control signals for the datapath based on decoded instruction
// 3-stage pipeline: FETCH -> DECODE/EXECUTE -> WRITEBACK
//=============================================================================

module arm_control (
    input  logic        clk,
    input  logic        rst_n,

    // From decoder
    input  logic        is_data_proc,
    input  logic        s_bit,
    input  logic        is_imm_op2,
    input  logic        is_load_store,
    input  logic        is_load,
    input  logic        is_store,
    input  logic        is_byte,
    input  logic        is_pre_index,
    input  logic        is_writeback,
    input  logic        is_branch,
    input  logic        is_branch_link,
    input  logic        is_block_trans,
    input  logic        is_swi,
    input  logic        is_mul,
    input  logic        is_msr,
    input  logic        is_mrs,
    input  logic        cond_pass,

    // Datapath control
    output logic        regfile_we,       // Register file write enable
    output logic        flags_we,         // CPSR flags write enable
    output logic        pc_we,            // PC write enable
    output logic        pc_sel,           // PC source: 0=PC+4, 1=branch target
    output logic        lr_we,            // Link register write (for BL)
    output logic        mem_req,          // Memory request
    output logic        mem_we,           // Memory write enable
    output logic        mem_byte,         // Byte access
    output logic [1:0]  result_sel,      // Result mux: 00=ALU, 01=mem, 10=PC+8 (for ADR)
    output logic        alu_op_en,        // ALU operation valid
    output logic        shifter_en,       // Shifter enable
    output logic        shift_imm_sel,    // 1=immediate shift encoding
    output logic        msr_we,           // MSR write to CPSR
    output logic        stall             // Pipeline stall (for multicycle ops)
);

    typedef enum logic [2:0] {
        FETCH   = 3'b000,
        DECODE  = 3'b001,
        EXECUTE = 3'b010,
        MEMORY  = 3'b011,
        WRITEBACK = 3'b100
    } state_t;

    state_t state, next_state;

    // State machine
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= FETCH;
        end else begin
            state <= next_state;
        end
    end

    // Next state logic
    always_comb begin
        next_state = FETCH;
        stall = 1'b0;

        case (state)
            FETCH: begin
                next_state = DECODE;
            end

            DECODE: begin
                next_state = EXECUTE;
            end

            EXECUTE: begin
                if (is_load_store && cond_pass) begin
                    next_state = MEMORY;
                end else begin
                    next_state = WRITEBACK;
                end
            end

            MEMORY: begin
                next_state = WRITEBACK;
                stall = 1'b1;
            end

            WRITEBACK: begin
                next_state = FETCH;
            end

            default: next_state = FETCH;
        endcase
    end

    // Control signal generation
    always_comb begin
        // Defaults
        regfile_we    = 1'b0;
        flags_we      = 1'b0;
        pc_we         = 1'b0;
        pc_sel        = 1'b0;
        lr_we         = 1'b0;
        mem_req       = 1'b0;
        mem_we        = 1'b0;
        mem_byte      = 1'b0;
        result_sel    = 2'b00;
        alu_op_en     = 1'b0;
        shifter_en    = 1'b0;
        shift_imm_sel = 1'b0;
        msr_we        = 1'b0;

        case (state)
            DECODE: begin
                shifter_en    = is_data_proc | is_load_store | is_mul;
                shift_imm_sel = is_imm_op2;
            end

            EXECUTE: begin
                alu_op_en = 1'b1;

                // Branch handling
                if (is_branch && cond_pass) begin
                    pc_sel = 1'b1;
                    pc_we  = 1'b1;
                    if (is_branch_link) begin
                        lr_we = 1'b1;
                    end
                end

                // SWI — treat as branch to vector
                if (is_swi && cond_pass) begin
                    pc_sel = 1'b1;
                    pc_we  = 1'b1;
                end

                // Data processing write
                if (is_data_proc && cond_pass) begin
                    regfile_we = 1'b1;
                    result_sel = 2'b00; // ALU result
                    flags_we   = s_bit;
                end

                // MSR/MRS
                if (is_msr && cond_pass) begin
                    msr_we = 1'b1;
                end

                if (is_mrs && cond_pass) begin
                    regfile_we = 1'b1;
                    result_sel = 2'b10;
                end
            end

            MEMORY: begin
                if (is_load_store && cond_pass) begin
                    mem_req  = 1'b1;
                    mem_we   = is_store;
                    mem_byte = is_byte;
                end
            end

            WRITEBACK: begin
                // Load: write data from memory to register
                if (is_load && cond_pass) begin
                    regfile_we = 1'b1;
                    result_sel = 2'b01; // Memory data
                end

                // PC increment for non-branch
                if (!is_branch || !cond_pass) begin
                    pc_we = 1'b1;
                    pc_sel = 1'b0; // PC + 4
                end
            end

            default: ; // Do nothing
        endcase
    end

endmodule
