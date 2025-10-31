// Simple Dual Port SRAM
// Write port for pcie_msg_receiver
// Read port for pcie_axi_to_sram

module sram #(
    parameter DATA_WIDTH = 256,
    parameter ADDR_WIDTH = 10,   // 1024 entries
    parameter DEPTH = 1024
)(
    input wire clk,

    // Write Port
    input wire                    wen,
    input wire [ADDR_WIDTH-1:0]   waddr,
    input wire [DATA_WIDTH-1:0]   wdata,

    // Read Port
    input wire                    ren,
    input wire [ADDR_WIDTH-1:0]   raddr,
    output reg [DATA_WIDTH-1:0]   rdata
);

    // Memory array
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    integer i;

    // Initialize memory
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            mem[i] = {DATA_WIDTH{1'b0}};
        end
    end

    // Write port
    always @(posedge clk) begin
        if (wen) begin
            mem[waddr] <= wdata;
            $display("[%0t] [SRAM] Write: addr=%0d, data=0x%h",
                     $time, waddr, wdata);
        end
    end

    // Read port
    always @(posedge clk) begin
        if (ren) begin
            rdata <= mem[raddr];
            $display("[%0t] [SRAM] Read: addr=%0d, data=0x%h",
                     $time, raddr, mem[raddr]);
        end
    end

endmodule
