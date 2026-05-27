// guide.jsx — "How to use ATLAS" reference screen.
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

  <div class="ag-foot">출처: <code>doc/wiki/default-agent-ip-flow.md</code> · <code>doc/wiki/workflow-ownership-and-boundaries.md</code> · <code>workflow/wiki/ip_knowledge/*.md</code></div>

</div>
`;

window.AtlasGuide = function AtlasGuide() {
  const __html = (window.DOMPurify && window.DOMPurify.sanitize)
    ? window.DOMPurify.sanitize(ATLAS_GUIDE_HTML, { ADD_ATTR: ['target', 'rel'] })
    : ATLAS_GUIDE_HTML;
  return (
    <div className="atlas-guide">
      <style>{ATLAS_GUIDE_CSS}</style>
      <div dangerouslySetInnerHTML={{ __html }} />
    </div>
  );
};
