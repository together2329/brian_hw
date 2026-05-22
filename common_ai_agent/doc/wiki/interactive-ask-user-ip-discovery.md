# Interactive Ask User IP Discovery

## Rule

Use the interactive `ask_user` flow when validating real SSOT discovery UX.
Headless, CI, and pipeline runs may execute the same workflow logic, but they do
not represent the real human Q&A surface.

## Why Earlier Runs Did Not Ask

The earlier `headless_workflow.py` runs were pipeline-style executions. When
`ssot-gen` needed human input, the run blocked on a `questions/*.json`
human-gate artifact instead of rendering interactive questions.

Another failure mode appeared when a seed requirements file or prior timer SSOT
was available: the agent treated those files as evidence and started filling the
SSOT before asking. That is useful for import-first flows, but it is not a clean
blank-slate Q&A test.

## Clean Discovery Protocol

1. Start an interactive common_ai_agent session, not `headless_workflow.py`.
2. Run `/new-ip <ip_name> <kind>`.
3. For blank-slate UX testing, explicitly forbid reuse of existing req, SSOT,
   RTL, TB, and same-family IP artifacts.
4. Require the first substantive action after scaffold to be `ask_user`.
5. Do not fill semantic SSOT fields from assumptions before the human answers.

## Current Proxy-User Decision

For `qa_timer_pure`, the human authorized Codex to answer as an RTL engineer
proxy user. Round 1 choices:

| Decision | Choice | Rationale |
| --- | --- | --- |
| Timer class | General-purpose peripheral timer | Best baseline for reusable SoC timer IP. |
| Register bus | APB4 slave | Peripheral-friendly bus with explicit error handling and clean verification surface. |
| Channels | 4 | Common MCU/SoC profile; enough complexity to exercise engineering flow without being oversized. |
| Counter width | 32-bit | Standard timer width; avoids toy RTL while keeping verification bounded. |
| Clock | 100 MHz | Conservative mid-range peripheral clock target. |

Round 2 choices:

| Decision | Choice | Rationale |
| --- | --- | --- |
| Count mode | Count-down only | Predictable timer FSM and clear zero-event semantics. |
| Prescaler | Per-channel 8-bit prescaler | Flexible enough for four channels without oversized divider logic. |
| Run modes | One-shot and auto-reload | Covers timeout and periodic interrupt use cases. |
| Match output | One match output per channel | Adds real external behavior without becoming a full PWM IP. |
| Interrupt sources | Per-channel match/count-zero | Keeps interrupt status/enable semantics unambiguous. |
| Reset polarity | Active low | Matches common AMBA/ARM peripheral reset convention. |

Round 3 choices:

| Decision | Choice | Rationale |
| --- | --- | --- |
| Match output behavior | Configurable toggle / pulse-high / pulse-low | Exercises real control fields and output verification without full PWM scope. |
| External capture/trigger | None | Keeps the block register-driven and avoids extra edge-detection/capture semantics. |
| Start/stop control | Explicit enable bit per channel | Avoids hidden write side effects and makes verification straightforward. |
| Interrupt clear | W1C | Standard, debug-friendly interrupt status behavior. |
| Per-channel registers | LOAD, COUNTER, CONTROL, PRESCALER, MATCH_OUT_CTRL, STATUS | Complete minimum register set for the selected feature profile. |
| Clock gating | No separate clock gating | Preserve a single clock domain; use internal enable conditions rather than generated gated clocks. |

## Related

- [[workflow-ownership-and-boundaries]]
- [[human-review-and-escalation]]
- [[full-flow-pipeline]]
