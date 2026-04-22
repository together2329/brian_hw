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
    // Import package
    // =========================================================================
    import dma330_pkg::*;

    // =========================================================================
    // Register Category Enumeration
    // =========================================================================
    typedef enum logic [2:0] {
        REG_CAT_CONTROL,     // DSR, DPC
        REG_CAT_INTERRUPT,   // INTEN, INT_EVENT_RIS, INTMIS, INTCLR
        REG_CAT_FAULT,       // FSRD, FSRC, FTRD, FTC
        REG_CAT_CHANNEL,     // CS, CPC, SA, DA, CC, LC0, LC1
        REG_CAT_DEBUG,       // DBGSTATUS, DBGCMD, DBGINST0, DBGINST1
        REG_CAT_CONFIG,      // CR0-CR4, CRD
        REG_CAT_ID           // PERIPH_ID, PCELL_ID
    } reg_category_t;

    // =========================================================================
    // APB Access FSM
    // =========================================================================
    typedef enum logic [1:0] {
        APB_IDLE   = 2'h0,
        APB_SETUP  = 2'h1,
        APB_ACCESS = 2'h2
    } apb_state_t;

    apb_state_t apb_state_s,  apb_state_ns;

    // =========================================================================
    // Mutual Exclusion & Active Port Selection
    // Secure port has priority when both ports are active simultaneously
    // =========================================================================
    logic active_is_secure;    // 1 = secure port is active
    logic active_psel;
    logic active_penable;
    logic active_pwrite;
    logic [APB_ADDR_WIDTH-1:0] active_paddr;
    logic [31:0]               active_pwdata;

    // Determine which port wins when both request simultaneously
    always_comb begin : port_select
        if (psel_s) begin
            // Secure port has priority
            active_is_secure = 1'b1;
            active_psel      = psel_s;
            active_penable   = penable_s;
            active_pwrite    = pwrite_s;
            active_paddr     = paddr_s;
            active_pwdata    = pwdata_s;
        end else if (psel_ns) begin
            active_is_secure = 1'b0;
            active_psel      = psel_ns;
            active_penable   = penable_ns;
            active_pwrite    = pwrite_ns;
            active_paddr     = paddr_ns;
            active_pwdata    = pwdata_ns;
        end else begin
            active_is_secure = 1'b1;  // default
            active_psel      = 1'b0;
            active_penable   = 1'b0;
            active_pwrite    = 1'b0;
            active_paddr     = '0;
            active_pwdata    = '0;
        end
    end

    // =========================================================================
    // Address Decode — categorize the accessed register
    // =========================================================================
    reg_category_t reg_category;
    logic          addr_is_secure_only;

    always_comb begin : address_decode
        reg_category      = REG_CAT_CONTROL;
        addr_is_secure_only = 1'b0;

        case (active_paddr)
            // Control registers
            DSR_OFFSET, DPC_OFFSET:
                reg_category = REG_CAT_CONTROL;

            // Interrupt registers
            INTEN_OFFSET, INT_EVENT_RIS_OFFSET, INTMIS_OFFSET, INTCLR_OFFSET:
                reg_category = REG_CAT_INTERRUPT;

            // Fault registers — secure-only
            FSRD_OFFSET:
                begin reg_category = REG_CAT_FAULT; addr_is_secure_only = 1'b1; end
            FSRC_OFFSET:
                reg_category = REG_CAT_FAULT;  // partially accessible from NS
            FTRD_OFFSET:
                begin reg_category = REG_CAT_FAULT; addr_is_secure_only = 1'b1; end
            default:
                if (active_paddr >= FTC_OFFSET_BASE &&
                    active_paddr < FTC_OFFSET_BASE + 8 * NUM_CHANNELS)
                    reg_category = REG_CAT_FAULT;

            // Channel registers
        endcase

        // Channel register range decode
        if (active_paddr >= CS_OFFSET_BASE &&
            active_paddr < CS_OFFSET_BASE + CS_CPC_STRIDE * NUM_CHANNELS) begin
            reg_category = REG_CAT_CHANNEL;
        end
        if (active_paddr >= SA_OFFSET_BASE &&
            active_paddr < SA_OFFSET_BASE + SAR_STRIDE * NUM_CHANNELS) begin
            reg_category = REG_CAT_CHANNEL;
        end

        // Debug registers — secure-only
        if (active_paddr >= DBGSTATUS_OFFSET && active_paddr <= DBGINST1_OFFSET) begin
            reg_category        = REG_CAT_DEBUG;
            addr_is_secure_only = 1'b1;
        end

        // Config registers
        if (active_paddr >= CR0_OFFSET && active_paddr <= CRD_OFFSET) begin
            reg_category = REG_CAT_CONFIG;
        end

        // ID registers — read-only, always accessible
        if (active_paddr >= PERIPH_ID_0 && active_paddr <= PCELL_ID_3) begin
            reg_category = REG_CAT_ID;
        end
    end

    // =========================================================================
    // Security Filter — NS port accessing secure-only register → PSLVERR
    // =========================================================================
    logic security_violation;

    assign security_violation = ~active_is_secure && addr_is_secure_only;

    // =========================================================================
    // APB FSM — Secure Port
    // =========================================================================
    logic secure_active;  // secure port has an active transaction
    assign secure_active = psel_s;

    always_ff @(posedge clk or negedge rst_n) begin : apb_fsm_secure
        if (!rst_n) begin
            apb_state_s <= APB_IDLE;
        end else begin
            case (apb_state_s)
                APB_IDLE: begin
                    if (psel_s && !penable_s)
                        apb_state_s <= APB_SETUP;
                end
                APB_SETUP: begin
                    if (psel_s && penable_s)
                        apb_state_s <= APB_ACCESS;
                end
                APB_ACCESS: begin
                    // Transfer complete when PENABLE asserted and PREADY=1
                    apb_state_s <= APB_IDLE;
                end
                default: apb_state_s <= APB_IDLE;
            endcase
        end
    end

    // APB FSM — Non-Secure Port
    apb_state_t apb_state_ns_reg;
    always_ff @(posedge clk or negedge rst_n) begin : apb_fsm_nonsecure
        if (!rst_n) begin
            apb_state_ns_reg <= APB_IDLE;
        end else begin
            case (apb_state_ns_reg)
                APB_IDLE: begin
                    if (psel_ns && !penable_ns && !psel_s)  // only if secure port not active
                        apb_state_ns_reg <= APB_SETUP;
                end
                APB_SETUP: begin
                    if (psel_ns && penable_ns)
                        apb_state_ns_reg <= APB_ACCESS;
                end
                APB_ACCESS: begin
                    apb_state_ns_reg <= APB_IDLE;
                end
                default: apb_state_ns_reg <= APB_IDLE;
            endcase
        end
    end

    // =========================================================================
    // Register File Interface Driving
    // =========================================================================
    // Use the active (selected) port for register access
    logic reg_access_valid;

    assign reg_access_valid  = active_psel && active_penable;
    assign reg_addr          = active_paddr;
    assign reg_wdata         = active_pwdata;
    assign reg_we            = reg_access_valid && active_pwrite && !security_violation;
    assign reg_re            = reg_access_valid && !active_pwrite && !security_violation;
    assign reg_secure_access = active_is_secure;

    // =========================================================================
    // APB Response Generation
    // =========================================================================
    // Secure port
    assign pready_s   = 1'b1;  // No wait states
    assign pslverr_s  = 1'b0;  // Secure port always has access
    assign prdata_s   = reg_rdata;

    // Non-secure port — security violation returns PSLVERR
    assign pready_ns  = 1'b1;
    assign pslverr_ns = security_violation ? 1'b1 : 1'b0;
    assign prdata_ns  = security_violation ? 32'h0 : reg_rdata;

endmodule : dma330_apb_slave
