// End-to-end scoreboard for the full assembler (sim lane). Interleaved 2-context
// traffic with header bytes; occasional bad-header (gate) and out-of-sequence.
// Checks the robustly-observable contracts in sim:
//   * every payload write is byte-exact and in the right context region
//   * bad-header and out-of-sequence packets write no payload
// The descriptor/header-snapshot contracts (no-early, first/last, content, queue
// bound) are proven on the formal lane; here we just drain the queue so it can't
// block. Mutants: BASE/SEQ/GATE caught here; FIRST/NOEARLY/FULL caught by formal.
module tb_full;
  localparam int REGION = 4;
  logic clk=0, rst_n, pkt_valid, pkt_ctx, pkt_som, pkt_eom, pkt_hdr_ok, desc_pop;
  logic [1:0] pkt_seq; logic [7:0] pkt_hdr, pkt_byte;
  logic wr_en; logic [2:0] wr_addr; logic [7:0] wr_byte;
  logic desc_valid, desc_ctx; logic [7:0] desc_first, desc_last, desc_len; logic [2:0] desc_base;
  logic drop_pulse, is_assembly_drop;

  mctp_rx_full dut (.*);
  always #5 clk = ~clk;

  reg        a [0:1];
  reg [2:0]  wp [0:1];
  reg [1:0]  es [0:1];
  reg [2:0]  L  [0:1];
  integer    step, c, errors=0;
  reg [7:0]  hdr, byt;

  task automatic drv(input v, input cc, input s, input e, input ok, input [1:0] q, input [7:0] hh, input [7:0] d, input pop);
    begin @(negedge clk); pkt_valid=v; pkt_ctx=cc; pkt_som=s; pkt_eom=e; pkt_hdr_ok=ok; pkt_seq=q; pkt_hdr=hh; pkt_byte=d; desc_pop=pop; #1; end
  endtask

  initial begin
    rst_n=0; pkt_valid=0; pkt_ctx=0; pkt_som=0; pkt_eom=0; pkt_hdr_ok=1; pkt_seq=0; pkt_hdr=0; pkt_byte=0; desc_pop=0;
    a[0]=0; a[1]=0; wp[0]=0; wp[1]=0; es[0]=0; es[1]=0; L[0]=1; L[1]=1;
    repeat (2) @(negedge clk); rst_n=1;

    for (step=0; step<5000; step++) begin
      c = $random & 1;  hdr = $random; byt = $random;
      if (!a[c]) begin
        if (($random&7)==0) begin
          // bad-header packet -> gate drop, no payload write
          drv(1'b1,c[0],1'b1,1'b0,1'b0,$random,hdr,byt,($random&1));
          if (wr_en!==1'b0) begin $display("[FULL FAIL] gate: bad-hdr wrote payload"); errors=errors+1; end
        end else begin
          L[c]=($random&2'h3)+1;
          drv(1'b1,c[0],1'b1,(L[c]==1),1'b1,$random,hdr,byt,($random&1));
          if (!(wr_en&&wr_addr===c*REGION&&wr_byte===byt)) begin $display("[FULL FAIL] start write ctx=%0d",c); errors=errors+1; end
          wp[c]=1; es[c]=pkt_seq+1; a[c]=(L[c]>1);
        end
      end else if (($random&7)==0) begin
        // out-of-sequence continuation -> drop, no write
        drv(1'b1,c[0],1'b0,1'b0,1'b1,es[c]+2'd1,hdr,byt,($random&1));
        if (wr_en!==1'b0) begin $display("[FULL FAIL] OOS wrote payload ctx=%0d",c); errors=errors+1; end
        a[c]=0;
      end else begin
        // in-sequence continuation / end
        drv(1'b1,c[0],1'b0,(wp[c]==L[c]-1),1'b1,es[c],hdr,byt,($random&1));
        if (!(wr_en&&wr_addr===(c*REGION+wp[c])&&wr_byte===byt)) begin $display("[FULL FAIL] cont write ctx=%0d idx=%0d",c,wp[c]); errors=errors+1; end
        if (wp[c]==L[c]-1) a[c]=0;
        else begin wp[c]=wp[c]+1; es[c]=es[c]+1; end
      end
      @(posedge clk); #1;
    end
    if (errors==0) $display("FULL_SIM_DONE ok");
    else begin $display("FULL_SIM_FAIL errors=%0d",errors); $fatal(1,"full mismatch"); end
    $finish;
  end
endmodule
