# MAS Plan Mode Rules

## IP Directory Structure (always use this layout)

```
<ip_name>/
├── mas/   ← <ip_name>_mas.md          [MAS] task output
├── rtl/   ← <ip_name>.sv              [RTL] task output
├── list/  ← <ip_name>.f               [RTL] task output (filelist)
├── tb/    ← tb_<ip_name>.sv, tc_*.sv  [TB] task output
├── sim/   ← sim_report.txt, *.vcd     [SIM] task output
└── lint/  ← lint_report.txt           [LINT] task output
```

## Rules

1. ALWAYS start with a [MAS] task — write `<ip>/mas/<ip>_mas.md` before any code
2. The MAS must cover both RTL (§2-§8) and DV (§9) before delegating to any sub-agent
3. Split tasks by agent: tag each task with [MAS], [RTL], [TB], [SIM], [LINT], [DOC]
4. RTL tasks must reference MAS §2 (Interface) and §8 (RTL Notes) — output to `<ip>/rtl/` and `<ip>/list/`
5. TB tasks must reference MAS §9 (DV Plan) — output to `<ip>/tb/`
6. RTL tasks must come before TB tasks in the sequence
7. Simulation loop task is REQUIRED — use loop=true, max_loop_iterations=15, runs in `<ip>/sim/`
8. Lint task runs on `<ip>/rtl/<ip>.sv` — writes `<ip>/lint/lint_report.txt`
9. Documentation task is LAST — only after sim passes — writes to `<ip>/mas/`
10. Each task detail must include: full relative input paths, full relative output paths, acceptance criteria
11. Use validator on simulation tasks: `"bash workflow/tb_gen/scripts/check_sim_pass.sh"`
