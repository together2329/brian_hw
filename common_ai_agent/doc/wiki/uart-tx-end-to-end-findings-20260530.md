# uart_tx 직접 end-to-end 실행 — flow 검증 + silent-PASS 실증 (2026-05-30)

> 핵심 교훈: **이 flow의 골격(사람이 lock한 진실 + evidence-gated + 코드에 박힌 치팅 방어)은 실제로 작동한다.** 약점은 골격이 아니라 "무엇을 관측하느냐(observation depth)"에 있고, 그 약점은 **MSB-first mutation 한 방으로 실물 재현**됐다. 가장 레버리지 큰 보강: audit을 goal *개수*가 아니라 **mutation kill-rate**로 채점.

비전문 기록이 아니라 **직접 손으로** `uart_tx`(APB 8N1 UART 송신기)를 req→SSOT→FL→goals→RTL→lint→TB→sim→audit까지 실제 스크립트로 몰아본 1차 실험 결과. 관련: [[default-agent-ip-flow]] · [[deterministic-emit-stages]] · [[workflow-ownership-and-boundaries]] · [[testing-methodology]] · [[agent-autonomous-ip-implementation-pattern]] · [[apb-uart-real-uart-signoff-20260527]].

생성 산출물 위치: `uart_tx/` (req/yaml/model/verify/cov/rtl/lint/list/tb/sim).

## 1. 무엇을 했나 (증거)

| Stage | 도구(실제) | 결과 |
|---|---|---|
| 1 req | `uart_tx/req/uart_tx_requirements.md` (사람이 결정) | ✅ |
| 2 SSOT | `workflow/ssot-gen/scripts/verify_ssot.py --mode starter` | ✅ PASS |
| 3 FL model | `workflow/fl-model-gen/scripts/emit_fl_model.py` → `model/functional_model.py` | ✅ self-check PASS (3 tx, AST `expr` 평가기 내장) |
| 4 equiv goals | `workflow/fl-model-gen/scripts/emit_equivalence_goals.py` | ✅ 29 goals, **stub observable 0개** |
| 5 RTL | 손작성 `rtl/uart_tx.sv` + `rtl-gen/scripts/rtl_compile_report.py` + `lint/scripts/dut_lint_report.py` | ✅ compile PASS / lint PASS (verilator+pyslang clean, 억제 0) |
| 6 TB | 손작성 cocotb (직렬선 역직렬화 = deep observation) | ✅ |
| 7 sim | `tb/cocotb/test_runner.py` (cocotb 1.9.2 + iverilog) | ✅ TESTS=1 PASS=1 |
| 9 audit | `workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py` | ⚠️ **status=fail 11/16** (honest partial) |

audit blockers: `req`(approval_manifest 없음 = **human gate**, LLM이 자가승인 불가), `scoreboard_contract`(29 중 8 goal만 커버), `fl_rtl_compare`/`mismatch_classification`(sim-debug 미실행), `functional_coverage`(미마감). → mctp_assembler의 현재 `status=fail`과 동일한 성격의 **정직한 부분-완성** 상태.

## 2. 발견

### F1. 얕은 관측 silent-PASS는 실재 — mutation으로 증명 (가장 중요)
직렬화기를 `frame_q[bit_index]` → `frame_q[9-bit_index]`(MSB-first 버그)로 깨고 동일 suite 재실행:

| 관측 | 정상 RTL | MUTANT |
|---|---|---|
| `tx_frame` (직렬선 비트단위 역직렬화 = deep) | 0x34A/0x200/0x3FE = FL과 일치 ✅ | `331≠842`, `1≠512`, `511≠1022` → **FAIL (버그 잡음)** |
| `tx_busy` (편한 상태 신호 = shallow) | 1 ✅ | 여전히 1 → **PASS** (SC5/SC6도 PASS) |

→ "편한 상태 신호만 보면 침묵, 진짜 출력선을 봐야 잡힌다"가 코드로 증명됨. 동일 suite가 정상엔 GREEN·깨진 RTL엔 RED = **negative control은 작동**하지만, 그건 *내가 직렬선을 깊게 관측한 goal에 한해서*다.

### F2. negative-control / mutation gate가 flow에 없다 (실유효 갭)
`grep mutation|fault-inject|must-fail` → 산문(system_prompt.md)만, RTL을 깨서 suite가 RED 되는지 동적 증명하는 단계는 없음. F1이 그 단계의 가치를 실물로 뒷받침. → **보강: sim과 goal-audit 사이에 `mutation-guard` 단계** (결정적 변이 카탈로그 → 동일 cocotb 재실행 → goal별 kill-rate). 변이는 LLM-editable RTL에만, **FL은 절대 변이 금지**.

### F3. 얕은 관측의 뿌리는 SSOT
내가 SSOT `function_model`에 진짜 `output_rules`(frame_rule 등)를 쓰니 29 goals 전부 실관측 가능(**stub 0**). mctp_assembler가 75% silent였던 건 SSOT가 auto-injected 스텁(`expr:'1'`, "replace before signoff")이었기 때문 → "얕은 관측의 근원은 SSOT observable"이라는 가설 확정. (cf. 2026-05-20 cocotb HARD-policy silent-PASS 폭로 건.)

