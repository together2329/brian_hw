# pl330 IP Wiki

Per-IP knowledge base. Read with `wiki_query(ip="pl330")` or run
`python3 workflow/wiki/build_graph.py --ip pl330` to refresh the index.

## Status snapshot

Populated by `workflow/wiki/build_graph.py --ip <ip>`; the synthetic
`[[ssot]]`, `[[fl_model]]`, `[[cl_model]]`, `[[rtl]]`, `[[filelist]]`,
`[[lint]]`, `[[tb]]`, `[[sim]]`, `[[coverage]]`, `[[audit]]`, and
`[[last_run]]` nodes carry status/digest fields.

## Tree

- [[notes]] — free-form owner/manager notes
- [[log]] — append-only event log
- requirements at `../req/`
- SSOT YAML at `../yaml/pl330.ssot.yaml`
- function/cycle model at `../model/`
- RTL at `../rtl/` (filelist `../list/pl330.f`)
- testbench at `../tb/`
- sim evidence at `../sim/`
- lint/coverage at `../lint/` and `../cov/`
- run logs at `../logs/`
