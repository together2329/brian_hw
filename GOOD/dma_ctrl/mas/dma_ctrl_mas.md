# DMA Controller — Micro Architecture Spec

## 1. Overview

The DMA Controller (`dma_ctrl`) is a multi-channel Direct Memory Access IP core that offloads the processor by autonomously moving data between memory-mapped sources and destinations without CPU intervention. It provides **8 independent channels**, each with a dedicated FSM, a 16-entry data FIFO, and per-channel interrupt generation. The controller connects to the SoC interconnect via an **AXI4 master interface** (configurable 32/64/128-bit data width) for data transfers and an **AXI4-Lite slave interface** for register programming. Supported transfer types include Memory-to-Memory, Memory-to-Peripheral, Peripheral-to-Memory, and Peripheral-to-Peripheral, with address modes covering fixed (FIFO), incrementing (linear buffer), and scatter-gather linked-list descriptors. Key design goals include achieving **>95% of theoretical AXI bandwidth** for memory-to-memory transfers, **<8 clock cycle latency** from channel enable to first AXI read address, **<4 clock cycle latency** from `dma_req` to `dma_ack`, and a maximum operating frequency of **≥200 MHz** in a 45 nm LP process, with a gate count target of **<25K gates** (32-bit, 8-channel) or **<60K gates** (128-bit, 8-channel).

## 2. Module Hierarchy

```
dma_ctrl
├── dma_reg_block          # AXI4-Lite slave register decode + per-channel registers
├── dma_channel_manager    # Channel array wrapper
│   ├── dma_channel [0]    # Channel 0: FSM + FIFO + address gen
│   ├── dma_channel [1]
│   ├── ...
│   └── dma_channel [7]
├── dma_arbiter            # Priority arbiter / mux among active channels
├── dma_axi_master         # AXI4 master read/write interface
└── dma_int_ctrl           # Interrupt controller (per-channel, global masking)
```

### Interface (Ports)

#### Clock and Reset

| Name      | Width | Dir | Clock Domain | Description                  |
|-----------|-------|-----|--------------|------------------------------|
| axi_clk   | 1     | in  | —            | AXI bus clock                |
| axi_rst_n | 1     | in  | —            | Active-low asynchronous reset|

#### AXI4-Lite Slave Interface (Register Programming)

| Name            | Width  | Dir | Clock Domain | Description                       |
|-----------------|--------|-----|--------------|-----------------------------------|
| s_axi_awaddr    | 12     | in  | axi_clk      | AXI-Lite slave write address      |
| s_axi_awprot    | 3      | in  | axi_clk      | AXI-Lite slave write protection   |
| s_axi_awvalid   | 1      | in  | axi_clk      | AXI-Lite slave write addr valid   |
| s_axi_awready   | 1      | out | axi_clk      | AXI-Lite slave write addr ready   |
| s_axi_wdata     | 32     | in  | axi_clk      | AXI-Lite slave write data         |
| s_axi_wstrb     | 4      | in  | axi_clk      | AXI-Lite slave write strobe       |
| s_axi_wvalid    | 1      | in  | axi_clk      | AXI-Lite slave write valid        |
| s_axi_wready    | 1      | out | axi_clk      | AXI-Lite slave write ready        |
| s_axi_bresp     | 2      | out | axi_clk      | AXI-Lite slave write response     |
| s_axi_bvalid    | 1      | out | axi_clk      | AXI-Lite slave write resp valid   |
| s_axi_bready    | 1      | in  | axi_clk      | AXI-Lite slave write resp ready   |
| s_axi_araddr    | 12     | in  | axi_clk      | AXI-Lite slave read address       |
| s_axi_arprot    | 3      | in  | axi_clk      | AXI-Lite slave read protection    |
| s_axi_arvalid   | 1      | in  | axi_clk      | AXI-Lite slave read addr valid    |
| s_axi_arready   | 1      | out | axi_clk      | AXI-Lite slave read addr ready    |
| s_axi_rdata     | 32     | out | axi_clk      | AXI-Lite slave read data          |
| s_axi_rresp     | 2      | out | axi_clk      | AXI-Lite slave read response      |
| s_axi_rvalid    | 1      | out | axi_clk      | AXI-Lite slave read valid         |
| s_axi_rready    | 1      | in  | axi_clk      | AXI-Lite slave read ready         |

#### AXI4 Master Interface (Data Transfers)

| Name            | Width          | Dir  | Clock Domain | Description                      |
|-----------------|----------------|------|--------------|----------------------------------|
| m_axi_awid      | 4              | out  | axi_clk      | AXI master write address ID      |
| m_axi_awaddr    | 32             | out  | axi_clk      | AXI master write address         |
| m_axi_awlen     | 8              | out  | axi_clk      | AXI master write burst length    |
| m_axi_awsize    | 3              | out  | axi_clk      | AXI master write burst size      |
| m_axi_awburst   | 2              | out  | axi_clk      | AXI master write burst type      |
| m_axi_awprot    | 3              | out  | axi_clk      | AXI master write protection      |
| m_axi_awcache   | 4              | out  | axi_clk      | AXI master write cache           |
| m_axi_awvalid   | 1              | out  | axi_clk      | AXI master write addr valid      |
| m_axi_awready   | 1              | in   | axi_clk      | AXI master write addr ready      |
| m_axi_wdata     | DATA_WIDTH     | out  | axi_clk      | AXI master write data            |
| m_axi_wstrb     | DATA_WIDTH/8   | out  | axi_clk      | AXI master write strobe          |
| m_axi_wlast     | 1              | out  | axi_clk      | AXI master write last            |
| m_axi_wvalid    | 1              | out  | axi_clk      | AXI master write valid           |
| m_axi_wready    | 1              | in   | axi_clk      | AXI master write ready           |
| m_axi_bid       | 4              | in   | axi_clk      | AXI master write response ID     |
| m_axi_bresp     | 2              | in   | axi_clk      | AXI master write response        |
| m_axi_bvalid    | 1              | in   | axi_clk      | AXI master write resp valid      |
| m_axi_bready    | 1              | out  | axi_clk      | AXI master write resp ready      |
| m_axi_arid      | 4              | out  | axi_clk      | AXI master read address ID       |
| m_axi_araddr    | 32             | out  | axi_clk      | AXI master read address          |
| m_axi_arlen     | 8              | out  | axi_clk      | AXI master read burst length     |
| m_axi_arsize    | 3              | out  | axi_clk      | AXI master read burst size       |
| m_axi_arburst   | 2              | out  | axi_clk      | AXI master read burst type       |
| m_axi_arprot    | 3              | out  | axi_clk      | AXI master read protection       |
| m_axi_arcache   | 4              | out  | axi_clk      | AXI master read cache            |
| m_axi_arvalid   | 1              | out  | axi_clk      | AXI master read addr valid       |
| m_axi_arready   | 1              | in   | axi_clk      | AXI master read addr ready       |
| m_axi_rid       | 4              | in   | axi_clk      | AXI master read ID               |
| m_axi_rdata     | DATA_WIDTH     | in   | axi_clk      | AXI master read data             |
| m_axi_rresp     | 2              | in   | axi_clk      | AXI master read response         |
| m_axi_rlast     | 1              | in   | axi_clk      | AXI master read last             |
| m_axi_rvalid    | 1              | in   | axi_clk      | AXI master read valid            |
| m_axi_rready    | 1              | out  | axi_clk      | AXI master read ready            |

