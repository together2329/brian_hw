// guide.tsx — "How to use ATLAS" reference screen.
//
// Registers window.AtlasGuide, mounted by app.jsx when screen === 'guide'.
//
// Framing (intentional): ATLAS is first and foremost an **SSOT · RTL
// Generation Agent**. Authoring the SSOT design-contract and generating RTL
// from it is the product; every other workflow (TB / SIM / LINT / COVERAGE /
// SYN / STA / PnR / STA-post) exists only to *assure the quality* of that
// generated RTL. The content below is distilled from the project wiki:
//   doc/wiki/default-agent-ip-flow.md         (default conversational mode)
//   doc/wiki/workflow-ownership-and-boundaries.md (per-workflow ownership)
//   workflow/wiki/ip_knowledge/*.md           (per-stage purpose / produces)
//
// Authored HTML (trusted, static) is rendered through DOMPurify; the scoped
// CSS lives in a sibling <style> element (class attributes survive sanitize).
import type { ReactElement } from 'react';

// DOMPurify is a cross-file global (vendored lib, owned elsewhere); it is not
// declared in the ambient atlas-window.d.ts, so we read it through a narrow
// locally-typed view of window. This is a type-only cast — runtime behavior is
// identical to the legacy `window.DOMPurify` access.
interface DOMPurifyLike {
  sanitize: (dirty: string, config?: { ADD_ATTR?: string[] }) => string;
}

const ATLAS_GUIDE_CSS = `
.atlas-guide { height: 100%; overflow-y: auto; padding: 28px 32px 64px; color: var(--fg); line-height: 1.6; }
.atlas-guide .ag-wrap { max-width: 920px; margin: 0 auto; }
.atlas-guide .ag-hero { border: 1px solid color-mix(in oklch, var(--accent) 45%, var(--line)); background: color-mix(in oklch, var(--accent) 12%, transparent); border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; }
.atlas-guide .ag-hero h1 { margin: 0 0 8px; font-size: 22px; letter-spacing: .2px; }
.atlas-guide .ag-hero .ag-sub { color: var(--fg-mute); font-size: 13px; }
.atlas-guide .ag-hero .ag-rule { margin-top: 12px; font-size: 13px; }
.atlas-guide .ag-hero .ag-rule b { color: var(--accent); }
.atlas-guide h2 { font-size: 16px; margin: 30px 0 10px; padding-bottom: 6px; border-bottom: 1px solid var(--line); }
.atlas-guide h2 .ag-star { color: var(--accent); }
.atlas-guide p { margin: 8px 0; }
.atlas-guide code { background: color-mix(in oklch, var(--fg) 10%, transparent); padding: 1px 5px; border-radius: 4px; font-size: 12px; }
.atlas-guide .ag-muted { color: var(--fg-mute); font-size: 12.5px; }
.atlas-guide table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }
.atlas-guide th, .atlas-guide td { text-align: left; padding: 8px 10px; border: 1px solid var(--line); vertical-align: top; }
.atlas-guide th { background: color-mix(in oklch, var(--fg) 6%, transparent); font-weight: 600; }
.atlas-guide .ag-core { border: 1px solid color-mix(in oklch, var(--accent) 50%, var(--line)); border-radius: 10px; overflow: hidden; }
.atlas-guide .ag-core th { background: color-mix(in oklch, var(--accent) 18%, transparent); }
.atlas-guide .ag-core td:first-child { font-weight: 700; color: var(--accent); white-space: nowrap; }
.atlas-guide .ag-core td:first-child .ag-tag { display: inline-block; margin-left: 6px; font-size: 9px; font-weight: 700; color: var(--bg); background: var(--accent); padding: 1px 5px; border-radius: 999px; vertical-align: middle; }
.atlas-guide .ag-aux td:first-child { font-weight: 600; white-space: nowrap; }
.atlas-guide .ag-aux { font-size: 12.5px; }
.atlas-guide .ag-cmds code { margin-right: 4px; }
.atlas-guide .ag-flow { font-size: 12.5px; }
.atlas-guide .ag-flow td:first-child { text-align: center; font-weight: 700; color: var(--accent); background: color-mix(in oklch, var(--accent) 10%, transparent); }
.atlas-guide .ag-flow .ag-cmds { margin-top: 4px; }
.atlas-guide .ag-gate { display: block; margin-top: 4px; color: var(--fg-mute); font-size: 11.5px; }
.atlas-guide .ag-tag2 { display: inline-block; margin-left: 4px; font-size: 9px; font-weight: 700; color: var(--bg); background: var(--accent); padding: 1px 5px; border-radius: 999px; vertical-align: middle; }
.atlas-guide .ag-foot { margin-top: 28px; padding-top: 12px; border-top: 1px solid var(--line); color: var(--fg-mute); font-size: 12px; }
`;

