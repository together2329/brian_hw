# CoreLink DMA-330 (PL330) DMA Controller Specification

> **Document Reference:** ARM DDI 0424 (r1p2) — CoreLink DMA-330 DMA Controller Technical Reference Manual  
> **Revision History:** r0p0 (Dec 2007) → r1p0 (Nov 2009) → r1p1 (Jul 2010) → r1p2 (Jun 2012)  
> **Copyright:** © 2007, 2009–2012 ARM Limited. All rights reserved.

---

## 1. Overview & Introduction

### 1.1 Product Identification

The **CoreLink DMA-330** (also referred to as **PL330** or simply **DMA-330**) is a high-performance
Direct Memory Access (DMA) controller designed, tested, and licensed by **ARM Limited**.
It is part of the ARM **CoreLink** family of system IP products.

| Name              | Context                                          |
|-------------------|--------------------------------------------------|
| **DMA-330**       | Short product name                               |
| **PL330**         | PrimeCell / legacy product code                  |
| **CoreLink DMA-330** | Full marketing name (CoreLink family branding) |
| **DMAC**          | Generic reference to the DMA Controller block    |

### 1.2 Purpose

The DMA-330 is a **Direct Memory Access (DMA) controller** that enables the movement of blocks of
data **without burdening the processor**. It supports:

- **Memory → Memory** transfers
- **Memory → Peripheral** transfers
- **Peripheral → Memory** transfers
- **Scatter-Gather** operations (non-contiguous source/destination addresses)

By offloading bulk data movement from the CPU to dedicated hardware, the DMA-330 can:

| Benefit                    | Description                                                        |
|----------------------------|--------------------------------------------------------------------|
| **Improve system performance** | CPU is free to execute code while DMA handles data transfers   |
| **Reduce power consumption**   | Fewer CPU memory accesses → lower dynamic power               |
| **Increase throughput**        | Optimized AXI bursting and pipelined transfers                |
| **Flexible programming**      | Instruction-set-based programming model (not fixed LLI)       |

### 1.3 AMBA Compliance

The DMA-330 is an **AMBA (Advanced Microcontroller Bus Architecture)** compliant peripheral.
Specifically, it uses the following AMBA protocol interfaces:

- **AXI4 (Advanced eXtensible Interface)** — Master interface for performing DMA data transfers
  over the system bus
- **APB (Advanced Peripheral Bus)** — Slave interfaces for CPU-based programming and control
  of the DMAC registers

The DMAC is designed for integration into **AMBA-based SoC (System-on-Chip)** systems and connects
seamlessly to ARM Cortex processors and other AMBA-compliant peripherals.

### 1.4 Key Features

- **Configurable DMA channels:** 1 to 8 independent channels, each executing a concurrent thread
  of DMA operations
- **Instruction-based programming:** Uses a small, variable-length instruction set to define DMA
  operations — providing greater flexibility than traditional Linked-List Item (LLI) based
  controllers
- **AXI master interface:** High-bandwidth data transfers with configurable burst sizes
- **Dual APB slave interfaces:** Secure and Non-secure programming interfaces implementing
  **ARM TrustZone** security technology
- **Peripheral request interface:** Supports flow-controlled transfers with DMA-capable
  peripherals (e.g., UART, SPI, I2S)
- **MFIFO data buffer:** Configurable multi-FIFO data storage for buffering load/store data
- **Run-from-reset:** Capability to execute DMA operations immediately after reset without
  processor intervention
- **Interrupt support:** Per-channel interrupt generation for transfer completion and fault
  reporting
- **Scatter-gather:** Non-contiguous memory transfers using address manipulation instructions

### 1.5 Documentation Reference

The authoritative source for the DMA-330 specification is:

> **ARM DDI 0424** — *CoreLink DMA-330 DMA Controller Technical Reference Manual*  
> Available at: https://developer.arm.com/documentation/ddi0424/latest

This document (the one you are reading) serves as a concise, consolidated reference based on
the official ARM TRM and supplementary sources. For register-level bit field definitions and
timing diagrams, always refer to the official ARM DDI 0424 document.

---

## 2. Architecture & Block Diagram

### 2.1 Top-Level Block Diagram

```
                           ┌─────────────────────────────────────────────────────────────┐
                           │                     DMA-330 (DMAC)                          │
                           │                                                             │
  ┌──────────┐             │  ┌──────────────────────────────────────────────────────┐   │
  │  CPU /   │   APB       │  │              DMAC Engine / Control Logic             │   │
  │  Secure  ├─────────────┤  │                                                      │   │
  │  Master  │  (Secure)   │  │  ┌──────────┐  ┌──────────────┐  ┌──────────────┐   │   │
  └──────────┘             │  │  │ Manager  │  │   Channel    │  │   Channel    │   │   │
                           │  │  │ Thread   │  │   Thread 0   │  │   Thread 1   │   │   │
  ┌──────────┐             │  │  │          │  │  (PC, Regs)  │  │  (PC, Regs)  │   │   │
  │  CPU /   │   APB       │  │  └────┬─────┘  └──────┬───────┘  └──────┬───────┘   │   │
  │  Non-    ├─────────────┤  │       │               │                 │            │   │
  │  Secure  │ (Non-secure)│  │       │         ┌─────┴─────┐     ┌─────┴─────┐     │   │
  │  Master  │             │  │       │         │  Instr    │     │  Instr    │     │   │
  └──────────┘             │  │       │         │  Buffer 0 │     │  Buffer 1 │     │   │
                           │  │       │         └───────────┘     └───────────┘     │   │
                           │  │       │                                              │   │
                           │  │       │               ... (up to 8 channels)       │   │
                           │  │       │                                              │   │
                           │  │  ┌────┴──────────────────────────────────────────┐ │   │
                           │  │  │              Instruction Cache                 │ │   │
                           │  │  │   (Temporarily stores DMA microcode from       │ │   │
                           │  │  │    system memory via AXI master)               │ │   │
                           │  │  └───────────────────────┬───────────────────────┘ │   │
                           │  │                          │                         │   │
                           │  │  ┌───────────────────────┴───────────────────────┐ │   │
                           │  │  │              MFIFO Data Buffer                 │ │   │
                           │  │  │   (Multi-FIFO for buffering load/store data)   │ │   │
                           │  │  └───────────────────────┬───────────────────────┘ │   │
                           │  └──────────────────────────┼─────────────────────────┘   │
                           │                             │                             │
  ┌──────────┐   AXI       │          AXI Master         │                             │
  │  System  ├─────────────┤  Interface  (read/write)    │                             │
  │  Memory  │◄────────────┤                             │                             │
  │  /Periph │             │                             │                             │
  └──────────┘             │                             │                             │
                           └─────────────────────────────┼─────────────────────────────┘
                                                         │
                           ┌─────────────────────────────┼─────────────────────────────┐
                           │                 Peripheral Request Interface               │
                           │  ┌─────┐  ┌─────┐  ┌─────┐       ┌─────┐                  │
                           │  │Req 0│  │Req 1│  │Req 2│ . . . │Req N│                  │
                           │  └─────┘  └─────┘  └─────┘       └─────┘                  │
                           └──────────────────────────────────────────────────────────────┘

                           ┌──────────────────────────────────────────────────────────────┐
                           │  IRQ Outputs: irq[0] .. irq[N]  (per-channel + fault)       │
                           └──────────────────────────────────────────────────────────────┘
```

### 2.2 Component Descriptions

#### 2.2.1 AXI Master Interface

- **Role:** Performs the actual data transfers (reads and writes) on the AXI system bus
- **Protocol:** AXI4 master
- **Usage:** The DMA engine uses this interface to:
  - Fetch DMA instructions from system memory (code fetch)
  - Read source data during `DMALD` operations
  - Write destination data during `DMAST` operations
- **Configurable parameters:** Data width (32/64/128/256-bit), burst length, address increment mode

#### 2.2.2 APB Slave Interfaces (Dual)

The DMAC provides **two independent APB slave interfaces**:

| Interface     | Security State | Purpose                                            |
|---------------|----------------|----------------------------------------------------|
| **APB Secure**    | Secure         | Full access to all registers and all channels  |
| **APB Non-secure**| Non-secure     | Access only to non-secure registers/channels   |

- **Protocol:** APB4 slave
- **Address space:** Each APB interface occupies a **4 KB** memory-mapped region
- **TrustZone:** Implements ARM TrustZone security partitioning — the secure APB can access and
  control all resources, while the non-secure APB is restricted to non-secure channels only

#### 2.2.3 DMAC Engine / Control Logic

The central processing block of the DMAC. It contains:

- **Manager Thread:** Controls overall DMAC operation, handles channel initialization (`DMAGO`),
  event processing, and fault management. The manager thread does not perform data transfers
  itself.
- **DMA Channel Threads (1–8):** Each channel is an independent thread of execution with its own:
  - **Program Counter (PC):** Tracks the current position in the DMA instruction stream
  - **Channel Registers:** Source address (SA), Destination address (DA), Transfer count (TC)
  - **State Machine:** Manages the channel's operating state (Stopped, Executing, etc.)
- **Instruction Buffers:** Per-channel FIFO queues that hold decoded DMA instructions waiting
  to be issued on the AXI bus. This allows the DMAC to prefetch instructions for pipelined
  execution.

#### 2.2.4 Instruction Cache

- **Role:** Temporarily stores DMA instructions fetched from system memory
- **Purpose:** Reduces AXI bus traffic by caching frequently-used instruction sequences, avoiding
  repeated code fetches
- **Behavior:** When a channel thread requires an instruction, the cache is checked first. On a
  cache miss, the instruction is fetched from system memory via the AXI master interface

#### 2.2.5 MFIFO Data Buffer

- **Role:** Multi-FIFO data storage that buffers data between AXI read (load) and write (store)
  operations
- **Sharing:** The MFIFO is a shared resource across all active DMA channels
- **Configurable depth:** Implementation-time parameter that determines total FIFO depth
- **Data flow:** During a `DMALD`, data read from the source is placed into the MFIFO. During a
  `DMAST`, data is taken from the MFIFO and written to the destination

#### 2.2.6 Peripheral Request Interface

- **Role:** Receives flow-control signals from DMA-capable peripherals
- **Signals per peripheral:**
  - `dmareq[n]` — DMA request (peripheral signals it has data to send or is ready to receive)
  - `dmaack[n]` — DMA acknowledge (DMAC acknowledges the request)
- **Usage:** Enables synchronized peripheral-to-memory and memory-to-peripheral transfers where
  the peripheral controls the pacing of data flow
- **Configurable:** Number of peripheral request interfaces is set at implementation time

#### 2.2.7 Interrupt Outputs

- **Role:** Notifies the processor of DMA events (completion, fault, etc.)
- **Lines:** One interrupt line per event/irq (configurable number, typically mapped to per-channel
  events plus a combined fault interrupt)
- **Triggering:** Interrupts are generated by the `DMASEV` instruction or by fault conditions

---

## 3. Interfaces

The DMA-330 provides four primary hardware interfaces for integration into an AMBA-based SoC.

### 3.1 AXI Master Interface

The AXI master interface is the **primary data movement interface** of the DMAC. It is used for
all data transfers and instruction fetches.

#### 3.1.1 Role in DMA Transfers

The AXI master interface performs the following operations:

| Operation          | Description                                                      |
|--------------------|------------------------------------------------------------------|
| **Instruction fetch** | Reads DMA microcode from system memory when the instruction cache misses |
| **DMA Load (DMALD)**  | Reads source data from memory or memory-mapped peripheral registers |
| **DMA Store (DMAST)** | Writes destination data to memory or memory-mapped peripheral registers |

