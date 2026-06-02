# ATLAS Perforce Split-Root Computer Use QA Plan

## TL;DR
> Summary:      Verify the already-running ATLAS Perforce split-root UI through a visible desktop browser surface, with Computer Use attempted first and AppleScript plus screencapture fallback only after the `cgWindowNotFound` failures are captured. Prove Add, Edit, Sync, and Submit operate across the separate Local Root and Perforce SCM Root, then cover edge and regression criteria with agent-run evidence.
> Deliverables:
> - Computer Use readiness/fallback receipt and desktop screenshots
> - Happy-path GUI action log, screenshots, API snapshots, and p4 transcripts
> - Edge-case GUI action log for empty submit description and no-selection Edit behavior
> - Regression evidence for split roots, stream selection, focused pytest, Vitest, and frontend build
> - Cleanup receipts and ultrawork quality gate artifacts
> Effort:       Medium
> Risk:         Medium - one live Chrome session and one Perforce default changelist must be driven serially to avoid cross-test contamination.

## Scope
### Must have
- Use the active ultrawork loop: `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58`.
- Use the already-running ATLAS UI at `http://127.0.0.1:18767/?session=admin/split_ip/default`.
- Use the already-running local p4d at `localhost:17889`.
- Use Local Root `/tmp/atlas_p4_split_ui_1780364766_75182/project/split_ip`.
- Use Perforce SCM Root `/tmp/atlas_p4_split_ui_1780364766_75182/perforce_workspace`.
- Use the saved ATLAS cookie file `/tmp/atlas_p4_split_ui_1780364766_75182/cookies.txt` for API probes.
- Use the SCM root `.p4config` from `/tmp/atlas_p4_split_ui_1780364766_75182/perforce_workspace/.p4config` for p4 commands, without copying its contents into evidence.
- Attempt direct Computer Use app-state capture before any fallback:
  - `mcp__computer_use.list_apps({})`
  - `mcp__computer_use.get_app_state({"app":"Google Chrome"})`
  - `mcp__computer_use.get_app_state({"app":"Safari"})`
  - `mcp__computer_use.get_app_state({"app":"Finder"})`
