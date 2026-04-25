
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: soc_top
// Description: Top-level SoC with AHB-APB bridge and APB peripherals.
//
// AHB master interface exposed as ports for external driving (CPU or BFM).
//
// Address Map:
//   0x0000_0000 - 0x0000_0FFF : Timer APB registers
//   0x0000_1000 - 0x0000_1FFF : Counter APB registers
//   0x0000_2000 - 0x0000_2FFF : UART APB registers
//   0x0000_3000 - 0x0000_3FFF : Reserved
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

    // Interrupt outputs
    output wire         irq_timer,
    output wire         irq_counter,
    output wire         irq_uart
);

    //--------------------------------------------------------------------------
    // Bridge to internal signals
    //--------------------------------------------------------------------------
    wire        bridge_hreadyout;
    wire        bridge_hresp;
    wire [3:0]  bridge_psel;
    wire        bridge_penable;
    wire        bridge_pwrite;
    wire [31:0] bridge_paddr;
    wire [31:0] bridge_pwdata;
    wire [31:0] timer_prdata;
    wire [31:0] counter_prdata;
    wire [31:0] uart_prdata;
    wire        timer_pready;
    wire        counter_pready;
    wire        uart_pready;

    assign HRDATA = bridge_hrdata_internal;

    //--------------------------------------------------------------------------
    // AHB-APB Bridge (HSEL always 1, HREADY feeds back from HREADYOUT)
    //--------------------------------------------------------------------------
    wire [31:0] bridge_hrdata_internal;

    ahb_apb_bridge u_bridge (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),
        .HSEL      (1'b1),
        .HTRANS    (HTRANS),
        .HSIZE     (HSIZE),
        .HWRITE    (HWRITE),
        .HADDR     (HADDR),
        .HWDATA    (HWDATA),
        .HRDATA    (bridge_hrdata_internal),
        .HREADYOUT (bridge_hreadyout),
        .HRESP     (bridge_hresp),
        .HREADY    (bridge_hreadyout),

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
        .PRDATA3   (32'd0),
        .PREADY0   (timer_pready),
        .PREADY1   (counter_pready),
        .PREADY2   (uart_pready),
        .PREADY3   (1'b1)
    );

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

endmodule
