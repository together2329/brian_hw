You are summarizing a YAML SSOT generation session.

Preserve:
- IP name and current YAML authoring status
- Current phase: REQ / YAML / VALIDATE / TEMPLATE / GENERATE / SIM
- File paths for all YAML files written
- Schema validation status: PASS/FAIL, error count
- Jinja2 template rendering status
- Simulation status: PASS/FAIL, scoreboard checks
- Current todo task index and total
- Any pending SSOT HANDOFF instructions
- Traceability decisions made

Format:
[SSOT Session Summary]
Project      : <ip_name>
Phase        : <REQ|YAML|VALIDATE|TEMPLATE|GENERATE|SIM>
YAML files   : <list with status>
Schema status: <PASS|FAIL> (errors=N)
Gen status   : <PASS|FAIL> (files generated=N)
Sim status   : <PASS|FAIL|PENDING> (checks=N passed)
Task         : <current>/<total> — <description>
Handoff      : <pending agent or NONE>
