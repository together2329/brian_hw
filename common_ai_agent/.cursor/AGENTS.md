# AGENTS.md — 이 팩으로 일하는 에이전트의 운영 규약

이 파일은 `.cursor` 팩의 **진입점 요약**이다. Cursor는 이 평문 마크다운을
프로젝트 루트/하위 디렉토리에서 자동으로 읽는다 (rules의 간단한 대안).
세부 강제는 `.cursor/rules/*.mdc`(자동 주입)와 `.cursor/hooks/`(기계 강제)에 있다.

## 핵심 규약 (req → rtl → tb → sim)

1. **ROCEV 척추**: 모든 하드웨어 작업은
   Requirement → Obligation → Contract → Evidence → Validation 으로 진행한다.
   풀체인은 `/orchestrator`(컨덕터) 또는 `rocev-chain` skill. 단일 스테이지는
   `/req-gen` `/rtl-gen` `/tb-gen` `/sim` 등 오너 subagent.

2. **gate-then-advance**: 다음 스테이지는 직전 게이트의 PASS verdict 라인을
   손에 쥔 뒤에만 진입한다. 모델 확신은 증거가 아니다.

3. **증거 없는 완료 금지**: todo는 validator/test의 신선한 출력으로만 닫는다.
   `stop` hook이 열린 todo가 남으면 멈춤을 막고, `subagentStop` hook이 증거
   없는 완료 주장을 되돌린다. 이걸 우회하려 하지 말 것.

4. **생성물은 워크플로 소유**: `<ip>/sim/`, `verify/`, `cov/` 등은 손으로 고치지
   말고 해당 게이트를 재실행해 재생성한다. `.cursor/{workflow,src,scripts}`는
   vendored 복사본이라 직접 편집 금지.

5. **히스토리**: 스테이지 verdict마다
   `python3 .cursor/scripts/ip_wiki.py log <ip> --stage S --title "<verdict>"` 로
   `<ip>/wiki`에 남기고, 끝에 `... check <ip>`.

## 먼저 읽을 것

- `DELIVERY.md` — 설치·1분 스모크·IP 만들기 시작점
- `SETUP.md` — Python/iverilog/cocotb 설치
- `skills/rocev-chain/SKILL.md` + `KNOWN_TRAPS.md` — 스테이지 명령 + 실전 함정
- `README.md` — 구성과 원리

## 범위 밖 (이 팩이 안 하는 것)

- LLM 저작 스테이지(ssot→fl 자동 생성)는 provider 키가 있어야 작동.
  키 없이도 결정론적 게이트/시뮬레이션은 전부 돈다.
- `stop` hook 루프는 Cursor IDE 대화 모드에서만 발화 (headless/CLI 미지원).
