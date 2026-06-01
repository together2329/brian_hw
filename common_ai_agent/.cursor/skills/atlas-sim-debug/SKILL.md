---
name: atlas-sim-debug
description: Work with sim_debug for FL-vs-RTL mismatch classification, simulation quality evidence, waveform/debug evidence, and goal audit. Use for sim-debug, mismatch classification, waveform analysis, simulation quality, or goal-audit tasks.
---

# Atlas Sim Debug

`sim_debug` owns FL-vs-RTL mismatch classification, simulation quality checks over scoreboard evidence, and final equivalence goal audit.

## Runtime Workspace

- Workspace: `workflow/sim_debug/workspace.json`
- Commands: `workflow/sim_debug/commands/sim-debug.json`, `workflow/sim_debug/commands/goal-audit.json`
- Scripts: `workflow/sim_debug/scripts/*`, especially `check_simulation_quality.py`, `compare_fl_rtl_results.py`, `mutation_guard.py`, `sig_search.sh`, and `wave_info.sh`

Common-engine stages:

- `sim-debug` → `/sim-debug <ip>`
- `goal-audit` → `/goal-audit <ip>`

Evidence:

- `sim/fl_rtl_compare.json`
- `sim/mismatch_classification.json`
- `sim/simulation_quality.json`
- `sim/simulation_quality.md`
- `sim/fl_rtl_goal_audit.json`
- `sim/scoreboard_events.jsonl`
- `logs/stage_engine/sim-debug.json`
- `logs/stage_engine/goal-audit.json`

## Cursor Use

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --from-stage sim-debug --until goal-audit
```

Run the focused quality gate when TB or sim evidence changed and the full stage is not needed:

```bash
python3 workflow/sim_debug/scripts/check_simulation_quality.py <ip> --root .
```

If classification says `llm_loop_allowed: false`, stop for human review instead of changing SSOT or expected behavior.
Do not claim a passing sim-debug state from stale `simulation_quality.json`; rerun the owning stage or quality script after RTL, TB, SSOT, equivalence-goal, or scoreboard changes.
