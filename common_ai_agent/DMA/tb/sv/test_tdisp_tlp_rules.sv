//============================================================================
// Test: TDISP TLP Access Control Enforcement Tests
// Directly instantiates tdisp_tlp_rules and verifies TLP access policy
// decisions across all TDI states and XT/T bit combinations.
//
// Test scenarios:
//   1. DMA (Mem Write) with T bit in RUN state - TEE access allowed
//   2. DMA blocked in ERROR state - all memory access denied
//   3. MMIO with T bit enforcement only active in RUN state
//   4. XT bit handling - strict vs. relaxed access control
//   5. MSI/MSI-X interrupt (Completion) always allowed
//   6. IS_NON_TEE_MEM attribute enforcement for non-TEE originator
//   7. IDE stream binding / P2P access control
//   8. Completer-side T bit verification on response completions
//   9. Requester-side T bit generation with XT mode
//  10. Config request blocked by firmware lock in CONFIG_LOCKED/RUN
//  11. I/O requests blocked in RUN state
//  12. ATS-translated redirect enforcement
//  13. Multi-TDI address matching and isolation
//  14. Violation capture and acknowledgement handshake
//  15. Reset clears all violations and blocked state
//  16. No TDI match - default allow for memory
//  17. Message TLP always allowed
//  18. Non-TEE originator blocked from TEE memory in RUN without XT
//  19. P2P blocked when p2p_enabled is false
//  20. Address range matching with 3DW and 4DW headers
//
// Reference: PCIe Base Spec Rev 7.0, Chapter 11 (TLP Processing Rules)
//============================================================================

