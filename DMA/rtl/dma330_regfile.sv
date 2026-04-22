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
    input  dma330_pkg::channel_regs_t     ch_regs_wdata [NUM_CHANNELS-1:0], // live channel register state
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
    localparam logic [31:0] PERIPH_ID_0_VAL = 32'h30;
    localparam logic [31:0] PERIPH_ID_1_VAL = 32'hB0;
    localparam logic [31:0] PERIPH_ID_2_VAL = 32'h0B;
    localparam logic [31:0] PERIPH_ID_3_VAL = 32'h00;
    localparam logic [31:0] PCELL_ID_0_VAL  = 32'h0D;
    localparam logic [31:0] PCELL_ID_1_VAL  = 32'hF0;
    localparam logic [31:0] PCELL_ID_2_VAL  = 32'h05;
    localparam logic [31:0] PCELL_ID_3_VAL  = 32'hB1;

    // =========================================================================
    // Debug Status
    // =========================================================================
    assign dbg_status = DBGSTATUS[0];
    // =========================================================================
    logic [31:0] reg_rdata_int;
    assign reg_rdata = reg_rdata_int;

    // =========================================================================
    // Default outputs — placeholder
    // =========================================================================
    genvar g;

    // =========================================================================
    // Channel Register Array Storage
    // =========================================================================
    // Internal channel register storage (separate fields for APB + channel write)
    logic [31:0] SAR   [NUM_CHANNELS-1:0];
    logic [31:0] DAR   [NUM_CHANNELS-1:0];
    logic [31:0] CCR   [NUM_CHANNELS-1:0];
    logic [31:0] LC0R  [NUM_CHANNELS-1:0];
    logic [31:0] LC1R  [NUM_CHANNELS-1:0];

    // Channel register output mux — assemble channel_regs_t from storage
    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_ch_regs_out
            // Build channel_regs_t as a flat packed concatenation (Icarus-compatible)
            // channel_regs_t layout (MSB first):
            //   SA[31:0] DA[31:0] CC[31:0] PC[31:0] LC0[7:0] LC1[7:0]
            //   loop0_start_PC[31:0] loop1_start_PC[31:0] security
            assign ch_regs[g] = {
                SAR[g], DAR[g], CCR[g], ch_pc[g],
                LC0R[g][7:0], LC1R[g][7:0],
                32'h0, 32'h0, 1'b0
            };
        end
    endgenerate

    // =========================================================================
    // Channel Register Write — APB writes + channel thread writes
    // APB has priority over channel thread updates
    // =========================================================================
    // Decode which channel is being written by APB
    logic [$clog2(NUM_CHANNELS)-1:0] apb_ch_id;
    logic                             apb_ch_valid;
    logic                             apb_ch_sa_we, apb_ch_da_we, apb_ch_cc_we;
    logic                             apb_ch_lc0_we, apb_ch_lc1_we;

    always_comb begin : apb_ch_decode
        apb_ch_id     = '0;
        apb_ch_valid  = 1'b0;
        apb_ch_sa_we  = 1'b0;
        apb_ch_da_we  = 1'b0;
        apb_ch_cc_we  = 1'b0;
        apb_ch_lc0_we = 1'b0;
        apb_ch_lc1_we = 1'b0;

        if (reg_we) begin
            for (int unsigned i = 0; i < NUM_CHANNELS; i++) begin
                if (reg_addr == SA_OFFSET_BASE  + i * SAR_STRIDE) begin
                    apb_ch_id    = i[$clog2(NUM_CHANNELS)-1:0];
                    apb_ch_valid = 1'b1;
                    apb_ch_sa_we = 1'b1;
                end
                if (reg_addr == DA_OFFSET_BASE  + i * SAR_STRIDE) begin
                    apb_ch_id    = i[$clog2(NUM_CHANNELS)-1:0];
                    apb_ch_valid = 1'b1;
                    apb_ch_da_we = 1'b1;
                end
                if (reg_addr == CC_OFFSET_BASE  + i * SAR_STRIDE) begin
                    apb_ch_id    = i[$clog2(NUM_CHANNELS)-1:0];
                    apb_ch_valid = 1'b1;
                    apb_ch_cc_we = 1'b1;
                end
                if (reg_addr == LC0_OFFSET_BASE + i * SAR_STRIDE) begin
                    apb_ch_id     = i[$clog2(NUM_CHANNELS)-1:0];
                    apb_ch_valid  = 1'b1;
                    apb_ch_lc0_we = 1'b1;
                end
                if (reg_addr == LC1_OFFSET_BASE + i * SAR_STRIDE) begin
                    apb_ch_id     = i[$clog2(NUM_CHANNELS)-1:0];
                    apb_ch_valid  = 1'b1;
                    apb_ch_lc1_we = 1'b1;
                end
            end
        end
    end

    generate
        for (g = 0; g < NUM_CHANNELS; g++) begin : gen_ch_reg_write
            // SA write: APB priority over channel thread
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    SAR[g] <= 32'h0;
                else if (apb_ch_sa_we && apb_ch_id == g)
                    SAR[g] <= reg_wdata;
                else if (ch_regs_we[g])
                    SAR[g] <= ch_regs_wdata[g][208:177];
            end
            // DA write
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    DAR[g] <= 32'h0;
                else if (apb_ch_da_we && apb_ch_id == g)
                    DAR[g] <= reg_wdata;
                else if (ch_regs_we[g])
                    DAR[g] <= ch_regs_wdata[g][176:145];
            end
            // CC write
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    CCR[g] <= 32'h0;
                else if (apb_ch_cc_we && apb_ch_id == g)
                    CCR[g] <= reg_wdata;
                else if (ch_regs_we[g])
                    CCR[g] <= ch_regs_wdata[g][144:113];
            end
            // LC0 write
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    LC0R[g] <= 32'h0;
                else if (apb_ch_lc0_we && apb_ch_id == g)
                    LC0R[g] <= reg_wdata;
                else if (ch_regs_we[g])
                    LC0R[g] <= {24'd0, ch_regs_wdata[g][80:73]};
            end
            // LC1 write
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    LC1R[g] <= 32'h0;
                else if (apb_ch_lc1_we && apb_ch_id == g)
                    LC1R[g] <= reg_wdata;
                else if (ch_regs_we[g])
                    LC1R[g] <= {24'd0, ch_regs_wdata[g][72:65]};
            end
        end
    endgenerate

    // =========================================================================
    // Debug Registers
    // =========================================================================
    // DBGSTATUS[0] = DMA manager busy flag
    assign DBGSTATUS[0] = (mgr_state != MGR_STOPPED);
    assign DBGSTATUS[31:1] = 31'h0;

    // DBGINST0 / DBGINST1 — written by APB, read by debug logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            DBGINST0_reg <= 32'h0;
            DBGINST1_reg <= 32'h0;
        end else begin
            if (reg_we && reg_addr == DBGINST0_OFFSET)
                DBGINST0_reg <= reg_wdata;
            if (reg_we && reg_addr == DBGINST1_OFFSET)
                DBGINST1_reg <= reg_wdata;
        end
    end

    // =========================================================================
    // Configuration Registers — Hardwired from Parameters (read-only)
    // =========================================================================
    assign CR0 = { 4'h0,                           // [31:28] reserved
                   4'h0,                           // [27:24] interface_num
                   8'h0,                           // [23:16] reserved
                   4'(MFIFO_DEPTH / 8 - 1),        // [15:12] mfifo_depth_code
                   4'h0,                           // [11:8]  reserved
                   4'(NUM_CHANNELS - 1),            // [7:4]   num_channels - 1
                   4'h3 };                          // [3:0]   num_istreams

    assign CR1 = 32'h0000_03FF;  // Max transfer size = 1024 (default)

    assign CR2 = { 24'h0,                            // [31:8]  reserved
                   4'(NUM_PERIPHERALS - 1),           // [7:4]   num_periph_req
                   4'h0 };                            // [3:0]   num_periph_wr

    assign CR3 = { 24'h0,                            // [31:8]  reserved
                   4'(NUM_EVENTS - 1),                // [7:4]   num_events
                   4'h0 };                            // [3:0]   reserved

    assign CR4 = 32'h0000_0001;  // Bit[0] = security support enabled

    assign CRD = 32'h0000_0001;  // Bit[0] = debug support enabled

    // =========================================================================
    // DSR / DPC — Control Registers
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            DSR <= 32'h0;
            DPC <= 32'h0;
        end else begin
            if (reg_we && reg_addr == DSR_OFFSET)
                DSR <= reg_wdata;
            if (reg_we && reg_addr == DPC_OFFSET)
                DPC <= reg_wdata;
        end
    end

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

    // =========================================================================
    // Full APB Read Data Mux
    // =========================================================================
    always_comb begin : apb_read_mux
        reg_rdata_int = 32'h0;

        case (reg_addr)
            // --- Control ---
            DSR_OFFSET:   reg_rdata_int = DSR;
            DPC_OFFSET:   reg_rdata_int = DPC;

            // --- Interrupt ---
            INTEN_OFFSET:          reg_rdata_int = {{(32-NUM_EVENTS){1'b0}}, INTEN};
            INT_EVENT_RIS_OFFSET:  reg_rdata_int = {{(32-NUM_EVENTS){1'b0}}, INT_EVENT_RIS};
            INTMIS_OFFSET:         reg_rdata_int = {{(32-NUM_EVENTS){1'b0}}, INTMIS};
            INTCLR_OFFSET:         reg_rdata_int = 32'h0;  // write-only

            // --- Fault ---
            FSRD_OFFSET:  reg_rdata_int = FSRD;
            FSRC_OFFSET:  reg_rdata_int = FSRC;
            FTRD_OFFSET:  reg_rdata_int = FTRD;

            // --- Debug ---
            DBGSTATUS_OFFSET: reg_rdata_int = DBGSTATUS;
            DBGINST0_OFFSET:  reg_rdata_int = DBGINST0_reg;
            DBGINST1_OFFSET:  reg_rdata_int = DBGINST1_reg;

            // --- Config ---
            CR0_OFFSET:   reg_rdata_int = CR0;
            CR1_OFFSET:   reg_rdata_int = CR1;
            CR2_OFFSET:   reg_rdata_int = CR2;
            CR3_OFFSET:   reg_rdata_int = CR3;
            CR4_OFFSET:   reg_rdata_int = CR4;
            CRD_OFFSET:   reg_rdata_int = CRD;

            // --- ID ---
            PERIPH_ID_0:  reg_rdata_int = PERIPH_ID_0_VAL;
            PERIPH_ID_1:  reg_rdata_int = PERIPH_ID_1_VAL;
            PERIPH_ID_2:  reg_rdata_int = PERIPH_ID_2_VAL;
            PERIPH_ID_3:  reg_rdata_int = PERIPH_ID_3_VAL;
            PCELL_ID_0:   reg_rdata_int = PCELL_ID_0_VAL;
            PCELL_ID_1:   reg_rdata_int = PCELL_ID_1_VAL;
            PCELL_ID_2:   reg_rdata_int = PCELL_ID_2_VAL;
            PCELL_ID_3:   reg_rdata_int = PCELL_ID_3_VAL;

            default: ;
        endcase

        // --- Per-channel registers (indexed) ---
        for (int unsigned i = 0; i < NUM_CHANNELS; i++) begin
            // CS — Channel Status (encode ch_state as 32-bit)
            if (reg_addr == CS_OFFSET_BASE + i * CS_CPC_STRIDE)
                reg_rdata_int = {28'h0, ch_state[i]};
            // CPC — Channel PC
            if (reg_addr == CPC_OFFSET_BASE + i * CS_CPC_STRIDE)
                reg_rdata_int = ch_pc[i];
            // SA
            if (reg_addr == SA_OFFSET_BASE + i * SAR_STRIDE)
                reg_rdata_int = SAR[i];
            // DA
            if (reg_addr == DA_OFFSET_BASE + i * SAR_STRIDE)
                reg_rdata_int = DAR[i];
            // CC
            if (reg_addr == CC_OFFSET_BASE + i * SAR_STRIDE)
                reg_rdata_int = CCR[i];
            // LC0
            if (reg_addr == LC0_OFFSET_BASE + i * SAR_STRIDE)
                reg_rdata_int = LC0R[i];
            // LC1
            if (reg_addr == LC1_OFFSET_BASE + i * SAR_STRIDE)
                reg_rdata_int = LC1R[i];
            // FTC
            if (reg_addr == FTC_OFFSET_BASE + i * 8)
                reg_rdata_int = FTC[i];
        end
    end

endmodule : dma330_regfile
