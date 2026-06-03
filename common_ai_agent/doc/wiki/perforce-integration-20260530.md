# Perforce integration 2026-05-30 — Helix Core adapter · Sync UI · test-isolation fix

Wires ATLAS's provider-abstracted SCM layer to a real Perforce (Helix Core)
server and adds a two-pane **Perforce Sync** tab. A developer can push IP folders
to Perforce (add → submit) and pull them back (force-sync = overwrite). Built on
a local dev server; design is site-portable. Related: [[common-ai-agent-map]] ·
[[atlas-pytest-hygiene]] (sibling test-hygiene note) · [[babel-retirement-cutover-20260529]]
(why the UI override needs the Vite bundle, not legacy babel injection).

## The "자리" (where it plugs in)

`core/scm.py` already abstracts SCM behind `SCMAdapter` (Git is the live impl).
The built-in `PerforceSCMAdapter` is an **intentional stub** — the contract test
`tests/test_scm_adapter.py::test_perforce_adapter_is_explicit_interface_until_implemented`
asserts it stays unimplemented. So the real p4 behavior is supplied via the
documented **override hook**, never by editing the stub:

```
ATLAS_SCM_PROVIDER=perforce
ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter   # in .env
```

Before this work `.env` had `ATLAS_SCM_PROVIDER=perforce` but **no adapter
override**, so every SCM op resolved to the stub → "not implemented". That was
the bug to fill.

## Local server (dev)

- Helix Core 2026.1 (arm64) binaries in `~/Desktop/Project/helix-core-server/`, symlinked into `~/.local/bin`.
- `p4d -r ~/p4root -p 1666 -d`; **security=4** (every command needs `p4 login`; `brian` is superuser).
- Depot **`GOOD_SOC`** (stream depot, StreamDepth `//GOOD_SOC/1`); stream **`//GOOD_SOC/GOOD_IP`** (mainline).

## Components

