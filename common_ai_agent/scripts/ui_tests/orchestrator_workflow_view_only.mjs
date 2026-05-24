// Regression for orchestrator mode workflow chips/dropdown:
// worker selections are transcript/artifact views only. The runtime session and
// prompt target must stay on <user>/<ip>/orchestrator so replies do not vanish.
import { launch, login, gotoWorkspace, jpost, shoot, assert, failures, results, log, uniqueIp, BASE } from './lib.mjs';

const { browser, page } = await launch({ viewport: { width: 1800, height: 1050 }, dsf: 1 });
const ip = uniqueIp('orchview');

const clickWorkflowChip = (wf) => page.evaluate((id) => {
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const b = [...document.querySelectorAll('button')]
    .find(x => x.offsetParent !== null && /[○◉]$/.test(norm(x.textContent)) && norm(x.textContent).includes(id));
  if (b) { b.click(); return true; }
  return false;
}, wf);

const send = async (text) => {
  const ta = await page.$('textarea');
  assert(!!ta, 'prompt textarea present');
  await ta.click();
  await ta.fill('');
  await ta.type(text);
  await page.keyboard.press('Enter');
};

try {
  const li = await login(page);
  assert(li.status === 200, `login ok (${li.status})`);
  const created = await jpost(page, '/api/ip/create', { name: ip });
  assert(created.status === 200 && created.body && created.body.ok, `created IP ${ip}`);
  await gotoWorkspace(page, { base: BASE, user: 'admin', ip, workflow: 'orchestrator' });
  await page.waitForTimeout(1200);

  await page.evaluate(() => {
    window.__atlasViewOnlyFetches = [];
    window.__atlasViewOnlySwitches = [];
    const oldFetch = window.fetch.bind(window);
    window.fetch = (input, init) => {
      const url = String((input && input.url) || input || '');
      if (url.includes('/api/session/activate')) {
        window.__atlasViewOnlyFetches.push({ url, body: init && init.body });
      }
      return oldFetch(input, init);
    };
    if (window.backend && typeof window.backend.switchSession === 'function') {
      const oldSwitch = window.backend.switchSession.bind(window.backend);
      window.backend.switchSession = (sid) => {
        window.__atlasViewOnlySwitches.push(String(sid || ''));
        return oldSwitch(sid);
      };
    }
  });

  const clicked = await clickWorkflowChip('ssot-gen');
  assert(clicked, 'clicked ssot-gen worker chip');
  await page.waitForTimeout(1800);
  const afterWorkerView = await page.evaluate(() => ({
    activeSession: window.ACTIVE_SESSION || '',
    activateCalls: window.__atlasViewOnlyFetches || [],
    switchCalls: window.__atlasViewOnlySwitches || [],
    body: document.body.innerText,
  }));
  assert(afterWorkerView.activeSession.endsWith(`/${ip}/orchestrator`), `runtime stayed on orchestrator (${afterWorkerView.activeSession})`);
  assert(afterWorkerView.activateCalls.length === 0, `worker view did not call /api/session/activate (${afterWorkerView.activateCalls.length})`);
  assert(afterWorkerView.switchCalls.every(s => s.endsWith(`/${ip}/orchestrator`)), 'backend switchSession was not pointed at a worker namespace');
  assert(/No ssot-gen worker transcript yet/i.test(afterWorkerView.body), 'ssot-gen worker view rendered a visible empty transcript');
  await shoot(page, 'orch-view-worker-ssot.png');

  await send('status ?');
  let replied = false;
  for (let i = 0; i < 10; i++) {
    await page.waitForTimeout(1000);
    replied = await page.evaluate(() => /no active worker jobs|active worker job\(s\)|registered in this server process|Latest job/i.test(document.body.innerText));
    if (replied) break;
  }
  assert(replied, 'orchestrator status reply rendered after returning from worker view');
  const afterStatus = await page.evaluate(() => ({
    activeSession: window.ACTIVE_SESSION || '',
    lastBody: document.body.innerText,
  }));
  assert(afterStatus.activeSession.endsWith(`/${ip}/orchestrator`), `status prompt used orchestrator session (${afterStatus.activeSession})`);
  await shoot(page, 'orch-view-status-reply.png');
} finally {
  await browser.close();
}

log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
process.exit(failures().length ? 1 : 0);
