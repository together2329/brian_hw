# mini_cpu Rerun (2026-05-17)

Purpose: rerun the existing `mini_cpu` artifact as a CPU-class regression and
separate SSOT/workflow blockers from RTL/sim failures.

## Scope

| Item | Value |
|---|---|
| Source artifact | `/Users/brian/Desktop/Project/NEW_IP_CPU/mini_cpu` |
| Scratch root | `/Users/brian/Desktop/Project/MINI_CPU_RERUN_20260517_001` |
| IP | `mini_cpu` |
| Architecture claimed by SSOT | ARMv7-M Thumb-2, 3-stage pipeline, AHB-Lite Harvard bus |
| Policy | Test from scratch copy; do not patch generated IP artifacts to create a pass |

## Commands Run

SSOT contract check:

```bash
bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh mini_cpu
```

Manual SV compile/sim smoke in the scratch copy:

```bash
cd /Users/brian/Desktop/Project/MINI_CPU_RERUN_20260517_001/mini_cpu
iverilog -g2012 -o sim/mini_cpu_rerun.out -f list/mini_cpu.f
vvp sim/mini_cpu_rerun.out > sim/sim_report_rerun.txt
```

Common headless workflow checks:

```bash
PYTHONPATH=src:. python3 src/headless_workflow.py \
  --root /Users/brian/Desktop/Project/MINI_CPU_RERUN_20260517_001 \
  --ip mini_cpu \
  --model gpt-5.3-codex \
  --stages fl-model-gen,equiv-goals,tb-gen,sim,sim-debug,coverage,goal-audit \
  --provider fake

PYTHONPATH=src:. python3 src/headless_workflow.py \
  --root /Users/brian/Desktop/Project/MINI_CPU_RERUN_20260517_001 \
  --ip mini_cpu \
  --model gpt-5.3-codex \
  --stages lint \
  --provider fake
```

## Evidence

SSOT:

- `check_ssot_disk.sh`: FAIL.
- Reason: `mini_cpu/yaml/mini_cpu.ssot.yaml only has 21 top-level section keys
  (need >=34)`.
- Parsed SSOT has 13 submodules and 15 test scenarios, but
  `function_model.transactions=0` and `cycle_model.pipeline=0`.

Common workflow:

- `fl-model-gen`: PASS, but only because the emitter can produce structural
  decomposition/coverage from the incomplete SSOT.
- `equiv-goals`: BLOCKED.
- `verify/equivalence_goals.json`: total 115, required 98, blocked 17.
- Blocked goals include `EQ_BLOCKED_FUNCTION_MODEL`,
  `EQ_BLOCKED_CYCLE_MODEL`, and `EQ_SCENARIO_SC1` through `EQ_SCENARIO_SC15`.
- Downstream common `tb-gen`, `sim`, `sim-debug`, `coverage`, and
  `goal-audit` did not run in the common sequence because `equiv-goals` blocked
  first.

Lint:

- Common lint stage: FAIL.
- `lint/dut_lint.json`: `errors=1`, `warnings=134`,
  `style_violations=44`, `suppression_violations=0`.
- pyslang: errors 0, warnings 120.
- Verilator: errors 1, warnings 14.
- Style violations include generated RTL subset violations such as
  `always_ff`, `always_comb`, and `for` loops in RTL.

Manual SV sim:

- Icarus compile returns 0 but emits decoder width warnings and unsupported
  constant-select warnings.
- `sim/sim_report_rerun.txt`: 2/4 checks passed, 2 failures.
- Passing checks: reset/thread-mode status and `cpu_lockup=0`.
- Failing checks: SC2 ADD/SUB result memory observations:
  expected `0x00000008`/`0x00000006`, observed `0x00000000`/`0x20000100`.

## Interpretation

This is not a green CPU-class reference run. The current `mini_cpu` artifact is
blocked before common TB/sim signoff because the SSOT is not canonical enough
for executable FL/CL/equivalence goals. Separately, the existing RTL/testbench
smoke run still fails basic ALU result observation, and lint is not clean.

The next productive fix order is:

1. Repair or regenerate `mini_cpu` SSOT through `ssot-gen` so it has canonical
   function_model transactions, cycle_model pipeline/ordering, coverage gates,
   and traceability.
2. Regenerate FL/CL/equivalence goals from that SSOT.
3. Run `rtl-gen` against the canonical SSOT/TODO ledger instead of treating the
   current hand-authored RTL as authority.
4. Then rerun lint, generated TB, sim, sim-debug, coverage, and goal-audit.

Do not treat the manual 2/4 sim result as a pipeline pass. It is useful failure
evidence only.
