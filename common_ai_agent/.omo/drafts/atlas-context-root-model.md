# Draft: Atlas Context Root Model

## Requirements (confirmed)
- "project root 가 있고 그 밑에 user name 이 있고 그 안에 ip 들이 있고. .session 이 있어서 user간 .session 과 ip를 완전 격리"
- "session id 를 추가해서 다른 session에서 여러 같은 ip를 테스트"
- "worker가 실행할때 부터 IP가 정해져 있으니, 아예 그 곳에서 실행"
- "tool call 에 injection 할 필요가 없어"
- "common_ai_agent의 cwd 는 worker 입장에서는 아예 필요 없을듯"
- "--root 를 지정하지 않을때" 기본 root는 user home 아래 특정 폴더
- "workflow-root 도 필요 없어 보여. 왜냐하면 workflow wiki 도 복사"
- "session 도 UI 에서 추가할 수 있어야"
- "명령도 관여해 context todo 등도 다 같이 관여"

## Technical Decisions
- Introduce a v2 context model, without immediately deleting existing `ATLAS_PROJECT_ROOT` behavior.
- Treat `--root` as `ATLAS_ROOT`, the visible storage root. Default it to `~/ATLAS`.
- Derive `ATLAS_WORKSPACE_ROOT = ATLAS_ROOT / user / session`.
- Derive `ATLAS_IP_ROOT = ATLAS_WORKSPACE_ROOT / ip`.
- Store session files at `ATLAS_WORKSPACE_ROOT / ".session" / ip / workflow`.
- Spawn worker processes with `cwd = ATLAS_IP_ROOT`.
- Keep `ATLAS_SOURCE_ROOT` or an installed package path only as runtime/import detail, not as semantic cwd.
- Keep `ATLAS_PROJECT_ROOT` as a compatibility alias for `ATLAS_WORKSPACE_ROOT` during migration.
- Add a canonical context object/key: `user/session/ip/workflow`.

## Research Findings
- `src/atlas_ui.py` currently defaults `PROJECT_ROOT` to `Path(os.getcwd()).resolve()` and injects it into file, git, jobs, and VCD routes.
- `src/atlas_runtime_run.py` seeds the current 3-part active session as `session_id/ip/workflow`.
- `core/session_process_manager.py` parses `session_id` as `owner/ip/workflow`, exports worker env, and starts worker `cwd=str(self._project_root)`.
- `core/session_setup.py` writes todo/history under `ATLAS_PROJECT_ROOT/.session/<session>`.
- `core/tools.py` contains heuristic cwd/path injection for active IP and currently runs shell tools from `$ATLAS_PROJECT_ROOT/$ATLAS_ACTIVE_IP` when possible.
- `frontend/atlas/data-helpers.tsx` and `workspace-session-routing.tsx` derive active IP from the last two session path segments.
- `core/slash_commands.py`, `src/config.py`, `lib/display.py`, and `src/atlas_runtime_run.py` read `TODO_FILE`, `SESSION_DIR`, `ATLAS_ACTIVE_SESSION`, and `ATLAS_PROJECT_ROOT`.
- `src/atlas_api_git.py` and `src/atlas_api_jobs.py` route git/perforce/jobs through project-root and IP-root helpers.

## Open Questions
- Should `session` be user-visible free text, generated IDs, or both?
- Should Desktop persist last `ATLAS_ROOT`, or always default to `~/ATLAS` when `--root` is omitted?
- Should v2 context be enabled by default after compatibility tests pass, or gated behind `ATLAS_CONTEXT_MODEL=v2` first?

## Scope Boundaries
- INCLUDE: root/session/IP/workflow path model, worker cwd, env contract, UI session selector, command plane, tests, review checklist.
- INCLUDE: compatibility shim so legacy `owner/ip/workflow` sessions keep working during migration.
- INCLUDE: `/context`, `/todo`, wiki refresh, git/perforce, jobs, file tree, healthz.
- EXCLUDE: changing auth/login/email recovery behavior.
- EXCLUDE: deleting `ATLAS_PROJECT_ROOT` immediately.
- EXCLUDE: rewriting workflow implementation to package entrypoints in the first wave.
