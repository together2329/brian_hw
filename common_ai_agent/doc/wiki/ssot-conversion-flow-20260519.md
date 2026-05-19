---
title: SSOT Conversion Flow — Upload → import_manifest → grill-me → to-ssot → validator
date: 2026-05-19
tags: [ssot, ssot-gen, import, to-ssot, grill-me, workflow, atlas-ui]
related:
  - ssot-import-multi-format-20260519
  - workflow-ownership-and-boundaries
  - run-mode-and-provenance-policy
  - golden-todo-evidence
---

# SSOT Conversion Flow

How an uploaded specification (pdf/pptx/docx/md/...) becomes a validated
`<ip>/yaml/<ip>.ssot.yaml`. The end-to-end pipeline is **deliberately split
into five stages** so a human can audit each intermediate artifact before the
next, heavier stage commits to it.

This page is the canonical "what happens after I click 📄 Import Doc" doc.
For the multi-format converter internals (markitdown subprocess, cursor-agent
vision), read [[ssot-import-multi-format-20260519]].

## TL;DR Pipeline

```
1. /api/ssot/import/upload        atlas_ui FastAPI handler (in-process)
   ─ .md + images + vision desc   <ip>/req/imports/*.md + originals/ + images/

2. /import --ip <ip> @<md>        ssot-gen worker (port 5621, import skill)
   ─ evidence-only                <ip>/req/import_manifest.json

3. /grill-me <ip>                 ssot-gen worker (grill-me skill, optional)
   ─ fill missing behavior facts  approved_qa appended to import_manifest.json

4. /to-ssot <ip>                  ssot-gen worker (to-ssot skill)
   ─ canonical SSOT synthesis     <ip>/yaml/<ip>.ssot.yaml

5. check_ssot_disk.sh <ip>        Stage gate validator
   ─ disk-truth, mode-aware       Exit 0 = SSOT stage PASS
```

The split exists because **vision OCR is fallible**, **import LLM judgement is
fallible**, and **grill-me decisions drive the actual RTL behaviour**. If any
single stage's output is wrong, we want it caught by the next reviewer (human
or validator) before it propagates into a 12-section yaml that downstream
workflows (rtl-gen, tb-gen, sim) will trust.

## Stage 1 — `/api/ssot/import/upload`

| Field | Value |
|---|---|
| Owner | atlas_ui FastAPI handler (`src/atlas_ui.py:9743 api_ssot_import_upload`) |
| Process | atlas_ui's own Python process — no worker dispatch |
| Trigger | SsotReviewPane's `📄 Import Doc` button (multipart) OR JSON body with base64 |
| Limits | ≤32 MiB / file, up to 16 files per request |

### Accepted extensions

Listed in `_SSOT_IMPORT_EXTENSIONS` (`src/atlas_ui.py:6836`):
`.pdf .pptx .docx .html .htm .md .txt .rst`. Passthrough (no conversion):
`.md .txt .rst`. Everything else flows through markitdown + per-format image
extraction.

### What gets written

```
<ip>/req/imports/
├── originals/<ts>_<idx>_<filename>      ← byte-exact original (audit/redo)
├── <ts>_<idx>_<base>.md                 ← markitdown text + vision section
└── images/<ts>_<idx>_<n>.<ext>          ← PyMuPDF / python-pptx / python-docx
```

### Response shape

```json
{
  "ok": true,
  "ip": "<ip>",
  "saved": [
    {
      "name": "...",
      "bytes": <int>,
      "original_path": "<ip>/req/imports/originals/...",
      "md_path":       "<ip>/req/imports/...md",
      "image_paths":   ["<ip>/req/imports/images/..."],
      "path":          "<ip>/req/imports/...md"
    }
  ],
  "paths":   ["<ip>/req/imports/...md"],
  "errors":  [],
  "command": "/import --ip <ip> @<path1> @<path2> ..."
}
```

The `command` field is the bridge to stage 2 — paste it into the orchestrator
chat (or trigger via dispatch) and ssot-gen worker takes over.

### What stage 1 does NOT do

- Does not write `import_manifest.json`.
- Does not touch `<ip>/yaml/`.
- Does not run any LLM beyond cursor-agent's per-image describe (3 sentences).

## Stage 2 — `/import --ip <ip> @<md>`

