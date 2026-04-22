================================================================================
                    DIRECT MEMORY ACCESS (DMA) CONTROLLER
                         ARCHITECTURAL SPECIFICATION
================================================================================

Document ID    : DMA-SPEC-001
Version        : 1.0
Author         : Auto-generated
Date           : 2025
Status         : Draft

================================================================================
                         TABLE OF CONTENTS
================================================================================

  1. Introduction
  2. Feature Summary
  3. System Architecture
     3.1 Block Diagram
     3.2 Interface Descriptions
  4. Channel Architecture
     4.1 Channel Overview
     4.2 Channel Registers
     4.3 Channel State Machine
  5. Register Map
     5.1 Global Registers
     5.2 Channel Registers
  6. Transfer Types
     6.1 Memory-to-Memory
     6.2 Memory-to-Peripheral
     6.3 Peripheral-to-Memory
     6.4 Peripheral-to-Peripheral
  7. Address Calculation
     7.1 Fixed Address
     7.2 Incrementing Address
     7.3 Scatter-Gather (Linked List)
  8. Data Path and FIFO
  9. Interrupt Model
  10. Programming Model
     10.1 Basic Transfer Sequence
     10.2 Scatter-Gather Sequence
  11. Clock and Reset
  12. Bus Protocol Details
     12.1 AXI Master Interface
     12.2 AXI Slave (Register) Interface
  13. Error Handling
  14. Security and Protection
  15. Power Management
  16. Verification Plan
  17. Performance Targets
  18. Revision History

================================================================================
1. INTRODUCTION
================================================================================

This document specifies the architecture and functional behavior of a
multi-channel Direct Memory Access (DMA) controller IP core. The DMA
controller offloads the processor by autonomously moving data between
memory-mapped sources and destinations without CPU intervention.

The controller is intended for use as an SoC peripheral, connected to
the system interconnect via standard AXI4 bus interfaces. It supports
multiple independent channels, each capable of performing block
transfers, scatter-gather operations, and interfacing with peripherals
through dedicated request/acknowledge handshake signals.

================================================================================
2. FEATURE SUMMARY
================================================================================

  - 8 independent DMA channels
  - AXI4 master interface (configurable 32/64/128-bit data width)
  - AXI4-Lite slave interface for register programming
  - Transfer types:
      * Memory-to-Memory
      * Memory-to-Peripheral
      * Peripheral-to-Memory
      * Peripheral-to-Peripheral
  - Address modes:
      * Fixed address (for FIFO-based peripherals)
      * Incrementing address (linear buffers)
      * Scatter-Gather using linked-list descriptors in memory
  - Configurable transfer size: 1 byte to 64 KB per block
  - Programmable source and destination burst lengths (1, 4, 8, 16 beats)
  - Per-channel programmable priority levels (0-3, 0 = highest)
  - Per-channel interrupt generation with status registers
  - Internal data FIFO per channel (depth: 16 data beats)
  - Error detection: bus error, alignment error, descriptor fetch error
  - Configurable endianness: little-endian or big-endian
  - Security support: TrustZone-aware with Secure/Non-secure attribution
  - Clock gating support for unused channels

================================================================================
3. SYSTEM ARCHITECTECTURE
================================================================================

3.1 Block Diagram
-----------------

                    +------------------------------------------+
                    |            DMA CONTROLLER                |
                    |                                          |
   AXI4-Lite  ---> |  +------------------+                    |
   Slave IF        |  | Register Block   |                    |
   (Cfg Bus)       |  |  (Per-Channel    |                    |
                    |  |   Registers)     |                    |
                    |  +--------+---------+                    |
                    |           |                              |
                    |  +--------v---------+    +------------+  |
                    |  | Channel Manager  |    | Interrupt   |  |
                    |  |  +--+--+--+--+   |    | Controller  |  |
                    |  |  |C0|C1|..|C7|   |    |            |  |
                    |  |  +--+--+--+--+   |    +------+-----+  |
                    |  +--------+---------+           |        |
                    |           |                      |        |
                    |  +--------v---------+           |        |
                    |  |  Arbiter /       |           |        |
                    |  |  Priority Mux    |           |        |
                    |  +--------+---------+           |        |
                    |           |                      |        |
                    |  +--------v---------+           |        |
                    |  |  AXI Master IF   |           |        |
                    |  |  (Read + Write)  |           |        |
                    |  +--------+---------+           |        |
                    |           |                      |        |
                    +-----------+---------+-----+------+--------+
                                |               |
                          AXI4 Master       IRQ[7:0]
                          (Data Bus)       (Per-Channel)

   Peripheral Request Lines:
     dma_req[7:0]   -->  (input, per-channel DMA request)
     dma_ack[7:0]  <--  (output, per-channel DMA acknowledge)
     dma_eop[7:0]   -->  (input, end-of-packet from peripheral)

