# sim_debug Coverage Plan

분석 차원: **정적 코드 분석 (static)** vs **VCD 사후처리 (dynamic from waveform)** vs
**Instrumented runtime (dynamic from counters)**.

세 채널은 같은 단어 ("coverage") 를 쓰지만 서로 다른 데이터를 본다. 이 문서는
ATLAS sim_debug 가 어느 layer 를 어떻게 활용할지 정리한 plan.

---

## 1. 기본 차이 — 어디를 들여다보나

| 채널 | 보는 것 | 데이터 소스 | 시뮬 실행 필요 |
|---|---|---|---|
| **Static (code)** | RTL 텍스트 / AST 자체 | `*.sv`, pyslang elab tree | ❌ 안 함 |
| **VCD post-process** | 실행된 신호의 시간순 값 | `*.vcd` (이미 만들어진 것) | ✅ 한 번 (재실행 안 해도 됨) |
| **Instrumented runtime** | 시뮬레이터 내부 카운터 | `coverage.dat` (verilator) / `.ucdb` (Questa) / `.vdb` (VCS) | ✅ 매번 (instrument 후 재실행) |

→ Static 은 "**무엇이** 존재하는가",
   VCD 는 "**어떤 신호가** 어떻게 변했는가",
   Instrumented 는 "**어떤 코드가** 몇 번 실행됐는가".

---

## 2. 메트릭 별 능력 매트릭스

| 메트릭 | Static (code) | VCD only | Instrumented | 비고 |
|---|---|---|---|---|
| **Coverage universe** (전체 line/branch/state list) | ✅ | ❌ | ✅ | static 의 본업 |
| **Reachability / dead-code 검출** | ✅ | ❌ | △ | static analysis 의 강점 |
| **Cyclomatic complexity, branch count** | ✅ | ❌ | △ | static 으로 즉시 |
| **Toggle (signal 0↔1)** | ❌ | ✅ | ✅ | VCD 의 본업 |
| **State (FSM) 방문값** | ❌ | ✅ (state 가 dump 됐을 때) | ✅ | VCD 면 충분 |
| **Transition (FSM 에지)** | ❌ | ✅ | ✅ | VCD 시간순 분석 |
| **Line coverage** | ❌ | ❌ | ✅ | 라인이 실행됐는지는 카운터만 안다 |
| **Branch (if/else) coverage** | ❌ | △ (LHS 신호 변화로 추정 — 부정확) | ✅ | instrument 가 정답 |
| **Expression / condition coverage** | ❌ | ❌ | ✅ | sub-condition 카운터 필요 |
| **Functional coverage (covergroup, cover property)** | △ (정의만 추출) | △ (직접 정의된 cover spec 평가 가능) | ✅ | instrument 가 정확 |
| **Cross coverage** | ❌ | ✅ | ✅ | VCD 두 신호 동시 평가 |
| **Internal hidden net** | ✅ | ❌ ($dumpvars 안 했으면 invisible) | ✅ | VCD 한계 |

---

## 3. 장단점 정리

### Static (code-only)
**장점**
- 시뮬레이터 안 돌려도 됨 — instant
- 어떤 시뮬레이터든 OK (vendor 중립)
- "정의됐지만 한 번도 cover 못 됨" 같은 누락 검출 (cross-check)
- pyslang 으로 100 % SV 구문 분석

**단점**
- 실제 hit count 는 모름 — 무엇이 부족한지 우선순위 못 정함
- "도달 가능" 인지 보수적 추정 (parameter-dependent dead code 일부만)
- 가장 의미있는 line/branch coverage 단독으로 못 함

### VCD post-process
**장점**
- 추가 셋업 0 — 이미 가진 VCD 만 있으면 끝
- 어떤 시뮬레이터든 VCD 만들면 OK
- 재컴파일 / 재시뮬 불필요
- toggle / state / transition 충분히 정확
- user-defined functional cover 도 평가 가능 (eg. "`req && !ack` 한 번이라도?")

**단점**
- **line / branch coverage 불가** — 가장 중요한 코드 커버리지 손실
- VCD 에 dump 안 된 internal net 은 invisible
- VCD 파일 크기 — 큰 design 은 GB 단위
- 토글 100 % 라도 의미있는 값 cover 한 건 아님 (단순 0↔1 변화만)
- 신호값 → 분기 추정은 신뢰성 낮음

