// =============================================================================
// mctp_rx_mc — multi-context RX assembler (deep-dive: §9 Assembly of v3 spec).
// Reflects the real MCTP requirements our toy slice simplified away:
//   * 3-field message key {source_eid, tag_owner, message_tag}   (v3 §9.1)
//   * CONTEXT_COUNT independent contexts + interleaving           (v3 §9.2/§9.3)
//   * per-context expected_seq, len, key                          (v3 §9.3)
//   * duplicate-SOM = assembly drop; table-full = packet drop     (v3 §9.2/§10)
// CONTEXT_COUNT = 2 (enough to prove interleaving isolation, keeps formal small).
// Payload kept as a byte count (SRAM packing is a separate stage).
//
// Mutation hooks: INJECT_ISO_BUG INJECT_ALLOC_BUG INJECT_DUP_BUG INJECT_SEQ_BUG
// =============================================================================
module mctp_rx_mc (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       pkt_valid,
  output logic       pkt_ready,
  input  logic       pkt_som,
  input  logic       pkt_eom,
  input  logic [1:0] pkt_seq,
  input  logic [1:0] pkt_src,        // source_eid (key field)
  input  logic       pkt_to,         // tag_owner  (key field)
  input  logic [1:0] pkt_tag,        // message_tag(key field)
  input  logic       pkt_hdr_ok,
  input  logic       msg_ready,
  output logic       msg_valid,
  output logic [4:0] msg_key,
  output logic [7:0] msg_len,
  output logic       drop_pulse
);
  localparam int KW = 5;

  // two independent contexts
  logic        c0_v, c1_v;
  logic [KW-1:0] c0_key, c1_key;
  logic [1:0]  c0_eseq, c1_eseq;
  logic [7:0]  c0_len, c1_len;

  assign pkt_ready = !msg_valid;                  // hold input while a message awaits handshake
  wire pkt_accept = pkt_valid & pkt_ready;
  wire [KW-1:0] key = {pkt_src, pkt_to, pkt_tag};

  wire m0 = c0_v && (c0_key == key);
  wire m1 = c1_v && (c1_key == key);
  wire any_m = m0 | m1;
  wire midx  = m1;                                 // matched index (valid when any_m)
  wire f0 = ~c0_v, f1 = ~c1_v;
  wire any_f = f0 | f1;
  wire fidx = f0 ? 1'b0 : 1'b1;                    // free index (valid when any_f)

  wire ev        = pkt_accept & pkt_hdr_ok;
  wire is_single = ev &  pkt_som &  pkt_eom;
  wire is_start  = ev &  pkt_som & ~pkt_eom;
  wire is_cont   = ev & ~pkt_som;

  wire [1:0] m_eseq = m0 ? c0_eseq : c1_eseq;
  wire [7:0] m_len  = m0 ? c0_len  : c1_len;

`ifdef INJECT_SEQ_BUG
  wire seq_ok = 1'b1;                              // BUG: ignore per-context sequence
`else
  wire seq_ok = (pkt_seq == m_eseq);
`endif

  // ---- combinational decision: which context to write, with what ----
  logic        tw, we, nv;
  logic [KW-1:0] nk;
  logic [1:0]  nseq;
  logic [7:0]  nlen;
  logic        do_drop, do_commit;
  logic [7:0]  clen;
  logic [KW-1:0] ckey;

  always @* begin
    tw=1'b0; we=1'b0; nv=1'b0; nk=key; nseq=2'd0; nlen=8'd0;
    do_drop=1'b0; do_commit=1'b0; clen=8'd0; ckey=key;
    if (is_single) begin
      do_commit=1'b1; clen=8'd1; ckey=key;
      if (any_m) begin                              // dup key -> abort matched ctx
        tw=midx; we=1'b1; nv=1'b0; do_drop=1'b1;
`ifdef INJECT_DUP_BUG
        we=1'b0; do_drop=1'b0;                      // BUG: ignore duplicate, leave ctx
`endif
      end
    end else if (is_start) begin
      if (any_m) begin                              // duplicate SOM -> abort + restart slot
        tw=midx; we=1'b1; nv=1'b1; nk=key; nseq=pkt_seq+2'd1; nlen=8'd1; do_drop=1'b1;
`ifdef INJECT_DUP_BUG
        do_drop=1'b0; nseq=m_eseq; nlen=m_len+8'd1; // BUG: append to existing, no abort
`endif
      end else if (any_f) begin                     // new key -> allocate free slot
        tw=fidx; we=1'b1; nv=1'b1; nk=key; nseq=pkt_seq+2'd1; nlen=8'd1;
`ifdef INJECT_ALLOC_BUG
        tw=1'b0;                                    // BUG: ignore free index, always slot0
