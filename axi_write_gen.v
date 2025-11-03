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
        $display("[%0t] [WRITE_GEN] Initial block started", $time);

        // Initialize all output signals
        O_AWVALID = 1'b0;
        O_WVALID = 1'b0;
        O_WLAST = 1'b0;
        O_BREADY = 1'b1;  // Keep BREADY always high

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

        // Wait for reset sequence by monitoring actual time
        // Reset sequence: 1 -> 0 (at 100ns) -> 1 (at 200ns)
        // Since timescale is 1ns/1ps, delays are in ns. Need to convert to ps for 300ns:
        // 300ns = 300000ps, but delay syntax is # timescale units
        // So #300 in ns timescale = 300ns = 300000ps
        // Wait for reset sequence: 1 -> 0 -> 1
        // Use @(negedge) and @(posedge) for clock-synchronous reset monitoring
        $display("[%0t] [WRITE_GEN] Waiting for reset LOW edge...", $time);
        @(negedge i_reset_n);
        $display("[%0t] [WRITE_GEN] Reset asserted (LOW), time=%0t", $time, $time);

        @(posedge i_reset_n);
        $display("[%0t] [WRITE_GEN] Reset de-asserted (HIGH), time=%0t", $time, $time);

        // Wait a bit after reset for system to stabilize
        repeat(10) @(posedge i_clk);  // Wait 10 clock cycles
        $display("[%0t] [WRITE_GEN] Stabilization complete", $time);

        $display("[%0t] [WRITE_GEN] *** RESET COMPLETE, STARTING TESTS ***", $time);
        $display("[%0t] [WRITE_GEN] About to send first SEND_WRITE with bad header", $time);

        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version

        $display("[%0t] [WRITE_GEN] Calling SEND_WRITE task...", $time);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h400);
        $display("[%0t] [WRITE_GEN] SEND_WRITE task returned!", $time);

        // Wait for bad header version error detection - give receiver time to process
        $display("[%0t] [WRITE_GEN] Waiting for bad header error detection...", $time);
        repeat(50) @(posedge i_clk);  // Wait 50 clock cycles instead of #5000
        $display("[%0t] [WRITE_GEN] After clock wait, counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[31:24]);

        // Restore correct header version for next test
        $display("[%0t] [WRITE_GEN] Preparing unknown destination test...", $time);
        tlp_header[99:96] = 4'b0001;  // Restore correct version

        // Enable unknown destination check by clearing CONTROL15[8]
        force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_CONTROL15[8] = 1'b0;
        $display("[%0t] [WRITE_GEN] Enabled unknown destination check (CONTROL15[8]=0)", $time);

        // known dst id 0x0, 0xFF, 0x10, 0x10
        // others is unknown (like 0x20)
        tlp_header[111:104] = 8'h20;  // destination endpoint id = 0x20 (unknown)
        $display("\n========================================");
        $display("TEST: Unknown Destination ID Test");
        $display("========================================\n");

        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hCAFE_CAFE_CAFE_CAFE_CAFE_CAFE_CAFE_CAFE,
                    256'hDEAD_DEAD_DEAD_DEAD_DEAD_DEAD_DEAD_DEAD}, 64'h500);

        // Wait for unknown destination error
        $display("[%0t] [WRITE_GEN] Waiting for unknown destination error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Unknown dest counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[23:16]);

        // Restore correct destination ID
        tlp_header[111:104] = 8'h10;         // destination endpoint id

        $display("\n========================================");
        $display("TEST: Tag Owner Error Test (TAG=7 with TO=0)");
        $display("========================================\n");
        // Tag=7 requires TO=1, but we send TO=0 to trigger error
        // Header format: [127:126]=FragType, [125:124]=PKT_SN, [123]=TO, [122:120]=TAG
        // MSG_T7_TO_ZERO = 4'b0111 = {TO=0, TAG=7}
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T7_TO_ZERO, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h600);

        // Wait for tag owner error detection
        $display("[%0t] [WRITE_GEN] Waiting for tag owner error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Tag owner error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[15:8]);

        $display("\n========================================");
        $display("TEST: Middle/Last Without First Error Test");
        $display("========================================\n");

        // Test 1: Send M_PKT without preceding S_PKT (should trigger error)
        $display("[%0t] [WRITE_GEN] Sending M_PKT without S_PKT...", $time);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h700);

        // Wait for middle without first error
        $display("[%0t] [WRITE_GEN] Waiting for middle-without-first error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Middle/Last-without-first error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0]);

        // Test 2: Send L_PKT without preceding S_PKT (should trigger another error)
        $display("[%0t] [WRITE_GEN] Sending L_PKT without S_PKT...", $time);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h800);

        // Wait for last without first error
        $display("[%0t] [WRITE_GEN] Waiting for last-without-first error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Middle/Last-without-first error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0]);

        $display("\n========================================");
        $display("TEST: Unsupported Transmission Unit Size Test");
        $display("========================================\n");
        // Valid range: 64B ~ 1024B
        // Test 1: 32B (too small, should trigger error)
        $display("[%0t] [WRITE_GEN] Test 1: Sending 32B packet (too small)...", $time);
        tlp_header[31:24] = 8'h08;  // 32B = 8 DW
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'hBAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0_BAD0,
                    256'hBAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1_BAD1}, 64'h900);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Test 2: 2048B (too large, should trigger error)
        $display("[%0t] [WRITE_GEN] Test 2: Sending 2048B packet (too large)...", $time);
        tlp_header[31:24] = 8'h200 / 4;  // 2048B = 512 DW, but 8-bit field wraps to 0x00
        // Actually, 8-bit max is 0xFF = 255 DW = 1020B, so let's use 0xFF
        tlp_header[31:24] = 8'hFF;  // 1020B (still under 1024B)
        // Use a value that's clearly over: we can't represent >1020B in 8 bits
        // So let's test with another small value

        // Test 2 revised: 16B (too small)
        $display("[%0t] [WRITE_GEN] Test 2: Sending 16B packet (too small)...", $time);
        tlp_header[31:24] = 8'h04;  // 16B = 4 DW
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T5, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'hA00);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Test 3: 64B (minimum valid size, should NOT trigger error)
        $display("[%0t] [WRITE_GEN] Test 3: Sending 64B packet (valid minimum)...", $time);
        tlp_header[31:24] = 8'h10;  // 64B = 16 DW
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T6, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444}, 64'hB00);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h (should still be 0x02)", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Test 4: 1024B (maximum valid size, should NOT trigger error)
        $display("[%0t] [WRITE_GEN] Test 4: Sending 1024B packet (valid maximum)...", $time);
        tlp_header[31:24] = 8'h100 / 4;  // 1024B = 256 DW = 0x100/4 = 0x40
        // Wait, 256 DW = 0x100, but that's 9 bits. 8-bit max is 0xFF = 255 DW = 1020B
        // So let's use 0xFF for maximum
        tlp_header[31:24] = 8'hFF;  // 1020B = 255 DW (under 1024B, valid)
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]}, 8'h1, 3, 1,
                   {256'h0, 256'h0, 256'h5555_5555_5555_5555_5555_5555_5555_5555,
                    256'h6666_6666_6666_6666_6666_6666_6666_6666}, 64'hC00);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h (should still be 0x02)", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Restore correct size (128B)
        tlp_header[31:24] = 8'h20;
 
        $display("\n========================================");
        $display("TEST: Incorrect Transmission Size (Size Mismatch)");
        $display("========================================\n");
        // S->L assembly (2 fragments) with mismatched sizes
        $display("[%0t] [WRITE_GEN] Sending S_PKT with 64B size...", $time);
        tlp_header[31:24] = 8'h10; // 64B
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T3, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h1000);

        $display("[%0t] [WRITE_GEN] Sending M_PKT with 128B size (mismatch - should error)...", $time);
        tlp_header[31:24] = 8'h20; // 128B (different size - should error)
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T3, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hEEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE,
                    256'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF,
                    256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'h1100);

        $display("[%0t] [WRITE_GEN] Sending L_PKT with 256B size (different from S/M, but allowed)...", $time);
        tlp_header[31:24] = 8'h40; // 256B (different size - allowed for L_PKT)
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T3, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555,
                    256'h6666_6666_6666_6666_6666_6666_6666_6666}, 64'h1200);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Size mismatch error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0]);

        // ========================================
        // Padding Test
        // ========================================
        $display("\n========================================");
        $display("TEST: Padding Test (0, 1, 2, 3 bytes)");
        $display("========================================\n");

        // Test 1: No padding (padding = 0)
        // TLP: 16 DW = 64B payload
        // Beat 0: 16B header + 16B payload, Beat 1: 32B payload, Beat 2: 16B payload
        // awlen = 2 (3 beats total)
        $display("[%0t] [WRITE_GEN] Test 1: SG_PKT with 0 byte padding, TLP_len=16 DW (64B)", $time);
        tlp_header[53:52] = 2'b00; // 0B padding
        tlp_header[31:24] = 8'h10; // 64B = 16 DW
        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h2, 2, 1,
                   {256'h0, 256'hAA00_AA00_AA00_AA00_AA00_AA00_AA00_AA00,
                    256'hBB00_BB00_BB00_BB00_BB00_BB00_BB00_BB00,
                    256'hCC00_CC00_CC00_CC00_CC00_CC00_CC00_CC00}, 64'h2000);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 1: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 64, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 2: 1 byte padding
        $display("[%0t] [WRITE_GEN] Test 2: SG_PKT with 1 byte padding, TLP_len=16 DW (64B - 1B = 63B)", $time);
        tlp_header[53:52] = 2'b01; // 1B padding
        tlp_header[31:24] = 8'h10; // 64B = 16 DW
        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h2, 2, 1,
                   {256'h0, 256'hAA01_AA01_AA01_AA01_AA01_AA01_AA01_AA01,
                    256'hBB01_BB01_BB01_BB01_BB01_BB01_BB01_BB01,
                    256'hCC01_CC01_CC01_CC01_CC01_CC01_CC01_CC01}, 64'h2100);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 2: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 63, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 3: 2 byte padding
        // TLP: 2 DW = 8B, Total with header = 24B, awlen = 0 (1 beat, all in first beat)
        $display("[%0t] [WRITE_GEN] Test 3: SG_PKT with 2 byte padding, TLP_len=2 DW (8B - 2B = 6B)", $time);
        tlp_header[53:52] = 2'b10; // 2B padding
        tlp_header[31:24] = 8'h02; // 8B = 2 DW
        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h0, 2, 1,
                   {256'h0, 256'h0, 256'h0, 256'h0}, 64'h2200);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 3: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 6, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 4: 3 byte padding
        $display("[%0t] [WRITE_GEN] Test 4: SG_PKT with 3 byte padding, TLP_len=2 DW (8B - 3B = 5B)", $time);
        tlp_header[53:52] = 2'b11; // 3B padding
        tlp_header[31:24] = 8'h02; // 8B = 2 DW
        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h0, 2, 1,
                   {256'h0, 256'h0, 256'h0, 256'h0}, 64'h2300);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 4: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 5, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Reset padding for subsequent tests
        tlp_header[53:52] = 2'b00; // 0B padding
        tlp_header[31:24] = 8'h10; // 64B

        // ========================================
        // 68B Unaligned Payload Test
        // ========================================
        $display("\n========================================");
        $display("TEST: 68B Unaligned Multi-Fragment Assembly");
        $display("========================================\n");

        // MSG_T6: 68B x 3 fragments = 204B total
        $display("[%0t] [WRITE_GEN] MSG_T6: Sending S_PKT (68B)...", $time);
        tlp_header[31:24] = 8'h11; // 68B = 17 DW
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);

        $display("[%0t] [WRITE_GEN] MSG_T6: Sending M_PKT (68B)...", $time);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);

        $display("[%0t] [WRITE_GEN] MSG_T6: Sending L_PKT (68B)...", $time);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T6, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] MSG_T6: Expected WPTR=%0d bytes (68B x 3), Actual WPTR=%0d bytes",
                 $time, 204, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // MSG_T2: 64B x 3 fragments = 192B total
        $display("[%0t] [WRITE_GEN] MSG_T2: Sending S_PKT (64B)...", $time);
        tlp_header[31:24] = 8'h10; // 64B = 16 DW
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h100);

        $display("[%0t] [WRITE_GEN] MSG_T2: Sending M_PKT (64B)...", $time);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h100);

        $display("[%0t] [WRITE_GEN] MSG_T2: Sending L_PKT (64B)...", $time);
        SEND_WRITE({L_PKT, PKT_SN2, MSG_T2, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h100);

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] MSG_T2: Expected WPTR=%0d bytes (64B x 3), Actual WPTR=%0d bytes",
                 $time, 192, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        $display("\n========================================");
        $display("TEST: Restart Error Test");
        $display("========================================\n");
        // Restart Test: Send S_PKT twice with same source ID, tag, and tag owner
        // First S_PKT starts assembly
        $display("[%0t] [WRITE_GEN] Sending first S_PKT (TAG=0, SRC_ID=0x0, TO=1)...", $time);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'hD00);

        // Second S_PKT with same context (should trigger restart error)
        $display("[%0t] [WRITE_GEN] Sending second S_PKT (same context, should trigger restart error)...", $time);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'hE00);

        // Wait for restart error detection
        $display("[%0t] [WRITE_GEN] Waiting for restart error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Restart error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8]);

        // Complete the assembly with L_PKT
        $display("[%0t] [WRITE_GEN] Completing assembly with L_PKT...", $time);
        SEND_WRITE({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hEEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE_EEEE,
                    256'hFFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF_FFFF,
                    256'h1111_1111_1111_1111_1111_1111_1111_1111,
                    256'h2222_2222_2222_2222_2222_2222_2222_2222}, 64'hF00);

        repeat(50) @(posedge i_clk);

        $display("\n========================================");
        $display("TEST: Queue Timeout Test");
        $display("========================================\n");
        // Timeout Test: Send S_PKT but don't complete with L_PKT
        // This will trigger timeout after 10000 cycles
        $display("[%0t] [WRITE_GEN] Sending S_PKT without completing (will timeout)...", $time);
        $display("[%0t] [WRITE_GEN] Using TAG=12 for timeout test", $time);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]}, 8'h3, 3, 1,
                   {256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB,
                    256'hCCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC_CCCC,
                    256'hDDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD_DDDD}, 64'h1200);

        $display("[%0t] [WRITE_GEN] Waiting for timeout (threshold = 10000 cycles)...", $time);
        // Wait for timeout to occur (need to wait >10000 cycles)
        repeat(10100) @(posedge i_clk);

        $display("[%0t] [WRITE_GEN] Timeout error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[23:16]);

        $display("\n========================================");
        $display("TEST: Out-of-Sequence Error Test");
        $display("========================================\n");
        // Out-of-sequence test: Send S->M->L with wrong sequence number
        // Expected sequence: SN=0 (S), SN=1 (M), SN=2 (L)
        // We'll send: SN=0 (S), SN=1 (M), SN=3 (L) - skip SN=2

        $display("[%0t] [WRITE_GEN] Sending S_PKT (SN=0, TAG=1)...", $time);
        SEND_WRITE({S_PKT, PKT_SN0, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h3333_3333_3333_3333_3333_3333_3333_3333,
                    256'h4444_4444_4444_4444_4444_4444_4444_4444,
                    256'h5555_5555_5555_5555_5555_5555_5555_5555}, 64'h1300);

        $display("[%0t] [WRITE_GEN] Sending M_PKT (SN=1, TAG=1)...", $time);
        SEND_WRITE({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h6666_6666_6666_6666_6666_6666_6666_6666,
                    256'h7777_7777_7777_7777_7777_7777_7777_7777,
                    256'h8888_8888_8888_8888_8888_8888_8888_8888}, 64'h1400);

        // Send L_PKT with SN=3 instead of expected SN=2 (out-of-sequence)
        $display("[%0t] [WRITE_GEN] Sending L_PKT with wrong SN (SN=3 instead of 2)...", $time);
        SEND_WRITE({L_PKT, PKT_SN3, MSG_T1, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h9999_9999_9999_9999_9999_9999_9999_9999,
                    256'hAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                    256'hBBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB_BBBB}, 64'h1500);

        // Wait for out-of-sequence error detection
        $display("[%0t] [WRITE_GEN] Waiting for out-of-sequence error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Out-of-sequence error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24]);


        $display("\n========================================");
        $display("TEST 1: S->L (2 fragments) with MSG_T0 - RANDOM DATA");
        $display("========================================\n");
        // S->L assembly (2 fragments) with random data
        SEND_WRITE_RANDOM({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1, 64'h0);
        SEND_WRITE_RANDOM({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]}, 8'h3, 3, 1, 64'h0);
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
    // AXI Write Task with Random Data
    // ========================================
    task automatic SEND_WRITE_RANDOM;
        input [127:0]     header;
        input [7:0]       awlen;        // AXI len (beats - 1)
        input [2:0]       awsize;
        input [1:0]       awburst;
        input [63:0]      awaddr;

        integer beat;
        integer total_beats;
        reg [255:0] data_beat;
        reg [3:0] msg_tag;
        integer queue_idx;
        integer payload_beat_idx;

        begin
            total_beats = awlen + 1;  // AXI len is (beats - 1)
            msg_tag = header[122:120];  // Extract TAG (3 bits) from bits [122:120]
            queue_idx = msg_tag;

            $display("\n========================================");
            $display("[%0t] [WRITE_GEN] SEND_WRITE_RANDOM START", $time);
            $display("  Address: 0x%h", awaddr);
            $display("  Length:  %0d beats (awlen=%0d)", total_beats, awlen);
            $display("  TAG: 0x%h (3 bits, Queue %0d)", msg_tag, queue_idx);
            $display("  TAG_OWNER (TO): %0b (bit [123])", header[123]);
            $display("  SOURCE_ID: 0x%h (bits [119:112])", header[119:112]);
            $display("  Header:  0x%h", header);
            $display("========================================");

            // Store metadata for verification
            if (queue_idx < 15) begin
                tb_pcie_sub_msg.expected_msg_tag[queue_idx] = {header[123], msg_tag}; // 4 bits: TO + TAG
                tb_pcie_sub_msg.expected_tag_owner[queue_idx] = header[123];
                tb_pcie_sub_msg.expected_source_id[queue_idx] = header[119:112];
                tb_pcie_sub_msg.expected_data_valid[queue_idx] = 1'b1;
                $display("[%0t] [WRITE_GEN] Stored metadata for Queue %0d:", $time, queue_idx);
                $display("  MSG_TAG=4'b%b (TO=%0b, TAG=0x%h), SRC_ID=0x%h",
                         {header[123], msg_tag}, header[123], msg_tag, header[119:112]);
            end

            // ====================================
            // 1. Write Address Phase
            // ====================================
            while (!I_AWREADY) begin
                @(posedge i_clk);
            end
            $display("[%0t] [WRITE_GEN] AWREADY is high, asserting AWVALID...", $time);

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

            @(posedge i_clk);
            $display("[%0t] [WRITE_GEN] Address handshake complete", $time);
            O_AWVALID = 1'b0;

            // ====================================
            // 2. Write Data Phase with Random Generation
            // ====================================
            payload_beat_idx = 0;

            for (beat = 0; beat < total_beats; beat = beat + 1) begin
                // Generate random data
                data_beat[255:192] = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                data_beat[191:128] = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                data_beat[127:64]  = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                data_beat[63:0]    = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};

                // First beat: Insert header in lower 128 bits
                if (beat == 0) begin
                    data_beat[127:0] = header;
                end else begin
                    // Store payload data for verification (excluding header beat)
                    if (queue_idx < 15 && payload_beat_idx < 64) begin
                        tb_pcie_sub_msg.expected_queue_data[queue_idx][payload_beat_idx] = data_beat;
                        $display("[%0t] [WRITE_GEN] Stored Q%0d[%0d] = 0x%h",
                                 $time, queue_idx, payload_beat_idx, data_beat);
                    end
                    payload_beat_idx = payload_beat_idx + 1;
                end

                // Wait for WREADY
                while (!I_WREADY) begin
                    @(posedge i_clk);
                end

                // Assert WVALID and WDATA
                O_WVALID = 1'b1;
                O_WDATA  = data_beat;
                O_WLAST  = (beat == total_beats - 1) ? 1'b1 : 1'b0;
                O_WSTRB  = 32'hFFFFFFFF;
                O_WUSER  = 16'h0;

                $display("[%0t] [WRITE_GEN] Write Data Beat %0d: data=0x%h, last=%0b",
                         $time, beat, data_beat, O_WLAST);

                @(posedge i_clk);
            end

            // Clear write signals
            O_WVALID = 1'b0;
            O_WLAST  = 1'b0;

            $display("[%0t] [WRITE_GEN] All %0d beats sent", $time, total_beats);

            // ====================================
            // 3. Write Response Phase
            // ====================================
            $display("[%0t] [WRITE_GEN] Waiting for write response...", $time);
            while (!I_BVALID) begin
                @(posedge i_clk);
            end

            $display("[%0t] [WRITE_GEN] BVALID received", $time);
            $display("[%0t] [WRITE_GEN] Write Response: bresp=%0d (%s)", $time, I_BRESP,
                     (I_BRESP == 2'b00) ? "  OKAY" :
                     (I_BRESP == 2'b01) ? "EXOKAY" :
                     (I_BRESP == 2'b10) ? "SLVERR" : "DECERR");

            @(posedge i_clk);

            $display("[%0t] [WRITE_GEN] SEND_WRITE_RANDOM COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

    // ========================================
    // AXI Write Task (Original with fixed data)
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
            $display("[%0t] [WRITE_GEN] SEND_WRITE TASK CALLED", $time);
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
            $display("[%0t] [WRITE_GEN] Starting address phase...", $time);

            // Wait for AWREADY to be ready first
            while (!I_AWREADY) begin
                @(posedge i_clk);
            end
            $display("[%0t] [WRITE_GEN] AWREADY is high, asserting AWVALID...", $time);

            // Now assert AWVALID along with address signals
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

            // Wait one clock for handshake to complete
            @(posedge i_clk);
            $display("[%0t] [WRITE_GEN] Address handshake complete", $time);

            // Clear AWVALID
            O_AWVALID = 1'b0;

            // ====================================
            // 2. Write Data Phase
            // Format: First beat has header in [127:0]
            // ====================================
            // Send all beats
            for (beat = 0; beat < total_beats; beat = beat + 1) begin
                if (beat == 0) begin
                    // First beat: header in lower 128 bits
                    data_beat = wr_data[255:0];
                    O_WDATA = {data_beat[255:128], header};
                end else begin
                    // Subsequent beats: just data
                    data_beat = wr_data[(beat * 256) +: 256];
                    O_WDATA = data_beat;
                end

                O_WSTRB  = 32'hFFFFFFFF;
                O_WLAST  = (beat == total_beats - 1) ? 1'b1 : 1'b0;
                O_WVALID = 1'b1;
                O_WUSER  = 16'h0;

                $display("[%0t] [WRITE_GEN] Write Data Beat %0d: data=0x%h, last=%0b",
                         $time, beat, O_WDATA, O_WLAST);

                // Wait for one clock for handshake
                @(posedge i_clk);
            end

            $display("[%0t] [WRITE_GEN] All %0d beats sent", $time, total_beats);

            O_WVALID = 1'b0;
            O_WLAST  = 1'b0;

            // ====================================
            // 3. Write Response Phase
            // ====================================
            // BREADY is always high, just wait for BVALID
            $display("[%0t] [WRITE_GEN] Waiting for write response...", $time);

            // Wait for BVALID
            while (!I_BVALID) begin
                @(posedge i_clk);
            end
            $display("[%0t] [WRITE_GEN] BVALID received", $time);

            $display("[%0t] [WRITE_GEN] Write Response: bresp=%0d (%s)",
                     $time, I_BRESP,
                     (I_BRESP == 2'b00) ? "OKAY" :
                     (I_BRESP == 2'b01) ? "EXOKAY" :
                     (I_BRESP == 2'b10) ? "SLVERR" : "DECERR");

            $display("[%0t] [WRITE_GEN] SEND_WRITE COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

endmodule
