// tb_counter.v — Testbench for 4-bit counter
// Generates clock, applies stimulus, monitors output via $display
// Designed for agent-server RTL pipeline testing

module tb_counter;
    reg             clk, rst_n, en;
    wire [3:0]      count;

    // ── DUT Instantiation ─────────────────────────────────────────
    counter #(.WIDTH(4)) dut (
        .clk    (clk),
        .rst_n  (rst_n),
        .en     (en),
        .count  (count)
    );

    // ── Clock Generation (100 MHz = 10ns period) ─────────────────
    always #5 clk = ~clk;

    // ── Stimulus ──────────────────────────────────────────────────
    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);

        clk   = 0;
        rst_n = 0;
        en    = 0;

        #15 rst_n = 1;          // Release reset at t=15
        #10 en = 1;             // Start counting at t=25
        #100 en = 0;            // Stop after 10 cycles at t=125
        #30 $finish;            // Drain pipeline, finish at t=155
    end

    // ── Monitor — prints on every posedge clock ──────────────────
    always @(posedge clk) begin
        $display("t=%0t rst_n=%b en=%b count=%d", $time, rst_n, en, count);
    end

    // ── Waveform dump (optional, for gtkwave) ────────────────────
    initial begin
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);
    end

endmodule