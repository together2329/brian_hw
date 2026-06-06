---
title: Locked Truth Concept
type: proposal
tags: [locked-truth, requirements, obligation, contract, evidence, validation, versioning, mctp, direction]
updated: 2026-06-06
related: [locked-truth-design-spec-workflow, llm-contract-repair-loop, mctp-assembler-contract-breakdown, contract-reflection-workflow, evidence-contract-obligation-traceability, truth-coverage-gate, human-review-and-escalation, workflow-ownership-and-boundaries]
---

# Locked Truth Concept

This page defines what "locked truth" *means* and how it differs from req,
contract, and evidence. It is the definitional companion to
[[locked-truth-design-spec-workflow]] (the file authority + workflow) and
[[llm-contract-repair-loop]] (the consumer that holds locked truth fixed while
patching RTL/SVA/TB).

## One-Line Definition

```text
Locked truth is the fixed reference fact that RTL/SVA/TB generators and reviewers
are no longer allowed to reinterpret.
```

It does **not** claim "the circuit is truly correct". It says: *in this design,
we lock this as the answer-standard.* Correctness is then proven against it by
evidence — not assumed by it.

## Position In The Flow

The existing spine was:

```text
req -> obligation -> contract -> evidence -> validation
```

Locked truth inserts the disambiguation/approval boundary:

```text
raw req
  -> interpreted / decomposed obligation candidate
  -> locked truth
  -> contract
  -> evidence
  -> validation
```

Practically, the human review gate sits at the obligation step:

```text
req
  -> obligation        <- human reviews and locks here
  -> contract          <- executable expression of the locked truth
  -> evidence
  -> validation
```

So locked truth is best seen **not as a separate stage but as a state on an
obligation/contract**:

```text
draft obligation
reviewed obligation
locked obligation
contract generated from locked obligation
```

## Why It Is Needed

The most dangerous thing a generator (LLM or otherwise) does is silently
reinterpret a requirement mid-stream. Take one MCTP assembler requirement:

```text
If a continuation packet's sequence is wrong, the message assembly must abort.
```

A generator must **not** be free to pick any of these:

```text
- drop only the packet, keep the existing assembly
- still commit the message if EOM later arrives
- only raise a status bit and keep appending payload
```

Locking the truth removes that freedom:

```text
Locked Truth:
  out-of-sequence continuation packet is fatal to the current assembly.
  the current partial message shall be dropped.
  no completed message shall be emitted from that dropped context.
```

Now RTL, SVA, and TB must all follow the same fact. This is the upstream half of
the anti-reinterpretation defense in [[llm-contract-repair-loop]].

## Locked Truth Is Not Evidence

This distinction is load-bearing:

```text
locked truth : the answer-standard we chose to hold fixed
evidence     : proof that the RTL satisfied that standard
validation   : decision that the trace from locked truth to evidence is closed
```

Example:

```text
Locked Truth:
  during backpressure (msg_out_valid=1, msg_out_ready=0),
  msg_out_* fields shall remain stable.
Evidence:
  p_msg_out_stable_when_backpressured proven (formal)
  random backpressure simulation passed
Validation:
  that locked truth is closed by formal + sim evidence
```

A locked truth with no kill-capable evidence is closed in name only — see the
evidence-quality warning in [[llm-contract-repair-loop]] (`## Risks`) and
[[truth-coverage-gate]].

## Granularity — Good Vs Bad

Too coarse to lock (cannot map to RTL/SVA/TB directly):

```text
LT-MCTP-ASM-001:
  MCTP Assembler shall assemble messages correctly.
```

Right-sized — each truth maps to one contract and one assertion family:

```text
LT-ASM-SEQ-001: an accepted continuation packet for an active context shall
                match the assembler's expected sequence value.
LT-ASM-SEQ-002: after a valid continuation packet, expected sequence updates modulo 4.
LT-ASM-SEQ-003: an accepted out-of-sequence continuation packet drops the current context.
LT-ASM-SEQ-004: a dropped context shall not produce a completed message output.
```

Each then traces cleanly:

```text
LT-ASM-SEQ-001
  -> OBIL-ASM-SEQ-MATCH
  -> C-ASM-SEQ-MATCH
  -> SVA p_continuation_seq_must_match
  -> formal proof / directed sim
  -> validation closed
```

## YAML Shape (proposed)

```yaml
locked_truth:
  - id: LT-ASM-SEQ-001
    block: mctp_rx_assembler
    status: locked
    version: 1
    statement: >
      For an active assembly context, an accepted continuation packet shall
      match the expected packet sequence value.
    scope: [rx_message_assembly, continuation_packet]
    assumptions:
      - "pkt_accept means pkt_valid && pkt_ready"
      - "context_active indicates an in-progress multi-packet message"
    derived_obligations: [OBIL-ASM-SEQ-001, OBIL-ASM-SEQ-002]
    contracts: [C-ASM-SEQ-MATCH]
    owner: architecture

contracts:
  - id: C-ASM-SEQ-MATCH
    locked_truth: [LT-ASM-SEQ-001]
    type: protocol_contract
    assertions: [p_continuation_seq_must_match]
```