| Piece | File(s) | Notes |
|---|---|---|
| Adapter | `core/scm_perforce.py` → `PerforceP4Adapter(SCMAdapter)` | `submit`=`p4 reconcile`+`p4 submit`; `sync`=`p4 sync -f` (force/overwrite); `status`/`diff`/`log`/`show`/`hard_reset`; UI helpers `sync_state`/`open_paths`/`revert_paths`/`sync_paths`. `-ztag` parsing; benign non-zero exits softened. **Guard**: refuses reconcile/submit when adapter root == client root (so a blanket reconcile can't sweep `.env`). Per-IP root = `PROJECT_ROOT/<ip>`. |
| API routes | `src/atlas_api_git.py` | Added `POST /api/scm/sync`, `GET /api/scm/pane`, `POST /api/scm/add`, `POST /api/scm/revert` via `_scm_optional` hasattr-guard (non-perforce providers get a clean "unsupported"). Reuses existing `/api/scm/{status,submit,push,log,show,diff}`. |
| UI tab | `frontend/atlas/perforce-sync.tsx` (+ `main.tsx` import after `./git-tab`) | Registers `window.AtlasSCMTabOverrides.perforce` (+ label "Perforce"). When `scm_provider=perforce`, the EXISTING SCM tab auto-swaps to it (`atlasResolveScmTab` in `workspace-tool-theme.tsx`) — **no rail/tab edits**. Two panes (LEFT Local IP w/ state badges, RIGHT Perforce depot w/ rev) + center actions (＋Add / Submit▶ / ◀Sync) + bottom PENDING changelist. |
| Provisioning | `scripts/perforce_setup.sh` (idempotent) | `p4 set P4CONFIG=.p4config P4IGNORE=.p4ignore`; stream client `atlas_GOOD_IP` (Root=PROJECT_ROOT, **clobber** so `sync -f` overwrites writable files); writes `.p4config` + `.p4ignore` (excludes `.env`/`.git`/`.omc`/`.omx`/`.session`/`node_modules`/`*.db`…); `.p4config`→`.gitignore`. |

**Rebuild after UI edits:** `npm --prefix frontend/atlas run build`. The
`text/babel` override-injection (`ATLAS_SCM_UI_OVERRIDE_*`) only executes in
legacy mode; the default Vite build (no in-browser babel) needs the component
bundled — hence the `main.tsx` import. See [[babel-retirement-cutover-20260529]].

## Verified end-to-end

- Adapter live round-trip vs `localhost:1666`: submit → modify local → `sync -f` overwrite → status clean (`tests/test_scm_perforce_adapter.py::test_live_submit_sync_roundtrip`).
- Real authenticated HTTP (`admin`/`1151`): `/api/scm/pane?ip=deepdeep_ip` → provider perforce, client `atlas_GOOD_IP`, local files "new", depot empty; git provider → graceful "unsupported".
- Browser (Vite bundle): Perforce tab renders two panes; Add→Submit→depot `#1`, badge flips to ✓ same; force-sync overwrites a locally-edited file. `.p4ignore` correctly excludes `.omc/` + `.gitignore`.

## Gotchas

- After submit, p4 marks files read-only (`noallwrite`); editing outside p4 needs `chmod +w` or `p4 edit`.
- Mapping is **1:1** (`<ip>` ↔ `//GOOD_SOC/GOOD_IP/<ip>`). Renamed/relocated depot paths would need per-IP classic clients.
- Remove a test submission with `p4 obliterate -y //GOOD_SOC/GOOD_IP/<path>/...` (superuser).

## Test-suite isolation fix (.env leak) — complements [[atlas-pytest-hygiene]]

Turning on the adapter exposed a **non-hermetic test** problem:
`core/chat_responder.py::_load_dotenv_if_present()` runs at import (transitively
via `atlas_ui`) and `load_dotenv(override=False)` injects the repo `.env` into
`os.environ` for any test importing atlas_ui. (Not a pytest plugin — `-p no:dotenv`
has no effect; there is no `pytest-dotenv`.) So `.env`'s `ATLAS_SCM_PROVIDER=perforce`
(pre-existing) + `ATLAS_SCM_ADAPTER_PERFORCE` (new) changed SCM defaults under tests:

- 2 git-API tests failed because the default provider resolved to perforce (**pre-existing** — perforce in `.env` predates this work).
- 2 perforce-stub tests failed because the real adapter ran (connecting to default `perforce:1666`) instead of returning "not implemented".
- Proof: `ATLAS_SCM_PROVIDER= ATLAS_SCM_ADAPTER_PERFORCE= pytest …` → all pass.

**Fix** in `tests/conftest.py` (module top):
```python
os.environ.setdefault("ATLAS_SCM_PROVIDER", "")
os.environ.setdefault("ATLAS_SCM_ADAPTER_PERFORCE", "")
```
`setdefault` keeps an explicit shell export winning while pinning a clean
("auto", no override) baseline; `load_dotenv(override=False)` then won't replace
the present-but-empty values. Tests needing a provider set it via `monkeypatch`.
Also `tests/test_atlas_scm_ui_override.py::test_scm_ui_override_file_is_served_and_injected_before_workspace`
asserts a legacy-only marker (`data-filename="workspace.jsx"`); pinned with
`monkeypatch.setenv("ATLAS_FRONTEND_MODE","legacy")` so a present Vite `dist/`
build doesn't flip it to vite HTML.

## Broad-sweep results — integration introduces 0 regressions

- SCM suite **20 passed** (adapter, live round-trip, stub contract, git API, UI override).
- `tests/test_lib` **88 passed**. `tests/test_workflow/test_workspace_configs` **56 passed**.
- `tests/test_core` **453 passed**, 16 failed + 3 collection errors — **all pre-existing & SCM-unrelated**: failing files have zero SCM references and fail identically when `ATLAS_SCM_PROVIDER=perforce` is forced (code drift vs stale tests: compression / enhanced_rag / parallel_executor / rag_db / tools / type_validation); collection errors are stale imports (`common_ai_agent.core.hybrid_rag`, `sub_agents`, `inspect`).
- `tests/test_workflow` LLM-integration files (`test_llm_pipeline` → `llm_client.chat_completion_stream` → `time.sleep` retry) **hang/timeout** without LLM network/key — pre-existing, environment-dependent.

**pytest-timeout note:** use `--timeout=N --timeout-method=signal` (POSIX default).
Avoid `--timeout-method=thread` — it `os._exit`s the whole process on the first
timeout (no summary).
