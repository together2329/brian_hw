# Cursor 활용 세미나

## 프롬프트보다 workflow 만들기

---

## 1. Cursor를 어떻게 볼 것인가

Cursor를 단순히 “AI 채팅이 붙은 에디터”로만 쓰면 매번 같은 설명을 반복하게 된다.

조금 더 실용적인 관점은 이렇다.

```text
Cursor = 내 프로젝트의 작업 방식을 실행하는 표면
```

즉, Cursor 안에 다음을 넣어두는 것이다.

| 넣어둘 것 | 의미 |
|---|---|
| 기준 | 이 프로젝트에서는 무엇을 완료로 보는가 |
| 절차 | 반복 작업을 어떤 순서로 하는가 |
| 역할 | 어떤 일을 누가 맡는가 |
| 안전장치 | 빠뜨리면 안 되는 순간에 어떻게 잡는가 |

오늘 볼 네 가지는 이것이다.

```text
Rules  -> 기준
Skills -> 절차
Agents -> 역할
Hooks  -> 안전장치
```

---

## 2. 왜 workflow가 필요한가

AI가 만든 코드가 항상 틀린다는 이야기가 아니다.

문제는 보통 더 평범하다.

```text
확인해야 할 조건이 workflow 안에 없으면,
테스트가 PASS여도 중요한 케이스가 빠질 수 있다.
```

MCTP 예시:

```text
mctp_assembler_v3 ingress

요구사항:
  non-contiguous WSTRB는 malformed AXI/TLP ingress event여야 한다.

처음 테스트:
  6개 directed scenario PASS

문제:
  모든 scenario가 contiguous WSTRB만 사용했다.
  그래서 WSTRB edge case를 실제로 확인하지 않았다.

adversarial probe:
  WSTRB = 0x00FF00FF
  DUT accept = 1
  FL accept  = 0

결론:
  테스트 PASS였지만 req edge case가 workflow에서 빠져 있었다.
```

여기서 얻을 교훈은 간단하다.

```text
좋은 Cursor 활용은 “잘 물어보기”만이 아니라
빠지면 안 되는 확인을 작업 흐름 안에 넣는 것이다.
```

참고 wiki:

- `doc/wiki/mctp-assembler-v3-ingress-fidelity-20260603.md`

---

## 3. Cursor의 네 가지 재료

Cursor에는 workflow를 만들 때 쓸 수 있는 네 가지 표면이 있다.

| 기능 | 역할 | 쉽게 말하면 |
|---|---|---|
| Rules | 기준 | “이 프로젝트에서는 이렇게 일한다” |
| Skills | 절차 | “이 일을 할 때는 이 순서로 한다” |
| Agents | 역할 | “이 종류의 일은 이 담당자가 맡는다” |
| Hooks | 안전장치 | “이 순간에는 자동으로 확인/차단한다” |

네 가지를 따로 보면 기능 설명이다.

하지만 같이 보면 workflow가 된다.

```text
Rules가 기준을 깔고
Skills가 절차를 실행하고
Agents가 각 단계를 맡고
Hooks가 빠뜨리는 것을 잡는다
```

예시:

```text
pwm_gen_cx1를 확인한다
  -> Rule: 완료 보고는 ROCEV 형식으로 한다
  -> Skill: compile → lint → sim → scoreboard → coverage 순서로 본다
  -> Agent: requirement / rtl / verification / validator가 역할을 나눈다
  -> Hook: "tests passed"만 보고 끝내는 것을 막는다
```

이 예시는 실제 repo artifact로도 이어진다:

```text
.cursor_new/examples/pwm-gen-cx1-rocev-worked-example.md
```

---

## 4. Rules: 생각의 기준을 깐다

Rules는 Cursor에게 항상 참고할 작업 기준을 알려준다.

하드웨어 작업에서는 먼저 “완료를 어떻게 볼 것인가”를 정해두는 게 좋다.

