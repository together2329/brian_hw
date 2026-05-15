# Karpathy LLM Wiki Pattern

Reference page summarizing Andrej Karpathy's LLM Wiki concept and how the
current `common_ai_agent/doc/wiki/` aligns to it. Captured 2026-05-16 so
future sessions can pick up the same vocabulary without re-searching.

Related: [[index]] · [[log]] · [[workflow-ownership-and-boundaries]] ·
[[deterministic-emit-stages]]

## What Karpathy's LLM Wiki Is

A markdown-only, three-layer personal knowledge base that an LLM agent
maintains. Core claim: you do not need RAG, vector embeddings, or a
graph DB — you need a structured directory of markdown, an index, a
log, and a schema document. The LLM does the bookkeeping; the human
directs analysis.

> The wiki is a persistent, compounding artifact. Rather than
> re-deriving knowledge at query time, synthesis accumulates.
> — Karpathy gist

## 3-Layer Architecture

```text
L1  raw/          immutable curated source documents
L2  wiki/         LLM-generated markdown (entity/topic/comparison/analysis)
                  + index.md (catalog) + log.md (append-only log)
L3  CLAUDE.md     schema/conventions document the LLM reads first
```

## Page Types

| Type | Purpose | Our equivalent |
|---|---|---|
| Entity | Concept/person/system page | `full-flow-pipeline`, `rtl-gen-ssot-contract` |
| Topic summary | Synthesized overview | `golden-todo-evidence`, `workflow-ownership-and-boundaries` |
| Comparison | When sources contradict | (not yet — candidate: provider/model comparison) |
| Source summary | Key takeaways from a single source | `arm-m0-min-pipeline-run` |
| Analysis | Answers to queries worth keeping | smoke-test result pages |

## Frontmatter (optional but recommended)

```yaml
---
title: <Page Title>
type: process | concept | rule | log | runbook | reference | run
tags: [pipeline, ssot, rtl-gen]
related: [common-ai-agent-map, workflow-ownership-and-boundaries]
updated: YYYY-MM-DD
confidence: high | medium | low      # optional
source_count: N                      # optional (raw/ docs cited)
---
```

Frontmatter unlocks Obsidian Dataview-style queries and a richer
`build_graph.py --check` (orphan/stale/contradiction detection).

## Cross-link syntax

`[[page-slug]]` everywhere. Cross-references are first-class — "the
connections between documents are as valuable as the documents
themselves."

## Operations

| Op | What | Our state |
|---|---|---|
| Ingest | Read raw source → write summary page → update index + log | Manual today; covered by `build_graph.py` indexing |
| Query | Search index → read pages → synthesize answer with citations | grep + Claude reading; OMC `wiki_query` MCP available |
| Lint | Detect contradictions, stale, orphan, broken refs, gaps | `build_graph.py --check` (broken refs only today) |
| Log | Append-only `## [YYYY-MM-DD] op \| description` entries | Have `log.md`; entry prefix not yet normalized |

## Index.md contract

- Sorted/grouped by category.
- One link per page + one-line summary.
- Optional metadata (date, source count).
- Must remain grep-friendly.

## Why this matters here

- We are already most of the way to Karpathy's model: markdown +
  `[[refs]]` + `index.md` + `log.md` + a schema document
  (`CLAUDE.md`/`AGENTS.md`/system prompts).
- The only meaningful gap is **frontmatter metadata** (tags, type,
  updated, related) so a deterministic index/lint can run without
  re-grepping.
- `workflow/wiki/build_graph.py` already emits `doc/wiki/_graph.json`
  with node/edge/broken-ref data — adding frontmatter unlocks
  type/tag/category queries without touching the rendered markdown.

## Open follow-ups (not done yet, parked here)

1. Add YAML frontmatter to all 14 pages (`type`, `tags`, `updated`,
   `related`).
2. Extend `build_graph.py` lint to detect orphan pages (no incoming
   links and not in `index.md`), stale pages (older than N days when
   `updated` exists), and missing cross-refs.
3. Normalize `log.md` entries to `## [YYYY-MM-DD] op | description`.
4. Try one comparison page (e.g. provider/model comparison) to exercise
   the Karpathy "comparison page" pattern.

## Sources

- Karpathy's gist — <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>
- VentureBeat: "Karpathy shares LLM Knowledge Base architecture that bypasses RAG" —
  <https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an>
- MindStudio: "What Is Andrej Karpathy's LLM Wiki?" —
  <https://www.mindstudio.ai/blog/andrej-karpathy-llm-wiki-knowledge-base-claude-code>
- Falconer Guides: "The enterprise LLM wiki: scaling Karpathy's pattern to your org" —
  <https://falconer.com/guides/enterprise-llm-wiki-karpathy>
- OMC `wiki` skill SKILL.md (local) —
  `~/.claude/plugins/cache/omc/oh-my-claudecode/4.13.5/skills/wiki/SKILL.md`
