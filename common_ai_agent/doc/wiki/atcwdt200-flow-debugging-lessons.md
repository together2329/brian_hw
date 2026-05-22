---
title: "ATCWDT200 Flow Debugging Lessons"
tags: ["atcwdt200", "rtl-audit", "cocotb", "scoreboard", "debugging"]
created: 2026-05-17T07:19:24.949Z
updated: 2026-05-17T07:19:24.949Z
sources: []
links: []
category: debugging
confidence: medium
schemaVersion: 1
---

# ATCWDT200 Flow Debugging Lessons

# ATCWDT200 Flow Debugging Lessons

## Static RTL Audit
- `derive_rtl_todos.py --audit-rtl` strips comments before matching evidence terms.
- Put required terms into real implementation paths, not comments.
- Prefer semantic closure:
  - CSR terms through decode/mask/read mux (`CR_FIELDS_x7ff`, `prdata_rule`).
  - output terms through real output equations (`wdt_int`, `wdt_rst`).
  - FSM/counter terms through counter/FSM datapath.
- If a harmless trace term is unavoidable, consume it in an expression that lint can prove used, and re-run Verilator with warnings as errors.

## Provenance Gate
- RTL authoring is not complete until `rtl/rtl_authoring_provenance.json` exists.
- Required fields observed by the gate:
  - `type: rtl_authoring_provenance`
  - `agent: common_ai_agent`
  - `workflow: rtl-gen`
  - `surface: headless_common_engine` or ATLAS/Textual equivalent
  - `todo_plan_sha256` matching current `rtl/rtl_todo_plan.json`
  - `rtl_files` covering manifest RTL plus current filelist sources.
- After provenance, rerun `derive_rtl_todos.py --audit-rtl` because the todo hash/gate status can change.

## Sandbox / Environment
- Python py_compile on macOS can try to write under `~/Library/Caches/com.apple.python`, which is outside sandbox.
- Use `PYTHONPYCACHEPREFIX=/private/tmp/pycache` for py_compile and cocotb runner invocations.

## TB/Sim Gate
- `check_tb_disk.sh` only proves TB files exist and are structurally plausible. It does not prove scoreboard equivalence.
- cocotb regression PASS can coexist with `[SIM ESCALATE]` if the generated scoreboard records failed rows but hard fail is disabled.
- Always inspect:
  - `atcwdt200/sim/sim_report.txt`
  - `atcwdt200/sim/scoreboard_events.jsonl`
  - `atcwdt200/tb/cocotb/tb_manifest.json`
- Final signoff requires no `[SIM ESCALATE]`, not just `TESTS=1 PASS=1 FAIL=0`.

## Current ATCWDT200 Debug Lead
- APB read mismatch currently shows `prdata expected=0 observed=50339842` for VER read.
- This likely means the FL output rule for `apb_read.prdata_rule` is under-specified (`expr: 0`) while RTL returns the real version register, or the TB sampled a default read at VER offset.
- Internal-state goals produce `no comparable RTL observable`; either add explicit debug observability/contract mapping or classify those goals as not externally comparable in this TB surface.
- Do not weaken scoreboard to force pass. Fix the owning contract: SSOT/FL if expected behavior is incomplete, TB if sampling/stimulus is wrong, RTL if DUT violates approved SSOT.

