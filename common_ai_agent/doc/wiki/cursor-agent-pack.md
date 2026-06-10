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

`skills/rocev-chain/SKILL.md` + `agents/atlas-rocev-chain.md`가
Requirement→Obligation→Contract→Evidence→Validation을 스테이지별로 닫는다:

| 스테이지 | Obligation 생성/계약 | Evidence | Validation |
|---|---|---|---|
| req | `emit_requirements_from_ssot` → `promote_requirement_review` → `lock_requirement_set` → `stage_contract_todos`(VCM projector) | `req/*.json` locked bundle | `check_locked_truth_bundle` + `stage_gate` |
| rtl | rtl todo ledger (`rtl/rtl_todo_plan.json`) | `rtl/*.sv` + `rtl_compile.json` | lint/compile gate + `--audit-rtl` |
| tb | scoreboard contract (equiv goals) | `tb/cocotb/*` + scoreboard events | tb gate + ledger 검증 |
| sim | per-obligation sim todos | `sim/results.xml`, `sim_report.txt` | `check_sim_disk` + `check_truth_coverage` + goal-audit |

실행 래퍼는 기존 `skills/rtl-to-signoff/scripts/rtl_to_signoff.py` (stage id:
`ssot-rtl`, `ssot-tb-cocotb`, `sim`, `goal-audit` 등)를 그대로 쓴다 — 구현 복제 금지.

## 무결성 게이트

`tests/test_cursor_pack.py`가 ratchet: hooks.json이 가리키는 스크립트 실재+실행성,
agents/skills frontmatter 유효성(skill name=folder명), SKILL이 참조하는 repo 스크립트
실재를 기계 검증한다. 온톨로지 등재: `REQ_PLAT_CURSOR_PARITY_001` (platform.cursor-pack).
