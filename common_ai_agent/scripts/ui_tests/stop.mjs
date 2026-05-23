import { chromium } from 'playwright';
const BASE = 'http://127.0.0.1:3001';
const IPS = ['shot_ctr2', 'shot_counter', 'confirmation'];
const log = (...a) => console.log('[stop]', ...a);

const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await (await browser.newContext()).newPage();
try {
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  await page.evaluate(async () => {
    await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: 'admin', password: '1151' }), credentials: 'include' });
  });
  for (const ip of IPS) {
    const r = await page.evaluate(async (ip) => {
      const res = await fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ message: 'Stop now. Do not dispatch anything else. Finalize this run as blocked immediately.', ip }),
      });
      let b = null; try { b = await res.json(); } catch (_) {}
      return { status: res.status, ip: b && b.ip, run: b && b.run_id, st: b && b.status };
    }, ip);
    log(ip, '->', JSON.stringify(r));
    await page.waitForTimeout(1500);
  }
} catch (e) { log('ERR', e.message); } finally { await browser.close(); }
