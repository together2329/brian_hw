`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_cdc (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             pclk,
    input  logic                                             presetn,
    input  logic                                             enable_pclk,
    input  logic                                             drop_mode_pclk,
    input  logic                                             raw_debug_read_enable_pclk,
    input  logic [12:0]                                      configured_tu_bytes_pclk,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base_pclk,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit_pclk,
    output logic                                             enable_axi,
    output logic                                             drop_mode_axi,
    output logic                                             raw_debug_read_enable_axi,
    output logic [12:0]                                      configured_tu_bytes_axi,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_base_axi,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_limit_axi,
    input  logic                                             packet_drop_axi,
    input  logic                                             assembly_drop_axi,
    input  logic                                             descriptor_event_axi,
    input  logic                                             read_error_axi,
    output logic                                             packet_drop_pclk,
    output logic                                             assembly_drop_pclk,
    output logic                                             descriptor_event_pclk,
    output logic                                             read_error_pclk
);
    logic unused_inputs;

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
