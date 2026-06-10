# .cursor 전달본 — 받는 사람용 설명서

이 `.cursor` 폴더 **하나만으로** Cursor에서 IP를 req→rtl→tb→sim까지 만들 수 있습니다.
repo 없이 자족합니다 (workflow 본체·엔진·헬퍼가 폴더 안에 vendored).

## 1. 설치

자기 프로젝트 루트에 `.cursor`를 둔다:

```
<your-project>/
└─ .cursor/        ← 이 폴더 통째로
```

Cursor IDE로 `<your-project>`를 열면 끝. rules가 자동 주입되고
`/orchestrator`, `/sim`, `/rtl-gen` 같은 subagent와 skill이 바로 보인다.

## 2. 준비물

| 필수 | 용도 |
|---|---|
| `python3` (3.9+) | 게이트·엔진·ip_wiki·MCP 전부 |
| `iverilog` + `cocotb` | 실제 시뮬레이션 |
| (선택) LLM provider 키 | ssot→fl 자동 **저작** 스테이지. 없어도 결정론적 게이트/시뮬은 동작 |

## 3. 1분 동작 확인 (스모크)

프로젝트 루트에서:

```bash
# ① 엔진이 vendored 경로로 import 되나
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py --help     # usage 출력 → OK

# ② 게이트 단독 실행 (없는 IP → 정상 FAIL verdict, crash 아님)
python3 .cursor/workflow/sim/scripts/check_sim_disk.py ghost_ip            # [check_sim_disk] FAIL ... → OK

# ③ IP wiki 라운드트립
mkdir demo_ip
python3 .cursor/scripts/ip_wiki.py init demo_ip
python3 .cursor/scripts/ip_wiki.py log demo_ip --stage sim --title "hello"
python3 .cursor/scripts/ip_wiki.py check demo_ip                           # [ip_wiki] PASS → OK
```

stop hook(todo 루프) 확인은 **Cursor IDE 대화창**에서만 가능 (cursor-agent CLI는 stop 미지원):
`current_todos.json`에 미완료 todo를 하나 남기고 에이전트가 멈추려 하면 자동으로 다음 todo를 재투입한다.

## 4. IP 하나 만들기 — 시작점

`/orchestrator`에게 "새 IP `<이름>`을 req부터 sim까지" 라고 시키거나,
`rocev-chain` skill을 따른다. **반드시 먼저 읽을 것**:

- `skills/rocev-chain/SKILL.md` — 스테이지별 명령
- `skills/rocev-chain/KNOWN_TRAPS.md` — 실전 함정 모음 (게이트 명령 보정, req 번들
  수동 저작법, SSOT/TB 생성기 워크어라운드). **이걸 안 읽으면 같은 함정에 다시 빠진다.**

스테이지마다 `ip_wiki log`로 verdict를 `<ip>/wiki`에 남기고, 끝에 `ip_wiki check`.

## 5. 동작 원리 (한 장)

```
rules(가드레일) + skills(절차) + agents(오너) → "정본 게이트를 통과해야 다음으로"
                                              ↓
hooks: stop=open todo 남으면 멈춤 금지 / subagentStop=증거 없는 완료 차단
                                              ↓
초록불로 가는 유일한 경로 = 진짜 게이트 PASS  (가짜 통과 불가)
```

자세히는 `README.md` 참조.

## 6. MCP (선택) — 외부 RTL DB query

`mcp.json`이 `rtl-db` 서버를 등록한다. 이전 프로젝트의 RTL 지식을 query하려면
`ATLAS_RTL_DB_QUERY` / `ATLAS_RTL_DB_WIKI` env를 자기 DB로 설정.
툴: `rtl_db_query`, `rtl_db_wiki` (+ `ontology_query`, `wiki_search`).

## 7. 주의

- `workflow/`, `src/`, `scripts/` 안은 **vendored 복사본** — 직접 고치지 말 것.
  업데이트는 보내준 쪽에서 새 `.cursor`를 받는다.
- 생성물(`<ip>/sim/`, `verify/`, `cov/`)은 워크플로가 소유 — 손으로 편집 금지,
  반드시 해당 게이트를 재실행해 재생성.
