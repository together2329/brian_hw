# rv32i_min IP Requirements

## Intent

Build a minimal **RV32I base integer ISA** CPU as a triple-LLM smoke
fixture for the common_ai_agent ssot→audit pipeline. The block is
deliberately broader than the `arm_m0_min` smoke fixture (37
instructions vs 15), but still excludes M/A/F/D/C extensions, debug,
PMP, MMU, interrupts, and CSR space. The same SSOT must drive an
identical run on three different model providers so we can compare
their authoring quality on a non-trivial CPU.

## Functional Behavior

- ISA: **RV32I base, 37 instructions**, all 32-bit aligned:
  `LUI AUIPC JAL JALR BEQ BNE BLT BGE BLTU BGEU LB LH LW LBU LHU SB SH SW
   ADDI SLTI SLTIU XORI ORI ANDI SLLI SRLI SRAI ADD SUB SLL SLT SLTU XOR
   SRL SRA OR AND FENCE ECALL EBREAK`.
- Width: 32-bit datapath, 32-bit fixed instructions.
- Register file: 32 × 32-bit (`x0..x31`); `x0` is hardwired zero
  (writes ignored, reads return 0).
- Pipeline: 3-stage IF / ID-EX / MEM-WB, in-order, single-issue.
- Bus: simple synchronous instruction bus + data bus
  (`i_addr/i_rdata/i_valid` and `d_addr/d_wdata/d_rdata/d_we/d_be/d_valid`),
  no AHB/AXI handshake — registered-ready model only.
- `clk` is the only clock; `rst_n` is active-low asynchronous reset.
- On reset: `pc <= 0x00000000`, all `x[1..31] <= 0`.
- `ECALL` and `EBREAK` advance `pc` by 4 and pulse a one-cycle
  `excpt_o` strobe; no trap delegation logic in this profile.
- `FENCE` is implemented as a one-cycle pipeline bubble (no memory
  ordering hardware in this profile).
- `JAL`/`JALR` write `pc + 4` into `rd`. `JALR` clears bit 0 of the
  computed target.
- Branches use signed comparisons except `BLTU`/`BGEU`.
- Loads and stores honour the byte-enable on `d_be`. `LB`/`LH` perform
  sign-extension; `LBU`/`LHU` zero-extend.
- Misaligned data accesses raise `excpt_o` for one cycle and do not
  retire the instruction (architectural state unchanged).
- `SLLI/SRLI/SRAI` shift amounts are restricted to `0..31` per the
  RV32I encoding (`shamt[5]` must be 0; otherwise illegal).

## Non-Goals

- No interrupts, NVIC, debug, performance counters, CSR file beyond
  what `ECALL`/`EBREAK`/`FENCE` need.
- No M / A / F / D / C extension support.
- No bus transactions beyond the registered ready synchronous bus.
- No clock-domain crossing, no power gating, no DFT chains.
- No branch prediction or speculative execution.

## Verification Hints

- Stimulus must exercise every one of the 37 mnemonics at least once
  with both random operands and edge values (0, ±1, INT_MAX, INT_MIN,
  0xFFFFFFFF, register `x0`, signed/unsigned compare boundaries).
- Coverage must include: every opcode hit, taken/untaken for each
  branch, sign-extension correctness for `LB`/`LH`, byte-enable
  patterns for stores, `x0` write-to-zero, `JAL`/`JALR` link-write,
  misaligned-fault, `ECALL`/`EBREAK` strobe.
- A simple ISS-style reference model (`functional_model.py`) drives
  expected register and PC trajectories cycle-by-cycle.

## Run Plan

This requirement file is the **single shared SSOT input** for three
parallel pipeline runs:

```
_runspaces/triple_llm_test/codex/   --model gpt-5.3-codex
_runspaces/triple_llm_test/claude/  --model claude-cli
_runspaces/triple_llm_test/cursor/  --model cursor-cli
```

Each sandbox runs `ssot-gen → fl-model-gen → cl-model-gen →
equiv-goals → rtl-gen → tb-gen → sim → sim-debug → lint → coverage →
goal-audit`. No manual fixes between stages; the pipeline must
self-repair through the existing repair loops or stop at the natural
human-gate. Side-by-side comparison of the three runs will populate
`_runspaces/triple_llm_test/COMPARISON.md` after the runs complete.
