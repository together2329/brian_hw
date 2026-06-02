# Frontend Streaming / Workflow Deep Test Notepad

Started: 2026-06-01T23:10+09:00
Goal: Find the optimal Atlas frontend fix for perceived response lag and run the broadest practical verification.

## Skill Survey
- Available skills surveyed from session list: imagegen, openai-docs, plugin-creator, skill-creator, skill-installer, browser:browser, chrome:Chrome, computer-use:computer-use, documents:documents, excalidraw-diagram, github:gh-address-comments, github:gh-fix-ci, github:github, github:yeet, obsidian-bases, omo:comment-checker, omo:debugging, omo:frontend-ui-ux, omo:init-deep, omo:lsp, omo:programming, omo:refactor, omo:remove-ai-slops, omo:review-work, omo:rules, omo:start-work, omo:ulw-loop, omo:ulw-plan, presentations, spreadsheets.
- Using omo:ulw-loop: user explicitly invoked `$omo:ulw-loop`; evidence-bound execution and manual QA required.
- Using omo:programming: TypeScript/TSX files are under test or change.
- Using omo:debugging: user-visible browser timing/perceived-lag issue; runtime evidence and Playwright/browser QA required.
- Not using omo:frontend-ui-ux: no new visual design or layout surface is being designed in this pass.
- Not using github:*: user did not request commit/push in this turn.

## Scope
- Surfaces: React streaming chat display, workflow chip switching, browser manual QA, Atlas frontend test/build pipeline.
- Files in scope: frontend/atlas/workspace-root-data-hook.tsx, frontend/atlas/workspace-root-session-hook.tsx, frontend/atlas/__tests__/workspace-render-smoke.test.tsx.
- Existing dirty worktree includes many unrelated files; only scoped Atlas files are touched.

## Success Criteria
- C1 token burst display is frame-coalesced:
  - Automated test: `frontend/atlas/__tests__/workspace-render-smoke.test.tsx` test id `coalesces rapid token display updates to the next animation frame`.
  - RED evidence: `npx vitest run __tests__/workspace-render-smoke.test.tsx --reporter verbose` failed with `expected <div class="md-agent"...> to be null` at line 541.
  - Manual QA channel: Browser use via Playwright script against `http://127.0.0.1:5173/index.vite.html`; emit rapid token burst and assert final visible text with no page errors.
  - Artifact target: `.omo/ulw-loop/019e7e69-3956-76b0-89df-6acc580185bd/evidence/token-burst-browser.txt` and screenshot `.png`.
- C2 workflow switch remains fast and IP-correct:
  - Automated test: `frontend/atlas/__tests__/workspace-render-smoke.test.tsx` test id `keeps the active IP when a workflow chip switches with an empty scope path`.
  - Manual QA channel: Browser use via Playwright delayed `/api/session/activate`; assert `backend.switchSession(brian/axi_dma/coverage)` happens before delayed activation resolves and no `/default/coverage`.
  - Artifact target: `.omo/ulw-loop/019e7e69-3956-76b0-89df-6acc580185bd/evidence/workflow-switch-browser.txt`.
- C3 forbidden activation does not resurrect the old fallback slash prompt:
  - Automated test: `frontend/atlas/__tests__/workspace-render-smoke.test.tsx` test id `does not fallback-dispatch a workflow slash prompt when activation is forbidden`.
  - Manual QA channel: Browser use or Playwright shim returning 403 for `/api/session/activate`; assert no backend prompt `/wf coverage`.
  - Artifact target: `.omo/ulw-loop/019e7e69-3956-76b0-89df-6acc580185bd/evidence/activation-403-browser.txt`.
- C4 adjacent regressions stay clean:
  - Automated tests: targeted smoke, grouped Atlas tests, `npx tsc --noEmit --pretty false`, `npm run build`, and broad `npm test -- --run --reporter verbose --testTimeout 30000`.
  - Manual QA channel: Browser use scenario C1/C2/C3 covers user-facing behavior; command outputs are supporting evidence.
  - Artifact target: `.omo/ulw-loop/019e7e69-3956-76b0-89df-6acc580185bd/evidence/test-matrix.txt`.

## Hypotheses
1. [CONFIRMED] Per-token `setStreamText(fullBuffer)` forces React work faster than the browser can paint; coalescing display updates to requestAnimationFrame should keep UI responsive while preserving immediate buffer capture.
2. [WATCH] Pending animation-frame flush can race with `parkLiveStream()` and resurrect stale text unless canceled before parking/clearing.
3. [WATCH] Workflow switch perceived slowness comes from binding websocket only after backend activation; this was already moved earlier and must remain covered.

## Evidence Log
- RED C1: `npx vitest run __tests__/workspace-render-smoke.test.tsx --reporter verbose` exited 1; 21 passed, 1 failed; failure text `expected <div class="md-agent"...> to be null`.
- GREEN C1: `npx vitest run __tests__/workspace-render-smoke.test.tsx --reporter verbose` exited 0; 22 passed, including `coalesces rapid token display updates to the next animation frame`.
- Regression group: `npx vitest run __tests__/workspace-render-smoke.test.tsx __tests__/switch-gate-wiring.test.tsx __tests__/adversarial-bugfixes.test.tsx --reporter verbose` exited 0; 3 files passed, 36 tests passed.
- Typecheck: `npx tsc --noEmit --pretty false` exited 0.
- Build: `npm run build` exited 0; Vite built production assets successfully.
- Broad suite: `npm test -- --run --reporter verbose --testTimeout 30000` exited 0; 37 files passed, 273 tests passed.
- Browser C1: Playwright against `http://127.0.0.1:5173/index.vite.html?view=workspace&session_id=brian&ip=axi_dma&wf=default` emitted token burst `frontend burst qa 1780323726942`; visible text appeared and `ATLAS_AGENT_RUNNING` cleared. Evidence: `evidence/token-burst-browser.txt`, `evidence/token-burst-browser.png`. Cleanup: Playwright context closed; `browser.close()` completed.
- Browser C2: Same Playwright run clicked `coverage`; `switchSession` event `brian/axi_dma/coverage` at t=5339.4 happened before delayed coverage `activate-end` at t=6240.0, and no `/default/coverage` route appeared. Evidence: `evidence/workflow-switch-browser.txt`. Cleanup: Playwright context closed; `browser.close()` completed.
- Browser C3: Playwright 403 activation run clicked `coverage`; `/api/session/activate` returned 403 and no backend `send` prompt `/wf coverage` appeared. Evidence: `evidence/activation-403-browser.txt`, `evidence/activation-403-browser.png`. Cleanup: Playwright context closed; `browser.close()` completed.

## Cleanup Receipts
- Existing Vite server on 127.0.0.1:5173 PID 76013 observed before browser QA; must be stopped if spawned by this session, otherwise left alone only if pre-existing.
- Worker `w_stream_text_coalescing` returned no implementation and was closed; implementation was applied directly after RED capture.
- Plan agent `plan_frontend_streaming_deep_test` did not return within repeated waits and was closed while still running; execution followed the criteria matrix above.
