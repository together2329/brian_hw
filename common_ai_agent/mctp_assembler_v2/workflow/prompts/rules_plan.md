# RULES — Plan Mode

1. Planning only — do NOT write files, run commands, or execute tools during planning
2. Research first with tools, then call todo_write() once with the complete task list
3. Each task must be atomic — one file, one concern per task
4. Every task MUST have BOTH fields filled — never leave either empty:
   - `detail`: HOW to implement — specific approach, constraints, file paths, key decisions
   - `criteria`: newline-separated acceptance checklist (2–4 items), e.g. "File compiles without errors\nAll ports connected\nSimulation passes"
5. Sequence matters — order tasks so each builds on the previous
6. Make reasonable assumptions based on research; only ask if genuinely blocked
7. Exit plan mode explicitly before any implementation begins
8. Use loop tasks for iterative work (simulation, lint cycles) with clear exit_condition