#### Peripheral DMA Request Interface

| Name       | Width | Dir  | Clock Domain | Description                      |
|------------|-------|------|--------------|----------------------------------|
| dma_req    | 8     | in   | axi_clk      | Per-channel DMA request          |
| dma_ack    | 8     | out  | axi_clk      | Per-channel DMA acknowledge      |
| dma_eop    | 8     | in   | axi_clk      | Per-channel end-of-packet        |

#### Interrupt Interface

| Name | Width | Dir  | Clock Domain | Description              |
|------|-------|------|--------------|--------------------------|
| irq  | 8     | out  | axi_clk      | Per-channel interrupt    |

### Parameters

| Name          | Default | Description                                          |
|---------------|---------|------------------------------------------------------|
| DATA_WIDTH    | 32      | AXI data bus width: 32, 64, or 128 bits              |
| ADDR_WIDTH    | 32      | AXI address width                                    |
| ID_WIDTH      | 4       | AXI transaction ID width (channel ID used as ID)     |
| NUM_CHANNELS  | 8       | Number of independent DMA channels                   |
| FIFO_DEPTH    | 16      | Per-channel data FIFO depth (in data beats)          |
| MAX_BURST_LEN | 16      | Maximum AXI burst length in beats                    |

## 3. Feature Operation

### Feature A: Memory-to-Memory Transfer

- **Trigger**: `CH_CR.ch_enable` is set while `src_per=0`, `dst_per=0`, `src_mode=00` (increment), `dst_mode=00` (increment). Global `DMA_GCR.dma_enable=1`.
- **Datapath**:
  1. Channel FSM transitions IDLE → READ_ADDR.
  2. AXI master issues INCR burst read from `CH_SAR` (source address increments by transfer width per beat).
  3. Read data is pushed into the per-channel FIFO.
  4. When FIFO threshold is reached (8 entries by default, or 4 per `CH_CFG.fifo_threshold`), FSM transitions to WRITE_ADDR.
  5. AXI master issues INCR burst write to `CH_DAR` (destination address increments by transfer width per beat).
  6. Data is popped from FIFO and driven on `m_axi_wdata`.
  7. Steps repeat until `CH_BCR.bytes_left=0`.
- **Control**: FSM states READ_ADDR → READ_DATA → WRITE_ADDR → WRITE_DATA → WRITE_RESP. No peripheral handshake required.
- **Output**: Data at `CH_DAR`..`CH_DAR+CH_LEN-1` matches source. `CH_SR.xfer_complete=1`, `irq[N]` asserted if `CH_CR.int_en=1`.

### Feature B: Memory-to-Peripheral Transfer

- **Trigger**: `CH_CR.ch_enable` set with `src_per=0`, `dst_per=1`, `src_mode=00` (increment), `dst_mode=01` (fixed). Global `DMA_GCR.dma_enable=1`.
- **Datapath**:
  1. Channel FSM transitions IDLE → READ_ADDR.
  2. AXI master reads from incrementing source address (`CH_SAR`).
  3. Data fills the per-channel FIFO.
  4. FSM waits in WAIT_REQ for peripheral to assert `dma_req[N]`.
  5. On `dma_req[N]=1`, FSM transitions to WRITE_ADDR → WRITE_DATA.
  6. AXI master writes to fixed destination address (`CH_DAR`, using FIXED burst type) — peripheral FIFO/register.
  7. `dma_ack[N]` is asserted to acknowledge the peripheral.
  8. Repeat until transfer complete or `dma_eop[N]` asserted.
- **Control**: FSM includes WAIT_REQ state between write phases. AXI AW channel uses burst type FIXED.
- **Output**: Data written to peripheral at `CH_DAR`. `dma_ack[N]` pulsed for each granted transfer. `CH_SR.xfer_complete=1` on completion.

### Feature C: Peripheral-to-Memory Transfer

- **Trigger**: `CH_CR.ch_enable` set with `src_per=1`, `dst_per=0`, `src_mode=01` (fixed), `dst_mode=00` (increment). Global `DMA_GCR.dma_enable=1`.
- **Datapath**:
  1. Channel FSM transitions IDLE → WAIT_REQ.
  2. Waits for peripheral to assert `dma_req[N]`.
  3. On `dma_req[N]=1`, FSM transitions to READ_ADDR → READ_DATA.
  4. AXI master reads from fixed source address (`CH_SAR`, FIXED burst) — peripheral FIFO/register.
  5. `dma_ack[N]` asserted to acknowledge the peripheral.
  6. Data is pushed into the per-channel FIFO.
  7. When FIFO threshold reached, FSM transitions to WRITE_ADDR → WRITE_DATA → WRITE_RESP.
  8. AXI master writes to incrementing destination (`CH_DAR`).
  9. Repeat until transfer complete or `dma_eop[N]` asserted.
- **Control**: FSM starts in WAIT_REQ. AXI AR channel uses burst type FIXED.
- **Output**: Data from peripheral stored in memory buffer at `CH_DAR`..`CH_DAR+CH_LEN-1`. `dma_ack[N]` pulsed. `CH_SR.xfer_complete=1`.

### Feature D: Peripheral-to-Peripheral Transfer

- **Trigger**: `CH_CR.ch_enable` set with `src_per=1`, `dst_per=1`, `src_mode=01` (fixed), `dst_mode=01` (fixed). Global `DMA_GCR.dma_enable=1`.
- **Datapath**:
  1. FSM transitions IDLE → WAIT_REQ.
  2. Waits for source peripheral `dma_req[N]`.
  3. On `dma_req[N]=1`, reads from fixed `CH_SAR` (AXI FIXED burst).
  4. Asserts `dma_ack[N]` to source peripheral.
  5. Data pushed to per-channel FIFO.
  6. Waits for destination peripheral `dma_req[N]` (or uses same channel req if single handshake).
  7. Writes to fixed `CH_DAR` (AXI FIXED burst).
  8. Asserts `dma_ack[N]` to destination peripheral.
  9. Repeat until complete or `dma_eop[N]`.
