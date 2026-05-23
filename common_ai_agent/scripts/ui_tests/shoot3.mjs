import { chromium } from 'playwright';

const BASE = process.env.BASE || 'http://127.0.0.1:3001';
const USER = process.env.U || 'admin';
const PASS = process.env.P || '1151';
const IP = process.env.IP || 'shot_ctr2';
const OUT = '/Users/brian/Desktop/Project/brian_hw/common_ai_agent/.omc/ui-shots';
const log = (...a) => console.log('[shoot3]', ...a);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();

const findChip = () => page.evaluate(() => {
  const btns = Array.from(document.querySelectorAll('button'));
  const chip = btns.find(b => /worker session for full live detail/i.test(b.getAttribute('title') || ''));
  return chip ? chip.textContent.trim() : null;
});

try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async ({ u, p }) => {
    await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u, password: p }), credentials: 'include' });
  }, { u: USER, p: PASS });

  // fresh run (hijack-safe message)
  const kick = await page.evaluate(async (ip) => {
    const r = await fetch('/api/pipeline/orchestrator/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
      body: JSON.stringify({ message: 'Dispatch ssot-gen now and begin a 4-bit synchronous counter design. Auto-advance every stage, never pause.', ip }),
    });
    let b = null; try { b = await r.json(); } catch (_) {}
    return { status: r.status, body: b };
  }, IP);
  const EFFIP = (kick.body && kick.body.ip) ? String(kick.body.ip) : IP;
  log('kick:', kick.status, 'effIP=', EFFIP);

  // land in the workspace chat for that IP
  await page.goto(`${BASE}/?session_id=${USER}&ip=${EFFIP}&workflow=orchestrator`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  // click the WORKSPACE nav tab
  const navClicked = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('button, a, [role="tab"], .dir-btn, .nav-btn, span'));
    const t = els.find(e => /^\s*[⌂\s]*WORKSPACE\s*$/i.test((e.textContent || '').trim()) && e.offsetParent !== null);
    if (t) { t.click(); return (t.textContent || '').trim(); }
    return null;
  });
  log('nav WORKSPACE click:', navClicked);
  await page.waitForTimeout(2500);

  // wait for the worker strip chip to appear (worker running → strip renders)
  let chip = null;
  for (let i = 0; i < 30; i++) {
    chip = await findChip();
    const snap = await page.evaluate(async (ip) => {
      try { const r = await fetch(`/api/orchestrator/workers?ip=${encodeURIComponent(ip)}`, { credentials: 'include' }); const d = await r.json(); const ws = (d.workers || []); const a = ws.filter(w => Number(w.running_count||0)>0||Number(w.pending_count||0)>0||Number(w.queued_count||0)>0); return a.map(w=>`${w.workflow}:${w.running_count||0}r/${w.pending_count||0}p`).join(','); } catch (_) { return 'err'; }
    }, EFFIP);
    log(`poll ${i}: chip=${chip ? JSON.stringify(chip) : 'none'} active=[${snap}]`);
    if (chip) break;
    await page.waitForTimeout(3000);
  }

  await page.screenshot({ path: `${OUT}/02-worker-strip-full.png`, fullPage: false });
  await page.screenshot({ path: `${OUT}/02-worker-strip-bottom.png`, clip: { x: 0, y: 720, width: 1600, height: 280 } });
  log('saved 02 strip shots (chip=', chip, ')');

  if (chip) {
    await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const c = btns.find(b => /worker session for full live detail/i.test(b.getAttribute('title') || ''));
      if (c) c.click();
    });
    await page.waitForTimeout(4500);
    await page.screenshot({ path: `${OUT}/03-after-click.png`, fullPage: false });
    log('saved 03-after-click.png');
  }
} catch (e) {
  log('ERROR', e.message);
} finally {
  await browser.close();
}
