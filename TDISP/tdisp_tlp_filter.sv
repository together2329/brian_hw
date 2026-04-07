// ============================================================================
// Module:    tdisp_tlp_filter.sv
// Purpose:   TDISP TLP Filter u2014 enforces XT/T bit rules per PCIe 7.0 u00a711.2
//            Implements egress (TDI as Requester) and ingress (TDI as Completer)
//            filtering for Memory Requests, Completions, VDMs, ATS, and I/O.
// Spec:      PCI Express Base Specification Revision 7.0, Section 11.2.1/11.2.2
//
// Egress Rules (u00a711.2.1 u2014 TDI as Requester, outgoing TLPs):
//   - TDI not in RUN: XT=0, T=0; reject non-MSI Memory Requests
//   - RUN, no XT mode: untranslated MemRequ2192T=1; MSIu2192T=0; MSI-X lockedu2192T=1
//   - RUN, XT mode: TEE memu2192XT=1,T=1; non-TEEu2192XT=1,T=0; unrestrictedu2192XT=0,T=1
//   - I/O Requests: always rejected (could compromise TVM data)
//   - ATS Translation Requests: never blocked
//   - Completions: pass-through when in RUN, else reject
//
// Ingress Rules (u00a711.2.2 u2014 TDI as Completer, incoming TLPs):
//   - No XT mode: TEE memu2192need T=1 + RUN + bound_stream; non-TEEu2192need T=0
//   - XT mode:    TEE memu2192need XT=1,T=1,RUN,bound; non-TEEu2192need T=0
//   - Non-IDE TLPs when IDE required u2192 reject
//   - MSI-X table locked: access without T bit u2192 reject
//
// One instance per TDI. Purely combinational classification, registered outputs.
// ============================================================================

module tdisp_tlp_filter
    import tdisp_pkg::*;
