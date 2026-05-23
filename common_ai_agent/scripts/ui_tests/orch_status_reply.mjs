// A status query ("status?", "all status?") is answered by the synchronous
// fast-path (HTTP body, no live WS emit). The UI must still render that reply
// AND stop the "Agent running" spinner. Regression for "답을 못 받아".
import { launch, assert, failures, results, log } from './lib.mjs';
const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const { browser, page } = await launch();
const ip = 'strep_' + Date.now().toString(36);
try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => { await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:'admin',password:'1151'}),credentials:'include'}); });
  await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=orchestrator`, { waitUntil: 'domcontentloaded' });
  await page.evaluate(()=>{const e=[...document.querySelectorAll('button,a,span,.dir-btn')].find(x=>/^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent||'').trim())&&x.offsetParent);if(e)e.click();});
  await page.waitForTimeout(2500);
  const ta = await page.$('textarea');
  assert(!!ta, 'prompt textarea present');
  const wf = await page.evaluate(()=> (window.CURRENT_WORKFLOW||new URL(location.href).searchParams.get('workflow')||''));
  log('workflow=', wf);
  await ta.click(); await ta.type('all status ?'); await page.keyboard.press('Enter');
  // the reply text ('...no active worker jobs...') must appear within ~10s
  let replied = false;
  for (let i=0;i<10;i++){ await page.waitForTimeout(1200); const has = await page.evaluate(()=>/no active worker jobs|active worker job\(s\)|registered in this server/i.test(document.body.innerText)); if (has) { replied=true; log(`reply text appeared after ~${(i+1)*1.2}s`); break; } }
  assert(replied, 'orchestrator status reply rendered in the feed');
  // spinner must be off shortly after
  let cleared=false;
  for (let i=0;i<8;i++){ if (!(await page.evaluate(()=>/Agent running/.test(document.body.innerText)))) { cleared=true; break; } await page.waitForTimeout(1200); }
  assert(cleared, '"Agent running" spinner cleared after status reply');
} finally { await browser.close(); }
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
