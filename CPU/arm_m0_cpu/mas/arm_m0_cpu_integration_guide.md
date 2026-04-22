# ARM Cortex-M0-Style CPU — Integration Guide

## 1. Overview

This guide explains how to integrate the `arm_m0_cpu` module into a System-on-Chip (SoC) or simulation testbench. The CPU uses a simple synchronous bus protocol with separate instruction fetch and data memory interfaces.

---

## 2. System-Level Block Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         SoC Top                              │
│                                                              │
│  ┌───────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │           │   │              │   │                  │   │
│  │  Clock    │   │   arm_m0_cpu │   │   Data SRAM      │   │
│  │  / Reset  │   │              │   │   (32-bit, R/W)  │   │
│  │  Gen      │   │              │   │                  │   │
│  │           │   │              │   │                  │   │
│  └─────┬─────┘   │              │   │                  │   │
│        │         │  instr_addr ├───►│                  │   │
│  clk ──┤         │  instr_req  ├───►│  Instr ROM      │   │
│  rst_n─┤         │  instr_rdata│◄───│  (16-bit, R)    │   │
│        │         │  instr_ack  │◄───│                  │   │
│        │         │              │   │                  │   │
│        │         │  mem_addr   ├───►│  addr            │   │
│        │         │  mem_wdata  ├───►│  wdata           │   │
│        │         │  mem_rdata  │◄───│  rdata           │   │
│        │         │  mem_we     ├───►│  we              │   │
│        │         │  mem_req    ├───►│  cs              │   │
│        │         │  mem_ack    │◄───│  ack             │   │
│        │         │  mem_size   ├───►│  size            │   │
│        │         │              │   │                  │   │
│        │         │  irq        │◄───│  IRQ Controller  │   │
│        │         │              │   │                  │   │
│        │         └──────────────┘   └──────────────────┘   │
│        │                                                     │
└────────┴─────────────────────────────────────────────────────┘
```

---

## 3. Clock and Reset Connections

```
            ┌──────────────┐
PLL/Clock ──►│     clk      │
 Generator   │              │
            ─►│    rst_n     │
  Power-on   │              │
  Reset      │  arm_m0_cpu  │
            ─►│    irq       │
  IRQ        │              │
  Controller └──────────────┘
```

**Requirements:**
- **Clock**: Single clock domain. No specific frequency requirement. Typical simulation: 10ns period (100 MHz).
- **Reset**: Active-low synchronous. Must be held LOW for ≥2 clock cycles after power-on. All registers initialized on reset.
- **IRQ**: Active-high level-sensitive. Tie to 0 if unused.

---

## 4. Memory Bus Hookup

### 4.1 Instruction Memory (ROM/SRAM)

The instruction fetch interface reads 16-bit Thumb instructions. The memory should respond within 1 clock cycle.

```systemverilog
// Instruction ROM model
always @(posedge clk) begin
    if (instr_req) begin
        instr_ack   <= 1'b1;
        instr_rdata <= imem[instr_addr[15:1]]; // Half-word addressed
    end else begin
        instr_ack <= 1'b0;
    end
end
```

**Address mapping**: `instr_addr` is byte-addressed but always even. Use `instr_addr[15:1]` as the half-word index into a 16-bit wide memory array.

### 4.2 Data Memory (SRAM)

The data memory interface uses a simple req/ack handshake:

```systemverilog
// Data SRAM model
always @(posedge clk) begin
    if (!rst_n) begin
        mem_ack <= 1'b0;
    end else if (mem_req && mem_we) begin
        // Write
        data_mem[mem_addr[15:2]] <= mem_wdata;
        mem_ack <= 1'b1;
    end else if (mem_req && !mem_we) begin
        // Read
        mem_rdata <= data_mem[mem_addr[15:2]];
        mem_ack <= 1'b1;
    end else begin
        mem_ack <= 1'b0;
    end
end
```

**Address mapping**: `mem_addr` is byte-addressed, word-aligned. Use `mem_addr[15:2]` as the word index into a 32-bit wide memory array.

### 4.3 Memory Bus Timing

```
Instruction Fetch (1-cycle latency):
  Cycle N  : CPU drives instr_addr, asserts instr_req
  Cycle N+1: Memory drives instr_rdata, asserts instr_ack
  Cycle N+2: CPU samples instr_rdata, deasserts instr_req

Data Store (STR, 1-cycle latency):
  Cycle N  : CPU drives mem_addr, mem_wdata, asserts mem_req + mem_we
  Cycle N+1: Memory writes data, asserts mem_ack
  Cycle N+2: CPU deasserts mem_req, mem_we

Data Load (LDR, 1-cycle latency):
  Cycle N  : CPU drives mem_addr, asserts mem_req (mem_we=0)
  Cycle N+1: Memory drives mem_rdata, asserts mem_ack
  Cycle N+2: CPU samples mem_rdata, deasserts mem_req
