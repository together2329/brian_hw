module axi_write_gen
(
// Clock
input i_clk,
// Reset
input i_reset_n,

// AXI I/F
// Write Address Channel
output reg [63:0] O_AWUSER,
output reg [6:0]  O_AWID,
output reg [63:0] O_AWADDR,
output reg [7:0]  O_AWLEN,
output reg [2:0]  O_AWSIZE,
output reg [1:0]  O_AWBURST,
output reg        O_AWLOCK,
output reg [3:0]  O_AWCACHE,
output reg [2:0]  O_AWPROT,
output reg        O_AWVALID,
input             I_AWREADY,

// Write Data Channel
output reg [15:0]  O_WUSER,
output reg [255:0] O_WDATA,
output reg [31:0]  O_WSTRB,
output reg         O_WLAST,
output reg         O_WVALID,
input              I_WREADY,

// Write Response Channel
input [6:0]  I_BID,
input [1:0]  I_BRESP,
input        I_BVALID,
output reg   O_BREADY
);

    localparam S_PKT = 2'b10;
    localparam M_PKT = 2'b00;
    localparam L_PKT = 2'b01;
    localparam SG_PKT = 2'b11;

    localparam PKT_SN0 = 2'b00;
    localparam PKT_SN1 = 2'b01;
    localparam PKT_SN2 = 2'b10;
    localparam PKT_SN3 = 2'b11;

    localparam MSG_T0 = 4'b1000;
    localparam MSG_T1 = 4'b1001;
    localparam MSG_T2 = 4'b1010;
    localparam MSG_T3 = 4'b1011;
    localparam MSG_T4 = 4'b1100;
    localparam MSG_T5 = 4'b1101;
    localparam MSG_T6 = 4'b1110;
    localparam MSG_T7 = 4'b1111;
    localparam MSG_T7_TO_ZERO = 4'b0111;

    localparam TO_0   = 1'b0;
    localparam TO_1   = 1'b1;

    reg [127:0] tlp_header;

    initial begin

        tlp_header = 128'h0;

        tlp_header[7:5] = 3'b011;           // fmt input
        tlp_header[4:3] = 2'b10;            // type input
        tlp_header[51:48] = 4'b0000;        // pcie_tag_mctp_vdm_code_input
        tlp_header[63:56] = 8'b01111111;    // msg code input
        tlp_header[87:80] = 8'h1A;          // vendor id input
        tlp_header[95:88] = 8'hB4;          // vendor id input
        tlp_header[99:96] = 4'b0001;        // header version
        tlp_header[111:104] = 8'h0;         // destination endpoint id
        tlp_header[119:112] = 8'h0;         // source endpoint id
        tlp_header[31:24]   = 8'h20;          // 128B, length
        tlp_header[122:120] = 3'b0; // Msg tag
        tlp_header[123]     = 1'b0; // TO
        tlp_header[125:124] = 1'b0; // Pkt Seq #
        tlp_header[126]     = 1'b0; // EOM
        tlp_header[127]     = 1'b0; // SOM

        // Wait for reset sequence: 1 -> 0 -> 1
        wait(i_reset_n);
        wait(!i_reset_n);
        wait(i_reset_n);
        #200;

        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24] == 8'h1);
        // Restore correct header version
        tlp_header[99:96] = 4'b0001;
        #200;

        // known dst id 0x0, 0xFF, 0x10, 0x10
        // others is unknown
        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15[8] = 1'b0;
        tlp_header[111:104] = 8'h20;         // destination endpoint id
        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[23:16] == 8'h1);
        // Restore correct header version
        tlp_header[111:104] = 8'h10;         // destination endpoint id
        #200;

        // Tag Owner Error TO != 1
        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T7_TO_ZERO, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8] == 8'h1);
        #200;

        // Middle or Last without First Test
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] == 8'h1);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0] == 8'h2);

        $display("\n========================================");
        $display("TEST 5: Unsupported Transmission unit Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[31:24] = 8'h8;  // 32B
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0] == 8'h1);
        // Restore correct header version
        tlp_header[31:24] = 8'h20;
        #200;
 
        $display("\n========================================");
        $display("TEST incorrect transmission size
        $display("========================================\n");
        // S->L assembly (2 fragments)
        tlp_header[31:24] = 8'h10; // 64B
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h0);
        tlp_header[31:24] = 8'h20; // 128B
        SEND_WRITE({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hEEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE,
                    256'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF,
                    256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'h0);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0] == 8'h1);
        #200;

        // Restart Test
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h0);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h0);
        SEND_WRITE({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hEEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE,
                    256'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF,
                    256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'h0);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8] == 8'h1);
        #200;

        // Timeout Test
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h0);
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[23:16] == 8'h1);
        #200;
        
        // Out-of-seq test
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);
        SEND_WRITE({L_PKT, PKT_SN3, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);
        #200;
    
        wait(tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24] == 8'h1);

        // Padding Test
        tlp_header[53:52] = 2'b10 // 2B padding
        tlp_header[31:24] = 8'h2; // 8B
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        tlp_header[53:52] = 2'b0 // 2B padding
        tlp_header[31:24] = 8'h10; // 64BB

        // Multi Packet 64B, 68B (unaligned)
        tlp_header[31:24] = 8'h11; // 68B
        // S->M->L assembly (3 fragments)
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);

        tlp_header[31:24] = 8'h10; // 64B
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);

        tlp_header[31:24] = 8'h11; // 68B
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);

        tlp_header[31:24] = 8'h10; // 64B
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);
        #200;


        $display("\n========================================");
        $display("TEST 1: S->L (2 fragments) with MSG_T0");
        $display("========================================\n");
        // S->L assembly (2 fragments)
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h0);
        SEND_WRITE({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hEEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE,
                    256'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF,
                    256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'h0);
        #200;

        $display("\n========================================");
        $display("TEST 2: S->M->L (3 fragments) with MSG_T1");
        $display("========================================\n");
        // S->M->L assembly (3 fragments)
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);
        #200;

        $display("\n========================================");
        $display("TEST 3: S->M->M->L (4 fragments) with MSG_T2");
        $display("========================================\n");
        // S->M->M->L assembly (4 fragments)
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hDEAD_BEEF_DEAD_BEEF_DEAD_BEEF_DEAD_BEEF,
                    256'hCAFE_BABE_CAFE_BABE_CAFE_BABE_CAFE_BABE}, 64'h200);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T2, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'h1234_5678_1234_5678_1234_5678_1234_5678,
                    256'hABCD_EF01_ABCD_EF01_ABCD_EF01_ABCD_EF01}, 64'h200);
        SEND_WRITE({M_PKT, PKT_SN2, MSG_T2, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hFEDC_BA98_FEDC_BA98_FEDC_BA98_FEDC_BA98,
                    256'h7654_3210_7654_3210_7654_3210_7654_3210}, 64'h200);
        SEND_WRITE({L_PKT, PKT_SN3, MSG_T2, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'h1111_2222_3333_4444_5555_6666_7777_8888,
                    256'h9999_AAAA_BBBB_CCCC_DDDD_EEEE_FFFF_0000}, 64'h200);
        #200;

        $display("\n========================================");
        $display("TEST 4: Single packet (SG_PKT) with MSG_T3");
        $display("========================================\n");
        // Single packet (no assembly)
        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T3, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'hAAAA_5555_AAAA_5555_AAAA_5555_AAAA_5555,
                    256'h5555_AAAA_5555_AAAA_5555_AAAA_5555_AAAA,
                    256'hFFFF_0000_FFFF_0000_FFFF_0000_FFFF_0000}, 64'h300);
        #200;

        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);

        // Restore correct header version
        tlp_header[99:96] = 4'b0001;
        #200;

