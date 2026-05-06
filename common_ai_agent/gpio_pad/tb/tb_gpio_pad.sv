// ============================================================================
// tb_gpio_pad.sv — SystemVerilog testbench for gpio_pad
// ============================================================================
`timescale 1ns/1ps
`include "tc_gpio_pad.sv"

module tb_gpio_pad;
    parameter CLK_PERIOD = 10;  // 100 MHz

    // DUT signals
    logic        pclk;
    logic        presetn;
    logic [11:0] paddr;
    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [31:0] pwdata;
    logic [3:0]  pstrb;
    logic [31:0] prdata;
    logic        pready;
    logic        pslverr;
    logic [31:0] gpio_in;
    logic [31:0] gpio_out;
    logic [31:0] gpio_oe;
    logic        gpio_irq;

    // DUT instance
    gpio_pad dut (
        .pclk(pclk),
        .presetn(presetn),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .pstrb(pstrb),
        .prdata(prdata),
        .pready(pready),
        .pslverr(pslverr),
        .gpio_in(gpio_in),
        .gpio_out(gpio_out),
        .gpio_oe(gpio_oe),
        .gpio_irq(gpio_irq)
    );

    // Clock generation
    initial pclk = 0;
    always #(CLK_PERIOD/2) pclk = ~pclk;

    // Waveform dump
    initial begin
        $dumpfile("sim/gpio_pad_wave.vcd");
        $dumpvars(0, tb_gpio_pad);
    end

    // Test sequence
    integer pass_cnt, fail_cnt;
    initial begin
        pass_cnt = 0;
        fail_cnt = 0;

        tc_sc1_basic_out();
        tc_sc3_readback();
        tc_sc5_reset_defaults();
        tc_sc7_mask_blocks();
        tc_sc9_output_no_irq();

        $display("Result: %0d/%0d tests passed", pass_cnt, pass_cnt + fail_cnt);
        if (fail_cnt == 0) begin
            $display("0 errors, 0 warnings");
        end
        $finish;
    end
endmodule
