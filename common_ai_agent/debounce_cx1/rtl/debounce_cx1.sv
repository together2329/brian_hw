// debounce_cx1 — Button debouncer with configurable stability counter
// db_out updates to btn_in after THRESH consecutive stable cycles.
module debounce_cx1 #(parameter THRESH = 4) (
    input  wire clk,
    input  wire rst_n,
    input  wire btn_in,
    output wire db_out
);
    localparam         CTR_W    = 8;
    localparam [CTR_W-1:0] THRESH_M1 = THRESH - 1;

    reg [CTR_W-1:0] ctr_q;   // stability counter
    reg             last_q;  // last sampled btn_in
    reg             db_q;    // debounced output register

    // Simulation initialisation (iverilog starts regs at X)
    initial begin
        ctr_q  = {CTR_W{1'b0}};
        last_q = 1'b0;
        db_q   = 1'b0;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctr_q  <= {CTR_W{1'b0}};
            last_q <= 1'b0;
            db_q   <= 1'b0;
        end else begin
            if (btn_in == last_q) begin
                // btn_in stable — increment counter, update db_q at threshold
                if (ctr_q < THRESH_M1) begin
                    ctr_q <= ctr_q + 1'b1;
                end else begin
                    ctr_q <= ctr_q;
                    db_q  <= btn_in;
                end
            end else begin
                // btn_in changed — reset counter, update last sample
                ctr_q  <= {CTR_W{1'b0}};
                last_q <= btn_in;
            end
        end
    end

    assign db_out = db_q;
endmodule
