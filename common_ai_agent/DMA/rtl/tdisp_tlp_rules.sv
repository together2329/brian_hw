//============================================================================
// TDISP TLP Access Control and XT/T Bit Enforcement
// Enforces per-TDI TLP access rules based on TDI state and XT/T bit policy
// Blocks disallowed TLPs and reports violations to FSM
// Per PCIe Base Spec Rev 7.0, Chapter 11 (TLP Processing Rules)
//============================================================================

module tdisp_tlp_rules #(
    parameter int unsigned NUM_TDI       = 4,
    parameter int unsigned ADDR_WIDTH    = 64,
    parameter int unsigned BUS_WIDTH     = 8,    // Max MMIO ranges per TDI
    parameter int unsigned PAGE_SIZE     = 4096
) (
    input  logic                            clk,
    input  logic                            rst_n,

    //--- Per-TDI context inputs (from tdisp_tdi_mgr) ---
    input  tdisp_types::tdisp_state_e       tdi_state_i      [NUM_TDI],
    input  logic                            tdi_xt_enabled_i  [NUM_TDI], // Per-TDI XT mode
    input  logic                            tdi_msix_locked_i [NUM_TDI],
    input  logic                            tdi_fw_locked_i   [NUM_TDI],
    input  logic                            tdi_p2p_enabled_i [NUM_TDI],
    input  logic                            tdi_req_redirect_i[NUM_TDI],

    //--- TLP input (from PCIe core upstream) ---
    input  logic                            tlp_valid_i,          // TLP header valid
    input  logic [31:0]                     tlp_header_dw0_i,     // TLP DW0 (fmt+type)
    input  logic [31:0]                     tlp_header_dw1_i,     // TLP DW1 (req_id, tag, addr)
    input  logic [31:0]                     tlp_header_dw2_i,     // TLP DW2 (address)
    input  logic [31:0]                     tlp_header_dw3_i,     // TLP DW3 (address high, 4DW)
    input  logic                            tlp_is_4dw_i,         // 4DW header flag
    input  logic [11:0]                     tlp_byte_count_i,     // Byte count
    input  logic [15:0]                     tlp_requester_id_i,   // Requester ID
    input  logic [7:0]                      tlp_tag_i,            // Tag
    input  logic [2:0]                      tlp_tc_i,             // Traffic class
    input  logic                            tlp_td_i,             // TLP digest flag
    input  logic                            tlp_ep_i,             // Error poisoned
    input  logic [1:0]                      tlp_at_i,             // Address type

    //--- XT/T bit inputs from IDE ---
    input  logic                            tlp_tee_originator_i, // T bit: 1=TEE originator
    input  logic                            tlp_xt_enabled_i,     // XT bit: 1=TEE-enforced traffic

    //--- MMIO range attributes (from SET_MMIO_ATTRIBUTE) ---
    input  logic [ADDR_WIDTH-1:0]           mmio_start_addr_i [NUM_TDI][BUS_WIDTH],
    input  logic [31:0]                     mmio_num_pages_i  [NUM_TDI][BUS_WIDTH],
    input  logic                            mmio_is_non_tee_i [NUM_TDI][BUS_WIDTH],
    input  logic                            mmio_range_valid_i[NUM_TDI][BUS_WIDTH],

    //--- Access decision output ---
    output logic                            tlp_allow_o,          // 1=TLP allowed, 0=blocked
    output logic                            tlp_blocked_o,        // 1=TLP access violation
    output logic [$clog2(NUM_TDI)-1:0]      tlp_tdi_index_o,     // Matching TDI index
    output logic                            tlp_violation_irq_o,  // Interrupt on violation

    //--- Violation report to FSM ---
    output logic                            violation_valid_o,
    output logic [$clog2(NUM_TDI)-1:0]      violation_tdi_o,
    output tdisp_types::tdisp_error_code_e  violation_code_o,
    input  logic                            violation_ack_i       // FSM acknowledged violation
);

    import tdisp_types::*;

    //==========================================================================
    // Local parameters for TLP type classification
    //==========================================================================
    // TLP format field (bits 31:29 of DW0)
    localparam logic [2:0] FMT_NO_DATA   = 3'b000;
    localparam logic [2:0] FMT_WITH_DATA = 3'b010;
    localparam logic [2:0] FMT_4DW_NO_DATA   = 3'b001;
    localparam logic [2:0] FMT_4DW_WITH_DATA = 3'b011;
    localparam logic [2:0] FMT_TLP_PREFIX    = 3'b100;

    // TLP type field (bits 28:24 of DW0)
    localparam logic [4:0] TLP_MRD   = 5'b00000; // Memory Read
    localparam logic [4:0] TLP_MRD64 = 5'b01000; // Memory Read 64-bit
    localparam logic [4:0] TLP_MWR   = 5'b10000; // Memory Write
    localparam logic [4:0] TLP_MWR64 = 5'b11000; // Memory Write 64-bit
    localparam logic [4:0] TLP_IORD  = 5'b00010; // I/O Read
    localparam logic [4:0] TLP_IOWR  = 5'b10010; // I/O Write
    localparam logic [4:0] TLP_CFGRD0 = 5'b00100; // Config Read Type 0
    localparam logic [4:0] TLP_CFGWR0 = 5'b10100; // Config Write Type 0
    localparam logic [4:0] TLP_CFGRD1 = 5'b01100; // Config Read Type 1
    localparam logic [4:0] TLP_CFGWR1 = 5'b11100; // Config Write Type 1
    localparam logic [4:0] TLP_MSG    = 5'b10001; // Message
    localparam logic [4:0] TLP_CPL    = 5'b01010; // Completion
    localparam logic [4:0] TLP_CPLD   = 5'b11010; // Completion with Data

    //==========================================================================
    // TLP classification (combinational)
    //==========================================================================
    logic [2:0]  tlp_fmt;
    logic [4:0]  tlp_type;
    logic        is_mem_read;
    logic        is_mem_write;
    logic        is_io_req;
    logic        is_cfg_req;
    logic        is_completion;
    logic        is_msg;
    logic        is_write;
    logic        is_read;
    logic [ADDR_WIDTH-1:0] tlp_addr;

    always_comb begin
        tlp_fmt  = tlp_header_dw0_i[31:29];
        tlp_type = tlp_header_dw0_i[28:24];

        // Classify TLP type
        is_mem_read  = (tlp_type == TLP_MRD)  || (tlp_type == TLP_MRD64);
        is_mem_write = (tlp_type == TLP_MWR)  || (tlp_type == TLP_MWR64);
        is_io_req    = (tlp_type == TLP_IORD) || (tlp_type == TLP_IOWR);
        is_cfg_req   = (tlp_type == TLP_CFGRD0) || (tlp_type == TLP_CFGWR0) ||
                       (tlp_type == TLP_CFGRD1) || (tlp_type == TLP_CFGWR1);
        is_completion = (tlp_type == TLP_CPL) || (tlp_type == TLP_CPLD);
        is_msg       = (tlp_type == TLP_MSG);

        is_write = is_mem_write || (tlp_type == TLP_IOWR) ||
                   (tlp_type == TLP_CFGWR0) || (tlp_type == TLP_CFGWR1);
        is_read  = is_mem_read  || (tlp_type == TLP_IORD) ||
                   (tlp_type == TLP_CFGRD0) || (tlp_type == TLP_CFGRD1);

        // Extract address
        if (tlp_is_4dw_i) begin
            // 64-bit address: DW2 = upper 32 bits, DW3 = lower 30 bits [31:2]
            tlp_addr = {tlp_header_dw2_i, tlp_header_dw3_i[31:2], 2'b00};
        end else begin
            // 32-bit address from DW2[31:2]
            tlp_addr = {32'b0, tlp_header_dw2_i[31:2], 2'b00};
        end
    end

    //==========================================================================
    // Address range matching (per TDI, per MMIO range)
    //==========================================================================
    logic [NUM_TDI-1:0]                tdi_match;       // TDI matched by address
    logic [NUM_TDI-1:0]                tdi_tee_mem_match; // Matched TEE memory range
    logic [NUM_TDI-1:0]                tdi_non_tee_mem_match; // Matched non-TEE memory range

    always_comb begin
        tdi_match           = '0;
        tdi_tee_mem_match   = '0;
        tdi_non_tee_mem_match = '0;

        for (int t = 0; t < NUM_TDI; t++) begin
            for (int r = 0; r < BUS_WIDTH; r++) begin
                if (mmio_range_valid_i[t][r]) begin
                    // Calculate range bounds
                    // Start address + num_pages * PAGE_SIZE
                    automatic logic [ADDR_WIDTH-1:0] range_start = mmio_start_addr_i[t][r];
                    automatic logic [ADDR_WIDTH-1:0] range_end;
                    automatic logic [ADDR_WIDTH-1:0] addr_mask;

                    range_end = range_start + (mmio_num_pages_i[t][r] * PAGE_SIZE) - 1;

                    if (tlp_addr >= range_start && tlp_addr <= range_end) begin
                        tdi_match[t] = 1'b1;
                        if (mmio_is_non_tee_i[t][r]) begin
                            tdi_non_tee_mem_match[t] = 1'b1;
                        end else begin
                            tdi_tee_mem_match[t] = 1'b1;
                        end
                    end
                end
            end
        end
    end

    //==========================================================================
    // Access policy evaluation
    //==========================================================================
    logic                                policy_allow;
    logic [$clog2(NUM_TDI)-1:0]          matched_tdi;
    logic                                has_tdi_match;
    tdisp_error_code_e                   violation_code;

    // Priority encoder for matched TDI
    always_comb begin
        matched_tdi   = '0;
        has_tdi_match = 1'b0;
        for (int t = NUM_TDI - 1; t >= 0; t--) begin
            if (tdi_match[t]) begin
                matched_tdi   = t[$clog2(NUM_TDI)-1:0];
                has_tdi_match = 1'b1;
            end
        end
    end

    always_comb begin
        policy_allow    = 1'b1;  // Default: allow if no rule blocks
        violation_code  = ERR_RESERVED;

        //--- Rule 1: Completions are always allowed ---
        if (is_completion) begin
            policy_allow = 1'b1;
        end
        //--- Rule 2: Messages are allowed ---
        else if (is_msg) begin
            policy_allow = 1'b1;
        end
        //--- Rule 3: Config requests - check firmware lock ---
        else if (is_cfg_req && has_tdi_match) begin
            if (tdi_state_i[matched_tdi] == TDI_CONFIG_LOCKED ||
                tdi_state_i[matched_tdi] == TDI_RUN) begin
                // Config writes blocked if firmware update locked
                if (is_write && tdi_fw_locked_i[matched_tdi]) begin
                    policy_allow   = 1'b0;
                    violation_code = ERR_INVALID_DEVICE_CONFIGURATION;
                end
            end
        end
        //--- Rule 4: I/O requests blocked in RUN state ---
        else if (is_io_req && has_tdi_match) begin
            if (tdi_state_i[matched_tdi] == TDI_RUN) begin
                policy_allow   = 1'b0;
                violation_code = ERR_INVALID_INTERFACE_STATE;
            end
        end
        //--- Rule 5: Memory access rules (XT/T bit enforcement) ---
        else if ((is_mem_read || is_mem_write) && has_tdi_match) begin
            automatic tdisp_state_e tdi_st;
            tdi_st = tdi_state_i[matched_tdi];

            case (tdi_st)
                //------------------------------------------
                TDI_CONFIG_UNLOCKED: begin
                    // Unlocked: all memory access allowed
                    policy_allow = 1'b1;
                end

                //------------------------------------------
                TDI_CONFIG_LOCKED: begin
                    // Locked: memory access allowed, but track MMIO ranges
                    policy_allow = 1'b1;
                end

                //------------------------------------------
                TDI_RUN: begin
                    // RUN state: enforce XT/T bit rules
                    if (tdi_xt_enabled_i[matched_tdi]) begin
                        // XT mode enabled: strict access control
                        if (!tlp_tee_originator_i) begin
                            // Non-TEE originator (T=0)
                            // Can only access non-TEE memory ranges
                            if (tdi_tee_mem_match[matched_tdi]) begin
                                // Accessing TEE memory with T=0: BLOCKED
                                policy_allow   = 1'b0;
                                violation_code = ERR_INVALID_INTERFACE_STATE;
                            end else if (tdi_non_tee_mem_match[matched_tdi]) begin
                                // Accessing non-TEE memory with T=0: ALLOWED
                                policy_allow = 1'b1;
                            end else begin
                                // Address not in any MMIO range: allowed
                                // (addresses outside TDI ranges are non-TEE by default)
                                policy_allow = 1'b1;
                            end
                        end else begin
                            // TEE originator (T=1)
                            if (tlp_xt_enabled_i) begin
                                // XT=1, T=1: TEE can access TEE memory only
                                if (tdi_non_tee_mem_match[matched_tdi] &&
                                    !tdi_tee_mem_match[matched_tdi]) begin
                                    // XT=1 TEE trying to access only non-TEE range
                                    policy_allow = 1'b1; // Still allowed for TEE
                                end else begin
                                    policy_allow = 1'b1; // TEE can access all
                                end
                            end else begin
                                // XT=0, T=1: TEE with no XT restriction
                                policy_allow = 1'b1;
                            end
                        end
                    end else begin
                        // XT mode disabled: standard access control
                        // Non-TEE memory accessible by all; TEE memory only by TEE
                        if (tdi_tee_mem_match[matched_tdi] &&
                            !tlp_tee_originator_i) begin
                            // Non-TEE accessing TEE memory: BLOCKED
                            policy_allow   = 1'b0;
                            violation_code = ERR_INVALID_INTERFACE_STATE;
                        end else begin
                            policy_allow = 1'b1;
                        end
                    end

                    // MSI-X lock enforcement
                    if (tdi_msix_locked_i[matched_tdi] && is_write) begin
                        // MSI-X table/PBA writes blocked when locked
                        // (Address match against MSI-X range would be done externally;
                        //  this flag gates the general policy)
                        // For now, allow; MSI-X check handled by dedicated comparator
                    end

                    // P2P access check
                    if (!tdi_p2p_enabled_i[matched_tdi] && is_write) begin
                        // P2P writes blocked if P2P not enabled
                        // Simplified: actual P2P detection needs bus number comparison
                    end
                end

                //------------------------------------------
                TDI_ERROR: begin
                    // Error state: all memory access blocked
                    policy_allow   = 1'b0;
                    violation_code = ERR_INVALID_INTERFACE_STATE;
                end

                default: policy_allow = 1'b1;
            endcase
        end
        //--- Rule 6: No TDI match - default allow for non-memory ---
        else if (!has_tdi_match && !is_mem_read && !is_mem_write) begin
            policy_allow = 1'b1;
        end
        //--- Rule 7: Memory access with no TDI match ---
        else if (!has_tdi_match && (is_mem_read || is_mem_write)) begin
            // Address doesn't match any TDI range - allow
            // (could be system memory not managed by TDISP)
            policy_allow = 1'b1;
        end
    end

    //==========================================================================
    // Output registration and violation capture
    //==========================================================================
    logic violation_pending_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tlp_allow_o        <= 1'b1;
            tlp_blocked_o      <= 1'b0;
            tlp_tdi_index_o    <= '0;
            tlp_violation_irq_o<= 1'b0;
            violation_pending_q<= 1'b0;
            violation_valid_o  <= 1'b0;
            violation_tdi_o    <= '0;
            violation_code_o   <= ERR_RESERVED;
        end else begin
            // Default: clear pulsed signals
            tlp_violation_irq_o <= 1'b0;

            if (violation_pending_q && violation_ack_i) begin
                violation_valid_o   <= 1'b0;
                violation_pending_q <= 1'b0;
            end

            if (tlp_valid_i) begin
                tlp_allow_o     <= policy_allow;
                tlp_blocked_o   <= ~policy_allow;
                tlp_tdi_index_o <= matched_tdi;

                if (!policy_allow) begin
                    // Capture violation for FSM
                    violation_valid_o   <= 1'b1;
                    violation_pending_q <= 1'b1;
                    violation_tdi_o     <= matched_tdi;
                    violation_code_o    <= violation_code;
                    tlp_violation_irq_o <= 1'b1;
                end
            end else if (!violation_pending_q) begin
                tlp_blocked_o <= 1'b0;
            end
        end
    end

endmodule : tdisp_tlp_rules
