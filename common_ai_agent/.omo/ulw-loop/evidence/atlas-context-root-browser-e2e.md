# ATLAS Context Root Browser E2E Evidence

Date: 2026-06-03
Branch: `feat/atlas-context-root-model`

## Session Worker Status Exact Scope

Temporary server:

```text
127.0.0.1:37971
ATLAS_MULTI_USER=1
ATLAS_MULTI_USER_PROC=1
ATLAS_SESSION_WORKER_POLICY=single-active-owner
ATLAS_SESSION_WORKER_KEEPALIVE=1
```

Scenario:

1. Register and log in as `alice_e2e_1780496049950`.
2. Activate `alice_e2e_1780496049950/s1/ip_a/default`.
3. Open the Web UI with that canonical session in the URL.
4. Activate `alice_e2e_1780496049950/s2/ip_a/default`.
5. Open the Web UI with the `s2` canonical session in the URL.
6. Inspect status polling requests and direct worker status responses.

Observed status polling:

```text
/api/session/worker/status?session_id=alice_e2e_1780496049950%2Fs1%2Fip_a%2Fdefault
/api/session/worker/status?session_id=alice_e2e_1780496049950%2Fs2%2Fip_a%2Fdefault
```

Direct status responses:

```json
{
  "s1": {
    "status": 200,
    "owner_active_session": "alice_e2e_1780496049950/s1/ip_a/default",
    "worker_session": "alice_e2e_1780496049950/s1/ip_a/default"
  },
  "s2": {
    "status": 200,
    "owner_active_session": "alice_e2e_1780496049950/s2/ip_a/default",
    "worker_session": "alice_e2e_1780496049950/s2/ip_a/default"
  },
  "cross_owner": {
    "status": 403
  }
}
```

Screenshot:

```text
.omo/ulw-loop/evidence/browser/atlas-session-status-e2e.png
```

Notes:

- The screenshot shows `SESSION s2`, `IP_ID ip_a`, and right-rail session
  worker `alive`.
- Computer Use was attempted against `/Applications/ATLAS.app` and the local
  Tauri bundle; the tool returned `cgWindowNotFound` / `remoteConnection` for
  this desktop window in this run.
