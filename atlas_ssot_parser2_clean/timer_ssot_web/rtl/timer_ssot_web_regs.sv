`default_nettype none

module timer_ssot_web_regs #(
    parameter integer DBITS = 32,
    parameter integer ABITS = 4
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire [ABITS-1:0]  paddr,
    input  wire              psel,
    input  wire              penable,
    input  wire              pwrite,
    input  wire [DBITS-1:0]  pwdata,
    input  wire [3:0]        pstrb,
    output reg  [DBITS-1:0]  prdata,
    output wire              pready,
    output wire              pslverr,
    input  wire [DBITS-1:0]  count_value,
    input  wire              irq_status,
    output reg               ctrl_enable,
    output reg               ctrl_irq_enable,
    output reg  [DBITS-1:0]  compare_value,
    output reg               status_clear
);
    localparam [ABITS-1:0] ADDR_CTRL    = 4'h0;
    localparam [ABITS-1:0] ADDR_COUNT   = 4'h4;
    localparam [ABITS-1:0] ADDR_COMPARE = 4'h8;
    localparam [ABITS-1:0] ADDR_STATUS  = 4'hc;

    wire apb_access;
    wire apb_write;
    wire apb_read;

    assign apb_access = psel & penable;
    assign apb_write  = apb_access & pwrite;
    assign apb_read   = apb_access & ~pwrite;
    assign pready     = 1'b1;
    assign pslverr    = 1'b0;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctrl_enable     <= 1'b0;
            ctrl_irq_enable <= 1'b0;
            compare_value   <= {DBITS{1'b0}};
            status_clear    <= 1'b0;
        end else begin
            status_clear <= 1'b0;
            if (apb_write) begin
                case (paddr)
                    ADDR_CTRL: begin
                        if (pstrb[0]) begin
                            ctrl_enable     <= pwdata[0];
                            ctrl_irq_enable <= pwdata[1];
                        end
                    end
                    ADDR_COMPARE: begin
                        if (pstrb[0]) compare_value[7:0]    <= pwdata[7:0];
                        if (pstrb[1]) compare_value[15:8]   <= pwdata[15:8];
                        if (pstrb[2]) compare_value[23:16]  <= pwdata[23:16];
                        if (pstrb[3]) compare_value[31:24]  <= pwdata[31:24];
                    end
                    ADDR_STATUS: begin
                        status_clear <= pwdata[0] & pstrb[0];
                    end
                    default: begin
                        status_clear <= 1'b0;
                    end
                endcase
            end
        end
    end

    always @(*) begin
        prdata = {DBITS{1'b0}};
        if (apb_read) begin
            case (paddr)
                ADDR_CTRL:    prdata = {{DBITS-2{1'b0}}, ctrl_irq_enable, ctrl_enable};
                ADDR_COUNT:   prdata = count_value;
                ADDR_COMPARE: prdata = compare_value;
                ADDR_STATUS:  prdata = {{DBITS-1{1'b0}}, irq_status};
                default:      prdata = {DBITS{1'b0}};
            endcase
        end
    end
endmodule

`default_nettype wire
