# CPU RTL Specification

## 1. Overview

A 32-bit RISC-V (RV32I) 5-stage pipelined CPU core with AXI4-Lite bus interface,
designed for integration with a DMA controller subsystem.

## 2. ISA

- **Base ISA**: RISC-V RV32I (47 instructions)
- **Privilege Level**: Machine mode only (M-mode)
- **Extensions**: None (base integer only)

### 2.1 Instruction Formats

| Type | Fields | Bits |
|------|--------|------|
| R-type | funct7[31:25] rs2[24:20] rs1[19:15] funct3[14:12] rd[11:7] opcode[6:0] |
| I-type | imm[31:20] rs1[19:15] funct3[14:12] rd[11:7] opcode[6:0] |
| S-type | imm[31:25] rs2[24:20] rs1[19:15] funct3[14:12] imm[11:7] opcode[6:0] |
| B-type | imm[12\|10:5] rs2[24:20] rs1[19:15] funct3[14:12] imm[4:1\|11] opcode[6:0] |
| U-type | imm[31:12] rd[11:7] opcode[6:0] |
| J-type | imm[20\|10:1\|11\|19:12] rd[11:7] opcode[6:0] |

### 2.2 Instruction List

**R-type (10):**
ADD, SUB, SLL, SLT, SLTU, XOR, SRL, SRA, OR, AND

**I-type ALU (9):**
ADDI, SLTI, SLTIU, XORI, ORI, ANDI, SLLI, SRLI, SRAI

**I-type Load (5):**
LB, LH, LW, LBU, LHU

**I-type Jump (1):**
JALR

**S-type Store (3):**
SB, SH, SW

**B-type Branch (6):**
BEQ, BNE, BLT, BGE, BLTU, BGEU

**U-type (2):**
LUI, AUIPC

**J-type (1):**
JAL

**System (6):**
ECALL, EBREAK, MRET, CSRRW, CSRRS, CSRRC
(+ CSRRWI, CSRRSI, CSRRCI)

## 3. Pipeline Architecture

5-stage pipeline: **IF → ID → EX → MEM → WB**

```
+-------+    +-------+    +-------+    +-------+    +-------+
|  IF   |--->|  ID   |--->|  EX   |--->|  MEM  |--->|  WB   |
+-------+    +-------+    +-------+    +-------+    +-------+
   |                          ^                          |
   |    Instruction Memory    |     Data Memory          |
   +--------------------------+--------------------------+
              AXI4-Lite Bus Interface
```

### 3.1 Pipeline Registers

| Register | Contents |
|----------|----------|
| IF/ID | instruction[31:0], pc[31:0], pc_plus4[31:0] |
| ID/EX | rs1_data[31:0], rs2_data[31:0], imm[31:0], pc[31:0], pc_plus4[31:0], rd_addr[4:0], control_signals |
| EX/MEM | alu_result[31:0], rs2_data[31:0], rd_addr[4:0], pc_plus4[31:0], control_signals |
| MEM/WB | mem_rdata[31:0], alu_result[31:0], rd_addr[4:0], pc_plus4[31:0], control_signals |

### 3.2 Control Signals

| Signal | Width | Description |
|--------|-------|-------------|
| RegWrite | 1 | Write to register file |
| MemRead | 1 | Read from data memory |
| MemWrite | 1 | Write to data memory |
| MemToReg | 1 | 0=ALU result, 1=memory data |
| ALUSrc | 1 | 0=register, 1=immediate |
| Branch | 1 | Branch instruction |
| Jump | 2 | 00=none, 01=JAL, 10=JALR |
| ALUOp | 2 | ALU operation type |
| MemSize | 2 | 00=byte, 01=halfword, 10=word |
| MemUnsigned | 1 | Unsigned load extension |

## 4. Bus Interface

### 4.1 AXI4-Lite Master (Instruction Fetch)

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| araddr | O | 32 | Read address |
| arprot | O | 3 | Protection type |
| arvalid | O | 1 | Read address valid |
| arready | I | 1 | Read address ready |
| rdata | I | 32 | Read data |
| rresp | I | 2 | Read response |
| rvalid | I | 1 | Read data valid |
| rready | O | 1 | Read data ready |

