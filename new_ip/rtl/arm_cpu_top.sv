//=============================================================================
// ARM CPU Top-Level Module
// Integrates CPU Core with Instruction and Data memories
// Supports ARM (32-bit) instruction set:
//   - Data Processing (AND, EOR, SUB, RSB, ADD, ADC, SBC, RSC,
//                      TST, TEQ, CMP, CMN, ORR, MOV, BIC, MVN)
//   - Load/Store (LDR, STR, LDRB, STRB)
//   - Branch (B, BL)
//   - Block Transfer (LDM, STM)
//   - Multiply (MUL, MLA)
//   - Software Interrupt (SWI)
//   - Status Register (MRS, MSR)
//=============================================================================

module arm_cpu_top (
    input  logic        clk,
    input  logic        rst_n,

    // External interface signals
    output logic [31:0] gpio_out,       // General purpose output (from memory-mapped IO)
    input  logic [31:0] gpio_in,        // General purpose input

    // Debug / status
    output logic [31:0] debug_pc,
    output logic [31:0] debug_instr,
    output logic [3:0]  debug_state,
    output logic [31:0] debug_reg_r0,
    output logic [31:0] debug_reg_r1,
    output logic [31:0] debug_reg_r2,
    output logic [31:0] debug_reg_r3,
    output logic        running         // CPU is active
);

    //=========================================================
    // Internal buses
    //=========================================================

    // Instruction memory bus
    logic [31:0] imem_addr;
    logic [31:0] imem_rdata;

    // Data memory bus
    logic        dmem_req;
    logic        dmem_we;
    logic        dmem_byte;
    logic [31:0] dmem_addr;
    logic [31:0] dmem_wdata;
    logic [31:0] dmem_rdata;
    logic        dmem_ready;

    //=========================================================
    // CPU Core Instance
    //=========================================================

    arm_cpu_core u_core (
        .clk          (clk),
        .rst_n        (rst_n),
        .imem_addr    (imem_addr),
        .imem_rdata   (imem_rdata),
        .dmem_req     (dmem_req),
        .dmem_we      (dmem_we),
        .dmem_byte    (dmem_byte),
        .dmem_addr    (dmem_addr),
        .dmem_wdata   (dmem_wdata),
        .dmem_rdata   (dmem_rdata),
        .dmem_ready   (dmem_ready),
        .debug_pc     (debug_pc),
        .debug_instr  (debug_instr),
        .debug_state  (debug_state),
        .debug_reg_r0 (debug_reg_r0),
        .debug_reg_r1 (debug_reg_r1),
        .debug_reg_r2 (debug_reg_r2),
        .debug_reg_r3 (debug_reg_r3)
    );

    //=========================================================
    // Instruction Memory Instance
    //=========================================================

    arm_imem u_imem (
        .clk   (clk),
        .addr  (imem_addr),
        .instr (imem_rdata)
    );

    //=========================================================
    // Data Memory Instance
    //=========================================================

    arm_dmem u_dmem (
        .clk       (clk),
        .rst_n     (rst_n),
        .mem_req   (dmem_req),
        .mem_we    (dmem_we),
        .mem_byte  (dmem_byte),
        .addr      (dmem_addr),
        .wdata     (dmem_wdata),
        .rdata     (dmem_rdata),
        .mem_ready (dmem_ready)
    );

    //=========================================================
    // Memory-mapped IO
    // Address 0xFFFF_0000 = GPIO output
    // Address 0xFFFF_0004 = GPIO input
    //=========================================================

    always_ff @(posedge clk) begin
        if (dmem_req && dmem_we && dmem_addr == 32'hFFFF_0000) begin
            gpio_out <= dmem_wdata;
        end
    end

    //=========================================================
    // Status
    //=========================================================
    assign running = rst_n;

endmodule
