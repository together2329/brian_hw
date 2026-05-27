# SSOT Datasheet Authoring — reaching demo-grade quality (2026-05-27)

> **Updated**: 2026-05-27
> **Scope**: How the SSOT → HTML datasheet (`/api/ssot/export?format=html`, shown in
> the interactive SSOT Preview) renders, and how to push a real IP's doc toward the
> hand-crafted `interactive_ui/ca53-trm.html` gold standard **by editing the SSOT alone**.
> **Reference**: `interactive_ui/ca53-trm.html` (CA53 TRM-style demo) · worked example: `new_axi`.

## What renders richly (already)

`_ssot_to_html` (src/atlas_ui.py) covers ~34 sections (`_SSOT_EXPORT_SECTION_ORDER`).
These have **bespoke renderers** — fill the SSOT and they render well, no code change:

- **Registers** → bit-field strips + per-field tables (`bits` like `2:0`, access, reset).
- **FSM** → real Mermaid `stateDiagram-v2` (`[*] -->`, labeled edges) + transition table.
  Supports multiple machines (`fsm: {eng_a: {states,transitions}, eng_b: {...}}`).
- **Timing** → waveform wave-table, with per-signal **source mapping** (see below).
- **Top module / block diagram**, **custom_blocks** (arbitrary md/mermaid/html).
- Most other sections → tables / definition lists from the data.

Quality is bounded by SSOT richness: a thin SSOT → thin doc; `new_axi` (rich, ~2.1k lines)
renders a ~97 KB datasheet with 47 sections, 5 Mermaid diagrams, 26 bit-field strips, 63 tables.

## Timing signal → RTL mapping (so waveforms are traceable)

A timing diagram lives under `timing.diagrams[]`; each signal maps to a real port or
internal net so the waveform isn't ambiguous:

```yaml
timing:
  diagrams:
  - name: MM2S AXI4 read burst
    clock: aclk                       # reference clock (shown)
    description: 4-beat read on m_axi_mm2s …
    signals:
    - name: arvalid
      module: new_axi                 # which module
      port: m_axi_mm2s_arvalid        # boundary port (from io_list)
      kind: port                      # port | reg | wire | logic | comb | ff
      values: ['0','1','1','0', …]    # per-cycle cells (or wave: "01x…")
    - name: mm2s_state
      module: new_axi_mm2s
      internal_signal: mm2s_state     # internal net instead of a port
      kind: ff
      description: read-engine FSM state register …   # optional per-signal detail (+ tooltip)
```
Rendered: row label + `module.port` (or `module.internal_signal`) + kind badge + optional
italic detail note. Cells colour by value (1/h → high, 0/l → low, else mark).

## `custom_blocks` — the demo-grade lever (SSOT-only)

Inject **arbitrary markdown / mermaid / html**, anchored after any section. This is how you
reach CA53-demo-style bespoke chapters (architecture/pipeline diagrams, sequences, prose,
or a whole hand-authored HTML chapter) **from the SSOT, surviving regeneration**:

```yaml
custom_blocks:
- after: features            # any key in _SSOT_EXPORT_SECTION_ORDER
  type: mermaid              # markdown | mermaid | html
  title: new_axi datapath architecture
  inline: |                  # inline content, OR
    flowchart LR
      CSR --> MM2S
      MM2S -->|AR / R| MAXI
# - after: registers
#   type: html
#   title: Programming Guide
#   file: new_axi/doc/prog_guide.html   # file under PROJECT_ROOT → embedded via <iframe src=/api/file/raw>
```
Renderers: `_ssot_html_render_custom_block` / `_ssot_html_custom_blocks_for` (src/atlas_ui.py).
`new_axi` ships 4 example blocks (datapath flowchart, MM2S pipeline, CSR programming
`sequenceDiagram`, and a markdown quick-start) — all authored purely in the SSOT.

## SSOT-only ceiling vs code-needed

- **Reachable by editing the SSOT**: every rich section above + any mermaid/markdown/html
  chapter via `custom_blocks` (incl. a full authored HTML chapter via `file:`). This covers
  essentially all of the CA53 demo's *content*.
- **Needs code (template)**: global page CSS / layout polish (sidebar TOC styling) and
  auto-converting a generic-table section into a bespoke renderer (or just drop a
  `custom_block` beside it).

## Verify

```sh
# render an IP's datasheet and inspect (md_text first, then html with data)
python3 - <<'PY'
import yaml; from src.atlas_ui import _ssot_to_markdown, _ssot_to_html
d=yaml.safe_load(open('<root>/new_axi/yaml/new_axi.ssot.yaml'))
h=_ssot_to_html(_ssot_to_markdown(d,'new_axi'),'new_axi',d)
print(h.count('class="mermaid"'),'mermaid;', h.count('wave-table'),'wave-tables')
PY
```
Backend (`_ssot_to_html`) changes need a server restart to show in the live Preview; SSOT
data edits are read at render time.
