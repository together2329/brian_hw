// =============================================================================
// dma330_apb_slave.sv — DMA-330 APB4 Slave Interface
//
// Dual APB4 slave ports (Secure + Non-secure) for register access.
// Performs address decode, security filtering, and forwards register
// read/write transactions to the register file module.
// =============================================================================

module dma330_apb_slave #(
    parameter int unsigned APB_ADDR_WIDTH = 12   // 4KB address space
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // Secure APB4 Slave Port
    // =========================================================================
    input  logic                          psel_s,
    input  logic                          penable_s,
    input  logic                          pwrite_s,
    input  logic [APB_ADDR_WIDTH-1:0]     paddr_s,
    input  logic [31:0]                   pwdata_s,
    output logic [31:0]                   prdata_s,
    output logic                          pready_s,
    output logic                          pslverr_s,

    // =========================================================================
    // Non-Secure APB4 Slave Port
    // =========================================================================
    input  logic                          psel_ns,
    input  logic                          penable_ns,
    input  logic                          pwrite_ns,
    input  logic [APB_ADDR_WIDTH-1:0]     paddr_ns,
    input  logic [31:0]                   pwdata_ns,
    output logic [31:0]                   prdata_ns,
    output logic                          pready_ns,
    output logic                          pslverr_ns,

    // =========================================================================
    // Register File Interface
    // =========================================================================
    output logic [APB_ADDR_WIDTH-1:0]     reg_addr,
    output logic [31:0]                   reg_wdata,
    input  logic [31:0]                   reg_rdata,
    output logic                          reg_we,
    output logic                          reg_re,
    output logic                          reg_secure_access
);

    // =========================================================================
    // Skeleton — logic to be implemented in Tasks 9-10
    // =========================================================================

    // Default APB outputs — no wait states, no errors
    assign pready_s   = 1'b1;
    assign pslverr_s  = 1'b0;
    assign prdata_s   = reg_rdata;

    assign pready_ns  = 1'b1;
    assign pslverr_ns = 1'b0;
    assign prdata_ns  = reg_rdata;

    // Default register file interface
    assign reg_addr          = {APB_ADDR_WIDTH{1'b0}};
    assign reg_wdata         = 32'h0;
    assign reg_we            = 1'b0;
    assign reg_re            = 1'b0;
    assign reg_secure_access = 1'b0;

endmodule : dma330_apb_slave
