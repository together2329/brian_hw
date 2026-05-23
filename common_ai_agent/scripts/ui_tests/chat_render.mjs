// Gap 8: faux-stream chat — DB messages render as agent/thought/tool DOM kinds.
import { launch, login, jget, gotoWorkspace, shoot, assert, failures, exitCode, log, skip } from './lib.mjs';

const ROLE_TO_KIND = { assistant: 'agent', thought: 'thought', reasoning: 'thought', tool: 'action', tool_result: 'obs', observation: 'obs', obs: 'obs' };

const { browser, page } = await launch();
try {
  await login(page);

  // find an IP that already has orchestrator chat history
  const list = await jget(page, '/api/ip/list');
  const names = (list.body && (list.body.items || list.body.ips || [])).map(x => x.name || x);
  const candidates = [...new Set([...names, 'vmode_orch', 'shot_ctr2', 'shot_counter'])].filter(Boolean);

  let target = null, msgs = [];
  for (const ip of candidates) {
    const r = await jget(page, `/api/orchestrator/chat/messages?ip=${encodeURIComponent(ip)}&since=0&limit=50`);
    const m = (r.body && r.body.messages) || [];
    if (m.length) { target = ip; msgs = m; break; }
  }

  if (!target) { skip('no IP has orchestrator chat history — nothing to render-test'); }
  else {
    log(`chat history found on ip=${target} (${msgs.length} msgs)`);
    const rolesPresent = [...new Set(msgs.map(m => String((m.payload || {}).role || '').toLowerCase()).filter(Boolean))];
    await gotoWorkspace(page, { ip: target, workflow: 'orchestrator' });
    await page.waitForTimeout(4000); // let the 1s poller hydrate the feed

    const dom = await page.evaluate(() => {
      const kinds = [...document.querySelectorAll('[data-kind]')].map(e => e.getAttribute('data-kind'));
      return { count: kinds.length, kinds: [...new Set(kinds)] };
    });
    assert(dom.count > 0, `feed rendered entries with [data-kind] (got ${dom.count})`);

    for (const role of rolesPresent) {
      const kind = ROLE_TO_KIND[role];
      if (!kind) continue;
      assert(dom.kinds.includes(kind), `role "${role}" → DOM kind "${kind}" present (kinds: ${dom.kinds.join(',')})`);
    }
    await shoot(page, 'chat-render.png');
  }
} catch (e) {
  assert(false, 'unexpected error: ' + e.message);
} finally {
  await browser.close();
}
log(`done: ${failures().length} failure(s)`);
process.exit(exitCode());
