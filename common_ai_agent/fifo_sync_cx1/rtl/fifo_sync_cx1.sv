// fifo_sync_cx1 - 8-deep x 8-bit synchronous FIFO with full/empty flags.
// SSOT: fifo_sync_cx1/yaml/fifo_sync_cx1.ssot.yaml
// FM_WRITE: push wr_data when wr_en && !full   [BC_FIFO_WRITE]
// FM_READ:  advance rd_ptr when rd_en && !empty; rd_data from head  [BC_FIFO_READ]
// full  = (count == 8)                          [BC_FIFO_FLAGS]
// empty = (count == 0)                          [BC_FIFO_FLAGS]
// Sync active-low reset clears all state.       [BC_FIFO_RESET]

module fifo_sync_cx1 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       wr_en,
    input  wire [7:0] wr_data,
    input  wire       rd_en,
    output wire [7:0] rd_data,
    output wire       full,
    output wire       empty
);

    localparam DEPTH = 8;
    localparam PTR_W = 3;
    localparam CNT_W = 4;

    reg [7:0] mem [0:DEPTH-1];
    reg [PTR_W-1:0] wr_ptr;
    reg [PTR_W-1:0] rd_ptr;
    reg [CNT_W-1:0] count;

    // Status flags - combinational decode of registered count  [BC_FIFO_FLAGS]
    assign full    = (count == 4'd8);
    assign empty   = (count == 4'd0);

    // rd_data presents head of FIFO combinationally  [BC_FIFO_READ]
    assign rd_data = mem[rd_ptr];

    // Write / read / pointer / count update
    always @(posedge clk) begin
        if (!rst_n) begin
            wr_ptr <= 3'd0;
            rd_ptr <= 3'd0;
            count  <= 4'd0;
        end else begin
            // Write: accepted when wr_en && !full  [BC_FIFO_WRITE]
            if (wr_en && !full) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr      <= wr_ptr + 3'd1;
            end
            // Read: accepted when rd_en && !empty  [BC_FIFO_READ]
            if (rd_en && !empty) begin
                rd_ptr <= rd_ptr + 3'd1;
            end
            // Count update - simultaneous write+read keeps count unchanged
            if ((wr_en && !full) && !(rd_en && !empty)) begin
                count <= count + 4'd1;
            end else if (!(wr_en && !full) && (rd_en && !empty)) begin
                count <= count - 4'd1;
            end
        end
    end

endmodule
