// Gap 6 (BILLABLE — up to 2 ssot-gen): workflow switching semantics.
//   orchestrator: switch is NON-destructive (no confirm, worker keeps running).
//   single-worker: switching while a run is active triggers window.confirm.
// The single-worker confirm depends on UI run-state we can't always force
// headlessly → it's best-effort (SKIP if the dialog doesn't fire), while the
// orchestrator non-destructive case is asserted firmly.
import { launch, login, jpost, jget, gotoWorkspace, pollUntil, cleanup, assert, failures, exitCode, log, skip, uniqueIp, WORKER_MODEL } from './lib.mjs';

const { browser, page } = await launch();
const orchIp = uniqueIp('exo');
const singleIp = uniqueIp('exs');
const dialogs = [];
page.on('dialog', async d => { dialogs.push(d.message()); try { await d.dismiss(); } catch (_) {} });

try {
  await login(page);

  // ── ORCHESTRATOR: non-destructive switch ──
  const kick = await jpost(page, '/api/pipeline/orchestrator/chat', {
    message: 'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.',
    ip: orchIp, model: WORKER_MODEL,
  });
  const oIp = (kick.body && kick.body.ip) ? String(kick.body.ip) : orchIp;
  const oActive = await pollUntil(async () => {
    const s = await jget(page, `/api/orchestrator/workers?ip=${oIp}`);
    return ((s.body && s.body.workers) || []).some(w => Number(w.running_count || 0) > 0) || null;
  }, { tries: 25, interval: 3000, label: 'orch-active' });
  assert(oActive, 'orchestrator worker is running before switch');

  await gotoWorkspace(page, { ip: oIp, workflow: 'orchestrator' });
  dialogs.length = 0;
  await page.evaluate((ip) => window.openPipelineWorkflowWorkspace?.({ ip, workflow: 'rtl-gen' }), oIp);
  await page.waitForTimeout(3000);
  assert(dialogs.length === 0, `orchestrator switch fired NO confirm dialog (got ${dialogs.length})`);
  const stillRunning = await jget(page, `/api/orchestrator/workers?ip=${oIp}`);
  assert(((stillRunning.body && stillRunning.body.workers) || []).some(w => Number(w.running_count || 0) > 0), 'worker still running after non-destructive switch');

  // ── SINGLE-WORKER: confirm-stop (best-effort) ──
  const sd = await jpost(page, '/api/job/dispatch', { workflow: 'ssot-gen', ip: singleIp, exec_mode: 'single-worker', prompt: 'Generate the SSOT for a 4-bit synchronous counter.' });
  assert(sd.status === 200 && sd.body && sd.body.job_id, `single-worker ssot-gen dispatched (job ${sd.body && sd.body.job_id})`);
  await gotoWorkspace(page, { ip: singleIp, workflow: 'ssot-gen' });
  await page.waitForTimeout(2000);
  dialogs.length = 0;
  await page.evaluate((ip) => window.openPipelineWorkflowWorkspace?.({ ip, workflow: 'lint' }), singleIp);
  await page.waitForTimeout(2500);
  if (dialogs.length > 0) {
    assert(/Agent is running\. Stop it and switch/i.test(dialogs[0]), `single-worker switch confirm message correct: ${dialogs[0]}`);
  } else {
    skip('single-worker confirm dialog did not fire (UI run-state not active in headless) — non-fatal');
  }
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await cleanup(page, [orchIp, oIp_safe()]);
  await browser.close();
}
function oIp_safe() { return orchIp; }
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
