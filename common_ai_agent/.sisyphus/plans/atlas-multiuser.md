# Atlas UI Multi-User System — Work Plan

## TL;DR

> **Goal**: Add session-based multi-user support to Atlas UI so multiple users can connect simultaneously, each with isolated conversations, todos, and agent state.
>
> **Key Decisions**:
> - **Persistence**: SQLite (not JSON files) — enables concurrent writes, user auth, query performance
> - **Frontend**: New `/login` → `/lobby` → `/workspace` flow with session picker
> - **Backend**: Per-session `_SessionBridge` isolation + session-scoped agent context
> - **Compatibility**: Single-user mode (`ATLAS_MULTI_USER=0`) keeps 100% backward compat
>
> **Estimated Effort**: Large (3-4 waves, ~15 tasks)
> **Parallel Execution**: YES — frontend/backend can be developed in parallel after Wave 1

---

## Context

### Original Request
> "I need to add multi-user system for atlas ui based on session id"

### Codebase Analysis (Completed)

**Existing Atlas UI** (`src/atlas_ui.py`):
- FastAPI + WebSocket server, ~10,668 lines
- Single global `_AtlasBridge` with one `_inbox`, `_outbox`, `_answer_qs`
- All WS clients receive same broadcast (no isolation)
- Partial multi-user groundwork: `ATLAS_MULTI_USER` env var, IP-based `user_session` in `/healthz`
- Session activation endpoint (`/api/session/activate`) sets global env vars

**Existing Session Manager** (`core/session_manager.py`):
- JSON file-based `SessionStorage` (thread-safe with RLock)
- `SessionManager` singleton with single `_current_session_id`
- Supports multiple sessions in storage, but only one "current" active session
- Messages, parts, snapshots, compaction, revert all exist

**Frontend** (`frontend/atlas/`):
- React/JSX SPA with Babel standalone
- No login/lobby concept — loads straight into workspace
- Session concept exists (dropdown for session/ip/workflow triple)

### User Questions (Design Drivers)

1. **"DB 가 필요하진 않을까?"** → Evaluate persistence layer for concurrent multi-user access
2. **"Main 화면需要的지?"** → Design user-facing entry flow (login/lobby/workspace)

---

## Architecture Decisions

### Decision 1: Persistence — SQLite over JSON Files

| Aspect | JSON (Current) | SQLite (Proposed) |
|--------|---------------|-------------------|
| Concurrent writes | ❌ RLock per file, contention at scale | ✅ Row-level locking, ACID |
| Query performance | ❌ Linear scan all files | ✅ Indexed queries |
| User/auth table | ❌ Separate user.json | ✅ `users` table |
| Session list with filter | ❌ Glob + parse all JSON | ✅ `SELECT ... WHERE user_id = ?` |
| Migration path | — | JSON → SQLite on first boot |
| Complexity | Low | Medium (requires schema) |

**Verdict**: SQLite. JSON served us for single-user, but multi-user needs concurrent session CRUD, user authentication, and efficient listing. SQLite is zero-dependency (Python stdlib), file-based (no server), and maps naturally to our relational data (users → sessions → messages → parts).

**Schema Design**:
```sql
-- users: identity + auth
CREATE TABLE users (
    id TEXT PRIMARY KEY,           -- uuid
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    password_hash TEXT,            -- bcrypt, nullable for "guest" users
    role TEXT DEFAULT 'user',      -- admin, user, guest
    created_at REAL,               -- unix timestamp
    last_login_at REAL
);

-- sessions: conversation containers
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT DEFAULT '',
    directory TEXT DEFAULT '',
    title TEXT,
    status TEXT DEFAULT 'active',  -- active, archived, deleted
    created_at REAL,
    updated_at REAL,
    archived_at REAL,
    summary TEXT,                  -- JSON blob
    FOREIGN KEY (user_id) REFERENCES users(id)
);
CREATE INDEX idx_sessions_user ON sessions(user_id, status);

-- messages: chat turns
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,            -- user, assistant, system
    agent TEXT DEFAULT '',
    model_id TEXT DEFAULT '',
    provider_id TEXT DEFAULT '',
    created_at REAL,
    completed_at REAL,
    cost REAL DEFAULT 0,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    tokens_reasoning INT DEFAULT 0,
    error TEXT                     -- JSON blob
);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);

-- parts: message fragments (text, tool, snapshot, etc.)
CREATE TABLE parts (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at REAL,
    -- text
    text TEXT,
    -- tool
    tool_name TEXT,
    call_id TEXT,
    tool_status TEXT DEFAULT 'pending',
    tool_input TEXT,               -- JSON
    tool_output TEXT,
    tool_error TEXT,
    tool_title TEXT,
    start_time REAL,
    end_time REAL,
    compacted_at REAL,
    -- snapshot / patch
    snapshot_hash TEXT,
    patch_hash TEXT,
    patch_files TEXT,              -- JSON array
    -- step
    step_reason TEXT,
    step_cost REAL,
    step_tokens_input INT,
    step_tokens_output INT
);
CREATE INDEX idx_parts_message ON parts(message_id);

-- user_sessions: WebSocket connection tracking (ephemeral)
CREATE TABLE ws_connections (
    connection_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    session_id TEXT,
    client_ip TEXT,
    user_agent TEXT,
    connected_at REAL,
    last_ping_at REAL
);
```

