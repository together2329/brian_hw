// Gap 1: cookie auth flow. login → me → logout → me(401) → anon API(401).
import { launch, login, logout, jget, assert, assertEq, failures, exitCode, log, BASE, USER } from './lib.mjs';

const { browser, page } = await launch();
try {
  const li = await login(page);
  assertEq(li.status, 200, 'login returns 200');

  const me1 = await jget(page, '/api/users/me');
  assertEq(me1.status, 200, 'me after login is 200');
  assertEq(me1.body && me1.body.user && me1.body.user.username, USER, 'me reports the logged-in username');

  const lo = await logout(page);
  assert(lo.status === 200 || lo.status === 204, `logout ok (got ${lo.status})`);

  const me2 = await jget(page, '/api/users/me');
  assertEq(me2.status, 401, 'me after logout is 401');

  // fresh context with no cookie at all
  const ctx2 = await browser.newContext();
  const p2 = await ctx2.newPage();
  await p2.goto(BASE, { waitUntil: 'domcontentloaded' });
  const anon = await jget(p2, '/api/ip/list');
  assert(anon.status === 401 || anon.status === 403, `anon /api/ip/list is denied (got ${anon.status})`);
  await ctx2.close();
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