| Field | Value |
|---|---|
| Owner | ssot-gen worker, port 5621 (model glm-5.1) |
| Skill | `workflow/ssot-gen/skills/import/SKILL.md` |
| Trigger | orchestrator chat or pipeline dispatch with prompt starting `/import` |

### Inputs

- Stage-1 markdown files
- Existing RTL (`*.sv`/`*.v`/filelists) when re-importing legacy IP
- Legacy SSOT yaml or spreadsheets when migrating

### RTL evidence extraction checklist

LLM walks each source with this checklist (skill file is the authoritative copy):

- `module` declarations + top-module candidate
- parameter names/defaults
- clock/reset ports + reset polarity
- interface ports grouped by prefix/protocol
- register address constants + bitfields
- FSM state names + transition conditions
- memory / FIFO instances or arrays
- interrupt / error / debug / status signals
- comments that describe requirements

Stub / tieoff / placeholder modules are **not** behavioural proof.

### Output

```
<ip>/req/import_manifest.json
{
  "imported_paths":     ["<ip>/req/imports/...md", ...],
  "evidence_type":      "doc | rtl | legacy_yaml | filelist | other",
  "facts":              [ {field, value, source_path, source_line?}, ... ],
  "conflicts":          [ {field, values:[{source,value}, ...]}, ... ],
  "pending_qa":         [ {field, question, candidates?}, ... ],
  "approved_qa":        [],
  "recommended_next":   "/grill-me <ip>" | "/to-ssot <ip>"
}
```

End-of-run log line: `[SSOT IMPORT]` with ip, evidence paths, fact count,
pending QA count, next step. atlas_ui surfaces this in the worker run log.

### Stage 2's discipline

- Imported RTL is **structural evidence**, never production RTL. The to-ssot
  step writes a fresh `<ip>/yaml/...` — it does not preserve imported RTL
  paths blindly.
- Conflicts (e.g. two docs disagree on reset polarity) become QA cards rather
  than a guess.
- `auto-select` mode (orchestrator policy) lets the worker choose defaults
  for low-risk QA and record them as `(source: auto-select)` in
  `approved_qa` — preserved for audit but not interactive.

## Stage 3 — `/grill-me <ip>` *(optional but usually required)*

| Field | Value |
|---|---|
| Owner | ssot-gen worker (same port 5621), grill-me skill |
| Skill | `workflow/ssot-gen/skills/grill-me/SKILL.md` |
| Trigger | Stage 2 emits non-empty `pending_qa` and recommends grill-me, or user invokes directly |

### What it asks

Behaviour decisions that drive RTL but aren't present in the import:

- "Reset: sync release? async assert?"
- "Register write: immediate effect or next clock edge?"
- "Interrupt: level or edge? what clears it?"
- "FIFO overflow: drop, stall, or assert error?"
- "Counter rollover: wrap, saturate, or interrupt?"

The skill drives questions one at a time. In `auto-select` mode, it picks a
conservative default and records it under `custom.assumptions` so reviewers
see it before sign-off.

### Output

Same `import_manifest.json`, augmented:

```json
{
  ...,
  "approved_qa": [
    {"field":"...", "answer":"...", "source":"human|auto-select", "ts": ...}
  ],
  "pending_qa": []   ← emptied (or only contains items deferred to sign-off)
}
```

### Why stage 3 cannot be skipped silently

A spec sheet rarely has the behaviour resolution needed to write deterministic
RTL. If a `pending_qa` field still has no answer at stage 4, to-ssot stops
with `[SSOT QUESTION] -> user` rather than guess — which would force a
revisit anyway, and burn the to-ssot LLM tokens.

## Stage 4 — `/to-ssot <ip>`

| Field | Value |
|---|---|
| Owner | ssot-gen worker (same port 5621), to-ssot skill |
| Skill | `workflow/ssot-gen/skills/to-ssot/SKILL.md` |
| Trigger | `/to-ssot <ip>` command after stage 3, or after stage 2 if no QA needed |

### LLM context

- `workflow/ssot-gen/rules/ssot-template.yaml` — canonical section ordering
- `<ip>/req/import_manifest.json` — facts + approved QA + conflicts
- Existing `<ip>/yaml/<ip>.ssot.yaml` if present (preserve user-authored parts)
- Current orchestrator chat history if grill-me was interactive

### Sections it fills

