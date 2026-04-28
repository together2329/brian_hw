`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: ahb_axi_bridge
// Description: AHB-Lite slave to AXI4-Lite master bridge.
//
// Translates AHB-Lite single word transfers to AXI4-Lite transactions.
// Lives at address region 0x3000_0000 - 0x3FFF_FFFF (HADDR[29:28] == 2'b11).
//
// FSM (3 states):
//   IDLE → ADDR (assert AW/AR, wait for respective READY)
//        → DATA (complete W+B or R handshake)
//        → IDLE
// HREADYOUT is deasserted during the entire AXI transaction.
//----------------------------------------------------------------------------

module ahb_axi_bridge (
    input  wire         HCLK,
    input  wire         HRESETn,
    input  wire         HSEL,
    input  wire [1:0]   HTRANS,
    input  wire [2:0]   HSIZE,
    input  wire         HWRITE,
    input  wire [31:0]  HADDR,
    input  wire [31:0]  HWDATA,
    output reg  [31:0]  HRDATA,
    output reg          HREADYOUT,
    output reg          HRESP,
    input  wire         HREADY,

    output reg          M_AXI_AWVALID,
    input  wire         M_AXI_AWREADY,
    output reg  [31:0]  M_AXI_AWADDR,
    output wire [2:0]   M_AXI_AWPROT,
    output reg          M_AXI_WVALID,
    input  wire         M_AXI_WREADY,
    output reg  [31:0]  M_AXI_WDATA,
    output wire [3:0]   M_AXI_WSTRB,
    input  wire         M_AXI_BVALID,
    output reg          M_AXI_BREADY,
    input  wire [1:0]   M_AXI_BRESP,
    output reg          M_AXI_ARVALID,
    input  wire         M_AXI_ARREADY,
    output reg  [31:0]  M_AXI_ARADDR,
    output wire [2:0]   M_AXI_ARPROT,
    input  wire         M_AXI_RVALID,
    output reg          M_AXI_RREADY,
    input  wire [31:0]  M_AXI_RDATA,
    input  wire [1:0]   M_AXI_RRESP
);

    assign M_AXI_AWPROT = 3'b000;
    assign M_AXI_WSTRB  = 4'b1111;
    assign M_AXI_ARPROT = 3'b000;

    localparam IDLE = 2'd0;
    localparam ADDR = 2'd1;
    localparam DATA = 2'd2;

    reg [1:0]  state;
    reg        is_write;
    reg [31:0] latched_addr;
    reg [31:0] latched_wdata;

    always @(posedge HCLK) begin
        if (!HRESETn) begin
            state         <= IDLE;
            HREADYOUT     <= 1'b1;
            HRESP         <= 1'b0;
            HRDATA        <= 32'd0;
            is_write      <= 1'b0;
            latched_addr  <= 32'd0;
            latched_wdata <= 32'd0;

            M_AXI_AWVALID <= 1'b0;
            M_AXI_AWADDR  <= 32'd0;
            M_AXI_WVALID  <= 1'b0;
            M_AXI_WDATA   <= 32'd0;
            M_AXI_BREADY  <= 1'b0;
            M_AXI_ARVALID <= 1'b0;
            M_AXI_ARADDR  <= 32'd0;
            M_AXI_RREADY  <= 1'b0;

        end else begin
            case (state)

                IDLE: begin
                    HREADYOUT     <= 1'b1;
                    M_AXI_AWVALID <= 1'b0;
                    M_AXI_WVALID  <= 1'b0;
                    M_AXI_BREADY  <= 1'b0;
                    M_AXI_ARVALID <= 1'b0;
                    M_AXI_RREADY  <= 1'b0;

                    if (HSEL && HTRANS[1] && HREADY) begin
                        is_write      <= HWRITE;
                        latched_addr  <= HADDR;
                        latched_wdata <= HWDATA;
                        HREADYOUT     <= 1'b0;

                        if (HWRITE) begin
                            M_AXI_AWVALID <= 1'b1;
                            M_AXI_AWADDR  <= HADDR;
                        end else begin
                            M_AXI_ARVALID <= 1'b1;
                            M_AXI_ARADDR  <= HADDR;
                        end
                        state <= ADDR;
                    end
                end

                ADDR: begin
                    if (is_write) begin
                        // Wait for AWREADY
                        if (M_AXI_AWREADY) begin
                            M_AXI_AWVALID <= 1'b0;
                            M_AXI_WVALID  <= 1'b1;
                            M_AXI_WDATA   <= latched_wdata;
                            M_AXI_BREADY  <= 1'b1;
                            state <= DATA;
                        end else begin
                            M_AXI_AWVALID <= 1'b1;
                            M_AXI_AWADDR  <= latched_addr;
                        end
                    end else begin
                        // Wait for ARREADY
                        if (M_AXI_ARREADY) begin
                            M_AXI_ARVALID <= 1'b0;
                            M_AXI_RREADY  <= 1'b1;
                            state <= DATA;
                        end else begin
                            M_AXI_ARVALID <= 1'b1;
                            M_AXI_ARADDR  <= latched_addr;
                        end
                    end
                end

                DATA: begin
                    if (is_write) begin
                        // W channel: deassert after WREADY
                        if (M_AXI_WREADY) begin
                            M_AXI_WVALID <= 1'b0;
                            M_AXI_WDATA  <= 32'd0;
                        end

                        // B channel: wait for BVALID
                        M_AXI_BREADY <= 1'b1;
                        if (M_AXI_BVALID) begin
                            M_AXI_BREADY <= 1'b0;
                            HRESP    <= (M_AXI_BRESP == 2'b00) ? 1'b0 : 1'b1;
                            HREADYOUT <= 1'b1;
                            state <= IDLE;
                        end
                    end else begin
                        // R channel: wait for RVALID
                        M_AXI_RREADY <= 1'b1;
                        if (M_AXI_RVALID) begin
                            M_AXI_RREADY <= 1'b0;
                            HRDATA   <= M_AXI_RDATA;
                            HRESP    <= (M_AXI_RRESP == 2'b00) ? 1'b0 : 1'b1;
                            HREADYOUT <= 1'b1;
                            state <= IDLE;
                        end
                    end
                end

                default: begin
                    state <= IDLE;
                    HREADYOUT <= 1'b1;
                end

            endcase
        end
    end

endmodule
