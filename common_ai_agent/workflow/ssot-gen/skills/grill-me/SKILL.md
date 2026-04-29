---
name: grill-me
description: Sweep the SSOT for every TBD / unknown / null / missing-required field and resolve each one with the ask_user tool so the answer is captured via a GUI question card. Use whenever a draft SSOT has gaps or the user says "grill me", "fill the SSOT", or "ask me what's missing".
---

# Grill Me — SSOT-Gen Edition (TBD-driven, ask_user-mandatory)

Adapted from <https://github.com/mattpocock/skills> (`productivity/grill-me`,
MIT). The original interviews the user about a plan; this version is
tuned for the ssot-gen workflow: **find every TBD field in the SSOT and
resolve it via the `ask_user` tool**, never via plain prose.

## Iron rules

1. **Use the `ask_user` tool for every question.** Plain-text "what should I
   set X to?" is forbidden in this skill — the Atlas UI renders `ask_user`
   calls as a GUI question card with options + a free-form note field, and
   that is the channel the user expects. The terminal UI also supports it.

2. **Never invent values.** If a field's correct value can't be derived
   from (a) the canonical template `workflow/ssot-gen/rules/ssot-template.yaml`,
   (b) an existing IP's `*.ssot.yaml`, (c) an explicit user message in the
   conversation, you MUST `ask_user`. Default values from the template are
   acceptable, but only after the user confirms via `ask_user`.

3. **One `ask_user` per gap, in dependency order.** Resolve §0 → §1 → §2 →
   … so later questions can use earlier answers. Do not batch-ask all
   gaps at once — the user picks one, agent re-evaluates the SSOT, then
   asks the next.

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
  sub_modules[*].name, register_map[*].address, etc.)

For each gap, record: `{section, path, current_value, allowed_values?,
why_required}`.

### 3. Walk the gaps in canonical SSOT order

§0 → §1 → … → §19. Within a section, parents before children
(e.g. `top_module.type` before `top_module.target.clock_freq_mhz`).
For each gap, emit ONE `ask_user` call. Keep the question *narrow* —
one decision per call.

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

Mandatory fields in the `ask_user` call:

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

After `ask_user` returns:

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

- Every TBD resolved → propose `/to-ssot` to write the YAML.
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
- Presenting more than one decision per `ask_user`.
- Using plain prose to elicit values when `ask_user` is available.
- Filling a value yourself and noting it as "(needs confirm)" without
  asking the user — the whole point of this skill is to NOT silently
  default.
- Asking about fields that are already concretely set in the conversation
  or in `<ip>.ssot.yaml`.
