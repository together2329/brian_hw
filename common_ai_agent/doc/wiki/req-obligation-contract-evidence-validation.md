---
title: Req Obligation Contract Evidence Validation
type: concept
tags: [spine, requirement, obligation, contract, evidence, validation, assume-guarantee, traceability, direction]
updated: 2026-06-06
related: [contract-reflection-workflow, evidence-contract-obligation-traceability, locked-truth-concept, llm-contract-repair-loop, mctp-assembler-contract-breakdown, formal-verification-evidence, truth-coverage-gate, golden-todo-evidence]
---

# Req → Obligation → Contract → Evidence → Validation

This is the keystone definition of the spine the whole direction set builds on.
It normalizes a requirement into a *machine-checkable promise* before any RTL is
written, then accumulates proof that the promise was kept.

```text
Requirement   →   Obligation   →   Contract   →   Evidence   →   Validation
```

```text
documents / interview / spec
  → decompose into atomic, verifiable obligations
  → lock req/obligation/contract/evidence as the authority
  → project into SSOT YAML / interface / timing / SVA contracts
  → generate RTL, assertions, testbench, sim/formal results, lint
  → check evidence against contracts and close the trace
```

Core sentence:

```text
The locked req bundle is the source. The Design Spec/SSOT projection and
contracts are the machine-readable promises. The RTL is a verifiable artifact,
not the authority.
```

One-liner:

```text
req       = what a human wants
obligation= what the RTL must hold
contract  = that duty made machine-checkable
evidence  = the artifact proving the duty was kept
validation= the judgment that the whole req→evidence chain is unbroken
```

In the newer locked-truth flow, `req/requirements_index.json`,
`req/obligations.json`, `req/contract_refs.json`, `req/evidence_plan.json`, and
`req/approval_manifest.json` are the authority. `yaml/<ip>.ssot.yaml` is the
generator-ready Design Spec projection. If the YAML is missing fields, the
worker should first project from locked req facts before asking the user for new
truth.

This page is the plain definition. For the realized layers, read:

- [[contract-reflection-workflow]] — the six-layer realization that inserts
  **Stage Reflection** (FL/CL/RTL/TB/sim all reflect the same `contract_ref` ID).
- [[evidence-contract-obligation-traceability]] — the closure plumbing
  (goal_id / scenario_id / ssot_refs / rtl_observed / fl_expected / passed).
- [[locked-truth-concept]] — what it means to *lock* the requirement/obligation
  before generation may proceed.
- [[mctp-assembler-contract-breakdown]] — a full worked IP instance.
- [[formal-verification-evidence]] / [[llm-contract-repair-loop]] — the evidence
  type and the close-it-one-contract-at-a-time loop.

## req — requirement

Human-readable, often ambiguous, possibly redundant or incomplete. Not an
implementation target yet — it is the input to decomposition.

```text
REQ-FIFO-001: the FIFO shall be empty after reset.
```

Open questions that must be resolved before RTL: sync or async reset? empty
guaranteed how many cycles after reset? which signal set must stay stable? does
it apply when valid is low? what if ready never comes? Converting req straight to
RTL skips these — that is where interpretation fights start.

## obligation — the duty

An obligation is a verifiable duty extracted from a requirement. A good one is:

```text
atomic · verifiable · has an owner · has a clear condition ·
has a pass/fail rule · traces to its requirement
```

```yaml
obligations:
  - id: OBIL-FIFO-001-A
    requirement: REQ-FIFO-001
    statement: "empty_o shall be asserted while reset is active."
    condition: "rst_n == 0"
    observable: [empty_o]
  - id: OBIL-FIFO-001-B
    requirement: REQ-FIFO-001
    statement: "write/read pointers shall be zero after reset release."
    condition: "$rose(rst_n)"
    observable: [wr_ptr, rd_ptr]
```

An obligation is a **design duty**, not a test item: the design owes it even if no
test exists yet; the contract and evidence later close it.

## contract — the machine-checkable promise

A contract turns obligations into something RTL generation and verification can
consume. It comes in layers: interface, register, FSM, timing, reset, protocol,
error/exception, coverage, and **assume/guarantee**.