### Instrumented runtime
**장점**
- 모든 메트릭 정확 — line / branch / expr / functional 다 됨
- 카운터 기반이라 작은 오버헤드
- 표준 출력 (LCOV / UCIS) → genhtml / vendor 도구 호환

**단점**
- 컴파일 옵션 + 재컴파일 필요
- 시뮬 다시 돌려야 함 (느릴 수 있음 — instrument 된 binary 는 미세하게 느림)
- 시뮬레이터 별 설정 / 산출물 다름 (verilator vs Cadence vs Synopsys)
- VCD 와 별도 채널 — 파일 두 개 관리

---

## 4. 핵심 통찰 — 세 채널은 보완 관계

세 채널이 보는 데이터가 **다르다**:

```
Static  → universe (분모)              "전체 240 라인 중"
VCD     → 신호 차원 hit set           "60 % 신호가 토글됨"
Instr.  → 코드 차원 hit set            "78 % 라인이 실행됨"
```

ATLAS sim_debug 의 view 는 셋을 한 화면에서 비교할 수 있어야 함:

```
gpio_pad_regs.sv                                        Static  VCD  Instr
  ├ line 74  always_ff @(posedge pclk ...)                ●     ━     1320×
  ├ line 76  dir_reg <= '0;  (reset branch)               ●     ?     1×
  ├ line 89  dir_reg <= pwdata;  (write branch)           ●     ?     1320×
  └ line 90  out_reg <= pwdata;  (case 1)                 ●     ?     0×  ← MISS
                                                                       ↑
                                                          이건 VCD 만
                                                          으론 모름
```

---

## 5. ATLAS sim_debug Coverage 통합 plan

### Phase A — Static-only baseline (즉시, 의존성 0)
- pyslang 으로 RTL elab → 모든 line/branch/state/cover bin universe 추출
- 화면: "이 IP 에는 240 라인, 12 분기, 4 FSM state 가 있다" — 분모만 표시
- API: `GET /api/coverage/universe?ip=<ip>` → static analysis
- 시간: ~1 시간 구현 (pyslang 도 이미 통합)
- 가치: coverage 의 분모 정의, "이게 전부야" 보장

### Phase B — Quick channel (VCD post-process)
- 이미 가진 VCD 파싱해서 toggle / state / transition 메트릭
- ATLAS 의 frontend `vcd-parser.js` 가 이미 신호 list 와 값 시퀀스 파싱 중 → 그 위에 카운터만 추가
- API: `GET /api/coverage/vcd?path=<vcd>&ip=<ip>` → 토글 / state coverage
- UI: COVERAGE 패널 "Quick" 탭 — 신호별 toggle %, FSM state visit list, transition 매트릭스
- 시간: ~3 시간 구현
- 가치: 추가 셋업 0, 즉시 신호 수준 coverage

### Phase C — Deep channel (Verilator instrumented, opt-in)
- `gpio_pad/cocotb/Makefile` 에 `EXTRA_ARGS += --coverage` patch 자동화
- 모든 testcase 돌려서 `coverage.dat` 모으고 `verilator_coverage --write-info merged.info` 로 LCOV
- Backend 에 LCOV 파서 + ATLAS internal JSON normalize
- UI: COVERAGE 패널 "Deep" 탭 — line / branch / expr / functional %, missed lines list
- SourceViewer: line gutter 에 hit/miss 바 (녹/빨/회) 오버레이
- API: `POST /api/coverage/build?ip=<ip>` → Makefile patch + 빌드 + run + LCOV 파싱
- 시간: ~5 시간 구현
- 가치: line / branch 수준 coverage — 진짜 검증 closure 메트릭

### Phase D — Vendor adapters (확장)
- Cadence Xcelium IMC / Synopsys URG / Mentor Questa / cocotb-coverage 어댑터
- `workflow/sim_debug/coverage_adapters/{verilator,cadence,vcs,questa,cocotb}.py`
- 각 adapter 가 native db → ATLAS internal JSON 변환
- UCIS 통한 vendor 간 merge 도 지원
- 시간: 어댑터 당 ~2 시간
- 가치: 어떤 EDA 환경이든 ATLAS 한 화면에서 통합 coverage

