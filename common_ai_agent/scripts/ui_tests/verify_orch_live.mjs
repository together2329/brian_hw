// Hands-on live UI check of orchestrator responsiveness:
//  A) a status query gets a VISIBLE reply + the spinner stops
//  B) a bare "Hi" greeting just greets — no triage / dispatch / ask_user
import { launch, login, gotoWorkspace, shoot, assert, failures, results, log, uniqueIp, jget } from './lib.mjs';
const { browser, page } = await launch();
const ipA = uniqueIp('stat'), ipB = uniqueIp('greet');
const clickChat = () => page.evaluate(()=>{const e=[...document.querySelectorAll('button,span,div,[role="tab"]')].find(x=>(x.textContent||'').trim().toUpperCase()==='CHAT'&&x.offsetParent);if(e)e.click();});
const send = async (text) => { const ta=await page.$('textarea'); await ta.click(); await ta.type(text); await page.keyboard.press('Enter'); };
const bodyHas = (re) => page.evaluate((s)=>new RegExp(s,'i').test(document.body.innerText), re.source);
try {
  const li = await login(page); assert(li.status===200, `login ok (${li.status})`);
  const me = await jget(page, '/api/users/me'); assert(me.status===200, `authed (me ${me.status})`);

  // ── A) status reply ──
  await gotoWorkspace(page, { ip: ipA, workflow: 'orchestrator' }); await clickChat(); await page.waitForTimeout(1500);
  await send('all status ?');
  let replied=false;
  for (let i=0;i<10;i++){ await page.waitForTimeout(1200); if (await bodyHas(/no active worker|worker job|no SSOT|pipeline|ready|status/)) { replied=true; break; } }
  assert(replied, 'A: status query produced a visible reply');
  let spinOff=false; for (let i=0;i<6;i++){ if(!(await bodyHas(/Agent running/))){spinOff=true;break;} await page.waitForTimeout(1200); }
  assert(spinOff, 'A: spinner stopped after status reply');
  await shoot(page, 'live-A-status.png');

  // ── B) greeting must NOT trigger triage/dispatch/ask_user ──
  await gotoWorkspace(page, { ip: ipB, workflow: 'orchestrator' }); await clickChat(); await page.waitForTimeout(1500);
  await send('Hi');
  // wait for a reply (gpt-5.5)
  let greeted=false;
  for (let i=0;i<20;i++){ await page.waitForTimeout(1500); const ents = await page.evaluate(()=>document.querySelectorAll('.feed-entry-agent,.md-agent').length); if (ents>0 && await bodyHas(/\b(hi|hello|hey|ready|help|드라이브|준비|안녕)\b/)) { greeted=true; log(`greeted after ~${(i+1)*1.5}s`); break; } }
  assert(greeted, 'B: "Hi" got a short greeting');
  // give it a few more seconds, then assert NO triage artifacts
  await page.waitForTimeout(4000);
  const triage = await page.evaluate(()=>({
    handoff: document.querySelectorAll('.handoff-card').length,
    askUser: /relax the clock|re-architect|stop as blocked|increase.*budget|sim-debug attempt/i.test(document.body.innerText),
    dispatch: /dispatch_workflow|Dispatch →/i.test(document.body.innerText),
  }));
  log('B triage artifacts:', JSON.stringify(triage));
  assert(triage.handoff===0 && !triage.dispatch, 'B: greeting did NOT dispatch a workflow');
  assert(!triage.askUser, 'B: greeting did NOT pop a big ask_user question');
  await shoot(page, 'live-B-greeting.png');
} finally { await browser.close(); }
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
