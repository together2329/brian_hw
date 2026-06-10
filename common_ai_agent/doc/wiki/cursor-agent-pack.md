---
title: Cursor Agent Pack — rules/hooks/subagents/skills + todo-loop + ROCEV chain
category: tooling
tags: [cursor, hooks, subagents, skills, rules, todo-loop, rocev]
status: v2 (2026-06-10) — todo-loop stop hook + ROCEV req→rtl→tb→sim chain skill 추가
---

# Cursor Agent Pack

`common_ai_agent/.cursor/`는 Cursor가 이 repo의 workflow를 Claude Code와 같은
권위 모델로 구동하기 위한 팩이다. 규약 원문은 repo 루트 `AGENTS.md`(공통)이며,
이 팩은 그것을 Cursor 네이티브 표면(rule/hook/subagent/skill)으로 구체화한다.

## 구성 (Cursor 공식 스펙 기준)

| 표면 | 위치 | 스펙 요점 |
|---|---|---|
| Rules | `.cursor/rules/*.mdc` | frontmatter `description`/`alwaysApply`/`globs` |
| Hooks | `.cursor/hooks.json` + `hooks/*.py` | stdin JSON → stdout JSON; `stop` hook은 `followup_message`로 자동 재투입 (`loop_limit`) |
| Subagents | `.cursor/agents/*.md` | frontmatter `name`/`description`/`model`/`readonly`; `/name` 또는 자동 위임 |
| Skills | `.cursor/skills/<name>/SKILL.md` | folder명 = skill명; name+description만 카탈로그 로드, 매칭 시 본문 로드 |

## Todo-loop hook (`hooks/stop-todo-loop.py`)

Claude Code의 "todo가 남아 있으면 멈추지 않는다" 루프를 Cursor `stop` hook으로 구현:

- 입력 `status == "completed"`일 때만 작동 (abort/error에는 개입 안 함)
- `TODO_FILE`(기본 `<project>/current_todos.json`, TodoTracker 스키마)을 읽어
  open todo(= status ∉ {completed, approved, cancelled, skipped})가 남아 있으면
  `followup_message`로 다음 todo + 증거 규율(rule 80)을 재투입
- `loop_limit`(hooks.json, 기본 20)으로 무한루프 방지; open 0이면 `{}` (정상 종료)
- 검증: `tests/test_cursor_pack.py` (subprocess로 stdin/stdout 계약 테스트)

## ROCEV chain (req → rtl → tb → sim)

`skills/rocev-chain/SKILL.md` + `agents/rocev-chain.md`가
Requirement→Obligation→Contract→Evidence→Validation을 스테이지별로 닫는다:

| 스테이지 | Obligation 생성/계약 | Evidence | Validation |
|---|---|---|---|
| req | `emit_requirements_from_ssot` → `promote_requirement_review` → `lock_requirement_set` → `stage_contract_todos`(VCM projector) | `req/*.json` locked bundle | `check_locked_truth_bundle` + `stage_gate` |
| rtl | rtl todo ledger (`rtl/rtl_todo_plan.json`) | `rtl/*.sv` + `rtl_compile.json` | lint/compile gate + `--audit-rtl` |
| tb | scoreboard contract (equiv goals) | `tb/cocotb/*` + scoreboard events | tb gate + ledger 검증 |
| sim | per-obligation sim todos | `sim/results.xml`, `sim_report.txt` | `check_sim_disk` + `check_truth_coverage` + goal-audit |

실행 래퍼는 기존 `skills/rtl-to-signoff/scripts/rtl_to_signoff.py` (stage id:
`ssot-rtl`, `ssot-tb-cocotb`, `sim`, `goal-audit` 등)를 그대로 쓴다 — 구현 복제 금지.

## Per-IP wiki (`<ip>/wiki/`) — 개발 히스토리 축적

