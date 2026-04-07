// ============================================================================
// pcie_dma_pkg.sv - PCIe DMA Package: TLP types, constants, and structs
// ============================================================================
package pcie_dma_pkg;

    // ----------------------------------------------------------------
    // Parameters & Constants
    // ----------------------------------------------------------------
    localparam int unsigned PCIE_DATA_WIDTH_128 = 128;
    localparam int unsigned PCIE_DATA_WIDTH_256 = 256;
    localparam int unsigned PCIE_DATA_WIDTH_512 = 512;

    localparam int unsigned PCIE_TAG_WIDTH   = 8;
    localparam int unsigned PCIE_ADDR_WIDTH  = 64;
    localparam int unsigned PCIE_BYTE_EN_WIDTH = 16; // for 128-bit data

    // TLP Fmt[2:0] field encoding
    localparam logic [2:0] FMT_3DW_NO_DATA = 3'b000;
    localparam logic [2:0] FMT_4DW_NO_DATA = 3'b001;
    localparam logic [2:0] FMT_3DW_DATA    = 3'b010;
    localparam logic [2:0] FMT_4DW_DATA    = 3'b011;

    // TLP Type[4:0] field encoding
    localparam logic [4:0] TYPE_MRD  = 5'b00000; // Memory Read
    localparam logic [4:0] TYPE_MWR  = 5'b10000; // Memory Write
    localparam logic [4:0] TYPE_CPL  = 5'b01010; // Completion
    localparam logic [4:0] TYPE_CPLD = 5'b11010; // Completion with Data

    // DMA Engine States
    typedef enum logic [2:0] {
        DMA_IDLE    = 3'b000,
        DMA_SETUP   = 3'b001,
        DMA_READ    = 3'b010,
        DMA_WRITE   = 3'b011,
        DMA_WAIT    = 3'b100,
        DMA_DONE    = 3'b101,
        DMA_ERROR   = 3'b110
    } dma_state_t;

    // DMA Descriptor (control registers view)
    typedef struct packed {
        logic [63:0] src_addr;    // Source address (PCIe bus address)
        logic [63:0] dst_addr;    // Destination address (PCIe bus address)
        logic [31:0] xfer_len;    // Transfer length in bytes
        logic        direction;   // 0: PCIe->Local, 1: Local->PCIe
        logic        start;       // Start transfer
        logic        irq_en;      // Interrupt enable
        logic [15:0] completion_code; // Status / completion code
    } dma_desc_t;

    // TLP header (128-bit aligned for 3DW and 4DW headers)
    typedef struct packed {
        logic [31:0] dw0;  // Fmt, Type, TC, Attr, TD, EP, TLP digest
        logic [31:0] dw1;  // Requester ID, Tag, Last DW BE, First DW BE
        logic [31:0] dw2;  // Address [63:32] (4DW) or [31:0] (3DW)
        logic [31:0] dw3;  // Address [31:0]  (4DW only)
    } tlp_header_t;

    // DMA Status
    typedef struct packed {
        logic        busy;
        logic        done;
        logic        error;
        logic [31:0] bytes_remaining;
        logic [7:0]  outstanding_tags;
    } dma_status_t;

endpackage : pcie_dma_pkg
