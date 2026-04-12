# Cortex-M0 Core — Interface Specification

## 1. Clock Domains

| Domain | Signal | Frequency | Description |
|--------|--------|-----------|-------------|
| sys_clk | HCLK | Implementation-dependent | Single clock domain — all logic clocked here |

## 2. Reset Strategy

| Signal | Polarity | Type | Description |
|--------|----------|------|-------------|
| HRESETn | Active-low | Asynchronous assert, synchronous deassert | System reset. Core initializes PC from INIT_PC, SP from INIT_SP. |

## 3. Top-Level Ports

### 3.1 Clock & Reset

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HCLK | 1 | input | sys_clk | System clock |
| HRESETn | 1 | input | sys_clk | Asynchronous active-low reset |

### 3.2 AHB-Lite Bus Interface

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HADDR | 32 | output | sys_clk | Address bus |
| HBURST | 3 | output | sys_clk | Burst type (SINGLE/INCR/WRAP) |
| HMASTLOCK | 1 | output | sys_clk | Locked transfer (for atomic ops) |
| HPROT | 4 | output | sys_clk | Protection control |
| HSIZE | 3 | output | sys_clk | Transfer size (byte/halfword/word) |
| HTRANS | 2 | output | sys_clk | Transfer type (IDLE/BUSY/NONSEQ/SEQ) |
| HWDATA | 32 | output | sys_clk | Write data bus |
| HWRITE | 1 | output | sys_clk | Transfer direction (1=write) |
| HRDATA | 32 | input | sys_clk | Read data bus |
| HREADY | 1 | input | sys_clk | Transfer done (1=ready) |
| HRESP | 1 | input | sys_clk | Transfer response (0=OKAY, 1=ERROR) |

### 3.3 Interrupts (NVIC)

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| IRQ | IRQ_NUM | input | sys_clk | External interrupt requests (active-high, level-sensitive) |
| NMI | 1 | input | sys_clk | Non-maskable interrupt (active-high, edge-sensitive) |
| EVTEXEC | 1 | output | sys_clk | Event executed signal (for WFE instruction) |

### 3.4 Debug

| Port | Width | Direction | Domain | Description |
|------|-------|-----------|--------|-------------|
| HALTED | 1 | output | sys_clk | Core is halted for debug |
| DBGRQ | 1 | input | sys_clk | External debug request |
| DBGACK | 1 | output | sys_clk | Debug acknowledge |

## 4. Parameters / Generics

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| IRQ_NUM | integer | 32 | Number of external IRQ lines (1–240) |
| INIT_PC | logic [31:0] | 32'h00000004 | Reset vector — initial PC value (vector table + 4) |
| INIT_SP | logic [31:0] | 32'h00000000 | Initial stack pointer (vector table offset 0) |

## 5. Port Width Constraint

All port widths are explicitly defined — no TBD or variable-width ports.
IRQ width is parameterized via IRQ_NUM with concrete default (32).
