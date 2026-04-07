// ============================================================================
// pcie_dma_pkg.sv - PCIe DMA Package: TLP types, constants, and structs
// ============================================================================
package pcie_dma_pkg;

    // ----------------------------------------------------------------
    // TLP Fmt[2:0] field encoding
    // ----------------------------------------------------------------
    localparam logic [2:0] FMT_3DW_NO_DATA = 3'b000;
    localparam logic [2:0] FMT_4DW_NO_DATA = 3'b001;
    localparam logic [2:0] FMT_3DW_DATA    = 3'b010;
    localparam logic [2:0] FMT_4DW_DATA    = 3'b011;

    // ----------------------------------------------------------------
    // TLP Type[4:0] field encoding
    // ----------------------------------------------------------------
    localparam logic [4:0] TYPE_MRD  = 5'b00000; // Memory Read
    localparam logic [4:0] TYPE_MWR  = 5'b10000; // Memory Write
    localparam logic [4:0] TYPE_CPLD = 5'b11010; // Completion with Data

    // ----------------------------------------------------------------
    // DMA Engine States
    // ----------------------------------------------------------------
    typedef enum logic [2:0] {
        DMA_IDLE    = 3'b000,
        DMA_SETUP   = 3'b001,
        DMA_READ    = 3'b010,
        DMA_WRITE   = 3'b011,
        DMA_WAIT    = 3'b100,
        DMA_DONE    = 3'b101,
        DMA_ERROR   = 3'b110
    } dma_state_t;

endpackage : pcie_dma_pkg
