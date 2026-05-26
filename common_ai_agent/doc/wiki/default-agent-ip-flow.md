# Default Agent IP Flow — conversational read/edit/run/signoff loop

> **Updated**: 2026-05-26  
> **Scope**: How a default agent creates and signs off an IP directly, without forcing the user to operate workflow/stage commands.  
> **Reference run**: `apb_uart_txrx_demo` — APB UART TX/RX built, decomposed, simulated, covered, statically checked, and reviewed through direct agent actions.

## Why this flow exists

The common-engine/orchestrator flow is the production authority for repeatable pipeline evidence, but it is not always the most comfortable user interface. For users who are not yet fluent in AI workflow commands, the default agent style is often better:

```text
User intent
→ agent searches/reads the repo
→ agent edits files directly
→ agent runs compile/sim/lint checks
→ agent inspects evidence
→ agent repairs failures
→ agent writes a signoff bundle/report
```

The user can say ordinary things like:

```text
"UART 만들어줘"
"이 테스트 왜 깨져?"
"컴파일 에러 고쳐줘"
"orchestrator 말고 직접 해줘"
```

The agent absorbs the workflow complexity. The user does not have to choose `ssot-gen`, `rtl-gen`, `tb-gen`, `sim-debug`, or understand `human_gate`/`blocked` states unless those concepts are actually needed.

## Mental model

Default-agent IP creation is **pair-programming with evidence discipline**:

```text
Read → Plan → Edit → Run → Inspect → Repair → Record evidence → Review
```

It keeps the short, human-friendly debugging loop of a normal developer, while still borrowing the good parts of the governed pipeline: SSOT awareness, artifact freshness, compile/lint/sim proof, coverage proof, waiver recording, and adversarial final review.

## When to use this instead of visible orchestrator mode

Use the default-agent flow when:

- The user wants a natural-language, low-friction experience.
- The task is exploratory: "make this work", "find the bug", "build a demo IP".
- The user does not want to drive stage commands manually.
- Fast read/edit/run loops matter more than visible multi-worker orchestration.
- The repo already has enough local tools to compile/simulate/check the IP.

Use orchestrator/common-engine mode when:

- The goal is product-flow proof through ATLAS UI/API/worker path.
- Multi-stage DAG scheduling, owner routing, and durable worker handoff matter.
- CI/reproducibility/auditability is the main deliverable.
- The project needs strict separation of `ssot-gen`, `rtl-gen`, `tb-gen`, `sim-debug`, etc.
- Human-gate and authority boundaries must be presented as first-class UI state.

Recommended product shape:

```text
Default agent = front door for the user
Common engine/orchestrator = backend power tool when useful
```

## End-to-end IP flow

### 1. Capture intent in normal language

The user gives a minimal request, for example:

```text
"APB UART TX/RX 하나 만들어줘"
```

The agent should clarify only if truly blocked. Otherwise it should infer a reasonable bounded scope and begin by searching existing project structure.

Typical actions:

- Inspect repo layout with `pwd`, `find_files`, `list_dir`.
- Look for an existing IP directory, requirements, SSOT, RTL, testbench, or scripts.
- If the IP does not exist, scaffold the normal IP layout.

### 2. Establish the contract

Even in default-agent mode, the agent should not freehand RTL without a contract.

Preferred contract sources, in order:

1. Existing requirements document.
2. Existing `yaml/<ip>.ssot.yaml`.
3. User-provided protocol/register description.
4. Agent-authored minimal requirements/SSOT draft for a demo/bounded IP.

For `apb_uart_txrx_demo`, the contract included:

- APB3 slave top interface.
- UART TX/RX fixed 8N1 behavior.
- Register offsets for `CTRL`, `STATUS`, `BAUD_DIV`, `TXDATA`, `RXDATA`, `IRQ_STATUS`.
- Sticky error/IRQ behavior.
- Reserved-bit masking and APB error policy.

### 3. Implement RTL directly, but against the contract

The agent reads the contract and writes RTL-owned artifacts.

Good practice:

- Preserve exact top module name, parameters, and ports.
- Keep register map offsets explicit.
- Use small, reviewable modules when the IP is non-trivial.
- Update filelists immediately after adding/removing RTL files.
- Do not silently change requirements/SSOT to fit the RTL.

`apb_uart_txrx_demo` started as a working monolithic RTL and was then refactored into decomposed modules:

```text
rtl/baud_div_eff.sv
rtl/apb_uart_irq.sv
rtl/uart_tx_8n1.sv
rtl/uart_rx_8n1.sv
rtl/apb_uart_regs.sv
rtl/apb_uart_txrx_demo.sv
list/apb_uart_txrx_demo.f
```

The top-level interface stayed stable while implementation was decomposed.

### 4. Compile early

Before writing a large testbench, compile the RTL.

Typical checks:

```text
iverilog -g2012 -Wall -o <ip>/sim/<ip>.vvp -f <ip>/list/<ip>.f
sv_get_ports / sv_compile when available
```

Acceptance examples:

- Filelist references all RTL files.
- Top module parses with expected ports.
- No unintended dependencies.
- Compile command returns zero.

### 5. Write a directed self-checking testbench

The default-agent flow favors a simple local testbench first, because it shortens the loop.

A useful directed TB should include:

- Clock/reset generation.
- DUT instantiation with every port connected.
- Bus tasks, e.g. APB read/write.
- Protocol stimulus helpers, e.g. UART frame drive/decode.
- Scoreboard event logging.
- JSON/CSV result artifacts.
- VCD dumping.
- Named scenario IDs.

For `apb_uart_txrx_demo`, the directed TB covered 12 scenarios:

```text
SC_APB_RESET
SC_APB_RW
SC_APB_INVALID
SC_TX_ONE_BYTE
SC_TX_BACK_TO_BACK
SC_TX_IRQ
SC_RX_ONE_BYTE
SC_RX_BACK_TO_BACK
SC_RX_FRAMING_ERROR
SC_RX_OVERRUN
SC_RX_IRQ
SC_BAUD_VARIANTS
```

### 6. Add a reproducible run harness

Do not rely on ad-hoc shell history. Create a script such as:

```text
sim/run_sim.sh
```

It should:

- Enforce running from the IP root.
- Clean stale artifacts before execution.
- Compile DUT + TB.
- Run simulator with logs.
- Fail nonzero on compile/sim/scoreboard failure.
- Require JSON/CSV/VCD outputs.

This is where default-agent work starts becoming reproducible evidence instead of just an interactive fix.

### 7. Iterate on failures by reading raw evidence

The core default-agent loop is:

```text
Run
→ read sim.log / JSON / CSV / waveform manifest
→ identify actual failing check
→ decide owner: RTL vs TB vs script vs stale artifact
→ patch smallest responsible file
→ rerun from clean state
```

Important habits:

- Read the failing artifact before editing.
- Prefer minimal targeted fixes over rewrites.
- Clean simulator build/cache artifacts when needed.
- Never claim a test passed without running it.
- Record the exact evidence used for approval.

For `apb_uart_txrx_demo`, the directed run was repaired until:

```json
{"passed": true, "scoreboard_pass": 30, "scoreboard_fail": 0, "scenario_count": 12}
```

and `scoreboard_events.csv` had no `FAIL` rows.

### 8. Add coverage evidence

A directed simulation can pass while still under-testing behavior. The default-agent flow should produce explicit coverage evidence, even if it is a lightweight JSON summary rather than a full EDA coverage database.

For each required bin, record:

- Bin ID/name.
- Required vs optional.
- Hit/missed/waived status.
- Evidence source: scenario, scoreboard row, log, or waveform.
- Rationale for any waiver.

For `apb_uart_txrx_demo`, coverage recorded:

- 12/12 directed scenarios hit.
- 23/23 required bins hit.
- 0 missed bins.
- 100% effective directed coverage.

### 9. Record waveform/debug evidence

A passing scoreboard is not the same as debuggability. The flow should confirm that waveforms exist and key signals are observable.

A useful `waveform_manifest.json` includes:

- VCD path.
- File size.
- Generation command.
- Whether waveform generation was testbench-only.
- Required top-level signal observability.
- Optional internal debug signal observability.

This prevents the common problem where a run is green but the next maintainer cannot debug failures.

### 10. Add constrained-random smoke/regression when useful

After directed tests pass, add a small random harness if the IP has meaningful state-space variation.

Good controls:

```text
+SEED=<n>
+TXNS=<n>
+VCD=<0|1>
```

Good artifacts:

```text
random_seed_<seed>.log
random_seed_<seed>.json
random_seed_<seed>.csv
random_regression_summary.json
```