The DMAC generates AXI read and write transactions autonomously — the CPU is never involved
in individual data beats. The AXI interface supports configurable data widths and burst lengths
to optimize bus utilization.

#### 3.1.2 Key AXI Signals

| Signal Group        | Direction   | Description                                       |
|---------------------|-------------|---------------------------------------------------|
| `AWADDR[31:0]`      | Output      | Write address                                     |
| `AWLEN[3:0]`        | Output      | Burst length (number of beats − 1)                |
| `AWSIZE[2:0]`       | Output      | Burst size (bytes per beat)                       |
| `AWBURST[1:0]`      | Output      | Burst type (FIXED, INCR, WRAP)                    |
| `AWVALID/AWREADY`   | Output/Input| Write address handshake                           |
| `WDATA[DATA_W-1:0]` | Output      | Write data (width is configurable: 32/64/128/256) |
| `WLAST`             | Output      | Last beat indicator                               |
| `WVALID/WREADY`     | Output/Input| Write data handshake                              |
| `ARADDR[31:0]`      | Output      | Read address                                      |
| `ARLEN[3:0]`        | Output      | Burst length                                      |
| `ARSIZE[2:0]`       | Output      | Burst size                                        |
| `ARVALID/ARREADY`   | Output/Input| Read address handshake                            |
| `RDATA[DATA_W-1:0]` | Input       | Read data                                         |
| `RLAST`             | Input       | Last beat indicator                               |
| `RVALID/RREADY`     | Input/Output| Read data handshake                               |

> **Note:** The actual data width (`DATA_W`) is a configuration parameter set at implementation
> time. Common implementations use 32-bit or 64-bit.

### 3.2 APB Slave Interfaces (Dual)

The DMAC provides **two independent APB4 slave interfaces** for CPU-based programming. Each
occupies a 4 KB address space and provides access to DMAC control and status registers.

#### 3.2.1 Secure APB Interface

| Property        | Value                                              |
|-----------------|----------------------------------------------------|
| Protocol        | APB4 slave                                         |
| Security state  | **Secure**                                         |
| Address space   | 4 KB (base address configured at SoC integration)  |
| Access scope    | **All** registers and **all** DMA channels          |

The Secure APB interface is intended for use by **secure-world software** (e.g., ARM TrustZone
secure monitor or secure OS). It has unrestricted access to:

- All DMAC control and configuration registers
- All DMA channels (both secure and non-secure channels)
- Debug registers
- Fault status and fault clear registers

#### 3.2.2 Non-secure APB Interface

| Property        | Value                                              |
|-----------------|----------------------------------------------------|
| Protocol        | APB4 slave                                         |
| Security state  | **Non-secure**                                     |
| Address space   | 4 KB (base address configured at SoC integration)  |
| Access scope    | **Only non-secure** registers and channels          |

The Non-secure APB interface is used by **normal-world software** (e.g., Linux kernel or
application processor). Access is restricted:

- Can only access channels configured as non-secure
- Cannot access secure channel registers or fault information for secure channels
- Cannot modify DMAC-wide security configuration

#### 3.2.3 Key APB Signals (per interface)

| Signal            | Direction   | Description                            |
|-------------------|-------------|----------------------------------------|
| `PADDR[11:0]`     | Input       | Address (12-bit for 4KB space)         |
| `PSEL`            | Input       | Select signal                          |
| `PENABLE`         | Input       | Enable signal (indicates second phase) |
| `PWRITE`          | Input       | Write (1) / Read (0)                   |
| `PWDATA[31:0]`    | Input       | Write data from CPU                    |
| `PRDATA[31:0]`    | Output      | Read data to CPU                       |
| `PREADY`          | Output      | Transfer complete                      |
| `PSLVERR`         | Output      | Slave error response                   |

### 3.3 Interrupt Output Interface

The DMAC generates interrupts to notify the processor of events and fault conditions.

#### 3.3.1 Interrupt Lines

| Signal          | Direction | Description                                       |
|-----------------|-----------|---------------------------------------------------|
| `irq[n]`        | Output    | Per-event interrupt line (configurable count)      |

The number of interrupt lines is a configuration parameter. Common configurations allocate
one interrupt per channel plus a combined fault interrupt, or a single combined interrupt line
shared across all events.

#### 3.3.2 Interrupt Sources

Interrupts are generated by:

1. **DMA Event (DMASEV instruction):** A channel thread executes a `DMASEV` instruction to signal
   completion or a specific event. This sets the corresponding bit in the `INT_EVENT_RIS` register.
2. **Fault conditions:** Bus errors, instruction decode errors, or security violations trigger
   fault interrupts.
3. **IRQ vs. FIQ:** The `INTEN` register controls which events generate IRQ outputs.

#### 3.3.3 Interrupt Registers

| Register           | Offset   | Description                              |
|--------------------|----------|------------------------------------------|
| `INTEN`            | `0x020`  | Interrupt enable (per-event mask)        |
| `INT_EVENT_RIS`    | `0x024`  | Raw interrupt status (event)             |
| `INTMIS`           | `0x028`  | Masked interrupt status                  |
| `INTCLR`           | `0x02C`  | Interrupt clear (write-to-clear)         |

### 3.4 Peripheral Request Interface

The peripheral request interface enables **flow-controlled DMA transfers** between memory and
DMA-capable peripherals (e.g., UART, SPI, I2S, SD/MMC).

#### 3.4.1 Signal Description

For each peripheral request line *n*:

| Signal           | Direction      | Description                                          |
|------------------|----------------|------------------------------------------------------|
| `dmareq[n]`      | Input          | DMA request — peripheral asserts when ready for data transfer |
| `dmaack[n]`      | Output         | DMA acknowledge — DMAC asserts to indicate it is servicing the request |

#### 3.4.2 Transfer Flow

```
  Peripheral                          DMAC                          Memory
  ──────────                          ────                          ──────
      │                                 │                              │
      │  ──── dmareq[n] (assert) ────►  │                              │
      │                                 │  ──── AXI Read (DMALD) ────► │
      │                                 │  ◄─── Data ────────────────  │
      │  ◄─── dmaack[n] (assert) ─────  │                              │
      │                                 │  ──── AXI Write (DMAST) ───► │
      │  ──── dmareq[n] (deassert) ──►  │                              │
      │                                 │                              │
```

1. Peripheral asserts `dmareq[n]` when it has data ready (or is ready to receive data)
2. DMAC acknowledges with `dmaack[n]` when it begins servicing the request
3. DMAC performs AXI read/write to move data between peripheral and memory
4. Peripheral deasserts `dmareq[n]` when the transfer is no longer needed

#### 3.4.3 Peripheral Request Instructions

Special load/store instructions are used with peripheral requests:

- **DMALDP[B|S]:** Load from peripheral (waits for `dmareq[n]` before reading)
- **DMASTP[B|S]:** Store to peripheral (waits for `dmareq[n]` before writing)

These instructions synchronize data movement with the peripheral's readiness, preventing data
overrun or underrun.

---

## 4. DMA Channels

### 4.1 Overview

The DMA-330 supports a **configurable number of independent DMA channels**, ranging from
**1 to 8 channels**. The exact number is set at SoC implementation time through a hardware
configuration parameter and cannot be changed at runtime.

Each DMA channel operates as an **autonomous, concurrent thread of execution** — multiple
channels can be active simultaneously, performing independent DMA transfers in parallel.

### 4.2 Channel Thread Model

The DMAC uses a **thread-based execution model** with two types of threads:

| Thread Type         | Count        | Purpose                                              |
|---------------------|--------------|------------------------------------------------------|
| **Manager Thread**  | Exactly 1    | Controls DMAC-wide operations, starts channels       |
| **DMA Channel Thread** | 1–8      | Executes DMA instruction sequences for data transfer |

#### 4.2.1 Manager Thread

The **manager thread** is a special thread that:

- **Does NOT perform data transfers** — it only manages the DMAC
- **Executes a fixed boot routine** on reset (run-from-reset capability)
- **Starts DMA channel threads** using the `DMAGO` instruction, which specifies:
  - Target channel number
  - Starting instruction address (initial PC value)
  - Security attribute (secure or non-secure)
- **Handles events** from channel threads via `DMAWFE` (Wait For Event) instruction
- **Manages faults** — detects and processes fault conditions across all channels
- Has its own set of registers independent from DMA channel registers

The manager thread's behavior is controlled by writing instructions to a special region in
system memory (or by the built-in boot routine), and then enabling the DMAC.

#### 4.2.2 DMA Channel Threads

Each of the **1 to 8 DMA channel threads** is an independent execution unit:

```
  Channel Thread n (n = 0 .. N-1)
  ┌─────────────────────────────────────────┐
  │  Program Counter (PC)                   │ ← Points to next instruction in memory
  │  Channel Registers:                     │
  │    SA  — Source Address (32-bit)        │
  │    DA  — Destination Address (32-bit)   │
  │    TC  — Transfer Count                 │
  │  Loop Counter 0, Loop Counter 1         │
  │  Channel State (FSM)                    │
  │  Security Attribute (S/NS)              │
  │  Instruction Buffer (FIFO)              │ ← Pre-fetches DMA instructions
  └─────────────────────────────────────────┘
```

**Per-channel resources:**

| Resource               | Description                                                     |
|-------------------------|-----------------------------------------------------------------|
| **Program Counter (PC)** | 32-bit pointer to the next DMA instruction to execute in system memory |
| **Source Address (SA)**  | Current source address for load operations                      |
| **Destination Address (DA)** | Current destination address for store operations           |
| **Transfer Count (TC)**  | Remaining number of data items to transfer                     |
| **Loop Counter 0 / 1**  | Two nested loop counters for DMALP/DMALPEND instructions       |
| **Channel State (FSM)**  | Current operating state of the channel thread                   |
| **Security Attribute**   | Set at channel start (DMAGO) — determines if channel is Secure or Non-secure |
| **Instruction Buffer**   | FIFO queue that holds pre-fetched, decoded DMA instructions    |

### 4.3 Channel Execution Flow

```
  CPU                        Manager Thread                   Channel Thread
  ───                        ──────────────                   ──────────────
   │                              │                               │
   │  Write DMAC CR0-CR4          │                               │
   │  (configuration)             │                               │
   │                              │                               │
   │  Write DMA instruction       │                               │
   │  sequence to memory          │                               │
   │                              │                               │
   │  Write DBGINST[0,1]          │                               │
   │  (DMAGO instruction)         │                               │
   │  ───────────────────────►    │                               │
   │                              │  Execute DMAGO                │
   │                              │  ──────────────────────────►  │
   │                              │                               │  PC ← start_addr
   │                              │                               │  State ← Executing
   │                              │                               │
   │                              │                               │  Fetch instruction
   │                              │                               │  Execute DMALD...
   │                              │                               │  Execute DMAST...
   │                              │                               │  ...
   │                              │                               │  Execute DMAEND
   │                              │                               │  State ← Stopped
   │                              │                               │
   │  ◄── irq (completion) ──────────────────────────────────────────┘
   │                              │                               │
```

### 4.4 Channel Instruction Buffer

Each channel has an associated **instruction buffer** (FIFO queue) that decouples instruction
fetch from instruction execution:

- **Purpose:** Pre-fetches and decodes DMA instructions from system memory before they are
  needed, hiding AXI fetch latency
