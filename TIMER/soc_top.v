
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: soc_top
// Description: Top-level SoC with AHB arbiter, AHB-APB bridge, SRAM, and
//              APB peripherals including DMA controller.
//
// Architecture:
//   CPU (AHB master 0) ──┐
//                         ├→ AHB Arbiter → Decoder ─┬→ AHB-APB Bridge → 5 APB slaves
//   DMA (AHB master 1) ──┘                          └→ SRAM (64KB, direct AHB slave)
//
// Address Map:
//   0x0000_0000 - 0x0000_0FFF : Timer APB registers      (bridge slave 0)
//   0x0000_1000 - 0x0000_1FFF : Counter APB registers     (bridge slave 1)
//   0x0000_2000 - 0x0000_2FFF : UART APB registers        (bridge slave 2)
//   0x0000_3000 - 0x0000_3FFF : SPI APB registers         (bridge slave 3)
//   0x0000_4000 - 0x0000_4FFF : DMA APB registers         (bridge slave 4)
//   0x2000_0000 - 0x2000_FFFF : SRAM (64KB)               (direct AHB slave)
//
// DMA has dual interfaces:
//   - APB slave (bridge slave 4) for CPU register configuration
//   - AHB master (arbiter master 1) for data transfers
//----------------------------------------------------------------------------

