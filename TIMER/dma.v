
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: dma
// Description: DMA controller with APB slave (register config) and
//              AHB master (data transfer) interfaces.
//
// Performs word-by-word memory-to-memory (or peripheral) transfers.
// CPU configures source/destination addresses and count, then sets
// the start bit. DMA requests the AHB bus, reads from source, writes
// to destination, and loops until count reaches zero.
//
// Register Map (APB, word-aligned, PADDR[7:0]):
//   Offset 0x00  SRC_ADDR   R/W  [31:0] source address
//   Offset 0x04  DST_ADDR   R/W  [31:0] destination address
//   Offset 0x08  COUNT      R/W  [31:0] number of words to transfer
//   Offset 0x0C  CONTROL    R/W  [0]=start (auto-clear), [1]=irq_enable
//   Offset 0x10  STATUS     R    [0]=busy, [1]=done (cleared on read)
//
// APB3 Slave Interface:
//   HCLK     - Bus clock (shared with AHB)
//   HRESETn  - Active-low reset
//   PSEL     - Select signal
//   PENABLE  - Enable signal
//   PWRITE   - Write strobe
//   PADDR    - Address [7:0]
//   PWDATA   - Write data [31:0]
//   PRDATA   - Read data [31:0]
//   PREADY   - Always 1
//   PSLVERR  - Always 0
//
// AHB-Lite Master Interface:
//   HADDR    - Address [31:0]
//   HWDATA   - Write data [31:0]
//   HRDATA   - Read data [31:0]
//   HWRITE   - Write strobe
//   HTRANS   - Transfer type [1:0]
//   HSIZE    - Transfer size [2:0] (always word)
//   HBUSREQ  - Bus request
//   HGRANT   - Bus grant input
//   HREADY   - Transfer ready input
//
// Interrupt:
//   dma_irq  - Asserted when done AND irq_enable set, cleared on STATUS read
//----------------------------------------------------------------------------

