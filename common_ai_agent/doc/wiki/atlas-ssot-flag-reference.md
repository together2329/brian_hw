# ATLAS — SSOT Flag Reference

Every opt-in flag and per-IP semantic switch in ATLAS, with the IPs that
use it and the behavior change it triggers. Maintained alongside the new
IP recipe (`atlas-new-ip-recipe.md`).

---

## `cycle_model.cosim`

**Type:** `bool`, default `false`
**Effect:** enables cycle-accurate CL ↔ RTL co-simulation in cocotb test

When `true`:
- `tb_manifest.cl_cosim` = `true`
- Cocotb test instantiates `FunctionalModel` and calls `cl.step(inputs)`
  each cycle in lock-step with the DUT.
- Each goal's cl outputs are compared with `rtl_observed` keys; if all
  overlapping integer keys match, `cl_passed=True` is passed to the
  scoreboard, which records the goal PASS regardless of single-shot
  `FL.apply()` verdict.

When `false`:
- Scoreboard uses only `FL.apply()` (single-shot per goal). Multi-cycle
  state evolution is not tracked.

**Use when:**
- IP has multi-cycle state (counters, FSMs, accumulators).
- You want cycle-by-cycle FL/RTL agreement, not just transaction-level.

**Example IPs:** `arbiter_rr`, `apb_gpio_demo`, `atcuart_mini`,
`apb_compare`, `apb_pulse_counter`.

```yaml
cycle_model:
  cosim: true
```

---

## `cycle_model.state_accumulating`

**Type:** `bool`, default `false`
**Effect:** disables `per_goal_reset` so DUT/CL state persists across goals

When `true`:
- `tb_manifest.per_goal_reset` = `false`
- Cocotb test does NOT reset between consecutive scenario/transaction
  goals. State (e.g. round-robin `last_winner`) accumulates as in
  multi-cycle tests.
- Non-scenario property goals (EQ_PROTOCOL_*, EQ_REGISTER_*, EQ_TIMING_*,
  EQ_ERROR_*, EQ_MODULE_*, EQ_COVERAGE_*) still get reset before each
  invocation, because they are standalone single-cycle checks.

When `false`:
- Cocotb resets DUT between every goal (default safe behavior).

**Use when:**
- IP's RTL behaviour depends on state accumulated across consecutive
  scenarios (e.g. round-robin rotation, persistent counter).

**Risk:**
- Without `state_accumulating: true`, scenarios with intentional state
  preservation will fail because the reset wipes the setup.
- With it, scenarios that need a clean start must explicitly include
  CSR clear / `assign` zeroing in their `stimulus_machine_spec.timeline`.

**Example IPs:** `arbiter_rr`.

```yaml
cycle_model:
  cosim: true
  state_accumulating: true
```

---

## `cycle_model.use_per_cycle_expected`

**Type:** `bool`, default `false`
**Effect:** auto-tags every equivalence goal with a `sample_cycle` from
`cycle_model.pipeline`, so the scoreboard's cycle_view path fires.

When `true`:
- `emit_equivalence_goals.py` auto-tags goals whose `transaction.kind`
  matches a `function_model.transactions[*].sample_stage`, using that
  stage's `cycle` as `sample_cycle`.
- Goals without an explicit `sample_stage` and *with* a
  `stimulus_machine_spec` get the default
  `max(integer pipeline cycles)`.
- Goals without `sample_stage` *and* without `stimulus_machine_spec` are
  NOT auto-tagged — preventing false fails from idle-vs-expected mismatch.

When `false`:
- Scoreboard relies on `FL.apply()` and (optionally) CL co-sim only;
  pipeline-stage expected values are not consulted.

**Use when:**
- IP has well-defined `cycle_model.pipeline` stages with `output_rules`
  expressions that ATLAS should compare at each stage's cycle.

**Example IPs:** `uart_lite` (TX FSM cycle-by-cycle output_rules).