`timescale 1ns / 1ps

module test_tdisp_tlp_rules;

    import tdisp_types::*;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter int unsigned NUM_TDI       = 4;
    parameter int unsigned ADDR_WIDTH    = 64;
    parameter int unsigned BUS_WIDTH     = 8;
    parameter int unsigned PAGE_SIZE     = 4096;
    parameter int unsigned CLK_PERIOD    = 10;

    //==========================================================================
    // Clock / Reset
    //==========================================================================
    logic clk;
    logic rst_n;

    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //==========================================================================
    // DUT Signals
    //==========================================================================
    // Per-TDI context inputs
    tdisp_state_e   tdi_state      [NUM_TDI];
    logic           tdi_xt_enabled [NUM_TDI];
    logic           tdi_fw_locked  [NUM_TDI];
    logic           tdi_p2p_enabled[NUM_TDI];
    logic           tdi_req_redirect[NUM_TDI];

    // TLP input
    logic           tlp_valid;
    logic [31:0]    tlp_header_dw0;
    logic [31:0]    tlp_header_dw2;
    logic [31:0]    tlp_header_dw3;
    logic           tlp_is_4dw;
    logic [15:0]    tlp_requester_id;
    logic [1:0]     tlp_at;

    // XT/T bit inputs
    logic           tlp_tee_originator;
    logic           tlp_xt_enabled;

    // MMIO range inputs
    logic [ADDR_WIDTH-1:0] mmio_start_addr [NUM_TDI][BUS_WIDTH];
    logic [31:0]           mmio_num_pages  [NUM_TDI][BUS_WIDTH];
    logic                  mmio_is_non_tee [NUM_TDI][BUS_WIDTH];
    logic                  mmio_range_valid[NUM_TDI][BUS_WIDTH];

    // Outputs
    logic           tlp_allow;
    logic           tlp_blocked;
    logic [$clog2(NUM_TDI)-1:0] tlp_tdi_index;
    logic           tlp_violation_irq;

    // Violation report
    logic                          violation_valid;
    logic [$clog2(NUM_TDI)-1:0]    violation_tdi;
    tdisp_types::tdisp_error_code_e violation_code;
    logic                          violation_ack;

    //==========================================================================
    // TLP Type Constants (matching tdisp_tlp_rules localparams)
    //==========================================================================
    localparam logic [4:0] TLP_MRD    = 5'b00000;
    localparam logic [4:0] TLP_MRD64  = 5'b01000;
    localparam logic [4:0] TLP_MWR    = 5'b10000;
    localparam logic [4:0] TLP_MWR64  = 5'b11000;
    localparam logic [4:0] TLP_IORD   = 5'b00010;
    localparam logic [4:0] TLP_IOWR   = 5'b10010;
    localparam logic [4:0] TLP_CFGRD0 = 5'b00100;
    localparam logic [4:0] TLP_CFGWR0 = 5'b10100;
    localparam logic [4:0] TLP_MSG    = 5'b10001;
    localparam logic [4:0] TLP_CPL    = 5'b01010;
    localparam logic [4:0] TLP_CPLD   = 5'b11010;

    //==========================================================================
    // Scoreboard / Tracking
    //==========================================================================
    int unsigned total_checks = 0;
    int unsigned total_passed = 0;
    int unsigned total_failed = 0;

    typedef struct {
        string          test_name;
        logic           passed;
        string          detail;
    } tlp_test_result_t;

    tlp_test_result_t results [$];

    //==========================================================================
    // DUT Instantiation
    //==========================================================================
    tdisp_tlp_rules #(
        .NUM_TDI   (NUM_TDI),
        .ADDR_WIDTH(ADDR_WIDTH),
        .BUS_WIDTH (BUS_WIDTH),
        .PAGE_SIZE (PAGE_SIZE)
    ) dut (.*);

    //==========================================================================
    // Helper: Build TLP DW0 from fmt/type
    // fmt[2:0] occupies bits 31:29 of DW0; type[4:0] occupies bits 28:24
    //==========================================================================
    function automatic logic [31:0] make_dw0(
        input logic [2:0] fmt,
        input logic [4:0] tlp_type
    );
        return {fmt, tlp_type, 19'b0};
    endfunction

    //==========================================================================
    // Helper: Build 3DW Memory Write header
    //==========================================================================
    function automatic logic [31:0] make_mwr32_dw0;
        return make_dw0(3'b010, TLP_MWR);
    endfunction

    //==========================================================================
    // Helper: Build 4DW Memory Write header
    //==========================================================================
    function automatic logic [31:0] make_mwr64_dw0;
        return make_dw0(3'b110, TLP_MWR64);
    endfunction

    //==========================================================================
    // Helper: Build 3DW Memory Read header
    //==========================================================================
    function automatic logic [31:0] make_mrd32_dw0;
        return make_dw0(3'b000, TLP_MRD);
    endfunction

    //==========================================================================
    // Helper: Build 4DW Memory Read header
    //==========================================================================
    function automatic logic [31:0] make_mrd64_dw0;
        return make_dw0(3'b100, TLP_MRD64);
    endfunction

    //==========================================================================
    // Helper: Build Completion header
    //==========================================================================
    function automatic logic [31:0] make_cpl_dw0;
        return make_dw0(3'b000, TLP_CPL);
    endfunction

    //==========================================================================
    // Helper: Build Completion with Data header
    //==========================================================================
    function automatic logic [31:0] make_cpld_dw0;
        return make_dw0(3'b010, TLP_CPLD);
    endfunction

    //==========================================================================
    // Helper: Build I/O Write header
    //==========================================================================
    function automatic logic [31:0] make_iowr_dw0;
        return make_dw0(3'b010, TLP_IOWR);
    endfunction

    //==========================================================================
    // Helper: Build I/O Read header
    //==========================================================================
    function automatic logic [31:0] make_iord_dw0;
        return make_dw0(3'b000, TLP_IORD);
    endfunction

    //==========================================================================
    // Helper: Build Config Write Type 0 header
    //==========================================================================
    function automatic logic [31:0] make_cfgwr0_dw0;
        return make_dw0(3'b010, TLP_CFGWR0);
    endfunction

    //==========================================================================
    // Helper: Build Message header
    //==========================================================================
    function automatic logic [31:0] make_msg_dw0;
        return make_dw0(3'b001, TLP_MSG);
    endfunction

    //==========================================================================
    // Helper: Record test result
    //==========================================================================
    function automatic void record_result(
        input string test_name,
        input logic  passed,
        input string detail = ""
    );
        tlp_test_result_t r;
        r.test_name = test_name;
        r.passed    = passed;
        r.detail    = detail;
        results.push_back(r);
        total_checks++;
        if (passed) total_passed++;
        else        total_failed++;
    endfunction

    //==========================================================================
    // Helper: Initialize all signals to reset state
    //==========================================================================
    task automatic init_signals;
        // Per-TDI defaults: CONFIG_UNLOCKED, no XT, no FW lock, no P2P
        for (int t = 0; t < NUM_TDI; t++) begin
            tdi_state[t]       = TDI_CONFIG_UNLOCKED;
            tdi_xt_enabled[t]  = 1'b0;
            tdi_fw_locked[t]   = 1'b0;
            tdi_p2p_enabled[t] = 1'b0;
            tdi_req_redirect[t]= 1'b0;
        end

        // TLP inputs quiesced
        tlp_valid          = 1'b0;
        tlp_header_dw0     = 32'h0;
        tlp_header_dw2     = 32'h0;
        tlp_header_dw3     = 32'h0;
        tlp_is_4dw         = 1'b0;
        tlp_requester_id   = 16'h0000; // Bus 0 (host)
        tlp_at             = 2'b00;     // Untranslated

        // XT/T bits
        tlp_tee_originator = 1'b0;
        tlp_xt_enabled     = 1'b0;

        // MMIO ranges: all invalid
        for (int t = 0; t < NUM_TDI; t++) begin
            for (int r = 0; r < BUS_WIDTH; r++) begin
                mmio_start_addr[t][r]  = '0;
                mmio_num_pages[t][r]   = '0;
                mmio_is_non_tee[t][r]  = 1'b0;
                mmio_range_valid[t][r] = 1'b0;
            end
        end

        violation_ack = 1'b0;
    endtask

    //==========================================================================
    // Helper: Apply reset
    //==========================================================================
    task automatic apply_reset;
        rst_n = 1'b0;
        init_signals;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);
    endtask

    //==========================================================================
    // Helper: Set up one MMIO range for a TDI
    //==========================================================================
    task automatic set_mmio_range(
        input int unsigned       tdi_idx,
        input int unsigned       range_idx,
        input logic [ADDR_WIDTH-1:0] start_addr,
        input logic [31:0]       num_pages,
        input logic              is_non_tee
    );
        mmio_start_addr[tdi_idx][range_idx]  = start_addr;
        mmio_num_pages[tdi_idx][range_idx]   = num_pages;
        mmio_is_non_tee[tdi_idx][range_idx]  = is_non_tee;
        mmio_range_valid[tdi_idx][range_idx] = 1'b1;
    endtask

    //==========================================================================
    // Helper: Send a 3DW TLP and capture the access decision (next cycle)
    //==========================================================================
    task automatic send_tlp_3dw(
        input logic [31:0] dw0,
        input logic [31:0] dw2_addr,
        input logic [15:0] requester_id,
        input logic [1:0]  at,
        input logic        tee_originator,
        input logic        xt_en,
        output logic       o_allow,
        output logic       o_blocked
    );
        tlp_valid          = 1'b1;
        tlp_header_dw0     = dw0;
        tlp_header_dw2     = dw2_addr;
        tlp_header_dw3     = 32'h0;
        tlp_is_4dw         = 1'b0;
        tlp_requester_id   = requester_id;
        tlp_at             = at;
        tlp_tee_originator = tee_originator;
        tlp_xt_enabled     = xt_en;
        @(posedge clk);
        o_allow   = tlp_allow;
        o_blocked = tlp_blocked;
        tlp_valid = 1'b0;
        @(posedge clk);
    endtask

    //==========================================================================
    // Helper: Send a 4DW TLP and capture the access decision (next cycle)
    //==========================================================================
    task automatic send_tlp_4dw(
        input logic [31:0] dw0,
        input logic [31:0] dw2_addr_hi,
        input logic [31:0] dw3_addr_lo,
        input logic [15:0] requester_id,
        input logic [1:0]  at,
        input logic        tee_originator,
        input logic        xt_en,
        output logic       o_allow,
        output logic       o_blocked
    );
        tlp_valid          = 1'b1;
        tlp_header_dw0     = dw0;
        tlp_header_dw2     = dw2_addr_hi;
        tlp_header_dw3     = dw3_addr_lo;
        tlp_is_4dw         = 1'b1;
        tlp_requester_id   = requester_id;
        tlp_at             = at;
        tlp_tee_originator = tee_originator;
        tlp_xt_enabled     = xt_en;
        @(posedge clk);
        o_allow   = tlp_allow;
        o_blocked = tlp_blocked;
        tlp_valid = 1'b0;
        @(posedge clk);
    endtask

    //==========================================================================
    // Helper: Check violation report
    //==========================================================================
    task automatic check_violation(
        input logic                  expect_valid,
        input logic [$clog2(NUM_TDI)-1:0] expect_tdi,
        input tdisp_error_code_e     expect_code,
        input string                 context
    );
        total_checks++;
        if (expect_valid) begin
            if (!violation_valid) begin
                $error("[TLP-RULES] FAIL @ %s: Expected violation valid", context);
                total_failed++;
                record_result(context, 1'b0, "Missing violation_valid");
            end else if (violation_tdi !== expect_tdi) begin
                $error("[TLP-RULES] FAIL @ %s: Violation TDI mismatch - got %0d, expected %0d",
                       context, violation_tdi, expect_tdi);
                total_failed++;
                record_result(context, 1'b0,
                    $sformatf("Wrong violation_tdi: %0d vs %0d", violation_tdi, expect_tdi));
            end else if (violation_code !== expect_code) begin
                $error("[TLP-RULES] FAIL @ %s: Violation code mismatch - got %s, expected %s",
                       context, violation_code.name(), expect_code.name());
                total_failed++;
                record_result(context, 1'b0,
                    $sformatf("Wrong violation_code: %s vs %s",
                              violation_code.name(), expect_code.name()));
            end else begin
                $display("[TLP-RULES] PASS @ %s: Violation TDI=%0d code=%s",
                         context, expect_tdi, expect_code.name());
                record_result(context, 1'b1);
            end
            // Acknowledge the violation to clear it
            violation_ack = 1'b1;
            @(posedge clk);
            violation_ack = 1'b0;
            @(posedge clk);
        end else begin
            if (violation_valid) begin
                $error("[TLP-RULES] FAIL @ %s: Unexpected violation (TDI=%0d code=%s)",
                       context, violation_tdi, violation_code.name());
                total_failed++;
                record_result(context, 1'b0, "Unexpected violation");
            end else begin
                $display("[TLP-RULES] PASS @ %s: No violation as expected", context);
                record_result(context, 1'b1);
            end
        end
    endtask

    //==========================================================================
    // Helper: Verify allow/blocked outputs
    //==========================================================================
    task automatic check_access(
        input logic  got_allow,
        input logic  got_blocked,
        input logic  expect_allow,
        input string context
    );
        total_checks++;
        if (got_allow !== expect_allow) begin
            $error("[TLP-RULES] FAIL @ %s: allow=%0b, expected=%0b",
                   context, got_allow, expect_allow);
            total_failed++;
            record_result(context, 1'b0,
                $sformatf("allow=%0b vs expected=%0b", got_allow, expect_allow));
        end else if (got_blocked !== ~expect_allow) begin
            $error("[TLP-RULES] FAIL @ %s: blocked=%0b but allow=%0b",
                   context, got_blocked, got_allow);
            total_failed++;
            record_result(context, 1'b0, "blocked/allow inconsistent");
        end else begin
            $display("[TLP-RULES] PASS @ %s: allow=%0b blocked=%0b", context, got_allow, got_blocked);
            record_result(context, 1'b1);
        end
    endtask

    //=========================================================================
    // TEST 1: DMA (Mem Write) with T bit in RUN state - TEE access allowed
    //=========================================================================
    task automatic test_dma_tee_in_run;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 1: DMA with T bit in RUN state ---");

        // Set TDI[0] to RUN, enable XT
        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;

        // Set up TEE memory range for TDI[0]: base=0x1000_0000, 16 pages
        set_mmio_range(0, 0, 64'h0000_0010_0000_0000, 32'd16, 1'b0);

        // TEE originator (T=1) with XT=1 writing to TEE memory: should be allowed
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0010_0004), // Within TEE range
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1, "DMA TEE T=1 XT=1 in RUN");
        check_violation(1'b0, '0, ERR_RESERVED, "DMA TEE no violation");
    endtask

    //=========================================================================
    // TEST 2: DMA blocked in ERROR state
    //=========================================================================
    task automatic test_dma_blocked_in_error;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 2: DMA blocked in ERROR state ---");

        tdi_state[0] = TDI_ERROR;
        set_mmio_range(0, 0, 64'h0000_0010_0000_0000, 32'd16, 1'b0);

        // Any memory access to ERROR state TDI should be blocked
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0010_0004),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b0, "DMA in ERROR state");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE, "DMA ERR violation");
    endtask

    //=========================================================================
    // TEST 3: MMIO with T bit enforcement only active in RUN
    //=========================================================================
    task automatic test_mmio_t_bit_run_only;
        logic got_allow_u, got_blocked_u;
        logic got_allow_l, got_blocked_l;
        logic got_allow_r, got_blocked_r;
        $display("[TLP-RULES] --- TEST 3: MMIO T bit enforcement in RUN only ---");

        set_mmio_range(0, 0, 64'h0000_0020_0000_0000, 32'd8, 1'b0);

        // CONFIG_UNLOCKED: non-TEE can access (T bit not enforced)
        tdi_state[0] = TDI_CONFIG_UNLOCKED;
        send_tlp_3dw(
            .dw0           (make_mrd32_dw0()),
            .dw2_addr      (32'h0020_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_u),
            .o_blocked     (got_blocked_u)
        );
        check_access(got_allow_u, got_blocked_u, 1'b1,
                     "MMIO non-TEE in CONFIG_UNLOCKED");

        // CONFIG_LOCKED: non-TEE can access (T bit not enforced)
        tdi_state[0] = TDI_CONFIG_LOCKED;
        send_tlp_3dw(
            .dw0           (make_mrd32_dw0()),
            .dw2_addr      (32'h0020_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_l),
            .o_blocked     (got_blocked_l)
        );
        check_access(got_allow_l, got_blocked_l, 1'b1,
                     "MMIO non-TEE in CONFIG_LOCKED");

        // RUN with XT enabled: non-TEE accessing TEE memory should be BLOCKED
        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;
        send_tlp_3dw(
            .dw0           (make_mrd32_dw0()),
            .dw2_addr      (32'h0020_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b1),
            .o_allow       (got_allow_r),
            .o_blocked     (got_blocked_r)
        );
        check_access(got_allow_r, got_blocked_r, 1'b0,
                     "MMIO non-TEE T=0 in RUN+XT");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "MMIO T=0 RUN+XT violation");
    endtask

    //=========================================================================
    // TEST 4: XT bit handling - strict vs relaxed access control
    //=========================================================================
    task automatic test_xt_bit_handling;
        logic got_allow_xt_on, got_blocked_xt_on;
        logic got_allow_xt_off, got_blocked_xt_off;
        $display("[TLP-RULES] --- TEST 4: XT bit handling ---");

        tdi_state[0] = TDI_RUN;
        set_mmio_range(0, 0, 64'h0000_0030_0000_0000, 32'd8, 1'b0);

        // XT disabled: non-TEE accessing TEE memory -> BLOCKED
        tdi_xt_enabled[0] = 1'b0;
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0030_0010),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_xt_off),
            .o_blocked     (got_blocked_xt_off)
        );
        check_access(got_allow_xt_off, got_blocked_xt_off, 1'b0,
                     "XT off: non-TEE to TEE mem in RUN");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "XT off violation");

        // XT enabled: TEE originator (T=1) with XT=1 to TEE memory -> ALLOWED
        tdi_xt_enabled[0] = 1'b1;
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0030_0010),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow_xt_on),
            .o_blocked     (got_blocked_xt_on)
        );
        check_access(got_allow_xt_on, got_blocked_xt_on, 1'b1,
                     "XT on: TEE T=1 to TEE mem in RUN");
    endtask

    //=========================================================================
    // TEST 5: Completion TLPs always allowed
    //=========================================================================
    task automatic test_completion_always_allowed;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 5: Completions always allowed ---");

        // Test CPL in ERROR state
        tdi_state[0] = TDI_ERROR;
        send_tlp_3dw(
            .dw0           (make_cpl_dw0()),
            .dw2_addr      (32'h0000_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "CPL in ERROR state allowed");

        // Test CPLD in RUN state
        tdi_state[0] = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;
        send_tlp_3dw(
            .dw0           (make_cpld_dw0()),
            .dw2_addr      (32'h0000_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "CPLD in RUN+XT allowed");
    endtask

    //=========================================================================
    // TEST 6: IS_NON_TEE_MEM attribute enforcement
    //=========================================================================
    task automatic test_non_tee_mem_attribute;
        logic got_allow_tee, got_blocked_tee;
        logic got_allow_non, got_blocked_non;
        $display("[TLP-RULES] --- TEST 6: IS_NON_TEE_MEM attribute enforcement ---");

        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;

        // Range 0: TEE memory (is_non_tee=0) at 0x4000_0000
        set_mmio_range(0, 0, 64'h0000_0040_0000_0000, 32'd4, 1'b0);
        // Range 1: Non-TEE memory (is_non_tee=1) at 0x5000_0000
        set_mmio_range(0, 1, 64'h0000_0050_0000_0000, 32'd4, 1'b1);

        // Non-TEE originator (T=0) accessing non-TEE memory: ALLOWED
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0050_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b1),
            .o_allow       (got_allow_non),
            .o_blocked     (got_blocked_non)
        );
        check_access(got_allow_non, got_blocked_non, 1'b1,
                     "Non-TEE to non-TEE mem in RUN+XT");

        // Non-TEE originator (T=0) accessing TEE memory: BLOCKED
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0040_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b1),
            .o_allow       (got_allow_tee),
            .o_blocked     (got_blocked_tee)
        );
        check_access(got_allow_tee, got_blocked_tee, 1'b0,
                     "Non-TEE to TEE mem in RUN+XT");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "Non-TEE to TEE mem violation");
    endtask

    //=========================================================================
    // TEST 7: P2P access control
    //=========================================================================
    task automatic test_p2p_access_control;
        logic got_allow_dis, got_blocked_dis;
        logic got_allow_en, got_blocked_en;
        $display("[TLP-RULES] --- TEST 7: P2P access control ---");

        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;
        tdi_p2p_enabled[0]= 1'b0; // P2P disabled
        set_mmio_range(0, 0, 64'h0000_0060_0000_0000, 32'd4, 1'b0);

        // P2P request from bus=1 (requester_id=0x0100): BLOCKED
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0060_0000),
            .requester_id  (16'h0100), // Bus=1
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow_dis),
            .o_blocked     (got_blocked_dis)
        );
        check_access(got_allow_dis, got_blocked_dis, 1'b0,
                     "P2P disabled: peer blocked");
        check_violation(1'b1, 'd0, ERR_INVALID_DEVICE_CONFIGURATION,
                        "P2P disabled violation");

        // Enable P2P: same request should be allowed (TEE originator)
        tdi_p2p_enabled[0] = 1'b1;
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0060_0000),
            .requester_id  (16'h0100),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow_en),
            .o_blocked     (got_blocked_en)
        );
        check_access(got_allow_en, got_blocked_en, 1'b1,
                     "P2P enabled: peer allowed");
    endtask

    //=========================================================================
    // TEST 8: Completer-side T bit verification (response direction)
    //=========================================================================
    task automatic test_completer_side_t_bit;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 8: Completer-side T bit verification ---");

        // Completions are always allowed regardless of T bit or state
        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;

        // Completion with T=0 (non-TEE originator response)
        send_tlp_3dw(
            .dw0           (make_cpld_dw0()),
            .dw2_addr      (32'h0000_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "Completer CPLD T=0 allowed");

        // Completion with T=1 (TEE originator response)
        send_tlp_3dw(
            .dw0           (make_cpld_dw0()),
            .dw2_addr      (32'h0000_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "Completer CPL T=1 allowed");
    endtask

    //=========================================================================
    // TEST 9: Requester-side T bit generation with XT mode
    //=========================================================================
    task automatic test_requester_t_bit_gen;
        logic got_allow_t1, got_blocked_t1;
        logic got_allow_t0, got_blocked_t0;
        $display("[TLP-RULES] --- TEST 9: Requester-side T bit generation ---");

        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;
        set_mmio_range(0, 0, 64'h0000_0070_0000_0000, 32'd8, 1'b0);

        // Requester with T=1, XT=1 to TEE memory: allowed
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0070_0010),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow_t1),
            .o_blocked     (got_blocked_t1)
        );
        check_access(got_allow_t1, got_blocked_t1, 1'b1,
                     "Requester T=1 XT=1 to TEE mem");

        // Requester with T=0, XT=1 to TEE memory: blocked
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0070_0010),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b1),
            .o_allow       (got_allow_t0),
            .o_blocked     (got_blocked_t0)
        );
        check_access(got_allow_t0, got_blocked_t0, 1'b0,
                     "Requester T=0 XT=1 to TEE mem blocked");
    endtask

    //=========================================================================
    // TEST 10: Config write blocked by firmware lock
    //=========================================================================
    task automatic test_config_fw_lock;
        logic got_allow_locked, got_blocked_locked;
        logic got_allow_unlocked, got_blocked_unlocked;
        $display("[TLP-RULES] --- TEST 10: Config write blocked by FW lock ---");

        set_mmio_range(0, 0, 64'h0000_0080_0000_0000, 32'd4, 1'b0);

        // CONFIG_LOCKED with FW lock: config write blocked
        tdi_state[0]     = TDI_CONFIG_LOCKED;
        tdi_fw_locked[0] = 1'b1;
        send_tlp_3dw(
            .dw0           (make_cfgwr0_dw0()),
            .dw2_addr      (32'h0080_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_locked),
            .o_blocked     (got_blocked_locked)
        );
        check_access(got_allow_locked, got_blocked_locked, 1'b0,
                     "CFG WR locked+fw");
        check_violation(1'b1, 'd0, ERR_INVALID_DEVICE_CONFIGURATION,
                        "CFG WR fw lock violation");

        // CONFIG_LOCKED without FW lock: config write allowed
        tdi_fw_locked[0] = 1'b0;
        send_tlp_3dw(
            .dw0           (make_cfgwr0_dw0()),
            .dw2_addr      (32'h0080_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_unlocked),
            .o_blocked     (got_blocked_unlocked)
        );
        check_access(got_allow_unlocked, got_blocked_unlocked, 1'b1,
                     "CFG WR locked no fw");
    endtask

    //=========================================================================
    // TEST 11: I/O requests blocked in RUN state
    //=========================================================================
    task automatic test_io_blocked_in_run;
        logic got_allow_io, got_blocked_io;
        $display("[TLP-RULES] --- TEST 11: I/O requests blocked in RUN ---");

        tdi_state[0] = TDI_RUN;
        set_mmio_range(0, 0, 64'h0000_0090_0000_0000, 32'd4, 1'b0);

        // I/O Write in RUN state: BLOCKED
        send_tlp_3dw(
            .dw0           (make_iowr_dw0()),
            .dw2_addr      (32'h0090_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_io),
            .o_blocked     (got_blocked_io)
        );
        check_access(got_allow_io, got_blocked_io, 1'b0,
                     "I/O WR in RUN blocked");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "I/O WR RUN violation");
    endtask

    //=========================================================================
    // TEST 12: ATS-translated redirect enforcement
    //=========================================================================
    task automatic test_ats_redirect;
        logic got_allow_redirect, got_blocked_redirect;
        logic got_allow_no_redirect, got_blocked_no_redirect;
        $display("[TLP-RULES] --- TEST 12: ATS-translated redirect ---");

        tdi_state[0]        = TDI_RUN;
        tdi_xt_enabled[0]   = 1'b1;
        tdi_req_redirect[0] = 1'b1;
        set_mmio_range(0, 0, 64'h0000_00A0_0000_0000, 32'd4, 1'b0);

        // ATS-translated (AT=01) non-TEE access to TEE memory with redirect: BLOCKED
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h00A0_0000),
            .requester_id  (16'h0000),
            .at            (2'b01), // ATS translated
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_redirect),
            .o_blocked     (got_blocked_redirect)
        );
        check_access(got_allow_redirect, got_blocked_redirect, 1'b0,
                     "ATS redirect non-TEE to TEE");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "ATS redirect violation");

        // Without redirect: same access should still be blocked by XT rule
        tdi_req_redirect[0] = 1'b0;
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h00A0_0000),
            .requester_id  (16'h0000),
            .at            (2'b01),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow_no_redirect),
            .o_blocked     (got_blocked_no_redirect)
        );
        check_access(got_allow_no_redirect, got_blocked_no_redirect, 1'b0,
                     "ATS no redirect non-TEE to TEE");
    endtask

    //=========================================================================
    // TEST 13: Multi-TDI address matching and isolation
    //=========================================================================
    task automatic test_multi_tdi_isolation;
        logic got_allow_0, got_blocked_0;
        logic got_allow_1, got_blocked_1;
        $display("[TLP-RULES] --- TEST 13: Multi-TDI isolation ---");

        // TDI[0] in ERROR, TDI[1] in RUN
        tdi_state[0]      = TDI_ERROR;
        tdi_state[1]      = TDI_RUN;
        tdi_xt_enabled[1] = 1'b1;

        // TDI[0] range: 0xB000_0000
        set_mmio_range(0, 0, 64'h0000_00B0_0000_0000, 32'd4, 1'b0);
        // TDI[1] range: 0xC000_0000 (non-TEE)
        set_mmio_range(1, 0, 64'h0000_00C0_0000_0000, 32'd4, 1'b1);

        // Access TDI[0] range (ERROR state): blocked
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h00B0_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow_0),
            .o_blocked     (got_blocked_0)
        );
        check_access(got_allow_0, got_blocked_0, 1'b0,
                     "TDI[0] ERROR blocked");

        // Access TDI[1] range (RUN, non-TEE): allowed
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h00C0_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b1),
            .o_allow       (got_allow_1),
            .o_blocked     (got_blocked_1)
        );
        check_access(got_allow_1, got_blocked_1, 1'b1,
                     "TDI[1] RUN non-TEE allowed");
    endtask

    //=========================================================================
    // TEST 14: Violation capture and acknowledgement handshake
    //=========================================================================
    task automatic test_violation_handshake;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 14: Violation capture and ack ---");

        tdi_state[0] = TDI_ERROR;
        set_mmio_range(0, 0, 64'h0000_00D0_0000_0000, 32'd4, 1'b0);

        // Send blocked TLP - violation should be captured
        tlp_valid          = 1'b1;
        tlp_header_dw0     = make_mwr32_dw0();
        tlp_header_dw2     = 32'h00D0_0000;
        tlp_header_dw3     = 32'h0;
        tlp_is_4dw         = 1'b0;
        tlp_requester_id   = 16'h0000;
        tlp_at             = 2'b00;
        tlp_tee_originator = 1'b0;
        tlp_xt_enabled     = 1'b0;
        @(posedge clk);

        // Check violation captured
        total_checks++;
        if (!violation_valid) begin
            $error("[TLP-RULES] FAIL: Violation not captured");
            total_failed++;
            record_result("Violation captured", 1'b0, "violation_valid not set");
        end else if (violation_tdi !== 'd0) begin
            $error("[TLP-RULES] FAIL: Wrong violation TDI %0d", violation_tdi);
            total_failed++;
            record_result("Violation TDI", 1'b0,
                $sformatf("Wrong TDI: %0d", violation_tdi));
        end else begin
            $display("[TLP-RULES] PASS: Violation captured TDI=0 code=%s",
                     violation_code.name());
            record_result("Violation captured", 1'b1);
        end

        // Send second violation without ack - should NOT overwrite
        tlp_tee_originator = 1'b1; // Different T bit
        @(posedge clk);
        total_checks++;
        if (violation_valid && violation_tdi === 'd0) begin
            // Still holding first violation (pending_q prevents overwrite)
            $display("[TLP-RULES] PASS: First violation held during pending");
            record_result("Violation held", 1'b1);
        end else begin
            $error("[TLP-RULES] FAIL: Violation state unexpected");
            total_failed++;
            record_result("Violation held", 1'b0, "Unexpected state");
        end

        tlp_valid = 1'b0;
        @(posedge clk);

        // Acknowledge - should clear
        violation_ack = 1'b1;
        @(posedge clk);
        total_checks++;
        if (!violation_valid) begin
            $display("[TLP-RULES] PASS: Violation cleared after ack");
            record_result("Violation ack clear", 1'b1);
        end else begin
            $error("[TLP-RULES] FAIL: Violation not cleared after ack");
            total_failed++;
            record_result("Violation ack clear", 1'b0, "Still valid");
        end
        violation_ack = 1'b0;
        @(posedge clk);
    endtask

    //=========================================================================
    // TEST 15: Reset clears all violations and blocked state
    //=========================================================================
    task automatic test_reset_clears_violations;
        $display("[TLP-RULES] --- TEST 15: Reset clears violations ---");

        // Force a violation state
        tdi_state[0] = TDI_ERROR;
        set_mmio_range(0, 0, 64'h0000_00E0_0000_0000, 32'd4, 1'b0);

        tlp_valid          = 1'b1;
        tlp_header_dw0     = make_mwr32_dw0();
        tlp_header_dw2     = 32'h00E0_0000;
        tlp_tee_originator = 1'b0;
        @(posedge clk);
        tlp_valid = 1'b0;

        // Apply reset
        apply_reset;

        // Check all outputs are clean
        total_checks++;
        if (tlp_blocked === 1'b0 && violation_valid === 1'b0 &&
            tlp_violation_irq === 1'b0) begin
            $display("[TLP-RULES] PASS: Reset cleared all violation state");
            record_result("Reset clears violations", 1'b1);
        end else begin
            $error("[TLP-RULES] FAIL: State not clean after reset");
            total_failed++;
            record_result("Reset clears violations", 1'b0, "State残留");
        end
    endtask

    //=========================================================================
    // TEST 16: No TDI match - default allow for memory
    //=========================================================================
    task automatic test_no_tdi_match;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 16: No TDI match default allow ---");

        // No MMIO ranges set up, all invalid from reset
        tdi_state[0] = TDI_RUN;
        tdi_xt_enabled[0] = 1'b1;

        // Memory write to address not matching any TDI range
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'hF000_0000), // No range covers this
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "No TDI match: mem default allow");
    endtask

    //=========================================================================
    // TEST 17: Message TLP always allowed
    //=========================================================================
    task automatic test_message_always_allowed;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 17: Message TLP always allowed ---");

        // Message TLP in ERROR state
        tdi_state[0] = TDI_ERROR;
        send_tlp_3dw(
            .dw0           (make_msg_dw0()),
            .dw2_addr      (32'h0000_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b1,
                     "Message TLP in ERROR allowed");
    endtask

    //=========================================================================
    // TEST 18: Non-TEE blocked from TEE memory in RUN without XT
    //=========================================================================
    task automatic test_non_tee_blocked_run_no_xt;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 18: Non-TEE blocked from TEE mem (no XT) ---");

        tdi_state[0]      = TDI_RUN;
        tdi_xt_enabled[0] = 1'b0; // XT disabled
        set_mmio_range(0, 0, 64'h0000_00F0_0000_0000, 32'd8, 1'b0);

        // Non-TEE (T=0) accessing TEE memory without XT: BLOCKED
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h00F0_0000),
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b0,
                     "Non-TEE to TEE mem RUN no XT");
        check_violation(1'b1, 'd0, ERR_INVALID_INTERFACE_STATE,
                        "Non-TEE to TEE no XT violation");
    endtask

    //=========================================================================
    // TEST 19: P2P blocked when p2p_enabled is false
    //=========================================================================
    task automatic test_p2p_blocked_in_run;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 19: P2P blocked in RUN (disabled) ---");

        tdi_state[0]       = TDI_RUN;
        tdi_xt_enabled[0]  = 1'b1;
        tdi_p2p_enabled[0] = 1'b0;
        set_mmio_range(0, 0, 64'h0000_0110_0000_0000, 32'd4, 1'b1); // Non-TEE range

        // P2P request from bus=2 (requester_id=0x0200) to non-TEE range
        // Even though non-TEE memory and TEE originator, P2P is blocked
        send_tlp_3dw(
            .dw0           (make_mwr32_dw0()),
            .dw2_addr      (32'h0110_0000),
            .requester_id  (16'h0200), // Bus=2 (P2P)
            .at            (2'b00),
            .tee_originator(1'b1),
            .xt_en         (1'b1),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        check_access(got_allow, got_blocked, 1'b0,
                     "P2P disabled blocks peer in RUN");
        check_violation(1'b1, 'd0, ERR_INVALID_DEVICE_CONFIGURATION,
                        "P2P disabled RUN violation");
    endtask

    //=========================================================================
    // TEST 20: 4DW header address range matching
    //=========================================================================
    task automatic test_4dw_address_matching;
        logic got_allow, got_blocked;
        $display("[TLP-RULES] --- TEST 20: 4DW header address matching ---");

        tdi_state[0]      = TDI_ERROR;
        set_mmio_range(0, 0, 64'h0000_0100_0000_0000, 32'd4, 1'b0);

        // 4DW Memory Write to 64-bit address
        send_tlp_4dw(
            .dw0           (make_mwr64_dw0()),
            .dw2_addr_hi   (32'h0000_0100), // Upper 32 bits
            .dw3_addr_lo   (32'h0000_0010), // Lower 32 bits (addr = 0x0100_0000_0010<<2... wait)
            .requester_id  (16'h0000),
            .at            (2'b00),
            .tee_originator(1'b0),
            .xt_en         (1'b0),
            .o_allow       (got_allow),
            .o_blocked     (got_blocked)
        );
        // Address = {dw2, dw3[31:2], 2'b00} = 0x0100_0000_0040
        // Range: 0x0100_0000_0000 to 0x0100_0000_3FFF (4 pages * 4096)
        // 0x0100_0000_0040 is within range, ERROR state -> blocked
        check_access(got_allow, got_blocked, 1'b0,
                     "4DW MWR in ERROR blocked");
    endtask

    //==========================================================================
    // Run all tests
    //==========================================================================
    task automatic run_all_tests;
        $display("[TLP-RULES] ================================================================");
        $display("[TLP-RULES]   Starting TLP Access Control Enforcement Tests");
        $display("[TLP-RULES] ================================================================");

        apply_reset;

        test_dma_tee_in_run;
        apply_reset;

        test_dma_blocked_in_error;
        apply_reset;

        test_mmio_t_bit_run_only;
        apply_reset;

        test_xt_bit_handling;
        apply_reset;

        test_completion_always_allowed;
        apply_reset;

        test_non_tee_mem_attribute;
        apply_reset;

        test_p2p_access_control;
        apply_reset;

        test_completer_side_t_bit;
        apply_reset;

        test_requester_t_bit_gen;
        apply_reset;

        test_config_fw_lock;
        apply_reset;

        test_io_blocked_in_run;
        apply_reset;

        test_ats_redirect;
        apply_reset;

        test_multi_tdi_isolation;
        apply_reset;

        test_violation_handshake;
        apply_reset;

        test_reset_clears_violations;
        apply_reset;

        test_no_tdi_match;
        apply_reset;

        test_message_always_allowed;
        apply_reset;

        test_non_tee_blocked_run_no_xt;
        apply_reset;

        test_p2p_blocked_in_run;
        apply_reset;

        test_4dw_address_matching;

        $display("[TLP-RULES] ================================================================");
        $display("[TLP-RULES]   ALL TLP RULES TESTS COMPLETE");
        $display("[TLP-RULES] ================================================================");
    endtask

    //==========================================================================
    // Final Report
    //==========================================================================
    task automatic print_report;
        int unsigned pass_count = 0;
        int unsigned fail_count = 0;

        $display("");
        $display("================================================================");
        $display("     TEST_TDISP_TLP_RULES - Detailed Report");
        $display("================================================================");
        $display("  %-50s | %-6s | %s", "Test Name", "Result", "Detail");
        $display("----------------------------------------------------------------");

        for (int i = 0; i < results.size(); i++) begin
            $display("  %-50s | %-6s | %s",
                     results[i].test_name,
                     results[i].passed ? "PASS" : "FAIL",
                     results[i].detail);
            if (results[i].passed) pass_count++;
            else                   fail_count++;
        end

        $display("----------------------------------------------------------------");
        $display("  Total Checks : %0d", total_checks);
        $display("  Passed       : %0d", pass_count);
        $display("  Failed       : %0d", fail_count);
        $display("  Raw Passed   : %0d", total_passed);
        $display("  Raw Failed   : %0d", total_failed);
        $display("================================================================");

        $display("  Per-TDI Final States:");
        for (int i = 0; i < NUM_TDI; i++) begin
            $display("    TDI[%0d]: state=%-16s xt=%0b fw_lock=%0b p2p=%0b redirect=%0b",
                     i, tdi_state[i].name(),
                     tdi_xt_enabled[i], tdi_fw_locked[i],
                     tdi_p2p_enabled[i], tdi_req_redirect[i]);
        end

        $display("================================================================");
        if (fail_count == 0) begin
            $display("   *** ALL TLP ACCESS CONTROL TESTS PASSED ***");
        end else begin
            $display("   *** %0d TEST FAILURES ***", fail_count);
        end
        $display("================================================================");
        $display("");
    endtask

    //==========================================================================
    // Main stimulus
    //==========================================================================
    initial begin
        run_all_tests;
        print_report;
        $finish;
    end

    //==========================================================================
    // Watchdog timeout
    //==========================================================================
    initial begin
        #100us;
        $error("[TLP-RULES] WATCHDOG: Simulation timeout");
        $finish;
    end

endmodule : test_tdisp_tlp_rules