module dma (
    input  wire         HCLK,
    input  wire         HRESETn,

    // APB3 Slave Interface (register access from CPU)
    input  wire         PSEL,
    input  wire         PENABLE,
    input  wire         PWRITE,
    input  wire [7:0]   PADDR,
    input  wire [31:0]  PWDATA,
    output wire [31:0]  PRDATA,
    output wire         PREADY,
    output wire         PSLVERR,

    // AHB-Lite Master Interface (data transfers)
    output reg  [31:0]  HADDR,
    output reg  [31:0]  HWDATA,
    input  wire [31:0]  HRDATA,
    output reg          HWRITE,
    output reg  [1:0]   HTRANS,
    output reg  [2:0]   HSIZE,
    output reg          HBUSREQ,
    input  wire         HGRANT,
    input  wire         HREADY,

    // Interrupt output
    output wire         dma_irq
);

    //--------------------------------------------------------------------------
    // AHB constants
    //--------------------------------------------------------------------------
    localparam [1:0] HTRANS_IDLE   = 2'b00;
    localparam [1:0] HTRANS_NONSEQ = 2'b10;
    localparam [2:0] HSIZE_WORD    = 3'b010;

    //--------------------------------------------------------------------------
    // DMA FSM states
    //--------------------------------------------------------------------------
    localparam [2:0] DMA_IDLE       = 3'd0;
    localparam [2:0] DMA_BUS_REQ    = 3'd1;
    localparam [2:0] DMA_READ_ADDR  = 3'd2;
    localparam [2:0] DMA_READ_DATA  = 3'd3;
    localparam [2:0] DMA_WRITE_ADDR = 3'd4;
    localparam [2:0] DMA_WRITE_DATA = 3'd5;
    localparam [2:0] DMA_DONE       = 3'd6;

    reg [2:0] dma_state;

    //--------------------------------------------------------------------------
    // APB registers (written by CPU)
    //--------------------------------------------------------------------------
    reg [31:0] reg_src_addr;
    reg [31:0] reg_dst_addr;
    reg [31:0] reg_count;
    reg        reg_start;
    reg        reg_irq_en;
    reg        reg_busy;
    reg        reg_done;

    //--------------------------------------------------------------------------
    // DMA working registers (modified during transfer)
    //--------------------------------------------------------------------------
    reg [31:0] work_src_addr;
    reg [31:0] work_dst_addr;
    reg [31:0] work_count;
    reg [31:0] data_buf;

    //--------------------------------------------------------------------------
    // APB address decode
    //--------------------------------------------------------------------------
    wire [2:0] addr_word = PADDR[4:2];
    wire       apb_write = PSEL && PENABLE && PWRITE;
    wire       apb_read  = PSEL && PENABLE && !PWRITE;

    //--------------------------------------------------------------------------
    // Main sequential logic: DMA FSM + APB register access
    //--------------------------------------------------------------------------
    always @(posedge HCLK) begin
        if (!HRESETn) begin
            dma_state     <= DMA_IDLE;
            reg_src_addr  <= 32'd0;
            reg_dst_addr  <= 32'd0;
            reg_count     <= 32'd0;
            reg_start     <= 1'b0;
            reg_irq_en    <= 1'b0;
            reg_busy      <= 1'b0;
            reg_done      <= 1'b0;
            work_src_addr <= 32'd0;
            work_dst_addr <= 32'd0;
            work_count    <= 32'd0;
            data_buf      <= 32'd0;
            HADDR         <= 32'd0;
            HWDATA        <= 32'd0;
            HWRITE        <= 1'b0;
            HTRANS        <= HTRANS_IDLE;
            HSIZE         <= HSIZE_WORD;
            HBUSREQ       <= 1'b0;
        end else begin
            // Default: HTRANS returns to IDLE each cycle (overridden in addr phases)
            HTRANS <= HTRANS_IDLE;

            //------------------------------------------------------------------
            // DMA FSM
            //------------------------------------------------------------------
            case (dma_state)
                DMA_IDLE: begin
                    HBUSREQ <= 1'b0;
                    if (reg_start) begin
                        reg_start <= 1'b0;  // Auto-clear always
                        if (reg_count > 32'd0) begin
                            reg_busy      <= 1'b1;
                            reg_done      <= 1'b0;
                            work_src_addr <= reg_src_addr;
                            work_dst_addr <= reg_dst_addr;
                            work_count    <= reg_count;
                            dma_state     <= DMA_BUS_REQ;
                        end
                    end
                end

                DMA_BUS_REQ: begin
                    HBUSREQ <= 1'b1;
                    if (HGRANT) begin
                        dma_state <= DMA_READ_ADDR;
                    end
                end

                DMA_READ_ADDR: begin
                    HADDR  <= work_src_addr;
                    HWRITE <= 1'b0;
                    HTRANS <= HTRANS_NONSEQ;
                    HSIZE  <= HSIZE_WORD;
                    dma_state <= DMA_READ_DATA;
                end

                DMA_READ_DATA: begin
                    if (HREADY) begin
                        data_buf  <= HRDATA;
                        dma_state <= DMA_WRITE_ADDR;
                    end
                end

                DMA_WRITE_ADDR: begin
                    HADDR  <= work_dst_addr;
                    HWDATA <= data_buf;
                    HWRITE <= 1'b1;
                    HTRANS <= HTRANS_NONSEQ;
                    HSIZE  <= HSIZE_WORD;
                    dma_state <= DMA_WRITE_DATA;
                end

                DMA_WRITE_DATA: begin
                    if (HREADY) begin
                        work_src_addr <= work_src_addr + 32'd4;
                        work_dst_addr <= work_dst_addr + 32'd4;
                        work_count    <= work_count - 32'd1;
                        if (work_count > 32'd1) begin
                            dma_state <= DMA_READ_ADDR;
                        end else begin
                            dma_state <= DMA_DONE;
                        end
                    end
                end

                DMA_DONE: begin
                    HBUSREQ  <= 1'b0;
                    reg_busy <= 1'b0;
                    reg_done <= 1'b1;
                    dma_state <= DMA_IDLE;
                end

                default: dma_state <= DMA_IDLE;
            endcase

            //------------------------------------------------------------------
            // APB register writes (from CPU)
            //------------------------------------------------------------------
            if (apb_write) begin
                case (addr_word)
                    3'd0: reg_src_addr <= PWDATA;   // SRC_ADDR
                    3'd1: reg_dst_addr <= PWDATA;   // DST_ADDR
                    3'd2: reg_count    <= PWDATA;   // COUNT
                    3'd3: begin                      // CONTROL
                        reg_irq_en <= PWDATA[1];
                        if (PWDATA[0]) begin
                            reg_start <= 1'b1;
                            reg_done  <= 1'b0;
                        end else begin
                            reg_start <= 1'b0;
                        end
                    end
                    // STATUS (0x10): read-only
                    default: ;
                endcase
            end

            // Clear done flag on STATUS register read
            if (apb_read && addr_word == 3'd4) begin
                reg_done <= 1'b0;
            end
        end
    end

    //--------------------------------------------------------------------------
    // APB read data mux
    //--------------------------------------------------------------------------
    reg [31:0] prdata_reg;

    always @(*) begin
        prdata_reg = 32'd0;
        case (addr_word)
            3'd0:    prdata_reg = reg_src_addr;
            3'd1:    prdata_reg = reg_dst_addr;
            3'd2:    prdata_reg = reg_count;
            3'd3:    prdata_reg = {30'd0, reg_irq_en, reg_start};
            3'd4:    prdata_reg = {30'd0, reg_done, reg_busy};
            default: prdata_reg = 32'd0;
        endcase
    end

    assign PRDATA  = prdata_reg;
    assign PREADY  = 1'b1;    // No wait states
    assign PSLVERR = 1'b0;    // No slave errors

    //--------------------------------------------------------------------------
    // Interrupt: asserted when done AND irq_enable
    //   Cleared when STATUS register is read
    //--------------------------------------------------------------------------
    assign dma_irq = reg_done && reg_irq_en;

endmodule