### Phase E — FSM 시각화 (functional coverage 의 시각적 표현)
- pyslang 이 covergroup / FSM state enum 추출 → 다이어그램
- VCD 또는 instrument hit count 로 노드 별 색상 (방문 = 녹, 미방문 = 빨)
- transition 화살표는 본 적 있으면 굵게, 못 본 transition 은 점선
- 시간: ~3 시간
- 가치: 큰 FSM 의 cover hole 한눈에 식별

---

## 6. UI 디자인 (COVERAGE 패널)

```
┌────────────────────────────────────────────────────────────────┐
│ COVERAGE                                                        │
│   ip: gpio_pad   [● Quick (VCD)]  [○ Deep (instr.)]  refresh   │
├────────────────────────────────────────────────────────────────┤
│ Universe (static, pyslang)                                     │
│   240 lines · 12 branches · 1 FSM (4 states) · 8 cover bins    │
├────────────────────────────────────────────────────────────────┤
│ Quick (VCD post-process — 0.3s)                                │
│   Toggle      72.5%  ████████░░  612 / 1024 transitions        │
│     · pclk          100%  137                                  │
│     · presetn        50%    1   (deassert only)                │
│     · gpio_in[31:0] 31%   10/32 bits  ← stim 부족              │
│   States       75%   ███████░░░  3 / 4 (IDLE/READ/WRITE seen,  │
│                                          ERROR not visited)    │
│   Transitions  50%   █████░░░░░  6 / 12                         │
├────────────────────────────────────────────────────────────────┤
│ Deep (verilator instrumented — last run 2026-05-01 17:50)      │
│   Lines       77.9%  ████████░░  187 / 240                     │
│   Branches    73.2%  ███████░░░  41  / 56                      │
│   Expressions 65.0%  ██████░░░░  39  / 60                      │
│   Functional  77.8%  ████████░░  14  / 18                      │
│                                                                │
│   Files (sorted by lowest cov):                                │
│    · gpio_pad_core.sv     63.2%   ← click to open + scroll to  │
│    · gpio_pad_regs.sv     85.4%      first missed line         │
│    · gpio_pad_wrapper.sv 100%                                  │
│                                                                │
│   [⚙ Rebuild deep cov]   [⌥ Per-test merge]   [⤓ LCOV export]  │
└────────────────────────────────────────────────────────────────┘
```

SourceViewer 의 gutter 오버레이 — Phase C 와 함께:
```
   ┌──┬───────────────────────────────────────────────────────
   │74│  always_ff @(posedge pclk or negedge presetn) begin
   │  │  ┌─ 1320 hits (warm green)
   │76│  │   if (!presetn) begin
   │  │  │  ┌─ 1 hit (cool green) — reset taken once
   │76│  │  │     dir_reg <= '0;
   │77│  │  │     out_reg <= '0;
   │  │  │  └─
   │78│  │   end else if (apb_write_valid) begin
   │  │  │  ┌─ 832 hits
   │89│  │  │     case (paddr[5:2])
   │  │  │  │  ┌─ 412 hits
   │90│  │  │  │     4'h0: dir_reg <= pwdata;
   │  │  │  │  ─ 0 hits ← MISS — 빨간 strip
   │91│  │  │  │     4'h1: out_reg <= pwdata;
```

---

## 7. 결론

세 채널을 같은 화면에서 비교하면 cover hole 이 분명히 보임:

- **Static** 이 "분모 240 라인" 이라고 알려주고
- **Quick (VCD)** 가 "신호 토글 60 %" 라고 빠르게 알려주고
- **Deep (instr.)** 가 "line 78 % / branch 73 % — 정확히 라인 90 / 95 / 132 가 안 됨" 이라고 알려줌

→ 사용자는 디버그 단계 따라 어느 layer 까지 깔지 선택. 평소엔 Static + Quick 으로 충분, 검증 closure 시점에 Deep 까지.

**즉시 시작 권장**: Phase A + B (static 분석 + VCD post-process) — 추가 셋업 0, 즉시 가치. Phase C 는 사용자가 "deep 메트릭 필요" 라고 명시할 때 button 하나 눌러서 실행되도록.
