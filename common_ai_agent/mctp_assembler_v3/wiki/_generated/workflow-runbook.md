# mctp_assembler_v3 — Workflow Runbook

Self-contained, executable flow for IP `mctp_assembler_v3`. The full workflow engine is copied into `../workflow/` at scaffold time — every stage's scripts, prompts, `system_prompt.md`, rules, and todo templates, plus the shared `scripts/`/`prompts/` and the flow guides. The IP runs on its own, with no dependency on the central checkout's project wiki. Run commands from the **project root** (the dir containing `mctp_assembler_v3/`).

## Pointers (all in-IP — only the RTL DB is an external link)
- **Stage knowledge graph:** [[workflow-stages]] — per-stage how-to (SSOT structure, lint/sim method, scripts, prompts) as a queryable graph (`wiki_query(ip="mctp_assembler_v3")`).
- **Flow guides (copied):** [`../workflow/GUIDE.md`](../workflow/GUIDE.md) · [`../workflow/COMMON_ENGINE_FLOW.md`](../workflow/COMMON_ENGINE_FLOW.md)
- **Per-stage system prompts (copied):** `../workflow/<stage>/system_prompt.md`
- **This IP's wiki graph:** [`_graph.json`](./_graph.json) · [`index.md`](./index.md)
- **Previous-project RTL DB (external link):** _not configured_ — set `ATLAS_RTL_DB_WIKI` in `.config` to a prior project's RTL wiki (dir or .md) to link reference designs here.

## Flow

```
SSOT → FL-Model → RTL → TB → SIM → LINT → (SYN → STA → PNR → STA-POST)
```

### SSOT · `ssot-gen`
Single Source of Truth from spec/import evidence.

- **Scripts:** `workflow/ssot-gen/scripts/`
- **Run:** `python3 workflow/ssot-gen/scripts/check_ssot_disk.sh mctp_assembler_v3`
- **Outputs:** yaml/mctp_assembler_v3.ssot.yaml

### FL-Model · `fl-model-gen`
Functional/reference model + equivalence goals from SSOT.

- **Scripts:** `workflow/fl-model-gen/scripts/`
- **Run:** `python3 workflow/fl-model-gen/scripts/check_fl_model_artifacts.py mctp_assembler_v3 --root .`
- **Outputs:** model/, equivalence goals

### RTL · `rtl-gen`
Synthesizable RTL authored from SSOT (+ FL equivalence).

- **Scripts:** `workflow/rtl-gen/scripts/`
- **Run:** `python3 workflow/rtl-gen/scripts/check_rtl_disk.sh mctp_assembler_v3`
- **Outputs:** rtl/mctp_assembler_v3.sv, list/mctp_assembler_v3.f, rtl/rtl_authoring_provenance.json

### TB · `tb-gen`
cocotb/pyuvm testbench from SSOT test_requirements.

- **Scripts:** `workflow/tb-gen/scripts/`
- **Run:** `python3 workflow/tb-gen/scripts/sim.sh mctp_assembler_v3`
- **Outputs:** tb/cocotb/test_mctp_assembler_v3.py, tb_manifest.json

### SIM · `sim`
Compile + run simulation, scoreboard, report.

- **Scripts:** `workflow/sim/scripts/`
- **Run:** `python3 workflow/sim/scripts/run_sim.py mctp_assembler_v3 --root .`
- **Outputs:** sim/ (waves, logs, results)

### LINT · `lint`
RTL lint — fix errors/warnings, emit report.

- **Scripts:** `workflow/lint/scripts/`
- **Run:** `python3 workflow/lint/scripts/dut_lint_report.py mctp_assembler_v3 --root .`
- **Outputs:** lint/ (lint report)

## Signoff stages
`coverage`, `syn`, `sta`, `pnr`, `sta-post` scripts are copied under `workflow/<stage>/scripts/` as well; drive them after SIM/LINT pass.

## Provenance & versioning
RTL/TB/SIM runs must reference immutable artifact versions (`rtl/rtl_authoring_provenance.json`, etc.). Do not overwrite old run results; new SSOT/RTL/TB gets new downstream runs.

## Wiki ownership
- Refresh-owned pages live under `wiki/_generated/`.
- User-authored development notes belong under `wiki/user/` or non-conflicting root `wiki/*.md` pages.
- `/refresh-wiki` overwrites only `wiki/_generated/`; it never overwrites user-authored pages.

