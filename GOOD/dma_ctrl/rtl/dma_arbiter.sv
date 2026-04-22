`default_nettype none
module dma_arbiter #(
    parameter int NUM_CHANNELS = 8,
    parameter int ID_WIDTH     = 4
)(
    input  logic                          clk,
    input  logic                          rst_n,

    // Channel requests
    input  logic [NUM_CHANNELS-1:0]       ch_req,
    input  logic [NUM_CHANNELS-1:0][1:0]  ch_priority,

    // Grant output
    output logic [ID_WIDTH-1:0]           grant_id,
    output logic                          grant_valid
);

    // ========================================================================
    // Round-robin pointer
    // ========================================================================
    localparam int CH_W = (NUM_CHANNELS > 1) ? $clog2(NUM_CHANNELS) : 1;
    logic [CH_W-1:0] rr_ptr_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            rr_ptr_q <= '0;
        // Keep pointer stable — only update on grant
    end

    // ========================================================================
    // Priority + round-robin arbitration
    // ========================================================================
    logic [CH_W-1:0] winner_idx;
    logic [1:0]      winner_priority;
    logic            has_request;

    always_comb begin
        winner_idx       = '0;
        winner_priority  = 2'b11; // Lowest priority
        has_request      = 1'b0;

        // Find highest priority among requesting channels
        for (int i = 0; i < NUM_CHANNELS; i++) begin
            if (ch_req[i]) begin
                if (!has_request || (ch_priority[i] < winner_priority)) begin
                    winner_idx      = CH_W'(i);
                    winner_priority = ch_priority[i];
                    has_request     = 1'b1;
                end
            end
        end
    end

    // Round-robin among equal priority: use a simple rotate approach
    // Scan from rr_ptr_q+1 wrapping around, pick first match with winner_priority
    logic [CH_W-1:0] rr_winner;
    logic            rr_found;

    always_comb begin
        rr_winner = winner_idx; // Default to highest priority winner
        rr_found  = 1'b0;
        if (has_request) begin
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                logic [CH_W-1:0] scan_idx;
                scan_idx = CH_W'((rr_ptr_q + CH_W'(i) + 1) % NUM_CHANNELS);
                if (!rr_found && ch_req[scan_idx] && ch_priority[scan_idx] == winner_priority) begin
                    rr_winner = scan_idx;
                    rr_found  = 1'b1;
                end
            end
        end
    end

    // ========================================================================
    // Grant output
    // ========================================================================
    assign grant_valid = has_request;
    assign grant_id    = ID_WIDTH'(rr_found ? rr_winner : winner_idx);

endmodule
