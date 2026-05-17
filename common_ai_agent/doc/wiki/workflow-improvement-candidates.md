# Workflow Improvement Candidates

Status: **open ideas, not decided design.** Captured 2026-05-17 after the
[[atcuart100-pipeline-run]] and the discussion around what to change
next. Each candidate below is a parking-lot entry: problem statement,
proposed shape, use cases, and decision questions. None has been
promoted to code or to a normative wiki page yet.

This page exists so the next session does not re-discover the same five
gaps. Promote a candidate to a dedicated page only after a real run
exercises the change.

Related: [[wiki-curation-policy]] · [[atcuart100-pipeline-run]] ·
[[ssot-gen-pass-pipeline]] · [[parallel-todo-sub-agent-workers]] ·
[[gpio-orchestrator-multiworker-run]]

## CAND-01 — Reference RTL Reuse Policy

### Problem

When an IP run starts with reference RTL in `req/imports/hdl/` (as
ATCUART100 did with the Andes 8-module source), the current workflow
ignores it entirely. The SSOT author has to manually re-extract module
names, port lists, register offsets, and CDC topology. ~30% of the
ATCUART100 SSOT-authoring effort was mechanical transcription of
information already present in the reference RTL.

### Use cases where reference RTL really matters

The "ignore reference, regenerate from scratch" rule
(per [[rtl-gen-ssot-contract]]) is correct for the LLM's RTL output —
existing RTL is evidence, not authority — but it does not say anything
about how to bootstrap SSOT from a reference. Cases where the reference
content is load-bearing:

1. **Legacy RTL extension.** "Add a CRC field to ATCUART100 LSR." The
   existing RTL is the contract everything else is built against; the
   change must preserve every observable behavior of the original. The
   reference RTL is the truth that the regenerated RTL must subsume.
2. **House style matching.** A team has a specific coding convention
   (signal naming, reset polarity, FSM encoding, comment header). The
   reference RTL is the only concrete record of that convention.
3. **Pin-compatible port.** Drop-in replacement of a vendor IP into an
   existing SoC. Top-level port list and timing must match exactly.
4. **Bug-fix-only iteration.** Existing RTL is mostly correct; only one
   bug in one module needs a fix. Regenerating from SSOT alone would
   introduce drift.
5. **Verification re-use.** Reusing an existing testbench against
   regenerated RTL requires the regenerated top-module ports to match
   the reference exactly.

### Proposed shape

Two scripts, both deterministic, both opt-in:

- `workflow/ssot-gen/scripts/seed_from_reference_rtl.py` — read
  `req/imports/hdl/*.v|*.sv`, emit `yaml/<ip>.ssot.partial.yaml` with
  `sub_modules[]`, `io_list.interfaces[].ports[]`, `parameters`,
  `integration.connections`, `registers.register_list[].offset` (from
  APB decode patterns). LLM/human only fills semantic gaps after.
- `workflow/rtl-gen/scripts/style_profile_from_reference.py` — extract
  a style profile (reset polarity, signal naming pattern, sync style)
  and inject it into the rtl-gen system prompt as authoring constraints.

For the "legacy extension" case (case 1), a third workflow may be
needed: `legacy-extend` instead of `rtl-gen`, where the LLM diffs
against the reference RTL rather than generating from scratch. This is
a bigger change and warrants its own candidate later.

### Decision questions

- Should `seed_from_reference_rtl.py` write to `yaml/.ssot.partial.yaml`
  (consumed by ssot-gen) or directly to `yaml/.ssot.yaml` (skipping the
  LLM for structural sections)?
- How does the style profile interact with the global coding rules in
  `coding_rules:` section of SSOT? Conflict policy?
- Does case 1 (legacy extension) need a dedicated `legacy-extend`
  workflow stage, or can it be a `rtl-gen` mode flag?
- Does the reference RTL become a `quality_gates.signoff.evidence`
  requirement when present (i.e., regenerated RTL must compile against
  the same testbench)?

### Related

- [[rtl-gen-ssot-contract]] — existing rule (reference is evidence not authority)
- [[deterministic-emit-stages]] — pattern for LLM-free workflow steps
- [[atcuart100-pipeline-run]] L1 — empirical motivation

---

## CAND-02 — Sectional SSOT-gen

