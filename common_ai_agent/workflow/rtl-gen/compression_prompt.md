You are summarizing an RTL generation session.

Preserve:
- Module name and file path
- Port list and parameter values
- Current implementation status (which always blocks are done)
- Lint result: errors=N warnings=N
- Current task index / total
- Any unresolved latch warnings or width mismatches

Format:
[RTL Gen Summary]
Module  : <name> → <file.sv>
Ports   : <count> inputs, <count> outputs
Status  : <SPEC_READ|HEADER|FF_BLOCKS|COMB_BLOCKS|DONE>
Lint    : <errors=N warnings=N | PENDING>
Task    : <index>/<total>
Issues  : <list or none>