### F4. 생성기 경로는 same-cycle 트랜잭션 IP를 가정 (능력 경계)
`ssot_to_rtl.py`·`emit_goal_scoreboard_cocotb.py`가 UART의 **다중 사이클 직렬** 동작에 5개 hard-gate(frame_rule→same-cycle 포트 매핑, state DSL)를 냄. 즉 조합/레지스터 IP(apb_xor류)는 풀 자동, **temporal 데이터패스(UART 직렬, streaming)는 generic auto-gen이 막고 LLM/worker가 RTL+TB를 직접 작성해야 함** (COMMON_ENGINE_FLOW의 "LLM writes RTL" 경로). 주의: 간판 데모 MCTP assembler 자체가 streaming이라 이 경계는 실무적으로 중요. `EquivalenceScoreboard`에 `sample_cycle`/`cycle_model.pipeline` 다중사이클 훅은 있으나 직렬 관측엔 미배선.

### F5. vacuous-pass(공허한 통과)는 프랙탈로 반복된다
같은 실패 모드가 3층에서 재현: ① FL observable(스텁), ② TB 관측(tx_busy-only), ③ **audit 채점**(깊은 8 goal과 공허한 29 goal을 구분 못 하고 똑같이 평평하게 fail). → "이 체크가 빡빡한가?"는 한 군데서 못 막고 매 층에서 물어야 하며, 보편적 답은 mutation뿐.

### F6. gate들이 정직하게 깐깐하다 (좋은 의미)
- lint(`dut_lint_report.py`)가 `verilator lint_off`/`-Wno-` 억제 주석을 **치팅으로 탐지**.
- compile(`rtl_compile_report.py`)이 always 블록 내 파라미터 part-select를 `no_parameterized_part_select_in_procedural_block` 스타일 위반으로 거부.
- audit이 sim의 `PASS=1`을 단독 신뢰 안 하고 scoreboard_contract/coverage까지 요구.
- `check_scoreboard_events.py`가 `rtl_observed ≠ fl_expected`, `model_api==FunctionalModel.apply`, 0행 거부, required goal 누락 거부를 강제. → silent-PASS 방어가 코드에 박혀 있음.

## 3. 권고
1. **audit = mutation kill-rate 채점**: goal 개수 대신 변이 사멸률로 채점하면 "깊은 8개"가 "공허한 29개"를 자동으로 이긴다. (F1·F5 정조준)
2. **observable-completeness 계약**: `check_scoreboard_events`가 `rtl_observed.keys() ⊇ goal.expected_contract.observables`를 강제 (지금은 non-empty + ≠fl_expected만). (F3)
3. **temporal-IP 레인**: 직렬/streaming은 `sample_cycle`/`cycle_model.pipeline` 기반 다중사이클 scoreboard를 배선하거나, 5개 hard-gate 대신 깔끔히 LLM-TB로 핸드오프. (F4)
4. **placeholder 거부**: audit `_text_has_placeholder`를 goal observable까지 확장해 스텁 observable이 남으면 signoff 차단. (F3)

## 4. 직접 구동 cheat-sheet (미래 에이전트 토큰 절약)
환경: `export ATLAS_PROJECT_ROOT=$PWD; export ATLAS_WORKFLOW_ROOT=$PWD/workflow; export COMMON_AI_AGENT_ROOT=$PWD`. cocotb는 user Python 3.9 → `export PATH=$HOME/Library/Python/3.9/bin:$PATH`.
```bash
# SSOT는 <ip>/yaml/<ip>.ssot.yaml. function_model.transactions[].output_rules에 port+expr 필수(스텁 금지).
python3 workflow/ssot-gen/scripts/verify_ssot.py <ip> --root . --mode starter   # engineering은 30+섹션(cdc/rdc/timing…) 요구
python3 workflow/fl-model-gen/scripts/emit_fl_model.py <ip> --root .            # → functional_model.py(+ apply/csr_write), decomposition, fcov, fl_model_check
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py <ip> --root .   # → verify/equivalence_goals.json
# RTL 손작성 → rtl/<ip>.sv (Verilog-2001 subset; package/interface/for/function 금지; 파라미터 part-select는 always 밖으로; lint 억제 금지)
printf '+incdir+rtl\nrtl/<ip>.sv\n' > <ip>/list/<ip>.f
python3 workflow/rtl-gen/scripts/rtl_compile_report.py <ip> --project-root .    # → rtl/rtl_compile.json
python3 workflow/lint/scripts/dut_lint_report.py <ip>                           # → lint/dut_lint.json (cwd=root, --project-root 없음)
# TB: tb/cocotb/{tb_manifest.json, test_<ip>.py, test_runner.py(apb_xor 복사)}.
#  EquivalenceScoreboard(ip, root, reset_events=True).record(goal_id, stimulus=..., rtl_observed=...) → 자동 FL비교 + 계약row 방출.
python3 <ip>/tb/cocotb/test_runner.py                                           # → sim/{results.xml, scoreboard_events.jsonl}
python3 workflow/tb-gen/scripts/check_scoreboard_events.py <ip> --root . --source-check --require-events --require-all-goals
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py <ip> --root .   # → sim/fl_rtl_goal_audit.json
```
주의: `FunctionalModel`은 **stateful** — 레지스터 read-back goal은 `sb.model.csr_write(off,data)`로 RTL write와 lockstep 동기 필요. 등록 신호(busy 등)는 NBA 델타 때문에 write 직후가 아니라 프레임 중간에서 샘플.

## 5. 한 줄
"기반은 생각보다 단단하고, 약점은 예상한 바로 그 자리(temporal 자동화 / 관측 깊이)에 정확히 있었다." 두 갭 모두 SSOT observable 깊이 강제 + post-sim mutation gate로 닫힌다.
