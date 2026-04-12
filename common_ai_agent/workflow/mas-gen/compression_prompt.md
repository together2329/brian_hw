You are summarizing a MAS (Master Agent System) RTL project session.

Preserve:
- Module name(s) and their current implementation status
- Current phase: SPEC / RTL / TB / SIM / DOC
- File paths for all generated files (.sv, .md, .vcd)
- Simulation status: PASS/FAIL, error count, warning count, loop iteration
- Current todo task index and total
- Any pending MAS HANDOFF instructions
- Key design decisions (interface, parameters, clock/reset)

Format:
[MAS Session Summary]
Project   : <module_name>
Phase     : <SPEC|RTL|TB|SIM|DOC>
Files     : <list>
Sim status: <PASS|FAIL|PENDING> (errors=N warnings=N iter=N)
Task      : <current_index>/<total> — <description>
Decisions : <list>
