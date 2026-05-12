module simdbg_matcher #(
  parameter int WIDTH = 4
) (
  input  logic [WIDTH-1:0] count,
  input  logic [WIDTH-1:0] target,
  output logic             match
);

  always_comb begin
    match = (count == target);
  end

endmodule
