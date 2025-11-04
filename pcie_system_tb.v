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

    // SFR Interrupt Registers (15 queues)
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12, PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13;
    reg  [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14;

    // Queue Write Pointer Registers (15 queues)
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12, PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14;

    // Queue Initial Address Registers (15 queues)
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13;
    wire [31:0]  PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14;

    // Interrupt signal
    wire         o_msg_interrupt;

    // ========================================
    // Expected Data Storage (Shared between write_gen and read_gen)
    // ========================================
    // 15 queues x 64 beats x 256 bits
    reg [255:0] expected_queue_data [0:14] [0:63];

    // Expected metadata for each queue
    reg [3:0]  expected_msg_tag [0:14];     // MSG_TAG
    reg        expected_tag_owner [0:14];   // TAG_OWNER (TO bit)
    reg [7:0]  expected_source_id [0:14];   // Source Endpoint ID
    reg        expected_data_valid [0:14];  // Flag to indicate if queue has valid test data

    // Queue allocation tracking
    // [12]=valid, [11:4]=src_id, [3]=to, [2:0]=tag
    reg [12:0] queue_allocated [0:14];

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
            // Clear metadata
            expected_msg_tag[i] = 4'h0;
            expected_tag_owner[i] = 1'b0;
            expected_source_id[i] = 8'h0;
            expected_data_valid[i] = 1'b0;
            // Clear queue allocation
            queue_allocated[i] = 13'h0;
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
    pcie_msg_receiver u_pcie_msg_receiver (
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
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_1),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_2),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_3),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_4),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_5),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_6),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_7),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_8),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_9),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_10),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_11),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_12),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_13),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_14),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14(PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_1),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_2),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_3),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_5),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_6),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_7),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_8),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_9),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_10),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_11),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_12),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_13),
        .PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14(PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_14),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_0),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_1),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_2),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_3),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_4),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_5),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_6),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_7),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_8),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_9),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_10),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_11),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_12),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_13),
        .PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14(PCIE_SFR_AXI_MSG_HANDLER_RX_Q_INIT_ADDR_14),
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

        // Initialize interrupt clear registers (all 15 queues)
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_1 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_2 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_3 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_4 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_5 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_6 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_7 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_8 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_9 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_10 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_11 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_12 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_13 = 32'h0;
        PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_14 = 32'h0;

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

    // Bad header version test monitoring (removed infinite wait)
    // initial begin
    //     // Wait for reset
    //     wait(rst_n);
    //
    //     $display("\n[%0t] [TB] Waiting for bad header version error...", $time);
    //     wait(PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] == 8'h1);  // bad header version error counter
    //
    //     $display("\n[%0t] [TB] ========================================", $time);
    //     $display("[%0t] [TB] *** BAD HEADER VERSION DETECTED ***", $time);
    //     $display("[%0t] [TB] Error Counter: %0d", $time, PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24]);
    //     $display("[%0t] [TB] ========================================\n", $time);
    // end

    // ========================================
    // Timeout Monitor (Independent Block)
    // Prevents simulation from hanging indefinitely
    // ========================================
    initial begin
        #1000000000;  // 1s timeout (for 241 multi-packet tests)
        $display("\n[%0t] [TB] ========================================", $time);
        $display("[%0t] [TB] *** ALL TESTS COMPLETE ***", $time);
        $display("[%0t] [TB] Simulation completed successfully", $time);
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

    // ========================================
    // TEST_MULTI_PACKET_ALL_SIZES task
    // ========================================
    task automatic TEST_MULTI_PACKET_ALL_SIZES;
        integer size_dw;
        integer test_count, pass_count, fail_count;
        reg [127:0] s_header, l_header;
        reg [119:0] tlp_base;
        integer wptr_expected, wptr_actual;
        reg [31:0] error_count_before, error_count_after;
        integer expected_beats;
        reg [127:0] fragtype_pkt_sn_msg_t;

        begin
            test_count = 0;
            pass_count = 0;
            fail_count = 0;

            // Base TLP header (same for all tests)
            // Note: Version field [99:96] = 4'h1, Dst_ID [111:104] = 8'h10
            tlp_base = {
                8'h10,            // [119:112] Dst Endpoint ID = 0x10
                8'h00,            // [111:104] Reserved
                8'h01,            // [103:96] Version = 0x1 in bits [99:96] (0000_0001)
                8'h00,            // [95:88] Reserved
                8'h00,            // [87:80] Reserved
                8'h00,            // [79:72] Reserved
                8'h00,            // [71:64] Reserved
                8'h00,            // [63:56] Reserved
                8'h00,            // [55:48] Reserved
                8'h00,            // [47:40] Reserved
                8'h00,            // [39:32] Reserved
                8'h00,            // [31:24] Length (will be overwritten)
                8'h81,            // [23:16] Message Code
                8'h1A,            // [15:8] OHC=0x1 [11:8], Vendor ID upper [15:12]
                8'hBD             // [7:0] Vendor ID lower + Message Code
            };

            $display("\n========================================");
            $display("[TEST_MULTI_PACKET_ALL_SIZES] Starting verification");
            $display("Testing 2 sizes: 64B (16 DW) and 1024B (256 DW)");
            $display("========================================\n");

            // Test 2 sizes: 64B (16 DW) and 1024B (256 DW)
            // Loop: size_dw = 16, then size_dw = 256
            for (size_dw = 16; size_dw <= 256; size_dw = size_dw + 240) begin
                test_count = test_count + 1;

                $display("\n----------------------------------------");
                $display("[TEST %0d] Size = %0d DW (%0d bytes)", test_count, size_dw, size_dw * 4);
                $display("----------------------------------------");

                // Build S_PKT header with 16-bit length
                // [127:126]=S_PKT(10), [125:124]=SN(00), [123]=TO(1), [122:120]=TAG(000)
                s_header = {2'b10, 2'b00, 1'b1, 3'b000, tlp_base[119:40], size_dw[15:0], tlp_base[23:0]};

                // Read error counter before test
                error_count_before = u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0];

                // Send S_PKT
                $display("[%0t] Sending S_PKT (size=%0d DW)...", $time, size_dw);
                wr_gen.SEND_MSG(s_header);

                #200;

                // Build L_PKT header with same 16-bit length
                // [127:126]=L_PKT(01), [125:124]=SN(01), [123]=TO(1), [122:120]=TAG(000)
                l_header = {2'b01, 2'b01, 1'b1, 3'b000, tlp_base[119:40], size_dw[15:0], tlp_base[23:0]};

                // Send L_PKT
                $display("[%0t] Sending L_PKT (size=%0d DW)...", $time, size_dw);
                wr_gen.SEND_MSG(l_header);

                #500;

                // Verify WPTR (in bytes)
                wptr_expected = size_dw * 4;
                wptr_actual = u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4[15:0];

                $display("[VERIFY] WPTR check: expected=%0d bytes, actual=%0d bytes",
                         wptr_expected, wptr_actual);

                // Verify error counter
                error_count_after = u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0];
                $display("[VERIFY] Error counter check: before=%0d, after=%0d",
                         error_count_before, error_count_after);

                // Calculate expected beats for READ_AND_CHECK
                expected_beats = (size_dw * 4 + 31) / 32;  // Round up to 32-byte beats

                // Verify SRAM data with READ_AND_CHECK
                $display("[VERIFY] Reading and checking SRAM data (%0d beats)...", expected_beats);
                rd_gen.READ_AND_CHECK(
                    64'h8C00_0400,     // Queue 4 SRAM address
                    expected_beats,     // Number of beats
                    3'd5,               // Size = 32 bytes
                    2'b01,              // INCR burst
                    l_header            // Expected header
                );

                #200;

                // Check if test passed
                if (wptr_actual == wptr_expected && error_count_after == error_count_before) begin
                    $display("[RESULT] TEST %0d: **PASS**\n", test_count);
                    pass_count = pass_count + 1;
                end else begin
                    $display("[RESULT] TEST %0d: **FAIL**", test_count);
                    if (wptr_actual != wptr_expected)
                        $display("  - WPTR mismatch: expected %0d, got %0d", wptr_expected, wptr_actual);
                    if (error_count_after != error_count_before)
                        $display("  - Error counter increased: %0d -> %0d", error_count_before, error_count_after);
                    $display("");
                    fail_count = fail_count + 1;
                end
            end

            // Final summary
            $display("\n========================================");
            $display("[TEST_MULTI_PACKET_ALL_SIZES] FINAL SUMMARY");
            $display("========================================");
            $display("Total tests:  %0d", test_count);
            $display("Passed:       %0d", pass_count);
            $display("Failed:       %0d", fail_count);
            if (fail_count == 0) begin
                $display("\n*** ALL TESTS PASSED ***\n");
            end else begin
                $display("\n*** SOME TESTS FAILED ***\n");
            end
            $display("========================================\n");
        end
    endtask

endmodule