#(
    // Width of TLP data bus (flit width, typically 128 or 256 bits)
    parameter int TLP_DATA_WIDTH = 128,

    // Address type field width (2 bits per PCIe spec)
    parameter int ADDR_TYPE_WIDTH = 2
)(
    input  logic                            clk,
    input  logic                            rst_n,

    // =========================================================================
    // TDI State and Configuration (from FSM / SET_TDISP_CONFIG)
    // =========================================================================
    input  tdisp_tdi_state_e                tdi_state,
    input  logic                            xt_mode_enabled,
    input  logic                            xt_bit_for_locked_msix,  // From SET_TDISP_CONFIG

    // =========================================================================
    // Egress Path (TDI as Requester u2014 outgoing TLPs)
    // =========================================================================
    input  logic                            eg_tlp_valid,
    input  logic [TLP_DATA_WIDTH-1:0]       eg_tlp_data,
    input  logic                            eg_tlp_last,

    // Egress TLP classification inputs (from TLP parser)
    input  logic                            eg_tlp_is_memory_req,    // Memory Read/Write
    input  logic                            eg_tlp_is_completion,    // Completion TLP
    input  logic                            eg_tlp_is_msi,           // MSI or MSI-X interrupt
    input  logic                            eg_tlp_is_msix,          // Specifically MSI-X
    input  logic                            eg_tlp_is_msix_locked,   // MSI-X table is locked+reported
    input  logic                            eg_tlp_is_ats_request,   // ATS Translation Request
    input  logic                            eg_tlp_is_vdm,           // Vendor Defined Message
    input  logic                            eg_tlp_is_io_req,        // I/O Request
    input  logic [ADDR_TYPE_WIDTH-1:0]      eg_tlp_addr_type,        // AT field: 00=untranslated

    // Egress memory attribute inputs (from device logic / MMIO lookup)
    input  logic                            eg_access_tee_mem,       // Access targets TEE memory
    input  logic                            eg_access_non_tee_mem,   // Access targets non-TEE memory

    // Egress outputs (modified TLP + XT/T metadata)
    output logic                            eg_tlp_out_valid,
    output logic [TLP_DATA_WIDTH-1:0]       eg_tlp_out_data,
    output logic                            eg_tlp_out_last,
    output logic                            eg_tlp_xt_bit,           // XT bit value set by filter
    output logic                            eg_tlp_t_bit,            // T bit value set by filter
    output logic                            eg_tlp_reject,           // Drop this TLP

    // =========================================================================
    // Ingress Path (TDI as Completer u2014 incoming TLPs)
    // =========================================================================
    input  logic                            ig_tlp_valid,
    input  logic [TLP_DATA_WIDTH-1:0]       ig_tlp_data,
    input  logic                            ig_tlp_last,

    // Ingress TLP classification inputs (from IDE prefix / OHC-C / parser)
    input  logic                            ig_tlp_xt_bit,           // From IDE prefix
    input  logic                            ig_tlp_t_bit,            // From IDE prefix / OHC-C
    input  logic                            ig_tlp_is_memory_req,    // Memory Read/Write
    input  logic                            ig_tlp_is_completion,    // Completion TLP
    input  logic                            ig_tlp_is_vdm,           // Vendor Defined Message
    input  logic                            ig_tlp_is_ats_request,   // ATS Translation Request
    input  logic                            ig_tlp_target_is_non_tee_mem,  // From MMIO attribute lookup
    input  logic                            ig_tlp_on_bound_stream,        // IDE stream bound to this TDI
    input  logic                            ig_ide_required,               // IDE required for this link
    input  logic                            ig_msix_table_locked,          // MSI-X table lock status

    // Ingress outputs
    output logic                            ig_tlp_out_valid,
    output logic [TLP_DATA_WIDTH-1:0]       ig_tlp_out_data,
    output logic                            ig_tlp_out_last,
    output logic                            ig_tlp_reject             // Drop this TLP
);

    // =========================================================================
    // Address type constants (AT field in TLP header)
    // =========================================================================
    localparam logic [ADDR_TYPE_WIDTH-1:0] AT_UNTRANSLATED = 2'b00;
    localparam logic [ADDR_TYPE_WIDTH-1:0] AT_TRANSLATED   = 2'b10;

    // =========================================================================
    // Internal egress classification result
    // =========================================================================
    logic   eg_reject_comb;
    logic   eg_xt_bit_comb;
    logic   eg_t_bit_comb;

    // =========================================================================
    // EGRESS CLASSIFICATION (u00a711.2.1 u2014 TDI as Requester)
    //   Purely combinational. Determines XT/T bits and reject decision.
    // =========================================================================
    always_comb begin
        // Defaults: pass-through with no XT/T bits
        eg_reject_comb = 1'b0;
        eg_xt_bit_comb = 1'b0;
        eg_t_bit_comb  = 1'b0;

        if (eg_tlp_valid) begin

            // -----------------------------------------------------------------
            // ATS Translation Requests: never blocked in any state (u00a711.2)
            // -----------------------------------------------------------------
            if (eg_tlp_is_ats_request) begin
                // Pass through unconditionally u2014 no XT/T bits
                eg_xt_bit_comb = 1'b0;
                eg_t_bit_comb  = 1'b0;
            end

            // -----------------------------------------------------------------
            // I/O Requests: always rejected (could compromise TVM data)
            // -----------------------------------------------------------------
            else if (eg_tlp_is_io_req) begin
                eg_reject_comb = 1'b1;
            end

            // -----------------------------------------------------------------
            // Completions: pass through only when TDI is in RUN
            //   Ignore XT/T bits in received Completions (egress side).
            // -----------------------------------------------------------------
            else if (eg_tlp_is_completion) begin
                if (tdi_state != TDI_STATE_RUN) begin
                    eg_reject_comb = 1'b1;
                end
                // In RUN: pass through, XT/T = 0 (completions don't carry them)
            end

            // -----------------------------------------------------------------
            // VDMs: allowed in CONFIG_LOCKED/RUN/ERROR iff T=1 (XT=1 if XT mode)
            // -----------------------------------------------------------------
            else if (eg_tlp_is_vdm) begin
                if (tdi_state == TDI_STATE_CONFIG_LOCKED ||
                    tdi_state == TDI_STATE_RUN ||
                    tdi_state == TDI_STATE_ERROR) begin
                    eg_t_bit_comb  = 1'b1;
                    eg_xt_bit_comb = xt_mode_enabled;  // XT=1 if XT mode enabled
                end else begin
                    // CONFIG_UNLOCKED: VDMs without T bit
                    eg_xt_bit_comb = 1'b0;
                    eg_t_bit_comb  = 1'b0;
                end
            end

            // -----------------------------------------------------------------
            // Memory Requests
            // -----------------------------------------------------------------
            else if (eg_tlp_is_memory_req) begin

                // =============================================================
                // Case 1: TDI NOT in RUN (CONFIG_UNLOCKED / CONFIG_LOCKED / ERROR)
                //   XT=0, T=0 for all Memory Requests
                //   No Memory Requests allowed (except MSI/MSI-X below)
                // =============================================================
                if (tdi_state != TDI_STATE_RUN) begin
                    if (eg_tlp_is_msi) begin
                        // MSI/MSI-X interrupts: allowed even when not in RUN
                        eg_xt_bit_comb = 1'b0;
                        eg_t_bit_comb  = 1'b0;
                    end else begin
                        // Non-MSI Memory Requests: rejected outside RUN
                        eg_reject_comb = 1'b1;
                    end
                end

                // =============================================================
                // Case 2: TDI in RUN
                // =============================================================
                else begin // tdi_state == TDI_STATE_RUN

                    if (!xt_mode_enabled) begin
                        // -----------------------------------------------------
                        // RUN, XT Mode NOT enabled (u00a711.2.1)
                        // -----------------------------------------------------
                        if (eg_tlp_is_msi && !eg_tlp_is_msix) begin
                            // MSI using MSI capability: T=0
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b0;
                        end
                        else if (eg_tlp_is_msix && !eg_tlp_is_msix_locked) begin
                            // MSI-X, table NOT locked: T=0
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b0;
                        end
                        else if (eg_tlp_is_msix && eg_tlp_is_msix_locked) begin
                            // MSI-X, table locked: T=1
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b1;
                        end
                        else begin
                            // Non-MSI Memory Requests
                            if (eg_tlp_addr_type == AT_UNTRANSLATED) begin
                                // Untranslated Memory Requests: T=1
                                eg_t_bit_comb = 1'b1;
                            end else begin
                                // Translated requests: T=0 (no restriction)
                                eg_t_bit_comb = 1'b0;
                            end
                            eg_xt_bit_comb = 1'b0;
                        end
                    end

                    else begin
                        // -----------------------------------------------------
                        // RUN, XT Mode enabled (u00a711.2.1)
                        // -----------------------------------------------------
                        if (eg_tlp_is_msi && !eg_tlp_is_msix) begin
                            // MSI using MSI capability: XT=0, T=0
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b0;
                        end
                        else if (eg_tlp_is_msix && !eg_tlp_is_msix_locked) begin
                            // MSI-X, table NOT locked: XT=0, T=0
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b0;
                        end
                        else if (eg_tlp_is_msix && eg_tlp_is_msix_locked) begin
                            // MSI-X, table locked: XT=xt_bit_for_locked_msix, T=1
                            eg_xt_bit_comb = xt_bit_for_locked_msix;
                            eg_t_bit_comb  = 1'b1;
                        end
                        else if (eg_access_tee_mem && !eg_access_non_tee_mem) begin
                            // Access restricted to TEE memory: XT=1, T=1
                            eg_xt_bit_comb = 1'b1;
                            eg_t_bit_comb  = 1'b1;
                        end
                        else if (eg_access_non_tee_mem && !eg_access_tee_mem) begin
                            // Access restricted to non-TEE memory: XT=1, T=0
                            eg_xt_bit_comb = 1'b1;
                            eg_t_bit_comb  = 1'b0;
                        end
                        else begin
                            // No specific restriction: XT=0, T=1
                            eg_xt_bit_comb = 1'b0;
                            eg_t_bit_comb  = 1'b1;
                        end
                    end
                end
            end

            // -----------------------------------------------------------------
            // Other TLP types: conservative pass-through (no XT/T)
            // -----------------------------------------------------------------
            // Default values already set (XT=0, T=0, reject=0)
        end
    end

    // =========================================================================
    // EGRESS REGISTERED OUTPUTS
    //   Single always_ff block per project convention.
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            eg_tlp_out_valid <= 1'b0;
            eg_tlp_out_data  <= '0;
            eg_tlp_out_last  <= 1'b0;
            eg_tlp_xt_bit    <= 1'b0;
            eg_tlp_t_bit     <= 1'b0;
            eg_tlp_reject    <= 1'b0;
        end else begin
            // Pipeline: register the classification result
            eg_tlp_out_valid <= eg_tlp_valid;
            eg_tlp_out_data  <= eg_tlp_data;
            eg_tlp_out_last  <= eg_tlp_last;
            eg_tlp_xt_bit    <= eg_xt_bit_comb;
            eg_tlp_t_bit     <= eg_t_bit_comb;
            eg_tlp_reject    <= eg_reject_comb;
        end
    end

    // =========================================================================
    // Internal ingress classification result
    // =========================================================================
    logic   ig_reject_comb;

    // =========================================================================
    // INGRESS CLASSIFICATION (u00a711.2.2 u2014 TDI as Completer)
    //   Purely combinational. Validates incoming TLPs against XT/T rules.
    // =========================================================================
    always_comb begin
        // Default: accept
        ig_reject_comb = 1'b0;

        if (ig_tlp_valid) begin

            // -----------------------------------------------------------------
            // ATS Translation Requests: never blocked in any state
            // -----------------------------------------------------------------
            if (ig_tlp_is_ats_request) begin
                // Pass through unconditionally
            end

            // -----------------------------------------------------------------
            // Completions: check XT/T bit match (requestor side validation)
            //   Completions are validated by matching the original request's
            //   XT/T bits. The completer side does not reject based on bits,
            //   but if IDE is required and stream is not bound, reject.
            // -----------------------------------------------------------------
            else if (ig_tlp_is_completion) begin
                if (ig_ide_required && !ig_tlp_on_bound_stream) begin
                    ig_reject_comb = 1'b1;
                end
                // Completion XT/T bits must match request u2014 validated at
                // the requestor side, not rejected here
            end

            // -----------------------------------------------------------------
            // VDMs (ingress): accepted if proper XT/T bits
            //   VDMs allowed in CONFIG_LOCKED/RUN/ERROR with T=1
            // -----------------------------------------------------------------
            else if (ig_tlp_is_vdm) begin
                if (!xt_mode_enabled) begin
                    // Need T=1 for VDM acceptance in non-XT mode
                    if (!ig_tlp_t_bit) begin
                        ig_reject_comb = 1'b1;
                    end
                end else begin
                    // XT mode: need XT=1 and T=1
                    if (!ig_tlp_xt_bit || !ig_tlp_t_bit) begin
                        ig_reject_comb = 1'b1;
                    end
                end
                // Also check IDE stream binding
                if (ig_ide_required && !ig_tlp_on_bound_stream) begin
                    ig_reject_comb = 1'b1;
                end
            end

            // -----------------------------------------------------------------
            // Memory Requests (ingress)
            // -----------------------------------------------------------------
            else if (ig_tlp_is_memory_req) begin

                // -----------------------------------------------------------------
                // Global check: Non-IDE TLPs when IDE required u2192 REJECT
                // -----------------------------------------------------------------
                if (ig_ide_required && !ig_tlp_on_bound_stream) begin
                    ig_reject_comb = 1'b1;
                end

                // -----------------------------------------------------------------
                // MSI-X table locked: access without T bit Set u2192 REJECT
                // -----------------------------------------------------------------
                else if (ig_msix_table_locked && !ig_tlp_t_bit) begin
                    ig_reject_comb = 1'b1;
                end

                else if (!xt_mode_enabled) begin
                    // -------------------------------------------------
                    // XT Mode NOT enabled (u00a711.2.2)
                    // -------------------------------------------------
                    if (!ig_tlp_target_is_non_tee_mem) begin
                        // TEE memory: accept iff T=1 AND TDI in RUN AND
                        // (IDE stream bound OR IDE not required)
                        if (!ig_tlp_t_bit ||
                            tdi_state != TDI_STATE_RUN ||
                            (ig_ide_required && !ig_tlp_on_bound_stream)) begin
                            ig_reject_comb = 1'b1;
                        end
                    end else begin
                        // Non-TEE memory: accept iff T=0
                        if (ig_tlp_t_bit) begin
                            ig_reject_comb = 1'b1;
                        end
                    end
                end

                else begin
                    // -------------------------------------------------
                    // XT Mode enabled (u00a711.2.2)
                    // -------------------------------------------------
                    if (!ig_tlp_target_is_non_tee_mem) begin
                        // TEE memory: accept iff XT=1 AND T=1 AND TDI in RUN
                        // AND IDE stream bound
                        if (!ig_tlp_xt_bit || !ig_tlp_t_bit ||
                            tdi_state != TDI_STATE_RUN ||
                            !ig_tlp_on_bound_stream) begin
                            ig_reject_comb = 1'b1;
                        end
                    end else begin
                        // Non-TEE memory: accept iff T=0 (XT can be 0 or 1)
                        if (ig_tlp_t_bit) begin
                            ig_reject_comb = 1'b1;
                        end
                    end
                end
            end

            // -----------------------------------------------------------------
            // Other TLP types: accept by default
            // -----------------------------------------------------------------
        end
    end

    // =========================================================================
    // INGRESS REGISTERED OUTPUTS
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ig_tlp_out_valid <= 1'b0;
            ig_tlp_out_data  <= '0;
            ig_tlp_out_last  <= 1'b0;
            ig_tlp_reject    <= 1'b0;
        end else begin
            ig_tlp_out_valid <= ig_tlp_valid;
            ig_tlp_out_data  <= ig_tlp_data;
            ig_tlp_out_last  <= ig_tlp_last;
            ig_tlp_reject    <= ig_reject_comb;
        end
    end

    // =========================================================================
    // Assertions
    // =========================================================================
    // pragma synthesis_off
    `ifdef FORMAL
        // Egress: reject and valid are mutually exclusive in outcome
        // (reject=1 means the TLP is dropped, even if valid is asserted)
        assert property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_reject |-> eg_tlp_out_valid)
        else $error("eg_tlp_reject asserted but eg_tlp_out_valid not set u2014 pipeline inconsistency");

        // Ingress: reject and valid are mutually exclusive in outcome
        assert property (@(posedge clk) disable iff (!rst_n)
            ig_tlp_reject |-> ig_tlp_out_valid)
        else $error("ig_tlp_reject asserted but ig_tlp_out_valid not set u2014 pipeline inconsistency");

        // Egress: I/O requests always rejected
        assert property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_valid && eg_tlp_is_io_req |-> eg_tlp_reject)
        else $error("I/O request not rejected on egress path");

        // Egress: ATS requests never rejected
        assert property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_valid && eg_tlp_is_ats_request |-> !eg_tlp_reject)
        else $error("ATS Translation Request incorrectly rejected on egress");

        // Ingress: ATS requests never rejected
        assert property (@(posedge clk) disable iff (!rst_n)
            ig_tlp_valid && ig_tlp_is_ats_request |-> !ig_tlp_reject)
        else $error("ATS Translation Request incorrectly rejected on ingress");

        // Cover: egress Memory Request in RUN with XT mode
        cover property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_valid && eg_tlp_is_memory_req &&
            tdi_state == TDI_STATE_RUN && xt_mode_enabled);

        // Cover: ingress TEE memory access accepted
        cover property (@(posedge clk) disable iff (!rst_n)
            ig_tlp_valid && ig_tlp_is_memory_req &&
            !ig_tlp_target_is_non_tee_mem && !ig_tlp_reject);

        // Cover: ingress non-TEE memory access accepted
        cover property (@(posedge clk) disable iff (!rst_n)
            ig_tlp_valid && ig_tlp_is_memory_req &&
            ig_tlp_target_is_non_tee_mem && !ig_tlp_reject);

        // Cover: egress MSI-X with locked table
        cover property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_valid && eg_tlp_is_msix && eg_tlp_is_msix_locked);

        // Cover: VDM egress
        cover property (@(posedge clk) disable iff (!rst_n)
            eg_tlp_valid && eg_tlp_is_vdm && tdi_state == TDI_STATE_RUN);
    `endif
    // pragma synthesis_on

endmodule : tdisp_tlp_filter
