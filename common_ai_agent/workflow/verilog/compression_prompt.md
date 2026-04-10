You are summarizing an RTL design session for context compression.

Preserve the following in your summary:
- Module names, port lists, and parameter definitions
- Current simulation status (pass/fail, error count, warning count)
- File paths for all .v and .sv files created or modified
- Any unresolved latch warnings, multi-driven net errors, or X-propagation issues
- Current todo task index and loop iteration count
- Key design decisions (clock domain, reset polarity, state machine encoding)

Format:
[RTL Session Summary]
Modules: <list>
Files: <list of paths>
Sim status: <PASS|FAIL|PENDING> (<error_count> errors, <warning_count> warnings)
Current task: <index>/<total> — <description>
Open issues: <list or "none">
Key decisions: <list>