- **Operation:** When a channel thread is in the Executing state, the DMAC proactively fetches
  upcoming instructions and places them in the channel's instruction buffer
- **Benefit:** Allows pipelined operation — while the current instruction's AXI data transfer
  is in progress, the next instruction can already be decoded and waiting in the buffer
- **Size:** Buffer depth is a configuration parameter (implementation-specific)

### 4.5 Channel States

Each channel thread has its own state machine. The primary states are:

| State               | Description                                                      |
|---------------------|------------------------------------------------------------------|
| **Stopped**         | Channel is idle. Not executing any instructions.                 |
| **Executing**       | Channel is actively fetching and executing DMA instructions.     |
| **Cache Miss**      | Channel is waiting for an instruction cache fill from memory.    |
| **Waiting for Event** | Channel is paused, waiting for a `DMAWFE`/`DMASEV` event.     |
| **At Barrier**      | Channel is waiting at a `DMARMB`/`DMAWMB` barrier.               |
| **Fault Completing** | Channel encountered a fault and is completing current operation. |
| **Fault (Locked)**   | Channel is locked due to an unresolvable fault.                 |

A channel transitions from **Stopped** to **Executing** when the manager thread executes
`DMAGO`. It returns to **Stopped** when it executes `DMAEND` or encounters a fault.

### 4.6 Channel Security

When a channel is started via `DMAGO`, the manager thread assigns a **security attribute**:

- **Secure channels:** Can access both secure and non-secure memory/peripheral regions
- **Non-secure channels:** Can only access non-secure memory/peripheral regions

This security attribute remains fixed for the lifetime of the channel's execution until the
channel is stopped and restarted. The security state of each channel is visible in the
`SAR` (Security Attribute Register) fields of the Channel Status registers.

---

## 5. MFIFO Data Buffer

### 5.1 Overview

The **MFIFO (Multi-FIFO)** is a shared data buffer inside the DMAC that temporarily stores data
during DMA transfers. It acts as an elastic buffer between AXI read (load) and AXI write (store)
operations, allowing the DMAC to decouple the source read timing from the destination write timing.

The MFIFO is a **single shared resource** used by all active DMA channels simultaneously. It is
not partitioned per-channel — instead, the DMAC dynamically manages buffer allocation across
channels based on demand.

### 5.2 Purpose

The MFIFO serves several key purposes:

| Purpose                  | Description                                                      |
|--------------------------|------------------------------------------------------------------|
| **Data buffering**       | Holds data read from source until it can be written to destination |
| **Bus decoupling**       | Allows AXI reads and writes to proceed at different rates        |
| **Burst optimization**   | Enables the DMAC to accumulate data for efficient AXI bursting   |
| **Multi-channel sharing** | All channels share the same buffer pool, maximizing utilization |
| **Flow control**         | Provides elasticity for peripheral-paced transfers               |

### 5.3 Configurable Depth

The total depth (in bytes) of the MFIFO is a **configuration parameter set at implementation
time**. This parameter determines the maximum amount of data the MFIFO can hold at any moment
across all channels.

- **Minimum depth:** Must be sufficient to hold at least one complete burst for a single channel
- **Recommended depth:** Depends on the number of channels, typical burst sizes, and system
  latency requirements
- **Trade-off:** Larger MFIFO → better performance under contention, but more silicon area

The MFIFO depth is reported in the DMAC configuration register `CRD` at runtime, allowing
software to query the available buffer space.

### 5.4 Data Flow: DMALD → MFIFO → DMAST

The MFIFO is central to the data movement pipeline. The flow for a typical memory-to-memory
DMA transfer is:

```
   Source Memory              DMAC (MFIFO)              Destination Memory
   ──────────────              ────────────              ──────────────────
         │                          │                           │
         │    AXI Read Burst        │                           │
         │ ◄─────────────────────── │                           │
         │                          │                           │
         │  Data beats (burst)      │                           │
         │ ────────────────────────►│                           │
         │                          │   MFIFO fills             │
         │                          │   ┌───┬───┬───┬───┐      │
         │                          │   │ D0│ D1│ D2│ D3│      │
         │                          │   └───┴───┴───┴───┘      │
         │                          │                           │
         │                          │   AXI Write Burst         │
         │                          │ ─────────────────────────►│
         │                          │                           │
         │                          │   Data beats (burst)      │
         │                          │ ─────────────────────────►│
         │                          │   MFIFO drains            │
         │                          │                           │
```

**Step-by-step flow:**

