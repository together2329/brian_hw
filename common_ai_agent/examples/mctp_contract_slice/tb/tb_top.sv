// End-to-end interleaved-traffic scoreboard for the integrated assembler.
// Two contexts' messages interleave; the TB tracks each context's expected write
// offset and checks every payload write (byte-exact + in the right region), and
// that an out-of-sequence packet is dropped (no write). Catches the coupling
// bugs (BASE: cross-region, XCTX: pointer corruption, SEQ: no per-ctx seq).
module tb_top;
  localparam int REGION = 4;
  logic clk = 0, rst_n, pkt_valid, pkt_ctx, pkt_som, pkt_eom;
  logic [1:0] pkt_seq; logic [7:0] pkt_byte;
  logic wr_en; logic [2:0] wr_addr; logic [7:0] wr_byte;
  logic msg_valid, msg_ctx; logic [7:0] msg_len; logic [2:0] msg_base; logic drop_pulse;

  mctp_rx_top dut (.*);
  always #5 clk = ~clk;

  // per-context reference
  reg        r_active [0:1];
  reg [2:0]  r_wp     [0:1];     // expected next byte index
  reg [1:0]  r_eseq   [0:1];
  reg [2:0]  r_len    [0:1];     // target length 1..REGION
  integer    step, c, errors = 0;
  reg [7:0]  b;

  task automatic drv(input v, input cc, input s, input e, input [1:0] q, input [7:0] d);
    begin @(negedge clk); pkt_valid=v; pkt_ctx=cc; pkt_som=s; pkt_eom=e; pkt_seq=q; pkt_byte=d; #1; end
  endtask

  task automatic ckwrite(input cc, input [2:0] j, input [7:0] d);
    begin
      if (!(wr_en===1'b1 && wr_addr===(cc*REGION+j) && wr_byte===d)) begin
        $display("[TOP FAIL] write ctx=%0d j=%0d exp addr=%0d byte=%02x got en=%b addr=%0d byte=%02x",
                 cc, j, cc*REGION+j, d, wr_en, wr_addr, wr_byte); errors=errors+1;
      end
    end
  endtask

  initial begin
    rst_n=0; pkt_valid=0; pkt_ctx=0; pkt_som=0; pkt_eom=0; pkt_seq=0; pkt_byte=0;
    r_active[0]=0; r_active[1]=0; r_wp[0]=0; r_wp[1]=0; r_eseq[0]=0; r_eseq[1]=0; r_len[0]=1; r_len[1]=1;
    repeat (2) @(negedge clk); rst_n=1;

    for (step = 0; step < 4000; step++) begin
      c = $random & 1;
      b = $random;
      if (!r_active[c]) begin
        // start a new message of length 1..REGION
        r_len[c] = ($random & 2'h3) + 1;
        drv(1'b1, c[0], 1'b1, (r_len[c]==1), $random, b);
        ckwrite(c, 3'd0, b);                                   // SOM byte -> offset 0
        r_wp[c] = 3'd1; r_eseq[c] = pkt_seq + 2'd1; r_active[c] = (r_len[c] > 1);
      end else if ((($random & 7) == 0)) begin
        // inject an out-of-sequence continuation -> must be dropped (no write)
        drv(1'b1, c[0], 1'b0, 1'b0, r_eseq[c] + 2'd1, b);
        if (wr_en !== 1'b0) begin $display("[TOP FAIL] OOS not dropped ctx=%0d (wr_en=%b)", c, wr_en); errors=errors+1; end
        r_active[c] = 1'b0;                                    // context dropped
      end else begin
        // normal continuation / end
        drv(1'b1, c[0], 1'b0, (r_wp[c]==r_len[c]-1), r_eseq[c], b);
        ckwrite(c, r_wp[c], b);
        if (r_wp[c] == r_len[c]-1) r_active[c] = 1'b0;
        else begin r_wp[c] = r_wp[c] + 3'd1; r_eseq[c] = r_eseq[c] + 2'd1; end
      end
      @(posedge clk); #1;
    end
    if (errors == 0) $display("TOP_SIM_DONE ok");
    else begin $display("TOP_SIM_FAIL errors=%0d", errors); $fatal(1, "top mismatch"); end
    $finish;
  end
endmodule