```yaml
cycle_model:
  use_per_cycle_expected: true
  pipeline:
    - stage: TX_IDLE
      cycle: 0
      output_rules:
        - { name: tx_serial, port: tx, expr: 1, width: 1 }
```

---

## `function_model.state_variables[*].drives_output`

**Type:** `string` (RTL port name)
**Effect:** scoreboard treats `state_var_name` and `drives_output` port
as aliases — comparison passes if either form matches `rtl_observed`.

When set:
- `EquivalenceScoreboard._mirror_view_via_input_map()` adds a bidirectional
  alias between the state variable and the named RTL port in the
  comparison view.
- Resolves cases where SSOT state name (e.g. `count_q`) differs from RTL
  output name (e.g. `count`).

**Use when:**
- Internal state variable has a suffixed name (e.g. `_q` for registered
  values) but the public RTL port drops the suffix.

**Example IPs:** `timer` (`count_q drives_output: count`).

```yaml
state_variables:
  - { name: count_q,   drives_output: count }
  - { name: running_q, drives_output: running }
  - { name: done_q,    drives_output: done }
```

---

## `function_model.transactions[*].sample_stage`

**Type:** `string` (pipeline stage name)
**Effect:** binds a transaction's `sample_cycle` to a specific
`cycle_model.pipeline` stage, so the cycle_view comparison samples at
the right point in the pipeline.

Requires `cycle_model.use_per_cycle_expected: true`.

When set:
- Transaction goals (`EQ_TRANSACTION_*`) get `sample_cycle` =
  `cycle_model.pipeline[<sample_stage>].cycle` instead of the default
  max cycle.

**Use when:**
- Different transactions sample at different pipeline stages (e.g.
  TX_START vs TX_DATA for UART).

**Example IPs:** `uart_lite` (`FM_TX_BYTE.sample_stage: TX_START`).

```yaml
transactions:
  - id: FM_TX_BYTE
    sample_stage: TX_START
```

---

## `function_model.state_variables[*].source`

**Type:** `string` (e.g. `registers.<REG>.<field>`)
**Effect:** declares which register/field the state variable mirrors;
used by `csr_write()` to update the state variable when the register is
written.

When set:
- `FunctionalModel.csr_write(offset, data)` updates the state variable
  if the offset matches the named register's offset and the field's
  bit-slice exists.

**Use when:**
- A state variable backs a register field (almost every CSR-backed
  state variable).

```yaml
state_variables:
  - { name: gpio_data, source: registers.DATA.data, reset: 0 }
  - { name: arb_enabled, source: registers.CTRL.enable, reset: 1 }
  - { name: req_mask, source: registers.REQ_MASK.mask, reset: 15 }
```

---

## `function_model.transactions[*].preconditions`

**Type:** list of strings (Python-evaluable boolean expressions)
**Effect:** determines which transaction `FL.step(inputs)` selects each
cycle.

The transaction whose preconditions ALL evaluate `True` (against env =
state + registers + inputs) is selected.

**Tips:**
- Order matters: first matching transaction wins. List specific
  conditions first, idle/default last.
- Support uppercase `OR` / `AND` / `NOT` (normalized to Python ops).
- Trailing natural-language `(...)` parenthetical comments are stripped.
- Unparseable expressions default to `True` (treated as "don't block").

```yaml
transactions:
  - id: FM_CLEAR    # specific
    preconditions: ["psel == 1", "penable == 1", "pwrite == 1", "paddr == 4"]
  - id: FM_PULSE    # next-priority
    preconditions: ["pulse_in == 1", "(psel == 0 or penable == 0 or pwrite == 0 or paddr != 4)"]
  - id: FM_IDLE     # catch-all
    preconditions: []   # always matches
```

---

## `scenarios[*].stimulus_machine_spec`

**Type:** `{ assign | csr_writes | timeline }`
**Effect:** machine-readable stimulus to drive the DUT — bypasses the
heuristic stimulus generator.

