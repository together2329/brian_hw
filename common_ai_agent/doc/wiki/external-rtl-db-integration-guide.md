# External RTL DB integration guide

Use this when another RTL corpus should become an optional `external-db` source for
agent reuse/reference queries.

## Directory-shaped DB

Preferred simple layout:

```text
<db>/
  <ip>/
    hdl/        # .v/.sv/.vh/.svh
    docs/       # optional PDFs, markdown, datasheets
    DOCS/       # optional alternate docs directory
  wiki/
```

Build a wiki and graph:

```sh
python3 scripts/build_andes_rtl_db_wiki.py --andes-root <db> --build-graph
# If using a generic builder contract, support:
#   <builder> --wiki <db>/wiki
python3 workflow/wiki/build_graph.py --wiki <db>/wiki
```

Useful generated content:

- `<db>/wiki/<ip>.md` — block summary, links, docs/datasheet references.
- `<db>/wiki/_rtl_facts/<ip>.json` — AST-level `module`, `port`, `parameter`, `fsm`,
  `datapath`, `register`, `memory`, `clock`, and `reset` facts.
- `<db>/wiki/_graph.json` — normalized graph consumed by `wiki_query`.

Enable:

```sh
export ATLAS_EXTERNAL_DB_WIKI=<db>/wiki
# legacy alias:
export ATLAS_RTL_DB_WIKI=<db>/wiki
```

Disable by unsetting those variables or by not loading the `external-db` skill/config.
Use `ATLAS_EXTERNAL_DB_NO_REBUILD=1` or `ATLAS_RTL_DB_NO_REBUILD=1` when the shipped
`_graph.json` must be trusted as-is.

Query:

```sh
wiki_query(ip="external-db", topic="uart apb module port register", depth=3)
wiki_query(ip="external-db", topic="fsm datapath memory clock reset docs datasheet", depth=3)
```

## Full adapter

When the corpus is not directory-shaped, keep ATLAS unchanged and provide an adapter:

```sh
export ATLAS_EXTERNAL_DB_BUILDER=/abs/build_foreign_db.py
# or legacy:
export ATLAS_RTL_DB_BUILDER=/abs/build_foreign_db.py
```

Builder contract: ATLAS invokes `<builder> --wiki <wiki_root>`; the builder writes
`<wiki_root>/_graph.json` and any markdown/sidecars it wants.

For complete ownership of lookup:

```sh
export ATLAS_EXTERNAL_DB_QUERY=/abs/query_foreign_db
# or legacy:
export ATLAS_RTL_DB_QUERY=/abs/query_foreign_db
```

Query contract: ATLAS writes `{ip, topic, depth, max_nodes}` JSON to stdin and returns
the command's stdout verbatim. The adapter may use files, SQL, HTTP, vector search, or
another transport.
