# HW Agent IP Experiment Batch - 2026-05-30

## 목표

여러 개의 작은 IP를 직접 만들어 보면서 `common_ai_agent` 운영 규칙과 실제 HW/IP signoff 규칙을 분리한다.

핵심 가설:

```text
AGENTS.md = agent가 어떻게 일하는지 정하는 운영 contract
HW/IP signoff = 무엇이 정답이고 어떤 evidence가 pass인지 정하는 기술 contract
```

지금 AGENTS.md는 agent 운영에는 강하지만, IP 관점에서는 locked truth, editable implementation, gate evidence, human approval boundary를 별도 문서로 더 명확히 해야 한다.

## 실험 Flow

각 IP는 아래 순서로 검증한다.

```text
req/spec
-> SSOT YAML
-> FL model emit/check
-> CL model emit/self-check
-> equivalence goals
-> RTL implementation
-> RTL todo/static audit
-> compile/lint
-> cocotb scoreboard
-> SSOT coverage summary
-> signoff ledger
```

## Locked vs Editable

사람이 lock해야 하는 artifact:

- requirement/spec intent
- SSOT behavior/register/interface/cycle contract
- 승인된 FL golden semantics
- coverage goals
- waiver, target change, final signoff

agent가 수정해도 되는 artifact:

- RTL
- cocotb/pyuvm TB
- sim harness
- evidence/report
- validator가 tool bug를 드러낸 경우의 제한적 workflow script fix

## Pass 기준

각 IP는 다음 evidence가 fresh하게 통과해야 실험상 pass로 본다.

- FL artifact check pass
- CL self-check pass
- equivalence goals blocked=0
- RTL todo/static audit blockers=0, orphans=0, gate=pass
- DUT-only compile diagnostics/style violations=0
- DUT-only lint errors/warnings/suppressions/style violations=0
- cocotb sim pass, scoreboard가 FL expected와 RTL observed를 비교
- coverage summary `Status: pass`

## 현재 Baseline

`apb_masked_match_demo`는 가장 단순한 useful lane을 증명했다.

- APB DATA/MASK register
- combinational derived output
- SSOT 기반 FL/CL 생성
- hand-authored RTL + cocotb scoreboard
- compile/lint/sim/coverage pass

이 과정에서 재사용 가능한 workflow 결함도 드러났다.

- CL self-check는 `{"kind": ...}`만 넣으면 안 되고 transaction required field를 채워야 한다.
- FL generator는 validator가 금지하는 placeholder string을 내보내면 안 되고, functional coverage description에 raw transaction ID가 들어가야 한다.

## 다음 실험 IP

다음 IP들은 서로 다른 failure mode를 보기 위해 만든다.

- event/sticky-status + write-one-to-clear semantics
- sequential counter/timer + external pulse/threshold behavior
- checksum/CRC-like datapath behavior

최종 제안은 한 개 green demo가 아니라 여러 IP에서 나온 friction과 실패 유형을 기준으로 정리한다.

## 실행 결과

세 개의 bounded IP에 대해 local evidence gate를 돌렸다.

| IP | Stress case | FL | CL | Equiv goals | RTL gate | Compile/lint | Sim | Coverage | TB schema |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `apb_masked_match_demo` | CSR + combinational mask datapath | pass | pass | 23 required, 0 blocked | 114 tasks, pass | 0 diagnostics/warnings | 1/1 pass, 6 scoreboard rows | pass | pass after TB evidence-schema repair |
| `apb_event_capture_demo` | sticky status + W1C + IRQ mask | pass | pass | 25 required, 0 blocked | 123 tasks, pass | 0 diagnostics/warnings | 1/1 pass, 7 scoreboard rows | pass | pass |
| `apb_crc8_demo` | byte datapath transform + enable/clear | pass | pass | 28 required, 0 blocked | 117 tasks, pass | 0 diagnostics/warnings | 1/1 pass, 9 scoreboard rows | pass | pass |

추가로 기본 gate 외에 아래도 확인했다.

- `workflow/tb-gen/scripts/check_scoreboard_events.py --source-check --require-events`
- `workflow/tb-gen/scripts/check_pyuvm_structure.sh`

## 관찰된 Friction

- 기존 `apb_masked_match_demo`는 sim/coverage는 pass였지만 stricter TB evidence schema에서는 실패했다. scoreboard row에 `cycle`, `stimulus`, `mismatch`, `model_api`, `equivalence_goals.json` load가 없었기 때문이다. 즉 "green이지만 evidence가 약한 상태"가 실제로 있었다.
- `apb_event_capture_demo`는 procedural block 안의 parameterized part-select 때문에 RTL style gate에서 처음 실패했다. helper wire로 빼서 해결했다.
- Verilator는 event IP에서 unused upper `PWDATA` bit와 unused APB phase register를 warning으로 잡았다. suppression 대신 no-effect read expression으로 실제 소스에서 consume하게 고쳤다.
- `rtl_todo_plan.json` 재생성 후 `todo_plan_sha256`이 provenance와 어긋날 수 있다. 이건 IP별 수작업이 아니라 표준 helper로 자동 refresh되어야 한다.
- FL self-check는 prose invariant를 executable expression으로 평가하지 못해 skip한다. pass 자체는 의미 있지만, 강한 proof를 원하면 machine-executable invariant field가 따로 필요하다.

## 다시 제안

`AGENTS.md` 밑에 HW/IP 전용 signoff contract를 추가하는 게 맞다.

```text
AGENTS.md
  agent 행동 규칙: autonomy, routing, verification discipline, commit protocol.

docs/hw-agent-contract.md 또는 IP_SIGNOFF.md
  IP 정답 규칙: locked artifacts, editable artifacts, gate sequence,
  scoreboard schema, provenance refresh, waiver protocol, human gates.
```

바로 반영할 개선안:

- stricter scoreboard row schema를 기본 TB template으로 승격한다.
- `todo_plan_sha256` 수동 입력을 없애는 `refresh_rtl_provenance.py` 또는 표준 command를 만든다.
- "sim pass"와 "evidence schema pass"를 별도 gate로 분리하고 둘 다 요구한다.
- demo IP tier를 CSR/combinational, sticky/event, datapath/sequential로 유지한다. 다음에는 timer/counter로 CL performance stress를 추가한다.
- prose invariant는 documentation으로 취급하고, executable invariant를 별도 필드로 추가한다.

## 2026-05-31 확장 라운드: 10개 IP Evidence 목표

사용자 방향:

```text
여러 IP를 직접 만들고,
여러 테스트를 돌리고,
실패/마찰을 보고,
좋은 방향을 다시 제안한다.
```

현재 목표는 기존 3개 pass IP를 anchor로 유지하고, 7개 작은 APB IP를 추가해 총 10개 IP에 대해 같은 evidence gate를 통과시키는 것이다.

기존 anchor:

- `apb_masked_match_demo`
- `apb_event_capture_demo`
- `apb_crc8_demo`

추가 후보:

- `apb_popcount_demo`
- `apb_gray_demo`
- `apb_rotate_demo`
- `apb_xor_mix_demo`
- `apb_saturating_add_demo`
- `apb_window_compare_demo`
- `apb_bit_reverse_demo`

이번 라운드의 stop condition:

- 10개 IP 모두 fresh local evidence로 FL check, CL self-check, equivalence goal generation, RTL todo/static audit, DUT compile, DUT lint, cocotb scoreboard simulation, coverage summary, scoreboard evidence schema, pyuvm structure를 통과한다.
- 7개 확장 과정에서 발견되는 generator/template 결함은 가능하면 개별 IP 땜질이 아니라 shared workflow 수정으로 고친다.
- 실패 유형과 마찰을 이 문서에 다시 기록하고, 다음 방향을 새로 제안한다.

## 2026-05-31 확장 결과

최종 fresh run:

```text
/tmp/common-ai-agent-10ip-final/status.json
SUMMARY 10/10 IPs passed all 11 gates
```

각 IP마다 실행한 gate:

```text
emit_fl
check_fl
emit_cl
emit_equiv
rtl_compile
dut_lint
sim
coverage
scoreboard_schema
pyuvm_structure
derive_rtl_todos
```

추가 provenance 검증:

```text
/tmp/common-ai-agent-10ip-final/provenance_refresh_status.json
refresh_rtl_provenance.py pass for 10/10
derive_rtl_todos.py pass after refresh for 10/10
```

| IP | Stress case | FL/CL | Equiv goals/blocked | RTL todo | Compile/lint | Sim | Scoreboard rows | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `apb_masked_match_demo` | CSR mask compare | pass | 23/0 | 114, gate=pass | 0/0 | 1/1 | 6 | pass |
| `apb_event_capture_demo` | sticky event/W1C | pass | 25/0 | 123, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_crc8_demo` | CRC8 datapath | pass | 28/0 | 117, gate=pass | 0/0 | 1/1 | 9 | pass |
| `apb_popcount_demo` | popcount/parity datapath | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_gray_demo` | gray-code transform | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_rotate_demo` | variable rotate datapath | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_xor_mix_demo` | XOR mix/datapath | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_saturating_add_demo` | saturating add/overflow | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_window_compare_demo` | threshold compare flag | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |
| `apb_bit_reverse_demo` | bit permutation datapath | pass | 27/0 | 108, gate=pass | 0/0 | 1/1 | 7 | pass |

10개 IP의 signoff ledger는 모두 `approved_by_local_evidence` 상태로 갱신했다.

## 2026-05-31 발견한 실패 유형

이번 7개 확장에서 RTL datapath 문제는 나오지 않았다. 실제로 드러난 것은 workflow/template 문제였다.

- 새 IP RTL은 compile/lint를 모두 통과했지만, generated `test_runner.py`의 newline escaping이 깨져 cocotb가 시작되지 못했다.
- generated `test_<ip>.py`도 `scoreboard_events.jsonl`, functional coverage JSON write 쪽 newline escaping이 깨져 있었다.
- 이 문제는 sim까지 가야 보였지만, `python3 -m py_compile <ip>/tb/cocotb/*.py`를 mandatory TB gate로 넣으면 더 빠르고 싸게 잡힌다.
- `derive_rtl_todos.py`는 일부러 strict하다. canonical compile/lint evidence가 없거나 `rtl_authoring_provenance.json.todo_plan_sha256`이 current stable todo plan hash와 맞지 않으면 pass하지 않는다.
- `refresh_rtl_provenance.py`가 metadata/hash refresh의 표준 helper로 맞다. 최종 라운드에서 10개 IP 모두 이 helper 적용 후 final derive pass를 확인했다.

## 2026-05-31 common_ai_agent vs 실제 IP Boundary

이번 batch에서 `common_ai_agent`가 증명한 것:

- bounded IP artifact를 만들고, generator/validator를 돌리고, failure를 읽고, 맞는 layer를 패치하고, evidence를 다시 만들고, wiki에 남길 수 있다.
- syntax, lint, compile, scoreboard, coverage, provenance, schema처럼 machine-checkable한 pass/fail이 있으면 convergence loop를 잘 돈다.
- agent가 맡을 영역은 editable implementation artifact와 evidence refresh loop다.

실제 IP flow가 `AGENTS.md` 밖에서 따로 정의해야 하는 것:

- locked truth: requirement, SSOT behavior, interface contract, FL golden semantics, coverage goal, performance/PPA target, waiver, final signoff policy
- approval boundary: agent는 locked truth 변경을 제안할 수는 있지만, RTL을 통과시키기 위해 몰래 locked truth를 바꾸면 안 된다.
- verification depth: 이번 10개는 APB micro-IP 실험으로는 의미 있지만, production-class IP methodology를 증명한 것은 아니다.

## 업데이트된 제안

다음 contract는 명확히 분리하는 게 맞다.

