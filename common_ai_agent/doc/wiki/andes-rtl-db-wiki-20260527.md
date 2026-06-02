# Andes RTL DB Wiki + External DB Pointer (2026-05-27)

> **Updated**: 2026-05-27
> **Scope**: Generated an LLM knowledge-graph wiki over the external Andes peripheral
> RTL corpus (`~/Desktop/andes`) and documented how ATLAS can optionally point at it
> as an external "previous-project RTL DB" via `ATLAS_RTL_DB_WIKI` or
> `ATLAS_EXTERNAL_DB_WIKI`.
> **Related**: [[rtl-gen-ssot-contract]] · [[workflow-ownership-and-boundaries]] · [[karpathy-llm-wiki-pattern]]

## What

`~/Desktop/andes` is a corpus of Andes IP (UART, SPI, I2C, GPIO, PIT, WDT, RTC, DMAC,
AHB bus matrix, APB/LM/SPI bridges) plus the **AE210P** SoC platform. It has an LLM
wiki at `~/Desktop/andes/wiki/` that ATLAS can query as a reuse/reference source during
RTL generation when the external DB is enabled.

## How it was built

Reusable generator: `scripts/build_andes_rtl_db_wiki.py`.

```sh
python3 scripts/build_andes_rtl_db_wiki.py --build-graph
# default: --andes-root ~/Desktop/andes, wiki at ~/Desktop/andes/wiki
```

Per block (dir with `hdl/`) it parses module declarations + the top module's port
list, classifies the bus interface (APB / AHB / SPI / I2C + DMA/interrupt) from port
names, counts RTL, and matches docs/datasheet material such as `AndeShape_*` PDFs. It
emits one page per block with YAML frontmatter (`id/title/type/tags/related`) and
inline `[[wiki-link]]`s, plus `index.md`, `rtl-inventory.md`, doc wiki pages, and an
`ae210p` platform hub. Cross-links are derived from bus tags + curated roles (APB
peripheral → `atcapbbrg100`/`atcapbdec100`; AHB block → `atcbmc200`; DMA-capable →
`atcdmac100`; SPI ↔ AHB2SPI; everything → AE210P). Those `[[links]]` resolve inside
the Andes wiki, not this one.

The builder also publishes AST-oriented RTL facts under
`~/Desktop/andes/wiki/_rtl_facts/<block>.json`. These sidecars are for agent queries
that need concrete `module`, `port`, `parameter`, `fsm`, `datapath`, `register`,
`memory`, `clock`, `reset`, docs, or datasheet evidence instead of prose-only reuse
guidance. Block pages link the sidecar path in an "AST RTL facts" section.

`workflow/wiki/build_graph.py --wiki ~/Desktop/andes/wiki` then produces `_graph.json`.
Regenerate after the corpus changes; `wiki_query(ip="rtl-db")` may lazy-rebuild unless
`NO_REBUILD=1` is set.

## Enable / disable

```sh
# Enable this corpus for agents:
export ATLAS_RTL_DB_WIKI=/Users/brian/Desktop/andes/wiki
# Preferred generic name also works:
export ATLAS_EXTERNAL_DB_WIKI=/Users/brian/Desktop/andes/wiki
```

Disable by unsetting those variables or by not loading the `external-db` skill/config.
With `ATLAS_RTL_DB_NO_REBUILD=1` or `ATLAS_EXTERNAL_DB_NO_REBUILD=1`, ATLAS trusts the
shipped `_graph.json` and does not rebuild/clobber it.

The value is read from the environment at process start. Restart the live ATLAS server
and workers after changing `ATLAS_RTL_DB_WIKI` / `ATLAS_EXTERNAL_DB_WIKI`.

## Query

```sh
external_db_query(topic="uart apb dma", depth=3)
wiki_query(ip="external-db", topic="uart apb dma", depth=3)
wiki_query(ip="rtl-db",      topic="atcspi200 module port register", depth=3)
wiki_query(ip="andes",       topic="fsm clock reset memory datapath", depth=3)
```

`external-db` is the data-source-agnostic name. `rtl-db` and `andes` are aliases for
this configured source.

## Plugging in another DB

`wiki_query(ip="external-db")` normally reads a normalized
`<wiki_root>/_graph.json` (`wiki_graph.v1`: nodes with `id/title/tags/summary/path/
outgoing`). So the lookup is identical across systems; only the source→graph conversion
differs. When a foreign RTL DB has a non-ATLAS structure, plug it in with env hooks:

| Env | Effect |
| --- | --- |
| `ATLAS_EXTERNAL_DB_BUILDER=/abs/builder.py` or `ATLAS_RTL_DB_BUILDER=/abs/builder.py` | ATLAS runs `<builder> --wiki <root>` instead of the default graph build. The builder understands the foreign structure and writes `<root>/_graph.json`. Contract + sample: `scripts/example_external_rtl_db_builder.py`. |
| `ATLAS_EXTERNAL_DB_NO_REBUILD=1` or `ATLAS_RTL_DB_NO_REBUILD=1` | ATLAS reads an externally-produced `_graph.json` as-is and never rebuilds/clobbers it. |
| `ATLAS_EXTERNAL_DB_QUERY=/abs/query_adapter` or `ATLAS_RTL_DB_QUERY=/abs/query_adapter` | External owns the whole lookup. ATLAS pipes `{ip,topic,depth,max_nodes}` as JSON on stdin and returns stdout verbatim. No wiki dir or `_graph.json` is required. Contract + sample: `scripts/example_external_rtl_db_query.py`. |

### `external-db` skill — when to use the DB

The `skills/external-db/` skill auto-triggers on reuse/reference keywords (uart, spi,
dma, apb, ahb, "reference design", "reuse", "external db"…) and instructs the agent to
call `external_db_query(...)` **before** writing RTL or citing a reference. The tool is
a dedicated wrapper over the same external scope as `wiki_query(ip="external-db")`
(aliases: `rtl-db` / `andes`). It is data-source-agnostic and optional/on-off via the
env configuration above. This is comparable to loading a protocol skill such as
`pcie-expert`, `nvme-expert`, or `ucie-expert`: the skill tells agents when to ask; the
configured data source determines what facts are available.

Implementation: `core/tools.py::wiki_query` (external-db/rtl-db scope). Relevant tests:
`tests/test_wiki_query_tool.py` and `tests/test_andes_rtl_db_wiki_builder.py`.
