// Gap 2: multi-user isolation through the real HTTP+cookie boundary.
// admin (ctxA) creates a unique IP; a fresh no-cookie context (ctxB) must NOT
// be able to read it. (We avoid creating a 2nd persistent DB user on the live
// server; the cookie gate is what enforces isolation, so anon = the probe.)
import { launch, login, jget, jpost, assert, failures, exitCode, log, uniqueIp, BASE } from './lib.mjs';

const { browser, page } = await launch();
const ip = uniqueIp('iso');
try {
  await login(page);
  const created = await jpost(page, '/api/ip/create', { name: ip });
  assert(created.status === 200 && created.body && created.body.ok, `admin created IP ${ip}`);

  const listA = await jget(page, '/api/ip/list');
  const namesA = (listA.body && (listA.body.items || listA.body.ips || [])).map(x => x.name || x);
  assert(Array.isArray(namesA) && namesA.includes(ip), 'admin sees the new IP in /api/ip/list');

  // ctxB: no cookie → must be denied / must not see admin's IP
  const ctxB = await browser.newContext();
  const pB = await ctxB.newPage();
  await pB.goto(BASE, { waitUntil: 'domcontentloaded' });
  const listB = await jget(pB, '/api/ip/list');
  const deniedOrEmpty = listB.status === 401 || listB.status === 403 ||
    !((listB.body && (listB.body.items || listB.body.ips || [])).map(x => x.name || x).includes(ip));
  assert(deniedOrEmpty, `anon context cannot see admin's IP (status ${listB.status})`);

  const runB = await jget(pB, `/api/orchestrator/active_run?ip=${ip}`);
  const runHidden = runB.status === 401 || runB.status === 403 || !(runB.body && runB.body.run);
  assert(runHidden, `anon cannot read admin IP active_run (status ${runB.status})`);
  await ctxB.close();
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