- If direct Computer Use returns `cgWindowNotFound` for Chrome/Safari/Finder, use the fallback branch: visible Chrome driven by AppleScript/JXA/osascript plus `screencapture`, with every fallback action recorded as an OS-level automation receipt.
- Verify UI selectors/labels from `frontend/atlas/perforce-sync.tsx`: `#perforce-scm-root`, `#perforce-stream-select`, local row text `rtl/<file>`, depot row text `//GOOD_SOC/GOOD_IP/rtl/<file>`, buttons `＋ Add`, `✎ Edit`, `◀ Sync`, `✔ Submit`, and input placeholder `changelist description…`.
- Prove `localRoot` and `scmRoot` are different real paths and that the stream selector exposes `//GOOD_SOC/GOOD_IP` and `//GOOD_SOC/GOOD_IP_DEV`.
- Execute GUI Add, Edit, Sync, and Submit against a real p4d-backed workspace.
- Execute edge cases: empty submit description shows `description required`; Edit with no selected local row shows `select local files to edit`.
- Run focused regression tests for backend split-root behavior and frontend Perforce tab behavior.
- Capture cleanup receipts proving no p4 files remain opened by the QA run and no server processes started by the QA run were left behind.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not edit product/source files.
- Do not add test IDs or change UI implementation to make QA easier.
- Do not stop the pre-existing ATLAS server on port `18767` or p4d on port `17889`; they were not started by this QA plan.
- Do not treat API-only success as satisfying the GUI criteria.
- Do not expose `.p4config` contents, `P4PASSWD`, cookie values, or ticket material in evidence.
- Do not use stale ports or fixture paths from `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13`; those files are references only.
- Do not run mutating GUI tasks in parallel; the visible browser session and Perforce default changelist are shared.
- Do not delete submitted Perforce changelists as cleanup. Cleanup means reverting unsubmitted QA-opened files, removing temporary local-only edge files when safe, and recording that no files remain open.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest, Vitest, Vite build, Computer Use/AppleScript visible Chrome automation, curl, p4, and screencapture.
- QA policy: every task has agent-executed scenarios.
- Evidence: `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. This QA plan intentionally serializes mutating GUI tasks because the same visible Chrome app and Perforce default changelist are shared. Non-mutating checks may run in parallel after the shared env is captured.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Capture Computer Use readiness, fallback decision, env snapshot, and visible Chrome launch receipt
- Task 2: Capture live ATLAS/p4 split-root API baseline
- Task 3: Prepare unique QA fixture files and preflight changelist cleanliness

Wave 2 (after Wave 1):
- Task 4: depends [1, 2, 3] - happy-path visible GUI Add, Edit, Sync, and Submit
- Task 6: depends [1, 2] - regression API/tests for root/stream split and existing contracts

Wave 3 (after Wave 2):
- Task 5: depends [1, 2, 3, 4] - edge-case visible GUI empty submit and no-selection Edit

Wave 4 (after Wave 3):
- Task 7: depends [4, 5, 6] - cleanup receipts, ultrawork evidence summary, and quality gate

Critical path: Task 1 -> Task 3 -> Task 4 -> Task 5 -> Task 7

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 4, 5, 6, 7 | 2, 3 |
| 2    | none       | 4, 5, 6, 7 | 1, 3 |
| 3    | none       | 4, 5, 7 | 1, 2 |
| 4    | 1, 2, 3    | 5, 7 | 6 |
| 5    | 1, 2, 3, 4 | 7 | none |
| 6    | 1, 2       | 7 | 4 |
| 7    | 4, 5, 6    | final verification | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Computer Use Readiness And Fallback Receipt

  What to do: Create the evidence directory and a nonsecret environment file for later tasks. Attempt direct Computer Use app-state capture for Chrome, Safari, and Finder. If any app-state call succeeds, record `GUI_MODE=computer-use-direct`; if all fail with `cgWindowNotFound`, record `GUI_MODE=osascript-fallback` and use AppleScript plus screencapture for visible desktop browser automation in later tasks. Append `GUI_MODE` to both the probe transcript and `task-1-env.sh`. Launch/focus Chrome on the active ATLAS URL and capture a desktop screenshot.
  Must NOT do: Do not paste cookie values, `.p4config` contents, or passwords into evidence. Do not skip the Computer Use app-state attempt before fallback.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `doc/wiki/atlas-ui-playwright-screenshot-recipe-2026-05-23.md:14` - local UI QA recipe expects real system Chrome where possible.
  - Pattern:  `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/brief.md:1` - active brief requires Computer Use or OS-level GUI automation, not API-only checks.
  - Pattern:  `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/goals.json:11` - active goal ID for evidence mapping.
  - External: `https://developer.apple.com/library/archive/documentation/OpenSource/Conceptual/ShellScripting/AdvancedTechniques/AdvancedTechniques.html` - Apple documents `osascript` as the command-line interface for application scripting.
  - External: `https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/` - AppleScript controls scriptable macOS applications through Apple events.
  - External: `https://ss64.com/mac/screencapture.html` - `screencapture` command options and output file behavior.

  Acceptance criteria (agent-executable only):
  - [ ] Command `test -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-env.sh` exits 0 and the file contains `REPO_ROOT=`, `EVIDENCE_DIR=`, `ATLAS_URL=`, `LOCAL_ROOT=`, `SCM_ROOT=`, `COOKIE_FILE=`, `QA_STAMP=`, `GUI_MODE=`, and no `P4PASSWD` or cookie token.
  - [ ] Command `grep -E 'GUI_MODE=(computer-use-direct|osascript-fallback)' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-computer-use-probe.txt` exits 0.
  - [ ] Command `test -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-chrome-open.png` exits 0.
  - [ ] Command `grep -E 'mcp__computer_use.get_app_state.*(Google Chrome|Safari|Finder)' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-computer-use-probe.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Direct Computer Use succeeds or fallback is explicitly justified
    Tool:     computer-use + bash
    Steps:    Invoke `mcp__computer_use.list_apps({})`, then `mcp__computer_use.get_app_state({"app":"Google Chrome"})`, `mcp__computer_use.get_app_state({"app":"Safari"})`, and `mcp__computer_use.get_app_state({"app":"Finder"})`; append the raw result summaries to `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-computer-use-probe.txt`. Then run:
              `mkdir -p .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence`
              `printf 'REPO_ROOT=/Users/brian/Desktop/Project/brian_hw/common_ai_agent\nEVIDENCE_DIR=/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence\nATLAS_URL=http://127.0.0.1:18767\nATLAS_PAGE=http://127.0.0.1:18767/?session=admin/split_ip/default\nBASE=/tmp/atlas_p4_split_ui_1780364766_75182\nLOCAL_ROOT=/tmp/atlas_p4_split_ui_1780364766_75182/project/split_ip\nSCM_ROOT=/tmp/atlas_p4_split_ui_1780364766_75182/perforce_workspace\nCOOKIE_FILE=/tmp/atlas_p4_split_ui_1780364766_75182/cookies.txt\nQA_STAMP=cu_p4_%s\n' "$(date +%Y%m%d%H%M%S)" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-env.sh`
              If all app-state calls fail with `cgWindowNotFound`, append `GUI_MODE=osascript-fallback` to both `task-1-computer-use-probe.txt` and `task-1-env.sh`; otherwise append `GUI_MODE=computer-use-direct` to both files.
    Expected: `task-1-computer-use-probe.txt` records all Computer Use attempts and exactly one GUI mode; fallback is allowed only when `cgWindowNotFound` appears for Chrome/Safari/Finder.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-computer-use-probe.txt

  Scenario: Visible Chrome surface is available for later GUI tasks
    Tool:     bash
    Steps:    Source `task-1-env.sh`, then run `/usr/bin/osascript` to activate Google Chrome, create a window if needed, set bounds to `{80,80,1680,1080}`, set the active tab URL to `$ATLAS_PAGE`, delay two seconds, and run `/usr/sbin/screencapture -x .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-chrome-open.png`.
    Expected: Screenshot file exists and has nonzero size; `curl -fsS "$ATLAS_URL/healthz?cost=0"` returns JSON containing `"ok":true`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-chrome-open.png
  ```

  Commit: NO | Message: `test(perforce): capture computer use readiness` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-1-*]