const ATLAS_GUIDE_HTML = `
<div class="ag-wrap">

  <div class="ag-hero">
    <h1>ATLAS = SSOT · RTL Generation Agent</h1>
    <div class="ag-sub">SSOT(설계 계약, Single Source of Truth)를 작성하고 그로부터 <b>RTL을 생성</b>하는 것이 이 도구의 본체입니다.</div>
    <div class="ag-rule">▸ <b>핵심</b>: <code>ssot-gen</code> → <code>rtl-gen</code> (SSOT 설계 → RTL 생성)<br/>
    ▸ <b>그 외 모든 워크플로우</b>(TB · SIM · LINT · COVERAGE · SYN · STA · PnR · STA-post)는 전부 <b>생성된 RTL의 품질(정확성·합성성·타이밍·사인오프)을 확보하기 위한 부수 단계</b>입니다.</div>
  </div>

  <h2>default 모드 — 무엇을 할 수 있나</h2>
  <p>특정 스테이지에 묶이지 않은 <b>범용 에이전트 모드</b>입니다. 명령어를 외울 필요 없이 자연어로 SSOT부터 RTL까지 직접 만들고 검증할 수 있어, 가장 편한 시작점입니다.</p>
  <table>
    <tr><th style="width:34%">할 수 있는 것</th><th>방법 / 예시</th></tr>
    <tr><td>자연어로 IP 만들기·고치기</td><td><code>"UART 만들어줘"</code>, <code>"이 테스트 왜 깨져?"</code>, <code>"orchestrator 말고 직접 해줘"</code></td></tr>
    <tr><td>IP 생성 / 문서·RTL 가져오기</td><td class="ag-cmds"><code>/new-ip &lt;name&gt;</code> <code>/import</code></td></tr>
    <tr><td>코드/파일 탐색·질문, 작업 범위 좁히기</td><td>scope 지정 후 대화</td></tr>
    <tr><td>워크플로우로 전환</td><td class="ag-cmds"><code>/wf &lt;workflow&gt;</code> 또는 상단 셀렉터</td></tr>
  </table>
  <p class="ag-muted">에이전트가 읽기→편집→컴파일/sim/lint 실행→증거 확인→수리→사인오프 리포트까지 "증거 기반 페어프로그래밍" 방식으로 진행합니다.</p>

  <h2><span class="ag-star">★</span> 핵심 워크플로우 — SSOT · RTL 생성</h2>
  <p>제품의 본체. SSOT는 downstream 전체가 따르는 <b>계약(전제)</b>이며, RTL은 그 SSOT로부터 생성됩니다.</p>
  <table class="ag-core">
    <tr><th style="width:18%">워크플로우</th><th>무엇을 하나</th><th style="width:30%">산출물</th></tr>
    <tr>
      <td>ssot-gen <span class="ag-tag">CORE</span></td>
      <td>설계 계약(SSOT YAML)을 작성·검증.<div class="ag-cmds" style="margin-top:4px"><code>/new-ip</code> <code>/import</code> <code>/grill-me</code> <code>/to-ssot</code></div></td>
      <td><code>&lt;ip&gt;/yaml/&lt;ip&gt;.ssot.yaml</code></td>
    </tr>
    <tr>
      <td>rtl-gen <span class="ag-tag">CORE</span></td>
      <td>SSOT로부터 <b>RTL을 생성</b>하고 컴파일 검증.</td>
      <td><code>rtl/*.sv</code>, <code>list/&lt;ip&gt;.f</code>, <code>rtl/rtl_compile.json</code></td>
    </tr>
  </table>

  <h2>전체 파이프라인 — 단계별 흐름 (req → signoff)</h2>
  <p class="ag-muted">공통 엔진의 캐노니컬 순서입니다. 각 단계는 <b>명령</b>으로 돌리고, <b>게이트</b>(검증기)가 산출물을 증거로 승인해야 다음으로 넘어갑니다. ATLAS Web UI · Textual · headless가 모두 같은 엔진 경로를 호출합니다.</p>
  <table class="ag-flow">
    <tr><th style="width:4%">#</th><th style="width:23%">단계 / 명령</th><th>하는 일</th><th style="width:30%">산출물 · 게이트</th></tr>
    <tr>
      <td>1</td>
      <td><b>요구사항 · 계약 포착</b><div class="ag-cmds"><code>/draft-req</code> → <code>/finalize-req</code> → <code>/lock-req</code> <code>/import</code></div></td>
      <td>요구사항을 기계검증 가능한 <b>obligation/계약</b>으로 정규화(req → obligation → contract). <code>/draft-req</code>(초안) → <code>/finalize-req</code>(사람 리뷰 준비) → <code>/lock-req</code>(사람 승인 후 잠금)의 라이프사이클. 사람이 의도·미정의동작·프로토콜·waiver·수용기준을 소유.</td>
      <td><code>req/requirements_index.json</code>, <code>obligations.json</code>, <code>structural/behavioral_contracts.json</code>, <code>approval_manifest.json</code><br/><span class="ag-gate">게이트: <code>check_contract_bundle.py</code> → <code>contract_authority_report.json</code> · <code>contract_closure.json</code></span></td>
    </tr>
    <tr>
      <td>2</td>
      <td><b>SSOT 생성 · 승인</b> <span class="ag-tag2">CORE</span><div class="ag-cmds"><code>/new-ip</code> <code>/import</code> <code>/grill-me</code> <code>/to-ssot</code></div></td>
      <td>설계 계약(SSOT YAML) 작성. 잠긴 req가 있으면 req가 authority이고 SSOT는 그 projection(새 의도 발명 금지). 빠진 의미는 템플릿 우회가 아니라 <b>사람 게이트</b>로.</td>
      <td><code>&lt;ip&gt;/yaml/&lt;ip&gt;.ssot.yaml</code><br/><span class="ag-muted">import 시: <code>req/imports/</code>, <code>import_manifest.json</code>, <code>extracted_decisions.json</code></span></td>
    </tr>
    <tr>
      <td>3</td>
      <td><b>기능(FL) 모델</b><div class="ag-cmds"><code>/ssot-fl-model</code></div></td>
      <td>실행 가능한 <b>골든 기능/사이클 모델</b> 생성 → RTL 등가성 기준 확보.</td>
      <td><code>model/functional_model.py</code>, <code>model/decomposition.json</code>, <code>model/fl_model_check.json</code>, <code>cov/fcov_plan.json</code></td>
    </tr>
    <tr>
      <td>4</td>
      <td><b>FL↔RTL 등가 목표</b><div class="ag-cmds"><code>/ssot-equiv-goals</code></div></td>
      <td>무엇을 LLM 루프가 증명하고 무엇이 사람 소유인지 정의.</td>
      <td><code>verify/equivalence_goals.json</code></td>
    </tr>
    <tr>
      <td>5</td>
      <td><b>RTL 생성 · DUT 승인</b> <span class="ag-tag2">CORE</span><div class="ag-cmds"><code>/gen-rtl</code></div></td>
      <td>SSOT를 <b>구속 계약</b>으로 RTL 생성. SSOT-derived TODO가 전부 <code>pass</code>될 때까지 생성·수리. 기존 RTL은 재사용 증거일 뿐.</td>
      <td><code>rtl/*.sv</code>, <code>list/&lt;ip&gt;.f</code>, <code>rtl/rtl_contract.json</code>, <code>rtl/rtl_traceability.json</code>, <code>rtl/rtl_compile.json</code>, <code>lint/dut_lint.json</code><br/><span class="ag-gate">게이트: DUT-only 컴파일/lint 무오류 (sim 로그는 lint 승인 아님)</span></td>
    </tr>
    <tr>
      <td>6</td>
      <td><b>테스트벤치 생성</b><div class="ag-cmds"><code>/gen-tb</code></div></td>
      <td>goal-driven 스코어보드를 가진 cocotb/pyuvm 검증 환경 생성.</td>
      <td><code>tb/cocotb/*</code>, TB manifest · 생성 리포트</td>
    </tr>
    <tr>
      <td>7</td>
      <td><b>시뮬레이션</b><div class="ag-cmds"><code>/sim</code></div></td>
      <td>FL-vs-RTL 동시 실행으로 기능 정확성 확인 + 파형 수집.</td>
      <td><code>sim/sim_report.txt</code>, <code>results.xml</code>, <code>*.vcd</code></td>
    </tr>
    <tr>
      <td>8</td>
      <td><b>Sim 디버그 · 소유자 분류</b><div class="ag-cmds"><code>/sim-debug</code></div></td>
      <td>FL↔RTL 불일치를 비교·분류. <code>llm_loop_allowed:true</code>만 LLM이 수리, 의미 결정은 사람 게이트.</td>
      <td><code>sim/fl_rtl_compare.json</code>, <code>sim/mismatch_classification.json</code></td>
    </tr>
    <tr>
      <td>9</td>
      <td><b>목표 감사 · 사인오프</b><div class="ag-cmds"><code>/goal-audit</code> <code>/ip-signoff</code></div></td>
      <td>SSOT 목표 마감 확인. 사인오프는 SSOT·FL·사이클·RTL·TB·sim·coverage·sim-debug·goal-audit 증거가 모두 있어야 성립.</td>
      <td><code>sim/fl_rtl_goal_audit.json</code> + 사인오프 묶음</td>
    </tr>
  </table>
  <p class="ag-muted">합성·타이밍·물리 품질이 필요하면 <code>syn → sta → pnr → sta-post</code>를 이어서 돌립니다(아래 부수 워크플로우).</p>
  <p class="ag-muted">▸ 사용자 명령 ↔ 엔진 스테이지: <code>/gen-rtl</code> = <code>ssot-rtl</code>, <code>/gen-tb</code> = <code>ssot-tb</code>. req는 <code>/draft-req</code>(초안) → <code>/finalize-req</code>(리뷰 준비) → <code>/lock-req</code>(승인 잠금). 한 줄 상태는 <code>scripts/flow_status.py</code>가 단계별로 보여줍니다.</p>

  <h2>사람 게이트 vs LLM 루프 — 누가 무엇을 소유하나</h2>
  <p class="ag-muted">LLM은 <b>객관 증거</b>(PASS/FAIL/DIFF, coverage gap, lint/compile 진단, 프로토콜 assertion, traceability gap, stale 증거, 파형 gap, 성능 gap)가 있는 곳에서만 루프합니다. "RTL이 FL과 다르면 → RTL을 수리하거나 사람 게이트를 연다"가 하드룰입니다.</p>
  <table class="ag-aux">
    <tr><th style="width:50%">🔒 사람이 소유 (LLM 변경 금지)</th><th>🔁 LLM 루프 가능</th></tr>
    <tr>
      <td>요구사항 의도·범위·우선순위·수용기준 · SSOT 동작/인터페이스 계약 · coverage 목표 · waiver · 성능 타깃 · FL 골든 의미 · <b>최종 사인오프</b></td>
      <td>RTL · cocotb/pyuvm TB · 테스트 벡터 · 스코어보드 구현 · lint/스타일 픽스 · 리포트 · 생성 증거 (목표는 바꾸지 않고 자극/구현을 보강)</td>
    </tr>
  </table>

  <h2>RTL 품질 확보용 부수 워크플로우</h2>
  <p class="ag-muted">생성된 RTL이 "맞는지·합성 가능한지·타이밍을 만족하는지"를 보증하는 보조 단계들입니다. 필요할 때만 돌립니다.</p>
  <table class="ag-aux">
    <tr><th style="width:18%">워크플로우</th><th>RTL 품질의 어떤 면을 보증하나</th><th style="width:28%">산출물</th></tr>
    <tr><td>fl-model-gen</td><td>골든 기능/사이클 모델 → RTL 등가성 기준 마련</td><td><code>model/…</code>, <code>verify/equivalence_goals.json</code></td></tr>
    <tr><td>tb-gen</td><td>cocotb 테스트벤치(검증 자극) 생성</td><td><code>tb/cocotb/*</code></td></tr>
    <tr><td>sim</td><td>시뮬레이션으로 기능 정확성 확인</td><td><code>sim/sim_report.txt</code>, <code>results.xml</code>, <code>*.vcd</code></td></tr>
    <tr><td>lint</td><td>RTL 코딩/합성성 품질 게이트</td><td><code>lint/dut_lint.json</code></td></tr>
    <tr><td>coverage</td><td>검증 충분성(커버리지) 마감</td><td><code>cov/coverage.json</code></td></tr>
    <tr><td>syn / sta / pnr / sta-post</td><td>합성 · 타이밍 · 배치배선 · 사인오프(물리/타이밍 품질)</td><td><code>syn/</code>, <code>sta/</code>, <code>pnr/</code>, <code>sta-post/</code></td></tr>
    <tr><td>architect · goal-audit · signoff · sim_debug</td><td>SoC 통합 뷰 · 목표 점검 · 사인오프 묶음 · 파형 디버그(보조 화면)</td><td>—</td></tr>
  </table>

  <h2>전환 방법</h2>
  <p>채팅에서 <code>/wf &lt;workflow&gt;</code> 를 입력하거나 상단 워크플로우 셀렉터로 바꿉니다. 어떤 단계를 돌릴지 정하지 않았다면 <code>default</code> 에서 자연어로 시작하세요.</p>

  <div class="ag-foot">출처: <code>workflow/COMMON_ENGINE_FLOW.md</code> (캐노니컬 flow) · <code>scripts/flow_status.py</code> (단계별 사용자 명령) · <code>doc/wiki/default-agent-ip-flow.md</code> · <code>doc/wiki/workflow-ownership-and-boundaries.md</code></div>

</div>
`;

export function AtlasGuide(): ReactElement {
  const purify = (window as unknown as { DOMPurify?: DOMPurifyLike }).DOMPurify;
  const __html = (purify && purify.sanitize)
    ? purify.sanitize(ATLAS_GUIDE_HTML, { ADD_ATTR: ['target', 'rel'] })
    : ATLAS_GUIDE_HTML;
  return (
    <div className="atlas-guide">
      <style>{ATLAS_GUIDE_CSS}</style>
      <div dangerouslySetInnerHTML={{ __html }} />
    </div>
  );
}

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// app.jsx reads window.AtlasGuide when screen === 'guide'. AtlasGuide is not
// (yet) declared in atlas-window.d.ts, so the assignment goes through a narrow
// cast. Remove once all consumers import { AtlasGuide } directly.
(window as unknown as { AtlasGuide: typeof AtlasGuide }).AtlasGuide = AtlasGuide;
