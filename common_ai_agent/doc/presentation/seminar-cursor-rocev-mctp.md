# Cursor 활용법 세미나 정리

## MCTP 예시로 보는 ROCEV와 Cursor

이 세미나는 "AI가 쓴 RTL을 믿을 수 있을까?"에서 시작하지만, 답을 거창하게
"AI를 믿자/믿지 말자"로 가져가지 않는다.

핵심은 조금 더 실용적이다.

> AI가 만든 RTL을 바로 믿는 것이 아니라, 무엇을 요구했고, 무엇을 확인했고,
> 어떤 파일이 그 증거인지 보이게 만들자.

러닝 예시는 `mctp_assembler_scratch`다. 이 IP는 AXI4 write로 들어온 PCIe VDM
TLP를 MCTP packet으로 해석하고, fragmented/interleaved message를 조립한 뒤,
payload만 256-bit SRAM에 저장하고 descriptor/readback/status까지 남긴다.

---

## 1. 이야기 흐름

| 순서 | 내용 | 말하고 싶은 점 |
|---|---|---|
| 1 | AI가 쓴 RTL을 믿을 수 있나? | 모델의 자신감은 증거가 아니다. |
| 2 | MCTP assembler 예시 소개 | 조금 복잡한 RTL에서는 확인 단위가 필요하다. |
| 3 | ROCEV로 요구를 쪼개기 | Requirement -> Obligation -> Contract -> Evidence -> Validation |
| 4 | 실제 MCTP 값으로 채우기 | 추상 설명이 아니라 파일과 scenario로 보여준다. |
| 5 | Cursor로 구현하면? | rules, skills, hooks, agents가 workflow를 덜 흩어지게 한다. |
| 6 | Codex/Claude Code로도 일반화 | 핵심은 tool이 아니라 plain file 기반의 evidence chain이다. |

---

## 2. MCTP 예시: 데이터 경로

`mctp_assembler_scratch`의 기본 흐름은 다음과 같다.

```text
AXI4 write transaction
  -> raw PCIe VDM TLP bytes
  -> MCTP-over-PCIe-VDM packet validation
  -> MCTP transport header decode
  -> packet payload assembly by message key with interleaving
  -> first/last TLP header snapshot
  -> MCTP payload-only 256-bit SRAM writes
  -> completed-message descriptor/status/readback
```

이 예시가 좋은 이유는 단순 counter보다 확인할 것이 많기 때문이다.

- AXI write transaction 하나가 TLP 하나인지
- PCIe VDM envelope가 MCTP transport로 유효한지
- MCTP transport header에서 key를 제대로 뽑는지
- interleaved message를 context별로 섞지 않는지
- SRAM에는 payload만, hole 없이 pack되는지
- bad packet은 SRAM/context를 망치지 않고 drop되는지
- descriptor와 APB/AXI readback으로 firmware가 볼 수 있는지

Source:

- [`mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md`](../../mctp_assembler_scratch/req/mctp_assembler_scratch_requirements.md)
- [`mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml`](../../mctp_assembler_scratch/yaml/mctp_assembler_scratch.ssot.yaml)

---

## 3. ROCEV 한 장 요약

| ROCEV | MCTP 예시 |
|---|---|
| Requirement | 한 AXI write transaction은 한 PCIe VDM TLP이고, MCTP payload만 조립해 SRAM에 저장한다. |
| Obligation | TLP boundary, MCTP key parse, interleave context, SRAM no-hole packing, descriptor/readback, drop-no-mutation을 각각 확인한다. |
| Contract | SSOT의 function model refs와 equivalence goals가 판단 기준이다. |
| Evidence | `scoreboard_events.jsonl`, `contract_v2_events.jsonl`, `scenario_e2e_summary.json`, `simulation_quality.json`, `sim_report.txt` |
| Validation | `stage_gate`, `check_sim_disk`, `check_truth_coverage`가 실제 artifact를 다시 읽어 PASS/FAIL을 판단한다. |

