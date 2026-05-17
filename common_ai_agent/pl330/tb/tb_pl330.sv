`timescale 1ns/1ps
module tb_pl330;
  localparam int MEM_WORDS = 256;

  logic pclk = 1'b0;
  logic presetn;
  logic psel;
  logic penable;
  logic pwrite;
  logic [7:0]  paddr;
  logic [31:0] pwdata;
  logic [31:0] prdata;
  logic pready;
  logic pslverr;
  logic dbg_we;
  logic [$clog2(MEM_WORDS)-1:0] dbg_addr;
  logic [31:0] dbg_wdata;
  logic [31:0] dbg_rdata;
  logic irq;
  logic busy_o;
  logic done_o;
  integer i;
  integer errors;

  always #5 pclk = ~pclk;

  pl330 #(.MEM_WORDS(MEM_WORDS)) dut (
    .pclk(pclk), .presetn(presetn), .psel(psel), .penable(penable),
    .pwrite(pwrite), .paddr(paddr), .pwdata(pwdata), .prdata(prdata),
    .pready(pready), .pslverr(pslverr), .dbg_we(dbg_we),
    .dbg_addr(dbg_addr), .dbg_wdata(dbg_wdata), .dbg_rdata(dbg_rdata),
    .irq(irq), .busy_o(busy_o), .done_o(done_o)
  );

  task automatic apb_write(input [7:0] addr, input [31:0] data);
    begin
      @(posedge pclk);
      paddr <= addr;
      pwdata <= data;
      pwrite <= 1'b1;
      psel <= 1'b1;
      penable <= 1'b0;
      @(posedge pclk);
      penable <= 1'b1;
      @(posedge pclk);
      psel <= 1'b0;
      penable <= 1'b0;
      pwrite <= 1'b0;
    end
  endtask

  task automatic dbg_write_word(input integer addr, input [31:0] data);
    begin
      @(posedge pclk);
      dbg_addr <= addr[$clog2(MEM_WORDS)-1:0];
      dbg_wdata <= data;
      dbg_we <= 1'b1;
      @(posedge pclk);
      dbg_we <= 1'b0;
    end
  endtask

  function automatic [31:0] expected_word(input integer idx);
    expected_word = 32'hA500_0000 + idx;
  endfunction

  initial begin
    $dumpfile("sim/pl330.vcd");
    $dumpvars(0, tb_pl330);
    presetn = 1'b0;
    psel = 1'b0;
    penable = 1'b0;
    pwrite = 1'b0;
    paddr = '0;
    pwdata = '0;
    dbg_we = 1'b0;
    dbg_addr = '0;
    dbg_wdata = '0;
    errors = 0;

    repeat (4) @(posedge pclk);
    presetn = 1'b1;

    for (i = 0; i < 4; i = i + 1) begin
      dbg_write_word(i, expected_word(i));
    end

    apb_write(8'h00, 32'd0);
    apb_write(8'h04, 32'd16);
    apb_write(8'h08, 32'd4);
    apb_write(8'h0c, 32'h0000_0003);

    wait (done_o === 1'b1);
    @(posedge pclk);
    if (irq !== 1'b1) begin
      $display("IRQ not asserted on completion");
      errors = errors + 1;
    end

    for (i = 0; i < 4; i = i + 1) begin
      dbg_addr = 16 + i;
      #1;
      if (dbg_rdata !== expected_word(i)) begin
        $display("DMA mismatch index=%0d got=%08x expected=%08x", i, dbg_rdata, expected_word(i));
        errors = errors + 1;
      end
    end

    apb_write(8'h14, 32'h0000_0001);
    if (errors == 0) begin
      $display("PL330_ATLAS_SIM_PASS copied 4 words and raised irq");
    end else begin
      $display("PL330_ATLAS_SIM_FAIL errors=%0d", errors);
      $fatal(1);
    end
    $finish;
  end
endmodule
