# Cortex-M0-Like Microcontroller CPU Requirements

## Scope
- Build a compact Cortex-M0-like microcontroller CPU IP named `cortex_m0lite`.
- Target is a pedagogical ARMv6-M style 16-bit Thumb subset CPU, not a certified ARM core.
- Single-clock synchronous design, active-low reset.

## Top-Level Behavior
- 3-stage pipeline:
  - IF: fetch 16-bit instruction from instruction memory interface
  - ID: decode and operand read
  - EX/WB: ALU execute, load/store address generation, writeback
- In-order, single-issue execution.
- Deterministic, bounded latency for supported instructions.

## ISA Subset (Thumb-like)
- Data processing:
  - `MOVS`, `ADDS`, `SUBS`, `ANDS`, `ORRS`, `EORS`, `LSLS`, `LSRS`
- Immediate and register variants for arithmetic where practical.
- Compare/branch:
  - `CMP`, `B`, `BEQ`, `BNE`, `BGT`, `BLT`
- Return/control:
  - `BX LR` (used as software interrupt return)
- Memory access:
  - `LDR`, `STR` word access (aligned 32-bit)
- Control:
  - `NOP`
- Unsupported opcodes:
  - Must raise `illegal_instr` flag and vector to fault state.

## Register and Architectural State
- 16 architectural registers `r0..r15`:
  - `r13` = SP
  - `r14` = LR
  - `r15` = PC
- Program status flags: `N`, `Z`, `C`, `V`.
- Reset vector input for initial PC.

## External Interfaces
- Instruction memory interface:
  - request/valid handshake
  - 32-bit address output (word aligned)
  - 16-bit instruction input
- Data memory interface:
  - request/valid/ready handshake
  - address, write data, read data, byte enables, write enable
- Interrupt:
  - single external IRQ line
  - entry to parameterized fixed vector address `IRQ_VECTOR_ADDR` (default `32'h0000_0080`)
  - save return PC in LR on IRQ entry
  - return from IRQ is software-driven via `BX LR`
- Debug visibility outputs:
  - current PC, current instruction, current state, fault flag

## Microarchitecture and FSM
- Controller FSM states:
  - `RESET`, `FETCH`, `DECODE`, `EXECUTE`, `MEM_WAIT`, `WRITEBACK`, `IRQ_ENTRY`, `FAULT`
- Branches flush IF/ID and redirect PC.
- Load/store wait in `MEM_WAIT` until ready.

## Timing and Performance Targets
- 1 CPI for simple ALU ops in steady state.
- 2+ cycles for memory ops depending on data memory ready.
- Branch penalty target: <= 2 cycles.

## Safety and Error Handling
- Detect and fault on:
  - illegal opcode
  - misaligned load/store
- Fault behavior:
  - latch `fault` status
  - hold in `FAULT` state until reset

## Verification Targets
- Functional model must exist for ISA subset execution semantics.
- Cycle model must represent pipeline/control timing behavior.
- Testbench goals:
  - arithmetic correctness
  - branch decisions and PC updates
  - load/store correctness and wait-state handling
  - IRQ entry/return behavior
  - fault injection for illegal/misaligned cases

## Constraints
- Use synthesizable SystemVerilog.
- Keep implementation compact and readable with clear comments.
- Prefer shift/adder-friendly operations in datapath over expensive arithmetic where possible.