여기서 중요한 것은 이름이 아니라 trace다.

요구 문장이 obligation으로 쪼개지고, obligation은 contract에 연결되고, contract는
TB/scoreboard가 관측하고, validation gate가 evidence 파일을 다시 읽는다.

---

## 4. Requirement 예시

원래 요구는 자연어다.

```text
One AXI4 write transaction carries exactly one PCIe VDM TLP.
The IP validates the TLP as MCTP-over-PCIe-VDM, extracts the MCTP
transport header and packet payload, assembles fragmented MCTP messages
across multiple interleaved TLP streams, writes only completed MCTP
message payload bytes to a 256-bit SRAM write interface, publishes
a completed descriptor, records drops/errors, and raises an interrupt.
```

이 문장을 그대로 RTL 생성 prompt에 넣으면 결과가 그럴듯해도 평가가 어렵다.
그래서 요구를 다음처럼 확인 가능한 경계로 내린다.

| 요구 조각 | 확인 포인트 |
|---|---|
| one AXI write transaction = one TLP | `AWLEN`, `WLAST`, `WSTRB`로 TLP byte stream이 맞게 만들어지는가 |
| validate MCTP-over-PCIe-VDM | unsupported VDM, bad MCTP header가 drop되는가 |
| assemble fragmented message | SOM/EOM/sequence/tag/key가 맞게 context에 들어가는가 |
| support interleaving | 두 message key가 교차해도 context가 섞이지 않는가 |
| payload-only SRAM write | PCIe/MCTP header, pad, digest가 SRAM payload로 쓰이지 않는가 |
| no packing holes | 32-byte SRAM word 안에서 payload byte가 빈칸 없이 이어지는가 |
| descriptor/readback | descriptor의 base/len으로 firmware가 payload를 읽을 수 있는가 |

---

## 5. Obligation 예시

Obligation은 "좋아 보인다"가 아니라 "무엇을 보면 닫힌다"까지 포함해야 한다.

| Obligation | 관측해야 하는 것 | 예시 scenario/evidence |
|---|---|---|
| `OBL_AXI_TLP_BOUNDARY` | 한 AXI write burst가 한 TLP byte stream으로 수집된다. | `SC_VALID_SINGLE_PACKET`, `SC_MAX_TU_4096_129_BEATS` |
| `OBL_MCTP_PARSE_KEY` | source EID, tag owner, message tag, sequence, SOM/EOM이 key/state로 반영된다. | `FM_PARSE_MCTP`, parser observables |
| `OBL_INTERLEAVE_CONTEXT` | 서로 다른 message key가 교차해도 context가 섞이지 않는다. | `SC_INTERLEAVE_TWO_KEYS`, `SC_INTERLEAVE_TWO_Q_COMPLETE` |
| `OBL_SRAM_PACK_NO_HOLES` | payload bytes가 256-bit SRAM word에 hole 없이 pack된다. | `SC_UNALIGNED_SRAM_PACK_NO_HOLES` |
| `OBL_DESCRIPTOR_READBACK` | descriptor가 payload base/len을 노출하고 AXI readback이 trim된다. | `SC_AXI_READBACK_TRIM`, `SC_APB_REGS_PER_Q` |
| `OBL_DROP_NO_MUTATION` | bad packet은 SRAM write/context mutation 없이 drop된다. | `PD_BAD_MCTP_HEADER`, drop scenarios |

---

## 6. Contract 예시

Contract는 "정답을 누가 말하는가"를 고정한다.

MCTP 예시에서는 SSOT YAML의 function model refs가 contract 역할을 한다.

| Block | Contract ref |
|---|---|
| AXI write ingress | `FM_ACCEPT_AXI_TLP` |
| PCIe VDM parser | `FM_FILTER_VDM` |
| MCTP parser | `FM_PARSE_MCTP` |
| Context table | `FM_ASSEMBLE_FRAGMENT`, `FM_COMPLETE_MESSAGE` |
| SRAM packer | `FM_SRAM_PACK_WRITE` |
| AXI readback | `FM_AXI_READBACK` |