`top_module`, `sub_modules`, `decomposition`, `parameters`, `io_list`
(clock/reset/interfaces with full port tables), `features` (trigger/datapath
/control/output), `dataflow`, `fsm`, `registers`, `interrupts`,
`function_model`, `test_requirements`, `coverage_goals.function`,
`coverage_goals.cycle`, `integration`, `timing`, `synthesis`, `dft`, `upf`,
`security`, plus `custom.assumptions` for grill-me auto-selections.

### Invariants enforced by the skill

- No default-stuffing for unknown behaviour fields → stop with `[SSOT
  QUESTION] -> user` instead.
- Imported RTL is consumed as evidence; only confirmed facts become SSOT
  fields. Production RTL paths are NOT preserved blindly.
- Output path is exactly `<ip>/yaml/<ip>.ssot.yaml` — never doubled
  (`<ip>/<ip>/...`).
- Scaffold output containing `<TBD>`, `<placeholder>`, or `TODO` is rejected
  and rewritten.

### Output + log

- `<ip>/yaml/<ip>.ssot.yaml`
- LLM emits a summary: written path, conversation-vs-default mix, remaining
  `# TODO: confirm` lines, validation result, recommended next (`/ssot-rtl
  <ip>`).
- End-of-run: `[SSOT HANDOFF] -> rtl-gen` (only on validator pass).

### RTL TBD feedback loop