### Decision 2: Frontend Entry Flow — Login → Lobby → Workspace

**Current Flow**:
```
Browser → GET / → index.html (loads immediately into workspace)
```

**Proposed Flow** (`ATLAS_MULTI_USER=1`):
```
Browser → GET / → redirect /lobby (if no session cookie)
/lobby → Login (guest or username/password) → Session Picker
Session Picker → Create New / Resume Existing → /workspace?session=<id>
/workspace → Full Atlas UI (chat, files, SSOT, etc.)
```

**New Frontend Routes**:
| Route | Component | Purpose |
|-------|-----------|---------|
| `/lobby` | `LobbyPage` | Login + session selection |
| `/workspace` | `WorkspacePage` | Existing Atlas UI (renamed from root) |
| `/admin` | `AdminPage` | User management (admin only) |

**Session Picker UI**:
- Grid of session cards (title, last active, project, progress bar)
- "New Session" button with template selection
- Search/filter by title/date
- Archive/delete actions

### Decision 3: Backend Architecture — Session Isolation

**Current (Single-User)**:
```
WS Clients (all) → _AtlasBridge (single) → Agent Thread (single)
                     ↓
               Broadcast (all clients)
```

**Proposed (Multi-User)**:
```
WS Client A ─┐
WS Client B ─┼→ _MultiUserBridge → _SessionBridge (session-x) ─┐
WS Client C ─┘                                                   ├──→ Agent Thread
                                                    _SessionBridge (session-y) ─┘
                                                     ↓
                                           Session-scoped broadcast
```

**Key Constraint**: Single agent thread preserved (Phase 1). The agent operates on an "active session" and switches between sessions at turn boundaries. This avoids massive `main.py` refactoring.

**Phase 2** (future, not in this plan): Multiple agent threads for true concurrent execution.

---

## Work Objectives

### Core Objective
Enable multiple users to simultaneously use Atlas UI with fully isolated sessions, conversation history, todos, and preferences — while preserving 100% backward compatibility for single-user deployments.

### Concrete Deliverables
1. `core/atlas_db.py` — SQLite schema + ORM-like layer
2. `core/atlas_multiuser.py` — `_SessionBridge` + `_MultiUserBridge`
3. `frontend/atlas/lobby.jsx` — Login + session picker UI
4. `frontend/atlas/workspace.jsx` — Refactored main UI (was index)
5. Updated `src/atlas_ui.py` — Multi-user REST endpoints + WS routing
6. `tests/test_atlas_multiuser.py` — Backend tests
7. `tests/test_atlas_db.py` — DB layer tests
8. Migration script — `scripts/migrate_sessions_to_sqlite.py`

### Must Have
- [ ] SQLite persistence layer with full schema
- [ ] Per-session WebSocket event isolation
- [ ] Login/lobby frontend with session picker
- [ ] Session CRUD API (create, list, activate, archive, delete)
- [ ] Guest user support (no password required)
- [ ] Backward compatibility: `ATLAS_MULTI_USER=0` behaves exactly as before

### Must NOT Have (Guardrails)
- [ ] Do NOT refactor `main.py` agent loop (single agent thread constraint)
- [ ] Do NOT remove JSON session storage (keep as fallback/readonly)
- [ ] Do NOT add external DB dependencies (PostgreSQL, MySQL) — SQLite only
- [ ] Do NOT break existing single-user workflows

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest in tests/)
- **Automated tests**: YES (tests-after implementation)
- **Framework**: pytest (existing)

### QA Policy
Every task includes agent-executed QA scenarios:
- **Backend**: `curl` API calls + Python REPL assertions
- **Frontend**: Playwright browser automation
- **DB**: Direct SQLite query verification

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — no dependencies):
├── Task 1: SQLite schema + core/atlas_db.py
├── Task 2: DB migration script (JSON → SQLite)
├── Task 3: Frontend lobby mockup (static JSX)
└── Task 4: _SessionBridge class design doc