3.2 Interface Descriptions
---------------------------

  +---------------------+------------+----------------------------------+
  | Interface           | Direction  | Description                      |
  +---------------------+------------+----------------------------------+
  | axi_clk             | input      | AXI bus clock                    |
  | axi_rst_n           | input      | Active-low async reset           |
  | s_axi_awaddr        | input      | AXI-Lite slave write address     |
  | s_axi_awprot        | input      | AXI-Lite slave write protection  |
  | s_axi_awvalid       | input      | AXI-Lite slave write addr valid  |
  | s_axi_awready       | output     | AXI-Lite slave write addr ready  |
  | s_axi_wdata         | input      | AXI-Lite slave write data        |
  | s_axi_wstrb         | input      | AXI-Lite slave write strobe      |
  | s_axi_wvalid        | input      | AXI-Lite slave write valid       |
  | s_axi_wready        | output     | AXI-Lite slave write ready       |
  | s_axi_bresp         | output     | AXI-Lite slave write response    |
  | s_axi_bvalid        | output     | AXI-Lite slave write resp valid  |
  | s_axi_bready        | input      | AXI-Lite slave write resp ready  |
  | s_axi_araddr        | input      | AXI-Lite slave read address      |
  | s_axi_arprot        | input      | AXI-Lite slave read protection   |
  | s_axi_arvalid       | input      | AXI-Lite slave read addr valid   |
  | s_axi_arready       | output     | AXI-Lite slave read addr ready   |
  | s_axi_rdata         | output     | AXI-Lite slave read data         |
  | s_axi_rresp         | output     | AXI-Lite slave read response     |
  | s_axi_rvalid        | output     | AXI-Lite slave read valid        |
  | s_axi_rready        | input      | AXI-Lite slave read ready        |
  | m_axi_awid          | output     | AXI master write address ID      |
  | m_axi_awaddr        | output     | AXI master write address         |
  | m_axi_awlen         | output     | AXI master write burst length    |
  | m_axi_awsize        | output     | AXI master write burst size      |
  | m_axi_awburst       | output     | AXI master write burst type      |
  | m_axi_awprot        | output     | AXI master write protection      |
  | m_axi_awcache       | output     | AXI master write cache           |
  | m_axi_awvalid       | output     | AXI master write addr valid      |
  | m_axi_awready       | input      | AXI master write addr ready      |
  | m_axi_wdata         | output     | AXI master write data            |
  | m_axi_wstrb         | output     | AXI master write strobe          |
  | m_axi_wlast         | output     | AXI master write last            |
  | m_axi_wvalid        | output     | AXI master write valid           |
  | m_axi_wready        | input      | AXI master write ready           |
  | m_axi_bid           | input      | AXI master write response ID     |
  | m_axi_bresp         | input      | AXI master write response        |
  | m_axi_bvalid        | input      | AXI master write resp valid      |
  | m_axi_bready        | output     | AXI master write resp ready      |
  | m_axi_arid          | output     | AXI master read address ID       |
  | m_axi_araddr        | output     | AXI master read address          |
  | m_axi_arlen         | output     | AXI master read burst length     |
  | m_axi_arsize        | output     | AXI master read burst size       |
  | m_axi_arburst       | output     | AXI master read burst type       |
  | m_axi_arprot        | output     | AXI master read protection       |
  | m_axi_arcache       | output     | AXI master read cache            |
  | m_axi_arvalid       | output     | AXI master read addr valid       |
  | m_axi_arready       | input      | AXI master read addr ready       |
  | m_axi_rid           | input      | AXI master read ID               |
  | m_axi_rdata         | input      | AXI master read data             |
  | m_axi_rresp         | input      | AXI master read response         |
  | m_axi_rlast         | input      | AXI master read last             |
  | m_axi_rvalid        | input      | AXI master read valid            |
  | m_axi_rready        | output     | AXI master read ready            |
  | dma_req[7:0]        | input      | Per-channel DMA request          |
  | dma_ack[7:0]        | output     | Per-channel DMA acknowledge      |
  | dma_eop[7:0]        | input      | Per-channel end-of-packet        |
  | irq[7:0]            | output     | Per-channel interrupt            |
  +---------------------+------------+----------------------------------+

================================================================================
4. CHANNEL ARCHITECTURE
================================================================================

4.1 Channel Overview
---------------------

Each of the 8 DMA channels operates independently and contains:

  - Source address register
  - Destination address register
  - Transfer length register (byte count)
  - Control register (transfer configuration)
  - Status register (current state and error flags)
  - A 16-entry data FIFO (width = AXI data width)
  - A dedicated finite state machine (FSM)
  - A link pointer (for scatter-gather mode)

