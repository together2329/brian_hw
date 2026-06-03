---
title: LLM Wiki And Knowledge Graph Discussion (2026-06-02)
type: reference
tags: [llm-wiki, knowledge-graph, triples, external-db, domain-knowledge]
updated: 2026-06-02
related: [karpathy-llm-wiki-pattern, andes-rtl-db-wiki-20260527, external-rtl-db-integration-guide, wiki-curation-policy]
---

# LLM Wiki and Knowledge Graph Discussion (2026-06-02)

Captured from a user Q&A on 2026-06-02 about whether LLM Wiki, LLM-generated
knowledge graphs, triples, and external DB tools are meaningfully different and
useful for domain knowledge management.

Related: [[karpathy-llm-wiki-pattern]] · [[andes-rtl-db-wiki-20260527]] ·
[[external-rtl-db-integration-guide]] · [[wiki-curation-policy]]

## Core Answer

LLM Wiki and LLM-generated knowledge graphs overlap, but they are not the same
thing.

```text
LLM Wiki          = editable human/agent-readable markdown knowledge layer
Knowledge Graph   = node/edge/triple index for relationship search and reasoning
```

The practical pattern is a hybrid:

```text
raw source        = final authority
LLM Wiki page     = explanation, summary, decision, runbook, caveat
Knowledge Graph   = index of page/entity relationships
query tool        = agent interface before doing work
lint/check        = stale link, broken reference, fabrication guard
```

## Terms

```text
node + edge + node = triple
subject --predicate/edge--> object = triple
```

Examples:

```text
ATCUART100 --uses_bus--> APB
ATCUART100 --has_register--> oscr_reg
oscr_reg  --belongs_to--> register_map
```

In triple form:

```text
(ATCUART100, uses_bus, APB)
(ATCUART100, has_register, oscr_reg)
(oscr_reg, belongs_to, register_map)
```

The edge is the relationship label (`uses_bus`, `has_register`,
`belongs_to`). The nodes are the things connected by that relationship.

## Difference From RAG

Classic RAG is usually query-time reconstruction:

```text
question -> retrieve chunks -> synthesize answer
```

LLM Wiki is accumulated synthesis:

```text
source/log/doc -> LLM writes linked markdown page -> index/log/graph update
question -> read wiki page/graph result -> answer -> preserve important result
```

The useful shift is that repeated domain understanding gets compiled into a
persistent knowledge layer instead of being re-derived from raw chunks every
time.

## Difference From Pure Knowledge Graphs

Pure KG systems optimize for structured relation queries and graph reasoning.
They often store triples in a graph DB, JSON graph, or GraphRAG index. That is
good for path finding and relationship traversal, but it can be hard for humans
to inspect, correct, and enrich with design rationale.

LLM Wiki keeps markdown as the primary editable artifact. A graph can be
derived from it (`_graph.json`) and used by tools such as `wiki_query` or
`external_db_query`, but the page remains the durable explanation layer.

## Domain Knowledge Management Usefulness

This approach is useful when:

- the domain has many recurring entities, rules, exceptions, and relationships;
- the same questions recur across projects or IPs;
- raw documents are too large to reread every time;
- agents must check prior art before authoring new artifacts;
- decisions, caveats, and known issues matter as much as facts.

For RTL/IP work, the pattern lets an agent consult external prior art before
generating new RTL:

```text
Andes RTL corpus
-> generated wiki pages + _rtl_facts JSON
-> _graph.json
-> external_db_query(topic="uart apb register", depth=3)
```

The agent can then see conventions such as ports, registers, datapaths, clocks,
resets, and related blocks without reading every raw source file first.

## Risk Boundary

Do not treat an LLM-built wiki or graph as the final truth source. It is a
search and synthesis layer over raw sources.

High-value use:

```text
raw source remains authoritative
wiki summarizes and links
graph indexes relationships
tool cites the page/path/fact before reuse
```

Dangerous use:

```text
LLM creates graph -> team treats graph as truth -> stale or fabricated edge ships
```

The guardrail is citation and rebuild discipline: every important external DB
claim should trace back to a `wiki_query` / `external_db_query` result and then
to the underlying page or source.

## Service Landscape

This space exists, but it is still early and mixed. Current shapes include:

- Obsidian plugins that generate or query wiki pages from a vault.
- MCP servers that expose markdown/wiki knowledge to agents.
- team knowledge services that store typed facts, decisions, artifacts, and open
  questions for agent retrieval.
- enterprise AI search over Confluence/Notion/Glean-style stores, which is
  adjacent but not the same as an LLM-maintained wiki.

The local ATLAS pattern is closest to:

```text
agent-native local LLM Wiki + derived graph index + dedicated query tools
```

Relevant local tools:

- `wiki_query`: project/IP/wiki graph query.
- `external_db_query`: dedicated external reference DB query, wrapping the
  external DB wiki scope.

