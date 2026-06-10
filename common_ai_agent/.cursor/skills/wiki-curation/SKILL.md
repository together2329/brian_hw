---
name: wiki-curation
description: Update or use the common_ai_agent LLM wiki. Use when capturing durable project knowledge, adding runbooks, refreshing the wiki graph, or deciding where documentation belongs.
---

# Atlas Wiki Curation

The durable project memory is `doc/wiki/`, not ad-hoc root markdown.

## Read First

- `doc/wiki/index.md`
- `doc/wiki/wiki-curation-policy.md`
- `doc/wiki/karpathy-llm-wiki-pattern.md`

## Update Pattern

1. Add or update focused wiki pages under `doc/wiki/`.
2. Keep the first page paragraph useful for future agents.
3. Add the page to `doc/wiki/index.md` when it is important for navigation.
4. Refresh the graph when needed:

```bash
python3 workflow/wiki/build_graph.py
```

Do not store secrets, transient session state, or generated logs in the wiki.