4.2 Channel State Machine
--------------------------

Each channel FSM has the following states:

  +-------------------+------------------------------------------------+
  | State             | Description                                    |
  +-------------------+------------------------------------------------+
  | IDLE              | Channel is inactive, no transfer in progress   |
  | DESC_FETCH        | Fetching scatter-gather descriptor from memory  |
  | WAIT_REQ          | Waiting for peripheral DMA request signal       |
  | READ_ADDR         | Issuing read address on AXI master              |
  | READ_DATA         | Receiving read data from AXI master             |
  | WRITE_ADDR        | Issuing write address on AXI master             |
  | WRITE_DATA        | Sending write data on AXI master                |
  | WRITE_RESP        | Waiting for write response from AXI master      |
  | COMPLETE          | Transfer finished, updating status              |
  | ERROR             | Transfer aborted due to error                   |
  +-------------------+------------------------------------------------+

State Transition Diagram:

  IDLE --> DESC_FETCH  (if scatter-gather enabled and channel started)
  IDLE --> WAIT_REQ    (if peripheral sync mode and channel started)
  IDLE --> READ_ADDR   (if mem-to-mem and channel started)
  DESC_FETCH --> READ_ADDR
  WAIT_REQ --> READ_ADDR   (on dma_req assertion)
  READ_ADDR --> READ_DATA
  READ_DATA --> WRITE_ADDR (when FIFO threshold reached or read complete)
  WRITE_ADDR --> WRITE_DATA
  WRITE_DATA --> WRITE_RESP (on WLAST)
  WRITE_RESP --> READ_ADDR (if more data to transfer)
  WRITE_RESP --> COMPLETE  (all data transferred)
  COMPLETE --> IDLE
  ANY_STATE --> ERROR  (on bus error or other fault)

================================================================================
5. REGISTER MAP
================================================================================

5.1 Global Registers
---------------------

Base Address: DMA_BASE

  +----------+----------+-----------------------------------------------+
  | Offset   | Name     | Description                                   |
  +----------+----------+-----------------------------------------------+
  | 0x000    | DMA_GCR  | Global Control Register                       |
  | 0x004    | DMA_GSR  | Global Status Register                        |
  | 0x008    | DMA_IER  | Interrupt Enable Register                     |
  | 0x00C    | DMA_ISR  | Interrupt Status Register (read)              |
  |          |          | Interrupt Clear Register (write-1-to-clear)   |
  | 0x010    | DMA_IIR  | Interrupt Masked Status Register (read-only)   |
  | 0x014    | DMA_ERR  | Error Status Register                         |
  | 0x018    | DMA_ERRC | Error Clear Register (write-1-to-clear)       |
  | 0x01C    | DMA_VER  | Version Register (read-only)                  |
  | 0x020-   | Reserved |                                               |
  | 0x07C    |          |                                               |
  +----------+----------+-----------------------------------------------+

DMA_GCR - Global Control Register (Offset: 0x000)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [0]   | dma_enable     | R/W | 0     | Global DMA enable (1=enabled)
  [1]   | endian_swap    | R/W | 0     | Endianness (0=little, 1=big)
  [3:2] | reserved       | -   | 0     | Reserved
  [7:4] | clk_gating     | R/W | 0x0   | Per-channel clock gating (bit=1 gated)
  [31:8]| reserved       | -   | 0     | Reserved

DMA_GSR - Global Status Register (Offset: 0x004)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [7:0] | channel_active | R   | 0x00  | Bit per channel (1=transfer active)
  [15:8]| channel_idle   | R   | 0xFF  | Bit per channel (1=IDLE state)
  [31:16] reserved       | -   | 0     | Reserved

DMA_IER - Interrupt Enable Register (Offset: 0x008)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [7:0] | irq_enable     | R/W | 0x00  | Per-channel interrupt enable
  [31:8]| reserved       | -   | 0     | Reserved

DMA_ISR - Interrupt Status Register (Offset: 0x00C)
  Read:  current interrupt status per channel
  Write: write-1-to-clear for each channel interrupt
  Bits  | Field          | R/W   | Reset | Description
  ------+----------------+-------+-------+--------------------------------
  [7:0] | irq_status     | R/W1C | 0x00  | Per-channel interrupt status
  [15:8]| irq_done       | R/W1C | 0x00  | Transfer complete flags
  [23:16]| irq_err       | R/W1C | 0x00  | Transfer error flags
  [31:24] reserved       | -     | 0     | Reserved

