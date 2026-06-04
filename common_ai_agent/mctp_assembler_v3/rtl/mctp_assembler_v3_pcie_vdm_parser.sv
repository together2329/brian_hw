// mctp_assembler_v3_pcie_vdm_parser.sv
// PCIe VDM parser implementing FM_DECODE_VDM (pcie_vdm_decode).
// Consumes the fixed 6-signal beat stream from axi_wr_ingress; decodes the
// 16-byte Non-Flit PCIe VDM header; validates message_code/vendor_id/vdm_code/
// routing/TC; strips header bytes; emits a 1-cycle vdm_valid pulse with the
// decoded bundle, or a packet_drop_valid pulse with PD_UNSUPPORTED_VDM /
// PD_BAD_PAD_OR_ALIGNMENT reason.
//
// Beat-stream protocol (from ingress, FROZEN):
//   tlp_beat_valid : 1-cycle pulse per accepted W beat
//   tlp_beat_data  : 256-bit raw beat data (byte N at bits [8N+7:8N])
//   tlp_beat_strb  : 32-bit byte strobes
//   tlp_beat_last  : 1-cycle pulse on the final beat of the TLP
//   tlp_accept     : 1-cycle pulse at B-handshake: TLP is legal & in-bounds
//   tlp_byte_count : total accepted TLP byte count (set together with tlp_accept)
//
// The 16-byte Non-Flit PCIe VDM header occupies the first 16 bytes of the
// first beat (tlp_beat_data[127:0]).  Byte indices follow the SSOT tlp[] array
// where tlp[N] = tlp_beat_data[8*N+7 : 8*N]:
//
//   tlp[0]        : {fmt[7:5], type[4:0]}  -- routing_type = tlp[0][2:0]
//   tlp[1]        : {TC[6:4], attr/flags}  -- traffic_class = tlp[1][6:4]
//   tlp[1], tlp[2]: requester_id[15:0]     -- per SSOT expr (tlp[1]<<8)|tlp[2]
//   tlp[3]        : pad_count in bits[1:0]
//   tlp[7]        : message_code
//   tlp[8], tlp[9]: vendor_id[15:0]        -- {tlp[8], tlp[9]}
//   tlp[10]       : vdm_code[7:0]
//
// Payload starts at byte offset 16 (= tlp_beat_data[255:128] of beat 0).
`default_nettype none
module mctp_assembler_v3_pcie_vdm_parser #(
    parameter integer AXI_DATA_WIDTH                = 256,
    parameter integer AXI_STRB_WIDTH                = 32,
    parameter integer MIN_TRANSMISSION_UNIT_BYTES   = 64,
    parameter integer MAX_TRANSMISSION_UNIT_BYTES   = 4096,
    parameter integer TRANSMISSION_UNIT_ALIGN_BYTES = 4,
    parameter integer TLP_HEADER_SNAPSHOT_BYTES     = 16,
    // Max TLP byte count (matches axi_wr_ingress.MAX_TLP_BYTES); sizes the
    // internal raw-beat replay buffer used by the pl_beat_* payload stream.
    parameter integer MAX_TLP_BYTES                 = 4112
) (
    input  wire                        axi_aclk,
    input  wire                        axi_aresetn,
    // ingress beat stream (FROZEN interface from axi_wr_ingress)
    input  wire                        tlp_beat_valid,
    input  wire [AXI_DATA_WIDTH-1:0]   tlp_beat_data,
    input  wire [AXI_STRB_WIDTH-1:0]   tlp_beat_strb,
    input  wire                        tlp_beat_last,
    input  wire                        tlp_accept,
    input  wire [12:0]                 tlp_byte_count,
    // configuration (from regfile via cdc_sync)
    input  wire [12:0]                 cfg_tu_bytes,
    // decoded VDM packet output
    output reg                         vdm_valid,
    output reg  [AXI_DATA_WIDTH-1:0]   vdm_word,
    output reg  [4:0]                  vdm_payload_offset,
    output reg  [12:0]                 vdm_payload_bytes,
    output reg  [TLP_HEADER_SNAPSHOT_BYTES*8-1:0]  vdm_first_header,
    output reg  [TLP_HEADER_SNAPSHOT_BYTES*8-1:0]  vdm_last_header,
    output reg  [15:0]                 vdm_requester_id,
    output reg  [2:0]                  vdm_routing_type,
    output reg  [AXI_DATA_WIDTH-1:0]   vdm_payload_word,
    output reg  [AXI_STRB_WIDTH-1:0]   vdm_payload_strb,
    // drop output
    output reg                         packet_drop_valid,
    output reg  [5:0]                  packet_drop_reason,
    // debug mirror: (message_code<<24)|(vendor_id<<8)|vdm_code  (SSOT FM_DECODE_VDM)
    output reg  [31:0]                 last_decoded_vdm,
    // DEBUG_CTX.parser_state[3:0] mirror (SSOT registers.DEBUG_CTX): the parser's
    // decode FSM state, exposed for the per-context debug read-back word.
    output reg  [3:0]                  parser_state,
    // -------------------------------------------------------------------------
    // Multi-beat payload stream (PAYLOAD_STREAM_CONTRACT.md §2 / §8).
    // A lane-0-aligned payload-byte stream emitted ONLY for an accepted clean
    // VDM (vdm_valid path), never on a drop and never for a zero-payload TLP.
    // The header is stripped and the payload is realigned to lane 0 with the
    // contract's fixed 16-byte (128-bit) down-shift + 1-beat carry register
    // (§1.1); there is NO variable shifter. Beats honor pl_beat_ready.
    // -------------------------------------------------------------------------
    output reg                         pl_beat_valid,   // 1 = aligned payload beat valid
    output reg  [AXI_DATA_WIDTH-1:0]   pl_beat_data,    // lane-0-aligned payload; msg byte 32*k at lane 0
    output reg  [AXI_STRB_WIDTH-1:0]   pl_beat_strb,    // (1<<pl_beat_bytes)-1, contiguous from lane 0
    output reg  [5:0]                  pl_beat_bytes,   // valid payload bytes this beat (1..32)
    output reg                         pl_beat_first,   // first emitted beat of this packet's payload
    output reg                         pl_beat_last,    // final emitted beat of this packet's payload
    input  wire                        pl_beat_ready    // downstream accepts this beat (valid/ready)
);

    // -----------------------------------------------------------------------
    // Drop-reason encoding (§4.2 of INTEGRATION_CONTRACT.md)
    // -----------------------------------------------------------------------
    localparam [5:0] PD_NONE                 = 6'd0;
    localparam [5:0] PD_UNSUPPORTED_VDM      = 6'd3;
    localparam [5:0] PD_BAD_PAD_OR_ALIGNMENT = 6'd5;

    // parser_state encoding for the DEBUG_CTX.parser_state[3:0] mirror.
    localparam [3:0] PS_IDLE   = 4'd0;  // awaiting tlp_accept / between TLPs
    localparam [3:0] PS_DECODE = 4'd1;  // beats captured, decoding on tlp_accept
    localparam [3:0] PS_VALID  = 4'd2;  // last decode emitted a clean VDM
    localparam [3:0] PS_DROP   = 4'd3;  // last decode classified a packet drop

    // VDM binding constants (SSOT FM_DECODE_VDM state_updates)
    localparam [7:0]  VDM_MSG_CODE  = 8'h7F;
    localparam [15:0] VDM_VENDOR_ID = 16'h1AB4;
    localparam [7:0]  VDM_CODE_VAL  = 8'h00;

    // Payload byte offset is always 16 (SSOT expr payload_offset=16)
    localparam [4:0] PAYLOAD_OFFSET = 5'd16;

    // Header snapshot width derived from parameter
    localparam integer HDR_BITS = TLP_HEADER_SNAPSHOT_BYTES * 8; // 128

    // Alignment mask for TU alignment check
    localparam [12:0] TU_ALIGN_MASK = TRANSMISSION_UNIT_ALIGN_BYTES[12:0] - 13'd1;

    // -----------------------------------------------------------------------
    // Beat-stream capture registers
    // -----------------------------------------------------------------------
    reg [AXI_DATA_WIDTH-1:0] first_beat_q;    // latched beat 0 (header + first payload slice)
    reg [AXI_STRB_WIDTH-1:0] first_strb_q;    // strobes of beat 0
    reg [AXI_DATA_WIDTH-1:0] last_beat_q;     // latched most-recent beat
    reg [AXI_STRB_WIDTH-1:0] last_strb_q;     // strobes of most-recent beat
    reg                       first_beat_seen; // set after beat 0 is captured for this TLP
    reg                       multi_beat;      // TLP has more than one beat

    // Helper wires for parameterized-width header slices (policy: no
    // parameterized part-selects inside procedural blocks; declared after
    // first_beat_q/last_beat_q so the drivers are in scope).
    wire [HDR_BITS-1:0] first_hdr_slice = first_beat_q[HDR_BITS-1:0];
    wire [HDR_BITS-1:0] last_hdr_slice  = last_beat_q[HDR_BITS-1:0];

    // -----------------------------------------------------------------------
    // TLP field extraction from first_beat_q (byte N = first_beat_q[8N+7:8N])
    // Fields follow the SSOT tlp[] byte array convention.
    // -----------------------------------------------------------------------
    // tlp[0]: {fmt[7:5], type[4:0]}; routing_type in type[2:0]
    wire [2:0]  routing_type  = first_beat_q[2:0];
    // tlp[1]: traffic_class in bits[6:4]
    wire [2:0]  traffic_class = first_beat_q[14:12];
    // requester_id = (tlp[1] << 8) | tlp[2]  (SSOT expr)
    wire [15:0] requester_id  = {first_beat_q[15:8], first_beat_q[23:16]};
    // tlp[3]: pad count in bits[1:0]
    wire [1:0]  pad_len       = first_beat_q[25:24];
    // tlp[7]: message_code
    wire [7:0]  message_code  = first_beat_q[63:56];
    // tlp[8..9]: vendor_id = {tlp[8], tlp[9]}
    wire [15:0] vendor_id     = {first_beat_q[71:64], first_beat_q[79:72]};
    // tlp[10]: vdm_code
    wire [7:0]  vdm_code      = first_beat_q[87:80];

    // routing_supported: routing types 0x0/0x2/0x3 are valid for MCTP VDM
    // (DSP0238 §7; PCIe spec type[2:0] encodes routing in Non-Flit VDM)
    wire routing_supported = (routing_type == 3'd0) ||
                             (routing_type == 3'd2) ||
                             (routing_type == 3'd3);

    // -----------------------------------------------------------------------
    // FM_DECODE_VDM: vdm_valid expression (SSOT):
    //   (message_code == 0x7F) and (vendor_id == 0x1AB4) and
    //   (vdm_code == 0x0) and routing_supported and (traffic_class == 0)
    // -----------------------------------------------------------------------
    wire decode_vdm_ok = (message_code == VDM_MSG_CODE) &&
                         (vendor_id    == VDM_VENDOR_ID) &&
                         (vdm_code     == VDM_CODE_VAL)  &&
                         routing_supported                &&
                         (traffic_class == 3'd0);

    // -----------------------------------------------------------------------
    // FM_DECODE_VDM: pad_ok expression (SSOT):
    //   (pad_len <= 3) and ((pad_len == 0) if not eom else True)
    // Every accepted TLP represents one complete VDM transfer (eom=True at
    // this boundary), so the "not eom" branch never fires.  pad_len is 2 bits;
    // widened to 3 bits for comparison to avoid a constant-comparison warning.
    // -----------------------------------------------------------------------
    wire pad_ok = ({1'b0, pad_len} <= 3'd3); // always true; kept for SSOT traceability

    // Payload byte count: tlp_byte_count includes the 16B header and pad bytes
    wire [12:0] payload_bytes_raw = tlp_byte_count - 13'd16 - {11'd0, pad_len};

    // cfg_tu_bytes must be in [MIN_TU, MAX_TU] and aligned to TRANSMISSION_UNIT_ALIGN_BYTES
    wire tu_range_ok = (cfg_tu_bytes >= MIN_TRANSMISSION_UNIT_BYTES[12:0]) &&
                       (cfg_tu_bytes <= MAX_TRANSMISSION_UNIT_BYTES[12:0]) &&
                       ((cfg_tu_bytes & TU_ALIGN_MASK) == 13'd0);

    // EOM payload must be <= TU (PD_BAD_PAD_OR_ALIGNMENT if violated)
    wire payload_size_ok = (payload_bytes_raw <= cfg_tu_bytes) && tu_range_ok;

    // Combined bad-pad-or-alignment drop condition (SSOT error_case_1)
    wire drop_bad_pad = !pad_ok || !payload_size_ok;

    // -----------------------------------------------------------------------
    // Beat-stream capture: latch beat 0 as first_beat_q; always update
    // last_beat_q.  Reset tracking on tlp_accept so the next TLP starts fresh.
    // -----------------------------------------------------------------------
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            first_beat_q    <= {AXI_DATA_WIDTH{1'b0}};
            first_strb_q    <= {AXI_STRB_WIDTH{1'b0}};
            last_beat_q     <= {AXI_DATA_WIDTH{1'b0}};
            last_strb_q     <= {AXI_STRB_WIDTH{1'b0}};
            first_beat_seen <= 1'b0;
            multi_beat      <= 1'b0;
        end else begin
            if (tlp_beat_valid) begin
                last_beat_q <= tlp_beat_data;
                last_strb_q <= tlp_beat_strb;
                if (!first_beat_seen) begin
                    first_beat_q    <= tlp_beat_data;
                    first_strb_q    <= tlp_beat_strb;
                    first_beat_seen <= 1'b1;
                    // multi_beat: true if this beat is not also the last beat
                    multi_beat      <= !tlp_beat_last;
                end else begin
                    // Any beat after the first makes this a multi-beat TLP
                    multi_beat <= 1'b1;
                end
            end
            // tlp_accept fires in S_RESP (after B-handshake), never simultaneous
            // with tlp_beat_last (which fires in S_DATA).  Reset tracking here so
            // the next TLP's beat 0 will be captured correctly.
            if (tlp_accept) begin
                first_beat_seen <= 1'b0;
                multi_beat      <= 1'b0;
            end
        end
    end

    // =======================================================================
    // Multi-beat payload stream (PAYLOAD_STREAM_CONTRACT.md §1.1 / §2)
    // =======================================================================
    // Raw-beat replay buffer: every raw beat of the current TLP is captured
    // during the COLLECT_W stream (on tlp_beat_valid). At tlp_accept the beat
    // count is frozen and, on a clean-accepted VDM with non-zero payload, the
    // replay FSM walks the buffer emitting lane-0-aligned payload beats with the
    // contract's fixed 16-byte down-shift + 1-beat carry register.
    //
    //   carry(after beat0) = beat_buf[0][255:128]          // payload bytes 0..15
    //   emit on beat n>=1  = { beat_buf[n][127:0], carry }  // 16-byte down-shift
    //   carry              = beat_buf[n][255:128]
    //   final residual     = { 128'h0, carry }              // if bytes remain
    //
    // The shift constant is always 16 lanes, so this is a fixed 128-bit splice
    // plus a 128-bit carry register -- NO variable shifter, loop-free.
    // Buffer depth = ceil(MAX_TLP_BYTES/32)+1 entries of one 256-bit beat each.
    localparam integer BEAT_BUF_DEPTH = (MAX_TLP_BYTES / 32) + 2; // 130 for 4112
    localparam integer BEAT_IDX_W     = $clog2(BEAT_BUF_DEPTH);

    reg [AXI_DATA_WIDTH-1:0] beat_buf [0:BEAT_BUF_DEPTH-1]; // raw beats of current TLP
    reg [BEAT_IDX_W-1:0]     beat_wr_idx;                   // next raw-beat write slot
    reg [BEAT_IDX_W-1:0]     n_beats_q;                     // raw beats captured (frozen @accept)

    // Last valid beat_buf slot index, hoisted out of the procedural block as a
    // continuous-assign helper (policy: no parameterized part-selects inside
    // procedural blocks). Used to saturate the write index at the buffer end.
    wire [BEAT_IDX_W-1:0]    beat_buf_last_idx = BEAT_BUF_DEPTH[BEAT_IDX_W-1:0] - 1'b1;

    // Capture raw beats into beat_buf during the beat stream. Mirrors the
    // existing first_beat_q/last_beat_q lifetime: the write index resets at
    // tlp_accept so the next TLP refills from slot 0 (one stream in flight).
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            beat_wr_idx <= {BEAT_IDX_W{1'b0}};
        end else begin
            if (tlp_beat_valid) begin
                beat_buf[beat_wr_idx] <= tlp_beat_data;
                // saturate at the last slot to avoid out-of-range write for an
                // (illegal, ingress-rejected) over-length TLP; ingress already
                // bounds byte_acc <= MAX_TLP_BYTES so this never fires in legal flow.
                if (beat_wr_idx != beat_buf_last_idx)
                    beat_wr_idx <= beat_wr_idx + 1'b1;
            end
            if (tlp_accept) begin
                beat_wr_idx <= {BEAT_IDX_W{1'b0}};
            end
        end
    end

    // -------------------------------------------------------------------------
    // Replay FSM: emits the lane-0-aligned payload beat stream. The walk state
    // registers (pl_carry / rep_raw_idx / bytes_rem) describe the CURRENT
    // in-flight emitted beat, and the pl_beat_* outputs are a combinational
    // function of that walk state (so they are stable -- "held" -- while a beat
    // waits for pl_beat_ready). Emit count = ceil(payload_bytes/32); termination
    // is by bytes_rem, so beat_buf is never read past n_beats_q.
    //
    //   RIDLE : valid=0; on a clean-accepted VDM with non-zero payload, seed the
    //           walk for emitted beat 0 and go RBEAT.
    //   RBEAT : present the current beat (combinationally); on handshake, if it
    //           is the last beat -> RIDLE, else advance carry/idx/bytes_rem to
    //           the next beat (stay RBEAT).
    //
    // Walk-state convention (emitted beat k, 0-based):
    //   pl_carry    = payload bytes [32*k .. 32*k+15]  (low 16 lanes of beat k)
    //   rep_raw_idx = raw beat whose low 16 bytes form lanes 16..31 of beat k
    //                 (= k+1; raw beat 0 is header+payload[0:16] consumed as the
    //                  seed carry, so emitted beat k splices raw beat k+1)
    //   bytes_rem   = payload bytes still to emit, INCLUDING beat k
    // -------------------------------------------------------------------------
    localparam [0:0] RIDLE = 1'b0;
    localparam [0:0] RBEAT = 1'b1;

    reg                  rep_state;     // RIDLE / RBEAT
    reg [BEAT_IDX_W-1:0] rep_raw_idx;   // raw beat spliced for the CURRENT emitted beat (=k+1)
    reg [127:0]          pl_carry;      // payload bytes [32*k .. 32*k+15] (low half of beat k)
    reg [12:0]           bytes_rem;     // payload bytes still to emit, incl. the current beat

    // Per-(current)-beat byte count / last flag from the walk state.
    wire [5:0] cur_bytes  = (bytes_rem >= 13'd32) ? 6'd32 : bytes_rem[5:0];
    wire       cur_islast = (bytes_rem <= 13'd32);

    // Aligned-data + next-carry mux (fixed 128-bit splice; no variable shifter).
    // While a raw beat remains (rep_raw_idx < n_beats_q) splice its low 16 bytes
    // above the carry to form lanes 16..31; once the raw beats are exhausted the
    // residual { 128'h0, carry } carries the final <=16 bytes. Guarded so beat_buf
    // is only read within [0..n_beats_q-1].
    wire         rep_have_raw   = (rep_raw_idx < n_beats_q);
    wire [127:0] rep_raw_lo     = rep_have_raw ? beat_buf[rep_raw_idx][127:0]   : 128'h0;
    wire [127:0] rep_raw_hi     = rep_have_raw ? beat_buf[rep_raw_idx][255:128] : 128'h0;
    wire [AXI_DATA_WIDTH-1:0] rep_aligned    = {rep_raw_lo, pl_carry};
    wire [127:0]              rep_next_carry = rep_raw_hi;

    // Contiguous lane-0 strobe for cur_bytes (1..32); handle 32 without 1<<32.
    wire [AXI_STRB_WIDTH-1:0] cur_strb =
        (cur_bytes == 6'd32) ? {AXI_STRB_WIDTH{1'b1}}
                             : ((32'd1 << cur_bytes) - 32'd1);

    // Launch qualifier: an accepted CLEAN VDM with real payload (mirrors the
    // vdm_valid path). A drop or zero-payload TLP emits NO beats.
    wire rep_launch = tlp_accept && decode_vdm_ok && !drop_bad_pad &&
                      (payload_bytes_raw != 13'd0);

    // Sequential walk state + replay-state machine.
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            rep_state   <= RIDLE;
            rep_raw_idx <= {BEAT_IDX_W{1'b0}};
            pl_carry    <= 128'h0;
            bytes_rem   <= 13'd0;
            n_beats_q   <= {BEAT_IDX_W{1'b0}};
        end else begin
            case (rep_state)
                RIDLE: begin
                    if (rep_launch) begin
                        // Seed emitted beat 0: carry = payload bytes 0..15 (high
                        // half of raw beat 0); the splice raw beat for beat 0 is
                        // raw beat 1 (rep_raw_idx=1). If only one raw beat exists,
                        // rep_have_raw is false and beat 0 is the residual emit.
                        n_beats_q   <= beat_wr_idx;               // raw beats captured
                        bytes_rem   <= payload_bytes_raw;
                        pl_carry    <= first_beat_q[255:128];     // payload bytes 0..15
                        rep_raw_idx <= {{(BEAT_IDX_W-1){1'b0}}, 1'b1};
                        rep_state   <= RBEAT;
                    end
                end

                RBEAT: begin
                    // Hold the (combinationally driven) current beat until accepted.
                    if (pl_beat_valid && pl_beat_ready) begin
                        if (cur_islast) begin
                            // Final beat consumed: stream complete.
                            rep_state <= RIDLE;
                        end else begin
                            // Advance the carry walk to the next emitted beat.
                            bytes_rem   <= bytes_rem - 13'd32;
                            pl_carry    <= rep_next_carry;
                            rep_raw_idx <= rep_raw_idx + 1'b1;
                        end
                    end
                end

                default: rep_state <= RIDLE;
            endcase
        end
    end

    // Combinational pl_beat_* outputs derived from the walk state. They are
    // declared `output reg` (procedural drive) but carry no state of their own;
    // RBEAT presents one stable beat per walk position until pl_beat_ready.
    always @* begin
        if (rep_state == RBEAT) begin
            pl_beat_valid = 1'b1;
            pl_beat_data  = rep_aligned;
            pl_beat_bytes = cur_bytes;
            pl_beat_strb  = cur_strb;
            pl_beat_first = (rep_raw_idx == {{(BEAT_IDX_W-1){1'b0}}, 1'b1});
            pl_beat_last  = cur_islast;
        end else begin
            pl_beat_valid = 1'b0;
            pl_beat_data  = {AXI_DATA_WIDTH{1'b0}};
            pl_beat_bytes = 6'd0;
            pl_beat_strb  = {AXI_STRB_WIDTH{1'b0}};
            pl_beat_first = 1'b0;
            pl_beat_last  = 1'b0;
        end
    end

    // -----------------------------------------------------------------------
    // Output decode: on tlp_accept, decode header fields and emit either
    // vdm_valid (clean packet) or packet_drop_valid (drop reason).
    // Both are 1-cycle pulses; all other cycles they are deasserted.
    // -----------------------------------------------------------------------
    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            vdm_valid          <= 1'b0;
            vdm_word           <= {AXI_DATA_WIDTH{1'b0}};
            vdm_payload_offset <= PAYLOAD_OFFSET;
            vdm_payload_bytes  <= 13'd0;
            vdm_first_header   <= {HDR_BITS{1'b0}};
            vdm_last_header    <= {HDR_BITS{1'b0}};
            vdm_requester_id   <= 16'd0;
            vdm_routing_type   <= 3'd0;
            vdm_payload_word   <= {AXI_DATA_WIDTH{1'b0}};
            vdm_payload_strb   <= {AXI_STRB_WIDTH{1'b0}};
            packet_drop_valid  <= 1'b0;
            packet_drop_reason <= PD_NONE;
            last_decoded_vdm   <= 32'd0;
            parser_state       <= PS_IDLE;
        end else begin
            // Default: de-assert single-cycle pulses
            vdm_valid          <= 1'b0;
            packet_drop_valid  <= 1'b0;
            packet_drop_reason <= PD_NONE;
            // parser_state tracks the decode FSM: it advances to PS_DECODE while a
            // TLP's beats are buffered and resolves to PS_VALID / PS_DROP on accept.
            if (first_beat_seen && !tlp_accept)
                parser_state <= PS_DECODE;

            if (tlp_accept) begin
                // Decode trigger: ingress declares the TLP legal and in-bounds.
                if (!decode_vdm_ok) begin
                    // PD_UNSUPPORTED_VDM: msg_code/vendor/vdm_code/routing/TC mismatch
                    packet_drop_valid  <= 1'b1;
                    packet_drop_reason <= PD_UNSUPPORTED_VDM;
                    parser_state       <= PS_DROP;
                end else if (drop_bad_pad) begin
                    // PD_BAD_PAD_OR_ALIGNMENT: pad count or TU size constraint violated
                    packet_drop_valid  <= 1'b1;
                    packet_drop_reason <= PD_BAD_PAD_OR_ALIGNMENT;
                    parser_state       <= PS_DROP;
                end else begin
                    // Valid VDM packet: emit the fully decoded bundle
                    vdm_valid          <= 1'b1;
                    parser_state       <= PS_VALID;
                    vdm_word           <= first_beat_q;
                    vdm_payload_offset <= PAYLOAD_OFFSET;
                    vdm_payload_bytes  <= payload_bytes_raw;
                    // First 16B header snapshot: low HDR_BITS of beat 0
                    vdm_first_header   <= first_hdr_slice;
                    // Last 16B header snapshot: low HDR_BITS of the last beat
                    // (equals first_beat_q when single-beat TLP)
                    vdm_last_header    <= last_hdr_slice;
                    vdm_requester_id   <= requester_id;
                    vdm_routing_type   <= routing_type;
                    // payload_word / payload_strb: for single-beat TLPs the
                    // payload occupies bytes 16-31 of beat 0 (upper 128b /
                    // strb[31:16]); for multi-beat TLPs forward the last beat.
                    vdm_payload_word   <= multi_beat ? last_beat_q : first_beat_q;
                    vdm_payload_strb   <= multi_beat ? last_strb_q : first_strb_q;
                end
                // Update the DEBUG_CTX mirror on every decode attempt
                // expr: (message_code<<24)|(vendor_id<<8)|vdm_code  (SSOT)
                last_decoded_vdm <= {message_code, vendor_id, vdm_code};
            end
        end
    end

endmodule
`default_nettype wire
