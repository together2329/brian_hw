module simdbg_demo #(
  parameter int WIDTH = 4
) (
  input  logic             clk,
  input  logic             rst_n,
  input  logic             start,
  input  logic [WIDTH-1:0] target,
  output logic             done,
  output logic             match,
  output logic [WIDTH-1:0] count
);

  logic active;

  simdbg_counter #(
    .WIDTH(WIDTH)
  ) u_counter (
    .clk    (clk),
    .rst_n  (rst_n),
    .enable (active),
    .count  (count)
  );

  simdbg_matcher #(
    .WIDTH(WIDTH)
  ) u_matcher (
    .count  (count),
    .target (target),
    .match  (match)
  );

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      active <= 1'b0;
      done   <= 1'b0;
    end else begin
      if (start) begin
        active <= 1'b1;
        done   <= 1'b0;
      end else if (match) begin
        active <= 1'b0;
        done   <= 1'b1;
      end else begin
        done   <= 1'b0;
      end
    end
  end

endmodule
