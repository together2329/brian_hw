// Switching orchestrator → worker session must NOT leave stale orchestrator
// chat content (worker session conversation.json is empty, so nothing
// re-hydrates to replace it). Free (no LLM): inject an orchestrator
// conversation, switch workflow in-app, assert the feed cleared.
import { launch, login, gotoWorkspace, shoot, assert, failures, results, log } from './lib.mjs';
const MARK = 'ZZSTALEMARKER_orchestrator_status_check';
const messages = [
  { role: 'assistant', tool_calls: [{ function: { name: 'ask_user', arguments: `question="${MARK}"` } }] },
  { role: 'assistant', content: `${MARK} mctp_axi is partially green but not signoff-ready.` },
];
const { browser, page } = await launch();
try {
  await login(page);
  await gotoWorkspace(page, { ip: 'mctp_axi', workflow: 'orchestrator' });
  await page.evaluate(() => { const e=[...document.querySelectorAll('button,span,div,[role="tab"]')].find(x=>(x.textContent||'').trim().toUpperCase()==='CHAT'&&x.offsetParent);if(e)e.click(); });
  await page.waitForTimeout(800);
  // inject WITHOUT a session field so onConvLoaded accepts it regardless of the
  // logged-in owner (admin vs brian) — sameActiveSession is true when session=''.
  await page.evaluate((m)=>window.dispatchEvent(new CustomEvent('atlas-conversation-loaded',{detail:{messages:m}})), messages);
  await page.waitForTimeout(1200);
  const before = await page.evaluate((mk)=>document.body.innerText.includes(mk), MARK);
  assert(before, 'orchestrator content present before switch (injected)');
  await shoot(page, 'stale-before.png');

  // switch to ssot-gen via the sidebar workflow list (in-app namespace change)
  const clicked = await page.evaluate(()=>{
    const el=[...document.querySelectorAll('*')].find(x=>(x.textContent||'').trim()==='ssot-gen'&&x.offsetParent&&x.getBoundingClientRect().width<400);
    if(el){ el.click(); return true; } return false;
  });
  log('clicked ssot-gen sidebar:', clicked);
  await page.waitForTimeout(3000);
  const wf = await page.evaluate(()=> (window.CURRENT_WORKFLOW||new URL(location.href).searchParams.get('workflow')||''));
  const after = await page.evaluate((mk)=>document.body.innerText.includes(mk), MARK);
  log('workflow after click:', wf, 'marker still visible:', after);
  assert(!after, 'orchestrator content CLEARED after switching to ssot-gen (no stale feed)');
  await shoot(page, 'stale-after.png');
} finally { await browser.close(); }
log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length?1:0);