`scripts/ip_wiki.py` (init/log/page/check) + `skills/ip-wiki`. doc/wiki와
같은 형태(frontmatter + `[[link]]`)를 IP 폴더에 내장 — 스테이지 통과/설계 결정/
함정을 `log`로 쌓고(append-only, 날짜 섹션 자동), `check`가 frontmatter·링크
무결성을 게이트한다. rocev-chain의 각 스테이지 Validation 후 log가 의무.
온톨로지: `platform.ip-wiki` 단위, OBL_IP_WIKI_HELPER / OBL_IP_WIKI_CHECK_KILLPROOF.

## MCP 서버 (`scripts/atlas_mcp_server.py`)

stdio JSON-RPC (MCP 2025-06-18, stdlib-only). `.cursor/mcp.json`으로 Cursor에 등록.

서버 키는 `rtl-db` — **본 용도는 외부 RTL DB query** (Brian 지시 2026-06-10).

| tool | 기능 |
|---|---|
| `rtl_db_query` (주) | 외부 RTL 설계 지식 DB 그래프 워크 (`ATLAS_RTL_DB_QUERY`/`ATLAS_EXTERNAL_DB_QUERY` env 계약) |
| `rtl_db_wiki` (주) | 외부 RTL DB wiki 코퍼스 토픽 워크 (`ATLAS_RTL_DB_WIKI`, core `wiki_query` 위임) |
| `ontology_query` | ontology/platform.db에 SELECT-only (단위 성숙도/spine/이력) |
| `wiki_search` | doc/wiki + 모든 `<ip>/wiki` 본문 검색 (file:line) |

Claude Code에서도 `claude mcp add rtl-db -- python3 scripts/atlas_mcp_server.py`로 동일 사용.
온톨로지: OBL_ATLAS_MCP_SERVER.

## 자가포함 배포 (v3, 2026-06-10 Brian 지시: "참조만 하면 안 돼")

`.cursor`는 **단독 전달 가능**: workflow 본체(517 파일 — 스크립트/manifest/템플릿)와
엔진(`src/workflow_stage_engine.py` 등 3종), 헬퍼(`ip_wiki`, MCP 서버)가
`.cursor/{workflow,src,scripts}/`에 vendoring돼 있다.

- 동기화: `python3 scripts/sync_cursor_pack.py sync` (정본→팩, 해시 manifest)
- drift ratchet: `... check` + `test_vendor_manifest_in_sync` — 정본이 바뀌면 빨간불
- 러너/서버는 풀 repo에선 정본을, 전달본에선 vendored 사본을 자동 선택
- 증명: `test_pack_is_self_contained` — 팩만 복사한 가짜 프로젝트에서
  엔진 import·게이트 실행·ip_wiki 라운드트립·MCP handshake 전부 통과

## Agents 전체 커버리지 + Orchestrator

활성 workflow family 전부에 owner agent 존재 (27 agents; system_prompt.md 기반,
`test_workflow_families_have_agents` ratchet). `orchestrator`는 명시적 컨덕터:
스테이지→owner 라우팅 표, gate-then-advance, 위임 계약(IP/스테이지/직전 verdict/기대
증거), ip_wiki 히스토리 의무, "done = signoff+verifier 재검" — 본인은 저작 금지.

## 이름 규칙

`.cursor` 밑 식별자(agents/skills/rules 파일·폴더명)에는 `atlas-` 접두어를 쓰지
않는다 (Brian 지시 2026-06-10; `test_no_atlas_prefixed_names_under_cursor` ratchet).
subagent 증거 의무 대상은 접두어가 아니라 **agents 디렉토리 동적 조회**(readonly 제외)로 판정.

## 무결성 게이트

`tests/test_cursor_pack.py`가 ratchet: hooks.json이 가리키는 스크립트 실재+실행성,
agents/skills frontmatter 유효성(skill name=folder명), SKILL이 참조하는 repo 스크립트
실재를 기계 검증한다. 온톨로지 등재: `REQ_PLAT_CURSOR_PARITY_001` (platform.cursor-pack).
