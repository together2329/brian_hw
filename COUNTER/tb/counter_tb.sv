`timescale 1ns/1ps

module counter_tb;
    localparam int WIDTH = 64;

    logic clk;
    logic rst_n;
    logic en;
    logic load;
    logic [WIDTH-1:0] load_value;
    logic [WIDTH-1:0] count;

    counter #(.WIDTH(WIDTH)) dut (
        .clk(clk),
        .rst_n(rst_n),
        .en(en),
        .load(load),
        .load_value(load_value),
        .count(count)
    );

    // Clock generation
    initial clk = 0;
    always #5 clk = ~clk; // 100MHz

    // Test sequence
    initial begin
        rst_n = 0;
        en = 0;
        load = 0;
        load_value = '0;

        repeat (2) @(posedge clk);
        rst_n = 1;

        // Basic count test
        @(posedge clk);
        en = 1;
        repeat (5) @(posedge clk);
        if (count !== 5) $fatal(1, "Counter failed basic increment test: %0d", count);

        // Load test
        load_value = 8'hA5;
        load = 1;
        @(posedge clk);
        load = 0;
        if (count !== 8'hA5) $fatal(1, "Counter failed load test: %0h", count);

        // Enable gate test
        en = 0;
        repeat (3) @(posedge clk);
        if (count !== 8'hA5) $fatal(1, "Counter changed while enable low: %0h", count);

        // Wrap test
        en = 1;
        load_value = {WIDTH{1'b1}};
        load = 1;
        @(posedge clk);
        load = 0;
        @(posedge clk);
        if (count !== '0) $fatal(1, "Counter failed wrap test: %0d", count);

        $display("All tests passed");
        $finish;
    end

endmodule
