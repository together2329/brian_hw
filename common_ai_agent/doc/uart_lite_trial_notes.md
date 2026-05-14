# uart_lite Trial Notes (2026-05-14)

End-to-end shakedown of the canonical pipeline — `ssot-gen → fl-model-gen → rtl-gen` — on a freshly-scaffolded `uart_lite` IP, driven from a headless stdin pipe. Captured here so the next attempt does not repeat the same wrong turns.

## Pipeline Used

```
ssot-gen        → uart_lite/yaml/uart_lite.ssot.yaml         (LLM-authored)
fl-model-gen    → uart_lite/model/*  + uart_lite/cov/*       (deterministic script)
rtl-gen         → uart_lite/rtl/*.sv + compile + lint        (LLM-authored, iterative)
```

(`ssot-equiv-goals`, `tb-cocotb`, `sim`, `sim-debug`, `goal-audit` not yet run for this IP.)

## Headless Launch Pattern

Each workflow was launched as a background `python3 src/main.py` with stdin redirected from a small seed file. Slash commands are interpreted by chat_loop **before** the user message reaches the LLM — so they must arrive on their own lines from stdin, not embedded in a `--prompt` payload.

```bash
nohup python3 src/main.py \
  -s <campaign>/<ip>/<workflow> \
  -w <workflow> \
  --model deepseek \
  --effort medium \
  < /tmp/<workflow>_seed.txt \
  > .omc/logs/<workflow>.log 2>&1 &
```

Example seed (ssot-gen):

```
/mode pipeline
/new-ip uart_lite uart
Use the loaded /new-ip todo list and create only the canonical SSOT for IP uart_lite. IP intent: <one-line, comma-separated, no embedded newlines>
Pipeline mode: do not block on ask_user; record conservative assumptions in custom.assumptions. Do not generate RTL/TB/sim/lint/syn artifacts in ssot-gen.
```

## Traps Encountered

### Trap 1 — Trailing `exit` in stdin

First attempt appended `exit` to the seed file, expecting it to cleanly terminate `chat_loop` after the agent finished. It did not: the `exit` got consumed by the chat loop **before** the ReAct loop had completed, killing the agent mid-Phase-1 thinking. Symptoms: process exit code 0, partial logs, no SSOT YAML on disk.

**Fix:** Do not write `exit` at the end of stdin. Let stdin reach EOF naturally; `chat_loop` raises `EOFError` on its next `input()` call only **after** the ReAct loop yields control, which happens after the agent finishes its work. Side effect: the process idles briefly after the work is done — kill it manually or wait for the workflow's last yield to trigger EOF cleanup.

### Trap 2 — Model choice affects wall time, not correctness

First attempt used `--model glm` (`glm-5.1`). Phase 1 thinking spinner ran for many minutes with very low CPU. Switching to `--model deepseek` (`deepseek-v4-pro`) completed Phase 1 in ~10 minutes and the entire 5-phase SSOT in ~12 minutes.

GLM was working, just slow on `medium` reasoning effort. Pattern for future runs: prefer `deepseek` (or `gpt-5.3-codex`) for time-sensitive shakedowns; reserve GLM for runs where you do not care about throughput.

### Trap 3 — "optional" in the seed leaked into SSOT and tripped RTL preflight

The seed used phrases like *"optional parity (none/even/odd)"* and *"1 or 2 stop bits as CSR config"*. The LLM faithfully recorded these in `uart_lite.ssot.yaml`. RTL preflight (`derive_rtl_todos.py --audit-rtl`) then emitted `uart_lite/rtl/rtl_blocked.json`:

```json
{
  "status": "blocked",
  "questions": [
    "OPTIONAL_BEHAVIOR_POLICY: SSOT contains 'optional' — must be required/disabled/parameterized",
    "RTL_TARGET_SCALE_POLICY: lock or waive production target scale"
  ]
}
```

The agent silently picked the "parameterize" path and continued — which is the recommended default but does NOT clear the SSOT-side blocker. `audit-rtl` will continue to flag it until the SSOT is repaired.

**Fix for next run:** Word the seed so policy is locked at SSOT time. Instead of *"optional parity"* write *"`parity_en` CSR bit (reset 0) selecting between no-parity and `parity_odd`-controlled even/odd"*. Same for stop bits: *"`stop_bits` CSR field (reset 0 = 1 stop bit, 1 = 2 stop bits)"*. Also lock a target scale in `quality_gates.rtl_gen.target_scale` (or set `target_scale_waiver.approved=true` with a reason).

### Trap 4 — Empty `custom.assumptions[]` is a smell

Pipeline mode says *"record conservative assumptions in custom.assumptions"*. The deepseek run produced **zero** assumption entries. That looked clean but turned out to mean the model silently baked decisions into the SSOT instead of surfacing them. The blocker above (`OPTIONAL_BEHAVIOR_POLICY`) is exactly what should have been an assumption.

