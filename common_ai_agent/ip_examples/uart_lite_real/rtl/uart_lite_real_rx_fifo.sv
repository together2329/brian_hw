// uart_lite_real_rx_fifo.sv — RX FIFO (parameterized depth/width)
// SSOT: memory.instances.rx_fifo

`include "uart_lite_real_param.vh"

module uart_lite_real_rx_fifo (
    input  wire                  PCLK,
    input  wire                  PRESETn,
    input  wire                  wr_en_i,
    input  wire [DATA_WIDTH-1:0] wr_data_i,
    input  wire                  rd_en_i,
    output wire [DATA_WIDTH-1:0] rd_data_o,
    output wire                  full_o,
    output wire                  empty_o,
    output wire [FIFO_PTR_WIDTH:0] count_o
);

    reg [DATA_WIDTH-1:0] mem [0:FIFO_DEPTH-1];
    reg [FIFO_PTR_WIDTH:0] wr_ptr;
    reg [FIFO_PTR_WIDTH:0] rd_ptr;

    assign full_o  = (count_o == FIFO_DEPTH[FIFO_PTR_WIDTH:0]);
    assign empty_o = (count_o == {FIFO_PTR_WIDTH+1{1'b0}});
    assign count_o = wr_ptr - rd_ptr;

    assign rd_data_o = mem[rd_ptr[FIFO_PTR_WIDTH-1:0]];

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            wr_ptr <= {(FIFO_PTR_WIDTH+1){1'b0}};
            rd_ptr <= {(FIFO_PTR_WIDTH+1){1'b0}};
        end else begin
            if (wr_en_i && !full_o) begin
                mem[wr_ptr[FIFO_PTR_WIDTH-1:0]] <= wr_data_i;
                wr_ptr <= wr_ptr + 1'b1;
            end
            if (rd_en_i && !empty_o) begin
                rd_ptr <= rd_ptr + 1'b1;
            end
        end
    end

endmodule
