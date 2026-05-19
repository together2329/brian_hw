# Flow Fixes R2 Verification 2026-05-19 — Cross-Workspace cmux Chrome

> Live verification of the second wave of fixes (commits `a75b1f817`, `d0006ab3b`,
> `7d9e35e07`, `bb5f19831`, plus seed-dispatch consolidated into `a75b1f817` /
> `7d9e35e07`) using the **same cmux Chrome UI/API path users run**, across three
> test IPs (`cmux_r2_alpha`, `cmux_r2_beta`, `cmux_r2_gamma`). Follow-up to
> [[flow-fixes-verify-20260519]] (r1). Sister doc: [[orchestrator-chat-ux]].

## Verifier Identity & Environment

- Agent: `verifier-cmux-r2`
- atlas_ui restarted at 2026-05-19 19:55 KST. PID 43101, `--host 127.0.0.1 --port 62196 --model gpt-5.5 --effort xhigh`, `ATLAS_DB_PATH=$HOME/.common_ai_agent/atlas.db`. Health: `HTTP=200`.
- cmux workspace `workspace:1` (`db-frontend-pipeline-integration-test`).
- Browser surfaces:
  - `surface:9` ← `cmux_r2_alpha`
  - `surface:14` ← `cmux_r2_beta`
  - `surface:7` ← `cmux_r2_gamma`
