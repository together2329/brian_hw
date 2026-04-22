// =============================================================================
// dma330_regfile.sv — DMA-330 Register File
//
// Contains all control, status, interrupt, fault, channel, debug,
// configuration, and ID registers.  Accessed by APB slave for
// software reads/writes.  Interfaces with channel threads, manager
// thread, and other internal modules.
// =============================================================================

module dma330_regfile #(
    parameter int unsigned NUM_CHANNELS = 4,
    parameter int unsigned NUM_EVENTS   = 8
)(
    // =========================================================================
    // Clock & Reset
    // =========================================================================
    input  logic                          clk,
    input  logic                          rst_n,

    // =========================================================================
    // APB Register Access Interface (from APB slave)
    // =========================================================================
    input  logic [11:0]                   reg_addr,
    input  logic [31:0]                   reg_wdata,
    output logic [31:0]                   reg_rdata,
    input  logic                          reg_we,
    input  logic                          reg_re,
    input  logic                          reg_secure_access,

    // =========================================================================
    // Channel Thread Interface
    // =========================================================================
    output dma330_pkg::channel_regs_t     ch_regs      [NUM_CHANNELS-1:0],
    input  logic [NUM_CHANNELS-1:0]       ch_regs_we,  // channel wants to update its own regs
    input  dma330_pkg::channel_state_t    ch_state     [NUM_CHANNELS-1:0],
    input  logic [31:0]                   ch_pc        [NUM_CHANNELS-1:0],

    // =========================================================================
    // Manager Thread Interface
    // =========================================================================
    input  dma330_pkg::manager_state_t    mgr_state,
    input  logic [31:0]                   mgr_pc,

    // =========================================================================
    // Event Interface
    // =========================================================================
    input  logic [NUM_EVENTS-1:0]         event_trigger,
    input  logic                          fault_trigger,

    // =========================================================================
    // Debug Interface
    // =========================================================================
    input  logic [31:0]                   dbginst0,
    input  logic [31:0]                   dbginst1,
    input  logic [3:0]                    dbgcmd,
    output logic                          dbg_status
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Control / Status Registers
    // =========================================================================
    logic [31:0] DSR;   // DMA Status Register
    logic [31:0] DPC;   // DMA Program Counter

    // =========================================================================
    // Interrupt Registers
    // =========================================================================
    logic [NUM_EVENTS-1:0] INTEN;           // Interrupt Enable (per event)
    logic [NUM_EVENTS-1:0] INTCLR;          // Interrupt Clear (write-1-to-clear)
    logic [NUM_EVENTS-1:0] INT_EVENT_RIS;   // Raw interrupt status (event-real)
    logic [NUM_EVENTS-1:0] INTMIS;          // Masked interrupt status

    // =========================================================================
    // Fault Registers
    // =========================================================================
    logic [31:0] FSRD;   // Fault Status — DMA Manager
    logic [31:0] FSRC;   // Fault Status — DMA Channels
    logic [31:0] FTRD;   // Fault Type — DMA Manager
    logic [31:0] FTC [NUM_CHANNELS-1:0]; // Fault Type per channel

    // =========================================================================
    // Debug Registers
    // =========================================================================
    logic [31:0] DBGSTATUS;
    logic [31:0] DBGINST0_reg;
    logic [31:0] DBGINST1_reg;

    // =========================================================================
    // Configuration Registers
    // =========================================================================
    logic [31:0] CR0, CR1, CR2, CR3, CR4, CRD;

    // =========================================================================
    // ID ROM Registers (read-only constants)
    // =========================================================================
    localparam logic [31:0] PERIPH_ID_VAL [3:0] = '{
        32'h30, 32'hB0, 32'h0B, 32'h00
    };
    localparam logic [31:0] PCELL_ID_VAL [3:0] = '{
        32'h0D, 32'hF0, 32'h05, 32'hB1
    };

    // =========================================================================
    // Debug Status
    // =========================================================================
    assign dbg_status = DBGSTATUS[0];

    // =========================================================================
    // Default reg_rdata — placeholder (full mux in Task 12-13)
    // =========================================================================
    assign reg_rdata = 32'h0;

    // =========================================================================
    // Default outputs — placeholder
    // =========================================================================
    genvar g;
    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_ch_regs_default
            assign ch_regs[g] = '0;
        end
    endgenerate

endmodule : dma330_regfile