### `assign: { field: value, ... }`
One-shot drive of named fields (uses `input_map` field→port mapping).

```yaml
stimulus_machine_spec:
  assign: { requests: 4 }            # → req_i = 4 for one cycle
```

### `csr_writes: [{ offset, data }, ...]`
Sequence of APB writes.

```yaml
stimulus_machine_spec:
  csr_writes:
    - { offset: 0x0, data: 0x55 }
    - { offset: 0x4, data: 0x1 }
```

### `timeline: [{ csr_write | assign | wait_cycles | wait_until }, ...]`
Ordered sequence of step types:

```yaml
stimulus_machine_spec:
  timeline:
    - { csr_write: { offset: 0x0, data: 0x55 } }
    - { assign: { pulse_in: 1 } }
    - { wait_cycles: 4 }
    - { wait_until: { signal: tx_active, equals: 1, timeout: 32 } }
```

**Use when:**
- The scenario needs specific input values (heuristic stimulus would
  guess wrong, e.g. CSR setup sequence).
- The scenario depends on a particular timing sequence.

---

## `rtl_contract.json` — `input_map`

**Type:** dict of field → port mappings
**Effect:** declares which SSOT field names map to which RTL port names.

```json
"input_map": {
  "psel":   "PSEL",
  "penable": "PENABLE",
  "pwrite":  "PWRITE",
  "paddr":   "PADDR",
  "pwdata":  "PWDATA",
  "pulse_in": "pulse_in"
}
```

- Cocotb test uses this to drive DUT pins from `stimulus` dict.
- CL co-sim mirrors both field and port names into the env (so an
  expression referencing `psel` works regardless of how cocotb keyed the
  stimulus).

---

## `validate_ssot.py` — schema gate

Run with `python3 workflow/ssot-gen/scripts/validate_ssot.py <ip> --root .`

### Blockers (must fix before emit)

| Rule | Why |
|---|---|
| `function_model.transactions.output_rules_required` | FL.apply cannot compute expected without output_rules. |
| `transactions.output_rules.expr_required` | Each output_rule needs an evaluable `expr`. |
| `transactions.output_rules.name_required` | Each output_rule needs a `name`. |
| `state_variables.reset_numeric` | English literal reset (`"all-ones"`) breaks bitwise eval. |
| `cycle_model.required` | Must declare cycle_model section. |
| `cycle_model.pipeline.output_rules_required_when_opt_in` | If `use_per_cycle_expected: true`, every stage needs output_rules. |
| `registers.register_list.offset_required` | Without offsets, csr_writes cannot resolve addresses. |

### Warnings (clear over time)

- `function_model.transactions.output_rules.port_recommended`
- `scenarios.stimulus_machine_spec_missing` / `shape`
- `cycle_model.pipeline_required`
- `io_list.required`

---

## Decision tree for a new IP

```
Is your IP stateful (registers / FSM)?
├─ No  → simple combinational IP, just FL.apply works. Skip cosim.
└─ Yes
   │
   Does the test need state preserved across scenarios?
   ├─ No  → cycle_model.cosim: true (default per_goal_reset)
   └─ Yes → cycle_model.cosim: true
            cycle_model.state_accumulating: true

   Does each transaction sample at a different pipeline cycle?
   ├─ No  → skip use_per_cycle_expected
   └─ Yes → cycle_model.use_per_cycle_expected: true
            function_model.transactions[*].sample_stage: <stage>
            cycle_model.pipeline[*].output_rules: [...]
```

---

## Related

- [[atlas-new-ip-recipe]] — full new-IP workflow with 4 demo patterns
- [[silent-pass-exposure-tb-stimulus-gap-20260520]] — context behind the
  HARD scoreboard policy and silent-green defenses
- [[systematic-quality-gates-20260521]] — validator + manifest hygiene
  + stale sim detection gates
