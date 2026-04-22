// =============================================================================
// dma330_instr_decoder.sv — DMA-330 Instruction Decoder
//
// Accepts raw instruction bytes (up to 6 bytes per instruction) from the
// instruction fetch unit, accumulates them, and decodes into a
// decoded_instr_t struct.  PL330 instructions are variable-length:
//   - 1 byte: DMAEND, DMANOP, DMARMB, DMAWMB, DMAWFE, DMAKILL
//             DMALD, DMALDP, DMAST, DMASTP
//   - 2 bytes: DMAADDH, DMAADNH, DMALP, DMALPEND, DMAFLUSHP, DMASEV
//   - 6 bytes: DMAMOV, DMAGO
//
// The byte pipeline uses valid/ready handshakes on both input and output.
// =============================================================================

module dma330_instr_decoder (
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // Byte Input Interface (from instruction fetch)
    // =========================================================================
    input  logic [47:0]                   instr_bytes,   // up to 6 bytes (byte0=LSB)
    input  logic [2:0]                    instr_bytes_cnt, // how many bytes valid (1-6)
    input  logic                          instr_valid,
    output logic                          instr_ready,

    // =========================================================================
    // Decoded Output Interface
    // =========================================================================
    output dma330_pkg::decoded_instr_t    decoded_o,
    output logic                          decoded_valid,
    input  logic                          decoded_ready,

    // =========================================================================
    // Current Program Counter (for context)
    // =========================================================================
    input  logic [31:0]                   current_pc
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // FSM States
    // =========================================================================
    typedef enum logic [1:0] {
        DEC_IDLE      = 2'h0,
        DEC_COLLECTING = 2'h1,
        DEC_READY     = 2'h2
    } dec_state_t;

    dec_state_t dec_state;

    // =========================================================================
    // Byte Accumulation Shift Register
    // =========================================================================
    logic [47:0] byte_shift_reg;    // collected instruction bytes
    logic [2:0]  byte_count;        // number of bytes collected (0-6)

    // =========================================================================
    // Instruction Length Predictor (combinational)
    //
    // Examines the opcode byte (byte0) to determine the instruction length.
    // PL330 encoding:
    //   6-byte: DMAMOV (0xBC), DMAGO (0xA0)
    //   2-byte: DMAADDH, DMAADNH, DMALP, DMALPEND, DMAFLUSHP, DMASEV
    //   1-byte: everything else
    // =========================================================================
    logic [2:0] predicted_len;  // 1, 2, or 6

    always_comb begin : length_predict
        logic [7:0] opcode;
        opcode = byte_shift_reg[7:0];  // byte0 is always the opcode

        case (opcode)
            8'hBC,   // DMAMOV
            8'hA0:   // DMAGO
                predicted_len = 3'd6;

            8'h54,   // DMAADDH
            8'h5C,   // DMAADNH
            8'h20, 8'h22,  // DMALP (loop start)
            8'h21, 8'h23, 8'h31, 8'h33,  // DMALPEND
            8'h35,   // DMAFLUSHP
            8'h34:   // DMASEV
                predicted_len = 3'd2;

            default:
                predicted_len = 3'd1;
        endcase
    end

    // =========================================================================
    // FSM — Byte Collection & Decode
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : decoder_fsm
        if (!rst_n) begin
            dec_state      <= DEC_IDLE;
            byte_shift_reg <= 48'h0;
            byte_count     <= 3'h0;
        end else begin
            case (dec_state)
                // -------------------------------------------------------------
                // DEC_IDLE: wait for new instruction bytes
                // -------------------------------------------------------------
                DEC_IDLE: begin
                    if (instr_valid && instr_bytes_cnt > 0) begin
                        // Load bytes directly into shift register
                        byte_shift_reg <= instr_bytes;
                        byte_count     <= instr_bytes_cnt;
                        if (predicted_len <= instr_bytes_cnt) begin
                            // We have enough bytes — decode is ready
                            dec_state <= DEC_READY;
                        end else begin
                            dec_state <= DEC_COLLECTING;
                        end
                    end
                end

                // -------------------------------------------------------------
                // DEC_COLLECTING: accumulate more bytes until we have enough
                // -------------------------------------------------------------
                DEC_COLLECTING: begin
                    if (instr_valid && instr_bytes_cnt > 0) begin
                        // Shift register loading — simplified for skeleton.
                        // Assumes full instruction arrives in at most 2 beats.
                        // Merge new bytes after already-collected bytes.
                        case (byte_count)
                            3'd1: byte_shift_reg[47:8]  <= instr_bytes[39:0];
                            3'd2: byte_shift_reg[47:16] <= instr_bytes[31:0];
                            3'd3: byte_shift_reg[47:24] <= instr_bytes[23:0];
                            3'd4: byte_shift_reg[47:32] <= instr_bytes[15:0];
                            3'd5: byte_shift_reg[47:40] <= instr_bytes[7:0];
                            default: byte_shift_reg <= instr_bytes;
                        endcase
                        byte_count <= byte_count + instr_bytes_cnt;
                        if (predicted_len <= byte_count + instr_bytes_cnt) begin
                            dec_state <= DEC_READY;
                        end
                    end
                end

                // -------------------------------------------------------------
                // DEC_READY: decoded instruction available, wait for consumer
                // -------------------------------------------------------------
                DEC_READY: begin
                    if (decoded_ready) begin
                        // Consumer accepted — return to idle
                        dec_state      <= DEC_IDLE;
                        byte_shift_reg <= 48'h0;
                        byte_count     <= 3'h0;
                    end
                end

                default: dec_state <= DEC_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Output Handshake
    // =========================================================================
    assign decoded_valid = (dec_state == DEC_READY);

    // Back-pressure to fetch unit: accept bytes when IDLE or COLLECTING
    assign instr_ready = (dec_state == DEC_IDLE) || (dec_state == DEC_COLLECTING);

    // =========================================================================
    // Decode Logic — combinational (full decode in next task)
    // =========================================================================
    always_comb begin : decode_output
        decoded_o = '0;
        decoded_o.valid = (dec_state == DEC_READY);
        // Opcode from byte0
        case (byte_shift_reg[7:0])
            8'h00: decoded_o.opcode = OPC_DMAEND;
            8'h01: decoded_o.opcode = OPC_DMAKILL;
            8'h18: decoded_o.opcode = OPC_DMANOP;
            8'h12: decoded_o.opcode = OPC_DMARMB;
            8'h13: decoded_o.opcode = OPC_DMAWMB;
            8'h36: decoded_o.opcode = OPC_DMAWFE;
            8'h04: decoded_o.opcode = OPC_DMALD;
            8'h24: decoded_o.opcode = OPC_DMALDP;
            8'h08: decoded_o.opcode = OPC_DMAST;
            8'h28: decoded_o.opcode = OPC_DMASTP;
            8'h54: decoded_o.opcode = OPC_DMAADDH;
            8'h5C: decoded_o.opcode = OPC_DMAADNH;
            8'h20, 8'h22: decoded_o.opcode = OPC_DMALP;
            8'h21, 8'h23, 8'h31, 8'h33: decoded_o.opcode = OPC_DMALPEND;
            8'h35: decoded_o.opcode = OPC_DMAFLUSHP;
            8'h34: decoded_o.opcode = OPC_DMASEV;
            8'hBC: decoded_o.opcode = OPC_DMAMOV;
            8'hA0: decoded_o.opcode = OPC_DMAGO;
            default: begin
                decoded_o.opcode = OPC_INVALID;
                decoded_o.fault  = 1'b1;
            end
        endcase
        decoded_o.instr_len = predicted_len[1:0];
    end

endmodule : dma330_instr_decoder