- **Control**: Both read and write AXI channels use FIXED burst type. Two wait phases for source and destination handshakes.
- **Output**: Data moved from source peripheral to destination peripheral. `dma_ack[N]` asserted for both read and write phases. `CH_SR.xfer_complete=1`.

### Feature E: Scatter-Gather (Linked List)

- **Trigger**: `CH_CR.ch_enable` set with `CH_CR.sg_en=1`. `CH_LLP` points to first descriptor in memory. Global `DMA_GCR.dma_enable=1`.
- **Datapath**:
  1. FSM transitions IDLE → DESC_FETCH.
  2. AXI master reads 16-byte descriptor from `CH_LLP` address.
  3. Descriptor fields extracted:
     - `desc[31:0]` → source address
     - `desc[63:32]` → destination address
     - `desc[95:64]` → control word
     - `desc[127:96]` → next descriptor pointer
  4. Control word format:
     | Bits    | Field        | Description                               |
     |---------|--------------|-------------------------------------------|
     | [15:0]  | xfer_len     | Transfer length in bytes                  |
     | [19:16] | reserved     | Reserved                                  |
     | [21:20] | src_mode     | Source address mode                       |
     | [23:22] | dst_mode     | Destination address mode                  |
     | [25:24] | src_burst    | Source burst length                       |
     | [27:26] | dst_burst    | Dest burst length                         |
     | [29:28] | src_width    | Source transfer width                     |
     | [30]    | int_on_done  | Interrupt on completion of this descriptor|
     | [31]    | end_of_list  | Last descriptor (1 = stop after this)     |
  5. FSM transitions DESC_FETCH → READ_ADDR and executes the transfer as per the descriptor configuration.
  6. When transfer completes, if `end_of_list=0`: load `CH_LLP` with next descriptor pointer, go to DESC_FETCH.
  7. If `end_of_list=1`: FSM transitions to COMPLETE → IDLE.
  8. If `CH_CR.cyclic_en=1`: instead of stopping, wrap to the first descriptor (circular).
- **Control**: DESC_FETCH state inserted before READ_ADDR. Descriptor loaded from memory via AXI master read.
- **Output**: Multiple blocks transferred automatically. Interrupt optionally generated per-descriptor if `int_on_done=1`.

### Feature F: Cyclic Mode

