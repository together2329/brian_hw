# RTL Gen Plan Mode Rules

1. Read the spec first — task 1 is ALWAYS "Read <module>_spec.md"
2. Split tasks: ports/params → registers → combinational → outputs → lint
3. Each task targets ONE always block or ONE output group
4. Include expected signal names in task detail
5. Final task MUST be lint check with 0-error exit criterion