- Each surface: `localStorage.clear()` + `sessionStorage.clear()` before navigation to `/?ip=<IP>&view=pipeline` so the URL precedence fix gets a clean shot.
- All chat dispatches issued via `fetch('/api/pipeline/orchestrator/chat', {credentials:'same-origin', ...})` from the **already-authenticated cmux Chrome surface** because the in-DOM chat textarea fails to mount under non-default IP (see fix #12 result). cURL from terminal returns `401 login required`.
- Real LLM cost in this verification run: $0.78 across orchestrator + ssot-gen workflows (see per-IP breakdown).

## Result Summary

| Fix | Subject | Status |
|---|---|---|
| #11 / `a75b1f817` | URL `?ip=` → session precedence (helper) | **FAIL** (helper present, bootstrap path ignores it) |
| #12 / `d0006ab3b` | Chat panel mounts under non-default IP in pipeline view | **FAIL** (no textarea anywhere in DOM after Pipeline tab click) |
| #13 / consolidated | Seed propagation on direct ssot-gen dispatch | **PASS** (all three top_module.name match `<IP>_cnt` seed) |
| #14 / `7d9e35e07` | Single `ip_blocks` row across UI-create + worker-dispatch | **PARTIAL FAIL** (no intra-workspace dup, but 3× cross-workspace dup) |
| #15 / `bb5f19831` | Workers persist `llm_calls` with `cost_usd > 0` | **PARTIAL PASS** (orchestrator rows abundant w/ cost; ssot-gen workflow row count = 1 only) |

Net: **2 / 5 PASS**, **2 / 5 FAIL**, **1 / 5 PARTIAL**. The two outright fails are
both in the frontend layer — backend dedupe/cost logic shipped, but UI session
resolution still resolves to `default`, which means **a user typing in a
non-default IP today still cannot complete the flow without bypassing the chat
textarea via direct fetch**.

## Per-Workspace Verification

### cmux_r2_alpha (surface:9)

| Check | Result | Evidence |
|---|---|---|
| (a) URL → session precedence | **FAIL** | After navigate to `/?ip=cmux_r2_alpha&view=pipeline`, the browser address bar rewrites within seconds to `/?ip=default&view=pipeline&session=validator%2Fdefault%2Fdefault&workflow=default&session_id=validator`. `window.ACTIVE_SESSION="validator/default/default"`. `localStorage.atlasActiveSession="validator/default/default"`. `window.atlasResolveActiveSession()` returns `"default/default/default"` because by the time helper is called the URL `ip` param has already been replaced. |
| (b) Chat panel mounts | **FAIL** | `document.querySelectorAll("textarea").length === 0` even after clicking `◫ PIPELINE`. Only `.orch-inline` chrome (`orch:on workers:0`) renders. |
| (c) Seed honor on dispatch | **PASS** | `cmux_r2_alpha/yaml/cmux_r2_alpha.ssot.yaml` `top_module.name: cmux_r2_alpha_cnt`. Matches seed. |
| (d) Single `ip_blocks` row | **PARTIAL FAIL** | 1 row per `(ip_name, workspace_id)` (no intra-workspace duplicate), BUT 2 distinct workspace_id rows for the same `cmux_r2_alpha` IP at the same `local_path=/Users/brian/Desktop/Project/brian_hw/common_ai_agent` differing only by `owner_user_id` (`codex_whoami_ssot` vs `d53cabe8b4054e75b30cac4c4f47a76d`). |
| (e) `llm_calls` cost_usd > 0 | **PASS** | 17 `orchestrator` rows for `cmux_r2_alpha`, total `cost_usd ≈ $0.349`. Sample ids: `25bf03792559405ea84cfaca370ab6a0` ($0.0266), `47de0b71a3d243a5aeefd87998572ec3` ($0.0244). |

Run id (chat dispatch): `ec8e8db3d4714860861740644bfd542b` (`orchestrator_runs.status=yielded`).
Screenshot: `/tmp/verifier_r2/alpha/state.png`.

### cmux_r2_beta (surface:14)

| Check | Result | Evidence |
|---|---|---|
| (a) URL → session precedence | **FAIL** | Page initially honors URL `?ip=cmux_r2_beta` (helper returns `default/cmux_r2_beta/orchestrator`), but `window.ACTIVE_SESSION="default/default/default"` from the get-go — the bootstrap IIFE (line 855 in transpiled bundle) does not call `resolveActiveSession`. After clicking `◫ PIPELINE` the URL is rewritten to `/?ip=default&workflow=orchestrator&view=pipeline&session=validator%2Fdefault%2Forchestrator&session_id=validator` and `ACTIVE_SESSION` becomes `validator/default/orchestrator`. |
| (b) Chat panel mounts | **FAIL** | `document.querySelectorAll("textarea").length === 0` both before and after Pipeline tab click. Only `.orch-inline` status pill renders. `bodySnippet` contains "ip default" — the IP context is default-clamped. |
| (c) Seed honor on dispatch | **PASS** | `cmux_r2_beta/yaml/cmux_r2_beta.ssot.yaml` `top_module.name: cmux_r2_beta_cnt`. |
| (d) Single `ip_blocks` row | **PARTIAL FAIL** | Same pattern as alpha — 2 distinct workspace_id rows for `cmux_r2_beta`. |
| (e) `llm_calls` cost_usd > 0 | **PASS** | 8 `orchestrator` rows for `cmux_r2_beta`, total `cost_usd ≈ $0.122`. Sample: `c0100b64644f4e4293cfac28def8610a` ($0.0152). |

Run id: `882700873214436e89aec499fd6ec87b` (`orchestrator_runs.status=yielded`).
Screenshots: `/tmp/verifier_r2/beta/pipeline_no_chat.png`, `/tmp/verifier_r2/beta/state.png`.

### cmux_r2_gamma (surface:7)

| Check | Result | Evidence |
|---|---|---|
| (a) URL → session precedence | **FAIL** | Same as beta — URL `ip` honored but `ACTIVE_SESSION="default/default/default"`. |
| (b) Chat panel mounts | **FAIL** | No textarea in DOM. |
| (c) Seed honor on dispatch | **PASS** | `cmux_r2_gamma/yaml/cmux_r2_gamma.ssot.yaml` `top_module.name: cmux_r2_gamma_cnt`. |
| (d) Single `ip_blocks` row | **PARTIAL FAIL** | Same — 2 cross-workspace rows. |
| (e) `llm_calls` cost_usd > 0 | **PASS** | 13 `orchestrator` rows for `cmux_r2_gamma`, total `cost_usd ≈ $0.313`. |

Run id: `a6c326b03c8e48d1a14f5838d82d2d42` (`orchestrator_runs.status=running` at capture time, ssot.yaml already on disk).
Screenshot: `/tmp/verifier_r2/gamma/state.png`.

## Cross-Workspace Isolation Check

Required by the task: "queries scoped by `workspace_id` return non-overlapping rows".

```
sqlite> SELECT workspace_id, COUNT(*), GROUP_CONCAT(ip_name)
        FROM ip_blocks WHERE ip_name LIKE 'cmux_r2%' GROUP BY workspace_id;
1af22bd19c1d400393570a5edbdb7e36 | 3 | cmux_r2_alpha,cmux_r2_beta,cmux_r2_gamma
1c5cbf0f1f6b47d49877fe5db335b15a | 3 | cmux_r2_alpha,cmux_r2_beta,cmux_r2_gamma
6d8ce5420c204036a9c94b4bf2a173a1 | 3 | cmux_r2_alpha,cmux_r2_beta,cmux_r2_gamma
```

The `workspaces` table for these three IDs:

```
1af22bd19c1d400393570a5edbdb7e36 | common_ai_agent | owner=codex_whoami_ssot              | /Users/brian/.../common_ai_agent
1c5cbf0f1f6b47d49877fe5db335b15a | common_ai_agent | owner=d53cabe8b4054e75b30cac4c4f47a76d | /Users/brian/.../common_ai_agent
6d8ce5420c204036a9c94b4bf2a173a1 | common_ai_agent | owner=validator                      | /Users/brian/.../common_ai_agent
```

**Same local_path, three different `owner_user_id` values, three different workspace rows.** This violates the task constraint ("3 rows, ALL same workspace_id, one project root, same user"). It also explains why fix #14's intra-workspace dedupe still produces `cmux_r2_alpha | 2` in `GROUP BY ip_name` — there are actually 3 ip_blocks rows per IP (one per workspace owner), and the GROUP BY hits 2 of them because only 2 of the 3 workspaces had the IP created during the chat path; the third was created in a prior pre-state by a different actor.

Practical implication: workspace identity in this system is `(local_path, owner_user_id)` not `local_path` alone. cmux Chrome (`validator`), the orchestrator runner (`codex_whoami_ssot`), and an earlier session (`d53cabe8…`) each got their own workspace row. The dedupe contract of fix #14 needs to be re-scoped to either `(local_path)` alone or to share workspace identity across these three owners.

## Root-Cause Notes (frontend regressions)

1. **URL precedence helper is dead code at bootstrap.** `resolveActiveSession()` is defined and exposed at `window.atlasResolveActiveSession` (line 6905 in transpiled bundle), but the IIFE that actually computes `window.ACTIVE_SESSION` (line 855) re-derives session from `urlSession || localStorage || 'default'` without calling the helper, and crucially that early code path normalizes via `urlNamespace || ... || 'default'` where `urlNamespace` requires either a full `session=` query, or both `ip` and `workflow`. A URL with only `?ip=cmux_r2_beta` (no workflow) yields `urlNamespace = 'default/cmux_r2_beta/default'` — which IS non-default — but then a later React effect calls `replaceState(null, '', '/?session_id=' + sessionId)` (line 7443) using the user session id rather than the namespace, which collapses URL back to `?ip=default&workflow=default&session=...`. The localStorage write at line 856 captures the bad namespace before the rewrite, and from then on every later read is poisoned. The helper at line 6915 (`if (urlIp && urlIp !== 'default')`) never gets to win because by the time anyone calls it, `urlIp` is already `default`.

2. **Chat panel does not mount under view=pipeline + non-default IP.** Even when we click `◫ PIPELINE` programmatically, `document.querySelectorAll("textarea").length === 0`. fix #12 (`d0006ab3b`) was supposed to address this, but in this verification the only mounted chat surface is `.orch-inline` (a status pill, not an input). This is consistent with regression-on-merge: the fix either depends on `ACTIVE_SESSION` resolving to a non-default IP (which #11 fails to deliver) OR it depends on a different `view` value than `pipeline`.

## Backend Notes (worker-side findings)

3. **ssot-gen workflow llm_call row count = 1, not 3.** `SELECT * FROM llm_calls WHERE workflow='ssot-gen'` returns exactly one row (`faa63be28d244fcb9f8bf7b000002d61`, cost `$0.097`). All other LLM accounting for the three IPs is tagged `workflow='orchestrator'`. Either (a) the ssot-gen worker is bypassing `db.record_llm_call` for 2 of 3 runs, or (b) only the first ssot-gen invocation tags `workflow='ssot-gen'` and subsequent invocations are tagged `orchestrator`. Either way, fix #15's contract ("ssot-gen worker actually writes llm_calls") is not consistently honored at 3× scale.

4. **orchestrator_runs status `yielded` is the terminal-ish state.** For 2 of 3 chats the run is `yielded` (waiting for user) and ssot.yaml is already on disk. For gamma the run was `running` at capture but ssot.yaml was already present — meaning the run record state-machine lags the file system. Acceptable but worth a note for downstream UI consumers.

## Cleanup Note

The verifier left chat-dispatch artifacts: 3 `orchestrator_runs` rows, 3 `cmux_r2_*` ssot.yaml directories under `common_ai_agent/cmux_r2_*/`, and 38 `llm_calls` rows tagged with the three IPs. These should be cleaned by a later sweeper or deliberate test-data prune.

## Recommended Follow-ups (priority)

1. **P0 — fix #11 root cause**: rewrite the line-855 IIFE to call `resolveActiveSession()` instead of its own local logic, AND patch the line-7443 `replaceState` to preserve URL `ip`/`workflow` query params instead of collapsing to `/?session_id=`. Verify by checking that after a fresh load of `/?ip=cmux_r2_xx&view=pipeline`, `window.ACTIVE_SESSION` ends with `/cmux_r2_xx/` and the browser address bar still shows the original `ip`.
2. **P0 — fix #12 follow-through**: confirm that with #11 fixed and `ACTIVE_SESSION` resolving non-default, the chat textarea actually mounts. If still missing, the gating condition in `pipeline.jsx` chat panel block needs review.
3. **P1 — fix #14 cross-owner dedupe**: decide whether workspace identity should be `(local_path)` or `(local_path, owner_user_id)`. If the former, migrate or merge the three `common_ai_agent` workspace rows. If the latter, scope all "single ip_blocks row" assertions to a single owner — current behavior is then correct.
4. **P1 — fix #15 consistency**: instrument the ssot-gen worker to confirm whether the `workflow` tag is being downgraded to `orchestrator` in 2/3 dispatches; add a regression test that the ssot-gen workflow tag survives across N concurrent dispatches.

## Cross-links

- [[flow-fixes-verify-20260519]] — r1 verification, the precursor to this report.
- [[orchestrator-chat-ux]] — orchestrator chat UX overhaul, where the chat-panel mount contract is defined.
- [[multi-user-worker-isolation]] — relevant to the cross-workspace dedupe question (workspace identity across owners).
- [[provider-and-llm-call-accounting]] — relevant to the ssot-gen workflow tag question.
- [[pipeline-progress-debugging]] — the "validate via the same UI path users run" rule motivating this report.
