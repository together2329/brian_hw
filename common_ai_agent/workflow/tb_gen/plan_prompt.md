# TB Gen Plan Mode Rules

## IP Directory Structure

```
<ip_name>/
├── mas/   → <ip_name>_mas.md     (READ — DV Plan §9)
├── rtl/   → <ip_name>.sv         (READ — DUT, never modify)
├── list/  → <ip_name>.f          (READ — filelist for sim compile)
├── tb/    → tb_<ip_name>.sv      (WRITE — TB top)
│            tc_<ip_name>.sv      (WRITE — test cases)
├── sim/   → sim_report.txt       (WRITE)
│            <ip_name>_wave.vcd   (WRITE)
└── lint/                         (never touch)
```

## Input: MAS Document + DUT RTL

Task 1 is ALWAYS **"Read `<ip>/mas/<ip>_mas.md` and `<ip>/rtl/<ip>.sv`"** — both required before any TB code.

To find input files:
1. If `MODULE_NAME` env var is set → read `${MODULE_NAME}/mas/${MODULE_NAME}_mas.md` and `${MODULE_NAME}/rtl/${MODULE_NAME}.sv`
2. Otherwise → run `/find-mas` to locate the MAS, then find matching `.sv` in `<ip>/rtl/`

## MAS Sections to Extract Before Planning

- **§2 ports** → DUT instantiation signal list
- **§4 registers** → register R/W task sequences
- **§5 interrupts** → interrupt flow sequences
- **§6 memory** → memory fill/check sequences
- **§9 DV Plan** → test sequence table S1-SN (these become tc_ tasks), coverage goals, SVA assertions

## Task Decomposition Rules

2. Split: `tc_*.sv` (test cases) before `tb_*.sv` (top level) — bottom-up order
3. Name each tc_ task after the MAS §9 sequence ID: `tc_S1_reset`, `tc_S2_normal_op`, etc.
4. List ALL test case names (from MAS §9 S1-SN) before writing any code
5. Sim loop task is REQUIRED — `loop=true`, `max=15`, `validator=check_sim_pass.sh`
6. Coverage review task at end — verify MAS §9 coverage goals met

## Bug Triage Rule

If sim fails:
- **TB bug** (wrong stimulus, wrong expected value) → fix tc_*.sv here
- **DUT bug** (RTL logic error, wrong output) → report `[MAS ESCALATE] rtl_gen` — do NOT edit DUT yourself
