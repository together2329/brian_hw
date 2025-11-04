// Test Selection Defines
// Comment out to disable specific test suites
//`define RUN_ORIGINAL_TESTS      // Original comprehensive tests (errors, assembly, etc.)
`define RUN_MULTI_PACKET_TEST   // Multi-packet size verification test (64B-1024B)

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

    // Queue allocation tracking (shared with testbench)
    // Access via: tb_pcie_sub_msg.queue_allocated[i]
    // Format: [12:12]=valid, [11:4]=src_id, [3]=to, [2:0]=tag

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

`ifdef RUN_ORIGINAL_TESTS
        $display("[%0t] [WRITE_GEN] Running ORIGINAL comprehensive tests", $time);
        $display("[%0t] [WRITE_GEN] About to send first SEND_WRITE with bad header", $time);

        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version

        $display("[%0t] [WRITE_GEN] Calling SEND_MSG task (auto-calculate from header)...", $time);
        SEND_MSG({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});
        $display("[%0t] [WRITE_GEN] SEND_MSG task returned!", $time);

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

        SEND_MSG({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});

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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T7_TO_ZERO, tlp_header[119:0]});

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
        SEND_MSG({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]});

        // Wait for middle without first error
        $display("[%0t] [WRITE_GEN] Waiting for middle-without-first error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Middle/Last-without-first error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_31[7:0]);

        // Test 2: Send L_PKT without preceding S_PKT (should trigger another error)
        $display("[%0t] [WRITE_GEN] Sending L_PKT without S_PKT...", $time);
        SEND_MSG({L_PKT, PKT_SN2, MSG_T1, tlp_header[119:0]});

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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});

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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T5, tlp_header[119:0]});

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Test 3: 64B (minimum valid size, should NOT trigger error)
        $display("[%0t] [WRITE_GEN] Test 3: Sending 64B packet (valid minimum)...", $time);
        tlp_header[31:24] = 8'h10;  // 64B = 16 DW
        SEND_MSG({S_PKT, PKT_SN0, MSG_T6, tlp_header[119:0]});

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] TX unit size error counter = 0x%h (should still be 0x02)", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_30[7:0]);

        // Test 4: 1024B (maximum valid size, should NOT trigger error)
        $display("[%0t] [WRITE_GEN] Test 4: Sending 1024B packet (valid maximum)...", $time);
        tlp_header[31:24] = 8'h100 / 4;  // 1024B = 256 DW = 0x100/4 = 0x40
        // Wait, 256 DW = 0x100, but that's 9 bits. 8-bit max is 0xFF = 255 DW = 1020B
        // So let's use 0xFF for maximum
        tlp_header[31:24] = 8'hFF;  // 1020B = 255 DW (under 1024B, valid)
        SEND_MSG({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]});

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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T3, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] Sending M_PKT with 128B size (mismatch - should error)...", $time);
        tlp_header[31:24] = 8'h20; // 128B (different size - should error)
        SEND_MSG({M_PKT, PKT_SN1, MSG_T3, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] Sending L_PKT with 256B size (different from S/M, but allowed)...", $time);
        tlp_header[31:24] = 8'h40; // 256B (different size - allowed for L_PKT)
        SEND_MSG({L_PKT, PKT_SN2, MSG_T3, tlp_header[119:0]});

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
        SEND_MSG({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 1: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 64, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 2: 1 byte padding
        $display("[%0t] [WRITE_GEN] Test 2: SG_PKT with 1 byte padding, TLP_len=16 DW (64B - 1B = 63B)", $time);
        tlp_header[53:52] = 2'b01; // 1B padding
        tlp_header[31:24] = 8'h10; // 64B = 16 DW
        SEND_MSG({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 2: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 63, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 3: 2 byte padding
        // TLP: 2 DW = 8B, Total with header = 24B, awlen = 0 (1 beat, all in first beat)
        $display("[%0t] [WRITE_GEN] Test 3: SG_PKT with 2 byte padding, TLP_len=2 DW (8B - 2B = 6B)", $time);
        tlp_header[53:52] = 2'b10; // 2B padding
        tlp_header[31:24] = 8'h02; // 8B = 2 DW
        SEND_MSG({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Test 3: Expected WPTR=%0d, Actual WPTR=%0d",
                 $time, 6, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // Test 4: 3 byte padding
        $display("[%0t] [WRITE_GEN] Test 4: SG_PKT with 3 byte padding, TLP_len=2 DW (8B - 3B = 5B)", $time);
        tlp_header[53:52] = 2'b11; // 3B padding
        tlp_header[31:24] = 8'h02; // 8B = 2 DW
        SEND_MSG({SG_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});
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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T6, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] MSG_T6: Sending M_PKT (68B)...", $time);
        SEND_MSG({M_PKT, PKT_SN1, MSG_T6, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] MSG_T6: Sending L_PKT (68B)...", $time);
        SEND_MSG({L_PKT, PKT_SN2, MSG_T6, tlp_header[119:0]});

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] MSG_T6: Expected WPTR=%0d bytes (68B x 3), Actual WPTR=%0d bytes",
                 $time, 204, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        // MSG_T2: 64B x 3 fragments = 192B total
        $display("[%0t] [WRITE_GEN] MSG_T2: Sending S_PKT (64B)...", $time);
        tlp_header[31:24] = 8'h10; // 64B = 16 DW
        SEND_MSG({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] MSG_T2: Sending M_PKT (64B)...", $time);
        SEND_MSG({M_PKT, PKT_SN1, MSG_T2, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] MSG_T2: Sending L_PKT (64B)...", $time);
        SEND_MSG({L_PKT, PKT_SN2, MSG_T2, tlp_header[119:0]});

        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] MSG_T2: Expected WPTR=%0d bytes (64B x 3), Actual WPTR=%0d bytes",
                 $time, 192, tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0);

        $display("\n========================================");
        $display("TEST: Restart Error Test");
        $display("========================================\n");
        // Restart Test: Send S_PKT twice with same source ID, tag, and tag owner
        // First S_PKT starts assembly
        $display("[%0t] [WRITE_GEN] Sending first S_PKT (TAG=0, SRC_ID=0x0, TO=1)...", $time);
        SEND_MSG({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]});

        // Second S_PKT with same context (should trigger restart error)
        $display("[%0t] [WRITE_GEN] Sending second S_PKT (same context, should trigger restart error)...", $time);
        SEND_MSG({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]});

        // Wait for restart error detection
        $display("[%0t] [WRITE_GEN] Waiting for restart error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Restart error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[15:8]);

        // Complete the assembly with L_PKT
        $display("[%0t] [WRITE_GEN] Completing assembly with L_PKT...", $time);
        SEND_MSG({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]});

        repeat(50) @(posedge i_clk);

        $display("\n========================================");
        $display("TEST: Queue Timeout Test");
        $display("========================================\n");
        // Timeout Test: Send S_PKT but don't complete with L_PKT
        // This will trigger timeout after 10000 cycles
        $display("[%0t] [WRITE_GEN] Sending S_PKT without completing (will timeout)...", $time);
        $display("[%0t] [WRITE_GEN] Using TAG=12 for timeout test", $time);
        SEND_MSG({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});

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
        SEND_MSG({S_PKT, PKT_SN0, MSG_T1, tlp_header[119:0]});

        $display("[%0t] [WRITE_GEN] Sending M_PKT (SN=1, TAG=1)...", $time);
        SEND_MSG({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]});

        // Send L_PKT with SN=3 instead of expected SN=2 (out-of-sequence)
        $display("[%0t] [WRITE_GEN] Sending L_PKT with wrong SN (SN=3 instead of 2)...", $time);
        SEND_MSG({L_PKT, PKT_SN3, MSG_T1, tlp_header[119:0]});

        // Wait for out-of-sequence error detection
        $display("[%0t] [WRITE_GEN] Waiting for out-of-sequence error detection...", $time);
        repeat(50) @(posedge i_clk);
        $display("[%0t] [WRITE_GEN] Out-of-sequence error counter = 0x%h", $time,
                 tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[31:24]);


        $display("\n========================================");
        $display("TEST 1: S->L (2 fragments) with MSG_T0 - RANDOM DATA");
        $display("========================================\n");
        // S->L assembly (2 fragments) with random data
        SEND_MSG({S_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]});
        SEND_MSG({L_PKT, PKT_SN1, MSG_T0, tlp_header[119:0]});
        #200;

        $display("\n========================================");
        $display("TEST 2: S->M->L (3 fragments) with MSG_T1");
        $display("========================================\n");
        // S->M->L assembly (3 fragments)
        SEND_MSG({S_PKT, PKT_SN0, MSG_T1, tlp_header[119:0]});
        SEND_MSG({M_PKT, PKT_SN1, MSG_T1, tlp_header[119:0]});
        SEND_MSG({L_PKT, PKT_SN2, MSG_T1, tlp_header[119:0]});
        #200;

        $display("\n========================================");
        $display("TEST 3: S->M->M->L (4 fragments) with MSG_T2");
        $display("========================================\n");
        // S->M->M->L assembly (4 fragments)
        SEND_MSG({S_PKT, PKT_SN0, MSG_T2, tlp_header[119:0]});
        SEND_MSG({M_PKT, PKT_SN1, MSG_T2, tlp_header[119:0]});
        SEND_MSG({M_PKT, PKT_SN2, MSG_T2, tlp_header[119:0]});
        SEND_MSG({L_PKT, PKT_SN3, MSG_T2, tlp_header[119:0]});
        #200;

        $display("\n========================================");
        $display("TEST 4: Single packet (SG_PKT) with MSG_T3");
        $display("========================================\n");
        // Single packet (no assembly)
        SEND_MSG({SG_PKT, PKT_SN0, MSG_T3, tlp_header[119:0]});
        #200;

        $display("\n========================================");
        $display("TEST 5: Bad Header Version Test");
        $display("========================================\n");
        // Send fragment with bad header version (0x2 instead of 0x1)
        // This should increment the bad header version error counter
        tlp_header[99:96] = 4'b0010;  // Bad version
        SEND_MSG({S_PKT, PKT_SN0, MSG_T4, tlp_header[119:0]});

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
        $display("\n[WRITE_GEN] Original tests completed\n");
`endif  // RUN_ORIGINAL_TESTS

`ifdef RUN_MULTI_PACKET_TEST
        $display("\n[%0t] [WRITE_GEN] Running MULTI-PACKET size verification test (64B-1024B)", $time);

        // Call multi-packet test
        TEST_MULTI_PACKET_ALL_SIZES();

        #1000;
        $display("\n[WRITE_GEN] Multi-packet tests completed\n");
`endif  // RUN_MULTI_PACKET_TEST

        $display("\n[WRITE_GEN] *** ALL SELECTED TESTS COMPLETED ***\n");
    end

    // ========================================
    // OHC (Optional Header Content) Size Calculation
    // ========================================
    function automatic [3:0] calc_ohc_size;
        input [3:0] ohc_field;  // header[11:8]
        begin
            calc_ohc_size = 0;

            // OHC-A: bit[8] = 1 → +2DW
            if (ohc_field[0]) calc_ohc_size = calc_ohc_size + 2;

            // OHC-B: bit[9] = 1 → +2DW
            if (ohc_field[1]) calc_ohc_size = calc_ohc_size + 2;

            // OHC-C: bit[10] = 1 → +2DW
            if (ohc_field[2]) calc_ohc_size = calc_ohc_size + 2;

            // OHC-E: bit[11] = 1 → +1DW
            if (ohc_field[3]) calc_ohc_size = calc_ohc_size + 1;
        end
    endfunction

    // ========================================
    // High-Level Message Send (Auto-calculates AXI parameters from header)
    // Now supports OHC (Optional Header Content)
    // OHC data is auto-generated randomly based on header[11:8]
    // ========================================
    task automatic SEND_MSG;
        input [127:0] header;           // 4DW base header

        reg [3:0]   ohc_field;          // OHC field from header[11:8]
        reg [3:0]   ohc_size_dw;        // OHC size in DW (0~7)
        reg [7:0]   payload_length_dw;  // Payload length in DW (from header[31:24])
        reg [7:0]   total_length_dw;    // Total length in DW
        reg [7:0]   awlen;              // AXI awlen (beats - 1)
        reg [2:0]   awsize;             // AXI awsize (fixed: 32 bytes = 2^5)
        reg [1:0]   awburst;            // AXI awburst (fixed: INCR)
        integer     total_bytes;
        integer     axi_beat_bytes;

        begin
            // 1. Extract OHC field from header[11:8]
            ohc_field = header[11:8];

            // 2. Calculate OHC size
            ohc_size_dw = calc_ohc_size(ohc_field);

            // 3. Extract payload length from header[31:24] (Payload only, no header/OHC)
            payload_length_dw = header[31:24];

            // 4. Calculate total bytes for AXI transfer
            // Beat 0 contains: Header(4DW=16B) + OHC + Payload_start
            // Remaining beats: Rest of payload
            // Total = (Header + OHC + Payload) bytes
            total_length_dw = 4 + ohc_size_dw + payload_length_dw;
            total_bytes = total_length_dw * 4;

            // 5. AXI parameters (fixed for PCIe message system)
            awsize = 3'd5;       // 2^5 = 32 bytes per beat
            awburst = 2'b01;     // INCR burst
            axi_beat_bytes = 32; // 2^awsize

            // 6. Calculate awlen (number of beats - 1)
            awlen = ((total_bytes + axi_beat_bytes - 1) / axi_beat_bytes) - 1;

            // 7. Debug output (optional, commented out for clean logs)
            // $display("[%0t] [SEND_MSG] OHC[11:8]=0x%h, OHC_size=%0dDW, Payload=%0dDW, Total=%0dDW (%0dB), Beats=%0d",
            //          ohc_field, ohc_size_dw, payload_length_dw, total_length_dw, total_bytes, awlen + 1);

            // 8. Call the low-level task (OHC will be auto-generated)
            SEND_WRITE_RANDOM(header, awlen, awsize, awburst, 64'h0);
        end
    endtask

    // ========================================
    // AXI Write Task with Random Data (Low-Level)
    // OHC data auto-generated based on header[11:8]
    // ========================================
    task automatic SEND_WRITE_RANDOM;
        input [127:0]     header;            // 4DW base header
        input [7:0]       awlen;             // AXI len (beats - 1)
        input [2:0]       awsize;
        input [1:0]       awburst;
        input [63:0]      awaddr_unused;     // Unused, will use 0x8C00000 + queue offset

        integer beat;
        integer total_beats;
        reg [255:0] data_beat;
        reg [2:0] tag;
        reg to_bit;
        reg [7:0] src_id;
        integer queue_idx;
        integer payload_beat_idx;
        integer i;
        reg [63:0] final_awaddr;

        // OHC-related variables
        reg [3:0] ohc_field;          // OHC field from header[11:8]
        reg [3:0] ohc_size_dw;        // OHC size in DW
        integer ohc_size_bytes;       // OHC size in bytes
        integer header_ohc_bytes;     // Total header + OHC size in bytes
        integer remaining_space;      // Remaining space in beat 0 for payload

        begin
            total_beats = awlen + 1;  // AXI len is (beats - 1)

            // Extract metadata from header
            tag = header[122:120];
            to_bit = header[123];
            src_id = header[119:112];

            // Calculate OHC size
            ohc_field = header[11:8];
            ohc_size_dw = calc_ohc_size(ohc_field);
            ohc_size_bytes = ohc_size_dw * 4;
            header_ohc_bytes = 16 + ohc_size_bytes;  // 4DW header + OHC

            // Find available queue based on tag, to, src_id
            queue_idx = -1;

            // First, check if this context already has a queue
            for (i = 0; i < 15; i = i + 1) begin
                if (tb_pcie_sub_msg.queue_allocated[i][12] &&
                    tb_pcie_sub_msg.queue_allocated[i][11:4] == src_id &&
                    tb_pcie_sub_msg.queue_allocated[i][3] == to_bit &&
                    tb_pcie_sub_msg.queue_allocated[i][2:0] == tag) begin
                    queue_idx = i;
                end
            end

            // If no queue found, allocate a new one
            if (queue_idx == -1) begin
                for (i = 0; i < 15; i = i + 1) begin
                    if (!tb_pcie_sub_msg.queue_allocated[i][12] && queue_idx == -1) begin
                        queue_idx = i;
                        tb_pcie_sub_msg.queue_allocated[i] = {1'b1, src_id, to_bit, tag};
                        $display("[%0t] [WRITE_GEN] Allocated Queue %0d for TAG=%0d, TO=%0b, SRC_ID=0x%h",
                                 $time, queue_idx, tag, to_bit, src_id);
                    end
                end
            end

            if (queue_idx == -1) begin
                $display("[%0t] [WRITE_GEN] ERROR: No available queue!", $time);
                queue_idx = 0;  // Fallback
            end

            // Fixed address: 0x8C20000 (queue address calculated by receiver)
            final_awaddr = 64'h08C20000;

            $display("\n========================================");
            $display("[%0t] [WRITE_GEN] SEND_WRITE_RANDOM START", $time);
            $display("  TAG=%0d, TO=%0b, SRC_ID=0x%h -> Queue %0d (allocated by receiver)", tag, to_bit, src_id, queue_idx);
            $display("  Address: 0x%h (fixed)", final_awaddr);
            $display("  Length:  %0d beats (awlen=%0d)", total_beats, awlen);
            $display("  Header:  0x%h (OHC[11:8]=0x%h, OHC_size=%0dDW)", header, ohc_field, ohc_size_dw);
            $display("========================================");

            // Store metadata for verification
            if (queue_idx < 15) begin
                tb_pcie_sub_msg.expected_msg_tag[queue_idx] = {to_bit, tag}; // 4 bits: TO + TAG
                tb_pcie_sub_msg.expected_tag_owner[queue_idx] = to_bit;
                tb_pcie_sub_msg.expected_source_id[queue_idx] = src_id;
                tb_pcie_sub_msg.expected_data_valid[queue_idx] = 1'b1;
                $display("[%0t] [WRITE_GEN] Stored metadata for Queue %0d:", $time, queue_idx);
                $display("  MSG_TAG=4'b%b (TO=%0b, TAG=0x%h), SRC_ID=0x%h",
                         {to_bit, tag}, to_bit, tag, src_id);
            end

            // ====================================
            // 1. Write Address Phase
            // ====================================
            // AWREADY should already be high (receiver in IDLE state)
            @(posedge i_clk);  // Wait one cycle for synchronization

            if (!I_AWREADY) begin
                $display("[%0t] [WRITE_GEN] WARNING: AWREADY not ready, waiting...", $time);
                while (!I_AWREADY) begin
                    @(posedge i_clk);
                end
            end
            $display("[%0t] [WRITE_GEN] AWREADY is high, asserting AWVALID...", $time);

            O_AWVALID = 1'b1;
            O_AWADDR  = final_awaddr;  // Use calculated queue address
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
                if (beat == 0) begin
                    // ========================================
                    // Beat 0: Header (4DW) + OHC + Payload
                    // OHC is auto-generated with random data
                    // ========================================

                    // 1. Insert header (128 bits = 16 bytes)
                    data_beat[127:0] = header;

                    // 2. Insert OHC data (auto-generated random)
                    if (ohc_size_bytes > 0) begin
                        // OHC goes into [255:128], up to 16 bytes max in first beat
                        for (i = 0; i < ohc_size_bytes && i < 16; i = i + 1) begin
                            data_beat[128 + i*8 +: 8] = $random(tb_pcie_sub_msg.random_seed);
                        end
                    end

                    // 3. Fill remaining space with random payload
                    remaining_space = 32 - header_ohc_bytes;
                    if (remaining_space > 0) begin
                        for (i = header_ohc_bytes; i < 32; i = i + 1) begin
                            data_beat[i*8 +: 8] = $random(tb_pcie_sub_msg.random_seed);
                        end
                    end

                end else if (beat == 1 && header_ohc_bytes > 32) begin
                    // ========================================
                    // Beat 1: Remaining OHC + Payload
                    // (only if header+OHC > 32 bytes)
                    // ========================================

                    integer remaining_ohc_bytes;
                    remaining_ohc_bytes = header_ohc_bytes - 32;

                    // Insert remaining OHC data (auto-generated random)
                    for (i = 0; i < remaining_ohc_bytes && i < 32; i = i + 1) begin
                        data_beat[i*8 +: 8] = $random(tb_pcie_sub_msg.random_seed);
                    end

                    // Fill remaining space with random payload
                    for (i = remaining_ohc_bytes; i < 32; i = i + 1) begin
                        data_beat[i*8 +: 8] = $random(tb_pcie_sub_msg.random_seed);
                    end

                    // Store payload data for verification
                    if (queue_idx < 15 && payload_beat_idx < 64) begin
                        tb_pcie_sub_msg.expected_queue_data[queue_idx][payload_beat_idx] = data_beat;
                        $display("[%0t] [WRITE_GEN] Stored Q%0d[%0d] = 0x%h",
                                 $time, queue_idx, payload_beat_idx, data_beat);
                    end
                    payload_beat_idx = payload_beat_idx + 1;

                end else begin
                    // ========================================
                    // Beat 2+: Pure random payload
                    // ========================================
                    data_beat[255:192] = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                    data_beat[191:128] = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                    data_beat[127:64]  = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};
                    data_beat[63:0]    = {$random(tb_pcie_sub_msg.random_seed), $random(tb_pcie_sub_msg.random_seed)};

                    // Store payload data for verification
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

                // Build TLP header with 16-bit length field
                tlp_header = {tlp_base[119:40], size_dw[15:0], tlp_base[23:0]};

                // Build S_PKT header using localparam constants
                s_header = {S_PKT, PKT_SN0, MSG_T0, tlp_header};

                // Read error counter before test
                error_count_before = tb_pcie_sub_msg.u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0];

                // Send S_PKT
                $display("[%0t] Sending S_PKT (size=%0d DW)...", $time, size_dw);
                SEND_MSG(s_header);

                #200;

                // Build L_PKT header using localparam constants
                l_header = {L_PKT, PKT_SN1, MSG_T0, tlp_header};

                // Send L_PKT
                $display("[%0t] Sending L_PKT (size=%0d DW)...", $time, size_dw);
                SEND_MSG(l_header);

                #500;

                // Verify WPTR (in bytes)
                wptr_expected = size_dw * 4;
                wptr_actual = tb_pcie_sub_msg.u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_4[15:0];

                $display("[VERIFY] WPTR check: expected=%0d bytes, actual=%0d bytes",
                         wptr_expected, wptr_actual);

                // Verify error counter
                error_count_after = tb_pcie_sub_msg.u_pcie_msg_receiver.PCIE_SFR_AXI_MSG_HANDLER_RX_DEBUG_29[7:0];
                $display("[VERIFY] Error counter check: before=%0d, after=%0d",
                         error_count_before, error_count_after);

                // Calculate expected beats for READ_AND_CHECK
                expected_beats = (size_dw * 4 + 31) / 32;  // Round up to 32-byte beats

                // Verify SRAM data with READ_AND_CHECK
                $display("[VERIFY] Reading and checking SRAM data (%0d beats)...", expected_beats);
                tb_pcie_sub_msg.u_axi_read_gen.READ_AND_CHECK(
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