module soc_top (
    input  wire         HCLK,
    input  wire         HRESETn,

    // AHB-Lite Master Interface (from CPU / testbench)
    input  wire [31:0]  HADDR,
    input  wire [31:0]  HWDATA,
    output wire [31:0]  HRDATA,
    input  wire         HWRITE,
    input  wire [1:0]   HTRANS,
    input  wire [2:0]   HSIZE,

    // UART serial pins
    input  wire         uart_rx_in,
    output wire         uart_tx_out,

    // SPI pins
    input  wire         spi_miso,
    output wire         spi_mosi,
    output wire         spi_sck,
    output wire         spi_cs_n,

    // Interrupt outputs
    output wire         irq_timer,
    output wire         irq_counter,
    output wire         irq_uart,
    output wire         irq_spi,
    output wire         dma_irq
);

    //==========================================================================
    // SIGNAL DECLARATIONS
    //==========================================================================

    //--------------------------------------------------------------------------
    // AHB Arbiter signals
    //--------------------------------------------------------------------------
    // CPU is master 0 (connected to external ports)
    // DMA is master 1
    wire        cpu_hgrant;
    wire [31:0] cpu_hrdata;
    wire        cpu_hready;

    wire [31:0] dma_m_haddr;
    wire [31:0] dma_m_hwdata;
    wire        dma_m_hwrite;
    wire [1:0]  dma_m_htrans;
    wire [2:0]  dma_m_hsize;
    wire        dma_m_hbusreq;
    wire        dma_m_hgrant;
    wire [31:0] dma_m_hrdata;
    wire        dma_m_hready;

    // Shared bus (arbiter output → decoder)
    wire [31:0] shared_haddr;
    wire [31:0] shared_hwdata;
    wire        shared_hwrite;
    wire [1:0]  shared_htrans;
    wire [2:0]  shared_hsize;

    // Slave response (decoder → arbiter)
    wire [31:0] shared_hrdata;
    wire        shared_hreadyout;
    wire        shared_hresp;

    //--------------------------------------------------------------------------
    // Address decoder signals
    //--------------------------------------------------------------------------
    wire sel_sram   = shared_haddr[29];   // 0x2000_0000+
    wire sel_bridge = ~shared_haddr[29];  // 0x0000_0000 - 0x1FFF_FFFF

    //--------------------------------------------------------------------------
    // Bridge signals
    //--------------------------------------------------------------------------
    wire [4:0]  bridge_psel;
    wire        bridge_penable;
    wire        bridge_pwrite;
    wire [31:0] bridge_paddr;
    wire [31:0] bridge_pwdata;
    wire [31:0] bridge_hrdata_internal;
    wire        bridge_hreadyout;
    wire        bridge_hresp;

    wire [31:0] timer_prdata,   counter_prdata,  uart_prdata,  spi_prdata,  dma_s_prdata;
    wire        timer_pready,   counter_pready,   uart_pready,  spi_pready,  dma_s_pready;

    //--------------------------------------------------------------------------
    // SRAM signals
    //--------------------------------------------------------------------------
    wire [31:0] sram_hrdata;
    wire        sram_hreadyout;
    wire        sram_hresp;

    //--------------------------------------------------------------------------
    // DMA APB slave signals (from bridge)
    //--------------------------------------------------------------------------
    wire        dma_s_psel    = bridge_psel[4];
    // PENABLE, PWRITE, PADDR, PWDATA shared from bridge

    //==========================================================================
    // ADDRESS DECODER + SLAVE RESPONSE MUX
    //==========================================================================

    // HSEL for each slave
    wire bridge_hsel = sel_bridge;
    wire sram_hsel   = sel_sram;

    // Global HREADY: selected slave's HREADYOUT feeds back to all slaves
    wire global_hready = sel_sram ? sram_hreadyout : bridge_hreadyout;

    // Slave response mux → arbiter
    assign shared_hrdata    = sel_sram ? sram_hrdata            : bridge_hrdata_internal;
    assign shared_hreadyout = global_hready;
    assign shared_hresp     = sel_sram ? sram_hresp             : bridge_hresp;

    // CPU HRDATA output from arbiter
    assign HRDATA = cpu_hrdata;

    //==========================================================================
    // AHB ARBITER (2 masters: CPU=0, DMA=1)
    //==========================================================================

    ahb_arbiter u_arbiter (
        .HCLK       (HCLK),
        .HRESETn    (HRESETn),

        // Master 0 (CPU)
        .m0_haddr   (HADDR),
        .m0_hwdata  (HWDATA),
        .m0_hwrite  (HWRITE),
        .m0_htrans  (HTRANS),
        .m0_hsize   (HSIZE),
        .m0_hbusreq (1'b0),          // CPU is default master, never requests
        .m0_hgrant  (cpu_hgrant),
        .m0_hrdata  (cpu_hrdata),
        .m0_hready  (cpu_hready),

        // Master 1 (DMA)
        .m1_haddr   (dma_m_haddr),
        .m1_hwdata  (dma_m_hwdata),
        .m1_hwrite  (dma_m_hwrite),
        .m1_htrans  (dma_m_htrans),
        .m1_hsize   (dma_m_hsize),
        .m1_hbusreq (dma_m_hbusreq),
        .m1_hgrant  (dma_m_hgrant),
        .m1_hrdata  (dma_m_hrdata),
        .m1_hready  (dma_m_hready),

        // Shared bus to decoder/slaves
        .haddr      (shared_haddr),
        .hwdata     (shared_hwdata),
        .hwrite     (shared_hwrite),
        .htrans     (shared_htrans),
        .hsize      (shared_hsize),

        // Slave response from decoder
        .s_hrdata   (shared_hrdata),
        .s_hreadyout(shared_hreadyout),
        .s_hresp    (shared_hresp)
    );

    //==========================================================================
    // AHB-APB BRIDGE (5 APB slaves)
    //==========================================================================

    ahb_apb_bridge u_bridge (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),
        .HSEL      (bridge_hsel),
        .HTRANS    (shared_htrans),
        .HSIZE     (shared_hsize),
        .HWRITE    (shared_hwrite),
        .HADDR     (shared_haddr),
        .HWDATA    (shared_hwdata),
        .HRDATA    (bridge_hrdata_internal),
        .HREADYOUT (bridge_hreadyout),
        .HRESP     (bridge_hresp),
        .HREADY    (global_hready),

        .PCLK      (),
        .PRESETn   (),
        .PSEL      (bridge_psel),
        .PENABLE   (bridge_penable),
        .PWRITE    (bridge_pwrite),
        .PADDR     (bridge_paddr),
        .PWDATA    (bridge_pwdata),
        .PRDATA0   (timer_prdata),
        .PRDATA1   (counter_prdata),
        .PRDATA2   (uart_prdata),
        .PRDATA3   (spi_prdata),
        .PRDATA4   (dma_s_prdata),
        .PREADY0   (timer_pready),
        .PREADY1   (counter_pready),
        .PREADY2   (uart_pready),
        .PREADY3   (spi_pready),
        .PREADY4   (dma_s_pready)
    );

    //==========================================================================
    // SRAM (direct AHB slave, 64KB)
    //==========================================================================

    sram u_sram (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),
        .HSEL      (sram_hsel),
        .HADDR     (shared_haddr),
        .HWDATA    (shared_hwdata),
        .HRDATA    (sram_hrdata),
        .HWRITE    (shared_hwrite),
        .HTRANS    (shared_htrans),
        .HSIZE     (shared_hsize),
        .HREADYOUT (sram_hreadyout),
        .HRESP     (sram_hresp),
        .HREADY    (global_hready)
    );

    //==========================================================================
    // DMA CONTROLLER (APB slave for config + AHB master for transfers)
    //==========================================================================

    dma u_dma (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),

        // APB slave interface (bridge slave 4)
        .PSEL      (dma_s_psel),
        .PENABLE   (bridge_penable),
        .PWRITE    (bridge_pwrite),
        .PADDR     (bridge_paddr[7:0]),
        .PWDATA    (bridge_pwdata),
        .PRDATA    (dma_s_prdata),
        .PREADY    (dma_s_pready),
        .PSLVERR   (),

        // AHB master interface (arbiter master 1)
        .HADDR     (dma_m_haddr),
        .HWDATA    (dma_m_hwdata),
        .HRDATA    (dma_m_hrdata),
        .HWRITE    (dma_m_hwrite),
        .HTRANS    (dma_m_htrans),
        .HSIZE     (dma_m_hsize),
        .HBUSREQ   (dma_m_hbusreq),
        .HGRANT    (dma_m_hgrant),
        .HREADY    (dma_m_hready),

        // Interrupt
        .dma_irq   (dma_irq)
    );

    //==========================================================================
    // APB PERIPHERALS
    //==========================================================================

    //--------------------------------------------------------------------------
    // Timer APB Slave (Slave 0: base 0x0000_0000)
    //--------------------------------------------------------------------------
    timer_apb u_timer_apb (
        .PCLK    (HCLK),
        .PRESETn (HRESETn),
        .PSEL    (bridge_psel[0]),
        .PENABLE (bridge_penable),
        .PWRITE  (bridge_pwrite),
        .PADDR   (bridge_paddr[7:0]),
        .PWDATA  (bridge_pwdata),
        .PRDATA  (timer_prdata),
        .PREADY  (timer_pready),
        .PSLVERR (),
        .irq     (irq_timer)
    );

    //--------------------------------------------------------------------------
    // Counter APB Slave (Slave 1: base 0x0000_1000)
    //--------------------------------------------------------------------------
    counter_apb u_counter_apb (
        .PCLK    (HCLK),
        .PRESETn (HRESETn),
        .PSEL    (bridge_psel[1]),
        .PENABLE (bridge_penable),
        .PWRITE  (bridge_pwrite),
        .PADDR   (bridge_paddr[7:0]),
        .PWDATA  (bridge_pwdata),
        .PRDATA  (counter_prdata),
        .PREADY  (counter_pready),
        .PSLVERR (),
        .irq     (irq_counter)
    );

    //--------------------------------------------------------------------------
    // UART APB Slave (Slave 2: base 0x0000_2000)
    //--------------------------------------------------------------------------
    uart_apb u_uart_apb (
        .PCLK        (HCLK),
        .PRESETn     (HRESETn),
        .PSEL        (bridge_psel[2]),
        .PENABLE     (bridge_penable),
        .PWRITE      (bridge_pwrite),
        .PADDR       (bridge_paddr[7:0]),
        .PWDATA      (bridge_pwdata),
        .PRDATA      (uart_prdata),
        .PREADY      (uart_pready),
        .PSLVERR     (),
        .rx_in       (uart_rx_in),
        .tx_out      (uart_tx_out),
        .irq         (irq_uart),
        .rx_overflow ()
    );

    //--------------------------------------------------------------------------
    // SPI APB Slave (Slave 3: base 0x0000_3000)
    //--------------------------------------------------------------------------
    spi_apb u_spi_apb (
        .PCLK    (HCLK),
        .PRESETn (HRESETn),
        .PSEL    (bridge_psel[3]),
        .PENABLE (bridge_penable),
        .PWRITE  (bridge_pwrite),
        .PADDR   (bridge_paddr[7:0]),
        .PWDATA  (bridge_pwdata),
        .PRDATA  (spi_prdata),
        .PREADY  (spi_pready),
        .PSLVERR (),
        .miso    (spi_miso),
        .mosi    (spi_mosi),
        .sck     (spi_sck),
        .cs_n    (spi_cs_n),
        .irq     (irq_spi)
    );

endmodule
