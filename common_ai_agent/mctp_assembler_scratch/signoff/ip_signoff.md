# IP Signoff - mctp_assembler_scratch

- Status: `fail`
- Generated: `2026-05-31T12:00:06Z`
- Contract: `IP_SIGNOFF.md`

| Gate | Status | Artifact | Summary |
| --- | --- | --- | --- |
| `ssot` | `pass` | `yaml/mctp_assembler_scratch.ssot.yaml` | SSOT exists and parses |
| `ip_contract` | `pass` | `verify/ip_contract.json` | capabilities=14 required_evidence=14 |
| `fl_model` | `pass` | `model/fl_model_check.json` | FL artifact check passed=true |
| `cl_model` | `pass` | `model/cl_model_check.json` | CL self-check passed=true |
| `equivalence_goals` | `pass` | `verify/equivalence_goals.json` | goals=91 blocked=0 |
| `rtl_todo` | `fail` | `rtl/rtl_todo_plan.json` | RTL todo/static audit gate |
| `rtl_provenance` | `pass` | `rtl/rtl_authoring_provenance.json` | RTL provenance matches current todo plan |
| `rtl_compile` | `pass` | `rtl/rtl_compile.json` | DUT-only RTL compile is clean |
| `lint` | `pass` | `lint/dut_lint.json` | DUT-only lint is clean |
| `tb_python_compile` | `pass` | `tb/cocotb/tb_py_compile.json` | TB Python compiled before simulation |
| `simulation` | `pass` | `sim/results.xml` | tests=1 failures=0 errors=0 |
| `scoreboard` | `fail` | `sim/scoreboard_events.jsonl` | rows=91 goals_with_rows=91 |
| `coverage` | `fail` | `cov/coverage.json` | status=owner_routed |
| `mutation_guard` | `pass` | `mutation/mutation_report.json` | status=blocked_baseline kill_rate=None |
| `waivers` | `pass` | `signoff/goal_ledger.json` | waivers explicit and reviewable |

## Issues

- `rtl_todo`: rtl_todo gate status is 'fail', expected pass; rtl_todo gate open_required_todos=23, expected 0; rtl_todo gate static_missing=19, expected 0; rtl_todo gate all_required_todos_pass must be true
- `scoreboard`: line 2: passed must be true; line 3: passed must be true; line 4: passed must be true; line 5: passed must be true; line 6: passed must be true; line 7: passed must be true; line 8: passed must be true; line 9: passed must be true; line 10: passed must be true; line 11: passed must be true; line 12: passed must be true; line 13: passed must be true; line 15: passed must be true; line 17: passed must be true; line 18: passed must be true; line 19: passed must be true; line 23: passed must be true; line 25: passed must be true; line 26: passed must be true; line 27: passed must be true
- `coverage`: coverage status is 'owner_routed', expected pass
