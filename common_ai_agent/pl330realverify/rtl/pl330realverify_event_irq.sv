module pl330realverify_event_irq #(
    parameter integer NUM_EVENTS = 32
) (
    input  logic                   clk_i,
    input  logic                   rst_ni,
    input  logic [NUM_EVENTS-1:0]  peripheral_events_i,
    input  logic [4:0]             wfp_event_sel_i,

    input  logic [31:0]            inten_i,
    input  logic                   w1c_valid_i,
    input  logic [31:0]            w1c_mask_i,

    input  logic                   set_complete_i,
    input  logic                   set_fault_i,
    input  logic                   set_dbg_done_i,

    output logic [31:0]            intstatus_o,
    output logic                   selected_event_o,
    output logic                   irq_o,
    output logic                   fault_clear_o
);
    logic [31:0] intstatus_q;

    // Peripheral WFP event selection comes directly from CONTROL.wfp_event index.
    assign selected_event_o = peripheral_events_i[wfp_event_sel_i];

    // Fault clear handshake for channel-fsm: clearing CH0_FAULT bit releases FAULTED->STOPPED.
    assign fault_clear_o = w1c_valid_i & w1c_mask_i[8];

    always @(posedge clk_i or negedge rst_ni) begin
        if (!rst_ni) begin
            intstatus_q <= 32'h0000_0000;
        end else begin
            // W1C clear: only written ones clear pending bits, zeros preserve state.
            if (w1c_valid_i) intstatus_q <= intstatus_q & (~w1c_mask_i);

            // Channel 0 completion and fault are mutually exclusive by source behavior.
            if (set_complete_i) intstatus_q[0] <= 1'b1;
            if (set_fault_i) intstatus_q[8] <= 1'b1;
            if (set_dbg_done_i) intstatus_q[16] <= 1'b1;
        end
    end

    assign intstatus_o = intstatus_q;
    assign irq_o = |(intstatus_q & inten_i);

endmodule
