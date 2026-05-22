// apb_pulse_counter.sv — APB-accessed pulse counter
// Matches yaml/apb_pulse_counter.ssot.yaml.

`timescale 1ns/1ps

module apb_pulse_counter #(
    parameter int APB_ADDR_WIDTH = 4,
    parameter int APB_DATA_WIDTH = 32,
    parameter int COUNTER_WIDTH  = 8
) (
    input  logic                       PCLK,
    input  logic                       PRESETn,
    input  logic [APB_ADDR_WIDTH-1:0]  PADDR,
    input  logic                       PSEL,
    input  logic                       PENABLE,
    input  logic                       PWRITE,
    input  logic [APB_DATA_WIDTH-1:0]  PWDATA,
    output logic [APB_DATA_WIDTH-1:0]  PRDATA,
    output logic                       PREADY,
    output logic                       PSLVERR,
    input  logic                       pulse_in,
    output logic [COUNTER_WIDTH-1:0]   count_out
);

    logic [COUNTER_WIDTH-1:0] count_q;

    wire access_phase = PSEL & PENABLE;
    wire is_count     = (PADDR == 'h0);
    wire is_clear     = (PADDR == 'h4);
    wire clear_write  = access_phase & PWRITE & is_clear;
    wire count_read   = access_phase & ~PWRITE & is_count;

    always_ff @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            count_q <= '0;
        end else if (clear_write) begin
            count_q <= '0;
        end else if (pulse_in) begin
            count_q <= count_q + 1'b1;
        end
    end

    assign PREADY    = 1'b1;
    assign PSLVERR   = 1'b0;
    assign PRDATA    = count_read ? {{(APB_DATA_WIDTH-COUNTER_WIDTH){1'b0}}, count_q} : '0;
    assign count_out = count_q;

endmodule
