# SSOT Q&A Workbench

`ssot-gen` should start from the Q&A Session tab. The tab is the authoring
surface for missing design decisions, not a passive history viewer.

## UI Contract

- Q&A Session is the first tab for `ssot-gen`.
- The active ask_user card uses the full center panel.
- The old QA history panel is hidden from this view; scoped QA records still
  live in backend/session state.
- The header exposes the primary authoring actions:
  - `Import` uploads requirement/source files.
  - `Deep Interview` runs `/grill-me <ip>`.
  - `To SSOT` runs `/to-ssot <ip>`.

## Import Contract

Import stores uploaded files under `<ip>/req/imports/` and then dispatches the
normal `/import --ip <ip> @<path>` command. The import path should extract clear
requirements directly into SSOT and leave unresolved decisions as Q&A items for
Deep Interview.

## Progress Contract

The Q&A tab reports remaining SSOT requirements from the backend-required
decision set. Filled decisions count toward progress; missing decisions stay
visible so the user and agent know what still needs clarification before
downstream workflows rely on the SSOT.

## Verification

2026-05-15 local checks covered:

- `tests/test_atlas_ssot_qa_workbench.py`
- `tests/test_atlas_qa_history_scope.py`
- `tests/test_atlas_multiuser_session_scope.py`
- ATLAS browser smoke on `ssot-gen` showing Q&A Session, Import, Deep Interview,
  To SSOT, and requirements remaining with no QA history panel.

## Related

- [[full-flow-pipeline]]
- [[human-review-and-escalation]]
- [[workflow-ownership-and-boundaries]]
