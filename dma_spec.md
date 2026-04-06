# DMA Controller RTL Specification

## Overview
A simple DMA (Direct Memory Access) controller that transfers data between memory-mapped peripherals and system memory without CPU intervention.

## Module: dma_top

### Parameters
- DATA_WIDTH: 32 (default)
- ADDR_WIDTH: 32 (default)
- BURST_LEN: 16 (default)

### Ports

#### Clock & Reset
- clk          : input  - System clock
- rst_n        : input  - Active-low reset

#### Bus Master Interface (AXI4-Lite compatible)
- m_awaddr     : output [ADDR_WIDTH-1:0] - Write address
- m_awprot     : output [2:0]            - Write protection
- m_awvalid    : output                   - Write address valid
- m_awready    : input                    - Write address ready
- m_wdata      : output [DATA_WIDTH-1:0]  - Write data
- m_wstrb      : output [DATA_WIDTH/8-1:0]- Write strobe
- m_wvalid     : output                   - Write data valid
- m_wready     : input                    - Write data ready
- m_bresp      : input [1:0]             - Write response
- m_bvalid     : input                    - Write response valid
- m_bready     : output                   - Write response ready
- m_araddr     : output [ADDR_WIDTH-1:0]  - Read address
- m_arprot     : output [2:0]            - Read protection
- m_arvalid    : output                   - Read address valid
- m_arready    : input                    - Read address ready
- m_rdata      : input [DATA_WIDTH-1:0]   - Read data
- m_rresp      : input [1:0]             - Read response
- m_rvalid     : input                    - Read data valid
- m_rready     : output                   - Read data ready

#### Register Interface (CPU config)
- reg_wdata    : input [DATA_WIDTH-1:0]   - Register write data
- reg_waddr    : input [7:0]              - Register write address
- reg_we       : input                    - Register write enable
- reg_rdata    : output [DATA_WIDTH-1:0]  - Register read data
- reg_raddr    : input [7:0]              - Register read address
- reg_re       : input                    - Register read enable

#### Interrupt
- irq_done     : output                   - Transfer complete interrupt
- irq_err      : output                   - Transfer error interrupt

### Registers (offset map)
| Offset | Name       | Description                     |
|--------|------------|---------------------------------|
| 0x00   | SRC_ADDR   | Source address for transfer      |
| 0x04   | DST_ADDR   | Destination address for transfer |
| 0x08   | XFER_LEN   | Transfer length in bytes         |
| 0x0C   | CTRL       | Control register                 |
| 0x10   | STATUS     | Status register (read-only)      |

#### CTRL Register (0x0C)
- [0]     START    - Start transfer (auto-clear)
- [1]     STOP     - Stop/abort transfer
- [2]     INT_EN   - Interrupt enable
- [4:3]   MODE     - 00=memory-to-memory, 01=peripheral-to-memory, 10=memory-to-peripheral
- [31:16] BURST    - Burst size override

#### STATUS Register (0x10)
- [0]     BUSY     - Transfer in progress
- [1]     DONE     - Transfer completed
- [2]     ERR      - Transfer error
- [7:4]   XFER_CNT - Bytes transferred (high bits)

### FSM States
1. IDLE      - Waiting for START command
2. READ_REQ  - Issuing read address on bus
3. READ_DATA - Receiving read data
4. WRITE_REQ - Issuing write address on bus
5. WRITE_DATA- Sending write data
6. WRITE_RESP- Waiting for write response
7. COMPLETE  - Transfer done, assert IRQ

### Sub-modules
1. dma_ctrl     - Main FSM and control logic
2. dma_reg      - Register file with R/W access
3. dma_axi_m    - AXI4-Lite master interface adapter
4. dma_irq      - Interrupt generation logic

### Implementation Requirements
- All transfers are burst-capable
- Support unaligned addresses
- Error handling with retry counter (max 3 retries)
- Byte-level strobes for partial writes
- Configurable burst length via register
