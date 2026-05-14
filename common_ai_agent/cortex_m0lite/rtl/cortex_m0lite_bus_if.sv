module cortex_m0lite_bus_if #(
    parameter integer AHB_ADDR_W = 32
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    input  logic                  if_bus_req,
    input  logic                  ex_bus_req,
    input  logic [AHB_ADDR_W-1:0] i_haddr,
    input  logic [AHB_ADDR_W-1:0] d_haddr,
    output logic                  bus_active
);
    // Bus interface CDC boundary — SSOT instr_ahb_m/data_ahb_m adapter
    // Registered bus activity indicator for future CDC/decoupling extensions.
    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            bus_active <= 1'b0;
        end else begin
            bus_active <= (|i_haddr) | (|d_haddr) | if_bus_req | ex_bus_req;
        end
    end
endmodule
