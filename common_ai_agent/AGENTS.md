# common_ai_agent ROCEV Work Guide

This file is intentionally small. The parent `../AGENTS.md` remains the common
platform rule. This repo-local file adds the hardware workflow convention used
by the Cursor/Codex seminar packs.

## Hardware Completion Shape

For RTL, TB, lint, simulation, coverage, formal, or signoff work, report closure
with this shape:

```text
Requirement:
Obligation:
Contract:
Evidence:
Validation:
```

Meanings:

- Requirement: what the block is expected to do.
- Obligation: the smaller behavior the design must satisfy.
- Contract: how that behavior can be judged mechanically.
- Evidence: the actual artifact on disk.
- Validation: the decision made from that evidence.

Do not collapse these into "tests passed." A compile PASS, lint PASS, sim PASS,
scoreboard PASS, coverage hit, VCD, and formal proof are different evidence
types and close different obligations.

## Evidence Examples

Use paths like these when they exist:

- Requirement and obligation: `<ip>/req/locked_truth.md`, `<ip>/req/obligations.json`
- Contract: `<ip>/req/evidence_plan.json`, `<ip>/verify/equivalence_goals.json`
- RTL evidence: `<ip>/rtl/rtl_compile.json`
- Lint evidence: `<ip>/lint/dut_lint.json`
- Simulation evidence: `<ip>/sim/results.xml`, `<ip>/sim/sim_report.txt`
- Scoreboard evidence: `<ip>/sim/scoreboard_events.jsonl`
- Coverage evidence: `<ip>/cov/coverage.json`
- Waveform evidence: `<ip>/sim/*.vcd` or `<ip>/sim/*.fst`
- Formal evidence: `<ip>/verify/*.sva`, `<ip>/verify/formal_status.json`
- Signoff evidence: `<ip>/signoff/truth_coverage.json`

If evidence is missing or stale, say so directly.

## IP Development Memory

For any IP creation, debug, verification, or signoff task, keep durable memory
inside the IP folder. Do not rely on the chat transcript or Codex global
memories as the only record.

At the start of IP work, run:

```bash
python3 scripts/ip_dev_memory.py init <ip>
```

This must ensure `<ip>/wiki/` exists and initialize `<ip>/.git/` when that IP
folder does not already have a git repository.

Before editing, read `<ip>/wiki/llm_memory.md` and recent `git -C <ip> log`.
After each meaningful stage boundary, record what changed and what evidence was
inspected:

```bash
python3 scripts/ip_dev_memory.py log <ip> --stage <stage> --title "<event>" --body "<summary>"
```

After behavior, test, or evidence changes, create an IP-local snapshot:

```bash
python3 scripts/ip_dev_memory.py snapshot <ip> --message "<stage>: <summary>"
```

Before claiming completion, run:

```bash
python3 scripts/ip_dev_memory.py check <ip> --require-git
```

If this check fails, report the memory/git gap instead of claiming closure.
