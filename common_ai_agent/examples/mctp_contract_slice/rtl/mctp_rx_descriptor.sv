// =============================================================================
// mctp_rx_descriptor — descriptor publish + first/last TLP header-snapshot queue.
// Reflects v3 spec §9.3/§9.5 and the §14 formal candidates:
//   * no descriptor is published before EOM
//   * first_hdr is written only by the accepted SOM packet
//   * last_hdr equals the most recent accepted packet for the context
//   * on EOM commit, a descriptor {first, last, len} is pushed to a small queue
//   * descriptor-queue-full on EOM is an assembly drop (no push) (§10.2 AD_DESCRIPTOR_FULL)
// Single context, 8-bit header proxy, DEPTH-deep descriptor queue.
//
// Mutation hooks: INJECT_NOEARLY_BUG INJECT_FIRST_BUG INJECT_LAST_BUG
//                 INJECT_CONTENT_BUG INJECT_FULL_BUG
// =============================================================================
module mctp_rx_descriptor #(parameter int DEPTH = 2) (
  input  logic       clk,
  input  logic       rst_n,
  input  logic       pkt_valid,
  input  logic       pkt_som,
  input  logic       pkt_eom,
  input  logic [7:0] pkt_hdr,
  input  logic       desc_pop,
  output logic [7:0] first_hdr,
  output logic [7:0] last_hdr,
  output logic       active,
  output logic       desc_push,
  output logic       desc_drop_full,
  output logic [7:0] push_first,
  output logic [7:0] push_last,
  output logic [7:0] push_len,
  output logic [1:0] q_cnt,
  output logic       desc_valid,
  output logic [7:0] desc_first,
  output logic [7:0] desc_last,
  output logic [7:0] desc_len
);
  logic [7:0] len;
  logic [7:0] q_first [0:DEPTH-1], q_last [0:DEPTH-1], q_len [0:DEPTH-1];
  logic [0:0] head, tail;

  wire accept    = pkt_valid;
  wire is_single = accept &  pkt_som &  pkt_eom;
  wire is_start  = accept &  pkt_som & ~pkt_eom;
  wire is_cont   = accept & ~pkt_som &  active;
  wire is_end    = is_cont & pkt_eom;
  wire room      = (q_cnt < DEPTH[1:0]);

`ifdef INJECT_NOEARLY_BUG
  wire publish_ev = is_single | is_cont;                 // BUG: publishes on any continuation
`else
  wire publish_ev = is_single | is_end;
`endif

`ifdef INJECT_FULL_BUG
  wire wpush = publish_ev;                               // BUG: push even when the queue is full
`else
  wire wpush = publish_ev & room;
`endif
  wire wpop  = desc_pop & desc_valid;

  assign desc_push      = wpush;
  assign desc_drop_full = publish_ev & ~room;
  assign push_last      = pkt_hdr;
  assign push_len       = is_single ? 8'd1 : (len + 8'd1);
`ifdef INJECT_CONTENT_BUG
  assign push_first     = is_single ? pkt_hdr : last_hdr;  // BUG: stores last header as first
`else
  assign push_first     = is_single ? pkt_hdr : first_hdr;
`endif

  assign desc_valid = (q_cnt != 2'd0);
  assign desc_first = q_first[head];
  assign desc_last  = q_last[head];
  assign desc_len   = q_len[head];

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active<=1'b0; len<=8'd0; first_hdr<=8'd0; last_hdr<=8'd0;
      q_cnt<=2'd0; head<=1'b0; tail<=1'b0;
    end else begin
      // header snapshot + length
      if (is_single) begin
        first_hdr<=pkt_hdr; last_hdr<=pkt_hdr; len<=8'd1; active<=1'b0;
      end else if (is_start) begin
        first_hdr<=pkt_hdr; last_hdr<=pkt_hdr; len<=8'd1; active<=1'b1;
      end else if (is_cont) begin
`ifdef INJECT_FIRST_BUG
        first_hdr<=pkt_hdr;                              // BUG: continuation overwrites first
`endif
`ifndef INJECT_LAST_BUG
        last_hdr<=pkt_hdr;                               // last = most recent accepted
`endif
        len<=len+8'd1;
        if (pkt_eom) active<=1'b0;
      end
      // descriptor queue
      if (wpush) begin
        q_first[tail]<=push_first; q_last[tail]<=push_last; q_len[tail]<=push_len;
        tail<=tail+1'b1;
      end
      if (wpop) head<=head+1'b1;
      q_cnt <= q_cnt + (wpush ? 2'd1 : 2'd0) - (wpop ? 2'd1 : 2'd0);
    end
  end

`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  always @(posedge clk) if (f_past_valid && rst_n && $past(rst_n)) begin
    // C-DESC-NO-EARLY: a descriptor is published only on an EOM packet
    if (desc_push) assert (pkt_valid && pkt_eom);
    // C-HDR-FIRST: SOM sets first_hdr; a continuation must not change it
    if ($past(is_start) || $past(is_single)) assert (first_hdr == $past(pkt_hdr));
    if ($past(is_cont))                       assert (first_hdr == $past(first_hdr));
    // C-HDR-LAST: last_hdr == the most recent accepted packet of the assembly
    if ($past(is_start) || $past(is_single) || $past(is_cont))
      assert (last_hdr == $past(pkt_hdr));
    // C-DESC-CONTENT: the published descriptor carries the right snapshots/length
    if (desc_push) begin
      assert (push_last == pkt_hdr);
      assert (push_len  == (is_single ? 8'd1 : (len + 8'd1)));
      if (!is_single) assert (push_first == first_hdr);
    end
    // C-DESC-FULL: the queue never overflows (full EOM -> drop, not overwrite)
    assert (q_cnt <= DEPTH[1:0]);
    // vacuity guards
    cover (desc_push && !is_single);            // a multi-packet descriptor publishes
    cover (desc_drop_full);                      // queue-full drop reachable
    cover (first_hdr != last_hdr && desc_push);  // first/last differ at publish (content matters)
  end
`endif
endmodule