```text
AI가 만든 RTL도 결국 확인 가능한 결과로 남아야 한다.
```

이 장에서 보여줄 핵심 예시는 이것 하나다.

```text
.cursor/rules/00-rocev-workflow.mdc
```

```md
---
description: Hardware completion must be reported in ROCEV form
alwaysApply: true
---

# ROCEV Completion Rule

When claiming RTL/TB/sim/formal work is done,
answer in this form:

Requirement: what behavior was required?
Obligation: what exact duty was closed?
Contract: what checker/model/property judged it?
Evidence: what fresh file/log/proof exists?
Validation: closed / not closed / needs more evidence

Do not write "tests passed" alone.
If one field is missing, say it is missing.
```

Rules에 넣기 좋은 것:

| Rule로 둘 것 | 이유 |
|---|---|
| ROCEV 보고 형식 | 완료 판단의 기본 언어 |
| evidence 없는 완료 금지 | 모델 확신과 증거를 분리 |
| PASS 종류 구분 | compile/sim/scoreboard/formal을 섞지 않기 |
| stale evidence 금지 | 예전 PASS를 현재 PASS로 착각 방지 |

슬라이드에서 한 줄로 정리하면:

```text
Rule은 Cursor에게 "이 프로젝트에서는 완료를 이렇게 판단한다"를 알려준다.
```

예시 완료 보고:

```text
Requirement: pwm_out follows counter_q < duty_reg.
Obligation: OBL_PWM_OUT_001.
Contract: FunctionalModel.apply + scoreboard compare.
Evidence: results.xml exists, scoreboard_events.jsonl has rows, VCD exists.
Validation: not fully closed yet; coverage.json is blocked.
```

여기서 evidence는 한 종류가 아니다. 필요에 따라 RTL compile, lint,
TB scenario, sim result, scoreboard row, coverage, VCD, formal proof가 모두
evidence가 될 수 있다.

이 표는 다음 장이나 appendix로 빼도 된다. Rules 장에서는 “완료의 언어를
정한다”는 메시지만 남기는 편이 더 좋다.

---

## 5. Skills: 반복 절차를 접어둔다

Skills는 재사용 가능한 지식, 지침, 스크립트를 패키징하는 방식이다.

공식 구조는 대략 이렇다.

```text
.agents/
  skills/
    my-skill/
      SKILL.md
      scripts/
      references/
      assets/
```

`SKILL.md`에는 언제 이 skill을 쓰는지, 어떤 순서로 작업하는지, 어떤 파일이나
명령을 확인해야 하는지 적는다.

예시:

```text
.cursor/skills/run-hw-validation/SKILL.md
```

```md
---
name: run-hw-validation
description: Run validation after RTL or TB changes.
---

# Run HW Validation

Use this after RTL/TB changes.

1. Read the changed files.
2. Identify affected requirement or obligation.
3. Run simulation.
4. Check scoreboard events.
5. Check simulation quality.
6. Report PASS only with evidence paths.
```

Rules와 Skills의 차이:

```text
Rule  = 항상 깔리는 기준
Skill = 필요할 때 실행하는 절차
```

MCTP 예시:

```text
MCTP ingress를 수정했다
  -> run-hw-validation skill 실행
  -> sim 실행
  -> scoreboard 확인
  -> WSTRB edge case evidence 확인
  -> evidence 없으면 PASS 금지
```

---

## 6. Agents: 역할을 나눠 맡긴다

Agents는 역할별 담당자다.

한 agent에게 모든 것을 시키면 실패했을 때 원인이 흐려진다.

하드웨어 workflow에서는 역할을 이렇게 나눌 수 있다.

| Agent | 담당 |
|---|---|
| `/req-gen` | requirement 정리, obligation 후보 |
| `/rtl-gen` | RTL 구현/수정 |
| `/tb-gen` | testbench, scoreboard, scenario |
| `/sim` | simulation 실행, evidence 수집 |

Skill 안에서 Agent 위임을 적어둘 수도 있다.

