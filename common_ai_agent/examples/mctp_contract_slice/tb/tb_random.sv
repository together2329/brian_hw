// Constrained-random stimulus for the embedded contracts (run with -DFORMAL).
// The --assert lane checks the embedded SVA live; mutants trip an assertion.
// Occasional mid-run reset/flush with an active context exposes RESET/FLUSH bugs.
module tb_random;
  localparam int N = 4000;
  logic clk = 0, rst_n, flush;
  logic pkt_valid, pkt_som, pkt_eom, pkt_hdr_ok, msg_ready;
  logic [1:0] pkt_seq; logic [2:0] pkt_tag; logic [7:0] pkt_data;
  logic pkt_ready, msg_valid, drop_pulse, ovf, context_active;
  logic [7:0] msg_len, msg_sum, commit_count, drop_count;
  logic [2:0] msg_tag, ctx_tag; logic [1:0] expected_seq;

  mctp_rx_assembler dut (.*);

  always #5 clk = ~clk;

  integer i;
  initial begin
    rst_n=0; flush=0; pkt_valid=0; pkt_som=0; pkt_eom=0;
    pkt_seq=0; pkt_tag=0; pkt_hdr_ok=1; pkt_data=0; msg_ready=1;
    repeat (3) @(negedge clk);
    rst_n = 1;
    for (i = 0; i < N; i++) begin
      @(negedge clk);
      pkt_valid  =  $random;
      pkt_som    =  $random;
      pkt_eom    =  $random;
      pkt_seq    =  $random;
      pkt_tag    =  $random;
      pkt_hdr_ok = ($random % 5) != 0;   // mostly good header
      pkt_data   =  $random;
      msg_ready  = ($random % 3) != 0;   // sometimes backpressure
      flush      = ($random % 23) == 0;  // occasional flush (may hit active ctx)
      rst_n      = ($random % 97) != 0;  // rare mid-run reset (may hit active ctx)
    end
    rst_n = 1;
    $display("RANDOM_SIM_DONE cycles=%0d commits=%0d drops=%0d", N, commit_count, drop_count);
    $finish;
  end
endmodule
