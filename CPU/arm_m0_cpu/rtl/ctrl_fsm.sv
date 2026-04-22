//============================================================================
// Module : ctrl_fsm
// Description : Control FSM for ARM M0-style CPU
//               Pipeline sequencer: RESET→FETCH→DECODE→EXECUTE→WRITEBACK
//               Interrupt handling: IRQ_ENTRY→IRQ_STACK_PUSH→IRQ_FETCH
//               PUSH/POP multi-cycle sequencing
//               BL two-instruction tracking
//============================================================================

module ctrl_fsm (
    input  logic         clk,
    input  logic         rst_n,

    // FSM state outputs
    output logic [1:0]   pc_sel,
    output logic [31:0]  branch_target,
    output logic         flush,
    output logic         de_clear,
    output logic         fetch_enable,

    // IRQ input
    input  logic         irq,

    // From execute_unit: branch resolution
    input  logic         branch_taken,
    input  logic [31:0]  branch_target_out,
    input  logic         exc_return_detected,

    // From decode_unit: instruction type
    input  logic         de_is_push,
    input  logic         de_is_pop,
    input  logic         de_is_bl,
    input  logic         de_valid,

    // Memory acknowledge
    input  logic         mem_ack,

    // BL tracking outputs to decode_unit
    output logic         bl_first_half,
    output logic [31:0]  bl_offset_hi,

    // Register file control
    output logic         reg_write_en,
    output logic [3:0]   reg_write_addr,
    output logic [31:0]  reg_write_data,

    // SP direct write for IRQ stacking
    output logic         sp_write_en,
    output logic [31:0]  sp_write_data,

    // IRQ state
    output logic         irq_masked,

    // Execute stage writeback
    input  logic         wb_reg_en,
    input  logic [3:0]   wb_reg_addr,
    input  logic [31:0]  wb_reg_data,
    input  logic         wb_sp_write_en,
    input  logic [31:0]  wb_sp_write_data
);

    // ---------------------------------------------------------------
    // FSM states
    // ---------------------------------------------------------------
    typedef enum logic [3:0] {
        STATE_RESET      = 4'd0,
        STATE_FETCH      = 4'd1,
        STATE_DECODE     = 4'd2,
        STATE_EXECUTE    = 4'd3,
        STATE_MEM_WAIT   = 4'd4,
        STATE_WRITEBACK  = 4'd5,
        STATE_IRQ_ENTRY  = 4'd6,
        STATE_IRQ_PUSH   = 4'd7,
        STATE_IRQ_FETCH  = 4'd8,
        STATE_PUSH_PREP  = 4'd9,
        STATE_PUSH_ITER  = 4'd10,
        STATE_POP_ITER   = 4'd11,
        STATE_BL_WAIT    = 4'd12
    } state_t;

    state_t state_reg, state_next;

    // PC selection encoding
    localparam [1:0] PC_SEQ   = 2'b00;
    localparam [1:0] PC_BRANCH = 2'b01;
    localparam [1:0] PC_IRQ   = 2'b10;
    localparam [1:0] PC_RESET = 2'b11;

    // ---------------------------------------------------------------
    // IRQ stacking registers
    // ---------------------------------------------------------------
    logic [2:0]   irq_push_count;     // 0-7: which register to push
    logic [31:0]  saved_sp;           // SP at IRQ entry
    logic [31:0]  irq_saved_regs [0:7]; // R0,R1,R2,R3,R12,LR,PC,xPSR

    // ---------------------------------------------------------------
    // PUSH/POP tracking
    // ---------------------------------------------------------------
    logic [2:0]   push_pop_count;
    logic [2:0]   push_pop_total;
    logic [7:0]   push_pop_rlist;
    logic         push_pop_lr;
    logic         push_pop_pc;
    logic [31:0]  push_pop_sp;
    logic         is_pushing;
    logic         is_popping;

    // ---------------------------------------------------------------
    // BL tracking
    // ---------------------------------------------------------------
    logic [31:0]  bl_offset_hi_reg;

    // ---------------------------------------------------------------
    // FSM state register
    // ---------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state_reg       <= STATE_RESET;
            bl_first_half   <= 1'b0;
            bl_offset_hi    <= 32'd0;
            bl_offset_hi_reg <= 32'd0;
            irq_masked      <= 1'b0;
            irq_push_count  <= 3'd0;
            saved_sp        <= 32'd0;
            push_pop_count  <= 3'd0;
            is_pushing      <= 1'b0;
            is_popping      <= 1'b0;
        end else begin
            state_reg <= state_next;

            // BL tracking
            if (state_reg == STATE_DECODE && de_valid && de_is_bl && !bl_first_half) begin
                bl_first_half   <= 1'b1;
                bl_offset_hi_reg <= {20'd0, 1'b0, de_valid ? 11'd0 : 11'd0}; // placeholder
                // Actually extract the imm11 from current instruction
                // For now, stored in decode
            end else if (state_reg == STATE_DECODE && de_valid && de_is_bl && bl_first_half) begin
                bl_first_half <= 1'b0;
            end

            // IRQ masking
            if (state_reg == STATE_IRQ_ENTRY) begin
                irq_masked <= 1'b1;
            end else if (exc_return_detected && branch_taken) begin
                irq_masked <= 1'b0;
            end
        end
    end

    // ---------------------------------------------------------------
    // Next state logic
    // ---------------------------------------------------------------
    always_comb begin
        state_next   = state_reg;
        pc_sel       = PC_SEQ;
        branch_target = 32'd0;
        flush        = 1'b0;
        de_clear     = 1'b0;
        fetch_enable = 1'b0;

        case (state_reg)
            // -------------------------------------------------------
            STATE_RESET: begin
                pc_sel       = PC_RESET;
                fetch_enable = 1'b1;
                state_next   = STATE_FETCH;
            end

            // -------------------------------------------------------
            STATE_FETCH: begin
                fetch_enable = 1'b1;
                // Check for interrupt
                if (irq && !irq_masked) begin
                    state_next = STATE_IRQ_ENTRY;
                end else begin
                    state_next = STATE_DECODE;
                end
            end

            // -------------------------------------------------------
            STATE_DECODE: begin
                if (!de_valid) begin
                    state_next = STATE_DECODE;  // Wait for valid decode
                end else begin
                    // Check for BL first half
                    if (de_is_bl && !bl_first_half) begin
                        state_next = STATE_BL_WAIT;
                    end else if (de_is_push) begin
                        state_next = STATE_PUSH_PREP;
                    end else if (de_is_pop) begin
                        state_next = STATE_POP_ITER;
                    end else begin
                        state_next = STATE_EXECUTE;
                    end
                end
            end

            // -------------------------------------------------------
            STATE_EXECUTE: begin
                if (branch_taken) begin
                    flush        = 1'b1;
                    de_clear     = 1'b1;
                    branch_target = branch_target_out;
                    pc_sel       = PC_BRANCH;
                    state_next   = STATE_FETCH;
                end else if (de_valid && (/* mem_req or mem_we */ 1'b0)) begin
                    state_next = STATE_MEM_WAIT;
                end else begin
                    state_next = STATE_WRITEBACK;
                end
            end

            // -------------------------------------------------------
            STATE_MEM_WAIT: begin
                if (mem_ack) begin
                    state_next = STATE_WRITEBACK;
                end
            end

            // -------------------------------------------------------
            STATE_WRITEBACK: begin
                de_clear    = 1'b1;
                state_next = STATE_FETCH;
            end

            // -------------------------------------------------------
            // BL first half received, wait for second half
            STATE_BL_WAIT: begin
                state_next = STATE_FETCH; // Will fetch next instruction (BL second half)
            end

            // -------------------------------------------------------
            // IRQ handling
            STATE_IRQ_ENTRY: begin
                state_next = STATE_IRQ_PUSH;
            end

            // -------------------------------------------------------
            STATE_IRQ_PUSH: begin
                if (irq_push_count == 3'd7) begin
                    state_next = STATE_IRQ_FETCH;
                end
            end

            // -------------------------------------------------------
            STATE_IRQ_FETCH: begin
                pc_sel    = PC_IRQ;
                flush     = 1'b1;
                state_next = STATE_FETCH;
            end

            // -------------------------------------------------------
            // PUSH multi-cycle
            STATE_PUSH_PREP: begin
                state_next = STATE_PUSH_ITER;
            end

            STATE_PUSH_ITER: begin
                if (push_pop_count >= push_pop_total) begin
                    state_next = STATE_FETCH;
                end
            end

            // -------------------------------------------------------
            // POP multi-cycle
            STATE_POP_ITER: begin
                if (push_pop_count >= push_pop_total) begin
                    state_next = STATE_FETCH;
                end
            end

            // -------------------------------------------------------
            default: begin
                state_next = STATE_RESET;
            end
        endcase
    end

    // ---------------------------------------------------------------
    // Register writeback pass-through
    // ---------------------------------------------------------------
    assign reg_write_en   = wb_reg_en;
    assign reg_write_addr = wb_reg_addr;
    assign reg_write_data = wb_reg_data;
    assign sp_write_en   = wb_sp_write_en;
    assign sp_write_data = wb_sp_write_data;

endmodule
