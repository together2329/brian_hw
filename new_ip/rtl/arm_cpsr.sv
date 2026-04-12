//=============================================================================
// ARM CPSR (Current Program Status Register)
// Stores N, Z, C, V flags and processor mode bits
//=============================================================================

module arm_cpsr (
    input  logic        clk,
    input  logic        rst_n,

    // Flag write interface
    input  logic        update_flags,  // Write enable for flags
    input  logic        flag_n_in,
    input  logic        flag_z_in,
    input  logic        flag_c_in,
    input  logic        flag_v_in,

    // MSR write interface (for MSR instruction)
    input  logic        msr_we,        // MSR write enable
    input  logic [31:0] msr_data,

    // Flag outputs
    output logic        flag_n,
    output logic        flag_z,
    output logic        flag_c,
    output logic        flag_v,

    // Full CPSR read
    output logic [31:0] cpsr_out,

    // Mode bits
    output logic [4:0]  mode,          // Processor mode
    output logic        thumb,         // Thumb state
    output logic        fiq_disable,
    output logic        irq_disable
);

    logic [31:0] cpsr_reg;

    // CPSR bit field definitions:
    // [31]    N - Negative
    // [30]    Z - Zero
    // [29]    C - Carry
    // [28]    V - Overflow
    // [27:24] Reserved
    // [23:20] Reserved (GE bits in ARMv6+)
    // [19:16] Reserved
    // [15]    I - IRQ disable
    // [14]    F - FIQ disable
    // [13:10] Reserved
    // [9]     E - Endianness
    // [8:6]   Reserved
    // [5]     T - Thumb state
    // [4:0]   M - Mode bits

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cpsr_reg <= 32'h0000_00D3; // SVC mode, IRQ/FIQ disabled, ARM state
        end else begin
            // MSR write takes priority
            if (msr_we) begin
                cpsr_reg[31:28] <= msr_data[31:28]; // NZCV flags
                cpsr_reg[15]    <= msr_data[15];     // I bit
                cpsr_reg[14]    <= msr_data[14];     // F bit
                cpsr_reg[5]     <= msr_data[5];      // T bit
                cpsr_reg[4:0]   <= msr_data[4:0];    // Mode
            end
            else if (update_flags) begin
                cpsr_reg[31] <= flag_n_in;
                cpsr_reg[30] <= flag_z_in;
                cpsr_reg[29] <= flag_c_in;
                cpsr_reg[28] <= flag_v_in;
            end
        end
    end

    // Output assignments
    assign flag_n       = cpsr_reg[31];
    assign flag_z       = cpsr_reg[30];
    assign flag_c       = cpsr_reg[29];
    assign flag_v       = cpsr_reg[28];
    assign irq_disable  = cpsr_reg[15];
    assign fiq_disable  = cpsr_reg[14];
    assign thumb        = cpsr_reg[5];
    assign mode         = cpsr_reg[4:0];
    assign cpsr_out     = cpsr_reg;

endmodule
