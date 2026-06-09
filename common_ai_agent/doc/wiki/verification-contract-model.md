---
title: Verification Contract Model (VCM)
category: architecture
tags: [contract-reflection, ssot, freshness, evidence, signoff, mctp]
status: generalized to a workflow primitive + locked by 6-case regression (2026-06-04); auto-generator INTEGRATED (2026-06-10); full matrix pending
---

# Verification Contract Model (VCM)

Agreed design (2026-06-04) for how a `requirement` is proven against locked truth in
the ATLAS workflow. Consolidates the contract-reflection + evidence-contract +
semantic-freshness layers into one model. See [[contract-reflection-workflow]].

## Spine

```
requirement -> obligation -> contract_ref -> evidence_artifact -> validator_result
```

## Stage layer

Each workflow stage (ssot, fl, cl, rtl, tb, sim, lint, mutation, coverage, signoff)
declares: **inputs, fingerprints, artifacts, owned obligations, validators.**

## Objects

### Requirement
```yaml
requirement:
  id: REQ_..._ASSEMBLY_001
  claim: "multi-beat MCTP payload is assembled into SRAM without loss"
  ssot_refs: [function_model.transactions.payload_pack_write]   # root provenance
  obligation_ids: [OBL_..._PAYLOAD_COUNT_001, OBL_..._PAYLOAD_CONTENT_001]
```

### Obligation  (stage is a ROLE set, not singular)
```yaml
obligation:
  id: OBL_..._PAYLOAD_CONTENT_001
  requirement_ids: [REQ_..._ASSEMBLY_001]
  contract_refs:   [SEMANTIC_STATE_PAYLOAD_CONTENT]
  granularity: content            # structural | count | content | temporal
  owned_by_stage: sim             # the stage that records the evidence
  required_stages: [fl, rtl, tb, sim]   # all stages that must exist for this to mean anything
  closure_stage: sim              # the stage at which this obligation closes
  failure_owner: rtl-gen          # which workflow owns the fix when it fails
  evidence_ref: {scenario_id: SC_RB_4096, goal_id: EQ_TRANSACTION_FM_PACK_SRAM}
  pass_conditions:
    - {kind: observed_equals_fl_expected, field: payload_digest,
       expected_path: fl_expected...payload_digest}
```

### ContractRef  (ssot_anchor MANDATORY)
```yaml
contract_ref:
  id: SEMANTIC_STATE_PAYLOAD_CONTENT
  ssot_anchor: function_model.transactions.payload_pack_write   # must trace to SSOT
  reflection:
    ssot: {section: function_model.transactions.payload_pack_write}
    fl:   {symbol: payload_pack_write}
    rtl:  {owner_files: [rtl/..._context_table.sv], observable_via: [payload_digest]}
    tb:   {monitor: DatapathMonitor}
    sim:  {scoreboard: sim/scoreboard_events.jsonl, wave: sim/...vcd}
```

### StageContract
```yaml
stage_contract:
  stage: sim
  inputs:
    - {artifact: "rtl/*.sv"}
    - {artifact: "tb/cocotb/*"}
    - {artifact: "verify/equivalence_goals.json"}
    - {ssot_section: function_model}
  source_fingerprint: <sha256(inputs)>     # stamped into produced artifact
  produces: sim/scoreboard_events.jsonl
  owns_obligations: [OBL_..._PAYLOAD_COUNT_001, OBL_..._PAYLOAD_CONTENT_001]
  validator: {script: workflow/.../check_evidence_contract.py}
```

### EvidenceArtifact  (separate object)
```yaml
evidence_artifact:
  path: sim/scoreboard_events.jsonl
  produced_by: sim
  source_fingerprint: <sha256 of stage inputs at production time>
```

### ValidatorResult  (separate object)
```yaml
validator_result:
  obligation_id: OBL_..._PAYLOAD_CONTENT_001
  status: pass | fail | blocked | stale
  condition_results: {payload_digest_matches_fl: true}
  freshness_ok: true
```

## Pass rule (every validator, every stage)

```
obligation PASS  =  correctness  AND  freshness
  correctness: pass_conditions hold on the evidence_artifact
  freshness:   evidence_artifact.source_fingerprint == sha256(current inputs)
               (SSOT / FL / CL / RTL / TB / scoreboard changed -> stale -> fail|stale-blocked)
```

## Closure rule (required cells only)

A requirement is closed iff **every REQUIRED (stage x granularity) cell** is
`pass | waived | explicitly human-blocked`. Not every cell is required.

```
example required cells for "MCTP payload content":
  fl/content       required
  rtl/structural   required
  tb/structural    required
  sim/content      required
  sim/temporal     required
```
A missing required cell (e.g. sim/content absent) -> truth-coverage gate FAIL.
This is what structurally prevents "count passes, content untested" fake-green.

## First must-have (proof-of-structure)

```yaml
OBL_MCTP_PAYLOAD_CONTENT_001:
  granularity: content
  required_stages: [fl, rtl, tb, sim]
  closure_stage: sim
  failure_owner: rtl-gen
  expected: FL-derived payload_digest
  observed: RTL readback / SRAM payload digest
  validator: payload_digest_matches_fl
  freshness: SSOT + FL + RTL + TB + scoreboard hash match
```
Closing this single obligation exercises the entire spine end-to-end and shows
whether the model actually works.

## Per-layer implementation map

