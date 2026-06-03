`include "mctp_assembler_scratch_v5_param.vh"

module mctp_assembler_scratch_v5_descriptor_queue (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             descriptor_push,
    input  wire [3:0]                                       descriptor_qid,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    input  wire [12:0]                                      descriptor_bytes,
    input  wire [17:0]                                      descriptor_key,
    input  wire [127:0]                                     descriptor_first_header,
    input  wire [127:0]                                     descriptor_last_header,
    input  wire                                             descriptor_pop,
    output wire                                             descriptor_valid,
    output wire                                             descriptor_full,
    output reg [3:0]                                       descriptor_count,
    output wire [3:0]                                       read_qid,
    output wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] read_base,
    output wire [12:0]                                      read_bytes,
    output wire [17:0]                                      read_key,
    output wire [127:0]                                     read_first_header,
    output wire [127:0]                                     read_last_header
);
    localparam DESC_DEPTH = 4;

    reg [3:0] qid_q [0:DESC_DEPTH-1];
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] base_q [0:DESC_DEPTH-1];
    reg [12:0] bytes_q [0:DESC_DEPTH-1];
    reg [17:0] key_q [0:DESC_DEPTH-1];
    reg [127:0] first_header_q [0:DESC_DEPTH-1];
    reg [127:0] last_header_q [0:DESC_DEPTH-1];
    reg [1:0] rd_ptr_q;
    reg [1:0] wr_ptr_q;
    wire push_ok;
    wire pop_ok;

    assign descriptor_valid = descriptor_count != 4'd0;
    assign descriptor_full = descriptor_count >= 4'd4;
    assign push_ok = descriptor_push & (!descriptor_full | pop_ok);
    assign pop_ok = descriptor_pop & descriptor_valid;
    assign read_qid = descriptor_valid ? qid_q[rd_ptr_q] : 4'd0;
    assign read_base = descriptor_valid ? base_q[rd_ptr_q] : 16'd0;
    assign read_bytes = descriptor_valid ? bytes_q[rd_ptr_q] : 13'd0;
    assign read_key = descriptor_valid ? key_q[rd_ptr_q] : 18'd0;
    assign read_first_header = descriptor_valid ? first_header_q[rd_ptr_q] : 128'd0;
    assign read_last_header = descriptor_valid ? last_header_q[rd_ptr_q] : 128'd0;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            descriptor_count <= 4'd0;
            rd_ptr_q <= 2'd0;
            wr_ptr_q <= 2'd0;
        end else begin
            if (push_ok) begin
                qid_q[wr_ptr_q] <= descriptor_qid;
                base_q[wr_ptr_q] <= descriptor_base;
                bytes_q[wr_ptr_q] <= descriptor_bytes;
                key_q[wr_ptr_q] <= descriptor_key;
                first_header_q[wr_ptr_q] <= descriptor_first_header;
                last_header_q[wr_ptr_q] <= descriptor_last_header;
                wr_ptr_q <= wr_ptr_q + 2'd1;
            end
            if (pop_ok) begin
                rd_ptr_q <= rd_ptr_q + 2'd1;
            end
            case ({push_ok, pop_ok})
                2'b10: descriptor_count <= descriptor_count + 4'd1;
                2'b01: descriptor_count <= descriptor_count - 4'd1;
                default: descriptor_count <= descriptor_count;
            endcase
        end
    end
endmodule
