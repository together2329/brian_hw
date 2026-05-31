# Perforce Live Client QA Plan

## Objective
Verify Atlas Perforce integration against a real local p4d server and a real Atlas client surface for Add, Edit, and Sync. Add the missing explicit Edit surface if tests prove it is absent.

## Constraints
- Use isolated temporary p4d servers on dedicated ports for QA; do not depend on the user's expired ticket on `localhost:1666`.
- Do not revert unrelated dirty worktree changes.
- Any production change must be test-first with RED before GREEN.
- Every criterion needs automated evidence plus a real channel artifact and cleanup receipt.

## Success Criteria
- C001 Browser happy path: real Atlas page can add a new file, edit/open a depot file, and sync/overwrite from Perforce. Evidence: `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13/evidence/C001-browser-add-edit-sync.json` and `.png`.
- C002 HTTP malformed edge: `/api/scm/edit` rejects path traversal and leaves no opened files. Evidence: `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13/evidence/C002-http-malformed-edit.txt`.
- C003 HTTP regression: explicit `provider=git` still works while default provider is Perforce. Evidence: `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13/evidence/C003-http-git-override.txt`.

## Waves
- Wave 1, TDD implementation: backend adapter/API edit operation and frontend Edit button with focused tests.
- Wave 2, verification: run focused backend/frontend tests, typecheck where touched, and existing adjacent Git/SCM tests.
- Wave 3, manual QA: run isolated p4d plus Atlas servers for C001/C002/C003, capture artifacts, clean every process/temp dir/port before recording PASS.
- Wave 4, final gate: full relevant suites, no-excuse checks on new TS files if any, reviewer audit, cleanup.

## Dependency Matrix
| Task | Depends on | Blocks | Parallel |
|---|---|---|---|
| Backend edit API test + implementation | none | C001, C002 | Frontend test |
| Frontend Edit control test + implementation | none | C001 | Backend test |
| HTTP malformed QA | backend edit implementation | C002 pass | Git regression QA |
| Browser Add/Edit/Sync QA | backend + frontend implementation | C001 pass | none |
| Git provider regression QA | none | C003 pass | HTTP malformed QA |

## Critical Path
Backend `/api/scm/edit` and `PerforceP4Adapter.edit_paths` are the critical path because both browser and malformed HTTP scenarios require a real Edit operation.
