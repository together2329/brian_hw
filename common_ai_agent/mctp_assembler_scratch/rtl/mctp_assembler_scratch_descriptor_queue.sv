`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_descriptor_queue (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             descriptor_push,
    input  logic [3:0]                                       descriptor_qid,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    input  logic [12:0]                                      descriptor_bytes,
    input  logic [17:0]                                      descriptor_key,
    input  logic [127:0]                                     descriptor_first_header,
    input  logic [127:0]                                     descriptor_last_header,
    input  logic                                             descriptor_pop,
    output logic                                             descriptor_valid,
    output logic                                             descriptor_full,
    output logic [3:0]                                       descriptor_count,
    output logic [3:0]                                       read_qid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] read_base,
    output logic [12:0]                                      read_bytes,
    output logic [17:0]                                      read_key,
    output logic [127:0]                                     read_first_header,
    output logic [127:0]                                     read_last_header
);
    localparam DESC_DEPTH = 4;

    logic [3:0] qid_q [0:DESC_DEPTH-1];
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] base_q [0:DESC_DEPTH-1];
    logic [12:0] bytes_q [0:DESC_DEPTH-1];
    logic [17:0] key_q [0:DESC_DEPTH-1];
    logic [127:0] first_header_q [0:DESC_DEPTH-1];
    logic [127:0] last_header_q [0:DESC_DEPTH-1];
    logic [1:0] rd_ptr_q;
    logic [1:0] wr_ptr_q;
    logic push_ok;
    logic pop_ok;
    integer reset_i;

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
            for (reset_i = 0; reset_i < DESC_DEPTH; reset_i = reset_i + 1) begin
                qid_q[reset_i] <= 4'd0;
                base_q[reset_i] <= 16'd0;
                bytes_q[reset_i] <= 13'd0;
                key_q[reset_i] <= 18'd0;
                first_header_q[reset_i] <= 128'd0;
                last_header_q[reset_i] <= 128'd0;
            end
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
