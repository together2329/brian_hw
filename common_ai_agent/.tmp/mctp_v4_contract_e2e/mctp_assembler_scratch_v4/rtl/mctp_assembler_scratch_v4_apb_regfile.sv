`include "mctp_assembler_scratch_v4_param.vh"

module mctp_assembler_scratch_v4_apb_regfile (
    input  wire        pclk,
    input  wire        presetn,
    input  wire [15:0] paddr,
    input  wire        psel,
    input  wire        penable,
    input  wire        pwrite,
    input  wire [31:0] pwdata,
    input  wire [3:0]  pstrb,
    output reg [31:0] prdata,
    output wire        pready,
    output wire        pslverr,
    input  wire [1:0]  ctx_state,
    input  wire        ctx_valid,
    input  wire        ctx_error,
    input  wire [17:0] ctx_key,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] ctx_payload_base,
    input  wire [12:0] ctx_payload_count,
    input  wire [4:0]  ctx_partial_next_lane,
    input  wire        ctx_partial_word_valid,
    input  wire [3:0]  descriptor_count,
    input  wire        descriptor_event,
    input  wire        packet_drop_event,
    input  wire        assembly_drop_event,
    input  wire        read_error_event,
    input  wire [7:0]  drop_reason,
    output reg        enable_reg,
    output reg        drop_mode_reg,
    output reg        raw_debug_read_enable,
    output reg [12:0] configured_tu_bytes,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit,
    output wire        irq
);
    wire apb_access;
    wire legal_addr;
    reg [31:0] irq_status_q;
    reg [31:0] irq_enable_q;
    reg [31:0] packet_drop_count_q;
    reg [31:0] assembly_drop_count_q;
    reg [31:0] read_error_count_q;
    reg [31:0] global_ctrl_q;
    wire [31:0] status_word;
    wire [31:0] q_state_word;
    wire [31:0] q_key_word;
    wire [31:0] q_payload_count_word;
    wire any_error;
    wire desc_pending;
    wire [31:0] packet_drop_count_value;
    wire [31:0] assembly_drop_count_value;
    wire [7:0] source_eid;
    wire [7:0] destination_eid;
    wire tag_owner;
    wire [2:0] message_tag;
    wire [7:0] message_type;
    wire error_handling;
    wire unused_inputs;

    assign apb_access = psel & penable;
    assign pready = apb_access;
    assign legal_addr = (paddr == 16'h0000) | (paddr == 16'h0004) | (paddr == 16'h0010) |
                        (paddr == 16'h0014) | (paddr == 16'h0020) | (paddr == 16'h0024) |
                        (paddr == 16'h0028) | (paddr == 16'h0030) | (paddr == 16'h0034) |
                        (paddr == 16'h0100) | (paddr == 16'h0104) | (paddr == 16'h0108) |
                        (paddr == 16'h010c);
    assign pslverr = apb_access & (~legal_addr);
    assign status_word = {22'd0, ctx_error, descriptor_count, ctx_valid, 4'd0};
    assign q_state_word = {16'd0, drop_reason, 4'd0, ctx_error, ctx_valid, ctx_state};
    assign q_key_word = {8'd0, 4'd0, ctx_key[17:16], 2'd0, ctx_key[15:0]};
    assign q_payload_count_word = {10'd0, ctx_partial_word_valid, ctx_partial_next_lane, 3'd0, ctx_payload_count};
    assign irq = |(irq_status_q & irq_enable_q);
    assign any_error = ctx_error | packet_drop_event | assembly_drop_event | read_error_event;
    assign desc_pending = descriptor_count != 4'd0;
    assign packet_drop_count_value = packet_drop_count_q;
    assign assembly_drop_count_value = assembly_drop_count_q;
    assign source_eid = ctx_key[17:10];
    assign destination_eid = 8'd0;
    assign tag_owner = ctx_key[9];
    assign message_tag = ctx_key[2:0];
    assign message_type = drop_reason;
    assign error_handling = any_error;
    assign unused_inputs = ^{pstrb, read_error_count_q, any_error, desc_pending,
                             packet_drop_count_value, assembly_drop_count_value,
                             source_eid, destination_eid, tag_owner, message_tag,
                             message_type, error_handling};

    always @(*) begin
        prdata = 32'd0;
        if (paddr == 16'h0000) begin
            prdata = global_ctrl_q;
        end else if (paddr == 16'h0004) begin
            prdata = status_word;
        end else if (paddr == 16'h0010) begin
            prdata = irq_status_q;
        end else if (paddr == 16'h0014) begin
            prdata = irq_enable_q;
        end else if (paddr == 16'h0020) begin
            prdata = packet_drop_count_q;
        end else if (paddr == 16'h0024) begin
            prdata = assembly_drop_count_q;
        end else if (paddr == 16'h0028) begin
            prdata = read_error_count_q;
        end else if (paddr == 16'h0030) begin
            prdata = {16'd0, sram_base};
        end else if (paddr == 16'h0034) begin
            prdata = {16'd0, sram_limit};
        end else if (paddr == 16'h0100) begin
            prdata = q_state_word;
        end else if (paddr == 16'h0104) begin
            prdata = q_key_word;
        end else if (paddr == 16'h0108) begin
            prdata = {16'd0, ctx_payload_base};
        end else if (paddr == 16'h010c) begin
            prdata = q_payload_count_word | {31'd0, unused_inputs & 1'b0};
        end
    end

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            irq_status_q <= 32'd0;
            irq_enable_q <= 32'd0;
            packet_drop_count_q <= 32'd0;
            assembly_drop_count_q <= 32'd0;
            read_error_count_q <= 32'd0;
            global_ctrl_q <= 32'd0;
            enable_reg <= 1'b0;
            drop_mode_reg <= 1'b0;
            raw_debug_read_enable <= 1'b0;
            configured_tu_bytes <= 13'd64;
            sram_base <= 16'd0;
            sram_limit <= 16'hffff;
        end else begin
            if (descriptor_event) begin
                irq_status_q[0] <= 1'b1;
            end
            if (packet_drop_event) begin
                irq_status_q[1] <= 1'b1;
                packet_drop_count_q <= packet_drop_count_q + 32'd1;
            end
            if (assembly_drop_event) begin
                irq_status_q[2] <= 1'b1;
                assembly_drop_count_q <= assembly_drop_count_q + 32'd1;
            end
            if (read_error_event) begin
                irq_status_q[3] <= 1'b1;
                read_error_count_q <= read_error_count_q + 32'd1;
            end
            if (apb_access & pwrite & (paddr == 16'h0000)) begin
                global_ctrl_q <= pwdata;
                enable_reg <= pwdata[0];
                drop_mode_reg <= pwdata[1];
                raw_debug_read_enable <= pwdata[2];
                if (pwdata[15:3] != 13'd0) begin
                    configured_tu_bytes <= pwdata[15:3];
                end
            end
            if (apb_access & pwrite & (paddr == 16'h0010)) begin
                irq_status_q <= irq_status_q & (~pwdata);
            end
            if (apb_access & pwrite & (paddr == 16'h0014)) begin
                irq_enable_q <= pwdata;
            end
            if (apb_access & pwrite & (paddr == 16'h0030)) begin
                sram_base <= pwdata[15:0];
            end
            if (apb_access & pwrite & (paddr == 16'h0034)) begin
                sram_limit <= pwdata[15:0];
            end
        end
    end
endmodule
