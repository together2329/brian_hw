---
name: ip-rocev-mini-run
description: Walk through any hardware IP using ROCEV. Use for seminar demos or short explanations of Requirement, Obligation, Contract, Evidence, and Validation.
---

# IP ROCEV Mini Run

Use this for any IP directory. Replace `<ip>`, `<case>`, and `<obligation>` with
the current block and behavior.

For a fully filled local example, read:

```text
.cursor_new/examples/pwm-gen-cx1-rocev-worked-example.md
```

## Step 1 - Requirement

```text
<ip> must handle <case> correctly.
```

Examples:

```text
fifo_sync: preserves push/pop order
timer: interrupt pulse is exactly one cycle
register_block: W1C bits clear only on write-one
packet_parser: invalid header is rejected
bridge: backpressure does not drop a transaction
```

## Step 2 - Obligation

```text
O1: when <condition> occurs, DUT must produce <expected behavior>.
O2: no unintended side effect occurs.
```

## Step 3 - Contract

Use at least one dynamic contract and, if available, one static/formal contract:

```text
Dynamic:
  expected model/checker defines <expected behavior>
  scoreboard compares RTL observed vs expected
  coverage includes <case>

Static/formal:
  SVA states that <bad condition> cannot produce <forbidden output/state>
```

## Step 4 - Evidence

Check the evidence bundle:

```bash
IP=<ip>
ls -lh "$IP/rtl/rtl_compile.json"
ls -lh "$IP/lint/dut_lint.json"
ls -lh "$IP/sim/results.xml"
ls -lh "$IP/sim/scoreboard_events.jsonl"
ls -lh "$IP/cov/coverage.json"
ls -lh "$IP/sim/"*.vcd
ls -lh "$IP/verify/formal_status.json"
```

Optional targeted search:

```bash
IP=<ip>
rg -n "<case>|<obligation>|scoreboard|coverage|formal|VCD" "$IP" doc/wiki
```

## Step 5 - Validation

Say exactly what is closed:

```text
Closed:
  <obligation> dynamic simulation evidence

Evidence:
  results.xml passed
  scoreboard row exists
  coverage bin hit
  VCD exists for debug

Not claimed:
  full formal proof unless formal_status.json proves the matching property
```

## Filled-in quick examples

```text
FIFO:
  Requirement: FIFO preserves order.
  Obligation: first pushed item is first popped item.
  Contract: reference queue model + scoreboard.
  Evidence: results.xml, scoreboard_events.jsonl, coverage for push/pop patterns.
  Validation: closed for ordering if all evidence passes.
```

```text
Register block:
  Requirement: W1C status bits clear only on write-one.
  Obligation: write-zero leaves status bit unchanged.
  Contract: register model/checker + readback scoreboard.
  Evidence: APB/AHB sim result, scoreboard row, W1C coverage bin.
  Validation: closed for write-zero behavior.
```
