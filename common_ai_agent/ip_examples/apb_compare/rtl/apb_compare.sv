// apb_compare.sv — Two-register equality comparator
// Matches yaml/apb_compare.ssot.yaml.

`timescale 1ns/1ps

module apb_compare #(
    parameter int APB_ADDR_WIDTH = 4,
    parameter int APB_DATA_WIDTH = 32
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
    output logic                       match_o
);

    logic [APB_DATA_WIDTH-1:0] value_q;
    logic [APB_DATA_WIDTH-1:0] reference_q;

    wire access_phase = PSEL & PENABLE;
    wire is_value     = (PADDR == 'h0);
    wire is_reference = (PADDR == 'h4);
    wire write_value  = access_phase & PWRITE & is_value;
    wire write_ref    = access_phase & PWRITE & is_reference;

    always_ff @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            value_q     <= '0;
            reference_q <= '0;
        end else begin
            if (write_value) value_q     <= PWDATA;
            if (write_ref)   reference_q <= PWDATA;
        end
    end

    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;
    assign PRDATA  = (access_phase & ~PWRITE & is_value)     ? value_q
                   : (access_phase & ~PWRITE & is_reference) ? reference_q
                   :                                            '0;
    assign match_o = (value_q == reference_q);

endmodule
