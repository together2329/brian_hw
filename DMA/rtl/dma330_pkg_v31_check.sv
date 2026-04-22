// =============================================================================
// dma330_pkg.sv — ARM DMA-330 (PL330) Controller Package
// Parameters, enums, and shared types
// =============================================================================

package dma330_pkg;

    // =========================================================================
    // Localparams — Configuration Constants
    // =========================================================================
    localparam int unsigned NUM_CHANNELS    = 4;
    localparam int unsigned DATA_WIDTH      = 32;
    localparam int unsigned ADDR_WIDTH      = 32;
    localparam int unsigned MFIFO_DEPTH     = 64;
    localparam int unsigned NUM_PERIPHERALS = 4;
    localparam int unsigned NUM_EVENTS      = 8;
    localparam int unsigned INSTR_BUF_DEPTH = 4;

    // Derived constants
    localparam int unsigned CH_ID_WIDTH     = $clog2(NUM_CHANNELS);
    localparam int unsigned PERIPH_WIDTH    = $clog2(NUM_PERIPHERALS);
    localparam int unsigned EVENT_WIDTH     = $clog2(NUM_EVENTS);
    localparam int unsigned MFIFO_PTR_WIDTH = $clog2(MFIFO_DEPTH);

    // =========================================================================
    // Enum: channel_state_t — DMA Channel Thread FSM States
    // =========================================================================
    typedef enum logic [3:0] {
        CH_STOPPED            = 4'h0,
        CH_EXECUTING          = 4'h1,
        CH_CACHE_MISS         = 4'h2,
        CH_UPDATING_PC        = 4'h3,
        CH_WAITING_FOR_EVENT  = 4'h4,
        CH_AT_BARRIER         = 4'h5,
        CH_WAITING_FOR_PERIPH = 4'h6,
        CH_FAULT_COMPLETING   = 4'h7,
        CH_FAULT_LOCKED       = 4'h8
    } channel_state_t;

    // =========================================================================
    // Enum: manager_state_t — DMA Manager Thread FSM States
    // =========================================================================
    typedef enum logic [2:0] {
        MGR_STOPPED           = 3'h0,
        MGR_EXECUTING         = 3'h1,
        MGR_WAITING_FOR_EVENT = 3'h2,
        MGR_FAULT_COMPLETING  = 3'h3,
        MGR_FAULT_LOCKED      = 3'h4
    } manager_state_t;

    // =========================================================================
    // Enum: instr_opcode_t — DMA Instruction Opcodes
    //
    // These are symbolic enum values used internally by the design.
    // The instruction decoder module maps raw PL330 byte patterns to
    // these opcodes.  We use unique sequential values to avoid collisions
    // since several PL330 instructions share overlapping byte patterns
    // and are distinguished by secondary bits (bit[4], bit[0], etc.).
    // =========================================================================
    typedef enum logic [7:0] {
        // --- 1-byte instructions ---
        OPC_DMAEND      = 8'h00,
        OPC_DMAKILL     = 8'h01,
        OPC_DMANOP      = 8'h02,
        OPC_DMARMB      = 8'h03,
        OPC_DMAWMB      = 8'h04,

        // --- Load instructions ---
        OPC_DMALD       = 8'h10,
        OPC_DMALDP      = 8'h11,
        OPC_DMALDS      = 8'h12,
        OPC_DMALDPS     = 8'h13,

        // --- Store instructions ---
        OPC_DMAST       = 8'h20,
        OPC_DMASTP      = 8'h21,
        OPC_DMASTS      = 8'h22,
        OPC_DMASTPS     = 8'h23,

        // --- 2-byte instructions ---
        OPC_DMAADDH     = 8'h30,
        OPC_DMAADNH     = 8'h31,
        OPC_DMALP       = 8'h32,
        OPC_DMALPEND    = 8'h33,
        OPC_DMAFLUSHP   = 8'h34,
        OPC_DMASEV      = 8'h35,
        OPC_DMAWFE      = 8'h36,

        // --- 6-byte instructions ---
        OPC_DMAMOV      = 8'h40,
        OPC_DMAGO       = 8'h41,

        // --- Invalid / sentinel ---
        OPC_INVALID     = 8'hFF
    } instr_opcode_t;

    // =========================================================================
    // Enum: axi_req_type_t — AXI Request Classification
    // =========================================================================
    typedef enum logic [1:0] {
        REQ_INSTR_FETCH = 2'h0,
        REQ_DMALD       = 2'h1,
        REQ_DMAST       = 2'h2
    } axi_req_type_t;

    // =========================================================================
    // Struct: decoded_instr_t — Decoded instruction from instruction decoder
    // =========================================================================
    typedef struct packed {
        logic          valid;         // instruction decode valid
        logic          fault;         // decode fault (illegal encoding)
        instr_opcode_t opcode;        // decoded opcode
        logic [1:0]    instr_len;     // instruction length in bytes minus 1 (0=1B, 1=2B, 2=3B, 3=6B)
        logic [1:0]    reg_select;    // register select: 0=SA, 1=DA, 2=CC (for DMAMOV)
        logic [31:0]   imm32;         // 32-bit immediate (DMAMOV operand)
        logic [15:0]   imm16;         // 16-bit immediate (DMAADDH, DMAADNH)
        logic          loop_cntr_sel; // loop counter select: 0=LC0, 1=LC1
        logic [3:0]    periph_num;    // peripheral number (DMALDP, DMASTP, DMAFLUSHP, DMAWFP)
        logic [3:0]    event_num;     // event number (DMASEV, DMAWFE)
    } decoded_instr_t;

    // =========================================================================
    // Struct: channel_regs_t — Per-channel register set
    // =========================================================================
    typedef struct packed {
        logic [31:0]  SA;             // Source Address register
        logic [31:0]  DA;             // Destination Address register
        logic [31:0]  CC;             // Channel Control register
                                      //   CC[3:0]   = burst_size (bytes: 1,2,4,8,16,32,64,128)
                                      //   CC[11:4]  = burst_len  (number of transfers - 1)
                                      //   CC[14]    = src_inc (1=increment, 0=fix)
                                      //   CC[15]    = dst_inc (1=increment, 0=fix)
                                      //   CC[23:20] = src_cache_prot
                                      //   CC[27:24] = dst_cache_prot
        logic [31:0]  PC;             // Program Counter
        logic [7:0]   LC0;            // Loop Counter 0
        logic [7:0]   LC1;            // Loop Counter 1
        logic [31:0]  loop0_start_PC; // Loop 0 start address (for DMALPEND)
        logic [31:0]  loop1_start_PC; // Loop 1 start address (for DMALPEND)
        logic         security;       // Security state (0=Secure, 1=Non-secure)
    } channel_regs_t;

    // =========================================================================
    // Struct: axi_req_t — Internal AXI request (from channels to AXI master)
    // =========================================================================
    typedef struct packed {
        axi_req_type_t req_type;      // request classification
        logic [31:0]   addr;          // AXI address
        logic [31:0]   data;          // write data (for DMAST)
        logic [7:0]    burst_len;     // AXI burst length (AxLEN)
        logic [2:0]    burst_size;    // AXI burst size (AxSIZE)
        logic [3:0]    id;            // AXI transaction ID
        logic          valid;         // request is valid
        logic          security;      // security attribute (0=Secure, 1=Non-secure)
    } axi_req_t;

    // =========================================================================
    // Struct: axi_resp_t — Internal AXI response (from AXI master to channels)
    // =========================================================================
    typedef struct packed {
        logic [31:0] data;            // read data (for DMALD)
        logic        last;            // last beat of burst
        logic [1:0]  resp;            // AXI response code
        logic        valid;           // response is valid
        logic        error;           // error flag (resp != OKAY)
    } axi_resp_t;

    // =========================================================================
    // Struct: mfifo_entry_t — MFIFO data entry
    // =========================================================================
    typedef struct packed {
        logic [31:0]          data;        // data payload
        logic [CH_ID_WIDTH-1:0] channel_id; // owning channel
        logic                 valid;       // entry is valid
    } mfifo_entry_t;

    // =========================================================================
    // Register Offset Constants — 4KB APB Address Space
    // Per ARM DMA-330 TRM address map
    // =========================================================================

    // --- Control / Status Registers ---
    localparam logic [11:0] DSR_OFFSET       = 12'h000;  // DMA Status Register
    localparam logic [11:0] DPC_OFFSET       = 12'h004;  // DMA Program Counter

    // --- Interrupt Registers ---
    localparam logic [11:0] INTEN_OFFSET     = 12'h020;  // Interrupt Enable
    localparam logic [11:0] INT_EVENT_RIS_OFFSET = 12'h024; // Event-Real Raw Interrupt Status
    localparam logic [11:0] INTMIS_OFFSET    = 12'h028;  // Masked Interrupt Status
    localparam logic [11:0] INTCLR_OFFSET    = 12'h02C;  // Interrupt Clear

    // --- Fault Registers ---
    localparam logic [11:0] FSRD_OFFSET      = 12'h030;  // Fault Status, DMA Manager
    localparam logic [11:0] FSRC_OFFSET      = 12'h034;  // Fault Status, DMA Channel
    localparam logic [11:0] FTRD_OFFSET      = 12'h038;  // Fault Type, DMA Manager
    localparam logic [11:0] FTC_OFFSET_BASE  = 12'h040;  // Fault Type, Channel 0 (+0x4*ch)

    // --- Channel Status / Control Registers ---
    // Channel-specific: address = BASE + stride * channel_id
    localparam logic [11:0] CS_OFFSET_BASE   = 12'h100;  // Channel Status (+0x8*ch)
    localparam logic [11:0] CPC_OFFSET_BASE  = 12'h104;  // Channel PC (+0x8*ch)
    localparam logic [11:0] SA_OFFSET_BASE   = 12'h400;  // Source Address (+0x20*ch)
    localparam logic [11:0] DA_OFFSET_BASE   = 12'h420;  // Destination Address (+0x20*ch)
    localparam logic [11:0] CC_OFFSET_BASE   = 12'h440;  // Channel Control (+0x20*ch)
    localparam logic [11:0] LC0_OFFSET_BASE  = 12'h480;  // Loop Counter 0 (+0x20*ch)
    localparam logic [11:0] LC1_OFFSET_BASE  = 12'h4A0;  // Loop Counter 1 (+0x20*ch)

    // Channel register strides
    localparam int unsigned CS_CPC_STRIDE    = 8;         // CS[n] = CS_BASE + 8*n, CPC[n] = CPC_BASE + 8*n
    localparam int unsigned SAR_STRIDE       = 32;        // SA[n] = SA_BASE + 32*n

    // --- Debug Registers ---
    localparam logic [11:0] DBGSTATUS_OFFSET = 12'hD00;  // Debug Status
    localparam logic [11:0] DBGCMD_OFFSET    = 12'hD04;  // Debug Command
    localparam logic [11:0] DBGINST0_OFFSET  = 12'hD08;  // Debug Instruction 0
    localparam logic [11:0] DBGINST1_OFFSET  = 12'hD0C;  // Debug Instruction 1

    // --- Configuration Registers ---
    localparam logic [11:0] CR0_OFFSET       = 12'hE00;  // Configuration Register 0
    localparam logic [11:0] CR1_OFFSET       = 12'hE04;  // Configuration Register 1
    localparam logic [11:0] CR2_OFFSET       = 12'hE08;  // Configuration Register 2
    localparam logic [11:0] CR3_OFFSET       = 12'hE0C;  // Configuration Register 3
    localparam logic [11:0] CR4_OFFSET       = 12'hE10;  // Configuration Register 4
    localparam logic [11:0] CRD_OFFSET       = 12'hE14;  // Configuration Register — Debug

    // --- Component & Peripheral ID Registers (read-only) ---
    localparam logic [11:0] PERIPH_ID_0      = 12'hFE0;
    localparam logic [11:0] PERIPH_ID_1      = 12'hFE4;
    localparam logic [11:0] PERIPH_ID_2      = 12'hFE8;
    localparam logic [11:0] PERIPH_ID_3      = 12'hFEC;
    localparam logic [11:0] PCELL_ID_0       = 12'hFF0;
    localparam logic [11:0] PCELL_ID_1       = 12'hFF4;
    localparam logic [11:0] PCELL_ID_2       = 12'hFF8;
    localparam logic [11:0] PCELL_ID_3       = 12'hFFC;

endpackage : dma330_pkg
