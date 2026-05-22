# Triple-LLM `rv32i_min` Pipeline Comparison

_Generated: 2026-05-16T04:36:58Z_

Same SSOT input (`requirements.md`, RV32I 37 instructions, 3-stage), three model providers, identical pipeline
(`ssot-gen → fl-model-gen → cl-model-gen → equiv-goals → rtl-gen → tb-gen → sim → sim-debug → lint → coverage → goal-audit`).
**No manual fixes between stages.**

## Overall outcome

| Provider | Model | Overall |
|---|---|---|
| codex | `gpt-5.3-codex` | **blocked** |
| claude | `claude-cli` | **blocked** |
| cursor | `cursor-cli` | **blocked** |

## Per-stage status

| Stage | codex | claude | cursor |
|---|---|---|---|
| ssot-gen | pass | blocked | blocked |
| fl-model-gen | pass | — | — |
| cl-model-gen | pass | — | — |
| equiv-goals | blocked | — | — |
| rtl-gen | — | — | — |
| tb-gen | — | — | — |
| sim | — | — | — |
| sim-debug | — | — | — |
| lint | — | — | — |
| coverage | — | — | — |
| goal-audit | — | — | — |

## Artifact digests

| Metric | codex | claude | cursor |
|---|---|---|---|
| ssot_size | 43482B | — | — |
| ssot_sections | 36 | — | — |
| fl_check | pass | — | — |
| rtl_files | 6 | — | — |
| rtl_compile_errors | 2 | — | — |
| rtl_compile_warnings | ? | — | — |
| lint_errors | 4 | — | — |
| lint_warnings | 196 | — | — |
| sim_total | — | — | — |
| sim_pass | — | — | — |
| sim_mismatch | — | — | — |
| bins_hit | — | — | — |
| bins_total | — | — | — |
| equiv_goals | 56 | — | — |
| equiv_blocked | 0 | — | — |
| mismatch_classified | — | — | — |
| mismatch_owners | — | — | — |
| run_status | fail | blocked | blocked |

## Reading guide

- `sim_mismatch=0` and `lint_errors=0` is the smoke-test green line.
- `equiv_blocked > 0` means the SSOT had at least one sub_module without function_model_refs (or another goal-level blocker).
- `mismatch_owners` (when present) shows how `compare_fl_rtl_results.py` classified the failures: `tb-gen` vs `rtl-gen` vs `ssot-gen`.
- `run_status` is `pass` only if every stage in this run passed its validator. `blocked` means the pipeline stopped at a human-gate; `fail` means a validator hard-failed.

## Raw evidence

- `codex/run.json` — pipeline run trace
- `codex/rv32i_min/` — full IP tree (yaml/, model/, rtl/, tb/, sim/, lint/, cov/, verify/, logs/)
- `codex/rv32i_min/wiki/_graph.json` — auto-generated knowledge graph (read with `wiki_query(ip='rv32i_min')`)
- `claude/run.json` — pipeline run trace
- `claude/rv32i_min/` — full IP tree (yaml/, model/, rtl/, tb/, sim/, lint/, cov/, verify/, logs/)
- `claude/rv32i_min/wiki/_graph.json` — auto-generated knowledge graph (read with `wiki_query(ip='rv32i_min')`)
- `cursor/run.json` — pipeline run trace
- `cursor/rv32i_min/` — full IP tree (yaml/, model/, rtl/, tb/, sim/, lint/, cov/, verify/, logs/)
- `cursor/rv32i_min/wiki/_graph.json` — auto-generated knowledge graph (read with `wiki_query(ip='rv32i_min')`)