### 4.2 AXI4-Lite Master (Data Access)

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| awaddr | O | 32 | Write address |
| awprot | O | 3 | Protection type |
| awvalid | O | 1 | Write address valid |
| awready | I | 1 | Write address ready |
| wdata | O | 32 | Write data |
| wstrb | O | 4 | Write strobes |
| wvalid | O | 1 | Write data valid |
| wready | I | 1 | Write data ready |
| bresp | I | 2 | Write response |
| bvalid | I | 1 | Write response valid |
| bready | O | 1 | Write response ready |
| araddr | O | 32 | Read address |
| arprot | O | 3 | Protection type |
| arvalid | O | 1 | Read address valid |
| arready | I | 1 | Read address ready |
| rdata | I | 32 | Read data |
| rresp | I | 2 | Read response |
| rvalid | I | 1 | Read data valid |
| rready | O | 1 | Read data ready |

## 5. Register Set

- **x0** (zero): Hardwired to 0
- **x1** (ra): Return address
- **x2** (sp): Stack pointer
- **x3** (gp): Global pointer
- **x4** (tp): Thread pointer
- **x5-x7** (t0-t2): Temporary registers
- **x8** (s0/fp): Saved register / frame pointer
- **x9** (s1): Saved register
- **x10-x17** (a0-a7): Function arguments / return values
- **x18-x27** (s2-s11): Saved registers
- **x28-x31** (t3-t6): Temporary registers

## 6. CSR Registers

| Address | Name | Description |
|---------|------|-------------|
| 0x300 | mstatus | Machine status (MIE bit) |
| 0x305 | mtvec | Machine trap vector base |
| 0x341 | mepc | Machine exception PC |
| 0x342 | mcause | Machine exception cause |
| 0x343 | mtval | Machine trap value |
| 0x304 | mie | Machine interrupt enable |

### mcause Encoding

| Code | Exception |
|------|-----------|
| 0 | Instruction address misaligned |
| 1 | Instruction access fault |
| 2 | Illegal instruction |
| 3 | Breakpoint (EBREAK) |
| 8 | ECALL from M-mode |
| 11 | ECALL from M-mode (alternative) |
| 0x80000003 | External interrupt (DMA irq_done) |
| 0x80000004 | External interrupt (DMA irq_err) |

## 7. Memory Map

| Address Range | Size | Peripheral |
|---------------|------|------------|
| 0x0000_0000 - 0x0FFF_FFFF | 256MB | Instruction Memory |
| 0x1000_0000 - 0x1FFF_FFFF | 256MB | Data Memory |
| 0x2000_0000 - 0x2000_001F | 32B | DMA Registers |
| 0x3000_0000 - 0x3000_00FF | 256B | CPU CSR Space |
| 0xFFFF_0000 - 0xFFFF_FFFF | 64KB | Boot ROM (reset vector) |

### DMA Register Map (CPU perspective)

| Offset | Register | Access |
|--------|----------|--------|
| 0x00 | SRC_ADDR | R/W |
| 0x04 | DST_ADDR | R/W |
| 0x08 | XFER_LEN | R/W |
| 0x0C | CTRL (START, MODE) | R/W |
| 0x10 | STATUS (BUSY, DONE, ERR) | R |
| 0x14 | IRQ_STATUS | R/W |

## 8. Interrupt Interface

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| irq_ext_0 | I | 1 | DMA irq_done |
| irq_ext_1 | I | 1 | DMA irq_err |

## 9. Top-Level Ports (cpu_top.sv)

