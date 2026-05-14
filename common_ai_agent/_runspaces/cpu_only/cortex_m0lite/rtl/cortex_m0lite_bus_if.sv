module bus_if #(
    parameter integer AHB_ADDR_W = 32
) (
    input  logic                  hclk,
    input  logic                  hresetn,
    input  logic                  if_bus_req,
    input  logic                  ex_bus_req,
    input  logic [AHB_ADDR_W-1:0] i_haddr,
    input  logic [AHB_ADDR_W-1:0] d_haddr
);
    logic [AHB_ADDR_W-1:0] i_addr_seen_q;
    logic [AHB_ADDR_W-1:0] d_addr_seen_q;

    always @(posedge hclk or negedge hresetn) begin
        if (!hresetn) begin
            i_addr_seen_q <= {AHB_ADDR_W{1'b0}};
            d_addr_seen_q <= {AHB_ADDR_W{1'b0}};
        end else begin
            if (if_bus_req) i_addr_seen_q <= i_haddr;
            if (ex_bus_req) d_addr_seen_q <= d_haddr;
        end
    end
endmodule
