// =============================================================================
// simple_pwm.sv — Configurable PWM Output Generator
// =============================================================================
// Generated from: yaml/simple_pwm.ssot.yaml
// Profile: standard (educational-tiny)
// =============================================================================

module simple_pwm #(
    parameter COUNTER_WIDTH = 8
) (
    input  logic                      clk,
    input  logic                      rst_n,
    input  logic                      enable,
    input  logic [COUNTER_WIDTH-1:0]  duty_cycle,
    input  logic [COUNTER_WIDTH-1:0]  period,
    output logic                      pwm_out
);

    // =========================================================================
    // Internal state
    // =========================================================================
    logic [COUNTER_WIDTH-1:0] counter;

    // =========================================================================
    // Counter logic (FM1, FM2, FM3)
    // =========================================================================
    // When enable=1: counter increments, wraps to 0 when reaching period.
    // When enable=0: counter resets to 0.
    // =========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= {COUNTER_WIDTH{1'b0}};
        end else if (!enable) begin
            // FM3: pwm_idle — counter stays at 0 when disabled
            counter <= {COUNTER_WIDTH{1'b0}};
        end else begin
            // FM1/FM2: counter increments, wraps at period
            if (counter >= period - 1) begin
                counter <= {COUNTER_WIDTH{1'b0}};
            end else begin
                counter <= counter + 1'b1;
            end
        end
    end

    // =========================================================================
    // PWM output logic (FM1, FM2, FM3)
    // =========================================================================
    // FM1: pwm_out=1 when enable=1 and counter < duty_cycle
    // FM2: pwm_out=0 when enable=1 and counter >= duty_cycle
    // FM3: pwm_out=0 when enable=0
    // =========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_out <= 1'b0;
        end else if (!enable) begin
            // FM3: pwm_idle — output forced to 0
            pwm_out <= 1'b0;
        end else if (counter < duty_cycle) begin
            // FM1: pwm_active_high
            pwm_out <= 1'b1;
        end else begin
            // FM2: pwm_active_low
            pwm_out <= 1'b0;
        end
    end

endmodule
