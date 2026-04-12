# RTL Gen Plan Mode Rules

## IP Directory Structure

```
<ip_name>/
├── mas/   → <ip_name>_mas.md     (READ — task 1 input)
├── rtl/   → <ip_name>.sv         (WRITE — your main output)
├── list/  → <ip_name>.f          (WRITE — filelist output)
├── tb/                           (never touch)
├── sim/                          (never touch)
└── lint/                         (never touch)
```

## Input: MAS Document

Task 1 is ALWAYS **"Read `<ip>/mas/<ip>_mas.md`"** — the Micro Architecture Specification from mas-gen.

To find the correct MAS file:
1. If `MODULE_NAME` env var is set → read `${MODULE_NAME}/mas/${MODULE_NAME}_mas.md`
2. Otherwise → run `/find-mas` to list available `*_mas.md` files, pick the target module
3. Confirm the MAS is complete (sections §2–§8 present) before planning RTL tasks

## Task Decomposition Rules

1. Split tasks by MAS section: §2 ports/params → §3 FSM → §3 datapath → §4 registers → §5 interrupt → §6 memory → filelist → lint
2. Each task targets ONE always block or ONE output group — never mix
3. Include expected signal names (from MAS §2 port table) in every task detail
4. Reference the MAS section explicitly in each task (e.g. "per MAS §3 FSM table")
5. Write `<ip>/list/<ip>.f` after RTL is complete — list all `.sv` files needed for sim
6. Final task MUST be lint check: `/lint <ip>/rtl/<ip>.sv` — writes `<ip>/lint/lint_report.txt`

## MAS Completeness Check (before planning)

Verify the MAS has:
- [ ] §2 port table with all signals named and sized
- [ ] §3 FSM state table (if stateful design)
- [ ] §4 register map (if CSR present)
- [ ] §8 RTL implementation notes (reset style, coding conventions)

If any required section is missing, report to mas-gen before starting RTL.
