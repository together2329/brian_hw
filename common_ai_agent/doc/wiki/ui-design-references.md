# UI Design References

Read-only external UI checkouts we study when building or extending
ATLAS UI surfaces. None of this code ships in `common_ai_agent`; we
only borrow patterns conceptually.

Related: [[atlas-pipeline-screen]] · [[full-flow-pipeline]]

## open-design (Apache-2.0)

- Source: <https://github.com/nexu-io/open-design>
- Local clone: `~/Desktop/Project/brian_hw/external_refs/open-design/`
- Stack: Next.js 16 App Router · React 18 · TypeScript · Node 24
- Why we keep it: ships a polished *live agent panel* with streaming
  todos, a multi-dimensional critique scoresheet, and live artifact
  badges — exactly the three primitives the ATLAS Pipeline screen
  needs (running-card live tail, per-stage scoresheet, state badges).

### File map (patterns borrowed conceptually, never copied)

| open-design file | What we borrow | ATLAS use |
|---|---|---|
| `apps/web/src/components/Theater/ScoreTicker.tsx` | tick-bar trajectory + threshold marker; empty state until first round closes | StageCard run-history strip and `MiniScoresheet` |
| `apps/web/src/components/Theater/PanelistLane.tsx` | `data-role` left-border tint + per-row trajectory | Phase band left-border tints (AUTHOR / DETERMINISTIC / IMPLEMENT / VERIFY / SIGN-OFF) |
| `apps/web/src/components/Theater/TheaterStage.tsx` | top-level phase switch (`idle` / `degraded` / `collapsed` / `running`) | `AtlasPipeline` mount switch (no-ip / loading / error / live / all-green-collapsed) |
| `apps/web/src/components/Theater/TheaterTranscript.tsx` | scrolling single-pane transcript style | StageCard live log tail (Row 5) |
| `apps/web/src/components/Theater/TheaterCollapsed.tsx` | shipped run summary chip | All-green Pipeline auto-collapse to `✓ shipped 14/14` |
| `apps/web/src/components/Theater/TheaterDegraded.tsx` | degraded chip pattern | `evidence-stale` / `locked` card chrome |
| `apps/web/src/components/Theater/InterruptButton.tsx` | abort glyph + Esc keybind + pending state | Running-card `⏹` (Esc keybind, `data-pending` for two-click protection) |
| `apps/web/src/components/Theater/RoundDivider.tsx` | thin between-rows divider rule | Phase-band divider |
| `apps/web/src/components/LiveArtifactBadges.tsx` | small inline status chips (live / refreshing / failed / archived) | DAG MAP node badges + StageCard state badges |
| `apps/web/src/runtime/todos.ts` | reverse-walk events to find latest `TodoWrite` and stream `pending → in_progress → completed` | StageCard inline mini-todo list (rtl-gen packets / tasks) |
| `apps/web/src/components/Theater/CritiqueTheaterMount.tsx` | top-level mount + i18n wrapper convention | `AtlasPipeline` mount + `uiLang` plumbing |
| `apps/web/tests/components/ChatPane.streaming.test.tsx` | streaming-UI test pattern | future Pipeline streaming tests |
| `apps/web/tests/components/assistant-message-tool-status.test.tsx` | tool-call status rendering | StageCard live-tail tests |

### `data-*` attribute styling

The Theater subsystem drives almost all visual variation through
`data-state`, `data-role`, `data-current`, `data-meets-threshold`,
`data-meets-half`, `data-active`, `data-phase` attributes — with CSS
selectors (`[data-state="running"]`, `[data-role="critic"] { border-left-color: … }`)
doing the visual mapping. ATLAS Pipeline follows the same pattern:
the 8-state model (`idle` / `ready` / `running` / `passed` / `failed` /
`blocked` / `stale` / `locked`) lives as `data-state` on
`.pipe-stage-card` and `.pipe-node`, with all colour and animation
selectors keyed off it. No inline style colour logic.

### Refresh

```bash
cd ~/Desktop/Project/brian_hw/external_refs
rm -rf open-design && git clone --depth 1 https://github.com/nexu-io/open-design.git
```

Bump the date below when you do.

- Last refreshed: 2026-05-16

### What we do NOT take

- No CSS, React component code, or TypeScript types.
- No fonts, images, or OKLch palettes (ATLAS already has its own
  semantic token set in `frontend/atlas/styles.css:105-145`).
- No package dependencies — strictly read-only reference.
- No service-worker, Next.js routing, or Vercel-deploy machinery.

## Cross-links

- [[full-flow-pipeline]] — the 14 canonical stages Pipeline dispatches.
- [[workflow-ownership-and-boundaries]] — why no Retry button.
- [[workflow-feedback-and-scheduling]] — feedback packet that
  `[ go fix <owner> ]` materializes.
- [[atlas-pipeline-screen]] — the Pipeline screen itself.
- [[deterministic-emit-stages]] — why FL/CL bands are visually muted.