```text
AGENTS.md
  agent 운영: autonomy, tool routing, progress update, verification discipline

IP_SIGNOFF.md 또는 docs/hw-agent-contract.md
  IP 정답: locked artifacts, editable artifacts, required gates,
  scoreboard schema, provenance refresh, py_compile gate, waiver protocol,
  human approval gates, final signoff language
```

다음 workflow 개선:

- `python3 -m py_compile <ip>/tb/cocotb/*.py`를 sim 이전 mandatory TB gate로 추가한다.
- compile/lint evidence 생성 후 final `derive_rtl_todos.py --audit-rtl` 전에 `refresh_rtl_provenance.py <ip> --root ip_examples`를 canonical RTL gate sequence에 넣는다.
- stricter scoreboard JSONL schema를 TB generator 기본값으로 승격하고, `check_scoreboard_events.py --source-check --require-events`를 mandatory로 둔다.
- 실험 IP를 난이도 tier로 나눈다.

## 2026-05-31 SPI General-IP Exercise

`ip_examples/spi_master_tx_demo`를 non-APB serial temporal IP로 만들었다. 목적은 `profiles/` 같은 정적 분류 없이도 일반 IP evidence contract가 만들어지고 검증되는지 확인하는 것이다.

구현 artifact:

- `req/spec.md`
- `yaml/spi_master_tx_demo.ssot.yaml`
- `model/functional_model.py`
- `model/cycle_model.py`
- `rtl/spi_master_tx_demo.sv`
- `tb/cocotb/test_spi_master_tx_demo.py`
- `verify/equivalence_goals.json`
- derived `verify/ip_contract.json`
- `mutation/mutation_report.json`
- `signoff/ip_signoff.json`

동작 범위:

- 8-bit SPI master transmit only
- CPHA=0 지원, CPHA=1은 `mode_fault_o`로 reject
- CPOL이 idle `sclk_o`를 결정
- `clk_div_i + 1`이 SCLK half-period
- MOSI는 active SCLK sample edge에서 MSB-first로 검증

per-IP contract는 정적 profile 선택이 아니라 IP artifact에서 파생됐다.

```text
generation = derived_from_ip_artifacts_not_static_profile
capabilities include serial_shift_protocol, chip_select_protocol, multi_cycle_timing, fsm_state, error_path
required monitors include serial_frame_monitor, chip_select_monitor
required observed evidence includes serial_bits, sample_edge_cycles, done_cycle, idle hold samples
```

초기 mutation 결과는 TB가 약하다는 것을 바로 보여줬다.

```text
mutation_guard --max-mutants 8
killed=1 survived=7 kill_rate=0.125
```

처음 TB는 전송 bit 값만 증명했고, idle stability, SCLK interval, completion latency를 증명하지 않았다. 그래서 TB를 강화했다.

- `idle_sclk_samples`, `idle_cs_n_samples`, `idle_done_samples`
- `serial_bits = [1,0,1,0,0,1,0,1]`
- `sample_edge_cycles = [2,6,10,14,18,22,26,30]`
- `done_cycle = 32`

그 결과 enforced mutation이 통과했다.

```text
mutation_guard --max-mutants 8 --enforce-threshold --threshold 0.70
killed=6 survived=2 kill_rate=0.75
```

최종 SPI evidence:

```text
rtl_compile: errors=0 diagnostics=0 style_violations=0
dut_lint: errors=0 warnings=0 suppression_violations=0 style_violations=0
tb_python_compile: compiled 4 files
cocotb: TESTS=1 PASS=1 FAIL=0
scoreboard_schema: goals=3 required=3 rows=3 goals_with_rows=3
ip_signoff: 15/15 gates pass
pytest workflow regression: 12 passed
```

배운 점:

- General IP 지원은 정적 `profiles/` selector가 아니다.
- 더 나은 구조는 SSOT, interface name/type, FL/CL, equivalence goals, debug observability에서 per-IP contract를 파생하는 것이다.
- mutation kill-rate는 serial IP에서 final-value comparison만으로는 부족하고 temporal observation이 필요하다는 것을 즉시 드러냈다.

다음 workflow gap:

- 현재 mutation guard는 SPI contract mutation 중 `bit_order_flip`, `serial_clock_edge_flip`, `chip_select_polarity_flip`, `reset_value_flip`, `state_update_drop`를 아직 unsupported로 보고한다.
- 다음 개선은 이것들을 SPI profile이 아니라 contract-driven mutation class와 reusable monitor template으로 구현하는 것이다.

## 2026-05-31 Contract-Driven Monitor/Mutation Improvement + UART

다음 generic 개선을 구현하고 새 non-APB IP인 `ip_examples/uart_tx_demo`로 검증했다.

workflow 변경:

- `workflow/tb-gen/runtime/protocol_monitors.py` 추가
- reusable monitor helper:
  - fixed-cycle idle signal sampling
  - SPI-style clocked serial frame capture
  - UART TX start/data/stop/timing capture
- `derive_ip_contract.py`가 UART-like tx/rx interface를 감지하고 아래 contract를 만든다.
  - `uart_frame_protocol`
  - `uart_frame_monitor`
  - `uart_start_stop_polarity_flip`
  - `serial_timing_flip`
- `mutation_guard.py`가 generic mutation보다 contract-specific mutation을 우선 생성한다.
  - `bit_order_flip`
  - `serial_clock_edge_flip`
  - `chip_select_polarity_flip`
  - `uart_start_stop_polarity_flip`
  - `serial_timing_flip`
- cocotb TB template guidance에 derived contract가 serial/UART/chip-select monitor를 요구하면 `protocol_monitors.py`를 재사용하라고 추가했다.

SPI도 reusable clocked serial monitor를 쓰게 업데이트했다. 이 과정에서 `0xA5`는 MSB와 LSB가 둘 다 `1`이라 bit-order mutation을 죽이기 약한 pattern이라는 점이 드러났다. 그래서 transfer vector를 `0x96`으로 바꾸고, serial sample edge마다 `cs_n_o`도 관측하게 했다.

