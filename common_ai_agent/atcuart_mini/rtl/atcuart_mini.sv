// atcuart_mini.sv — Minimal Andes-style UART register interface
// Matches yaml/atcuart_mini.ssot.yaml. Simplified single-cycle TX: tx_serial
// pulses to PWDATA[0] for the access phase of a THR write, idles high
// otherwise.

`timescale 1ns/1ps

module atcuart_mini #(
    parameter int APB_ADDR_WIDTH = 4,
    parameter int APB_DATA_WIDTH = 32,
    parameter int DATA_WIDTH     = 8
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
    output logic                       tx_serial
);

    logic [DATA_WIDTH-1:0] thr_data_q;

    wire access_phase = PSEL & PENABLE;
    wire is_thr       = (PADDR == 'h0);
    wire is_lsr       = (PADDR == 'h4);
    wire thr_write    = access_phase & PWRITE & is_thr;
    wire thr_read     = access_phase & ~PWRITE & is_thr;
    wire lsr_read     = access_phase & ~PWRITE & is_lsr;

    always_ff @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            thr_data_q <= '0;
        end else if (thr_write) begin
            thr_data_q <= PWDATA[DATA_WIDTH-1:0];
        end
    end

    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

    assign PRDATA = thr_read ? {{(APB_DATA_WIDTH-DATA_WIDTH){1'b0}}, thr_data_q}
                  : lsr_read ? {{(APB_DATA_WIDTH-1){1'b0}}, 1'b1}  // LSR.THRE=1
                  : '0;

    // tx_serial: combinational mirror of PWDATA[0] during a THR write
    // access phase; idle high (1) otherwise.
    assign tx_serial = thr_write ? PWDATA[0] : 1'b1;

endmodule
