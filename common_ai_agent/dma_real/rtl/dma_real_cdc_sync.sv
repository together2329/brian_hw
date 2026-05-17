// dma_real_cdc_sync.sv — Parameterized 2-stage flip-flop synchronizer for CDC
//
// SSOT refs: cdc_requirements.crossings, memory.internal.ch_async_fifo.implementation
//
// Usage: gray-code pointer sync for async FIFO, pulse sync, status sync.

module dma_real_cdc_sync #(
    parameter integer WIDTH = 1
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [WIDTH-1:0] din,
    output logic [WIDTH-1:0] dout
);

    logic [WIDTH-1:0] sync_q0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_q0 <= {WIDTH{1'b0}};
            dout    <= {WIDTH{1'b0}};
        end else begin
            sync_q0 <= din;     // stage 1
            dout    <= sync_q0; // stage 2
        end
    end

endmodule
