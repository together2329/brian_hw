// =============================================================================
// mctp_rx_top — INTEGRATION of multi-context + byte-exact payload + per-ctx seq.
// The real coupling neither slice proved alone: two contexts' packets interleave,
// each writing payload bytes byte-exact into its OWN SRAM region, without
// corrupting the other context. (mctp_rx_mc proved context-state isolation;
// mctp_rx_payload proved byte-exact for one context; this proves them TOGETHER.)
//
//   pkt_ctx selects the context lane (key%2 in the real IP). Each context:
//   SOM starts, continuations append (per-ctx mod-4 seq), EOM commits.
//   context c writes its byte j to mem[c*REGION + j].
//
// Mutation hooks: INJECT_BASE_BUG INJECT_XCTX_BUG INJECT_SEQ_BUG
// =============================================================================
module mctp_rx_top #(parameter int REGION = 4) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       pkt_valid,
  input  logic       pkt_ctx,            // which context lane (0/1)
  input  logic       pkt_som,
  input  logic       pkt_eom,
  input  logic [1:0] pkt_seq,
  input  logic [7:0] pkt_byte,
  output logic       wr_en,
  output logic [2:0] wr_addr,
  output logic [7:0] wr_byte,
  output logic       msg_valid,
  output logic       msg_ctx,
  output logic [7:0] msg_len,
  output logic [2:0] msg_base,
  output logic       drop_pulse
);
  logic       c0_v,    c1_v;
  logic [1:0] c0_eseq, c1_eseq;
  logic [2:0] c0_wp,   c1_wp;            // bytes written so far for the context (0..REGION)
  logic [7:0] mem [0:2*REGION-1];

  wire accept = pkt_valid;
  wire cv     = pkt_ctx ? c1_v    : c0_v;
  wire [1:0] ceseq = pkt_ctx ? c1_eseq : c0_eseq;
  wire [2:0] cwp   = pkt_ctx ? c1_wp   : c0_wp;

  wire is_single = accept &  pkt_som &  pkt_eom;
  wire is_start  = accept &  pkt_som & ~pkt_eom;
  wire is_cont   = accept & ~pkt_som &  cv;

`ifdef INJECT_SEQ_BUG
  wire seq_ok = 1'b1;                                 // BUG: ignore per-context sequence
`else
  wire seq_ok = (pkt_seq == ceseq);
`endif
  wire room = (cwp < REGION[2:0]);

  wire [2:0] off  = (pkt_som) ? 3'd0 : cwp;           // byte index within the message
`ifdef INJECT_BASE_BUG
  wire [2:0] base = 3'd0;                             // BUG: ignore context base (all to region 0)
