---

## name: to-ssot

description: Synthesize the current conversation context or approved Locked Truth bundle into a canonical SSOT YAML Design Spec projection, including source_refs, contract_refs, function_model, and cycle_model, and write it to /yaml/.ssot.yaml. Use when the user wants to convert a finished discussion or grill-me session into a concrete generator-ready SSOT/Design Spec YAML file.

# To SSOT

Take the current conversation context (typically the output of a `grill-me`
session) or the approved Locked Truth bundle under `<ip>/req/` and produce a
complete generator-ready Design Spec YAML file conforming to the project's
canonical SSOT template. Adapted from
[https://github.com/mattpocock/skills](https://github.com/mattpocock/skills) (`to-prd` / `to-issues`, MIT) —
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

## Locked Truth Projection Rule

`req/*.json` is the authority when it exists. `yaml/<ip>.ssot.yaml` is not the
authority; it is a generator-ready Design Spec projection of that authority.

When `<ip>/req/approval_manifest.json` exists:

- Read `approval_manifest.json`, `requirements_index.json`, `obligations.json`,
  `contract_refs.json`, `structural_contracts.json`,
  `behavioral_contracts.json`, and `evidence_plan.json` before writing YAML.
- Do not write or modify canonical `req/*.json` files from this skill.
- Add authority metadata under `custom.locked_truth_authority`; do not add a new
  top-level `authority:` key because the canonical SSOT top-level section set is
  fixed.
- Add projection coverage under `traceability.locked_truth_projection`.
- `traceability.locked_truth_projection.requirements`, `.obligations`,
  `.contract_refs`, `.structural_contracts`, and `.behavioral_contracts` must
  include **every** locked ID from the corresponding req JSON file. Do not put
  only the IDs you happened to use in one section.
- Project `structural_contracts.json` into `io_list` and clock/reset domains
  exactly: signal name, direction, width, clock/reset association, and
  sync/async timing metadata.
- Project `behavioral_contracts.json` into `function_model`, `cycle_model`,
  `fsm`/register behavior, `test_requirements`, and `quality_gates` using the
  decision tables, state/transaction rules, and stage checks from req/.
- Do not satisfy behavioral projection with anchor-only rows. Each behavioral
  contract needs a concrete machine-readable `function_model` row and a concrete
  machine-readable `cycle_model` timing/protocol row, or an explicit
  `cycle_model_waiver` when cycle timing is genuinely not applicable.
- When **all** locked behavioral contracts are cycle-waived/combinational (every
  contract is `cycle_model_waiver` or its locked decision table has no
  clock/cycle/reset/handshake/state vocabulary), the IP is purely combinational:
  author **no** `fsm` block, **no** `function_model.state_variables`, and **no**
  `function_model.transactions[*].state_updates`. Keep transactions
  combinational (decision_table when/then + output_rules). `verify_ssot` rejects
  a state-control FSM or architectural state for a combinational IP.
- Attach `source_refs`, `contract_refs`, and where useful `evidence_refs` to
  important Design Spec items.
- If the user explicitly wants direct RTL before FL/CL, record
  `quality_gates.rtl_gen.direct_rtl_allowed.approved: true` with a rationale.
  This does not waive locked contract projection or RTL evidence; it only tells
  downstream rtl-gen not to require executable FL/CL artifacts for that path.

Use this shape:

```yaml
custom:
  locked_truth_authority:
    kind: "locked_truth_projection"
    approval_manifest: "req/approval_manifest.json"
    bundle_sha256: "<approval_manifest.bundle_sha256>"
    projected_files:
      - "req/requirements_index.json"
      - "req/obligations.json"
      - "req/contract_refs.json"
      - "req/structural_contracts.json"
      - "req/behavioral_contracts.json"
      - "req/evidence_plan.json"

traceability:
  locked_truth_projection:
    requirements: ["REQ_..."]     # every ID from req/requirements_index.json
    obligations: ["OBL_..."]      # every ID from req/obligations.json
    contract_refs: ["C_..."]      # every ID from req/contract_refs.json
    structural_contracts: ["C_STRUCT_..."]  # every ID from req/structural_contracts.json
    behavioral_contracts: ["BC_..."]  # every ID from req/behavioral_contracts.json
```

For section items, use this shape:

```yaml
source_refs:
  requirements: ["REQ_..."]
  obligations: ["OBL_..."]
contract_refs:
  central: ["C_..."]
  behavioral: ["BC_..."]
  stage: ["DESIGN_...", "RTL_...", "TB_..."]
evidence_refs:
  planned: ["E_..."]
```

Existing sections remain valuable. Do not replace `io_list`, `registers`,
`function_model`, `cycle_model`, `test_requirements`, or `quality_gates` with a
single requirement table. Instead, project the locked truth into those sections
and preserve the trace. The full locked text remains in `req/`; the SSOT should
use IDs and source-backed design fields rather than duplicating every
requirement sentence verbatim.

If SSOT validation reports missing Preview fields while a locked truth bundle
exists, treat that as a projection gap, not as an immediate user-interview gap.
Resolve it from req/ first:

- `top_module.description` from requirement purpose/title/statement.
- `io_list.interfaces[].ports[]` from interface requirements, obligations, and
  contract_refs.
- `registers.register_list[]` from register/CSR requirements and contracts.
- `clock_reset_domains` from clock/reset requirements and obligations.
- `interrupts` from interrupt requirements.
- `test_requirements.scenarios[]` and quality gates from evidence_plan entries,
  obligations, behavioral_contracts, and pass_conditions.
- FSM, memory, child submodule, DFT, power, security, and transport features as
  explicit no-feature/external-owner/non-goal policies when req/ is silent.

Ask the user only when the locked req/ bundle is genuinely under-specified for
an RTL-affecting fact. Missing YAML sections alone are not proof that the truth
is missing; they may only mean the Design Spec projection has not been written
yet.

If `/import` was run first, use `<ip>/req/import_manifest.json`,
`<ip>/req/extracted_decisions.json`, `<ip>/req/imports/`, and
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
  note: filled / partial / missing. Sections grill-me typically resolves
   the user-facing behavior and interface anchors first; remaining signoff
   sections come from explicit requirements, approved assumptions, or
   conservative repair defaults that are visible in provenance.
4. **Use the Preview/validator YAML shape exactly.**
  - Top level is one YAML mapping. Do not wrap the document in `ssot:`,
   `sections:`, `spec:`, or markdown fences.
  - Use these exact top-level keys, in this order:
  `top_module`, `sub_modules`, `decomposition`, `rtl_contract`,
  `parameters`, `io_list`, `features`, `dataflow`, `function_model`,
  `cycle_model`, `clock_reset_domains`, `cdc_requirements`,
  `rdc_requirements`, `registers`, `memory`, `interrupts`, `fsm`,
  `timing`, `power`, `security`, `error_handling`,
  `debug_observability`, `integration`, `dft`, `synthesis`, `pnr`,
  `coding_rules`, `reuse_modules`, `custom`, `dir_structure`,
  `filelist`, `test_requirements`, `quality_gates`, `traceability`,
  `workflow_todos`, `generation_flow`.
  Do not add `authority` as a new top-level key. Put Locked Truth authority
  data under `custom.locked_truth_authority`.
  - Do not use legacy top-level aliases such as `interface`,
  `bus_interface`, `register_map`, `clock_reset`, `errors`, `debug`,
  `dv_plan`, or `verification_plan`.
  - SSOT Preview renders typed cards from `top_module.description`,
  `io_list.interfaces[].ports[]`, `function_model.transactions[]`,
  `cycle_model.pipeline[]`, `cycle_model.scenarios[]` or
  `function_model.scenarios[]`, `registers.register_list[]` or an
  explicit no-register policy, `fsm.states/transitions` or an explicit
  no-FSM policy, and `test_requirements.scenarios[]`. Treat these as
  required for a previewable engineering SSOT.
5. **Write executable workflow todos.** Preserve and enrich
  `workflow_todos.<stage>[]` as the downstream handoff ledger. Every
   executable item must include `id`, `content`, `detail`, `command`, `script`,
   `instructions`, `criteria`, `source_refs`, `priority`, and `required`.
   Use `command` for the ATLAS slash entrypoint (`/to-ssot <ip>`,
   `/gen-rtl <ip>`, `/ssot-tb <ip>`) and `script` for the deterministic
   workflow script that validates or expands that handoff. The todo detail and
   instructions must be IP-specific and source-backed; do not leave generic
   template text when import evidence exists. When Locked Truth exists,
   source these todos from `req/contract_refs.json`,
   `req/behavioral_contracts.json`, and `req/evidence_plan.json` where
   possible.
6. **Fill the YAML generically from the approved context.**
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
  - For every important interface, register field, transaction, cycle rule,
  test scenario, and quality gate, include `source_refs` and `contract_refs`
  when Locked Truth exists.
  - For every register field, include bit range, access, reset, description,
  reserved behavior, and write/clear side effects where applicable.
  - Split coverage into `coverage_goals.function` and
  `coverage_goals.cycle`; each must have target, model, bins, source_refs,
  classes, and descriptions.
  - Comments are optional; do not add `TODO` comments for behavior that
  rtl-gen needs. Ask/stop instead.
7. **Write the file.** Path is exactly `<ip>/yaml/<ip>.ssot.yaml` from the
  project root. Do not add a second `<ip>/` segment when the UI scope is
   already set to that IP; for `gpio`, the path is `gpio/yaml/gpio.ssot.yaml`,
   never `gpio/gpio/yaml/gpio.ssot.yaml`. Use `write_file`.
   Scaffold output containing `<TBD>`, `<placeholder>`, `TODO`, or a tiny
   template-only YAML is not user-authored content; replace it with the
   complete canonical SSOT. For a substantive existing SSOT, read it first
   and preserve user-authored facts while completing missing sections.
8. **Validate before final handoff.** Use the workflow validators:
   run `python3 "$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py" <ip> --root "$ATLAS_PROJECT_ROOT" --mode engineering`.
   `verify_ssot.py` also runs `check_ssot_disk.sh` and writes
   `<ip>/req/ssot_validation.json`. When Locked Truth is active, this verifier
   also gates that every req/obligation/contract/structural-contract ID appears in
   `traceability.locked_truth_projection` and that
   `custom.locked_truth_authority.bundle_sha256` matches the manifest.
   If validation fails, fix the YAML yourself and rerun. Do not run broad repair
   scripts as the default authoring loop; `/repair-ssot` is a manual rescue
   command. Do not run RTL/TB generators from ssot-gen.
9. **Summary.** After writing, list:
  - the path written
  - whether it was generated from Locked Truth or unlocked chat context
  - which sections came from conversation vs. template defaults
  - any `# TODO: confirm` lines that need follow-up
  - whether validation passed
10. **Suggest next steps.** Use `/gen-rtl <ip>` after the SSOT validates,
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
# SSOT / Design Spec — <ip_name>
# Generated: <iso-date> · source: locked truth projection + to-ssot
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
When Locked Truth exists, include `custom.locked_truth_authority` and
`traceability.locked_truth_projection` in their canonical section locations.

## Do NOT

- Do not rewrite existing user-authored prose; preserve their phrasing
in `description` fields where they gave one.
- Do not invent register addresses, bit positions, protocol timing, memory
depth, security transforms, DFT obligations, PPA targets, quality gates, or
expected outputs. Ask or record a clearly non-blocking assumption.
- Do not say the Design Spec is the source of truth. It is a projection from
Locked Truth when `req/approval_manifest.json` exists.
- Do not run code generators, deterministic fallback writers, Jinja2
expansion, RTL generation, TB generation, lint, or simulation. Those are
downstream workflows.
