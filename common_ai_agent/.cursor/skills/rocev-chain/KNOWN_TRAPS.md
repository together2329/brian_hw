# KNOWN TRAPS — 10-IP 실전 캠페인(2026-06-10, *_cx1 10종)에서 수확한 함정 전부

새 IP를 이 팩으로 만들 때 아래를 먼저 읽어라. 전부 실제로 부딪힌 것들이다.

## 올바른 스테이지 명령 (SKILL.md 보정)

- `stage_gate.py`는 **tb|sim|lint만** 받는다. req 게이트는
  `check_contract_bundle.py` / `check_locked_truth_bundle.py` 직접 호출. rtl 게이트는
  iverilog/verilator + `dut_lint_report.py` 직접.
- **sim 실행의 유일한 안정 경로는 `python3 <ip>/tb/cocotb/test_runner.py` 직접 실행.**
  `stage_gate sim`의 `sim_run` 서브게이트는 IP명을 iverilog 소스로 넘기는 버그로 전 IP FAIL
  (검증은 `sim_evidence`+`evidence_contract_closure`로). LLM 차단 환경에서 rtl_to_signoff
  의 sim 스테이지 대신 이 폴백을 써라.
- 모든 체커는 **repo 루트에서 실행** (IP 디렉토리에서 돌리면 경로 이중첩 오류).
- 신규 IP는 `ATLAS_COV_BLOCK_IS_FAIL=0` 없이는 coverage summary가 rc=3로 sim을 막는다.
- `ip_wiki.py log <ip_dir> --stage S --title T --body B` (플래그 필수).

## req 번들 (최대 마찰 구간 — scaffold 생성기 없음)

- `emit_requirements_from_ssot.py`는 .md만 생성. **JSON 번들 6~8종은 수동 저작**:
  기존 `*_cx1/req/`를 템플릿으로 복사-수정하는 게 정석.
- `promote_requirement_review.py`: `--source <doc>` (≥1000자 리뷰 문서 필요) + `--force`.
- `lock_requirement_set.py`: `--approved-by <실명>` (placeholder 거부) + `--from-candidate`.
- `approval_manifest.json`: requirements는 `{requirement_id, required, status}` 객체 배열;
  `files[]` 경로는 `req/<file>` 형식; `bundle_sha256` = 파일 sha256들의 정렬 연결 해시
  (req/*.json 수정 시마다 재계산).
- behavioral contract `stage_contracts[]`에는 cycle/latency/clock 키워드가 있어야 통과.
- evidence_plan은 requirement뿐 아니라 **모든 SC_*/BC_* contract id를 명시 커버**해야 함.

## SSOT 저작 함정

- 표현식 DSL: `min()` 불가 (`a if a < b else b` 사용); 허용 함수는 reduction_or/parity 계열.
- `sample_condition`이 `input_map`에 있는 토큰이면 `sample_inputs: []`로 비어버림 —
  enable 신호는 input_map에서 빼라.
- `memory.instances`가 비어있지 않으면 관측 불가능한 `EQ_MEMORY_*_retention` goal 생성.
- FSM 없는 RTL이면 `fsm.control.states: []`.
- io_list 포트마다 `timing: {kind, clock_domain}` 필수 (structural projection 블로커).
- transactions/cycle_model에 `behavioral_contract_refs` 교차링크 필수.
- **FL은 pre-state, RTL은 post-state**: registered 출력 flag는 output_rules에서
  `count+1`/`count-1`식으로 post-update 의미로 써야 일치.
- SSOT 수정 후 `ssot-fl-model` 재생성 필수 (옛 스냅샷이 functional_model.py에 박힘).

## TB/sim 생성기의 알려진 버그 (워크어라운드 포함)

- `_idle_input_value`가 미지 입력에 idx+1을 주입 → synchronizer류는 워밍업 중 오염
  (edge_det 실패 원인). idle_low_ports/reset값 명시로 완화.
- `FM_RESET`/`name=reset` 트랜잭션은 output_rules를 우회 → reset goal은 항상 미비교.
- `latency_cycles`가 manifest에 1로 하드코딩 (cycle_model.latency 무시).
- registered output의 per-cycle 비교는 워밍업 1-cycle off-by-one을 만든다 (debounce/parity
  부분 실패 원인) — scenario 기반 검증 패턴 필요.
- TB 전제: `verify/equivalence_goals.json`(emit_equivalence_goals) + `rtl/rtl_contract.json`
  (생성기 없음 — SSOT rtl_contract 섹션에서 수동 변환) 선행 필수.
- pyuvm 게이트는 8계층 클래스 전부 요구 — 기존 *_cx1 TB를 템플릿으로.
- RTL은 `parameter [W-1:0]` 스타일 + `timescale 1ns/1ps` 필수; `always_ff/logic/typedef/
  enum/int/for`는 정책 금지 (SSOT 에미터 출력도 고쳐 써야 함).
- JSON엔 hex 리터럴 불가 (equivalence_goals 자극값은 10진수로).
- scoreboard 이벤트에 `fl_expected.model_api="FunctionalModel.apply"` 문자열 필수,
  truth_coverage는 레지스터명/시나리오ID/에러소스ID가 coverage_refs에 있어야 커버 인정.
- `rtl_authoring_provenance.json`: `surface`는 허용 집합(headless_common_engine 등),
  `todo_plan_sha256`는 `_stable_json_sha256` 사용.