```

---

## 5. Example Memory Map

```
Address Range          Size    Region         Description
───────────────────── ─────── ────────────── ──────────────────────
0x00000000–0x0000FFFF  64 KB   Code ROM       Thumb-16 instructions
0x20000000–0x2000FFFF  64 KB   Data SRAM      Read/write data + stack
0x20004000             —       Stack Top      Default SP reset value
0x40000000–0x40000FFF   4 KB   Peripherals   Memory-mapped I/O
```

### Boot Sequence

1. **Reset**: `rst_n` goes HIGH
2. **CPU initializes**: PC=0x00000000, SP=0x20004000, all other regs=0
3. **Fetch from 0x00000000**: First instruction loaded from Code ROM
4. **Execution begins**: Instructions execute sequentially from address 0x0000

### Vector Table (Minimal)

```
Offset   Content            Usage
──────── ────────────────── ───────────────────────
0x0000   First instruction  Entry point after reset
0x0002   Second instruction
...
0x0018   IRQ handler        (reserved for future use)
```

**Note**: In a full ARMv6-M implementation, offset 0x0000 would contain the initial SP value and offset 0x0004 would contain the reset vector. This simplified CPU starts executing directly from address 0x0000.

---

## 6. Verilog Instantiation Example

```systemverilog
module soc_top (
    input  logic clk,       // System clock
    input  logic rst_n,     // Active-low reset (from power-on reset)
    input  logic irq_in     // External interrupt request
);

    // ---------------------------------------------------------------
    // CPU signals
    // ---------------------------------------------------------------
    logic [31:0] instr_addr;
    logic        instr_req;
    logic [15:0] instr_rdata;
    logic        instr_ack;

    logic [31:0] mem_addr;
    logic [31:0] mem_wdata;
    logic [31:0] mem_rdata;
    logic        mem_we;
    logic        mem_req;
    logic [1:0]  mem_size;
    logic        mem_ack;

    // ---------------------------------------------------------------
    // CPU instantiation
    // ---------------------------------------------------------------
    arm_m0_cpu u_cpu (
        .clk         (clk),
        .rst_n       (rst_n),
        .instr_addr  (instr_addr),
        .instr_req   (instr_req),
        .instr_rdata (instr_rdata),
        .instr_ack   (instr_ack),
        .mem_addr    (mem_addr),
        .mem_wdata   (mem_wdata),
        .mem_rdata   (mem_rdata),
        .mem_we      (mem_we),
        .mem_req     (mem_req),
        .mem_size    (mem_size),
        .mem_ack     (mem_ack),
        .irq         (irq_in)
    );

    // ---------------------------------------------------------------
    // Instruction ROM (16-bit, 32K entries = 64KB)
    // ---------------------------------------------------------------
    logic [15:0] imem [0:32767];

    initial begin
        $readmemh("firmware.hex", imem);  // Load program
    end

    always @(posedge clk) begin
        if (instr_req) begin
            instr_ack   <= 1'b1;
            instr_rdata <= imem[instr_addr[16:1]];
        end else begin
            instr_ack <= 1'b0;
        end
    end

    // ---------------------------------------------------------------
    // Data SRAM (32-bit, 16K entries = 64KB)
    // ---------------------------------------------------------------
    logic [31:0] dmem [0:16383];

    always @(posedge clk) begin
        if (!rst_n) begin
            mem_ack <= 1'b0;
        end else if (mem_req && mem_we) begin
            dmem[mem_addr[15:2]] <= mem_wdata;
            mem_ack <= 1'b1;
        end else if (mem_req && !mem_we) begin
            mem_rdata <= dmem[mem_addr[15:2]];
            mem_ack   <= 1'b1;
        end else begin
            mem_ack <= 1'b0;
        end
    end

endmodule
```

---

## 7. Pin Checklist for Integration

| Signal | Direction | Connected To | Notes |
|--------|-----------|-------------|-------|
| `clk` | in | System clock generator | Single domain, no PLL required |
| `rst_n` | in | Power-on reset controller | Must stay LOW for ≥2 cycles |
| `instr_addr[31:0]` | out | Instruction ROM address | Use [N:1] as half-word index |
| `instr_req` | out | Instruction ROM chip select | Active-high pulse |
| `instr_rdata[15:0]` | in | Instruction ROM data out | Valid when instr_ack=1 |
| `instr_ack` | in | Instruction ROM ready | Assert 1 cycle after instr_req |
| `mem_addr[31:0]` | out | Data SRAM address | Use [N:2] as word index |
| `mem_wdata[31:0]` | out | Data SRAM data in | Valid during STR |
| `mem_rdata[31:0]` | in | Data SRAM data out | Valid when mem_ack=1 |
| `mem_we` | out | Data SRAM write enable | Active-high |
| `mem_req` | out | Data SRAM chip select | Active-high |
| `mem_size[1:0]` | out | Transfer size | Always 2'b10 (word) |
| `mem_ack` | in | Data SRAM ready | Assert 1 cycle after mem_req |
| `irq` | in | Interrupt controller | Tie to 0 if unused |

---

## 8. Common Integration Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| CPU fetches wrong instructions | instr_addr used as word index instead of half-word | Use `instr_addr[N:1]` to index 16-bit memory |
| Memory read returns stale data | mem_rdata not registered | Sample mem_rdata on clock edge when mem_ack=1 |
| CPU hangs after reset | rst_n not held LOW long enough | Hold rst_n LOW for ≥5 clock cycles |
| STR writes to wrong address | mem_addr byte vs word confusion | Use `mem_addr[N:2]` for 32-bit word addressing |
| LDR returns garbage | Memory not initialized | Initialize data memory or ensure writes before reads |
