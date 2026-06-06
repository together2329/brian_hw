// Random-condition stimulus for the drop classifier. Reference model in the TB:
// expected reason = lowest set index +1, drop = |cond, assembly = reason>=9.
module tb_drop;
  logic clk = 0, rst_n;
  logic [13:0] cond;
  logic drop; logic [3:0] reason; logic is_assembly_drop;

  mctp_drop_classifier dut (.*);
  always #5 clk = ~clk;

  integer m, k, errors = 0;
  reg [3:0] exp_reason; reg exp_drop, exp_asm;

  initial begin
    rst_n = 0; cond = '0;
    repeat (2) @(negedge clk); rst_n = 1;
    for (m = 0; m < 2000; m++) begin
      @(negedge clk); cond = $random; #1;
      exp_drop = |cond; exp_reason = 4'd0;
      for (k = 13; k >= 0; k = k - 1) if (cond[k]) exp_reason = k[3:0] + 4'd1;
      exp_asm = exp_drop && (exp_reason >= 4'd9);
      if (!(drop === exp_drop && reason === exp_reason && is_assembly_drop === exp_asm)) begin
        $display("[DROP FAIL] cond=%014b  exp(drop=%b reason=%0d asm=%b)  got(drop=%b reason=%0d asm=%b)",
                 cond, exp_drop, exp_reason, exp_asm, drop, reason, is_assembly_drop);
        errors = errors + 1;
      end
    end
    if (errors == 0) $display("DROP_SIM_DONE ok");
    else begin $display("DROP_SIM_FAIL errors=%0d", errors); $fatal(1, "drop mismatch"); end
    $finish;
  end
endmodule
