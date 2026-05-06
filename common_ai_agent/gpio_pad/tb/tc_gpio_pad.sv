// ============================================================================
// tc_gpio_pad.sv — Test case tasks for gpio_pad (SV Icarus-compatible)
// ============================================================================

// Register address constants
`define ADDR_DIR      12'h000
`define ADDR_OUT      12'h004
`define ADDR_IN       12'h008
`define ADDR_INTEN    12'h00C
`define ADDR_INTSTAT  12'h010
`define ADDR_INTCLEAR 12'h014

// APB write helper — uses global DUT signals
task automatic apb_write(input [11:0] addr, input [31:0] data);
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.paddr   = addr;
    tb_gpio_pad.pwrite  = 1'b1;
    tb_gpio_pad.psel    = 1'b1;
    tb_gpio_pad.penable = 1'b0;
    tb_gpio_pad.pwdata  = data;
    tb_gpio_pad.pstrb   = 4'hF;
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.penable = 1'b1;
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.psel    = 1'b0;
    tb_gpio_pad.penable = 1'b0;
    @(posedge tb_gpio_pad.pclk);
endtask

// APB read helper
task automatic apb_read(input [11:0] addr, output [31:0] rdata);
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.paddr   = addr;
    tb_gpio_pad.pwrite  = 1'b0;
    tb_gpio_pad.psel    = 1'b1;
    tb_gpio_pad.penable = 1'b0;
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.penable = 1'b1;
    @(posedge tb_gpio_pad.pclk);
    rdata = tb_gpio_pad.prdata;
    @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.psel    = 1'b0;
    tb_gpio_pad.penable = 1'b0;
endtask

// Check helper
`define CHECK(name, got, exp) \
    if ((got) === (exp)) begin \
        $display("[PASS] %s: got=0x%08X exp=0x%08X", name, got, exp); \
        tb_gpio_pad.pass_cnt++; \
    end else begin \
        $display("[FAIL] %s: got=0x%08X exp=0x%08X", name, got, exp); \
        tb_gpio_pad.fail_cnt++; \
    end

// Software reset helper
task automatic sw_reset();
    tb_gpio_pad.presetn = 1'b0;
    repeat(5) @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.presetn = 1'b1;
    tb_gpio_pad.psel = 0; tb_gpio_pad.penable = 0; tb_gpio_pad.pwrite = 0;
    tb_gpio_pad.paddr = 0; tb_gpio_pad.pwdata = 0; tb_gpio_pad.pstrb = 0;
    tb_gpio_pad.gpio_in = 0;
    repeat(3) @(posedge tb_gpio_pad.pclk);
endtask

// ============================================================================
// Test cases — use global pass_cnt/fail_cnt (no ref ports)
// ============================================================================

task automatic tc_sc1_basic_out();
    reg [31:0] rd, oe, out_val;
    $display("=== SC1: Direction output + write data ===");
    sw_reset();

    apb_write(`ADDR_DIR, 32'hFFFFFFFF);
    apb_write(`ADDR_OUT, 32'hDEADBEEF);
    repeat(3) @(posedge tb_gpio_pad.pclk);

    oe      = tb_gpio_pad.gpio_oe;
    out_val = tb_gpio_pad.gpio_out;
    `CHECK("SC1 oe", oe, 32'hFFFFFFFF);
    `CHECK("SC1 out", out_val, 32'hDEADBEEF);

    apb_read(`ADDR_DIR, rd);
    `CHECK("SC1 dir_rb", rd, 32'hFFFFFFFF);
    apb_read(`ADDR_OUT, rd);
    `CHECK("SC1 out_rb", rd, 32'hDEADBEEF);
endtask


task automatic tc_sc3_readback();
    reg [31:0] rd;
    $display("=== SC3: APB readback ===");

    apb_write(`ADDR_DIR,   32'hAAAAAAAA);
    apb_write(`ADDR_OUT,   32'h55555555);
    apb_write(`ADDR_INTEN, 32'h0000FFFF);
    repeat(2) @(posedge tb_gpio_pad.pclk);

    apb_read(`ADDR_DIR, rd);
    `CHECK("SC3 dir_rb", rd, 32'hAAAAAAAA);
    apb_read(`ADDR_OUT, rd);
    `CHECK("SC3 out_rb", rd, 32'h55555555);
    apb_read(`ADDR_INTEN, rd);
    `CHECK("SC3 inten_rb", rd, 32'h0000FFFF);
endtask


task automatic tc_sc5_reset_defaults();
    reg [31:0] rd;
    $display("=== SC5: Reset defaults ===");
    sw_reset();

    apb_read(`ADDR_DIR, rd);
    `CHECK("SC5 dir", rd, 32'h00000000);
    apb_read(`ADDR_OUT, rd);
    `CHECK("SC5 out", rd, 32'h00000000);
    apb_read(`ADDR_INTEN, rd);
    `CHECK("SC5 inten", rd, 32'h00000000);
    apb_read(`ADDR_INTSTAT, rd);
    `CHECK("SC5 intstat", rd, 32'h00000000);
    apb_read(`ADDR_INTCLEAR, rd);
    `CHECK("SC5 intclear", rd, 32'h00000000);
    `CHECK("SC5 gpio_oe", tb_gpio_pad.gpio_oe, 32'h00000000);
    `CHECK("SC5 gpio_out", tb_gpio_pad.gpio_out, 32'h00000000);
endtask


task automatic tc_sc7_mask_blocks();
    $display("=== SC7: Interrupt mask blocks ===");

    apb_write(`ADDR_DIR,      32'h00000000);
    apb_write(`ADDR_INTEN,    32'h00000000);
    apb_write(`ADDR_INTCLEAR, 32'hFFFFFFFF);
    repeat(3) @(posedge tb_gpio_pad.pclk);

    tb_gpio_pad.gpio_in = 32'h00000001;
    repeat(2) @(posedge tb_gpio_pad.pclk);
    tb_gpio_pad.gpio_in = 32'h00000000;
    repeat(2) @(posedge tb_gpio_pad.pclk);

    `CHECK("SC7 irq", tb_gpio_pad.gpio_irq, 1'b0);
endtask


task automatic tc_sc9_output_no_irq();
    reg [31:0] intstat;
    $display("=== SC9: Output pin no interrupt ===");

    apb_write(`ADDR_DIR,      32'h00000001);
    apb_write(`ADDR_OUT,      32'h00000000);
    apb_write(`ADDR_INTEN,    32'h00000001);
    apb_write(`ADDR_INTCLEAR, 32'hFFFFFFFF);
    repeat(5) @(posedge tb_gpio_pad.pclk);

    apb_write(`ADDR_OUT, 32'h00000001);
    repeat(3) @(posedge tb_gpio_pad.pclk);
    apb_write(`ADDR_OUT, 32'h00000000);
    repeat(3) @(posedge tb_gpio_pad.pclk);

    `CHECK("SC9 irq", tb_gpio_pad.gpio_irq, 1'b0);
    apb_read(`ADDR_INTSTAT, intstat);
    `CHECK("SC9 intstat", intstat, 32'h00000000);
endtask
