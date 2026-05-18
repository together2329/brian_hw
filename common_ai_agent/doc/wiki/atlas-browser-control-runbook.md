# ATLAS Browser Control Runbook

This page is the concrete handoff for agents that must operate the visible
ATLAS UI, not just call backend scripts. Use it when the user asks for "web
browser", "ATLAS UI", "I want to see it", or visible click/type validation.

## Rule

Use the Codex in-app Browser (`iab`) for visible product-flow validation. Do not
substitute `open`, a hidden Playwright browser, or backend-only API calls when
the user wants to see ATLAS. Backend API checks are useful evidence, but the
visible browser is the product surface.

## Start Or Reuse ATLAS UI

From `common_ai_agent/`, start the UI if no server is listening:

```bash
python3 -u src/atlas_ui.py --host 127.0.0.1 --port 62196 --model gpt-5.5 --effort xhigh
```

For orchestrator/worker tests, preserve the worker URL environment from the
current run. A typical live setup has:

```bash
ATLAS_DB_PATH=/Users/brian/Desktop/Project/brian_hw/common_ai_agent/atlas.db
WORKER_URL_SSOT_GEN=http://127.0.0.1:5621
WORKER_URL_FL_MODEL_GEN=http://127.0.0.1:5622
WORKER_URL_RTL_GEN=http://127.0.0.1:5623
WORKER_URL_LINT=http://127.0.0.1:5624
WORKER_URL_TB_GEN=http://127.0.0.1:5625
WORKER_URL_SIM=http://127.0.0.1:5626
WORKER_URL_COVERAGE=http://127.0.0.1:5627
WORKER_URL_SIM_DEBUG=http://127.0.0.1:5628
WORKER_URL_SYN=http://127.0.0.1:5629
WORKER_URL_STA=http://127.0.0.1:5630
WORKER_URL_PNR=http://127.0.0.1:5631
WORKER_URL_STA_POST=http://127.0.0.1:5632
```

Check the listener before claiming the UI is live:

```bash
lsof -nP -iTCP:62196 -sTCP:LISTEN
```

## Connect To The In-App Browser

If `mcp__node_repl__js` is not visible, use tool discovery for
`node_repl browser playwright in-app browser current tab`. Then run this guarded
bootstrap once in the JS tool. The Browser plugin path can move between
installations; resolve it from the Browser skill path and use its sibling
`scripts/browser-client.mjs`.

```js
if (!globalThis.agent) {
  const { setupAtlasRuntime } = await import(
    "/Users/brian/.codex/plugins/cache/openai-bundled/browser-use/0.1.0-alpha2/scripts/browser-client.mjs"
  );
  await setupAtlasRuntime({ globals: globalThis });
}
if (!globalThis.browser) {
  globalThis.browser = await agent.browsers.get("iab");
}
await browser.nameSession("ATLAS visible validation");
if (typeof tab === "undefined" || !globalThis.tab) {
  globalThis.tab = await browser.tabs.selected();
  if (!globalThis.tab) globalThis.tab = await browser.tabs.new();
}
```

Keep reusing the top-level `tab`. Do not redeclare it with `const tab = ...` in
later cells.

## Open The Exact ATLAS URL

Use the URL the user provided when possible. For a pipeline/orchestrator view:

```js
globalThis.atlasUrl =
  "http://127.0.0.1:62196/?backend=live&session=codexadmin%2Fpl330realverify%2Forchestrator&ip=pl330realverify&workflow=orchestrator&session_id=codexadmin";

if ((await tab.url()) !== globalThis.atlasUrl) {
  await tab.goto(globalThis.atlasUrl);
} else {
  await tab.reload();
}
await tab.playwright.waitForLoadState({
  state: "domcontentloaded",
  timeoutMs: 10000,
});
```

After backend code changes, restart the ATLAS UI process and reload the same
browser tab. A stale server process will keep serving old Python code even if
the file is edited.

## Inspect What The User Sees

Take a DOM snapshot first. It is cheaper and more stable than a screenshot for
finding buttons, status labels, and input fields.

```js
globalThis.snap = await tab.playwright.domSnapshot();
nodeRepl.write(
  globalThis.snap
    .split("\n")
    .filter((line) =>
      /SSOT|RTL|LINT|SYN|STA|PNR|PSTA|AUDIT|passed|failed|running/.test(line)
    )
    .slice(0, 160)
    .join("\n")
);
```

Use a screenshot when visual layout matters:

```js
await display(await tab.playwright.screenshot({ fullPage: false }));
```

## Click And Type With Semantic Locators

