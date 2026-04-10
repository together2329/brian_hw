# RULES — Plan Mode

1. Planning only — do NOT write files, run commands, or execute tools during planning
2. Use todo_write() as the FIRST action to establish the task list
3. Each task must be atomic — one file, one concern per task
4. Include `detail` field with acceptance criteria and implementation notes
5. Sequence matters — order tasks so each builds on the previous
6. No assumptions — add open questions as low-priority tasks
7. Exit plan mode explicitly before any implementation begins
8. Use loop tasks for iterative work (simulation, lint cycles) with clear exit_condition
