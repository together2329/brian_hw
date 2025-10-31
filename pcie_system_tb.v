`timescale 1ns/1ps

module pcie_system_tb;

    // Clock and Reset
    reg clk;
    reg rst_n;

    // AXI Write Channel (Write Generator → Receiver)
    wire [63:0] axi_awuser;
    wire [6:0]  axi_awid;
    wire [63:0] axi_awaddr;
    wire [7:0]  axi_awlen;
    wire [2:0]  axi_awsize;
    wire [1:0]  axi_awburst;
    wire        axi_awlock;
    wire [3:0]  axi_awcache;
    wire [2:0]  axi_awprot;
    wire        axi_awvalid;
    wire        axi_awready;

    wire [15:0]  axi_wuser;
    wire [255:0] axi_wdata;
    wire [31:0]  axi_wstrb;
    wire         axi_wlast;
    wire         axi_wvalid;
    wire         axi_wready;

    wire [6:0]  axi_bid;
    wire [1:0]  axi_bresp;
    wire        axi_bvalid;
    wire        axi_bready;

    // AXI Read Channel (Read Generator ← AXI to SRAM)
    wire [6:0]   axi_arid;
    wire [31:0]  axi_araddr;
    wire [7:0]   axi_arlen;
    wire [2:0]   axi_arsize;
    wire [1:0]   axi_arburst;
    wire         axi_arvalid;
    wire         axi_arready;

    wire [6:0]   axi_rid;
    wire [255:0] axi_rdata;
    wire [1:0]   axi_rresp;
    wire         axi_rlast;
    wire         axi_rvalid;
    wire         axi_rready;

    // SRAM Write Interface
    wire         sram_wen;
    wire [9:0]   sram_waddr;
    wire [255:0] sram_wdata;

    // SRAM Read Interface
    wire         sram_ren;
    wire [9:0]   sram_raddr;
    wire [255:0] sram_rdata;

    // Message info
    wire [127:0] msg_header;
    wire         msg_valid;
    wire [11:0]  msg_length;

    // Module instantiations

    // 1. AXI Write Generator (with internal initial block that calls task)
    axi_write_gen wr_gen (
        .i_clk(clk),
        .i_reset_n(rst_n),
        .O_AWUSER(axi_awuser),
        .O_AWID(axi_awid),
        .O_AWADDR(axi_awaddr),
        .O_AWLEN(axi_awlen),
        .O_AWSIZE(axi_awsize),
        .O_AWBURST(axi_awburst),
        .O_AWLOCK(axi_awlock),
        .O_AWCACHE(axi_awcache),
        .O_AWPROT(axi_awprot),
        .O_AWVALID(axi_awvalid),
        .I_AWREADY(axi_awready),
        .O_WUSER(axi_wuser),
        .O_WDATA(axi_wdata),
        .O_WSTRB(axi_wstrb),
        .O_WLAST(axi_wlast),
        .O_WVALID(axi_wvalid),
        .I_WREADY(axi_wready),
        .I_BID(axi_bid),
        .I_BRESP(axi_bresp),
        .I_BVALID(axi_bvalid),
        .O_BREADY(axi_bready)
    );

    // 2. AXI Read Generator (with internal initial block that calls task)
    axi_read_gen rd_gen (
        .i_clk(clk),
        .i_reset_n(rst_n),
        .arid(axi_arid),
        .araddr(axi_araddr),
        .arlen(axi_arlen),
        .arsize(axi_arsize),
        .arburst(axi_arburst),
        .arvalid(axi_arvalid),
        .arready(axi_arready),
        .rid(axi_rid),
        .rdata(axi_rdata),
        .rresp(axi_rresp),
        .rlast(axi_rlast),
        .rvalid(axi_rvalid),
        .rready(axi_rready)
    );

    // 3. PCIe Message Receiver
    pcie_msg_receiver receiver (
        .clk(clk),
        .rst_n(rst_n),
        .axi_awvalid(axi_awvalid),
        .axi_awaddr(axi_awaddr),
        .axi_awlen({4'h0, axi_awlen}),  // Extend to 12 bits
        .axi_awsize(axi_awsize),
        .axi_awburst(axi_awburst),
        .axi_awready(axi_awready),
        .axi_wvalid(axi_wvalid),
        .axi_wdata(axi_wdata),
        .axi_wstrb(axi_wstrb),
        .axi_wlast(axi_wlast),
        .axi_wready(axi_wready),
        .axi_bvalid(axi_bvalid),
        .axi_bresp(axi_bresp),
        .axi_bready(axi_bready),
        .sram_wen(sram_wen),
        .sram_waddr(sram_waddr),
        .sram_wdata(sram_wdata),
        .msg_header(msg_header),
        .msg_valid(msg_valid),
        .msg_length(msg_length)
    );

    // 4. SRAM
    sram #(
        .DATA_WIDTH(256),
        .ADDR_WIDTH(10),
        .DEPTH(1024)
    ) sram_inst (
        .clk(clk),
        .wen(sram_wen),
        .waddr(sram_waddr),
        .wdata(sram_wdata),
        .ren(sram_ren),
        .raddr(sram_raddr),
        .rdata(sram_rdata)
    );

    // 5. PCIe AXI to SRAM (Read)
    pcie_axi_to_sram axi_sram_reader (
        .clk(clk),
        .rst_n(rst_n),
        .axi_arvalid(axi_arvalid),
        .axi_araddr({32'h0, axi_araddr}),  // Extend to 64 bits
        .axi_arlen({4'h0, axi_arlen}),     // Extend to 12 bits
        .axi_arsize(axi_arsize),
        .axi_arburst(axi_arburst),
        .axi_arready(axi_arready),
        .axi_rvalid(axi_rvalid),
        .axi_rdata(axi_rdata),
        .axi_rresp(axi_rresp),
        .axi_rlast(axi_rlast),
        .axi_rready(axi_rready),
        .sram_ren(sram_ren),
        .sram_raddr(sram_raddr),
        .sram_rdata(sram_rdata)
    );

    // Assign unused signals
    assign axi_bid = 7'h0;
    assign axi_rid = 7'h0;

    // Clock generation (100MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset and test control
    initial begin
        $display("\n[%0t] [TB] ========================================", $time);
        $display("[%0t] [TB] PCIe System Test Started", $time);
        $display("[%0t] [TB] ========================================\n", $time);

        // Initialize
        rst_n = 0;

        // Reset
        #100;
        rst_n = 1;
        $display("[%0t] [TB] Reset released", $time);
        $display("[%0t] [TB] Modules will now execute their internal tasks\n", $time);

        // All tests are now run by the modules' internal initial blocks
        // axi_write_gen will write data
        // axi_read_gen will read and verify data
    end

    // Timeout
    initial begin
        #10000;
        $display("\n[%0t] [TB] ========================================", $time);
        $display("[%0t] [TB] Simulation timeout - ending", $time);
        $display("[%0t] [TB] ========================================\n", $time);
        $finish;
    end

    // Waveform dump
    initial begin
        $dumpfile("pcie_system.vcd");
        $dumpvars(0, pcie_system_tb);
    end

    // Monitor message reception
    always @(posedge clk) begin
        if (msg_valid) begin
            $display("\n[%0t] [TB] *** MESSAGE RECEIVED ***", $time);
            $display("[%0t] [TB]   Header: 0x%h", $time, msg_header);
            $display("[%0t] [TB]   Length: %0d beats\n", $time, msg_length);
        end
    end

endmodule
