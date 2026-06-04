// mctp_assembler_v3_context_table.sv
// Interleaved MCTP message-assembly context table for the MCTP assembler v3.
// Implements function_model.FM_ALLOC_CONTEXT + FM_APPEND plus the per-context
// fsm.context_fsm (IDLE / ASSEMBLING / ERROR / DONE_WAIT_DESCRIPTOR_POP):
//   - CONTEXT_COUNT independent contexts keyed by frag_assembly_key
//     (assembly_key = (source_eid<<4)|(tag_owner<<3)|message_tag)
//   - allocate on accepted SOM; append on matching SOM=0 packet with seq ok
//   - issue a per-packet handshaked payload-write request to the sram_packer
//   - push one completed descriptor to the descriptor_queue on a successful EOM
//   - own drop classification for the assembly path (PD_* pass-through priority,
//     then this stage's PD_*, then AD_* assembly drops)
//   - bump-allocate SRAM (sram_alloc_ptr) and hold the per-context byte write
//     pointer (ctx_payload_next_addr; its low 5 bits are the partial-word lane)
//   - run the multi-beat pack engine that writes the streamed payload bytes into
//     SRAM in <=32B-per-word chunks with no holes across beats and fragments
//   - expose STATUS aggregates and the debug_context_select CTX_STATE mirror
`default_nettype none
module mctp_assembler_v3_context_table #(
    parameter integer CONTEXT_COUNT            = 15,
    parameter integer TLP_HEADER_SNAPSHOT_BYTES = 16,
    parameter integer MAX_MESSAGE_BYTES        = 4096,
    parameter integer SRAM_ADDR_WIDTH          = 16,
    parameter integer AXI_DATA_WIDTH           = 256,
    parameter integer AXI_STRB_WIDTH           = 32,
    parameter integer TIMEOUT_COUNTER_WIDTH    = 24,
    parameter [1:0]   ASSEMBLING               = 2'd1,
    parameter [1:0]   DONE_WAIT_DESCRIPTOR_POP = 2'd3
) (
    input  wire                          axi_aclk,
    input  wire                          axi_aresetn,
    // ---- decoded MCTP fragment in (from mctp_decoder) -------------------
    input  wire                          frag_valid,
    input  wire [7:0]                    frag_source_eid,
    input  wire [7:0]                    frag_dest_eid,
    input  wire                          frag_tag_owner,
    input  wire [2:0]                    frag_message_tag,
    input  wire [1:0]                    frag_packet_seq,
    input  wire                          frag_som,
    input  wire                          frag_eom,
    input  wire [6:0]                    frag_message_type,
    input  wire [11:0]                   frag_assembly_key,
    input  wire [AXI_DATA_WIDTH-1:0]     frag_payload_word,
    input  wire [AXI_STRB_WIDTH-1:0]     frag_payload_strb,
    input  wire [12:0]                   frag_payload_bytes,
    input  wire [127:0]                  frag_first_header,
    input  wire [127:0]                  frag_last_header,
    input  wire [5:0]                    packet_drop_reason_in,
    // ---- configuration (from regfile via cdc_sync) ----------------------
    input  wire                          cfg_enable,
    input  wire                          cfg_drop_when_disabled,
    input  wire [15:0]                   cfg_sram_base,
    input  wire [15:0]                   cfg_sram_limit,
    input  wire [12:0]                   cfg_max_message_bytes,
    input  wire [23:0]                   cfg_timeout_cycles,
    // ---- downstream backpressure / retire -------------------------------
    input  wire                          descriptor_full,
    input  wire                          descriptor_pop,
    // context_id of the descriptor at the FIFO read head (descriptor_queue
    // rd_context_id); a pop consumes exactly this one descriptor, so only the
    // context it belongs to is retired (retire=1, pop=1, count-=1 stay aligned).
    input  wire [3:0]                    pop_context_id,
    // ---- payload write request to the sram_packer (handshaked) ----------
    output reg                           pack_wr_valid,
    input  wire                          pack_wr_ready,
    output reg  [AXI_DATA_WIDTH-1:0]     pack_wr_data,
    output reg  [AXI_STRB_WIDTH-1:0]     pack_wr_strb,
    output reg  [15:0]                   pack_wr_addr,
    output reg  [12:0]                   pack_wr_bytes,
    // ---- descriptor push to the descriptor_queue (on EOM) ---------------
    output reg                           descriptor_push,
    output reg  [15:0]                   desc_base_addr,
    output reg  [12:0]                   desc_payload_len,
    output reg  [7:0]                    desc_source_eid,
    output reg  [7:0]                    desc_dest_eid,
    output reg                           desc_tag_owner,
    output reg  [2:0]                    desc_message_tag,
    output reg  [6:0]                    desc_message_type,
    output reg  [1:0]                    desc_final_seq,
    output reg  [3:0]                    desc_context_id,
    output reg  [2:0]                    desc_completion_status,
    output reg  [15:0]                   desc_requester_id,
    output reg  [2:0]                    desc_routing_type,
    output reg  [127:0]                  desc_first_header,
    output reg  [127:0]                  desc_last_header,
    // ---- forwarded VDM descriptor sideband (from decoder) ---------------
    input  wire [15:0]                   frag_requester_id,
    input  wire [2:0]                    frag_routing_type,
    // ---- multi-beat payload stream in (PAYLOAD_STREAM_CONTRACT §4) -------
    // Lane-0-aligned payload beats for the in-flight accepted fragment; the
    // pack engine splits each beat into <=32B-per-word writes and walks the
    // per-context byte pointer so the FULL payload lands in SRAM with no holes.
    input  wire                          pl_beat_valid,
    input  wire [AXI_DATA_WIDTH-1:0]     pl_beat_data,
    input  wire [AXI_STRB_WIDTH-1:0]     pl_beat_strb,
    input  wire [5:0]                    pl_beat_bytes,
    input  wire                          pl_beat_first,
    input  wire                          pl_beat_last,
    output wire                          pl_beat_ready,
    // ---- drop / event reporting -----------------------------------------
    output reg                           packet_drop_pulse,
    output reg                           assembly_drop_pulse,
    output reg  [1:0]                    drop_class_o,
    output reg  [5:0]                    drop_reason_o,
    output reg                           sram_overflow_pulse,
    output reg                           timeout_pulse,
    // ---- STATUS aggregates ----------------------------------------------
    output reg  [4:0]                    active_context_count,
    output wire                          context_active_any,
    output wire                          context_error_any,
    output reg  [3:0]                    last_error_context_id,
    // ---- DEBUG_CTX / CTX_STATE mirror (selected slot) -------------------
    output reg  [1:0]                    ctx_state_sel,
    output reg  [11:0]                   ctx_key_sel,
    output reg  [1:0]                    ctx_expected_seq_sel,
    output reg  [12:0]                   ctx_payload_count_sel,
    input  wire [7:0]                    debug_context_select
);

    // ---- FSM state encoding (fsm.context_fsm) -------------------------------
    // state_0 IDLE, state_1 ASSEMBLING, state_2 ERROR, state_3 DONE_WAIT_*.
    localparam [1:0] CTX_IDLE  = 2'd0;
    localparam [1:0] CTX_ASM   = ASSEMBLING;               // 2'd1
    localparam [1:0] CTX_ERR   = 2'd2;
    localparam [1:0] CTX_DONE  = DONE_WAIT_DESCRIPTOR_POP;  // 2'd3

    // ---- drop reason code space (INTEGRATION_CONTRACT §4.2) -----------------
    localparam [5:0] PD_UNEXPECTED_MIDDLE_END = 6'd7;
    localparam [5:0] PD_BAD_OR_EXPIRED_TAG    = 6'd8;
    localparam [5:0] AD_DUPLICATE_SOM         = 6'd9;
    localparam [5:0] AD_SEQUENCE_MISMATCH     = 6'd10;
    localparam [5:0] AD_MESSAGE_OVERFLOW      = 6'd11;
    localparam [5:0] AD_SRAM_OVERFLOW         = 6'd12;
    localparam [5:0] AD_DESCRIPTOR_FULL       = 6'd13;
    localparam [5:0] AD_TIMEOUT               = 6'd14;
    localparam [5:0] PD_DISABLED_DROP_MODE    = 6'd1;

    // drop_class encoding (drop_class_o → top last_drop_class)
    localparam [1:0] DC_NONE   = 2'd0;
    localparam [1:0] DC_PACKET = 2'd1;
    localparam [1:0] DC_ASM    = 2'd2;

    localparam [2:0] CS_OK = 3'd0;  // completion_status: assembled OK at EOM

`define MCTP_V3_RESET_CONTEXT(IDX) \
        ctx_state[IDX]        <= CTX_IDLE; \
        ctx_valid[IDX]        <= 1'b0; \
        ctx_key[IDX]          <= 12'd0; \
        ctx_source_eid[IDX]   <= 8'd0; \
        ctx_dest_eid[IDX]     <= 8'd0; \
        ctx_tag_owner[IDX]    <= 1'b0; \
        ctx_message_tag[IDX]  <= 3'd0; \
        ctx_message_type[IDX] <= 7'd0; \
        ctx_expected_seq[IDX] <= 2'd0; \
        ctx_payload_base[IDX] <= 16'd0; \
        ctx_payload_next[IDX] <= 16'd0; \
        ctx_payload_cnt[IDX]  <= 13'd0; \
        ctx_first_header[IDX] <= {HEADER_SNAPSHOT_BITS{1'b0}}; \
        ctx_requester_id[IDX] <= 16'd0; \
        ctx_routing_type[IDX] <= 3'd0; \
        ctx_timeout_age[IDX]  <= {TIMEOUT_COUNTER_WIDTH{1'b0}};

`define MCTP_V3_AGE_CONTEXT(IDX) \
        if (ctx_valid[IDX] && (ctx_state[IDX] == CTX_ASM)) begin \
            if (ctx_timeout_age[IDX] < cfg_timeout_cycles) begin \
                ctx_timeout_age[IDX] <= ctx_timeout_age[IDX] + \
                                        {{(TIMEOUT_COUNTER_WIDTH-1){1'b0}}, 1'b1}; \
            end \
        end

// Publish the descriptor that was deferred at EOM, once the pack engine has
// drained the packet's payload beats (PAYLOAD_STREAM_CONTRACT §4.6).
`define MCTP_V3_FIRE_DEFERRED_DESC \
        descriptor_push        <= 1'b1; \
        desc_base_addr         <= dp_base_addr; \
        desc_payload_len       <= dp_payload_len; \
        desc_source_eid        <= dp_source_eid; \
        desc_dest_eid          <= dp_dest_eid; \
        desc_tag_owner         <= dp_tag_owner; \
        desc_message_tag       <= dp_message_tag; \
        desc_message_type      <= dp_message_type; \
        desc_final_seq         <= dp_final_seq; \
        desc_context_id        <= dp_context_id; \
        desc_completion_status <= dp_completion_status; \
        desc_requester_id      <= dp_requester_id; \
        desc_routing_type      <= dp_routing_type; \
        desc_first_header      <= dp_first_header; \
        desc_last_header       <= dp_last_header; \
        desc_pending           <= 1'b0;

    // First/last header snapshot width in bits (TLP_HEADER_SNAPSHOT_BYTES*8);
    // fixed at 128 by the frozen descriptor/header ports for the 16B snapshot.
    localparam integer HEADER_SNAPSHOT_BITS = TLP_HEADER_SNAPSHOT_BYTES * 8;
    // Effective message-byte budget = min(parameter cap, runtime cfg cap).
    wire [12:0] msg_byte_budget =
        (cfg_max_message_bytes <= MAX_MESSAGE_BYTES[12:0]) ? cfg_max_message_bytes
                                                           : MAX_MESSAGE_BYTES[12:0];

    // -------------------------------------------------------------------------
    // Per-context architectural state (flattened arrays; no SystemVerilog
    // structs/interfaces per the coding-style contract).
    // -------------------------------------------------------------------------
    reg  [1:0]   ctx_state        [0:CONTEXT_COUNT-1];
    reg          ctx_valid        [0:CONTEXT_COUNT-1];
    reg  [11:0]  ctx_key          [0:CONTEXT_COUNT-1];
    reg  [7:0]   ctx_source_eid   [0:CONTEXT_COUNT-1];
    reg  [7:0]   ctx_dest_eid     [0:CONTEXT_COUNT-1];
    reg          ctx_tag_owner    [0:CONTEXT_COUNT-1];
    reg  [2:0]   ctx_message_tag  [0:CONTEXT_COUNT-1];
    reg  [6:0]   ctx_message_type [0:CONTEXT_COUNT-1];
    reg  [1:0]   ctx_expected_seq [0:CONTEXT_COUNT-1];
    reg  [15:0]  ctx_payload_base [0:CONTEXT_COUNT-1];
    // ctx_payload_next is the running BYTE write pointer and the SINGLE source of
    // truth for the SRAM address AND the partial-word lane (lane = addr & 31): the
    // sram_packer derives word_addr/lane from it, so no separate partial-lane reg
    // is kept (the old ctx_partial_next_lane was redundant with addr[4:0]).
    reg  [15:0]  ctx_payload_next [0:CONTEXT_COUNT-1];
    reg  [12:0]  ctx_payload_cnt  [0:CONTEXT_COUNT-1];
    reg  [HEADER_SNAPSHOT_BITS-1:0] ctx_first_header [0:CONTEXT_COUNT-1];
    reg  [15:0]  ctx_requester_id [0:CONTEXT_COUNT-1];
    reg  [2:0]   ctx_routing_type [0:CONTEXT_COUNT-1];
    reg  [TIMEOUT_COUNTER_WIDTH-1:0] ctx_timeout_age [0:CONTEXT_COUNT-1];

    // Global bump allocator + status registers (function_model state_variables).
    // sram_alloc_ptr is the linear allocator in [sram_base, sram_limit); it is
    // (re)seeded from cfg_sram_base while the table is fully idle so a config
    // change to SRAM_BASE takes effect before any context is allocated.
    reg  [SRAM_ADDR_WIDTH-1:0] sram_alloc_ptr;
    reg                        alloc_seeded;  // sram_alloc_ptr has tracked cfg

    // -------------------------------------------------------------------------
    // Multi-beat pack engine (PAYLOAD_STREAM_CONTRACT §4.3/§4.4). Consumes the
    // lane-0-aligned pl_beat_* stream and issues <=32B-per-256-bit-word pack
    // writes to the sram_packer, walking the per-context byte pointer
    // (ctx_payload_next) so the full payload lands with no
    // holes across beats AND fragments. One straddling beat needs up to TWO
    // sequential writes (A into the current partial word, B into the next word),
    // serialized behind pack_wr_ready by a 3-state per-beat FSM.
    localparam [1:0] S_BEAT_IDLE = 2'd0;  // ready for a new payload beat
    localparam [1:0] S_WRA       = 2'd1;  // chunk-A write outstanding
    localparam [1:0] S_WRB       = 2'd2;  // chunk-B write outstanding
    reg  [1:0]  pack_state;
    reg  [3:0]  stream_ctx_id;            // context the in-flight stream targets
    reg         stream_write;             // 1=accepted (write SRAM); 0=dropped (drain)
    reg         stream_armed;             // stream config latched & ready to consume
    reg  [AXI_DATA_WIDTH-1:0] pack_data_q; // beat data held for chunk-B (pre-shifted)
    reg  [5:0]  chunk1_q;                 // chunk-B byte count held across S_WRA
    reg  [15:0] pack_addrB_q;             // chunk-B byte start address (32B-aligned)
    reg         pl_last_q;                // in-flight beat was the stream's last

    // Deferred-descriptor state (PAYLOAD_STREAM_CONTRACT §4.6): an EOM whose
    // payload streams must not publish its descriptor until the pack engine has
    // drained every beat, so a readback after descriptor_valid sees the full
    // bytes in SRAM. The desc_* field set is latched at the EOM metadata cycle
    // and the push fires when the stream ends (pack engine idle, last consumed).
    reg         desc_pending;
    reg  [15:0] dp_base_addr;
    reg  [12:0] dp_payload_len;
    reg  [7:0]  dp_source_eid;
    reg  [7:0]  dp_dest_eid;
    reg         dp_tag_owner;
    reg  [2:0]  dp_message_tag;
    reg  [6:0]  dp_message_type;
    reg  [1:0]  dp_final_seq;
    reg  [3:0]  dp_context_id;
    reg  [2:0]  dp_completion_status;
    reg  [15:0] dp_requester_id;
    reg  [2:0]  dp_routing_type;
    reg  [127:0] dp_first_header;
    reg  [127:0] dp_last_header;

    // -------------------------------------------------------------------------
    // Combinational lookup: match the incoming fragment to an existing context
    // by assembly_key, and find the lowest free slot for allocation.
    // -------------------------------------------------------------------------
    reg          match_found;
    reg  [3:0]   match_idx;
    reg          free_found;       // free_slot_available
    reg  [3:0]   free_idx;

    always @(*) begin
        match_found = 1'b0;
        match_idx   = 4'd0;
        free_found  = 1'b0;
        free_idx    = 4'd0;
        if (ctx_valid[0] && (ctx_state[0] == CTX_ASM) && (ctx_key[0] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd0; end
        else if (ctx_valid[1] && (ctx_state[1] == CTX_ASM) && (ctx_key[1] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd1; end
        else if (ctx_valid[2] && (ctx_state[2] == CTX_ASM) && (ctx_key[2] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd2; end
        else if (ctx_valid[3] && (ctx_state[3] == CTX_ASM) && (ctx_key[3] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd3; end
        else if (ctx_valid[4] && (ctx_state[4] == CTX_ASM) && (ctx_key[4] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd4; end
        else if (ctx_valid[5] && (ctx_state[5] == CTX_ASM) && (ctx_key[5] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd5; end
        else if (ctx_valid[6] && (ctx_state[6] == CTX_ASM) && (ctx_key[6] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd6; end
        else if (ctx_valid[7] && (ctx_state[7] == CTX_ASM) && (ctx_key[7] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd7; end
        else if (ctx_valid[8] && (ctx_state[8] == CTX_ASM) && (ctx_key[8] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd8; end
        else if (ctx_valid[9] && (ctx_state[9] == CTX_ASM) && (ctx_key[9] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd9; end
        else if (ctx_valid[10] && (ctx_state[10] == CTX_ASM) && (ctx_key[10] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd10; end
        else if (ctx_valid[11] && (ctx_state[11] == CTX_ASM) && (ctx_key[11] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd11; end
        else if (ctx_valid[12] && (ctx_state[12] == CTX_ASM) && (ctx_key[12] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd12; end
        else if (ctx_valid[13] && (ctx_state[13] == CTX_ASM) && (ctx_key[13] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd13; end
        else if (ctx_valid[14] && (ctx_state[14] == CTX_ASM) && (ctx_key[14] == frag_assembly_key)) begin match_found = 1'b1; match_idx = 4'd14; end

        if (!ctx_valid[0]) begin free_found = 1'b1; free_idx = 4'd0; end
        else if (!ctx_valid[1]) begin free_found = 1'b1; free_idx = 4'd1; end
        else if (!ctx_valid[2]) begin free_found = 1'b1; free_idx = 4'd2; end
        else if (!ctx_valid[3]) begin free_found = 1'b1; free_idx = 4'd3; end
        else if (!ctx_valid[4]) begin free_found = 1'b1; free_idx = 4'd4; end
        else if (!ctx_valid[5]) begin free_found = 1'b1; free_idx = 4'd5; end
        else if (!ctx_valid[6]) begin free_found = 1'b1; free_idx = 4'd6; end
        else if (!ctx_valid[7]) begin free_found = 1'b1; free_idx = 4'd7; end
        else if (!ctx_valid[8]) begin free_found = 1'b1; free_idx = 4'd8; end
        else if (!ctx_valid[9]) begin free_found = 1'b1; free_idx = 4'd9; end
        else if (!ctx_valid[10]) begin free_found = 1'b1; free_idx = 4'd10; end
        else if (!ctx_valid[11]) begin free_found = 1'b1; free_idx = 4'd11; end
        else if (!ctx_valid[12]) begin free_found = 1'b1; free_idx = 4'd12; end
        else if (!ctx_valid[13]) begin free_found = 1'b1; free_idx = 4'd13; end
        else if (!ctx_valid[14]) begin free_found = 1'b1; free_idx = 4'd14; end
    end

    // free_slot_available drives FM_ALLOC_CONTEXT.alloc_ok.
    wire        free_slot_available = free_found;
    // single_packet drives FM_ALLOC_CONTEXT.single_packet (som and eom).
    wire        single_packet       = frag_som & frag_eom;
    // seq_ok drives FM_APPEND.seq_ok (packet_seq == ctx_expected_seq).
    wire        seq_ok = match_found &&
                         (frag_packet_seq == ctx_expected_seq[match_idx]);
    // message_complete drives FM_APPEND.message_complete (eom).
    wire        message_complete = frag_eom;

    // SRAM bump-allocation length for a new context (whole assembled message
    // budget reserved up front); the effective budget is the min of the
    // MAX_MESSAGE_BYTES parameter cap and the runtime cfg cap.
    wire [SRAM_ADDR_WIDTH-1:0] allocated_len =
        {{(SRAM_ADDR_WIDTH-13){1'b0}}, msg_byte_budget};

    // -------------------------------------------------------------------------
    // Pack-engine combinational split for the beat at the head of the stream.
    // The byte write pointer ctx_payload_next[stream_ctx_id] may sit at an
    // arbitrary lane L (carried from the previous fragment's partial tail), so a
    // lane-0-aligned pl_beat can straddle two physical 32B words:
    //   chunk0 = bytes into the CURRENT word (cap = 32 - L)
    //   chunk1 = remainder into the NEXT 32B-aligned word
    // pack_wr_data for write A shifts the lane-0 bytes up to lane L; write B
    // (the remainder) is already lane-0 aligned in the next word.
    wire [15:0] strm_next_addr = ctx_payload_next[stream_ctx_id];
    wire [4:0]  strm_lane      = strm_next_addr[4:0];                 // L = addr & 31
    wire [5:0]  strm_room      = AXI_STRB_WIDTH[5:0] - {1'b0, strm_lane}; // 32 - L (1..32)
    wire [5:0]  chunk0_c       = (pl_beat_bytes < strm_room) ? pl_beat_bytes : strm_room;
    wire [5:0]  chunk1_c       = pl_beat_bytes - chunk0_c;           // 0..31
    // Lane-0 bytes shifted up to lane L for the current-word (A) write.
    wire [AXI_DATA_WIDTH-1:0] beat_shifted_a = pl_beat_data << {strm_lane, 3'b000};
    // Remainder bytes (those past chunk0) right-shifted back to lane 0 for the
    // next-word (B) write.
    wire [AXI_DATA_WIDTH-1:0] beat_shifted_b = pl_beat_data >> {chunk0_c, 3'b000};
    // Contiguous strobe for the chunk-A write: chunk0 lanes starting at lane L.
    // (The chunk-B strobe is rebuilt from the registered chunk1_q in strb_b_held.)
    wire [AXI_STRB_WIDTH-1:0] strb_a = (({{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1} << chunk0_c) -
                                        {{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1}) << strm_lane;
    // Byte start address for the B (next-word) write = current addr + chunk0.
    wire [15:0] strm_addrB = strm_next_addr + {10'd0, chunk0_c};

    // Contiguous strobe for the held chunk-B byte count (lane-0 aligned word).
    wire [AXI_STRB_WIDTH-1:0] strb_b_held =
        ({{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1} << chunk1_q) -
        {{(AXI_STRB_WIDTH-1){1'b0}}, 1'b1};

    // The pack engine accepts a new beat only when idle AND the stream config
    // (stream_ctx_id / stream_write) has been latched (stream_armed) — the latter
    // is set the cycle after frag_valid, which both targets the right context and
    // prevents the first beat from being consumed before its config settles.
    assign pl_beat_ready = (pack_state == S_BEAT_IDLE) & stream_armed;
    // pl_beat handshake accepted this cycle (engine ready and a valid beat).
    wire pl_beat_fire = pl_beat_valid & pl_beat_ready;

    // Frozen inputs the pack engine does not consume, tied off to keep the ports
    // lint-clean without an ad-hoc suppression (matches the decoder's
    // unused-input idiom):
    //  - frag_payload_word/frag_payload_strb: the single-beat metadata payload is
    //    superseded by the multi-beat pl_beat_* stream; only frag_payload_bytes
    //    (the logical count) is still used for accounting.
    //  - pl_beat_strb: redundant with pl_beat_bytes for a lane-0 contiguous run
    //    (the engine rebuilds per-word strobes from chunk0/chunk1).
    //  - pl_beat_first: the target context is latched at fragment-accept
    //    (stream_ctx_id), so the first-beat marker carries no extra information.
    wire _unused_payload_in = ^{frag_payload_word, frag_payload_strb,
                                pl_beat_strb, pl_beat_first};

    // Overflow guards for the append datapath.
    wire [13:0] append_total = {1'b0, (match_found ? ctx_payload_cnt[match_idx]
                                                    : 13'd0)} +
                               {1'b0, frag_payload_bytes};
    wire        msg_overflow = (append_total > {1'b0, msg_byte_budget});
    // SRAM window overflow: would the reserved region run past the limit?
    wire [SRAM_ADDR_WIDTH:0] alloc_end =
        {1'b0, sram_alloc_ptr} + {1'b0, allocated_len};
    wire        sram_overflow = (alloc_end > {1'b0, cfg_sram_limit});

    // disabled-drop: when not enabled and configured to drop, classify a PD.
    wire        disabled_drop = (!cfg_enable) & cfg_drop_when_disabled;

    // SSOT CFG_TIMEOUT.assembly_timeout_cycles == 0 disables the assembly
    // timeout entirely (write_effect "0=disabled"); aging and the AD_TIMEOUT
    // check are both gated by this so timeout-disabled mode never drops.
    wire        timeout_enabled = (cfg_timeout_cycles != 24'd0);

    // Constant/parameterised part-selects pulled out of the procedural blocks
    // into continuous-assign helper wires (project style: no parameterized
    // part-selects inside always_*).
    wire [SRAM_ADDR_WIDTH-1:0]      cfg_sram_base_w   = cfg_sram_base[SRAM_ADDR_WIDTH-1:0];
    wire [HEADER_SNAPSHOT_BITS-1:0] frag_first_hdr_w  = frag_first_header[HEADER_SNAPSHOT_BITS-1:0];

    // An accepted fragment qualifies for assembly only when there is no
    // upstream packet drop and the block is enabled.
    wire        upstream_drop = (packet_drop_reason_in != 6'd0);

    assign context_active_any =
        (ctx_valid[0] && (ctx_state[0] != CTX_IDLE)) ||
        (ctx_valid[1] && (ctx_state[1] != CTX_IDLE)) ||
        (ctx_valid[2] && (ctx_state[2] != CTX_IDLE)) ||
        (ctx_valid[3] && (ctx_state[3] != CTX_IDLE)) ||
        (ctx_valid[4] && (ctx_state[4] != CTX_IDLE)) ||
        (ctx_valid[5] && (ctx_state[5] != CTX_IDLE)) ||
        (ctx_valid[6] && (ctx_state[6] != CTX_IDLE)) ||
        (ctx_valid[7] && (ctx_state[7] != CTX_IDLE)) ||
        (ctx_valid[8] && (ctx_state[8] != CTX_IDLE)) ||
        (ctx_valid[9] && (ctx_state[9] != CTX_IDLE)) ||
        (ctx_valid[10] && (ctx_state[10] != CTX_IDLE)) ||
        (ctx_valid[11] && (ctx_state[11] != CTX_IDLE)) ||
        (ctx_valid[12] && (ctx_state[12] != CTX_IDLE)) ||
        (ctx_valid[13] && (ctx_state[13] != CTX_IDLE)) ||
        (ctx_valid[14] && (ctx_state[14] != CTX_IDLE));
    assign context_error_any =
        (ctx_valid[0] && (ctx_state[0] == CTX_ERR)) ||
        (ctx_valid[1] && (ctx_state[1] == CTX_ERR)) ||
        (ctx_valid[2] && (ctx_state[2] == CTX_ERR)) ||
        (ctx_valid[3] && (ctx_state[3] == CTX_ERR)) ||
        (ctx_valid[4] && (ctx_state[4] == CTX_ERR)) ||
        (ctx_valid[5] && (ctx_state[5] == CTX_ERR)) ||
        (ctx_valid[6] && (ctx_state[6] == CTX_ERR)) ||
        (ctx_valid[7] && (ctx_state[7] == CTX_ERR)) ||
        (ctx_valid[8] && (ctx_state[8] == CTX_ERR)) ||
        (ctx_valid[9] && (ctx_state[9] == CTX_ERR)) ||
        (ctx_valid[10] && (ctx_state[10] == CTX_ERR)) ||
        (ctx_valid[11] && (ctx_state[11] == CTX_ERR)) ||
        (ctx_valid[12] && (ctx_state[12] == CTX_ERR)) ||
        (ctx_valid[13] && (ctx_state[13] == CTX_ERR)) ||
        (ctx_valid[14] && (ctx_state[14] == CTX_ERR));

    // debug_context_select clamp into [0, CONTEXT_COUNT-1]; the full 8-bit
    // CONTROL.debug_context_select is range-checked so out-of-range selects
    // (including any value in the upper bits) mirror slot 0.
    wire [3:0]  sel_idx = (debug_context_select < CONTEXT_COUNT[7:0])
                          ? debug_context_select[3:0] : 4'd0;

    // -------------------------------------------------------------------------
    // Sequential: FSM, datapath, allocation, drop classification, descriptor.
    // -------------------------------------------------------------------------
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            `MCTP_V3_RESET_CONTEXT(0)
            `MCTP_V3_RESET_CONTEXT(1)
            `MCTP_V3_RESET_CONTEXT(2)
            `MCTP_V3_RESET_CONTEXT(3)
            `MCTP_V3_RESET_CONTEXT(4)
            `MCTP_V3_RESET_CONTEXT(5)
            `MCTP_V3_RESET_CONTEXT(6)
            `MCTP_V3_RESET_CONTEXT(7)
            `MCTP_V3_RESET_CONTEXT(8)
            `MCTP_V3_RESET_CONTEXT(9)
            `MCTP_V3_RESET_CONTEXT(10)
            `MCTP_V3_RESET_CONTEXT(11)
            `MCTP_V3_RESET_CONTEXT(12)
            `MCTP_V3_RESET_CONTEXT(13)
            `MCTP_V3_RESET_CONTEXT(14)
            sram_alloc_ptr         <= {SRAM_ADDR_WIDTH{1'b0}};
            alloc_seeded           <= 1'b0;
            active_context_count   <= 5'd0;
            last_error_context_id  <= 4'd0;
            pack_wr_valid          <= 1'b0;
            pack_wr_data           <= {AXI_DATA_WIDTH{1'b0}};
            pack_wr_strb           <= {AXI_STRB_WIDTH{1'b0}};
            pack_wr_addr           <= 16'd0;
            pack_wr_bytes          <= 13'd0;
            descriptor_push        <= 1'b0;
            desc_base_addr         <= 16'd0;
            desc_payload_len       <= 13'd0;
            desc_source_eid        <= 8'd0;
            desc_dest_eid          <= 8'd0;
            desc_tag_owner         <= 1'b0;
            desc_message_tag       <= 3'd0;
            desc_message_type      <= 7'd0;
            desc_final_seq         <= 2'd0;
            desc_context_id        <= 4'd0;
            desc_completion_status <= 3'd0;
            desc_requester_id      <= 16'd0;
            desc_routing_type      <= 3'd0;
            desc_first_header      <= 128'd0;
            desc_last_header       <= 128'd0;
            packet_drop_pulse      <= 1'b0;
            assembly_drop_pulse    <= 1'b0;
            drop_class_o           <= DC_NONE;
            drop_reason_o          <= 6'd0;
            sram_overflow_pulse    <= 1'b0;
            timeout_pulse          <= 1'b0;
            ctx_state_sel          <= CTX_IDLE;
            ctx_key_sel            <= 12'd0;
            ctx_expected_seq_sel   <= 2'd0;
            ctx_payload_count_sel  <= 13'd0;
            pack_state             <= S_BEAT_IDLE;
            stream_ctx_id          <= 4'd0;
            stream_write           <= 1'b0;
            stream_armed           <= 1'b0;
            pack_data_q            <= {AXI_DATA_WIDTH{1'b0}};
            chunk1_q               <= 6'd0;
            pack_addrB_q           <= 16'd0;
            pl_last_q              <= 1'b0;
            desc_pending           <= 1'b0;
            dp_base_addr           <= 16'd0;
            dp_payload_len         <= 13'd0;
            dp_source_eid          <= 8'd0;
            dp_dest_eid            <= 8'd0;
            dp_tag_owner           <= 1'b0;
            dp_message_tag         <= 3'd0;
            dp_message_type        <= 7'd0;
            dp_final_seq           <= 2'd0;
            dp_context_id          <= 4'd0;
            dp_completion_status   <= 3'd0;
            dp_requester_id        <= 16'd0;
            dp_routing_type        <= 3'd0;
            dp_first_header        <= 128'd0;
            dp_last_header         <= 128'd0;
        end else begin
            // single-cycle pulses default low each cycle (held below only when
            // a payload-write request is still waiting for pack_wr_ready).
            pack_wr_valid       <= pack_wr_valid & ~pack_wr_ready;
            descriptor_push     <= 1'b0;
            packet_drop_pulse   <= 1'b0;
            assembly_drop_pulse <= 1'b0;
            sram_overflow_pulse <= 1'b0;
            timeout_pulse       <= 1'b0;

            // Seed the bump allocator from cfg_sram_base while the table is
            // fully idle; once any context is live the pointer advances itself.
            if ((active_context_count == 5'd0) && !alloc_seeded) begin
                sram_alloc_ptr <= cfg_sram_base_w;
                alloc_seeded   <= 1'b1;
            end

            // -----------------------------------------------------------------
            // Per-cycle timeout aging for active (ASSEMBLING) contexts.
            // The first context whose age reaches the configured timeout is
            // aborted to ERROR (AD_TIMEOUT). Cleared back to IDLE next match.
            // -----------------------------------------------------------------
            if (timeout_enabled) begin
                `MCTP_V3_AGE_CONTEXT(0)
                `MCTP_V3_AGE_CONTEXT(1)
                `MCTP_V3_AGE_CONTEXT(2)
                `MCTP_V3_AGE_CONTEXT(3)
                `MCTP_V3_AGE_CONTEXT(4)
                `MCTP_V3_AGE_CONTEXT(5)
                `MCTP_V3_AGE_CONTEXT(6)
                `MCTP_V3_AGE_CONTEXT(7)
                `MCTP_V3_AGE_CONTEXT(8)
                `MCTP_V3_AGE_CONTEXT(9)
                `MCTP_V3_AGE_CONTEXT(10)
                `MCTP_V3_AGE_CONTEXT(11)
                `MCTP_V3_AGE_CONTEXT(12)
                `MCTP_V3_AGE_CONTEXT(13)
                `MCTP_V3_AGE_CONTEXT(14)
            end

            // -----------------------------------------------------------------
            // descriptor_pop retires the single DONE_WAIT_DESCRIPTOR_POP context
            // that owns the popped descriptor (fsm.context_fsm transition_5).
            // A pop consumes exactly ONE descriptor from the FIFO, so only the
            // context indexed by pop_context_id (the FIFO read-head's context_id)
            // is retired and active_context_count is decremented by exactly one.
            // Indexing the unpacked arrays directly keeps this loop-free.
            // -----------------------------------------------------------------
            if (descriptor_pop) begin
                if (ctx_valid[pop_context_id] &&
                    (ctx_state[pop_context_id] == CTX_DONE)) begin
                    ctx_state[pop_context_id] <= CTX_IDLE;
                    ctx_valid[pop_context_id] <= 1'b0;
                    if (active_context_count != 5'd0)
                        active_context_count <= active_context_count - 5'd1;
                end
            end

            // -----------------------------------------------------------------
            // Accept exactly one decoded fragment per cycle.
            // -----------------------------------------------------------------
            if (frag_valid) begin
                // Arm the pack engine for this decoder-accepted fragment's payload
                // stream (if any). stream_armed becomes effective next cycle, which
                // both targets the right context and holds pl_beat_ready low for
                // one cycle so the first beat is not consumed before stream_ctx_id
                // and stream_write settle. stream_write defaults to 0 (drain): only
                // the genuine alloc/append branches below set it to 1 so a
                // CONTEXT-TABLE-level drop discards its payload (no SRAM write).
                stream_armed <= (frag_payload_bytes != 13'd0);
                stream_write <= 1'b0;
                if (upstream_drop) begin
                    // Drop-priority invariant: an earlier (upstream) packet-drop
                    // reason wins; this stage only reports it, mutates nothing.
                    packet_drop_pulse <= 1'b1;
                    drop_class_o      <= DC_PACKET;
                    drop_reason_o     <= packet_drop_reason_in;
                end else if (disabled_drop) begin
                    // Block disabled in drop mode: classify a packet drop.
                    packet_drop_pulse <= 1'b1;
                    drop_class_o      <= DC_PACKET;
                    drop_reason_o     <= PD_DISABLED_DROP_MODE;
                end else if (frag_som) begin
                    // -------- FM_ALLOC_CONTEXT (SOM packet) ------------------
                    if (match_found) begin
                        // SOM for an already-active key → AD_DUPLICATE_SOM:
                        // abort the old context, suppress its descriptor.
                        ctx_state[match_idx]   <= CTX_ERR;
                        last_error_context_id  <= match_idx;
                        assembly_drop_pulse    <= 1'b1;
                        drop_class_o           <= DC_ASM;
                        drop_reason_o          <= AD_DUPLICATE_SOM;
                    end else if (!free_slot_available) begin
                        // No free context for a new fragmented SOM →
                        // PD_BAD_OR_EXPIRED_TAG (context-table-full); no alloc.
                        packet_drop_pulse <= 1'b1;
                        drop_class_o      <= DC_PACKET;
                        drop_reason_o     <= PD_BAD_OR_EXPIRED_TAG;
                    end else if (sram_overflow) begin
                        // Allocation would exceed the SRAM window → AD_SRAM_OVERFLOW.
                        sram_overflow_pulse <= 1'b1;
                        assembly_drop_pulse <= 1'b1;
                        drop_class_o        <= DC_ASM;
                        drop_reason_o       <= AD_SRAM_OVERFLOW;
                    end else begin
                        // Allocate a fresh context in free_idx.
                        ctx_valid[free_idx]        <= 1'b1;
                        ctx_key[free_idx]          <= frag_assembly_key;
                        ctx_source_eid[free_idx]   <= frag_source_eid;
                        ctx_dest_eid[free_idx]     <= frag_dest_eid;
                        ctx_tag_owner[free_idx]    <= frag_tag_owner;
                        ctx_message_tag[free_idx]  <= frag_message_tag;
                        ctx_message_type[free_idx] <= frag_message_type;
                        // first_tlp_header stored from the accepted SOM packet.
                        ctx_first_header[free_idx] <= frag_first_hdr_w;
                        ctx_requester_id[free_idx] <= frag_requester_id;
                        ctx_routing_type[free_idx] <= frag_routing_type;
                        ctx_timeout_age[free_idx]  <= {TIMEOUT_COUNTER_WIDTH{1'b0}};
                        // ctx_payload_base_addr = sram_alloc_ptr.
                        ctx_payload_base[free_idx] <= sram_alloc_ptr;
                        ctx_payload_next[free_idx] <= sram_alloc_ptr;
                        // ctx_payload_byte_count += payload_bytes (this packet).
                        ctx_payload_cnt[free_idx]  <= frag_payload_bytes;
                        // ctx_expected_seq = (packet_seq + 1) % 4.
                        ctx_expected_seq[free_idx] <= frag_packet_seq + 2'd1;
                        // ctx_state = DONE_WAIT_* if single_packet else ASSEMBLING.
                        ctx_state[free_idx]        <= single_packet ? CTX_DONE
                                                                    : CTX_ASM;
                        // active_context_count += 1.
                        active_context_count       <= active_context_count + 5'd1;
                        // sram_alloc_ptr += allocated_len (bump allocator).
                        sram_alloc_ptr             <= sram_alloc_ptr + allocated_len;

                        // Payload bytes for this packet arrive as the pl_beat_*
                        // stream and are written by the pack engine; target it at
                        // this freshly-allocated context (stream_write=1).
                        stream_ctx_id <= free_idx;
                        stream_write  <= 1'b1;

                        if (single_packet) begin
                            // SOM+EOM single packet: publish a descriptor
                            // (FM_PUBLISH_DESCRIPTOR) unless the queue is full.
                            if (descriptor_full) begin
                                ctx_state[free_idx] <= CTX_ERR;
                                last_error_context_id <= free_idx;
                                assembly_drop_pulse <= 1'b1;
                                drop_class_o        <= DC_ASM;
                                drop_reason_o       <= AD_DESCRIPTOR_FULL;
                            end else if (frag_payload_bytes != 13'd0) begin
                                // Defer the push until the pack engine has drained
                                // this packet's payload beats (§4.6 water-tight).
                                desc_pending           <= 1'b1;
                                dp_base_addr           <= sram_alloc_ptr;
                                dp_payload_len         <= frag_payload_bytes;
                                dp_source_eid          <= frag_source_eid;
                                dp_dest_eid            <= frag_dest_eid;
                                dp_tag_owner           <= frag_tag_owner;
                                dp_message_tag         <= frag_message_tag;
                                dp_message_type        <= frag_message_type;
                                dp_final_seq           <= frag_packet_seq;
                                dp_context_id          <= free_idx;
                                dp_completion_status   <= CS_OK;
                                dp_requester_id        <= frag_requester_id;
                                dp_routing_type        <= frag_routing_type;
                                dp_first_header        <= frag_first_header;
                                dp_last_header         <= frag_last_header;
                            end else begin
                                // Zero-payload single packet: no stream, push now.
                                descriptor_push        <= 1'b1;
                                desc_base_addr         <= sram_alloc_ptr;
                                desc_payload_len       <= frag_payload_bytes;
                                desc_source_eid        <= frag_source_eid;
                                desc_dest_eid          <= frag_dest_eid;
                                desc_tag_owner         <= frag_tag_owner;
                                desc_message_tag       <= frag_message_tag;
                                desc_message_type      <= frag_message_type;
                                desc_final_seq         <= frag_packet_seq;
                                desc_context_id        <= free_idx;
                                desc_completion_status <= CS_OK;
                                desc_requester_id      <= frag_requester_id;
                                desc_routing_type      <= frag_routing_type;
                                desc_first_header      <= frag_first_header;
                                desc_last_header       <= frag_last_header;
                            end
                        end
                    end
                end else begin
                    // -------- FM_APPEND (SOM=0 packet) -----------------------
                    if (!match_found) begin
                        // Middle/end with no active matching context (or EOM
                        // without a prior SOM) → PD_UNEXPECTED_MIDDLE_END.
                        packet_drop_pulse <= 1'b1;
                        drop_class_o      <= DC_PACKET;
                        drop_reason_o     <= PD_UNEXPECTED_MIDDLE_END;
                    end else if (!seq_ok) begin
                        // packet_seq != expected modulo-4 → AD_SEQUENCE_MISMATCH.
                        ctx_state[match_idx]  <= CTX_ERR;
                        last_error_context_id <= match_idx;
                        assembly_drop_pulse   <= 1'b1;
                        drop_class_o          <= DC_ASM;
                        drop_reason_o         <= AD_SEQUENCE_MISMATCH;
                    end else if (msg_overflow) begin
                        // Append would exceed MAX_MESSAGE_BYTES → AD_MESSAGE_OVERFLOW.
                        ctx_state[match_idx]  <= CTX_ERR;
                        last_error_context_id <= match_idx;
                        assembly_drop_pulse   <= 1'b1;
                        drop_class_o          <= DC_ASM;
                        drop_reason_o         <= AD_MESSAGE_OVERFLOW;
                    end else if (timeout_enabled &&
                                 (ctx_timeout_age[match_idx] >= cfg_timeout_cycles)) begin
                        // Context age exceeds assembly_timeout_cycles → AD_TIMEOUT.
                        // SSOT CFG_TIMEOUT.assembly_timeout_cycles==0 means the
                        // timeout is DISABLED, so the check is gated by
                        // timeout_enabled (= cfg_timeout_cycles != 0).
                        ctx_state[match_idx]  <= CTX_ERR;
                        last_error_context_id <= match_idx;
                        timeout_pulse         <= 1'b1;
                        assembly_drop_pulse   <= 1'b1;
                        drop_class_o          <= DC_ASM;
                        drop_reason_o         <= AD_TIMEOUT;
                    end else begin
                        // Accepted append: update per-context state.
                        // ctx_payload_byte_count += payload_bytes.
                        ctx_payload_cnt[match_idx]  <= ctx_payload_cnt[match_idx] +
                                                       frag_payload_bytes;
                        // ctx_expected_seq = (ctx_expected_seq + 1) % 4.
                        ctx_expected_seq[match_idx] <= ctx_expected_seq[match_idx] + 2'd1;
                        // ctx_last_seq (= packet_seq) and the updated last_tlp_header
                        // for this context are materialised at the descriptor
                        // boundary (desc_final_seq / desc_last_header) on EOM.
                        ctx_timeout_age[match_idx]  <= {TIMEOUT_COUNTER_WIDTH{1'b0}};

                        // Payload bytes for this append arrive as the pl_beat_*
                        // stream; the pack engine writes them and advances
                        // ctx_payload_next per pack word (it is the sole owner of
                        // that pointer now). Target the stream at the matched
                        // context (stream_write=1).
                        stream_ctx_id <= match_idx;
                        stream_write  <= 1'b1;

                        if (message_complete) begin
                            // EOM → FM_PUBLISH_DESCRIPTOR (move to DONE_WAIT_*).
                            if (descriptor_full) begin
                                ctx_state[match_idx]  <= CTX_ERR;
                                last_error_context_id <= match_idx;
                                assembly_drop_pulse   <= 1'b1;
                                drop_class_o          <= DC_ASM;
                                drop_reason_o         <= AD_DESCRIPTOR_FULL;
                            end else if (frag_payload_bytes != 13'd0) begin
                                // Move to DONE now; defer the descriptor push until
                                // the pack engine drains this packet's payload beats
                                // (§4.6) so readback after descriptor_valid is exact.
                                ctx_state[match_idx]   <= CTX_DONE;
                                desc_pending           <= 1'b1;
                                dp_base_addr           <= ctx_payload_base[match_idx];
                                dp_payload_len         <= ctx_payload_cnt[match_idx] +
                                                          frag_payload_bytes;
                                dp_source_eid          <= ctx_source_eid[match_idx];
                                dp_dest_eid            <= ctx_dest_eid[match_idx];
                                dp_tag_owner           <= ctx_tag_owner[match_idx];
                                dp_message_tag         <= ctx_message_tag[match_idx];
                                dp_message_type        <= ctx_message_type[match_idx];
                                dp_final_seq           <= frag_packet_seq;
                                dp_context_id          <= match_idx;
                                dp_completion_status   <= CS_OK;
                                dp_requester_id        <= ctx_requester_id[match_idx];
                                dp_routing_type        <= ctx_routing_type[match_idx];
                                dp_first_header        <= ctx_first_header[match_idx];
                                dp_last_header         <= frag_last_header;
                            end else begin
                                // Zero-payload EOM append: no stream, push now.
                                ctx_state[match_idx]   <= CTX_DONE;
                                descriptor_push        <= 1'b1;
                                desc_base_addr         <= ctx_payload_base[match_idx];
                                desc_payload_len       <= ctx_payload_cnt[match_idx] +
                                                          frag_payload_bytes;
                                desc_source_eid        <= ctx_source_eid[match_idx];
                                desc_dest_eid          <= ctx_dest_eid[match_idx];
                                desc_tag_owner         <= ctx_tag_owner[match_idx];
                                desc_message_tag       <= ctx_message_tag[match_idx];
                                desc_message_type      <= ctx_message_type[match_idx];
                                desc_final_seq         <= frag_packet_seq;
                                desc_context_id        <= match_idx;
                                desc_completion_status <= CS_OK;
                                desc_requester_id      <= ctx_requester_id[match_idx];
                                desc_routing_type      <= ctx_routing_type[match_idx];
                                desc_first_header      <= ctx_first_header[match_idx];
                                desc_last_header       <= frag_last_header;
                            end
                        end
                    end
                end
            end

            // -----------------------------------------------------------------
            // Multi-beat pack engine (PAYLOAD_STREAM_CONTRACT §4.3/§4.4).
            // For an ACCEPTED stream (stream_write=1) it splits each lane-0-aligned
            // pl_beat into <=32B-per-word writes (A into the current partial word,
            // B into the next word on a 32B straddle), serialized behind
            // pack_wr_ready, and is the SOLE driver of ctx_payload_next / pack_wr_*.
            // For a DROPPED stream (stream_write=0) it DRAINS the beats (consumes
            // them with no SRAM write, mutating no context). stream_armed is
            // cleared once the stream's last beat is processed. pl_beat_ready (a
            // wire) is asserted only in S_BEAT_IDLE while armed.
            // -----------------------------------------------------------------
            case (pack_state)
                S_BEAT_IDLE: begin
                    if (pl_beat_fire) begin
                        if (stream_write) begin
                            // Issue chunk-A write at the current partial-word lane.
                            pack_wr_valid <= (chunk0_c != 6'd0);
                            pack_wr_data  <= beat_shifted_a;
                            pack_wr_strb  <= strb_a;
                            pack_wr_addr  <= strm_next_addr;
                            pack_wr_bytes <= {7'd0, chunk0_c};
                            // Advance the byte pointer by chunk0 (no-hole); its low
                            // 5 bits are the partial-word lane the packer uses.
                            ctx_payload_next[stream_ctx_id] <= strm_next_addr +
                                                               {10'd0, chunk0_c};
                            // Hold the remainder for the chunk-B write.
                            pack_data_q   <= beat_shifted_b;
                            chunk1_q      <= chunk1_c;
                            pack_addrB_q  <= strm_addrB;
                            pl_last_q     <= pl_beat_last;
                            pack_state    <= S_WRA;
                        end else begin
                            // DROP path: discard this beat (no SRAM write). When the
                            // last dropped beat is consumed, disarm the stream.
                            if (pl_beat_last) stream_armed <= 1'b0;
                        end
                    end
                end
                S_WRA: begin
                    // chunk-A write retires when the packer accepts it.
                    if (pack_wr_ready) begin
                        if (chunk1_q != 6'd0) begin
                            // Straddle: issue chunk-B into the next 32B word.
                            pack_wr_valid <= 1'b1;
                            pack_wr_data  <= pack_data_q;
                            pack_wr_strb  <= strb_b_held;
                            pack_wr_addr  <= pack_addrB_q;
                            pack_wr_bytes <= {7'd0, chunk1_q};
                            ctx_payload_next[stream_ctx_id] <= pack_addrB_q +
                                                               {10'd0, chunk1_q};
                            pack_state    <= S_WRB;
                        end else begin
                            // Beat fully written; return to idle for the next beat.
                            pack_state    <= S_BEAT_IDLE;
                            if (pl_last_q) begin
                                // Stream end: disarm and publish the deferred desc.
                                stream_armed <= 1'b0;
                                if (desc_pending) begin
                                    `MCTP_V3_FIRE_DEFERRED_DESC
                                end
                            end
                        end
                    end
                end
                S_WRB: begin
                    // chunk-B write retires; the straddling beat is complete.
                    if (pack_wr_ready) begin
                        pack_state    <= S_BEAT_IDLE;
                        if (pl_last_q) begin
                            stream_armed <= 1'b0;
                            if (desc_pending) begin
                                `MCTP_V3_FIRE_DEFERRED_DESC
                            end
                        end
                    end
                end
                default: pack_state <= S_BEAT_IDLE;
            endcase

            // -----------------------------------------------------------------
            // CTX_STATE / DEBUG_CTX mirror for the selected slot.
            // -----------------------------------------------------------------
            ctx_state_sel         <= ctx_state[sel_idx];
            ctx_key_sel           <= ctx_key[sel_idx];
            ctx_expected_seq_sel  <= ctx_expected_seq[sel_idx];
            ctx_payload_count_sel <= ctx_payload_cnt[sel_idx];
        end
    end

`undef MCTP_V3_RESET_CONTEXT
`undef MCTP_V3_AGE_CONTEXT
`undef MCTP_V3_FIRE_DEFERRED_DESC
endmodule
`default_nettype wire
