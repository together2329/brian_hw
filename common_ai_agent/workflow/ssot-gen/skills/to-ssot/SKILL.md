---
name: to-ssot
description: Synthesize the current conversation context (and codebase understanding) into a canonical SSOT YAML, including function_model and cycle_model, and write it to <ip>/yaml/<ip>.ssot.yaml. Use when the user wants to convert a finished discussion or grill-me session into a concrete SSOT YAML file.
---

# To SSOT

Take the current conversation context (typically the output of a `grill-me`
session) and produce a complete SSOT YAML file conforming to the project's
canonical template. Adapted from
<https://github.com/mattpocock/skills> (`to-prd` / `to-issues`, MIT) —
issue-tracker output replaced with a YAML write, story breakdown replaced
with the SSOT section schema.

This skill **does not interview the user** — synthesize what you already
know from the approved Plan Mode / grill-me context. If a field affects
RTL behavior and is unknown, do not invent it and do not hide it behind a
template default. Stop with `[SSOT QUESTION] -> user` or record a
non-blocking conservative assumption in `custom.assumptions`.

Approved QA may come from a human answer or from explicit `auto-select` mode.
When it came from auto-select, preserve the fact in `custom.assumptions` or the
handoff summary so reviewers can audit the generated SSOT before signoff.

If `/import` was run first, use `<ip>/req/imports/` and
`<ip>/wiki/import-evidence.md` as evidence. Do not treat imported RTL as the
production output of this workflow; convert only the confirmed facts into SSOT
fields.

`/to-ssot` is an execution step. Do not call `todo_write` here; it is
Plan Mode only and will be rejected in Normal mode. If progress tracking is
useful, use a short prose ledger or `todo_add`, then immediately read/write
the SSOT and run validation.

## RTL TBD Feedback Mode

If the current context contains `[SSOT TBD REPORT] -> ssot-gen`, run targeted
enrichment instead of rewriting the whole SSOT:

1. Parse each `Missing` row: `yaml_path`, `needed_for`, `question`, and
   `current_rtl_action`.
2. Read the existing `<ip>/yaml/<ip>.ssot.yaml` once.
3. Patch only the named YAML fields when the missing fact is available from
   the conversation, requirements, imported documents, or approved QA.
4. If the fact is still unknown, record a pending QA item for that exact
   `yaml_path` and `needed_for` instead of inventing a value.
5. Validate the patched SSOT and emit a refreshed `[SSOT HANDOFF] -> rtl-gen`
   with `Resolved RTL TBD rows: N` and any `Pending QA rows: ...`.

## Process

1. **Locate the canonical template.** Read
   `workflow/ssot-gen/rules/ssot-template.yaml` to confirm the section
   ordering and field names you must use. (It's also embedded in the
   ssot-gen system prompt.)

2. **Resolve the IP name.** Take it from the latest user message, an
   existing `<ip>/` directory, or the first `top_module.name` referenced
   in conversation context. Refuse if the name is ambiguous — ask the
   user once.

3. **Sketch the section map** internally. For each canonical section,
   note: filled / partial / missing. Sections grill-me typically
   resolves: 0, 1, 2, 3, 4, 5, 6, 7. The remaining 12 (synthesis,
   timing, DFT, UPF, integration, technology, documentation, etc.) come
   from defaults unless the conversation explicitly addressed them.

4. **Fill the YAML generically from the approved context.**
   - Do not use IP-specific fixed templates.
   - Required behavior fields must come from the conversation, local requirements, or explicit assumptions.
   - List sections preserve the order grill-me elicited them in.
   - Include enough detail for downstream generic workflows:
     interfaces, parameters, memories, registers/no-CSR policy, interrupts,
     function_model transactions/invariants, cycle_model latency/handshake/
     pipeline rules, FSM states/transitions, feature triggers/datapaths/
     outputs, timing/power/security/error/integration/DFT/synthesis
     constraints, reset defaults, error behavior, test scenarios, expected
     results, scoreboard checks, coverage goals, quality gates, and traceability.
   - For every interface, include machine-readable protocol/timing/handshake
     rules in addition to ports. Port declarations alone are not enough.
   - For every register field, include bit range, access, reset, description,
     reserved behavior, and write/clear side effects where applicable.
   - Split coverage into `coverage_goals.function` and
     `coverage_goals.cycle`; each must have target, model, bins, source_refs,
     classes, and descriptions.
   - Comments are optional; do not add `TODO` comments for behavior that
     rtl-gen needs. Ask/stop instead.

5. **Validate before writing final handoff.** Use the workflow validator:
   `workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>` after writing, or
   an equivalent YAML parse/structure command before finalizing. If
   validation fails, fix the YAML and rerun. Do not run RTL/TB generators
   from ssot-gen.

6. **Write the file.** Path is exactly `<ip>/yaml/<ip>.ssot.yaml` from the
   project root. Do not add a second `<ip>/` segment when the UI scope is
   already set to that IP; for `gpio`, the path is `gpio/yaml/gpio.ssot.yaml`,
   never `gpio/gpio/yaml/gpio.ssot.yaml`. Use `write_file`.
   Scaffold output containing `<TBD>`, `<placeholder>`, `TODO`, or a tiny
   template-only YAML is not user-authored content; replace it with the
   complete canonical SSOT. For a substantive existing SSOT, read it first
   and preserve user-authored facts while completing missing sections.

7. **Summary.** After writing, list:
   - the path written
   - which sections came from conversation vs. template defaults
   - any `# TODO: confirm` lines that need follow-up
   - whether validation passed

8. **Suggest next steps.** Use `/ssot-rtl <ip>` after the SSOT validates,
   or another `/grill-me` round if blocking behavioral fields are missing.

## Bounded execution rule

`/to-ssot` must make forward progress with real file tools. The allowed
discovery budget for one run is:

- read the canonical template at most once;
- read the existing `<ip>/yaml/<ip>.ssot.yaml` at most once;
- read the validator at most once, only if its requirements are not already
  included in the prompt;
- then the next tool action must be `write_file`, `replace_in_file`, or
  `run_command` validation if the file was already complete.

If an existing SSOT is substantive, prefer a targeted patch over rewriting the
whole file. Insert or replace only the missing/weak canonical sections, preserve
approved facts, then run the exact validator. Re-reading the same template or
same SSOT after identifying the missing section list is a workflow failure; use
that turn to write or patch the file instead.

For large YAML outputs, do not narrate the entire file in prose first. Emit the
file tool call directly. Validation output is the proof, not an explanation of
why the YAML should pass.

## Output template (header)

```yaml
# =============================================================================
# SSOT — <ip_name>
# Generated: <iso-date> · source: grill-me + to-ssot
# =============================================================================

top_module:
  name: "<ip_name>"
  version: "1.0"
  type: "<dma|cpu|accelerator|bus|peripheral|memory>"
  description: "<one-sentence purpose>"
  target:
    technology: "generic"
    clock_freq_mhz: 500
```

(Continue with the remaining canonical sections from `ssot-template.yaml`.)

## Do NOT

- Do not rewrite existing user-authored prose; preserve their phrasing
  in `description` fields where they gave one.
- Do not invent register addresses, bit positions, protocol timing, memory
  depth, security transforms, DFT obligations, PPA targets, quality gates, or
  expected outputs. Ask or record a clearly non-blocking assumption.
- Do not run code generators, deterministic fallback writers, Jinja2
  expansion, RTL generation, TB generation, lint, or simulation. Those are
  downstream workflows.
