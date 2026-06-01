# Goal

objective: Upgrade the Andes external RTL DB LLM Wiki to practical production-use quality and verify that every discovered IP in `/Users/brian/Desktop/andes` is represented with searchable wiki pages, graph links, AST facts, document metadata, query coverage, reusable tests, and manual QA evidence.
status: in_progress

## Skills

- `omo:ulw-loop`: required by the user; drives durable criteria, evidence, tmux QA, and checkpointing.
- `omo:programming`: required because this task will likely edit Python generator/tests.
- `omo:lsp`: required for diagnostics on changed Python files after edits.
- `omo:review-work`: required final verification gate because this is significant implementation work.

## Bootstrap Notes

- `create_goal` tool was attempted and rejected because this thread still has a completed legacy Atlas goal. The binding goal above and OMO G002 subgoal are used for this follow-up.
- OMO G002 was added through `omo ulw-loop steer --kind add_subgoal`.
- Current durable plan path: `.omo/ulw-loop/019e7d68-e85d-7b32-af8c-a77d3f0b01ae/goals.json`.
- Ledger path: `.omo/ulw-loop/019e7d68-e85d-7b32-af8c-a77d3f0b01ae/ledger.jsonl`.

## Scope Size

- Surfaces: Andes RTL corpus, generated wiki markdown, `_rtl_facts` JSON sidecars, `_graph.json`, `wiki_query`, tests, docs/guide behavior.
- Expected files: Python generator and tests at minimum; possible docs if reusable guide gaps are found.
- Non-trivial multi-step work: plan agent required after context gathering.

## Execution Plan

- Plan-agent attempts for this follow-up timed out, so execution proceeds from direct corpus/repo inspection and the accepted G002 criteria.
- Wave 1: add RED pytest coverage for nested HDL roots, coverage manifest, empty-root diagnostics, and wiki_query visibility.
- Wave 2: implement a small production helper module for quality/coverage artifacts and keep the existing oversized builder as a minimal shim.
- Wave 3: rerun targeted tests, LSP diagnostics, and regenerate the real `/Users/brian/Desktop/andes/wiki`.
- Wave 4: run C001-C003 tmux QA scenarios, record OMO evidence with cleanup receipts, then run final reviewer audit.

## Corpus Baseline

- `/Users/brian/Desktop/andes` currently has 93 `hdl` directories: 84 with `.v/.sv` RTL and 9 empty roots.
- Existing wiki has only the 14 canonical top-level `_rtl_facts` sidecars and top-level pages; nested platform/VIP/core HDL roots need generated coverage pages/facts.
