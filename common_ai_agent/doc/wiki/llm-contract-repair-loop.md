---
title: LLM Contract Repair Loop
type: proposal
tags: [repair-loop, locked-truth, contract, evidence, validation-closure, rtl-repair, mctp, patch-agent, direction]
updated: 2026-06-06
related: [locked-truth-concept, mctp-assembler-contract-breakdown, formal-verification-evidence, spec-loop-and-equivalence-check, locked-truth-design-spec-workflow, contract-reflection-workflow, evidence-contract-obligation-traceability, workflow-feedback-and-scheduling, human-review-and-escalation, golden-todo-evidence, parallel-todo-sub-agent-workers, sim-debug-agent-tool-2026-05-31, mctp-assembler-scratch-flow-20260531]
---

# LLM Contract Repair Loop

This page records the agreed forward direction for how the LLM is positioned in
the IP flow. It builds directly on [[locked-truth-design-spec-workflow]] (Locked
Truth is the authority) and [[contract-reflection-workflow]] (the
req→obligation→contract→evidence spine).

The core decision:

```text
The LLM is not an "RTL generator".
The LLM is a "patch agent" that closes one unclosed contract at a time.
```

## Re-centering The Loop

The center of the loop changes from generation to contract closure.

Bad structure:

```text
LLM -> generate RTL -> loose test -> on failure, ask again
```

Good structure:

```text
locked truth -> contract -> run evidence -> create failure ticket
-> LLM diagnosis/patch -> re-verify -> refresh evidence -> validation closure
```

The unit of one repair iteration is **one unclosed contract**, never a whole
module.

Public research points the same way. VerilogEval proposed evaluating
LLM-generated Verilog by automatically simulating it against a golden solution.
RTLFixer showed an iterative repair structure that uses RAG/ReAct plus compiler
feedback to fix LLM-generated Verilog. RTLFixer is mostly syntax/compile repair;
our direction extends that idea into a **contract-level functional repair loop**
for the MCTP assembler and any other IP.

- VerilogEval — LLM Verilog generation evaluated by automatic simulation vs golden.
- RTLFixer — RAG/ReAct + compiler feedback iterative repair (compile/simulate
  modes; binary / compiler-log / RAG feedback). We extend this to compiler +
  simulation + formal counterexample + contract RAG.

## 1. Base Structure

```text
Locked Truth Store
  v
Obligation / Contract DB
  v
RTL + SVA + TB generation
  v
Compile / lint / sim / formal / coverage
  v
Failure Normalizer
  v
Repair Ticket
  v
LLM Diagnosis
  v
Patch Proposal
  v
Patch Apply
  v
Re-run evidence
  v
Validation closed or loop again
```

As a block diagram:

```text
+---------------------+
| locked truth        |  read-only
+----------+----------+
           v
+---------------------+
| contract DB         |  versioned
+----------+----------+
           v
+---------------------+
| RTL / SVA / TB      |  generated or hand-written
+----------+----------+
           v
+---------------------+
| evidence runner     |  compile, sim, formal, lint
+----------+----------+
           v
+---------------------+
| failure ticket      |  contract-linked failure
+----------+----------+
           v
+---------------------+
| LLM repair agent    |  diagnosis + minimal patch
+----------+----------+
           v
+---------------------+
| validation gate     |  accept / reject / escalate
+---------------------+
```

The single most important rule:

```text
The LLM never edits locked truth.
The LLM proposes RTL/SVA/TB patches that make the design satisfy locked truth.
```

If locked truth is itself wrong or ambiguous, the LLM must emit a
**clarification request**, not a patch. See [[human-review-and-escalation]].

## 2. Input Is A Failure Ticket, Not A Raw Log

Handing the LLM raw logs makes it fix the wrong place. Every failure must be
normalized against the contract first. A failure ticket carries the failing
contract, the locked-truth IDs it serves, observed vs expected behavior, edit
policy, and the evidence that must pass after the patch.