SPI 최종 evidence:

```text
spi_master_tx_demo signoff: 15/15 gates pass
spi_master_tx_demo mutation: 12 executed, 11 killed, kill_rate=0.9167
```

UART IP 동작:

- 8-bit transmit-only UART
- idle line `tx_o=1`
- accepted `start_i`가 start bit `0`, 8 data bits LSB-first, stop bit `1` 전송
- `baud_div_i + 1`이 bit period
- stop bit 완료 후 `done_o` pulse

UART scoreboard evidence (`data_i=0x53`, `baud_div_i=1`):

```text
data_bits          = [1,1,0,0,1,0,1,0]
data_sample_cycles = [2,4,6,8,10,12,14,16]
stop_bits          = [1]
stop_sample_cycles = [18]
done_cycle         = 20
```

UART 최종 evidence:

```text
rtl_compile: errors=0 diagnostics=0 style_violations=0
dut_lint: errors=0 warnings=0 suppression_violations=0 style_violations=0
tb_python_compile: compiled 4 files
cocotb: TESTS=1 PASS=1 FAIL=0
scoreboard_schema: goals=2 required=2 rows=2 goals_with_rows=2
pyuvm_structure: PASS
mutation_guard enforced: 16 executed, 12 killed, kill_rate=0.75
ip_signoff: 15/15 gates pass
workflow regression: 14 passed
```

남은 gap:

- `reset_value_flip`, `state_update_drop`는 아직 unsupported category다.
- 다음으로는 equivalent-mutant filtering이 포함된 state/reset mutation class를 추가하고, backpressure/order를 더 강하게 보는 ready/valid FIFO를 만드는 게 좋다.
  - Tier 1: APB combinational/datapath CSR IP. 이번 batch로 커버됨.
  - Tier 2: sequential timer/counter/FIFO/interrupt IP. CL latency check 강화.
  - Tier 3: streaming ready/valid packet IP. backpressure, ordering, multi-transaction scoreboard 필요.
  - Tier 4: synthesis/PnR report를 붙여 CL 예측과 실제 PPA 비교.

## 2026-05-31 반영한 개선

10개 IP 결과에서 나온 첫 번째 hardening을 실제 workflow에 반영했다.

- `workflow/tb-gen/scripts/check_tb_python_compile.py` 추가
- 이 gate는 `tb/cocotb/*.py` 전체를 compile하고 `tb/cocotb/tb_py_compile.json` evidence를 남긴다.
- 7개 IP 확장에서 나온 newline escaping 오류 같은 Python syntax 문제를 sim 전에 잡는다.
- `workflow/tb-gen/scripts/check_pyuvm_structure.sh`는 inline `py_compile` 대신 이 gate를 사용한다.
- `workflow/ssot-gen/scripts/new_ip_emit_chain.sh`는 cocotb sim 전에 `tb_python_compile`을 실행한다.
- `workflow/orchestrator/todo_templates/run-to-green.json`에는 다음 순서를 명시했다.
  - sim 전 `check_tb_python_compile.py`
  - compile/lint evidence 후 `refresh_rtl_provenance.py`
  - 마지막 `derive_rtl_todos.py --audit-rtl`
- TB todo template도 pre-sim Python compile gate를 요구하도록 갱신했다.

검증:

```text
python3 -m pytest -q tests/test_tb_python_compile_gate.py
2 passed

python3 workflow/tb-gen/scripts/check_tb_python_compile.py <ip> --root ip_examples
10/10 IPs pass

(cd ip_examples && IP_NAME=<ip> bash ../workflow/tb-gen/scripts/check_pyuvm_structure.sh)
10/10 IPs pass
```

즉, wiki에 적은 제안 하나를 실제 reusable gate로 승격했다.

## 2026-05-31 Signoff Contract 분리 반영

10개 IP 결과에서 나온 두 번째 boundary를 실제 파일/워크플로우로 반영했다.

```text
AGENTS.md
  agent를 위한 것: autonomy, routing, tool use, progress update,
  commit style, verification discipline

IP_SIGNOFF.md
  IP를 위한 것: locked truth, editable artifacts, required evidence gates,
  waiver policy, human-owned decisions, result language
```

추가한 실행 workflow:

- `IP_SIGNOFF.md`
- `workflow/signoff/README.md`
- `workflow/signoff/workspace.json`
- `workflow/signoff/commands/ip-signoff.json`
- `workflow/signoff/todo_templates/ip-signoff.json`
- `workflow/signoff/scripts/check_ip_signoff.py`
- `workflow/signoff/scripts/run_ip_signoff.sh`

canonical command:

```text
python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root <ip-parent>
```

출력:

```text
<ip>/signoff/ip_signoff.json
<ip>/signoff/ip_signoff.md
```

검증:

```text
python3 -m pytest -q tests/test_ip_signoff_gate.py tests/test_tb_python_compile_gate.py
4 passed

python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root ip_examples
10/10 IPs pass
```

이제 구분이 실제로 생겼다. `AGENTS.md`는 자동화가 어떻게 행동하는지 통제하고, `IP_SIGNOFF.md` + `workflow/signoff`는 IP를 pass라고 불러도 되는지 판단한다.

## 2026-05-31 Workflow 통합: Manifest, Observables, Mutation

이번에는 제안을 문서에만 두지 않고 workflow surface로 넣었다.

- `workflow/STAGE_MANIFEST.json` 추가
  - IP stage 단일 routing table 역할
  - agent가 workflow tree를 뒤지기 전에 읽을 entrypoint
- `workflow/README.md` 추가
  - `new_ip_emit_chain.sh`
  - `mutation_guard.py`
  - `check_ip_signoff.py`
  를 바로 보이게 했다.
- `workflow/tb-gen/scripts/check_scoreboard_events.py` 강화
  - `expected_contract.observables` 안에서 신호명처럼 생긴 항목은 반드시 `rtl_observed`에 있어야 한다.
  - 문장형 observable은 static completeness gate에서 무시한다.
