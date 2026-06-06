// =============================================================================
// mctp_rx_assembler — unified single-context RX assembler, 12 contracts.
// packet stream -> message. 1 byte payload/packet, bounded buffer DEPTH.
// Key simplified to pkt_tag. Formal assertions are EMBEDDED under `ifdef FORMAL`
// so they observe internal state (len_q, sum_q, ...) natively — no debug ports,
// no `bind` (yosys-native ignores bind).
//
// Per-contract mutation hooks (define one to break exactly that contract):
//   INJECT_GATE_BUG INJECT_KEY_BUG INJECT_START_BUG INJECT_SINGLE_BUG
//   INJECT_SEQ_BUG  INJECT_PAYLOAD_BUG INJECT_END_BUG INJECT_DROP_BUG
//   INJECT_OUT_BUG  INJECT_RESET_BUG INJECT_STATUS_BUG
// =============================================================================
module mctp_rx_assembler #(parameter int DEPTH = 4) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       flush,
  input  logic       pkt_valid,
  output logic       pkt_ready,
  input  logic       pkt_som,
  input  logic       pkt_eom,
  input  logic [1:0] pkt_seq,
  input  logic [2:0] pkt_tag,
  input  logic       pkt_hdr_ok,
  input  logic [7:0] pkt_data,
  input  logic       msg_ready,
  output logic       msg_valid,
  output logic [7:0] msg_len,
  output logic [2:0] msg_tag,
  output logic [7:0] msg_sum,
  output logic       drop_pulse,
  output logic       ovf,
  output logic       context_active,
  output logic [1:0] expected_seq,
  output logic [2:0] ctx_tag,
  output logic [7:0] commit_count,
  output logic [7:0] drop_count
);
  logic [7:0] len_q, sum_q;

  assign pkt_ready = !msg_valid;                 // OUT: no new input while output pending
  wire pkt_accept = pkt_valid & pkt_ready;

`ifdef INJECT_GATE_BUG
  wire hdr_ok_eff = 1'b1;                         // BUG: ignore bad header
`else
  wire hdr_ok_eff = pkt_hdr_ok;
`endif
`ifdef INJECT_KEY_BUG
  wire key_ok_eff = 1'b1;                         // BUG: ignore tag mismatch
`else
  wire key_ok_eff = (pkt_tag == ctx_tag);
`endif
`ifdef INJECT_SEQ_BUG
  wire seq_ok_eff = 1'b1;                         // BUG: ignore sequence mismatch
`else
  wire seq_ok_eff = (pkt_seq == expected_seq);
`endif

`ifdef INJECT_STATUS_BUG
  `define DROP_INC drop_count <= drop_count            // BUG: drops not counted
`else
  `define DROP_INC drop_count <= drop_count + 8'd1
`endif

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      expected_seq <= 2'd0; ctx_tag <= 3'd0; len_q <= 8'd0; sum_q <= 8'd0;
      msg_valid <= 1'b0; msg_len <= 8'd0; msg_tag <= 3'd0; msg_sum <= 8'd0;
      drop_pulse <= 1'b0; ovf <= 1'b0; commit_count <= 8'd0; drop_count <= 8'd0;
`ifdef INJECT_RESET_BUG
      context_active <= context_active;            // BUG: reset does not clear context
`else
      context_active <= 1'b0;
`endif
    end else begin
      drop_pulse <= 1'b0;
      ovf        <= 1'b0;

      if (msg_valid && msg_ready) msg_valid <= 1'b0;  // OUT: release on handshake

      if (flush) begin
        if (context_active) begin drop_pulse <= 1'b1; `DROP_INC; end
        context_active <= 1'b0; len_q <= 8'd0; sum_q <= 8'd0;
      end else if (pkt_accept) begin
        if (!hdr_ok_eff) begin
          drop_pulse <= 1'b1; `DROP_INC;       // GATE
        end else if (pkt_som && pkt_eom) begin                        // SINGLE
          if (context_active) begin drop_pulse <= 1'b1; `DROP_INC; end
          msg_valid <= 1'b1; msg_len <= 8'd1; msg_tag <= pkt_tag; msg_sum <= pkt_data;
          commit_count <= commit_count + 8'd1;
`ifdef INJECT_SINGLE_BUG
          context_active <= 1'b1;                                     // BUG: stale context
`else
          context_active <= 1'b0;
`endif
          len_q <= 8'd0; sum_q <= 8'd0;
        end else if (pkt_som && !pkt_eom) begin                       // START
          if (context_active) begin drop_pulse <= 1'b1; `DROP_INC; end
`ifdef INJECT_START_BUG
          msg_valid <= 1'b1; msg_len <= 8'd1; msg_tag <= pkt_tag; msg_sum <= pkt_data;
          commit_count <= commit_count + 8'd1;                       // BUG: early commit
`endif
          context_active <= 1'b1; ctx_tag <= pkt_tag; expected_seq <= pkt_seq + 2'd1;
          len_q <= 8'd1; sum_q <= pkt_data;
        end else begin                                                // continuation
          if (!context_active) begin
            drop_pulse <= 1'b1; `DROP_INC;     // GATE: stray middle/end
          end else if (!key_ok_eff) begin
            drop_pulse <= 1'b1; `DROP_INC;     // KEY: foreign tag -> ignore
          end else if (!seq_ok_eff) begin
            drop_pulse <= 1'b1; `DROP_INC;     // SEQ: out of sequence -> drop
            context_active <= 1'b0;
`ifdef INJECT_DROP_BUG
                                                                      // BUG: stale payload (no clear)
`else
            len_q <= 8'd0; sum_q <= 8'd0;
