# Worked Example - `pwm_gen_cx1` ROCEV

This example is built from real repository material:

- `pwm_gen_cx1/req/pwm_gen_cx1_requirements.md`
- `pwm_gen_cx1/req/locked_truth.md`
- `pwm_gen_cx1/req/obligations.json`
- `pwm_gen_cx1/req/evidence_plan.json`
- `pwm_gen_cx1/verify/equivalence_goals.json`
- `pwm_gen_cx1/rtl/rtl_compile.json`
- `pwm_gen_cx1/lint/dut_lint.json`
- `pwm_gen_cx1/sim/results.xml`
- `pwm_gen_cx1/sim/scoreboard_events.jsonl`
- `pwm_gen_cx1/cov/coverage.json`
- `pwm_gen_cx1/sim/pwm_gen_cx1.vcd`

Reference concepts:

- `doc/wiki/req-obligation-contract-evidence-validation.md`
- `doc/wiki/evidence-contract-obligation-traceability.md`
- `doc/wiki/formal-verification-evidence.md`
- `.cursor/workflow/COMMON_ENGINE_FLOW.md`

## Slide-Sized Version

Use this block in the "Cursor's four ingredients" slide.

```text
Example: pwm_gen_cx1

Requirement
  8-bit PWM generator.
  duty_reg controls duty cycle.
  pwm_out = 1 when counter_q < duty_reg.
  reset clears counter_q and duty_reg.

Obligations
  O1 counter_q increments and wraps 0..255.
  O2 duty_reg latches duty_in when wr_en=1.
  O3 pwm_out follows counter_q < duty_reg.
  O4 reset clears counter_q/duty_reg and pwm_out=0.
  O5 lint: no latch / no single-driver violation.

Workflow
  Rules: report completion in ROCEV form.
  Skills: run compile -> lint -> sim -> scoreboard -> coverage.
  Agents: requirement / rtl / verification / validator split the work.
  Hooks: block shallow "tests passed" claims without evidence context.
```

The teaching point:

```text
Simulation can pass while validation is still not closed.
For this IP, sim/results.xml exists, but cov/coverage.json is blocked.
That is exactly why Evidence and Validation are separate.
```

## Requirement

From `pwm_gen_cx1/req/pwm_gen_cx1_requirements.md`:

```text
Purpose:
  8-bit PWM generator.
  Counter counts 0-255 per period.
  pwm_out=1 when counter < DUTY register.

Features:
  PWM generation: pwm_out duty cycle equals duty_reg/256.
  Duty cycle register write: duty_reg updated; next PWM period reflects new duty.

Reset:
  rst_n low clears counter_q and duty_reg to 0; pwm_out=0.
```

This is reasonably concrete, but still too broad to validate as one sentence.
ROCEV makes it smaller.

## Obligation

From `pwm_gen_cx1/req/locked_truth.md` and `req/obligations.json`:

| Obligation | What it means | Closure stage |
|---|---|---|
| `OBL_PWM_COUNTER_001` | `counter_q` increments by 1 each rising clock and wraps `0..255`. | sim |
| `OBL_PWM_DUTY_001` | `duty_reg` latches `duty_in` when `wr_en=1`. | sim |
| `OBL_PWM_OUT_001` | `pwm_out` follows `counter_q < duty_reg`. | sim |
| `OBL_PWM_RESET_001` | reset clears state and output. | sim |
| `OBL_PWM_LINT_001` | no latch / no single-driver violation. | lint |

This is the important step for the seminar:

```text
Requirement is a human-sized statement.
Obligation is the checkable unit.
```

## Contract

Contracts come from locked truth, evidence plan, and equivalence goals.

| Contract | Artifact | Meaning |
|---|---|---|
| `BC_PWM_COUNT` | `req/evidence_plan.json` | `pwm_out` matches FL expected each cycle. |
| `BC_PWM_DUTY` | `req/evidence_plan.json` | `duty_reg` matches `duty_in` one cycle after `wr_en`. |
| `BC_PWM_RESET` | `req/evidence_plan.json` | reset observes `counter_q=0`, `duty_reg=0`. |
| `BC_PWM_LINT` | `req/evidence_plan.json` | no latch / no single-driver lint findings. |
| `EQ_TRANSACTION_FM_WRITE` | `verify/equivalence_goals.json` | duty write transaction matches `FunctionalModel.apply`. |
| `EQ_TRANSACTION_FM_TICK` | `verify/equivalence_goals.json` | counter tick transaction matches `FunctionalModel.apply`. |