- `workflow/signoff/scripts/check_ip_signoff.py`에도 같은 observable completeness check를 넣었다.
- `workflow/mutation` stage 추가
  - `README.md`
  - `workspace.json`
  - `commands/mutation-guard.json`
  - `todo_templates/mutation-guard.json`
  - `scripts/mutation_guard.py`
  - `scripts/run_mutation_guard.sh`
- `workflow/orchestrator/todo_templates/run-to-green.json` 갱신
  - sim 후 scoreboard schema/observable validation
  - coverage 후 advisory mutation guard

정책:

```text
mutation_guard는 기본적으로 advisory다.
--enforce-threshold는 IP class별 kill-rate 정책을 사람이 승인한 뒤에만 사용한다.
```

검증:

```text
python3 -m pytest -q \
  tests/test_scoreboard_observable_completeness.py \
  tests/test_mutation_guard.py \
  tests/test_ip_signoff_gate.py \
  tests/test_tb_python_compile_gate.py
8 passed

python3 workflow/tb-gen/scripts/check_scoreboard_events.py <ip> --root ip_examples --source-check --require-events
10/10 IPs pass

python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root ip_examples
10/10 IPs pass

python3 workflow/mutation/scripts/mutation_guard.py apb_popcount_demo --root ip_examples --max-mutants 5 --timeout-sec 20
candidates=5 executed=5 killed=1 survived=4 invalid=0 kill_rate=0.2
```

중요한 관찰:

- 기존 pass/fail gate는 여전히 전부 pass한다.
- 하지만 mutation kill-rate는 `apb_popcount_demo`에서 0.2에 불과했다.
- survived mutant는 `APB_PHASE_*`, `write_ctrl`, `popcount_value` 주변이었다.
- 즉 다음 개선은 추상적인 "coverage를 늘리자"가 아니라, 이 survivor들을 죽이는 directed TB/observable 강화로 잡을 수 있다.

## 2026-05-31 General IP Contract 방향

static profile 방식은 폐기했다.

```text
profiles/apb_csr.json
profiles/fifo.json
profiles/streaming_ready_valid.json
```

이런 구조는 "any IP"에 맞지 않는다. IP가 여러 성격을 섞으면 profile 선택이 애매하고, 새로운 IP마다 profile이 늘어나며, 선택한 profile이 충분하다는 false confidence가 생긴다.

대신 per-IP evidence contract를 자동 파생하도록 했다.

추가:

- `workflow/ip-contract/scripts/derive_ip_contract.py`
- `workflow/ip-contract/workspace.json`
- `workflow/ip-contract/commands/derive-ip-contract.json`
- `workflow/ip-contract/todo_templates/derive-ip-contract.json`
- `workflow/ip-contract/scripts/run_derive_ip_contract.sh`

canonical command:

```text
python3 workflow/ip-contract/scripts/derive_ip_contract.py <ip> --root <ip-parent>
```

출력:

```text
<ip>/verify/ip_contract.json
```

이 contract는 profile 이름이 아니라 IP artifact에서 파생한 내용을 담는다.

- `generation = derived_from_ip_artifacts_not_static_profile`
- SSOT/IO/goals 기반 capabilities
- interface와 output observability
- required monitors
- required mutation categories
- required evidence gates
- static profile을 선택하지 않았다는 policy

downstream 반영:

- `workflow/STAGE_MANIFEST.json`에 `derive_ip_contract` stage 추가
- `workflow/ssot-gen/scripts/new_ip_emit_chain.sh`가 equivalence goals 뒤에 contract를 생성
- `workflow/signoff/scripts/check_ip_signoff.py`가 `verify/ip_contract.json`을 required gate로 검사
- `workflow/mutation/scripts/mutation_guard.py`가 contract mutation obligation과 unsupported category를 report에 기록
- `workflow/orchestrator/todo_templates/run-to-green.json`에 contract derivation step 추가
- `IP_SIGNOFF.md`에 per-IP contract를 required local evidence로 명시

검증:

```text
python3 -m pytest -q \
  tests/test_ip_contract_derivation.py \
  tests/test_scoreboard_observable_completeness.py \
  tests/test_mutation_guard.py \
  tests/test_ip_signoff_gate.py \
  tests/test_tb_python_compile_gate.py
11 passed

python3 workflow/ip-contract/scripts/derive_ip_contract.py <ip> --root ip_examples
10/10 IPs derived verify/ip_contract.json

python3 workflow/signoff/scripts/check_ip_signoff.py <ip> --root ip_examples
10/10 IPs pass with 15 gates including ip_contract
```

핵심 결론:

```text
General IP support는 profile 선택이 아니라,
각 IP artifact에서 evidence obligation을 파생해야 한다.
```

## 2026-05-31 Ready/Valid FIFO Probe

SPI/UART 다음 general-IP probe로 `ready_valid_fifo_demo`를 만들고 signoff까지 돌렸다.

범위:

- 2-entry single-clock ready/valid FIFO
- sink: `s_valid_i/s_ready_o/s_data_i`
- source: `m_valid_o/m_ready_i/m_data_o`
- status: `level_o`
- stress case: reset idle, FIFO ordering, full backpressure, 1-entry same-cycle push/pop, full-state same-cycle pop+push

Evidence:

```text
python3 workflow/ip-contract/scripts/derive_ip_contract.py ready_valid_fifo_demo --root ip_examples
capabilities=9 monitors=6 evidence=14

python3 ip_examples/ready_valid_fifo_demo/tb/cocotb/test_runner.py
TESTS=1 PASS=1 FAIL=0

python3 workflow/tb-gen/scripts/check_scoreboard_events.py ready_valid_fifo_demo --root ip_examples --source-check --require-events --require-all-goals
goals=5 required=5 scoreboard_rows=5 goals_with_rows=5

python3 workflow/mutation/scripts/mutation_guard.py ready_valid_fifo_demo --root ip_examples --max-mutants 24 --enforce-threshold --threshold 0.70
candidates=24 executed=24 killed=17 survived=7 invalid=0 kill_rate=0.7083

python3 workflow/signoff/scripts/check_ip_signoff.py ready_valid_fifo_demo --root ip_examples
15/15 gates pass

python3 -m pytest -q tests/test_ip_contract_derivation.py tests/test_scoreboard_observable_completeness.py tests/test_mutation_guard.py tests/test_ip_signoff_gate.py tests/test_tb_python_compile_gate.py
16 passed
```

