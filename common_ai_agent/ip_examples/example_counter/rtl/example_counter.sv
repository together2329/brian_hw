// example_counter.sv — 4-bit up-counter with sync reset, enable, load, overflow
// Generated from example_counter.ssot.yaml
// SSOT contract: load > en > hold; overflow on MAX->0 wrap

module example_counter #(
    parameter WIDTH = 4
)(
    input  logic             clk,
    input  logic             rst_n,
    input  logic             en,
    input  logic             load,
    input  logic [WIDTH-1:0] data_in,
    output logic [WIDTH-1:0] count,
    output logic             overflow
);

    logic [WIDTH-1:0] count_r;
    logic             overflow_r;
    logic [WIDTH-1:0] next_count;
    logic             overflow_det;

    // Combinational next-state logic
    assign next_count  = load ? data_in :
                         en   ? (count_r + 1'b1) :
                                count_r;

    assign overflow_det = (count_r == {WIDTH{1'b1}}) && en && !load;

    // Registered state
    always @(posedge clk) begin
        if (!rst_n) begin
            count_r    <= {WIDTH{1'b0}};
            overflow_r <= 1'b0;
        end else begin
            count_r    <= next_count;
            overflow_r <= overflow_det;
        end
    end

    // Output assignments
    assign count    = count_r;
    assign overflow = overflow_r;

endmodule
