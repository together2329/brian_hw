import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const USER = process.env.U || 'admin';
const PASS = process.env.P || '1151';
const IP = process.env.IP || 'shot_counter';
const OUT = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omc/ui-shots';
const log = (...a) => console.log('[shoot2]', ...a);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  const login = await page.evaluate(async ({ u, p }) => {
    const r = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }), credentials: 'include' });
    return r.status;
  }, { u: USER, p: PASS });
  log('login:', login);

  // existing workers (global)
  const pre = await page.evaluate(async () => {
    try { const r = await fetch('/api/orchestrator/workers', { credentials: 'include' }); return await r.json(); } catch (e) { return { error: String(e) }; }
  });
  log('pre workers:', JSON.stringify(pre).slice(0, 300));

  // kick an orchestrator run that forces an immediate dispatch.
  // NOTE: avoid "for <noun>" / "on <noun>" — the IP extractor hijacks those.
  const kick = await page.evaluate(async (ip) => {
    const r = await fetch('/api/pipeline/orchestrator/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ message: 'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.', ip }),
    });
    let b = null; try { b = await r.json(); } catch (_) {}
    return { status: r.status, body: b };
  }, IP);
  log('kick:', kick.status, JSON.stringify(kick.body || {}).slice(0, 300));
  // whatever IP the run actually used (extractor may still override) — track that one
  const EFFIP = (kick.body && kick.body.ip) ? String(kick.body.ip) : IP;
  log('effective IP:', EFFIP);

  // poll for an active worker (running/pending/queued > 0)
  let active = [];
  for (let i = 0; i < 50; i++) {
    await page.waitForTimeout(3000);
    const snap = await page.evaluate(async (ip) => {
      try { const r = await fetch(`/api/orchestrator/workers?ip=${encodeURIComponent(ip)}`, { credentials: 'include' }); return await r.json(); } catch (e) { return { error: String(e) }; }
    }, EFFIP);
    const ws = Array.isArray(snap && snap.workers) ? snap.workers : [];
    active = ws.filter(w => Number(w.running_count || 0) > 0 || Number(w.pending_count || 0) > 0 || Number(w.queued_count || 0) > 0);
    // also peek at orchestrator chat tail + pipeline state to diagnose
    let tail = '';
    if (i % 3 === 0) {
      const diag = await page.evaluate(async (ip) => {
        const out = {};
        try { const r = await fetch(`/api/orchestrator/chat/messages?ip=${encodeURIComponent(ip)}&since=0&limit=50`, { credentials: 'include' }); const d = await r.json(); const m = (d.messages||[]).slice(-1)[0]; out.lastRole = m && m.payload && m.payload.role; out.last = m && m.payload && String(m.payload.content||'').slice(0,80); } catch (_) {}
        try { const r = await fetch(`/api/pipeline/state?ip=${encodeURIComponent(ip)}`, { credentials: 'include' }); const d = await r.json(); out.ssot = d && (d.stages ? (d.stages.ssot && d.stages.ssot.status) : (d.passed||[]).includes('ssot') ? 'passed' : undefined); out.running = d && d.running; } catch (_) {}
        return out;
      }, EFFIP);
      tail = ` | orch:${diag.lastRole||'-'}="${diag.last||''}" running=${JSON.stringify(diag.running||[])}`;
    }
    log(`poll ${i}: workers=${ws.length} active=${active.length}`, active.map(w => `${w.workflow}:${w.running_count||0}r/${w.pending_count||0}p`).join(',') + tail);
    if (active.length) break;
  }

  // open the orchestrator workspace for this IP and screenshot
  const url = `${BASE}/?session_id=${USER}&ip=${EFFIP}&workflow=orchestrator`;
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(5000);
  await page.screenshot({ path: `${OUT}/02-worker-strip-full.png`, fullPage: false });
  log('saved 02-worker-strip-full.png');

  // crop bottom area (input row + strip above it)
  await page.screenshot({ path: `${OUT}/02-worker-strip-bottom.png`, clip: { x: 0, y: 760, width: 1600, height: 240 } });
  log('saved 02-worker-strip-bottom.png');

  // detect & click the strip chip button (title contains 'worker session')
  const clicked = await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const chip = btns.find(b => /worker session for full live detail/i.test(b.getAttribute('title') || ''));
    if (chip) { chip.click(); return chip.textContent.trim(); }
    return null;
  });
  log('clicked chip:', clicked);
  if (clicked) {
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${OUT}/03-after-click.png`, fullPage: false });
    log('saved 03-after-click.png');
  }
} catch (e) {
  log('ERROR', e.message);
} finally {
  await browser.close();
}
