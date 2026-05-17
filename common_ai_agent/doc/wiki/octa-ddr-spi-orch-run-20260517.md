# OCTA DDR SPI Orchestrator Run (2026-05-17)

Status: pipeline reaches `sim-debug` clean owner-routing. SSOT, FL/CL/equiv,
RTL (compile+lint clean), TB, sim cocotb PASS. 24 SOFT_EQ_MISMATCH after
fresh oracle regen — owner split 18 → `rtl-gen`, 6 → `tb-gen`. Same
Frontier pattern as [[quad-spi-orch-run-20260517]] but reproduced from
scratch with the workflow fixes that QUAD SPI surfaced.

Related: [[quad-spi-orch-run-20260517]] · [[ssot-gen-pass-pipeline]] ·
[[orchestrator-worker-handoff]] · [[parallel-todo-sub-agent-workers]] ·
[[multi-user-worker-conflicts]] · [[full-flow-pipeline]]

## Run Scope

| Item | Value |
|---|---|
| Scratch root | `/Users/brian/Desktop/Project/OCTA_DDR_SPI_ORCH_20260517_001` |
| IP | `octa_ddr_spi_ctrl` |
| Top module | `octa_ddr_spi_ctrl_top` (ip-name ≠ top-name pattern) |
| Manifest modules | 5 children (`apb_regs`, `fifo`, `clkgen`, `engine`, `integration`) + `_top` |
| Model | `gpt-5.3-codex` (CLI / OAuth) |
| LLM timeout | `ATLAS_HEADLESS_LLM_TIMEOUT=600` (new default) |
| Pipeline mode | orchestrator + headless |
| Lane modes | 1/2/4/8 SDR + 8 DDR (`io_oe[7:0]` full octal) |

## Pipeline Result

| Stage | Status |
|---|---|
| `req` | ✅ |
| `ssot-gen` | ✅ (after the flow-mapping bracket fix + sub_modules normalization) |
| `fl-model-gen` | ✅ |
| `cl-model-gen`, `dual-fcov` | ✅ |
| `equiv-goals` | ✅ 67/67 required, 0 blocked |
| `rtl-gen` | 🟡 fail-as-audit (compile/lint clean, downstream artifact gates open) |
| `lint` | ✅ pyslang + verilator clean |
| `tb-gen` | ✅ |
| `sim` | 🟡 cocotb PASS, 24 SOFT_EQ_MISMATCH → router to sim-debug |
| `sim-debug` | 🟡 owner-routed: 18 → `rtl-gen`, 6 → `tb-gen` |
| `coverage`, `goal-audit` | ⏸ gated by sim-debug |

`sim-debug` summary: `total=67 passed=43 failed=24 blocked=0` —
about 64% of goals pass against the FL oracle.

## Workflow Fixes Applied During This Run

The QUAD SPI run produced six BUG items in [[quad-spi-orch-run-20260517]].
OCTA DDR SPI exercised the fixes for those bugs end-to-end:

1. **180 s LLM timeout → 600 s default** (`src/headless_workflow.py:1134`).
   Without this, ssot-gen would have given up after three 180 s retries.
2. **`top_module.name` is single authority for top in tb-gen**
   (`workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py:399,578`).
   Reading SSOT.top_module.name first prevents `tb_manifest.json.top` from
   silently drifting back to the IP name on regen.
3. **SSOT structural invariants in `check_ssot_disk.sh`**
   (`require_top_sub_module_consistency`). Now rejects:
   - `top_module.name`/`top_module.file` empty.
   - `sub_modules[*].name == ip_name` unless `wiring_only: true`.
   - `sub_modules[*].name == top_module.name` unless legacy `top_name == ip`.
   - `sub_modules[*].file == top_module.file` unless `wiring_only: true`.
4. **HTTP worker `/run` workflow-binding guard** (`core/agent_server.py`).
   When the worker was launched with `--workflow rtl-gen`, a `/run` with
   `workflow: "tb-gen"` is now 403. `/health` exposes the binding.
5. **Flow-mapping bracket trap auto-repair**
   (`workflow/ssot-gen/scripts/repair_ssot_schema.py:_expand_flow_mappings_with_brackets`).
   LLM-emitted lines like
   `- { name: ST_BUSY, enable_reg: IRQ_EN[0], status_reg: STATUS[0], ... }`
   are rewritten to block style before YAML parsing.
