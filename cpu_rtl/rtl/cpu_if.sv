// ============================================================================
// Module: cpu_if
// Description: Instruction Fetch Stage - RISC-V RV32I 5-stage pipeline
//              - PC management (increment, branch, jump)
//              - AXI4-Lite master for instruction fetch
//              - Pipeline register IF/ID
// ============================================================================

module cpu_if #(
    parameter ADDR_WIDTH = 32,
    parameter DATA_WIDTH = 32
)(
    input  logic                     clk,
    input  logic                     rst_n,

    // Control inputs
    input  logic                     stall_i,        // Freeze PC and IF/ID reg
    input  logic                     flush_i,        // Insert NOP bubble
    input  logic                     branch_taken_i, // Branch/jump taken from EX
    input  logic [ADDR_WIDTH-1:0]    branch_target_i,// Branch/jump target address
    input  logic                     jump_i,         // Jump instruction (JAL/JALR)
    input  logic [ADDR_WIDTH-1:0]    jump_target_i,  // Jump target address

    // AXI4-Lite Instruction Fetch (AR channel)
    output logic [ADDR_WIDTH-1:0]    if_araddr,
    output logic [2:0]               if_arprot,
    output logic                     if_arvalid,
    input  logic                     if_arready,

    // AXI4-Lite Instruction Fetch (R channel)
    input  logic [DATA_WIDTH-1:0]    if_rdata,
    input  logic [1:0]               if_rresp,
    input  logic                     if_rvalid,
    output logic                     if_rready,

    // Pipeline register outputs (IF/ID)
    output logic [DATA_WIDTH-1:0]    if_id_instruction_o,
    output logic [ADDR_WIDTH-1:0]    if_id_pc_o,
    output logic [ADDR_WIDTH-1:0]    if_id_pc_plus4_o,
    output logic                     if_id_valid_o
);

    // =========================================================================
    // Internal signals
    // =========================================================================
    logic [ADDR_WIDTH-1:0] pc_reg;
    logic [ADDR_WIDTH-1:0] pc_next;
    logic [ADDR_WIDTH-1:0] pc_plus4;
    logic                  pc_en;

    logic [DATA_WIDTH-1:0] if_id_instruction_reg;
    logic [ADDR_WIDTH-1:0] if_id_pc_reg;
    logic [ADDR_WIDTH-1:0] if_id_pc_plus4_reg;
    logic                  if_id_valid_reg;

    // AXI fetch state machine
    typedef enum logic [1:0] {
        FETCH_IDLE   = 2'b00,
        FETCH_ADDR   = 2'b01,
        FETCH_DATA   = 2'b10,
        FETCH_DONE   = 2'b11
    } fetch_state_t;

    fetch_state_t fetch_state;
    logic [DATA_WIDTH-1:0] fetched_instruction;
    logic                  fetch_complete;

    // =========================================================================
    // PC Management
    // =========================================================================
    assign pc_plus4 = pc_reg + 4;

    // PC next logic: priority -> branch/jump > normal increment
    always_comb begin
        pc_next = pc_plus4; // Default: sequential
        if (branch_taken_i) begin
            pc_next = branch_target_i;
        end else if (jump_i) begin
            pc_next = jump_target_i;
        end
    end

    // PC enable: freeze during stall or AXI wait
    assign pc_en = ~stall_i & ~flush_i;

    // PC register
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc_reg <= 32'hFFFF0000; // Reset vector (Boot ROM)
        end else if (pc_en) begin
            pc_reg <= pc_next;
        end
    end

    // =========================================================================
    // AXI4-Lite Instruction Fetch FSM
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fetch_state    <= FETCH_IDLE;
            if_araddr      <= '0;
            if_arprot      <= 3'b000; // Unprivileged, secure, data access
            if_arvalid     <= 1'b0;
            if_rready      <= 1'b0;
            fetch_complete <= 1'b0;
            fetched_instruction <= 32'h00000013; // NOP
        end else begin
            fetch_complete <= 1'b0;

            case (fetch_state)
                FETCH_IDLE: begin
                    if_arvalid  <= 1'b0;
                    if_rready   <= 1'b0;
                    if (!stall_i) begin
                        fetch_state <= FETCH_ADDR;
                    end
                end

                FETCH_ADDR: begin
                    if_araddr  <= pc_reg;
                    if_arprot  <= 3'b110; // Instruction fetch, privileged
                    if_arvalid <= 1'b1;
                    if (if_arready && if_arvalid) begin
                        if_arvalid  <= 1'b0;
                        fetch_state <= FETCH_DATA;
                    end
                end

                FETCH_DATA: begin
                    if_rready <= 1'b1;
                    if (if_rvalid && if_rready) begin
                        if_rready         <= 1'b0;
                        fetched_instruction <= if_rdata;
                        fetch_complete    <= 1'b1;
                        fetch_state       <= FETCH_DONE;
                    end
                end

                FETCH_DONE: begin
                    if (stall_i) begin
                        fetch_state <= FETCH_DONE; // Wait until stall releases
                    end else begin
                        fetch_state <= FETCH_IDLE;
                    end
                end

                default: fetch_state <= FETCH_IDLE;
            endcase

            // Handle flush: restart fetch from new target
            if (flush_i) begin
                fetch_state    <= FETCH_IDLE;
                if_arvalid     <= 1'b0;
                if_rready      <= 1'b0;
                fetch_complete <= 1'b0;
            end
        end
    end

    // =========================================================================
    // IF/ID Pipeline Register
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            if_id_instruction_reg <= 32'h00000013; // NOP
            if_id_pc_reg         <= 32'hFFFF0000;
            if_id_pc_plus4_reg   <= 32'hFFFF0004;
            if_id_valid_reg      <= 1'b0;
        end else if (flush_i) begin
            // Insert NOP bubble on flush
            if_id_instruction_reg <= 32'h00000013; // NOP (ADDI x0, x0, 0)
            if_id_pc_reg         <= pc_reg;
            if_id_pc_plus4_reg   <= pc_plus4;
            if_id_valid_reg      <= 1'b0;
        end else if (stall_i) begin
            // Hold current values during stall
        end else if (fetch_complete) begin
            if_id_instruction_reg <= fetched_instruction;
            if_id_pc_reg         <= pc_reg;
            if_id_pc_plus4_reg   <= pc_plus4;
            if_id_valid_reg      <= 1'b1;
        end
    end

    // =========================================================================
    // Output assignments
    // =========================================================================
    assign if_id_instruction_o = if_id_instruction_reg;
    assign if_id_pc_o          = if_id_pc_reg;
    assign if_id_pc_plus4_o    = if_id_pc_plus4_reg;
    assign if_id_valid_o       = if_id_valid_reg;

endmodule
