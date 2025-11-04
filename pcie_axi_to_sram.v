// PCIe AXI to SRAM
// AXI Read Slave - reads data from SRAM and provides via AXI read channel

module pcie_axi_to_sram (
    input wire clk,
    input wire rst_n,

    // AXI Read Address Channel
    input wire         axi_arvalid,
    input wire  [63:0] axi_araddr,
    input wire  [11:0] axi_arlen,
    input wire  [2:0]  axi_arsize,
    input wire  [1:0]  axi_arburst,
    output reg         axi_arready,

    // AXI Read Data Channel
    output reg         axi_rvalid,
    output reg [255:0] axi_rdata,
    output reg  [1:0]  axi_rresp,
    output reg         axi_rlast,
    input wire         axi_rready,

    // SRAM Read Interface
    output reg         sram_ren,
    output reg  [9:0]  sram_raddr,
    input wire  [255:0] sram_rdata
);

    // State machine
    localparam IDLE   = 2'b00;
    localparam R_WAIT = 2'b01;
    localparam R_DATA = 2'b10;

    reg [1:0] state;
    reg [63:0] read_addr;
    reg [11:0] beat_count;
    reg [11:0] total_beats;
    reg [9:0] sram_addr_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            axi_arready <= 1'b0;
            axi_rvalid <= 1'b0;
            axi_rdata <= 256'h0;
            axi_rresp <= 2'b00;
            axi_rlast <= 1'b0;
            read_addr <= 64'h0;
            beat_count <= 12'h0;
            total_beats <= 12'h0;
            sram_ren <= 1'b0;
            sram_raddr <= 10'h0;
            sram_addr_cnt <= 10'h0;
        end else begin
            // Default
            sram_ren <= 1'b0;

            case (state)
                IDLE: begin
                    axi_arready <= 1'b1;
                    axi_rvalid <= 1'b0;

                    if (axi_arvalid && axi_arready) begin
                        read_addr <= axi_araddr;
                        total_beats <= axi_arlen + 1;
                        beat_count <= 12'h0;
                        sram_addr_cnt <= axi_araddr[9:0];
                        axi_arready <= 1'b0;

`ifdef DEBUG
                        $display("[%0t] [AXI_SRAM] Read request: addr=0x%h, len=%0d",
                                 $time, axi_araddr, axi_arlen + 1);
`endif

                        // Start SRAM read
                        sram_ren <= 1'b1;
                        sram_raddr <= axi_araddr[9:0];
                        state <= R_WAIT;
                    end
                end

                R_WAIT: begin
                    // Wait 1 cycle for SRAM read latency
                    state <= R_DATA;
                end

                R_DATA: begin
                    // Always set up signals every cycle (continuously drive)
                    axi_rdata <= sram_rdata;
                    axi_rvalid <= 1'b1;
                    axi_rresp <= 2'b00;
                    axi_rlast <= (beat_count == total_beats - 1);

                    // Check for handshake
                    if (axi_rvalid && axi_rready) begin
`ifdef DEBUG
                        $display("[%0t] [AXI_SRAM] Read beat %0d: sram[%0d] = 0x%h, last=%0b",
                                 $time, beat_count, sram_addr_cnt, axi_rdata, axi_rlast);
`endif

                        axi_rvalid <= 1'b0;

                        if (axi_rlast) begin
                            // Last beat completed
                            axi_rlast <= 1'b0;
                            state <= IDLE;
`ifdef DEBUG
                            $display("[%0t] [AXI_SRAM] Read complete\n", $time);
`endif
                        end else begin
                            // Continue reading from SRAM
                            beat_count <= beat_count + 1;
                            sram_addr_cnt <= sram_addr_cnt + 1;
                            sram_ren <= 1'b1;
                            sram_raddr <= sram_addr_cnt + 1;
                            state <= R_WAIT;
                        end
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
