---
title: General IP Flow Trial And Error
type: lessons
tags: [ip-flow, ssot, signoff, mutation, formal, mctp, general-ip]
updated: 2026-06-02
related: [truth-coverage-gate, evidence-contract-obligation-traceability, mctp-assembler-scratch-flow-20260531, hw-agent-ip-experiment-batch-20260530, uart-tx-end-to-end-findings-20260530, full-flow-pipeline, human-review-and-escalation]
---

# General IP Flow Trial And Error - 2026-06-01

This page records the full set of practical lessons from the recent General IP experiments. It is intentionally a trial-and-error log, not a polished success story.

The main conclusion:

```text
LLM can search for an implementation.
Human-confirmed locked truth defines what correct means.
The workflow must prove that locked truth is covered by executable evidence.
```

## Starting Point

The initial methodology came from the PyMTL-style split:

```text
Requirement / intent
-> SSOT
-> FL golden model
-> CL performance model
-> RTL
-> cocotb/scoreboard
-> lint/sim/coverage
-> optional synth/DFT/PnR/PPA/formal
```

The important distinction was not the tool name. It was the boundary:

```text
Human = decide truth, targets, tradeoffs, waivers.
LLM    = generate, run, debug, patch toward that truth.
```

This led to a second distinction:

```text
AGENTS.md
  governs the worker: how the agent behaves.

IP_SIGNOFF.md
  governs the work product: what counts as IP evidence.
```

## Small IP Batch

The first experiments used bounded APB-style IPs:

- `apb_masked_match_demo`
- `apb_event_capture_demo`
- `apb_crc8_demo`
- seven more small datapath/control IPs for a 10-IP batch

What worked:

- SSOT -> FL/CL -> equivalence goals -> RTL -> cocotb -> coverage could run repeatedly.
- Small IPs exposed template bugs cheaply.
- `rtl_todo_plan.json`, `rtl_authoring_provenance.json`, and scoreboard schema became real gates, not paperwork.

What failed:

- A sim pass could still be weak evidence.
- A generated TB row could miss required fields like cycle, stimulus, mismatch, or FL model API.
- Provenance could go stale after regenerating RTL TODOs.
- Green compile/lint did not imply the RTL implemented the SSOT.

Workflow response:

- stricter scoreboard event schema
- RTL todo/static audit
- provenance refresh
- separate coverage and signoff evidence

## UART Trial

UART exposed the first serious "green while shallow" issue.

The original same-cycle generated TB could observe easy outputs like `busy`, but it did not deeply observe the serialized bit frame. A wrong bit-order mutation could survive because the monitor did not reconstruct the actual UART frame.

Lesson:

```text
For temporal/serial IP, same-cycle output checks are not enough.
The monitor must observe the semantic output over time.
```

This drove the idea of reusable monitor classes:

- serial frame monitor
- ready/valid monitor
- packet boundary monitor
- FIFO/backpressure monitor
- register/interrupt monitor
- SRAM no-hole packing monitor

## SPI Trial

SPI confirmed that static profiles are the wrong abstraction.

The tempting approach was:

```text
profile = SPI
load SPI-specific monitor/mutation/checklist
```

The better approach:

```text
read the IP's own SSOT/io_list/goals
derive capabilities and obligations
```

So the flow moved toward:

```text
<ip>/verify/ip_contract.json
```

That contract records capabilities, observables, monitors, mutations, and evidence obligations derived from the IP itself. This handles custom IP better than hardcoded labels like APB/FIFO/SPI/AXI.

## Mini CPU Trial

The simple CPU experiment showed that the methodology scales beyond bus adapters, but only if the evidence remains specific.

Useful evidence:

- instruction-level FL behavior
- architectural state observables
- cycle/retire behavior
- directed instruction scenarios
- mutation on decode, ALU, PC update, register writeback

Risk:

- A CPU can generate many plausible green tests while missing corner cases.
- Mutation helps reveal shallow observation, but it does not replace architectural coverage or formal invariants.

## Custom I/F -> FIFO -> Processing -> Custom I/F

The custom-interface pipeline question clarified the "General IP" target.

Yes, the flow should support:

```text
Custom I/F
-> FIFO / buffering engine
-> internal processing
-> Custom I/F
```

But the contract must be derived from facts in SSOT:

- interface handshake
- packet/frame boundary
- FIFO occupancy/backpressure
- ordering
- drop/error behavior
- transform correctness
- latency/throughput target
- observable outputs

No static profile is necessary. If the SSOT says a custom interface has `valid/ready/last/data`, the flow derives stream-like obligations. If it says request/ack, it derives request/ack obligations.

## Mutation Lessons

Mutation means intentionally breaking a copy of the RTL and checking whether the tests fail.

Example mutations:

- operator flip: `+` -> `-`, `^` -> `&`
- comparator flip: `==` -> `!=`
- handshake hold drop
- state update drop
- constant flip
- bit-order flip
- interrupt clear priority flip

What mutation is good for:

```text
It measures whether the verification harness can detect plausible RTL mistakes.
```

What mutation is not:

```text
It is not functional correctness proof.
It is not exhaustive.
It can include equivalent or irrelevant mutants.
It depends on mutation quality and sampling.
```

Important improvement:

```text
mutation_report category kill-rate
```

Example:

```text
operator_flip:       2/2 killed
comparator_flip:    14/14 killed
handshake_hold_drop: 2/2 killed
state_update_drop:  14/14 killed
```

This is more useful than one global kill-rate because it tells which behavior class is under-observed.

Policy:

- LLM may propose mutation classes.
- The deterministic workflow should own the mutation catalog used for signoff evidence.
- Humans decide whether a kill-rate threshold is required for an IP.
- Mutation remains advisory unless a human approves enforcement policy.

## Formal Proof Lessons

Formal proof was discussed as an optional workflow, not a required baseline.

Tools like `sby` and `prove` run formal engines against assertions. Unlike simulation, formal does not just try chosen test vectors. For a bounded property, it attempts to prove that no legal input sequence violates the assertion.

Useful examples:

- no descriptor before EOM
- no SRAM write on packet drop
- AXI valid data remains stable while valid and not ready
- FIFO never pops empty
- interrupt sticky bit clears only by W1C

Why it is optional:

- needs assertions
- needs tool availability
- can be hard to constrain correctly
- can prove the wrong thing if assumptions are wrong
- does not replace FL/RTL scoreboard testing

Workflow placement:

```text
SSOT
-> RTL
-> simulation and coverage
-> targeted assertions
-> optional formal proof for small safety invariants
```

## MCTP Assembler Trial

MCTP was the first broad, realistic IP trial.

Requirements evolved through conversation:

- PCIe VDM TLP enters through AXI4 write `WDATA`.
- AXI4 data width is 256 bits.
- One TLP is one AXI write transaction.
- AXI transaction may be a multi-beat burst.
- Internal assembly contexts support interleaving.
- First TLP header and last TLP header are stored per Q.
- SRAM stores only MCTP payload, not TLP headers.
- SRAM interface width is 256 bits.
- Payload packing must be contiguous with no holes even when fragment length is not 32B aligned.
- Transmission unit size is 64B to 4KB, 4B aligned, with shorter final fragment allowed.
- Packet drop and assembly drop reasons must be counted and exposed.
- AXI read path allows firmware to read assembled payload from SRAM-backed descriptors.
- Debug, control, status, and interrupt registers are separated.
- Each Q exposes state, error, SRAM base, counters, and metadata.
- Each Q has its own FSM.

Implementation evidence reached:

- RTL compile pass
- DUT lint pass
- cocotb simulation pass
- FL/RTL compare pass
- coverage pass
- simulation quality pass
- mutation report present
- signoff passed before the truth-coverage gate existed

Then the key workflow bug appeared:

```text
The IP could have green local evidence while the full human requirement set was not proven.
```

The issue was not simply "missing req.md". The deeper issue was:

```text
Locked truth was broader than the evidence map.
```

Some requirements existed in prose or SSOT, but final signoff did not require every one of them to appear in executable evidence.

## Verilog Style Trial

The MCTP RTL also exposed style policy ambiguity.

User constraint:

```text
No integer.
No function/task.
Verilog-2001-ish style.
logic is allowed.
```

Lesson:

- style constraints must be SSOT/workflow-readable, not inferred late
- compile pass is not enough if the user has RTL style rules
- lint/style gate should distinguish language subset policy from simulator compatibility

## Direct SSOT Without Req

Important correction:

```text
req document is optional.
direct SSOT authoring is allowed.
```

Therefore the workflow must support both:

```text
req/spec -> SSOT -> evidence
direct SSOT -> evidence
```

The requirement is not "there must be a req file." The requirement is:

```text
whatever is locked truth must be traceable to evidence.
```

If no req ledger exists, SSOT itself is the locked-truth source.

## Truth Coverage Gate

The response was to add:

```text
workflow/reqcov/scripts/check_truth_coverage.py
```

It writes:

```text
<ip>/signoff/truth_coverage.json
```

It reads obligations from:

- SSOT `function_model.transactions`
- SSOT `error_handling.error_sources`
- SSOT `registers.register_list`
- SSOT `interrupts.sources`
- SSOT `test_requirements.scenarios`
- SSOT `test_requirements.coverage_goals`
- SSOT `workflow_todos`
- optional `<ip>/req/requirement_coverage.json`

It reads evidence from:

- `sim/scoreboard_events.jsonl`
- `cov/coverage.json`
- `rtl/rtl_todo_plan.json`
- `signoff/ip_signoff.json`

Final signoff now requires `truth_coverage` to pass.

Initial MCTP result immediately after adding this stricter gate:

```text
truth_coverage: status=fail
obligations=95
covered=61
uncovered_required=34
signoff: status=fail, 16/17 gates pass
```

This is a good failure. It means the workflow now refuses to claim full requirement satisfaction when the evidence map is incomplete.

After the evidence map was repaired, the same scratch IP reached local signoff:

```text
truth_coverage: status=pass
obligations=95
covered=95
uncovered_required=0
signoff: status=pass, 18/18 gates pass
```

This is still a local workflow signoff, not a production or standards-conformance signoff. The lesson is:

```text
green gates are only meaningful when their scope is explicit.
```

The next improvement is not more pass/fail gates. It is stronger traceability:

```text
SSOT requirement
-> atomic obligation
-> scenario
-> required observable
-> pass condition
-> scoreboard row
```

That proposed layer is recorded in [[evidence-contract-obligation-traceability]].

## Post-Signoff Design Review Lessons

The later assemble-logic review found important issues that were not visible from the headline signoff number.

Assemble path currently behaves as:

```text
AXI4 write burst
-> PCIe VDM parser
-> MCTP parser
-> context table / per-Q FSM
-> AXI ingress payload replay
-> SRAM packer
-> descriptor queue
-> AXI read egress
```

Main design lessons:

- The payload write path is too indirect. `context_table` decides the destination address and payload count, then AXI ingress replays captured burst bytes into the SRAM packer. This passed local tests, but the responsibility split is weak. Payload replay should be separated from AXI transaction capture.
- The context key must be explicitly locked. Current RTL keying was observed as source EID, tag owner, and message tag. If approved truth requires destination EID in the assembly key, the RTL is incomplete even if interleave tests pass.
- SRAM packing must be an explicit byte-pack and flush contract. "No holes" is not proven by a wide SRAM interface alone; it needs byte-lane evidence for unaligned fragment lengths and final partial beats.
- Descriptor publication must be tied to SRAM write completion. Pushing a descriptor at EOM is not enough if the final packed SRAM word can still be pending.
- cocotb exists under the IP, but it is not yet fully separated into a reusable contract-driven monitor generator. The flow needs reusable monitor templates so each new IP does not re-hand-author the same scoreboard plumbing.
- Mutation survivors are useful review signals. They point to monitor or stimulus weakness, but they do not prove the RTL wrong by themselves because some survivors can be equivalent or irrelevant.
- Commit/push evidence should be scoped to the IP and workflow artifacts only. Dirty unrelated frontend/core files can exist in the same worktree and must not be reverted or accidentally claimed.

The practical quality label for this MCTP run is:

```text
local verification prototype:
  compile/lint/sim/coverage/truth_coverage/signoff pass
  useful for workflow learning
  not yet production IP
```

## What Changed In Workflow

Landed changes from these trials:

- `IP_SIGNOFF.md` separates IP evidence policy from `AGENTS.md`.
- `workflow/STAGE_MANIFEST.json` is the single routing table for agents.
- `derive_ip_contract.py` derives per-IP contract from SSOT/IO/goals instead of static profiles.
- `mutation_guard.py` reports category kill-rate and supports per-IP mutation obligations.
- `check_truth_coverage.py` checks locked-truth coverage from direct SSOT or optional req ledger.
- `check_ip_signoff.py` now fails if `truth_coverage.json` is missing or failing.
- `doc/wiki/truth-coverage-gate.md` records the new gate.
- `doc/wiki/evidence-contract-obligation-traceability.md` records the next obligation-level traceability proposal.

## What Is Still Weak

Known remaining gaps:

- Some evidence mapping can still become too token-like unless it is backed by concrete scenario rows.
- Workflow acceptance criteria are sometimes too prose-like.
- Mutation kill-rate remains advisory and can still be low.
- Formal proof is documented as optional but not integrated as a running gate.
- PPA/DFT/PnR remain out of local scratch signoff.
- External PCIe/MCTP standards conformance is not certified by this flow.
- Reusable cocotb monitor generation is still weaker than the SSOT/RTL/signoff machinery.
- RTL design review still matters after machine signoff, especially for ownership split, flush ordering, and keying rules.

## Current Best Practice

For a new General IP:

```text
1. Author req or direct SSOT.
2. Lock SSOT as truth.
3. Generate FL/CL/equivalence goals.
4. Derive ip_contract from actual IP artifacts.
5. Derive or review evidence_contract obligations.
6. Implement RTL and TB.
7. Run compile/lint/sim/scoreboard/coverage.
8. Run mutation as harness-depth signal.
9. Run truth_coverage.
10. Run final local signoff.
11. Add explicit quality label: local evidence pass, engineering review pass/partial, production signoff blocked/pass.
12. If truth_coverage or evidence_contract coverage fails, improve evidence or explicitly defer/waive the requirement.
```

The stop condition is not "all possible EDA gates exist." The stop condition for local workflow signoff is:

```text
every required locked-truth obligation has executable evidence,
all machine gates pass,
remaining optional production gates are explicitly out-of-scope or human-owned.
```

Implementation quality should be judged separately from local signoff:

```text
correctness:
  RTL observed behavior matches FL/expected results.

coverage:
  important scenarios and corner cases are exercised.

robustness:
  mutation/assertion/bug-injection pressure shows monitors can fail.

RTL review:
  structure naturally implements the requirement, not just the narrow test.

production readiness:
  standard conformance, CDC, PPA, DFT, STA, formal, and human approval are done
  if the project scope requires them.
```

The operational default should stay simple:

```text
1. 맞게 동작하나?
   RTL observed output/readback matches FL expected.

2. 충분히 때려봤나?
   Important scenarios and corner cases executed.

3. 일부러 깨면 잡나?
   Mutation, assertion, or targeted bug injection can fail the test.

4. 구조가 이상하지 않은가?
   Human RTL review finds no blocker for the claimed scope.
```

## Hard Conclusions

- General IP flow must not use fixed profiles as authority.
- Direct SSOT is valid, but then SSOT must be the traceable obligation source.
- requirement satisfaction needs an explicit evidence contract, not only token-level matching.
- cocotb pass is necessary, not sufficient.
- coverage pass is necessary, not sufficient unless coverage is tied to locked truth.
- mutation is useful for test depth, not correctness proof.
- formal proof is useful for small invariants, not a substitute for missing tests.
- signoff must fail loudly when evidence does not cover full locked truth.
- LLM should not change locked truth to make RTL pass.

Related pages: [[truth-coverage-gate]], [[mctp-assembler-scratch-flow-20260531]], [[hw-agent-ip-experiment-batch-20260530]], [[uart-tx-end-to-end-findings-20260530]], [[full-flow-pipeline]], [[human-review-and-escalation]].