DMA_VER - Version Register (Offset: 0x01C)
  Bits  | Field          | R/W | Reset   | Description
  ------+----------------+-----+---------+--------------------------------
  [15:0]| minor          | R   | 0x0001  | Minor version
  [31:16]| major         | R   | 0x0001  | Major version

5.2 Channel Registers
----------------------

Each channel occupies a 64-byte region starting at offset 0x100.

Channel N base offset = 0x100 + (N * 0x40), where N = 0..7

  +----------+----------+-----------------------------------------------+
  | Offset   | Name     | Description                                   |
  +----------+----------+-----------------------------------------------+
  | +0x00    | CH_SAR   | Source Address Register                       |
  | +0x04    | CH_DAR   | Destination Address Register                  |
  | +0x08    | CH_LEN   | Transfer Length (in bytes)                    |
  | +0x0C    | CH_CR    | Channel Control Register                     |
  | +0x10    | CH_SR    | Channel Status Register                      |
  | +0x14    | CH_LLP   | Linked List Pointer (Scatter-Gather)         |
  | +0x18    | CH_BCR   | Byte Count Remaining (read-only)             |
  | +0x1C    | CH_CFG   | Channel Configuration Register               |
  | +0x20-   | Reserved |                                               |
  | +0x3C    |          |                                               |
  +----------+----------+-----------------------------------------------+

CH_SAR - Source Address Register (Offset: +0x00)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [31:0]| src_addr       | R/W | 0     | Source start address (word-aligned)

CH_DAR - Destination Address Register (Offset: +0x04)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [31:0]| dst_addr       | R/W | 0     | Destination start address (word-aligned)

CH_LEN - Transfer Length Register (Offset: +0x08)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [15:0]| xfer_len       | R/W | 0     | Transfer length in bytes (1 - 65536)
  [31:16] reserved       | -   | 0     | Reserved
  Note: Writing 0x0000 means 65536 bytes.

CH_CR - Channel Control Register (Offset: +0x0C)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [0]   | ch_enable      | R/W | 0     | Channel enable (1=start transfer)
  [1]   | ch_done        | R   | 0     | Transfer done flag
  [2]   | ch_pause       | R/W | 0     | Pause transfer (1=paused)
  [3]   | ch_abort       | R/W | 0     | Abort current transfer
  [5:4] | src_mode       | R/W | 0     | Source address mode:
        |                |     |       |   00 = increment
        |                |     |       |   01 = fixed (FIFO)
        |                |     |       |   10 = scatter-gather
        |                |     |       |   11 = reserved
  [7:6] | dst_mode       | R/W | 0     | Destination address mode:
        |                |     |       |   00 = increment
        |                |     |       |   01 = fixed (FIFO)
        |                |     |       |   10 = scatter-gather
        |                |     |       |   11 = reserved
  [8]   | src_per        | R/W | 0     | Source is peripheral (1=yes)
  [9]   | dst_per        | R/W | 0     | Destination is peripheral (1=yes)
  [11:10] src_burst      | R/W | 0     | Source burst length:
        |                |     |       |   00 = 1 beat
        |                |     |       |   01 = 4 beats
        |                |     |       |   10 = 8 beats
        |                |     |       |   11 = 16 beats
  [13:12] dst_burst      | R/W | 0     | Dest burst length (same encoding)
  [15:14] src_width      | R/W | 0     | Source transfer width:
        |                |     |       |   00 = 8 bits (byte)
        |                |     |       |   01 = 16 bits (halfword)
        |                |     |       |   10 = 32 bits (word)
        |                |     |       |   11 = 64 bits (doubleword)
  [17:16] dst_width      | R/W | 0     | Dest transfer width (same encoding)
  [19:18] priority       | R/W | 0     | Channel priority (0=highest, 3=lowest)
  [20]  | int_en         | R/W | 0     | Interrupt on transfer complete
  [21]  | int_err_en     | R/W | 0     | Interrupt on transfer error
  [22]  | sg_en          | R/W | 0     | Scatter-gather enable
  [23]  | cyclic_en      | R/W | 0     | Cyclic (circular) mode enable
  [31:24] reserved       | -   | 0     | Reserved

CH_SR - Channel Status Register (Offset: +0x10)
  Bits  | Field          | R/W   | Reset | Description
  ------+----------------+-------+-------+--------------------------------
  [2:0] | state          | R     | 0     | Current FSM state (encoded)
  [3]   | fifo_empty     | R     | 1     | Channel FIFO empty flag
  [4]   | fifo_full      | R     | 0     | Channel FIFO full flag
  [7:5] | fifo_count     | R     | 0     | FIFO occupancy (0-16)
  [8]   | bus_error      | W1C   | 0     | AXI bus error occurred
  [9]   | align_error    | W1C   | 0     | Address alignment error
  [10]  | desc_error     | W1C   | 0     | Descriptor fetch error
  [11]  | xfer_complete  | W1C   | 0     | Transfer completed
  [31:12] reserved       | -     | 0     | Reserved

