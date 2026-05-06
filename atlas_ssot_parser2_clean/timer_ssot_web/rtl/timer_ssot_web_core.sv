`default_nettype none

module timer_ssot_web_core #(
    parameter integer DBITS = 32
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              enable,
    input  wire              irq_enable,
    input  wire [DBITS-1:0]  compare_value,
    input  wire              status_clear,
    output reg  [DBITS-1:0]  count_value,
    output reg               irq_status,
    output wire              irq
);
    wire [DBITS-1:0] count_next;
    wire             compare_hit;

    assign count_next  = count_value + {{DBITS-1{1'b0}}, 1'b1};
    assign compare_hit = enable && (count_next == compare_value);
    assign irq         = irq_status & irq_enable;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count_value <= {DBITS{1'b0}};
            irq_status  <= 1'b0;
        end else begin
            if (enable) begin
                count_value <= count_next;
                if (compare_hit) begin
                    irq_status <= 1'b1;
                end
            end

            if (status_clear) begin
                irq_status <= 1'b0;
            end
        end
    end
endmodule

`default_nettype wire
