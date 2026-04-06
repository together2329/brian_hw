//============================================================================
// TDISP Nonce Generator and Validator
// Generates 32-byte cryptographic nonces for LOCK_INTERFACE_RESPONSE
// Validates nonces for START_INTERFACE_REQUEST
// LFSR/PRNG based for RTL simulation; production replaces with TRNG interface
// Per PCIe Base Spec Rev 7.0, Chapter 11
//============================================================================

module tdisp_nonce_gen #(
    parameter int unsigned NUM_TDI      = 4,
    parameter int unsigned NONCE_WIDTH  = 256,
    parameter int unsigned SEED         = 32'hDEADBEEF
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- Nonce generation request (from lock_ctrl) ---
    input  logic                            gen_req_i,               // Request nonce generation
    input  logic [$clog2(NUM_TDI)-1:0]      gen_tdi_index_i,         // TDI index for generated nonce
    output logic                            gen_ack_o,               // Nonce ready
    output logic [NONCE_WIDTH-1:0]          gen_nonce_o,             // Generated nonce

    //--- Nonce validation request (from start_interface handler) ---
    input  logic                            val_req_i,               // Request nonce validation
    input  logic [$clog2(NUM_TDI)-1:0]      val_tdi_index_i,         // TDI index to validate
    input  logic [NONCE_WIDTH-1:0]          val_nonce_i,             // Nonce to validate against
    output logic                            val_ack_o,               // Validation complete
    output logic                            val_match_o,             // 1=nonce matches

    //--- Nonce invalidation (one-time use after START_INTERFACE) ---
    input  logic                            inv_req_i,               // Invalidate used nonce
    input  logic [$clog2(NUM_TDI)-1:0]      inv_tdi_index_i,         // TDI index to invalidate

    //--- Status ---
    output logic                            entropy_warn_o           // Low entropy warning
);

    import tdisp_types::*;

    //==========================================================================
    // Local parameters
    //==========================================================================
    localparam int unsigned NONCE_BYTES = NONCE_WIDTH / 8;
    // Number of 32-bit LFSR steps to fill 256-bit nonce (8 steps)
    localparam int unsigned LFSR_ROUNDS = NONCE_WIDTH / 32;

    //==========================================================================
    // LFSR-based PRNG (32-bit maximal-length Galois LFSR)
    // Production note: Replace with hardware TRNG interface
    //==========================================================================
    logic [31:0] lfsr_state_q;
    logic        lfsr_en;
    logic [31:0] lfsr_next;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lfsr_state_q <= SEED[31:0];
        end else if (lfsr_en) begin
            lfsr_state_q <= lfsr_next;
        end
    end

    // Galois LFSR with polynomial x^32 + x^22 + x^2 + x^1 + 1
    always_comb begin
        lfsr_next = lfsr_state_q;
        if (lfsr_state_q[0]) begin
            lfsr_next = {1'b0, lfsr_state_q[31:1]} ^ 32'h8020_0003;
        end else begin
            lfsr_next = {1'b0, lfsr_state_q[31:1]};
        end
    end

    //==========================================================================
    // Per-TDI nonce storage (consolidated to single always_ff)
    //==========================================================================
    logic [NONCE_WIDTH-1:0] nonce_store_q [NUM_TDI];
    logic [NUM_TDI-1:0]     nonce_valid_q;     // Per-TDI nonce valid flag
    logic                   gen_store_pulse;   // Pulse from generation FSM to store
    logic [NONCE_WIDTH-1:0] gen_nonce_final;   // Final nonce value to store
    logic [$clog2(NUM_TDI)-1:0] gen_tdi_target;// Target TDI for storage

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < NUM_TDI; i++) begin
                nonce_store_q[i] <= '0;
                nonce_valid_q[i] <= 1'b0;
            end
        end else begin
            // Generation store (lower priority)
            if (gen_store_pulse && gen_tdi_target < NUM_TDI) begin
                nonce_store_q[gen_tdi_target] <= gen_nonce_final;
                nonce_valid_q[gen_tdi_target] <= 1'b1;
            end
            // Invalidation (highest priority - one-time use enforcement)
            if (inv_req_i && inv_tdi_index_i < NUM_TDI) begin
                nonce_valid_q[inv_tdi_index_i] <= 1'b0;
                nonce_store_q[inv_tdi_index_i]  <= '0;
            end
        end
    end

    //==========================================================================
    // Generation FSM
    //==========================================================================
    typedef enum logic [2:0] {
        GEN_IDLE,
        GEN_RUN,
        GEN_COMPLETE
    } gen_state_e;

    gen_state_e     gen_state_q;
    logic [2:0]     gen_count_q;           // 0..7 rounds
    logic [NONCE_WIDTH-1:0] gen_buf_q;     // Accumulating nonce buffer
    logic [$clog2(NUM_TDI)-1:0] gen_tdi_q; // Latched TDI index for storage

    // Store-interface signals (driven combinationally from FSM state)
    always_comb begin
        gen_store_pulse = 1'b0;
        gen_nonce_final = '0;
        gen_tdi_target  = '0;
        if (gen_state_q == GEN_COMPLETE) begin
            gen_store_pulse = 1'b1;
            gen_nonce_final = gen_buf_q;
            gen_tdi_target  = gen_tdi_q;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gen_state_q  <= GEN_IDLE;
            gen_count_q  <= '0;
            gen_buf_q    <= '0;
            gen_tdi_q    <= '0;
            gen_ack_o    <= 1'b0;
            gen_nonce_o  <= '0;
            lfsr_en      <= 1'b0;
            entropy_warn_o <= 1'b0;
        end else begin
            lfsr_en    <= 1'b0;
            gen_ack_o  <= 1'b0;

            case (gen_state_q)
                //----------------------------------------------------------
                GEN_IDLE: begin
                    entropy_warn_o <= 1'b0;
                    if (gen_req_i) begin
                        gen_count_q <= '0;
                        gen_buf_q   <= '0;
                        gen_tdi_q   <= gen_tdi_index_i; // Latch TDI index from port
                        lfsr_en     <= 1'b1;
                        gen_state_q <= GEN_RUN;
                    end
                end

                //----------------------------------------------------------
                GEN_RUN: begin
                    // Shift LFSR and accumulate 32 bits per round
                    lfsr_en <= 1'b1;
                    gen_buf_q[{gen_count_q, 5'd0} +: 32] <= lfsr_next;

                    if (gen_count_q == LFSR_ROUNDS - 1) begin
                        gen_state_q <= GEN_COMPLETE;
                    end else begin
                        gen_count_q <= gen_count_q + 3'd1;
                    end
                end

                //----------------------------------------------------------
                GEN_COMPLETE: begin
                    // Output completed nonce
                    gen_nonce_o <= gen_buf_q;
                    gen_ack_o   <= 1'b1;

                    // Check entropy (simple heuristic: nonce should not be all zeros)
                    entropy_warn_o <= (gen_buf_q == '0);

                    gen_state_q <= GEN_IDLE;
                end

                default: gen_state_q <= GEN_IDLE;
            endcase
        end
    end

    //==========================================================================
    // Validation logic (combinational, runs when val_req_i asserted)
    //==========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            val_ack_o   <= 1'b0;
            val_match_o <= 1'b0;
        end else begin
            val_ack_o <= 1'b0;

            if (val_req_i) begin
                val_ack_o <= 1'b1;
                if (val_tdi_index_i < NUM_TDI && nonce_valid_q[val_tdi_index_i]) begin
                    val_match_o <= (val_nonce_i == nonce_store_q[val_tdi_index_i]);
                end else begin
                    val_match_o <= 1'b0; // No valid nonce stored
                end
            end
        end
    end

endmodule : tdisp_nonce_gen
