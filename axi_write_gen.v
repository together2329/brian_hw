module axi_write_gen
(
// Clock
input i_clk,
// Reset
input i_reset_n,

// AXI I/F
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

// write data
output reg [15:0] O_AWUSER,
output reg [255:0] O_WDATA,
output reg        O_WSTRB,
output reg        O_WLAST,
input             I_WREADY,

// write response
input [6:0]       I_BID,
input [1:0]       I_BRESP,
input             I_BVALID,
output reg        O_BREADY
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

reg [127:0] tlp_header;

initial begin

tlp_header = 128'h0;

tlp_header[7:5] = 3'b011;    // fmt input
tlp_header[4:3] = 2'10;      // type input
tlp_header[51:48] = 4'b0000; // pcie_tag_mctp_vdm_code_input
tlp_header[63:56] = 8'b01111111; // msg code input
tlp_header[87:80] = 8'h1A;  // vendor id input
tlp_header[95:88] = 8'hB4;  // vendor id input
tlp_header[99:96] = 4'b0001; // header version
tlp_header[119:112] = 8'h0; // source endpoint id
tlp_header[31:24] = 8'h20;  // 128B , length

end

    // ========================================
    // AXI Write Task
    // ========================================
    task automatic SEND_WRITE;
        input [127:0] header;
        input [11:0]  length;
        input [2:0]   size;
        input [1:0]   burst_type;
        input [256*4-1:0] wr_data;
        input [63:0]  awaddr;

        integer beat;
        reg [255:0] data_beat;

        begin
            $display("\n========================================");
            $display("[%0t] [MASTER] SEND_WRITE START", $time);
            $display("  Address: 0x%h", awaddr);
            $display("  Length:  %0d beats", length);
            $display("  Size:    %0d (2^%0d = %0d bytes)", size, size, 1 << size);
            $display("  Burst:   %0d (%s)", burst_type,
                     (burst_type == 2'b00) ? "FIXED" :
                     (burst_type == 2'b01) ? "INCR" : "WRAP");
            $display("========================================");

            // ====================================
            // 1. Write Address Phase
            // ====================================
            @(posedge clk);
            #1;
            axi_awvalid = 1'b1;
            axi_awaddr  = awaddr;
            axi_awlen   = length - 1;  // AXI protocol: length-1
            axi_awsize  = size;
            axi_awburst = burst_type;

            // Wait for awready
            @(posedge clk);
            while (!axi_awready) begin
                @(posedge clk);
            end

            $display("[%0t] [MASTER] Write Address Sent", $time);

            @(posedge clk);
            #1;
            axi_awvalid = 1'b0;

            // ====================================
            // 2. Write Data Phase
            // ====================================
            axi_wvalid = 1'b0;

            for (beat = 0; beat < length; beat = beat + 1) begin
                // Extract data for this beat
                data_beat = wr_data[beat*256 +: 256];

                // Set data and control signals
                axi_wdata  = data_beat;
                axi_wstrb  = 32'hFFFFFFFF;  // All bytes valid
                axi_wlast  = (beat == length - 1);
                axi_wvalid = 1'b1;

                // Wait for handshake
                do begin
                    @(posedge clk);
                end while (!axi_wready);

                #1;  // Small delay after clock edge

                $display("[%0t] [MASTER] Write Data Beat %0d: data=0x%h, last=%0b",
                         $time, beat, data_beat, axi_wlast);
            end

            axi_wvalid = 1'b0;
            axi_wlast  = 1'b0;

            // ====================================
            // 3. Write Response Phase
            // ====================================
            axi_bready = 1'b1;

            // Wait for bvalid
            @(posedge clk);
            while (!axi_bvalid) begin
                @(posedge clk);
            end

            $display("[%0t] [MASTER] Write Response: bresp=%0d (%s)",
                     $time, axi_bresp,
                     (axi_bresp == 2'b00) ? "OKAY" :
                     (axi_bresp == 2'b01) ? "EXOKAY" :
                     (axi_bresp == 2'b10) ? "SLVERR" : "DECERR");

            @(posedge clk);
            #1;
            axi_bready = 1'b0;

            $display("[%0t] [MASTER] SEND_WRITE COMPLETE\n", $time);
        end
    endtask

   
endmodule

