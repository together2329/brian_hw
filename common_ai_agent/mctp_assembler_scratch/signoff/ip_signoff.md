# IP Signoff - mctp_assembler_scratch

- Status: `pass`
- Generated: `2026-06-01T11:37:45Z`
- Contract: `IP_SIGNOFF.md`

| Gate | Status | Artifact | Summary |
| --- | --- | --- | --- |
| `ssot` | `pass` | `yaml/mctp_assembler_scratch.ssot.yaml` | SSOT exists and parses |
| `ip_contract` | `pass` | `verify/ip_contract.json` | capabilities=14 required_evidence=14 |
| `fl_model` | `pass` | `model/fl_model_check.json` | FL artifact check passed=true |
| `cl_model` | `pass` | `model/cl_model_check.json` | CL self-check passed=true |
| `equivalence_goals` | `pass` | `verify/equivalence_goals.json` | goals=86 blocked=0 |
| `rtl_todo` | `pass` | `rtl/rtl_todo_plan.json` | RTL todo/static audit gate |
| `rtl_provenance` | `pass` | `rtl/rtl_authoring_provenance.json` | RTL provenance matches current todo plan |
| `rtl_compile` | `pass` | `rtl/rtl_compile.json` | DUT-only RTL compile is clean |
| `lint` | `pass` | `lint/dut_lint.json` | DUT-only lint is clean |
| `tb_python_compile` | `pass` | `tb/cocotb/tb_py_compile.json` | TB Python compiled before simulation |
| `simulation` | `pass` | `sim/results.xml` | tests=1 failures=0 errors=0 |
| `simulation_quality` | `pass` | `sim/simulation_quality.json` | status=pass issues=0 |
| `scoreboard` | `pass` | `sim/scoreboard_events.jsonl` | rows=86 goals_with_rows=86 |
| `coverage` | `pass` | `cov/coverage.json` | status=pass |
| `mutation_guard` | `pass` | `mutation/mutation_report.json` | status=pass kill_rate=0.5938 |
| `waivers` | `pass` | `signoff/goal_ledger.json` | waivers explicit and reviewable |
