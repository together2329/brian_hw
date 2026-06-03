`include "mctp_assembler_scratch_v5_param.vh"

module mctp_assembler_scratch_v5_cdc (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             pclk,
    input  wire                                             presetn,
    input  wire                                             enable_pclk,
    input  wire                                             drop_mode_pclk,
    input  wire                                             raw_debug_read_enable_pclk,
    input  wire [12:0]                                      configured_tu_bytes_pclk,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base_pclk,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit_pclk,
    output reg                                             enable_axi,
    output reg                                             drop_mode_axi,
    output reg                                             raw_debug_read_enable_axi,
    output reg [12:0]                                      configured_tu_bytes_axi,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base_axi,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit_axi,
    input  wire                                             packet_drop_axi,
    input  wire                                             assembly_drop_axi,
    input  wire                                             descriptor_event_axi,
    input  wire                                             read_error_axi,
    output reg                                             packet_drop_pclk,
    output reg                                             assembly_drop_pclk,
    output reg                                             descriptor_event_pclk,
    output reg                                             read_error_pclk
);
    wire unused_inputs;

    assign unused_inputs = ^{pclk, presetn};

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            enable_axi <= 1'b0;
            drop_mode_axi <= 1'b0;
            raw_debug_read_enable_axi <= 1'b0;
            configured_tu_bytes_axi <= 13'd64;
            sram_base_axi <= 16'd0;
            sram_limit_axi <= 16'hffff;
            packet_drop_pclk <= 1'b0;
            assembly_drop_pclk <= 1'b0;
            descriptor_event_pclk <= 1'b0;
            read_error_pclk <= 1'b0;
        end else begin
            enable_axi <= enable_pclk;
            drop_mode_axi <= drop_mode_pclk;
            raw_debug_read_enable_axi <= raw_debug_read_enable_pclk;
            configured_tu_bytes_axi <= configured_tu_bytes_pclk;
            sram_base_axi <= sram_base_pclk;
            sram_limit_axi <= sram_limit_pclk;
            packet_drop_pclk <= packet_drop_axi | (unused_inputs & 1'b0);
            assembly_drop_pclk <= assembly_drop_axi;
            descriptor_event_pclk <= descriptor_event_axi;
            read_error_pclk <= read_error_axi;
        end
    end
endmodule