배운 점:

- 첫 mutation run은 kill-rate `0.5455`로 실패했다. 진짜 누락은 full 상태에서 same-cycle pop+push를 허용해야 하는 동작이었다. 즉 `m_ready_i`가 같은 cycle에 drain하면 FIFO가 full이어도 `s_ready_o`가 assert되어야 한다.
- per-IP contract가 처음에는 `backpressure` capability를 놓쳤다. SSOT 문장에 `no same-cycle dequeue`가 있었고 detector가 단순히 `no ` substring만 보고 backpressure를 부정했기 때문이다. 이제는 `no/none/never/without backpressure/stall/flow-control`처럼 문장 자체가 명시적으로 backpressure 부정을 말할 때만 suppress한다.
- `handshake_hold_drop`, `state_update_drop` ready/valid mutation 후보를 추가하니 FIFO kill-rate가 `0.7083`으로 올라갔다.
- 남은 survived mutant는 대부분 내부 clear/self-hold 계열이다. 예: invalid data clear, 사용되지 않는 tail storage clear, 이미 해당 occupancy branch에서 self-hold인 level assignment. 이런 것은 black-box contract가 invalid data나 unused storage clear value를 요구하지 않으면 무조건 TB를 더 깊게 만들 이유는 아니다.

결론:

```text
아직 더 큰 abstraction은 추가하지 않는다.
실제 실패가 요구한 작은 보강만 했다:
  1. full simultaneous FIFO goal 추가
  2. backpressure capability detector 수정
  3. ready/valid-specific mutation 후보 추가
```

다음 IP에서도 같은 원칙을 유지한다. 추상화는 먼저 만들지 말고, 실제 IP가 구체적인 실패나 blind spot을 보여줄 때만 재사용 메커니즘으로 승격한다.

## 2026-05-31 Simple CPU Probe

bounded CPU-class general-IP probe로 `simple_cpu_demo`를 만들고 signoff까지 돌렸다.

범위:

- 8-bit accumulator CPU
- external instruction memory interface: `pc_o`, `instr_i`
- external data memory interface: `data_addr_o`, `data_rdata_i`, `data_wdata_o`, `data_we_o`
- control/status: `start_i`, `running_o`, `done_o`, `acc_o`, `zero_o`
- ISA: `NOP`, `LDI`, `ADDI`, `XORI`, `LOAD`, `STORE`, `JZ`, `JMP`, `HALT`

검증한 program:

- Arithmetic: `LDI 0x12; ADDI 0x05; XORI 0x03; HALT` -> final `acc=0x14`
- Memory: `LDI 0xAB; STORE [2]; LDI 0; LOAD [2]; HALT` -> store event + final `acc=0xAB`
- Branch: `LDI 0; JZ 4; LDI 0x55; NOP; LDI 0x99; HALT` -> executed PCs `[0, 1, 4, 5]`

Evidence:

```text
python3 workflow/ip-contract/scripts/derive_ip_contract.py simple_cpu_demo --root ip_examples
capabilities=7 monitors=5 evidence=13

python3 workflow/rtl-gen/scripts/rtl_compile_report.py simple_cpu_demo --project-root ip_examples
errors=0 diagnostics=0 style_violations=0

python3 ../workflow/lint/scripts/dut_lint_report.py simple_cpu_demo
errors=0 warnings=0 suppression_violations=0 style_violations=0

python3 ip_examples/simple_cpu_demo/tb/cocotb/test_runner.py
TESTS=1 PASS=1 FAIL=0

python3 workflow/tb-gen/scripts/check_scoreboard_events.py simple_cpu_demo --root ip_examples --source-check --require-events --require-all-goals
goals=4 required=4 scoreboard_rows=4 goals_with_rows=4

python3 workflow/mutation/scripts/mutation_guard.py simple_cpu_demo --root ip_examples --max-mutants 32 --enforce-threshold --threshold 0.70
candidates=32 executed=32 killed=23 survived=9 invalid=0 kill_rate=0.7188

python3 workflow/signoff/scripts/check_ip_signoff.py simple_cpu_demo --root ip_examples
15/15 gates pass

python3 -m pytest -q tests/test_ip_contract_derivation.py tests/test_scoreboard_observable_completeness.py tests/test_mutation_guard.py tests/test_ip_signoff_gate.py tests/test_tb_python_compile_gate.py
16 passed
```

배운 점:

- CPU도 static profile 없이 per-IP contract로 잡혔다. 파생 capability는 `datapath_transform`, `fsm_state`, `register_state`, `multi_cycle_timing`, interface obligation 조합이었다.
- Verilator가 9-bit add의 carry bit 미사용을 warning으로 잡았다. ISA가 modulo-256 `ADDI`를 요구하므로 suppression이 아니라 8-bit add로 고치는 게 맞았다.
- mutation은 `0.7188`로 demo threshold를 넘었다. 살아남은 mutant는 대부분 아직 program set에 없는 boundary다: idle `done_q` clear, start-time reset-to-zero self-hold, `NOP`, `JMP`, default PC update.
- provenance refresh와 signoff를 처음에 병렬로 돌려 signoff가 stale provenance를 읽고 한 번 실패했다. refresh 후 signoff를 순차 재실행하니 pass했다. dependent gate는 병렬화하면 안 된다.

결론:

```text
CPU-class IP라고 해서 새 framework가 바로 필요하지는 않다.
CPU가 bounded이고 program set이 명확하면 현재 general flow로 처리된다.

다음 CPU depth가 필요해질 때 추가할 것:
  - NOP/JMP/default-op program
  - non-zero JZ-not-taken program
  - 필요하면 tiny instruction coverage generator
```

