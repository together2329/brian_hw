---
name: default-ip-signoff
description: Execute the conversational default-agent IP creation and signoff loop. Use when the user asks to build, debug, simulate, or sign off an IP directly instead of using orchestrator mode.
---

# Atlas Default IP Signoff

Use this when the user wants direct IP work, especially phrases like "build this IP", "fix the sim", "orchestrator 말고 직접", or "signoff".

## Flow

Read `doc/wiki/default-agent-ip-flow.md`, then follow:

```text
Read -> Plan -> Edit -> Run -> Inspect -> Repair -> Record evidence -> Review
```

## Contract Sources

Prefer, in order:

1. Existing `req/*_requirements.md`.
2. Existing `yaml/*.ssot.yaml`.
3. User-provided protocol/register description.
4. A bounded agent-authored draft for demo work.

## Evidence

After source changes, rerun compile/sim/lint scripts and inspect fresh outputs before claiming PASS.

For the tracked APB UART demo:

```bash
cd apb_uart_txrx_demo && ./sim/run_sim.sh
cd apb_uart_txrx_demo && ./sim/run_random_regression.sh 7 12
```

Do not edit generated sim JSON, VCD manifests, or signoff bundles to greenwash a result.