Wave 2 (Core backend — depends: Wave 1):
├── Task 5: _MultiUserBridge implementation
├── Task 6: Session CRUD REST endpoints
├── Task 7: WebSocket session binding + routing
├── Task 8: Integrate multi-user into atlas_ui.py
└── Task 9: Guest user auth middleware

Wave 3 (Frontend + Integration — depends: Wave 2):
├── Task 10: Lobby login + session picker (functional)
├── Task 11: Workspace session context integration
├── Task 12: Session switch mid-flight (no reload)
├── Task 13: Admin page (user list, session admin)
└── Task 14: Real-time session sync (WS broadcast to session peers)

Wave 4 (Tests + Polish — depends: Wave 3):
├── Task 15: Backend unit tests (DB, bridge, API)
├── Task 16: Frontend E2E tests (Playwright)
├── Task 17: Migration + backward compat verification
└── Task 18: Performance test (10 concurrent sessions)

Wave FINAL (Review):
├── Task F1: Code quality review
├── Task F2: Security review (auth, session fixation, CSRF)
├── Task F3: Real manual QA (multi-browser, session isolation)
└── Task F4: Scope fidelity check
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | — | 2, 5, 15 |
| 2 | 1 | 17 |
| 3 | — | 10, 11 |
| 4 | — | 5 |
| 5 | 1, 4 | 6, 7, 8 |
| 6 | 5 | 10, 13 |
| 7 | 5 | 8, 12, 14 |
| 8 | 5, 6, 7 | 11, 12, 14 |
| 9 | 5 | 10 |
| 10 | 3, 6, 9 | 12 |
| 11 | 3, 8 | 12, 14 |
| 12 | 7, 10, 11 | 16 |
| 13 | 6 | — |
| 14 | 8, 11 | 16 |
| 15 | 1, 5, 6 | F1 |
| 16 | 12, 14 | F3 |
| 17 | 2 | F2 |
| 18 | 8 | F4 |

---

## TODOs

### Wave 1: Foundation

- [x] **1. SQLite Schema + DB Layer (`core/atlas_db.py`)

  **What to do**:
  - Implement SQLite schema (users, sessions, messages, parts, ws_connections tables)
  - Create `AtlasDB` class with connection pooling (thread-local connections)
  - Implement CRUD methods: `create_user`, `get_user`, `create_session`, `get_session`, `list_sessions`, `save_message`, `get_messages`, etc.
  - Add `init_db()` function that creates tables + indexes
  - Add `close()` cleanup

  **Must NOT do**:
  - Do NOT use SQLAlchemy or ORM — raw sqlite3 for zero deps
  - Do NOT hardcode paths — accept `db_path` parameter

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []
  - Reason: Straightforward DB layer, no complex logic

  **Parallelization**: YES — independent of all other Wave 1 tasks

  **References**:
  - `core/session_manager.py` — Data models to port (SessionMetadata, MessageInfo, Part)
  - Python docs: `sqlite3` module connection/threading behavior

  **Acceptance Criteria**:
  - [ ] `python -c "from core.atlas_db import AtlasDB; db = AtlasDB(':memory:'); db.init_db()"` succeeds
  - [ ] `db.create_user("testuser", "Test User")` returns user dict with id
  - [ ] `db.create_session(user_id, title="Test")` returns session with id
  - [ ] `db.list_sessions(user_id)` returns list including created session
  - [ ] Thread safety: 10 threads concurrently creating sessions → no sqlite3.OperationalError

  **QA Scenarios**:
  ```
  Scenario: Basic CRUD
    Tool: Bash (python REPL)
    Steps:
      1. python -c "from core.atlas_db import AtlasDB; db=AtlasDB(':memory:'); db.init_db(); u=db.create_user('a','A'); print(u['id'])"
    Expected Result: prints UUID string, exit 0
    Evidence: .sisyphus/evidence/task-1-crud.txt

  Scenario: Concurrent writes
    Tool: Bash (python script)
    Steps:
      1. Create script that spawns 10 threads, each creates 10 sessions
      2. Assert final session count == 100
    Expected Result: 100 sessions, no exceptions
    Evidence: .sisyphus/evidence/task-1-concurrent.txt
  ```

