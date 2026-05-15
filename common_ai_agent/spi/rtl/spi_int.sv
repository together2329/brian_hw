// spi_int.sv — sticky/level interrupt pending and masked irq from SSOT interrupts
module spi_int (
    input  logic        PCLK,
    input  logic        PRESETn,
    input  logic        soft_reset,
    input  logic [7:0]  int_mask,
    input  logic [7:0]  int_clear_w1c,
    input  logic        done_event,
    input  logic        tx_overrun_event,
    input  logic        rx_overrun_event,
    input  logic        rx_underrun_event,
    input  logic        mode_fault_event,
    input  logic        illegal_access_event,
    input  logic        tx_empty_level,
    input  logic        rx_full_level,
    output logic [7:0]  int_pending_raw,
    output logic        irq_o
);
    logic [5:0] sticky_pending;

    // Sticky sources clear only through INT_CLEAR W1C, soft_reset, or PRESETn.
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            sticky_pending <= 6'b000000;
        end else if (soft_reset) begin
            sticky_pending <= 6'b000000;
        end else begin
            if (int_clear_w1c[0]) sticky_pending[0] <= 1'b0;
            else if (done_event) sticky_pending[0] <= 1'b1;
            if (int_clear_w1c[1]) sticky_pending[1] <= 1'b0;
            else if (tx_overrun_event) sticky_pending[1] <= 1'b1;
            if (int_clear_w1c[2]) sticky_pending[2] <= 1'b0;
            else if (rx_overrun_event) sticky_pending[2] <= 1'b1;
            if (int_clear_w1c[3]) sticky_pending[3] <= 1'b0;
            else if (rx_underrun_event) sticky_pending[3] <= 1'b1;
            if (int_clear_w1c[4]) sticky_pending[4] <= 1'b0;
            else if (mode_fault_event) sticky_pending[4] <= 1'b1;
            if (int_clear_w1c[5]) sticky_pending[5] <= 1'b0;
            else if (illegal_access_event) sticky_pending[5] <= 1'b1;
        end
    end

    always @(*) begin
        int_pending_raw[0] = sticky_pending[0];
        int_pending_raw[1] = sticky_pending[1];
        int_pending_raw[2] = sticky_pending[2];
        int_pending_raw[3] = sticky_pending[3];
        int_pending_raw[4] = sticky_pending[4];
        int_pending_raw[5] = sticky_pending[5];
        int_pending_raw[6] = tx_empty_level;
        int_pending_raw[7] = rx_full_level;
    end

    // SSOT invariant: irq_o is OR(INT_PENDING & INT_MASK).
    always @(*) begin
        irq_o = |(int_pending_raw & int_mask);
    end
endmodule
