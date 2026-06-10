# sim_debug — no TODO templates by design

This directory is intentionally empty.

`sim_debug` is an investigative workflow: sim-failure root-cause analysis
follows a different pattern every time (wave inspection, signal grep, FL/RTL
goal audit, regression bisect). A fixed TODO sequence would force premature
structure on what is really a free-form debugging session.

## Use these slash commands instead

| Command | Defined in | Purpose |
|---|---|---|
| `/wave <ip>` | `workflow/sim_debug/commands/wave.json` | Open VCD / FST inspection helpers |
| `/sig <ip> <pattern>` | `workflow/sim_debug/commands/sig.json` | Grep signals in waveform / scoreboard |
| `/goal-audit <ip>` | `workflow/sim_debug/commands/goal-audit.json` | Audit FL-vs-RTL equivalence goal status |
| `/sim-debug <ip>` | `workflow/sim_debug/commands/sim-debug.json` | Interactive debug entry point |

If a repeatable diagnostic pattern emerges from sim_debug sessions, capture it
as a wiki entry under `doc/wiki/` rather than forcing it into a TODO template.
