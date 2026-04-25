
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: ahb_apb_bridge
// Description: AHB-Lite to APB3 bridge.
//
// Translates AHB-Lite single transfers to APB3 transactions.
// Supports 4 APB slaves selected by address decode:
//   Slave 0 (timer_apb)  : 0x0000_0000 - 0x0000_0FFF
//   Slave 1 (counter_apb): 0x0000_1000 - 0x0000_1FFF
//   Slave 2 (uart_apb)   : 0x0000_2000 - 0x0000_2FFF
//   Slave 3 (reserved)   : 0x0000_3000 - 0x0000_3FFF
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
//   PSEL      - Peripheral select [3:0], one-hot
//   PENABLE   - Enable
//   PWRITE    - Write strobe
//   PADDR     - Address [31:0]
//   PWDATA    - Write data [31:0]
//   PRDATA0-3 - Read data from slaves 0-3 [31:0]
//   PREADY0-3 - Ready from slaves 0-3
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
    output wire [3:0]   PSEL,
    output wire         PENABLE,
    output wire         PWRITE,
    output wire [31:0]  PADDR,
    output wire [31:0]  PWDATA,
    input  wire [31:0]  PRDATA0,
    input  wire [31:0]  PRDATA1,
    input  wire [31:0]  PRDATA2,
    input  wire [31:0]  PRDATA3,
    input  wire         PREADY0,
    input  wire         PREADY1,
    input  wire         PREADY2,
    input  wire         PREADY3
);

    assign PCLK    = HCLK;
    assign PRESETn = HRESETn;

    //--------------------------------------------------------------------------
    // Address decode - use upper bits of address
    //   Each slave gets 4KB address space (12-bit offset)
    //   Slave index = HADDR[13:12]
    //--------------------------------------------------------------------------
    wire [1:0] slave_idx = HADDR[13:12];

    wire sel_slave0 = (slave_idx == 2'd0);  // 0x0000 - 0x0FFF
    wire sel_slave1 = (slave_idx == 2'd1);  // 0x1000 - 0x1FFF
    wire sel_slave2 = (slave_idx == 2'd2);  // 0x2000 - 0x2FFF
    wire sel_slave3 = (slave_idx == 2'd3);  // 0x3000 - 0x3FFF

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
    reg [3:0]  latched_sel;

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
            latched_sel   <= 4'd0;
        end else begin
            case (state)
                IDLE: begin
                    HREADYOUT <= 1'b1;
                    if (HSEL && HTRANS[1] && HREADY) begin
                        // Latch AHB transfer
                        latched_write <= HWRITE;
                        latched_addr  <= HADDR;
                        latched_wdata <= HWDATA;
                        latched_sel   <= {sel_slave3, sel_slave2, sel_slave1, sel_slave0};
                        state         <= SETUP;
                        HREADYOUT     <= 1'b0;
                    end
                end

                SETUP: begin
                    // APB SETUP phase (1 cycle)
                    state <= ACCESS;
                end

                ACCESS: begin
                    // APB ACCESS phase - check PREADY from selected slave
                    if ((latched_sel[0] && PREADY0) ||
                        (latched_sel[1] && PREADY1) ||
                        (latched_sel[2] && PREADY2) ||
                        (latched_sel[3] && PREADY3) ||
                        (latched_sel == 4'd0)) begin

                        // Read data mux
                        case (latched_sel)
                            4'b0001: HRDATA <= PRDATA0;
                            4'b0010: HRDATA <= PRDATA1;
                            4'b0100: HRDATA <= PRDATA2;
                            4'b1000: HRDATA <= PRDATA3;
                            default: HRDATA <= 32'd0;
                        endcase

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
    assign PSEL    = (state == SETUP || state == ACCESS) ? latched_sel : 4'd0;
    assign PENABLE = (state == ACCESS);
    assign PWRITE  = latched_write;
    assign PADDR   = latched_addr;
    assign PWDATA  = latched_wdata;

endmodule
