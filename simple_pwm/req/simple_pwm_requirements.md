# simple_pwm — Requirements Document

## Overview

| Item       | Value                            |
|------------|----------------------------------|
| IP Name    | simple_pwm                       |
| Type       | peripheral                       |
| Purpose    | Configurable PWM output generator |
| Target     | educational-tiny, generic technology, 100 MHz |
| Version    | 1.0                              |

## Parameters

| Name           | Default | Type | Description                  |
|----------------|---------|------|------------------------------|
| COUNTER_WIDTH  | 8       | int  | Counter width in bits (1–16) |

## Ports

| Port        | Direction | Width          | Description                        |
|-------------|-----------|----------------|------------------------------------|
| clk         | input     | 1              | System clock (rising-edge active)  |
| rst_n       | input     | 1              | Active-low asynchronous reset      |
| enable      | input     | 1              | PWM enable (1=running, 0=stopped) |
| duty_cycle  | input     | COUNTER_WIDTH  | Duty cycle threshold value         |
| period      | input     | COUNTER_WIDTH  | Counter period (rollover value)    |
| pwm_out     | output    | 1              | PWM output signal                  |

## Clock and Reset

- **Clock domain**: Single domain, `clk` at 100 MHz.
- **Reset**: `rst_n` is active-low, asynchronous assert, synchronous deassert.
- On reset: counter clears to 0, `pwm_out` clears to 0.

## Functional Behavior

### State Machine

```
        ┌─────────┐    enable=1     ┌──────────┐
        │  IDLE   │ ──────────────> │ RUNNING  │
        │counter=0│ <────────────── │counter++ │
        │pwm_out=0│    enable=0     │pwm_out=* │
        └─────────┘                 └──────────┘
```

### Transaction Descriptions

**FM1 — pwm_active_high**
- Precondition: `enable == 1` AND `counter < duty_cycle`
- Effect: `pwm_out = 1`, `counter` increments by 1 on next clock edge.
- Output rule: `pwm_out = 1`

**FM2 — pwm_active_low**
- Precondition: `enable == 1` AND `counter >= duty_cycle`
- Effect: `pwm_out = 0`, `counter` increments by 1 on next clock edge.
- Output rule: `pwm_out = 0`

**FM3 — pwm_idle**
- Precondition: `enable == 0`
- Effect: `counter = 0`, `pwm_out = 0`.
- Output rule: `pwm_out = 0`

### Period Rollover

When `counter` reaches `period` value, the counter resets to 0 on the next
clock edge. The period parameter defines the total number of counter steps in
one PWM cycle. The duty_cycle parameter defines how many of those steps have
`pwm_out = 1`.

### Duty Cycle Calculation

```
duty_ratio = duty_cycle / period
```

- `duty_cycle = 0` → `pwm_out` is always 0.
- `duty_cycle >= period` → `pwm_out` is always 1.
- `duty_cycle = period / 2` → 50% duty cycle (symmetric).

## Edge Cases

1. **period = 0**: Treated as period = 1 (minimum one count per cycle).
   Counter rolls over immediately; `pwm_out` reflects `duty_cycle >= 1`.
2. **duty_cycle > period**: `pwm_out` remains 1 continuously.
3. **Runtime changes**: `duty_cycle` and `period` inputs are sampled every
   clock cycle. Changes take effect on the next counter increment.
4. **Enable toggle**: Disabling (`enable = 0`) immediately forces `pwm_out = 0`
   and `counter = 0`. Re-enabling starts from counter = 0.

## Verification Requirements

### Scenario 1 — Basic PWM Generation
- Set `period = 10`, `duty_cycle = 3`, `enable = 1`.
- Verify: 3 clocks of `pwm_out = 1`, 7 clocks of `pwm_out = 0`, repeating.

### Scenario 2 — Duty Cycle Variation
- Run with `duty_cycle = 3`, then change to `duty_cycle = 7` mid-cycle.
- Verify: PWM output adjusts within one period.

### Scenario 3 — Period Rollover
- Set `period = 5`, `duty_cycle = 2`.
- Verify: counter counts 0,1,2,3,4 then resets to 0; `pwm_out` pattern is
  `1,1,0,0,0` repeating.

### Scenario 4 — Disable Behavior
- Run PWM, then set `enable = 0`.
- Verify: `pwm_out` goes to 0 immediately, counter resets to 0.
- Re-enable: `pwm_out` starts from counter = 0.

## Scope Exclusions

- No register map or bus interface (APB/AXI).
- No interrupts.
- No clock gating or power management.
- No multi-channel support.
- No glitch-free transition guarantees for runtime parameter changes.

## Quality Targets

- Compile: zero errors with iverilog.
- Lint: zero unwaived errors.
- Simulation: FL-vs-RTL equivalence 100% (0 mismatches).
- Coverage: all declared function and cycle bins hit.
