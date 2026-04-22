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
    output logic                          dbg_status,

    // =========================================================================
    // Interrupt Output
    // =========================================================================
    output logic [NUM_EVENTS-1:0]         irq_o
);

    // =========================================================================
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // assign reg_rdata = 32'h0;  // placeholder — full mux in Task 13
    // =========================================================================
    logic [31:0] reg_rdata_int;
    assign reg_rdata = reg_rdata_int;

    // =========================================================================
    // Default outputs — placeholder
    // =========================================================================
    genvar g;
    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_ch_regs_default
            assign ch_regs[g] = '0;
        end
    endgenerate

    // =========================================================================
    // INT_EVENT_RIS — Set by event_trigger, cleared by INTCLR write
    // =========================================================================
    logic [NUM_EVENTS-1:0] intclr_sync;  // write-1-to-clear pulse

    always_ff @(posedge clk or negedge rst_n) begin : int_event_ris
        if (!rst_n) begin
            INT_EVENT_RIS <= '0;
        end else begin
            // Set bits from event_trigger (DMASEV)
            for (int i = 0; i < NUM_EVENTS; i++) begin
                if (event_trigger[i])
                    INT_EVENT_RIS[i] <= 1'b1;
            end
            // Clear bits from INTCLR write (write-1-to-clear)
            if (reg_we && reg_addr == INTCLR_OFFSET) begin
                for (int i = 0; i < NUM_EVENTS; i++) begin
                    if (reg_wdata[i])
                        INT_EVENT_RIS[i] <= 1'b0;
                end
            end
        end
    end

    // =========================================================================
    // INTCLR — Write-only, no storage needed (pulse decoded above)
    // =========================================================================
    assign INTCLR = '0;  // Write-only register, reads return 0

    // =========================================================================
    // INTEN — Read-Write mask register
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : int_enable
        if (!rst_n) begin
            INTEN <= '0;
        end else if (reg_we && reg_addr == INTEN_OFFSET) begin
            INTEN <= reg_wdata[NUM_EVENTS-1:0];
        end
    end

    // =========================================================================
    // INTMIS — Masked interrupt status (combinational)
    // =========================================================================
    assign INTMIS = INT_EVENT_RIS & INTEN;

    // =========================================================================
    // irq_o — Interrupt output driven from INTMIS
    // =========================================================================
    assign irq_o = INTMIS;

    // =========================================================================
    // FSRD — Fault Status, DMA Manager
    // Bit[0]: mgr_dma_fault (any manager fault)
    // Bit[4]: mgr_fault_enable
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : fsrd
        if (!rst_n) begin
            FSRD <= 32'h0;
        end else begin
            // Set by fault_trigger from manager thread
            if (fault_trigger)
                FSRD[0] <= 1'b1;
        end
    end

    // =========================================================================
    // FSRC — Fault Status, DMA Channels
    // Bit[i]: channel i fault active
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : fsrc
        if (!rst_n) begin
            FSRC <= 32'h0;
        end else begin
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                // Set when channel enters fault state
                if (ch_state[i] == CH_FAULT_COMPLETING ||
                    ch_state[i] == CH_FAULT_LOCKED)
                    FSRC[i] <= 1'b1;
            end
        end
    end

    // =========================================================================
    // FTRD — Fault Type, DMA Manager (captures fault reason code)
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin : ftrd
        if (!rst_n)
            FTRD <= 32'h0;
        else if (fault_trigger)
            FTRD <= FTRD;  // Latched — actual fault reason from manager thread
    end

    // =========================================================================
    // FTC[i] — Fault Type per Channel
    // =========================================================================
    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_ftc
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    FTC[g] <= 32'h0;
                else if (ch_state[g] == CH_FAULT_COMPLETING)
                    FTC[g] <= FTC[g];  // Latched — actual reason from channel
            end
        end
    endgenerate

endmodule : dma330_regfile
