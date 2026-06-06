// =============================================================================
// mctp_rx_payload — payload byte-exact SRAM packer (deep-dive: v3 §9.4 / §14).
// Reflects the CONTENT-semantic requirement (not just byte count):
//   "for every published descriptor, every byte address base..base+len-1 is
//    written exactly as the corresponding assembled payload byte, no gap."
// One byte per beat, base = 0, small SRAM (DEPTH). Exposes an SRAM write port
// (wr_en/wr_addr/wr_byte) like v3 §6.5.
//
// The formal lane uses the SYMBOLIC-BYTE technique (an anyconst address proves
// the property for ALL addresses at once) — the abstraction noted in
// doc/wiki/formal-verification-evidence.md for data-heavy properties.
//
// Mutation hooks: INJECT_OFFSET_BUG INJECT_GAP_BUG INJECT_OVERWRITE_BUG INJECT_LOSS_BUG
// =============================================================================
module mctp_rx_payload #(parameter int AW = 3) (   // DEPTH = 8 bytes
  input  logic           clk,
  input  logic           rst_n,
  input  logic           in_valid,
  input  logic           in_som,
  input  logic           in_eom,
  input  logic [7:0]     in_byte,
  output logic           wr_en,
  output logic [AW-1:0]  wr_addr,
  output logic [7:0]     wr_byte,
  output logic           msg_valid,
  output logic [AW:0]    msg_len
);
  localparam int DEPTH = (1 << AW);
  logic [7:0]    mem [0:DEPTH-1];
  logic [AW-1:0] wp;        // write address pointer
  logic [AW:0]   cnt;       // logical byte index within the message
  logic          active;

  wire acc = in_valid;                       // always ready in this slice
  wire start = acc & in_som;
  wire body  = acc & (in_som | active);      // a payload byte to store

  wire [AW:0]   idx = in_som ? '0 : cnt;     // logical index of this byte (0-based)
  wire room = (idx < DEPTH[AW:0]);           // v3 §10.2: byte must fit in SRAM, else overflow-drop
  logic ovf;

  // write address (OFFSET/GAP/OVERWRITE bugs corrupt the addr<->index relation)
  logic [AW-1:0] wa;
  always @* begin
    wa = in_som ? '0 : wp;
`ifdef INJECT_OFFSET_BUG
    wa = wa + 1'b1;                           // BUG: every byte one slot too high
`endif
  end

`ifdef INJECT_LOSS_BUG
  assign wr_en = body & room & (idx != 3'd2); // BUG: silently drop byte index 2
`else
  assign wr_en = body & room;
`endif
  assign wr_addr = wa;
  assign wr_byte = in_byte;

  // next write pointer
  logic [AW-1:0] wp_n;
  always @* begin
    if (in_som)      wp_n = 'd1;
`ifdef INJECT_GAP_BUG
    else             wp_n = wp + 2'd2;        // BUG: leave a one-slot gap
`elsif INJECT_OVERWRITE_BUG
    else             wp_n = wp;               // BUG: never advance -> overwrite
`else
    else             wp_n = wp + 1'b1;
`endif
  end

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active<=1'b0; wp<=0; cnt<=0; msg_valid<=1'b0; msg_len<=0; ovf<=1'b0;
    end else begin
      msg_valid <= 1'b0;
      if (wr_en) mem[wa] <= in_byte;
      if (start) begin
        ovf <= 1'b0;                                  // new message (SOM byte always fits, idx 0)
        active <= ~in_eom; wp <= wp_n; cnt <= 'd1;
        if (in_eom) begin msg_valid<=1'b1; msg_len<='d1; active<=1'b0; end
      end else if (body) begin
        if (room) begin
          wp <= wp_n; cnt <= cnt + 1'b1;
          if (in_eom) begin msg_valid<=1'b1; msg_len<=cnt + 1'b1; active<=1'b0; end
        end else begin
          ovf <= 1'b1;                                // v3 §10.2 AD_MESSAGE_OVERFLOW: drop, no success
          if (in_eom) active <= 1'b0;
        end
      end
    end
  end

`ifdef FORMAL
  reg f_past_valid = 1'b0;
  always @(posedge clk) f_past_valid <= 1'b1;
  always @(posedge clk) if (!f_past_valid) assume (!rst_n);

  // ---- direct per-write contract: byte i is written to address i, value intact ----
  always @(posedge clk) begin
    if (f_past_valid && rst_n && $past(rst_n)) begin
      if ($past(body) && $past(room)) begin
        assert ($past(wr_en));                       // every in-range payload byte is written...
        assert ($past(wr_addr) == $past(idx[AW-1:0]));// ...to address == its index (no gap/offset)
        assert ($past(wr_byte) == $past(in_byte));    // ...with its own value
      end
    end
  end

  // ---- auxiliary invariants that strengthen k-induction (true by construction) ----
  always @(posedge clk) if (f_past_valid && rst_n) begin
    assert (cnt <= DEPTH[AW:0]);        // byte counter bounded by SRAM depth (no wrap)
    assert (wp == cnt[AW-1:0]);          // write pointer tracks the logical index
  end

  // ---- SYMBOLIC-BYTE memory proof: final SRAM content is byte-exact for ALL addrs ----
  (* anyconst *) reg [AW-1:0] f_addr;   // one symbolic address -> proves every address
  reg       f_have;                     // the byte destined for f_addr was accepted
  reg [7:0] f_exp;                      // ...and this is its value
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) f_have <= 1'b0;
    else if (start) begin
      f_have <= (f_addr == '0);  f_exp <= in_byte;        // index 0 lands at addr 0
    end else if (body && (cnt == f_addr)) begin
      f_have <= 1'b1;           f_exp <= in_byte;          // index f_addr -> addr f_addr
    end
  end
  // continuous (inductive) form: once captured, address f_addr always holds the
  // byte that belongs there (subsumes the at-commit check; k-induction closes it).
  always @(posedge clk) begin
    if (rst_n && f_have && (f_addr < cnt))
      assert (mem[f_addr] == f_exp);
  end

  // vacuity guards
  always @(posedge clk) if (rst_n) begin
    cover (msg_valid && msg_len > 'd3);  // a real multi-byte message completes
    cover (body);
  end
`endif
endmodule
