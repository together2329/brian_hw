// =============================================================================
// mctp_rx_full — FULL-ASSEMBLER INTEGRATION: every proven contract group fused
// into one DUT. gate + 2-context key lane + start/single/continuation + per-ctx
// mod-4 sequence + byte-exact SRAM payload (per-context region) + first/last TLP
// header snapshot + EOM descriptor publish into a queue + drop classification.
//
// Contract groups (each proven as a slice; here they must COEXIST):
//   GATE(hdr_ok)  KEY/CTX  START/SINGLE  SEQ  PAYLOAD(byte-exact)  HDR(first/last)
//   DESC(no-early + content + queue-full)  DROP(packet vs assembly)
//
// Mutations: INJECT_BASE_BUG INJECT_SEQ_BUG INJECT_FIRST_BUG
//            INJECT_NOEARLY_BUG INJECT_FULL_BUG INJECT_GATE_BUG
// =============================================================================
module mctp_rx_full #(parameter int REGION = 4, parameter int QDEPTH = 2) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       pkt_valid,
  input  logic       pkt_ctx,
  input  logic       pkt_som,
  input  logic       pkt_eom,
  input  logic       pkt_hdr_ok,
  input  logic [1:0] pkt_seq,
  input  logic [7:0] pkt_hdr,
  input  logic [7:0] pkt_byte,
  input  logic       desc_pop,
  // SRAM payload write
  output logic       wr_en,
  output logic [2:0] wr_addr,
  output logic [7:0] wr_byte,
  // descriptor queue head
  output logic       desc_valid,
  output logic       desc_ctx,
  output logic [7:0] desc_first,
  output logic [7:0] desc_last,
  output logic [7:0] desc_len,
  output logic [2:0] desc_base,
  // status
  output logic       drop_pulse,
  output logic       is_assembly_drop
);
  // per-context state
  logic       c0_v,    c1_v;
  logic [1:0] c0_eseq, c1_eseq;
  logic [2:0] c0_wp,   c1_wp;
  logic [7:0] c0_first,c1_first, c0_last, c1_last;
  logic [7:0] mem [0:2*REGION-1];
  // descriptor queue
  logic        q_ctx   [0:QDEPTH-1];
  logic [7:0]  q_first [0:QDEPTH-1], q_last [0:QDEPTH-1], q_len [0:QDEPTH-1];
  logic [2:0]  q_base  [0:QDEPTH-1];
  logic [0:0]  head, tail;
  logic [1:0]  q_cnt;

  wire accept = pkt_valid;
`ifdef INJECT_GATE_BUG
  wire ev = accept;                                  // BUG: ignore header-ok gate
`else
  wire ev = accept & pkt_hdr_ok;
`endif
  wire        cv     = pkt_ctx ? c1_v     : c0_v;
  wire [1:0]  ceseq  = pkt_ctx ? c1_eseq  : c0_eseq;
  wire [2:0]  cwp    = pkt_ctx ? c1_wp    : c0_wp;
  wire [7:0]  cfirst = pkt_ctx ? c1_first : c0_first;

  wire is_single = ev &  pkt_som &  pkt_eom;
  wire is_start  = ev &  pkt_som & ~pkt_eom;
  wire is_cont   = ev & ~pkt_som &  cv;

`ifdef INJECT_SEQ_BUG
  wire seq_ok = 1'b1;
`else
  wire seq_ok = (pkt_seq == ceseq);
`endif
  wire room = (cwp < REGION[2:0]);

  wire [2:0] off  = pkt_som ? 3'd0 : cwp;
`ifdef INJECT_BASE_BUG
  wire [2:0] base = 3'd0;                             // BUG: ignore context region base
`else
  wire [2:0] base = pkt_ctx ? REGION[2:0] : 3'd0;
