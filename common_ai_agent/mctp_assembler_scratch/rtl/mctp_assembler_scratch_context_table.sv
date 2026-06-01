`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_context_table (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             assembly_enable,
    input  logic                                             drop_mode,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit,
    input  logic                                             descriptor_full,
    input  logic                                             descriptor_pop,
    input  logic                                             fragment_valid,
    input  logic [7:0]                                       source_eid,
    input  logic [7:0]                                       destination_eid,
    input  logic                                             tag_owner,
    input  logic [2:0]                                       message_tag,
    input  logic [1:0]                                       packet_seq,
    input  logic                                             som,
    input  logic                                             eom,
    input  logic [7:0]                                       message_type,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_data_word,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_byte_strobe,
    input  logic [12:0]                                      payload_byte_count,
    input  logic [127:0]                                     first_tlp_header,
    input  logic [127:0]                                     last_tlp_header,
    input  logic [7:0]                                       packet_drop_reason_in,
    output logic                                             payload_write_valid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_write_data,
    output logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_write_strb,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_write_addr,
    output logic [12:0]                                      payload_write_bytes,
    output logic                                             descriptor_push,
    output logic [3:0]                                       descriptor_qid,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] descriptor_base,
    output logic [12:0]                                      descriptor_bytes,
    output logic [17:0]                                      descriptor_key,
    output logic [127:0]                                     descriptor_first_header,
    output logic [127:0]                                     descriptor_last_header,
    output logic                                             packet_drop_pulse,
    output logic                                             assembly_drop_pulse,
    output logic [7:0]                                       drop_reason,
    output logic [1:0]                                       ctx_state,
    output logic                                             ctx_valid,
    output logic                                             ctx_error,
    output logic [17:0]                                      ctx_key,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] ctx_payload_base,
    output logic [12:0]                                      ctx_payload_count,
    output logic [4:0]                                       ctx_partial_next_lane,
    output logic                                             ctx_partial_word_valid,
    output logic [3:0]                                       debug_context_id,
    output logic [17:0]                                      debug_context_key
);
    logic [1:0] expected_seq_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] alloc_ptr_q;
    logic [12:0] next_payload_count;
    logic [15:0] next_alloc_addr;
    logic [15:0] write_start_addr;
    logic [4:0] write_next_lane;
    logic [17:0] incoming_key;
    logic descriptor_publish;
    logic interrupt;
    logic irq;
    logic unused_context_inputs;

    assign incoming_key = {source_eid, tag_owner, 6'd0, message_tag};
    assign next_payload_count = ctx_payload_count + payload_byte_count;
    assign next_alloc_addr = next_addr_q + {3'd0, payload_byte_count};
    assign write_start_addr = som ? (alloc_ptr_q | sram_base) : next_addr_q;
    assign write_next_lane = write_start_addr[4:0] + payload_byte_count[4:0];
    assign descriptor_publish = descriptor_push;
    assign interrupt = descriptor_push | packet_drop_pulse | assembly_drop_pulse;
    assign irq = interrupt;
    assign unused_context_inputs = ^{message_type, destination_eid, descriptor_publish, interrupt, irq};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            expected_seq_q <= 2'd0;
            next_addr_q <= 16'd0;
            alloc_ptr_q <= 16'd0;
            payload_write_valid <= 1'b0;
            payload_write_data <= 256'd0;
            payload_write_strb <= 32'd0;
            payload_write_addr <= 16'd0;
            payload_write_bytes <= 13'd0;
            descriptor_push <= 1'b0;
            descriptor_qid <= 4'd0;
            descriptor_base <= 16'd0;
            descriptor_bytes <= 13'd0;
            descriptor_key <= 18'd0;
            descriptor_first_header <= 128'd0;
            descriptor_last_header <= 128'd0;
            packet_drop_pulse <= 1'b0;
            assembly_drop_pulse <= 1'b0;
            drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_IDLE;
            ctx_valid <= 1'b0;
            ctx_error <= 1'b0;
            ctx_key <= 18'd0;
            ctx_payload_base <= 16'd0;
            ctx_payload_count <= 13'd0;
            ctx_partial_next_lane <= 5'd0;
            ctx_partial_word_valid <= 1'b0;
            debug_context_id <= 4'd0;
            debug_context_key <= 18'd0;
        end else begin
            payload_write_valid <= 1'b0;
            descriptor_push <= 1'b0;
            packet_drop_pulse <= 1'b0;
            assembly_drop_pulse <= 1'b0;
            drop_reason <= `MCTP_ASSEMBLER_SCRATCH_DROP_NONE;
            if (descriptor_pop & (ctx_state == `MCTP_ASSEMBLER_SCRATCH_STATE_DONE)) begin
                ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_IDLE;
                ctx_valid <= 1'b0;
                ctx_error <= 1'b0;
                ctx_partial_word_valid <= 1'b0;
            end
            if (fragment_valid | (packet_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE)) begin
                debug_context_id <= {1'b0, message_tag};
                debug_context_key <= incoming_key;
                if (!assembly_enable | drop_mode) begin
                    packet_drop_pulse <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_DISABLED_DROP_MODE;
                end else if (packet_drop_reason_in != `MCTP_ASSEMBLER_SCRATCH_DROP_NONE) begin
                    packet_drop_pulse <= 1'b1;
                    drop_reason <= packet_drop_reason_in;
                end else if ((ctx_state == `MCTP_ASSEMBLER_SCRATCH_STATE_IDLE) & (~som)) begin
                    packet_drop_pulse <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_PD_UNEXPECTED_MIDDLE_END;
                end else if ((ctx_state == `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING) & som & (incoming_key == ctx_key)) begin
                    assembly_drop_pulse <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_DUPLICATE_SOM;
                end else if ((ctx_state == `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING) & (packet_seq != expected_seq_q) & (~som)) begin
                    assembly_drop_pulse <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SEQUENCE_MISMATCH;
                end else if (descriptor_full & eom) begin
                    assembly_drop_pulse <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_DESCRIPTOR_FULL;
                end else if (next_alloc_addr > sram_limit) begin
                    assembly_drop_pulse <= 1'b1;
                    ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ERROR;
                    ctx_error <= 1'b1;
                    drop_reason <= `MCTP_ASSEMBLER_SCRATCH_AD_SRAM_OVERFLOW;
                end else begin
                    if (som) begin
                        ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_ASSEMBLING;
                        ctx_valid <= 1'b1;
                        ctx_error <= 1'b0;
                        ctx_key <= incoming_key;
                        ctx_payload_base <= alloc_ptr_q | sram_base;
                        next_addr_q <= alloc_ptr_q | sram_base;
                        ctx_payload_count <= 13'd0;
                    end
                    payload_write_valid <= 1'b1;
                    payload_write_data <= payload_data_word;
                    payload_write_strb <= payload_byte_strobe;
                    payload_write_addr <= write_start_addr;
                    payload_write_bytes <= payload_byte_count;
                    ctx_payload_count <= som ? payload_byte_count : next_payload_count;
                    next_addr_q <= som ? ((alloc_ptr_q | sram_base) + {3'd0, payload_byte_count}) : next_alloc_addr;
                    expected_seq_q <= packet_seq + 2'd1;
                    ctx_partial_next_lane <= write_next_lane;
                    ctx_partial_word_valid <= |write_next_lane;
                    if (eom) begin
                        ctx_state <= `MCTP_ASSEMBLER_SCRATCH_STATE_DONE_WAIT_DESCRIPTOR_POP;
                        descriptor_push <= 1'b1;
                        descriptor_qid <= {1'b0, message_tag};
                        descriptor_base <= som ? (alloc_ptr_q | sram_base) : ctx_payload_base;
                        descriptor_bytes <= som ? payload_byte_count : next_payload_count;
                        descriptor_key <= incoming_key | {17'd0, unused_context_inputs & 1'b0};
                        descriptor_first_header <= first_tlp_header;
                        descriptor_last_header <= last_tlp_header;
                        alloc_ptr_q <= som ? ((alloc_ptr_q | sram_base) + {3'd0, payload_byte_count}) : next_alloc_addr;
                    end
                end
            end
        end
    end
endmodule