- [ ] 2. Live Split-Root Baseline Snapshot

  What to do: Capture read-only ATLAS health, pane, p4 info, stream list, depot files, and opened-file baseline for the live fixture. Assert the ATLAS API reports `localRoot` and `scmRoot`, the p4 client root matches the SCM root, and no Perforce files are open before mutating GUI QA starts.
  Must NOT do: Do not run submit, sync, add, edit, reconcile, revert, or any mutating p4/API command in this task.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 6, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - API/Type: `src/atlas_api_git.py:145` - API responses include `cwd`, `localRoot`, and `scmRoot`.
  - API/Type: `src/atlas_api_git.py:364` - `/api/scm/pane` resolves split roots and calls `sync_state`.
  - API/Type: `core/scm_perforce.py:638` - `sync_state` returns local, depot, pending, client, stream, streams, and head.
  - Pattern:  `core/scm_perforce.py:185` - adapter preserves literal `/tmp` client root on macOS rather than resolving to `/private/tmp`.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/commands.html` - Perforce command reference for p4 command semantics.

  Acceptance criteria (agent-executable only):
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-pane-main.json >/dev/null` exits 0.
  - [ ] Command `python3 - <<'PY'\nimport json, pathlib\np=json.load(open('.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-pane-main.json'))\nassert p['ok'] is True\nassert p['localRoot'] != p['scmRoot']\nassert pathlib.Path(p['localRoot']).resolve() != pathlib.Path(p['scmRoot']).resolve()\nassert {'//GOOD_SOC/GOOD_IP','//GOOD_SOC/GOOD_IP_DEV'}.issubset(set(p.get('streams', [])))\nassert any(r.get('path','').startswith('rtl/') for r in p['local'])\nassert any(r.get('path','').startswith('//GOOD_SOC/GOOD_IP/rtl/') for r in p['depot'])\nPY` exits 0.
  - [ ] Command `grep -q 'Client root: /tmp/atlas_p4_split_ui_1780364766_75182/perforce_workspace' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-info.txt` exits 0.
  - [ ] Command `grep -q 'file(s) not opened on this client' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-opened-before.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Baseline API and p4 state is healthy
    Tool:     bash
    Steps:    Source `task-1-env.sh`; run:
              `curl -fsS "$ATLAS_URL/healthz?cost=0" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-health.json`
              `curl -fsS -b "$COOKIE_FILE" "$ATLAS_URL/api/scm/pane?ip=split_ip&provider=perforce&scm_root=$SCM_ROOT" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-pane-main.json`
              `P4CONFIG=.p4config p4 info > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-info.txt"` from `$SCM_ROOT`.
    Expected: health has `"ok":true`; pane has `"provider":"perforce"`, different `localRoot`/`scmRoot`, and both local and depot rows.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-pane-main.json

  Scenario: No pre-existing p4 opened files will contaminate GUI QA
    Tool:     bash
    Steps:    Source `task-1-env.sh`; from `$SCM_ROOT`, run `P4CONFIG=.p4config p4 opened //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-opened-before.txt" 2>&1 || true` and `P4CONFIG=.p4config p4 streams //GOOD_SOC/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-streams.txt"`.
    Expected: opened output contains `file(s) not opened on this client`; streams output contains both `//GOOD_SOC/GOOD_IP` and `//GOOD_SOC/GOOD_IP_DEV`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-p4-opened-before.txt
  ```

  Commit: NO | Message: `test(perforce): capture split root baseline` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-2-*]

- [ ] 3. Prepare Unique QA Fixture Files

  What to do: Create unique local-only files for happy Add and edge Add, modify the local copy of `rtl/ui_edit_seed.sv` for Edit, and overwrite the local copy of `rtl/ui_sync_seed.sv` so Sync has a visible restoration target. Save all relative paths in a fixture env file and capture a pre-GUI file manifest. The unique filenames must use `QA_STAMP` from Task 1.
  Must NOT do: Do not submit, open, reconcile, or delete Perforce files in this task. Do not modify files outside `$LOCAL_ROOT/rtl`.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 7] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/perforce-sync.tsx:173` - Add opens selected local rows or all non-`same` local rows.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:178` - Edit uses selected local rows and refuses empty selection.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:188` - Sync uses selected depot rows or all depot rows.
  - API/Type: `core/scm_perforce.py:724` - `_stage_local_sources` copies selected local files into mapped Perforce targets.
  - API/Type: `core/scm_perforce.py:766` - `edit_paths` opens existing targets before copying changed local content.

  Acceptance criteria (agent-executable only):
  - [ ] Command `test -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-fixture-vars.env` exits 0.
  - [ ] Command `grep -E '^ADD_REL=rtl/cu_p4_[0-9]+_add\\.sv$' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-fixture-vars.env` exits 0.
  - [ ] Command `grep -E '^EDGE_REL=rtl/cu_p4_[0-9]+_edge_no_desc\\.sv$' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-fixture-vars.env` exits 0.
  - [ ] Command `grep -q 'LOCAL_OVERWRITE_' /tmp/atlas_p4_split_ui_1780364766_75182/project/split_ip/rtl/ui_sync_seed.sv` exits 0 before Task 4 Sync runs.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Unique local QA files and modified local edit/sync targets exist
    Tool:     bash
    Steps:    Source `task-1-env.sh`; run:
              `ADD_REL="rtl/${QA_STAMP}_add.sv"; EDGE_REL="rtl/${QA_STAMP}_edge_no_desc.sv"; EDIT_REL="rtl/ui_edit_seed.sv"; SYNC_REL="rtl/ui_sync_seed.sv"; printf 'ADD_REL=%s\nEDGE_REL=%s\nEDIT_REL=%s\nSYNC_REL=%s\n' "$ADD_REL" "$EDGE_REL" "$EDIT_REL" "$SYNC_REL" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-fixture-vars.env`
              `mkdir -p "$LOCAL_ROOT/rtl"`
              `printf 'module %s_add; endmodule\n' "$QA_STAMP" > "$LOCAL_ROOT/$ADD_REL"`
              `printf 'module %s_edge_no_desc; endmodule\n' "$QA_STAMP" > "$LOCAL_ROOT/$EDGE_REL"`
              `cp "$LOCAL_ROOT/$EDIT_REL" .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-edit-before.sv`
              `cp "$LOCAL_ROOT/$SYNC_REL" .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-sync-before.sv`
              `chmod u+w "$LOCAL_ROOT/$EDIT_REL" "$LOCAL_ROOT/$SYNC_REL"`
              `printf 'module ui_edit_seed; initial begin $display("%s_EDIT"); end endmodule\n' "$QA_STAMP" > "$LOCAL_ROOT/$EDIT_REL"`
              `printf 'module ui_sync_seed; initial begin $display("LOCAL_OVERWRITE_%s"); end endmodule\n' "$QA_STAMP" > "$LOCAL_ROOT/$SYNC_REL"`
              `find "$LOCAL_ROOT/rtl" -maxdepth 1 -type f -print | sort > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-local-manifest.txt`
    Expected: The two unique files exist; edit target contains `${QA_STAMP}_EDIT`; sync target contains `LOCAL_OVERWRITE_${QA_STAMP}`; manifest includes all four relative targets.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-local-manifest.txt

  Scenario: Fixture preparation did not open Perforce files
    Tool:     bash
    Steps:    Source `task-1-env.sh`; from `$SCM_ROOT`, run `P4CONFIG=.p4config p4 opened //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-p4-opened-after-prep.txt" 2>&1 || true`.
    Expected: Output contains `file(s) not opened on this client`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-p4-opened-after-prep.txt
  ```

  Commit: NO | Message: `test(perforce): prepare split root qa fixtures` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-3-*]

- [ ] 4. Happy Path Visible GUI Add Edit Sync Submit

  What to do: Through the visible Chrome window, open the Perforce tab, set `#perforce-scm-root` to `$SCM_ROOT`, verify `#perforce-stream-select` exposes both streams, click the unique Add local row and `＋ Add`, click `rtl/ui_edit_seed.sv` plus depot row `//GOOD_SOC/GOOD_IP/rtl/ui_edit_seed.sv` and `✎ Edit`, click depot row `//GOOD_SOC/GOOD_IP/rtl/ui_sync_seed.sv` and `◀ Sync`, enter a nonblank changelist description, and click `✔ Submit`. Capture screenshots, action logs, API response logs, p4 opened before submit, p4 changes after submit, and local/depot sync content comparison.
  Must NOT do: Do not satisfy this task with curl/API POSTs alone. Do not run this task in parallel with Task 5. Do not click `Submit ▶` before the changelist description field is filled.

  Parallelization: Can parallel: YES, only with non-mutating Task 6 | Wave 2 | Blocks: [5, 7] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/perforce-sync.tsx:214` - SCM root input has id `perforce-scm-root`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:222` - stream selector has id `perforce-stream-select`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:255` - local rows are clickable divs rendered by path text.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:281` - depot rows are clickable divs rendered by depot path text.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:267` - center action buttons are `＋ Add`, `✎ Edit`, `Submit ▶`, and `◀ Sync`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:315` - changelist description input placeholder is `changelist description…`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:318` - bottom submit button is `✔ Submit`.
  - API/Type: `src/atlas_api_git.py:249` - `/api/scm/submit` requires a nonblank message and returns root fields.
  - API/Type: `src/atlas_api_git.py:388` - `/api/scm/add` passes split roots and target paths to the adapter.
  - API/Type: `src/atlas_api_git.py:438` - `/api/scm/edit` passes split roots, target paths, and stream.
  - API/Type: `src/atlas_api_git.py:332` - `/api/scm/sync` passes split roots and target paths.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/2025.1/Content/CmdRef/p4_edit.html` - p4 edit opens workspace files before submit.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/p4_submit.html` - p4 submit commits opened changelist files.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/current/Content/CmdRef/p4_sync.html` - p4 sync updates workspace contents from depot revisions.

  Acceptance criteria (agent-executable only):
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-happy-actions.json >/dev/null` exits 0 and JSON field `ok` is `true`.
  - [ ] Command `grep -q '/api/scm/add' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-network.log` exits 0.
  - [ ] Command `grep -q '/api/scm/edit' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-network.log` exits 0.
  - [ ] Command `grep -q '/api/scm/sync' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-network.log` exits 0.
  - [ ] Command `grep -q '/api/scm/submit' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-network.log` exits 0.
  - [ ] Command `grep -q 'computer-use split-root happy' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-changes-after.txt` exits 0.
  - [ ] Command `grep -q 'file(s) not opened on this client' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-opened-after-submit.txt` exits 0.
  - [ ] Command `cmp -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-sync-depot.txt /tmp/atlas_p4_split_ui_1780364766_75182/project/split_ip/rtl/ui_sync_seed.sv` exits 0.
  - [ ] Command `test -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-after-submit.png` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Add, Edit, Sync, and Submit through a visible desktop browser
    Tool:     computer-use if direct mode succeeded; otherwise bash with osascript/JXA and screencapture
    Steps:    Source `task-1-env.sh` and `task-3-fixture-vars.env`. If `GUI_MODE=computer-use-direct`, use `mcp__computer_use.get_app_state({"app":"Google Chrome"})`, then click the visible Perforce/SCM tab, local row `$ADD_REL`, button `＋ Add`, local row `$EDIT_REL`, depot row `//GOOD_SOC/GOOD_IP/rtl/ui_edit_seed.sv`, button `✎ Edit`, depot row `//GOOD_SOC/GOOD_IP/rtl/ui_sync_seed.sv`, button `◀ Sync`, type `computer-use split-root happy $QA_STAMP` into the input with placeholder `changelist description…`, and click `✔ Submit`; capture screenshots with `get_app_state` after Add, after Sync, and after Submit. If `GUI_MODE=osascript-fallback`, run a visible Chrome AppleScript/JXA driver that performs the same text/selector clicks in the front Chrome tab using DOM events, records every click selector/text into `task-4-happy-actions.json`, records `/api/scm/*` responses into `task-4-network.log`, and captures `/usr/sbin/screencapture -x` screenshots after Add, after Sync, and after Submit.
    Expected: The visible page shows the Perforce tab; the action log contains `click local:$ADD_REL`, `click button:＋ Add`, `click local:$EDIT_REL`, `click depot://GOOD_SOC/GOOD_IP/rtl/ui_edit_seed.sv`, `click button:✎ Edit`, `click depot://GOOD_SOC/GOOD_IP/rtl/ui_sync_seed.sv`, `click button:◀ Sync`, `type description`, and `click button:✔ Submit`; network log contains successful `/api/scm/add`, `/api/scm/edit`, `/api/scm/sync`, and `/api/scm/submit` calls.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-happy-actions.json

  Scenario: p4 and local/depot state prove the GUI actions hit the split roots
    Tool:     bash
    Steps:    Source `task-1-env.sh` and `task-3-fixture-vars.env`; from `$SCM_ROOT`, run:
              `P4CONFIG=.p4config p4 opened //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-opened-after-submit.txt" 2>&1 || true`
              `P4CONFIG=.p4config p4 changes -m 3 //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-changes-after.txt"`
              `P4CONFIG=.p4config p4 files "//GOOD_SOC/GOOD_IP/$ADD_REL" > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-add-file.txt"`
              `P4CONFIG=.p4config p4 print -q //GOOD_SOC/GOOD_IP/rtl/ui_sync_seed.sv > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-sync-depot.txt"`
              `curl -fsS -b "$COOKIE_FILE" "$ATLAS_URL/api/scm/pane?ip=split_ip&provider=perforce&scm_root=$SCM_ROOT" > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-pane-after-submit.json"`
    Expected: Latest p4 changes include `computer-use split-root happy $QA_STAMP`; added file exists in depot; no files are open; local sync target exactly matches depot print output; pane JSON still has different `localRoot` and `scmRoot`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-p4-changes-after.txt
  ```

  Commit: NO | Message: `test(perforce): verify split root gui happy path` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-4-*]

- [ ] 5. Edge Case Visible GUI Empty Submit And No Selection

  What to do: Use the visible Chrome Perforce tab to open the unique edge local file with `＋ Add`, attempt `✔ Submit` with an empty description, assert the UI shows `description required` and no `/api/scm/submit` request was sent, then clear selections/reload the pane and click `✎ Edit` with no selected local file, asserting `select local files to edit` and no `/api/scm/edit` request was sent. Revert the edge file afterward and record cleanup.
  Must NOT do: Do not leave the edge file opened in p4. Do not use the center `Submit ▶` button for this edge; use the bottom `✔ Submit` next to the description field.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [7] | Blocked by: [1, 2, 3, 4]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/perforce-sync.tsx:178` - Edit with no selected local row sets `select local files to edit`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:183` - Submit with blank description sets `description required`.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:184` - Submit returns before POST when description is blank.
  - Pattern:  `frontend/atlas/perforce-sync.tsx:315` - description field placeholder is `changelist description…`.
  - API/Type: `src/atlas_api_git.py:258` - backend empty submit message would be `commit message required`; this edge expects the frontend guard to prevent the POST.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/2024.1/Content/CmdRef/p4_opened.html` - p4 opened lists files open in pending changelists.

  Acceptance criteria (agent-executable only):
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-edge-actions.json >/dev/null` exits 0 and JSON field `ok` is `true`.
  - [ ] Command `grep -q 'description required' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-edge-actions.json` exits 0.
  - [ ] Command `grep -q 'select local files to edit' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-edge-actions.json` exits 0.
  - [ ] Command `! grep -q '/api/scm/submit' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-network-after-empty-submit.log` exits 0.
  - [ ] Command `! grep -q '/api/scm/edit' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-network-after-no-selection-edit.log` exits 0.
  - [ ] Command `grep -q 'file(s) not opened on this client' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-p4-opened-after-revert.txt` exits 0.
  - [ ] Command `test -s .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-edge-error.png` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Empty submit description is blocked in the visible UI
    Tool:     computer-use if direct mode succeeded; otherwise bash with osascript/JXA and screencapture
    Steps:    Source `task-1-env.sh` and `task-3-fixture-vars.env`; drive the visible Chrome tab to the Perforce UI; click local row `$EDGE_REL`; click `＋ Add`; wait for `/api/scm/add`; ensure the description input with placeholder `changelist description…` is empty; click `✔ Submit`; capture `task-5-edge-error.png` and `task-5-network-after-empty-submit.log`.
    Expected: UI action log records visible error text `description required`; no `/api/scm/submit` appears in the network log; p4 opened contains `$EDGE_REL` before cleanup.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-edge-actions.json

  Scenario: Edit with no local selection is blocked in the visible UI and edge file is reverted
    Tool:     computer-use if direct mode succeeded; otherwise bash with osascript/JXA and screencapture
    Steps:    Refresh/reload the Perforce pane to clear local selections; click `✎ Edit` without selecting any local row; capture network log `task-5-network-after-no-selection-edit.log`. Then from `$SCM_ROOT`, run `P4CONFIG=.p4config p4 revert "//GOOD_SOC/GOOD_IP/$EDGE_REL" > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-p4-revert-edge.txt" 2>&1 || true` and `P4CONFIG=.p4config p4 opened //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-p4-opened-after-revert.txt" 2>&1 || true`.
    Expected: UI action log records `select local files to edit`; no `/api/scm/edit` appears in the no-selection network log; final opened output says no files are open.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-p4-opened-after-revert.txt
  ```

  Commit: NO | Message: `test(perforce): verify split root gui edge guards` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-5-*]

- [ ] 6. Regression API And Test Suite Verification

  What to do: Run read-only API assertions for main and dev streams, then focused backend/frontend regression tests and frontend build. The API assertions must use the saved cookie file, prove root separation with realpath comparison, and prove both streams are exposed. The tests must run from the correct directories.
  Must NOT do: Do not run the old live QA shell script from `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13`; it targets different ports and roots. Do not run tests from the wrong package root.

  Parallelization: Can parallel: YES, only with Task 4 | Wave 2 | Blocks: [7] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Test:     `tests/test_scm_perforce_adapter.py:176` - selected stream returns two streams and maps to `atlas_GOOD_IP_DEV`.
  - Test:     `tests/test_scm_perforce_adapter.py:202` - local root and depot scope stay independent.
  - Test:     `tests/test_scm_perforce_adapter.py:235` - depot files sync into a separate local root.
  - Test:     `tests/test_scm_perforce_adapter.py:270` - Add/open copies local files to a Perforce target.
  - Test:     `tests/test_scm_perforce_adapter.py:304` - Edit opens existing target before copying.
  - Test:     `tests/test_atlas_git_api.py:192` - `/api/scm/edit` passes `local_root`, `scmRoot`, `targetPaths`, and stream to the adapter.
  - Test:     `frontend/atlas/__tests__/perforce-sync.test.tsx:69` - frontend Edit payload includes provider, IP, SCM root, paths, and target paths.
  - Test:     `frontend/atlas/__tests__/perforce-sync.test.tsx:94` - stream selection reloads pane and propagates stream to actions.
  - Test:     `frontend/atlas/__tests__/perforce-sync.test.tsx:118` - Sync uses depot paths when no depot row is selected.
  - Pattern:  `frontend/atlas/package.json:5` - frontend test/build scripts live under `frontend/atlas`.
  - Pattern:  `frontend/atlas/vitest.config.js:4` - Vitest uses jsdom config for component tests.
  - External: `https://playwright.dev/docs/browsers` - official Playwright docs for real Chrome channels, if a browser fallback runner needs headed Chrome support.

  Acceptance criteria (agent-executable only):
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-main.json >/dev/null` exits 0.
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-dev.json >/dev/null` exits 0.
  - [ ] Command `grep -q 'passed' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pytest.txt` exits 0.
  - [ ] Command `grep -q 'Test Files' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-vitest.txt` exits 0.
  - [ ] Command `grep -q 'built in' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-vite-build.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: API root and stream regression assertions pass
    Tool:     bash
    Steps:    Source `task-1-env.sh`; run:
              `curl -fsS -b "$COOKIE_FILE" "$ATLAS_URL/api/scm/pane?ip=split_ip&provider=perforce&scm_root=$SCM_ROOT" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-main.json`
              `curl -fsS -b "$COOKIE_FILE" "$ATLAS_URL/api/scm/pane?ip=split_ip&provider=perforce&stream=%2F%2FGOOD_SOC%2FGOOD_IP_DEV&scm_root=$SCM_ROOT" > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-dev.json`
              `python3 - <<'PY'\nimport json, pathlib\nmain=json.load(open('.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-main.json'))\ndev=json.load(open('.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-dev.json'))\nassert main['provider']=='perforce'\nassert pathlib.Path(main['localRoot']).resolve() != pathlib.Path(main['scmRoot']).resolve()\nassert main['scmRoot'].endswith('/perforce_workspace')\nassert {'//GOOD_SOC/GOOD_IP','//GOOD_SOC/GOOD_IP_DEV'}.issubset(set(main['streams']))\nassert dev['stream'] == '//GOOD_SOC/GOOD_IP_DEV'\nassert dev['client'] == 'atlas_GOOD_IP_DEV'\nPY`
    Expected: Both pane JSON files are valid; main root realpaths differ; dev stream selects `atlas_GOOD_IP_DEV`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pane-main.json

  Scenario: Focused backend/frontend tests and build pass
    Tool:     bash
    Steps:    Run `python3 -m pytest -q tests/test_scm_perforce_adapter.py::test_sync_state_accepts_selected_stream_and_lists_available_streams tests/test_scm_perforce_adapter.py::test_sync_state_keeps_local_root_and_depot_scope_independent tests/test_scm_perforce_adapter.py::test_sync_paths_copies_depot_filespecs_into_local_root tests/test_scm_perforce_adapter.py::test_open_paths_copies_local_file_to_perforce_target tests/test_scm_perforce_adapter.py::test_edit_paths_opens_existing_target_before_copy tests/test_atlas_git_api.py::test_scm_edit_route_uses_perforce_adapter > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pytest.txt 2>&1`; run `npm --prefix frontend/atlas test -- __tests__/perforce-sync.test.tsx > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-vitest.txt 2>&1`; run `npm --prefix frontend/atlas run build > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-vite-build.txt 2>&1`.
    Expected: pytest exits 0 and reports passed tests; Vitest exits 0 and reports the Perforce component test file; build exits 0 and reports `built in`.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-pytest.txt
  ```

  Commit: NO | Message: `test(perforce): verify split root regressions` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-6-*]