In plain words:

```text
The expected behavior is not guessed by the final answer.
It is encoded in the FL/checker/scoreboard/equivalence goal contracts.
```

## Evidence

Evidence is stage-specific.

| Stage | Evidence path | What it can prove |
|---|---|---|
| req | `req/locked_truth.md`, `req/obligations.json` | Requirements and obligations are explicit. |
| rtl | `rtl/rtl_compile.json` | DUT compiles. |
| lint | `lint/dut_lint.json` | DUT lint is clean. |
| tb | `tb/cocotb/test_pwm_gen_cx1.py`, `tb/cocotb/scoreboard.py` | TB and scoreboard exist. |
| sim | `sim/results.xml` | Simulation test ran. |
| scoreboard | `sim/scoreboard_events.jsonl` | RTL observed values were compared with expected values. |
| coverage | `cov/coverage.json` | Coverage closure status. |
| waveform | `sim/pwm_gen_cx1.vcd` | Cycle-level debug trace exists. |

Concrete observations from current local artifacts:

```text
rtl/rtl_compile.json
  passed: true
  errors: 0

lint/dut_lint.json
  passed: true
  errors: 0
  warnings: 0

sim/results.xml
  contains testcase fl_rtl_equivalence_goals

sim/scoreboard_events.jsonl
  contains FL expected vs RTL observed rows
  references FunctionalModel.apply and coverage_refs

cov/coverage.json
  status: blocked
  function_coverage target not met
  cycle_coverage target not met
```

## Validation

This is the part that makes the example useful.

Bad final report:

```text
PWM tests passed.
```

Better final report:

```text
Requirement:
  pwm_out follows the 8-bit counter and duty register behavior.

Obligations:
  OBL_PWM_COUNTER_001, OBL_PWM_DUTY_001, OBL_PWM_OUT_001,
  OBL_PWM_RESET_001, OBL_PWM_LINT_001.

Contract:
  FunctionalModel.apply + equivalence goals + lint contract + coverage plan.

Evidence:
  rtl_compile.json passed.
  dut_lint.json passed.
  results.xml has a simulation testcase.
  scoreboard_events.jsonl has FL-vs-RTL rows.
  pwm_gen_cx1.vcd exists.
  coverage.json is currently blocked.

Validation:
  Not fully closed.
  Compile/lint/sim evidence exists, but coverage closure is blocked.
```

Teaching sentence:

```text
Evidence can be partly good while validation is still open.
That is why "tests passed" is not enough.
```

## Cursor Four Ingredients Applied

| Cursor surface | Example in this IP |
|---|---|
| Rules | Completion must be reported as Requirement / Obligation / Contract / Evidence / Validation. |
| Skills | `ip-rocev-mini-run` runs compile, lint, sim, scoreboard, coverage checks in order. |
| Agents | requirement agent owns obligation split; rtl agent owns compile/lint; verification agent owns sim/scoreboard/coverage; validator agent owns closure wording. |
| Hooks | warn on shallow `grep PASS results.xml`; remind if evidence/validation todo is still open. |

## Commands To Show In A Demo

These are read/check commands, useful for a seminar without changing artifacts:

```bash
IP=pwm_gen_cx1

sed -n '1,120p' "$IP/req/locked_truth.md"
python3 -m json.tool "$IP/req/obligations.json" | sed -n '1,120p'
python3 -m json.tool "$IP/req/evidence_plan.json" | sed -n '1,160p'
python3 -m json.tool "$IP/rtl/rtl_compile.json" | rg 'passed|errors|returncode'
python3 -m json.tool "$IP/lint/dut_lint.json" | rg 'passed|errors|warnings'
sed -n '1,40p' "$IP/sim/results.xml"
sed -n '1,3p' "$IP/sim/scoreboard_events.jsonl"
python3 -m json.tool "$IP/cov/coverage.json" | rg 'status|pct|meets_target|missing_bins' -n
ls -lh "$IP/sim/"*.vcd
```

## Why This Example Works For The Seminar

It is not too abstract:

```text
PWM counter / duty / output / reset are easy to understand.
```

It is not too trivial:

```text
The current artifacts show a realistic state:
compile and lint can pass,
simulation can run,
but validation can still remain open because coverage is blocked.
```

It maps cleanly to the workflow:

```text
req -> obligations -> evidence_plan/equivalence_goals
-> rtl_compile/dut_lint
-> results.xml/scoreboard_events.jsonl
-> coverage.json
-> validation decision
```

