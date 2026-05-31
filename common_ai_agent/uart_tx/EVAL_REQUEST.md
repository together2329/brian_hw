# RTL 엔지니어 평가 요청 — LLM-구동 IP 검증 플로우 (uart_tx 예시)

**부탁**: 격려 말고 **혹독한 현실 점검**을 원합니다. ~45분, 블록 1개. "예/아니오"로 떨어지는 답이 가장 도움 됩니다.

## 이게 뭐고, 뭐가 *아닌지* (정직하게)
- **무엇**: 사람이 lock한 SSOT에서 출발해 LLM이 RTL/TB로 수렴하는 검증 플로우입니다. `uart_tx`(APB 8N1 송신기)는 **방법론을 inspect 가능하게** 만든 *일부러 작은* 블록이에요.
- **아님**: 이건 signoff 된 IP가 **아닙니다**(audit 11/16 fail). 스펙도 제가 자작한 toy라 독립 reference가 없습니다. 그래서 "이 블록이 맞냐"보다 **"이 방법론이 건전하냐, 진짜 IP에서 어디서 깨지냐"**를 봐주세요.

## 평가 대상 방법론 (5줄)
1. **SSOT(YAML)** = 사람이 승인하는 단일 진실 (스펙/인터페이스/coverage/function_model).
2. SSOT에서 **실행가능 FL golden model**(`functional_model.py`)을 자동 생성 → 정답 오라클.
3. SSOT+FL에서 **FL-vs-RTL 등가 goal** 자동 생성(`equivalence_goals.json`).
4. **RTL**은 사람/LLM이 작성, 게이트 통과 필수: compile + lint(verilator+pyslang, **lint 억제 주석 금지**, 스타일 룰).
5. **cocotb TB**가 실제 `tx` 직렬선을 **비트 단위로 역직렬화**해 FL 기대 프레임과 비교. **mutation-guard**가 RTL을 일부러 깨서 TB가 잡는지(kill-rate)로 *관측의 빡빡함*을 측정.

## 볼 순서 (파일)
1. `req/uart_tx_requirements.md` — 사람이 정한 계약
2. `yaml/uart_tx.ssot.yaml` — SSOT (특히 `function_model.transactions[].output_rules`)
3. `model/functional_model.py` — 생성된 golden (오라클)
4. `verify/equivalence_goals.json` — 29 goals
5. `rtl/uart_tx.sv` — DUT
6. `tb/cocotb/test_uart_tx.py` — 직렬 역직렬화 + FL 비교 + invariant
7. `sim/fl_rtl_goal_audit.json`(11/16) + `verify/mutation_report.json`(kill-rate 73%)

## 재현 (env: cocotb는 user Python 3.9, `export PATH=$HOME/Library/Python/3.9/bin:$PATH`)
```bash
export ATLAS_PROJECT_ROOT=$PWD ATLAS_WORKFLOW_ROOT=$PWD/workflow COMMON_AI_AGENT_ROOT=$PWD
python3 workflow/fl-model-gen/scripts/emit_fl_model.py uart_tx --root .          # SSOT→FL
python3 workflow/fl-model-gen/scripts/emit_equivalence_goals.py uart_tx --root . # →goals
python3 workflow/rtl-gen/scripts/rtl_compile_report.py uart_tx --project-root .  # compile
python3 workflow/lint/scripts/dut_lint_report.py uart_tx                         # lint
python3 uart_tx/tb/cocotb/test_runner.py                                         # cocotb sim (FL-vs-RTL)
python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py uart_tx --root .   # audit
python3 workflow/sim_debug/scripts/mutation_guard.py uart_tx --root .            # mutation kill-rate
```

## 핵심 질문 (틀렸다고 답할 수 있게)
**방법론**
1. **FL golden model + cocotb 비교** — 건전한 접근인가, 아니면 UVM / SVA assertion / formal equivalence를 **어설프게 재발명**한 건가? 표준 실무는 이걸 어떻게 하나?
2. **mutation kill-rate**가 "검증이 얼마나 빡빡한가"의 실제 신호인가, 아니면 **functional coverage + formal**로 대체될 ceremony인가?

**RTL/TB 품질**
3. 이 `uart_tx.sv`, 실무에서 받아들일 수준인가? LLM-생성 냄새가 나쁜 쪽으로 나나? (reset, CDC, X-propagation, clock-gating, async)
4. 이 TB로 이 블록 **signoff를 신뢰**하겠나? 못 한다면 *무엇을* 더 요구하나?

**규모/현실** (진짜 IP는 `../apb_uart_txrx_demo`: RTL 9-module 실 UART TX/RX)
5. toy UART는 됐다 치고, **진짜 IP에선 이 플로우가 어디서 깨지나?** (coverage closure, corner case, 다중 클록, backpressure, reset 시퀀스)
6. **baseline 대비**: 숙련 엔지니어가 손으로 RTL+TB 짜거나 상용 flow 쓰는 것보다 **빠르거나 나은가**, 아니면 그냥 의식인가?

## 답변 형식 (이대로면 충분)
- **이 블록 signoff 신뢰? Y/N** + 그 이유 한 줄.
- **상위 3개 갭** (실무라면 막을 것).
- **"이건 X를 재발명한 거다"** 콜아웃 (UVM/SVA/formal/mutation testing 등) — 어디서 표준을 채택해야 하나.
- 한 줄 총평: 이 방향, **추구할 가치 있나 없나.**

> 비판을 *반증*이 아니라 *선물*로 받겠습니다. "너 그거 이미 있는 X 재발명했다"가 가장 값진 답입니다.