CH_LLP - Linked List Pointer (Offset: +0x14)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [31:0]| ll_pointer     | R/W | 0     | Address of next descriptor in memory

CH_BCR - Byte Count Remaining (Offset: +0x18, Read-Only)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [15:0]| bytes_left     | R   | 0     | Remaining bytes to transfer
  [31:16] reserved       | -   | 0     | Reserved

CH_CFG - Channel Configuration Register (Offset: +0x1C)
  Bits  | Field          | R/W | Reset | Description
  ------+----------------+-----+-------+----------------------------------
  [0]   | secure         | R/W | 0     | TrustZone Secure attribute
  [3:1] | prot           | R/W | 0     | AXI protection attributes
  [6:4] | cache          | R/W | 0x3   | AXI cache attributes (default: Modifiable)
  [7]   | fifo_threshold | R/W | 0     | FIFO threshold mode (0=half, 1=quarter)
  [31:8]| reserved       | -   | 0     | Reserved

================================================================================
6. TRANSFER TYPES
================================================================================

6.1 Memory-to-Memory
---------------------

  - Source address: incrementing
  - Destination address: incrementing
  - No peripheral handshake required
  - Channel starts immediately when ch_enable is set
  - Achieves maximum bus bandwidth

  Configuration:
    src_per   = 0,  src_mode = 00 (increment)
    dst_per   = 0,  dst_mode = 00 (increment)

6.2 Memory-to-Peripheral
-------------------------

  - Source address: incrementing (memory buffer)
  - Destination address: fixed (peripheral FIFO/register)
  - Waits for dma_req[N] before writing each data beat/burst

  Configuration:
    src_per   = 0,  src_mode = 00 (increment)
    dst_per   = 1,  dst_mode = 01 (fixed)

6.3 Peripheral-to-Memory
-------------------------

  - Source address: fixed (peripheral FIFO/register)
  - Destination address: incrementing (memory buffer)
  - Waits for dma_req[N] before reading each data beat/burst

  Configuration:
    src_per   = 1,  src_mode = 01 (fixed)
    dst_per   = 0,  dst_mode = 00 (increment)

6.4 Peripheral-to-Peripheral
-----------------------------

  - Source address: fixed (source peripheral)
  - Destination address: fixed (destination peripheral)
  - Waits for source dma_req, then destination dma_req

  Configuration:
    src_per   = 1,  src_mode = 01 (fixed)
    dst_per   = 1,  dst_mode = 01 (fixed)

================================================================================
7. ADDRESS CALCULATION
================================================================================

7.1 Fixed Address
------------------

  The address remains constant throughout the transfer.
  Used for accessing peripheral FIFOs or single registers.

  After each data beat: addr_next = addr_current (no change)

7.2 Incrementing Address
-------------------------

  The address increments by the transfer width after each data beat.

  After each data beat:
    addr_next = addr_current + (transfer_width_in_bytes)

  For a 32-bit transfer width:
    addr_next = addr_current + 4

7.3 Scatter-Gather (Linked List)
---------------------------------

  Descriptors are stored as an array in memory. Each descriptor has the
  following 16-byte structure:

  +--------+----------------------------+
  | Offset | Field                      |
  +--------+----------------------------+
  | +0x00  | Source Address (32 bits)   |
  | +0x04  | Destination Address (32 b) |
  | +0x08  | Control Word (32 bits)     |
  | +0x0C  | Next Descriptor Pointer    |
  +--------+----------------------------+

  Control Word format (within descriptor):
    [15:0]  = transfer length in bytes
    [19:16] = reserved
    [21:20] = src_mode
    [23:22] = dst_mode
    [25:24] = src_burst
    [27:26] = dst_burst
    [29:28] = src_width
    [30]    = interrupt on completion of this descriptor
    [31]    = end of list (1 = last descriptor, stop after this)

  The DMA controller fetches the next descriptor from the address pointed
  to by CH_LLP. If the end-of-list bit is set, the channel returns to IDLE.
  If cyclic_en is set, the controller wraps to the first descriptor.

================================================================================
8. DATA PATH AND FIFO
================================================================================

Each channel contains a 16-entry FIFO that decouples the read and write
phases of a transfer. The FIFO width matches the AXI data bus width.

  +-----------+       +-------+       +-----------+
  | AXI Read  | ----> |  FIFO | ----> | AXI Write |
  |  Master   |       | 16xN  |       |  Master   |
  +-----------+       +-------+       +-----------+