```md
# MCTP validation flow

1. `/rtl-gen` checks RTL changes.
2. `/tb-gen` checks missing scenarios and scoreboard rows.
3. `/sim` runs simulation and collects evidence.
4. Final answer cites validation output.
```

주의해서 말하면:

```text
Skill이 Agent를 “마법처럼 실행한다”기보다는,
Skill 안에 어떤 Agent에게 어떤 일을 맡길지 절차로 적어둘 수 있다.
```

이렇게 나누면 좋은 점:

```text
실패가 났을 때
  RTL 문제인지
  TB 관측 누락인지
  sim evidence 문제인지
  requirement가 애매한지
더 빨리 분류할 수 있다.
```

---

## 7. Hooks: 중요한 순간에 자동으로 잡는다

Hooks는 특정 순간에 자동으로 실행되는 안전장치다.

대단한 자동화보다, 작은 나쁜 습관을 막는 데 유용하다.

예시:

```json
{
  "hooks": {
    "beforeShellExecution": [
      { "command": ".cursor/hooks/guard-shell.py" }
    ],
    "stop": [
      { "command": ".cursor/hooks/stop-todo-loop.py" }
    ],
    "subagentStop": [
      { "command": ".cursor/hooks/subagent-evidence-check.py" }
    ]
  }
}
```

Hook으로 잡기 좋은 것:

| Hook | 예시 |
|---|---|
| `beforeShellExecution` | `run_sim.py | head`처럼 sim output을 잘라 보는 명령 차단 |
| `stop` | todo가 남았으면 종료하지 않고 이어가기 |
| `subagentStop` | agent가 evidence 없이 완료 선언하면 다시 확인 |
| `preToolUse` | generated artifact를 손으로 고치는 위험 차단 |

MCTP 예시로 보면:

```text
처음 테스트 PASS
하지만 edge case evidence가 없음

Hook이 직접 WSTRB 케이스를 만들어주지는 않는다.
대신 “evidence 없이 완료”나 “sim output 잘라 보기” 같은 습관을 막아준다.
```

즉:

```text
Hooks = workflow의 안전벨트
```

---

## 8. 네 개를 묶으면 workflow가 된다

마지막으로 네 가지를 다시 묶어보면:

| Cursor 기능 | workflow에서의 역할 |
|---|---|
| Rules | 기준을 깐다 |
| Skills | 절차를 실행한다 |
| Agents | 역할을 나눈다 |
| Hooks | 빠뜨리는 것을 잡는다 |

전체 그림:

```text
작업 요청
  -> Rules가 기준을 제공
  -> Skill이 실행 순서를 제시
  -> Agents가 단계별로 처리
  -> Hooks가 위험한 순간에 개입
  -> Evidence를 보고 완료 판단
```

MCTP 사례의 교훈:

```text
테스트 PASS가 곧 충분한 확인은 아니다.
빠진 edge case가 있으면 workflow에 다시 넣어야 한다.
```

마무리 문장:

```text
Cursor 자체가 품질을 보장하지는 않는다.

하지만 프로젝트의 기준, 반복 절차, 역할 분리, 안전장치를
Cursor 안에 넣어두면 같은 실수를 덜 반복하게 만들 수 있다.
```

한 줄 요약:

```text
프롬프트를 잘 쓰는 것보다,
반복되는 작업 방식을 workflow로 고정하는 것이 더 오래 간다.
```

---

## 참고 링크

- Cursor Rules: https://cursor.com/docs/rules
- Cursor Skills: https://cursor.com/docs/skills
- Cursor Hooks: https://cursor.com/docs/hooks
- Cursor Subagents: https://cursor.com/docs/subagents

## 참고 wiki

- `doc/wiki/mctp-assembler-v3-ingress-fidelity-20260603.md`
- `doc/wiki/mctp-assembler-scratch-flow-20260531.md`
- `doc/wiki/evidence-contract-obligation-traceability.md`
