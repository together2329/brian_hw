// Constrained-random stimulus for the multi-context assembler (run with -DFORMAL).
// Random key fields -> packets for different keys interleave across the 2 contexts.
module tb_mc;
  localparam int N = 6000;
  logic clk = 0, rst_n;
  logic pkt_valid, pkt_som, pkt_eom, pkt_hdr_ok, msg_ready;
  logic [1:0] pkt_seq, pkt_src, pkt_tag;
  logic       pkt_to;
  logic pkt_ready, msg_valid, drop_pulse;
  logic [4:0] msg_key;
  logic [7:0] msg_len;

  mctp_rx_mc dut (.*);

  always #5 clk = ~clk;

  integer i;
  initial begin
    rst_n=0; pkt_valid=0; pkt_som=0; pkt_eom=0; pkt_seq=0;
    pkt_src=0; pkt_to=0; pkt_tag=0; pkt_hdr_ok=1; msg_ready=1;
    repeat (3) @(negedge clk);
    rst_n = 1;
    for (i = 0; i < N; i++) begin
      @(negedge clk);
      pkt_valid  =  $random;
      pkt_som    =  $random;
      pkt_eom    =  $random;
      pkt_seq    =  $random;
      pkt_src    =  $random % 2;     // few distinct keys -> contexts collide/interleave
      pkt_to     =  $random;
      pkt_tag    =  $random % 2;
      pkt_hdr_ok = ($random % 6) != 0;
      msg_ready  = ($random % 3) != 0;
    end
    $display("MC_SIM_DONE cycles=%0d", N);
    $finish;
  end
endmodule