`else
  wire [2:0] base = pkt_ctx ? REGION[2:0] : 3'd0;
`endif
  wire [2:0] waddr = base + off;

  wire payload_ev = is_single | is_start | (is_cont & seq_ok & room);
  assign wr_en   = payload_ev;
  assign wr_addr = waddr;
  assign wr_byte = pkt_byte;

  wire commit_ev = is_single | (is_cont & seq_ok & room & pkt_eom);
  wire seq_drop  = is_cont & ~seq_ok;

  // next state for the addressed context
  logic       upd, nv;
  logic [1:0] neseq;
  logic [2:0] nwp;
  always @* begin
    upd=1'b0; nv=cv; neseq=ceseq; nwp=cwp;
    if (is_single)      begin upd=1'b1; nv=1'b0; nwp=3'd0;            end
    else if (is_start)  begin upd=1'b1; nv=1'b1; neseq=pkt_seq+2'd1; nwp=3'd1; end
    else if (is_cont) begin
      if (seq_ok && room) begin upd=1'b1; nwp=cwp+3'd1; neseq=ceseq+2'd1; nv=~pkt_eom; end
      else                begin upd=1'b1; nv=1'b0;                    end   // seq/overflow -> drop ctx
    end
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      c0_v<=1'b0; c1_v<=1'b0; c0_eseq<=2'd0; c1_eseq<=2'd0; c0_wp<=3'd0; c1_wp<=3'd0;
      msg_valid<=1'b0; msg_ctx<=1'b0; msg_len<=8'd0; msg_base<=3'd0; drop_pulse<=1'b0;
    end else begin
      msg_valid<=1'b0; drop_pulse<=1'b0;
      if (wr_en) mem[wr_addr] <= pkt_byte;
      if (upd) begin
        if (pkt_ctx==1'b0) begin c0_v<=nv; c0_eseq<=neseq; c0_wp<=nwp; end
        else               begin c1_v<=nv; c1_eseq<=neseq; c1_wp<=nwp; end
`ifdef INJECT_XCTX_BUG
        if (pkt_ctx==1'b1) c0_wp <= c0_wp + 3'd1;     // BUG: ctx1 activity bumps ctx0 pointer
`endif
      end
      if (commit_ev) begin
        msg_valid<=1'b1; msg_ctx<=pkt_ctx; msg_base<=base;
        msg_len <= is_single ? 8'd1 : (cwp + 8'd1);
      end
      if (seq_drop) drop_pulse<=1'b1;
    end
  end

`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  // C-INT-ISO: a payload write lands only in the addressed context's region
  always @(posedge clk) if (f_past_valid && rst_n) begin
    if (wr_en) begin
      assert (wr_addr >= (pkt_ctx ? REGION[2:0] : 3'd0));
      assert (wr_addr <= (pkt_ctx ? REGION[2:0] : 3'd0) + (REGION[2:0] - 3'd1));
    end
    // aux invariants (true by construction; strengthen induction)
    assert (c0_wp <= REGION[2:0]);
    assert (c1_wp <= REGION[2:0]);
    // C-INT-SEQ: an out-of-sequence continuation produces no payload write (dropped)
    if (is_cont && (pkt_seq != ceseq)) assert (!wr_en);
  end

  // C-INT-BYTE: symbolic (ctx, index) -> the byte for context f_ctx's index f_k
  // is stored at mem[f_ctx*REGION + f_k], regardless of the other context's
  // interleaved writes.
  (* anyconst *) reg       f_ctx;
  (* anyconst *) reg [2:0] f_k;
  reg       f_have;
  reg [7:0] f_exp;
  wire [2:0] cur_off = pkt_som ? 3'd0 : cwp;
  wire       this_is_f = payload_ev && (pkt_ctx == f_ctx) && (cur_off == f_k);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) f_have <= 1'b0;
    else if (accept && (pkt_ctx == f_ctx) && pkt_som) begin
      f_have <= (f_k == 3'd0);  f_exp <= pkt_byte;    // SOM byte = index 0; restarts the tracker
    end else if (this_is_f) begin
      f_have <= 1'b1;           f_exp <= pkt_byte;
    end
  end
  always @(posedge clk) assume (f_k < REGION[2:0]);   // symbolic index is a valid in-region offset
  wire [2:0] f_addr      = (f_ctx ? REGION[2:0] : 3'd0) + f_k;
  wire [2:0] f_cwp       = f_ctx ? c1_wp : c0_wp;
  wire       f_active    = f_ctx ? c1_v  : c0_v;
  always @(posedge clk) if (f_past_valid && rst_n) begin
    // aux (inductive strengthening): while the captured byte's context is active,
    // its write pointer is already past the captured index (so no later write
    // overwrites f_addr until the context restarts, which resets the tracker)
    if (f_have) assert (!f_active || (f_k < f_cwp));
    if (f_have) assert (mem[f_addr] == f_exp);        // byte-exact across interleaving
  end

  always @(posedge clk) if (rst_n) begin
    cover (c0_v && c1_v);                              // two contexts live at once (interleaving)
    cover (msg_valid);
  end
`endif
endmodule
