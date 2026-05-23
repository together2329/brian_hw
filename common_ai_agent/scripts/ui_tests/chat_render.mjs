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
    // The chat feed mounts under the center CHAT tab; orchestrator workflow
    // lands on the worker-status tab, where the feed isn't rendered.
    await page.evaluate(() => {
      const el = [...document.querySelectorAll('button,span,div,[role="tab"]')]
        .find(x => (x.textContent || '').trim().toUpperCase() === 'CHAT' && x.offsetParent !== null);
      if (el) el.click();
    });
    // Wait for the 1s poller to actually hydrate feed entries (avoids a
    // 0-entry race under server load), then a beat for fusion to settle.
    await page.waitForFunction(
      () => document.querySelectorAll('.feed-entry, .react-block, .tool-card').length > 0,
      { timeout: 15000 },
    ).catch(() => {});
    await page.waitForTimeout(2500);

    // Feed entries are class-marked, not [data-kind] (that attr only exists in
    // the code-fold tree view). Map each kind to its real DOM marker.
    const KIND_SELECTORS = {
      agent:   '.feed-entry-agent, .md-agent',
      thought: '.react-block.thought',
      action:  '.react-block.action, .tool-card',          // tool-card = fused action+obs / handoff
      // A result renders standalone (.react-block.obs) or fused inside a tool
      // card. Fused single-line results have no body class, but the card draws
      // a .tool-card-sep separator only when it carries a result; markdown/pre
      // bodies and the handoff result block are the multi-line/special forms.
      obs:     '.react-block.obs, .md-tool-result, .tool-output-pre, .handoff-result, .tool-card-sep',
    };
    const dom = await page.evaluate((sel) => {
      const present = {};
      for (const k of Object.keys(sel)) present[k] = document.querySelectorAll(sel[k]).length;
      const totalFeed = document.querySelectorAll('.feed-entry, .react-block, .tool-card').length;
      return { present, totalFeed };
    }, KIND_SELECTORS);
    assert(dom.totalFeed > 0, `feed rendered entries (got ${dom.totalFeed})`);

    for (const role of rolesPresent) {
      const kind = ROLE_TO_KIND[role];
      if (!kind) continue;
      assert((dom.present[kind] || 0) > 0, `role "${role}" → DOM kind "${kind}" present (counts: ${JSON.stringify(dom.present)})`);
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