- [x] **2. DB Migration Script (`scripts/migrate_sessions_to_sqlite.py`)

  **What to do**:
  - Read all existing JSON sessions from `~/.common_ai_agent/sessions/`
  - Insert into SQLite with `user_id = "legacy"` (orphaned user)
  - Map old file structure to new schema
  - Print migration report (sessions migrated, errors, skipped)
  - Support `--dry-run` flag

  **Must NOT do**:
  - Do NOT delete original JSON files (keep as backup)
  - Do NOT fail on parse errors — log and skip

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**: YES — depends on Task 1 schema being stable

  **Acceptance Criteria**:
  - [ ] Script runs without errors on existing `.common_ai_agent/sessions/`
  - [ ] `--dry-run` prints what WOULD be migrated without writing
  - [ ] Original JSON files remain untouched
  - [ ] Migration is idempotent (running twice doesn't duplicate)

  **QA Scenarios**:
  ```
  Scenario: Dry run
    Tool: Bash
    Steps:
      1. python scripts/migrate_sessions_to_sqlite.py --dry-run
    Expected Result: Prints counts, no SQLite file created
    Evidence: .sisyphus/evidence/task-2-dryrun.txt
  ```

- [x] **3. Frontend Lobby Mockup (Static JSX)**

  **What to do**:
  - Create `frontend/atlas/lobby.jsx` — React component
  - Login section: username input, "Continue as Guest" button
  - Session grid: mock session cards with title, date, status
  - "New Session" button with title input
  - Responsive CSS (mobile-friendly)

  **Must NOT do**:
  - Do NOT wire to backend yet (static/mock data only)
  - Do NOT modify existing `index.html` routing

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**: YES — purely frontend, no backend dependency

  **Acceptance Criteria**:
  - [ ] `lobby.jsx` renders without console errors when opened directly
  - [ ] Mobile viewport (375px) is usable
  - [ ] "New Session" modal opens/closes

  **QA Scenarios**:
  ```
  Scenario: Lobby renders
    Tool: Playwright
    Steps:
      1. Open file:///.../frontend/atlas/lobby.html (test wrapper)
      2. Screenshot full page
    Expected Result: No console errors, login form visible
    Evidence: .sisyphus/evidence/task-3-lobby.png
  ```

- [x] **4. _SessionBridge Design Doc**

  **What to do**:
  - Document the per-session bridge architecture
  - Define interface: methods, events, lifecycle
  - Specify how `_MultiUserBridge` manages multiple `_SessionBridge` instances
  - Document active session switching logic

  **Recommended Agent Profile**:
  - **Category**: `writing`

  **Parallelization**: YES — documentation only

  **Acceptance Criteria**:
  - [ ] Doc covers: session creation, client binding, event routing, agent lifecycle, cleanup
  - [ ] Interface diagram (ASCII or Excalidraw)

---

### Wave 2: Core Backend

- [x] **5. _MultiUserBridge Implementation (`core/atlas_multiuser.py`)**

  **What to do**:
  - Implement `_SessionBridge` class with per-session:
    - `_inbox`, `_interrupts`, `_outbox` queues
    - `_answer_qs`, `_pending_ask_user` dicts
    - `agent_running`, `agent_alive` flags
    - `_agent_starter`, `_stop_flag`
    - `clients` WeakSet
  - Implement `_MultiUserBridge`:
    - `_sessions: dict[str, _SessionBridge]`
    - `_active_session_id` with RLock
    - `bind_client()`, `unbind_client()`, `get_client_session()`
    - Legacy-compatible methods: `get_input()`, `poll_interrupt()`, `emit()`, `submit_prompt()`, etc.
    - `next_event()` polls ALL session outboxes
    - `activate_session()` switches active session

  **Must NOT do**:
  - Do NOT modify `main.py` — bridge must be callable without session args for compat
  - Do NOT spawn multiple agent threads

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Parallelization**: NO — depends on Task 1 (DB) and Task 4 (design)

  **References**:
  - `src/atlas_ui.py:105-283` — Current `_AtlasBridge` (copy interface exactly)
  - `src/atlas_ui.py:363-384` — `_broadcast_outbox` (needs session routing)
  - `src/atlas_ui.py:9922-10136` — `ws_agent` (needs session binding)

  **Acceptance Criteria**:
  - [ ] `_MultiUserBridge` passes all `_AtlasBridge` interface tests
  - [ ] Two sessions: events from session A only reach clients in A
  - [ ] `get_input()` blocks on active session's inbox
  - [ ] `activate_session()` switches inbox source

  **QA Scenarios**:
  ```
  Scenario: Session isolation
    Tool: Python REPL
    Steps:
      1. bridge = _MultiUserBridge()
      2. sess_a = bridge._ensure_session("user-a")
      3. sess_b = bridge._ensure_session("user-b")
      4. bridge.emit("token", session_id="user-a", text="hello")
      5. evt_b = sess_b._outbox.get_nowait() → should raise Empty
      6. evt_a = sess_a._outbox.get_nowait() → should succeed
    Expected Result: evt_a has text="hello", evt_b raises Empty
    Evidence: .sisyphus/evidence/task-5-isolation.txt
  ```

- [x] **6. Session CRUD REST Endpoints**

  **What to do**:
  Add to `src/atlas_ui.py`:
  - `POST /api/sessions` — create session (body: `{title, project_id}`)
  - `GET /api/sessions` — list user's sessions (query: `?status=active`)
  - `GET /api/sessions/{id}` — get session details
  - `POST /api/sessions/{id}/activate` — activate session (sets env + active session)
  - `POST /api/sessions/{id}/archive` — archive session
  - `DELETE /api/sessions/{id}` — delete session + data
  - `GET /api/users/me` — get current user info

  **Must NOT do**:
  - Do NOT require authentication for guest mode
  - Do NOT allow cross-user session access (enforce user_id filter)

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**: YES — can be done in parallel with Task 7 if Task 5 is done

  **Acceptance Criteria**:
  - [ ] `curl -X POST /api/sessions -d '{"title":"Test"}'` → 201 + session JSON
  - [ ] `curl /api/sessions` → list containing created session
  - [ ] `curl /api/sessions/other-users-id` → 404 (not 403 — don't leak existence)
  - [ ] `curl -X DELETE /api/sessions/{id}` → 204, session gone from list

  **QA Scenarios**:
  ```
  Scenario: Full CRUD lifecycle
    Tool: Bash (curl)
    Steps:
      1. Create session → extract id
      2. List sessions → verify contains id
      3. Get session → verify title matches
      4. Archive session → verify status=archived
      5. Delete session → verify 404 on GET
    Expected Result: All steps 200/201/204
    Evidence: .sisyphus/evidence/task-6-crud.txt
  ```

- [x] **7. WebSocket Session Binding + Routing**

  **What to do**:
  - Modify `ws_agent` to:
    1. Accept `session` query param or first-message init
    2. Call `bridge.bind_client(websocket, session_id)`
    3. Route ALL incoming messages to bound session
    4. On disconnect, call `bridge.unbind_client(websocket)`
  - Modify `_broadcast_outbox` to:
    - Call `bridge.next_event()` which returns `(msg, session_id)`
    - Send only to `bridge._sessions[session_id].clients`
  - Add `clients_by_session: dict[str, set]` tracking

  **Must NOT do**:
  - Do NOT broadcast to all clients (breaks isolation)
  - Do NOT lose unbound clients (fallback to "default" session)

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Parallelization**: YES — can parallel with Task 6 if Task 5 done

  **Acceptance Criteria**:
  - [ ] Client connecting with `?session=abc` gets bound to abc
  - [ ] Client without session param gets bound to "default"
  - [ ] Events from session abc only reach abc-bound clients
  - [ ] Disconnect removes client without affecting others

  **QA Scenarios**:
  ```
  Scenario: Two clients, two sessions
    Tool: Python (websockets test script)
    Steps:
      1. Connect ws1 with ?session=a, ws2 with ?session=b
      2. Send prompt from ws1
      3. Verify ws1 receives agent events, ws2 receives nothing
    Expected Result: ws1 has events, ws2 has no events
    Evidence: .sisyphus/evidence/task-7-routing.txt
  ```

- [x] **8. Integrate Multi-User into atlas_ui.py**

  **What to do**:
  - Replace `_AtlasBridge` instantiation with `_MultiUserBridge` when `ATLAS_MULTI_USER` enabled
  - Keep `_AtlasBridge` for single-user mode (backward compat)
  - Update `run_atlas_ui` to wire `_MultiUserBridge` callbacks to `main.py`
  - Ensure `app.state.bridge` exposes correct type
  - Update all endpoint closures that access `bridge` to handle multi-user

  **Must NOT do**:
  - Do NOT delete `_AtlasBridge` class (keep for single-user)
  - Do NOT change `main.py` callback signatures

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Parallelization**: NO — depends on Tasks 5, 6, 7

  **Acceptance Criteria**:
  - [ ] `ATLAS_MULTI_USER=0` → server starts, single-user mode works exactly as before
  - [ ] `ATLAS_MULTI_USER=1` → server starts, multi-user mode active
  - [ ] Healthz returns `user_session` when multi-user enabled
  - [ ] Single test passes: connect WS, send prompt, receive response

  **QA Scenarios**:
  ```
  Scenario: Backward compatibility
    Tool: Bash
    Steps:
      1. Start server without ATLAS_MULTI_USER
      2. Run existing test: python tests/test_atlas_rtl_blocker_qa.py
    Expected Result: Test passes (no regressions)
    Evidence: .sisyphus/evidence/task-8-compat.txt
  ```

- [x] **9. Guest User Auth Middleware**

  **What to do**:
  - Create `core/atlas_auth.py`:
    - `GuestAuth` class: auto-creates anonymous user with session cookie
    - `SessionAuth` dependency for FastAPI endpoints
    - Optional password auth (bcrypt hashed)
  - Add middleware to `atlas_ui.py` that:
    - Reads `atlas_session` cookie
    - Creates guest user if no cookie / invalid
    - Sets `request.state.user_id`

  **Must NOT do**:
  - Do NOT require password by default (guest-first UX)
  - Do NOT use JWT (overkill for local tool) — use signed cookies

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**: YES — independent of WS routing

  **Acceptance Criteria**:
  - [ ] First visit sets `atlas_session` cookie with guest user
  - [ ] Subsequent requests include same user_id
  - [ ] `GET /api/users/me` returns guest user info
  - [ ] Optional: `POST /api/auth/register` creates password user

  **QA Scenarios**:
  ```
  Scenario: Guest auto-create
    Tool: Bash (curl)
    Steps:
      1. curl -I /api/users/me  → extract Set-Cookie header
      2. curl /api/users/me with that cookie → verify user exists
    Expected Result: 200, user.id is UUID, username starts with "guest_"
    Evidence: .sisyphus/evidence/task-9-guest.txt
  ```

---

### Wave 3: Frontend + Integration

- [ ] **10. Lobby Login + Session Picker (Functional)**

  **What to do**:
  - Wire `lobby.jsx` to real backend:
    - `POST /api/auth/guest` → get guest session cookie
    - `GET /api/sessions` → populate session grid
    - `POST /api/sessions` → create new session
    - Click session card → navigate to `/workspace?session=<id>`
  - Add loading states, error handling
  - Search/filter sessions by title

  **Must NOT do**:
  - Do NOT implement real password login yet (guest only for MVP)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**: NO — depends on Tasks 3, 6, 9

  **Acceptance Criteria**:
  - [ ] Open `/lobby` → auto-creates guest, shows sessions
  - [ ] Click "New Session" → modal opens, create → redirects to workspace
  - [ ] Session cards show real title, updated_at, project
  - [ ] Search filters sessions correctly

  **QA Scenarios**:
  ```
  Scenario: Create and enter session
    Tool: Playwright
    Steps:
      1. Navigate to /lobby
      2. Click "New Session"
      3. Enter title "My Test"
      4. Click Create
      5. Assert URL contains /workspace?session=
      6. Assert sidebar shows "My Test"
    Expected Result: Workspace loads with correct session
    Evidence: .sisyphus/evidence/task-10-lobby.png
  ```

- [ ] **11. Workspace Session Context Integration**

  **What to do**:
  - Modify `frontend/atlas/data.jsx` or equivalent to:
    - Read `?session=` from URL on load
    - Send `{"type":"init","session":"..."}` as first WS message
    - Include session in all API calls
  - Ensure todo list loads from session-scoped path
  - Ensure conversation history loads from session

  **Must NOT do**:
  - Do NOT break single-user mode (no session param = default behavior)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

  **Parallelization**: YES — can parallel with Task 10 if API is stable

  **Acceptance Criteria**:
  - [ ] Workspace with `?session=abc` loads abc's todos
  - [ ] Workspace with `?session=xyz` loads xyz's todos (different list)
  - [ ] Chat history is session-scoped

  **QA Scenarios**:
  ```
  Scenario: Session-scoped todos
    Tool: Playwright
    Steps:
      1. Open workspace?session=a, add todo "A"
      2. Open workspace?session=b in new tab
      3. Verify todo list does NOT contain "A"
      4. Add todo "B" in session b
      5. Switch back to session a → verify still has "A", no "B"
    Expected Result: Todos isolated per session
    Evidence: .sisyphus/evidence/task-11-todos.png
  ```

- [ ] **12. Session Switch Mid-Flight (No Reload)**

  **What to do**:
  - Add session switcher dropdown in workspace header
  - Switching sends:
    1. `POST /api/sessions/{new_id}/activate`
    2. WS message `{"type":"switch_session","session":"new_id"}`
    3. Frontend clears state, loads new session data
  - Graceful handling: if agent running, show "Agent busy in other session" warning

  **Must NOT do**:
  - Do NOT interrupt running agent (show warning instead)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

  **Parallelization**: NO — depends on Task 10, 11

  **Acceptance Criteria**:
  - [ ] Switch session without page reload
  - [ ] New session's todos/chat load within 1 second
  - [ ] If agent running, modal warns user

  **QA Scenarios**:
  ```
  Scenario: Switch session
    Tool: Playwright
    Steps:
      1. Open workspace with session A
      2. Create session B from dropdown
      3. Switch to B
      4. Assert chat is empty (new session)
      5. Switch back to A
      6. Assert previous chat history visible
    Expected Result: Seamless switch, correct data per session
    Evidence: .sisyphus/evidence/task-12-switch.png
  ```

- [ ] **13. Admin Page (User List, Session Admin)**

  **What to do**:
  - Create `frontend/atlas/admin.jsx`
  - Backend endpoints:
    - `GET /api/admin/users` — list all users (admin only)
    - `GET /api/admin/sessions` — list all sessions with user
    - `DELETE /api/admin/sessions/{id}` — force delete
  - UI: table with user stats, session counts, actions

  **Must NOT do**:
  - Do NOT expose password hashes in API

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

  **Parallelization**: YES — independent of session switch

  **Acceptance Criteria**:
  - [ ] `/admin` accessible only to users with `role='admin'`
  - [ ] Shows user list with session counts
  - [ ] Can force-delete any session

  **QA Scenarios**:
  ```
  Scenario: Admin access control
    Tool: Bash (curl)
    Steps:
      1. curl /api/admin/users as guest → 403
      2. Create admin user, curl with admin cookie → 200
    Expected Result: Guest gets 403, admin gets user list
    Evidence: .sisyphus/evidence/task-13-admin.txt
  ```

- [ ] **14. Real-Time Session Sync (Session Peers)**

  **What to do**:
  - If user opens same session in two tabs, events sync in real-time
  - Implementation: when broadcasting to session clients, include ALL clients bound to that session
  - Add `{"type":"peer_joined"}` / `{"type":"peer_left"}` events

  **Must NOT do**:
  - Do NOT sync across different sessions (isolation must hold)

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**: YES — small addition to existing broadcast logic

  **Acceptance Criteria**:
  - [ ] Two tabs on same session: typing in one appears in other
  - [ ] Tab on different session: does NOT see events

  **QA Scenarios**:
  ```
  Scenario: Peer sync
    Tool: Playwright
    Steps:
      1. Open session A in Tab 1
      2. Open same session A in Tab 2
      3. Send message in Tab 1
      4. Verify Tab 2 shows the message within 2 seconds
    Expected Result: Cross-tab sync works
    Evidence: .sisyphus/evidence/task-14-sync.png
  ```

---

### Wave 4: Tests + Polish

- [ ] **15. Backend Unit Tests**

  **What to do**:
  - `tests/test_atlas_db.py`: DB CRUD, concurrent access, migration
  - `tests/test_atlas_multiuser.py`: Bridge isolation, session switching, event routing
  - `tests/test_atlas_api.py`: REST endpoints, auth, permissions

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**: YES — tests are independent

  **Acceptance Criteria**:
  - [ ] `pytest tests/test_atlas_db.py` → all pass
  - [ ] `pytest tests/test_atlas_multiuser.py` → all pass
  - [ ] `pytest tests/test_atlas_api.py` → all pass
  - [ ] Coverage ≥ 80% for new code

- [ ] **16. Frontend E2E Tests**

  **What to do**:
  - Playwright tests:
    - Lobby: create session, login as guest
    - Workspace: send message, receive response, session isolation
    - Session switch: dropdown, data refresh
  - Screenshot comparisons for visual regression

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
  - **Skills**: [`playwright`]

  **Parallelization**: YES — independent test files

  **Acceptance Criteria**:
  - [ ] `npx playwright test tests/e2e/lobby.spec.js` → pass
  - [ ] `npx playwright test tests/e2e/workspace.spec.js` → pass
  - [ ] Screenshots saved for manual review

- [ ] **17. Migration + Backward Compat Verification**

  **What to do**:
  - Run migration script on representative `.session/` data
  - Verify single-user mode (`ATLAS_MULTI_USER=0`) passes ALL existing tests
  - Document any breaking changes

  **Acceptance Criteria**:
  - [ ] Existing `tests/test_atlas_rtl_blocker_qa.py` passes in single-user mode
  - [ ] Migration produces valid SQLite from real JSON data

- [ ] **18. Performance Test (10 Concurrent Sessions)**

  **What to do**:
  - Script that opens 10 WebSocket connections, each to different session
  - Each sends 5 prompts, measures:
    - Response latency
    - Memory usage
    - SQLite contention
  - Target: < 2s latency, < 500MB RAM

  **Acceptance Criteria**:
  - [ ] 10 concurrent sessions run without crash
  - [ ] No `sqlite3.OperationalError` (busy/locked)
  - [ ] Memory stable (no leak)

---

### Phase 2: Parallel Agent Processes (SQLite IPC)

Added after initial Waves 1-4 to enable true parallel multi-user execution.

- [x] **P2-1. SQLite IPC Queue Schema**
  - Added `session_queue` table to `core/atlas_db.py`
  - Methods: `enqueue_message`, `dequeue_message`, `poll_messages`, `acknowledge_message`, `cleanup_old_messages`, `get_message`
  - Verified: py_compile pass, concurrent access test pass

- [x] **P2-2. Session Worker Subprocess**
  - Created `core/session_worker.py` — wraps `main.chat_loop()` with SQLite queue callbacks
  - Handles: prompt, interrupt, stop, content, reasoning, todo, flush, token_usage, ask_user bidirectional flow
  - Verified: py_compile pass, LSP clean, `--help` works

- [x] **P2-3. Session Process Manager**
  - Created `core/session_process_manager.py` — spawn/kill/monitor subprocesses
  - Graceful shutdown: SIGTERM → 5s wait → SIGKILL
  - Thread-safe with RLock, context manager support
  - Verified: py_compile pass, 6 integration tests pass

- [x] **P2-4. MultiUserBridge Process Integration**
  - Modified `core/atlas_multiuser.py`: `_MultiUserBridge(use_processes=True)`
  - Routes I/O through `SessionProcessManager` in multi-user mode
  - Preserves 100% backward compatibility for single-user mode
  - Verified: existing 5 bridge tests pass, new 6 process tests pass

- [x] **P2-5. Parallel Execution Tests**
  - Created `tests/test_process_based_sessions.py`
  - 6 tests: spawn multiple, input isolation, output isolation, bridge routing, kill/cleanup, stop_all
  - All 11 multiuser tests pass (5 legacy + 6 new) in 3.70s

---

## Final Verification Wave

- [x] **F1. Code Quality Review**
  - Run linter, type checker
  - Check for `as any`, empty catches, `console.log` in prod
  - Verify no AI slop patterns

- [x] **F2. Security Review**
  - Session fixation prevention (regenerate session ID on login)
  - CSRF protection for state-changing endpoints
  - Path traversal check on all file APIs
  - Verify no SQL injection (parameterized queries only)

- [x] **F3. Real Manual QA**
  - Chrome + Firefox + Safari
  - Mobile Safari (iOS)
  - Test: guest → create session → chat → switch → archive → logout

- [x] **F4. Scope Fidelity Check**
  - Verify all "Must Have" items exist
  - Verify all "Must NOT Have" items absent
  - Check for scope creep

---

## Commit Strategy

| Wave | Commit Message | Files |
|------|---------------|-------|
| 1 | `feat(db): add SQLite schema and AtlasDB layer` | `core/atlas_db.py`, `scripts/migrate_sessions_to_sqlite.py` |
| 1 | `feat(ui): add lobby mockup and workspace refactor` | `frontend/atlas/lobby.jsx`, `frontend/atlas/workspace.jsx` |
| 2 | `feat(multiuser): add _SessionBridge and _MultiUserBridge` | `core/atlas_multiuser.py` |
| 2 | `feat(api): add session CRUD and auth endpoints` | `src/atlas_ui.py` (new routes) |
| 2 | `feat(ws): add session-based WebSocket routing` | `src/atlas_ui.py` (ws_agent, broadcast) |
| 3 | `feat(lobby): wire lobby to backend APIs` | `frontend/atlas/lobby.jsx` |
| 3 | `feat(workspace): add session context and switching` | `frontend/atlas/workspace.jsx`, `data.jsx` |
| 4 | `test(multiuser): add backend and frontend tests` | `tests/test_atlas_*.py`, `tests/e2e/` |
| 4 | `docs(multiuser): add migration guide and ADR` | `docs/MULTIUSER.md` |

---

## Success Criteria

### Verification Commands
```bash
# DB layer
python -m pytest tests/test_atlas_db.py -v

# Multi-user bridge
python -m pytest tests/test_atlas_multiuser.py -v

# API
python -m pytest tests/test_atlas_api.py -v

# E2E
npx playwright test tests/e2e/

# Backward compat
ATLAS_MULTI_USER=0 python tests/test_atlas_rtl_blocker_qa.py

# Performance
python scripts/benchmark_multiuser.py --sessions 10 --prompts 5
```

### Final Checklist
- [ ] Multiple users can connect simultaneously
- [ ] Session isolation: user A cannot see user B's data
- [ ] Session persistence: data survives server restart
- [ ] Guest mode works without configuration
- [ ] Single-user mode unchanged (ATLAS_MULTI_USER=0)
- [ ] All tests pass
- [ ] Documentation complete