- [ ] 7. Cleanup Receipts And Ulw Evidence Closure

  What to do: Re-check p4 opened state, revert any remaining QA-opened files, record that the pre-existing ATLAS and p4d servers were not stopped by QA, write cleanup receipts, update the active `goals.json` criteria with captured evidence paths, and write a final quality gate JSON summarizing C001/C002/C003. This is QA-state/evidence closure only.
  Must NOT do: Do not stop port `18767` or `17889`. Do not mark the ultrawork goal complete until final verification F1-F4 approves and the caller explicitly says okay. Do not delete submitted changelists from Task 4.

  Parallelization: Can parallel: NO | Wave 4 | Blocks: [final verification] | Blocked by: [4, 5, 6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/goals.json:15` - C001/C002/C003 criteria are pending and need captured evidence.
  - Pattern:  `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13/evidence/quality-gate.json` - prior Perforce QA used a JSON quality gate summary.
  - Pattern:  `.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13/evidence/C001-cleanup.txt` - prior Perforce QA used cleanup receipts.
  - External: `https://help.perforce.com/helix-core/server-apps/cmdref/2024.1/Content/CmdRef/p4_opened.html` - p4 opened is the direct check for pending opened files.

  Acceptance criteria (agent-executable only):
  - [ ] Command `grep -q 'file(s) not opened on this client' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-p4-opened-final.txt` exits 0.
  - [ ] Command `python3 -m json.tool .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/quality-gate.json >/dev/null` exits 0.
  - [ ] Command `python3 - <<'PY'\nimport json\np=json.load(open('.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/quality-gate.json'))\nassert p['status']=='passed'\nassert set(p['criteria']) == {'C001','C002','C003'}\nassert all(p['criteria'][k]['status']=='passed' for k in p['criteria'])\nPY` exits 0.
  - [ ] Command `grep -q 'pre-existing atlas port 18767 preserved' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-cleanup.txt` exits 0.
  - [ ] Command `grep -q 'pre-existing p4 port 17889 preserved' .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-cleanup.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Cleanup leaves no pending p4 files and preserves pre-existing servers
    Tool:     bash
    Steps:    Source `task-1-env.sh` and `task-3-fixture-vars.env`; from `$SCM_ROOT`, run `P4CONFIG=.p4config p4 revert "//GOOD_SOC/GOOD_IP/$EDGE_REL" > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-revert-edge-repeat.txt" 2>&1 || true`; run `P4CONFIG=.p4config p4 opened //GOOD_SOC/GOOD_IP/... > "$OLDPWD/.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-p4-opened-final.txt" 2>&1 || true`; run `lsof -nP -iTCP:18767 -sTCP:LISTEN > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-atlas-listener.txt 2>&1 || true`; run `lsof -nP -iTCP:17889 -sTCP:LISTEN > .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-p4-listener.txt 2>&1 || true`; write `task-7-cleanup.txt` with lines `pre-existing atlas port 18767 preserved`, `pre-existing p4 port 17889 preserved`, `no QA-started process to stop`, and the final opened-file result.
    Expected: p4 opened final says no files are open; listener files show the pre-existing servers still listening; cleanup receipt states no QA-started process was stopped.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-cleanup.txt

  Scenario: Ulw criteria evidence is summarized without declaring completion early
    Tool:     bash
    Steps:    Write `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/quality-gate.json` with `status:"passed"` and criteria C001, C002, C003 mapping to Task 4, Task 5, and Task 6 evidence files. Update `.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/goals.json` so C001/C002/C003 have `capturedEvidence` paths and `status:"passed"`, but keep the goal-level `status` unchanged until F1-F4 and caller okay.
    Expected: quality gate JSON validates; goals JSON references concrete evidence paths; goal-level status is not set to complete in this task.
    Evidence: .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/quality-gate.json
  ```

  Commit: NO | Message: `test(perforce): close split root qa evidence` | Files: [.omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/task-7-*, .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/evidence/quality-gate.json, .omo/ulw-loop/019e8515-13e8-7591-bec9-79c442364d58/goals.json]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/computer-use-perforce-split-root-qa.md`.
- This QA plan marks implementation tasks `Commit: NO` because the requested deliverables are evidence and ultrawork state, not product source changes. If a maintainer requires committing evidence, use one commit after F1-F4: `test(perforce): capture split root gui qa evidence`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
