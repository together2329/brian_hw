# Flow Fixes R3 Verify — Real Textarea Typing E2E (2026-05-19)

Live cmux-Chrome verification of the four R3 follow-up fixes shipped after the
[[flow-fixes-r2-verify-20260519]] gaps. Unlike R1/R2 (which used `fetch` bypass
to drive `/api/...`), R3 was driven exclusively by **real keystroke input** into
the rendered `textarea.orch-chat-input` element via `cmux browser.type` /
`browser.press`, then the cost was paid by the live orchestrator/ssot-gen
pipeline.

Verifier: agent `verifier-r3`. Test IP: `cmux_p0_final`. Single workspace
(no need for 3 IPs — focus is end-to-end UI plumbing).

Cross-refs: [[flow-fixes-r2-verify-20260519]], [[orchestrator-chat-ux]],
[[atlas-browser-control-runbook]].

## Landed R3 commits under test

| Task | Commit | Fix |
|---|---|---|
| #17 | `f63e1324a` | bootstrap IIFE/replaceState preserves URL `ip`/`workflow` instead of collapsing to default |
| #18 | `440c9a896` | chat textarea always mounts under non-default IP |
| #19 | `74086629a` | canonical `owner_user_id` resolution across chat + worker |
| #20 | `68b9559fb` | worker `llm_calls` rows tagged with correct `workflow` from env |

## Backend restart for fix pickup

```
kill <atlas_ui pid>  # PID 47908 (etime 10:59) before restart
nohup env ATLAS_DB_PATH="$HOME/.common_ai_agent/atlas.db" \
  python3 -u src/atlas_ui.py --host 127.0.0.1 --port 62196 \
  --model gpt-5.5 --effort xhigh \
  > .session/canonical_atlas_ui/atlas_ui.log 2>&1 &
```

Restart confirmed: PID 12126, `HTTP=200`, multi-user with
`process_per_session=on`.

## Verification scenario

1. cmux Chrome `surface:9` already attached to ATLAS.
2. `cmux rpc browser.navigate` → `http://127.0.0.1:62196/?ip=cmux_p0_final`.
3. Wait 6 s for bootstrap/replaceState.
4. Assert URL preservation.
5. Assert `textarea.orch-chat-input` rendered + enabled in DOM.
6. `cmux rpc browser.focus` textarea, then `cmux rpc browser.type` with the
   seed sentence "make an 8-bit counter with sync reset and enable, top
   module name: p0_cnt." — this is a **real keystroke stream**, no
   `value=…` setter, no `dispatchEvent` shim.
7. Read back `textarea.value` to confirm typing landed.
8. `cmux rpc browser.press key=Enter` to submit (no shift).
9. Wait for backend round-trip, then poll DOM bubbles + `~/.common_ai_agent/atlas.db`.
10. Inspect `cmux_p0_final/yaml/cmux_p0_final.ssot.yaml`.

## Step-by-step result

| Step | Goal | Verdict | Evidence |
|---|---|---|---|
| 1 | URL preservation under `/?ip=cmux_p0_final` | **PASS** | `location.search` = `?ip=cmux_p0_final&session=validator%2Fcmux_p0_final%2Forchestrator&session_id=validator&workflow=orchestrator`. No collapse to `?ip=default`. |
| 2 | Pipeline screen mounted | **PASS** (selector caveat) | `.atlas-pipeline` selector returns null, but textarea ancestor chain shows `pipe-screen.arch-screen > pipe-board > pipe-col-right > pipe-orch-chat-shell orch-chat-panel > orch-chat-input-row > textarea.orch-chat-input`. The pipeline UI **is** rendered; the spec-quoted class name was wrong. |
| 3 | textarea exists + enabled | **PASS** | `document.querySelector("textarea.orch-chat-input")` returns element; `disabled === false`. Screenshot `/tmp/verifier_r3/atlas_post_submit.png`. |
| 4 | Real keystroke typing lands in `textarea.value` | **PASS** | After `browser.type`, `textarea.value === "make an 8-bit counter with sync reset and enable, top module name: p0_cnt."` |
| 4b | Enter submit → textarea clears + bubble appears | **PASS** | Post-Enter `textarea.value.length === 0`; `.md-bubble` count=4, `.md-user`=1, `.md-agent`=1 within 8 s. |
| 5a | `ip_blocks` single canonical row for `cmux_p0_final` | **PARTIAL FAIL** | 2 rows under different `workspace_id`s (`1c5cbf...` and `9d33c3...`), both `ip_name='cmux_p0_final'`, both `status='active'`. Fix #19 corrected the `owner_user_id` collapsing but **workspace identity** is still bifurcating — `(workspace_id, ip_name)` UNIQUE constraint accepts both because the *workspace_id* differs. See "Follow-up #1". |
| 5b | `llm_calls` rows include `workflow='ssot-gen'` with `cost_usd > 0` | **PASS** | `SELECT workflow, COUNT(*), SUM(cost_usd) FROM llm_calls GROUP BY workflow` yields `ssot-gen|1|0.09667`, `orchestrator|71|1.569143`, `rtl-gen|1|0.086585`. Fix #20 working. |
| 5c | `workflow_runs` row for ssot-gen against this IP | **PASS** | Most recent row: `ssot-gen|running|orchestrator_chat|<ip_id 1fd78985…>` — `trigger_source='orchestrator_chat'`, `ip_id` matches first `ip_blocks` row for `cmux_p0_final`. |
| 6 | SSOT honors seed `top_module.name = p0_cnt` | **PASS** | `cmux_p0_final/yaml/cmux_p0_final.ssot.yaml` → `top_module: { name: p0_cnt, file: rtl/p0_cnt.sv }`. Seed text from real textarea typing reached the ssot-gen worker and produced a faithful artifact. |

