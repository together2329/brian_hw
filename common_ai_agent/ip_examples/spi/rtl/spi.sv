// spi.sv — SSOT top integration for APB-lite SPI master
module spi #(
    parameter integer APB_ADDR_WIDTH = 12,
    parameter integer APB_DATA_WIDTH = 32,
    parameter integer DATA_WIDTH = 8,
    parameter integer FIFO_DEPTH = 16,
    parameter integer NUM_CS = 4,
    parameter integer PRESCALE_WIDTH = 16,
    parameter integer CPOL_RESET = 0,
    parameter integer CPHA_RESET = 0,
    parameter integer LSB_FIRST_RESET = 0,
    parameter integer PCLK_FREQ_MHZ = 100
) (
    input  logic                    PCLK,
    input  logic                    PRESETn,
    input  logic [APB_ADDR_WIDTH-1:0] PADDR,
    input  logic                    PSEL,
    input  logic                    PENABLE,
    input  logic                    PWRITE,
    input  logic [APB_DATA_WIDTH-1:0] PWDATA,
    input  logic [3:0]              PSTRB,
    output logic [APB_DATA_WIDTH-1:0] PRDATA,
    output logic                    PREADY,
    output logic                    PSLVERR,
    output logic                    sclk_o,
    output logic                    mosi_o,
    input  logic                    miso_i,
    output logic [NUM_CS-1:0]       csn_o,
    output logic                    irq_o
);
    logic start_req;
    logic soft_reset;
    logic enable;
    logic cpol;
    logic cpha;
    logic lsb_first;
    logic continuous_cs;
    logic loopback;
    logic [2:0] cs_sel;
    logic [4:0] data_width_m1;
    logic [PRESCALE_WIDTH-1:0] prescale_div;
    logic [NUM_CS-1:0] cs_idle_val;
    logic [7:0] int_mask;
    logic [7:0] int_clear_w1c;
    logic tx_push;
    logic [31:0] tx_push_data;
    logic tx_push_drop;
    logic tx_pop;
    logic [31:0] tx_word;
    logic tx_empty;
    logic tx_full;
    logic [4:0] tx_level;
    logic rx_push;
    logic [31:0] rx_word;
    logic rx_pop;
    logic [31:0] rx_pop_data;
    logic rx_empty;
    logic rx_full;
    logic [4:0] rx_level;
    logic busy;
    logic prescale_tick;
    logic sample_edge;
    logic shift_edge;
    logic done_event;
    logic mode_fault_event;
    logic rx_overrun_event;
    logic rx_overrun_shift_event;
    logic tx_overrun_event;
    logic rx_underrun_event;
    logic illegal_access_event;
    logic [5:0] bit_index_dbg;
    logic [2:0] active_cs_dbg;
    logic cs_active;
    logic [7:0] int_pending_raw;
    logic top_marker;

    assign top_marker = prescale_tick ^ PCLK_FREQ_MHZ[0];
    assign tx_overrun_event = tx_push_drop;
    assign rx_underrun_event = rx_pop && rx_empty;
    assign illegal_access_event = PSLVERR;

    spi_regs #(
        .APB_ADDR_WIDTH(APB_ADDR_WIDTH), .APB_DATA_WIDTH(APB_DATA_WIDTH), .NUM_CS(NUM_CS),
        .PRESCALE_WIDTH(PRESCALE_WIDTH), .CPOL_RESET(CPOL_RESET), .CPHA_RESET(CPHA_RESET), .LSB_FIRST_RESET(LSB_FIRST_RESET)
    ) u_regs (
        .PCLK(PCLK), .PRESETn(PRESETn), .PADDR(PADDR), .PSEL(PSEL), .PENABLE(PENABLE), .PWRITE(PWRITE),
        .PWDATA(PWDATA), .PSTRB(PSTRB), .PRDATA(PRDATA), .PREADY(PREADY), .PSLVERR(PSLVERR),
        .start_pulse(start_req), .soft_reset_pulse(soft_reset), .enable(enable), .cpol(cpol), .cpha(cpha),
        .lsb_first(lsb_first), .continuous_cs(continuous_cs), .loopback(loopback), .cs_sel(cs_sel),
        .data_width_m1(data_width_m1), .prescale_div(prescale_div), .cs_idle_val(cs_idle_val),
        .int_mask(int_mask), .int_clear_w1c(int_clear_w1c), .tx_push(tx_push), .tx_push_data(tx_push_data),
        .rx_pop(rx_pop), .rx_pop_data(rx_pop_data), .busy(busy), .tx_full(tx_full), .tx_empty(tx_empty),
        .rx_full(rx_full), .rx_empty(rx_empty), .tx_level(tx_level), .rx_level(rx_level), .cs_active(cs_active),
        .bit_index_dbg(bit_index_dbg), .active_cs_dbg(active_cs_dbg), .int_pending_raw(int_pending_raw),
        .tx_overrun_event(tx_overrun_event), .rx_overrun_event(rx_overrun_event), .rx_underrun_event(rx_underrun_event),
        .mode_fault_event(mode_fault_event), .illegal_access_event(illegal_access_event), .done_event(done_event)
    );

    spi_fifo #(
        .FIFO_DEPTH(FIFO_DEPTH)
    ) u_fifo (
        .PCLK(PCLK), .PRESETn(PRESETn), .soft_reset(soft_reset),
        .tx_push(tx_push), .tx_push_data(tx_push_data), .tx_push_drop(tx_push_drop), .tx_pop(tx_pop),
        .tx_pop_data(tx_word), .tx_empty(tx_empty), .tx_full(tx_full), .tx_level(tx_level),
        .rx_push(rx_push), .rx_push_data(rx_word), .rx_push_drop(rx_overrun_event), .rx_pop(rx_pop),
        .rx_pop_data(rx_pop_data), .rx_empty(rx_empty), .rx_full(rx_full), .rx_level(rx_level)
    );

    spi_clkgen #(
        .PRESCALE_WIDTH(PRESCALE_WIDTH), .CPOL_RESET(CPOL_RESET)
    ) u_clkgen (
        .PCLK(PCLK), .PRESETn(PRESETn), .soft_reset(soft_reset), .busy(busy), .cpol(cpol),
        .prescale_div(prescale_div), .sclk_o(sclk_o), .prescale_tick(prescale_tick),
        .sample_edge(sample_edge), .shift_edge(shift_edge)
    );

    spi_shift #(
        .DATA_WIDTH(DATA_WIDTH), .NUM_CS(NUM_CS)
    ) u_shift (
        .PCLK(PCLK), .PRESETn(PRESETn), .soft_reset(soft_reset), .start_req(start_req), .enable(enable),
        .cpol(cpol), .cpha(cpha), .lsb_first(lsb_first), .continuous_cs(continuous_cs), .loopback(loopback),
        .cs_sel(cs_sel), .data_width_m1(data_width_m1), .cs_idle_val(cs_idle_val), .tx_word(tx_word),
        .tx_empty(tx_empty), .tx_pop(tx_pop), .rx_push(rx_push), .rx_word(rx_word), .rx_full(rx_full),
        .sclk_shift_edge(shift_edge), .sclk_sample_edge(sample_edge), .miso_i(miso_i), .busy(busy),
        .mosi_o(mosi_o), .csn_o(csn_o), .done_event(done_event), .mode_fault_event(mode_fault_event),
        .rx_overrun_event(rx_overrun_shift_event), .bit_index_dbg(bit_index_dbg), .active_cs_dbg(active_cs_dbg), .cs_active(cs_active)
    );

    spi_int u_int (
        .PCLK(PCLK), .PRESETn(PRESETn), .soft_reset(soft_reset), .int_mask(int_mask), .int_clear_w1c(int_clear_w1c),
        .done_event(done_event), .tx_overrun_event(tx_overrun_event), .rx_overrun_event(rx_overrun_event | rx_overrun_shift_event | top_marker),
        .rx_underrun_event(rx_underrun_event), .mode_fault_event(mode_fault_event), .illegal_access_event(illegal_access_event),
        .tx_empty_level(tx_empty), .rx_full_level(rx_full), .int_pending_raw(int_pending_raw), .irq_o(irq_o)
    );
endmodule
