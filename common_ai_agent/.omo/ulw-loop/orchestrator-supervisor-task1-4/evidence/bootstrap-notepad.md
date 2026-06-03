ULW Task1-4 bootstrap note
===========================

Session: orchestrator-supervisor-task1-4
Plan: .omo/plans/orchestrator-supervisor-ipc.md
Requested skills: omo:ulw-loop, omo:programming, computer-use

Initial constraints
-------------------

- User requested Task1-4 TDD.
- Existing Codex goal state is blocked from an older objective, so create_goal cannot be reused for this work.
- Worktree is dirty with many unrelated changes; do not revert or clean unrelated files.
- No AGENTS.md applies under common_ai_agent itself; AGENTS.md files found only in ../external_refs/open-design.
- Python edits must follow omo:programming guidance: TDD first, strict typing, and new production modules should stay below 250 pure LOC when possible.
- Existing large files such as src/atlas_api_jobs.py and src/orchestrator/runner.py should receive minimal seam edits only.
- Computer Use manual QA must be attempted and either captured or explicitly recorded as blocked if the tool cannot inspect the desktop window.

Execution shape
---------------

- Normalize ULW goals to four Task1-4 implementation goals rather than the accidental 35-goal split.
- Add RED tests before production source edits.
- Implement new runtime/supervisor/wake logic mostly in new modules.
- Run targeted GREEN tests, then manual HTTP/tmux/Computer Use checks.
- Use a reviewer gate before final delivery.
