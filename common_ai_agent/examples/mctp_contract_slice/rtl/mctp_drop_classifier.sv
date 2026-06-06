// =============================================================================
// mctp_drop_classifier — drop priority + packet/assembly classification.
// Reflects v3 spec §10.1/§10.2/§10.3:
//   * 14 drop reasons in a fixed priority order (reason 1 highest .. 14 lowest)
//   * when several conditions hold for one accepted transaction, report the
//     SINGLE highest-priority one (a later assembly failure must NOT mask an
//     earlier packet-format failure)
//   * reasons 1..8 are packet drops, 9..14 are assembly drops
// cond[i] is the condition for reason (i+1); cond[0]=highest priority.
//
// Mutation hooks: INJECT_PRIO_BUG INJECT_CLASS_BUG INJECT_ANY_BUG
// =============================================================================
module mctp_drop_classifier (
  input  logic        clk,
  input  logic        rst_n,
  input  logic [13:0] cond,             // 14 drop-reason conditions (cond[0] = reason 1, highest prio)
  output logic        drop,
  output logic [3:0]  reason,           // 1..14, 0 = no drop
  output logic        is_assembly_drop  // reasons 9..14
);
  integer i;
  always @* begin
    reason = 4'd0;
`ifdef INJECT_PRIO_BUG
    for (i = 0;  i <= 13; i = i + 1) if (cond[i]) reason = i[3:0] + 4'd1;  // BUG: lowest priority wins
`else
    for (i = 13; i >= 0;  i = i - 1) if (cond[i]) reason = i[3:0] + 4'd1;  // highest priority (lowest index) wins
`endif
  end

`ifdef INJECT_ANY_BUG
  assign drop = |cond[12:0];                            // BUG: ignores reason 14 (timeout)
`else
  assign drop = |cond;
`endif

`ifdef INJECT_CLASS_BUG
  assign is_assembly_drop = drop && (reason >= 4'd8);   // BUG: packet/assembly boundary off by one
`else
  assign is_assembly_drop = drop && (reason >= 4'd9);
`endif

`ifdef FORMAL
  always @(posedge clk) if (rst_n) begin
    // C-DROP-ANY: a drop is reported exactly when some condition holds
    assert (drop == (|cond));
    assert ((reason != 4'd0) == drop);
    if (drop) begin
      // C-DROP-PRIORITY: the winning reason's condition holds, and NO higher-
      // priority (lower-index) condition is set (later cannot mask earlier)
      assert (cond[reason - 4'd1]);
      assert ((cond & (({13'd0, 1'b1} << (reason - 4'd1)) - 14'd1)) == 14'd0);
      // C-DROP-CLASS: 1..8 packet, 9..14 assembly
      assert (is_assembly_drop == (reason >= 4'd9));
    end else begin
      assert (reason == 4'd0);
      assert (!is_assembly_drop);
    end
    // vacuity guards
    cover (drop && reason <= 4'd8);                 // a packet drop is reachable
    cover (drop && reason >= 4'd9);                 // an assembly drop is reachable
    cover ((cond & (cond - 14'd1)) != 14'd0);       // >=2 conditions at once (priority actually matters)
  end
`endif
endmodule
