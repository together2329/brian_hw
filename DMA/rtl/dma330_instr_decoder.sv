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
            8'h21, 8'h23,  // DMALPEND (loop end, lc0/lc1)
            8'h31, 8'h33,  // DMALPEND (forever variants)
            8'h35,   // DMAFLUSHP
            8'h34,   // DMASEV
            8'h36,   // DMAWFE
            8'h24, 8'h25,  // DMALDP
            8'h2C, 8'h2D,  // DMALDPS
            8'h28, 8'h29,  // DMASTP
            8'h2E, 8'h2F:  // DMASTPS
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
    // Decode Logic — Full Opcode Decode & Operand Extraction
    //
    // PL330 byte layout (little-endian, byte0 = opcode):
    //   byte0[7:0]   = opcode
    //   byte1[7:0]   = secondary byte (immediate / register select)
    //   byte2[7:0]..byte5[7:0] = 32-bit immediate (byte2=LSB)
    //
    // Many instructions use bit patterns in byte0 and byte1 to distinguish
    // sub-variants.  The raw byte patterns below follow the PL330 TRM.
    // =========================================================================
    always_comb begin : decode_output
        logic [7:0] byte0, byte1;
        logic [31:0] imm32_field;
        byte0 = byte_shift_reg[7:0];
        byte1 = byte_shift_reg[15:8];
        imm32_field = byte_shift_reg[47:16];  // bytes 2-5 (6-byte instructions)

        decoded_o = '0;
        decoded_o.valid     = (dec_state == DEC_READY);
        // Encode instruction length: 0=1B, 1=2B, 2=3B, 3=6B
        // predicted_len stores the actual byte count (1,2,3,6).
        case (predicted_len)
            3'd6:    decoded_o.instr_len = 2'd3;  // 6-byte
            3'd3:    decoded_o.instr_len = 2'd2;  // 3-byte
            3'd2:    decoded_o.instr_len = 2'd1;  // 2-byte
            3'd1:    decoded_o.instr_len = 2'd0;  // 1-byte
            default: decoded_o.instr_len = 2'd0;  // fallback: 1-byte
        endcase

        case (byte0)
            // ==============================================================
            // 1-byte instructions
            // ==============================================================
            8'h00:   // DMAEND
                decoded_o.opcode = OPC_DMAEND;

            8'h01:   // DMAKILL (manager only)
                decoded_o.opcode = OPC_DMAKILL;

            8'h18:   // DMANOP
                decoded_o.opcode = OPC_DMANOP;

            8'h12:   // DMARMB
                decoded_o.opcode = OPC_DMARMB;

            8'h13:   // DMAWMB
                decoded_o.opcode = OPC_DMAWMB;

            8'h36:   // DMAWFE — wait for event
                begin
                    decoded_o.opcode    = OPC_DMAWFE;
                    decoded_o.event_num = byte1[3:0];
                end

            8'h34:   // DMASEV — send event
                begin
                    decoded_o.opcode    = OPC_DMASEV;
                    decoded_o.event_num = byte1[3:0];
                end

            // ==============================================================
            // Load / Store — 1-byte or 2-byte variants
            // byte0 bit[1] = 0:DMALD, 1:DMAST
            // byte0 bit[4] = 1:peripheral variant (DMALDP/DMASTP)
            // byte0 bit[0] = ns (non-secure) hint
            // ==============================================================
            8'h04, 8'h05:   // DMALD / DMALD (ns-bit)
                decoded_o.opcode = OPC_DMALD;

            8'h0C, 8'h0D:   // DMALD with store-and-forward hint
                decoded_o.opcode = OPC_DMALDS;

            8'h24, 8'h25:   // DMALDP — load from peripheral
                begin
                    decoded_o.opcode    = OPC_DMALDP;
                    decoded_o.periph_num = byte1[3:0];
                end

            8'h2C, 8'h2D:   // DMALDPS — load from peripheral (S&F)
                begin
                    decoded_o.opcode    = OPC_DMALDPS;
                    decoded_o.periph_num = byte1[3:0];
                end

            8'h08, 8'h09:   // DMAST / DMAST (ns-bit)
                decoded_o.opcode = OPC_DMAST;

            8'h0E, 8'h0F:   // DMASTS
                decoded_o.opcode = OPC_DMASTS;

            8'h28, 8'h29:   // DMASTP — store to peripheral
                begin
                    decoded_o.opcode    = OPC_DMASTP;
                    decoded_o.periph_num = byte1[3:0];
                end

            8'h2E, 8'h2F:   // DMASTPS
                begin
                    decoded_o.opcode    = OPC_DMASTPS;
                    decoded_o.periph_num = byte1[3:0];
                end

            // ==============================================================
            // 2-byte instructions
            // ==============================================================
            8'h54:   // DMAADDH — add immediate to SA or DA
                begin
                    decoded_o.opcode     = OPC_DMAADDH;
                    // byte1[7] = 0:DA, 1:SA
                    decoded_o.reg_select = byte1[7] ? 2'd0 : 2'd1;
                    decoded_o.imm16      = {8'h0, byte1[6:0]};  // 7-bit unsigned imm
                end

            8'h5C:   // DMAADNH — subtract immediate from SA or DA
                begin
                    decoded_o.opcode     = OPC_DMAADNH;
                    decoded_o.reg_select = byte1[7] ? 2'd0 : 2'd1;
                    decoded_o.imm16      = {8'h0, byte1[6:0]};
                end

            8'h20:   // DMALP — loop start (loop counter 0)
                begin
                    decoded_o.opcode       = OPC_DMALP;
                    decoded_o.loop_cntr_sel = 1'b0;
                    decoded_o.imm16        = {8'h0, byte1};
                end

            8'h22:   // DMALP — loop start (loop counter 1)
                begin
                    decoded_o.opcode       = OPC_DMALP;
                    decoded_o.loop_cntr_sel = 1'b1;
                    decoded_o.imm16        = {8'h0, byte1};
                end

            8'h21:   // DMALPEND — loop end (loop counter 0, backwards jump)
                begin
                    decoded_o.opcode       = OPC_DMALPEND;
                    decoded_o.loop_cntr_sel = 1'b0;
                    decoded_o.imm16        = {8'h0, byte1};  // backwards jump offset
                end

            8'h23:   // DMALPEND — loop end (loop counter 1, backwards jump)
                begin
                    decoded_o.opcode       = OPC_DMALPEND;
                    decoded_o.loop_cntr_sel = 1'b1;
                    decoded_o.imm16        = {8'h0, byte1};
                end

            8'h31, 8'h33:  // DMALPEND — forever loop variants
                begin
                    decoded_o.opcode       = OPC_DMALPEND;
                    decoded_o.loop_cntr_sel = byte0[1];  // 0=LC0, 1=LC1
                    decoded_o.imm16        = {8'h0, byte1};
                end

            8'h35:   // DMAFLUSHP — flush peripheral
                begin
                    decoded_o.opcode     = OPC_DMAFLUSHP;
                    decoded_o.periph_num = byte1[3:0];
                end

            // ==============================================================
            // 6-byte instructions
            // ==============================================================
            8'hBC:   // DMAMOV — move immediate to SA/DA/CC
                begin
                    decoded_o.opcode     = OPC_DMAMOV;
                    decoded_o.reg_select = byte1[1:0];  // 0=SA, 1=DA, 2=CC
                    decoded_o.imm32      = imm32_field;
                end

            8'hA0:   // DMAGO — start channel (manager only)
                begin
                    decoded_o.opcode = OPC_DMAGO;
                    // byte1[5:3] = channel number, byte1[0] = ns bit
                    decoded_o.periph_num = byte1[5:3];
                    decoded_o.imm32      = imm32_field;  // starting PC
                end

            // ==============================================================
            // Invalid / Unrecognized
            // ==============================================================
            default: begin
                decoded_o.opcode = OPC_INVALID;
                decoded_o.fault  = 1'b1;
                decoded_o.valid  = 1'b1;  // still assert valid for fault handling
            end
        endcase
    end

endmodule : dma330_instr_decoder
