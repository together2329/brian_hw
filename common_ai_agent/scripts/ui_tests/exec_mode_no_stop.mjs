// Verifies the workflow-switch confirm gate (free, no LLM):
//   orchestrator mode + agent running  → switch WITHOUT a stop confirm, run kept
//   single-worker  mode + agent running → "Agent is running…" confirm DOES fire
// Drives the real switchWorkflow() by clicking left-rail workflow chips and
// intercepting window.confirm via page.on('dialog').
import { launch, jpost, shoot, assert, failures, results, log, BASE, USER, PASS } from './lib.mjs';

// Lightweight nav that does NOT wait for networkidle — an active orchestrator
// run keeps the network busy forever, so networkidle never settles.
const WORKSPACE_TAB = () => [...document.querySelectorAll('button,a,span,[role="tab"]')]
  .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent !== null);
// A workflow chip uniquely ends with the ○/◉ status circle.
const HAS_WF_CHIPS = () => [...document.querySelectorAll('button')]
  .some(b => /[○◉]$/.test((b.textContent || '').replace(/\s+/g, ' ').trim()));

async function loginAndOpen(page, ip) {
  // The active orchestrator run loads the server; use generous timeouts and
  // wait for real mount markers instead of fixed sleeps.
  page.setDefaultNavigationTimeout(120000);
  page.setDefaultTimeout(120000);
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await jpost(page, '/api/auth/login', { username: USER, password: PASS });
  await page.goto(`${BASE}/?session_id=${USER}&ip=${ip}&workflow=orchestrator`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(WORKSPACE_TAB, { timeout: 120000 });
  await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,a,span,[role="tab"]')]
      .find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent !== null);
    if (e) e.click();
  });
  await page.waitForFunction(HAS_WF_CHIPS, { timeout: 120000 });
  await page.waitForTimeout(800);
}

// Click the left-rail workflow chip. Each chip renders "<n> <glyph> <label> <○|◉>",
// so it uniquely ends with the ○/◉ status circle and contains the stage label.
const clickWf = (page, wf) => page.evaluate((id) => {
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const b = [...document.querySelectorAll('button')]
    .find(x => x.offsetParent !== null && /[○◉]$/.test(norm(x.textContent)) && norm(x.textContent).includes(id));
  if (b) { b.click(); return true; }
  return false;
}, wf);

const main = async () => {
  const { browser, page } = await launch();
  const dialogs = [];
  page.on('dialog', d => { dialogs.push(d.message()); d.dismiss().catch(() => {}); });
  try {
    await loginAndOpen(page, 'uart_tx');

    // --- Case A: orchestrator mode, agent running → no confirm ---
    await page.evaluate(() => { window.ATLAS_EXEC_MODE = 'orchestrator'; window.ATLAS_AGENT_RUNNING = true; });
    dialogs.length = 0;
    const clickedA = await clickWf(page, 'ssot-gen');
    await page.waitForTimeout(1500);
    assert(clickedA, 'orchestrator: ssot-gen chip found + clicked');
    assert(dialogs.length === 0, `orchestrator: NO stop confirm (saw ${dialogs.length}: ${JSON.stringify(dialogs)})`);
    const stillRunning = await page.evaluate(() => window.ATLAS_AGENT_RUNNING === true);
    assert(stillRunning, 'orchestrator: run NOT stopped (ATLAS_AGENT_RUNNING stays true)');

    // --- Case B: single-worker mode, agent running → confirm fires ---
    await page.evaluate(() => { window.ATLAS_EXEC_MODE = 'single'; window.ATLAS_AGENT_RUNNING = true; });
    dialogs.length = 0;
    const clickedB = await clickWf(page, 'fl-model-gen');
    await page.waitForTimeout(1500);
    assert(clickedB, 'single: fl-model-gen chip found + clicked');
    assert(dialogs.length >= 1, `single: stop confirm DID fire (saw ${dialogs.length})`);
    assert(dialogs.some(m => /Agent is running/i.test(m)), 'single: confirm message is the stop prompt');

    await shoot(page, 'exec_mode_no_stop.png');
  } finally {
    await browser.close();
  }
  log(`RESULT: ${results().length - failures().length}/${results().length} passed`);
  process.exit(failures().length ? 1 : 0);
};
main().catch(e => { log('FATAL', e); process.exit(2); });
