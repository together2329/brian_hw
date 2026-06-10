// =============================================================================
// pwm_gen_cx1.sv — 8-bit PWM generator with duty-cycle register
// SSOT: pwm_gen_cx1/yaml/pwm_gen_cx1.ssot.yaml
// Free-running 8-bit counter; pwm_out = (counter_q < duty_reg) combinational.
// Active-low async reset clears counter_q and duty_reg to 0.
// =============================================================================
module pwm_gen_cx1 #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] duty_in,
    input  wire             wr_en,
    output wire             pwm_out
);

    reg [WIDTH-1:0] counter_q;
    reg [WIDTH-1:0] duty_reg;

    // Free-running counter + DUTY register: async reset, sync update
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter_q <= {WIDTH{1'b0}};
            duty_reg  <= {WIDTH{1'b0}};
        end else begin
            counter_q <= counter_q + 1'b1;       // wraps 0..255
            if (wr_en)
                duty_reg <= duty_in;
        end
    end

    // Combinational compare: pwm_out=1 when counter_q < duty_reg
    assign pwm_out = (counter_q < duty_reg) ? 1'b1 : 1'b0;

endmodule
