// mctp_assembler_v3_cdc_sync.sv
// Explicit CDC bridge between pclk (APB/config) and axi_aclk (datapath).
// Implements cdc_requirements.crossings + synchronizers:
//   - pclk -> axi_aclk: cfg_* config levels via 2-FF synchronizers
//   - pclk -> axi_aclk: cmd_* command pulses via pulse-sync (toggle/2-FF/re-edge)
//   - axi_aclk -> pclk: evt_* event pulses via pulse-sync (toggle/2-FF/re-edge)
//   - axi_aclk -> pclk: sts_* status levels via 2-FF synchronizers
//   - axi_aclk -> pclk: 4x32-bit read words via req/ack handshake synchronizer
// Pure synchronizer fabric; no logic transforms on crossing data.
`default_nettype none
module mctp_assembler_v3_cdc_sync #(
    parameter integer SRAM_ADDR_WIDTH = 16
) (
    input  wire         axi_aclk,
    input  wire         axi_aresetn,
    input  wire         pclk,
    input  wire         presetn,

    // ------------------------------------------------------------------
    // pclk -> axi_aclk: configuration levels (from regfile cfg_* outputs)
    // ------------------------------------------------------------------
    input  wire         cfg_enable_p,
    input  wire         cfg_drop_when_disabled_p,
    input  wire         cfg_dest_filter_enable_p,
    input  wire         cfg_accept_broadcast_eid_p,
    input  wire         cfg_accept_null_eid_p,
    input  wire         cfg_raw_sram_debug_read_enable_p,
    input  wire [7:0]   cfg_local_eid_p,
    input  wire [7:0]   cfg_debug_context_select_p,
    input  wire [12:0]  cfg_tu_bytes_p,
    input  wire [12:0]  cfg_max_message_bytes_p,
    input  wire [23:0]  cfg_timeout_cycles_p,
    input  wire [15:0]  cfg_sram_base_p,
    input  wire [15:0]  cfg_sram_limit_p,

    output reg          cfg_enable_a,
    output reg          cfg_drop_when_disabled_a,
    output reg          cfg_dest_filter_enable_a,
    output reg          cfg_accept_broadcast_eid_a,
    output reg          cfg_accept_null_eid_a,
    output reg          cfg_raw_sram_debug_read_enable_a,
    output reg  [7:0]   cfg_local_eid_a,
    output reg  [7:0]   cfg_debug_context_select_a,
    output reg  [12:0]  cfg_tu_bytes_a,
    output reg  [12:0]  cfg_max_message_bytes_a,
    output reg  [23:0]  cfg_timeout_cycles_a,
    output reg  [15:0]  cfg_sram_base_a,
    output reg  [15:0]  cfg_sram_limit_a,

    // ------------------------------------------------------------------
    // pclk -> axi_aclk: command pulses
    // ------------------------------------------------------------------
    input  wire         cmd_soft_reset_p,
    input  wire         cmd_descriptor_pop_p,
    input  wire         cmd_counter_clear_p,

    output reg          cmd_soft_reset_a,
    output reg          cmd_descriptor_pop_a,
    output reg          cmd_counter_clear_a,

    // ------------------------------------------------------------------
    // axi_aclk -> pclk: event pulses (from datapath)
    // ------------------------------------------------------------------
    input  wire         evt_descriptor_ready_a,
    input  wire         evt_packet_drop_a,
    input  wire         evt_assembly_drop_a,
    input  wire         evt_context_timeout_a,
    input  wire         evt_sram_overflow_a,
    input  wire         evt_descriptor_queue_full_a,
    input  wire         evt_axi_write_malformed_a,
    input  wire         evt_axi_read_error_a,
    input  wire         evt_fatal_internal_error_a,

    output reg          evt_descriptor_ready_p,
    output reg          evt_packet_drop_p,
    output reg          evt_assembly_drop_p,
    output reg          evt_context_timeout_p,
    output reg          evt_sram_overflow_p,
    output reg          evt_descriptor_queue_full_p,
    output reg          evt_axi_write_malformed_p,
    output reg          evt_axi_read_error_p,
    output reg          evt_fatal_internal_error_p,

    // ------------------------------------------------------------------
    // axi_aclk -> pclk: status levels
    // ------------------------------------------------------------------
    input  wire         sts_descriptor_available_a,
    input  wire         sts_descriptor_queue_full_a,
    input  wire [5:0]   sts_active_context_count_a,
    input  wire         sts_context_active_any_a,
    input  wire         sts_context_error_any_a,
    input  wire         sts_ingress_busy_a,
    input  wire         sts_axi_read_busy_a,
    input  wire         sts_sram_write_busy_a,
    input  wire         sts_sram_read_busy_a,
    input  wire [1:0]   sts_last_drop_class_a,
    input  wire [5:0]   sts_last_drop_reason_a,
    input  wire [3:0]   sts_last_error_context_id_a,

    output reg          sts_descriptor_available_p,
    output reg          sts_descriptor_queue_full_p,
    output reg  [5:0]   sts_active_context_count_p,
    output reg          sts_context_active_any_p,
    output reg          sts_context_error_any_p,
    output reg          sts_ingress_busy_p,
    output reg          sts_axi_read_busy_p,
    output reg          sts_sram_write_busy_p,
    output reg          sts_sram_read_busy_p,
    output reg  [1:0]   sts_last_drop_class_p,
    output reg  [5:0]   sts_last_drop_reason_p,
    output reg  [3:0]   sts_last_error_context_id_p,

    // ------------------------------------------------------------------
    // axi_aclk -> pclk: multi-bit read words (req/ack handshake)
    // ------------------------------------------------------------------
    input  wire [31:0]  cnt_block_a,
    input  wire [31:0]  ctx_state_a,
    input  wire [31:0]  desc_word_a,
    input  wire [31:0]  debug_ctx_a,

    output reg  [31:0]  cnt_block_p,
    output reg  [31:0]  ctx_state_p,
    output reg  [31:0]  desc_word_p,
    output reg  [31:0]  debug_ctx_p
);

    // ====================================================================
    // SECTION 1: pclk -> axi_aclk  level synchronizers (2-FF) for cfg_*
    //
    // Multi-bit config buses are sampled quasi-statically from APB writes;
    // each bit is independently 2-FF synchronized.  Glitch across bits is
    // acceptable for config registers (level, not transaction coherent).
    // ====================================================================

    // 1-bit cfg levels
    reg cfg_enable_ff1,                    cfg_enable_ff2;
    reg cfg_drop_when_disabled_ff1,        cfg_drop_when_disabled_ff2;
    reg cfg_dest_filter_enable_ff1,        cfg_dest_filter_enable_ff2;
    reg cfg_accept_broadcast_eid_ff1,      cfg_accept_broadcast_eid_ff2;
    reg cfg_accept_null_eid_ff1,           cfg_accept_null_eid_ff2;
    reg cfg_raw_sram_debug_read_enable_ff1,cfg_raw_sram_debug_read_enable_ff2;

    // multi-bit cfg levels (each bit independently synchronised)
    reg [7:0]   cfg_local_eid_ff1,              cfg_local_eid_ff2;
    reg [7:0]   cfg_debug_context_select_ff1,   cfg_debug_context_select_ff2;
    reg [12:0]  cfg_tu_bytes_ff1,               cfg_tu_bytes_ff2;
    reg [12:0]  cfg_max_message_bytes_ff1,       cfg_max_message_bytes_ff2;
    reg [23:0]  cfg_timeout_cycles_ff1,          cfg_timeout_cycles_ff2;
    reg [15:0]  cfg_sram_base_ff1,              cfg_sram_base_ff2;
    reg [15:0]  cfg_sram_limit_ff1,             cfg_sram_limit_ff2;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            cfg_enable_ff1                     <= 1'b0;
            cfg_enable_ff2                     <= 1'b0;
            cfg_drop_when_disabled_ff1         <= 1'b0;
            cfg_drop_when_disabled_ff2         <= 1'b0;
            cfg_dest_filter_enable_ff1         <= 1'b0;
            cfg_dest_filter_enable_ff2         <= 1'b0;
            cfg_accept_broadcast_eid_ff1       <= 1'b0;
            cfg_accept_broadcast_eid_ff2       <= 1'b0;
            cfg_accept_null_eid_ff1            <= 1'b0;
            cfg_accept_null_eid_ff2            <= 1'b0;
            cfg_raw_sram_debug_read_enable_ff1 <= 1'b0;
            cfg_raw_sram_debug_read_enable_ff2 <= 1'b0;
            cfg_local_eid_ff1                  <= 8'd0;
            cfg_local_eid_ff2                  <= 8'd0;
            cfg_debug_context_select_ff1       <= 8'd0;
            cfg_debug_context_select_ff2       <= 8'd0;
            cfg_tu_bytes_ff1                   <= 13'd0;
            cfg_tu_bytes_ff2                   <= 13'd0;
            cfg_max_message_bytes_ff1          <= 13'd0;
            cfg_max_message_bytes_ff2          <= 13'd0;
            cfg_timeout_cycles_ff1             <= 24'd0;
            cfg_timeout_cycles_ff2             <= 24'd0;
            cfg_sram_base_ff1                  <= {SRAM_ADDR_WIDTH{1'b0}};
            cfg_sram_base_ff2                  <= {SRAM_ADDR_WIDTH{1'b0}};
            cfg_sram_limit_ff1                 <= {SRAM_ADDR_WIDTH{1'b0}};
            cfg_sram_limit_ff2                 <= {SRAM_ADDR_WIDTH{1'b0}};
        end else begin
            // FF stage 1 (sample from pclk domain)
            cfg_enable_ff1                     <= cfg_enable_p;
            cfg_drop_when_disabled_ff1         <= cfg_drop_when_disabled_p;
            cfg_dest_filter_enable_ff1         <= cfg_dest_filter_enable_p;
            cfg_accept_broadcast_eid_ff1       <= cfg_accept_broadcast_eid_p;
            cfg_accept_null_eid_ff1            <= cfg_accept_null_eid_p;
            cfg_raw_sram_debug_read_enable_ff1 <= cfg_raw_sram_debug_read_enable_p;
            cfg_local_eid_ff1                  <= cfg_local_eid_p;
            cfg_debug_context_select_ff1       <= cfg_debug_context_select_p;
            cfg_tu_bytes_ff1                   <= cfg_tu_bytes_p;
            cfg_max_message_bytes_ff1          <= cfg_max_message_bytes_p;
            cfg_timeout_cycles_ff1             <= cfg_timeout_cycles_p;
            cfg_sram_base_ff1                  <= cfg_sram_base_p;
            cfg_sram_limit_ff1                 <= cfg_sram_limit_p;
            // FF stage 2 (stable output to axi_aclk consumers)
            cfg_enable_ff2                     <= cfg_enable_ff1;
            cfg_drop_when_disabled_ff2         <= cfg_drop_when_disabled_ff1;
            cfg_dest_filter_enable_ff2         <= cfg_dest_filter_enable_ff1;
            cfg_accept_broadcast_eid_ff2       <= cfg_accept_broadcast_eid_ff1;
            cfg_accept_null_eid_ff2            <= cfg_accept_null_eid_ff1;
            cfg_raw_sram_debug_read_enable_ff2 <= cfg_raw_sram_debug_read_enable_ff1;
            cfg_local_eid_ff2                  <= cfg_local_eid_ff1;
            cfg_debug_context_select_ff2       <= cfg_debug_context_select_ff1;
            cfg_tu_bytes_ff2                   <= cfg_tu_bytes_ff1;
            cfg_max_message_bytes_ff2          <= cfg_max_message_bytes_ff1;
            cfg_timeout_cycles_ff2             <= cfg_timeout_cycles_ff1;
            cfg_sram_base_ff2                  <= cfg_sram_base_ff1;
            cfg_sram_limit_ff2                 <= cfg_sram_limit_ff1;
        end
    end

    // Drive synchronized cfg outputs
    always @(*) begin
        cfg_enable_a                     = cfg_enable_ff2;
        cfg_drop_when_disabled_a         = cfg_drop_when_disabled_ff2;
        cfg_dest_filter_enable_a         = cfg_dest_filter_enable_ff2;
        cfg_accept_broadcast_eid_a       = cfg_accept_broadcast_eid_ff2;
        cfg_accept_null_eid_a            = cfg_accept_null_eid_ff2;
        cfg_raw_sram_debug_read_enable_a = cfg_raw_sram_debug_read_enable_ff2;
        cfg_local_eid_a                  = cfg_local_eid_ff2;
        cfg_debug_context_select_a       = cfg_debug_context_select_ff2;
        cfg_tu_bytes_a                   = cfg_tu_bytes_ff2;
        cfg_max_message_bytes_a          = cfg_max_message_bytes_ff2;
        cfg_timeout_cycles_a             = cfg_timeout_cycles_ff2;
        cfg_sram_base_a                  = cfg_sram_base_ff2;
        cfg_sram_limit_a                 = cfg_sram_limit_ff2;
    end

    // ====================================================================
    // SECTION 2: pclk -> axi_aclk  pulse synchronizers for cmd_*
    //
    // Scheme: toggle in pclk on each pulse; 2-FF sync in axi_aclk;
    // re-edge detect produces a single axi_aclk-wide output pulse.
    // ====================================================================

    // -- cmd_soft_reset --
    reg  cmd_soft_reset_tog_p;
    reg  cmd_soft_reset_sync1_a, cmd_soft_reset_sync2_a, cmd_soft_reset_prev_a;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) cmd_soft_reset_tog_p <= 1'b0;
        else if (cmd_soft_reset_p) cmd_soft_reset_tog_p <= ~cmd_soft_reset_tog_p;
    end

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            cmd_soft_reset_sync1_a <= 1'b0;
            cmd_soft_reset_sync2_a <= 1'b0;
            cmd_soft_reset_prev_a  <= 1'b0;
            cmd_soft_reset_a       <= 1'b0;
        end else begin
            cmd_soft_reset_sync1_a <= cmd_soft_reset_tog_p;
            cmd_soft_reset_sync2_a <= cmd_soft_reset_sync1_a;
            cmd_soft_reset_prev_a  <= cmd_soft_reset_sync2_a;
            cmd_soft_reset_a       <= cmd_soft_reset_sync2_a ^ cmd_soft_reset_prev_a;
        end
    end

    // -- cmd_descriptor_pop --
    reg  cmd_descriptor_pop_tog_p;
    reg  cmd_descriptor_pop_sync1_a, cmd_descriptor_pop_sync2_a, cmd_descriptor_pop_prev_a;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) cmd_descriptor_pop_tog_p <= 1'b0;
        else if (cmd_descriptor_pop_p) cmd_descriptor_pop_tog_p <= ~cmd_descriptor_pop_tog_p;
    end

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            cmd_descriptor_pop_sync1_a <= 1'b0;
            cmd_descriptor_pop_sync2_a <= 1'b0;
            cmd_descriptor_pop_prev_a  <= 1'b0;
            cmd_descriptor_pop_a       <= 1'b0;
        end else begin
            cmd_descriptor_pop_sync1_a <= cmd_descriptor_pop_tog_p;
            cmd_descriptor_pop_sync2_a <= cmd_descriptor_pop_sync1_a;
            cmd_descriptor_pop_prev_a  <= cmd_descriptor_pop_sync2_a;
            cmd_descriptor_pop_a       <= cmd_descriptor_pop_sync2_a ^ cmd_descriptor_pop_prev_a;
        end
    end

    // -- cmd_counter_clear --
    reg  cmd_counter_clear_tog_p;
    reg  cmd_counter_clear_sync1_a, cmd_counter_clear_sync2_a, cmd_counter_clear_prev_a;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) cmd_counter_clear_tog_p <= 1'b0;
        else if (cmd_counter_clear_p) cmd_counter_clear_tog_p <= ~cmd_counter_clear_tog_p;
    end

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            cmd_counter_clear_sync1_a <= 1'b0;
            cmd_counter_clear_sync2_a <= 1'b0;
            cmd_counter_clear_prev_a  <= 1'b0;
            cmd_counter_clear_a       <= 1'b0;
        end else begin
            cmd_counter_clear_sync1_a <= cmd_counter_clear_tog_p;
            cmd_counter_clear_sync2_a <= cmd_counter_clear_sync1_a;
            cmd_counter_clear_prev_a  <= cmd_counter_clear_sync2_a;
            cmd_counter_clear_a       <= cmd_counter_clear_sync2_a ^ cmd_counter_clear_prev_a;
        end
    end

    // ====================================================================
    // SECTION 3: axi_aclk -> pclk  pulse synchronizers for evt_*
    //
    // Same toggle/2-FF/re-edge scheme, reversed domain.
    // ====================================================================

    // -- evt_descriptor_ready --
    reg  evt_descriptor_ready_tog_a;
    reg  evt_descriptor_ready_sync1_p, evt_descriptor_ready_sync2_p, evt_descriptor_ready_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_descriptor_ready_tog_a <= 1'b0;
        else if (evt_descriptor_ready_a) evt_descriptor_ready_tog_a <= ~evt_descriptor_ready_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_descriptor_ready_sync1_p <= 1'b0;
            evt_descriptor_ready_sync2_p <= 1'b0;
            evt_descriptor_ready_prev_p  <= 1'b0;
            evt_descriptor_ready_p       <= 1'b0;
        end else begin
            evt_descriptor_ready_sync1_p <= evt_descriptor_ready_tog_a;
            evt_descriptor_ready_sync2_p <= evt_descriptor_ready_sync1_p;
            evt_descriptor_ready_prev_p  <= evt_descriptor_ready_sync2_p;
            evt_descriptor_ready_p       <= evt_descriptor_ready_sync2_p ^ evt_descriptor_ready_prev_p;
        end
    end

    // -- evt_packet_drop --
    reg  evt_packet_drop_tog_a;
    reg  evt_packet_drop_sync1_p, evt_packet_drop_sync2_p, evt_packet_drop_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_packet_drop_tog_a <= 1'b0;
        else if (evt_packet_drop_a) evt_packet_drop_tog_a <= ~evt_packet_drop_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_packet_drop_sync1_p <= 1'b0;
            evt_packet_drop_sync2_p <= 1'b0;
            evt_packet_drop_prev_p  <= 1'b0;
            evt_packet_drop_p       <= 1'b0;
        end else begin
            evt_packet_drop_sync1_p <= evt_packet_drop_tog_a;
            evt_packet_drop_sync2_p <= evt_packet_drop_sync1_p;
            evt_packet_drop_prev_p  <= evt_packet_drop_sync2_p;
            evt_packet_drop_p       <= evt_packet_drop_sync2_p ^ evt_packet_drop_prev_p;
        end
    end

    // -- evt_assembly_drop --
    reg  evt_assembly_drop_tog_a;
    reg  evt_assembly_drop_sync1_p, evt_assembly_drop_sync2_p, evt_assembly_drop_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_assembly_drop_tog_a <= 1'b0;
        else if (evt_assembly_drop_a) evt_assembly_drop_tog_a <= ~evt_assembly_drop_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_assembly_drop_sync1_p <= 1'b0;
            evt_assembly_drop_sync2_p <= 1'b0;
            evt_assembly_drop_prev_p  <= 1'b0;
            evt_assembly_drop_p       <= 1'b0;
        end else begin
            evt_assembly_drop_sync1_p <= evt_assembly_drop_tog_a;
            evt_assembly_drop_sync2_p <= evt_assembly_drop_sync1_p;
            evt_assembly_drop_prev_p  <= evt_assembly_drop_sync2_p;
            evt_assembly_drop_p       <= evt_assembly_drop_sync2_p ^ evt_assembly_drop_prev_p;
        end
    end

    // -- evt_context_timeout --
    reg  evt_context_timeout_tog_a;
    reg  evt_context_timeout_sync1_p, evt_context_timeout_sync2_p, evt_context_timeout_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_context_timeout_tog_a <= 1'b0;
        else if (evt_context_timeout_a) evt_context_timeout_tog_a <= ~evt_context_timeout_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_context_timeout_sync1_p <= 1'b0;
            evt_context_timeout_sync2_p <= 1'b0;
            evt_context_timeout_prev_p  <= 1'b0;
            evt_context_timeout_p       <= 1'b0;
        end else begin
            evt_context_timeout_sync1_p <= evt_context_timeout_tog_a;
            evt_context_timeout_sync2_p <= evt_context_timeout_sync1_p;
            evt_context_timeout_prev_p  <= evt_context_timeout_sync2_p;
            evt_context_timeout_p       <= evt_context_timeout_sync2_p ^ evt_context_timeout_prev_p;
        end
    end

    // -- evt_sram_overflow --
    reg  evt_sram_overflow_tog_a;
    reg  evt_sram_overflow_sync1_p, evt_sram_overflow_sync2_p, evt_sram_overflow_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_sram_overflow_tog_a <= 1'b0;
        else if (evt_sram_overflow_a) evt_sram_overflow_tog_a <= ~evt_sram_overflow_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_sram_overflow_sync1_p <= 1'b0;
            evt_sram_overflow_sync2_p <= 1'b0;
            evt_sram_overflow_prev_p  <= 1'b0;
            evt_sram_overflow_p       <= 1'b0;
        end else begin
            evt_sram_overflow_sync1_p <= evt_sram_overflow_tog_a;
            evt_sram_overflow_sync2_p <= evt_sram_overflow_sync1_p;
            evt_sram_overflow_prev_p  <= evt_sram_overflow_sync2_p;
            evt_sram_overflow_p       <= evt_sram_overflow_sync2_p ^ evt_sram_overflow_prev_p;
        end
    end

    // -- evt_descriptor_queue_full --
    // Source is a level (descriptor_full); edge-detect in axi_aclk to produce
    // a pulse before toggling across the domain.
    reg  evt_descriptor_queue_full_prev_a;
    reg  evt_descriptor_queue_full_tog_a;
    reg  evt_descriptor_queue_full_sync1_p, evt_descriptor_queue_full_sync2_p;
    reg  evt_descriptor_queue_full_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            evt_descriptor_queue_full_prev_a <= 1'b0;
            evt_descriptor_queue_full_tog_a  <= 1'b0;
        end else begin
            evt_descriptor_queue_full_prev_a <= evt_descriptor_queue_full_a;
            if (evt_descriptor_queue_full_a & ~evt_descriptor_queue_full_prev_a)
                evt_descriptor_queue_full_tog_a <= ~evt_descriptor_queue_full_tog_a;
        end
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_descriptor_queue_full_sync1_p <= 1'b0;
            evt_descriptor_queue_full_sync2_p <= 1'b0;
            evt_descriptor_queue_full_prev_p  <= 1'b0;
            evt_descriptor_queue_full_p       <= 1'b0;
        end else begin
            evt_descriptor_queue_full_sync1_p <= evt_descriptor_queue_full_tog_a;
            evt_descriptor_queue_full_sync2_p <= evt_descriptor_queue_full_sync1_p;
            evt_descriptor_queue_full_prev_p  <= evt_descriptor_queue_full_sync2_p;
            evt_descriptor_queue_full_p       <= evt_descriptor_queue_full_sync2_p ^ evt_descriptor_queue_full_prev_p;
        end
    end

    // -- evt_axi_write_malformed --
    reg  evt_axi_write_malformed_tog_a;
    reg  evt_axi_write_malformed_sync1_p, evt_axi_write_malformed_sync2_p, evt_axi_write_malformed_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_axi_write_malformed_tog_a <= 1'b0;
        else if (evt_axi_write_malformed_a) evt_axi_write_malformed_tog_a <= ~evt_axi_write_malformed_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_axi_write_malformed_sync1_p <= 1'b0;
            evt_axi_write_malformed_sync2_p <= 1'b0;
            evt_axi_write_malformed_prev_p  <= 1'b0;
            evt_axi_write_malformed_p       <= 1'b0;
        end else begin
            evt_axi_write_malformed_sync1_p <= evt_axi_write_malformed_tog_a;
            evt_axi_write_malformed_sync2_p <= evt_axi_write_malformed_sync1_p;
            evt_axi_write_malformed_prev_p  <= evt_axi_write_malformed_sync2_p;
            evt_axi_write_malformed_p       <= evt_axi_write_malformed_sync2_p ^ evt_axi_write_malformed_prev_p;
        end
    end

    // -- evt_axi_read_error --
    reg  evt_axi_read_error_tog_a;
    reg  evt_axi_read_error_sync1_p, evt_axi_read_error_sync2_p, evt_axi_read_error_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_axi_read_error_tog_a <= 1'b0;
        else if (evt_axi_read_error_a) evt_axi_read_error_tog_a <= ~evt_axi_read_error_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_axi_read_error_sync1_p <= 1'b0;
            evt_axi_read_error_sync2_p <= 1'b0;
            evt_axi_read_error_prev_p  <= 1'b0;
            evt_axi_read_error_p       <= 1'b0;
        end else begin
            evt_axi_read_error_sync1_p <= evt_axi_read_error_tog_a;
            evt_axi_read_error_sync2_p <= evt_axi_read_error_sync1_p;
            evt_axi_read_error_prev_p  <= evt_axi_read_error_sync2_p;
            evt_axi_read_error_p       <= evt_axi_read_error_sync2_p ^ evt_axi_read_error_prev_p;
        end
    end

    // -- evt_fatal_internal_error --
    reg  evt_fatal_internal_error_tog_a;
    reg  evt_fatal_internal_error_sync1_p, evt_fatal_internal_error_sync2_p, evt_fatal_internal_error_prev_p;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) evt_fatal_internal_error_tog_a <= 1'b0;
        else if (evt_fatal_internal_error_a) evt_fatal_internal_error_tog_a <= ~evt_fatal_internal_error_tog_a;
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            evt_fatal_internal_error_sync1_p <= 1'b0;
            evt_fatal_internal_error_sync2_p <= 1'b0;
            evt_fatal_internal_error_prev_p  <= 1'b0;
            evt_fatal_internal_error_p       <= 1'b0;
        end else begin
            evt_fatal_internal_error_sync1_p <= evt_fatal_internal_error_tog_a;
            evt_fatal_internal_error_sync2_p <= evt_fatal_internal_error_sync1_p;
            evt_fatal_internal_error_prev_p  <= evt_fatal_internal_error_sync2_p;
            evt_fatal_internal_error_p       <= evt_fatal_internal_error_sync2_p ^ evt_fatal_internal_error_prev_p;
        end
    end

    // ====================================================================
    // SECTION 4: axi_aclk -> pclk  level synchronizers (2-FF) for sts_*
    // ====================================================================

    // 1-bit sts levels
    reg sts_descriptor_available_ff1,   sts_descriptor_available_ff2;
    reg sts_descriptor_queue_full_ff1,  sts_descriptor_queue_full_ff2;
    reg sts_context_active_any_ff1,     sts_context_active_any_ff2;
    reg sts_context_error_any_ff1,      sts_context_error_any_ff2;
    reg sts_ingress_busy_ff1,           sts_ingress_busy_ff2;
    reg sts_axi_read_busy_ff1,          sts_axi_read_busy_ff2;
    reg sts_sram_write_busy_ff1,        sts_sram_write_busy_ff2;
    reg sts_sram_read_busy_ff1,         sts_sram_read_busy_ff2;

    // multi-bit sts levels
    reg [5:0] sts_active_context_count_ff1,    sts_active_context_count_ff2;
    reg [1:0] sts_last_drop_class_ff1,         sts_last_drop_class_ff2;
    reg [5:0] sts_last_drop_reason_ff1,        sts_last_drop_reason_ff2;
    reg [3:0] sts_last_error_context_id_ff1,   sts_last_error_context_id_ff2;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            sts_descriptor_available_ff1   <= 1'b0;
            sts_descriptor_available_ff2   <= 1'b0;
            sts_descriptor_queue_full_ff1  <= 1'b0;
            sts_descriptor_queue_full_ff2  <= 1'b0;
            sts_context_active_any_ff1     <= 1'b0;
            sts_context_active_any_ff2     <= 1'b0;
            sts_context_error_any_ff1      <= 1'b0;
            sts_context_error_any_ff2      <= 1'b0;
            sts_ingress_busy_ff1           <= 1'b0;
            sts_ingress_busy_ff2           <= 1'b0;
            sts_axi_read_busy_ff1          <= 1'b0;
            sts_axi_read_busy_ff2          <= 1'b0;
            sts_sram_write_busy_ff1        <= 1'b0;
            sts_sram_write_busy_ff2        <= 1'b0;
            sts_sram_read_busy_ff1         <= 1'b0;
            sts_sram_read_busy_ff2         <= 1'b0;
            sts_active_context_count_ff1   <= 6'd0;
            sts_active_context_count_ff2   <= 6'd0;
            sts_last_drop_class_ff1        <= 2'd0;
            sts_last_drop_class_ff2        <= 2'd0;
            sts_last_drop_reason_ff1       <= 6'd0;
            sts_last_drop_reason_ff2       <= 6'd0;
            sts_last_error_context_id_ff1  <= 4'd0;
            sts_last_error_context_id_ff2  <= 4'd0;
        end else begin
            // FF stage 1 (sample from axi_aclk domain)
            sts_descriptor_available_ff1   <= sts_descriptor_available_a;
            sts_descriptor_queue_full_ff1  <= sts_descriptor_queue_full_a;
            sts_context_active_any_ff1     <= sts_context_active_any_a;
            sts_context_error_any_ff1      <= sts_context_error_any_a;
            sts_ingress_busy_ff1           <= sts_ingress_busy_a;
            sts_axi_read_busy_ff1          <= sts_axi_read_busy_a;
            sts_sram_write_busy_ff1        <= sts_sram_write_busy_a;
            sts_sram_read_busy_ff1         <= sts_sram_read_busy_a;
            sts_active_context_count_ff1   <= sts_active_context_count_a;
            sts_last_drop_class_ff1        <= sts_last_drop_class_a;
            sts_last_drop_reason_ff1       <= sts_last_drop_reason_a;
            sts_last_error_context_id_ff1  <= sts_last_error_context_id_a;
            // FF stage 2 (stable output to pclk consumers)
            sts_descriptor_available_ff2   <= sts_descriptor_available_ff1;
            sts_descriptor_queue_full_ff2  <= sts_descriptor_queue_full_ff1;
            sts_context_active_any_ff2     <= sts_context_active_any_ff1;
            sts_context_error_any_ff2      <= sts_context_error_any_ff1;
            sts_ingress_busy_ff2           <= sts_ingress_busy_ff1;
            sts_axi_read_busy_ff2          <= sts_axi_read_busy_ff1;
            sts_sram_write_busy_ff2        <= sts_sram_write_busy_ff1;
            sts_sram_read_busy_ff2         <= sts_sram_read_busy_ff1;
            sts_active_context_count_ff2   <= sts_active_context_count_ff1;
            sts_last_drop_class_ff2        <= sts_last_drop_class_ff1;
            sts_last_drop_reason_ff2       <= sts_last_drop_reason_ff1;
            sts_last_error_context_id_ff2  <= sts_last_error_context_id_ff1;
        end
    end

    // Drive synchronized sts outputs
    always @(*) begin
        sts_descriptor_available_p   = sts_descriptor_available_ff2;
        sts_descriptor_queue_full_p  = sts_descriptor_queue_full_ff2;
        sts_context_active_any_p     = sts_context_active_any_ff2;
        sts_context_error_any_p      = sts_context_error_any_ff2;
        sts_ingress_busy_p           = sts_ingress_busy_ff2;
        sts_axi_read_busy_p          = sts_axi_read_busy_ff2;
        sts_sram_write_busy_p        = sts_sram_write_busy_ff2;
        sts_sram_read_busy_p         = sts_sram_read_busy_ff2;
        sts_active_context_count_p   = sts_active_context_count_ff2;
        sts_last_drop_class_p        = sts_last_drop_class_ff2;
        sts_last_drop_reason_p       = sts_last_drop_reason_ff2;
        sts_last_error_context_id_p  = sts_last_error_context_id_ff2;
    end

    // ====================================================================
    // SECTION 5: axi_aclk -> pclk  req/ack handshake for 4x32-bit words
    //
    // A single shared handshake serializes the four read words.
    // Protocol (all registers):
    //   axi side: detect req_p rising (synced) -> latch all four words ->
    //             assert ack_a -> wait for req_p to deassert -> deassert ack_a
    //   pclk side: pclk asserts req_p -> waits for ack_p rising ->
    //              captures latched words -> deasserts req_p
    //
    // The pclk side continuously re-samples; the handshake ensures the
    // capture register is stable before the pclk side reads it.
    // ====================================================================

    // pclk-side handshake control
    reg  hs_req_p;                          // request from pclk side
    reg  hs_ack_sync1_p, hs_ack_sync2_p;   // ack synchronized into pclk
    reg  hs_ack_prev_p;                     // previous ack for edge detect
    wire hs_ack_rise_p = hs_ack_sync2_p & ~hs_ack_prev_p;

    // axi-side handshake control
    reg  hs_req_sync1_a, hs_req_sync2_a;   // req synchronized into axi_aclk
    reg  hs_req_prev_a;                     // previous req for edge detect
    wire hs_req_rise_a = hs_req_sync2_a & ~hs_req_prev_a;
    reg  hs_ack_a;                          // ack driven from axi_aclk side

    // captured word registers (axi side, written on req rise)
    reg [31:0] cnt_block_cap_a;
    reg [31:0] ctx_state_cap_a;
    reg [31:0] desc_word_cap_a;
    reg [31:0] debug_ctx_cap_a;

    // synchronized capture registers visible to pclk (written on ack rise)
    reg [31:0] cnt_block_latch_p;
    reg [31:0] ctx_state_latch_p;
    reg [31:0] desc_word_latch_p;
    reg [31:0] debug_ctx_latch_p;

    // pclk-side: auto-cycle req to keep read words fresh
    // req is asserted when idle (not waiting for ack) then deasserted on ack
    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            hs_req_p        <= 1'b0;
            hs_ack_sync1_p  <= 1'b0;
            hs_ack_sync2_p  <= 1'b0;
            hs_ack_prev_p   <= 1'b0;
            cnt_block_p     <= 32'd0;
            ctx_state_p     <= 32'd0;
            desc_word_p     <= 32'd0;
            debug_ctx_p     <= 32'd0;
            cnt_block_latch_p <= 32'd0;
            ctx_state_latch_p <= 32'd0;
            desc_word_latch_p <= 32'd0;
            debug_ctx_latch_p <= 32'd0;
        end else begin
            // 2-FF sync of ack from axi side
            hs_ack_sync1_p <= hs_ack_a;
            hs_ack_sync2_p <= hs_ack_sync1_p;
            hs_ack_prev_p  <= hs_ack_sync2_p;

            // on ack rising edge: capture and deassert req
            if (hs_ack_rise_p) begin
                cnt_block_latch_p <= cnt_block_cap_a;
                ctx_state_latch_p <= ctx_state_cap_a;
                desc_word_latch_p <= desc_word_cap_a;
                debug_ctx_latch_p <= debug_ctx_cap_a;
                hs_req_p          <= 1'b0;
            end else if (!hs_req_p && !hs_ack_sync2_p) begin
                // re-assert req once ack is also gone (handshake complete)
                hs_req_p <= 1'b1;
            end

            // expose latched values
            cnt_block_p <= cnt_block_latch_p;
            ctx_state_p <= ctx_state_latch_p;
            desc_word_p <= desc_word_latch_p;
            debug_ctx_p <= debug_ctx_latch_p;
        end
    end

    // axi-side: respond to req, latch words, drive ack
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            hs_req_sync1_a  <= 1'b0;
            hs_req_sync2_a  <= 1'b0;
            hs_req_prev_a   <= 1'b0;
            hs_ack_a        <= 1'b0;
            cnt_block_cap_a <= 32'd0;
            ctx_state_cap_a <= 32'd0;
            desc_word_cap_a <= 32'd0;
            debug_ctx_cap_a <= 32'd0;
        end else begin
            // 2-FF sync of req from pclk side
            hs_req_sync1_a <= hs_req_p;
            hs_req_sync2_a <= hs_req_sync1_a;
            hs_req_prev_a  <= hs_req_sync2_a;

            // on req rising edge: latch data and assert ack
            if (hs_req_rise_a) begin
                cnt_block_cap_a <= cnt_block_a;
                ctx_state_cap_a <= ctx_state_a;
                desc_word_cap_a <= desc_word_a;
                debug_ctx_cap_a <= debug_ctx_a;
                hs_ack_a        <= 1'b1;
            end else if (!hs_req_sync2_a) begin
                // req gone: deassert ack to complete handshake
                hs_ack_a <= 1'b0;
            end
        end
    end

endmodule
`default_nettype wire