```yaml
failure_ticket:
  id: F-ASM-SEQ-0007
  block: mctp_rx_assembler
  failing_contract: C-ASM-SEQ-OOS-DROP
  locked_truth:
    - LT-ASM-SEQ-003
    - LT-ASM-DROP-001
  statement: >
    Out-of-sequence continuation packet shall drop the active assembly
    and shall not emit a completed message from the dropped context.
  failure_type: formal_counterexample
  failing_property: p_oos_drops_current_assembly
  observed:
    cycle_12: { context_active: 1, expected_seq: 2, pkt_accept: 1, pkt_som: 0, pkt_eom: 0, pkt_seq: 3 }
    cycle_13: { context_active: 1, drop_pulse: 0, msg_out_valid: 0 }
  expected:
    cycle_13: { context_active: 0, drop_pulse: 1, msg_out_valid: 0 }
  suspect_files:   [rtl/mctp_rx_assembler.sv, rtl/mctp_asm_context.sv]
  editable_files:  [rtl/mctp_rx_assembler.sv, rtl/mctp_asm_context.sv]
  forbidden_edits: [ssot/locked_truth.yaml, contracts/mctp_asm_contracts.yaml, sva/mctp_asm_seq_sva.sv]
  required_evidence_after_patch:
    - E-FORMAL-ASM-SEQ-OOS-DROP
    - E-SIM-ASM-SEQ-OOS-02
    - E-SIM-ASM-SEQ-NORMAL-0123
    - E-REGRESSION-ASM-BASIC
```

With this, the LLM reasons about *which locked truth which evidence failed to
close*, not merely "what broke".

## 3. Roles Inside The Loop

Do not give one large LLM the whole job. Split roles (this maps onto the
sub-agent worker fan-out in [[parallel-todo-sub-agent-workers]]):

```text
1. Failure Normalizer  — tool log / assertion fail / sim mismatch / waveform
                         summary  ->  contract-linked failure ticket
2. Diagnosis Agent     — classify: RTL bug | SVA bug | TB bug | contract ambiguity
3. Patch Agent         — minimal diff within allowed files only
4. Critic Agent        — did the patch bypass locked truth or weaken assertions?
5. Evidence Runner     — actually run compile/lint/sim/formal
6. Validation Gate     — enough evidence -> closure, else loop
```

## 4. Three Levels Of Repair

Not every failure is an RTL bug. The loop must branch at least three ways:

```text
A. RTL repair loop                    — locked truth & contract correct, RTL wrong
B. verification collateral repair     — RTL correct, but SVA/TB/scoreboard
                                        mis-expresses the contract
C. truth clarification loop           — requirement / locked truth ambiguous or
                                        self-conflicting  (human authority)
```

MCTP example: the spec identifies an assembly by `Msg Tag`, `TO`, and
`Source Endpoint ID`, and only one assembly proceeds per message terminus.

```text
RTL uses {src_eid, msg_tag} only, dropping TO   -> A (RTL repair)
SVA uses {src_eid, msg_tag} only as the key      -> B (SVA repair)
Spec intends to ignore TO                         -> C (locked truth change, human-approved)
```

```text
failure:    different-TO packets merged into the same assembly context
root cause: context key missing TO bit
repair:     context_key <= {src_eid, to, msg_tag}
```

## 5. Split The Loop By Contract Unit (MCTP Assembler)

Work items should be contract-sized:

```text
C-ASM-GATE-DROP
C-ASM-KEY-ISOLATION
C-ASM-START-CONTEXT-ALLOC
C-ASM-SINGLE-COMMIT
C-ASM-SEQ-MOD4
C-ASM-SEQ-OOS-DROP
C-ASM-PAYLOAD-LEN-ACCOUNTING
C-ASM-PAYLOAD-NO-DROP-DUP
C-ASM-END-COMMIT-ONCE
C-ASM-DROP-NO-STALE-DATA
C-ASM-OUT-STABLE-BACKPRESSURE
C-ASM-RESET-NO-STALE-OUTPUT
```

Repair then runs scoped:

```text
C-ASM-SEQ-OOS-DROP failed
  -> give only sequence/drop-related RTL as context
  -> generate patch
  -> run sequence formal + sequence directed sim first
  -> if pass, run assembler regression
  -> if pass, evidence closed
```

This keeps the LLM from trying to "fix all of MCTP".

## 6. The Loop Algorithm

```text
MAX_REPAIR_ITERS = 5
for contract in validation_plan:
    evidence_result = run_required_evidence(contract)
    if evidence_result.pass_all():
        close_validation(contract); continue

    ticket = normalize_failure(
        contract=contract,
        locked_truth=get_locked_truth(contract),
        evidence=evidence_result,
        rtl_snapshot=current_rtl_snapshot(),
        allowed_files=edit_policy(contract),
    )

    for i in range(MAX_REPAIR_ITERS):
        diagnosis = llm_diagnose(ticket)
        if diagnosis.kind == "locked_truth_ambiguity":
            create_clarification_request(ticket, diagnosis); mark_blocked(contract); break
        if diagnosis.kind == "verification_collateral_bug":
            patch = llm_patch_verification_collateral(ticket, diagnosis)
        else:
            patch = llm_patch_rtl(ticket, diagnosis)

        if not static_patch_policy_check(patch):
            ticket.add_rejection("patch_policy_failed"); continue

        apply_patch_on_branch(patch)
        targeted = run_targeted_evidence(contract)        # the broken contract only — fast
        if not targeted.pass_all():
            ticket = update_ticket_with_new_failure(ticket, targeted)
            revert_or_continue_patch_branch(); continue

        regression = run_impacted_regression(contract)    # did the patch break others?
        if regression.pass_all():
            record_evidence(contract, targeted, regression, patch)
            close_validation(contract); merge_patch(patch); break
        ticket = update_ticket_with_regression_failure(ticket, regression)
        revert_or_continue_patch_branch()
    else:
        mark_needs_human_review(contract)
```

