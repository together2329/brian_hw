// Gap 4 (BILLABLE — 1 ssot-gen): orchestrator worker strip renders in real
// time, and clicking a chip switches to that worker's session.
// Runs only via run_all.mjs when UI_E2E_LLM=1, or directly.
import { launch, login, jpost, jget, gotoWorkspace, findChip, pollUntil, shoot, cleanup, assert, failures, exitCode, log, uniqueIp, WORKER_MODEL } from './lib.mjs';

const { browser, page } = await launch();
const ip = uniqueIp('strip');
try {
  await login(page);
  // hijack-safe message (no "for <noun>" / "on <noun>"); single stage
  const kick = await jpost(page, '/api/pipeline/orchestrator/chat', {
    message: 'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.',
    ip, model: WORKER_MODEL,
  });
  const effIp = (kick.body && kick.body.ip) ? String(kick.body.ip) : ip;
  assert(kick.status === 200, `orchestrator chat accepted (status ${kick.status})`);
  log('effective IP:', effIp);

  const active = await pollUntil(async () => {
    const s = await jget(page, `/api/orchestrator/workers?ip=${effIp}`);
    const ws = (s.body && s.body.workers) || [];
    return ws.some(w => Number(w.running_count || 0) > 0 || Number(w.pending_count || 0) > 0) || null;
  }, { tries: 25, interval: 3000, label: 'worker-active' });
  assert(active, 'a worker reached running/pending for the orchestrator run');

  await gotoWorkspace(page, { ip: effIp, workflow: 'orchestrator' });
  const chip = await pollUntil(() => findChip(page), { tries: 15, interval: 2000, label: 'chip' });
  assert(chip, `worker strip chip rendered (text: ${JSON.stringify(chip)})`);
  if (chip) assert(/▶[\s\S]*running/i.test(chip), `chip shows a running worker (text: ${chip})`);
  await shoot(page, 'ws-strip.png', { x: 0, y: 720, width: 1600, height: 280 });

  if (chip) {
    const wfBefore = await page.evaluate(() => new URL(location.href).searchParams.get('workflow'));
    await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /worker session for full live detail/i.test(x.getAttribute('title') || '')); if (b) b.click(); });
    await page.waitForTimeout(4000);
    const wfAfter = await page.evaluate(() => (window.CURRENT_WORKFLOW || new URL(location.href).searchParams.get('workflow') || ''));
    assert(wfAfter && wfAfter !== 'orchestrator', `clicking chip switched workflow away from orchestrator (now: ${wfAfter}, was: ${wfBefore})`);
    await shoot(page, 'ws-after-click.png');
  }
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await cleanup(page, [ip]);
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
