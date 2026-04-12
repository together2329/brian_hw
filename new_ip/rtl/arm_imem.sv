//=============================================================================
// ARM Instruction Memory
// Simple instruction memory with 32-bit wide read port
// Preloaded with test program at initialization
//=============================================================================

module arm_imem (
    input  logic        clk,
    input  logic [31:0] addr,         // Word-aligned address
    output logic [31:0] instr         // 32-bit instruction output
);

    // 4KB instruction memory (1024 x 32-bit words)
    logic [31:0] mem [0:1023];

    // Instruction read — synchronous
    always_ff @(posedge clk) begin
        instr <= mem[addr[11:2]]; // Word-aligned, ignore [1:0]
    end

    // Include test program initialization
    initial begin
        $readmemh("arm_program.hex", mem);
    end

endmodule