```yaml
contracts:
  - id: C-FIFO-RESET-001
    obligations: [OBIL-FIFO-001-A, OBIL-FIFO-001-B]
    type: reset_contract
    clock: clk
    reset: rst_n
    assumptions:                       # the environment must hold these
      - "rst_n remains low for at least 2 cycles"
    guarantees:                        # the RTL must hold these
      - "empty_o == 1 during reset"
      - "wr_ptr == 0 && rd_ptr == 0 after reset release"
    assertions: [SVA-FIFO-RESET-EMPTY, SVA-FIFO-RESET-PTR]
```

The assume/guarantee split is load-bearing: **RTL must satisfy the guarantees;
the testbench/formal environment must satisfy the assumptions.** An undischarged
assumption makes any proof meaningless (see [[formal-verification-evidence]]).
The contract — anchored in SSOT YAML — is also the traceability center: it is the
source of every assertion, testbench, and formal target.

## evidence — proof attached to a contract

Evidence is not "it works" — it is a concrete artifact tied to a specific
contract, recording how and with what result.

```text
bad:  "simulation passed"
good: names the contract, the method, the artifact, and the result
```

```yaml
evidence:
  - id: E-FIFO-RESET-SVA-001
    contract: C-FIFO-RESET-001
    type: assertion
    artifact: assertions/fifo_reset_sva.sv
    result: pass
  - id: E-FIFO-RESET-SIM-001
    contract: C-FIFO-RESET-001
    type: simulation
    artifact: reports/tb_fifo_reset.log
    result: pass
```

Evidence types include RTL, SVA, directed/random TB, sim logs, formal proofs,
lint/CDC/RDC, coverage, waveforms, and review sign-off. Each must hang off the
contract it closes (this is the freshness/closure discipline in
[[golden-todo-evidence]] and [[truth-coverage-gate]]).

## validation — closing the chain

Validation is not "did sim pass". It judges whether the whole chain is sound:

```text
is every requirement decomposed into obligations?
is every obligation linked to a contract?
does every contract have evidence?
is the evidence strong enough?
did failures route back through the repair loop?
are there coverage gaps?
have RTL and SSOT drifted?
```

```yaml
validation:
  - id: V-FIFO-RESET-001
    requirement: REQ-FIFO-001
    obligations: [OBIL-FIFO-001-A, OBIL-FIFO-001-B]
    contracts: [C-FIFO-RESET-001]
    evidence: [E-FIFO-RESET-SVA-001, E-FIFO-RESET-SIM-001]
    status: closed
```

```text
verification = the act of checking a contract.
validation   = judging that the entire req→evidence chain is sound and unbroken.
```

## The Accident Zone — req → obligation

This is where most breakage originates. A sloppy obligation makes everything
downstream wrong.

```text
bad obligation:  "it must respond quickly."
good obligation: "ack_o shall assert within 3 cycles of an accepted request
                  (req_i && ready_o)."
```

And every contract needs explicit assumptions (reset min-width, input stability
until ready, whether ready is guaranteed to arrive). Missing environment
conditions make verdicts meaningless.

## Why This Spine

It keeps RTL generation and verification from drifting apart. Instead of
`spec → RTL → TB → bug → spec-interpretation fight`, it runs
`spec → obligation → contract → RTL/SVA/TB together → evidence → validation
closure`. The contract is the shared reference point, so interpretation fights
shrink — and this matters most for AI-generated RTL: do not let an LLM emit RTL
directly; build the SSOT/contract first, then generate RTL, SVA, TB, and docs
against it (the basis of [[llm-contract-repair-loop]]).

```text
Requirement: why it is needed
Obligation : what must be held
Contract   : how to define it mechanically
Evidence   : what proves it
Validation : whether we may call it closed
```

한 줄 요약: req는 사람이 원하는 것, obil은 RTL이 져야 할 의무, contract는 그
의무를 기계가 검증 가능하게 만든 약속, evidence는 그 약속을 지켰다는 산출물,
validation은 req부터 evidence까지 trace chain이 끊기지 않았는지의 판정이다.
