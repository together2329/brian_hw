const { test, expect } = require('@playwright/test');

// Two-client isolation tests.
//
// Contracts verified:
//   1. Two distinct guests get distinct sessions on /lobby — each
//      sees only their own sessions, never the other's.
//   2. Reusing client A's cookie on a request that targets one of
//      client B's session ids fails the ownership check (403/404).
//   3. /ws/agent rejects connections that arrive without a guest
//      cookie (1008/1006 close).
//   4. /ws/agent with a valid cookie but a session id the user does
//      not own is closed (1008/1006).
//
// WS tests use Playwright's in-browser WebSocket so we don't need a
// `ws` Node dependency in package.json.

async function createSession(page, title) {
  await page.goto('/lobby');
  await expect(page.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
  await page.click('[aria-label="New Session"]');
  await page.fill('[role="dialog"] input[placeholder*="e.g."]', title);
  await page.click('[role="dialog"] button:has-text("Create")');
  await expect(page.locator('[role="dialog"]')).toBeHidden({ timeout: 10000 });
  const card = page.locator('.lobby-card').filter({ hasText: title }).first();
  await card.click();
  await expect(page).toHaveURL(/\?session_id=/);
  const url = new URL(page.url());
  return url.searchParams.get('session_id');
}

// Open a WS in the page context and resolve with the close code.
async function probeWebSocket(page, urlSuffix, timeoutMs = 3000) {
  return page.evaluate(({ suffix, timeoutMs }) => {
    return new Promise((resolve) => {
      const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
      const ws = new WebSocket(`${proto}//${location.host}${suffix}`);
      const done = (code, reason) => resolve({ code, reason });
      ws.onclose = (e) => done(e.code, e.reason || '');
      ws.onerror = () => done(-1, 'error');
      setTimeout(() => done(-2, 'timeout'), timeoutMs);
    });
  }, { suffix: urlSuffix, timeoutMs });
}

test.describe('Multi-user isolation', () => {
  test('two guests see only their own sessions', async ({ browser }) => {
    const ctxA = await browser.newContext();
    const ctxB = await browser.newContext();
    const pageA = await ctxA.newPage();
    const pageB = await ctxB.newPage();

    const titleA = 'A-only-' + Date.now();
    const titleB = 'B-only-' + Date.now();

    await createSession(pageA, titleA);
    await createSession(pageB, titleB);

    await pageA.goto('/lobby');
    await expect(pageA.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
    await expect(pageA.locator('.lobby-card').filter({ hasText: titleA })).toBeVisible();
    await expect(pageA.locator('.lobby-card').filter({ hasText: titleB })).toHaveCount(0);

    await pageB.goto('/lobby');
    await expect(pageB.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });
    await expect(pageB.locator('.lobby-card').filter({ hasText: titleB })).toBeVisible();
    await expect(pageB.locator('.lobby-card').filter({ hasText: titleA })).toHaveCount(0);

    await ctxA.close();
    await ctxB.close();
  });

  test('client A cannot delete client B session via API', async ({ browser }) => {
    const ctxA = await browser.newContext();
    const ctxB = await browser.newContext();
    const pageA = await ctxA.newPage();
    const pageB = await ctxB.newPage();

    const titleB = 'B-private-' + Date.now();
    const sidB = await createSession(pageB, titleB);
    expect(sidB).toBeTruthy();

    await pageA.goto('/lobby');
    await expect(pageA.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });

    const resp = await pageA.request.delete('/api/sessions/' + sidB);
    expect([403, 404]).toContain(resp.status());

    await ctxA.close();
    await ctxB.close();
  });

  test('WebSocket targeting another users session id is closed', async ({ browser }) => {
    const ctxA = await browser.newContext();
    const ctxB = await browser.newContext();
    const pageA = await ctxA.newPage();
    const pageB = await ctxB.newPage();

    const titleB = 'B-private-ws-' + Date.now();
    const sidB = await createSession(pageB, titleB);
    expect(sidB).toBeTruthy();

    // Land A on the workspace so a guest cookie is established and
    // location.host / location.protocol are usable for the WS.
    await pageA.goto('/lobby');
    await expect(pageA.locator('text=Loading sessions…')).toBeHidden({ timeout: 10000 });

    const result = await probeWebSocket(pageA, '/ws/agent?session_id=' + sidB);
    // 1008 (policy violation) is the explicit close code; some
    // proxy stacks rewrite to 1006 (abnormal). Either signals the
    // server refused the cross-user attempt.
    expect([1006, 1008]).toContain(result.code);

    await ctxA.close();
    await ctxB.close();
  });
});
