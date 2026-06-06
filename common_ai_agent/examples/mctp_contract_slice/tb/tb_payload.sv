// Random byte-stream stimulus for the payload packer. Same-cycle scoreboard on
// the SRAM write port: byte j of a message must be written to address j with its
// own value. Mutants (offset/gap/overwrite/loss) trip the check.
module tb_payload;
  localparam int AW = 3;
  logic clk = 0, rst_n, in_valid, in_som, in_eom;
  logic [7:0] in_byte;
  logic wr_en; logic [AW-1:0] wr_addr; logic [7:0] wr_byte;
  logic msg_valid; logic [AW:0] msg_len;

  mctp_rx_payload dut (.*);
  always #5 clk = ~clk;

  integer errors = 0, m, len, j;
  reg [7:0] b;

  task automatic drive(input logic s, input logic e, input logic [7:0] d);
    begin
      @(negedge clk); in_valid = 1'b1; in_som = s; in_eom = e; in_byte = d;
      #1;  // let combinational write outputs settle
    end
  endtask

  initial begin
    rst_n=0; in_valid=0; in_som=0; in_eom=0; in_byte=0;
    repeat (3) @(negedge clk); rst_n = 1;
    for (m = 0; m < 400; m++) begin
      len = ($random & 3'h7); if (len == 0) len = 1;     // 1..7 bytes
      for (j = 0; j < len; j++) begin
        b = $random;
        drive(j==0, j==len-1, b);
        if (!(wr_en === 1'b1 && wr_addr === j[AW-1:0] && wr_byte === b)) begin
          $display("[PAYLOAD FAIL] msg=%0d idx=%0d  expect addr=%0d byte=%02x  got en=%b addr=%0d byte=%02x",
                   m, j, j, b, wr_en, wr_addr, wr_byte);
          errors = errors + 1;
        end
      end
      @(negedge clk); in_valid=0; in_som=0; in_eom=0;    // inter-message gap
    end
    if (errors == 0) $display("PAYLOAD_SIM_DONE msgs=400 ok");
    else begin $display("PAYLOAD_SIM_FAIL errors=%0d", errors); $fatal(1, "payload mismatch"); end
    $finish;
  end
endmodule