FIFO Operation:
  - Write side: AXI read data is pushed into the FIFO
  - Read side:  AXI write data is popped from the FIFO
  - Flow control: read stalls when FIFO is empty, write stalls when full

FIFO Thresholds:
  - Default: Write begins when FIFO is at least half full (8 entries)
  - Configurable via CH_CFG.fifo_threshold:
      0 = half-full (8 entries for 16-deep FIFO)
      1 = quarter-full (4 entries for 16-deep FIFO)

Data Width Conversion:
  When source and destination widths differ:
  - Narrower-to-wider: Multiple narrow reads fill a single wide write
  - Wider-to-narrower: A single wide read feeds multiple narrow writes

================================================================================
9. INTERRUPT MODEL
================================================================================

Each channel can generate an interrupt under the following conditions:

  +------------------+-----------------------------------------------+
  | Condition        | Description                                   |
  +------------------+-----------------------------------------------+
  | Transfer Done    | All bytes in the transfer have been moved      |
  | Bus Error        | AXI slave returned SLVERR or DECERR           |
  | Alignment Error  | Address not aligned to configured width        |
  | Descriptor Error | Invalid descriptor fetched (null pointer,     |
  |                  | unsupported configuration)                     |
  +------------------+-----------------------------------------------+

Interrupt Flow:
  1. Event occurs on channel N
  2. Corresponding bit set in CH_SR
  3. If the event type is enabled (int_en or int_err_en), bit is set
     in DMA_ISR
  4. If the corresponding bit in DMA_IER is set, irq[N] is asserted
  5. Software reads DMA_ISR to identify the channel and cause
  6. Software clears the interrupt by writing 1 to the corresponding
     bits in DMA_ISR and CH_SR

Interrupt Registers Summary:

  DMA_ISR[7:0]   = Transfer complete pending (per channel)
  DMA_ISR[15:8]  = Transfer error pending (per channel)
  DMA_ISR[23:16] = Raw status before masking
  DMA_IER[7:0]   = Interrupt enable mask
  DMA_IIR[7:0]   = Masked interrupt status (ISR & IER)

================================================================================
10. PROGRAMMING MODEL
================================================================================

10.1 Basic Transfer Sequence (Memory-to-Memory)
-------------------------------------------------

  Step 1: Ensure the channel is idle
    Read CH_SR.state == 0 (IDLE)

  Step 2: Program the transfer parameters
    Write CH_SAR  = source_address
    Write CH_DAR  = destination_address
    Write CH_LEN  = transfer_length_in_bytes
    Write CH_CR   = {int_en=1, src_mode=00, dst_mode=00, src_burst, dst_burst, ...}

  Step 3: Enable global DMA
    Write DMA_GCR = {dma_enable=1, ...}

  Step 4: Start the channel
    Write CH_CR.ch_enable = 1

  Step 5: Wait for completion
    Poll DMA_ISR or wait for irq[N] interrupt

  Step 6: Clear interrupt and check status
    Read  CH_SR  (check for errors)
    Write CH_SR  = {xfer_complete=1, ...} (clear flags)
    Write DMA_ISR = (1 << N) (clear interrupt)

10.2 Scatter-Gather Transfer Sequence
---------------------------------------

  Step 1: Prepare descriptor chain in memory
    For each descriptor:
      Write desc[i].src_addr, desc[i].dst_addr, desc[i].control, desc[i].next
    Set desc[last].control[31] = 1 (end of list)

  Step 2: Program channel
    Write CH_LLP = &desc[0]  (address of first descriptor)
    Write CH_CR  = {sg_en=1, int_en=1, ...}

  Step 3: Enable and start
    Write DMA_GCR.dma_enable = 1
    Write CH_CR.ch_enable = 1

  Step 4: The controller fetches each descriptor and executes the
          transfer automatically, proceeding through the linked list.

  Step 5: On end-of-list descriptor, the channel returns to IDLE and
          generates an interrupt (if enabled).

================================================================================
11. CLOCK AND RESET
================================================================================

Clock:
  - Single clock domain: axi_clk
  - All registers and state machines are synchronous to axi_clk
  - Peripheral interface signals (dma_req/ack/eop) must be synchronous
    to axi_clk

Reset:
  - axi_rst_n: Active-low asynchronous reset
  - Reset action:
      * All channels return to IDLE state
      * All registers reset to default values (see Section 5)
      * All FIFOs are flushed
      * All interrupts are deasserted (irq = 0)
      * AXI master interfaces are quiesced (no outstanding transactions)
  - Reset duration: Minimum 16 axi_clk cycles
  - After reset deassertion, the DMA controller requires 4 clock cycles
    before it can accept register accesses