| Layer | Change |
|---|---|
| SSOT `function_model` | declare `payload_digest` as a derived output of `payload_pack_write` + a content invariant |
| FL (`emit_fl_model`) | compute golden `payload_digest` over assembled payload bytes |
| TB/scoreboard | monitor computes digest over SRAM payload (already captured by readback) + FL golden; record both in `rtl_observed` / `fl_expected` (minimal/no RTL change — digest derivable from existing readback) |
| Obligation generator | rule: payload-bearing transaction -> emit a `content` obligation, not only `count` |
| ContractRef | add `ssot_anchor` |
| Validator | `observed_equals_fl_expected` already supports it; ADD freshness check (all stages) |
| Signoff gate | extend truth-coverage to the (stage x granularity) matrix; required cell missing -> FAIL |

## Implemented (2026-06-04) — first must-have proven

`OBL_MCTP_PAYLOAD_CONTENT_001` is live and proven on mctp_assembler_v3:

```
VCM-1 (tb): test_sram_write_monitor.py records SC_RB_4096 + SC_RB_FRAG rows with
            rtl_observed.payload_digest (sha256 of actual SRAM bytes) and
            fl_expected.model_result.state_updates.payload_digest (sha256 of golden
            build_vdm_tlp bytes) — independent sources, non-circular.
VCM-2 (semantic): obligation added to verify/semantic_contracts.json (granularity=content,
            ssot_anchor=function_model.transactions.payload_pack_write, pass_condition
            observed_equals_fl_expected over payload_digest); overlay propagated it into
            verify/evidence_contract.json (105 -> 106 obligations). No validator change
            (observed_equals_fl_expected already existed); content-axis keys accepted as-is.
VCM-6 (gate): NEW signoff gate `contract_content_coverage` in check_ip_signoff.py — an IP
            with a contract layer must carry >=1 passing granularity:content obligation,
            else FAIL. Backward-compatible (no contract layer -> not applicable). Gate test
            suite 11/11 unchanged.

Proof:
  positive:        run_contract_check -> PASS, evidence 106/106 (digest==digest, 4096 bytes)
  negative control: flip 1 hex char of observed digest -> OBL_MCTP_PAYLOAD_CONTENT_001 FAILS
                    -> contract-check BLOCKED 105/106 (non-vacuous)
  full signoff:    19/19 (contract_content_coverage pass; content_obligations=1)
```

Workflow dependency introduced: `run_contract_check.py` must run before `check_ip_signoff`
(the gate reads `signoff/evidence_contract_coverage.json`). Freshness of that file is the
fingerprint layer's job ([[contract-reflection-workflow]] semantic_source_fingerprint),
to be generalized to all stages.

Still pending (full generalization, not in this slice): SSOT `function_model` declaring
`payload_digest` for FL-native golden; per-stage input fingerprints + the
(stage x granularity) matrix in the truth-coverage gate.

## Generator (integrated 2026-06-10, extracted from feat/vcm-generator 4d866ca4)

The obligation generator is now in the tree — `semantic_contracts.json` no longer has
to be hand-authored:

- `workflow/contract-reflection/scripts/emit_semantic_contracts.py` — deterministically
  derives `verify/semantic_contracts.json` from the SSOT `function_model`
  (transactions/state_variables/invariants) + `test_requirements`, joined to REAL
  passing scoreboard rows and the VCD wave. Every obligation is grounded in a row that
  passes at generation time (no unsatisfiable claims); a payload-bearing transaction
  MUST yield a `granularity:content` obligation or the generator hard-fails; the
  document is self-validated with `semantic_source_validation.source_issues` before
  writing. Runs AFTER sim (needs scoreboard + wave), BEFORE contract-check.
- `workflow/contract-reflection/scripts/annotate_scoreboard_obligations.py` — additive
  sidecar `sim/scoreboard_obligation_links.json` mapping evidence rows back to
  obligation_ids/contract_refs (append-only `scoreboard_events.jsonl` untouched). Runs
  after the overlay produces `evidence_contract.json`.
- `workflow/contract-reflection/system_prompt.md` + `todo_templates/contract-reflection.json`
  — agent-facing VCM authoring guidance and the 4-step todo plan
  (emit -> annotate -> strict check -> resolve-at-owning-stage).

E2E proof (mctp_assembler_v3, 2026-06-10): generated 8 requirements / 9 obligations
(2 count, 6 temporal, 1 content) vs the hand-authored 2/4; `run_contract_check`
passes in BOTH default and `--require-contract-closure` strict mode (reflection 10/10,
evidence 111/111); output is byte-identical across reruns (deterministic). NOT taken
from the branch: its edits to `check_ip_signoff.py` / `workflow_stage_engine.py` /
`STAGE_MANIFEST.json` predate the silent-pass gate hardening — re-judge those against
current main if engine-stage wiring is wanted (see "Workflow linkage" in
[[contract-reflection-workflow]]).

## Status / coordination

- First must-have IMPLEMENTED + proven (above). Generator integrated (2026-06-10).
  Full-matrix generalization pending.
- The contract-reflection workflow files (`workflow/contract_reflection/*`,
  `workflow/contract-reflection/scripts/*`) are being **actively edited by another
  actor** (the semantic-freshness slice). The obligation-generator + validator-freshness
  work here touches the SAME files -> must be **sequenced**, not edited concurrently,
  to avoid the clobber hazard ([[project_classify_survivors_clobber]] is one instance).
- Already-present building blocks: requirement/obligation/contract_ref/reflection,
  `observed_equals_fl_expected`, byte-exact readback oracle (`test_pl_readback.py`),
  semantic_source_fingerprint (semantic stage only — to be generalized to all stages).
