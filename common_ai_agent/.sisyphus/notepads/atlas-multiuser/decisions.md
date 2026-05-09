## 2026-05-09 — SQLite queue worker architecture

- Implemented `core.session_worker` as the requested CLI entry point despite general core-module convention preferring CLI code in `src/`, because the plan explicitly requires `python -m core.session_worker --session-id <id> --db-path <path>`.
- Queue payloads are JSON strings for every outbound message type, keeping SQLite transport generic and leaving type-specific rendering to consumers.
- The worker uses simple 50ms polling for input, interrupt, stop, and ask_user answers; no event loop or WebSocket handling was introduced.