이것도 기존 원칙과 같다. CPU-specific profile은 지금 만들지 않는다. 같은 gap이 반복될 때만 재사용 메커니즘으로 승격한다.

## 2026-05-31 Custom FIFO Processor Probe

`custom_fifo_processor_demo`를 만들어서 아래 구조를 실제로 돌렸다.

```text
Custom req/ack ingress
-> Input FIFO
-> Internal packet processing engine
-> Output FIFO
-> Custom valid/ready egress
```

범위:

- ingress custom packet stream: `in_req_i/in_ack_o/in_sop_i/in_eop_i/in_data_i`
- egress custom packet stream: `out_valid_o/out_ready_i/out_sop_o/out_eop_o/out_data_o`
- ingress/output FIFO depth 4
- 처리 규칙: packet SOP byte를 key로 사용한다. SOP 출력은 `key ^ 8'hff`, 나머지 payload byte는 `byte ^ key`. SOP/EOP와 순서는 보존한다.
- status/debug: `in_level_o`, `out_level_o`, `processed_count_o`

Evidence:

```text
python3 workflow/ip-contract/scripts/derive_ip_contract.py custom_fifo_processor_demo --root ip_examples
capabilities=10 monitors=7 evidence=14

python3 workflow/rtl-gen/scripts/rtl_compile_report.py custom_fifo_processor_demo --project-root ip_examples
errors=0 diagnostics=0 style_violations=0

python3 ../workflow/lint/scripts/dut_lint_report.py custom_fifo_processor_demo
errors=0 warnings=0 suppression_violations=0 style_violations=0

python3 ip_examples/custom_fifo_processor_demo/tb/cocotb/test_runner.py
TESTS=1 PASS=1 FAIL=0

python3 workflow/tb-gen/scripts/check_scoreboard_events.py custom_fifo_processor_demo --root ip_examples --source-check --require-events --require-all-goals
goals=4 required=4 scoreboard_rows=4 goals_with_rows=4

python3 workflow/mutation/scripts/mutation_guard.py custom_fifo_processor_demo --root ip_examples --max-mutants 32 --enforce-threshold --threshold 0.70
candidates=32 executed=32 killed=32 survived=0 invalid=0 kill_rate=1.0

python3 workflow/signoff/scripts/check_ip_signoff.py custom_fifo_processor_demo --root ip_examples
15/15 gates pass

python3 -m pytest -q tests/test_ip_contract_derivation.py tests/test_scoreboard_observable_completeness.py tests/test_mutation_guard.py tests/test_ip_signoff_gate.py tests/test_tb_python_compile_gate.py
17 passed
```

배운 점:

- custom ingress와 custom egress도 static profile 없이 per-IP contract로 처리됐다. contract는 packet stream, FIFO/backpressure, datapath transform, register state, multi-cycle timing obligation 조합으로 파생됐다.
- 첫 mutation run은 `9/32`, kill-rate `0.2812`로 실패했다. RTL 기능 문제가 아니라 mutation 후보 선택이 너무 얕았다. 처음 32개가 state self-hold 후보로만 채워졌고, 그중 상당수는 reset/tail-clear 또는 branch상 이미 self-hold인 값이었다.
- mutation 후보를 contract-required category별로 balance하도록 바꾸자 comparator, handshake, operator, state-update 후보가 첫 32개에 같이 들어왔다.
- full FIFO pop+push에 대한 cycle-level throughput observable을 추가했다. output FIFO가 full이어도 egress ready가 같은 cycle에 drain하면 processor가 move할 수 있으므로 ingress ack가 assert되어야 한다. 이 관측이 `full_pop_ready_drop` mutant를 죽였다.
- 사용하지 않는 내부 `in_packet_q`는 monitor를 붙이지 않고 삭제했다. black-box contract에 영향을 주지 않는 state는 더 깊게 관측하는 것보다 제거하는 게 맞다.
- capped mutation run에서는 literal clear보다 non-literal state update를 우선 선택하도록 했다. reset/tail-clear self-hold가 mutation budget을 잡아먹는 것을 막기 위한 작은 일반화다.

결론:

```text
Custom I/F -> FIFO Engine -> Internal Processing -> Custom I/F 구조도 현재 general flow로 가능하다.
새 static profile은 필요 없었다.

받아들인 reusable 개선:
  mutation_guard는 contract-required mutation class를 balance하고,
  cap이 있을 때 의미 있는 state update를 literal clear보다 먼저 선택해야 한다.

받아들인 verification 개선:
  custom backpressure test는 최종 output ordering뿐 아니라
  full+pop+push cycle-level throughput observable을 포함해야 한다.
```

## 2026-05-31 Optional Formal-Proof Workflow Note

formal proof는 유용하지만 지금은 optional로 둔다. 현재
`workflow/STAGE_MANIFEST.json`의 canonical stage가 아니고, general IP flow를
막는 필수 gate로 넣지 않는다.

현재 repo 상태:

- `workflow/STAGE_MANIFEST.json`에는 `formal`, `sby`, `prove` stage가 없다.
- SSOT에는 formal/protocol 재료가 일부 있다.
  - `invariants`
  - `forbidden_states`
  - `forbidden_environment`
  - `formal_property`
  - `cycle_model.handshake_rules`
  - `cycle_model.ordering`
- assertion source를 생성하는 스크립트는 있다.
  - `workflow/fl-model-gen/scripts/emit_protocol_assertions.py`
  - `workflow/fl-model-gen/scripts/emit_formal_properties.py`
- 하지만 이건 assertion source/stub 생성이지 완성된 proof workflow는 아니다.

진짜 proof라고 부르려면 최소 artifact는 아래가 필요하다.

```text
formal/<ip>_formal_top.sv     # harness/wrapper
formal/<ip>_properties.sv     # assume/assert/cover property
formal/run.sby                # SymbiYosys recipe 또는 상용 formal script
formal/formal_report.json     # PASS/FAIL/UNKNOWN 결과
```

