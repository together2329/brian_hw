# Round 2 — Retry Budget + Cross-Workflow Routing Validation (2026-05-17)

Status: end-to-end orchestrator routing flow validated on `simple_uart_tx`.
RTL bug injected, kimi `sim_debug` worker silent-failed twice, retry budget
exhausted, orchestrator escalated to fallback classification, codex `rtl-gen`
applied the repair, and the re-run cocotb suite returned **5/5 PASS**.

Related: [[orchestrator-worker-handoff]] ·
[[quad-spi-orch-run-20260517]] · [[octa-ddr-spi-orch-run-20260517]] ·
[[run-mode-and-provenance-policy]]

## Run Scope

| Item | Value |
|---|---|
| Scratch root | `/tmp/orch_round2/simple_uart_tx` |
| IP | `simple_uart_tx` (8N1 UART transmitter-only APB-lite peripheral) |
| Source root | `/Users/brian/Desktop/Project/brian_hw/common_ai_agent` |
| Workers | `:5521` ssot-gen deepseek-v4-pro · `:5522` rtl-gen gpt-5.3-codex · `:5523` tb-gen kimi-2.6 · `:5524` sim deepseek-v4-pro · `:5525` sim_debug kimi-2.6 |
| Orchestrator role | gpt-5.5 xhigh (acting as routing arbiter / fallback classifier) |
| Test goal | Validate cross-workflow routing decision + retry budget escalation when a worker silent-fails |

## Stage Timeline

1. **Baseline build** — `ssot-gen` (deepseek) → `rtl-gen` (codex) → `tb-gen`
   (kimi) → cocotb runner: 5/5 PASS.
2. **Bug injection** — `rtl/simple_uart_tx.sv` line 93 manually mutated:
   `tx_done_irq <= 1'b0;` replaced with `// BUG: tx_done_irq self-clear removed`.
   Pristine backed up at `rtl/simple_uart_tx.sv.pristine`.
3. **First sim** — `test_tx_done_irq_pulse` FAIL (AssertionError: irq must be 0
   one cycle after pulse). 4/5 pass, owner unknown.
