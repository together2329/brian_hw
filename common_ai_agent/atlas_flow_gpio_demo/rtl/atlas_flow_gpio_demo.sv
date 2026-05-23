// atlas_flow_gpio_demo.sv — 8-bit APB-Lite GPIO output peripheral
// Generated to match yaml/atlas_flow_gpio_demo.ssot.yaml.
// Single DATA register at offset 0x0; low 8 bits drive gpio_out.

`timescale 1ns/1ps

module atlas_flow_gpio_demo #(
    parameter int GPIO_WIDTH     = 8,
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
    output logic [GPIO_WIDTH-1:0]      gpio_out
);

    // DATA register backs the gpio_out pins.
    logic [APB_DATA_WIDTH-1:0] DATA_q;

    // APB access-phase write update.
    wire access_phase = PSEL & PENABLE;
    wire write_access = access_phase & PWRITE;
    wire data_addr    = (PADDR == 'h0);

    always_ff @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            DATA_q <= '0;
        end else if (write_access & data_addr) begin
            DATA_q <= {{(APB_DATA_WIDTH-GPIO_WIDTH){1'b0}}, PWDATA[GPIO_WIDTH-1:0]};
        end
    end

    // Zero-wait-state slave: PREADY always 1, PSLVERR always 0.
    assign PREADY  = 1'b1;
    assign PSLVERR = 1'b0;

    // PRDATA returns DATA on read access of offset 0; zero elsewhere.
    assign PRDATA = (access_phase & ~PWRITE & data_addr) ? DATA_q : '0;

    // gpio_out follows the registered DATA value.
    assign gpio_out = DATA_q[GPIO_WIDTH-1:0];

endmodule