For `apb_uart_txrx_demo`, a smoke seed preserved the requested seed and reported `scoreboard_fail=0`.

### 11. Run static/lint/signoff checks

The default-agent flow should still include objective static evidence.

Typical checks:

- SSOT validation if an SSOT exists.
- RTL compile.
- Lint, e.g. Verilator.
- Optional synthesis/check, e.g. Yosys, with explicit waivers for tool limitations.
- Targeted structural checks: ports, register offsets, reset constants, filelist completeness.

Record a structured result such as:

```text
verify/static_signoff_results.json
```

The important rule is not "all tools must be available". The rule is:

> Available checks must be run, unavailable/limited checks must be explicitly recorded, and waivers must be justified.

### 12. Create a signoff bundle/report

At the end, collect evidence in one place.

Suggested files:

```text
.session/<ip>/signoff/final_signoff_bundle.json
.session/<ip>/signoff/final_signoff_report.md
```

The bundle should list evidence paths with:

- Exists/readable status.
- Size or timestamp where useful.
- Summary fields from JSON artifacts.
- Commands used.
- Residual risks/waivers.
- Recommendation based only on fresh artifacts.

### 13. Perform adversarial self-review

Before final approval, reread the ground-truth artifacts and try to disprove the signoff claim.

Checklist:

- Are all referenced files present and readable?
- Are sim results fresh relative to latest RTL/filelist changes?
- Does JSON summary match raw CSV/log evidence?
- Are there hidden `FAIL` rows?
- Are coverage claims backed by actual scenarios/events?
- Are waivers explicit and bounded?
- Did the final RTL refactor invalidate previous evidence?

For `apb_uart_txrx_demo`, the final adversarial review produced an explicit `GO` only after rereading raw artifacts and confirming no stale/missing/contradictory evidence.

## Todo discipline in default-agent mode

For multi-step IP work, keep a visible todo ledger. Each task should have:

- Concrete deliverable.
- Implementation detail.
- Acceptance criteria.
- Completed state when work is done.
- Approved state only after evidence review.

The useful pattern is:

```text
complete the task
→ mark completed
→ reread/check evidence critically
→ approve or reject with exact evidence
```

This gives the default-agent flow some of the same auditability as the orchestrator flow without forcing the user to operate the orchestrator.

## What not to do

Avoid these shortcuts:

- Do not edit SSOT/requirements just to make RTL pass.
- Do not approve from LLM prose alone.
- Do not accept stale artifacts after RTL/TB changes.
- Do not hide simulator/lint limitations.
- Do not skip raw log/CSV/JSON inspection.
- Do not make every small debugging task a full pipeline-stage problem.

## Relationship to the canonical pipeline

This page does not replace [[full-flow-pipeline]]. It describes a friendlier **execution style** for interactive use.

Mapping:

| Canonical concern | Default-agent expression |
|---|---|
| Requirements / SSOT | Agent reads or drafts the contract before RTL |
| RTL-gen | Agent writes RTL-owned files directly |
| Lint | Agent runs local compile/lint/static checks |
| TB-gen | Agent writes directed/random local TBs |
| Sim | Agent creates and runs reproducible sim scripts |
| Coverage | Agent writes coverage/result JSON tied to scenarios |
| Sim-debug | Agent reads logs/CSV/VCD and patches owner file |
| Goal/signoff audit | Agent writes bundle/report and adversarial review |

For product claims, especially UI/orchestrator claims, still validate through the common engine/UI path. For building and debugging an IP with a novice or conversational user, default-agent mode is usually the better front door.

## Reusable prompt to start this flow

A user can start with:

```text
Default agent로 <ip_name> IP 만들어줘.
요구사항/SSOT/RTL/TB/sim/coverage/signoff evidence까지 직접 read-edit-run 루프로 진행해줘.
Orchestrator stage 명령은 사용자가 직접 고르지 않아도 되게 해줘.
```

The agent should then manage the flow, ask only necessary clarification questions, and report progress in evidence terms rather than workflow jargon.

## Related

- [[full-flow-pipeline]]
- [[agent-autonomous-ip-implementation-pattern]]
- [[golden-todo-evidence]]
- [[workflow-ownership-and-boundaries]]
- [[orchestrator-worker-handoff]]
- [[pipeline-progress-debugging]]
