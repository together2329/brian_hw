# interactive_ui — self-contained interactive diagrams (2026-05-23)

A gallery of dependency-free, single-file HTML diagrams under
`common_ai_agent/interactive_ui/`. Each opens by double-clicking (`file://`) —
no build, server, or install. All CSS/JS/data is inlined; the only `http://`
string is the SVG XML namespace (`createElementNS`), not a network fetch.

## Contents

Open `interactive_ui/index.html` for the gallery.

| file | what | data | interaction |
|------|------|------|-------------|
| `chat-feel-demo.html` | chat UX: DB-dump vs typing-stream | static | replay |
| `timing-diagram.html` | WaveDrom-style waveform | editable JSON | hover readout, ▶ sweep |
| `timing-compare.html` | **SSOT-expected vs VCD-actual** diff | `data/gpio_*.json` | cell diff, ⚠ inject-violation |
| `architecture-diagram.html` | IP block diagram | `data/gpio_arch.json` | block/port hover, ▶ dataflow trace |
| `fsm-diagram.html` | APB handshake FSM | `data/gpio_fsm.json` | click state, psel/penable, ⏭ step |

## Generators (reusable)

`common_ai_agent/scripts/wavespec/` — turn project artifacts into wavespec JSON:

- `vcd_to_wavespec.py` — VCD → actual RTL waveform; samples on clock rising
  edges, supports `--anchor NAME=VALUE`/`--pre`/`--cycles` windowing. stdlib only.
- `ssot_to_wavespec.py` — SSOT YAML → expected APB handshake from the
  `protocol` contract + register map; idle-only control signals become
  don't-care (`x`) so the diff doesn't flag unconstrained cycles. Needs `pyyaml`.

Wave tokens: `p` clock · `0/1` level · `.` hold · `=` bus(+`data` label) ·
`x` don't-care (never flagged) · `z` hi-Z.

Regenerate cached data:

```bash
python3 scripts/wavespec/ssot_to_wavespec.py atlas_flow_gpio_demo/yaml/atlas_flow_gpio_demo.ssot.yaml --reg DATA --data 0x55 > interactive_ui/data/gpio_expected.json
python3 scripts/wavespec/vcd_to_wavespec.py atlas_flow_gpio_demo/sim/atlas_flow_gpio_demo.vcd --clock PCLK --anchor "PWDATA=0x55" --pre 1 --cycles 5 --signals PCLK PSEL PENABLE PWRITE PADDR PWDATA PREADY gpio_out > interactive_ui/data/gpio_actual.json
```

`timing-compare.html` currently inlines these specs so it stays standalone;
re-paste after regenerating (or add an HTTP loader if served).

## Export to image (SVG / PNG)

The four SVG-based viewers carry floating **⬇ SVG** / **⬇ PNG** buttons that
serialize the live diagram with inlined computed styles into a self-contained
file (SVG = true vector for docs/slides; PNG = 2× raster). Batch/CI export:

```bash
node scripts/wavespec/export_svg.mjs   # -> interactive_ui/img/*.{svg,png}
```

`export_svg.mjs` drives each page via system Chrome (Playwright
`channel:'chrome'`), clicks the in-page buttons, captures downloads, and
validates them — doubling as an E2E test. Multi-`<svg>` pages (timing-compare's
two lanes) are composed into one stacked SVG. Pre-rendered output in
`interactive_ui/img/`.

## Why timing-compare matters

It lays the **SSOT contract** (`protocol.setup_phase`/`access_phase`/
`write_rule`, zero-wait-state PREADY, register mirror) next to the **actual VCD**
waveform and diffs cell-by-cell. A green "sim passed" can mask a TB stimulus /
timing-contract gap; this makes the contract explicit. For the gpio demo the RTL
satisfies the contract (0 mismatches); toggling **위반 주입** flips to a wrong
contract variant and the offending cells (PENABLE @cyc3, gpio_out @cyc2) light up
red — demonstrating the detection path.

## Verification done

- All 6 HTML files: inline JS parses via `new Function(...)`; embedded JSON valid.
- Generators run on the real gpio VCD/SSOT; outputs match hand-traced behavior.
- Diff logic: normal contract = 0 mismatches; injected violation = 2 mismatches.
- No external/network dependencies (only the SVG namespace literal).

## Status / next

- Generated for `atlas_flow_gpio_demo` (APB-Lite GPIO). The generators are
  IP-agnostic — point them at any IP's `sim/*.vcd` + `yaml/*.ssot.yaml`.
- Possible follow-ups: auto-pick the write transaction by register offset rather
  than `--anchor PWDATA=…`; load `data/*.json` at runtime to drop the inline copy;
  read-transaction (PRDATA) compare; generate compare specs in the ATLAS flow.
