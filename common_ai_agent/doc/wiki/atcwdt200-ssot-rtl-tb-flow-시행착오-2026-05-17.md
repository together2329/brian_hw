---
title: "ATCWDT200 SSOT RTL TB Flow 시행착오 2026-05-17"
tags: ["atcwdt200", "ssot", "rtl-gen", "tb-gen", "sim", "lint", "debugging"]
created: 2026-05-17T07:19:09.155Z
updated: 2026-05-17T07:19:09.155Z
sources: []
links: ["atcwdt200-flow-debugging-lessons.md"]
category: session-log
confidence: medium
schemaVersion: 1
---

# ATCWDT200 SSOT RTL TB Flow 시행착오 2026-05-17

# ATCWDT200 SSOT RTL TB Flow 시행착오 2026-05-17

## Context
- 목표: `/Users/brian/Desktop/andes/atcwdt200` reference evidence를 요구사항으로 삼아, RTL engineer user 관점에서 SSOT Q&A -> SSOT -> FL/CL/equiv -> RTL -> TB -> sim -> lint 흐름을 끝까지 실행.
- IP: `atcwdt200`, APB-like watchdog timer.
- Canonical flow reference: `doc/wiki/full-flow-pipeline.md`.

## What Worked
- SSOT Q&A 9개를 approved 처리하고 `atcwdt200/yaml/atcwdt200.ssot.yaml` 생성.
- `check_ssot_disk.sh` PASS: 36 sections, 0 TBDs.
- FL/CL/equiv deterministic emit 성공: FunctionalModel, CycleModel, equivalence goals 41 required / 41 unblocked.
- RTL 직접 작성 후 `rtl_compile_report.py`, `check_rtl_disk.sh`, `dut_lint_report.py` 모두 PASS.
- `derive_rtl_todos.py --audit-rtl` 최종 PASS: 204 tasks, blockers 0, orphans 0, gate pass.
- `ssot_to_rtl.py --mode engineering` preflight PASS.
- TB-gen generic cocotb 생성 성공: `atcwdt200/tb/cocotb/test_atcwdt200.py`, `test_runner.py`, manifest 등 8개 Python 파일.
- `check_tb_disk.sh atcwdt200` PASS.
- cocotb/icarus runner 실행 완료, results.xml / VCD / scoreboard_events 생성.

## 시행착오 / Lessons
- `derive_rtl_todos.py --audit-rtl`는 SystemVerilog comments를 제거하고 정적 evidence를 검사한다. 주석에 SSOT trace term을 넣어도 static evidence는 닫히지 않는다.
- audit evidence term은 실제 RTL identifier/declaration/expression 경로에 있어야 한다. 단, evidence-only alias wire는 원칙상 피해야 하고, 가능한 한 실제 CSR mask, read mux, output equation, FSM/counter path에 자연스럽게 연결해야 한다.
- Verilator `UNUSEDSIGNAL` 때문에 trace용 mask의 일부 bit만 쓰면 lint가 fail한다. 예: `CR_FIELDS_x7ff[7:4]`도 no-op expression에 소비해 warning 0을 유지해야 했다.
- macOS Python bytecode cache가 `/Users/brian/Library/Caches/com.apple.python/...`에 쓰이면서 sandbox permission error가 났다. `PYTHONPYCACHEPREFIX=/private/tmp/pycache`를 붙이면 py_compile이 통과한다.
- TB generator는 `rtl/rtl_contract.json`을 요구한다. LLM-authored RTL을 직접 작성한 경우에도 SSOT에서 파생한 `generic_ssot_rule_rtl_contract`를 기록해야 cocotb manifest 생성이 가능하다.
- `emit_goal_scoreboard_cocotb.py`는 legacy APB assumptions가 아니라 `rtl_contract`, `equivalence_goals`, `functional_model.py`, filelist를 읽어 TB를 만든다. contract가 없으면 `[SSOT QUESTION]`으로 block한다.
- cocotb runner 자체 PASS와 FL-vs-RTL scoreboard PASS는 별개다. 이번 실행은 runner는 `TESTS=1 PASS=1 FAIL=0`였지만 scoreboard가 11개 mismatch를 `[SIM ESCALATE]`로 남겼다. 최종 signoff로 간주하면 안 된다.

## Current Blocker
- `atcwdt200/sim/sim_report.txt`에 `[SIM ESCALATE] scoreboard_failed=11`이 남아 있음.
- 주요 mismatch:
  - `EQ_TRANSACTION_APB_READ`: `prdata expected=0 observed=50339842`.
  - `EQ_SCENARIO_APB_REGISTER_ACCESS`: 동일한 VER read 관측 mismatch.
  - unlock/restart/timeout/state transition 관련 goal들은 `no comparable RTL observable`.
- 다음 action은 scoreboard row와 generated stimulus를 읽어서 mismatch owner를 분리하는 것:
  - SSOT/FL expected가 너무 generic한지,
  - TB stimulus가 APB address phase/read phase를 잘못 샘플링하는지,
  - RTL read mux가 reference-compatible하지만 FL rule이 `expr: 0`이라 mismatch인지,
  - 내부 state observability가 필요한 goal을 외부 pin만으로 비교하려는 TB contract gap인지 판단.

## Commands With Evidence
- `python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atcwdt200 --root ... --audit-rtl` -> gate pass.
- `bash workflow/rtl-gen/scripts/check_rtl_disk.sh atcwdt200` -> PASS.
- `python3 workflow/lint/scripts/dut_lint_report.py atcwdt200 --top atcwdt200` -> errors=0 warnings=0.
- `python3 workflow/tb-gen/runtime/equivalence_scoreboard.py atcwdt200 --root ... --self-check` -> passed=true, checked=41.
- `bash workflow/tb-gen/scripts/check_tb_disk.sh atcwdt200` -> PASS.
- `SIM=icarus COCOTB_TESTCASE=fl_rtl_equivalence_goals PYTHONPYCACHEPREFIX=/private/tmp/pycache python3 atcwdt200/tb/cocotb/test_runner.py` -> cocotb PASS, scoreboard escalate.

## Cross Links
- See [[atcwdt200-flow-debugging-lessons]] for reusable debugging patterns from this run.

