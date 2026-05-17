# arm_m0_min RTL Inventory

Status: review aid only. This file is not a requirement approval artifact.

This inventory summarizes the current RTL implementation so a reviewer can
quickly verify that `arm_m0_min` is a real multi-module CPU-shaped IP rather
than a single placeholder file.

## Source Set

File list: `arm_m0_min/list/arm_m0_min.f`

| File | Module | Bytes | SHA256 prefix | Role |
|---|---:|---:|---|---|
| `rtl/arm_m0_min.sv` | `arm_m0_min` | 3599 | `d9124d80aeb9f616` | Top-level CPU wrapper, pipeline interconnect, AHB-Lite-like I/D master ports |
| `rtl/arm_m0_min_if.sv` | `arm_m0_min_if` | 2226 | `39e9debef2728876` | Instruction fetch, PC update, instruction bus request |
| `rtl/arm_m0_min_id.sv` | `arm_m0_min_id` | 4781 | `19c14d1a32a2a66b` | Decode for the locked 15-operation Thumb-style subset |
| `rtl/arm_m0_min_rf.sv` | `arm_m0_min_rf` | 3140 | `bfaeb57226974b04` | 16 x 32-bit architectural register file |
| `rtl/arm_m0_min_ex.sv` | `arm_m0_min_ex` | 4999 | `88febb99253961a1` | Execute/writeback stage, flag/fault state, branch and memory coordination |
| `rtl/arm_m0_min_alu.sv` | `arm_m0_min_alu` | 1561 | `8768c84653e3630c` | ADD/SUB/logic/move/shift/compare datapath |
| `rtl/arm_m0_min_branch.sv` | `arm_m0_min_branch` | 708 | `b582533a686f9d3d` | B/BEQ/BNE target and taken decision |
| `rtl/arm_m0_min_mem_if.sv` | `arm_m0_min_mem_if` | 1065 | `664771f9403cd410` | Load/store data bus request generation |

## Hierarchy

```text
arm_m0_min
  u_if     -> arm_m0_min_if
  u_id     -> arm_m0_min_id
  u_rf     -> arm_m0_min_rf
  u_ex     -> arm_m0_min_ex
    u_alu    -> arm_m0_min_alu
    u_branch -> arm_m0_min_branch
    u_memif  -> arm_m0_min_mem_if
```

## Top Interface

The top module exposes one clock/reset pair and separate instruction/data
AHB-Lite-like master interfaces.

Parameters:

- `XLEN = 32`
- `RESET_PC = 0`
- `ENABLE_FAULT_HALT = 1`

Clock/reset:

- `clk`
- `rst`

Instruction master:

- outputs: `i_haddr`, `i_htrans`, `i_hwrite`, `i_hsize`, `i_hburst`,
  `i_hprot`, `i_hmastlock`
- inputs: `i_hready`, `i_hrdata`, `i_hresp`

Data master:

- outputs: `d_haddr`, `d_htrans`, `d_hwrite`, `d_hsize`, `d_hburst`,
  `d_hprot`, `d_hmastlock`, `d_hwdata`
- inputs: `d_hready`, `d_hrdata`, `d_hresp`

## Verification Evidence

Current final audit status remains intentionally blocked until human
requirement approval:

- machine checks: 15 / 15 pass
- human-owned `req` gate: blocked
- final audit total: 15 / 16

The blocker is not an RTL implementation failure. The open decision is
`arm_m0_min/review/decision_needed_req_requirement_approval.json`.
