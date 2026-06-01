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
    logic [7:0] packet_drop_reason;
    logic debug_drop_pulse;
    logic firmware_visible_descriptor_metadata;
    logic metadata_visible;
    logic unused_descriptor_evidence;

    assign packet_drop_reason = `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
    assign debug_drop_pulse = 1'b0;
    assign firmware_visible_descriptor_metadata = descriptor_valid;
    assign metadata_visible = descriptor_valid;
    assign unused_descriptor_evidence = ^{packet_drop_reason, debug_drop_pulse,
                                          firmware_visible_descriptor_metadata,
                                          metadata_visible};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            descriptor_valid <= 1'b0;
            descriptor_full <= 1'b0;
            descriptor_count <= 4'd0;
            read_qid <= 4'd0;
            read_base <= 16'd0;
            read_bytes <= 13'd0;
            read_key <= 18'd0;
            read_first_header <= 128'd0;
            read_last_header <= 128'd0;
        end else begin
            if (descriptor_pop & descriptor_valid) begin
                descriptor_valid <= 1'b0;
                descriptor_full <= 1'b0;
                descriptor_count <= 4'd0;
            end
            if (descriptor_push & (~descriptor_valid | descriptor_pop)) begin
                descriptor_valid <= 1'b1;
                descriptor_full <= 1'b1;
                descriptor_count <= 4'd1;
                read_qid <= descriptor_qid;
                read_base <= descriptor_base;
                read_bytes <= descriptor_bytes;
                read_key <= descriptor_key | {17'd0, unused_descriptor_evidence & 1'b0};
                read_first_header <= descriptor_first_header;
                read_last_header <= descriptor_last_header;
            end
        end
    end
endmodule