The key is separating `run_targeted_evidence()` (confirm the broken contract
fast) from `run_impacted_regression()` (confirm no other contract regressed).
This is the contract-scoped specialization of the repair feedback in
[[workflow-feedback-and-scheduling]].

## 7. Constrained Patch Prompt

Never tell the LLM "just fix it". The prompt must be a contract-repair form:

```text
You are repairing RTL for one failing contract.
Rules:
1. Do not modify locked truth.
2. Do not weaken assertions.
3. Do not modify tests unless the failure is classified as verification collateral bug.
4. Produce a minimal diff only.
5. Preserve all existing passing contracts unless explicitly listed as impacted.
6. Explain root cause using signal-level reasoning.
7. Every behavioral change must map to one obligation ID.
```

Input bundle:

```text
[LOCKED_TRUTH]      LT-ASM-SEQ-003 ...
[CONTRACT]          C-ASM-SEQ-OOS-DROP ...
[FAILING_EVIDENCE]  formal counterexample summary ...
[RTL_CONTEXT]       only relevant modules/functions/always blocks ...
[EDIT_POLICY]       allowed files, forbidden files ...
[OUTPUT_FORMAT]     diagnosis / patch / impacted_contracts / required_tests / risk
```

Output is structured, not prose:

```yaml
repair_proposal:
  id: R-ASM-SEQ-0007-P1
  diagnosis: >
    The continuation-packet sequence mismatch is detected, but the FSM remains
    in ASM_ACTIVE instead of transitioning to ASM_DROP.
  root_cause:
    file: rtl/mctp_rx_assembler.sv
    signal: seq_mismatch
    issue: "seq_mismatch is not included in the active-context abort condition."
  patch_summary: >
    Add seq_mismatch to abort_current_assembly and suppress commit for the
    dropped context.
  changed_contracts:
    intended_to_fix: [C-ASM-SEQ-OOS-DROP]
    must_not_change:  [C-ASM-END-COMMIT-ONCE, C-ASM-PAYLOAD-LEN-ACCOUNTING, C-ASM-OUT-STABLE-BACKPRESSURE]
  diff: |
    ...
  required_evidence: [E-FORMAL-ASM-SEQ-OOS-DROP, E-SIM-ASM-SEQ-OOS-02, E-REGRESSION-ASM-BASIC]
```

## 8. Worked Example — MCTP Sequence Repair

Locked truth:

```yaml
locked_truth:
  - id: LT-ASM-SEQ-003
    statement: >
      For a multi-packet message, each accepted continuation packet shall have a
      packet sequence number that is the expected modulo-4 increment of the
      previously accepted packet.
  - id: LT-ASM-DROP-001
    statement: >
      If an out-of-sequence continuation packet is accepted, all data for the
      active assembly shall be dropped and no completed message shall be emitted
      from that dropped context.
```

These bind directly to MCTP's modulo-4 sequence and out-of-sequence drop rules.
Contract:

```yaml
contract:
  id: C-ASM-SEQ-OOS-DROP
  obligations: [OBIL-ASM-SEQ-004, OBIL-ASM-DROP-002]
  assertions:  [p_oos_drops_current_assembly, p_oos_never_commits_message]
  simulations: [tc_start_seq0_then_seq2_drop]
```

The repair target is this condition, not "the MCTP assembler":

```systemverilog
// bad pattern
if (pkt_accept && context_active && !pkt_som) begin
  if (pkt_seq == expected_seq) begin
    append_payload <= 1'b1;
    expected_seq   <= expected_seq + 2'd1;
  end
end
```

```systemverilog
// patched direction
seq_mismatch = pkt_accept && context_active && !pkt_som && (pkt_seq != expected_seq);
if (seq_mismatch) begin
  context_active <= 1'b0;
  drop_pulse     <= 1'b1;
  commit_pending <= 1'b0;
end else if (pkt_accept && context_active && !pkt_som) begin
  append_payload <= 1'b1;
  expected_seq   <= expected_seq + 2'd1;
end
```

