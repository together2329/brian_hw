
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: ahb_arbiter
// Description: AHB-Lite bus arbiter for 2 masters (CPU and DMA).
//
// Fixed priority: CPU (master 0) > DMA (master 1).
// Bus handover occurs only when the current master is IDLE (HTRANS == 00).
// CPU gets the bus by default. DMA requests via HBUSREQ, granted when
// CPU is idle. Bus returns to CPU when DMA completes (idle + no request).
//
// Master Interface (per master):
//   mX_haddr    - Address [31:0]
//   mX_hwdata   - Write data [31:0]
//   mX_hwrite   - Write strobe
//   mX_htrans   - Transfer type [1:0]
//   mX_hsize    - Transfer size [2:0]
//   mX_hbusreq  - Bus request
//   mX_hgrant   - Bus grant
//   mX_hrdata   - Read data [31:0]
//   mX_hready   - Transfer ready
//
// Shared Bus Output (to address decoder):
//   haddr, hwdata, hwrite, htrans, hsize
//
// Slave Response Input (from decoder):
//   s_hrdata, s_hreadyout, s_hresp
//----------------------------------------------------------------------------

module ahb_arbiter (
    input  wire         HCLK,
    input  wire         HRESETn,

    // Master 0 (CPU) signals
    input  wire [31:0]  m0_haddr,
    input  wire [31:0]  m0_hwdata,
    input  wire         m0_hwrite,
    input  wire [1:0]   m0_htrans,
    input  wire [2:0]   m0_hsize,
    input  wire         m0_hbusreq,
    output wire         m0_hgrant,
    output wire [31:0]  m0_hrdata,
    output wire         m0_hready,

    // Master 1 (DMA) signals
    input  wire [31:0]  m1_haddr,
    input  wire [31:0]  m1_hwdata,
    input  wire         m1_hwrite,
    input  wire [1:0]   m1_htrans,
    input  wire [2:0]   m1_hsize,
    input  wire         m1_hbusreq,
    output wire         m1_hgrant,
    output wire [31:0]  m1_hrdata,
    output wire         m1_hready,

    // Shared bus output (to decoder / slaves)
    output wire [31:0]  haddr,
    output wire [31:0]  hwdata,
    output wire         hwrite,
    output wire [1:0]   htrans,
    output wire [2:0]   hsize,

    // Slave response input (from decoder)
    input  wire [31:0]  s_hrdata,
    input  wire         s_hreadyout,
    input  wire         s_hresp
);

    //--------------------------------------------------------------------------
    // Grant register: 0 = CPU, 1 = DMA
    //--------------------------------------------------------------------------
    reg grant;

    always @(posedge HCLK) begin
        if (!HRESETn) begin
            grant <= 1'b0;   // Default: CPU has the bus
        end else begin
            case (grant)
                1'b0: begin  // CPU currently granted
                    // Switch to DMA only when CPU is idle, DMA requests, AND slave is ready
                    // (prevents mid-transfer switch while bridge is in SETUP/ACCESS)
                    if (m0_htrans == 2'b00 && m1_hbusreq && s_hreadyout)
                        grant <= 1'b1;
                end
                1'b1: begin  // DMA currently granted
                    // Return to CPU when DMA is idle, not requesting, AND slave is ready
                    if (m1_htrans == 2'b00 && !m1_hbusreq && s_hreadyout)
                        grant <= 1'b0;
                end
            endcase
        end
    end

    //--------------------------------------------------------------------------
    // Mux master signals onto shared bus (combinational)
    //--------------------------------------------------------------------------
    assign haddr  = grant ? m1_haddr  : m0_haddr;
    assign hwdata = grant ? m1_hwdata : m0_hwdata;
    assign hwrite = grant ? m1_hwrite : m0_hwrite;
    assign htrans = grant ? m1_htrans : m0_htrans;
    assign hsize  = grant ? m1_hsize  : m0_hsize;

    //--------------------------------------------------------------------------
    // Grant outputs
    //--------------------------------------------------------------------------
    assign m0_hgrant = ~grant;
    assign m1_hgrant =  grant;

    //--------------------------------------------------------------------------
    // Demux slave response back to granted master
    //   - Granted master sees actual slave response
    //   - Non-granted master sees HREADY=1 (no stall), HRDATA=0
    //--------------------------------------------------------------------------
    assign m0_hrdata = grant ? 32'd0      : s_hrdata;
    assign m0_hready = grant ? 1'b1       : s_hreadyout;

    assign m1_hrdata = grant ? s_hrdata   : 32'd0;
    assign m1_hready = grant ? s_hreadyout : 1'b1;

endmodule
