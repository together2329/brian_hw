# `soc.ssot.yaml` — SoC-level SSOT schema

The single source of truth for the **whole-SoC** view. Owned by the
Architect supervisor. Lives at `<project_root>/soc.ssot.yaml`.

## Top-level fields

```yaml
name:    aurora_soc           # SoC name (free-form)
version: 0.1.0                # semver

clusters:                     # logical subsystems
  - id: cpu_ss
    role: CPU                 # one of: CPU, MEM, BUS, PERIPH, ANALOG, MISC
    label: "CPU subsystem"    # display name (optional)
    members: [cpu0, cpu1, l2] # references to instance ids

instances:                    # IP instances
  - id: cpu0                  # unique within the SoC
    ssot: cortexa15/yaml/cortexa15.ssot.yaml   # leaf SSOT path (relative to project root)
    name: cortexa15           # leaf top_module override (optional — defaults to leaf's top_module)
    kind: cpu                 # display category (optional — auto-inferred from name)
    addr: 0x0000_0000         # base address in the SoC addrMap (optional)
    overrides:                # leaf parameter overrides for this instance
      L1I_SIZE: 32K
      L1D_SIZE: 32K

connections:                  # IP↔IP bus links
  - from: cpu0/M_AXI          # <inst_id>/<busInterface name>
    to:   cci_400/S0_ACE
    proto: ACE                # must match on both ends

addrMap:                      # whole-SoC address layout
  - { name: spi_master_0, base: 0x4000_2000, range: 0x1000 }
  - { name: ddr_phy,      base: 0x8000_0000, range: 0x4000_0000 }

generators:                   # auto-generated artifacts
  top:
    template: rtl/aurora_soc.sv.j2
    output:   rtl/aurora_soc.sv
```

## Field-by-field rules

### `clusters`
- `id` is required, must be unique, `[A-Za-z][A-Za-z0-9_]*`.
- `role` is one of CPU / MEM / BUS / PERIPH / ANALOG / MISC. Drives
  the diagram glyph + colour.
- `members[]` references `instances[].id`. Unknown ids are silently
  dropped (the architect logs a warning).

### `instances`
- `id` required, unique, `[A-Za-z][A-Za-z0-9_]*`.
- `ssot` required, points to a leaf SSOT file. The leaf provides:
  `top_module`, `parameters`, `clocks`, `resets`, `busInterfaces`,
  `memoryMap`. The architect *reads* but never *writes* leaf SSOTs
  directly (that's ssot-gen's job).
- `addr` (optional) — when present, must appear in `addrMap` with
  the same base.
- `overrides` (optional) — instance-level parameter overrides. They
  win over the leaf's defaults but do not modify the leaf file.

### `connections`
- `from` and `to` are `<inst_id>/<busInterface_name>` strings.
- `proto` is whitelist: AXI4 / AXI4L / ACE / AHB / APB / AXIS / IRQ.
- Master role on one side, slave on the other (the architect verifies
  this against the leaf SSOTs).
- A `busInterface` may participate in at most one connection per
  family (no fan-out except via an explicit interconnect IP).

### `addrMap`
- Sorted by `base`. Every entry: `{ name, base, range }`.
- `base` is a multi-of-4KB hex literal (`0x4000_0000`, `0x4000_1000`).
- `addrmap_check` validates: no overlaps, no zero-base entries,
  ranges power-of-two-aligned.

### `generators.top`
- Optional. When present, `wrapper_gen` reads the template at
  `template:` and writes the rendered SystemVerilog to `output:`.
- The template receives the parsed `soc.ssot.yaml` plus a flat list
  of every leaf SSOT.

## Lifecycle

1. **Genesis.** Architect creates the file when one is missing. Initial
   content has no instances; the user adds them via `/add-ip`,
   `/import-ipxact`, or by calling tools directly.
2. **Mutation.** Every edit is diff-shown then written. After every
   structural change, `addrmap_check` runs.
3. **Wrapper regen.** After any change to `instances` or `connections`,
   the architect prompts the user to regenerate the top-level wrapper.
4. **Hand-off.** Sub-workflows (rtl-gen, sim, lint, syn, sta) read
   `soc.ssot.yaml` for context but never modify it. They only touch
   their per-IP files.
