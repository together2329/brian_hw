# ATLAS UI: real-screenshot / headless test recipe (Playwright)

> **Date:** 2026-05-23
> **Why:** Verify ATLAS frontend features against a **live running server**
> (not mocks) and capture real screenshots — login, drive an orchestrator
> run so a worker actually spawns, then screenshot the resulting UI. This is
> the working recipe distilled from getting the orchestrator-chat
> "worker strip" + 13px font screenshots to succeed.

---

## TL;DR — what makes it work

1. **Use system Chrome via Playwright** `channel:'chrome'` (no `playwright
   install` needed). The `playwright` node module is already resolvable in
   `common_ai_agent`.
2. **Auth = cookie session.** `POST /api/auth/login {username,password}`
   inside the page context (`credentials:'include'`), then reload. Default
   admin: `admin` / `1151`.
3. **To make a worker appear**, drive a real run:
   `POST /api/pipeline/orchestrator/chat {message, ip}`.
4. **Get onto the Workspace screen** — URL params set the session but land
   on the **Dashboard**; you must click the `⌂ Workspace` nav tab to reach
   the chat where in-chat UI (e.g. the worker strip) lives.

## Gotchas that cost us the first attempts

- **IP-extractor hijack.** `_extract_ip_from_orchestrator_message`
  (`src/atlas_api_jobs.py`) parses `for <word>` / `on <word>` out of the
  chat message and **overrides the explicit `ip` field**. A message ending
  `"...do not pause for confirmation"` sent the whole run to `ip=confirmation`.
  - Fix: never put `for <noun>` / `on <noun>` in the seed message. Use e.g.
    `"Dispatch ssot-gen now and begin a 4-bit synchronous counter design.
    Auto-advance every stage, never pause."`
  - Defensive: read back `kick.body.ip` and poll/screenshot **that** IP, not
    the one you sent. (See [[orchestrator-pnr-run-issues-2026-05-23]] — this
    is the still-open P1 extractor bug.)
- **Dashboard vs Workspace.** `?session_id=&ip=&workflow=orchestrator`
  activates the namespace (CURRENT FOCUS shows `admin/<ip>/orchestrator`) but
  the screen stays on Dashboard. Click `⌂ Workspace` to see the chat.
- **Worker model.** The provider now **rejects `glm-5.1`** (HTTP 400:
  "supported names are deepseek-v4-pro or deepseek-v4-flash"). Use
  `deepseek-v4-pro` for `ATLAS_WORKER_MODEL_*`. The gpt-5.5 orchestrator
  needs `USE_OPENCODE_OAUTH=true` (else 403). (Supersedes the glm-5.1 in
  [[orchestrator-new-ip-to-pnr-recipe-2026-05-23]].)
- **The strip is data-gated.** It only renders while a worker is active
  (`running_count|pending_count|queued_count > 0`). `ssot-gen` finishes fast,
  so poll for the chip and screenshot the moment it appears.
- **Multi-user isolation.** Logging in as `admin` will NOT show another
  user's (e.g. `brian`'s) IP data. Drive a **fresh IP under the test user**.
- `deviceScaleFactor: 2` for crisp text; `clip` the bottom ~280px to frame
  the input row + strip.

## Skeleton (Playwright, ES module)

```js
import { chromium } from 'playwright';
const BASE = 'http://127.0.0.1:3001';            // a running atlas_ui server
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport:{width:1600,height:1000}, deviceScaleFactor:2 });
const page = await ctx.newPage();

await page.goto(BASE, { waitUntil: 'domcontentloaded' });
await page.evaluate(async () => {                 // cookie-session login
  await fetch('/api/auth/login', { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ username:'admin', password:'1151' }),
    credentials:'include' });
});

const kick = await page.evaluate(async (ip) => {  // drive a run → worker spawns
  const r = await fetch('/api/pipeline/orchestrator/chat', { method:'POST',
    headers:{'Content-Type':'application/json'}, credentials:'include',
    body: JSON.stringify({ message:'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.', ip }) });
  return await r.json();
}, 'shot_ctr2');
const IP = kick.ip || 'shot_ctr2';                // track the EFFECTIVE ip

await page.goto(`${BASE}/?session_id=admin&ip=${IP}&workflow=orchestrator`, { waitUntil:'networkidle' });
await page.evaluate(() => {                        // click the Workspace tab
  const e = [...document.querySelectorAll('button,a,span,.dir-btn')]
    .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent||'').trim()) && x.offsetParent);
  if (e) e.click();
});
// poll for the strip chip, then screenshot
for (let i=0;i<30;i++){
  const chip = await page.evaluate(() => {
    const b=[...document.querySelectorAll('button')].find(b=>/worker session for full live detail/i.test(b.getAttribute('title')||''));
    return b ? b.textContent.trim() : null; });
  if (chip) break; await page.waitForTimeout(3000);
}
await page.screenshot({ path:'.omc/ui-shots/strip.png', clip:{x:0,y:720,width:1600,height:280} });
await browser.close();
```

Useful read-only probes (all need the session cookie):
`GET /api/orchestrator/workers?ip=<ip>` · `GET /api/orchestrator/active_run?ip=<ip>` ·
`GET /api/pipeline/state?ip=<ip>` · `GET /api/orchestrator/chat/messages?ip=<ip>&since=0&limit=50`.

## Cleanup — IMPORTANT (no dedicated stop API)

Test seeds say "auto-advance", so a run will keep dispatching stages
(billable). There is **no stop endpoint**; stop a run **in-band**:

```js
POST /api/pipeline/orchestrator/chat
  { message: 'Stop now. Do not dispatch anything else. Finalize this run as blocked immediately.', ip }
```

The orchestrator wakes on the user message and calls `dispatch_workflow(__final__,
state=blocked)`. Verify with `active_run?ip=` returning `run:null`. **Do NOT
kill workers** — `ssot-gen` etc. are shared canonical workers used by other
IPs; the in-flight stage just finishes and idles.

## Reusable scripts
Tracked in **`scripts/ui_tests/`** (see its `README.md` for the principle +
usage): `shoot.mjs` (login + toolbar/font shot), `shoot3.mjs` (run +
Workspace + strip + click), `stop.mjs` (finalize test runs), `verify_stop.mjs`.
Screenshot **outputs** land in `.omc/ui-shots/*.png` (git-ignored).

```
node scripts/ui_tests/shoot3.mjs     # capture → .omc/ui-shots/
node scripts/ui_tests/stop.mjs       # cleanup
```

## See also
- [[orchestrator-new-ip-to-pnr-recipe-2026-05-23]] — driving a new IP to PnR
  (update its worker model to deepseek-v4-pro).
- [[orchestrator-pnr-run-issues-2026-05-23]] — the IP-extractor hijack P1.
- [[atlas-test-feature-coverage]] — which test gates which feature.
