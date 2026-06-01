# IP Signoff - mctp_assembler_scratch

- Status: `fail`
- Generated: `2026-05-31T23:50:09Z`
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
| `simulation_quality` | `fail` | `sim/simulation_quality.json` | status=fail issues=3 |
| `scoreboard` | `pass` | `sim/scoreboard_events.jsonl` | rows=86 goals_with_rows=86 |
| `coverage` | `pass` | `cov/coverage.json` | status=pass |
| `mutation_guard` | `pass` | `mutation/mutation_report.json` | status=pass kill_rate=0.2812 |
| `waivers` | `pass` | `signoff/goal_ledger.json` | waivers explicit and reviewable |

## Issues

- `simulation_quality`: simulation_quality status is 'fail', expected pass; SC_015_EQ_SCENARIO_SC_MAX_TU_4096_129_BEATS: payload evidence 16 below expected 4096; SC_017_EQ_SCENARIO_SC_INTERLEAVE_TWO_Q_COMPLETE: valid/interleave scenario asserted drop or error; SC_021_EQ_SCENARIO_SC_READBACK_AFTER_MULTI_ASSEMBLE: payload evidence 0 below expected 76