1. **DMALD (Load):** The channel thread executes a `DMALD` instruction
   - The DMAC issues an AXI read burst to the source address (from channel's SA register)
   - The read data is placed into the MFIFO
   - The SA register is automatically incremented by the burst size × beat count

2. **MFIFO Buffering:** Data resides in the MFIFO temporarily
   - Multiple channels may have data in the MFIFO simultaneously
   - The DMAC tracks which data belongs to which channel
   - Data ordering is maintained per-channel (FIFO order)

3. **DMAST (Store):** The channel thread executes a `DMAST` instruction
   - The DMAC takes data from the MFIFO for this channel
   - It issues an AXI write burst to the destination address (from channel's DA register)
   - The DA register is automatically incremented by the burst size × beat count

### 5.5 MFIFO Sharing Model

Since all channels share a single MFIFO, the following rules apply:

- **No fixed partitioning:** Channels do not have reserved MFIFO space. Buffer allocation is
  dynamic and demand-driven.
- **Fairness:** The DMAC arbiter ensures that no single channel can monopolize the MFIFO.
- **Back-pressure:** If the MFIFO is full, load operations stall until space becomes available
  from pending store operations completing.
- **Starvation prevention:** The DMAC prioritizes channels whose MFIFO entries are oldest, ensuring
  forward progress.

### 5.6 MFIFO and Peripheral Transfers

For peripheral-paced transfers (using `DMALDP`/`DMASTP`), the MFIFO plays an additional role:

- **Peripheral → Memory:** When a peripheral asserts `dmareq`, the DMAC reads peripheral data
  into the MFIFO. Once sufficient data is accumulated (or the peripheral transfer completes),
  the DMAC writes it to memory.
- **Memory → Peripheral:** The DMAC pre-fetches data from memory into the MFIFO. When the
  peripheral asserts `dmareq`, data is drained from the MFIFO and written to the peripheral.

This allows the DMAC to smooth out the rate mismatch between fast AXI memory accesses and
slower peripheral timing.

### 5.7 MFIFO Configuration Registers

| Register   | Description                                        |
|------------|----------------------------------------------------|
| `CRD`      | DMA Configuration Register — reports MFIFO data buffer depth and interface data widths |

The `CRD` register is read-only and reflects the hardware configuration chosen at
implementation time.

---

## 6. Instruction Set

### 6.1 Overview

Unlike traditional DMA controllers that use fixed Linked-List Item (LLI) descriptors, the
DMA-330 uses a **programmable instruction set** to define DMA operations. This approach provides
significantly greater flexibility, allowing:

- **Arbitrary transfer sequences** — not limited to fixed descriptor formats
- **Conditional execution** — branches, loops, and event waits
- **Dynamic address manipulation** — increment, add offsets during execution
- **Variable-length instructions** — minimizes program memory footprint

DMA programs are stored in **system memory** and fetched by the DMAC via the AXI master
interface. The DMAC decodes and executes instructions one at a time per channel thread.

### 6.2 Instruction Encoding Format

DMA-330 instructions are **variable-length**, encoded as a sequence of bytes:

```
  ┌─────────┬──────────────┬─────────────────────────┐
  │ Opcode  │   Operand(s) │   Optional Immediate(s) │
  │ (1 byte)│  (0-1 bytes) │     (0-5 bytes)         │
  └─────────┴──────────────┴─────────────────────────┘
```

| Field                | Size      | Description                                       |
|----------------------|-----------|---------------------------------------------------|
| **Opcode**           | 1 byte    | Identifies the instruction type                   |
| **Operand(s)**       | 0–1 byte  | Register specifier, condition code, or modifier   |
| **Immediate value(s)**| 0–5 bytes| Literal values (addresses, counters, offsets)     |

Total instruction length ranges from **1 byte** (e.g., `DMAEND`) to **6 bytes**
(e.g., `DMAMOV` with a 32-bit immediate).

### 6.3 Complete Instruction Reference

#### 6.3.1 Instruction Summary Table

| Mnemonic      | Opcode | Length | Description                                        | Thread Type    |
|---------------|--------|--------|----------------------------------------------------|----------------|
| `DMAMOV`      | `0xBC` | 6 B    | Move 32-bit value to channel register              | Channel        |
| `DMAADDH`     | `0x04` | 3 B    | Add 16-bit immediate to source or destination addr | Channel        |
| `DMAADNH`     | —      | 3 B    | Add negative 16-bit value to address               | Channel        |
| `DMALD`       | `0x04` | 1-2 B  | Load (read) data from source address               | Channel        |
| `DMALDS`      | —      | 1-2 B  | Load with shared transaction                       | Channel        |
| `DMALDB`      | —      | 1-2 B  | Load with burst length override                    | Channel        |
| `DMALDP`      | —      | 2 B    | Load from peripheral (waits for dmareq)            | Channel        |
| `DMAST`       | `0x08` | 1-2 B  | Store (write) data to destination address          | Channel        |
| `DMASTS`      | —      | 1-2 B  | Store with shared transaction                      | Channel        |
| `DMASTB`      | —      | 1-2 B  | Store with burst length override                   | Channel        |
| `DMASTP`      | —      | 2 B    | Store to peripheral (waits for dmareq)             | Channel        |
| `DMAEND`      | `0x00` | 1 B    | End of DMA program, stop channel                   | Channel        |
| `DMAFLUSHP`   | `0x35` | 2 B    | Flush peripheral request lines                     | Channel        |
| `DMAGO`       | `0xA0` | 6 B    | Start a DMA channel thread (go)                    | Manager        |
| `DMALP`       | `0x20` | 2-5 B  | Start a loop (loop counter 0 or 1)                 | Channel        |
| `DMALPEND`    | `0x28` | 2-3 B  | Loop end — decrement counter and branch if ≠ 0     | Channel        |
| `DMASEV`      | `0x34` | 2 B    | Send event (signal interrupt/event)                | Channel        |
| `DMAWFE`      | `0x36` | 2 B    | Wait for event (block until event received)        | Channel/Mgr    |
| `DMANOP`      | `0x18` | 1 B    | No operation                                       | Channel/Mgr    |
| `DMARMB`      | —      | 1 B    | Read memory barrier                                | Channel        |
| `DMAWMB`      | —      | 1 B    | Write memory barrier                               | Channel        |
| `DMAKILL`     | —      | 1 B    | Terminate a channel thread immediately             | Manager        |

> **Note:** Some opcodes are simplified; refer to ARM DDI 0424 for exact encoding bit fields.
> Certain instructions share base opcodes with modifier bits.

### 6.4 Detailed Instruction Descriptions

#### 6.4.1 DMAMOV — Move to Channel Register

**Format:** `DMAMOV <register>, <32-bit_immediate>`  
**Encoding:** 6 bytes (1 opcode + 1 register + 4 bytes immediate)  
**Opcode:** `0xBC`  

Sets a channel register to a 32-bit value. The target registers are:

| Register Code | Register Name          | Description                       |
|---------------|------------------------|-----------------------------------|
| `0b00` (SA)   | Source Address         | Address for DMALD operations      |
| `0b01` (DA)   | Destination Address    | Address for DMAST operations      |
| `0b10` (CC)   | Channel Control        | Burst size, address increment, etc. |

**Channel Control Register (CC) bit fields:**

| Bits     | Field               | Description                             |
|----------|----------------------|-----------------------------------------|
| `[31:28]`| Source burst size    | 0=1, 1=2, 2=4, 3=8, 4=16, 5=32, ...    |
| `[27:24]`| Source burst length  | Number of beats − 1 (1-16)             |
| `[23:20]`| Destination burst size| Same encoding as source                |
| `[19:16]`| Destination burst length| Same encoding as source              |
| `[15:14]`| Source address increment| 00=increment, 01=decrement, 10=none |
| `[13:12]`| Destination address increment| Same encoding as source          |

**Example:**
```
  DMAMOV  SA, 0x1000_0000    ; Set source address to 0x10000000
  DMAMOV  DA, 0x2000_0000    ; Set destination address to 0x20000000
  DMAMOV  CC, 0x0C0C_0100    ; 4-byte burst, both addresses incrementing
```

#### 6.4.2 DMALD / DMALDB / DMALDS — Load Data

**Format:** `DMALD[B|S] [condition]`  
**Encoding:** 1–2 bytes (opcode + optional condition byte)  
**Opcode:** `0x04` (base)  

Reads data from the source address (SA) into the MFIFO.

| Variant   | Description                                    |
|-----------|------------------------------------------------|
| `DMALD`   | Standard load — AXI read from SA into MFIFO     |
| `DMALDB`  | Load with user-specified burst length           |
| `DMALDS`  | Load using AXI shared (modifiable) transaction  |

**Behavior:**
1. DMAC issues an AXI read burst to the address in the SA register
2. Burst size and length are determined by the Channel Control (CC) register
3. Data is placed into the MFIFO
4. SA is automatically incremented/decremented based on CC settings
5. The transfer count (TC) is decremented

**Conditional execution:** The optional condition byte allows the load to execute only when
a specific condition is true (e.g., based on the state of the peripheral request line).

#### 6.4.3 DMAST / DMASTB / DMASTS — Store Data

**Format:** `DMAST[B|S] [condition]`  
**Encoding:** 1–2 bytes (opcode + optional condition byte)  
**Opcode:** `0x08` (base)  

Writes data from the MFIFO to the destination address (DA).

| Variant   | Description                                    |
|-----------|------------------------------------------------|
| `DMAST`   | Standard store — AXI write from MFIFO to DA     |
| `DMASTB`  | Store with user-specified burst length          |
| `DMASTS`  | Store using AXI shared transaction              |

**Behavior:**
1. DMAC takes data from the MFIFO (for this channel)
2. Issues an AXI write burst to the address in the DA register
3. Burst parameters come from the CC register
4. DA is automatically incremented/decremented
5. TC is decremented

#### 6.4.4 DMALDP / DMASTP — Peripheral Load/Store

**Format:** `DMALDP <peripheral_num>` / `DMASTP <peripheral_num>`  
**Encoding:** 2 bytes  

These are the **peripheral-aware** variants of load and store. They behave like `DMALD`/`DMAST`
but additionally:

- **Wait** for the peripheral request line (`dmareq[n]`) to be asserted before proceeding
- **Assert** the acknowledge signal (`dmaack[n]`) during the transfer
- Use the peripheral number to index into the request interface

These are essential for flow-controlled transfers to/from peripherals like UART, SPI, I2S.

#### 6.4.5 DMAADDH — Add Half-word to Address

**Format:** `DMAADDH <register>, <16-bit_immediate>`  
**Encoding:** 3 bytes  

Adds a 16-bit unsigned value to the source or destination address register.

| Register Code | Target         |
|----------------|----------------|
| `0b0`          | Source Address (SA) |
| `0b1`          | Destination Address (DA) |

**Use case:** Implementing scatter-gather by adding non-contiguous offsets to the address
registers between transfers.

**Example:**
```
  DMAADDH  SA, #0x0010     ; Add 16 bytes to source address (skip gap)
```

#### 6.4.6 DMAEND — End Program

**Format:** `DMAEND`  
**Encoding:** 1 byte (`0x00`)  

Terminates the DMA program on the current channel thread. The channel transitions to the
**Stopped** state.

- No operands required
- Must be the last instruction in every DMA program
- After `DMAEND`, the channel must be restarted with `DMAGO` to execute again

#### 6.4.7 DMALP / DMALPEND — Loop

**Format:** `DMALP[0|1] <loop_count>` / `DMALPEND[0|1] <backwards_jump>`  
**Encoding:** `DMALP` 2–5 bytes, `DMALPEND` 2–3 bytes  

Implements a **hardware loop** with zero overhead (no branch penalty).

| Component     | Description                                              |
|---------------|----------------------------------------------------------|
| `DMALP[0|1]`  | Loop start — loads loop counter 0 or 1 with count value  |
| `DMALPEND[0|1]`| Loop end — decrements counter, branches to loop start if ≠ 0 |

- **Two nested loops:** Counter 0 (inner) and Counter 1 (outer) allow two levels of nesting
- **Loop count:** Encoded as 8-bit or 32-bit immediate (determines instruction length)
- **Backwards jump:** `DMALPEND` encodes a relative jump offset back to the instruction after
  the matching `DMALP`

**Example (transfer 256 items in blocks of 16):**
```
  DMAMOV  SA, 0x1000_0000
  DMAMOV  DA, 0x2000_0000
  DMALP   1, #16            ; Outer loop: 16 iterations
    DMALP  0, #16           ; Inner loop: 16 iterations
      DMALD                 ; Load one burst
      DMAST                 ; Store one burst
    DMALPEND  0             ; End inner loop
  DMALPEND  1               ; End outer loop
  DMAEND                     ; Done: 16 × 16 = 256 transfers
```

#### 6.4.8 DMAFLUSHP — Flush Peripheral

**Format:** `DMAFLUSHP <peripheral_num>`  
**Encoding:** 2 bytes (`0x35` + periph_num)  

Clears (flushes) the state of the specified peripheral request line. This ensures that any
stale request signals are cleared before starting a new transfer sequence.

#### 6.4.9 DMAGO — Go (Start Channel)

**Format:** `DMAGO <channel_num>, <start_address>, [security]`  
**Encoding:** 6 bytes  
**Thread:** Manager thread only  

Starts a DMA channel thread executing at the specified address.

| Field              | Description                                      |
|--------------------|--------------------------------------------------|
| Channel number     | 0–7 (which channel to start)                    |
| Start address      | 32-bit initial value for the channel's PC        |
| Security attribute | Secure (0) or Non-secure (1)                     |

**Behavior:**
1. Manager thread decodes `DMAGO`
2. Target channel thread's PC is set to the start address
3. Channel security attribute is set
4. Channel transitions from **Stopped** to **Executing**
5. Channel begins fetching and executing instructions

#### 6.4.10 DMASEV — Send Event

**Format:** `DMASEV <event_num>`  
**Encoding:** 2 bytes (`0x34` + event_num)  

Sends an event to signal completion or a specific condition. The event can:
- Trigger an interrupt (if enabled in `INTEN`)
- Wake up another channel thread waiting with `DMAWFE`

#### 6.4.11 DMAWFE — Wait For Event

**Format:** `DMAWFE <event_num>`  
**Encoding:** 2 bytes (`0x36` + event_num)  

Blocks the current thread until the specified event is received. The channel transitions to
the **Waiting for Event** state and consumes no AXI bandwidth while waiting.

- Can be used by both channel threads and the manager thread
- When the event is received (via `DMASEV` from another channel), the thread resumes execution

#### 6.4.12 DMANOP — No Operation

**Format:** `DMANOP`  
**Encoding:** 1 byte (`0x18`)  

Does nothing. Used for timing padding or as a placeholder.

#### 6.4.13 DMARMB / DMAWMB — Memory Barriers

| Instruction | Encoding | Description                                          |
|-------------|----------|------------------------------------------------------|
| `DMARMB`    | 1 byte   | **Read Memory Barrier** — ensures all prior loads complete before subsequent loads begin |
| `DMAWMB`    | 1 byte   | **Write Memory Barrier** — ensures all prior stores complete before subsequent stores begin |

These implement AXI memory ordering semantics. The channel transitions to the **At Barrier**
state until the barrier condition is satisfied.

#### 6.4.14 DMAKILL — Kill Channel

**Format:** `DMAKILL`  
**Encoding:** 1 byte  
**Thread:** Manager thread only  

Immediately terminates a DMA channel thread. The channel transitions to **Stopped** regardless
of its current state. Used for error recovery or forced termination.

### 6.5 Example DMA Programs

#### 6.5.1 Simple Memory-to-Memory Copy (128 bytes)

```
  ; Simple memcpy: 128 bytes from 0x10000000 to 0x20000000
  DMAMOV  SA, 0x1000_0000       ; Source address
  DMAMOV  DA, 0x2000_0000       ; Destination address
  DMAMOV  CC, 0x0440_0C01       ; src_burst=4B, dst_burst=4B, 16 beats, incrementing
  DMALP   0, #8                 ; Loop 8 times (8 × 16 = 128 bytes)
    DMALD                        ; Read burst from source
    DMAST                        ; Write burst to destination
  DMALPEND 0
  DMAEND                        ; Done
```

#### 6.5.2 Peripheral-to-Memory Transfer (UART RX)

```
  ; Receive 64 bytes from UART (peripheral 0) to memory at 0x30000000
  DMAMOV  SA, 0x4000_0000       ; UART data register address (memory-mapped)
  DMAMOV  DA, 0x3000_0000       ; Destination buffer in RAM
  DMAMOV  CC, 0x0000_0001       ; Single byte transfers, DA increments
  DMAFLUSHP 0                   ; Clear peripheral request state
  DMALP   0, #64                ; Loop 64 times (64 bytes)
    DMALDP  0                    ; Load byte from UART, wait for dmareq[0]
    DMAST                        ; Store byte to memory
  DMALPEND 0
  DMAEND
```

#### 6.5.3 Scatter-Gather (linked buffers)

```
  ; Copy 3 scattered 32-byte blocks to contiguous destination
  ; Source blocks at 0x1000, 0x2000, 0x3000 → Dest at 0x4000, 0x4020, 0x4040
  DMAMOV  CC, 0x0C0C_0100       ; 4-byte burst, 8 beats = 32 bytes per block

  ; Block 1
  DMAMOV  SA, 0x0000_1000
  DMAMOV  DA, 0x0000_4000
  DMALD
  DMAST

  ; Block 2
  DMAMOV  SA, 0x0000_2000
  DMALD
  DMAST

  ; Block 3
  DMAMOV  SA, 0x0000_3000
  DMALD
  DMAST

  DMAEND
```

---

## 7. Register Map

### 7.1 Overview

The DMAC registers are accessed through the **APB slave interfaces**. Each APB interface
occupies a **4 KB** (0x000–0xFFF) address space. The register space is divided into **six
major sections**:

| Section | Offset Range    | Description                                    |
|---------|-----------------|------------------------------------------------|
| 1       | `0x000–0x04C`  | **Control Registers** — DMAC control and status |
| 2       | `0x100–0x1FC`  | **Channel Thread Status Registers**             |
| 3       | `0x200–0x2FC`  | **AXI and Loop Counter Status Registers**       |
| 4       | `0x300–0x3FC`  | **Debug Registers**                             |
| 5       | `0x400–0x4FF`  | **Configuration Registers** (CR0–CR4, CRD)      |
| 6       | `0xFE0–0xFFC`  | **PrimeCell ID Registers**                      |

> **Note:** Addresses not listed in the tables below are reserved. Accessing reserved addresses
> returns undefined values and may cause a slave error.

### 7.2 Section 1: Control Registers (0x000–0x04C)

These registers control overall DMAC operation and report global status.

| Offset   | Name             | Access   | Description                                        |
|----------|------------------|----------|----------------------------------------------------|
| `0x000`  | `DSR`            | R        | DMA Status Register — DMAC operating state          |
| `0x004`  | `DPC`            | R        | DMA Program Counter — Manager thread PC             |
| `0x008`  | `INTEN`          | R/W      | Interrupt Enable — per-event interrupt mask          |
| `0x010`  | `INT_EVENT_RIS`  | R        | Interrupt Event Raw Status — event pending before mask |
| `0x014`  | `INTMIS`         | R        | Interrupt Masked Status — event pending after mask   |
| `0x018`  | `INTCLR`         | W        | Interrupt Clear — write 1 to clear corresponding event |
| `0x020`  | `FSRD`           | R        | Fault Status DMAC — global fault indicators          |
| `0x024`  | `FSRC`           | R        | Fault Status per Channel — per-channel fault bits    |
| `0x028`  | `FTRD`           | R/W      | Fault Type DMAC — type of DMAC-level fault           |
| `0x030`  | `FTC[n]`         | R/W      | Fault Type per Channel — type of fault on channel n  |
| `0x040`  | `CS[n]`          | R        | Channel Status — operating state of channel n        |
| `0x044`  | `CPC[n]`         | R        | Channel Program Counter — PC of channel n            |
| `0x048`  | `SA[n]`          | R        | Source Address — current SA for channel n            |
| `0x04C`  | `DA[n]`          | R        | Destination Address — current DA for channel n       |

> **Note:** `[n]` indicates per-channel registers. The number of valid channel registers depends
> on the configured number of channels (1–8). Accessing registers for non-existent channels
> returns zero.

### 7.3 Section 2: Channel Thread Status Registers (0x100–0x1FC)

Provides status information for each DMA channel thread.

| Offset   | Name              | Access | Description                                    |
|----------|-------------------|--------|------------------------------------------------|
| `0x100`  | `SAR0`            | R      | Channel 0 Security Attribute Register          |
| `0x104`  | `SAR1`            | R      | Channel 1 Security Attribute Register          |
| ...      | ...               | ...    | (up to SAR7 at 0x11C for 8 channels)           |
| `0x120`  | `CCR0`            | R      | Channel 0 Cache Register — cached instruction  |
| ...      | ...               | ...    | (up to CCR7 at 0x13C)                          |
| `0x140`  | `LC0_0`           | R      | Channel 0 Loop Counter 0 value                 |
| `0x144`  | `LC1_0`           | R      | Channel 0 Loop Counter 1 value                 |
| ...      | ...               | ...    | (up to LC0_7, LC1_7)                           |

### 7.4 Section 3: AXI and Loop Counter Status Registers (0x200–0x2FC)

Provides AXI transaction status and loop counter values for each channel.

| Offset   | Name              | Access | Description                                    |
|----------|-------------------|--------|------------------------------------------------|
| `0x200`  | `AXI_ERR_CLR`     | W      | AXI Error Clear — write to clear AXI error flags|
| `0x208`  | `AXI_ERR_ID`      | R      | AXI Error ID — transaction ID that caused error |
| `0x210`  | `AXI_ERR_DATA`    | R      | AXI Error Data — data value during error        |
| `0x214`  | `AXI_ERR_ADDR`    | R      | AXI Error Address — address of failed transaction|
| `0x220`  | `CH_LC0[n]`       | R      | Channel n Loop Counter 0 current value          |
| `0x224`  | `CH_LC1[n]`       | R      | Channel n Loop Counter 1 current value          |

### 7.5 Section 4: Debug Registers (0x300–0x3FC)

Used for debug and diagnostic purposes.

| Offset   | Name              | Access | Description                                    |
|----------|-------------------|--------|------------------------------------------------|
| `0x300`  | `DBGCMD`          | W      | Debug Command — write to issue debug command    |
| `0x304`  | `DBGINST[0]`      | W      | Debug Instruction 0 — instruction to execute    |
| `0x308`  | `DBGINST[1]`      | W      | Debug Instruction 1 — instruction to execute    |
| `0x30C`  | `DBGCMDINTSTAT`   | R      | Debug Command Interrupt Status                  |
| `0x310`  | `DBGSTATUS`       | R      | Debug Status — debug state of DMAC              |
| `0x314`  | `DBGBPT[n]`       | R/W    | Debug Breakpoint — address breakpoint for channel n |

> **Usage:** The debug registers allow software to:
> - Inject instructions into the manager thread (`DBGINST[0,1]` + `DBGCMD`)
> - Set breakpoints at specific instruction addresses (`DBGBPT`)
> - Query debug status (`DBGSTATUS`)

### 7.6 Section 5: Configuration Registers (0x400–0x4FF)

Read-only registers that report the **implementation-time configuration** of the DMAC.
Software reads these to discover the DMAC's capabilities.

| Offset   | Name    | Access | Description                                              |
|----------|---------|--------|----------------------------------------------------------|
| `0x400`  | `CR0`   | R      | Configuration Register 0 — number of channels, events     |
| `0x404`  | `CR1`   | R      | Configuration Register 1 — address width, burst support    |
| `0x408`  | `CR2`   | R      | Configuration Register 2 — MFIFO depth, data width        |
| `0x40C`  | `CR3`   | R      | Configuration Register 3 — peripheral interface config     |
| `0x410`  | `CR4`   | R      | Configuration Register 4 — security, boot configuration    |
| `0x414`  | `CRD`   | R      | DMA Configuration — MFIFO depth and data widths            |

#### 7.6.1 CR0 — Number of Channels and Events

| Bits     | Field               | Description                                    |
|----------|----------------------|------------------------------------------------|
| `[7:0]`  | `num_dma_chan`       | Number of DMA channels (1–8)                   |
| `[15:8]` | `num_periph_req`     | Number of peripheral request interfaces        |
| `[23:16]`| `num_events`         | Number of event/interrupt lines                |

#### 7.6.2 CR1 — Bus Interface Configuration

| Bits     | Field               | Description                                    |
|----------|----------------------|------------------------------------------------|
| `[3:0]`  | `src_addr_incr`     | Source address increment support (bit mask)     |
| `[7:4]`  | `dst_addr_incr`     | Destination address increment support (bit mask)|
| `[15:8]` | `max_burst_len`     | Maximum AXI burst length supported             |
| `[19:16`]| `addr_width`        | Address bus width in bits (32 or 64)           |

#### 7.6.3 CR2 — MFIFO and Data Width

| Bits     | Field               | Description                                    |
|----------|----------------------|------------------------------------------------|
| `[3:0]`  | `data_width`        | AXI data width (0=32, 1=64, 2=128, 3=256 bits) |
| `[7:4]`  | `data_buffer_depth` | MFIFO depth encoded as log2(depth_in_bytes)     |

#### 7.6.4 CR3 — Peripheral Interface Configuration

| Bits     | Field               | Description                                    |
|----------|----------------------|------------------------------------------------|
| `[0]`    | `periph_req_support` | 1 = peripheral request interface present       |
| `[1]`    | `boot_from_addr`    | 1 = manager boot address configurable          |

#### 7.6.5 CR4 — Security Configuration

| Bits     | Field               | Description                                    |
|----------|----------------------|------------------------------------------------|
| `[0]`    | `security_support`  | 1 = TrustZone security enabled                 |
| `[1]`    | `managed_ns_events` | 1 = non-secure events managed by secure only   |
| `[7:2]`  | `reserved`          | Reserved                                       |

### 7.7 Section 6: PrimeCell ID Registers (0xFE0–0xFFC)

Standard ARM PrimeCell identification registers, following the AMBA PrimeCell convention.

| Offset   | Name            | Value     | Description                        |
|----------|-----------------|-----------|------------------------------------|
| `0xFE0`  | `periph_id_0`   | `0x30`    | Peripheral ID byte 0               |
| `0xFE4`  | `periph_id_1`   | `0x33`    | Peripheral ID byte 1 (='3')        |
| `0xFE8`  | `periph_id_2`   | `0x24`    | Peripheral ID byte 2               |
| `0xFEC`  | `periph_id_3`   | `0x00`    | Peripheral ID byte 3               |
| `0xFF0`  | `pcell_id_0`    | `0x0D`    | PrimeCell ID byte 0                |
| `0xFF4`  | `pcell_id_1`    | `0xF0`    | PrimeCell ID byte 1                |
| `0xFF8`  | `pcell_id_2`    | `0x05`    | PrimeCell ID byte 2                |
| `0xFFC`  | `pcell_id_3`    | `0xB1`    | PrimeCell ID byte 3                |

> The 4-byte PrimeCell ID reads as `0xB105F00D` ("ARMIDO" in little-endian), which is the
> standard ARM PrimeCell identification value. The peripheral ID encodes the product code
> (PL330 = `0x30, 0x33`).

### 7.8 Register Access Summary

```
  4KB APB Address Space
  ┌─────────────────────────────────────┐ 0x000
  │  Control Registers (DSR, DPC, etc.) │
  │  0x000 - 0x04C                      │
  ├─────────────────────────────────────┤ 0x100
  │  Channel Thread Status              │
  │  (SAR, CCR, LC0, LC1 per channel)  │
  │  0x100 - 0x1FC                      │
  ├─────────────────────────────────────┤ 0x200
  │  AXI & Loop Counter Status          │
  │  0x200 - 0x2FC                      │
  ├─────────────────────────────────────┤ 0x300
  │  Debug Registers                    │
  │  (DBGCMD, DBGINST, etc.)           │
  │  0x300 - 0x3FC                      │
  ├─────────────────────────────────────┤ 0x400
  │  Configuration Registers            │
  │  (CR0-CR4, CRD)                    │
  │  0x400 - 0x4FF                      │
  ├─────────────────────────────────────┤
  │          ... Reserved ...           │
  ├─────────────────────────────────────┤ 0xFE0
  │  PrimeCell ID Registers             │
  │  0xFE0 - 0xFFC                      │
  └─────────────────────────────────────┘ 0xFFF
```

---

## 8. Operating States

### 8.1 Overview

The DMA-330 DMAC uses **finite state machines (FSMs)** to control its operation at two levels:

1. **DMAC-level state** — overall controller state (managed by the manager thread)
2. **Channel-level states** — per-channel thread execution states

Each channel thread independently transitions through its own set of states based on the
instructions it executes and external events.

### 8.2 DMAC-Level Operating States

The overall DMAC has the following top-level states:

| State                 | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| **Disabled**          | DMAC is not operational. Clocks may be gated. Entered after reset before enabling. |
| **Enabled (Idle)**    | DMAC is enabled but no channels are executing. Manager thread is idle. |
| **Enabled (Active)**  | One or more channel threads are executing DMA programs.          |

The DMAC transitions from Disabled → Enabled when software enables it (via the `DSR` register).
It returns to Disabled when explicitly disabled or on reset.

### 8.3 Channel Thread FSM States

Each DMA channel thread has its own independent state machine. The following states are defined:

| State Code | State Name              | Description                                                    |
|------------|-------------------------|----------------------------------------------------------------|
| `0b000`    | **Stopped**             | Channel is idle. Not executing any instructions. PC is undefined until restarted. |
| `0b001`    | **Executing**           | Channel is actively fetching and executing DMA instructions. The channel processes instructions from its instruction buffer. |
| `0b010`    | **Cache Miss**          | Channel requires an instruction that is not in the cache. Waiting for an AXI read to fetch the instruction from system memory. |
| `0b011`    | **Updating PC**         | Channel is updating its Program Counter (e.g., after a loop branch or jump). Transient state before returning to Executing. |
| `0b100`    | **Waiting for Event**   | Channel has executed `DMAWFE` and is blocked, waiting for the specified event to be signaled by `DMASEV`. |
| `0b101`    | **At Barrier**          | Channel has executed `DMARMB` or `DMAWMB` and is waiting for all prior AXI transactions to complete. |
| `0b110`    | **Waiting for Peripheral Request** | Channel has executed `DMALDP` or `DMASTP` and is waiting for the peripheral to assert `dmareq[n]`. |
| `0b111`    | **Reserved**            | —                                                               |

### 8.4 Fault-Related States

In addition to the normal operating states, channels can enter fault states when errors occur:

| State Name              | Description                                                    |
|--------------------------|----------------------------------------------------------------|
| **Fault Completing**     | Channel encountered a fault (e.g., AXI error, security violation) and is completing any in-progress AXI transaction before stopping. |
| **Fault (Locked)**       | Channel has completed fault handling and is now locked. It cannot be restarted until the fault is cleared via the Fault Type register (`FTC[n]`). The `DMAKILL` instruction can force a locked channel to Stopped. |

Fault sources include:

| Fault Type               | Cause                                                         |
|--------------------------|---------------------------------------------------------------|
| **AXI Read Error**       | SLVERR or DECERR on an AXI read transaction                  |
| **AXI Write Error**      | SLVERR or DECERR on an AXI write transaction                 |
| **Instruction Decode Error** | Invalid opcode or malformed instruction encoding         |
| **Security Violation**   | Non-secure channel attempting to access secure resource       |
| **MFIFO Overflow/Underflow** | Data buffer exceeded or read when empty                    |
| **Slave Instruction Error** | Invalid instruction issued to the DMAC via debug registers |

### 8.5 State Transition Diagram

```
                          ┌──────────┐
                          │ Stopped  │ ◄──────────────────────────────────────┐
                          └────┬─────┘                                        │
                               │ DMAGO (manager starts channel)              │
                               ▼                                              │
                    ┌─────────────────┐                                       │
             ┌─────►│    Executing    │──────────────────────────────────┐    │
             │      └────┬────────────┘                                  │    │
             │           │                                               │    │
             │    ┌──────┴───────────────┐                               │    │
             │    │                      │                               │    │
             │    ▼                      ▼                               │    │
             │ ┌───────────┐    ┌──────────────────┐                    │    │
             │ │Cache Miss │    │ Waiting for      │                    │    │
             │ │(fetching  │    │ Peripheral Req   │                    │    │
             │ │ from mem) │    │ (DMALDP/DMASTP)  │                    │    │
             │ └─────┬─────┘    └────────┬─────────┘                    │    │
             │       │                   │                              │    │
             │       │ cache filled      │ dmareq[n] asserted           │    │
             │       ▼                   ▼                              │    │
             │  ┌───────────┐    ┌──────────────────┐                  │    │
             │  │ (back to  │    │ (back to          │                  │    │
             │  │Executing) │    │  Executing)       │                  │    │
             │  └───────────┘    └──────────────────┘                  │    │
             │                                                           │    │
             │    ┌──────────────────────┐                               │    │
             │    ▼                      ▼                               │    │
             │ ┌───────────────┐  ┌──────────────┐                       │    │
             │ │Waiting for    │  │ At Barrier   │                       │    │
             │ │Event (DMAWFE) │  │(DMARMB/DMAWMB)│                      │    │
             │ └───────┬───────┘  └──────┬───────┘                       │    │
             │         │                 │                                │    │
             │  DMASEV  │ barrier clear  │                                │    │
             │  received│                 │                                │    │
             │         ▼                 ▼                                │    │
             │  ┌────────────────────────────────┐                       │    │
             │  │       (back to Executing)       │                       │    │
             │  └────────────────────────────────┘                       │    │
             │                                                            │    │
             │                                                            │    │
             │                   Fault occurs ──────────────────────┐     │    │
             │                                                     ▼     ▼    │
             │                                          ┌──────────────┐    │
             │                                          │Fault         │    │
             │                                          │Completing    │    │
             │                                          └──────┬───────┘    │
             │                                                 │ fault      │
             │                                                 │ handling   │
             │                                                 ▼ complete   │
             │                                          ┌──────────────┐    │
             │                                          │Fault (Locked)│    │
             │                                          └──────┬───────┘    │
             │                                                 │ FTC clear  │
             │                                                 │ or DMAKILL │
             └─────────────────────────────────────────────────┴────────────┘

  DMAEND ──────────────────────────────► Stopped
```

### 8.6 Manager Thread States

The manager thread has its own simplified state machine:

| State                | Description                                                    |
|----------------------|----------------------------------------------------------------|
| **Stopped**          | Manager is idle (DMAC disabled or no boot routine)             |
| **Executing**        | Manager is executing its instruction sequence (boot routine or debug commands) |
| **Waiting for Event**| Manager executed `DMAWFE` and is waiting for an event          |
| **Fault Completing** | Manager encountered a fault and is completing                  |
| **Fault (Locked)**   | Manager is locked due to fault, requires fault clear           |

### 8.7 State Register Access

The current state of each channel can be read from:

| Register  | Description                                          |
|-----------|------------------------------------------------------|
| `CS[n]`   | Channel Status — 3-bit FSM state code for channel n  |
| `DSR`     | DMA Status Register — overall DMAC state              |

Software can poll `CS[n]` to determine when a channel reaches **Stopped** (transfer complete)
or detect if it has entered a fault state.

---

## 9. TrustZone Security

### 9.1 Overview

The DMA-330 implements **ARM TrustZone** security technology to prevent non-secure software from
accessing secure data or initiating DMA transfers that target secure memory regions. This is
critical in systems where trusted and untrusted code run simultaneously (e.g., a secure trusted
execution environment alongside a rich OS like Linux).

The security model operates at two levels:

1. **APB interface security** — controls which software can program the DMAC
2. **Channel security attribution** — controls what each DMA channel can access

### 9.2 Dual APB Interface Security Model

The DMAC provides **two physically separate APB slave interfaces**, each operating in a different
security domain:

```
  ┌──────────────────┐                     ┌──────────────────────────┐
  │   Secure World   │                     │                          │
  │   (TrustZone     │    APB Secure       │                          │
  │    Secure FSM)   ├────────────────────►│                          │
  │                  │   (Full access)     │      DMA-330 (DMAC)      │
  └──────────────────┘                     │                          │                                           │
                                           │                          │
  ┌──────────────────┐                     │                          │
  │  Non-secure World│    APB Non-secure   │                          │
  │  (Normal World   ├────────────────────►│                          │
  │   OS / Apps)     │  (Restricted access)│                          │
  └──────────────────┘                     └──────────────────────────┘
```

| APB Interface   | Security State | Access Scope                                        |
|-----------------|----------------|-----------------------------------------------------|
| **Secure APB**  | Secure         | All registers, all channels, fault info, debug      |
| **Non-secure APB** | Non-secure  | Only non-secure channels and non-secure registers   |

**Secure APB** (accessed by secure-world software):
- Can read/write all DMAC registers
- Can start and control both secure and non-secure channels
- Can read fault status for all channels
- Can access debug registers
- Can modify interrupt enables and security configuration

**Non-secure APB** (accessed by normal-world software):
- Can only access registers for channels configured as non-secure
- Cannot view or modify secure channel state
- Cannot access debug registers or fault information for secure channels
- Cannot change the security configuration of the DMAC

Any attempt by the Non-secure APB to access secure resources results in a **security fault**
and the transaction is blocked.

### 9.3 Channel Security Attribution

Each DMA channel is assigned a **security attribute** when it is started. This attribute
determines what memory and peripheral regions the channel can access during its execution.

#### 9.3.1 Setting Channel Security

Channel security is set by the **manager thread** when it executes `DMAGO`:

```
  DMAGO <channel_num>, <start_address>, <ns_bit>
```

| `ns_bit` Value | Security Attribute | Access Permission                            |
|-----------------|--------------------|----------------------------------------------|
| `0`             | **Secure**         | Can access both secure and non-secure memory/peripherals |
| `1`             | **Non-secure**     | Can only access non-secure memory/peripherals           |

The security attribute is **fixed for the lifetime** of the channel's execution. It cannot be
changed while the channel is running. To change a channel's security, it must be stopped
(`DMAEND` or `DMAKILL`) and restarted with a new `DMAGO`.

#### 9.3.2 AXI Transaction Security

When a DMA channel performs AXI read/write transactions, the **AXI AxPROT** signals encode
the security attribute:

| Channel Security | AxPROT[1] (Non-secure bit) | Meaning                    |
|------------------|----------------------------|----------------------------|
| Secure           | `0`                        | Access is secure           |
| Non-secure       | `1`                        | Access is non-secure only  |

AXI interconnects and memory controllers use AxPROT to enforce access permissions, blocking
non-secure channels from accessing secure memory regions at the system level.

#### 9.3.3 Security Enforcement

The DMAC enforces the following security rules:

1. **Non-secure channel → Secure resource:** AXI transaction is rejected by the interconnect
   or peripheral, causing a fault. The DMAC reports this as a security violation fault.
2. **Non-secure APB → Secure channel register:** Access is blocked; returns slave error or
   zero (implementation-defined).
3. **DMASEV from non-secure channel:** Only visible to non-secure event registers. Secure
   event registers are not affected.
4. **DMAWFE in non-secure channel:** Only responds to non-secure events.

### 9.4 Boot-Time Security Configuration

The DMA-330 supports a **run-from-reset** capability that allows the DMAC to begin executing
a boot routine immediately after system reset, without waiting for CPU intervention.

#### 9.4.1 Secure Boot Sequence

```
  System Reset
       │
       ▼
  ┌──────────────────────────────┐
  │  DMAC enters Disabled state  │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Secure firmware enables DMAC│
  │  (via Secure APB)            │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Manager thread executes     │
  │  boot routine from secure    │
  │  memory (TrustZone protected)│
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Boot routine configures     │
  │  secure DMA channels and     │
  │  transfers (e.g., load secure│
  │  OS image into protected RAM)│
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Control passed to normal    │
  │  world via Non-secure APB    │
  └──────────────────────────────┘
```

#### 9.4.2 Boot Address Configuration

The manager thread's boot instruction address is configured through:

| Method              | Description                                               |
|---------------------|-----------------------------------------------------------|
| **Hardware config** | Fixed boot address set at implementation time              |
| **CR3 register**    | `boot_from_addr` bit indicates if boot address is configurable |
| **Debug registers** | `DBGINST[0,1]` can be used to inject initial instructions  |

The boot routine is stored in **secure memory** and is only accessible via the Secure APB,
ensuring that the initial DMA operations cannot be tampered with by non-secure software.

### 9.5 Security Configuration Register

The security configuration is reported in the **CR4** register (read-only):

| CR4 Bit  | Field                | Description                                        |
|----------|----------------------|----------------------------------------------------|
| `[0]`    | `security_support`   | `1` = TrustZone security is implemented            |
| `[1]`    | `managed_ns_events`  | `1` = Non-secure events can only be managed by secure software |

When `managed_ns_events` is set, non-secure software cannot clear or modify event registers
for events that have been assigned to secure channels.

### 9.6 Security Best Practices

For SoC integrators using the DMA-330 with TrustZone:

1. **Always enable security** (`CR4.security_support = 1`) in systems with mixed secure/non-secure software
2. **Use secure boot** to initialize the DMAC before handing the Non-secure APB to the normal world
3. **Reserve low channel numbers for secure use** — keep a pool of secure channels for trusted operations
4. **Configure the AXI interconnect** to enforce AxPROT-based access control on memory regions
5. **Lock debug registers** after initialization to prevent non-secure injection of DMA instructions

---

## 10. Transfer Types

### 10.1 Overview

The DMA-330 supports four primary transfer types, each suited to different use cases:

| Transfer Type              | Source       | Destination  | Flow Control | Typical Use Case              |
|----------------------------|--------------|--------------|--------------|-------------------------------|
| **Memory → Memory**        | Memory (RAM) | Memory (RAM) | None         | memcpy, buffer copy           |
| **Memory → Peripheral**    | Memory (RAM) | Peripheral   | `dmareq[n]`  | UART TX, SPI TX, I2S TX      |
| **Peripheral → Memory**    | Peripheral   | Memory (RAM) | `dmareq[n]`  | UART RX, SPI RX, ADC capture  |
| **Scatter-Gather**         | Variable     | Variable     | Optional     | Non-contiguous buffer ops     |

### 10.2 Memory-to-Memory Transfer

The simplest transfer type — moves a block of data from one memory region to another.

#### 10.2.1 Data Flow

```
  Source Memory (SA)              DMAC (MFIFO)              Destination Memory (DA)
  ┌──────────────────┐            ┌─────────┐              ┌──────────────────┐
  │ 0x1000_0000      │  AXI Read  │         │  AXI Write   │ 0x2000_0000      │
  │ ┌──┬──┬──┬──┐   │ ◄────────  │  MFIFO  │  ────────►   │ ┌──┬──┬──┬──┐   │
  │ │W0│W1│W2│W3│   │            │ Buffer  │              │ │W0│W1│W2│W3│   │
  │ └──┴──┴──┴──┘   │            │         │              │ └──┴──┴──┴──┘   │
  │ ...              │            └─────────┘              │ ...              │
  └──────────────────┘                                     └──────────────────┘

  SA increments ──────►             FIFO             ◄────── DA increments
```

#### 10.2.2 Instructions

```
  DMAMOV  SA, <source_address>
  DMAMOV  DA, <dest_address>
  DMAMOV  CC, <channel_control>    ; burst size, increment mode
  DMALP   0, <loop_count>          ; repeat for total transfer size / burst size
    DMALD                           ; read burst from source
    DMAST                           ; write burst to destination
  DMALPEND 0
  DMAEND
```

#### 10.2.3 Use Cases

- **memcpy:** Copying buffers in RAM (e.g., frame buffer operations)
- **Data movement:** Transferring data between memory-mapped regions
- **Zero-copy I/O:** Moving data between network buffers

### 10.3 Memory-to-Peripheral Transfer

Transfers data from memory to a DMA-capable peripheral, with **peripheral flow control**.

#### 10.3.1 Data Flow

```
  Source Memory (SA)            DMAC (MFIFO)          Peripheral
  ┌──────────────────┐          ┌─────────┐          ┌──────────────┐
  │ 0x3000_0000      │ AXI Read │         │          │ UART TX FIFO │
  │ ┌──┬──┬──┬──┐   │ ◄─────── │  MFIFO  │  ──────► │ ┌──┬──┬──┐  │
  │ │B0│B1│B2│B3│   │          │ Buffer  │  DMASTP  │ │B0│B1│B2│  │
  │ └──┴──┴──┴──┘   │          │         │  ◄───    │ └──┴──┴──┘  │
  │ ...              │          └─────────┘  dmareq  │ ...          │
  └──────────────────┘                        ack    └──────────────┘

  SA increments ──────►
```

#### 10.3.2 Instructions

```
  DMAMOV  SA, <source_buffer_addr>
  DMAMOV  DA, <peripheral_data_reg>
  DMAMOV  CC, <channel_control>    ; typically fixed DA, incrementing SA
  DMAFLUSHP <periph_num>           ; clear stale peripheral request
  DMALP   0, <count>
    DMASTP  <periph_num>           ; wait for peripheral ready, then write
    DMALD                           ; fetch next data from memory
  DMALPEND 0
  DMAEND
```

#### 10.3.3 Use Cases

- **UART TX:** Sending data from buffer to UART transmit FIFO
- **SPI TX:** Transmitting data to SPI controller
- **I2S TX:** Streaming audio data to I2S transmitter
- **Display:** Sending pixel data to display controller

### 10.4 Peripheral-to-Memory Transfer

Transfers data from a DMA-capable peripheral to memory, with **peripheral flow control**.

#### 10.4.1 Data Flow

```
  Peripheral                DMAC (MFIFO)          Destination Memory (DA)
  ┌──────────────┐          ┌─────────┐          ┌──────────────────┐
  │ UART RX FIFO │          │         │ AXI Read │ 0x4000_0000      │
  │ ┌──┬──┬──┐  │  ──────► │  MFIFO  │ ──────── │ ┌──┬──┬──┬──┐   │
  │ │B0│B1│B2│  │  DMALDP  │ Buffer  │          │ │B0│B1│B2│B3│   │
  │ └──┴──┴──┘  │  ────►   │         │ ◄─────── │ └──┴──┴──┴──┘   │
  │ ...          │  dmareq  └─────────┘ AXI Write│ ...              │
  └──────────────┘                           └──────────────────┘
                                DA increments ──────►
```

#### 10.4.2 Instructions

```
  DMAMOV  SA, <peripheral_data_reg>
  DMAMOV  DA, <dest_buffer_addr>
  DMAMOV  CC, <channel_control>    ; typically fixed SA, incrementing DA
  DMAFLUSHP <periph_num>
  DMALP   0, <count>
    DMALDP  <periph_num>           ; wait for peripheral data, then read
    DMAST                           ; write to memory
  DMALPEND 0
  DMAEND
```

#### 10.4.3 Use Cases

- **UART RX:** Receiving data from UART receive FIFO to buffer
- **SPI RX:** Receiving data from SPI controller
- **ADC capture:** Streaming analog-to-digital converter samples to memory
- **Sensor data:** Collecting data from IMU, temperature sensors, etc.

### 10.5 Scatter-Gather Transfer

Scatter-gather transfers handle **non-contiguous source and/or destination addresses**. This is
essential for operations like:

- Network packet processing (packet headers in one buffer, payload in another)
- File system I/O (pages scattered across physical memory)
- Graphics operations (compositing from multiple frame buffers)

#### 10.5.1 How Scatter-Gather Works

Unlike fixed-address transfers, scatter-gather uses the instruction set to **dynamically modify
addresses** between individual DMA operations:

```
  Scatter-Gather: Multiple source blocks → Contiguous destination

  Source Blocks                  DMAC                   Destination
  ┌──────────┐ 0x1000           │                    ┌──────────────┐
  │ Block A  │ ──────┐          │                    │ Block A      │ 0x5000
  └──────────┘       │          │                    ├──────────────┤
  ┌──────────┐ 0x3000 │ DMALD   │  DMAST  ──────►   │ Block B      │ 0x5080
  │ Block B  │ ──────┤ ───────► │ MFIFO  ───────►   ├──────────────┤
  └──────────┘       │          │                    │ Block C      │ 0x5100
  ┌──────────┐ 0x5000 │          │                    │              │
  │ Block C  │ ──────┘          │                    └──────────────┘
  └──────────┘
```

#### 10.5.2 Techniques for Address Manipulation

| Instruction   | Usage in Scatter-Gather                               |
|---------------|-------------------------------------------------------|
| `DMAMOV`      | Set a completely new 32-bit address (SA or DA)        |
| `DMAADDH`     | Add a 16-bit offset to the current address            |
| `DMAADNH`     | Subtract a 16-bit offset from the current address     |

#### 10.5.3 Example: Gather from Multiple Buffers

```
  ; Gather: Copy Block A (0x1000, 128B), Block B (0x3000, 128B) → Contiguous at 0x5000
  DMAMOV  DA, 0x0000_5000           ; Destination start
  DMAMOV  CC, 0x0C0C_0100           ; 4B burst, 32 beats = 128 bytes

  ; Block A
  DMAMOV  SA, 0x0000_1000
  DMALP   0, #32                    ; 32 bursts × 4B = 128 bytes
    DMALD
    DMAST
  DMALPEND 0

  ; Block B — update source address, destination continues automatically
  DMAMOV  SA, 0x0000_3000
  DMALP   0, #32
    DMALD
    DMAST
  DMALPEND 0

  DMAEND
```

#### 10.5.4 Example: Scatter with DMAADDH (Stride-based)

```
  ; Scatter: Copy every other 64-byte block from 0x1000 to 0x2000
  ; Using DMAADDH to skip 64 bytes between transfers
  DMAMOV  SA, 0x0000_1000
  DMAMOV  DA, 0x0000_2000
  DMAMOV  CC, <64_byte_burst_config>
  DMALP   0, #8
    DMALD
    DMAST
    DMAADDH  SA, #0x0080           ; Skip 128 bytes in source (64 data + 64 gap)
    DMAADDH  DA, #0x0040           ; Advance 64 bytes in destination (contiguous)
  DMALPEND 0
  DMAEND
```

### 10.6 Address Increment Modes

The Channel Control (CC) register configures how addresses are updated after each burst:

| Mode        | Encoding | Behavior                                           |
|-------------|----------|----------------------------------------------------|
| **Incrementing** | `00` | Address increases by burst size after each beat     |
| **Decrementing** | `01` | Address decreases by burst size after each beat     |
| **Fixed**        | `10` | Address does not change (used for peripheral registers) |

**Source and destination increment modes are set independently** in the CC register:

- SA increment: `CC[15:14]`
- DA increment: `CC[13:12]`

### 10.7 Burst Size and Length Options

The CC register also configures burst parameters:

#### 10.7.1 Burst Size (bytes per beat)

| Encoding | Bytes per Beat | Typical Usage                    |
|----------|----------------|----------------------------------|
| `000`    | 1 byte         | Byte-wide peripheral transfers   |
| `001`    | 2 bytes        | 16-bit peripheral transfers      |
| `010`    | 4 bytes        | 32-bit memory transfers (common) |
| `011`    | 8 bytes        | 64-bit memory transfers          |
| `100`    | 16 bytes       | Wide bus transfers               |
| `101`    | 32 bytes       | Maximum width transfers          |
| `110`    | 64 bytes       | Very wide implementations        |
| `111`    | 128 bytes      | Very wide implementations        |

Source burst size: `CC[31:28]`  
Destination burst size: `CC[23:20]`

#### 10.7.2 Burst Length (beats per burst)

| Encoding | Beats | Total (with 4B size) |
|----------|-------|----------------------|
| `0000`   | 1     | 4 bytes              |
| `0001`   | 2     | 8 bytes              |
| `0011`   | 4     | 16 bytes             |
| `0111`   | 8     | 32 bytes             |
| `1111`   | 16    | 64 bytes             |

Source burst length: `CC[27:24]`  
Destination burst length: `CC[19:16]`

> **Note:** Source and destination burst sizes/lengths can differ. The DMAC handles the
> data width conversion through the MFIFO.

---

## 11. Interrupts

### 11.1 Overview

The DMA-330 generates interrupts to notify the processor of two categories of events:

1. **DMA completion/events** — signaled by the `DMASEV` instruction during normal DMA execution
2. **Fault conditions** — triggered by errors (AXI errors, security violations, decode errors)

The interrupt subsystem is **configurable** — software controls which events generate IRQ outputs
through the `INTEN` register.

### 11.2 Interrupt Architecture

```
  DMA Channel Threads                 Interrupt Controller              CPU
  ──────────────────                  ─────────────────────             ────

  Channel 0 ──┐                       ┌─────────────┐
  DMASEV 0    │  Event 0              │             │
              ├──────────────────────►│  INTEN      │     irq[0]
  Channel 1 ──┤  Event 1              │  (mask)     ├───────────────► IRQ/FIQ
  DMASEV 1    ├──────────────────────►│             │
              │                       │ INT_EVENT   │     irq[1]
  ...         │                       │ _RIS (raw)  ├───────────────►
              │                       │             │
  Channel N ──┘  Event N              │ INTMIS      │     irq[N]
  DMASEV N    ├──────────────────────►│ (masked)    ├───────────────►
              │                       │             │
  Fault       │  Fault Event          │ INTCLR      │
  Detector ───┘──────────────────────►│ (clear)     │
                                      └─────────────┘
```

### 11.3 Event Mechanism (DMASEV / DMAWFE)

The DMA-330 uses an **event signaling mechanism** for inter-thread communication and
interrupt generation.

#### 11.3.1 DMASEV — Send Event

When a DMA channel thread executes `DMASEV <event_num>`:

1. The corresponding bit is set in the `INT_EVENT_RIS` (raw interrupt status) register
2. If the event is enabled in `INTEN`, the `INTMIS` (masked interrupt status) bit is also set
   and the corresponding `irq[n]` output is asserted
3. If any channel thread (or the manager thread) is executing `DMAWFE <event_num>`, it is
   woken up and resumes execution
4. The event is consumed — the `INT_EVENT_RIS` bit is automatically cleared if a `DMAWFE`
   was waiting

#### 11.3.2 DMAWFE — Wait For Event

When a DMA channel thread executes `DMAWFE <event_num>`:

1. The channel transitions to the **Waiting for Event** state
2. The channel stops consuming resources (no AXI transactions, no instruction fetches)
3. When the specified event is signaled (via `DMASEV` from another thread), the channel
   resumes execution from the instruction after `DMAWFE`
4. If the event was already pending, the channel continues immediately without waiting

#### 11.3.3 Event Flow Example

```
  Channel 0 (UART RX)              Channel 1 (Process Data)         CPU
  ─────────────────                 ──────────────────────          ────
       │                                    │                        │
       │  DMALDP 0 (receive byte)           │                        │
       │  ... (receive complete)            │                        │
       │  DMASEV 1 ◄── send event 1        │                        │
       │  DMAEND                            │                        │
       │                                    │                        │
       │                         DMAWFE 1 ──┤  (was waiting)         │
       │                                    │  (resumes execution)   │
       │                                    │  DMAMOV SA, ...         │
       │                                    │  ... (process data)     │
       │                                    │  DMASEV 0 ──────────────┤ irq[0]
       │                                    │  DMAEND                 │ ◄── interrupt
       │                                    │                        │
```

### 11.4 Interrupt Registers

The interrupt subsystem is controlled through the following registers in the Control Register
section (Section 1 of the register map):

| Offset  | Register          | Access | Description                                          |
|---------|-------------------|--------|------------------------------------------------------|
| `0x008` | `INTEN`           | R/W    | **Interrupt Enable** — per-event mask. Bit[n]=1 enables irq[n] output for event n. |
| `0x010` | `INT_EVENT_RIS`   | R      | **Raw Interrupt Status** — shows all events that have occurred, regardless of INTEN mask. |
| `0x014` | `INTMIS`          | R      | **Masked Interrupt Status** — shows only events that are both pending AND enabled. This is what triggers actual IRQ outputs. |
| `0x018` | `INTCLR`          | W      | **Interrupt Clear** — write 1 to bit[n] to clear event n. Writing 0 has no effect. |

#### 11.4.1 Register Relationships

```
  INT_EVENT_RIS (raw status)     INTEN (enable mask)        INTMIS (masked status)
  ┌───────────────────┐         ┌───────────────────┐      ┌───────────────────┐
  │ bit 0: event 0    │         │ bit 0: 1=enabled  │      │ bit 0: event 0    │
  │ bit 1: event 1    │   AND   │ bit 1: 0=disabled │ ───► │ bit 1: 0 (masked) │
  │ bit 2: event 2    │         │ bit 2: 1=enabled  │      │ bit 2: event 2    │
  │ ...               │         │ ...               │      │ ...               │
  └───────────────────┘         └───────────────────┘      └───────────────────┘
          │                                                        │
          │                                                        │
          │  INTCLR (write 1 to clear)                             │  Drives irq[] outputs
          │  ┌───────────────────┐                                 │
          └──│ write 1 to clear  │◄── Software interrupt handler   │
             └───────────────────┘                                 ▼
                                                             irq[0..N] → CPU
```

#### 11.4.2 Typical Interrupt Handling Sequence

```
  1. Software writes INTEN to enable desired events
  2. DMA channel executes DMASEV to signal completion
  3. INT_EVENT_RIS bit is set; if enabled in INTEN, INTMIS bit is set and irq[] asserted
  4. CPU enters IRQ handler
  5. Handler reads INTMIS to determine which event(s) occurred
  6. Handler processes the completed transfer
  7. Handler writes INTCLR with bits set for processed events
  8. irq[] deasserts; handler returns
```

### 11.5 Fault Interrupt Handling

Faults are a special category of interrupts that indicate error conditions.

#### 11.5.1 Fault Status Registers

| Offset  | Register   | Access | Description                                         |
|---------|------------|--------|-----------------------------------------------------|
| `0x020` | `FSRD`     | R      | **Fault Status DMAC** — indicates DMAC-level faults (bit per fault type) |
| `0x024` | `FSRC`     | R      | **Fault Status per Channel** — bit[n]=1 means channel n has a fault |
| `0x028` | `FTRD`     | R/W    | **Fault Type DMAC** — encodes the specific DMAC-level fault type |
| `0x030` | `FTC[n]`   | R/W    | **Fault Type per Channel** — encodes the fault type for channel n |

#### 11.5.2 Fault Types

The `FTC[n]` and `FTRD` registers encode the specific fault type:

| Fault Type Code | Description                                              |
|------------------|----------------------------------------------------------|
| AXI Read Error  | Slave returned SLVERR or DECERR on an AXI read beat     |
| AXI Write Error | Slave returned SLVERR or DECERR on an AXI write beat    |
| Instruction Decode Error | Invalid or unsupported instruction encoding      |
| Security Violation | Non-secure access to secure resource attempted        |
| MFIFO Error     | MFIFO overflow (too much data) or underflow (read empty) |
| Lock-up         | Channel is locked due to unresolvable error              |

#### 11.5.3 Fault Handling Flow

```
  Fault Occurs
       │
       ▼
  ┌──────────────────────────┐
  │ Channel enters            │
  │ Fault Completing state    │
  │ (completes current AXI    │
  │  transaction)             │
  └───────────┬──────────────┘
              │
              ▼
  ┌──────────────────────────┐
  │ Channel transitions to    │
  │ Fault (Locked) state      │
  │                           │
  │ FSRD/FSRC bits set        │
  │ FTRD/FTC registers set    │
  │ Interrupt asserted (if    │
  │ fault IRQ enabled)        │
  └───────────┬──────────────┘
              │
              ▼
  ┌──────────────────────────┐
  │ CPU IRQ handler reads:   │
  │  - FSRD for DMAC faults  │
  │  - FSRC for channel faults│
  │  - FTRD/FTC for details  │
  └───────────┬──────────────┘
              │
              ▼
  ┌──────────────────────────┐
  │ Software recovery:       │
  │  1. Write FTC[n] to clear│
  │  2. Execute DMAKILL if   │
  │     channel is locked    │
  │  3. Restart channel with │
  │     DMAGO if needed      │
  └──────────────────────────┘
```

#### 11.5.4 Fault Clearing

To clear a fault and recover:

1. Read `FSRC` to identify which channel(s) have faults
2. Read `FTC[n]` to determine the fault type
3. Take appropriate action (e.g., fix buffer, correct address)
4. Write `FTC[n]` to clear the fault type register
5. If channel is locked, use `DMAKILL` (via debug registers) to force it to Stopped
6. Restart the channel with `DMAGO` if the transfer should be retried

### 11.6 Interrupt Configuration

The number of interrupt lines (`irq[n]`) is determined at implementation time and reported
in the `CR0` register (`num_events` field, bits [23:16]).

Common configurations:

| Configuration        | Description                                           |
|----------------------|-------------------------------------------------------|
| **Per-channel IRQ**  | One `irq` per DMA channel + one for faults            |
| **Single combined**  | All events share one `irq` line; software reads INTMIS |
| **Grouped**          | Events grouped (e.g., channels 0-3 → irq[0], 4-7 → irq[1]) |

---

## 12. References

### 12.1 Official ARM Documentation

| Ref # | Document | URL |
|-------|----------|-----|
| [1] | **ARM DDI 0424** — CoreLink DMA-330 DMA Controller Technical Reference Manual (r1p2) | https://developer.arm.com/documentation/ddi0424/latest |
| [2] | **ARM DDI 0424 PDF** — Direct download of the TRM PDF | https://documentation-service.arm.com/static/5e8e25befd977155116a5ad9 |
| [3] | **ARM CoreLink DMA-330 Product Page** | https://www.arm.com/products/silicon-ip-system/embedded-system-design/dma-330 |

### 12.2 Community & Educational Resources

| Ref # | Resource | URL |
|-------|----------|-----|
| [4] | **SoC Labs — CoreLink DMA-330** Technology page with overview and resources | https://soclabs.org/technology/corelink-dma-330 |
| [5] | **PL330 DMA Controller Notes** — ARM SoC Device Assignment Notes (cwshu) | https://cwshu.github.io/arm_virt_notes/notes/dma/pl330.html |

### 12.3 Open Source Implementations & Drivers

| Ref # | Resource | URL |
|-------|----------|-----|
| [6] | **Linux Kernel PL330 DMA Driver** — `drivers/dma/pl330.c` | https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/dma/pl330.c |
| [7] | **DMA-330 Assembler** — Unofficial CoreLink DMA-330 assembler (GitHub) | https://github.com/profi200/dma330as |

### 12.4 Academic & Technical Papers

| Ref # | Resource | URL |
|-------|----------|-----|
| [8] | **Design and Implementation of Direct Memory Access Controller** — N. Sasidhar, IIT Madras (2017) | https://eescholars.iitm.ac.in/sites/default/files/eethesis/ee15m079.pdf |

### 12.5 Related ARM Specifications

| Ref # | Document | Description |
|-------|----------|-------------|
| [9] | **ARM Architecture Reference Manual** | ARMv7-A/R architecture, TrustZone security model |
| [10] | **AMBA AXI4 Protocol Specification** | AXI4 master/slave interface protocol |
| [11] | **AMBA APB4 Protocol Specification** | APB4 slave interface protocol |
| [12] | **ARM TrustZone Technology Overview** | Security partitioning framework |

---

*End of DMA-330 Specification Document*