TB는 임의로 "PASS"를 만들면 안 된다. 기본 형태는 다음이어야 한다.

```text
RTL observed == SSOT / FunctionalModel expected
```

즉, contract가 먼저 있고, TB/scoreboard는 그 contract를 관측하는 쪽이다.

---

## 7. Evidence 예시

Evidence는 "테스트 돌렸습니다"라는 말이 아니라, 나중에 다시 열어볼 수 있는 파일이다.

| Evidence file | 실제 내용 |
|---|---|
| `sim/sim_report.txt` | `TESTS=3 PASS=3 FAIL=0`, `0 errors, 0 warnings` |
| `sim/scenario_e2e_summary.json` | `26/26` directed scenarios observed, missing/fail/issue 없음 |
| `sim/simulation_quality.json` | `86` evidence rows, `13` classes, issue/missing observable 없음 |
| `sim/contract_v2_events.jsonl` | SRAM backpressure row, APB payload count row |
| `sim/scoreboard_events.jsonl` | scenario/equivalence scoreboard rows |

`contract_v2_events.jsonl`의 예시는 특히 발표에 쓰기 좋다.

```json
{
  "goal_id": "CONTRACT_V2_SRAM_BACKPRESSURE",
  "passed": true,
  "rtl_observed": {
    "sram_wr_valid": 1,
    "sram_wr_ready": 0,
    "sram_wr_addr": 0,
    "sram_wr_strb": 131071
  }
}
```

```json
{
  "goal_id": "CONTRACT_V2_APB_Q_PAYLOAD_COUNT_AFTER_UPDATE",
  "passed": true,
  "rtl_observed": {
    "payload_byte_count": 17,
    "pready": 1
  }
}
```

Source:

- [`sim_report.txt`](../../mctp_assembler_scratch/sim/sim_report.txt)
- [`scenario_e2e_summary.json`](../../mctp_assembler_scratch/sim/scenario_e2e_summary.json)
- [`simulation_quality.json`](../../mctp_assembler_scratch/sim/simulation_quality.json)
- [`contract_v2_events.jsonl`](../../mctp_assembler_scratch/sim/contract_v2_events.jsonl)

---

## 8. Validation 예시

Validation은 evidence 파일을 다시 읽어 PASS/FAIL을 판단하는 단계다.

예시 명령:

```bash
python3 mctp_assembler_scratch/tb/cocotb/test_runner.py
ATLAS_COV_BLOCK_IS_FAIL=0 python3 .cursor/workflow/req-gen/scripts/stage_gate.py sim mctp_assembler_scratch --root .
python3 .cursor/workflow/sim/scripts/check_sim_disk.py mctp_assembler_scratch
python3 .cursor/workflow/reqcov/scripts/check_truth_coverage.py mctp_assembler_scratch --root .
```

여기서 조심할 점은 `results.xml` 하나만 보고 끝내지 않는 것이다.

빈 XML, 오래된 summary, 잘린 로그는 좋은 증거가 아니다. 그래서 sim report,
scoreboard/event rows, scenario summary, coverage/truth coverage를 같이 본다.

---

## 9. Cursor로 구현하면?

Cursor 부분은 네 가지 표면으로 설명하면 된다.

| Cursor 표면 | 이 예시에서의 역할 |
|---|---|
| Rules | 작업 중 계속 깔리는 기본 규칙. SSOT 권위, evidence discipline, sim output truncation 금지. |
| Skills | 반복 실행 순서. `rocev-chain`이 `req -> rtl -> tb -> sim` 순서를 제공. |
| Hooks | 멈추거나 막아야 하는 순간. open todo, unsafe shell, evidence 없는 완료를 잡음. |
| Agents | stage owner 분리. `/req-gen`, `/rtl-gen`, `/tb-gen`, `/sim`이 자기 영역을 맡음. |

