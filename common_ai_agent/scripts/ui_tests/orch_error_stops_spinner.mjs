// When an orchestrator run errors (e.g. bad model → 403), the chat must show
// the error AND the "Agent running" spinner must STOP. Drives the real UI
// input so frontend `streaming` is set, then asserts it clears on run end.
import { launch, assert, failures, results, log } from './lib.mjs';
const BASE = process.env.BASE || 'http://127.0.0.1:7000';
const { browser, page } = await launch();
const ip = 'spin_' + Date.now().toString(36);
try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => { await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'admin',password:'1151'}),credentials:'include'}); });
  await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=orchestrator`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(()=>{const e=[...document.querySelectorAll('button,a,span,.dir-btn')].find(x=>/^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent||'').trim())&&x.offsetParent);if(e)e.click();});
  await page.waitForTimeout(2000);
  // type into the prompt and submit (sets frontend streaming=true)
  const ta = await page.$('textarea');
  assert(!!ta, 'prompt textarea present');
  await ta.click(); await ta.type('status?'); await page.keyboard.press('Enter');

  // spinner should appear shortly
  let sawRunning = false;
  for (let i=0;i<5;i++){ await page.waitForTimeout(700); if (await page.evaluate(()=>/Agent running/.test(document.body.innerText))) { sawRunning=true; break; } }
  assert(sawRunning, '"Agent running" spinner appeared after submit');

  // ...and must CLEAR within ~14s (run errors/ends → run-status poll stops it)
  let cleared = false;
  for (let i=0;i<14;i++){ await page.waitForTimeout(1500); if (!(await page.evaluate(()=>/Agent running/.test(document.body.innerText)))) { cleared=true; log(`spinner cleared after ~${(i+1)*1.5}s`); break; } }
  assert(cleared, '"Agent running" spinner STOPPED after run ended');

  // the error must be visible in the feed
  const errShown = await page.evaluate(()=>/403|Forbidden|error/i.test(document.body.innerText));
  assert(errShown, 'error surfaced in the chat feed');
} finally { await browser.close(); }
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