`endif
  assign wr_en   = is_single | is_start | (is_cont & seq_ok & room);
  assign wr_addr = base + off;
  assign wr_byte = pkt_byte;

  wire commit_ev = is_single | (is_cont & seq_ok & room & pkt_eom);
  wire qroom     = (q_cnt < QDEPTH[1:0]);
`ifdef INJECT_FULL_BUG
  wire wpush = commit_ev;                             // BUG: push even if queue full
`else
  wire wpush = commit_ev & qroom;
`endif
`ifdef INJECT_NOEARLY_BUG
  // BUG: also "commit" on a non-EOM continuation
  wire wpush_eff = wpush | (is_cont & seq_ok & room & ~pkt_eom & qroom);
`else
  wire wpush_eff = wpush;
`endif
  wire wpop = desc_pop & desc_valid;

  wire [7:0] push_first = is_single ? pkt_hdr : cfirst;
  wire [7:0] push_last  = pkt_hdr;
  wire [7:0] push_len   = is_single ? 8'd1 : (cwp + 8'd1);

  // drops
  wire gate_drop  = accept & ~pkt_hdr_ok;            // packet drop (uses REAL hdr_ok)
  wire stray_drop = ev & ~pkt_som & ~cv;             // continuation with no active ctx
  wire seq_drop   = is_cont & ~seq_ok;               // assembly drop
  wire ovf_drop   = is_cont & seq_ok & ~room;        // assembly drop
  wire dfull_drop = commit_ev & ~qroom;              // assembly drop
  assign drop_pulse       = gate_drop | stray_drop | seq_drop | ovf_drop | dfull_drop;
  assign is_assembly_drop = seq_drop | ovf_drop | dfull_drop;

  assign desc_valid = (q_cnt != 2'd0);
  assign desc_ctx   = q_ctx[head];
  assign desc_first = q_first[head];
  assign desc_last  = q_last[head];
  assign desc_len   = q_len[head];
  assign desc_base  = q_base[head];

  // next state for the addressed context
  logic       upd, nv;
  logic [1:0] neseq;
  logic [2:0] nwp;
  logic [7:0] nfirst, nlast;
  always @* begin
    upd=1'b0; nv=cv; neseq=ceseq; nwp=cwp; nfirst=cfirst; nlast=(pkt_ctx?c1_last:c0_last);
    if (is_single)     begin upd=1'b1; nv=1'b0; nwp=3'd0; nfirst=pkt_hdr; nlast=pkt_hdr; end
    else if (is_start) begin upd=1'b1; nv=1'b1; neseq=pkt_seq+2'd1; nwp=3'd1; nfirst=pkt_hdr; nlast=pkt_hdr; end
    else if (is_cont) begin
      if (seq_ok && room) begin
        upd=1'b1; nwp=cwp+3'd1; neseq=ceseq+2'd1; nv=~pkt_eom; nlast=pkt_hdr;
`ifdef INJECT_FIRST_BUG
        nfirst=pkt_hdr;                              // BUG: continuation overwrites first
