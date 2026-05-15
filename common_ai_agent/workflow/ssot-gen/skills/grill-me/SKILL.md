---
name: grill-me
description: Sweep the SSOT for every TBD / unknown / null / missing-required field and capture each human decision through ATLAS QA tools. Use ask_user for immediate blockers and record_ssot_qa for deferred Review cards, so both paths appear as pending/approved in QA Review.
---

# Grill Me — SSOT-Gen Edition (TBD-driven QA Review)

Adapted from <https://github.com/mattpocock/skills> (`productivity/grill-me`,
MIT). The original interviews the user about a plan; this version is
tuned for the ssot-gen workflow: **find every TBD field in the SSOT and
capture it through ATLAS QA tools**, never via plain prose. Use
`record_ssot_qa` for deferred Review items and `ask_user` only when the
answer blocks the next SSOT write/import pass.

## Iron rules

1. **Use QA tools for every question.** Plain-text "what should I set X to?"
   is forbidden in this skill. Use `record_ssot_qa` when the decision can
   stay pending in QA Review while drafting continues. Use `ask_user` when
   the answer is an immediate blocker. Both paths must create QA Review
   records: pending first, approved after the user answers.

2. **Never invent values.** If a field's correct value can't be derived
   from (a) the canonical template `workflow/ssot-gen/rules/ssot-template.yaml`,
   (b) an existing IP's `*.ssot.yaml`, (c) an explicit user message in the
   conversation, you MUST create a QA Review item. Default values from the
   template are acceptable, but only after the user confirms via
   `ask_user` or answers a `record_ssot_qa` pending card.

3. **Status is part of the contract.** `record_ssot_qa` creates pending
   cards. `ask_user` creates pending cards while open and flips them to
   approved when the user submits. Do not leave an `ask_user` answer only in
   chat history when it belongs to SSOT.

4. **Auto-select is explicit pipeline behavior.** If the current mode is
   `auto-select`, `ask_user` may return an automatically chosen answer based on
   the `Suggest:` hint, recommended/default option, or first safe option. Treat
   that as approved QA evidence for smoke testing, but keep the generated QA
   card reviewable with `field_path`, `criteria`, `source_refs`, and a clear
   recommendation. Do not silently fill a value outside QA.

## Process

### 1. Locate the work-in-progress SSOT

- If the user named an IP, look for `<ip>/yaml/<ip>.ssot.yaml` (and
  `<ip>/<ip>.ssot.yaml` as legacy fallback) via `read_file` /
  `find_files`.
- If no draft exists, start from the canonical template at
  `workflow/ssot-gen/rules/ssot-template.yaml` and treat the entire file
  as TBD.
- If no IP name yet, the FIRST `ask_user` is:
  ```
  ask_user(
    question="What's the IP name?",
    kind="input",
    subtitle="Used as top_module.name and the directory prefix.",
  )
  ```

### 2. Sweep for TBD markers

Walk the YAML and collect a list of unresolved fields. A field is TBD if
ANY of these are true:

- value is `null`, `~`, empty string, or missing entirely
- value is `"<…>"` placeholder (template style), `"TBD"`, `"TODO"`,
  `"unknown"`, `"???"`
- there is a `# TODO`, `# TBD`, or `# confirm` comment on the line
- a required-by-schema field is absent (top_module.name, top_module.type,
  sub_modules[*].name, function_model.transactions[*].outputs,
  cycle_model.handshake_rules[*].rule, timing.target_clocks[*],
  quality_gates.signoff.evidence, register_map[*].address, etc.)

For each gap, record: `{section, path, current_value, allowed_values?,
why_required}`.

### 3. Walk the gaps in canonical SSOT order

§0 → §1 → … through the canonical SSOT sections. Within a section, parents before children
(e.g. `top_module.type` before `top_module.target.clock_freq_mhz`).
For each gap, emit one QA item. Keep the question *narrow* — one decision
per card. Prefer `record_ssot_qa(questions=[...])` for non-blocking gaps
so the user can answer them from QA Review. Use `ask_user(questions=[...])`
only for immediate blockers.

#### Question shape

For each TBD field, pick the right `kind`:

| Field type | `kind` | Options source |
|---|---|---|
| Enum (e.g. `top_module.type`, `interface.protocol`, `reset.polarity`) | `"single"` | template's allowed values; surface verbatim |
| Boolean (`ssot_gen: true/false`) | `"single"` | `["yes","no"]` |
| Multi-pick (interface list, irq sources, power domains) | `"multi"` | template enumerated values |
| Numeric (clock_freq_mhz, register address, bit width) | `"input"` | (no options) |
| Identifier / free name (sub-module name, signal name) | `"input"` | (no options) |
| Description text | `"input"` | (no options) |

Mandatory fields in each `record_ssot_qa` or `ask_user` question object:

- `question` — short, single-decision
- `subtitle` — cite §section + field path so the user sees where the
  answer lands, e.g. `"§3 register_map[2].access — RW lets firmware
  modify; RO is hardware-set; W1C clears on write of 1"`
- `options` — for `single`/`multi`, surface 2–6 *real* options; never
  include "Other" (the GUI auto-adds a custom note field)
- `kind` — see table above

#### Recommendation in the subtitle

Always include your *recommended* answer at the end of the subtitle,
prefixed with `Suggest: …`. The user can override via the custom-note
field. Recommendations follow these defaults:

- pick the simplest option that doesn't paint the design into a corner
- match adjacent IPs' style when one exists in the project
- prefer template defaults over inventing new values

### 4. Apply each answer

After `ask_user` returns or the user answers a pending QA card:

- Parse the result string (it comes back as `"selected: <label>"` or
  `"selected: …  ·  note: <free-form>"`).
- Apply the value to the in-memory SSOT model.
- Re-sweep for TBDs (a single answer may unlock or invalidate other
  fields, e.g. picking `top_module.type=memory` changes which sub-module
  templates apply).
- If the answer references something checkable in the codebase (a file
  path, an existing module name), verify with `read_file` /
  `find_files` before trusting it.

### 5. Stop conditions

- Every TBD resolved or recorded as a pending QA Review card → propose the
  next review/write step.
- User says "stop", "done", "skip the rest" → write the YAML with the
  remaining gaps left as `# TODO: confirm` comments.
- A single `ask_user` returns empty (no selection, no note) → treat as
  "use suggested default" and continue.

### 6. Report

When done, summarize:

- which sections are now fully filled
- which still have `# TODO: confirm`
- the next workflow step (typically `/gen-rtl` or another `/grill-me`)

## Anti-patterns (do not do)

- Asking "what do you want for §3?" without the field path or options.
- Presenting more than one decision per QA card.
- Using plain prose to elicit values when ATLAS QA tools are available.
- Filling a value yourself and noting it as "(needs confirm)" without
  asking the user — the whole point of this skill is to NOT silently
  default.
- Asking about fields that are already concretely set in the conversation
  or in `<ip>.ssot.yaml`.