Do not judge pass/fail immediately — re-run the evidence set:

```text
1. compile
2. lint
3. p_oos_drops_current_assembly  (formal)
4. p_oos_never_commits_message   (formal)
5. tc_start_seq0_then_seq2_drop  (sim)
6. normal sequence 0->1->2->3    (sim)
7. end-commit regression
8. output-backpressure regression
```

This prevents fixing OOS-drop while breaking normal EOM commit.

## 9. Evidence Runner Is Cheap-To-Expensive

Running expensive formal/regression first makes the loop slow. Stage it:

```text
L0  parse / compile
L1  elaboration / width / interface check
L2  lint / reset / X-prop quick checks
L3  generated SVA simulation
L4  targeted directed simulation
L5  targeted formal
L6  random simulation + scoreboard
L7  impacted regression
L8  coverage / validation closure
```

In practice, per patch: `compile -> targeted contract check -> impacted
regression`.

## 10. Record Every Repair In The Evidence Ledger

A passing patch is not merged silently; it updates the evidence ledger (the
contract-closure extension of [[golden-todo-evidence]]).

```yaml
repair_record:
  id: R-ASM-SEQ-0007
  failure: F-ASM-SEQ-0007
  patch: patches/R-ASM-SEQ-0007.patch
  fixed_contract: [C-ASM-SEQ-OOS-DROP]
  impacted_contracts_checked: [C-ASM-SEQ-MOD4, C-ASM-END-COMMIT-ONCE, C-ASM-DROP-NO-STALE-DATA, C-ASM-OUT-STABLE-BACKPRESSURE]
  evidence_after_patch:
    - { id: E-FORMAL-ASM-SEQ-OOS-DROP-2026-06-06, result: proven }
    - { id: E-SIM-ASM-SEQ-OOS-02-2026-06-06,      result: pass }
    - { id: E-REGRESSION-ASM-BASIC-2026-06-06,    result: pass }
  validation_status: closed
```

This makes every patch auditable: why it landed, which locked truth it closed,
which contracts it did not break, and what evidence backed it.

## 11. What The LLM Must Never Do

The most dangerous failure mode is making the gate green by cheating:

```text
weaken an assertion to force pass
change a testbench expected value to force pass
over-add a formal `assume` to hide a bug
silently edit locked truth
rewrite unrelated RTL at large scale
break a passing contract but only run the targeted test
```

So a deterministic policy check guards every patch (aligns with the Hard Rules in
[[index]] and [[workflow-ownership-and-boundaries]]):

```yaml
patch_policy:
  locked_truth_edit: forbidden
  contract_edit: forbidden_by_default
  assertion_weakening: forbidden
  assume_addition: human_review_required
  test_expected_change: allowed_only_if_ticket_type_is_tb_bug
  max_files_changed: 2
  max_behavioral_contracts_impacted: 1
  require_impacted_regression: true
```

Formal `assume` additions are especially risky: a bad one narrows the
environment to hide the bug instead of fixing the RTL.

## 12. End State — A "Contract Closure Bot"

```text
mctp_rx_assembler/
  ssot/        locked_truth.yaml  obligations.yaml  contracts.yaml
  rtl/         mctp_rx_assembler.sv  mctp_asm_context.sv  mctp_asm_payload_buffer.sv
  sva/         mctp_asm_seq_sva.sv  mctp_asm_drop_sva.sv  mctp_asm_out_sva.sv
  tb/          tb_mctp_asm.sv  scoreboard_mctp_asm.sv  tests/{tc_seq_oos,tc_single_packet,tc_start_middle_end}.py
  evidence/    formal/  sim/  lint/  coverage/
  repair/      failures/  proposals/  patches/  records/
```

The loop only ever asks:

```text
is there an open validation item?
  no  -> done
  yes -> create failure ticket -> LLM patch -> re-run evidence
         -> closed: record in ledger
         -> not closed: next repair attempt (or human review at the cap)
```

## Summary

```text
LLM repair loop =
  hold locked truth and contracts fixed,
  turn evidence failures into contract-linked failure tickets,
  let the LLM propose minimal RTL/SVA/TB patches,
  let the deterministic toolchain regenerate evidence,
  and let the validation gate decide closure — repeated until dry.
```

For the MCTP assembler, run a separate repair loop per contract group:

```text
gate · key/context · start · single · continuation · sequence ·
payload · end/commit · drop/error · output handshake · reset/flush
```

한 줄 요약: LLM이 MCTP Assembler를 "고치는" 게 아니라,
`C-ASM-SEQ-OOS-DROP` 같은 작은 contract failure를 하나씩 닫게 만드는 구조가
우리의 방향이다.
