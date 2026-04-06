// ============================================================================
// Module: cpu_ctrl
// Description: Main Control Unit for RISC-V RV32I
//              Decodes opcode and generates control signals for pipeline
// ============================================================================

module cpu_ctrl (
    input  logic [6:0]  opcode_i,
    input  logic [2:0]  funct3_i,
    input  logic        funct7_5_i,    // funct7[5] for R-type sub/sra distinction

    // Control signals
    output logic        reg_write_o,    // Write to register file
    output logic        mem_read_o,     // Read from data memory
    output logic        mem_write_o,    // Write to data memory
    output logic        mem_to_reg_o,   // 0=ALU result, 1=memory data
    output logic        alu_src_o,      // 0=register, 1=immediate
    output logic        branch_o,       // Branch instruction
    output logic [1:0]  jump_o,         // 00=none, 01=JAL, 10=JALR
    output logic [1:0]  alu_op_o,       // ALU operation type
    output logic [1:0]  mem_size_o,     // 00=byte, 01=halfword, 10=word
    output logic        mem_unsigned_o, // Unsigned load extension
    output logic        csr_read_o,     // CSR read
    output logic        csr_write_o,    // CSR write
    output logic        csr_imm_o,      // CSR immediate (vs register)
    output logic        system_o        // System instruction (ECALL/EBREAK/MRET)
);

    // =========================================================================
    // Opcode definitions
    // =========================================================================
    localparam [6:0] OP_RTYPE  = 7'b0110011;  // R-type ALU
    localparam [6:0] OP_ITYPE  = 7'b0010011;  // I-type ALU
    localparam [6:0] OP_LOAD   = 7'b0000011;  // Load
    localparam [6:0] OP_STORE  = 7'b0100011;  // Store
    localparam [6:0] OP_BRANCH = 7'b1100011;  // Branch
    localparam [6:0] OP_LUI    = 7'b0110111;  // LUI
    localparam [6:0] OP_AUIPC  = 7'b0010111;  // AUIPC
    localparam [6:0] OP_JAL    = 7'b1101111;  // JAL
    localparam [6:0] OP_JALR   = 7'b1100111;  // JALR
    localparam [6:0] OP_SYSTEM = 7'b1110011;  // System (ECALL/EBREAK/CSR/MRET)

    // =========================================================================
    // Main decoder
    // =========================================================================
    always_comb begin
        // Default: all signals deasserted
        reg_write_o    = 1'b0;
        mem_read_o     = 1'b0;
        mem_write_o    = 1'b0;
        mem_to_reg_o   = 1'b0;
        alu_src_o      = 1'b0;
        branch_o       = 1'b0;
        jump_o         = 2'b00;
        alu_op_o       = 2'b00;
        mem_size_o     = 2'b10;  // Default word
        mem_unsigned_o = 1'b0;
        csr_read_o     = 1'b0;
        csr_write_o    = 1'b0;
        csr_imm_o      = 1'b0;
        system_o       = 1'b0;

        case (opcode_i)
            OP_RTYPE: begin
                reg_write_o = 1'b1;
                alu_src_o   = 1'b0;    // Register source
                alu_op_o    = 2'b10;   // R-type ALU
            end

            OP_ITYPE: begin
                reg_write_o = 1'b1;
                alu_src_o   = 1'b1;    // Immediate source
                alu_op_o    = 2'b11;   // I-type ALU
            end

            OP_LOAD: begin
                reg_write_o  = 1'b1;
                mem_read_o   = 1'b1;
                mem_to_reg_o = 1'b1;
                alu_src_o    = 1'b1;   // Base + offset
                alu_op_o     = 2'b00;  // ADD for address calc
                // Memory size based on funct3
                case (funct3_i)
                    3'b000: begin mem_size_o = 2'b00; mem_unsigned_o = 1'b0; end // LB
                    3'b001: begin mem_size_o = 2'b01; mem_unsigned_o = 1'b0; end // LH
                    3'b010: begin mem_size_o = 2'b10; mem_unsigned_o = 1'b0; end // LW
                    3'b100: begin mem_size_o = 2'b00; mem_unsigned_o = 1'b1; end // LBU
                    3'b101: begin mem_size_o = 2'b01; mem_unsigned_o = 1'b1; end // LHU
                    default: begin mem_size_o = 2'b10; mem_unsigned_o = 1'b0; end
                endcase
            end

            OP_STORE: begin
                mem_write_o = 1'b1;
                alu_src_o   = 1'b1;    // Base + offset
                alu_op_o    = 2'b00;   // ADD for address calc
                // Memory size based on funct3
                case (funct3_i)
                    3'b000: mem_size_o = 2'b00; // SB
                    3'b001: mem_size_o = 2'b01; // SH
                    3'b010: mem_size_o = 2'b10; // SW
                    default: mem_size_o = 2'b10;
                endcase
            end

            OP_BRANCH: begin
                branch_o = 1'b1;
                alu_op_o = 2'b01;      // Branch compare
            end

            OP_LUI: begin
                reg_write_o = 1'b1;
                alu_op_o    = 2'b00;   // Pass immediate
                alu_src_o   = 1'b1;
            end

            OP_AUIPC: begin
                reg_write_o = 1'b1;
                alu_op_o    = 2'b00;   // ADD PC + imm
                alu_src_o   = 1'b1;
            end

            OP_JAL: begin
                reg_write_o = 1'b1;
                jump_o      = 2'b01;   // JAL
            end

            OP_JALR: begin
                reg_write_o = 1'b1;
                jump_o      = 2'b10;   // JALR
                alu_src_o   = 1'b1;
            end

            OP_SYSTEM: begin
                system_o = 1'b1;
                case (funct3_i)
                    3'b000: begin
                        // ECALL/EBREAK/MRET - handled by system_o
                        reg_write_o = 1'b0;
                    end
                    3'b001: begin // CSRRW
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    3'b010: begin // CSRRS
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    3'b011: begin // CSRRC
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    3'b101: begin // CSRRWI
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        csr_imm_o   = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    3'b110: begin // CSRRSI
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        csr_imm_o   = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    3'b111: begin // CSRRCI
                        csr_read_o  = 1'b1;
                        csr_write_o = 1'b1;
                        csr_imm_o   = 1'b1;
                        reg_write_o = 1'b1;
                    end
                    default: begin
                        csr_read_o  = 1'b0;
                        csr_write_o = 1'b0;
                    end
                endcase
            end

            default: begin
                // Unknown opcode - treat as NOP
            end
        endcase
    end

endmodule
