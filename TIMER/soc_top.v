
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: soc_top
// Description: Top-level SoC with AHB arbiter, AHB-APB bridge, SRAM,
//              AHB-AXI bridge, AI engine, DMA, and APB peripherals.
//
// Architecture:
//   CPU (AHB master 0) ──┐
//                         ├→ AHB Arbiter → Decoder ─┬→ AHB-APB Bridge → 7 APB slaves
//   DMA (AHB master 1) ──┘                          ├→ SRAM (64KB, direct AHB slave)
//                                                   └→ AHB-AXI Bridge → AI Engine
//
// Address Map:
//   0x0000_0000 - 0x0000_0FFF : Timer APB registers      (bridge slave 0)
//   0x0000_1000 - 0x0000_1FFF : Counter APB registers     (bridge slave 1)
//   0x0000_2000 - 0x0000_2FFF : UART APB registers        (bridge slave 2)
//   0x0000_3000 - 0x0000_3FFF : SPI APB registers         (bridge slave 3)
//   0x0000_4000 - 0x0000_4FFF : DMA APB registers         (bridge slave 4)
//   0x0000_5000 - 0x0000_5FFF : I3C APB registers         (bridge slave 5)
//   0x0000_6000 - 0x0000_6FFF : SMBus APB registers       (bridge slave 6)
//   0x2000_0000 - 0x2000_FFFF : SRAM (64KB)               (direct AHB slave)
//   0x3000_0000 - 0x3FFF_FFFF : AI Engine (via AXI bridge)
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
    output wire         HREADY,

    // UART serial pins
    input  wire         uart_rx_in,
    output wire         uart_tx_out,

    // SPI pins
    input  wire         spi_miso,
    output wire         spi_mosi,
    output wire         spi_sck,
    output wire         spi_cs_n,

    // I3C pins (triplet for bidirectional SDA)
    input  wire         i3c_sda_in,
    output wire         i3c_sda_out,
    output wire         i3c_sda_oe,
    output wire         i3c_scl_out,
    output wire         i3c_scl_oe,

    // SMBus pins (triplet for bidirectional SMBDAT)
    input  wire         smbus_smbdat_in,
    output wire         smbus_smbdat_out,
    output wire         smbus_smbdat_oe,
    output wire         smbus_smbclk_out,
    output wire         smbus_smbclk_oe,

    // Interrupt outputs
    output wire         irq_timer,
    output wire         irq_counter,
    output wire         irq_uart,
    output wire         irq_spi,
    output wire         dma_irq,
    output wire         irq_i3c,
    output wire         irq_smbus,
    output wire         irq_ai
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
    // Decode address regions:
    //   [29] = 0: AHB-APB bridge (0x0000_0000 - 0x1FFF_FFFF)
    //   [29] = 1, [28] = 0: SRAM (0x2000_0000 - 0x2FFF_FFFF)
    //   [29] = 1, [28] = 1: AHB-AXI bridge (0x3000_0000 - 0x3FFF_FFFF)
    wire sel_axi    = shared_haddr[29] && shared_haddr[28];   // 0x3000_0000+
    wire sel_sram   = shared_haddr[29] && ~shared_haddr[28];   // 0x2000_0000+
    wire sel_bridge = ~shared_haddr[29];                       // 0x0000_0000 - 0x1FFF_FFFF

    //--------------------------------------------------------------------------
    // Bridge signals
    //--------------------------------------------------------------------------
    wire [6:0]  bridge_psel;
    wire        bridge_penable;
    wire        bridge_pwrite;
    wire [31:0] bridge_paddr;
    wire [31:0] bridge_pwdata;
    wire [31:0] bridge_hrdata_internal;
    wire        bridge_hreadyout;
    wire        bridge_hresp;

    wire [31:0] timer_prdata,   counter_prdata,  uart_prdata,  spi_prdata,  dma_s_prdata,  i3c_prdata,  smbus_prdata;
    wire        timer_pready,   counter_pready,   uart_pready,  spi_pready,  dma_s_pready,  i3c_pready,  smbus_pready;

    //--------------------------------------------------------------------------
    // SRAM signals
    //--------------------------------------------------------------------------
    wire [31:0] sram_hrdata;
    wire        sram_hreadyout;
    wire        sram_hresp;

    //--------------------------------------------------------------------------
    // AHB-AXI Bridge signals
    //--------------------------------------------------------------------------
    wire [31:0] axi_hrdata;
    wire        axi_hreadyout;
    wire        axi_hresp;

    // AXI4-Lite channels (bridge master → AI engine slave)
    wire        m_axi_awvalid;
    wire        m_axi_awready;
    wire [31:0] m_axi_awaddr;
    wire        m_axi_wvalid;
    wire        m_axi_wready;
    wire [31:0] m_axi_wdata;
    wire        m_axi_bvalid;
    wire        m_axi_bready;
    wire [1:0]  m_axi_bresp;
    wire        m_axi_arvalid;
    wire        m_axi_arready;
    wire [31:0] m_axi_araddr;
    wire        m_axi_rvalid;
    wire        m_axi_rready;
    wire [31:0] m_axi_rdata;
    wire [1:0]  m_axi_rresp;

    // AI engine IRQ (internal wire → top-level port)
    wire        ai_irq_int;

    //--------------------------------------------------------------------------
    // DMA APB slave signals (from bridge)
    //--------------------------------------------------------------------------
    wire        dma_s_psel    = bridge_psel[4];

    // I3C APB slave signals (from bridge)
    wire        i3c_psel      = bridge_psel[5];

    // SMBus APB slave signals (from bridge)
    wire        smbus_psel    = bridge_psel[6];
    // PENABLE, PWRITE, PADDR, PWDATA shared from bridge

    //==========================================================================
    // ADDRESS DECODER + SLAVE RESPONSE MUX
    //==========================================================================

    // HSEL for each slave
    wire bridge_hsel = sel_bridge;
    wire sram_hsel   = sel_sram;
    wire axi_hsel    = sel_axi;

    // Global HREADY: selected slave's HREADYOUT feeds back to all slaves
    wire global_hready = sel_axi ? axi_hreadyout :
                         sel_sram ? sram_hreadyout :
                         bridge_hreadyout;

    // Slave response mux → arbiter
    assign shared_hrdata    = sel_axi ? axi_hrdata            :
                              sel_sram ? sram_hrdata          :
                              bridge_hrdata_internal;
    assign shared_hreadyout = global_hready;
    assign shared_hresp     = sel_axi ? axi_hresp             :
                              sel_sram ? sram_hresp           :
                              bridge_hresp;

    // CPU HRDATA and HREADY outputs from arbiter
    assign HRDATA = cpu_hrdata;
    assign HREADY = cpu_hready;

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
        .PRDATA5   (i3c_prdata),
        .PRDATA6   (smbus_prdata),
        .PREADY0   (timer_pready),
        .PREADY1   (counter_pready),
        .PREADY2   (uart_pready),
        .PREADY3   (spi_pready),
        .PREADY4   (dma_s_pready),
        .PREADY5   (i3c_pready),
        .PREADY6   (smbus_pready)
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

    //--------------------------------------------------------------------------
    // I3C APB Slave (Slave 5: base 0x0000_5000)
    //--------------------------------------------------------------------------
    i3c_apb u_i3c_apb (
        .PCLK        (HCLK),
        .PRESETn     (HRESETn),
        .PSEL        (i3c_psel),
        .PENABLE     (bridge_penable),
        .PWRITE      (bridge_pwrite),
        .PADDR       (bridge_paddr[7:0]),
        .PWDATA      (bridge_pwdata),
        .PRDATA      (i3c_prdata),
        .PREADY      (i3c_pready),
        .PSLVERR     (),
        .sda_in      (i3c_sda_in),
        .sda_out     (i3c_sda_out),
        .sda_oe      (i3c_sda_oe),
        .scl_out     (i3c_scl_out),
        .scl_oe      (i3c_scl_oe),
        .irq         (irq_i3c)
    );

    //--------------------------------------------------------------------------
    // SMBus APB Slave (Slave 6: base 0x0000_6000)
    //--------------------------------------------------------------------------
    smbus_apb u_smbus_apb (
        .PCLK        (HCLK),
        .PRESETn     (HRESETn),
        .PSEL        (smbus_psel),
        .PENABLE     (bridge_penable),
        .PWRITE      (bridge_pwrite),
        .PADDR       (bridge_paddr[7:0]),
        .PWDATA      (bridge_pwdata),
        .PRDATA      (smbus_prdata),
        .PREADY      (smbus_pready),
        .PSLVERR     (),
        .smbdat_in   (smbus_smbdat_in),
        .smbdat_out  (smbus_smbdat_out),
        .smbdat_oe   (smbus_smbdat_oe),
        .smbclk_out  (smbus_smbclk_out),
        .smbclk_oe   (smbus_smbclk_oe),
        .irq         (irq_smbus)
    );

    //==========================================================================
    // AHB-AXI BRIDGE (translates AHB accesses to AI engine AXI-Lite)
    //   Addr decode: sel_axi = HADDR[29] && HADDR[28] → 0x3000_0000+
    //==========================================================================

    ahb_axi_bridge u_axi_bridge (
        .HCLK           (HCLK),
        .HRESETn        (HRESETn),
        .HSEL           (axi_hsel),
        .HTRANS         (shared_htrans),
        .HSIZE          (shared_hsize),
        .HWRITE         (shared_hwrite),
        .HADDR          (shared_haddr),
        .HWDATA         (shared_hwdata),
        .HRDATA         (axi_hrdata),
        .HREADYOUT      (axi_hreadyout),
        .HRESP          (axi_hresp),
        .HREADY         (global_hready),

        // AXI4-Lite master → AI engine
        .M_AXI_AWVALID  (m_axi_awvalid),
        .M_AXI_AWREADY  (m_axi_awready),
        .M_AXI_AWADDR   (m_axi_awaddr),
        .M_AXI_AWPROT   (),
        .M_AXI_WVALID   (m_axi_wvalid),
        .M_AXI_WREADY   (m_axi_wready),
        .M_AXI_WDATA    (m_axi_wdata),
        .M_AXI_WSTRB    (),
        .M_AXI_BVALID   (m_axi_bvalid),
        .M_AXI_BREADY   (m_axi_bready),
        .M_AXI_BRESP    (m_axi_bresp),
        .M_AXI_ARVALID  (m_axi_arvalid),
        .M_AXI_ARREADY  (m_axi_arready),
        .M_AXI_ARADDR   (m_axi_araddr),
        .M_AXI_ARPROT   (),
        .M_AXI_RVALID   (m_axi_rvalid),
        .M_AXI_RREADY   (m_axi_rready),
        .M_AXI_RDATA    (m_axi_rdata),
        .M_AXI_RRESP    (m_axi_rresp)
    );

    //==========================================================================
    // AI ENGINE (AXI4-Lite slave, 256B SRAM, 8-wide MAC, 5 operations)
    //==========================================================================

    ai_engine u_ai_engine (
        .S_AXI_ACLK     (HCLK),
        .S_AXI_ARESETn  (HRESETn),

        .S_AXI_AWVALID  (m_axi_awvalid),
        .S_AXI_AWREADY  (m_axi_awready),
        .S_AXI_AWADDR   (m_axi_awaddr),
        .S_AXI_AWPROT   (3'b0),
        .S_AXI_WVALID   (m_axi_wvalid),
        .S_AXI_WREADY   (m_axi_wready),
        .S_AXI_WDATA    (m_axi_wdata),
        .S_AXI_WSTRB    (4'b1111),
        .S_AXI_BVALID   (m_axi_bvalid),
        .S_AXI_BREADY   (m_axi_bready),
        .S_AXI_BRESP    (m_axi_bresp),
        .S_AXI_ARVALID  (m_axi_arvalid),
        .S_AXI_ARREADY  (m_axi_arready),
        .S_AXI_ARADDR   (m_axi_araddr),
        .S_AXI_ARPROT   (3'b0),
        .S_AXI_RVALID   (m_axi_rvalid),
        .S_AXI_RREADY   (m_axi_rready),
        .S_AXI_RDATA    (m_axi_rdata),
        .S_AXI_RRESP    (m_axi_rresp),

        .ai_irq         (ai_irq_int)
    );

    // Drive top-level AI IRQ port
    assign irq_ai = ai_irq_int;

endmodule
