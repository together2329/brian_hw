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

    // ========================================
    // AXI Read Task with Internal Verification
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
            for (beat = 0; beat < total_beats; beat = beat + 1) begin
                // Wait for rvalid
                @(posedge i_clk);
                while (!rvalid) begin
                    @(posedge i_clk);
                end

                #1;  // Small delay after clock edge

                // Capture data
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

endmodule
