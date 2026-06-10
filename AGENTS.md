# brian_hw 개발 규약 (모든 코딩 에이전트 공통 — Claude / Codex / Cursor)

## Platform Ontology-first 개발 루프 (필수)

common_ai_agent의 기능 구현·수정·버그픽스는 **항상 온톨로지 레이어를 거친다**
(Requirement → Obligation → Evidence → Validation). 상세 설계:
`common_ai_agent/doc/wiki/platform-ontology.md`

1. **선언** — 코드를 만지기 전에 `common_ai_agent/ontology/platform_requirements.yaml`에
   약속을 적는다: 기존 requirement에 obligation 추가(또는 새 requirement + 실재하는
   wiki `design_anchor`), `status: open`, `owned_by`는 DevUnit id. 새 모듈을 만들면
   `common_ai_agent/ontology/platform_ontology.yaml`의 단위 `owns`에 등록
   (orphan ratchet이 강제).
2. **구현** — owned 경계 안에서 작성. 경계가 안 맞으면 단위 정의부터 고친다.
3. **증거** — content test를 쓰고, pytest 노드 ID를 `evidence`로 선언,
   `observed_at` = 그 코드가 실린 커밋 sha.
4. **닫기** — `status: closed` 전환 후 (common_ai_agent에서)
   `python3 scripts/platform_ontology.py check` PASS 확인(유령 선언·신선도 기계검증).
   stale 경고가 나오면 테스트 재실행 후 `observed_at` 갱신.
   **check PASS 전에는 merge하지 않는다.**

규칙:
- 작업 중 발견한 결함은 채팅 메모가 아니라 `status: refuted` obligation으로 즉시
  등재한다 (`refuted_by` 필수). 결함 수정의 완료 정의 = closed로 뒤집는 evidence.
- 작업 큐 확인: `python3 scripts/platform_ontology.py backlog` (refuted > stale > open).
- 현황 확인: `... report` (단위 성숙도 + requirement 추적표).
- 래칫: `common_ai_agent/tests/test_platform_ontology.py`가 미등록 모듈·유령 선언을
  차단한다.
