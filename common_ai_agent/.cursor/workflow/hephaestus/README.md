# Hephaestus Workflow

Deep-worker behavior layer for `common_ai_agent`. Domain-agnostic. Model-agnostic.

```bash
python3 src/main.py -w hephaestus
# or pin a specific model:
python3 src/main.py -w hephaestus --model glm-5.1
python3 src/main.py -w hephaestus --model deepseek-chat
python3 src/main.py -w hephaestus --model gpt-5
```

## What this is

A behavior layer (`system_prompt_mode: "prepend"`) that adds five guardrails on top of the base Common AI Agent:

1. **Persistence** — do not stop at analysis; finish the task or escalate explicitly.
2. **Exploration-first** — read 3-5 files before the first edit on non-trivial tasks.
3. **Root-cause bias** — symptom patches are forbidden when the source is reachable.
4. **Three-attempt protocol** — three materially different approaches, then escalate.
5. **Evidence-based completion** — re-read after writes; capture exit codes and pass counts.

This workflow does NOT change tools, dispatch sub-workflows, or pin a model. It only changes how the agent persists, explores, fails, and finishes.

## Files

```
hephaestus/
├── workspace.json              workspace contract — env empty, model not pinned
├── system_prompt.md            entry contract; layered ON TOP of base prompt
├── plan_prompt.md              plan-mode addendum (explore → implement → verify → report)
├── compression_prompt.md       context compression rules (CLAIMED vs VERIFIED preserved)
├── README.md                   this file
└── rules/
    ├── forbidden-stops.md      stop patterns that are incomplete work
    ├── exploration-first.md    pre-edit reads, parallel dispatch, dig deeper
    ├── three-attempt-protocol.md  material difference, three-attempt cap, escalation
    ├── evidence-required.md    5-level evidence ladder, CLAIMED vs VERIFIED
    ├── instruction-priority.md priority order, AGENTS.md hierarchy
    ├── scope-discipline.md     exact-scope, ambition vs precision, anti-slop
    └── communication-style.md  opener blacklist, commentary cadence, 5-section final
```

All `rules/*.md` files are **auto-injected** into the agent's todo-rule context by `workflow/loader.py:patch_todo_rules()`. They appear as `## [<filename>]` blocks in the agent's working context. You do not need to reference them manually.

## Model selection

Resolution order (first match wins):

1. `--model <name>` CLI flag.
2. `LLM_BASE_NAME` env var.
3. `common_ai_agent`'s own defaults (typically from `.config` / `.env`).

This workflow's `workspace.json` deliberately leaves `env` empty — it never overrides model selection.

## Image reading

Image read uses the active multimodal LLM client by default. Leave
`IMAGE_READ_MODEL` unset when the selected `MODEL_NAME` / Azure deployment
already supports image input:

```
ENABLE_IMAGE_READ=true
# default: inherits MODEL_NAME
# IMAGE_READ_MODEL=
```

For a Windows/Azure SOC deployment, point both the active deployment and the
optional image-read override at the Azure deployment name:

```
LLM_PROVIDER=azure
AZURE_OPENAI_DEPLOYMENT=soc-sol-gpt-5.5
USE_RESPONSES_API=true
# Optional when the active deployment is already soc-sol-gpt-5.5:
IMAGE_READ_MODEL=soc-sol-gpt-5.5
```

Document imports also render PDF pages that contain figure captions and append
their image-read notes under `## Visual Evidence`. DOCX/PPTX imports use the
same path after conversion to PDF through LibreOffice/soffice. This catches
vector drawings and slide/page layouts that are not embedded raster images:

```
ATLAS_IMPORT_VISUAL_EVIDENCE=true
ATLAS_IMPORT_VISUAL_EVIDENCE_MAX_PAGES=100
ATLAS_IMPORT_VISUAL_EVIDENCE_SCALE=2.0
# Optional when soffice/libreoffice is not on PATH:
ATLAS_OFFICE_RENDERER_BIN=/path/to/soffice
```

## Why `@<file>` does not work in this agent

`common_ai_agent` is a **strict ReAct loop** — there is no `@-mention` pre-parser in `src/` or `core/`. File references must be explicit tool calls:

```
# Does NOT work (silently treated as plain text):
@src/main.py

# Works:
Action: read_file(path="src/main.py")
Action: read_lines(path="src/main.py", start=42, end=80)
Action: grep_file(pattern="def foo", path="src/")
```

If you want to "include" a file in the agent's context, ask Hephaestus to read it — it will issue the `read_file` Action and the contents land in the next observation.

## Auto-loaded rule injection — how it works

Looking at `workflow/loader.py:432`:

```python
def patch_todo_rules(ws: WorkspaceConfig, _base_rule_fn=None) -> None:
    # ...
    for f in sorted(ws.rules_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8").strip()
        if content:
            extra_parts.append(f"## [{f.stem}]\n{content}")
    extra = "\n\n".join(extra_parts)
    # ... appended to base todo rule
```

Every `.md` file in `rules/` is read at workspace load and appended to the agent's todo-rule context. The filename (without `.md`) becomes the section header. Order is alphabetical.

This means **adding a rule = dropping a `.md` file into `rules/`**. No registration step needed.

## Adding a new rule

```bash
echo "# My new rule\n\nRule body..." > workflow/hephaestus/rules/my-rule.md
```

The rule auto-loads on the next `python3 src/main.py -w hephaestus` start. To verify load:

```bash
python3 workflow/integrate.py -w hephaestus
```

## Verifying the workflow

```bash
cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent
python3 workflow/integrate.py -w hephaestus
# Expected: 13/13 PASS
```

## Not part of this workflow

- **No `dispatch_workflow`.** Hephaestus is a worker, not an orchestrator. If you need cross-workflow handoff (rtl-gen, tb-gen, sim, ...), use `mas-gen` or `architect` and let them dispatch.
- **No domain-specific tools.** Hephaestus does not enable Verilog tools, EDA tools, or hardware-specific helpers. Use the matching workspace for those.
- **No model pinning.** Pick the model at the shell — `--model` flag or `LLM_BASE_NAME` env.
