# Draft: Lint Report Diagnostics

## Requirements (confirmed)
- "lint error 별로 몇개인지 보여주는 걸로"
- "그 error 별로 folding 펼쳐서 detail 볼 수 있게"
- "specific error 선택하면 rtl view 켜지면서 해당 line 밑에 왜 error 인지 알려줘"
- "좌우 width 안맞으면 보여준다"
- Fix the currently broken lint report layout shown in the screenshot.

## Technical Decisions
- Group diagnostics by `rule` first, then recognizable Verilator `%Warning-FOO`/`%Error-FOO` code, then a short message bucket.
- Keep backend JSON shape unchanged; current `tool_results[].diagnostics[]` already carries `severity`, `rule`, `file/path`, `line`, `column`, `message`, and `source`.
- Preserve the existing utilitarian Atlas visual system; no landing-page or decorative redesign.
- Add new helper modules for diagnostic presentation because touched files are already oversized.

## Research Findings
- `frontend/atlas/workspace-lint-coverage.tsx` owns `LintReportSummary` and currently renders only the first five diagnostics flat.
- `frontend/atlas/workflow-report.tsx` already has `openLintDiagnostic` that selects a path and `focusLine`, but does not store/pass the diagnostic payload.
- `frontend/atlas/preview-pane.tsx` already scrolls to `focusLine` in `FoldablePane`, so inline annotation can be attached to the same line row.
- `frontend/atlas/__tests__/workflow-report-click.test.tsx` is the focused Vitest surface for lint/coverage report interactions.

## Open Questions
- None blocking; default is to group by tool rule/error code and show raw diagnostic message/source for "why".

## Scope Boundaries
- INCLUDE: lint report layout, grouped/foldable diagnostics, click-through source focus, inline line annotation, focused tests, browser QA.
- EXCLUDE: changing lint agent execution backend, changing JSON report schema, adding waivers, broad PreviewPane refactor.
