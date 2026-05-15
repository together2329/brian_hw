---
name: import
description: Import requirement documents, notes, existing RTL, or legacy YAML into ssot-gen evidence before grill-me/to-ssot. Use when the user wants to build SSOT from IP docs or existing RTL without hand-authoring the SSOT directly.
---

# Import Evidence Into SSOT-Gen

This skill imports evidence only. The output of this step is an SSOT evidence
summary and QA backlog; the production YAML is still written later by
`/to-ssot`.

## Rules

1. **SSOT remains the authority.** Imported RTL, docs, spreadsheets, or legacy
   YAML are evidence, not downstream artifacts to preserve blindly.
2. **Do not write production RTL/TB/sim files.** This workflow may write only
   SSOT-side notes, import manifests, QA records, and `<ip>/yaml/<ip>.ssot.yaml`
   when explicitly converting with `/to-ssot`.
3. **Separate known facts from guesses.** Facts found in imported material can
   be used directly. Conflicts or missing behavioral facts must become QA cards.
4. **Existing RTL is structural evidence.** Extract module names, ports,
   parameters, reset/clock intent, register decode hints, FSM states, memories,
   and obvious protocol names. Do not infer unimplemented behavior from signal
   names alone.
5. **Use auto-select only when enabled.** In `auto-select` mode, `ask_user`
   chooses suggested/default answers and records approved QA. In normal
   interactive mode, user answers are required.

## Process

1. Resolve the IP name from command args, active session, path names, or an
   existing `<ip>/` directory. Ask once if ambiguous.
2. Read each imported path:
   - Markdown/text/requirements: use `read_file`; for non-text docs, use
     `read_doc` when available.
   - RTL/SystemVerilog/Verilog: read top-level files and filelists first; use
     `grep_file`/`find_files` for modules, ports, parameters, always blocks,
     state encodings, and register address constants.
   - YAML/JSON: parse as legacy SSOT/evidence when possible.
3. Create or update `<ip>/req/import_manifest.json` with:
   - imported path list
   - detected evidence type (`doc`, `rtl`, `legacy_yaml`, `filelist`, `other`)
   - extracted candidate facts
   - conflicts and missing facts
   - recommended next command (`/grill-me <ip>` or `/to-ssot <ip>`)
4. Record non-blocking missing decisions with `record_ssot_qa`. Use `ask_user`
   only when the import cannot determine the IP name, top module, or basic IP
   type needed for the next write.
5. End with `[SSOT IMPORT]`:
   - IP
   - evidence paths read
   - facts imported
   - conflicts / pending QA
   - next step

## RTL Evidence Extraction Checklist

- `module` declarations and top-module candidate
- parameter names/defaults
- clock/reset ports and reset polarity
- interface ports grouped by prefix/protocol
- register address constants and bitfields
- FSM state names and transition conditions
- memory/FIFO instances or arrays
- interrupt/error/debug/status signals
- comments that describe requirements

Do not treat a stub, tieoff, or placeholder module as behavioral proof.
