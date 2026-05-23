// Verify BOTH exec modes drive a worker, using the recipe tooling.
//   single-worker : POST /api/job/dispatch {workflow:'ssot-gen', ...}
//   orchestrator  : POST /api/pipeline/orchestrator/chat {message, ip}
// Each dispatches ONE cheap stage (ssot-gen) — no full-chain cascade.
// See README.md for the principle + gotchas.
import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const OUT = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omc/ui-shots';
const SINGLE_IP = process.env.SINGLE_IP || 'vmode_single';
const ORCH_IP = process.env.ORCH_IP || 'vmode_orch';
const log = (...a) => console.log('[verify-modes]', ...a);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
const jget = (path) => page.evaluate(async (p) => { try { const r = await fetch(p, { credentials: 'include' }); return await r.json(); } catch (e) { return { error: String(e) }; } }, path);

try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => { await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'admin', password: '1151' }), credentials: 'include' }); });

  // ── SINGLE-WORKER ────────────────────────────────────────────────
  const sKick = await page.evaluate(async (ip) => {
    const r = await fetch('/api/job/dispatch', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ workflow: 'ssot-gen', ip, exec_mode: 'single-worker', prompt: 'Generate the SSOT for a 4-bit synchronous counter.' }) });
    let b = null; try { b = await r.json(); } catch (_) {}
    return { status: r.status, body: b };
  }, SINGLE_IP);
  log('single-worker dispatch:', sKick.status, JSON.stringify(sKick.body || {}).slice(0, 200));
  const sJobId = sKick.body && sKick.body.job_id;
  let sStatus = 'unknown';
  for (let i = 0; i < 20; i++) {
    await page.waitForTimeout(3000);
    const jobs = await jget('/api/jobs');
    const arr = Array.isArray(jobs) ? jobs : (jobs.jobs || []);
    const j = arr.find(x => String(x.job_id || x.id) === String(sJobId)) || arr.find(x => (x.ip === SINGLE_IP));
    sStatus = j ? (j.status || j.state || '?') : 'not-found';
    log(`single poll ${i}: job ${sJobId} status=${sStatus}`);
    if (['running', 'passed', 'done', 'error', 'failed', 'completed'].includes(String(sStatus))) break;
  }

  // ── ORCHESTRATOR ─────────────────────────────────────────────────
  const oKick = await page.evaluate(async (ip) => {
    const r = await fetch('/api/pipeline/orchestrator/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ message: 'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.', ip }) });
    let b = null; try { b = await r.json(); } catch (_) {}
    return { status: r.status, body: b };
  }, ORCH_IP);
  const OEFF = (oKick.body && oKick.body.ip) ? String(oKick.body.ip) : ORCH_IP;
  log('orchestrator chat:', oKick.status, 'effIP=', OEFF);
  let oActive = [];
  for (let i = 0; i < 25; i++) {
    await page.waitForTimeout(3000);
    const snap = await jget(`/api/orchestrator/workers?ip=${OEFF}`);
    const ws = Array.isArray(snap && snap.workers) ? snap.workers : [];
    oActive = ws.filter(w => Number(w.running_count || 0) > 0 || Number(w.pending_count || 0) > 0 || Number(w.queued_count || 0) > 0);
    log(`orch poll ${i}: active=[${oActive.map(w => `${w.workflow}:${w.running_count || 0}r/${w.pending_count || 0}p`).join(',')}]`);
    if (oActive.length) break;
  }

  // ── screenshots ──────────────────────────────────────────────────
  const shoot = async (ip, wf, name) => {
    await page.goto(`${BASE}/?session_id=admin&ip=${ip}&workflow=${wf}`, { waitUntil: 'networkidle' });
    await page.evaluate(() => { const e = [...document.querySelectorAll('button,a,span,.dir-btn')].find(x => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((x.textContent || '').trim()) && x.offsetParent); if (e) e.click(); });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${OUT}/${name}`, fullPage: false });
    log('saved', name);
  };
  await shoot(SINGLE_IP, 'ssot-gen', '10-single-worker.png');
  await shoot(OEFF, 'orchestrator', '11-orchestrator.png');

  // ── cleanup: finalize the orchestrator run (single-stage ssot-gen just finishes) ──
  await page.evaluate(async (ip) => { await fetch('/api/pipeline/orchestrator/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ message: 'Stop now. Do not dispatch anything else. Finalize this run as blocked immediately.', ip }) }); }, OEFF);

  log('RESULT single-worker:', sStatus, '| orchestrator active:', oActive.map(w => w.workflow).join(',') || 'none');
} catch (e) {
  log('ERROR', e.message);
} finally {
  await browser.close();
}
