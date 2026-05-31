// =============================================================================
// apb_add_demo.sv — Two-register combinational adder (OPA + OPB)
// SSOT: apb_add_demo/yaml/apb_add_demo.ssot.yaml
// Verilog-2001 subset (no package/interface/always_ff). Active-low async reset.
// {carry_out, add_out} = opa_q + opb_q
// =============================================================================
module apb_add_demo #(
    parameter APB_ADDR_WIDTH = 4,
    parameter APB_DATA_WIDTH = 8
) (
    input  wire                        PCLK,
    input  wire                        PRESETn,
    input  wire [APB_ADDR_WIDTH-1:0]   PADDR,
    input  wire                        PSEL,
    input  wire                        PENABLE,
    input  wire                        PWRITE,
    input  wire [APB_DATA_WIDTH-1:0]   PWDATA,
    output reg  [APB_DATA_WIDTH-1:0]   PRDATA,
    output wire                        PREADY,
    output wire                        PSLVERR,
    output wire [APB_DATA_WIDTH-1:0]   add_out,
    output wire                        carry_out
);

    localparam [APB_ADDR_WIDTH-1:0] ADDR_OPA = 4'h0;
    localparam [APB_ADDR_WIDTH-1:0] ADDR_OPB = 4'h4;

    reg  [APB_DATA_WIDTH-1:0] opa_q;
    reg  [APB_DATA_WIDTH-1:0] opb_q;

    wire access    = PSEL & PENABLE;
    wire write_opa = access & PWRITE & (PADDR == ADDR_OPA);
    wire write_opb = access & PWRITE & (PADDR == ADDR_OPB);

    // {carry_out, add_out} = opa_q + opb_q
    wire [APB_DATA_WIDTH:0] sum = {1'b0, opa_q} + {1'b0, opb_q};

    assign PREADY    = 1'b1;
    assign PSLVERR   = 1'b0;
    assign add_out   = sum[APB_DATA_WIDTH-1:0];
    assign carry_out = sum[APB_DATA_WIDTH];

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            opa_q <= {APB_DATA_WIDTH{1'b0}};
            opb_q <= {APB_DATA_WIDTH{1'b0}};
        end else begin
            if (write_opa) opa_q <= PWDATA;
            if (write_opb) opb_q <= PWDATA;
        end
    end

    always @(*) begin
        PRDATA = {APB_DATA_WIDTH{1'b0}};
        if (access && ~PWRITE) begin
            case (PADDR)
                ADDR_OPA: PRDATA = opa_q;
                ADDR_OPB: PRDATA = opb_q;
                default:  PRDATA = {APB_DATA_WIDTH{1'b0}};
            endcase
        end
    end

endmodule
