// dma_real_tb.sv — Cocotb testbench wrapper for dma_real_top
//
// Instantiates DUT with all interfaces connected to cocotbmodifiable signals.

module dma_real_tb #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer N_CHANNELS = 4,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 8
) ();

    // Clock and reset
    logic pclk;
    logic presetn;

    // APB slave
    logic                  psel;
    logic                  penable;
    logic                  pwrite;
    logic [11:0]           paddr;
    logic [DATA_WIDTH-1:0] pwdata;
    logic [DATA_WIDTH-1:0] prdata;
    logic                  pready;
    logic                  pslverr;

    // AHB-Lite master
    logic [ADDR_WIDTH-1:0] haddr;
    logic                  hwrite;
    logic [1:0]            htrans;
    logic [2:0]            hsize;
    logic [2:0]            hburst;
    logic [DATA_WIDTH-1:0] hwdata;
    logic [DATA_WIDTH-1:0] hrdata;
    logic                  hready;
    logic                  hresp;
    logic                  hbusreq;
    logic                  hgrant;

    // IRQ outputs
    logic [N_CHANNELS-1:0] irq;
    logic                  irq_combined;

    // Status outputs
    logic [N_CHANNELS-1:0] ch_busy;
    logic [N_CHANNELS-1:0] ch_done;
    logic [N_CHANNELS-1:0] ch_error;
    logic [7:0]            ch_err_code;
    logic [2:0]            arb_grant;

    // Clock generation
    initial begin
        pclk = 1'b0;
        forever #5 pclk = ~pclk;
    end

    // DUT instance
    dma_real_top #(
        .ADDR_WIDTH (ADDR_WIDTH),
        .DATA_WIDTH (DATA_WIDTH),
        .N_CHANNELS (N_CHANNELS),
        .BURST_MAX  (BURST_MAX),
        .FIFO_DEPTH (FIFO_DEPTH)
    ) u_dut (
        .pclk        (pclk),
        .presetn     (presetn),
        .psel        (psel),
        .penable     (penable),
        .pwrite      (pwrite),
        .paddr       (paddr),
        .pwdata      (pwdata),
        .prdata      (prdata),
        .pready      (pready),
        .pslverr     (pslverr),
        .haddr       (haddr),
        .hwrite      (hwrite),
        .htrans      (htrans),
        .hsize       (hsize),
        .hburst      (hburst),
        .hwdata      (hwdata),
        .hrdata      (hrdata),
        .hready      (hready),
        .hresp       (hresp),
        .hbusreq     (hbusreq),
        .hgrant      (hgrant),
        .irq         (irq),
        .irq_combined(irq_combined),
        .ch_busy     (ch_busy),
        .ch_done     (ch_done),
        .ch_error    (ch_error),
        .ch_err_code (ch_err_code),
        .arb_grant   (arb_grant)
    );

    // AHB-Lite slave response model (simple memory)
    logic [DATA_WIDTH-1:0] ahb_mem [0:65535];

    always @(posedge pclk) begin
        hready <= 1'b1;
        hresp  <= 1'b0;
        if (htrans == 2'b10 || htrans == 2'b11) begin
            if (hwrite) begin
                ahb_mem[haddr[17:2]] <= hwdata;
            end else begin
                hrdata <= ahb_mem[haddr[17:2]];
            end
        end
    end

    // Grant bus when requested
    assign hgrant = hbusreq;

endmodule
