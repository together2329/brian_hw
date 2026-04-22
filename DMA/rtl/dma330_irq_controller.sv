// =============================================================================
// dma330_irq_controller.sv — DMA-330 IRQ Controller
//
// Manages interrupt generation for DMA events and faults.
//
// Registers:
//   INT_EVENT_RIS — Raw interrupt status (set by event pulses, W1C)
//   INTEN         — Interrupt enable mask (R/W)
//   INTMIS        — Masked interrupt status = INT_EVENT_RIS & INTEN
//   Fault IRQ     — Dedicated bit at position NUM_EVENTS
//
// irq_o: one IRQ line per event, driven from INTMIS
// =============================================================================

module dma330_irq_controller #(
    parameter int unsigned NUM_EVENTS = 8
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                      clk,
    input  logic                      rst_n,

    // =========================================================================
    // Event inputs (pulses from DMASEV instructions, one bit per event)
    // =========================================================================
    input  logic [NUM_EVENTS-1:0]     event_i,

    // =========================================================================
    // Fault input (from fault detection logic)
    // =========================================================================
    input  logic                      fault_i,

    // =========================================================================
    // APB Control Interface
    // =========================================================================
    input  logic [31:0]               inten_wdata,
    input  logic                      inten_we,
    input  logic [31:0]               intclr_wdata,
    input  logic                      intclr_we,

    // =========================================================================
    // Status Outputs
    // =========================================================================
    output logic [NUM_EVENTS-1:0]     int_event_ris_o,
    output logic [NUM_EVENTS-1:0]     intmis_o,

    // =========================================================================
    // IRQ Outputs (one per event + 1 fault IRQ)
    // =========================================================================
    output logic [NUM_EVENTS:0]       irq_o
);

    // =========================================================================
    // Internal Registers
    // =========================================================================
    logic [NUM_EVENTS-1:0] int_event_ris;  // Raw interrupt status
    logic [NUM_EVENTS-1:0] inten;           // Interrupt enable mask
    logic                  fault_ris;       // Fault raw status (sticky)

    // =========================================================================
    // INT_EVENT_RIS: set by event_i pulses, cleared by intclr_wdata (W1C)
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : ris_update
        if (!rst_n) begin
            int_event_ris <= '0;
        end else begin
            // Set bits on event pulses (OR-set)
            int_event_ris <= (int_event_ris | event_i) &
                             // Clear bits on write-to-clear (1 in intclr_wdata clears)
                             ~(intclr_we ? intclr_wdata[NUM_EVENTS-1:0] : '0);
        end
    end

    // =========================================================================
    // INTEN: read-write register, write-enabled by inten_we
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : inten_update
        if (!rst_n) begin
            inten <= '0;
        end else if (inten_we) begin
            inten <= inten_wdata[NUM_EVENTS-1:0];
        end
    end

    // =========================================================================
    // Fault: sticky, set by fault_i, cleared only by reset or intclr bit[NUM_EVENTS]
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : fault_update
        if (!rst_n) begin
            fault_ris <= 1'b0;
        end else begin
            // Set by fault_i (sticky)
            if (fault_i) begin
                fault_ris <= 1'b1;
            end
            // Clear by intclr write to bit NUM_EVENTS
            if (intclr_we && intclr_wdata[NUM_EVENTS]) begin
                fault_ris <= 1'b0;
            end
        end
    end

    // =========================================================================
    // Masked interrupt status
    // =========================================================================
    assign intmis_o = int_event_ris & inten;

    // =========================================================================
    // Status outputs
    // =========================================================================
    assign int_event_ris_o = int_event_ris;

    // =========================================================================
    // IRQ outputs: event IRQs from INTMIS, fault IRQ from fault_ris
    // =========================================================================
    assign irq_o[NUM_EVENTS-1:0] = intmis_o;
    assign irq_o[NUM_EVENTS]     = fault_ris;

endmodule : dma330_irq_controller