6. **`top_module.file` auto-added to `SSOT.filelist.rtl`**
   (`workflow/ssot-gen/scripts/repair_ssot_schema.py` around 3585). Stops
   iverilog/verilator from failing with "Unable to find the root module"
   when `top_module.file != rtl/<ip>.sv`.
7. **`_ensure_sub_modules` respects `top_module.name`**
   (`workflow/ssot-gen/scripts/repair_ssot_schema.py:522`). When the SSOT
   top name differs from the IP (e.g. `<ip>_top`), the deterministic
   repair no longer appends a duplicate wrapper sub_module — which would
   collide with the new invariants.

## Iteration Cost

| Phase | Wall clock |
|---|---|
| `ssot-gen` initial → first valid YAML | 2 retries × 200–230 s LLM + repair |
| `ssot-gen` flow-mapping bracket trap recovery | required `_expand_flow_mappings_with_brackets` |
| `rtl-gen` 3 attempts | compile clean by 3rd attempt (after filelist fix) |
| `sim` → `sim-debug` route | one round-trip, classifier accurate first time |

Total: ~25 minutes wall clock from `rm -rf` to `sim-debug` with all owner
classifications populated. Without the fixes, the same run would have hit
the same six workflow bugs that took multiple debugging cycles on QUAD SPI.

## Frontier Analysis

Identical frontier classification as QUAD SPI; absolute counts smaller
because the OCTA SSOT is simpler.

### Frontier-A: scoreboard `*_next`/`_reg` aliasing (~6–8 mismatches)
- `prdata_next: expected=18 observed=2` — same pattern as QUAD SPI's
  `tx_fifo_count: expected=1 observed=0`. The base name appears in the
  expected contract; RTL emits a `_next` projection; scoreboard fails to
  alias.
- Fix lives in `workflow/tb-gen/runtime/equivalence_scoreboard.py`.

### Frontier-B: FL multi-field result without comparable observable (6)
- `EQ_TRANSACTION_APB_W1C_STATUS`,
  `EQ_TRANSACTION_APB_WRITE_TXDATA`, `_ADDR`, `_CMD`, etc.
- All return "no comparable RTL observable for FunctionalModel result".
- Fix lives in `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py`.

### Frontier-C: real FL-vs-RTL semantic gaps (~6–10)
- `EQ_TRANSACTION_START_TRANSFER: irq: expected=1 observed=0`
- `EQ_SCENARIO_SC01: irq: expected=1 observed=0` — DDR start triggers IRQ
  in FL but RTL waits for `DONE`. Needs SSOT clarification on IRQ launch
  vs IRQ done semantics.
- Routed through [[human-review-and-escalation]].

## What This Run Confirms

- The fixes from [[quad-spi-orch-run-20260517]] generalise. OCTA DDR SPI
  hit the same workflow bugs but they were closed at the workflow layer,
  not by manual SSOT edits.
- The new SSOT invariants catch the LLM's "redundant ip-name sub_module"
  habit immediately, *before* rtl-gen wastes packet repair budget on a
  malformed manifest.
- Owner classification at `sim-debug` is still the right place to fork
  between RTL behaviour fixes (Frontier-C, human review) and workflow
  fixes (Frontier-A/B, scoreboard/oracle tooling).

## Next Workflow Improvements Surfaced By This Run

Going forward (not blocking this run):

- `repair_ssot_schema.py` should also keep `<ip>.f` on disk in sync with
  the SSOT.filelist.rtl change at the same time it patches the SSOT, so
  the operator does not have to rerun rtl-gen just to refresh the
  filelist file. The disk filelist is refreshed by
  `_refresh_rtl_filelist_and_provenance` only when `rtl-gen` runs.
- `ssot_to_rtl.py:_top_name` should reuse the same precedence rule
  (`top_module.name` → `top_module` → ip) so `rtl_contract.json.top`
  matches what tb-gen sees (currently `rtl_contract.json.top ==
  octa_ddr_spi_ctrl` even when SSOT says `_top`).
- The `tb_bug "no comparable RTL observable"` class needs a structured
  mapper from FL transaction result fields → RTL state observables, with
  a fallback to declaring the goal *observable_missing* so it does not
  silently classify as `tb_bug`.

## What Did Not Need Manual Fixing

Unlike the QUAD SPI run, **no manual SSOT YAML edit** was needed beyond a
single `resolve_rtl_blockers.py` answer for the `integration` wiring-only
module contract. Every other "fix" was a workflow code change that closed
the bug for future IPs as well.
