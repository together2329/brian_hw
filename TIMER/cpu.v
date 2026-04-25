`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: cpu
// Description: AHB-Lite master Bus Functional Model (BFM).
//
// Drives AHB transactions for testbench use. Provides tasks:
//   ahb_write(addr, data) - Single write transfer
//   ahb_read(addr, data)  - Single read transfer
//
// AHB-Lite Master Interface:
//   HCLK      - Bus clock
//   HRESETn   - Active-low reset
//   HADDR     - Address [31:0]
//   HWDATA    - Write data [31:0]
//   HRDATA    - Read data [31:0]
//   HWRITE    - Write strobe
//   HTRANS    - Transfer type [1:0]
//   HSIZE     - Transfer size [2:0] (always word)
//   HBURST    - Burst type [2:0] (always single)
//   HSEL      - Not used at master (bridge has its own decode)
//   HREADY    - Bus ready input
//   HPROT     - Protection [3:0] (always 0011 = data, privileged)
//----------------------------------------------------------------------------

module cpu (
    input  wire         HCLK,
    input  wire         HRESETn,
    output reg  [31:0]  HADDR,
    output reg  [31:0]  HWDATA,
    input  wire [31:0]  HRDATA,
    output reg          HWRITE,
    output reg  [1:0]   HTRANS,
    output reg  [2:0]   HSIZE,
    output reg  [2:0]   HBURST,
    output reg  [3:0]   HPROT,
    input  wire         HREADY
);

    // AHB transfer types
    localparam [1:0] HTRANS_IDLE   = 2'b00;
    localparam [1:0] HTRANS_NONSEQ = 2'b10;

    // AHB burst types
    localparam [2:0] HBURST_SINGLE = 3'b000;

    // AHB sizes
    localparam [2:0] HSIZE_WORD = 3'b010;

    //--------------------------------------------------------------------------
    // Initialize
    //--------------------------------------------------------------------------
    initial begin
        HADDR  <= 32'd0;
        HWDATA <= 32'd0;
        HWRITE <= 1'b0;
        HTRANS <= HTRANS_IDLE;
        HSIZE  <= HSIZE_WORD;
        HBURST <= HBURST_SINGLE;
        HPROT  <= 4'b0011;
    end

    //--------------------------------------------------------------------------
    // AHB Write task
    //--------------------------------------------------------------------------
    task ahb_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            // Address phase
            HADDR  <= addr;
            HWDATA <= data;
            HWRITE <= 1'b1;
            HTRANS <= HTRANS_NONSEQ;
            @(negedge HCLK);
            // Wait for ready
            while (!HREADY) @(negedge HCLK);
            // Return to idle
            HTRANS <= HTRANS_IDLE;
            HWRITE <= 1'b0;
            HADDR  <= 32'd0;
            HWDATA <= 32'd0;
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Read task
    //--------------------------------------------------------------------------
    task ahb_read;
        input  [31:0] addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            // Address phase
            HADDR  <= addr;
            HWRITE <= 1'b0;
            HTRANS <= HTRANS_NONSEQ;
            @(negedge HCLK);
            // Wait for ready
            while (!HREADY) @(negedge HCLK);
            // Capture read data
            data <= HRDATA;
            // Return to idle
            HTRANS <= HTRANS_IDLE;
            HADDR  <= 32'd0;
        end
    endtask

endmodule
