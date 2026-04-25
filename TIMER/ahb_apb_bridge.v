`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: ahb_apb_bridge
// Description: AHB-Lite to APB3 bridge.
//
// Translates AHB-Lite single transfers to APB3 transactions.
// Supports 2 APB slaves selected by address decode:
//   Slave 0 (timer_apb)  : 0x0000_0000 - 0x0000_0FFF
//   Slave 1 (counter_apb): 0x0000_1000 - 0x0000_1FFF
//
// AHB-Lite Slave Interface:
//   HCLK      - Bus clock
//   HRESETn   - Active-low reset
//   HSEL      - Slave select
//   HTRANS    - Transfer type [1:0]: 00=IDLE, 10=NONSEQ
//   HSIZE     - Transfer size [2:0]: 000=byte, 010=word (only word supported)
//   HWRITE    - Write strobe (1=write, 0=read)
//   HADDR     - Address [31:0]
//   HWDATA    - Write data [31:0]
//   HRDATA    - Read data [31:0]
//   HREADYOUT - Transfer complete
//   HRESP     - Response (0=OKAY)
//   HREADY    - Bus ready (from mux, input)
//
// APB3 Master Interface:
//   PCLK      - APB clock (same as HCLK)
//   PRESETn   - APB reset (same as HRESETn)
//   PSEL      - Peripheral select [1:0], one-hot
//   PENABLE   - Enable
//   PWRITE    - Write strobe
//   PADDR     - Address [31:0]
//   PWDATA    - Write data [31:0]
//   PRDATA0   - Read data from slave 0 [31:0]
//   PRDATA1   - Read data from slave 1 [31:0]
//   PREADY0   - Ready from slave 0
//   PREADY1   - Ready from slave 1
//----------------------------------------------------------------------------

module ahb_apb_bridge (
    // AHB-Lite Slave Interface
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

    // APB3 Master Interface
    output wire         PCLK,
    output wire         PRESETn,
    output wire [1:0]   PSEL,
    output wire         PENABLE,
    output wire         PWRITE,
    output wire [31:0]  PADDR,
    output wire [31:0]  PWDATA,
    input  wire [31:0]  PRDATA0,
    input  wire [31:0]  PRDATA1,
    input  wire         PREADY0,
    input  wire         PREADY1
);

    assign PCLK   = HCLK;
    assign PRESETn = HRESETn;

    //--------------------------------------------------------------------------
    // Address decode
    //--------------------------------------------------------------------------
    wire sel_slave0 = (HADDR[31:12] == 20'd0);    // 0x0000_0000 - 0x0000_0FFF
    wire sel_slave1 = (HADDR[19:12] == 8'd1) &&
                      (HADDR[31:20] == 12'd0);     // 0x0000_1000 - 0x0000_1FFF

    //--------------------------------------------------------------------------
    // FSM states
    //--------------------------------------------------------------------------
    localparam IDLE   = 2'd0;
    localparam SETUP  = 2'd1;
    localparam ACCESS = 2'd2;

    reg [1:0] state;

    // Latched transfer info
    reg        latched_write;
    reg [31:0] latched_addr;
    reg [31:0] latched_wdata;
    reg [1:0]  latched_sel;

    //--------------------------------------------------------------------------
    // FSM
    //--------------------------------------------------------------------------
    always @(posedge HCLK) begin
        if (!HRESETn) begin
            state         <= IDLE;
            HREADYOUT     <= 1'b1;
            HRESP         <= 1'b0;
            HRDATA        <= 32'd0;
            latched_write <= 1'b0;
            latched_addr  <= 32'd0;
            latched_wdata <= 32'd0;
            latched_sel   <= 2'd0;
        end else begin
            case (state)
                IDLE: begin
                    HREADYOUT <= 1'b1;
                    if (HSEL && HTRANS[1] && HREADY) begin
                        // Latch AHB transfer
                        latched_write <= HWRITE;
                        latched_addr  <= HADDR;
                        latched_wdata <= HWDATA;
                        latched_sel   <= {sel_slave1, sel_slave0};
                        state         <= SETUP;
                        HREADYOUT     <= 1'b0;
                    end
                end

                SETUP: begin
                    // APB SETUP phase (1 cycle)
                    state <= ACCESS;
                end

                ACCESS: begin
                    // APB ACCESS phase
                    if ((latched_sel[0] && PREADY0) ||
                        (latched_sel[1] && PREADY1) ||
                        (latched_sel == 2'd0)) begin

                        // Read data mux
                        if (latched_sel[0])
                            HRDATA <= PRDATA0;
                        else if (latched_sel[1])
                            HRDATA <= PRDATA1;
                        else
                            HRDATA <= 32'd0;

                        HRESP     <= 1'b0;
                        HREADYOUT <= 1'b1;
                        state     <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

    //--------------------------------------------------------------------------
    // APB output assignments
    //--------------------------------------------------------------------------
    assign PSEL    = (state == SETUP || state == ACCESS) ? latched_sel : 2'd0;
    assign PENABLE = (state == ACCESS);
    assign PWRITE  = latched_write;
    assign PADDR   = latched_addr;
    assign PWDATA  = latched_wdata;

endmodule