### Problem

A production-grade SSOT for an 8-module peripheral is ~70 KB. The
current `ssot-gen` asks for the entire document in one LLM call. In the
ATCUART100 run, **5 of 5 providers failed** at this single-shot
attempt (codex truncate, kimi/deepseek HTTP 400, glm/claude envelope
mismatch). [[ssot-gen-pass-pipeline]] handles recovery from one
truncated attempt, but does not prevent the single-shot ceiling itself.

### Proposed shape

Split SSOT authoring into ~7 sections, each emitted by a separate LLM
call, then deterministically merged:

```text
section_1: top_module + io_list + parameters + clock_reset_domains
section_2: function_model.state_variables + transactions + invariants
section_3: cycle_model + fsm
section_4: registers + memory + interrupts + cdc_requirements + rdc_requirements
section_5: rtl_contract + integration + sub_modules connections
section_6: timing + power + security + error_handling + debug_observability
           + dft + synthesis + pnr + coding_rules + reuse_modules
section_7: test_requirements + quality_gates + traceability + workflow_todos
           + generation_flow
```

Each section is 8-15 KB, well within single-shot limits. Sections are
naturally independent enough to parallelize across providers
(codex writes section_2, glm writes section_4, etc.). Final merge is
deterministic concatenation plus a single `check_ssot_disk.sh` gate.

### Decision questions

- Section boundaries: are these seven the right split, or should
  function_model.transactions be further split (one transaction per LLM
  call)?
- Cross-section references (e.g., `function_model_refs` in
  `sub_modules` must match transaction ids in section_2) — handle by
  emit order, or by a second-pass deterministic linker?
- Failure isolation: if section_4 fails 3 times, does the whole run
  block, or can we partially commit sections 1-3 + 5-7 with section_4
  human-gated?
- Schema for partial section output — share with
  [[ssot-gen-pass-pipeline]] repair envelope, or new schema?

### Related

- [[ssot-gen-pass-pipeline]] — current single-shot + repair mechanism
- [[atcuart100-pipeline-run]] L1 — empirical motivation
- [[parallel-todo-sub-agent-workers]] — dispatcher for parallel section emit

---

## CAND-03 — Multi-LLM as Reviewer Pattern

### Problem

`parallel_todo_dispatch` distributes **different work** across N LLMs
(one packet per worker). It does not support the "same work, different
viewpoints" pattern: 1 author + N reviewers. The ATCUART100 run gave
the same SSOT prompt to 5 providers and got 4 redundant failures plus
1 partial draft. The reviewer-pattern would have been strictly more
useful.

### Proposed shape

```text
author_llm    : writes section / SSOT / RTL packet / TB scenario
reviewer_llm_1: reads (author_output + validator_schema) → emits FIX_CARDS
reviewer_llm_2: same, different model
reviewer_llm_3: same, different model
orchestrator  : dedup FIX_CARDS, auto-apply safe ones, present ambiguous ones
                to author/human, re-run validator
```

FIX_CARD example:

```json
{
  "card_id": "FIX-001",
  "target": "function_model.transactions[3].output_rules",
  "issue": "missing 'width' field on rule 'prdata_out'",
  "fix": "add width: 32",
  "confidence": "high",
  "rationale": "All other output_rules with port=prdata declare width: 32"
}
```

Reviewer LLMs produce short, structured output (no HTTP 400 from large
generation). Reviewer cost is small (claude-cli + glm-5.1 reading
12 KB section + emitting 1 KB FIX_CARDS each). Author keeps the
expensive role on the strongest provider.

### Decision questions

- Reviewer selection policy: do we always run all available reviewers,
  or select by cost/specialty?
- FIX_CARD schema standardization — JSONSchema or freeform?
- Auto-apply threshold: which confidence level allows auto-apply
  vs. needs human?
- Where do reviewer prompts live? Per-stage system prompt or a single
  shared "you are a critic" prompt?
- How does this compose with [[ssot-gen-pass-pipeline]] repair calls?
  Does a failed validator immediately trigger reviewers, or only after
  one repair attempt?

### Related

- [[parallel-todo-sub-agent-workers]] — different-work dispatcher
- [[ssot-gen-pass-pipeline]] — author + deterministic repair loop
- [[atcuart100-pipeline-run]] L4 — 5/5 redundant author failure motivation
- [[triple-llm-rv32i-experiment]] — earlier multi-LLM author experiment

