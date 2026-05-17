# SSOT-Gen Pass Pipeline

How `ssot-gen` moves from "LLM produced something" to `status=pass`. This page
exists because the QUAD SPI run on 2026-05-17 only reached pass after a
deterministic→deterministic→LLM-repair→deterministic→validator chain, and the
behavior is not obvious from the stage name alone.

Related: [[full-flow-pipeline]] · [[rtl-gen-ssot-contract]] · [[workflow-ownership-and-boundaries]] · [[golden-todo-evidence]]

## State Machine

```text
LLM call                  → write artifact files
  ↓
deterministic_repair(canonicalize_llm_ssot)
  ↓
check_ssot_contract  ─pass→ stage_end pass
  ↓ fail
deterministic_repair(<validator failure reason>)   # one more try, same script
  ↓
check_ssot_contract  ─pass→ stage_end pass
  ↓ fail
LLM repair call  (log_stage = ssot-gen-repair-N)   # rewrites the YAML
  ↓
deterministic_repair(canonicalize_llm_repair_N)
  ↓
check_ssot_contract  ─pass→ stage_end pass
  ↓ fail / retries exhausted
human_gate
```

Authoritative implementation: `src/headless_workflow.py:2325-2382`
(`_run_ssot_generation`), `:2220-2275` (`_run_deterministic_ssot_repair`),
`:2218` final pass message `"SSOT contract valid"`.

## What Each Stage Does

### 1. LLM artifact write

`_call_llm("ssot-gen")` returns a `LLMResponse` whose
`parsed_artifacts` is the structured `files[]` array produced by
`parse_llm_artifacts`. `_apply_artifacts` writes those files to disk.

The LLM is asked to return one JSON object that contains an SSOT YAML payload
under `files[*].content`. In practice the model sometimes:

- emits a JSON object whose `content` string is truncated mid-quote
- emits the YAML directly without the JSON wrapper
- mixes markdown around the JSON

The headless runner accepts all three forms because the artifact parser is
tolerant. But the on-disk file may still be malformed YAML at this point —
that is the next layer's job.

### 2. Deterministic canonicalization

`_run_deterministic_ssot_repair(reason="canonicalize_llm_ssot")` runs:

```text
workflow/ssot-gen/scripts/repair_ssot_schema.py <ip> --root <root>
```

with a 60-second wall-clock timeout. The repair script:

- loads the SSOT YAML (folds wrapped expression continuation lines so PyYAML
  does not break on lines starting with `|`/operator characters — see
  BUG-021 in [[gpio-orchestrator-multiworker-run]])
- canonicalizes section order against `REQUIRED_ORDER`
- backfills derived APB helper signals from `registers.register_list`
  (BUG-020)
- backfills `function_model.transactions[*].outputs` from
  `output_rules` / `state_updates` so a parameterized APB width does not
  block (BUG-018)
- writes the repaired YAML back with wide line width

If the loader cannot read the file at all (for example because the LLM
emitted JSON-as-YAML and the first quoted scalar is truncated), the script
exits non-zero and `deterministic_repair_end status=fail` is logged.

Both successful and failed runs leave `logs/validators/repair_ssot_schema.log`
with stdout/stderr.

### 3. Validator gate

`_check_ssot_contract` runs `workflow/ssot-gen/scripts/check_ssot_disk.sh`
against the on-disk YAML. The validator is what produces the
`SSOT contract valid` message that downstream stages key off. It enforces:

- minimum required section keys
- non-empty `function_model.transactions`
- non-empty `cycle_model.pipeline` and `cycle_model.states`
- coverage gate references
- traceability anchors

The pass result is appended to `logs/headless_run.json` as
`stage="ssot-gen", status="pass", message="SSOT contract valid"`.

### 4. Single second deterministic retry

If the first canonicalization or the validator fails, the runner gives the
deterministic repair *one* more chance with the validator's failure message
as the `reason` field. This catches cases where the LLM output was almost
valid YAML and the repair script just needed a re-pass on the now-on-disk
file rather than the raw LLM blob.

This second attempt is gated by
`not validation.message.startswith("SSOT contract incomplete")` — pure
contract-completeness misses (missing whole sections) skip straight to LLM
repair because the deterministic script cannot invent missing semantics.

### 5. LLM repair pass

When deterministic repair cannot save the file, an LLM call is made with a
**different** prompt. The prompt includes:

- the current on-disk YAML, clipped to 30k chars
- the validator's failure log
- any human-gate JSON the previous attempt may have produced
- explicit JSON output schema: one object, `files[*].content` carries the
  complete repaired YAML, no markdown

This call is logged as `log_stage="ssot-gen-repair-{attempt}"` so trace
summaries can distinguish authoring spend from repair spend.

The number of LLM repair attempts is `self.ssot_repair_attempts`. Each
attempt is followed by a `canonicalize_llm_repair_{attempt}` deterministic
pass before re-running the validator.

