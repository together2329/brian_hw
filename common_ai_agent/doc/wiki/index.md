# common_ai_agent Wiki

This wiki is the cross-linked operating map for common_ai_agent. It is optimized
for long-context LLMs and agent handoffs: read the linked pages in order, then
follow the source docs for implementation detail.

## Fast Context

Use this first when a future LLM session needs the current system shape quickly.
This section is additive; it does not replace the reading order below.

| Need | Read |
|---|---|
| Overall source-of-truth map | [[common-ai-agent-map]] |
| What owns SSOT/RTL/TB/sim/coverage artifacts | [[workflow-ownership-and-boundaries]] |
| How to verify test quality / which test gates which feature | [[atlas-test-feature-coverage]] |
| 2026-05-23 test-hardening session summary | [[atlas-test-hardening-2026-05-23]] |
| How to run/debug the visible product flow | [[atlas-pipeline-screen]] + [[pipeline-progress-debugging]] |
| How to control the visible in-app browser | [[atlas-browser-control-runbook]] |
| How Pipeline worker detail opens real workspaces | [[atlas-pipeline-worker-workspace-jump]] |
| Guide tab + Architect "My IPs" landing (mock SoC removed) | [[guide-tab-and-architect-my-ips-20260527]] |
| Andes external RTL DB wiki + optional `ATLAS_RTL_DB_WIKI` / `ATLAS_EXTERNAL_DB_WIKI` pointer | [[andes-rtl-db-wiki-20260527]] |
| Reusable external RTL DB adapter guide | [[external-rtl-db-integration-guide]] |
| LLM Wiki vs knowledge graph / node-edge-triple / domain knowledge management Q&A | [[llm-wiki-knowledge-graph-discussion-20260602]] |
| SSOT datasheet authoring — demo-grade via custom_blocks / timing mapping / FSM | [[ssot-datasheet-authoring-20260527]] |
| Review note for Atlas single-worker readiness / warmup refactor | [[atlas-refactoring-review-20260528]] |
| Tech direction (language/runtime/build): keep Python backend, finish TSX + Vite build cutover, Go/Rust/Bun/Tauri surgical only | [[tech-direction-recommendation-20260529]] |
| Frontend modernization arc (overview): .jsx→.tsx migration + Vite cutover (ATLAS_FRONTEND_MODE) + Tauri desktop + gpt-5.5 | [[frontend-modernization-2026-05-29]] |
| 테스트 방법론 — 4층 피라미드 + green-while-broken 교훈 + 프론트 컷오버 전 E2E 필수 | [[testing-methodology]] |
| uart_tx 직접 end-to-end 실행 — flow 골격 검증 + MSB-first mutation으로 shallow-observation silent-PASS 실증 + same-cycle 생성기 경계 + 직접 구동 cheat-sheet (audit=mutation kill-rate 권고) | [[uart-tx-end-to-end-findings-20260530]] |
| MCTP assembler scratch req-to-audit run — AXI4/VDM/MCTP/SRAM/APB scope, truth_coverage refresh, local signoff 18/18 pass, mutation advisory interpretation, post-signoff RTL risks | [[mctp-assembler-scratch-flow-20260531]] |
| General IP 시행착오 종합 — PyMTL식 FL/CL/RTL, small IP/UART/SPI/CPU/MCTP lessons, mutation/formal/truth_coverage 경계, direct SSOT 허용 정책 | [[general-ip-flow-trial-and-error-20260601]] |
| Evidence contract proposal — requirement를 atomic obligation / scenario / observable / pass condition / scoreboard row로 연결하는 다음 traceability layer | [[evidence-contract-obligation-traceability]] |
| Contract reflection workflow — requirement→obligation→contract_ref→stage reflection→evidence→closure 6층 모델; SSOT→FL→CL→RTL→TB→scoreboard trace와 MCTP v3 semantic slice 포함 | [[contract-reflection-workflow]] |
| ATLAS vite 프론트 자동 E2E 검증(실브라우저) 런북 + `scripts/atlas_vite_e2e_verify.sh` | [[atlas-vite-e2e-verification]] |
| Sim Debug RTL module-signal panel (pyslang ports+internal, in/out/internal filter, regex search, Ctrl+W/right-click→wave, wave-scroll fix, 50/50 split) | [[sim-debug-module-signals-2026-05-30]] |
| Sim Debug agent tool `sim_debug` (VCD parser + pyslang; show/goto/cursor/trace/find/value; file-intent + UI polling channel) | [[sim-debug-agent-tool-2026-05-31]] |
| Sim Debug waveform renderer decision: current React/SVG row renderer, why not React Flow, future Canvas trigger, VCD slice zero-extension | [[sim-debug-waveform-renderer-2026-05-31]] |
| Sim Debug full feature review: 4-pane UI, loading/preload, scoped signal identity, source selection, waveform interactions, tool/API contracts, verification and risks | [[sim-debug-feature-review-2026-05-31]] |
| Sim Debug requirements ledger: four-pane loading, source/signal multi-select, exact slices, waveform RC/radix/cursors, tool-call lookup, pyslang/VCD contracts | [[sim-debug-requirements-2026-06-01]] |
| Babel/legacy-jsx retirement cutover — PAUSED progress + resume plan (Step1 flip done; Round1 partial; 4 decisions; Rounds 2–4) | [[babel-retirement-cutover-20260529]] |
| Local IP-root + thin LLM-license server (desktop-app arch): already half-built via --root, Tauri = delivery not enabler; + remote-brain/local-hands variant | [[local-iproot-thin-llm-server-arch-20260529]] |
| Desktop local tool execution PLAN (2026-06-03): "tools local, LLM on server" (=Variant A) removes the 30-worker ceiling; dispatch_tool seam, git-sync secured by B1 _fs_authz gate, EDA packaging (pyslang≫iverilog>verilator), phased roadmap | [[desktop-local-tool-execution-plan-20260603]] |
| Run Mode / Exec Mode and SSOT provenance policy | [[run-mode-and-provenance-policy]] |
| Single active session worker + orchestrator worker chat + future rtl-gen subworker lanes | [[atlas-single-active-orchestrator-subworkers-20260603]] |
| Atlas DB Router + Runtime DB sharding concept for multi-user prompt/worker write isolation | [[atlas-db-router-runtime-sharding-20260602]] |
| Atlas context root model proposal — user/session/IP/workflow isolation, worker cwd at IP root, command/todo/context/SCM/jobs migration plan, and IP-local workflow root rule | [[atlas-context-root-model-20260603]] |
| Atlas context root deep test plan — branch-level Web/Desktop/API/DB/worker verification before merge | [[atlas-context-root-deep-test-plan-20260604]] |
| Admin operational dashboard priorities from the real local DB snapshot: inactivity, unattributed cost, queue backlog, stale workflows, identity gaps | [[admin-operational-dashboard-db-snapshot-20260603]] |
| Why headless is not product-flow authority | [[pipeline-progress-debugging]] |
| Current CPU handoff / approval / README status | [[arm-m0-min-current-status]] |
| Multi-user or shared-worker collision risk | [[multi-user-worker-isolation]] + [[multi-user-worker-conflicts]] |
| Orchestrator/worker handoff concept | [[orchestrator-worker-handoff]] + [[orchestrator-worker-handoff-review]] |
| Orchestrator-only product plan + Phase 3 LLM loop implementation | [[orchestrator-chat-only-product-plan]] + [[orchestrator-llm-loop-phase3]] |
| Proposed reuse of `core/react_loop.py` for the orchestrator (review needed) | [[orchestrator-loop-on-react-loop-plan]] |
| Cross-reference of orchestrator wiki against source code (accuracy audit) | [[orchestrator-verification-report]] |
| End-to-end orchestrator-loop validation plan on a real scratch IP | [[e2e-orchestrator-validation-plan]] |
| PL330 visible UI Orchestrator/worker lessons | [[pl330-real-orchestrator-ui-lessons-20260517]] |
| ATCDMAC100 document-flow honesty record | [[atcdmac100-document-flow-ui-honesty-20260518]] |
| Evidence approval and TodoTracker behavior | [[golden-todo-evidence]] |
| When to update wiki during development | [[wiki-curation-policy]] |
| How agent autonomously implements a new IP end-to-end | [[agent-autonomous-ip-implementation-pattern]] |
| Default-agent conversational IP creation flow for non-expert users | [[default-agent-ip-flow]] |
| Current apb_uart_txrx_demo signoff (framed TX/RX engines) | [[apb-uart-enhanced-signoff-20260527]] (earlier 8n1 record, superseded: [[apb-uart-real-uart-signoff-20260527]]) |
| Full orchestrator workflow bring-up history (system_prompt, multi-model worker spawn, trace, UI orchestra view) | [[orchestrator-workflow-bring-up-20260517]] |
| pytest collection crash fix (pytest_pymtl3 stale hook) and canonical PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 invocation | [[atlas-pytest-hygiene]] |
| Side-by-side LLM provider comparison on the same SSOT input | [[triple-llm-rv32i-experiment]] |
| Orchestrator chat UX overhaul 2026-05-19 (backend persist, endpoint contract bug, frontend hydrate regression) | [[orchestrator-chat-ux]] |
| UI resolution + theme matrix verify 2026-05-19 (12 cells across viewports/views/themes, WKWebView viewport-set limitation, single-fix proposal) | [[ui-resolution-matrix-20260519]] |
| Flow fixes live verification 2026-05-19 (5 landed fixes — seed/workspace/cost/import/db-path — 0/5 PASS, evidence + follow-ups) | [[flow-fixes-verify-20260519]] |
| Flow fixes R2 cross-workspace verification 2026-05-19 (5 follow-up fixes across 3 IPs — 2/5 PASS, frontend URL+chat-mount regress, backend seed/cost partial) | [[flow-fixes-r2-verify-20260519]] |
| Flow fixes R3 real-textarea-typing verification 2026-05-19 (4 R3 fixes #17–#20 — 6/7 PASS, full UI end-to-end via real keystrokes, ssot.yaml top_module=p0_cnt; remaining: workspace_id bifurcation in ip_blocks) | [[flow-fixes-r3-verify-20260519]] |
| atlas.db FK integrity audit 2026-05-19 (5 FK checks across home + PWD DBs — all PASS; Q4 apparent orphans in llm_calls.run_id are polymorphic refs to orchestrator_runs, zero truly dangling rows) | [[db-fk-audit-20260519]] |
| Single main-loop restoration verify 2026-05-19 (ATLAS_SINGLE_MAIN_LOOP=1 → atlas_ui auto-spawns one --all-workflows worker on 5601; ssot+rtl sequential dispatch handled by same PID; spawn-path bug `SOURCE_ROOT/main.py` → `HERE/main.py` fixed mid-verify) | [[single-main-loop-restore-20260519]] |
| Auth cookie expiry + multi-session policy 2026-05-19 (Max-Age=90 days, HttpOnly, Secure absent on localhost, logout is client-side only — no server-side revocation, deterministic HMAC token means all logins share same cookie value) | [[auth-cookie-expiry-20260519]] |
| SSOT import multi-format converter 2026-05-19 (`/api/ssot/import/upload` now accepts pptx/docx/pdf/html; markitdown via subprocess on /opt/homebrew/bin/python3.10 because atlas_ui is on 3.9; emits `originals/<file>` + `<base>.md`; corrupt files keep original and continue batch) | [[ssot-import-multi-format-20260519]] |
| End-to-end SSOT conversion flow 2026-05-19 (upload → /import → /grill-me → /to-ssot → check_ssot_disk.sh; why each stage is split for human audit; file index + chaining diagram in Atlas UI) | [[ssot-conversion-flow-20260519]] |
| SSOT export reverse direction 2026-05-19 (`/api/ssot/export?ip=&format=md|docx|html` renders `<ip>/yaml/<ip>.ssot.yaml` → `<ip>/doc/<ip>_ssot.<ext>` deterministically; md via yaml walker, html via python-`markdown`, docx via python-docx; pdf deferred — see [[ssot-conversion-flow-20260519]] `## Export (reverse direction)`) | [[ssot-conversion-flow-20260519]] |
| DAG pipeline payload, worker command map, and signoff evidence checklist | [[atlas-dag-ip-flow-runbook]] |
| Clean interactive `ask_user` discovery protocol | [[interactive-ask-user-ip-discovery]] |
| `workspace.jsx` decomposition plan — historical design rationale; decomposition realized via the .tsx migration | [[workspace-jsx-decomposition-plan]] |

Current practical rule: final product-flow claims should be validated through
the same ATLAS UI/API/worker path users run, not only through headless runs.
Headless remains useful for reproduction, contract tests, and workflow-script
regression.

## LLM Reading Order

1. [[common-ai-agent-map]] — mental model and source-of-truth hierarchy.
2. [[workflow-ownership-and-boundaries]] — who owns each artifact and what must not be edited directly.
3. [[ssot-qa-workbench]] — SSOT authoring UX: import, interview, requirement progress, and To SSOT. Internal pass mechanism: [[ssot-gen-pass-pipeline]] — LLM → deterministic canonicalize → validator → LLM-repair loop, with the actual progress-log signatures and `ATLAS_HEADLESS_LLM_TIMEOUT` knob.
4. [[full-flow-pipeline]] — SSOT to signoff stage order and commands.
4a. [[default-agent-ip-flow]] — conversational front-door flow where the default agent hides stage jargon and directly performs read/edit/run/signoff loops for IP creation.
4b. [[truth-coverage-gate]] — direct-SSOT or req-ledger locked-truth coverage gate required before signoff.
4c. [[general-ip-flow-trial-and-error-20260601]] — consolidated trial/error record behind the current General IP workflow.
4d. [[evidence-contract-obligation-traceability]] — proposed next traceability layer between SSOT/truth_coverage and cocotb scoreboard evidence.
4e. [[contract-reflection-workflow]] — proposed `contract_ref` reflection layer that ties SSOT/FL/CL/RTL/TB/scoreboard evidence together.
5. [[run-mode-and-provenance-policy]] — why `Starter` / `Engineering` / `Signoff` are work-maturity modes, why `Exec Mode` is separate, and how clean SSOT YAML pairs with resolved SSOT plus sidecar provenance.
6. [[rtl-gen-ssot-contract]] — why rtl-gen must follow SSOT exactly before downstream stages run.
7. [[workflow-feedback-and-scheduling]] — worker-aware serial/DAG scheduling and workflow repair feedback.
8. [[orchestrator-worker-handoff]] — orchestrator agent, live worker dispatch, JSON handoff fallback, and `/take` semantics. Spec-vs-shipped gaps tracked in [[orchestrator-worker-handoff-review]]. Concrete shipped realization: [[parallel-todo-sub-agent-workers]] — `parallel_todo_dispatch` fans a TODO batch out to N clean sub-agent workers (auto-picks from claude-cli / cursor-cli / gpt-5.3-codex / glm / deepseek / kimi by available credentials + cheapest cost).
9. [[multi-user-worker-isolation]] — current collision risk for live HTTP workers, what is already user-scoped, what is still URL-scoped, and the lease/gateway fix needed for safe multi-user operation. Companion: [[multi-user-worker-conflicts]] — same risk surface with explicit source-line citations (`core/agent_server.py:35,103,117,664,703`) and four named failure modes (F1 wrong-root writes, F2 mixed registry/session state, F3 wrong-workflow acceptance, F4 provider/credential contention).
10. [[pipeline-progress-debugging]] — how to debug real UI/worker progress versus headless reproduction logs; `/api/pipeline/state.progress_debug`, `/api/pipeline/progress-debug`, and the rule that product claims must use the same UI/API/worker path as users.
11. [[rtl-version-run-history]] — SSOT/RTL/TB artifact version anchors for workflow evidence.
12. [[golden-todo-evidence]] — TodoTracker, evidence approval, and human review states.
13. [[provider-and-llm-call-accounting]] — provider normalization and how to count one LLM call.
14. [[human-review-and-escalation]] — when to stop automation and ask for product/spec authority.
15. [[deterministic-emit-stages]] — why fl-model-gen and cl-model-gen run without an LLM, and what contract that places on the upstream SSOT.
16. [[karpathy-llm-wiki-pattern]] — reference page for Andrej Karpathy's LLM Wiki concept (3-layer markdown + index + log + schema; no RAG, no vector DB) and how `doc/wiki/` already aligns to it.
17. [[llm-wiki-knowledge-graph-discussion-20260602]] — follow-up Q&A on LLM Wiki vs knowledge graph, node/edge/triple terminology, service landscape, and domain knowledge management usefulness.
18. [[wiki-curation-policy]] — what to capture, when to capture it, and what to deliberately leave out of the wiki. Lives next to the code so the policy evolves with usage.

## UI

- [[atlas-pipeline-screen]] — `◫ Pipeline` top-level screen: click-to-run stage dispatcher, per-stage scoresheet, owner-aware blame routing.
- [[atlas-browser-control-runbook]] — exact recipe for future agents to open the in-app Browser, reload ATLAS, inspect DOM/screenshot state, click/type with Playwright locators, and move/click/type by mouse coordinates.
- [[atlas-pipeline-worker-workspace-jump]] — how `ssot-gen`, `rtl-gen`, and `tb-gen` worker detail clicks open the real workflow workspace, chat history, and representative artifacts.
- [[run-mode-and-provenance-policy]] — placement and semantics for global `Run Mode` plus `Exec Mode`, and the Pipeline-specific evidence summary.
- [[atlas-pipeline-db-state]] — how `/api/pipeline/state` derives state (DB-first, FS-fallback for hand-placed evidence) and the migration plan for moving KPI dots fully into the DB.
- [[pipeline-progress-debugging]] — shared observability contract for worker jobs, headless reproduction logs, stuck LLM calls, and same-environment validation.
- [[ui-design-references]] — external UI checkouts under `external_refs/` (currently `nexu-io/open-design`) and which patterns inform ATLAS.
- [[tauri-desktop-shell]] — native desktop window for ATLAS (Tauri v2, Option A webview → running backend) for distribution and native file access.
- [[react-flow-adoption-20260529]] — decision to adopt `@xyflow/react` v12 narrowly (SoC Architect first) in the next cycle, unblocked by the Vite cutover.
- [[interactive-ui-diagrams-2026-05-23]] — standalone `interactive_ui/` gallery of dependency-free single-file HTML diagrams plus their generators.

## Reference Runs (working examples on real IPs)

Reloadable snapshots live in [`ip_examples/ref_ip_flow/`](../../ip_examples/ref_ip_flow/README.md)
— each run is portable (IP artifacts + ATLAS sessions + seeds) so it can
be loaded on a different machine and inspected without recreating the DB.

- [[arm-m0-min-pipeline-run]] — minimal ARMv6-M Thumb CPU, full ssot→lint pipeline with green compile/lint/sim/function+cycle coverage; 2026-05-17 refresh shows 39/39 FL-vs-RTL goals pass and final human-approved `req` signoff approved 2026-05-17 (see [[arm-m0-min-current-status]]). See `arm_m0_min/doc/arm_m0_min_completion_audit.md` for the prompt-to-artifact checklist.
- [[arm-m0-min-current-status]] — current project-level handoff page for the same CPU; points reviewers to `arm_m0_min/README.md`, the user handoff, and the `approve_locked_scope` approval boundary.
- [[mini-cpu-rerun-20260517]] — existing `NEW_IP_CPU/mini_cpu` rerun from a scratch copy; SSOT is non-canonical, `equiv-goals` blocks, lint fails, and manual SV sim reaches only 2/4 checks passing (2026-05-17).
- [[gpio-serial-pipeline-run]] — `simple_gpio_lite` serial smoke run; RTL clean, tb-gen blocks on prose-only FunctionalModel `ssot_question` gaps, and ssot-gen now catches the same missing machine-rule transactions before downstream token spend (2026-05-16).
- [[gpio-orchestrator-multiworker-run]] — `gpio_orch_scratch` Atlas orchestrator plus author/verify worker run; tracks current RTL gate/tool-evidence bugs and UI run-status gaps (2026-05-16).
- [[quad-spi-orch-run-20260517]] — `quad_spi_ctrl` brand-new orchestrator + multi-worker + multi-sub-agent run on a Quad SPI APB peripheral; reaches `tb-gen` clean, `sim` cocotb PASS with 31 SOFT_EQ_MISMATCH → `sim-debug` owner-routes 28 → `rtl-gen`, 3 → `tb-gen`. Surfaces tb-gen "top defaults to IP name" bug and SSOT redundant-sub-module emission patterns (2026-05-17).
- [[octa-ddr-spi-orch-run-20260517]] — `octa_ddr_spi_ctrl` from-scratch run on an Octal DDR SPI APB peripheral (lane modes 1/2/4/8 SDR + 8 DDR). Re-runs the QUAD SPI pipeline with the seven workflow fixes applied (600 s LLM timeout, SSOT.top_module.name as single top authority, SSOT structural invariants, /run workflow-binding guard, flow-mapping bracket auto-repair, filelist.rtl includes top file, `_ensure_sub_modules` respects top_module.name). Reaches `sim-debug` with 67/67 goals checked, 43 PASS, 24 mismatches owner-routed (18 rtl-gen, 6 tb-gen). Same Frontier-A/B/C classification surface as quad-spi-orch-run; no manual SSOT edits beyond a single `resolve_rtl_blockers` answer (2026-05-17).
- [[round2-retry-budget-cross-workflow-routing-20260517]] — `simple_uart_tx` end-to-end orchestrator-routing validation with deepseek/codex/kimi worker mix. Injected RTL bug (tx_done_irq self-clear removed) → kimi `sim_debug` silent-failed twice (0 tool calls, 0 writes, status mis-reported as "completed") → retry budget exhausted → orchestrator (gpt-5.5) authored the mismatch classification → codex `rtl-gen` restored the self-clear → re-run cocotb 5/5 PASS. Documents the kimi-on-`sim_debug` regression and the `core/agent_server.py:1131` silent-fail detection patch needed to surface this as `status="error"` (2026-05-17).
- [[atcuart100-pipeline-run]] — Andes 16550-class APB UART (8 modules, dual-clock pclk/uclk, FIFO+DMA+modem) full canonical DAG end-to-end; 5-LLM parallel SSOT-gen failed (codex truncate, kimi/deepseek HTTP 400, glm/claude envelope blocked) → Claude direct-authored 70 KB SSOT to unblock; compile clean, sim ran, sim-debug 64/64 owner=rtl-gen, goal-audit 12/16 passed; includes 7 lessons (monolithic-SSOT single-shot limit, validator chain effectiveness, packet-parallel vs multi-provider trade-off, YAML flow-mapping bracket trap, file-lock against runaway helpers, stale headless_run.json + monitor PID-scope) (2026-05-17).
- [[atcwdt200-pipeline-run-20260517]] - Andes APB watchdog timer from legacy `/Users/brian/Desktop/andes/atcwdt200`; SSOT/FL/CL/equiv/RTL/TB/lint evidence is clean, cocotb infra passes, and sim stops correctly on `[SIM ESCALATE] scoreboard_failed=11`. Captures the `rtl_contract.json`, comment-stripped audit evidence, version-register FL rule, and internal-state observability lessons (2026-05-17).
- [[atcwdt200-flow-debugging-lessons]] — compact reusable debugging rules from the same watchdog run: comment-stripped RTL audit evidence, provenance gate shape, macOS `PYTHONPYCACHEPREFIX`, and scoreboard-vs-cocotb signoff.
- [[atcwdt200-ssot-rtl-tb-flow-시행착오-2026-05-17]] — Korean/English session log for the ATCWDT200 SSOT→RTL→TB flow, including exact commands and mismatch owner hypotheses.
- [[dma-real-sim-debug-knowhow]] — `dma_real` 4-channel DMA controller (APB slave / AHB-Lite master) sim-debug 완주 노하우: 1-cycle pulse latch 패턴, cocotb+Icarus VVP 캐시 함정, scoreboard contract 통과 요령, coverage 100% 달성 전략, goal-audit 15/16 체크리스트. 최종 성과: Simulation 6/6 PASS, Coverage 58/58 bins, Goal Audit 15/16 (req human gate only) (2026-05-17).
- [[agent-autonomous-ip-implementation-pattern]] — "Wiki만 보고 DMA 구현 완주한 패턴" 메타 분석: 에이전트가 문서를 선별하고, 합리적 순서를 도출하고, 소유자 규칙을 준수하고, 증거 기반으로 자가 교정하고, 노하우를 기록하는 5가지 자율 실행 능력의 분해. 14태스크 타이임라인, 7개 결정 갈림길, arm-m0-min 비교, 재사용 템플릿 포함 (2026-05-17).
- [[triple-llm-rv32i-experiment]] — `rv32i_min` SSOT 동일 입력을 3개 LLM provider(claude / gpt-codex / glm)에 병렬로 흘려 동일 파이프라인(ssot-gen → fl/cl → equiv-goals → rtl-gen)을 거치게 한 비교 실험. provider별 출력 품질·실패 패턴·재시도 비용을 한 시야로 측정.
- [[orchestrator-workflow-bring-up-20260517]] — `workflow/orchestrator/` 디렉토리가 실재로 만들어진 날의 풀 세션 기록: 13파일(system_prompt + routing_policy + retry_budget + 7 slash commands + run-to-green template) 생성, 5 worker × 4 model spawn (glm / gpt-5.3-codex / deepseek / kimi), trace JSONL 인프라(`core/orchestrator_trace.py` + `/api/orchestrator/trace`), Pipeline UI orchestra view (WorkerOrchestraBar + PendingQABanner + OrchestratorTraceStrip + 양방향 화살표), 그리고 sub-agent fire-and-forget 패턴이 interactive workflow(ssot-gen)에서 hang 되는 mismatch 발견 + QA card escape hatch fix까지. e2e 검증: real-LLM orchestrator(gpt-5.5 xhigh)가 3개 worker에 분산 dispatch + sim_debug worker 단일 dispatch + scratch `simple_counter` SSOT 생성 후 pending QA로 자동 정지 (2026-05-17).
- [[pl330-real-orchestrator-ui-lessons-20260517]] — visible ATLAS UI validation on `pl330realverify`: user challenged fake-looking progress, real Browser/API/worker evidence was required, Orchestrator must dispatch workers instead of direct worker chat, RTL handoff should be `/ssot-rtl <ip>` rather than a giant TODO payload, and active scoped job dedupe prevents duplicate loading runs. RTL compile/lint passed; full RTL audit still had open required TODOs. Also records the accidental `tb-gen` dispatch/cancel that polluted the TB stage card (2026-05-17).
- [[atcdmac100-document-flow-ui-honesty-20260518]] — corrective record for the Andes ATCDMAC100 PDF-based DMA flow. Real backend/common-engine artifacts were produced through SSOT, models, RTL, lint, TB, sim, coverage, goal-audit, synthesis, and pre-route STA, but the run is explicitly not valid ATLAS UI Orchestrator product-flow proof because most stages were driven by backend scripts rather than right-side Orchestrator chat. Records STA setup failure (`hclk@10ns` WNS `-22.560ns`) and interrupted PnR route.
- [[apb-uart-enhanced-signoff-20260527]] — current `apb_uart_txrx_demo` signoff: enhanced v2+ bounded UART with framed TX/RX engines, configurable framing, TX/RX FIFOs, IRQ/error behavior, RX timeout, and loopback regression evidence. Supersedes the earlier 8n1 [[apb-uart-real-uart-signoff-20260527]] record.
- [[orchestrator-new-ip-to-pnr-recipe-2026-05-23]] — orchestrator recipe for taking a brand-new IP from SSOT through to PnR.
- [[atlas-new-ip-recipe]] — concise recipe for starting a new IP end-to-end in ATLAS.

## Debugging And Operations

- [[admin-operational-dashboard-db-snapshot-20260603]] — first stop for what the Atlas admin home screen should prioritize from the real `~/.common_ai_agent/atlas.db`: unattributed LLM cost, queue backlog, stale workflows/sessions, inactive users, and identity integrity.
- [[pipeline-progress-debugging]] — first stop for "is it really running?", "is worker or LLM stuck?", and "where is progress recorded?"
- [[atlas-browser-control-runbook]] — first stop for "use the web browser so I can see it", visible mouse/keyboard interaction, and browser reload after backend code changes.
- [[multi-user-worker-isolation]] — first stop for "could this worker belong to another user/IP/session?"
- [[provider-and-llm-call-accounting]] — first stop for "how many LLM calls/tokens/cost did this workflow use?"
- [[rtl-version-run-history]] — first stop for "which SSOT/RTL/TB version did this lint/sim/coverage/syn/sta/pnr run use?"
- [[atlas-dag-ip-flow-runbook]] — first stop for DAG dispatch payloads, rerun scopes, worker command mapping, and final signoff evidence lists.
- [[interactive-ask-user-ip-discovery]] — first stop for validating real interactive SSOT discovery instead of headless/pipeline proxy behavior.
- [[pl330-real-orchestrator-ui-lessons-20260517]] — first stop for visible UI Orchestrator/worker validation, `/ssot-rtl` handoff versus TODO payloads, duplicate dispatch loading, and contaminated stage-card status.
- [[atcdmac100-document-flow-ui-honesty-20260518]] — first stop for distinguishing backend-generated ATCDMAC100 evidence from real UI Orchestrator/worker proof.
- [[atlas-modular-refactor-status-20260528]] — first stop for "what's been extracted from `src/atlas_ui.py` / `frontend/atlas/workspace.jsx`?" and how to verify a new phase without booting the server (Node `vm`-sandbox integration rig at `scripts/atlas_jsx_integration_test.js`).
- [[atlas-refactoring-review-20260528]] — review note for the single-worker warmup/readiness refactor; current open risks are premature input release on `scheduled` warmup and duplicate in-flight warmup scheduling.
- [[atlas-refactoring-exceptions]] — sub-1000-line file-size policy + the registry of files that remain ≥1000 with per-file technical justification (single mega-component / mega-factory / cross-module hydration constraints), the decomposition cost matrix, and the verified extraction-pattern catalogue.
- [[worker-model-gpt-switch]] — first stop for worker/orchestrator LLM model latency: switching off cost-optimized glm/deepseek onto `gpt-5.5` (glm-5.1 ~80s vs gpt-5.3-codex ~10s per call, ≈8×), with the coupled model+auth-route caveat.
- [[systematic-quality-gates-20260521]] — hub for the system-wide quality gates (manifest hygiene + SSOT validator) applied across all IPs without per-IP hand-tuning.
- [[atlas-ssot-flag-reference]] — reference for every opt-in flag and per-IP SSOT semantic switch in ATLAS, with the IPs using each and the behavior change it triggers.

## Open Improvements

- [[workflow-improvement-candidates]] — parking lot for design candidates not yet decided (reference RTL reuse incl. legacy-extend / style-match / pin-compat cases, sectional SSOT-gen, multi-LLM reviewer pattern, stage repair convergence budget, requirements authoring guide). Captured 2026-05-17 from [[atcuart100-pipeline-run]]. None promoted to code yet; do not treat as normative.
- [[workspace-jsx-decomposition-plan]] — historical design rationale (2026-05-25) for splitting `frontend/atlas/workspace.jsx`; decomposition now largely realized via the completed .jsx→.tsx migration. Live progress + verification rig under [[atlas-modular-refactor-status-20260528]] (workspace.jsx 21,415 → 15,562 lines as of Phase 13f, −27.3%).

## Hard Rules

- Use the common engine and workflow commands for IP generation and repair.
- Do not manually patch generated IP artifacts to make a test pass.
- Do not change SSOT, FunctionalModel, CycleModel, coverage goals, timing targets, waivers, or interface contracts to hide downstream failures.
- RTL-gen must implement the current SSOT contract; existing RTL is evidence, not authority.
- Sim evidence must name SSOT/RTL/TB versions; lint/syn/sta/pnr evidence must name the RTL version it ran against.
- If evidence fails, classify the owner first, then route the fix to the owner workflow.
- In worker mode, the orchestrator dispatches owner feedback to live workflow workers; outside worker mode it persists handoff JSON for `/take`.
- `Run Mode` (`Starter` / `Engineering` / `Signoff`) controls evidence strictness; `Exec Mode` (`Single Worker` / `Orchestrator`) controls execution topology. Do not merge them.
- Keep user-visible SSOT YAML clean; store resolved defaults and field authority in resolved SSOT plus provenance sidecars.
- Approval comes from deterministic evidence or human authority, not from LLM prose.
- When a debugging surface changes, update code, tests, real-use validation notes, and wiki together.
- For RTL worker handoff, dispatch `/ssot-rtl <ip>` and let `rtl-gen` read the dynamic RTL ledgers from disk. Do not preload the `ssot-rtl` TODO template as an HTTP payload.

## Source Docs

- [AI-Driven IP Development Guide](../ai_driven_ip_development_guide.md)
- [Golden Todo Evidence Flow](../golden_todo_evidence_flow.md)
- [Common Engine IP Flow](../../workflow/COMMON_ENGINE_FLOW.md)
- [Workflow Long-Term Improvements](../workflow_long_term_improvements.md)
- [RTL Gen Flow](../../workflow/rtl-gen/RTL_GEN_FLOW.md)

## Maintenance

- [[log]] — project-wide append-only event log (the Karpathy L2 log) recording dated wiki/system changes.
- Add a wiki page when a concept is reused across multiple docs or workflows.
- Keep wiki pages short and cross-linked.
- Put implementation details in source docs and scripts; put navigation and authority rules here.
- When a workflow rule changes, update the source doc first, then update the wiki link map.
- Run `python3 workflow/wiki/build_graph.py --check` after wiki edits.
