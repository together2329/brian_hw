# Worker→UI Workflow Sync 2026-06-10

## Symptom

Inside a worker, `/to-ssot` (or any in-agent `/wf` switch) printed
"✅ Workflow switched to 'ssot-gen'" and did the work under the ssot-gen
system prompt — but `/wf` still reported `default`, the UI workflow dropdown
never moved, `/healthz active_workflow` stayed `default`, and a respawned
worker booted WITHOUT the ssot-gen system prompt.

## Root cause

Workflow propagation was one-way (UI → backend → worker):

- UI dropdown → `POST /api/session/activate` → canonical session key +
  DB row + structured `workspace_changed` emit → dropdown/healthz agree.
- Worker-side switch (`src/main.py` `WORKSPACE_SWITCH:` block) only set the
  worker-local `ACTIVE_WORKSPACE` overlay and emitted **chat text**. No
  structured event, no canonical update. `/wf` reads the canonical key's last
  segment (`core/slash_commands.py _current_workflow_name`), so it kept saying
  `default`.
- Worse, the switch block still assumed 3-seg `<owner>/<ip>/<workflow>`
  namespaces; a 4-seg v2 key (`<owner>/<ws>/<ip>/<wf>`) had its
  workspace_session treated as the IP and the real IP silently dropped.
- `core/session_worker.py run_worker` only loads a workspace's system prompt
  when the spawn key's workflow segment != `default` — a session whose
  canonical key is stuck at `.../default` therefore NEVER boots with the
  switched workspace's prompt.

Note: in worker mode `setup_session()` is pinned by the spawn-time
`ATLAS_SESSION_DIR` env, so an in-worker switch cannot really move the session
dir — it is inherently a prompt/workspace overlay. The durable move has to go
through the activate path, same as a dropdown click.

## Fix (commit on fix/worker-workflow-ui-sync)

1. `core/session_setup.py workflow_switch_target()` — pure helper that swaps
   ONLY the workflow segment, preserving 4-seg v2 namespaces
   (tests/test_workflow_switch_target.py).
2. `src/main.py` — switch block uses the helper and emits structured
   `workspace_changing`/`workspace_changed` events with
   `session=<new canonical key>` and `source="worker/workflow-switch"` via a
   new `_textual_emit_event_fn` hook.
3. `core/session_worker.py` — binds `_textual_emit_event_fn = worker.emit`
   (events reach the browser through the worker out-queue on the spawn key).
4. `frontend/atlas/app-session-hook.tsx` — subscribes `workspace_changed`;
   when the event is worker-sourced, same-owner, and announces a key different
   from the live one, it follows via the SAME `activateNamespace` path a
   dropdown click uses (dropdown, URL, healthz, next worker spawn all agree).
   Guards: `source.startsWith('worker/')` (UI-initiated activate emits the
   same event type — following those would loop), owner match (never follow a
   cross-owner key — see the phantom-IP leak), and key-differs.

## Gotchas for future work

- The worker that performed the switch keeps its spawn identity
  (`.../default` queue key); following via activate spawns/connects the proper
  `.../ssot-gen` worker. Conversation history does NOT carry across — same UX
  as switching workflow from the dropdown (per-workflow conversations).
- vitest harness realism: the roster guard collapses an IP the mocked
  `/api/ip/list` doesn't confirm, and a no-op mock `unsubscribe` accumulates
  duplicate handlers when hook deps change mid-mount. Both produced
  false-positive follow calls until the mocks mirrored real semantics.

Related: [[atlas-session-canonicalization-backlog-20260606]],
[[atlas-context-root-model-20260603]].

## Responding-state reconciliation 2026-06-16

Symptom: the Workspace footer can keep showing `Agent responding` while the
right-side worker panel says `ready` and `/healthz` reports `agent_running:
false`. In that state a submitted prompt appears in the feed, but no agent
output follows because the local optimistic streaming latch missed the terminal
`agent_state(false)` / `done` event.

Design rule: the optimistic responding pill may outrank worker polling only
during the normal startup grace window. After that window, the current session's
worker-status poll is authoritative when it says the session worker is alive,
not running, and ready/idle. The UI must route this through the same
`finishLiveRun()` path used by terminal websocket events so buffered stream
text, runtime labels, and command busy state are all cleared consistently.