`endif
      end else begin                                // table full -> packet drop
        do_drop=1'b1;
`ifdef INJECT_ALLOC_BUG
        tw=1'b0; we=1'b1; nv=1'b1; nk=key; nseq=pkt_seq+2'd1; nlen=8'd1; do_drop=1'b0; // BUG: overwrite slot0
`endif
      end
    end else if (is_cont) begin
      if (any_m) begin
        if (seq_ok) begin
          tw=midx; we=1'b1; nk=key;
          if (pkt_eom) begin nv=1'b0; do_commit=1'b1; clen=m_len+8'd1; ckey=key; end
          else         begin nv=1'b1; nseq=m_eseq+2'd1; nlen=m_len+8'd1;          end
        end else begin                              // per-context seq mismatch -> assembly drop
          tw=midx; we=1'b1; nv=1'b0; do_drop=1'b1;
        end
      end else begin
        do_drop=1'b1;                               // unexpected middle/end -> packet drop
      end
    end
  end

  wire wr0 = we && (tw == 1'b0);
  wire wr1 = we && (tw == 1'b1);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      c0_v<=1'b0; c1_v<=1'b0; c0_key<='0; c1_key<='0;
      c0_eseq<=2'd0; c1_eseq<=2'd0; c0_len<=8'd0; c1_len<=8'd0;
      msg_valid<=1'b0; msg_len<=8'd0; msg_key<='0; drop_pulse<=1'b0;
    end else begin
      drop_pulse <= do_drop;
      if (msg_valid && msg_ready) msg_valid <= 1'b0;
      if (do_commit) begin msg_valid <= 1'b1; msg_len <= clen; msg_key <= ckey; end

      // context 0
      if (wr0) begin c0_v<=nv; c0_key<=nk; c0_eseq<=nseq; c0_len<=nlen; end
`ifdef INJECT_ISO_BUG
      else if (wr1) c0_len <= 8'd0;                 // BUG: writing ctx1 clobbers ctx0
`endif
      // context 1
      if (wr1) begin c1_v<=nv; c1_key<=nk; c1_eseq<=nseq; c1_len<=nlen; end
    end
  end

`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  // real (un-mutated) per-context seq-mismatch antecedent
  wire a_seqbad = is_cont & any_m & (pkt_seq != m_eseq);

  always @(posedge clk) begin
    if (f_past_valid && rst_n && $past(rst_n)) begin
      // C-ISO: any context NOT written this cycle is byte-for-byte unchanged
      if (!$past(wr0)) begin
        assert (c0_v==$past(c0_v) && c0_key==$past(c0_key) &&
                c0_eseq==$past(c0_eseq) && c0_len==$past(c0_len));
      end
      if (!$past(wr1)) begin
        assert (c1_v==$past(c1_v) && c1_key==$past(c1_key) &&
                c1_eseq==$past(c1_eseq) && c1_len==$past(c1_len));
      end
      // C-ALLOC-FULL: a new-key start with no free slot changes nothing + drops
      if ($past(is_start) && !$past(any_m) && !$past(any_f)) begin
        assert (drop_pulse);
        assert (c0_v==$past(c0_v) && c0_key==$past(c0_key) && c0_len==$past(c0_len));
        assert (c1_v==$past(c1_v) && c1_key==$past(c1_key) && c1_len==$past(c1_len));
      end
      // C-ALLOC-NEW: a new-key allocation must land on a slot that was FREE
      // (must not overwrite a live, different-key context)
      if ($past(is_start) && !$past(any_m) && $past(any_f)) begin
        if ($past(wr0)) assert (!$past(c0_v));
        if ($past(wr1)) assert (!$past(c1_v));
      end
      // C-DUP-SOM: SOM for an already-active key is an abort (drop), never a silent append
      if ($past(is_start) && $past(any_m)) assert (drop_pulse);
      // C-SEQ-PERCTX: an out-of-sequence continuation aborts that context, never commits
      if ($past(a_seqbad)) begin
        assert (drop_pulse);
        assert (!msg_valid);
      end
    end
  end

  // vacuity / reachability guards (the interesting one: two contexts live at once)
  always @(posedge clk) if (rst_n) begin
    cover (c0_v && c1_v && (c0_key != c1_key));      // INTERLEAVING actually reachable
    cover (is_start && !any_m && !any_f);            // table full reachable
    cover (is_start && any_m);                       // duplicate SOM reachable
    cover (a_seqbad);                                // per-ctx seq mismatch reachable
    cover (do_commit);
  end
`endif
endmodule
