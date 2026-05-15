// priority_enc.sv — top-level integration wrapper for priority_enc
module priority_enc #(
    parameter integer N = 8,
    parameter integer INDEX_WIDTH = $clog2(N)
) (
    input  logic                   PCLK,
    input  logic                   PRESETn,
    input  logic [N-1:0]           data_in,
    output logic [INDEX_WIDTH-1:0] index_out,
    output logic                   valid_out,
    input  logic [11:0]            PADDR,
    input  logic                   PSEL,
    input  logic                   PENABLE,
    input  logic                   PWRITE,
    input  logic [31:0]            PWDATA,
    output logic [31:0]            PRDATA,
    output logic                   PREADY,
    output logic                   PSLVERR
);
    // Top-level wiring connects priority_enc_regs and priority_enc_core from SSOT sub_modules.

    logic                   ctrl_enable;
    logic [N-1:0]           mask;
    logic [INDEX_WIDTH-1:0] core_index;
    logic                   core_valid;

    assign index_out = core_index;
    assign valid_out = core_valid;

    priority_enc_regs #(
        .N(N),
        .INDEX_WIDTH(INDEX_WIDTH)
    ) u_priority_enc_regs (
        .PCLK(PCLK),
        .PRESETn(PRESETn),
        .PADDR(PADDR),
        .PSEL(PSEL),
        .PENABLE(PENABLE),
        .PWRITE(PWRITE),
        .PWDATA(PWDATA),
        .status_index_i(core_index),
        .status_valid_i(core_valid),
        .PRDATA(PRDATA),
        .PREADY(PREADY),
        .PSLVERR(PSLVERR),
        .ctrl_enable_o(ctrl_enable),
        .mask_o(mask)
    );

    priority_enc_core #(
        .N(N),
        .INDEX_WIDTH(INDEX_WIDTH)
    ) u_priority_enc_core (
        .PCLK(PCLK),
        .PRESETn(PRESETn),
        .data_in(data_in),
        .enable_i(ctrl_enable),
        .mask_i(mask),
        .index_out(core_index),
        .valid_out(core_valid)
    );
endmodule