Summary: **6/7 PASS, 1 PARTIAL FAIL** (`ip_blocks` workspace-id duplication —
distinct from R2's `owner_user_id` duplication; fix #19 fixed only half the
identity collapse).

## Evidence files

- `/tmp/verifier_r3/atlas_post_submit.png` — post-Enter ATLAS screenshot
- `/tmp/verifier_r3/ip_blocks.txt` — both rows for `cmux_p0_final`
- `/tmp/verifier_r3/llm_calls_summary.txt` — workflow distribution
- `/tmp/verifier_r3/llm_calls_recent.txt` — last 12 llm_calls
- `/tmp/verifier_r3/workflow_runs_recent.txt` — last 5 workflow_runs full rows
- `/tmp/verifier_r3/ssot_head.yaml` — head of generated ssot.yaml (top_module=p0_cnt)
- `/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.session/canonical_atlas_ui/atlas_ui.log` — backend log
- Generated SSOT: `cmux_p0_final/yaml/cmux_p0_final.ssot.yaml` + `cmux_p0_final.ssot.provenance.json`

## Responsibility-boundary assessment

| Component | Verdict |
|---|---|
| Frontend (`workspace.jsx`, `pipeline.jsx`) | **GREEN** — URL preserved, textarea mounts, keystrokes accepted, submission fires, bubble renders. R3 frontend fixes #17/#18 confirmed live. |
| Backend orchestrator/worker dispatch | **GREEN** — orchestrator routed chat → ssot-gen worker; workflow tag correct; cost recorded. R3 backend fix #20 confirmed live. |
| DB identity (workspace + IP) | **YELLOW** — `owner_user_id` collapse fix landed (#19) but `workspace_id` still bifurcates per session/process. UNIQUE `(workspace_id, ip_name)` does not protect against multiple workspace_ids for the same logical IP. |
| Worker output fidelity | **GREEN** — seed `p0_cnt` from real keystrokes reached SSOT YAML. |

## Follow-ups

1. **`workspace_id` canonicalization (P1, blocks data-model honesty).** Even with the fix-19 owner change, `ip_blocks` is forking on `workspace_id`. Either (a) collapse the workspace identity key for the same `local_path`, or (b) replace UNIQUE `(workspace_id, ip_name)` with UNIQUE `(local_path_canonical, ip_name)` so identical IPs converge. See `src/atlas_api_jobs.py` + `core/atlas_db.py` workspace-ensure paths.
2. **`.atlas-pipeline` class consistency (P2, cosmetic).** Test specs reference `.atlas-pipeline`, real DOM uses `pipe-screen arch-screen`. Either rename to match expectation or update the runbook in [[atlas-browser-control-runbook]].
3. **`browser.eval` long-string return timeouts (P3, infra).** Long innerText returns from cmux RPC frequently time out. Base64-encode + decode locally is a reliable workaround; consider documenting in [[atlas-browser-control-runbook]].

## Conclusion

R3 is the first round where the full UI plumbing — URL preservation, chat
textarea mounting, real keystroke input, submission round-trip, worker
dispatch with correct workflow tagging, and seed-honoring SSOT generation —
worked **end-to-end through the visible product surface**, without any
`fetch` bypass. The one remaining gap (`workspace_id` duplication) is a
narrow DB-identity issue, not a UI/backend contract failure.
