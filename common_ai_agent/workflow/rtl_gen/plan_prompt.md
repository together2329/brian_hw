# RTL Gen Plan Mode Rules

## Input: MAS Document

Task 1 is ALWAYS **"Read `<module>_mas.md`"** — the Micro Architecture Specification from mas_gen.

To find the correct MAS file:
1. If `MODULE_NAME` env var is set → read `${MODULE_NAME}_mas.md`
2. Otherwise → run `/find-mas` to list available `*_mas.md` files, pick the target module
3. Confirm the MAS is complete (sections §2–§8 present) before planning RTL tasks

## Task Decomposition Rules

2. Split tasks by MAS section: §2 ports/params → §4 registers → §3 FSM → §3 datapath → §5 interrupt → §6 memory → lint
3. Each task targets ONE always block or ONE output group — never mix
4. Include expected signal names (from MAS §2 port table) in every task detail
5. Reference the MAS section explicitly in each task (e.g. "per MAS §3 FSM table")
6. Final task MUST be lint check: `/lint <module>.sv` with 0 errors exit criterion

## MAS Completeness Check (before planning)

Verify the MAS has:
- [ ] §2 port table with all signals named and sized
- [ ] §3 FSM state table (if stateful design)
- [ ] §4 register map (if CSR present)
- [ ] §8 RTL implementation notes (reset style, coding conventions)

If any required section is missing, report to mas_gen before starting RTL.