With this shape the generator has little room to reinterpret.

## What Locked Truth Locks (MCTP Assembler candidates)

```text
packet classification rule        context key rule
SOM/EOM handling rule             single-packet message rule
continuation packet rule          packet sequence update rule
out-of-sequence drop rule         payload append rule
length accounting rule            commit rule
no-stale-data-after-drop rule     output valid/ready stability rule
reset/flush rule                  status/counter update rule
```

Concrete examples:

```text
LT-ASM-SINGLE-001: SOM=1 & EOM=1 packet is a complete single-packet message.
LT-ASM-START-001 : SOM=1 & EOM=0 packet allocates/replaces a context per the
                   configured collision policy.
LT-ASM-END-001   : a valid EOM packet commits exactly one completed message
                   after its payload is appended.
LT-ASM-DROP-001  : a dropped partial message is never later emitted as completed.
LT-ASM-OUT-001   : while msg_out_valid=1 and msg_out_ready=0, all msg_out payload
                   and metadata fields stay stable.
```

These are the per-contract work items the repair loop closes one at a time
(see [[llm-contract-repair-loop]] `## 5`).

## Locked Truth Vs Contract

```text
locked truth : the policy / meaning / answer-standard a human approved
contract     : the machine-usable expression RTL/SVA/TB consume
```

```text
Locked Truth:
  output must be stable during backpressure.
Contract:
  msg_out_valid && !msg_out_ready |=> msg_out_valid && $stable(msg_out_bundle)
```

So: locked truth = policy/semantics; contract = executable constraint. The
stage-by-stage reflection of one central contract is detailed in
[[contract-reflection-workflow]].

## Locked Truth Vs Req

```text
req          : the raw input requirement (may be ambiguous)
locked truth : the disambiguated, approved standard
```

```text
REQ: Assembler shall properly handle malformed packets.   # ambiguous

LT-ASM-DROP-OOS-001: an out-of-sequence continuation packet drops the active context.
LT-ASM-DROP-OOS-002: no completed message is emitted for the dropped context.
LT-ASM-DROP-OOS-003: the OOS-drop counter increments exactly once per drop event.
```

This is why a raw `*_requirements.md` is not yet locked truth — interpretation
and approval have to happen first. (See the open req→lock handoff gap noted in
[[locked-truth-design-spec-workflow]].)

## Change Rule (versioning)

Once locked, a truth is not edited in place. To change it:

```text
1. create a new version
2. find the affected obligations/contracts
3. invalidate the existing evidence
4. regenerate or re-verify RTL/SVA/TB
5. re-run validation
```

```text
LT-ASM-DROP-OOS-001 v1: OOS packet drops current assembly.
LT-ASM-DROP-OOS-001 v2: OOS packet drops current assembly AND enters a 1-cycle
                        recovery state.
```

v2 can invalidate existing SVA/TB/evidence, which is exactly why each locked
truth carries a `version`. Stale evidence after a truth change is the same
freshness failure mode tracked in [[golden-todo-evidence]] and the Hard Rules in
[[index]].

## Current Implementation Vs Proposed Refinement

The shipped lock writer (`workflow/req-gen/scripts/lock_requirement_set.py`,
validated end-to-end — see [[locked-truth-design-spec-workflow]]) already
realizes the *authority* idea, but at a coarser granularity than the per-truth
model above:

| Aspect | Shipped today | Proposed here |
|---|---|---|
| IDs | `requirement_id` / `obligation_id` / `contract_ref_id` | semantic `LT-*` truths with `derived_obligations` |
| Versioning | one bundle `bundle_sha256` + `schema_version: 1` (file format) | per-truth `version` with change cascade |
| Status | requirement `status: locked/approved`; manifest `requirements_locked` | per-obligation `draft -> reviewed -> locked` state |
| Change cascade | re-lock the whole bundle (new hash) | targeted invalidation of affected contracts/evidence only |
| Tamper check | per-file hash + bundle hash (proven to catch drift) | same, plus per-truth version pinning on each contract/evidence |

So this page is the **direction**, not a claim about current behavior: move from
bundle-level locking toward per-truth, versioned locking so that a single
changed truth invalidates only its dependent contracts and evidence rather than
the whole bundle.

## Summary

```text
Locked truth =
  take an ambiguous requirement,
  interpret it into a standard the design/verification/generation must follow,
  approve it, and pin it with a version.
```

Refined flow:

```text
req
  -> interpreted obligations
  -> locked truth        (approved, versioned answer-standard)
  -> executable contracts
  -> RTL/SVA/TB evidence
  -> validation closure
```

For the MCTP assembler, "assemble correctly" is too big — SOM, EOM, sequence,
tag/context, payload append, drop, commit, backpressure, and reset each lock as
their own truth, and the repair loop in [[llm-contract-repair-loop]] closes them
one contract at a time.

한 줄 요약: locked truth는 "회로가 맞다"가 아니라 "이걸 정답 기준으로 잠근다"는
뜻이고, 모호한 req를 해석·승인·버전 고정해 generator/리뷰어가 임의 해석하지
못하게 만드는 기준 사실이다.
