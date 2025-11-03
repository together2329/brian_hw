`timescale 1ns/1ps

module tb_pcie_sub_msg;

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
    wire         assembled_valid;
    wire [3:0]   assembled_tag;

    // SFR Debug Registers
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29;

    // SFR Control Register
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15;

    // SFR Interrupt Registers
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0;

    // Queue Write Pointer Register
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0;

    // Queue Initial Address Registers (15 queues)
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14;

    // Interrupt signal
    wire         o_msg_interrupt;

    // ========================================
    // Expected Data Storage (Shared between write_gen and read_gen)
    // ========================================
    // 15 queues x 64 beats x 256 bits
    reg [255:0] expected_queue_data [0:14] [0:63];
    integer random_seed;

    initial begin
        integer i, j;
        // Initialize random seed
        random_seed = 12345;

        // Clear expected data storage
        for (i = 0; i < 15; i = i + 1) begin
            for (j = 0; j < 64; j = j + 1) begin
                expected_queue_data[i][j] = 256'h0;
            end
        end
    end

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
        .msg_length(msg_length),
        .assembled_valid(assembled_valid),
        .assembled_tag(assembled_tag),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31(PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30(PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29(PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15(PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_1),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_2),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_3),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_4),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_5),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_6),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_7),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_8),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_9),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_10),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_11),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_12),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_13),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14(PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_14),
        .o_msg_interrupt(o_msg_interrupt)
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
        $display("[%0t] [TB] PCIe Assembly System Test Started", $time);
        $display("[%0t] [TB] ========================================\n", $time);

        // Initialize interrupt clear register
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0 = 32'h0;

        // Reset sequence: 1 -> 0 -> 1 (as required)
        rst_n = 1;
        #100;
        rst_n = 0;
        $display("[%0t] [TB] Reset asserted", $time);
        #100;
        rst_n = 1;
        $display("[%0t] [TB] Reset released", $time);
        $display("[%0t] [TB] Modules will now execute their internal tasks\n", $time);

        // All tests are now run by the modules' internal initial blocks
        // axi_write_gen will send fragmented messages
        // pcie_msg_receiver will assemble them
        // axi_read_gen will read and verify assembled messages
    end

    // Bad header version test monitoring
    initial begin
        // Wait for reset
        wait(rst_n);

        $display("\n[%0t] [TB] Waiting for bad header version error...", $time);
        wait(PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] == 8'h1);  // bad header version error counter

        $display("\n[%0t] [TB] ========================================", $time);
        $display("[%0t] [TB] *** BAD HEADER VERSION DETECTED ***", $time);
        $display("[%0t] [TB] Error Counter: %0d", $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24]);
        $display("[%0t] [TB] ========================================\n", $time);
    end

    // ========================================
    // Timeout Monitor (Independent Block)
    // Prevents simulation from hanging indefinitely
    // ========================================
    initial begin
        #20000000;  // 20ms timeout (after all tests should complete)
        $display("\n[%0t] [TB] ========================================", $time);
        $display("[%0t] [TB] *** SIMULATION TIMEOUT ***", $time);
        $display("[%0t] [TB] Tests did not complete within 20ms", $time);
        $display("[%0t] [TB] Force ending simulation...", $time);
        $display("[%0t] [TB] ========================================\n", $time);
        $finish;
    end

    // Waveform dump
    initial begin
        $dumpfile("pcie_system.vcd");
        $dumpvars(0, tb_pcie_sub_msg);
    end

    // Monitor message reception
    always @(posedge clk) begin
        if (msg_valid) begin
            $display("\n[%0t] [TB] *** FRAGMENT RECEIVED ***", $time);
            $display("[%0t] [TB]   Header: 0x%h", $time, msg_header);
            $display("[%0t] [TB]   Length: %0d beats\n", $time, msg_length);
        end

        if (assembled_valid) begin
            $display("\n[%0t] [TB] *** ASSEMBLY COMPLETE ***", $time);
            $display("[%0t] [TB]   MSG_TAG: 0x%h", $time, assembled_tag);
            $display("[%0t] [TB]   Assembled message written to SRAM\n", $time);
        end
    end

    // Monitor SFR register (display only on change)
    reg [7:0] prev_bad_hdr_count;
    initial prev_bad_hdr_count = 8'h0;

    always @(posedge clk) begin
        if (PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] != prev_bad_hdr_count) begin
            prev_bad_hdr_count <= PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24];
            if (PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] != 8'h0) begin
                $display("[%0t] [TB] SFR Debug Register [31:24] = %0d (Bad Header Version Count)",
                         $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24]);
            end
        end
    end

endmodule