### 6. Exhaustion → human gate

If all repair attempts fail, `_validate_ssot` writes a human-gate JSON under
`<ip>/review/decision_needed_pipeline_repeated_ssot_gen_mismatch.json` with
the validator output as evidence. The stage record is `status=human_gate`
with a blocker pointing at the gate JSON.

## Observed Run: QUAD SPI 2026-05-17

Times from `quad_spi_ctrl/logs/run_progress.jsonl`:

| t (UTC)             | event                                          | result |
|---------------------|------------------------------------------------|--------|
| 18:33:14            | ssot-gen llm_call_start                         | —      |
| 18:35:03 (+108s)    | ssot-gen llm_call_end                           | pass   |
| 18:35:03            | deterministic_repair_start canonicalize_llm_ssot| —      |
| 18:35:03            | deterministic_repair_end                        | fail (truncated quoted scalar at line 6) |
| 18:35:03            | deterministic_repair_start (validator reason)   | —      |
| 18:35:03            | deterministic_repair_end                        | fail (same YAML parse error) |
| 18:35:03            | ssot-gen-repair-1 llm_call_start                | —      |
| 18:38:12 (+188s)    | ssot-gen-repair-1 llm_call_end                  | pass   |
| 18:38:12            | deterministic_repair_start canonicalize_llm_repair_1 | —  |
| 18:38:12            | deterministic_repair_end                        | pass   |
| 18:38:13            | stage_end "SSOT contract valid"                 | pass   |
| 18:38:13            | run_end                                         | pass   |

Total wall time: 4:59. LLM time: 4:56 (108s + 188s). Deterministic
repair time: < 1s. Validator: < 1s.

Why the first canonicalization failed: the LLM emitted a JSON object whose
`files[0].content` string contained the SSOT YAML with escaped newlines
(`"top_module:\n  name: \"quad_spi..."`). The string was truncated mid-quote
(missing closing `"`), so PyYAML refused to load the file with
"found unexpected end of stream". The repair script reports its own load
error verbatim, which is why the second `deterministic_repair_start.reason`
field carries the YAML parser exception text.

Why the LLM repair worked: the repair prompt embeds the partial on-disk
YAML and the validator/parser error, then asks for a fresh complete YAML.
The repair model (same `gpt-5.3-codex` here) emitted the full YAML without
the JSON wrapper, and `canonicalize_llm_repair_1` accepted it.

## Run-Time Knobs

- `ATLAS_HEADLESS_LLM_TIMEOUT` — per-LLM-call timeout in seconds. Default
  `180`. The QUAD SPI run had to set `900` because the first attempt at the
  default kept hitting `real provider timed out after 180s` and retrying.
  Source: `src/headless_workflow.py:1134`. The LLM retry logic is at
  `:1378-1392`.
- `ssot_repair_attempts` — runtime field on `HeadlessWorkflowRunner`,
  controls how many LLM-repair iterations are allowed before human gate.
- `repair_ssot_schema.py` 60-second internal timeout — set in
  `_run_deterministic_ssot_repair` at `:2234`. Increase only if the schema
  size grows beyond what the script can canonicalize in 60s.

## Useful Failure Signatures

When the pipeline stalls in `ssot-gen`, the progress log signature tells you
what to fix:

| Signature                                                       | Owner / Fix |
|------------------------------------------------------------------|-------------|
| `llm_call_end ... error="real provider timed out after Ns"`     | bump `ATLAS_HEADLESS_LLM_TIMEOUT`; check provider contention ([[multi-user-worker-conflicts]] F4) |
| `deterministic_repair_end status=fail reason=canonicalize_llm_ssot` followed by `reason=<YAML parse error>` | LLM emitted malformed wrapper; LLM repair will run automatically. Watch for `ssot-gen-repair-1`. |
| Multiple `ssot-gen-repair-N` cycles ending in human gate         | LLM cannot recover from this artifact shape; either fix `repair_ssot_schema.py` to canonicalize the new pattern (preferred), or escalate to human review |
| `human_gate` with `missing function_model.transactions`          | SSOT contract truly incomplete; do *not* deterministic-repair, escalate to product/spec ([[human-review-and-escalation]]) |

## What This Page Is Not

This page documents the **success path** mechanism — how a single SSOT YAML
becomes valid. It does not cover:

- multi-IP scheduling on shared workers ([[multi-user-worker-conflicts]])
- downstream stale-oracle detection ([[gpio-orchestrator-multiworker-run]]
  BUG-008)
- the SSOT Q&A workbench UI ([[ssot-qa-workbench]])
- requirement-to-SSOT semantic gaps

Update this page when the LLM-repair contract or the deterministic
canonicalization rules change. Do **not** add per-IP run summaries here —
those belong in [[mini-cpu-rerun-20260517]] style reference-run pages.
