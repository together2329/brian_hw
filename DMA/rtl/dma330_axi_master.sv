// =============================================================================
// dma330_axi_master.sv — DMA-330 AXI4 Master Interface
//
// Arbitrates internal DMA requesters (instruction fetch, channel LD/ST,
// manager) onto a shared AXI4 bus.  Supports:
//   - Up to NUM_REQUESTERS internal requesters
//   - Separate read and write channels (full-duplex)
//   - Fixed-priority or round-robin arbitration (to be implemented)
//   - Error capture and reporting
// =============================================================================

module dma330_axi_master #(
    parameter int unsigned DATA_WIDTH      = 32,
    parameter int unsigned ADDR_WIDTH      = 32,
    parameter int unsigned NUM_REQUESTERS  = 6   // 1 instr_fetch + 4 channels + 1 manager
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // AXI4 Master — Write Address Channel (AW)
    // =========================================================================
    output logic [ADDR_WIDTH-1:0]         m_awaddr,
    output logic [7:0]                    m_awlen,
    output logic [2:0]                    m_awsize,
    output logic [1:0]                    m_awburst,
    output logic                          m_awvalid,
    input  logic                          m_awready,

    // =========================================================================
    // AXI4 Master — Write Data Channel (W)
    // =========================================================================
    output logic [DATA_WIDTH-1:0]         m_wdata,
    output logic [(DATA_WIDTH/8)-1:0]     m_wstrb,
    output logic                          m_wlast,
    output logic                          m_wvalid,
    input  logic                          m_wready,

    // =========================================================================
    // AXI4 Master — Write Response Channel (B)
    // =========================================================================
    input  logic [1:0]                    m_bresp,
    input  logic                          m_bvalid,
    output logic                          m_bready,

    // =========================================================================
    // AXI4 Master — Read Address Channel (AR)
    // =========================================================================
    output logic [ADDR_WIDTH-1:0]         m_araddr,
    output logic [7:0]                    m_arlen,
    output logic [2:0]                    m_arsize,
    output logic [1:0]                    m_arburst,
    output logic                          m_arvalid,
    input  logic                          m_arready,

    // =========================================================================
    // AXI4 Master — Read Data Channel (R)
    // =========================================================================
    input  logic [DATA_WIDTH-1:0]         m_rdata,
    input  logic [1:0]                    m_rresp,
    input  logic                          m_rlast,
    input  logic                          m_rvalid,
    output logic                          m_rready,

    // =========================================================================
    // Internal Requester Interface (array of requesters)
    // =========================================================================
    input  dma330_pkg::axi_req_t          req_i    [NUM_REQUESTERS-1:0],
    output dma330_pkg::axi_resp_t         resp_o   [NUM_REQUESTERS-1:0],
    output logic [NUM_REQUESTERS-1:0]     grant_o,
    output logic [NUM_REQUESTERS-1:0]     w_grant_o,   // 1 per requester during write txn

    // =========================================================================
    // Error output
    // =========================================================================
    output logic                          error_o
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Icarus Compatibility: Extract struct fields into separate arrays
    // Icarus can't handle struct field access on dynamically-indexed unpacked arrays
    // =========================================================================
    logic [ADDR_WIDTH-1:0]   req_addr       [NUM_REQUESTERS-1:0];
    logic [DATA_WIDTH-1:0]   req_data       [NUM_REQUESTERS-1:0];
    logic [7:0]              req_burst_len  [NUM_REQUESTERS-1:0];
    logic [2:0]              req_burst_size [NUM_REQUESTERS-1:0];
    logic [1:0]              req_type       [NUM_REQUESTERS-1:0];
    logic                    req_valid_arr  [NUM_REQUESTERS-1:0];

    genvar g;
    generate
        for (g = 0; g < NUM_REQUESTERS; g++) begin : gen_field_extract
            // axi_req_t layout (83 bits, MSB-first):
            //   [82:81] req_type  [80:49] addr  [48:17] data
            //   [16:9]  burst_len [8:6] burst_size  [5:2] id
            //   [1] valid  [0] security
            assign req_addr[g]       = req_i[g][80:49];
            assign req_data[g]       = req_i[g][48:17];
            assign req_burst_len[g]  = req_i[g][16:9];
            assign req_burst_size[g] = req_i[g][8:6];
            assign req_type[g]       = req_i[g][82:81];
            assign req_valid_arr[g]  = req_i[g][1];
        end
    endgenerate

    // =========================================================================
    // Read-Channel FSM States
    // =========================================================================
    typedef enum logic [1:0] {
        R_IDLE = 2'h0,
        R_ADDR = 2'h1,
        R_DATA = 2'h2
    } r_fsm_state_t;

    // =========================================================================
    // Read-Channel Internal Registers
    // =========================================================================
    r_fsm_state_t             r_state;
    logic [CH_ID_WIDTH:0]     r_grant_id;       // winning requester (extended to hold max index)
    logic [7:0]               r_beat_cnt;       // current beat within burst
    logic [7:0]               r_beat_total;     // total beats in this burst (ARLEN+1)
    logic                     r_error_flag;     // sticky error per burst
    logic [ADDR_WIDTH-1:0]    r_araddr_reg;
    logic [7:0]               r_arlen_reg;
    logic [2:0]               r_arsize_reg;

    // =========================================================================
    // Round-Robin Arbiter for Read Requests
    //
    // Maintains a rotating priority pointer.  After each transaction completes
    // the pointer advances past the last-served requester so that all
    // requesters get fair access and no starvation occurs.
    // =========================================================================
    logic [$clog2(NUM_REQUESTERS)-1:0] r_rr_ptr;     // round-robin pointer (next to serve)
    logic [$clog2(NUM_REQUESTERS)-1:0] r_winner;
    logic                               r_any_req;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            r_rr_ptr <= '0;
        else if (r_state == R_IDLE)
            // Advance pointer past last served ID on transaction completion
            r_rr_ptr <= r_grant_id[$clog2(NUM_REQUESTERS)-1:0] + 1;
    end

    // Icarus Verilog work-around: always_comb with for-loops over unpacked arrays
    // driven by generate blocks may not trigger correctly.  Unroll the arbiter
    // explicitly for each supported NUM_REQUESTERS value.
    always_comb begin : read_arbiter
        r_any_req = 1'b0;
        r_winner  = r_rr_ptr;
        // Priority scan from RR pointer (lower index = higher priority when tied)
        // Covers up to 6 requesters (cache, mgr, ch0-ch3)
        begin : scan
            logic [2:0] idx;
            for (int unsigned offset = 0; offset < NUM_REQUESTERS; offset++) begin
                idx = (r_rr_ptr + offset) % NUM_REQUESTERS;
                case (idx)
                    3'd0: if (req_valid_arr[0] && (req_type[0] == REQ_INSTR_FETCH || req_type[0] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd0; end
                    3'd1: if (req_valid_arr[1] && (req_type[1] == REQ_INSTR_FETCH || req_type[1] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd1; end
                    3'd2: if (req_valid_arr[2] && (req_type[2] == REQ_INSTR_FETCH || req_type[2] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd2; end
                    3'd3: if (req_valid_arr[3] && (req_type[3] == REQ_INSTR_FETCH || req_type[3] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd3; end
                    3'd4: if (req_valid_arr[4] && (req_type[4] == REQ_INSTR_FETCH || req_type[4] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd4; end
                    3'd5: if (req_valid_arr[5] && (req_type[5] == REQ_INSTR_FETCH || req_type[5] == REQ_DMALD))
                          begin r_any_req = 1'b1; r_winner = 3'd5; end
                    default: ;
                endcase
            end
        end
    end

    // =========================================================================
    // Read-Channel FSM
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : read_fsm
        if (!rst_n) begin
            r_state       <= R_IDLE;
            r_grant_id    <= '0;
            r_beat_cnt    <= 8'h00;
            r_beat_total  <= 8'h00;
            r_error_flag  <= 1'b0;
            r_araddr_reg  <= '0;
            r_arlen_reg   <= 8'h00;
            r_arsize_reg  <= 3'b000;
        end else begin
            case (r_state)
                // -----------------------------------------------------------------
                // R_IDLE: wait for a read request from any requester
                // -----------------------------------------------------------------
                R_IDLE: begin
                    r_error_flag <= 1'b0;
                    r_beat_cnt   <= 8'h00;
                    if (r_any_req) begin
                        // Capture requester info
                        r_araddr_reg <= req_addr[r_winner];
                        r_arlen_reg  <= req_burst_len[r_winner];
                        r_arsize_reg <= req_burst_size[r_winner];
                        r_beat_total <= req_burst_len[r_winner];  // ARLEN = beats-1
                        r_grant_id   <= r_winner;
                        r_state      <= R_ADDR;
                    end
                end

                // -----------------------------------------------------------------
                // R_ADDR: drive AR channel, wait for ARREADY handshake
                // -----------------------------------------------------------------
                R_ADDR: begin
                    if (m_arvalid && m_arready) begin
                        // Address phase accepted
                        r_state <= R_DATA;
                    end
                end

                // -----------------------------------------------------------------
                // R_DATA: receive RDATA beats, count until RLAST
                // -----------------------------------------------------------------
                R_DATA: begin
                    if (m_rvalid && m_rready) begin
                        // Capture error from RRESP
                        if (m_rresp != 2'b00) begin  // 2'b00 = OKAY
                            r_error_flag <= 1'b1;
                        end
                        r_beat_cnt <= r_beat_cnt + 8'h01;

                        if (m_rlast) begin
                            r_state <= R_IDLE;
                        end
                    end
                end

                default: r_state <= R_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Read-Channel AXI Signal Driving
    // =========================================================================

    // AR channel — active only in R_ADDR
    assign m_araddr  = r_araddr_reg;
    assign m_arlen   = r_arlen_reg;
    assign m_arsize  = r_arsize_reg;
    assign m_arburst = 2'b01;  // INCR burst
    assign m_arvalid = (r_state == R_ADDR) ? 1'b1 : 1'b0;

    // R channel — accept data in R_DATA, always ready
    assign m_rready  = (r_state == R_DATA) ? 1'b1 : 1'b0;

    // =========================================================================
    // Read-Channel Grant — asserted during entire read transaction
    // =========================================================================
    logic [NUM_REQUESTERS-1:0] r_grant_mask;
    always_comb begin
        r_grant_mask = '0;
        if (r_state != R_IDLE) begin
            r_grant_mask[r_grant_id[$clog2(NUM_REQUESTERS)-1:0]] = 1'b1;
        end
    end

    // =========================================================================
    // Write-Channel FSM States
    // =========================================================================
    typedef enum logic [1:0] {
        W_IDLE = 2'h0,
        W_ADDR = 2'h1,
        W_DATA = 2'h2,
        W_RESP = 2'h3
    } w_fsm_state_t;

    // =========================================================================
    // Write-Channel Internal Registers
    // =========================================================================
    w_fsm_state_t             w_state;
    logic [$clog2(NUM_REQUESTERS)-1:0] w_grant_id;
    logic [7:0]               w_beat_cnt;
    logic [7:0]               w_beat_total;
    logic                     w_error_flag;
    logic [ADDR_WIDTH-1:0]    w_awaddr_reg;
    logic [7:0]               w_awlen_reg;
    logic [2:0]               w_awsize_reg;

    // =========================================================================
    // Round-Robin Arbiter for Write Requests
    // =========================================================================
    logic [$clog2(NUM_REQUESTERS)-1:0] w_rr_ptr;
    logic [$clog2(NUM_REQUESTERS)-1:0] w_winner;
    logic                               w_any_req;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            w_rr_ptr <= '0;
        else if (w_state == W_IDLE)
            w_rr_ptr <= w_grant_id + 1;
    end

    always_comb begin : write_arbiter
        w_any_req = 1'b0;
        w_winner  = w_rr_ptr;
        // Explicit case-based arbitration (avoids Icarus Verilog for-loop issues)
        case (w_rr_ptr)
            3'd0: begin
                if (req_valid_arr[0] && req_type[0] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd0; end
                else if (req_valid_arr[1] && req_type[1] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd1; end
                else if (req_valid_arr[2] && req_type[2] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd2; end
                else if (req_valid_arr[3] && req_type[3] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd3; end
                else if (req_valid_arr[4] && req_type[4] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd4; end
                else if (req_valid_arr[5] && req_type[5] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd5; end
            end
            3'd1: begin
                if (req_valid_arr[1] && req_type[1] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd1; end
                else if (req_valid_arr[2] && req_type[2] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd2; end
                else if (req_valid_arr[3] && req_type[3] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd3; end
                else if (req_valid_arr[4] && req_type[4] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd4; end
                else if (req_valid_arr[5] && req_type[5] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd5; end
                else if (req_valid_arr[0] && req_type[0] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd0; end
            end
            3'd2: begin
                if (req_valid_arr[2] && req_type[2] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd2; end
                else if (req_valid_arr[3] && req_type[3] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd3; end
                else if (req_valid_arr[4] && req_type[4] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd4; end
                else if (req_valid_arr[5] && req_type[5] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd5; end
                else if (req_valid_arr[0] && req_type[0] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd0; end
                else if (req_valid_arr[1] && req_type[1] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd1; end
            end
            default: begin
                if (req_valid_arr[0] && req_type[0] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd0; end
                else if (req_valid_arr[1] && req_type[1] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd1; end
                else if (req_valid_arr[2] && req_type[2] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd2; end
                else if (req_valid_arr[3] && req_type[3] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd3; end
                else if (req_valid_arr[4] && req_type[4] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd4; end
                else if (req_valid_arr[5] && req_type[5] == REQ_DMAST) begin w_any_req = 1'b1; w_winner = 3'd5; end
            end
        endcase
    end

    // =========================================================================
    // Write-Channel FSM
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : write_fsm
        if (!rst_n) begin
            w_state       <= W_IDLE;
            w_grant_id    <= '0;
            w_beat_cnt    <= 8'h00;
            w_beat_total  <= 8'h00;
            w_error_flag  <= 1'b0;
            w_awaddr_reg  <= '0;
            w_awlen_reg   <= 8'h00;
            w_awsize_reg  <= 3'b000;
        end else begin
            case (w_state)
                // -----------------------------------------------------------------
                // W_IDLE: wait for a write request from any requester
                // -----------------------------------------------------------------
                W_IDLE: begin
                    w_error_flag <= 1'b0;
                    w_beat_cnt   <= 8'h00;
                    if (w_any_req) begin
                        w_awaddr_reg <= req_addr[w_winner];
                        w_awlen_reg  <= req_burst_len[w_winner];
                        w_awsize_reg <= req_burst_size[w_winner];
                        w_beat_total <= req_burst_len[w_winner];
                        w_grant_id   <= w_winner;
                        w_state      <= W_ADDR;
                    end
                end

                // -----------------------------------------------------------------
                // W_ADDR: drive AW channel, wait for AWREADY handshake
                // -----------------------------------------------------------------
                W_ADDR: begin
                    if (m_awvalid && m_awready) begin
                        w_state <= W_DATA;
                    end
                end

                // -----------------------------------------------------------------
                // W_DATA: drive WDATA beats, wait for WREADY, count to WLAST
                // -----------------------------------------------------------------
                W_DATA: begin
                    if (m_wvalid && m_wready) begin
                        w_beat_cnt <= w_beat_cnt + 8'h01;
                        if (w_beat_cnt == w_beat_total) begin
                            // This is the last beat — transition to response phase
                            w_state <= W_RESP;
                        end
                    end
                end

                // -----------------------------------------------------------------
                // W_RESP: wait for BVALID+BREADY handshake
                // -----------------------------------------------------------------
                W_RESP: begin
                    if (m_bvalid && m_bready) begin
                        if (m_bresp != 2'b00) begin
                            w_error_flag <= 1'b1;
                        end
                        w_state <= W_IDLE;
                    end
                end

                default: w_state <= W_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Write-Channel AXI Signal Driving
    // =========================================================================

    // AW channel — active only in W_ADDR
    assign m_awaddr  = w_awaddr_reg;
    assign m_awlen   = w_awlen_reg;
    assign m_awsize  = w_awsize_reg;
    assign m_awburst = 2'b01;  // INCR burst
    assign m_awvalid = (w_state == W_ADDR) ? 1'b1 : 1'b0;

    // W channel — drive data in W_DATA
    // Data sourced from the winning requester's data field
    assign m_wdata   = (w_state == W_DATA) ? req_data[w_grant_id] : {DATA_WIDTH{1'b0}};
    assign m_wstrb   = (w_state == W_DATA) ? {(DATA_WIDTH/8){1'b1}} : {(DATA_WIDTH/8){1'b0}};
    assign m_wlast   = (w_state == W_DATA && w_beat_cnt == w_beat_total) ? 1'b1 : 1'b0;
    assign m_wvalid  = (w_state == W_DATA) ? 1'b1 : 1'b0;

    // B channel — accept response in W_RESP
    assign m_bready  = (w_state == W_RESP) ? 1'b1 : 1'b0;

    // =========================================================================
    // Write-Channel Grant
    // =========================================================================
    logic [NUM_REQUESTERS-1:0] w_grant_mask;
    always_comb begin
        w_grant_mask = '0;
        if (w_state != W_IDLE) begin
            w_grant_mask[w_grant_id] = 1'b1;
        end
    end

    // =========================================================================
    // Combined Grant & Response
    // =========================================================================
    assign grant_o   = r_grant_mask | w_grant_mask;
    assign w_grant_o = w_grant_mask;

    // Generate responses per requester
    // Icarus work-around: unrolled response generation (for-loops over unpacked
    // arrays in always_comb may not propagate writes correctly in Icarus).
    //   axi_resp_t = { data[31:0], last, resp[1:0], valid, error }
    always_comb begin : resp_gen
        // Defaults: all zero
        resp_o[0] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        resp_o[1] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        resp_o[2] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        resp_o[3] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        resp_o[4] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        resp_o[5] = {32'b0, 1'b0, 2'b0, 1'b0, 1'b0};
        // Read response — route to winning requester
        begin : read_resp
            logic [2:0] gid;
            gid = r_grant_id[$clog2(NUM_REQUESTERS)-1:0];
            if (r_state == R_DATA) begin
                case (gid)
                    3'd0: resp_o[0] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    3'd1: resp_o[1] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    3'd2: resp_o[2] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    3'd3: resp_o[3] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    3'd4: resp_o[4] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    3'd5: resp_o[5] = {m_rdata, (m_rlast && m_rvalid && m_rready), m_rresp, (m_rvalid && m_rready), r_error_flag};
                    default: ;  // NUM_REQUESTERS=6, gid[2:0] can't exceed 5
                endcase
            end
        end
        // Write response — route to winning requester
        begin : write_resp
            logic [2:0] gid;
            gid = w_grant_id[$clog2(NUM_REQUESTERS)-1:0];
            if (w_state == W_RESP && m_bvalid && m_bready) begin
                case (gid)
                    3'd0: resp_o[0] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    3'd1: resp_o[1] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    3'd2: resp_o[2] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    3'd3: resp_o[3] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    3'd4: resp_o[4] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    3'd5: resp_o[5] = {32'b0, 1'b1, m_bresp, 1'b1, (m_bresp != 2'b00)};
                    default: ;  // NUM_REQUESTERS=6, gid[2:0] can't exceed 5
                endcase
            end
        end
    end

    // =========================================================================
    // Per-Requester Error Tagging
    //
    // Tracks which requester experienced an AXI error.  The error flag is
    // sticky per requester until software clears it via the register file.
    // =========================================================================
    logic [NUM_REQUESTERS-1:0] error_per_requester;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            error_per_requester <= '0;
        end else begin
            // Read-channel error — tag on RRESP error during R_DATA
            if (r_state == R_DATA && m_rvalid && m_rready && m_rresp != 2'b00) begin
                error_per_requester[r_grant_id[$clog2(NUM_REQUESTERS)-1:0]] <= 1'b1;
            end
            // Write-channel error — tag on BRESP error during W_RESP
            if (w_state == W_RESP && m_bvalid && m_bready && m_bresp != 2'b00) begin
                error_per_requester[w_grant_id] <= 1'b1;
            end
        end
    end

    // =========================================================================
    // Error Output — OR of all per-requester errors
    // =========================================================================
    assign error_o = |error_per_requester;

endmodule : dma330_axi_master
