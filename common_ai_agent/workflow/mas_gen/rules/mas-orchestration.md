# MAS Orchestration Rules

## Agent Context Switching

When you switch to a sub-agent context (rtl_gen, tb_gen), you MUST:
1. Output a [MAS HANDOFF] block (format defined in system_prompt)
2. Read the target agent's system_prompt.md before proceeding
3. Follow that agent's coding rules strictly
4. Report back with [MAS RESULT] when the delegated task is complete

## Quality Gates

| Gate | Condition | Blocks |
|------|-----------|--------|
| RTL → TB | lint: 0 errors | tb_gen cannot start |
| TB → SIM | TB compiles | sim loop cannot start |
| SIM → DOC | sim: 0 errors, 0 warnings | doc_gen cannot start |

## File Ownership

| Agent | Owns | Never touches |
|-------|------|---------------|
| rtl_gen | `<module>.sv` | `tb_*.sv`, `tc_*.sv`, `*.md` |
| tb_gen | `tb_*.sv`, `tc_*.sv` | `<module>.sv` |
| mas_gen | `*_spec.md` | source files (read-only) |

## Error Recovery

- RTL lint error → return to rtl_gen context, fix, re-lint
- Sim error → return to tb_gen context if TB bug, rtl_gen if DUT bug
- Max sim iterations → escalate to user with [MAS BLOCKED] report
