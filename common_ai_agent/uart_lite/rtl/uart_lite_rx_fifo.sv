// uart_lite_rx_fifo.sv — Synchronous RX FIFO
// Implements: memory.instances.rx_fifo, dataflow.rx_path
// Parameterized depth (FIFO_DEPTH), width = DATA_WIDTH
// Write to full FIFO ignored (rx_overrun flagged externally); read from empty returns 0
// Empty/full flags are combinatorial

module uart_lite_rx_fifo #(
    parameter integer DATA_WIDTH = 8,
    parameter integer FIFO_DEPTH = 16
) (
    input  logic                        clk,
    input  logic                        rst_n,
    // Write port (from RX FSM)
    input  logic                        wr_en,
    input  logic [DATA_WIDTH-1:0]       wr_data,
    // Read port (from APB RXDATA pop)
    input  logic                        rd_en,
    output logic [DATA_WIDTH-1:0]       rd_data,
    // Status flags — combinatorial
    output logic                        empty,
    output logic                        full
);

    localparam integer ADDR_W = $clog2(FIFO_DEPTH);

    // Memory array
    logic [DATA_WIDTH-1:0] mem [0:FIFO_DEPTH-1];

    // FIFO pointers
    logic [ADDR_W:0] wr_ptr;
    logic [ADDR_W:0] rd_ptr;

    // Helper wire for write address — avoid parameterized part-select in procedural block
    wire [ADDR_W-1:0] wr_addr;
    assign wr_addr = wr_ptr[ADDR_W-1:0];

    // Write logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= {(ADDR_W+1){1'b0}};
        end else if (wr_en && !full) begin
            mem[wr_addr] <= wr_data;
            wr_ptr <= wr_ptr + 1'b1;
        end
    end

    // Read logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= {(ADDR_W+1){1'b0}};
        end else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 1'b1;
        end
    end

    // Precompute read address outside procedural block
    wire [ADDR_W-1:0] rd_addr;
    assign rd_addr = rd_ptr[ADDR_W-1:0];

    // Read data muxed from memory array; return 0 when empty
    assign rd_data = (rd_en && !empty) ? mem[rd_addr] : {DATA_WIDTH{1'b0}};

    // Combinational empty/full flags
    assign empty = (wr_ptr == rd_ptr);
    assign full  = (wr_ptr[ADDR_W] != rd_ptr[ADDR_W]) && (wr_ptr[ADDR_W-1:0] == rd_ptr[ADDR_W-1:0]);

endmodule