Prefer stable locators over coordinates. Confirm uniqueness before clicking or
typing.

```js
globalThis.runButton = tab.playwright.getByRole("button", {
  name: "Run Full IP pipeline",
  exact: true,
});
if ((await globalThis.runButton.count()) !== 1) {
  throw new Error("Run button is not unique");
}
await globalThis.runButton.click({ timeoutMs: 5000 });
```

For orchestrator chat input:

```js
globalThis.chatInput = tab.playwright.getByPlaceholder(
  "/move",
  { exact: false }
);
if ((await globalThis.chatInput.count()) !== 1) {
  throw new Error("Chat input is not unique");
}
await globalThis.chatInput.fill(
  "Run lint, syn, sta, pnr, sta-post, and goal-audit for this IP.",
  { timeoutMs: 5000 }
);
await globalThis.chatInput.press("Enter", { timeoutMs: 5000 });
```

Notes:

- Do not pass regex names to `getByRole`; use plain string names.
- If a locator fails, take a fresh `domSnapshot()` before trying a new locator.
- Do not use `.first()` as a shortcut unless you already counted and know why
  the first match is correct.

## Move The Mouse And Type By Coordinates

Use coordinate control only when the DOM does not expose a reliable target, for
example a canvas, waveform area, or custom graph. Coordinates are viewport
coordinates from the visible browser area.

```js
await tab.cua.move({ x: 1530, y: 980 });
await tab.cua.click({ x: 1530, y: 980 });
await tab.cua.type({ text: "status?" });
await tab.cua.keypress({ keys: ["ENTER"] });
```

For scrolling:

```js
await tab.cua.scroll({
  x: 1000,
  y: 800,
  scrollX: 0,
  scrollY: 600,
});
```

For DOM-node clicking when visible DOM node IDs are available:

```js
globalThis.visibleDom = await tab.dom_cua.get_visible_dom();
nodeRepl.write(JSON.stringify(globalThis.visibleDom, null, 2).slice(0, 4000));
await tab.dom_cua.click({ node_id: "node-id-from-visible-dom" });
```

## Run And Verify Synthesis

If the user specifically asks for synthesis, prefer dispatching the `syn` stage
through the visible Pipeline/Orchestrator path, then verify the real synthesis
artifacts. The worker should run `/syn-auto <ip>` and consume the SSOT
`synthesis` / timing policy plus current RTL filelist.

Display contract:

- `Full IP pipeline` must include the same 15-stage order as the backend:
  `ssot`, `fl-model`, `cl-model`, `equivalence`, `rtl`, `lint`, `tb`, `sim`,
  `coverage`, `sim-debug`, `syn`, `sta`, `pnr`, `sta-post`, `goal-audit`.
- `PPA signoff` remains the focused physical-signoff route:
  `rtl`, `syn`, `sta`, `pnr`, `sta-post`.
- If `SYN` is not visible while the API reports `stages.syn.state=passed`,
  check whether the browser is still on an older `Full IP pipeline` route
  definition that stopped at `goal-audit`. That UI definition hides signoff
  stages even though the backend/artifacts are real.

Visible-browser approach:

1. Open the Pipeline/Orchestrator URL for the IP.
2. In the Pipeline view, select the `PPA signoff` route. Synthesis is exposed
   there as `2 SYN`; the route also shows `STA`, `PNR`, and `PSTA`.
3. In Orchestrator chat, type a direct stage request such as:

```text
Run synthesis for this IP through the syn worker. Use /syn-auto <ip>, then report cells, area, warnings, and artifact paths.
```

4. Wait for the `SYN` card to leave `running`.
5. Reload the tab and inspect `SYN · passed` or `SYN · failed`.

Backend dispatch fallback, only when the UI control is unavailable but the
visible browser remains open for validation:

```bash
python3 - <<'PY'
import json, urllib.request
body = json.dumps({
    "ip": "pl330realverify",
    "stages": ["syn"],
    "schedule": "serial",
    "exec_mode": "orchestrator",
    "run_mode": "signoff",
    "prompt": "Run synthesis through the syn worker and report cells, area, warnings, and artifacts.",
}).encode()
req = urllib.request.Request(
    "http://127.0.0.1:62196/api/pipeline/dispatch",
    data=body,
    method="POST",
    headers={"Content-Type": "application/json"},
)
print(urllib.request.urlopen(req, timeout=20).read().decode())
PY
```

Synthesis is not green just because `syn/out/` exists. Check content:

```bash
python3 - <<'PY'
import json, pathlib
ip = "pl330realverify"
area = pathlib.Path(ip) / "syn" / "out" / "area.json"
report = pathlib.Path(ip) / "syn" / "out" / "syn.report.md"
netlist = pathlib.Path(ip) / "syn" / "out" / "synth.v"
doc = json.loads(area.read_text())
print({
    "top": doc.get("top"),
    "corner": doc.get("corner"),
    "total_cells": doc.get("total_cells"),
    "total_area_um2": doc.get("total_area_um2"),
    "unmapped_cells": doc.get("unmapped_cells"),
    "generic_cells": doc.get("generic_cells"),
    "latch_cells": doc.get("latch_cells"),
    "netlist_exists": netlist.is_file(),
    "report_exists": report.is_file(),
})
PY
```

For the PL330 signoff run on 2026-05-18, synthesis evidence was:

- `pl330realverify/syn/out/synth.v`
- `pl330realverify/syn/out/syn.report.md`
- `pl330realverify/syn/out/area.json`
- top: `pl330realverify`
- corner: `sky130_fd_sc_hd__ss_100C_1v40.lib`
- total cells: `1321`
- total area: `16400.0 um2`
- top cell type: `sky130_fd_sc_hd__dfrtp_1` count `372`
- warnings: none

For the same run, the related signoff evidence was:

- `STA`: ran OpenSTA and failed setup timing from
  `pl330realverify/sta/out/wns.json`; `dmaclk` period `2.0 ns`, setup
  WNS `-15.92 ns`, setup violations `5`, hold WNS `0.78 ns`.
- `SDC`: generated at `pl330realverify/sta/out/pl330realverify.sdc` by
  `workflow/sta/scripts/write_sdc.sh`; it creates `dmaclk` at `2.0 ns`,
  applies conservative `0.400 ns` input/output delays, and marks
  `dmacresetn` as a reset false path.
- `PNR`: ran OpenROAD and passed DRC from
  `pl330realverify/pnr/out/drc.json`; `drc_count=0`, with routed DEF/Verilog
  and SPEF under `pl330realverify/pnr/out/`.
- `PSTA`: ran post-route OpenSTA and failed setup timing from
  `pl330realverify/sta-post/out/wns.json`; setup WNS `-30.89 ns`, setup
  violations `5`, hold WNS `0.79 ns`.

If the `syn` worker hand-writes a temporary Yosys script and fails on a literal
environment expression such as `$::env(SKY130_LIB)`, rerun the canonical driver:

```bash
bash workflow/syn/scripts/auto_syn.sh <ip>
```

Then refresh the browser and verify `/api/pipeline/state` reports `SYN` from
the new artifact summary, for example `cells=1321` and `area=16400.0 um2`.

## Verify A Pipeline Claim

Use both visible UI and API evidence:

1. Browser: reload the ATLAS URL and inspect the visible stage cards.
2. API: query `/api/pipeline/state?ip=<ip>&session_id=<user>`.
3. Artifacts: inspect the stage-owned files on disk.

Example API check:

```bash
python3 - <<'PY'
import json, urllib.request
base = "http://127.0.0.1:62196"
data = json.load(urllib.request.urlopen(
    base + "/api/pipeline/state?ip=pl330realverify&session_id=codexadmin",
    timeout=20,
))
for sid in ["lint", "syn", "sta", "pnr", "sta-post", "goal-audit"]:
    st = data["stages"].get(sid, {})
    print(sid, st.get("state"), st.get("top"), st.get("error_summary"))
PY
```

For the PL330 signoff run on 2026-05-18, the correct visible result was:

- `LINT`: passed, `errors=0 warnings=0`
- `SYN`: passed, `cells=1321`
- `STA`: failed, `pre-route setup WNS=-15.92`
- `PNR`: passed, `DRC=0`
- `PSTA`: failed, `post-route setup WNS=-30.89`
- `AUDIT`: failed

This was important because artifact-existence logic originally made STA/PSTA
look green even though `wns.json` reported setup failure.

## Common Failure Modes

- **User says "I cannot see it"**: you probably used backend commands or a
  hidden browser. Open the exact localhost URL in the in-app browser.
- **UI shows stale state after code edits**: restart the ATLAS UI Python
  process and reload the tab.
- **Stage card says passed but artifact says failed**: fix `/api/pipeline/state`
  derivation so it reads artifact contents, not just file existence.
- **Worker says it wrote a report but job ends silent-fail**: verify the file on
  disk. Some workers emit final prose without tool writes; run the deterministic
  stage script if the canonical JSON gate is missing.
- **Click target is ambiguous**: use `domSnapshot()`, count the locator, then
  click. Fall back to coordinate CUA only for custom/canvas UI.
