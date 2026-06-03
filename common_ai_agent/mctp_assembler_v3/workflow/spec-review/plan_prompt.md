
════════════════════════════════════════
SPEC REVIEW PLAN MODE RULES
════════════════════════════════════════
- Before planning any analysis task, call spec_navigate(spec, "root") to map the spec structure.
- Each task must target ONE spec section or ONE spec comparison — do not mix specs in one task.
- Include the target section reference (§X.Y.Z) in each task's detail= field.
- Always add a "Summarize findings" task at the end.
- For cross-spec comparisons, create separate tasks per spec, then a synthesis task.
