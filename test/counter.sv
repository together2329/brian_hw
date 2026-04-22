// counter.sv — Parameterizable up/down counter
// Synchronous active-low reset, load priority, enable-gated counting

module counter #(
    parameter int WIDTH = 8
)(
    input  logic             clk,
    input  logic             rst_n,      // Synchronous active-low reset
    input  logic             en,         // Count enable
    input  logic             up_down,    // 1 = count up, 0 = count down
    input  logic             load,       // Synchronous load (priority over count)
    input  logic [WIDTH-1:0] load_data,  // Data to load
    output logic [WIDTH-1:0] count       // Current count value
);

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            count <= '0;
        end else if (load) begin
            count <= load_data;
        end else if (en) begin
            if (up_down)
                count <= count + 1'b1;
            else
                count <= count - 1'b1;
        end
    end

endmodule
