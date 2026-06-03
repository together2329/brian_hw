# IP Signoff - mctp_assembler_v3

- Status: `fail`
- Generated: `2026-06-03T13:24:52Z`
- Contract: `IP_SIGNOFF.md`

| Gate | Status | Artifact | Summary |
| --- | --- | --- | --- |
| `ssot` | `pass` | `yaml/mctp_assembler_v3.ssot.yaml` | SSOT exists and parses |
| `ip_contract` | `pass` | `verify/ip_contract.json` | capabilities=12 required_evidence=14 |
| `fl_model` | `pass` | `model/fl_model_check.json` | FL artifact check passed=true |
| `cl_model` | `pass` | `model/cl_model_check.json` | CL self-check passed=true |
| `equivalence_goals` | `pass` | `verify/equivalence_goals.json` | goals=90 blocked=0 |
| `rtl_todo` | `fail` | `rtl/rtl_todo_plan.json` | RTL todo/static audit gate |
| `rtl_provenance` | `fail` | `rtl/rtl_authoring_provenance.json` | RTL provenance matches current todo plan |
| `rtl_compile` | `pass` | `rtl/rtl_compile.json` | DUT-only RTL compile is clean |
| `lint` | `fail` | `lint/dut_lint.json` | DUT-only lint is clean |
| `tb_python_compile` | `fail` | `tb/cocotb/tb_py_compile.json` | TB Python compiled before simulation |
| `simulation` | `fail` | `sim/results.xml` | tests=0 failures=0 errors=0 |
| `simulation_quality` | `fail` | `sim/simulation_quality.json` | status=None issues=None |
| `scoreboard` | `fail` | `sim/scoreboard_events.jsonl` | rows=0 goals_with_rows=0 |
| `coverage` | `fail` | `cov/coverage.json` | status=None |
| `truth_coverage` | `fail` | `signoff/truth_coverage.json` | status=fail uncovered_required=72 |
| `mutation_guard` | `pass` | `mutation/mutation_report.json` | not run; advisory until a human approves an IP-class kill-rate policy |
| `verification_hardening` | `pass` | `sim/scenario_e2e_summary.json + sim/monitor_evidence.json + mutation/survivor_classification.json + verify/formal_status.json` | not run; advisory until an IP emits verification-hardening artifacts |
| `waivers` | `fail` | `signoff/goal_ledger.json` | waivers explicit and reviewable |

## Issues

- `rtl_todo`: rtl_todo gate status is 'fail', expected pass; rtl_todo gate open_required_todos=337, expected 0; rtl_todo gate static_missing=276, expected 0; rtl_todo gate all_required_todos_pass must be true
- `rtl_provenance`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/rtl/rtl_authoring_provenance.json
- `lint`: dut_lint passed must be true; dut_lint warnings=23, expected 0
- `tb_python_compile`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/tb/cocotb/tb_py_compile.json
- `simulation`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/sim/sim_report.txt; missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/sim/results.xml
- `simulation_quality`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/sim/simulation_quality.json
- `scoreboard`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/sim/scoreboard_events.jsonl; scoreboard must contain at least one row
- `coverage`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/cov/coverage.json
- `truth_coverage`: truth_coverage status is 'fail', expected pass; uncovered_required=72, expected 0; uncovered_required list has 72 item(s)
- `waivers`: missing /Users/brian/Desktop/Project/brian_hw/common_ai_agent/mctp_assembler_v3/signoff/goal_ledger.json
