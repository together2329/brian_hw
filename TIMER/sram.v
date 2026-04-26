
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: sram
// Description: AHB-Lite behavioral SRAM slave (64KB).
//
// 64KB storage implemented as 16384 x 32-bit register array.
// Single-cycle read/write with no wait states (HREADYOUT always 1).
// Read data is provided combinationally for zero-latency access.
//
// Address Map:
//   Base: 0x2000_0000
//   HADDR[15:2] used as word index (14 bits = 16K words = 64KB)
//
// AHB-Lite Slave Interface:
//   HCLK      - Bus clock
//   HRESETn   - Active-low reset
//   HSEL      - Slave select
//   HADDR     - Address [31:0]
//   HWDATA    - Write data [31:0]
//   HRDATA    - Read data [31:0] (combinational)
//   HWRITE    - Write strobe
//   HTRANS    - Transfer type [1:0]
//   HSIZE     - Transfer size [2:0]
//   HREADYOUT - Transfer complete (always 1)
//   HRESP     - Response (always OKAY)
//   HREADY    - Bus ready input
//----------------------------------------------------------------------------

module sram (
    input  wire         HCLK,
    input  wire         HRESETn,
    input  wire         HSEL,
    input  wire [31:0]  HADDR,
    input  wire [31:0]  HWDATA,
    output reg  [31:0]  HRDATA,
    input  wire         HWRITE,
    input  wire [1:0]   HTRANS,
    input  wire [2:0]   HSIZE,
    output wire         HREADYOUT,
    output wire         HRESP,
    input  wire         HREADY
);

    //--------------------------------------------------------------------------
    // Memory array: 16384 words x 32 bits = 64KB
    //--------------------------------------------------------------------------
    reg [31:0] mem [0:16383];

    //--------------------------------------------------------------------------
    // Word address from byte address
    //   HADDR[15:2] gives 14-bit word index (0 to 16383)
    //--------------------------------------------------------------------------
    wire [13:0] word_addr = HADDR[15:2];

    //--------------------------------------------------------------------------
    // AHB transfer detection
    //   Valid transfer when selected, NONSEQ, and bus ready
    //--------------------------------------------------------------------------
    wire ahb_valid = HSEL && HTRANS[1] && HREADY;

    //--------------------------------------------------------------------------
    // Write: sequential (at posedge)
    //--------------------------------------------------------------------------
    always @(posedge HCLK) begin
        if (!HRESETn) begin
            // Nothing to reset for the memory array
        end else if (ahb_valid && HWRITE) begin
            mem[word_addr] <= HWDATA;
        end
    end

    //--------------------------------------------------------------------------
    // Read: combinational (zero-latency)
    //   Provides data immediately during the address phase so the master
    //   can capture it at the next clock edge.
    //--------------------------------------------------------------------------
    always @(*) begin
        if (HSEL && !HWRITE)
            HRDATA = mem[word_addr];
        else
            HRDATA = 32'd0;
    end

    //--------------------------------------------------------------------------
    // Constant outputs: always ready, no errors
    //--------------------------------------------------------------------------
    assign HREADYOUT = 1'b1;   // No wait states
    assign HRESP     = 1'b0;   // Always OKAY

endmodule
