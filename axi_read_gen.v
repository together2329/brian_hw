module axi_read_gen
(
// Clock
input i_clk,
// Reset
input i_reset_n,
// AXI I/F
// Read Address Channel
output reg [6:0] arid,
output reg [31:0] araddr,
output reg [7:0] arlen,
output reg [2:0] arsize,
output reg [1:0] arburst,
output reg       arvalid,
input            arready,

// Read Data/Response Channel
input [6:0] rid,
input [255:0] rdata,
input [1:0] rresp,
input       rlast,
input       rvalid,
output reg  rready
);

    // Internal storage for read data verification
    reg [255:0] read_data_mem [0:15];

    // Fragment type definitions (must match write gen)
    localparam S_PKT  = 2'b10;
    localparam M_PKT  = 2'b00;
    localparam L_PKT  = 2'b01;
    localparam SG_PKT = 2'b11;

    localparam MSG_T0 = 4'b1000;
    localparam MSG_T1 = 4'b1001;
    localparam MSG_T2 = 4'b1010;
    localparam MSG_T3 = 4'b1011;

    reg [127:0] expected_header;
    reg [119:0] tlp_base;

    initial begin
        // Wait for reset
        wait(i_reset_n);
        #6500;  // Wait for all assembly operations to complete (including bad header test)

        // TLP header base (same as write gen)
        tlp_base = 120'h0;
        tlp_base[7:5] = 3'b011;           // fmt
        tlp_base[4:3] = 2'b10;            // type
        tlp_base[31:24] = 8'h20;          // length (128B)
        tlp_base[51:48] = 4'b0000;        // pcie_tag
        tlp_base[63:56] = 8'b01111111;    // msg code
        tlp_base[87:80] = 8'h1A;          // vendor id
        tlp_base[95:88] = 8'hB4;          // vendor id
        tlp_base[99:96] = 4'b0001;        // header version
        tlp_base[119:112] = 8'h0;         // source endpoint id

        $display("\n========================================");
        $display("VERIFY TEST 1: S->L assembly (MSG_T0, 6 payload beats)");
        $display("========================================\n");
        // Test 1: S->L assembly (6 payload beats, header not stored in SRAM)
        // SRAM order: CCCC, BBBB, AAAA, 1111, FFFF, EEEE
        expected_header = {L_PKT, 2'b01, MSG_T0, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            32'h0,      // address
            8'd5,       // arlen = 5 (6 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            6,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h00000000000000000000000000000000EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE,
             256'h00000000000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
             256'h0000000000000000000000000000000011111111111111111111111111111111,
             256'h00000000000000000000000000000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
             256'h00000000000000000000000000000000BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,
             256'h00000000000000000000000000000000CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC}  // First payload (LSB)
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 2: S->M->L assembly (MSG_T1, 6 payload beats)");
        $display("========================================\n");
        // Test 2: S->M->L assembly (6 payload beats, header not stored in SRAM)
        // SRAM order: 4444, 3333, 7777, 6666, AAAA, 9999
        expected_header = {L_PKT, 2'b10, MSG_T1, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            32'h100,    // address
            8'd5,       // arlen = 5 (6 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            6,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0000000000000000000000000000000099999999999999999999999999999999,
             256'h00000000000000000000000000000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
             256'h0000000000000000000000000000000066666666666666666666666666666666,
             256'h0000000000000000000000000000000077777777777777777777777777777777,
             256'h0000000000000000000000000000000033333333333333333333333333333333,
             256'h0000000000000000000000000000000044444444444444444444444444444444}  // First payload (LSB)
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 3: S->M->M->L assembly (MSG_T2, 4 payload beats)");
        $display("========================================\n");
        // Test 3: S->M->M->L assembly (4 payload beats, header not stored in SRAM)
        // SRAM order: DEADBEEF, 12345678, FEDCBA98, 11112222...
        expected_header = {L_PKT, 2'b11, MSG_T2, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            32'h200,    // address
            8'd3,       // arlen = 3 (4 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            4,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0,
             256'h0,
             256'h0000000000000000000000000000000011112222333344445555666677778888,
             256'h00000000000000000000000000000000FEDCBA98FEDCBA98FEDCBA98FEDCBA98,
             256'h0000000000000000000000000000000012345678123456781234567812345678,
             256'h00000000000000000000000000000000DEADBEEFDEADBEEFDEADBEEFDEADBEEF}  // First payload (LSB)
        );

        #200;

        $display("\n========================================");
        $display("VERIFY TEST 4: Single packet (MSG_T3, 2 payload beats)");
        $display("========================================\n");
        // Test 4: Single packet (2 payload beats, header not stored in SRAM)
        // SRAM order: 5555AAAA..., AAAA5555...
        expected_header = {SG_PKT, 2'b00, MSG_T3, tlp_base};
        READ_AND_CHECK_ASSEMBLY(
            32'h300,    // address
            8'd1,       // arlen = 1 (2 beats)
            3'd5,       // 32 bytes
            2'b01,      // INCR
            expected_header,
            2,          // payload beats only
            {256'h0,  // Padding (MSB)
             256'h0,
             256'h0,
             256'h0,
             256'h0,
             256'h0,
             256'h00000000000000000000000000000000AAAA5555AAAA5555AAAA5555AAAA5555,
             256'h000000000000000000000000000000005555AAAA5555AAAA5555AAAA5555AAAA}  // First payload (LSB)
        );

        #200;
        $display("\n[READ_GEN] All assembly verifications completed\n");
        #200;
        $finish;
    end

    // ========================================
    // AXI Read Task with Assembly Payload Verification
    // ========================================
    task automatic READ_AND_CHECK_ASSEMBLY;
        input [31:0]      read_araddr;
        input [7:0]       read_arlen;
        input [2:0]       read_arsize;
        input [1:0]       read_arburst;
        input [127:0]     expected_header;
        input integer     exp_beats;
        input [256*16-1:0] expected_payload;  // Up to 16 beats

        integer beat;
        reg [255:0] data_beat;
        reg [127:0] received_header;
        reg verification_pass;
        integer total_beats;
        reg [255:0] exp_beat_data;

        begin
            total_beats = read_arlen + 1;

            $display("\n========================================");
            $display("[%0t] [READ_GEN] READ_AND_CHECK_ASSEMBLY START", $time);
            $display("  Address: 0x%h", read_araddr);
            $display("  Length:  %0d payload beats", total_beats);
            $display("  (Header assembled but not stored in SRAM)");
            $display("========================================");

            verification_pass = 1'b1;

            // Read Address Phase
            @(posedge i_clk);
            #1;
            arvalid = 1'b1;
            araddr  = read_araddr;
            arlen   = read_arlen;
            arsize  = read_arsize;
            arburst = read_arburst;
            arid    = 7'h0;

            @(posedge i_clk);
            while (!arready) begin
                @(posedge i_clk);
            end

            $display("[%0t] [READ_GEN] Read Address Sent", $time);

            @(posedge i_clk);
            arvalid = 1'b0;
            rready  = 1'b1;

            // Read Data Phase
            beat = 0;
            while (beat < total_beats) begin
                @(posedge i_clk);
                #1;

                if (rvalid && rready) begin
                    data_beat = rdata;
                    read_data_mem[beat] = data_beat;

                    $display("[%0t] [READ_GEN] Sampled beat %0d: data=0x%h", $time, beat, data_beat);

                    // Verify payload data (all beats are payload, header not stored in SRAM)
                    if (beat < exp_beats) begin
                        // Expected data: first payload beat is at lowest address
                        exp_beat_data = expected_payload[beat * 256 +: 256];
                        if (data_beat == exp_beat_data) begin
                            $display("[%0t] [READ_GEN] Beat %0d: PAYLOAD MATCH (0x%h)",
                                     $time, beat, data_beat);
                        end else begin
                            $display("[%0t] [READ_GEN] Beat %0d: PAYLOAD MISMATCH", $time, beat);
                            $display("  Expected: 0x%h", exp_beat_data);
                            $display("  Received: 0x%h", data_beat);
                            verification_pass = 1'b0;
                        end
                    end

                    // Check response
                    if (rresp != 2'b00) begin
                        $display("[%0t] [READ_GEN] WARNING: Non-OKAY response: %0d", $time, rresp);
                        verification_pass = 1'b0;
                    end

                    // Check RLAST
                    if (rlast && (beat != total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: Unexpected RLAST at beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end else if (!rlast && (beat == total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: RLAST not asserted at last beat", $time);
                        verification_pass = 1'b0;
                    end

                    beat = beat + 1;
                end
            end

            // Wait one more cycle for AXI slave to see the last handshake
            @(posedge i_clk);
            #1;

            rready = 1'b0;

            $display("\n========================================");
            if (verification_pass) begin
                $display("[%0t] [READ_GEN] *** ASSEMBLY VERIFICATION PASSED ***", $time);
            end else begin
                $display("[%0t] [READ_GEN] *** ASSEMBLY VERIFICATION FAILED ***", $time);
            end
            $display("[%0t] [READ_GEN] READ_AND_CHECK_ASSEMBLY COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

    // ========================================
    // AXI Read Task with Internal Verification (Legacy)
    // ========================================
    task automatic READ_AND_CHECK;
        input [31:0]  read_araddr;
        input [7:0]   read_arlen;      // AXI len (beats - 1)
        input [2:0]   read_arsize;
        input [1:0]   read_arburst;
        input [127:0] expected_header;  // Expected header to verify

        integer beat;
        reg [255:0] data_beat;
        reg [127:0] received_header;
        reg verification_pass;
        integer total_beats;

        begin
            total_beats = read_arlen + 1;  // AXI len is (beats - 1)

            $display("\n========================================");
            $display("[%0t] [READ_GEN] READ_AND_CHECK START", $time);
            $display("  Address: 0x%h", read_araddr);
            $display("  Length:  %0d beats (arlen=%0d)", total_beats, read_arlen);
            $display("  Size:    %0d (2^%0d = %0d bytes)", read_arsize, read_arsize, 1 << read_arsize);
            $display("  Burst:   %0d (%s)", read_arburst,
                     (read_arburst == 2'b00) ? "FIXED" :
                     (read_arburst == 2'b01) ? "INCR" : "WRAP");
            $display("  Expected Header: 0x%h", expected_header);
            $display("========================================");

            verification_pass = 1'b1;

            // ====================================
            // 1. Read Address Phase
            // ====================================
            @(posedge i_clk);
            #1;
            arvalid = 1'b1;
            araddr  = read_araddr;
            arlen   = read_arlen;
            arsize  = read_arsize;
            arburst = read_arburst;
            arid    = 7'h0;

            // Wait for arready
            @(posedge i_clk);
            while (!arready) begin
                @(posedge i_clk);
            end

            $display("[%0t] [READ_GEN] Read Address Sent", $time);

            @(posedge i_clk);
            #1;
            arvalid = 1'b0;
            rready  = 1'b1;  // Ready to receive data

            // ====================================
            // 2. Read Data Phase
            // ====================================
            beat = 0;
            while (beat < total_beats) begin
                @(posedge i_clk);
                #1;  // Small delay to let signals settle

                if (rvalid && rready) begin
                    // Capture data immediately
                    data_beat = rdata;
                    read_data_mem[beat] = data_beat;

                    $display("[%0t] [READ_GEN] Read Data Beat %0d: data=0x%h, last=%0b, resp=%0d",
                             $time, beat, data_beat, rlast, rresp);

                    // Verify first beat contains expected header
                    if (beat == 0) begin
                        received_header = data_beat[127:0];
                        if (received_header == expected_header) begin
                            $display("[%0t] [READ_GEN] *** HEADER MATCH *** ", $time);
                            $display("  Expected: 0x%h", expected_header);
                            $display("  Received: 0x%h", received_header);
                        end else begin
                            $display("[%0t] [READ_GEN] *** HEADER MISMATCH *** ", $time);
                            $display("  Expected: 0x%h", expected_header);
                            $display("  Received: 0x%h", received_header);
                            verification_pass = 1'b0;
                        end
                    end

                    // Check response
                    if (rresp != 2'b00) begin
                        $display("[%0t] [READ_GEN] WARNING: Non-OKAY response: %0d", $time, rresp);
                        verification_pass = 1'b0;
                    end

                    // Check if this is the last beat
                    if (rlast && (beat != total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: Unexpected RLAST at beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end else if (!rlast && (beat == total_beats - 1)) begin
                        $display("[%0t] [READ_GEN] WARNING: RLAST not asserted at last beat %0d", $time, beat);
                        verification_pass = 1'b0;
                    end

                    beat = beat + 1;
                end
            end

            rready = 1'b0;

            $display("\n========================================");
            if (verification_pass) begin
                $display("[%0t] [READ_GEN] *** VERIFICATION PASSED ***", $time);
            end else begin
                $display("[%0t] [READ_GEN] *** VERIFICATION FAILED ***", $time);
            end
            $display("[%0t] [READ_GEN] READ_AND_CHECK COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

    task WAIT_INTR_ERR;
      begin
        // TODO: Implement interrupt error wait logic
        // wait(tb_pcie_sub_msg.o_msg_interrupt == 1);
        // force tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_CLEAR_0[3] = tb_pcie_sub_msg.PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[3];
      end
    endtask

    task WAIT_INTR;
      input [31:0] expected_wptr;
      begin
        // TODO: Implement interrupt wait logic
        // PCIE_SFR_AXI_MSG_HANDLER_Q_INTR_STATUS_0[0];
        // PCIE_SFR_AXI_MSG_HANDLER_Q_INIT_ADDR_0[15:0];
        // PCIE_SFR_AXI_MSG_HANDLER_Q_DATA_WPTR_0[15:0];
      end
    endtask


endmodule
