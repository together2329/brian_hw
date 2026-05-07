# Human-LLM Authority Manifest — atciic100_real

> Human = 정답/목표/판단 기준 확정. LLM = 그 기준에 수렴하도록 생성·실행·수정 loop 수행.

## Cardinal Rule
> LLM은 RTL/test/vector/report을 자유롭게 수정한다. 그러나 RTL이 FL과 어긋났을 때 FL을 바꿔서 PASS시키는 것은 금지된다. FL/spec/coverage_goal/perf_target/interface contract 변경은 사람 승인 없이는 불가능하며, PASS의 의미는 항상 locked truth(FL+SSOT) 기준으로만 판단한다. model_signature.json drift가 감지되면 downstream worker는 [SSOT HANDOFF] golden_changed를 발행하고 멈춰야 한다.

## General Flow Guarantee
> 이 manifest는 IP-agnostic이다. 9 gates / 9 loops / 6 rules / repo_layout 모두 특정 IP의 프로토콜이나 도메인을 가정하지 않으며, 게이트 상태는 on-disk artifact 존재/내용만 근거로 자동 감지된다. 어떤 IP의 SSOT도 동일한 manifest 골격을 받는다.

## Operating Rules
1. **R1** — LLM은 RTL을 고칠 수 있다 (scope: rtl/, tb/, vectors/)
2. **R2** — LLM은 test를 추가할 수 있다 (scope: tb/, sim/)
3. **R3** — LLM은 coverage gap을 채울 수 있다 (scope: tb stimulus, vectors/)
4. **R4** — LLM은 spec/FL/coverage/perf target을 바꾸려면 change request 필수 (scope: yaml/, model/, cov/)
5. **R5** — 사람 승인 전에는 golden artifact 변경 금지 (scope: model/functional_model.py, model/cycle_model.py, cov/fl_fcov_plan.json, cov/cl_fcov_plan.json)
6. **R6** — PASS의 의미는 항상 locked truth 기준으로만 판단 (scope: all evidence rooted in SSOT + FL)

## Human Gates (9)
- [x] **G1 Requirement 승인** — approved
- [x] **G2 Spec 승인** — approved
- [x] **G3 Interface 승인** — approved
- [x] **G4 FL golden model 승인** — approved
- [x] **G5 Coverage goal 승인** — approved
- [x] **G6 CL/performance target 승인** — approved
- [x] **G7 RTL architecture 방향 승인** — approved
- [x] **G8 PPA/DFT trade-off 승인** — approved
- [ ] **G9 Final sign-off** — pending

## LLM Loops (9)
- **L1 RTL correctness loop** — FL expected vs RTL actual diff → Patch RTL and rerun cocotb. Validator: atciic100_real/sim/scoreboard_events.jsonl. Owner-on-fail: rtl.
- **L2 Module-level loop** — scope.level=module equivalence diff at module boundary → Patch only the owning RTL module. Validator: atciic100_real/sim/module_scoreboard_*.jsonl. Owner-on-fail: rtl.
- **L3 Coverage closure loop** — coverage goals vs hit bins → Add stimulus/tests; never weaken coverage goals. Validator: atciic100_real/cov/coverage.json. Owner-on-fail: tb.
- **L4 Lint/compile loop** — DUT-only lint/compile diagnostics → Patch RTL syntax/width/driver/style. Validator: atciic100_real/lint/dut_lint.json. Owner-on-fail: rtl.
- **L5 Assertion/protocol loop** — SSOT interface/cycle assertion failure → Patch RTL or TB monitor depending on classified owner. Validator: atciic100_real/sim/assertion_failures.jsonl. Owner-on-fail: rtl|tb.
- **L6 CL performance loop** — cycle_model performance target vs measured latency/throughput → Run parameter/architecture sweeps and propose tradeoff candidates. Validator: atciic100_real/reports/perf_sweep.json. Owner-on-fail: rtl|architect.
- **L7 PPA loop (Synthesis / DFT / PnR / STA / Power / Area)** — synthesis/dft/pnr/sta/power reports vs PPA budget → Propose RTL/architecture improvements per sub-stage; final acceptance is human. Validator: atciic100_real/reports/ppa_sweep.json. Owner-on-fail: architect|human.
  - synthesis: atciic100_real/reports/synth/qor.json (WNS, TNS, cell_area, register_count, est_power)
  - dft: atciic100_real/reports/dft/atpg.json (fault_coverage, pattern_count, scan_chains, scan_shift_power, dft_area_overhead)
  - pnr: atciic100_real/reports/pnr/route.json (post_route_WNS, clock_skew, wirelength, cell_density, congestion_overflow, ir_drop_risk)
  - sta: atciic100_real/reports/sta/timing.json (setup_slack, hold_slack, fmax_mhz)
  - power: atciic100_real/reports/power/power.json (dynamic_mw, leakage_mw, toggle_hotspot)
  - area: atciic100_real/reports/pnr/area.json (total_um2, utilization_pct, macro_area)
  - feedback: CL predicted vs measured: latency_ns=cycles*period; throughput=tx/cycle*Fmax; energy/op=power/ops; area_efficiency=throughput/area
- **L8 Regression minimization loop** — Large failing test → minimal reproducer that still fails → Bisect/shrink stimulus until a minimal vector reproduces the same failure; then patch RTL or escalate. Validator: atciic100_real/sim/min_repro_*.jsonl. Owner-on-fail: tb|rtl.
- **L9 Report / root-cause loop** — Diff/log/coverage-miss/waveform evidence → Synthesize fail_analysis.md with expected vs actual, likely cause, and suggested RTL patch — never modify FL/spec/coverage to make tests pass. Validator: atciic100_real/reports/fail_analysis.md. Owner-on-fail: tb|rtl|architect.

## Repo Layout
**Locked (human-owned)**: yaml/, model/, cov/fl_fcov_plan.json, cov/cl_fcov_plan.json, verify/equivalence_goals.json
**LLM-editable**: rtl/, tb/, sim/, vectors/, assertions/, reports/
**Agent-runnable validators**: lint/, sim/, cov/coverage.json, reports/ppa_sweep.json

## Summary
- Gates approved: 8/9
- Gates pending: 1/9
- Gates blocked: 0/9
