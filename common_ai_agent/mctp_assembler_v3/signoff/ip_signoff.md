# IP Signoff - mctp_assembler_v3

- Status: `fail`
- Generated: `2026-06-05T13:42:58Z`
- Contract: `IP_SIGNOFF.md`

| Gate | Status | Artifact | Summary |
| --- | --- | --- | --- |
| `ssot` | `pass` | `yaml/mctp_assembler_v3.ssot.yaml` | SSOT exists and parses |
| `ip_contract` | `pass` | `verify/ip_contract.json` | capabilities=12 required_evidence=14 |
| `fl_model` | `pass` | `model/fl_model_check.json` | FL artifact check passed=true |
| `cl_model` | `pass` | `model/cl_model_check.json` | CL self-check passed=true |
| `equivalence_goals` | `pass` | `verify/equivalence_goals.json` | goals=102 blocked=0 |
| `rtl_todo` | `pass` | `rtl/rtl_todo_plan.json` | RTL todo/static audit gate |
| `rtl_provenance` | `pass` | `rtl/rtl_authoring_provenance.json` | RTL provenance matches current todo plan |
| `rtl_compile` | `pass` | `rtl/rtl_compile.json` | DUT-only RTL compile is clean |
| `lint` | `pass` | `lint/dut_lint.json` | DUT-only lint is clean |
| `tb_python_compile` | `pass` | `tb/cocotb/tb_py_compile.json` | TB Python compiled before simulation |
| `simulation` | `pass` | `sim/results.xml` | tests=10 failures=0 errors=0 |
| `simulation_quality` | `pass` | `sim/simulation_quality.json` | status=pass issues=0 |
| `scoreboard` | `pass` | `sim/scoreboard_events.jsonl` | rows=106 goals_with_rows=102 |
| `coverage` | `pass` | `cov/coverage.json` | status=pass |
| `truth_coverage` | `pass` | `signoff/truth_coverage.json` | status=pass uncovered_required=0 |
| `mutation_guard` | `pass` | `mutation/mutation_report.json` | status=pass kill_rate=0.5833 |
| `verification_hardening` | `pass` | `sim/scenario_e2e_summary.json + sim/monitor_evidence.json + mutation/survivor_classification.json + verify/formal_status.json` | directed scenarios, protocol monitors, survivor classification, and optional formal artifacts present |
| `contract_content_coverage` | `pass` | `signoff/evidence_contract_coverage.json` | content_obligations=1 contract_check=pass |
| `contract_sim_freshness` | `fail` | `sim/evidence_freshness.json` | PASS = correctness AND freshness (sim evidence current vs SSOT/FL/CL/TB/RTL inputs) |
| `waivers` | `pass` | `signoff/goal_ledger.json` | waivers explicit and reviewable |

## Issues

- `contract_sim_freshness`: sim evidence metadata fingerprint mismatch: verify/contract_reflection.json; sim evidence metadata fingerprint mismatch: verify/evidence_contract.json