/*        // Test Case 1: Single beat
        SEND_WRITE(
            128'hDEADBEEF_CAFEBABE_12345678_ABCDEF01,
            8'd0,       // awlen = 0 (1 beat)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            {256'h0, 256'h0, 256'h0, 256'h0},
            64'h0       // address
        );

        #200;

        // Test Case 2: Multi-beat
        SEND_WRITE(
            128'h1111_2222_3333_4444_5555_6666_7777_8888,
            8'd3,       // awlen = 3 (4 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            {256'h3333_3333_3333_3333_3333_3333_3333_3333,
             256'h2222_2222_2222_2222_2222_2222_2222_2222,
             256'h1111_1111_1111_1111_1111_1111_1111_1111,
             256'h0000_0000_0000_0000_0000_0000_0000_0000},
            64'h10      // address
        );
*/
        #200;
        $display("\n[WRITE_GEN] All writes completed\n");
    end

    // ========================================
    // AXI Write Task
    // ========================================
    task automatic SEND_WRITE;
        input [127:0]     header;
        input [7:0]       awlen;        // AXI len (beats - 1)
        input [2:0]       awsize;
        input [1:0]       awburst;
        input [256*4-1:0] wr_data;
        input [63:0]      awaddr;

        integer beat;
        integer total_beats;
        reg [255:0] data_beat;

        begin
            total_beats = awlen + 1;  // AXI len is (beats - 1)

            $display("\n========================================");
            $display("[%0t] [WRITE_GEN] SEND_WRITE START", $time);
            $display("  Address: 0x%h", awaddr);
            $display("  Length:  %0d beats (awlen=%0d)", total_beats, awlen);
            $display("  Size:    %0d (2^%0d = %0d bytes)", awsize, awsize, 1 << awsize);
            $display("  Burst:   %0d (%s)", awburst,
                     (awburst == 2'b00) ? "FIXED" :
                     (awburst == 2'b01) ? "INCR" : "WRAP");
            $display("  Header:  0x%h", header);
            $display("========================================");

            // ====================================
            // 1. Write Address Phase
            // ====================================
            @(posedge i_clk);
            #1;
            O_AWVALID = 1'b1;
            O_AWADDR  = awaddr;
            O_AWLEN   = awlen;
            O_AWSIZE  = awsize;
            O_AWBURST = awburst;
            O_AWID    = 7'h0;
            O_AWUSER  = 64'h0;
            O_AWLOCK  = 1'b0;
            O_AWCACHE = 4'h0;
            O_AWPROT  = 3'h0;

            // Wait for awready
            //@(posedge i_clk);
            while (!I_AWREADY) begin
                @(posedge i_clk);
            end

            $display("[%0t] [WRITE_GEN] Write Address Sent", $time);

            @(posedge i_clk);
            #1;
            O_AWVALID = 1'b0;

            // ====================================
            // 2. Write Data Phase
            // Format: First beat has header in [127:0]
            // ====================================
            for (beat = 0; beat < total_beats; beat = beat + 1) begin
                @(posedge i_clk);
                #1;

                // First beat: combine header + payload
                if (beat == 0) begin
                    data_beat = wr_data[255:0];
                    O_WDATA = {data_beat[255:128], header};
                end else begin
                    // Subsequent beats: payload only
                    data_beat = wr_data[beat*256 +: 256];
                    O_WDATA = data_beat;
                end

                O_WSTRB  = 32'hFFFFFFFF;  // All bytes valid
                O_WLAST  = (beat == total_beats - 1);
                O_WVALID = 1'b1;
                O_WUSER  = 16'h0;

                // Wait for wready handshake
                while (!I_WREADY) begin
                    @(posedge i_clk);
                end

                $display("[%0t] [WRITE_GEN] Write Data Beat %0d: data=0x%h, last=%0b",
                         $time, beat, O_WDATA, O_WLAST);
            end

            @(posedge i_clk);
            #1;
            O_WVALID = 1'b0;
            O_WLAST  = 1'b0;

            // ====================================
            // 3. Write Response Phase
            // ====================================
            O_BREADY = 1'b1;

            // Wait for bvalid
            @(posedge i_clk);
            while (!I_BVALID) begin
                @(posedge i_clk);
            end

            $display("[%0t] [WRITE_GEN] Write Response: bresp=%0d (%s)",
                     $time, I_BRESP,
                     (I_BRESP == 2'b00) ? "OKAY" :
                     (I_BRESP == 2'b01) ? "EXOKAY" :
                     (I_BRESP == 2'b10) ? "SLVERR" : "DECERR");

            @(posedge i_clk);
            #1;
            O_BREADY = 1'b0;

            $display("[%0t] [WRITE_GEN] SEND_WRITE COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

endmodule