If the current context contains `[SSOT TBD REPORT] -> ssot-gen` (sent by
rtl-gen when it can't proceed), to-ssot runs targeted enrichment instead of
rewriting the whole yaml:

1. Parse each `Missing` row (`yaml_path`, `needed_for`, `question`).
2. Patch only the named fields if the answer is available.
3. Record a pending QA for fields still unknown.
4. Emit a refreshed `[SSOT HANDOFF] -> rtl-gen`.

## Stage 5 — `check_ssot_disk.sh <ip>`

| Field | Value |
|---|---|
| Owner | `workflow/ssot-gen/scripts/check_ssot_disk.sh` |
| Run by | atlas_ui stage gate (auto) or operator (manual) |
| Modes | `starter` / `engineering` / `signoff` (mode tightens MIN_YAML and MIN_SECTIONS) |

### Validation checklist

- `<ip>/yaml/<ip>.ssot.yaml` exists on disk (file inspection, not LLM trust)
- File size ≥ `MIN_YAML` for the mode
- Top-level section count ≥ `MIN_SECTIONS`
- `yaml.safe_load` parses without exception
- Core sections present (`top_module`, `io_list`, `features`, ...)

### Outcomes

- **Exit 0** → SSOT stage marked PASS → downstream stages (fl-model-gen,
  cl-model, rtl-gen) become eligible.
- **Exit 1** → stage FAIL → file missing / too small / sections missing /
  YAML invalid. `_job_artifact_failure` blocks promotion. Operator must rerun
  /to-ssot or hand-edit the yaml.

### Why a disk-truth validator

"LLM said it wrote the file" was once trusted directly — and it lied on
corrupt yaml output that still printed a happy summary. This script replaces
that trust with `test -s <file>` + `yaml.safe_load`, so a corrupted output
can never silently promote the stage.

## How the stages chain in Atlas UI

```
[user] SsotReviewPane → 📄 Import Doc → upload spec.pdf
   │
   ▼
[atlas_ui in-process] stage 1 — ~30s (vision describe per image)
   │  returns command="/import --ip <ip> @<md>"
   ▼
[orchestrator chat OR direct dispatch] sends command to ssot-gen worker
   │
   ▼
[ssot-gen worker 5621] stage 2 — ~1-3 min
   │  writes <ip>/req/import_manifest.json
   ▼
[orchestrator] sees pending_qa, sends "/grill-me <ip>"   (skipped if none)
   │
   ▼
[ssot-gen worker 5621] stage 3 — 5-15 min depending on QA count
   │  appends approved_qa
   ▼
[user / orchestrator] sends "/to-ssot <ip>"
   │
   ▼
[ssot-gen worker 5621] stage 4 — ~3-8 min synthesis
   │  writes <ip>/yaml/<ip>.ssot.yaml
   ▼
[atlas_ui stage gate] stage 5 — check_ssot_disk.sh (~1s)
   │
   ▼
[Pipeline UI] SSOT stage = passed ✓
   │  fl-model-gen becomes eligible
```

## Separation principle (why not one big call)

- **Stage 1 vs 2**: vision OCR can mislabel diagrams. A human can fix the
  `## Extracted Images` block in the .md before /import promotes those
  descriptions to "facts".
- **Stage 2 vs 4**: import LLM's facts are claims about source text. to-ssot's
  yaml is a commitment about RTL behaviour. Splitting them lets a reviewer
  check `import_manifest.json` before the yaml is synthesised.
- **Stage 3 explicit**: behavioural decisions are recorded with `source:
  human|auto-select` so 6 months later someone can answer "why is reset
  async-assert?".
- **Stage 5 disk-truth**: stage gate trusts the filesystem, not the LLM's
  self-report.

## File index

| Purpose | Path |
|---|---|
| Upload handler | `src/atlas_ui.py:9743 api_ssot_import_upload` |
| markitdown wrapper | `src/atlas_ui.py:9527 _markitdown_convert` |
| cursor-agent vision | `src/atlas_ui.py:9555 _describe_image` |
| Multi-format converter | `src/atlas_ui.py:9595 _convert_upload_to_markdown` |
| Import skill | `workflow/ssot-gen/skills/import/SKILL.md` |
| Grill-me skill | `workflow/ssot-gen/skills/grill-me/SKILL.md` |
| To-ssot skill | `workflow/ssot-gen/skills/to-ssot/SKILL.md` |
| Canonical SSOT template | `workflow/ssot-gen/rules/ssot-template.yaml` |
| Disk-truth validator | `workflow/ssot-gen/scripts/check_ssot_disk.sh` |
| Stage gate hook | `src/atlas_api_jobs.py _job_artifact_failure (ssot branch)` |

## Export (reverse direction)

The forward flow above takes evidence -> markdown -> grill-me -> SSOT
yaml. The export endpoint provides the inverse direction: take the
canonical `<ip>/yaml/<ip>.ssot.yaml` and emit a human-readable
artifact for sign-off review.

| Endpoint | Effect |
|---|---|
| `GET /api/ssot/export?ip=<ip>&format=md` | Render Markdown |
| `GET /api/ssot/export?ip=<ip>&format=docx` | Render Word (python-docx) |
| `GET /api/ssot/export?ip=<ip>&format=html` | Render HTML (python-`markdown` wrapper around the md output) |

Output paths (idempotent; overwritten on each call):

- `<ip>/doc/<ip>_ssot.md`
- `<ip>/doc/<ip>_ssot.docx`
- `<ip>/doc/<ip>_ssot.html`

Implementation notes:

- Module-scope helpers in `src/atlas_ui.py`: `_ssot_yaml_path`,
  `_load_ssot_yaml`, `_ssot_to_markdown`, `_ssot_to_html`,
  `_ssot_to_docx`. Section order matches
  `workflow/ssot-gen/rules/ssot-template.yaml`.
- Markdown rendering is deterministic (yaml walker; no LLM); HTML is
  the same markdown wrapped via `markdown.markdown(..., extensions=
  ["tables","fenced_code","toc"])` with embedded CSS; docx walks the
  same canonical section list with python-docx (tables for
  list-of-dicts, bold-run definition lists for dict scalars).
- Unknown / unrecognized nested structures fall back to a fenced
  ```yaml``` block in markdown and a `Consolas` paragraph in docx so
  nothing is dropped silently.
- pdf is deferred: weasyprint is not installed on the bound Python
  3.9 environment. Users can convert html -> pdf via the browser
  print dialog if needed.

UI surface: workspace SSOT Review pane has a `📥 Export` select next
to `📄 Import Doc`; choosing a format navigates the browser to the
endpoint, which sets `Content-Disposition: attachment` so the file
downloads.

Test coverage: `tests/test_ssot_export.py` (helpers + endpoint, both
qa_timer_pure and quad_spi_ctrl, all three formats, plus bad-ip /
bad-format / missing-yaml paths).

## Related wiki

- [[ssot-import-multi-format-20260519]] — converter internals (markitdown,
  cursor-agent vision, per-format image extraction)
- [[workflow-ownership-and-boundaries]] — which workflow owns which artifact
- [[run-mode-and-provenance-policy]] — starter/engineering/signoff mode
  effect on MIN_YAML, MIN_SECTIONS, and approval gates
- [[golden-todo-evidence]] — TodoTracker semantics that the stage gate
  consumes
- [[atlas-pipeline-screen]] — where stage status renders for the user
