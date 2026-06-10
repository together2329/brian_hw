---
title: Platform Ontology — 개발 단위/테스트/완성도 DB
category: architecture
tags: [ontology, dev-units, maturity, ratchet, meta]
status: v1 live (2026-06-10) — 19 units seeded, orphan ratchet @124, first snapshot in DB
---

# Platform Ontology

**목적**: Brian과 실제 구현 사이의 공용 언어층. common_ai_agent **플랫폼 자체**
(엔진·런타임·DB·API·UI)의 개발 단위(DevUnit)를 선언하고, 각 단위의 테스트와
완성도를 **기계 측정**으로 추정한다. IP 검증용 VCM([[verification-contract-model]])과는
별개 장부 — workflow 게이트들의 명부는 GateSelfTest 레지스트리가 계속 담당한다.

## 구성

| 파일 | 역할 |
|---|---|
| `ontology/platform_ontology.yaml` | **선언부 (source of truth)** — 단위/소유/증거, git 추적 |
| `scripts/platform_ontology.py` | 스캐너 CLI: `scan` / `report` / `check` |
| `ontology/platform.db` | 측정 스냅샷 SQLite (derived, git-ignored) |
| `tests/test_platform_ontology.py` | 래칫 + 스캐너 kill-proof (10 tests) |

## 모델

- **DevUnit** = 책임 하나 (파일 경계 아님). `owns`(글롭/literal), `kind`, `summary`,
  `known_gaps`, 선언 증거 3종(`content_tests`/`e2e_evidence`/`ratchet_tests`).
- **성숙도 사다리 (누적, 기계 판정)**:
  `L0 존재 < L1 단위테스트(import-스캔 자동발견) < L2 내용검증 < L3 E2E < L4 래칫`
- **silent-PASS 금지**: 선언 경로가 디스크에 없으면 레벨 불인정 + `check` 실패.
  자기신고만으로 레벨이 오르는 일은 없다 (kill-proof 테스트로 증명).
- **orphan ratchet**: scope(core/src/lib `*.py`) 내 미등록 파일 수가
  `orphan_baseline`(현재 124)을 초과하면 `check` 실패 → 새 모듈은 등록을 강제당한다.
  baseline은 줄어들 때마다 따라 내린다.

## 첫 측정 (2026-06-10, snapshot #2)

scope 156 files / orphans 124 / overlaps 0. 19 units:

```
L3 E2E   ██ 2   (agent.compression, engine.stage)
L2 내용   ████ 4 (agent.tools, platform.ontology, runtime.authz, task.todo-tracker)
L1 단위   ███████████ 11
L0 존재   ██ 2   (agent.memory, ui.workspace)
L4 래칫   0
```

읽는 법: api.jobs(11.5k줄, hot-path 1위)가 L1에 머무는 것, agent.memory가 테스트 0인 것 —
이런 게 "다음에 뭘 할지"의 좌표다. known_gaps 필드(run_command Windows, llm 이미지
flatten, /compact 모델 미스코프 등)는 단위에 붙은 백로그다.

## 사용법

```bash
python3 scripts/platform_ontology.py report   # 표 + 히스토그램 + orphan top
python3 scripts/platform_ontology.py scan     # DB에 스냅샷 적재 (이력 누적)
python3 scripts/platform_ontology.py check    # 게이트 (rc 0/1) — CI/훅용
```

## 남은 일

- orphan 124개 그룹핑 (top: runtime_rollup, graph_lite, session_manager,
  session_flow_usage, tools_verilog, atlas_admin_usage, scm*, atlas_auth …) →
  단위 추가하며 baseline 인하
- L1→L2 승급 캠페인 (content_tests 선언은 사람이, 실재 검증은 스캐너가)
- `check`를 훅/CI에 배선할지 결정 (현재는 pytest 래칫이 동일 역할 수행)
