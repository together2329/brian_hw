// PCIe Message Receiver
// Receives AXI write transactions and stores to SRAM
// First beat contains header[127:0] + payload[255:128]

module pcie_msg_receiver (
    input wire clk,
    input wire rst_n,

    // AXI Write Address Channel
    input wire         axi_awvalid,
    input wire  [63:0] axi_awaddr,
    input wire  [11:0] axi_awlen,
    input wire  [2:0]  axi_awsize,
    input wire  [1:0]  axi_awburst,
    output reg         axi_awready,

    // AXI Write Data Channel
    input wire         axi_wvalid,
    input wire  [255:0] axi_wdata,
    input wire  [31:0] axi_wstrb,
    input wire         axi_wlast,
    output reg         axi_wready,

    // AXI Write Response Channel
    output reg        axi_bvalid,
    output reg [1:0]  axi_bresp,
    input wire        axi_bready,

    // SRAM Write Interface
    output reg         sram_wen,
    output reg  [9:0]  sram_waddr,
    output reg  [255:0] sram_wdata,

    // Message info output
    output reg [127:0] msg_header,
    output reg         msg_valid,
    output reg [11:0]  msg_length  // in beats
);

    // State machine
    localparam IDLE   = 2'b00;
    localparam W_DATA = 2'b01;
    localparam W_RESP = 2'b10;

    reg [1:0] state;
    reg [63:0] write_addr;
    reg [11:0] beat_count;
    reg [11:0] total_beats;
    reg [9:0] sram_addr_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            axi_awready <= 1'b0;
            axi_wready <= 1'b0;
            axi_bvalid <= 1'b0;
            axi_bresp <= 2'b00;
            write_addr <= 64'h0;
            beat_count <= 12'h0;
            total_beats <= 12'h0;
            sram_wen <= 1'b0;
            sram_waddr <= 10'h0;
            sram_wdata <= 256'h0;
            msg_header <= 128'h0;
            msg_valid <= 1'b0;
            msg_length <= 12'h0;
            sram_addr_cnt <= 10'h0;
        end else begin
            // Default
            sram_wen <= 1'b0;
            msg_valid <= 1'b0;

            case (state)
                IDLE: begin
                    axi_awready <= 1'b1;
                    axi_bvalid <= 1'b0;

                    if (axi_awvalid) begin
                        $display("[%0t] [MSG_RX] Detected awvalid, awready=%0b", $time, axi_awready);
                    end

                    if (axi_awvalid && axi_awready) begin
                        write_addr <= axi_awaddr;
                        total_beats <= axi_awlen + 1;
                        beat_count <= 12'h0;
                        sram_addr_cnt <= axi_awaddr[9:0];
                        axi_awready <= 1'b0;
                        state <= W_DATA;

                        $display("[%0t] [MSG_RX] Received write addr: 0x%h, len=%0d",
                                 $time, axi_awaddr, axi_awlen + 1);
                    end
                end

                W_DATA: begin
                    axi_wready <= 1'b1;

                    if (axi_wvalid && axi_wready) begin
                        // First beat: extract header
                        if (beat_count == 0) begin
                            msg_header <= axi_wdata[127:0];
                            msg_length <= total_beats;
                            $display("[%0t] [MSG_RX] Header extracted: 0x%h",
                                     $time, axi_wdata[127:0]);
                        end

                        // Write to SRAM
                        sram_wen <= 1'b1;
                        sram_waddr <= sram_addr_cnt;
                        sram_wdata <= axi_wdata;

                        $display("[%0t] [MSG_RX] Beat %0d: sram[%0d] = 0x%h, last=%0b",
                                 $time, beat_count, sram_addr_cnt, axi_wdata, axi_wlast);

                        beat_count <= beat_count + 1;
                        sram_addr_cnt <= sram_addr_cnt + 1;

                        if (axi_wlast) begin
                            axi_wready <= 1'b0;
                            msg_valid <= 1'b1;
                            state <= W_RESP;
                        end
                    end
                end

                W_RESP: begin
                    axi_bvalid <= 1'b1;
                    axi_bresp <= 2'b00;  // OKAY

                    if (axi_bvalid && axi_bready) begin
                        $display("[%0t] [MSG_RX] Response sent: OKAY\n", $time);
                        axi_bvalid <= 1'b0;
                        state <= IDLE;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
