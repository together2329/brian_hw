// Structured-message stimulus for the descriptor/header-snapshot module.
// The TB drives whole messages (som..eom) so it knows the golden first/last header,
// and checks: no publish before EOM, header snapshots, published content, q bound.
module tb_desc;
  logic clk = 0, rst_n, pkt_valid, pkt_som, pkt_eom, desc_pop;
  logic [7:0] pkt_hdr;
  logic [7:0] first_hdr, last_hdr, push_first, push_last, push_len, desc_first, desc_last, desc_len;
  logic active, desc_push, desc_drop_full, desc_valid;
  logic [1:0] q_cnt;

  mctp_rx_descriptor dut (.*);
  always #5 clk = ~clk;

  integer m, j, len, errors = 0;
  reg [7:0] tb_first, tb_last, h;

  task automatic drive(input v, input s, input e, input [7:0] hh, input p);
    begin
      @(negedge clk); pkt_valid=v; pkt_som=s; pkt_eom=e; pkt_hdr=hh; desc_pop=p; #1;
    end
  endtask

  initial begin
    rst_n=0; pkt_valid=0; pkt_som=0; pkt_eom=0; pkt_hdr=0; desc_pop=0;
    tb_first=0; tb_last=0;
    repeat (2) @(negedge clk); rst_n=1;
    for (m = 0; m < 1500; m++) begin
      len = ($random & 3) + 1;                 // 1..4 packets
      for (j = 0; j < len; j++) begin
        h = m*4 + j + 1;                        // distinct headers so first != last on multi-packet
        drive(1'b1, j==0, j==len-1, h, ($random & 7) == 0);  // pop rarely -> queue can fill
        // combinational publish contract
        if (desc_push && !(j==len-1))         begin $display("[FAIL] publish before EOM m=%0d j=%0d",m,j); errors=errors+1; end
        if (desc_push && (j!=0) && push_first !== first_hdr) begin $display("[FAIL] push_first wrong"); errors=errors+1; end
        if (desc_push && push_last !== h)     begin $display("[FAIL] push_last wrong"); errors=errors+1; end
        if (q_cnt > 2'd2)                     begin $display("[FAIL] q_cnt overflow %0d",q_cnt); errors=errors+1; end
        if (j==0) tb_first = h;
        tb_last = h;
        @(posedge clk); #1;   // let NBA latch settle before reading registered outputs
        // registered header-snapshot contract
        if (first_hdr !== tb_first) begin $display("[FAIL] first_hdr m=%0d j=%0d got %0d exp %0d",m,j,first_hdr,tb_first); errors=errors+1; end
        if (last_hdr  !== tb_last)  begin $display("[FAIL] last_hdr  m=%0d j=%0d got %0d exp %0d",m,j,last_hdr,tb_last);  errors=errors+1; end
      end
      drive(1'b0, 1'b0, 1'b0, 8'd0, ($random & 1)); @(posedge clk);  // idle/maybe-pop gap
    end
    if (errors == 0) $display("DESC_SIM_DONE ok");
    else begin $display("DESC_SIM_FAIL errors=%0d", errors); $fatal(1, "desc mismatch"); end
    $finish;
  end
endmodule