Clock Gating:
  - DMA_GCR.clk_gating[N] = 1 disables the clock to channel N
  - A channel must be in IDLE state before its clock is gated
  - Writing to registers of a clock-gated channel returns a DECERR
    on the AXI-Lite slave interface

================================================================================
12. BUS PROTOCOL DETAILS
================================================================================

12.1 AXI Master Interface
--------------------------

  - Protocol: AXI4 (full)
  - Data width: Configurable (32, 64, or 128 bits via parameter)
  - ID width: 4 bits (channel ID used as transaction ID)
  - Outstanding transactions: Up to 4 per channel
  - Burst type: INCR (incrementing) for memory, FIXED for FIFO
  - Maximum burst length: 16 beats (256 bytes for 128-bit width)
  - Exclusive access: Not supported
  - Locked access: Not supported
  - QoS: Not supported (all transactions use QoS=0)

  Cache attributes (set via CH_CFG.cache):
    Default = 0x3 (Modifiable, Bufferable) for memory transactions
    Forced  = 0x0 (Non-modifiable, Non-bufferable) for peripheral access

  Protection attributes (set via CH_CFG.prot):
    Bit [0]: Privilege level (0=unprivileged, 1=privileged)
    Bit [1]: Secure (0=secure, 1=non-secure)
    Bit [2]: Instruction/Data (0=data, 1=instruction)

12.2 AXI Slave (Register) Interface
-------------------------------------

  - Protocol: AXI4-Lite
  - Data width: 32 bits
  - Address width: 12 bits (4 KB address space)
  - Protection: Checked against CH_CFG.secure for TrustZone
  - Response codes:
      OKAY   = Normal access
      SLVERR = Attempted access to clock-gated channel
      DECERR = Attempted access to non-existent register

================================================================================
13. ERROR HANDLING
================================================================================

The DMA controller detects and reports the following error conditions:

  +--------------------+-----------------------------------------------+
  | Error Type         | Action                                        |
  +--------------------+-----------------------------------------------+
  | AXI Read SLVERR    | Channel enters ERROR state.                   |
  |                    | CH_SR.bus_error = 1.                          |
  |                    | Current transfer is aborted.                  |
  +--------------------+-----------------------------------------------+
  | AXI Read DECERR    | Same as SLVERR. Decode error at address.      |
  +--------------------+-----------------------------------------------+
  | AXI Write SLVERR   | Same as read SLVERR.                          |
  +--------------------+-----------------------------------------------+
  | AXI Write DECERR   | Same as read DECERR.                          |
  +--------------------+-----------------------------------------------+
  | Alignment Error    | Source or destination address is not aligned  |
  |                    | to the configured transfer width.             |
  |                    | CH_SR.align_error = 1.                        |
  |                    | Transfer is aborted before starting.          |
  +--------------------+-----------------------------------------------+
  | Descriptor Error   | Fetched descriptor has invalid configuration  |
  |                    | or null pointer.                              |
  |                    | CH_SR.desc_error = 1.                        |
  |                    | Scatter-gather chain is terminated.           |
  +--------------------+-----------------------------------------------+
  | Length Error       | Transfer length of 0 with scatter-gather     |
  |                    | descriptor that is not end-of-list.           |
  +--------------------+-----------------------------------------------+

Error Recovery:
  1. Software reads CH_SR to identify the error type
  2. Software clears error flags by writing CH_SR (W1C)
  3. Software can optionally reprogram the channel and restart
  4. The channel must be explicitly re-enabled (ch_enable = 1)

================================================================================
14. SECURITY AND PROTECTION
================================================================================

TrustZone Support:
  - Each channel has a secure attribute (CH_CFG.secure)
  - When secure=1, the channel generates Secure AXI transactions
  - Non-secure register access to a secure channel returns SLVERR
  - The global DMA_GCR can only be written by Secure transactions

AXI Protection:
  - CH_CFG.prot[2:0] sets the AXI ArProt/AwProt for all transactions
    issued by the channel
  - Default prot = 000 (unprivileged, secure, data access)

Access Permissions:
  - Only Secure bus transactions can program Secure channels
  - Non-secure bus transactions can only program Non-secure channels
  - Attempted cross-domain access results in SLVERR response

================================================================================
15. POWER MANAGEMENT
================================================================================

Clock Gating:
  - Individual channel clock gating via DMA_GCR.clk_gating
  - Unused channels should be clock-gated to save power

Software Clock Gating Procedure:
  1. Wait for channel to reach IDLE state (CH_SR.state == 0)
  2. Set DMA_GCR.clk_gating[N] = 1
  3. Channel N is now clock-gated