`endif
          end else if (len_q == DEPTH[7:0]) begin
            ovf <= 1'b1; drop_pulse <= 1'b1; `DROP_INC;   // PAYLOAD overflow
            context_active <= 1'b0; len_q <= 8'd0; sum_q <= 8'd0;
          end else if (pkt_eom) begin                                 // END commit
            msg_valid <= 1'b1;
`ifdef INJECT_PAYLOAD_BUG
            msg_len <= len_q + 8'd2;                                  // BUG: length miscount
`else
            msg_len <= len_q + 8'd1;
`endif
            msg_tag <= ctx_tag; msg_sum <= sum_q + pkt_data;
            commit_count <= commit_count + 8'd1;
`ifdef INJECT_END_BUG
            context_active <= 1'b1;                                   // BUG: context not cleared
`else
            context_active <= 1'b0;
`endif
            len_q <= 8'd0; sum_q <= 8'd0;
          end else begin                                              // CONT/PAYLOAD append
            len_q <= len_q + 8'd1; sum_q <= sum_q + pkt_data; expected_seq <= expected_seq + 2'd1;
          end
        end
      end

      // STATUS mutation is expressed via the `DROP_INC macro (single, unambiguous)
`ifdef INJECT_OUT_BUG
      if (msg_valid && !msg_ready) msg_len <= msg_len + 8'd1;         // BUG: output moves under backpressure
`endif
    end
  end

// =============================================================================
// Embedded formal contracts (open with -DFORMAL). They reference internal
// len_q/sum_q directly — no debug ports, no bind.
// =============================================================================
`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  // assume a clean power-on reset so proofs start from the defined reset state
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  wire a_gate   = pkt_accept & ~pkt_hdr_ok;
  wire a_unexp  = pkt_accept &  pkt_hdr_ok & ~pkt_som & ~context_active;
  wire a_single = pkt_accept &  pkt_hdr_ok &  pkt_som &  pkt_eom;
  wire a_start  = pkt_accept &  pkt_hdr_ok &  pkt_som & ~pkt_eom;
  wire a_cont   = pkt_accept &  pkt_hdr_ok & ~pkt_som &  context_active;
  wire a_key    = a_cont & (pkt_tag != ctx_tag);
  wire a_okkey  = a_cont & (pkt_tag == ctx_tag);
  wire a_seq    = a_okkey & (pkt_seq != expected_seq);
  wire a_inseq  = a_okkey & (pkt_seq == expected_seq);
  wire a_ovf    = a_inseq & (len_q == DEPTH[7:0]);
  wire a_end    = a_inseq & (len_q != DEPTH[7:0]) &  pkt_eom;
  wire a_append = a_inseq & (len_q != DEPTH[7:0]) & ~pkt_eom;

  always @(posedge clk) begin
    if (f_past_valid && rst_n && $past(rst_n) && !$past(flush)) begin
      // C-ASM-GATE
      if ($past(a_gate) || $past(a_unexp)) begin
        assert (drop_pulse);
        assert (context_active == $past(context_active));
        assert (commit_count  == $past(commit_count));
        assert (len_q         == $past(len_q));
      end
      // C-ASM-KEY
      if ($past(a_key)) begin
        assert (drop_pulse);
        assert (context_active);
        assert (len_q        == $past(len_q));
        assert (expected_seq == $past(expected_seq));
        assert (ctx_tag      == $past(ctx_tag));
        assert (commit_count == $past(commit_count));
      end
      // C-ASM-START
      if ($past(a_start)) begin
        assert (context_active);
        assert (commit_count == $past(commit_count));
      end
      // C-ASM-SINGLE
      if ($past(a_single)) begin
        assert (msg_valid);
        assert (!context_active);
        assert (commit_count == $past(commit_count) + 8'd1);
      end
      // C-ASM-SEQ-OOS-DROP
      if ($past(a_seq)) begin
        assert (drop_pulse);
        assert (!context_active);
        assert (commit_count == $past(commit_count));
      end
      // C-ASM-DROP-NO-STALE
      if ($past(a_seq) || $past(a_ovf)) begin
        assert (!context_active);
        assert (len_q == 8'd0);
      end
      // C-ASM-PAYLOAD (append increments; commit length exact)
      if ($past(a_append)) assert (len_q   == $past(len_q) + 8'd1);
      if ($past(a_end))    assert (msg_len == $past(len_q) + 8'd1);
      // C-ASM-END
      if ($past(a_end)) begin
        assert (msg_valid);
        assert (!context_active);
        assert (commit_count == $past(commit_count) + 8'd1);
      end
      // C-ASM-OUT (stable under backpressure)
      if ($past(msg_valid) && $past(!msg_ready)) begin
        assert (msg_valid);
        assert (msg_len == $past(msg_len));
        assert (msg_tag == $past(msg_tag));
        assert (msg_sum == $past(msg_sum));
      end
      // C-ASM-STATUS (drop_count tracks every drop)
      if (drop_pulse) assert (drop_count == $past(drop_count) + 8'd1);
    end
  end

  // C-ASM-RESET / C-ASM-FLUSH (checked across reset; no disable)
  always @(posedge clk) begin
    if (f_past_valid && $past(!rst_n)) begin
      assert (!context_active);
      assert (!msg_valid);
    end
    if (f_past_valid && rst_n && $past(rst_n) && $past(flush))
      assert (!context_active);
  end

  // vacuity guards
  always @(posedge clk) if (rst_n) begin
    cover (a_seq); cover (a_end); cover (a_key); cover (a_single);
    cover (a_start); cover (a_ovf); cover (msg_valid && !msg_ready); cover (drop_pulse);
  end
`endif
endmodule
