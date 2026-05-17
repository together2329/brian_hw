// dma_real_tb.sv — Cocotb testbench wrapper for dma_real_top v2
// Dual-clock: pclk + hclk
module dma_real_tb #(
    parameter integer ADDR_WIDTH = 32,
    parameter integer DATA_WIDTH = 32,
    parameter integer N_CHANNELS = 4,
    parameter integer BURST_MAX  = 16,
    parameter integer FIFO_DEPTH = 8
) ();

    logic pclk, hclk;
    logic presetn, hresetn;
    logic psel, penable, pwrite;
    logic [11:0]           paddr;
    logic [DATA_WIDTH-1:0] pwdata, prdata;
    logic                  pready, pslverr;
    logic [ADDR_WIDTH-1:0] haddr;
    logic                  hwrite;
    logic [1:0]            htrans;
    logic [2:0]            hsize, hburst;
    logic [3:0]            hprot;
    logic [3:0]            hmaster;
    logic                  hmastlock;
    logic [DATA_WIDTH-1:0] hwdata, hrdata;
    logic                  hready;
    logic [1:0]            hresp;
    logic                  hbusreq, hgrant;
    logic [N_CHANNELS-1:0] irq;
    logic                  irq_combined;
    logic [N_CHANNELS-1:0] ch_busy, ch_done, ch_error;
    logic [7:0]            ch_err_code;
    logic [2:0]            arb_grant;

    initial begin
        pclk = 1'b0; hclk = 1'b0;
        forever #5 begin pclk = ~pclk; hclk = ~pclk; end
    end

    dma_real_top #(
        .ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH),
        .N_CHANNELS(N_CHANNELS), .BURST_MAX(BURST_MAX), .FIFO_DEPTH(FIFO_DEPTH)
    ) u_dut (
        .pclk(pclk), .hclk(hclk), .presetn(presetn), .hresetn(hresetn),
        .psel(psel), .penable(penable), .pwrite(pwrite),
        .paddr(paddr), .pwdata(pwdata), .prdata(prdata), .pready(pready), .pslverr(pslverr),
        .haddr(haddr), .hwrite(hwrite), .htrans(htrans), .hsize(hsize), .hburst(hburst),
        .hprot(hprot), .hmaster(hmaster), .hmastlock(hmastlock),
        .hwdata(hwdata), .hrdata(hrdata), .hready(hready), .hresp(hresp),
        .hbusreq(hbusreq), .hgrant(hgrant),
        .irq(irq), .irq_combined(irq_combined),
        .ch_busy(ch_busy), .ch_done(ch_done), .ch_error(ch_error),
        .ch_err_code(ch_err_code), .arb_grant(arb_grant)
    );

    // AHB-Lite slave response model
    logic [DATA_WIDTH-1:0] ahb_mem [0:65535];
    always @(posedge hclk) begin
        hready <= 1'b1;
        hresp  <= 2'b00;
        if (htrans == 2'b10 || htrans == 2'b11) begin
            if (hwrite)
                ahb_mem[haddr[17:2]] <= hwdata;
            else
                hrdata <= ahb_mem[haddr[17:2]];
        end
    end
    assign hgrant = hbusreq;

endmodule