**Next run:** explicitly enumerate ambiguities in the seed and tell the agent to either lock them or list them in `custom.assumptions`. An empty `assumptions[]` for an IP with optional features is a red flag, not a feature.

## Stage Characters (Observed)

| Stage | Mostly | LLM iters (deepseek) | Wall time | Notes |
|---|---|---|---|---|
| `ssot-gen` | LLM authoring | 71 of 300 | ~12 min | Heaviest at Phase 3 (write 72 KB YAML). Phase 1 absorbed ~44 iters loading the 36-section template. |
| `fl-model-gen` | Deterministic script | 0 | <1 min | `emit_fl_model.py` parses SSOT and emits 65 KB `functional_model.py`, 14 decomposition units, 90 fcov bins. LLM never engaged for this IP. |
| `rtl-gen` | LLM + tool loop | 86+ of 150 (still running at writeup) | ~34 min so far | 8 SV files, 1315 lines, ~48 KB. Compile/lint clean (0 errors, 0 warnings). Audit 240/279 pass; 39 open are mostly derive-tool owner-file mapping bugs, not real defects. |

## TODO ↔ LLM Call Ratio

279 RTL TODOs were closed by ~86 LLM calls. This is not a contradiction:

- `derive_rtl_todos.py` generates fine-grained **evidence checks** (signal exists, register at right offset, FSM state has correct transition).
- One `Write` tool call authoring a 370-line `uart_lite_regs.sv` simultaneously satisfies ~60 evidence-check TODOs on the next `--audit-rtl` pass.
- 8 bulk authoring calls covered roughly 169 TODOs in one audit cycle. The remaining ~78 calls were compile/lint feedback loops, small edits, and audit re-runs that closed the long tail.

The unit of LLM work is "coherent batch of file edits"; the unit of TODO closure is "evidence appears in RTL on next audit". The two are decoupled.

## Token Accounting (Cache Matters)

For `rtl-gen` at iter 85 of the run:

| Metric | Tokens |
|---|---|
| Uncached input | 157 k |
| **Cached input** | **10.6 M** |
| Output | 26 k |
| Effective billable (uncached + output) | **~183 k** |

The 10.6 M cached-input number is not the bill — prompt caching reuses system prompt + SSOT YAML across every call at low cost. The real signal is the ~183 k uncached cost for an end-to-end RTL authoring loop.

## Files Produced (uart_lite)

```
uart_lite/yaml/uart_lite.ssot.yaml             72 KB  (LLM)
uart_lite/model/functional_model.py            65 KB  (script)
uart_lite/model/decomposition.json             51 KB  (script)
uart_lite/model/fl_model_check.json           7.3 KB  (script, passed=True)
uart_lite/model/manifest.json                  262 B  (script)
uart_lite/cov/fcov_plan.json                   30 KB  (script, 90 bins)
uart_lite/rtl/uart_lite.sv                     54 L   (LLM)
uart_lite/rtl/uart_lite_core.sv                218 L  (LLM)
uart_lite/rtl/uart_lite_regs.sv                371 L  (LLM, 11 registers)
uart_lite/rtl/uart_lite_baud_gen.sv            81 L   (LLM)
uart_lite/rtl/uart_lite_tx_fsm.sv              217 L  (LLM)
uart_lite/rtl/uart_lite_rx_fsm.sv              235 L  (LLM, mid-bit @ oversample=7)
uart_lite/rtl/uart_lite_tx_fifo.sv             72 L   (LLM)
uart_lite/rtl/uart_lite_rx_fifo.sv             67 L   (LLM)
uart_lite/rtl/rtl_blocked.json                 —      (preflight, NOT cleared)
uart_lite/rtl/rtl_compile.json                 —      (iverilog: 0/0/0)
uart_lite/lint/dut_lint.json                   —      (pyslang+verilator: 0/0)
```

## Recommended Next-Run Checklist

1. **Seed must lock policy, not describe options.** Replace "optional X" with concrete CSR-controlled field names and reset defaults.
2. **Lock target scale** in `quality_gates.rtl_gen.target_scale` at SSOT time, or set an approved waiver.
3. **Validate `custom.assumptions[]` is non-empty** for any IP with conditional features; otherwise the decisions are hidden.
4. **Do not append `exit`** to the seed file. EOF terminates `chat_loop` cleanly only after ReAct yields.
5. **Pick deepseek for shakedowns**, GLM for cost-sensitive non-time-critical runs.
6. **Run `derive_rtl_todos.py --audit-rtl` from the shell** before declaring done — this is the canonical RTL gate, not whatever the agent claims.
7. **Treat the 30 derive-owner-file mismatches as a tool bug**, not an RTL defect — fix the derive script's owner-file resolution before the next IP, or the same 30 spurious failures will recur.
