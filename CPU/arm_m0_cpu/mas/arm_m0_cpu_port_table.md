# ARM Cortex-M0-Style CPU — Port Table

## 1. Clock and Reset

| Name | Width | Direction | Active Level | Clock Domain | Reset Value | Description |
|------|-------|-----------|-------------|-------------|-------------|-------------|
| `clk` | 1 | input | Rising edge | — | — | System clock. All sequential logic clocked on positive edge. |
| `rst_n` | 1 | input | Active-low | — | — | Synchronous reset. When LOW, all registers cleared, FSM → RESET state. Must be held LOW for ≥2 clock cycles. |

---

## 2. Instruction Fetch Interface

Separate 16-bit instruction fetch port for Thumb-16 instructions.

| Name | Width | Direction | Active Level | Clock Domain | Reset Value | Description |
|------|-------|-----------|-------------|-------------|-------------|-------------|
| `instr_addr` | 32 | output | — | clk | 0x00000000 | Instruction fetch address. Points to the next 16-bit Thumb instruction to fetch. Increments by 2 per instruction. |
| `instr_req` | 1 | output | Active-high | clk | 0 | Instruction fetch request. Asserted for one cycle during FETCH state. |
| `instr_rdata` | 16 | input | — | clk | 0x0000 | Fetched 16-bit Thumb instruction data. Valid when `instr_ack` is HIGH. |
| `instr_ack` | 1 | input | Active-high | clk | 0 | Instruction fetch acknowledge. Memory asserts this when instruction data is ready (typically 1 cycle latency). |

### Instruction Fetch Protocol

```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
clk     │   │   │   │   │   │   │   │
      ──┘   └───┘   └───┘   └───┘   └──

        ┌───────────────────┐
instr   │                   │
_req  ──┘                   └──────────

                         ┌───────────────┐
instr                     │               │
_ack  ────────────────────┘               └──

                         ┌───────────────┐
instr                     │  instruction  │
_rdata────────────────────│    0x2005     │──
                         └───────────────┘
```

---

## 3. Data Memory Interface

32-bit von Neumann data memory bus for load/store operations.

| Name | Width | Direction | Active Level | Clock Domain | Reset Value | Description |
|------|-------|-----------|-------------|-------------|-------------|-------------|
| `mem_addr` | 32 | output | — | clk | 0x00000000 | Data memory address. Driven during MEM_WR and MEM_RD states. |
| `mem_wdata` | 32 | output | — | clk | 0x00000000 | Data memory write data. Driven during MEM_WR state with the value to store. |
| `mem_rdata` | 32 | input | — | clk | 0x00000000 | Data memory read data. Valid when `mem_ack` is HIGH during MEM_RD state. |
| `mem_we` | 1 | output | Active-high | clk | 0 | Memory write enable. HIGH during store operations (STR). LOW for loads. |
| `mem_req` | 1 | output | Active-high | clk | 0 | Memory request. Asserted when a load or store is in progress. |
| `mem_ack` | 1 | input | Active-high | clk | 0 | Memory acknowledge. External memory asserts when data is ready (read) or written (store). |
| `mem_size` | 2 | output | — | clk | 2'b10 | Transfer size encoding. Always 2'b10 (32-bit word) in current implementation. |

### Data Memory Bus Protocol

**Write (STR):**
```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
clk     │   │   │   │   │   │   │   │
      ──┘   └───┘   └───┘   └───┘   └──

        ┌───────────────────────────┐
mem_req │                           │
      ──┘                           └──

        ┌───────────────────────────┐
mem_we  │                           │
      ──┘                           └──

        ┌───────────────────────────┐
mem_addr│      0x00000004           │
      ──┘                           └──

        ┌───────────────────────────┐
mem_wdt │      0x000000AB           │
      ──┘                           └──

                             ┌───────┐
mem_ack                     │       │
      ──────────────────────┘       └──
```

**Read (LDR):**
```
        ┌───┐   ┌───┐   ┌───┐   ┌───┐
clk     │   │   │   │   │   │   │   │
      ──┘   └───┘   └───┘   └───┘   └──

        ┌───────────────────────────┐
mem_req │                           │
      ──┘                           └──

mem_we ────────────────────────────────── (stays LOW)

        ┌───────────────────────────┐
mem_addr│      0x00000004           │
      ──┘                           └──

                             ┌───────┐
mem_ack                     │       │
      ──────────────────────┘       └──

                             ┌───────┐
mem_rdata                   │ 0xAB  │
      ──────────────────────┘       └──
```

---

## 4. Interrupt Interface

| Name | Width | Direction | Active Level | Clock Domain | Reset Value | Description |
|------|-------|-----------|-------------|-------------|-------------|-------------|
| `irq` | 1 | input | Active-high, level-sensitive | clk | 0 | Interrupt request. When HIGH, CPU will enter IRQ handler at next opportunity. **Note**: IRQ handling is reserved for future implementation in the current RTL. |

---

## 5. Signal Summary

| Category | Count | Signals |
|----------|-------|---------|
| Clock/Reset | 2 | `clk`, `rst_n` |
| Instruction Fetch | 4 | `instr_addr`, `instr_req`, `instr_rdata`, `instr_ack` |
| Data Memory | 7 | `mem_addr`, `mem_wdata`, `mem_rdata`, `mem_we`, `mem_req`, `mem_ack`, `mem_size` |
| Interrupt | 1 | `irq` |
| **Total** | **14** | **12 outputs, 6 inputs** |

### Drive Strength

All outputs are registered (driven from flip-flops clocked on `clk` rising edge). No combinational outputs.

### Reset Behavior

When `rst_n` goes LOW:
- All outputs reset to their reset values (see table above)
- FSM enters RESET state
- All internal registers (R0–R15) cleared to 0x00000000
- R13 (SP) set to 0x20004000
- APSR flags (N, Z, C, V) cleared to 0
- PC set to 0x00000000
