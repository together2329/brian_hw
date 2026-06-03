# Draft: Session Flow Dashboard

## Requirements (confirmed)
- "Session 을 새로 신설하게 지금 쭉 만들고 있어. 이 관점에서 다시 한 번 나누어줘."
- "User가 Session 에서 얼마나 Input을 날렸는지? LLM Call 은 얼마나 했는지? IP 별로는 ? 뭐 이런 것도? IP는 언제 생성이 되었니? IP에 대해 어떤 worker가 어떤 일을 했는지?"
- "다 종합적으로 이 흐름이 잘 가고 있는지 어떻게 잘 사용하고 있는지 문제 없는지? 다시 리스트업좀"
- "그럼 UI로 한다면 어떻게?"
- "좋네. 이렇게 하기 위해 기반은 되어 있나? DB는 이걸 저장하나?"
- "어떻게 바꾸면 좋을지 planning 좀."

## Technical Decisions
- Core unit: Session, not User. User/IP/worker/cost/artifact/status become dimensions attached to session flow.
- UI approach: add a dedicated Admin "Session Flow" tab instead of replacing existing admin tabs.
- Backend approach: add a focused session-flow aggregation module and `/api/admin/session-flow`; keep `/api/admin/usage` stable.
- Data approach: use additive schema only. Preserve historical rows and backfill best-effort attribution with explicit confidence/gap fields.
- Event approach: add an append-only session-flow ledger for durable lifecycle events, then derive rollups from it.
- Privacy approach: count user inputs and store metadata; do not copy full raw prompts into admin rollups.
- Test approach default: tests-first for schema/API aggregation invariants, tests-after/smoke for frontend rendering and interaction.

## Research Findings
- Backend admin API lives in `src/atlas_admin.py`; `/api/admin/usage` delegates to `core/atlas_admin_usage.py`.
- Canonical DB schema and methods live in `core/atlas_db.py` for `sessions`, `session_queue`, `ip_blocks`, `artifact_versions`, `workflow_runs`, `trace_events`, and `llm_calls`.
- Session UI/admin roots live in `frontend/atlas/admin.tsx`, with tabs split across `admin-overview.tsx`, `admin-tables-a.tsx`, `admin-tables-b.tsx`, `admin-runtime.tsx`, and helpers.
- Session lifecycle routes live in `src/atlas_api_sessions.py`, especially `/api/session/history`, `/api/session/state`, `/api/session/list`, `/api/session/worker/status`, and `/api/sessions`.
- Test coverage exists for DB schema/admin usage/session routing/user dashboard, but frontend admin has no dedicated smoke test comparable to user dashboard.
- Current DB supports a v1 view but not full truth-grade attribution: `messages`/`parts` are empty, `trace_events.llm_call_id` and `artifact_id` are unfilled, many `llm_calls.session_id` values are empty or unmatched, and worker identity is not first-class.

## Open Questions
- No user-blocking question. Default scope is to design the implementation plan, not modify runtime code in this planning turn.

## Scope Boundaries
- INCLUDE: schema additions, write-path attribution, backfill, session-flow aggregation API, admin UI tab, tests, QA, wiki/doc update.
- INCLUDE: three stakeholder lenses: builder/system creator, team lead, executive.
- INCLUDE: user input counts, LLM call/token/cost counts, IP created/provenance, worker activity per IP/session, flow health/problem flags.
- EXCLUDE: destructive historical data rewrite, replacement of existing admin dashboard, full raw prompt exposure in admin rollups, billing or permission system redesign.