Software Ungating Procedure:
  1. Clear DMA_GCR.clk_gating[N] = 0
  2. Wait 2 clock cycles for the clock to stabilize
  3. Channel N is now active and can be programmed

Dynamic Power:
  - The FIFO in each channel uses clock gating on empty entries
  - The arbiter powers down when no channels are active

================================================================================
16. VERIFICATION PLAN
================================================================================

16.1 Test Categories
---------------------

  Category 1: Register Access
    - Read/write all global registers
    - Read/write all channel registers
    - Verify reset values
    - Verify W1C behavior on status registers
    - Verify read-only fields cannot be written
    - Verify AXI-Lite protocol compliance

  Category 2: Memory-to-Memory Transfers
    - Single beat transfer (1 byte, 2 bytes, 4 bytes, 8 bytes)
    - Multi-beat INCR burst transfers
    - Maximum length transfer (65536 bytes)
    - Various source/destination address alignments
    - Different transfer widths and burst configurations
    - Back-to-back transfers on same channel
    - Simultaneous transfers on different channels

  Category 3: Peripheral Transfers
    - Memory-to-Peripheral with dma_req/ack handshake
    - Peripheral-to-Memory with dma_req/ack handshake
    - Peripheral-to-Peripheral transfers
    - Single-beat peripheral request
    - Burst peripheral request
    - End-of-packet (dma_eop) handling

  Category 4: Scatter-Gather
    - Single descriptor chain (2-16 descriptors)
    - Descriptor chain with varying transfer sizes
    - Mixed address modes across descriptors
    - End-of-list termination
    - Invalid descriptor handling (null pointer)
    - Cyclic scatter-gather mode

  Category 5: Interrupts
    - Transfer complete interrupt generation
    - Error interrupt generation
    - Interrupt enable/disable masking
    - Interrupt clearing (W1C)
    - Simultaneous interrupts on multiple channels

  Category 6: Error Handling
    - AXI SLVERR on read
    - AXI SLVERR on write
    - AXI DECERR on read
    - AXI DECERR on write
    - Alignment error detection
    - Descriptor error detection
    - Error recovery and channel restart

  Category 7: Arbitration and Priority
    - Two channels with same priority (round-robin)
    - Higher priority channel preempts lower
    - Priority change during active transfer
    - All 8 channels active simultaneously

  Category 8: Corner Cases
    - Zero-length transfer
    - Maximum-length transfer
    - Transfer abort during active transfer
    - Transfer pause and resume
    - Reset during active transfer
    - Clock gating/ungating during various states

16.2 Coverage Goals
--------------------

  - 100% register bit coverage (all bits read and written)
  - 100% FSM state coverage per channel
  - 100% FSM state transition coverage
  - 100% FIFO state coverage (empty, full, all depths)
  - 95%+ toggle coverage on all ports
  - All transfer type combinations (4 types x 4 address modes)
  - All burst length and width combinations

16.3 Assertions
----------------

  - AXI4-Lite protocol assertions (handshake rules)
  - AXI4 master protocol assertions (handshake, burst rules)
  - FIFO overflow/underflow never occurs
  - Interrupt asserted only when enabled
  - Channel FSM transitions are legal
  - Byte count remaining never exceeds initial transfer length
  - Write data matches read data (for mem-to-mem loopback)

================================================================================
17. PERFORMANCE TARGETS
================================================================================

  +----------------------------------+----------------------------------+
  | Metric                           | Target                           |
  +----------------------------------+----------------------------------+
  | Maximum bus bandwidth            | > 95% of theoretical AXI         |
  |                                  | bandwidth (mem-to-mem)           |
  +----------------------------------+----------------------------------+
  | Latency: channel start to first  | < 8 clock cycles                 |
  | AXI read address                 |                                  |
  +----------------------------------+----------------------------------+
  | Latency: dma_req to dma_ack      | < 4 clock cycles                 |
  +----------------------------------+----------------------------------+
  | Maximum operating frequency      | >= 200 MHz (45nm LP process)     |
  +----------------------------------+----------------------------------+
  | Gate count (8-channel, 32-bit)   | < 25K gates                      |
  +----------------------------------+----------------------------------+
  | Gate count (8-channel, 128-bit)  | < 60K gates                      |
  +----------------------------------+----------------------------------+
  | Max outstanding AXI transactions | 4 per channel, 8 total           |
  +----------------------------------+----------------------------------+

================================================================================
18. REVISION HISTORY
================================================================================

  +-------+------------+----------------------------------------------+
  | Ver   | Date       | Description                                  |
  +-------+------------+----------------------------------------------+
  | 1.0   | 2025       | Initial specification                         |
  +-------+------------+----------------------------------------------+

================================================================================
                         END OF SPECIFICATION
================================================================================