공식 문서:

- [Cursor Rules](https://cursor.com/docs/rules)
- [Cursor Hooks](https://cursor.com/docs/hooks)
- [Cursor Skills](https://cursor.com/docs/skills)
- [Cursor Subagents](https://cursor.com/docs/subagents)

---

## 10. Cursor Rules 예시

실제 파일:

- [`.cursor/rules/30-hardware-workflow.mdc`](../../.cursor/rules/30-hardware-workflow.mdc)
- [`.cursor/rules/80-todo-evidence.mdc`](../../.cursor/rules/80-todo-evidence.mdc)
- [`.cursor/rules/85-rocev-todo-loop.mdc`](../../.cursor/rules/85-rocev-todo-loop.mdc)

역할:

| Rule | MCTP 예시에서 하는 일 |
|---|---|
| `30-hardware-workflow.mdc` | `req/`와 `yaml/`을 contract로 보고, generated artifact를 손으로 고쳐 PASS 만들지 않게 함 |
| `80-todo-evidence.mdc` | todo를 prompt decoration이 아니라 evidence contract로 취급 |
| `85-rocev-todo-loop.mdc` | full chain은 `rocev-chain` 또는 `/rocev-chain`으로 돌리고, `current_todos.json`을 stop hook이 읽게 함 |

발표 멘트:

> Rules는 Cursor에게 "이 repo에서는 어떤 습관으로 일해야 하는지"를 계속 깔아두는 장치입니다.
> MCTP 예시에서는 특히 SSOT 권위와 evidence discipline을 잊지 않게 합니다.

---

## 11. Cursor Skill 예시

실제 파일:

- [`.cursor/skills/rocev-chain/SKILL.md`](../../.cursor/skills/rocev-chain/SKILL.md)

`rocev-chain`은 다음 stage 순서를 제공한다.

```text
req -> rtl -> tb -> sim
```

MCTP 예시로 쓰면:

```bash
IP=mctp_assembler_scratch

python3 .cursor/workflow/req-gen/scripts/emit_requirements_from_ssot.py $IP --root .
python3 .cursor/workflow/req-gen/scripts/promote_requirement_review.py $IP --root .
python3 .cursor/workflow/req-gen/scripts/lock_requirement_set.py $IP --root .
python3 .cursor/workflow/req-gen/scripts/check_locked_truth_bundle.py $IP --root .

python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py \
  $IP --root . --profile dv --execute --from-stage ssot-rtl --until lint

python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py \
  $IP --root . --profile dv --execute --from-stage ssot-tb-cocotb --until ssot-tb-cocotb

python3 $IP/tb/cocotb/test_runner.py
python3 .cursor/workflow/sim/scripts/check_sim_disk.py $IP
```

발표 멘트:

> Skill은 Cursor의 마법이 아니라, 반복 실행 순서를 접어둔 것입니다.
> 세미나에서는 skill 파일을 열어서 "이 명령들이 stage를 어떻게 닫는지" 보여주면 충분합니다.

---

## 12. Cursor Hooks 예시

실제 파일:

- [`.cursor/hooks.json`](../../.cursor/hooks.json)
- [`.cursor/hooks/guard-shell.py`](../../.cursor/hooks/guard-shell.py)
- [`.cursor/hooks/stop-todo-loop.py`](../../.cursor/hooks/stop-todo-loop.py)

역할:

| Hook | 하는 일 |
|---|---|
| `beforeShellExecution` -> `guard-shell.py` | `vvp`, `cocotb`, `run_sim.py` output을 `head/tail/grep`로 잘라 보는 습관을 막음 |
| `stop` -> `stop-todo-loop.py` | `current_todos.json`에 open todo가 남아 있으면 follow-up message로 작업을 이어감 |
| `subagentStop` -> `subagent-evidence-check.py` | subagent가 증거 없이 완료 선언하는 흐름을 잡음 |
| `preToolUse` -> `protect-generated-artifacts.py` | workflow-owned artifact를 손으로 고치는 위험을 줄임 |

발표 멘트:

> Hooks는 큰 기능보다 작은 사고 방지에 가깝습니다.
> MCTP처럼 evidence가 여러 파일에 나뉘면, 잘린 로그나 빈 evidence를 PASS로 오해하기 쉽습니다.

---

## 13. Cursor Agents 예시

실제 파일:

- [`.cursor/agents/rocev-chain.md`](../../.cursor/agents/rocev-chain.md)
- [`.cursor/agents/tb-gen.md`](../../.cursor/agents/tb-gen.md)
- [`.cursor/agents/sim.md`](../../.cursor/agents/sim.md)

역할:

| Agent | 담당 |
|---|---|
| `/rocev-chain` | 전체 stage order와 gate citation을 관리 |
| `/req-gen` | requirements와 locked truth bundle |
| `/rtl-gen` | RTL repair, compile/lint evidence |
| `/tb-gen` | FunctionalModel/equivalence goals 기반 scoreboard |
| `/sim` | sim log, JSON, XML, VCD, scoreboard evidence |

발표 멘트:

> 역할을 나누면 failure를 분류하기 쉬워집니다.
> MCTP 실패가 TB 관측 누락인지, RTL 동작 문제인지, sim 증거 문제인지 말할 수 있습니다.

---

## 14. 8분 데모 흐름

세미나에서 짧게 보여줄 수 있는 흐름:

| Step | 보여줄 것 | 파일/명령 |
|---|---|---|
| 1 | 요구 문장 확인 | `req/mctp_assembler_scratch_requirements.md` |
| 2 | obligation 하나 선택 | `OBL_SRAM_PACK_NO_HOLES` |
| 3 | contract 위치 확인 | SSOT `FM_SRAM_PACK_WRITE` |
| 4 | scenario 연결 확인 | `SC_UNALIGNED_SRAM_PACK_NO_HOLES` |
| 5 | Cursor skill 확인 | `.cursor/skills/rocev-chain/SKILL.md` |
| 6 | evidence 파일 열기 | `sim_report`, `scenario_e2e_summary`, `simulation_quality`, `contract_v2_events` |

짧은 마무리:

> Cursor는 실행 표면이고, 판단 기준은 ROCEV 파일입니다.
> 예시는 작게 보여주고, 같은 모양을 다른 IP에도 옮길 수 있게 합니다.

---

## 15. 슬라이드 구성

| Slide | 제목 | 역할 |
|---:|---|---|
| 1 | MCTP 예시로 보는 ROCEV와 Cursor | 세미나 톤과 러닝 예시 소개 |
| 2 | 문제는 AI라기보다 확인 단위가 흐릿한 데서 생김 | 도입 질문 |
| 3 | MCTP 데이터 경로 | 예시 IP 구조 |
| 4 | ROCEV ledger | 다섯 칸 한눈에 보기 |
| 5 | Requirement | 자연어 요구를 경계 조건으로 내리기 |
| 6 | Obligation | 관측 가능한 obligation으로 쪼개기 |
| 7 | Contract | SSOT function model refs |
| 8 | Evidence | 실제 evidence 파일과 수치 |
| 9 | Validation | gate가 다시 읽는 기준 |
| 10 | Cursor map | rules/skills/hooks/agents 개요 |
| 11 | Rules example | 실제 `.cursor/rules` 파일 |
| 12 | Skill example | `rocev-chain` 실행 순서 |
| 13 | Hooks example | guard/stop/evidence hooks |
| 14 | Agents example | stage owner 분리 |
| 15 | Demo flow | 8분짜리 예시 흐름 |

PPTX:

- [`seminar-cursor-rocev-mctp.pptx`](seminar-cursor-rocev-mctp.pptx)