`endif
      end else begin
        upd=1'b1; nv=1'b0;                            // seq/overflow -> drop ctx
      end
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      c0_v<=0; c1_v<=0; c0_eseq<=0; c1_eseq<=0; c0_wp<=0; c1_wp<=0;
      c0_first<=0; c1_first<=0; c0_last<=0; c1_last<=0;
      head<=0; tail<=0; q_cnt<=0;
    end else begin
      if (wr_en) mem[wr_addr] <= pkt_byte;
      if (upd) begin
        if (pkt_ctx==1'b0) begin c0_v<=nv; c0_eseq<=neseq; c0_wp<=nwp; c0_first<=nfirst; c0_last<=nlast; end
        else               begin c1_v<=nv; c1_eseq<=neseq; c1_wp<=nwp; c1_first<=nfirst; c1_last<=nlast; end
      end
      if (wpush_eff) begin
        q_ctx[tail]<=pkt_ctx; q_first[tail]<=push_first; q_last[tail]<=push_last;
        q_len[tail]<=push_len; q_base[tail]<=base; tail<=tail+1'b1;
      end
      if (wpop) head<=head+1'b1;
      q_cnt <= q_cnt + (wpush_eff ? 2'd1 : 2'd0) - (wpop ? 2'd1 : 2'd0);
    end
  end

`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  wire hdr_upd = is_single | is_start | (is_cont & seq_ok & room);  // when last_hdr := pkt_hdr

  always @(posedge clk) if (f_past_valid && rst_n && $past(rst_n)) begin
    // C-GATE: a bad-header packet writes no payload
    if (accept && !pkt_hdr_ok) assert (!wr_en);
    // C-ISO: payload write stays in the addressed context's region
    if (wr_en) begin
      assert (wr_addr >= (pkt_ctx ? REGION[2:0] : 3'd0));
      assert (wr_addr <= (pkt_ctx ? REGION[2:0] : 3'd0) + (REGION[2:0]-3'd1));
    end
    // C-SEQ: an out-of-sequence continuation writes no payload
    if (is_cont && (pkt_seq != ceseq)) assert (!wr_en);
    // C-DESC-NO-EARLY: a descriptor is queued only on an EOM packet
    if (wpush_eff) assert (pkt_valid && pkt_eom);
    // C-DESC-CONTENT: published last/first reflect this packet/state
    if (wpush_eff) begin
      assert (push_last == pkt_hdr);
      if (!is_single) assert (push_first == cfirst);
    end
    // C-HDR-FIRST: a continuation must not change the addressed context's first
    if ($past(is_cont) && ($past(pkt_ctx)==1'b0)) assert (c0_first == $past(c0_first));
    if ($past(is_cont) && ($past(pkt_ctx)==1'b1)) assert (c1_first == $past(c1_first));
    // C-HDR-LAST: last == the most recent accepted packet of that context
    if ($past(hdr_upd) && ($past(pkt_ctx)==1'b0)) assert (c0_last == $past(pkt_hdr));
    if ($past(hdr_upd) && ($past(pkt_ctx)==1'b1)) assert (c1_last == $past(pkt_hdr));
    // bounds (aux invariants)
    assert (q_cnt <= QDEPTH[1:0]);
    assert (c0_wp <= REGION[2:0]);
    assert (c1_wp <= REGION[2:0]);
  end

  // ---- C-BYTE: symbolic per-context byte-exact payload (carried from mctp_rx_top) ----
  (* anyconst *) reg       f_ctx;
  (* anyconst *) reg [2:0] f_k;
  reg        f_have;
  reg [7:0]  f_exp;
  wire [2:0] cur_off = pkt_som ? 3'd0 : cwp;
  always @(posedge clk) assume (f_k < REGION[2:0]);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) f_have <= 1'b0;
    else if (ev && (pkt_ctx==f_ctx) && pkt_som) begin
      f_have <= (f_k==3'd0);  f_exp <= pkt_byte;            // SOM byte = index 0; restarts tracker
    end else if (wr_en && (pkt_ctx==f_ctx) && (cur_off==f_k)) begin
      f_have <= 1'b1;          f_exp <= pkt_byte;
    end
  end
  wire [2:0] f_addr   = (f_ctx ? REGION[2:0] : 3'd0) + f_k;
  wire [2:0] f_cwp    = f_ctx ? c1_wp : c0_wp;
  wire       f_active = f_ctx ? c1_v  : c0_v;
  always @(posedge clk) if (f_past_valid && rst_n && $past(rst_n)) begin
    if (f_have) assert (!f_active || (f_k < f_cwp));
    if (f_have) assert (mem[f_addr] == f_exp);             // byte-exact across interleaving
  end

  always @(posedge clk) if (rst_n) begin
    cover (c0_v && c1_v);            // two contexts live (interleaving)
    cover (desc_valid);             // a descriptor published
    cover (is_assembly_drop);       // an assembly drop reachable
  end
`endif
endmodule