---

## CAND-04 — Stage Repair Convergence Budget

### Problem

Only `ssot-gen` documents an explicit repair budget
(`ssot_repair_attempts` in [[ssot-gen-pass-pipeline]]). `rtl-gen`,
`tb-gen`, `sim-debug` have repair-N attempts in practice
(per gpio-orchestrator BUG-014/BUG-017) but no design page captures the
**convergence rule**: when do you stop iterating and escalate?

### Proposed shape

A workflow-level page `stage-repair-convergence.md` that defines:

- per-stage `max_repair_attempts` env vars (default + override)
- mismatch-signature stability detection: if the same set of failing
  goals (sorted goal_ids hash) repeats N times, halt and write
  `<ip>/review/decision_needed_pipeline_repeated_<stage>_mismatch.json`
- per-stage convergence-stuck signature library: which signatures are
  known infinite-loops vs. expected progress
- escalation chain: convergence stuck → owner-routed handoff →
  cross-stage feedback → human gate

### Decision questions

- One unified `MAX_REPAIR_ATTEMPTS` env var or per-stage knobs?
- Where is mismatch_signature computed? In `sim-debug`, or upstream?
- Convergence detection metric: same-signature count, or progress
  metric (e.g., warning count must strictly decrease)?
- Should the convergence rule be expressed in code
  (`_pipeline_repair_request` in headless_workflow) or in a config
  file that the workflow loads?

### Related

- [[ssot-gen-pass-pipeline]] — only stage with explicit budget today
- [[gpio-orchestrator-multiworker-run]] BUG-014 — majority-owner fix
- [[workflow-feedback-and-scheduling]] — retry_budget mention but no concrete rule
- [[orchestrator-worker-handoff]] — Review Decision Needed gate

---

## CAND-05 — Requirements Authoring Guide

### Problem

The only documented req spec is in `headless_workflow.py:1668`:

```python
if len(text.strip()) < 200 or PLACEHOLDER_RE.search(text):
    ...human_gate(requirements are incomplete)
```

That is: >= 200 chars and no `TBD|TODO|FIXME|PLACEHOLDER|STUB|MOCK`.
Nothing else. [[ssot-qa-workbench]] documents the UI for filling
ambiguous decisions but does not say what a *good req document* looks
like in the first place. Input quality directly determines output
quality, but the workflow does not teach the user how to write good
input.

### Proposed shape

A `requirements-authoring-guide.md` page with:

- minimal req structure: identity / interfaces / register map /
  FSM intent / coverage and quality intent
- bad examples (prose-only without machine-checkable behavior)
- good examples — link to ATCUART100 `req/atcuart100_requirements.md`
  as a worked reference
- rule: "anything that would force the LLM to invent must be in req or
  be flagged as `ask_user` later"
- machine pre-checks: a `req_lint.sh` that catches common omissions
  (no register table, no port direction, no clock domain mention)
  before SSOT-gen wastes tokens

### Decision questions

- Is the guide a static doc, or a generator (e.g.,
  `req_template.py --ip-class peripheral` writes a starter req)?
- How strict is the lint? Soft warnings or hard human_gate?
- Does the guide replace the `200 chars + no TBD` check, or extend it?
- Should the req be a YAML/structured format instead of free markdown?
  (Trade-off: usability vs. machine-readability)

### Related

- [[ssot-qa-workbench]] — UI for resolving SSOT ambiguity
- [[golden-todo-evidence]] — evidence-required policy
- [[atcuart100-pipeline-run]] — req drove this run
- [[wiki-curation-policy]] — same "what to capture" pattern, applied to req

---

## How to promote a candidate

When a real run validates or refutes a candidate:

1. Run the candidate against a concrete IP (use [[atcuart100-pipeline-run]] or a
   new scratch IP).
2. Update this page with the run anchor and what worked / failed.
3. If validated and reused, promote to a dedicated wiki page; demote
   this entry to a one-line pointer.
4. If refuted, leave it here with the failure note so future sessions
   do not re-attempt the same shape.

Until a candidate is exercised, it stays here, not in [[index]] reading
order.