- **Trigger**: `CH_CR.cyclic_en=1` and `CH_CR.sg_en=1`. The descriptor chain must form a ring (last descriptor's next pointer points to the first descriptor, or `end_of_list` causes wrap to first).
- **Datapath**: Same as scatter-gather, but after the last descriptor completes, the controller wraps to the first descriptor and continues indefinitely.
- **Control**: No IDLE transition. FSM loops DESC_FETCH → transfer → DESC_FETCH indefinitely until `CH_CR.ch_abort=1` or `DMA_GCR.dma_enable=0`.
- **Output**: Continuous circular buffer transfers. Useful for audio/ streaming peripherals.

### Feature G: Pause and Abort

- **Trigger**:
  - **Pause**: Software writes `CH_CR.ch_pause=1` during an active transfer.
  - **Abort**: Software writes `CH_CR.ch_abort=1` during an active transfer.
- **Datapath**:
  - **Pause**: Channel FSM stops issuing new AXI transactions. In-flight transactions complete. FIFO is allowed to drain. No data loss. Transfer resumes when `ch_pause` is cleared.
  - **Abort**: Channel FSM immediately enters ERROR state. Outstanding AXI transactions may complete or be dropped. FIFO is flushed. `CH_SR.xfer_complete` is not set.
- **Control**: Pause gates the FSM state advancement. Abort forces transition to ERROR state from any state.
- **Output**: Pause — transfer suspends, `CH_BCR.bytes_left` holds. Abort — `CH_SR` error flags set, channel returns to IDLE after software clears error and re-enables.

### Address Calculation

#### Fixed Address
- Address remains constant throughout the transfer.
- Used for peripheral FIFO/register access.
- `addr_next = addr_current` (no change)

#### Incrementing Address
- Address increments by the transfer width after each data beat.
- `addr_next = addr_current + (transfer_width_in_bytes)`
- For 8-bit width: `+1`; 16-bit: `+2`; 32-bit: `+4`; 64-bit: `+8`

#### Scatter-Gather Address
- Source and destination addresses come from the descriptor.
- Each descriptor specifies its own `src_addr` and `dst_addr`.
- Within a single descriptor's transfer, the address mode (fixed or incrementing) applies as configured in the descriptor's control word.

### Control FSM

| State       | Next State   | Condition                          | Output Actions                                              |
|-------------|-------------|------------------------------------|-------------------------------------------------------------|
| IDLE        | DESC_FETCH  | `ch_enable=1` AND `sg_en=1`       | Load LLP into descriptor fetch address                      |
| IDLE        | WAIT_REQ    | `ch_enable=1` AND `src_per=1`     | Assert channel active in DMA_GSR                            |
| IDLE        | READ_ADDR   | `ch_enable=1` AND mem-to-mem      | Issue AXI AR request for source address                     |
| DESC_FETCH  | READ_ADDR   | Descriptor loaded successfully    | Parse descriptor → update SAR, DAR, LEN, control            |
| DESC_FETCH  | ERROR       | Null pointer or invalid desc      | Set `CH_SR.desc_error=1`                                    |
| WAIT_REQ    | READ_ADDR   | `dma_req[N]=1`                    | Assert `dma_ack[N]`, issue AXI AR request                   |
| READ_ADDR   | READ_DATA   | `m_axi_arready=1`                 | Latch AXI read address, drive ARVALID=0                     |
| READ_DATA   | WRITE_ADDR  | FIFO threshold reached OR read done | Push data into FIFO, prepare write address                |
| READ_DATA   | READ_ADDR   | More beats in burst AND FIFO not full | Continue receiving read data                             |
| WRITE_ADDR  | WRITE_DATA  | `m_axi_awready=1`                 | Latch AXI write address, drive AWVALID=0                    |
| WRITE_DATA  | WRITE_RESP  | `m_axi_wlast=1` AND `m_axi_wready=1` | Pop data from FIFO, drive on WDATA                       |
| WRITE_RESP  | READ_ADDR   | More data to transfer             | Continue with next read burst                               |
| WRITE_RESP  | COMPLETE    | All bytes transferred             | —                                                           |
| COMPLETE    | IDLE        | Acknowledge (1 cycle)             | Set `CH_SR.xfer_complete=1`, set `CH_CR.ch_done=1`, assert irq if enabled |
| ERROR       | IDLE        | Software clears errors + re-enable | Clear CH_SR error flags, re-enable channel                 |
| ANY_STATE   | ERROR       | Bus error (SLVERR/DECERR) OR alignment error | Set `CH_SR.bus_error` or `CH_SR.align_error`, abort transfer |
| ANY_STATE   | —           | `ch_pause=1`                       | Freeze FSM advancement (in-flight AXI completes)            |
| ANY_STATE   | ERROR       | `ch_abort=1`                       | Force ERROR state, flush FIFO                               |

## 4. Registers (FAM — Functional Address Map)

### Global Registers

Base Address: `DMA_BASE`

| Offset | Name     | Width | Access   | Reset     | Description                                    |
|--------|----------|-------|----------|-----------|------------------------------------------------|
| 0x000  | DMA_GCR  | 32    | RW       | 0x00000000 | Global Control Register                        |
| 0x004  | DMA_GSR  | 32    | RO       | 0x0000FF00 | Global Status Register                         |
| 0x008  | DMA_IER  | 32    | RW       | 0x00000000 | Interrupt Enable Register                      |
| 0x00C  | DMA_ISR  | 32    | R/W1C    | 0x00000000 | Interrupt Status Register (R) / Clear (W1C)    |
| 0x010  | DMA_IIR  | 32    | RO       | 0x00000000 | Interrupt Masked Status Register (read-only)   |
| 0x014  | DMA_ERR  | 32    | RO       | 0x00000000 | Error Status Register                          |
| 0x018  | DMA_ERRC | 32    | W1C      | 0x00000000 | Error Clear Register                           |
| 0x01C  | DMA_VER  | 32    | RO       | 0x00010001 | Version Register (read-only)                   |

#### DMA_GCR — Global Control Register (Offset: 0x000)

| Bits    | Name        | Access | Reset | Description                                      |
|---------|-------------|--------|-------|--------------------------------------------------|
| [0]     | dma_enable  | RW     | 0     | Global DMA enable (1=enabled)                    |
| [1]     | endian_swap | RW     | 0     | Endianness (0=little-endian, 1=big-endian)       |
| [3:2]   | reserved    | —      | 0     | Reserved                                         |
| [7:4]   | clk_gating  | RW     | 0x0   | Per-channel clock gating (bit N=1 gates channel N)|
| [31:8]  | reserved    | —      | 0     | Reserved                                         |

#### DMA_GSR — Global Status Register (Offset: 0x004)

| Bits    | Name          | Access | Reset | Description                                    |
|---------|---------------|--------|-------|------------------------------------------------|
| [7:0]   | channel_active| RO     | 0x00  | Bit per channel (1=transfer active)            |
| [15:8]  | channel_idle  | RO     | 0xFF  | Bit per channel (1=IDLE state)                 |
| [31:16] | reserved      | —      | 0     | Reserved                                       |

#### DMA_IER — Interrupt Enable Register (Offset: 0x008)

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [7:0]   | irq_enable  | RW     | 0x00  | Per-channel interrupt enable                   |
| [31:8]  | reserved    | —      | 0     | Reserved                                       |

#### DMA_ISR — Interrupt Status Register (Offset: 0x00C)

Read: current interrupt status. Write: write-1-to-clear.

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [7:0]   | irq_status  | R/W1C  | 0x00  | Per-channel interrupt status                   |
| [15:8]  | irq_done    | R/W1C  | 0x00  | Transfer complete flags                        |
| [23:16] | irq_err     | R/W1C  | 0x00  | Transfer error flags                           |
| [31:24] | reserved    | —      | 0     | Reserved                                       |

#### DMA_IIR — Interrupt Masked Status Register (Offset: 0x010)

Read-only. `DMA_IIR = DMA_ISR[7:0] & DMA_IER[7:0]`

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [7:0]   | irq_masked  | RO     | 0x00  | Masked interrupt status                         |
| [31:8]  | reserved    | —      | 0     | Reserved                                       |

#### DMA_ERR — Error Status Register (Offset: 0x014)

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [7:0]   | err_bus     | RO     | 0x00  | Per-channel bus error flag                     |
| [15:8]  | err_align   | RO     | 0x00  | Per-channel alignment error flag               |
| [23:16] | err_desc    | RO     | 0x00  | Per-channel descriptor error flag              |
| [31:24] | reserved    | —      | 0     | Reserved                                       |

#### DMA_ERRC — Error Clear Register (Offset: 0x018)

Write-1-to-clear for corresponding bits in DMA_ERR.

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [7:0]   | err_bus_clr | W1C    | 0x00  | Clear per-channel bus error                    |
| [15:8]  | err_align_clr| W1C   | 0x00  | Clear per-channel alignment error              |
| [23:16] | err_desc_clr| W1C    | 0x00  | Clear per-channel descriptor error             |
| [31:24] | reserved    | —      | 0     | Reserved                                       |

#### DMA_VER — Version Register (Offset: 0x01C)

| Bits    | Name        | Access | Reset   | Description                                    |
|---------|-------------|--------|---------|------------------------------------------------|
| [15:0]  | minor       | RO     | 0x0001  | Minor version                                  |
| [31:16] | major       | RO     | 0x0001  | Major version                                  |

### Channel Registers

Channel N base offset = `0x100 + (N × 0x40)`, where N = 0..7

| Offset | Name   | Width | Access | Reset     | Description                           |
|--------|--------|-------|--------|-----------|---------------------------------------|
| +0x00  | CH_SAR | 32    | RW     | 0x00000000 | Source Address Register               |
| +0x04  | CH_DAR | 32    | RW     | 0x00000000 | Destination Address Register          |
| +0x08  | CH_LEN | 32    | RW     | 0x00000000 | Transfer Length Register              |
| +0x0C  | CH_CR  | 32    | RW     | 0x00000000 | Channel Control Register              |
| +0x10  | CH_SR  | 32    | R/W1C  | 0x00000008 | Channel Status Register               |
| +0x14  | CH_LLP | 32    | RW     | 0x00000000 | Linked List Pointer                   |
| +0x18  | CH_BCR | 32    | RO     | 0x00000000 | Byte Count Remaining (read-only)      |
| +0x1C  | CH_CFG | 32    | RW     | 0x00000030 | Channel Configuration Register        |

#### CH_SAR — Source Address Register (Offset: +0x00)

| Bits    | Name      | Access | Reset | Description                                  |
|---------|-----------|--------|-------|----------------------------------------------|
| [31:0]  | src_addr  | RW     | 0     | Source start address (word-aligned)           |

#### CH_DAR — Destination Address Register (Offset: +0x04)

| Bits    | Name      | Access | Reset | Description                                  |
|---------|-----------|--------|-------|----------------------------------------------|
| [31:0]  | dst_addr  | RW     | 0     | Destination start address (word-aligned)      |

#### CH_LEN — Transfer Length Register (Offset: +0x08)

| Bits    | Name      | Access | Reset | Description                                  |
|---------|-----------|--------|-------|----------------------------------------------|
| [15:0]  | xfer_len  | RW     | 0     | Transfer length in bytes (1–65536; 0x0000 = 65536) |
| [31:16] | reserved  | —      | 0     | Reserved                                     |

#### CH_CR — Channel Control Register (Offset: +0x0C)

| Bits    | Name        | Access | Reset | Description                                                |
|---------|-------------|--------|-------|------------------------------------------------------------|
| [0]     | ch_enable   | RW     | 0     | Channel enable (1=start transfer)                          |
| [1]     | ch_done     | RO     | 0     | Transfer done flag                                         |
| [2]     | ch_pause    | RW     | 0     | Pause transfer (1=paused)                                  |
| [3]     | ch_abort    | RW     | 0     | Abort current transfer                                     |
| [5:4]   | src_mode    | RW     | 0     | Source address mode: 00=increment, 01=fixed, 10=scatter-gather, 11=reserved |
| [7:6]   | dst_mode    | RW     | 0     | Destination address mode: 00=increment, 01=fixed, 10=scatter-gather, 11=reserved |
| [8]     | src_per     | RW     | 0     | Source is peripheral (1=yes)                               |
| [9]     | dst_per     | RW     | 0     | Destination is peripheral (1=yes)                          |
| [11:10] | src_burst   | RW     | 0     | Source burst length: 00=1, 01=4, 10=8, 11=16 beats        |
| [13:12] | dst_burst   | RW     | 0     | Dest burst length: 00=1, 01=4, 10=8, 11=16 beats          |
| [15:14] | src_width   | RW     | 0     | Source transfer width: 00=8-bit, 01=16-bit, 10=32-bit, 11=64-bit |
| [17:16] | dst_width   | RW     | 0     | Dest transfer width: 00=8-bit, 01=16-bit, 10=32-bit, 11=64-bit |
| [19:18] | priority    | RW     | 0     | Channel priority (0=highest, 3=lowest)                     |
| [20]    | int_en      | RW     | 0     | Interrupt on transfer complete                             |
| [21]    | int_err_en  | RW     | 0     | Interrupt on transfer error                                |
| [22]    | sg_en       | RW     | 0     | Scatter-gather enable                                      |
| [23]    | cyclic_en   | RW     | 0     | Cyclic (circular) mode enable                              |
| [31:24] | reserved    | —      | 0     | Reserved                                                   |

#### CH_SR — Channel Status Register (Offset: +0x10)

| Bits    | Name          | Access | Reset | Description                                       |
|---------|---------------|--------|-------|---------------------------------------------------|
| [2:0]   | state         | RO     | 0     | Current FSM state (encoded)                       |
| [3]     | fifo_empty    | RO     | 1     | Channel FIFO empty flag                           |
| [4]     | fifo_full     | RO     | 0     | Channel FIFO full flag                            |
| [7:5]   | fifo_count    | RO     | 0     | FIFO occupancy (0–16)                             |
| [8]     | bus_error     | W1C    | 0     | AXI bus error occurred                            |
| [9]     | align_error   | W1C    | 0     | Address alignment error                           |
| [10]    | desc_error    | W1C    | 0     | Descriptor fetch error                            |
| [11]    | xfer_complete | W1C    | 0     | Transfer completed                                |
| [31:12] | reserved      | —      | 0     | Reserved                                          |

#### CH_LLP — Linked List Pointer (Offset: +0x14)

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [31:0]  | ll_pointer  | RW     | 0     | Address of next descriptor in memory            |

#### CH_BCR — Byte Count Remaining (Offset: +0x18, Read-Only)

| Bits    | Name        | Access | Reset | Description                                    |
|---------|-------------|--------|-------|------------------------------------------------|
| [15:0]  | bytes_left  | RO     | 0     | Remaining bytes to transfer                    |
| [31:16] | reserved    | —      | 0     | Reserved                                       |

#### CH_CFG — Channel Configuration Register (Offset: +0x1C)

| Bits    | Name           | Access | Reset | Description                                    |
|---------|----------------|--------|-------|------------------------------------------------|
| [0]     | secure         | RW     | 0     | TrustZone Secure attribute                     |
| [3:1]   | prot           | RW     | 0     | AXI protection attributes                      |
| [6:4]   | cache          | RW     | 0x3   | AXI cache attributes (default: Modifiable)     |
| [7]     | fifo_threshold | RW     | 0     | FIFO threshold mode (0=half, 1=quarter)        |
| [31:8]  | reserved       | —      | 0     | Reserved                                       |

## 5. Interrupt Model

### Interrupt Sources

Each channel can generate interrupts under the following conditions:

| Source           | CH_SR Bit       | DMA_ISR Bit(s) | Type  | Enable Reg        | Status Reg  | Description                               |
|------------------|-----------------|----------------|-------|-------------------|-------------|-------------------------------------------|
| Transfer Done    | xfer_complete [11] | irq_done [15:8] (bit N) | level | CH_CR.int_en [20] | DMA_ISR     | All bytes transferred successfully        |
| Bus Error        | bus_error [8]   | irq_err [23:16] (bit N) | level | CH_CR.int_err_en [21] | DMA_ISR | AXI SLVERR or DECERR                      |
| Alignment Error  | align_error [9] | irq_err [23:16] (bit N) | level | CH_CR.int_err_en [21] | DMA_ISR | Address not aligned to transfer width     |
| Descriptor Error | desc_error [10] | irq_err [23:16] (bit N) | level | CH_CR.int_err_en [21] | DMA_ISR | Invalid/null descriptor fetched           |

- **Interrupt output**: `irq[7:0]` — active-high, level-sensitive. Each bit corresponds to one channel.
- **Clear mechanism**: Write-1-to-clear (W1C) on `DMA_ISR` bits (irq_done, irq_err) and `CH_SR` error/xfer_complete bits.
- **Masking**: `DMA_IER.irq_enable[N]` must be set for `irq[N]` to propagate. `DMA_IIR[7:0] = DMA_ISR[7:0] & DMA_IER[7:0]`.

### Interrupt Flow

1. Event occurs on channel N (transfer complete, bus error, alignment error, or descriptor error).
2. Corresponding bit set in `CH_SR` (e.g., `CH_SR.xfer_complete=1` or `CH_SR.bus_error=1`).
3. If the event type is enabled (`CH_CR.int_en=1` for done, `CH_CR.int_err_en=1` for errors), the corresponding bit is set in `DMA_ISR`:
   - Done: `DMA_ISR.irq_done[N]=1`
   - Error: `DMA_ISR.irq_err[N]=1`
4. If `DMA_IER.irq_enable[N]=1`, then `irq[N]` is asserted (active-high level).
5. Software reads `DMA_ISR` to identify the channel and cause.
6. Software clears the interrupt by writing 1 to the corresponding bits in `DMA_ISR` (W1C) and `CH_SR` (W1C).
7. After clearing, `irq[N]` deasserts if no other pending sources remain for that channel.

### Interrupt Register Summary

| Register   | Bits [7:0]        | Bits [15:8]    | Bits [23:16]   | Bits [31:24] |
|------------|--------------------|----------------|----------------|--------------|
| DMA_ISR    | irq_status (R/W1C) | irq_done (R/W1C) | irq_err (R/W1C) | reserved   |
| DMA_IER    | irq_enable (RW)    | reserved       | reserved       | reserved     |
| DMA_IIR    | irq_masked (RO)    | reserved       | reserved       | reserved     |

## 6. Memory

### Per-Channel Data FIFO

Each of the 8 channels contains an independent data FIFO that decouples the AXI read (source) and AXI write (destination) phases of a transfer.

| Instance          | Type | Depth | Width               | R ports | W ports | Latency | Description                     |
|-------------------|------|-------|---------------------|---------|---------|---------|---------------------------------|
| ch_fifo[0]–ch_fifo[7] | FIFO | 16    | DATA_WIDTH (32/64/128) | 1    | 1       | 1 cycle | Per-channel data buffer         |

#### FIFO Operation

- **Write side**: AXI read data (`m_axi_rdata`) is pushed into the FIFO during READ_DATA state.
- **Read side**: Data is popped from the FIFO and driven on `m_axi_wdata` during WRITE_DATA state.
- **Flow control**: Read side stalls when FIFO is empty; write side stalls when FIFO is full.
- **Occupancy tracking**: `CH_SR.fifo_count[7:5]` reports current FIFO fill level (0–16). `CH_SR.fifo_empty` and `CH_SR.fifo_full` provide single-bit flags.

#### FIFO Thresholds

The write phase begins when the FIFO reaches a configurable threshold:

| `CH_CFG.fifo_threshold` | Threshold         | Description                       |
|--------------------------|-------------------|-----------------------------------|
| 0 (default)              | Half-full (8 entries) | Start writing when ≥8 entries  |
| 1                        | Quarter-full (4 entries) | Start writing when ≥4 entries |

Lower threshold reduces latency but may reduce burst efficiency. Default half-full optimizes for AXI burst bandwidth.

#### Data Width Conversion

When source and destination transfer widths differ (`CH_CR.src_width ≠ CH_CR.dst_width`):

| Conversion          | Mechanism                                                   |
|---------------------|-------------------------------------------------------------|
| Narrower → Wider    | Multiple narrow reads fill a single wide FIFO entry / write beat. E.g., four 8-bit reads → one 32-bit write. |
| Wider → Narrower    | A single wide read feeds multiple narrow write beats. E.g., one 32-bit read → four 8-bit writes. |

The FIFO internal width matches the AXI data bus width (`DATA_WIDTH`). Width conversion logic sits at the FIFO read/write adapters.

## 7. Timing

- **Clock**: `axi_clk` — single clock domain for all logic. Target frequency **≥200 MHz** (45 nm LP process). Period ≤ 5 ns.
- **Reset**: `axi_rst_n` — active-low asynchronous reset.
  - Minimum reset assertion: 16 `axi_clk` cycles.
  - After reset deassertion: 4 clock cycles before the controller can accept register accesses.
  - Reset action: all channels → IDLE, all registers → default values, all FIFOs flushed, all interrupts deasserted (`irq = 0`), AXI master interfaces quiesced.
- **Input-to-output latency**:
  - Channel enable (`CH_CR.ch_enable=1`) to first AXI read address: **< 8 clock cycles**
  - `dma_req[N]` assertion to `dma_ack[N]` assertion: **< 4 clock cycles**
  - FIFO read/write latency: 1 clock cycle
- **Throughput**: **>95% of theoretical AXI bandwidth** for memory-to-memory transfers (back-to-back INCR bursts, minimal idle cycles on the bus).
- **Critical path**: Arbiter priority resolution → AXI master address channel mux → AXI interconnect path. The arbiter must evaluate up to 8 channel requests within a single cycle.
- **CDC crossings**: None. All interfaces (`dma_req`, `dma_ack`, `dma_eop`, AXI signals) are synchronous to `axi_clk`. No synchronizers required.
- **Clock gating**: Per-channel via `DMA_GCR.clk_gating[N]`. Channel must be in IDLE before gating. Ungating requires 2 clock cycles for stabilization.

## 8. RTL Implementation Notes

### Coding Style

- Use nonblocking assignments (`<=`) in all `always_ff` blocks (sequential logic).
- Use blocking assignments (`=`) in all `always_comb` blocks (combinational logic).
- No latches: every `always_comb` block must assign all outputs in every branch.
- Use `logic` type for all signals (no `wire`/`reg` ambiguity).
- All state machines use `enum` for state encoding with `typedef enum logic [3:0]`.
- Parameterized module headers using `#(parameter int DATA_WIDTH = 32)` style.

### Reset Strategy

- All flip-flops use asynchronous assertion (`negedge axi_rst_n`), synchronous deassertion of reset.
- Reset releases all channels to IDLE, clears all registers to defaults, flushes all FIFOs, deasserts all interrupts.
- AXI master interface cleanly quiesces on reset: no outstanding transactions, all valid signals deasserted.

### Parameterization

- `DATA_WIDTH`: parameterizes all AXI data signals, FIFO width, and data path mux widths. Supported values: 32, 64, 128.
- `NUM_CHANNELS`: controls the generate loop for channel instances. Default 8.
- `FIFO_DEPTH`: per-channel FIFO depth, default 16. Must be a power of 2.
- `ADDR_WIDTH`: AXI address width, default 32.
- `ID_WIDTH`: AXI transaction ID width, default 4 (supports up to 16 outstanding transaction IDs).

### Channel Generate Pattern

- Use `generate` / `for` loop to instantiate `NUM_CHANNELS` instances of `dma_channel`.
- Each channel gets a unique index (`genvar i`) used as:
  - AXI transaction ID (`m_axi_awid = i`, `m_axi_arid = i`)
  - `dma_req[i]` / `dma_ack[i]` / `dma_eop[i]` mapping
  - `irq[i]` mapping
  - Register decode base offset: `0x100 + (i × 0x40)`

### Arbiter Design

- Priority levels 0–3 per channel (`CH_CR.priority[19:18]`). 0 = highest.
- When multiple channels have the same priority: **round-robin** arbitration prevents starvation.
- When priorities differ: **strict priority** — higher-priority channel always wins.
- Arbiter selects one channel per cycle to drive the shared AXI master interface.
- Up to 4 outstanding AXI transactions per channel, 8 total across all channels.

### AXI Burst Type Selection

| Address Mode | AXI Burst Type | Condition                        |
|--------------|----------------|----------------------------------|
| Incrementing | INCR (0b01)    | `src_mode=00` or `dst_mode=00`   |
| Fixed        | FIXED (0b00)   | `src_mode=01` or `dst_mode=01`   |

- Cache attributes: `CH_CFG.cache` for memory transactions (default `0x3` = Modifiable, Bufferable). Forced `0x0` for peripheral (fixed address) transactions.
- Protection attributes: `CH_CFG.prot[2:0]` sets `AxProt` on all transactions.

### Endianness

- When `DMA_GCR.endian_swap=1`: byte-swap logic is applied at the FIFO write interface to convert endianness of data entering the FIFO.
- Default (`endian_swap=0`): little-endian — data passes through unmodified.

### Security (TrustZone)

- Each channel has a `CH_CFG.secure` attribute.
- When `secure=1`: AXI `AxProt[1]` is driven to `0` (secure transaction).
- When `secure=0`: AXI `AxProt[1]` is driven to `1` (non-secure transaction).
- Non-secure register access to a secure channel returns SLVERR on AXI-Lite.
- `DMA_GCR` can only be written by Secure bus transactions.

### Tie-off and Defaults

- All reserved register bits must be tied to 0 on write and read back as 0.
- AXI signals not used (e.g., `m_axi_awlock`, `m_axi_awqos`, `m_axi_awregion`) must be tied to 0.
- No exclusive or locked access support.

## 9. DV Plan

### Test Sequences

| ID  | Sequence Name              | Steps                                                                                                                                                       | Expected Result                                                                  | Priority |
|-----|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|----------|
| S1  | Power-on Reset             | 1. Assert `axi_rst_n` for ≥16 cycles 2. Deassert 3. Wait 4 cycles 4. Read all global and channel registers                                                | All registers at reset values. `DMA_GSR.channel_idle=0xFF`. `irq=0`. All `dma_ack=0`. | High     |
| S2  | Register R/W               | 1. Write/read all global registers 2. Write/read all channel 0 registers 3. Verify W1C on `DMA_ISR` and `CH_SR` 4. Verify RO fields unchanged on write    | Read data matches written data for RW fields. W1C bits clear correctly. RO fields unchanged. | High     |
| S3  | Mem-to-Mem Basic           | 1. Write pattern to source memory 2. Program CH0: SAR, DAR, LEN, CR (src_mode=00, dst_mode=00, int_en=1) 3. Enable DMA 4. Set ch_enable 5. Wait for irq     | Data at destination matches source. `CH_SR.xfer_complete=1`. `irq[0]=1`. `CH_BCR=0`. | High     |
| S4  | Mem-to-Periph Handshake    | 1. Program CH1: src_mode=00, dst_mode=01, dst_per=1 2. Enable channel 3. Assert `dma_req[1]` after FIFO fill 4. Verify `dma_ack[1]` 5. Check fixed addr write | `dma_ack[1]` asserted within 4 cycles of `dma_req[1]`. AXI AW burst type FIXED. Data at peripheral correct. | High     |
| S5  | Periph-to-Mem              | 1. Program CH2: src_mode=01, src_per=1, dst_mode=00 2. Assert `dma_req[2]` 3. Verify `dma_ack[2]` 4. Read data from memory 5. Compare with peripheral data | AXI AR burst type FIXED. Data in memory matches peripheral output. `xfer_complete=1`. | High     |
| S6  | Scatter-Gather Chain       | 1. Create 4-descriptor chain in memory (set end_of_list on last) 2. Program CH0: sg_en=1, LLP=&desc[0] 3. Enable and start 4. Wait for completion           | All 4 blocks transferred. Each descriptor executed in order. `CH_SR.xfer_complete=1` after last descriptor. | High     |
| S7  | Interrupt Flow             | 1. Enable interrupts: `DMA_IER[0]=1`, `CH_CR.int_en=1` 2. Start transfer 3. Verify `irq[0]` assertion 4. Read `DMA_ISR` 5. W1C clear 6. Verify `irq[0]` deasserts | `irq[0]` asserts on completion. `DMA_ISR.irq_done[0]=1`. `irq[0]` deasserts within 1 cycle of W1C clear. | High     |
| S8  | Error Injection            | 1. Inject AXI SLVERR on read (return SLVERR) 2. Inject DECERR on write 3. Test alignment error (unaligned address) 4. Test null descriptor pointer        | `CH_SR.bus_error=1` for SLVERR/DECERR. `CH_SR.align_error=1` for unaligned. `CH_SR.desc_error=1` for null desc. Channel enters ERROR state. `irq_err` fires if enabled. | High     |
| S9  | Priority Arbitration       | 1. Start CH0 (priority=0) and CH1 (priority=1) simultaneously 2. Verify CH0 wins bus 3. Start CH0 and CH1 both priority=0 4. Verify round-robin fairness  | Higher priority wins. Equal priority: alternating bus access (round-robin). Both transfers complete correctly. | Medium   |
| S10 | Pause and Abort            | 1. Start transfer on CH0 2. Mid-transfer, write `CH_CR.ch_pause=1` 3. Verify FSM freezes, FIFO drains 4. Clear pause, verify resume 5. Start new transfer, abort mid-way | Pause: no data loss, transfer completes after unpause. Abort: channel enters ERROR, `CH_SR` error flags set. | Medium   |
| S11 | Peripheral-to-Peripheral   | 1. Program CH3: src_mode=01, src_per=1, dst_mode=01, dst_per=1 2. Assert source `dma_req[3]` then dest `dma_req[3]` 3. Verify data movement                | Data moves from source peripheral to dest peripheral. Both handshakes complete. Fixed addr on both sides. | Medium   |
| S12 | Cyclic Scatter-Gather      | 1. Create 2-descriptor ring (last→first) 2. Set `CH_CR.cyclic_en=1, sg_en=1` 3. Start transfer 4. Let run for 10+ iterations 5. Abort                    | Transfers repeat continuously. No IDLE transition between iterations. Abort stops the cycle. | Medium   |
| S13 | Zero-Length Transfer       | 1. Program CH_LEN=0 (means 65536 bytes) 2. Execute transfer 3. Verify 65536 bytes transferred                                                              | Full 64 KB transfer completes correctly. `CH_BCR` decrements to 0.               | Medium   |
| S14 | Max-Length Transfer        | 1. Program CH_LEN=0xFFFF (65535 bytes) with max burst (16 beats) 2. Execute mem-to-mem                                                                     | All 65535 bytes transferred. No data corruption. Back-to-back bursts utilized.  | Medium   |
| S15 | Reset During Transfer      | 1. Start a large mem-to-mem transfer 2. Assert `axi_rst_n` mid-transfer 3. Deassert 4. Check state                                                          | All channels return to IDLE. FIFOs flushed. Registers at reset values. No spurious AXI transactions. | Medium   |
| S16 | Clock Gating               | 1. Verify CH4 is IDLE 2. Set `DMA_GCR.clk_gating[4]=1` 3. Access CH4 registers 4. Verify SLVERR 5. Ungate 6. Verify channel works again                   | Gated channel returns SLVERR on register access. After ungating + 2 cycles, channel is programmable. | Medium   |
| S17 | Back-to-Back Transfers     | 1. Complete transfer on CH0 2. Immediately reprogram and restart CH0 3. Repeat 5 times                                                                     | All 5 transfers complete without data loss. No deadlock or hang.                 | Medium   |
| S18 | Simultaneous 8-Channel     | 1. Start all 8 channels simultaneously with different priorities 2. Verify all complete                                                                    | All 8 transfers complete. Arbiter services all channels. No starvation.          | Medium   |
| S19 | Width Conversion           | 1. Configure src_width=8-bit, dst_width=32-bit 2. Transfer 16 bytes 3. Verify data packing 4. Reverse: src_width=32, dst_width=8                          | Narrow→wide: 4 bytes packed correctly. Wide→narrow: 4 bytes unpacked correctly.  | Medium   |
| S20 | End-of-Packet (dma_eop)    | 1. Start peripheral transfer 2. Assert `dma_eop[N]` before transfer complete 3. Verify channel terminates gracefully                                       | Transfer terminates on `dma_eop`. Partial data written correctly. Status updated. | Low      |

### Coverage Goals

#### Functional Coverage

- **FSM state coverage**: 100% — all 10 states visited per channel (IDLE, DESC_FETCH, WAIT_REQ, READ_ADDR, READ_DATA, WRITE_ADDR, WRITE_DATA, WRITE_RESP, COMPLETE, ERROR)
- **FSM transition coverage**: 100% — all legal state transitions exercised
- **Interrupt coverage**: All 4 interrupt sources fired and cleared on each channel
- **Register bit coverage**: 100% — all RW bits written and read back; all RO bits read; all W1C bits written-1-to-clear
- **FIFO coverage**: Full (16 entries), empty (0), single-entry (1), threshold points (4, 8)
- **Transfer type combinations**: All 4 types × all supported address mode combinations
- **Burst length/width**: All burst lengths (1, 4, 8, 16) × all widths (8, 16, 32, 64 bit)

#### Code Coverage

- **Line coverage**: ≥ 90%
- **Branch coverage**: ≥ 85%
- **Toggle coverage**: ≥ 80% on all ports; ≥ 95% on data path signals
- **Condition coverage**: All arbiter priority resolution paths

### SVA Assertions

1. **AXI4-Lite protocol assertions**:
   - `s_axi_awvalid` remains stable until `s_axi_awready`
   - `s_axi_wvalid` remains stable until `s_axi_wready`
   - `s_axi_arvalid` remains stable until `s_axi_arready`
   - Response valid only after address/data handshake completes

2. **AXI4 master protocol assertions**:
   - `m_axi_awvalid` / `m_axi_arvalid` remain stable until ready
   - `m_axi_wlast` is asserted on the last beat of every burst
   - Burst length matches `m_axi_awlen` / `m_axi_arlen` + 1
   - No new transaction on a channel until previous B response received (if required)

3. **FIFO integrity**:
   - FIFO never overflows: push is gated when `fifo_full=1`
   - FIFO never underflows: pop is gated when `fifo_empty=1`
   - `fifo_count` is consistent with number of pushes minus pops

4. **Interrupt behavior**:
   - `irq[N]` must deassert within 1 cycle of W1C clear (if no other pending source)
   - `irq[N]` is never asserted when `DMA_IER.irq_enable[N]=0`
   - `DMA_IIR[7:0] == DMA_ISR[7:0] & DMA_IER[7:0]` always

5. **FSM legal transitions**:
   - Only state transitions defined in the §3 FSM table are legal
   - Channel must be in IDLE before `ch_enable` can be set
   - ERROR state can only be exited by software clearing errors and re-enabling

6. **Byte count monotonicity**:
   - `CH_BCR.bytes_left` never exceeds the initial `CH_LEN.xfer_len`
   - `CH_BCR.bytes_left` decrements monotonically during active transfer (never increases)

### Known Corner Cases / Hazards

- **Zero-length transfer**: `CH_LEN=0` maps to 65536 bytes — must not cause immediate completion
- **Unaligned address with fixed mode**: No alignment requirement for fixed mode — but alignment error for incrementing mode if address not aligned to width
- **Abort during AXI burst**: Outstanding AXI beats may still complete on the bus — the channel FSM enters ERROR but the AXI protocol is not violated
- **Clock gating during non-IDLE**: Must be prevented by software; hardware returns DECERR if gated channel accessed
- **Descriptor fetch error mid-chain**: SG chain terminates, channel enters ERROR, partial data may have been written
- **Simultaneous `dma_req` on multiple channels**: Arbiter resolves — one at a time; no `dma_req` lost
- **FIFO threshold crossing during burst**: Write phase may start mid-read-burst if threshold crossed — requires careful FIFO pointer management
