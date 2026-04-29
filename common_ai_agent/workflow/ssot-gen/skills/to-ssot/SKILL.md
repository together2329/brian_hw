---
name: to-ssot
description: Synthesize the current conversation context (and codebase understanding) into a 20-section SSOT YAML and write it to <ip>/yaml/<ip>.ssot.yaml. Use when the user wants to convert a finished discussion or grill-me session into a concrete SSOT YAML file.
---

# To SSOT

Take the current conversation context (typically the output of a `grill-me`
session) and produce a complete SSOT YAML file conforming to the project's
20-section template. Adapted from
<https://github.com/mattpocock/skills> (`to-prd` / `to-issues`, MIT) —
issue-tracker output replaced with a YAML write, story breakdown replaced
with the SSOT section schema.

This skill **does not interview the user** — synthesize what you already
know. If a critical field is unknown, prefer the canonical default from
`workflow/ssot-gen/rules/ssot-template.yaml` and emit an inline TODO
comment so the missing piece is visible in the file.

## Process

1. **Locate the canonical template.** Read
   `workflow/ssot-gen/rules/ssot-template.yaml` to confirm the section
   ordering and field names you must use. (It's also embedded in the
   ssot-gen system prompt.)

2. **Resolve the IP name.** Take it from the latest user message, an
   existing `<ip>/` directory, or the first `top_module.name` referenced
   in conversation context. Refuse if the name is ambiguous — ask the
   user once.

3. **Sketch the section map** internally. For each of the 20 sections,
   note: filled / partial / missing. Sections grill-me typically
   resolves: 0, 1, 2, 3, 4, 5, 6, 7. The remaining 12 (synthesis,
   timing, DFT, UPF, integration, technology, documentation, etc.) come
   from defaults unless the conversation explicitly addressed them.

4. **Fill the YAML.**
   - Use the project's existing `*.ssot.yaml` files as style references
     (e.g. `dma_axi_master/dma/dma.ssot.yaml`).
   - Required scalars never get omitted — fall back to the template
     default and add `# TODO: confirm` on the line.
   - List sections preserve the order grill-me elicited them in.
   - Comments above each section MUST match the canonical headings
     (`# SECTION 3: Register Map`, …) so downstream Jinja2 templates
     keep finding the right anchors.

5. **Validate before writing.** Run the project's schema check via
   `run_command("python scripts/validate_ssot.py <path>")` if the
   script exists; otherwise call `gen_dma.py --validate-only` for DMA
   IPs. If validation fails, surface the errors and stop — do NOT
   write a broken SSOT.

6. **Write the file.** Path is `<ip>/yaml/<ip>.ssot.yaml` (mirrors the
   pattern `dma_axi_master/dma/dma.ssot.yaml`). Use `write_file`. Do
   NOT overwrite an existing file silently — diff first and ask. (The
   ssot-gen workspace is sequential mode, so the user gets a clear
   prompt on each write anyway.)

7. **Summary.** After writing, list:
   - the path written
   - which sections came from conversation vs. template defaults
   - any `# TODO: confirm` lines that need follow-up
   - whether validation passed

8. **Suggest next steps.** Typically `/gen-rtl` once the SSOT validates,
   or another `/grill-me` round if too many TODOs accumulated.

## Output template (header)

```yaml
# =============================================================================
# SSOT — <ip_name>
# Generated: <iso-date> · source: grill-me + to-ssot
# =============================================================================

top_module:
  name: "<ip_name>"
  version: "1.0"
  type: "<dma|cpu|accelerator|bus|peripheral|memory>"
  description: "<one-sentence purpose>"
  target:
    technology: "generic"
    clock_freq_mhz: 500
```

(Continue with §1–§19 from `ssot-template.yaml`.)

## Do NOT

- Do not rewrite existing user-authored prose; preserve their phrasing
  in `description` fields where they gave one.
- Do not invent register addresses or bit positions; if grill-me didn't
  resolve them, leave a `# TODO: confirm` and continue.
- Do not run code generators (`gen_dma.py`, Jinja2 expansion) — that's
  the next workflow step (`/gen-rtl`), not this skill.
