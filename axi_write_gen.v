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

        // Initialize all outputs
        O_AWUSER = 64'h0;
        O_AWID = 7'h0;
        O_AWADDR = 64'h0;
        O_AWLEN = 8'h0;
        O_AWSIZE = 3'h0;
        O_AWBURST = 2'h0;
        O_AWLOCK = 1'b0;
        O_AWCACHE = 4'h0;
        O_AWPROT = 3'h0;
        O_AWVALID = 1'b0;
        O_WUSER = 16'h0;
        O_WDATA = 256'h0;
        O_WSTRB = 32'h0;
        O_WLAST = 1'b0;
        O_WVALID = 1'b0;
        O_BREADY = 1'b0;

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

        $display("[%0t] [WRITE_GEN] Waiting for reset sequence...", $time);
        // Wait for reset sequence completion
        // Reset starts at time 0: rst_n=1, then 0 at #100, then 1 at #200
        wait(!i_reset_n);  // Wait for reset to be asserted
        $display("[%0t] [WRITE_GEN] Reset asserted", $time);
        wait(i_reset_n);   // Wait for reset to be released
        $display("[%0t] [WRITE_GEN] Reset released, tests starting", $time);

        $display("[%0t] [WRITE_GEN] About to start TEST 1", $time);
        $display("\n========================================");
        $display("TEST 1: Single Packet (SG_PKT, MSG_T0)");
        $display("========================================\n");

        // Send single packet with 2 payload beats
        tlp_header[99:96] = 4'b0001;  // Correct version
        $display("[%0t] [WRITE_GEN] Calling SEND_WRITE", $time);

        SEND_WRITE({SG_PKT, PKT_SN0, MSG_T0, tlp_header[119:0]}, 8'h2, 3, 1,
                   {256'h0, 256'h0, 256'h0,
                    256'hBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,
                    256'hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA}, 64'h0);

        $display("[%0t] [WRITE_GEN] SEND_WRITE returned", $time);

        $display("[%0t] [WRITE_GEN] TEST 1 complete", $time);
        $display("[%0t] [WRITE_GEN] All tests completed", $time);

        // For now, only TEST 1 is enabled
    end

    // SEND_WRITE task definition continues below...
    task SEND_WRITE;
        input [127:0] header;
        input [7:0]   awlen;
        input [2:0]   awsize;
        input [1:0]   awburst;
        input [256*4-1:0] wr_data;
        input [63:0]  awaddr;

        integer beat;
        reg [255:0] data_beat;
        integer total_beats;

        begin
            total_beats = awlen + 1;

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

            // AXI handshake: receiver will see awvalid and assert awready,
            // completing the handshake on that same cycle.
            @(posedge i_clk);

            $display("[%0t] [WRITE_GEN] Write Address Sent", $time);

            @(posedge i_clk);
            O_AWVALID = 1'b0;
            $display("[%0t] [WRITE_GEN] Cleared AWVALID", $time);

            @(posedge i_clk);  // Extra delay before data phase starts
            $display("[%0t] [WRITE_GEN] About to enter data loop with %0d beats", $time, total_beats);

            // ====================================
            // 2. Write Data Phase
            // Format: First beat has header in [127:0]
            // ====================================
            for (beat = 0; beat < total_beats; beat = beat + 1) begin
                @(posedge i_clk);
                $display("[%0t] [WRITE_GEN] Beat %0d: Setting up data...", $time, beat);

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

                // AXI write data handshake - receiver sees wvalid and asserts wready
                @(posedge i_clk);

                $display("[%0t] [WRITE_GEN] Write Data Beat %0d: data=0x%h, last=%0b",
                         $time, beat, O_WDATA, O_WLAST);
            end

            @(posedge i_clk);
            O_WVALID = 1'b0;
            O_WLAST  = 1'b0;

            // ====================================
            // 3. Write Response Phase
            // ====================================
            @(posedge i_clk);
            O_BREADY = 1'b1;

            // AXI write response handshake - receiver asserts bvalid
            @(posedge i_clk);

            $display("[%0t] [WRITE_GEN] Write Response: bresp=%0d (%s)",
                     $time, I_BRESP,
                     (I_BRESP == 2'b00) ? "OKAY" :
                     (I_BRESP == 2'b01) ? "EXOKAY" :
                     (I_BRESP == 2'b10) ? "SLVERR" : "DECERR");

            @(posedge i_clk);
            O_BREADY = 1'b0;

            $display("[%0t] [WRITE_GEN] SEND_WRITE COMPLETE", $time);
            $display("========================================\n");
        end
    endtask

endmodule