| Signal | Direction | Width | Description |
|--------|-----------|-------|-------------|
| clk | I | 1 | System clock |
| rst_n | I | 1 | Active-low synchronous reset |
| irq_ext_0 | I | 1 | DMA done interrupt |
| irq_ext_1 | I | 1 | DMA error interrupt |
| -- IF AXI -- | | | |
| if_araddr | O | 32 | Instruction fetch address |
| if_arprot | O | 3 | Protection |
| if_arvalid | O | 1 | Address valid |
| if_arready | I | 1 | Address ready |
| if_rdata | I | 32 | Instruction data |
| if_rresp | I | 2 | Response |
| if_rvalid | I | 1 | Data valid |
| if_rready | O | 1 | Data ready |
| -- MEM AXI -- | | | |
| mem_awaddr | O | 32 | Write address |
| mem_awprot | O | 3 | Protection |
| mem_awvalid | O | 1 | Address valid |
| mem_awready | I | 1 | Address ready |
| mem_wdata | O | 32 | Write data |
| mem_wstrb | O | 4 | Write strobes |
| mem_wvalid | O | 1 | Data valid |
| mem_wready | I | 1 | Data ready |
| mem_bresp | I | 2 | Write response |
| mem_bvalid | I | 1 | Response valid |
| mem_bready | O | 1 | Response ready |
| mem_araddr | O | 32 | Read address |
| mem_arprot | O | 3 | Protection |
| mem_arvalid | O | 1 | Address valid |
| mem_arready | I | 1 | Address ready |
| mem_rdata | I | 32 | Read data |
| mem_rresp | I | 2 | Read response |
| mem_rvalid | I | 1 | Data valid |
| mem_rready | O | 1 | Data ready |

## 10. Design Parameters

| Parameter | Value |
|-----------|-------|
| DATA_WIDTH | 32 |
| ADDR_WIDTH | 32 |
| REG_ADDR_WIDTH | 5 |
| NUM_REGS | 32 |
| RESET_PC | 0xFFFF0000 |
| PIPELINE_STAGES | 5 |
| CLOCK_DOMAIN | Single |
| RESET_TYPE | Synchronous active-low |

## 11. File Structure

```
cpu_rtl/
├── cpu_spec.md              -- This specification
├── rtl/
│   ├── cpu_top.sv           -- Top-level CPU wrapper
│   ├── cpu_if.sv            -- Instruction fetch stage
│   ├── cpu_id.sv            -- Instruction decode stage
│   ├── cpu_regfile.sv       -- Register file (32x32)
│   ├── cpu_imm_gen.sv       -- Immediate generator
│   ├── cpu_ctrl.sv          -- Control signal decoder
│   ├── cpu_ex.sv            -- Execution stage
│   ├── cpu_alu.sv           -- Arithmetic Logic Unit
│   ├── cpu_alu_ctrl.sv      -- ALU control decoder
│   ├── cpu_branch_comp.sv   -- Branch comparator
│   ├── cpu_mem.sv           -- Memory access stage
│   ├── cpu_lsu.sv           -- Load/Store Unit
│   ├── cpu_wb.sv            -- Writeback stage
│   ├── cpu_hazard.sv        -- Hazard detection unit
│   ├── cpu_forwarding.sv    -- Data forwarding unit
│   ├── cpu_csr.sv           -- CSR register file
│   ├── cpu_trap.sv          -- Trap/exception handler
│   ├── soc_top.sv           -- SoC top-level integration
│   └── axi_interconnect.sv  -- AXI4-Lite bus interconnect
├── tb/
│   ├── tb_cpu_alu.sv        -- ALU testbench
│   ├── tb_cpu_regfile.sv    -- Register file testbench
│   ├── tb_cpu_pipeline.sv   -- Pipeline testbench
│   └── tb_soc_integration.sv -- SoC integration testbench
└── sim/
    └── (simulation scripts, waveforms, reports)
```

## 12. Hazard Handling Strategy

### Data Hazards
- **EX/EX forwarding**: Forward ALU result from EX/MEM to EX inputs
- **MEM/EX forwarding**: Forward result from MEM/WB to EX inputs
- **Load-use stall**: Stall 1 cycle when load in EX targets source in ID

### Control Hazards
- **Branch taken**: Flush IF and ID (2 NOP bubbles)
- **Jump (JAL/JALR)**: Flush IF and ID (2 NOP bubbles)
- **No branch prediction**: Static not-taken

## 13. Exception & Interrupt Flow

1. Exception/interrupt detected
2. Complete current pipeline stage (synchronous at WB boundary)
3. Save PC to mepc
4. Set mcause (exception code or interrupt ID)
5. Clear mstatus.MIE (disable further interrupts)
6. PC ← mtvec (jump to trap handler)
7. Software handles exception via MRET:
   - PC ← mepc
   - Restore mstatus.MIE