formal이 잘 맞는 영역:

```text
FIFO level이 DEPTH를 넘지 않음
empty FIFO에서 pop 안 됨
full FIFO에서 pop 없으면 push accept 안 됨
valid && !ready 동안 output data stable
reset이 architectural state를 초기화
arbiter grant one-hot
```

formal이 첫 도구가 아닌 영역:

```text
CPU program 전체 실행 결과
packet/message reconstruction
large DMA transaction behavior
복잡한 performance/PPA tradeoff
```

도입 규칙:

```text
formal은 optional로 유지한다.
처음에는 ready_valid_fifo_demo 같은 작은 protocol IP에만 pilot으로 붙인다.
다음 조건 전에는 universal signoff gate로 승격하지 않는다:
  1. toolchain 설치
  2. assumption 사람 검토
  3. proof report를 machine evidence로 파싱
  4. pilot에서 실제 bug를 찾거나 의미 있는 risk를 닫음
```

2026-05-31 local tool 확인:

```text
yosys          있음
yosys-smtbmc   있음
sby            없음
SMT solver     없음: z3/yices/boolector/bitwuzla not found
```

결론:

```text
지금은 formal을 구현하지 않는다.
optional future workflow로만 기록한다.
현재 practical loop는 mutation + cocotb + scoreboard를 유지한다.
```

## 2026-05-31 AXI + MCTP Assembler Demo

`ip_examples/axi_mctp_assembler_demo`를 추가했다. 이전 FIFO/CPU/UART/SPI보다
실제 protocol block에 가까운 packet assembly IP다.

IP 범위:

```text
AXI4-Stream byte ingress
  -> simplified MCTP fragment parser
  -> {tag, source EID} 기준 single active message slot
  -> 8-byte bounded payload buffer
  -> AXI4-Stream byte egress
```

단순화한 fragment header:

```text
byte0: bit7=SOM, bit6=EOM, bits3:0=tag
byte1: source EID
byte2..N: payload
```

의도적으로 제외한 것:

```text
multiple active message slots
interleaved tags
real PCIe VDM header parsing
large payload memory / SRAM mapping
```

fresh evidence:

```text
python3 ip_examples/axi_mctp_assembler_demo/model/functional_model.py
passed=true

python3 ip_examples/axi_mctp_assembler_demo/model/cycle_model.py
passed=true

python3 workflow/ip-contract/scripts/derive_ip_contract.py axi_mctp_assembler_demo --root ip_examples
capabilities=12 monitors=7 evidence=14

python3 workflow/rtl-gen/scripts/rtl_compile_report.py axi_mctp_assembler_demo --project-root ip_examples
errors=0 diagnostics=0 style_violations=0

python3 ../workflow/lint/scripts/dut_lint_report.py axi_mctp_assembler_demo
errors=0 warnings=0 suppression_violations=0 style_violations=0

python3 ip_examples/axi_mctp_assembler_demo/tb/cocotb/test_runner.py
TESTS=1 PASS=1 FAIL=0

python3 workflow/tb-gen/scripts/check_scoreboard_events.py axi_mctp_assembler_demo --root ip_examples --source-check --require-events --require-all-goals
goals=11 required=11 scoreboard_rows=11 goals_with_rows=11

bash ../workflow/tb-gen/scripts/check_pyuvm_structure.sh axi_mctp_assembler_demo
PASS

python3 workflow/mutation/scripts/mutation_guard.py axi_mctp_assembler_demo --root ip_examples --max-mutants 32 --enforce-threshold --threshold 0.70
candidates=32 executed=32 killed=25 survived=7 invalid=0 kill_rate=0.7812

python3 workflow/signoff/scripts/check_ip_signoff.py axi_mctp_assembler_demo --root ip_examples
15/15 gates pass

python3 -m pytest -q tests/test_ip_contract_derivation.py tests/test_scoreboard_observable_completeness.py tests/test_mutation_guard.py tests/test_ip_signoff_gate.py tests/test_tb_python_compile_gate.py
18 passed
```

mutation category 결과:

```text
operator_flip:      4/4 killed
comparator_flip:    9/9 killed
state_update_drop:  7/9 killed
constant_flip:      5/10 killed
overall:            25/32 killed
```

중요한 발견:

```text
첫 AXI/MCTP mutation run은 실패했다:
  killed=19/32, kill_rate=0.5938

이 실패는 유용했다.
관측이 빠진 부분을 찾아냈다:
  - output drain 후 m_axis_tvalid_o가 내려가는지
  - 긴 payload에서 buffer 뒤쪽 위치가 맞는지
  - malformed short fragment가 active message state를 지우는지
  - error 후 정상 message에서 error가 clear되는지
  - 이전 EOM 상태가 다음 non-EOM fragment로 새지 않는지
```

해결은 새 profile이 아니었다. per-IP directed goal을 보강했다.

```text
EQ_LONG_PAYLOAD
EQ_MALFORMED_CLEARS_ACTIVE
EQ_ERROR_RECOVERY
EQ_SEQUENTIAL_MESSAGES
post_drain_m_axis_tvalid_o observable 추가
```

남은 survived mutant는 대부분 low-value/equivalent 후보였다.

```text
reset 직후 곧 overwrite되는 internal fragment flag
HDR0에서 clear된 뒤 HDR1에서 다시 결정되는 flag
이미 ST_HDR0인 malformed one-byte frame에서 state_q <= ST_HDR0 self-hold
```

결론:

```text
AXI-stream packet assembly도 general IP workflow에 들어간다.
static AXI/MCTP profile은 필요 없었다.

mutation은 여전히 유용하다.
다만 survivor는 category와 line context로 해석해야 한다.

다음 mutation 개선:
  reset/overwrite-equivalent constant clear 후보를 따로 분류하거나
  capped run에서 낮은 우선순위로 내려야 한다.
```
