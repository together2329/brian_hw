# Andes RTL DB Wiki + RTL DB Pointer (2026-05-27)

> **Updated**: 2026-05-27
> **Scope**: Generated an LLM knowledge-graph wiki over the external Andes peripheral
> RTL corpus (`~/Desktop/andes`) and pointed ATLAS at it as the external "previous-project
> RTL DB" via `ATLAS_RTL_DB_WIKI`.
> **Related**: [[rtl-gen-ssot-contract]] · [[workflow-ownership-and-boundaries]] · [[karpathy-llm-wiki-pattern]]

## What

`~/Desktop/andes` is a corpus of silicon-proven Andes IP (UART, SPI, I2C, GPIO, PIT,
WDT, RTC, DMAC, AHB bus matrix, APB/LM/SPI bridges) plus the **AE210P** SoC platform
(~507 `.v` files). It now has an LLM wiki at `~/Desktop/andes/wiki/` that ATLAS can
query as reuse reference during RTL generation.

## How it was built

Reusable generator: `scripts/build_andes_rtl_db_wiki.py`.

```sh
python3 scripts/build_andes_rtl_db_wiki.py --build-graph        # default --andes-root ~/Desktop/andes
```

Per block (dir with `hdl/`) it parses module declarations + the top module's port
list, classifies the bus interface (APB / AHB / SPI / I2C + DMA/interrupt) from port
names, counts RTL, and matches `AndeShape_*` datasheet/RN PDFs. It emits one page per
block with YAML frontmatter (`id/title/type/tags/related`) and inline `[[wiki-link]]`s,
plus `index.md`, `rtl-inventory.md`, and an `ae210p` platform hub. Cross-links are
derived from bus tags + curated roles (APB peripheral → `atcapbbrg100`/`atcapbdec100`;
AHB block → `atcbmc200`; DMA-capable → `atcdmac100`; SPI ↔ AHB2SPI; everything → AE210P).
(Those `[[links]]` resolve inside the Andes wiki, not this one.)

`workflow/wiki/build_graph.py --wiki ~/Desktop/andes/wiki` then produces
`_graph.json` (**17 nodes, 108 edges, broken_refs=0**). Regenerate after the corpus
changes; `wiki_query(ip="rtl-db")` also lazy-rebuilds the graph.

## The RTL DB pointer

`.env` (gitignored — not committed):

```sh
ATLAS_RTL_DB_WIKI=/Users/brian/Desktop/andes/wiki
```

`core/tools.py::resolve_rtl_db_wiki()` reads it; `wiki_query(ip="rtl-db" | "andes")`
resolves the `wiki/` child and renders the graph; `_scaffold_ip` bakes the resolved
value into each new IP's `wiki/workflow-runbook.md` as the legacy-RTL link.

> **Activation:** the value is read from the environment at process start. The live
> ATLAS server / workers must be **restarted** to pick up the new `ATLAS_RTL_DB_WIKI`.

## Plugging in a *different* external wiki (override)

`wiki_query(ip="rtl-db")` never reads raw RTL — it reads a normalized
`<wiki_root>/_graph.json` (`wiki_graph.v1`: nodes with `id/title/tags/summary/path/
outgoing`). So the **lookup is identical across systems**; only the source→graph
conversion differs. When a foreign RTL DB has a non-ATLAS structure, plug it in with
two `.env` hooks (no ATLAS code change; same idiom as `ATLAS_SCM_UI_OVERRIDE`):

| Env | Effect |
| --- | --- |
| `ATLAS_RTL_DB_BUILDER=/abs/builder.py` | ATLAS runs `<builder> --wiki <root>` instead of `build_graph.py`; the builder understands the foreign structure and writes `<root>/_graph.json`. Contract + working sample: `scripts/example_external_rtl_db_builder.py`. |
| `ATLAS_RTL_DB_NO_REBUILD=1` | ATLAS reads an externally-produced `_graph.json` as-is and **never (re)builds or clobbers** it — for foreign wikis that ship their own graph (any pipeline), even when their source files look newer. |

Implementation: `core/tools.py::wiki_query` (rtl-db scope). Verified end-to-end by
`tests/test_wiki_query_tool.py` (`..._external_builder_override...`, `..._no_rebuild_trusts_shipped_graph`).

## Query

```sh
wiki_query(ip="rtl-db", topic="uart apb dma", depth=3)
wiki_query(ip="andes",  topic="atcspi200",    depth=3)
```

Verified: `resolve_rtl_db_wiki()` → `/Users/brian/Desktop/andes/wiki`; query returns the
matching block with links + summary.