4. **sim_debug attempt #1** — `run_6b38c71a` on kimi-2.6: completed in 5.04s,
   **0 tool calls, 0 file writes**. Plain-text plan messages only ("I'll
   analyze the simulation failure systematically..."). Worker reported
   `status="completed"` — silent fail.
5. **sim_debug attempt #2** — `run_855bd2cd` on kimi-2.6 with stripped
   "mandatory: write_file NOW" prompt: 9.45s, **0 tool calls, 0 file writes**.
   Three plain-text assistant messages, no `tool_calls` field, no wrapped
   `<|tool_call_begin|>` tokens emitted. K2 parser fix
   (`core/action_parser.py:626 _convert_kimi_tool_calls`) is present but had
   nothing to parse.
6. **Retry budget exhausted** — orchestrator wrote the classification itself
   (`/tmp/orch_round2/simple_uart_tx/sim/mismatch_classification.json`):
   `owner=rtl_bug`, `suggested_fix_workflow=rtl-gen`.
7. **RTL repair routed** — `run_a8446d3b` on codex (rtl-gen :5522): 25s,
   `write_file` of full RTL with restored self-clear:
   `// Default low each cycle; STOP->IDLE assignment below creates a 1-cycle pulse.`
   `tx_done_irq <= 1'b0;` (rtl line 94).
8. **Re-run sim** — `5/5 PASS`, including `test_tx_done_irq_pulse`. Pipeline
   green.

## Architectural Validations

| Capability | Result | Evidence |
|---|---|---|
| Cross-workflow routing (`sim_debug → rtl-gen`) | ✓ | classification JSON + codex `run_a8446d3b` writes |
| Retry budget escalation (N=2 → fallback) | ✓ | two kimi silent fails before orchestrator stepped in |
| Multi-model heterogeneous pipeline | ✓ | deepseek (ssot) + codex (rtl) + kimi (tb) + deepseek (sim) + kimi (sim_debug, regressed) |
| Workflow binding guard (`/run` 403) | ✓ (prior runs) | workers rejected cross-workflow `/run` posts |
| Honest gate verdicts | partial | gate `result.json` files written, but **worker status="completed"** for both kimi silent fails — silent-fail detection NOT live on workers |

## Open Findings

### F1 — Kimi-2.6 `sim_debug` regression (reproducible)

On `sim_debug` workflow with a multi-file read + classify task, kimi-2.6 emits
sequential plain-text messages ("I'll fetch them in parallel", "I'll execute
the two writes immediately") with no `tool_calls` field and no wrapped K2
tokens. ReAct loop exits after the first turn with 0 iterations.

Hypothesis: the resumed conversation history (5–17 messages per session) is
pushing kimi out of the wrapped-token tool-call mode that the parser at
`core/action_parser.py:626` expects.

Mitigation already used: `rtl-gen` codex on the same task shape did work
(25s, full RTL write). So the orchestrator's correct move is **swap model**
on second retry of the same workflow.

### F2 — `agent_server.py` silent-fail detection patch landed in source, not on running workers

`core/agent_server.py:1131` now wraps the `terminal_status` decision with a
producing-workflows check:

```python
_PRODUCING_WORKFLOWS = {
    "ssot-gen", "rtl-gen", "tb-gen", "fl-gen", "cl-gen",
    "sim", "sim_debug", "lint", "cov",
}
if is_producing and not had_writes:
    if tracker.current == 0:
        terminal_status = "error"
        silent_fail_reason = (
            f"silent-fail: workflow={wf_norm} produced 0 tool calls "
            f"and 0 file writes"
        )
    elif tracker.current >= 3:
        terminal_status = "error"
        silent_fail_reason = (
            f"silent-fail: workflow={wf_norm} ran {tracker.current} "
            f"tool calls but wrote 0 files"
        )
```

Existing workers (:5521–:5525) are running pre-patch code, so the two kimi
silent fails in this run still reported `completed`. A worker restart cycle
will activate the detection.

### F3 — Pristine `rtl/simple_uart_tx.sv.pristine` no longer matches post-fix
RTL — that is expected; the codex fix is a real repair, not a revert. The
backup remains as evidence of the bug-injection delta.

## Replay

```bash
# 1. Inject bug
sed -i '' '93s|.*|            // BUG: tx_done_irq self-clear removed|' \
  /tmp/orch_round2/simple_uart_tx/rtl/simple_uart_tx.sv

# 2. Verify failure
cd /tmp/orch_round2/simple_uart_tx/tb/cocotb && \
  rm -rf sim_build results.xml && SIM=icarus python3 runner.py

# 3. Dispatch sim_debug (will silent-fail on kimi)
curl -s -X POST http://127.0.0.1:5525/run -H "Content-Type: application/json" \
  -d @/tmp/sim_debug_payload.json

# 4. Orchestrator fallback classification → route to rtl-gen
curl -s -X POST http://127.0.0.1:5522/run -H "Content-Type: application/json" \
  -d @/tmp/rtl_fix_payload.json

# 5. Re-run sim, expect 5/5 PASS
cd /tmp/orch_round2/simple_uart_tx/tb/cocotb && \
  rm -rf sim_build results.xml && SIM=icarus python3 runner.py
```

## Lessons

- `status="completed" + 0 writes` is the dominant silent-fail signature on
  this fleet. Silent-fail detection must live in the worker, not just in the
  orchestrator's eyeball.
- Kimi-2.6 on multi-step diagnostic workflows reverts to "planning out loud"
  when conversation history grows. Retry-with-same-model is wasted budget;
  retry-with-different-model is the correct next probe.
- Cross-workflow routing (`sim_debug → rtl-gen`) is functional once a
  classification JSON exists at the canonical path; the orchestrator can
  legitimately author that JSON itself when worker triage fails.
- A bit-palindrome (e.g., `0xA5`) hides MSB/LSB-ordering bugs from TB
  coverage. Earlier injection attempts of MSB-first reordering went
  undetected — that is a real TB coverage gap, not a routing failure.
- `cocotb-config` CLI is not in PATH on this host (only the Python module
  v1.9.2). The hand-written `runner.py` using `cocotb.runner.get_runner(
  "icarus")` is the workaround.
